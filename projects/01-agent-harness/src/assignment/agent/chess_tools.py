"""Chess tool implementations, decoupled from the agent that registers them.

Every function here takes the HTTP client explicitly instead of reading it off
an agent, so the same code can run in the agent process or inside the sandbox
beside the server it talks to.
"""

from __future__ import annotations

import base64
import json
from typing import Any
import base64
import json

import httpx

CHESS_PORT = 8000


def _request_state(
    client: httpx.Client, method: str, endpoint: str, **kwargs: Any
) -> dict[str, Any]:
    """Make one chess API request and validate its JSON response."""

    response = client.request(method, endpoint, **kwargs)
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Chess server returned non-JSON ({response.status_code})."
        ) from exc
    if response.status_code >= 400:
        detail = (
            payload.get("detail", payload) if isinstance(payload, dict) else payload
        )
        raise ValueError(str(detail))
    if not isinstance(payload, dict):
        raise RuntimeError("Chess server response must be a JSON object.")
    return payload


def _simulate_move(client: httpx.Client, arguments: str) -> str:
    """New tool: inspect FEN or simulate one ply without changing the game.

    Takes the raw JSON arguments of one tool call and returns the observation
    to send back, so a bad argument or a server error reaches the model as a
    recoverable ``<chess_error>`` instead of ending the run.
    """
    # TODO(Part 3.3.b): Parse the arguments, call the provided
    # /api/simulate endpoint with fen and optional move, and return its JSON.
    # Catch any errors raised by the tool and return an error message between
    # `<chess_error></chess_error>` for the agent to address. Cover malformed
    # JSON arguments, arguments that are not an object, a missing or
    # non-string fen, a non-string move, a position or move the server rejects,
    # and a transport failure.
    try:
        args = json.loads(arguments)

        if not isinstance(args, dict):
            raise ValueError("Arguments must be a JSON object.")

        fen = args.get("fen")
        move = args.get("move")

        if not isinstance(fen, str) or not fen:
            raise ValueError("fen must be a non-empty string.")

        if move is not None and not isinstance(move, str):
            raise ValueError("move must be a string or null.")

        payload = {"fen": fen}

        if move is not None:
            payload["move"] = move

        state = _request_state(
            client,
            "POST",
            "/api/simulate",
            json=payload,
        )

        return json.dumps(state)

    except (
        json.JSONDecodeError,
        ValueError,
        TypeError,
        RuntimeError,
        httpx.HTTPError,
    ) as exc:
        return f"<chess_error>{exc}</chess_error>"


def _play_move(client: httpx.Client, arguments: str) -> str:
    """Existing tool: play one move as White and return the resulting state.

    Takes the raw JSON arguments of one tool call. Returns the new state, or a
    `<chess_error>` observation if the move could not be played.
    """
    # TODO(3.1.b): Parse the arguments and POST {"move": <uci move>} to
    # /api/move. Return its JSON object. Catch any errors raised by the
    # tool and return an error message between `<chess_error></chess_error>`
    # for the agent to address. Cover malformed JSON arguments, arguments
    # that are not an object, a missing or non-string fen, a non-string move,
    # a position or move the server rejects, and a transport failure.
    try:
        args = json.loads(arguments)

        if not isinstance(args, dict):
            raise ValueError("Arguments must be a JSON object.")

        move = args.get("move")

        if not isinstance(move, str):
            raise ValueError("move must be a string.")

        state = _request_state(
            client,
            "POST",
            "/api/move",
            json={"move": move},
        )

        return json.dumps(state)

    except (
        json.JSONDecodeError,
        ValueError,
        TypeError,
        RuntimeError,
        httpx.HTTPError,
    ) as exc:
        return f"<chess_error>{exc}</chess_error>"


def _run_python(env: Any, port: int, arguments: str) -> str:
    """Run model-written Python inside the sandbox."""

    try:
        args = json.loads(arguments)

        if not isinstance(args, dict):
            raise ValueError("Arguments must be a JSON object.")

        code = args.get("code")

        if not isinstance(code, str):
            raise ValueError("code must be a string.")

        # Encode the Python so quotes/newlines don't get mangled by the shell.
        encoded = base64.b64encode(code.encode()).decode()

        result = env.execute(
            [
                "python",
                "/opt/assignment/sandbox_python.py",
                str(port),
                encoded,
            ],
            shell=False,
        )

        # If the sandbox command itself failed, that's a tool failure.
        if result.get("returncode") != 0:
            message = (
                result.get("exception_info")
                or result.get("stderr")
                or result.get("output")
                or "Sandbox execution failed."
            )

            return f"<chess_error>{message}</chess_error>"

        # sandbox_python.py puts its JSON result on stdout.
        stdout = result.get("stdout", "")

        if not isinstance(stdout, str) or not stdout.strip():
            raise RuntimeError("Sandbox runner returned no output.")

        return stdout

    except (
        json.JSONDecodeError,
        ValueError,
        TypeError,
        RuntimeError,
    ) as exc:
        return f"<chess_error>{exc}</chess_error>"


def _invoke_skill(
    skills: dict[str, dict[str, str]],
    arguments: str,
) -> str:
    """Load one skill's instructions into the conversation."""

    try:
        args = json.loads(arguments)

        if not isinstance(args, dict):
            raise ValueError("Arguments must be a JSON object.")

        name = args.get("name")

        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string.")

        if name not in skills:
            raise ValueError(f"Unknown skill: {name}")

        content = skills[name].get("content")

        if not isinstance(content, str):
            raise ValueError(f"Skill {name} has invalid content.")

        return content

    except (
        json.JSONDecodeError,
        ValueError,
        TypeError,
    ) as exc:
        return f"<chess_error>{exc}</chess_error>"


def _game_state(client: httpx.Client, reset: bool = False) -> dict:
    """Read the live game, or start a new one and read the opening position."""

    method, endpoint = ("POST", "/api/reset") if reset else ("GET", "/api/state")
    return _request_state(client, method, endpoint)
