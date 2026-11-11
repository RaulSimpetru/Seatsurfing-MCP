"""API-token mode, and unchanged password mode, against a fake Seatsurfing server.

Run with: uv run python tests/test_token_mode.py
"""

import asyncio
import json
import os

import httpx

import seatsurfing_mcp as m

ME = "me@example.com"
seen: list[httpx.Request] = []


def handler(request: httpx.Request) -> httpx.Response:
    seen.append(request)
    assert request.headers["Authorization"] == "Bearer tok"
    path, method = request.url.path, request.method
    if path == "/booking/filter/":
        assert request.url.params["user"] == ME
        return httpx.Response(200, json=[{"id": "b1"}])
    if path == "/booking/" and method == "POST":
        assert json.loads(request.content)["userEmail"] == ME
        return httpx.Response(201, headers={"X-Object-ID": "b2"})
    if path == "/booking/mine":
        return httpx.Response(200, json={"userEmail": ME.upper()})
    if path == "/booking/theirs":
        assert method == "GET", "must not delete someone else's booking"
        return httpx.Response(200, json={"userEmail": "other@example.com"})
    raise AssertionError(f"unexpected request {method} {path}")


async def scenario() -> None:
    real = httpx.AsyncClient
    m.httpx.AsyncClient = lambda: real(transport=httpx.MockTransport(handler))
    try:
        c = m.SeatsurfingClient("https://seats.test", api_token="tok", user_email=ME)
        assert [b["id"] for b in await c.get_my_bookings()] == ["b1"]
        enter, leave = "2030-01-01T09:00:00.000Z", "2030-01-01T10:00:00.000Z"
        assert await c.create_booking("s1", enter, leave) == "b2"
        await c.delete_booking("mine")
        assert seen[-1].method == "DELETE"
        try:
            await c.delete_booking("theirs")
        except RuntimeError:
            pass
        else:
            raise AssertionError("cancelling another user's booking must be refused")
        assert not any(r.url.path.startswith("/auth/") for r in seen)
    finally:
        m.httpx.AsyncClient = real


def password_handler(request: httpx.Request) -> httpx.Response:
    path, method = request.url.path, request.method
    if path == "/auth/login":
        assert "Authorization" not in request.headers
        return httpx.Response(200, json={"accessToken": "acc", "refreshToken": "ref"})
    assert request.headers["Authorization"] == "Bearer acc"
    if path == "/booking/" and method == "GET":
        return httpx.Response(200, json=[])
    if path == "/booking/" and method == "POST":
        assert json.loads(request.content)["userEmail"] == ""
        return httpx.Response(201, headers={"X-Object-ID": "b3"})
    if path == "/booking/b3" and method == "DELETE":
        return httpx.Response(204)
    raise AssertionError(f"unexpected request {method} {path}")


async def password_scenario() -> None:
    real = httpx.AsyncClient
    m.httpx.AsyncClient = lambda: real(transport=httpx.MockTransport(password_handler))
    try:
        c = m.SeatsurfingClient("https://seats.test")
        await c.login(ME, "password", "org")
        assert await c.get_my_bookings() == []
        assert await c.create_booking("s1", "2030-01-01T09:00:00.000Z", "2030-01-01T10:00:00.000Z") == "b3"
        await c.delete_booking("b3")
    finally:
        m.httpx.AsyncClient = real


async def login_tool_scenario() -> None:
    """Tool arguments must not redirect the token or change who is booked for."""
    hosts: list[str] = []

    def login_handler(request: httpx.Request) -> httpx.Response:
        hosts.append(request.url.host)
        assert request.url.path == "/user/me"
        return httpx.Response(200, json={"email": "bot@example.com"})

    real, real_load, old_env = httpx.AsyncClient, m.load_config, dict(os.environ)
    m.httpx.AsyncClient = lambda: real(transport=httpx.MockTransport(login_handler))
    m.load_config = lambda: {"url": "https://seats.test", "email": ME, "api_token": "tok"}
    for name in list(os.environ):
        if name.startswith("SEATSURFING_"):
            del os.environ[name]
    try:
        out = await m.call_tool("seatsurfing_login", {"url": "https://evil.test", "email": "other@example.com"})
        assert "Token accepted" in out[0].text, out[0].text
        assert hosts == ["seats.test"], hosts
        assert m.client.user_email == ME
    finally:
        m.httpx.AsyncClient, m.load_config = real, real_load
        os.environ.clear()
        os.environ.update(old_env)


def test_token_mode() -> None:
    asyncio.run(scenario())


def test_login_tool_ignores_arguments_in_token_mode() -> None:
    asyncio.run(login_tool_scenario())


def test_password_mode_unchanged() -> None:
    asyncio.run(password_scenario())


if __name__ == "__main__":
    test_token_mode()
    test_login_tool_ignores_arguments_in_token_mode()
    test_password_mode_unchanged()
    print("ok")
