"""FastAPI bridge for the P0 browser -> authoritative Python vertical slice."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .. import config
from ..application.dashboard_service import DashboardService
from ..application.season_service import SeasonService
from ..career import CareerEngine
from ..persistence import deserialize_game, serialize_game
from ..player import Player
from ..production_advance import ProductionAdvanceService
from ..rng import RNG
from .store import IdempotencyConflict, RevisionConflict, SQLiteSessionStore, SessionStore

COOKIE_NAME = "baseball_sim_session"


class NewCareerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    position: str
    bats: Literal["LEFT", "RIGHT"]
    throws: Literal["LEFT", "RIGHT"]
    traitCount: int = Field(ge=0, le=3)


class AdvanceRequest(BaseModel):
    command: Literal["next_game", "week", "month", "season"]
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class SaveRequest(BaseModel):
    expected_revision: int = Field(ge=1)


class ApiProblem(RuntimeError):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        revision: int | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.revision = revision
        self.details = details


class DisabledProductionStore:
    """Fail closed when serverless deployment lacks an external durable store."""

    def _fail(self):
        raise ApiProblem(
            503,
            "SAVE_FAILED",
            "external transactional durable store is required in production",
            retryable=False,
        )

    def get(self, session_id: str):
        self._fail()

    def replace(self, session_id: str, payload: dict[str, object]):
        self._fail()

    def mutate(self, session_id: str, **kwargs):
        self._fail()


def _default_store() -> SessionStore:
    configured = os.getenv("BASEBALL_SIM_SQLITE_PATH")
    if configured:
        return SQLiteSessionStore(configured)
    if os.getenv("VERCEL") or os.getenv("BASEBALL_SIM_PRODUCTION") == "1":
        return DisabledProductionStore()  # type: ignore[return-value]
    return SQLiteSessionStore(Path(".local") / "baseball-sim.sqlite3")


def _session_id(request: Request, response: Response) -> str:
    existing = request.cookies.get(COOKIE_NAME)
    if existing:
        return existing
    session_id = uuid4().hex
    response.set_cookie(
        COOKIE_NAME,
        session_id,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return session_id


def _progress(engine: CareerEngine) -> dict[str, object]:
    session = engine.current_session
    advance_state = getattr(engine, "advance_state", None)
    game = int(session.games_completed) if session is not None else 0
    current_date = getattr(advance_state, "current_date", None)
    return {
        "year": int(engine.year),
        "game": game,
        "games_completed": game,
        "total_games": int(config.KBO_FIRST_TEAM_GAMES),
        "current_date": current_date.isoformat() if current_date is not None else None,
        "progress": round((game / int(config.KBO_FIRST_TEAM_GAMES)) * 100) if config.KBO_FIRST_TEAM_GAMES else 0,
    }


def _presentation(engine: CareerEngine, revision: int) -> dict[str, object]:
    progress = _progress(engine)
    dashboard = DashboardService().build(engine.player, year=engine.year, progress=progress).as_dict()
    season = SeasonService().build(engine.player, year=engine.year, progress=progress).as_dict()
    return {
        "data": {"dashboard": dashboard, "season": season},
        "meta": {"revision": revision},
    }


def _fingerprint(request: AdvanceRequest) -> str:
    canonical = json.dumps(
        {"command": request.command, "expected_revision": request.expected_revision},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_app(store: SessionStore | None = None) -> FastAPI:
    app = FastAPI(title="Baseball Player Simulator API", version="1")
    session_store = store or _default_store()
    app.state.session_store = session_store

    @app.exception_handler(ApiProblem)
    async def api_problem_handler(_request: Request, exc: ApiProblem):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "retryable": exc.retryable,
                    "details": exc.details,
                },
                "meta": {"revision": exc.revision},
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "request validation failed",
                    "retryable": False,
                    "details": {"errors": exc.errors()},
                },
                "meta": {"revision": None},
            },
        )

    @app.get("/api/v1/session")
    def get_session(request: Request, response: Response):
        session_id = _session_id(request, response)
        stored = session_store.get(session_id)
        return {
            "has_career": stored is not None,
            "revision": stored.revision if stored is not None else None,
        }

    @app.post("/api/v1/career", status_code=201)
    def create_career(body: NewCareerRequest, request: Request, response: Response):
        if body.position not in config.POSITIONS:
            raise ApiProblem(400, "INVALID_REQUEST", f"unsupported position: {body.position}")
        session_id = _session_id(request, response)
        seed = secrets.randbits(63)
        rng = RNG(seed)
        bats_throws = f"{'L' if body.bats == 'LEFT' else 'R'}/{'L' if body.throws == 'LEFT' else 'R'}"
        player = Player.random(body.name.strip(), rng, body.position, bats_throws, body.traitCount)
        engine = CareerEngine(player, rng)
        # Reuse the canonical domain transition; the HTTP layer does not invent
        # draft/team assignment semantics. The P0 slice begins at playable PRO.
        engine.evaluate_draft()
        ProductionAdvanceService(engine)
        stored = session_store.replace(session_id, serialize_game(engine))
        return _presentation(engine, stored.revision)

    @app.get("/api/v1/state")
    def get_state(request: Request, response: Response):
        session_id = _session_id(request, response)
        stored = session_store.get(session_id)
        if stored is None:
            raise ApiProblem(404, "NO_CAREER", "no career exists for this session")
        engine = deserialize_game(stored.payload)
        return _presentation(engine, stored.revision)

    @app.post("/api/v1/advance")
    def advance(body: AdvanceRequest, request: Request, response: Response):
        session_id = _session_id(request, response)
        if body.command != "next_game":
            raise ApiProblem(
                400,
                "INVALID_REQUEST",
                "P0 vertical slice supports command=next_game only",
                revision=body.expected_revision,
            )

        def mutate(payload: dict[str, object]):
            engine = deserialize_game(payload)
            service = ProductionAdvanceService(engine)
            service.advance_one_game()
            next_payload = serialize_game(engine)
            # Store supplies the committed revision after CAS; placeholder meta
            # is replaced atomically by SQLiteSessionStore.mutate.
            response_payload = _presentation(engine, body.expected_revision + 1)
            return next_payload, response_payload

        try:
            commit = session_store.mutate(
                session_id,
                expected_revision=body.expected_revision,
                idempotency_key=body.idempotency_key,
                fingerprint=_fingerprint(body),
                mutator=mutate,
            )
        except KeyError as exc:
            raise ApiProblem(404, "NO_CAREER", "no career exists for this session") from exc
        except RevisionConflict as exc:
            raise ApiProblem(
                409,
                "REVISION_CONFLICT",
                "expected_revision is stale",
                revision=exc.revision,
            ) from exc
        except IdempotencyConflict as exc:
            current = session_store.get(session_id)
            raise ApiProblem(
                409,
                "SIMULATION_CONFLICT",
                str(exc),
                revision=current.revision if current else None,
            ) from exc
        return commit.response

    @app.post("/api/v1/save", status_code=204)
    def save_checkpoint(body: SaveRequest, request: Request, response: Response):
        session_id = _session_id(request, response)
        stored = session_store.get(session_id)
        if stored is None:
            raise ApiProblem(404, "NO_CAREER", "no career exists for this session")
        if stored.revision != body.expected_revision:
            raise ApiProblem(
                409,
                "REVISION_CONFLICT",
                "expected_revision is stale",
                revision=stored.revision,
            )
        response.status_code = 204
        return None

    return app


app = create_app()
