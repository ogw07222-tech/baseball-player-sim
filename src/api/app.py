"""FastAPI bridge for the browser -> authoritative Python production slice."""
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
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .. import config
from ..application.dashboard_service import DashboardService
from ..application.season_service import SeasonService
from ..career import CareerEngine
from ..interactive_event_effects import InteractiveCareerEffectState, UnsupportedInteractiveEffect
from ..persistence import deserialize_game, serialize_game
from ..player import Player
from ..production_advance import ProductionAdvanceService, SeasonCompleteError
from ..rng import RNG
from ..time_advance import AdvanceResultViewModel
from .store import (
    IdempotencyConflict,
    PostgresSessionStore,
    RevisionConflict,
    SQLiteSessionStore,
    SessionStore,
    StoreUnavailable,
)

COOKIE_NAME = "baseball_sim_session"
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365


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


class ResolveEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    choice_id: str = Field(min_length=1, max_length=200)
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


def _is_production_runtime() -> bool:
    return bool(os.getenv("VERCEL") or os.getenv("BASEBALL_SIM_PRODUCTION") == "1")


def _external_database_url() -> str | None:
    for name in ("BASEBALL_SIM_DATABASE_URL", "DATABASE_URL", "POSTGRES_URL"):
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def _default_store() -> SessionStore:
    database_url = _external_database_url()
    if _is_production_runtime():
        if database_url:
            return PostgresSessionStore(database_url)
        return DisabledProductionStore()  # type: ignore[return-value]

    if database_url:
        return PostgresSessionStore(database_url)
    configured_sqlite = os.getenv("BASEBALL_SIM_SQLITE_PATH")
    if configured_sqlite:
        return SQLiteSessionStore(configured_sqlite)
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
        secure=_is_production_runtime(),
        path="/",
        max_age=COOKIE_MAX_AGE_SECONDS,
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


def _pending_events(engine: CareerEngine) -> list[dict[str, object]]:
    state = getattr(engine, "interactive_event_state", None)
    pending = getattr(state, "pending", ())
    return [event.as_dict() for event in pending]


def _presentation(
    engine: CareerEngine,
    revision: int,
    *,
    mutation: dict[str, object] | None = None,
) -> dict[str, object]:
    progress = _progress(engine)
    dashboard = DashboardService().build(engine.player, year=engine.year, progress=progress).as_dict()
    season = SeasonService().build(engine.player, year=engine.year, progress=progress).as_dict()
    payload: dict[str, object] = {
        "data": {
            "dashboard": dashboard,
            "season": season,
            "pending_events": _pending_events(engine),
        },
        "meta": {"revision": revision},
    }
    if mutation is not None:
        payload["mutation"] = mutation
    return payload


def _fingerprint(request: AdvanceRequest) -> str:
    canonical = json.dumps(
        {"command": request.command, "expected_revision": request.expected_revision},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _resolve_fingerprint(event_id: str, request: ResolveEventRequest) -> str:
    canonical = json.dumps(
        {
            "kind": "resolve_event",
            "event_id": event_id,
            "choice_id": request.choice_id,
            "expected_revision": request.expected_revision,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _problem_response(
    *,
    status_code: int,
    code: str,
    message: str,
    retryable: bool,
    revision: int | None = None,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "retryable": retryable,
                "details": details,
            },
            "meta": {"revision": revision},
        },
    )


def create_app(store: SessionStore | None = None) -> FastAPI:
    app = FastAPI(title="Baseball Player Simulator API", version="1")
    session_store = store or _default_store()
    app.state.session_store = session_store

    @app.exception_handler(ApiProblem)
    async def api_problem_handler(_request: Request, exc: ApiProblem):
        return _problem_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            retryable=exc.retryable,
            revision=exc.revision,
            details=exc.details,
        )

    @app.exception_handler(StoreUnavailable)
    async def store_unavailable_handler(_request: Request, _exc: StoreUnavailable):
        return _problem_response(
            status_code=503,
            code="SAVE_FAILED",
            message="external durable store is unavailable",
            retryable=True,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        return _problem_response(
            status_code=422,
            code="INVALID_REQUEST",
            message="request validation failed",
            retryable=False,
            details={"errors": exc.errors()},
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
        if body.command == "season":
            raise ApiProblem(
                400,
                "INVALID_REQUEST",
                "automatic season advance is not available; season finalization remains explicit",
                revision=body.expected_revision,
            )

        def mutate(payload: dict[str, object]):
            engine = deserialize_game(payload)
            service = ProductionAdvanceService(engine)
            if body.command == "next_game":
                summary = service.advance_one_game()
            elif body.command == "week":
                summary = service.advance_one_week()
            elif body.command == "month":
                summary = service.advance_one_month()
            else:  # Pydantic constrains this branch; keep fail-closed for type drift.
                raise ApiProblem(400, "INVALID_REQUEST", f"unsupported advance command: {body.command}")
            next_payload = serialize_game(engine)
            result = AdvanceResultViewModel.from_summary(summary).as_dict()
            result["pending_events"] = _pending_events(engine)
            response_payload = _presentation(
                engine,
                body.expected_revision + 1,
                mutation={
                    "kind": "advance",
                    "command": body.command,
                    "result": result,
                },
            )
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
        except SeasonCompleteError as exc:
            raise ApiProblem(
                409,
                "SEASON_COMPLETE",
                str(exc),
                retryable=False,
                revision=body.expected_revision,
            ) from exc
        return commit.response

    @app.post("/api/v1/events/{event_id}/resolve")
    def resolve_event(event_id: str, body: ResolveEventRequest, request: Request, response: Response):
        session_id = _session_id(request, response)

        def mutate(payload: dict[str, object]):
            engine = deserialize_game(payload)
            service = ProductionAdvanceService(engine)
            resolution = service.resolve_interactive_event(event_id, body.choice_id)
            event_state = getattr(engine, "interactive_event_state", None)
            resolved_event = next(
                event for event in getattr(event_state, "events", ()) if event.event_id == event_id
            )
            effect_state = getattr(engine, "interactive_career_effect_state", None)
            applied_effects = []
            if isinstance(effect_state, InteractiveCareerEffectState):
                applied_effects = [
                    effect.as_dict()
                    for effect in effect_state.active_effects
                    if effect.source_event_id == event_id
                ]
            result = {
                "resolved_event": resolved_event.as_dict(),
                "applied_effects": applied_effects,
                "resolution": resolution.as_dict(),
                "pending_events": _pending_events(engine),
            }
            next_payload = serialize_game(engine)
            response_payload = _presentation(
                engine,
                body.expected_revision + 1,
                mutation={
                    "kind": "resolve_event",
                    "event_id": event_id,
                    "choice_id": body.choice_id,
                    "result": result,
                },
            )
            return next_payload, response_payload

        try:
            commit = session_store.mutate(
                session_id,
                expected_revision=body.expected_revision,
                idempotency_key=body.idempotency_key,
                fingerprint=_resolve_fingerprint(event_id, body),
                mutator=mutate,
            )
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
        except UnsupportedInteractiveEffect as exc:
            current = session_store.get(session_id)
            raise ApiProblem(
                422,
                "UNSUPPORTED_EVENT_EFFECT",
                str(exc),
                retryable=False,
                revision=current.revision if current else body.expected_revision,
            ) from exc
        except KeyError as exc:
            current = session_store.get(session_id)
            if current is None:
                raise ApiProblem(404, "NO_CAREER", "no career exists for this session") from exc
            raise ApiProblem(
                404,
                "EVENT_NOT_FOUND",
                str(exc),
                retryable=False,
                revision=current.revision,
            ) from exc
        except ValueError as exc:
            current = session_store.get(session_id)
            raise ApiProblem(
                400,
                "INVALID_EVENT_CHOICE",
                str(exc),
                retryable=False,
                revision=current.revision if current else body.expected_revision,
            ) from exc
        except RuntimeError as exc:
            current = session_store.get(session_id)
            message = str(exc)
            if "not pending" in message:
                code = "EVENT_ALREADY_RESOLVED"
            else:
                code = "EVENT_RESOLUTION_UNAVAILABLE"
            raise ApiProblem(
                409,
                code,
                message,
                retryable=False,
                revision=current.revision if current else body.expected_revision,
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

    @app.api_route(
        "/api/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        include_in_schema=False,
    )
    def unknown_api(path: str):
        raise ApiProblem(404, "NOT_FOUND", f"API route not found: /api/{path}")

    frontend_dir = Path(__file__).resolve().parents[2] / "web" / "dist"
    if frontend_dir.is_dir():
        frontend_root = frontend_dir.resolve()
        assets_dir = frontend_root / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa_frontend(path: str):
            candidate = (frontend_root / path).resolve()
            if path and candidate.is_file() and frontend_root in candidate.parents:
                return FileResponse(candidate)
            return FileResponse(frontend_root / "index.html")

    return app


app = create_app()
