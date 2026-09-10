#!/usr/bin/env python3
"""Reproducible deployed P0 smoke test.

Usage:
    python tools/deployed_p0_smoke.py https://your-project.vercel.app
"""
from __future__ import annotations

import argparse
import sys
from uuid import uuid4

import httpx


CAREER = {
    "name": "Deployment Smoke",
    "position": "SS",
    "bats": "RIGHT",
    "throws": "RIGHT",
    "traitCount": 1,
}


def require(response: httpx.Response, status: int, label: str) -> dict:
    if response.status_code != status:
        raise AssertionError(
            f"{label}: expected {status}, got {response.status_code}: {response.text[:500]}"
        )
    if status == 204:
        return {}
    payload = response.json()
    if not isinstance(payload, dict):
        raise AssertionError(f"{label}: response must be a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", help="Production deployment URL")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    with httpx.Client(base_url=base_url, follow_redirects=True, timeout=60) as client:
        session = require(client.get("/api/v1/session"), 200, "session")
        print("session", session)

        created = require(client.post("/api/v1/career", json=CAREER), 201, "career")
        revision = int(created["meta"]["revision"])
        if revision != 1:
            raise AssertionError(f"career: expected revision 1, got {revision}")

        state = require(client.get("/api/v1/state"), 200, "state")
        if state != created:
            raise AssertionError("state after create does not match committed career snapshot")

        key = f"deployment-smoke-{uuid4().hex}"
        advance_body = {
            "command": "next_game",
            "expected_revision": revision,
            "idempotency_key": key,
        }
        advanced = require(client.post("/api/v1/advance", json=advance_body), 200, "advance")
        next_revision = int(advanced["meta"]["revision"])
        if next_revision != revision + 1:
            raise AssertionError(
                f"advance: expected revision {revision + 1}, got {next_revision}"
            )
        games = int(advanced["data"]["dashboard"]["progress"]["game"])
        if games != 1:
            raise AssertionError(f"advance: expected one completed game, got {games}")

        replay = require(client.post("/api/v1/advance", json=advance_body), 200, "replay")
        if replay != advanced:
            raise AssertionError("idempotent replay returned a different committed response")

        stale = require(
            client.post(
                "/api/v1/advance",
                json={
                    "command": "next_game",
                    "expected_revision": revision,
                    "idempotency_key": f"stale-{uuid4().hex}",
                },
            ),
            409,
            "stale revision",
        )
        if stale.get("error", {}).get("code") != "REVISION_CONFLICT":
            raise AssertionError(f"stale revision: wrong error schema: {stale}")

        cookie = client.cookies.get("baseball_sim_session")
        if not cookie:
            raise AssertionError("session cookie missing")

        with httpx.Client(base_url=base_url, follow_redirects=True, timeout=60) as resumed:
            resumed.cookies.set("baseball_sim_session", cookie)
            recovered = require(resumed.get("/api/v1/state"), 200, "resume")
        if recovered != advanced:
            raise AssertionError("durable resume did not recover the committed state")

        bad_api = require(client.get("/api/v1/not-a-route"), 404, "api 404")
        if bad_api.get("error", {}).get("code") != "NOT_FOUND":
            raise AssertionError(f"API 404 was not the normal error schema: {bad_api}")

    print(
        "PASS: create/state/next_game/revision/idempotency/stale-409/"
        "new-client persistence/API-error-schema"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise
