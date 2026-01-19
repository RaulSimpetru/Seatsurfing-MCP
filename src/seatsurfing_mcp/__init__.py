"""
Seatsurfing MCP Server

An MCP server that lets you book desks and rooms in Seatsurfing via Claude.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx


def get_config_path() -> Path:
    """Get the path to the config file."""
    return Path.home() / ".seatsurfing" / "config.json"


def get_spaces_cache_path() -> Path:
    """Get the path to the spaces cache file."""
    return Path.home() / ".seatsurfing" / "spaces.json"


def load_config() -> dict:
    """Load config from ~/.seatsurfing/config.json if it exists."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def load_spaces_cache() -> dict:
    """Load spaces cache from ~/.seatsurfing/spaces.json if it exists."""
    cache_path = get_spaces_cache_path()
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_spaces_cache(data: dict) -> None:
    """Save spaces cache to ~/.seatsurfing/spaces.json."""
    cache_path = get_spaces_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data, indent=2))


def get_credential(key: str, env_var: str, config: dict) -> str:
    """Get a credential from environment variable or config file."""
    return os.environ.get(env_var, "") or config.get(key, "")


from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ============================================================================
# Seatsurfing API Client
# ============================================================================

class SeatsurfingClient:
    """Client for the Seatsurfing REST API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.token_expires_at: float = 0

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
        authenticated: bool = True,
    ) -> httpx.Response:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        if authenticated and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                json=json_data,
                headers=headers,
                timeout=30.0,
            )
            return response

    async def login(self, email: str, password: str, organization_id: str) -> None:
        """Login and store tokens."""
        response = await self._request(
            "POST",
            "/auth/login",
            {"email": email, "password": password, "organizationId": organization_id},
            authenticated=False,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Login failed with status {response.status_code}: {response.text}")
        data = response.json()

        self.access_token = data["accessToken"]
        self.refresh_token = data["refreshToken"]
        # Token valid for 15 minutes
        self.token_expires_at = datetime.now().timestamp() + 14 * 60

    async def ensure_authenticated(self) -> None:
        """Ensure we have a valid token, refreshing if needed."""
        if not self.access_token:
            raise RuntimeError("Not authenticated - please login first")

        # Refresh if expiring in next minute
        if datetime.now().timestamp() > self.token_expires_at - 60:
            await self._refresh_token()

    async def _refresh_token(self) -> None:
        """Refresh the access token."""
        if not self.refresh_token:
            raise RuntimeError("No refresh token available")

        response = await self._request(
            "POST",
            "/auth/refresh",
            {"refreshToken": self.refresh_token},
            authenticated=False,
        )

        if response.status_code != 200:
            self.access_token = None
            self.refresh_token = None
            raise RuntimeError("Token refresh failed - please login again")

        data = response.json()
        self.access_token = data["accessToken"]
        self.refresh_token = data["refreshToken"]
        self.token_expires_at = datetime.now().timestamp() + 14 * 60

    def is_authenticated(self) -> bool:
        """Check if we have valid credentials."""
        return self.access_token is not None

    async def get_me(self) -> dict:
        """Get current user info."""
        await self.ensure_authenticated()
        response = await self._request("GET", "/user/me")
        response.raise_for_status()
        return response.json()

    async def get_locations(self) -> list[dict]:
        """Get all locations."""
        await self.ensure_authenticated()
        response = await self._request("GET", "/location/")
        response.raise_for_status()
        return response.json()

    async def get_spaces(self, location_id: str) -> list[dict]:
        """Get all spaces in a location."""
        await self.ensure_authenticated()
        response = await self._request("GET", f"/location/{location_id}/space/")
        response.raise_for_status()
        return response.json()

    async def get_space_availability(
        self, location_id: str, enter: str, leave: str
    ) -> list[dict]:
        """Get space availability for a time period."""
        await self.ensure_authenticated()
        params = urlencode({"enter": enter, "leave": leave})
        response = await self._request(
            "GET",
            f"/location/{location_id}/space/availability?{params}",
        )
        response.raise_for_status()
        return response.json()

    async def get_my_bookings(self) -> list[dict]:
        """Get current user's bookings."""
        await self.ensure_authenticated()
        response = await self._request("GET", "/booking/")
        response.raise_for_status()
        return response.json()

    async def create_booking(self, space_id: str, enter: str, leave: str, subject: str = "") -> str:
        """Create a new booking. Returns booking ID."""
        await self.ensure_authenticated()
        response = await self._request(
            "POST",
            "/booking/",
            {"spaceId": space_id, "enter": enter, "leave": leave, "subject": subject, "userEmail": ""},
        )
        if response.status_code != 201:
            raise RuntimeError(f"Booking failed with status {response.status_code}: {response.text}")
        return response.headers.get("X-Object-ID", "created")

    async def delete_booking(self, booking_id: str) -> None:
        """Delete a booking."""
        await self.ensure_authenticated()
        response = await self._request("DELETE", f"/booking/{booking_id}")
        response.raise_for_status()


# ============================================================================
# Helper Functions
# ============================================================================

def format_datetime(iso_string: str) -> str:
    """Format ISO datetime for display."""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_string


def parse_datetime(input_str: str) -> str:
    """Parse various datetime formats to ISO format."""
    # If already ISO format, return as-is
    if "T" in input_str and len(input_str) >= 16:
        return input_str

    # Try common formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(input_str, fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except ValueError:
            continue

    # Last resort: let Python try to parse it
    try:
        dt = datetime.fromisoformat(input_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except Exception:
        raise ValueError(f"Could not parse datetime: {input_str}")


# ============================================================================
# Cache Functions
# ============================================================================

async def refresh_spaces_cache(c: "SeatsurfingClient") -> dict:
    """Fetch all locations and spaces, save to cache, and return the data."""
    locations = await c.get_locations()

    spaces_by_location = {}
    for loc in locations:
        spaces = await c.get_spaces(loc["id"])
        spaces_by_location[loc["id"]] = [
            {
                "id": s["id"],
                "name": s["name"],
                "x": s.get("x", 0),
                "y": s.get("y", 0),
                "width": s.get("width", 0),
                "height": s.get("height", 0),
                "rotation": s.get("rotation", 0),
            }
            for s in spaces
        ]

    cache_data = {
        "updated_at": datetime.now().isoformat(),
        "locations": [{"id": loc["id"], "name": loc["name"]} for loc in locations],
        "spaces": spaces_by_location,
    }

    save_spaces_cache(cache_data)
    return cache_data


def render_spaces_list(spaces: list[dict], availability: dict[str, bool]) -> str:
    """Render a simple list of spaces with availability status."""
    if not spaces:
        return "No spaces found."

    # Sort alphabetically by name
    sorted_spaces = sorted(spaces, key=lambda s: s["name"].lower())

    available = []
    occupied = []

    for space in sorted_spaces:
        is_available = availability.get(space["id"], True)
        if is_available:
            available.append(space["name"])
        else:
            occupied.append(space["name"])

    lines = []

    lines.append(f"AVAILABLE ({len(available)}):")
    for name in available:
        lines.append(f"\t- {name}")

    lines.append("")
    lines.append(f"OCCUPIED ({len(occupied)}):")
    for name in occupied:
        lines.append(f"\t- {name}")

    return "\n".join(lines)


# ============================================================================
# MCP Server
# ============================================================================

# Global client instance
client: SeatsurfingClient | None = None


def get_client() -> SeatsurfingClient:
    """Get the client instance, raising if not configured."""
    if client is None:
        raise RuntimeError(
            "Seatsurfing not configured. Set SEATSURFING_URL environment variable "
            "or use the seatsurfing_login tool."
        )
    return client


# Create MCP server
server = Server("seatsurfing-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="seatsurfing_login",
            description="Login to Seatsurfing with email and password. Required before using other tools (unless auto-login via environment variables is configured).",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Base URL of the Seatsurfing instance (e.g., https://seatsurfing.example.com). Only needed if SEATSURFING_URL env var is not set.",
                    },
                    "email": {
                        "type": "string",
                        "description": "User email address. Only needed if SEATSURFING_EMAIL env var is not set.",
                    },
                    "password": {
                        "type": "string",
                        "description": "User password. Only needed if SEATSURFING_PASSWORD env var is not set.",
                    },
                    "organization_id": {
                        "type": "string",
                        "description": "Organization ID. Only needed if SEATSURFING_ORG_ID env var is not set.",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="seatsurfing_list_locations",
            description="List all available locations (buildings/floors) where spaces can be booked.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="seatsurfing_list_spaces",
            description="List all spaces (desks/rooms) in a specific location.",
            inputSchema={
                "type": "object",
                "properties": {
                    "location_id": {
                        "type": "string",
                        "description": "ID of the location. Use seatsurfing_list_locations to get IDs.",
                    },
                },
                "required": ["location_id"],
            },
        ),
        Tool(
            name="seatsurfing_check_availability",
            description="Check which spaces are available in a location for a specific time period.",
            inputSchema={
                "type": "object",
                "properties": {
                    "location_id": {
                        "type": "string",
                        "description": "ID of the location to check.",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time (ISO format or YYYY-MM-DD HH:MM).",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time (ISO format or YYYY-MM-DD HH:MM).",
                    },
                },
                "required": ["location_id", "start_time", "end_time"],
            },
        ),
        Tool(
            name="seatsurfing_create_booking",
            description="Create a new booking for a space (desk/room) at a specific time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "space_id": {
                        "type": "string",
                        "description": "ID of the space to book. Use seatsurfing_check_availability to find available spaces.",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time of the booking (YYYY-MM-DD HH:MM).",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time of the booking (YYYY-MM-DD HH:MM).",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Optional subject/reason for the booking.",
                    },
                },
                "required": ["space_id", "start_time", "end_time"],
            },
        ),
        Tool(
            name="seatsurfing_list_my_bookings",
            description="List all upcoming bookings for the current user.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="seatsurfing_cancel_booking",
            description="Cancel an existing booking by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "ID of the booking to cancel. Use seatsurfing_list_my_bookings to find IDs.",
                    },
                },
                "required": ["booking_id"],
            },
        ),
        Tool(
            name="seatsurfing_refresh_spaces",
            description="Refresh the cached list of locations and bookable spaces. Run this after setup or when spaces have changed.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="seatsurfing_view_availability",
            description="List all spaces in a location grouped by availability status for a given time period.",
            inputSchema={
                "type": "object",
                "properties": {
                    "location_id": {
                        "type": "string",
                        "description": "ID of the location. Use seatsurfing_list_locations to get IDs.",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time to check availability (YYYY-MM-DD HH:MM).",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time to check availability (YYYY-MM-DD HH:MM).",
                    },
                },
                "required": ["location_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    global client

    try:
        if name == "seatsurfing_login":
            config = load_config()
            url = arguments.get("url") or get_credential("url", "SEATSURFING_URL", config)
            email = arguments.get("email") or get_credential("email", "SEATSURFING_EMAIL", config)
            password = arguments.get("password") or get_credential("password", "SEATSURFING_PASSWORD", config)
            organization_id = arguments.get("organization_id") or get_credential("organization_id", "SEATSURFING_ORG_ID", config)

            if not url:
                return [TextContent(
                    type="text",
                    text="Error: Seatsurfing URL is required. Run /seatsurfing:setup to configure.",
                )]
            if not email or not password:
                return [TextContent(
                    type="text",
                    text="Error: Email and password are required. Run /seatsurfing:setup to configure.",
                )]
            if not organization_id:
                return [TextContent(
                    type="text",
                    text="Error: Organization ID is required. Run /seatsurfing:setup to configure.",
                )]

            client = SeatsurfingClient(url)
            await client.login(email, password, organization_id)
            user = await client.get_me()

            return [TextContent(
                type="text",
                text=f"Successfully logged in as {user.get('email', 'unknown')}",
            )]

        elif name == "seatsurfing_list_locations":
            c = get_client()
            locations = await c.get_locations()

            if not locations:
                return [TextContent(type="text", text="No locations found.")]

            lines = [f"Found {len(locations)} location(s):\n"]
            for loc in locations:
                desc = f"\n\t{loc.get('description')}" if loc.get("description") else ""
                lines.append(f"- {loc['name']} (ID: {loc['id']}){desc}")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "seatsurfing_list_spaces":
            c = get_client()
            location_id = arguments["location_id"]
            spaces = await c.get_spaces(location_id)

            if not spaces:
                return [TextContent(type="text", text="No spaces found in this location.")]

            lines = [f"Found {len(spaces)} space(s):\n"]
            for space in spaces:
                lines.append(f"- {space['name']} (ID: {space['id']})")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "seatsurfing_check_availability":
            c = get_client()
            location_id = arguments["location_id"]
            start_time = parse_datetime(arguments["start_time"])
            end_time = parse_datetime(arguments["end_time"])

            spaces = await c.get_space_availability(location_id, start_time, end_time)

            available = [s for s in spaces if s.get("available")]
            occupied = [s for s in spaces if not s.get("available")]

            lines = [f"Availability for {format_datetime(start_time)} to {format_datetime(end_time)}:\n"]

            if available:
                lines.append(f"Available ({len(available)}):")
                for s in available:
                    lines.append(f"\t- {s['name']} (ID: {s['id']})")
                lines.append("")

            if occupied:
                lines.append(f"Occupied ({len(occupied)}):")
                for s in occupied:
                    lines.append(f"\t- {s['name']}")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "seatsurfing_create_booking":
            c = get_client()
            space_id = arguments["space_id"]
            start_time = parse_datetime(arguments["start_time"])
            end_time = parse_datetime(arguments["end_time"])
            subject = arguments.get("subject", "")

            booking_id = await c.create_booking(space_id, start_time, end_time, subject)

            return [TextContent(
                type="text",
                text=f"Booking created successfully!\n\nBooking ID: {booking_id}\nTime: {format_datetime(start_time)} to {format_datetime(end_time)}",
            )]

        elif name == "seatsurfing_list_my_bookings":
            c = get_client()
            bookings = await c.get_my_bookings()

            if not bookings:
                return [TextContent(type="text", text="You have no upcoming bookings.")]

            lines = [f"Your upcoming bookings ({len(bookings)}):\n"]
            for b in bookings:
                space_name = b.get("space", {}).get("name", b.get("spaceId", "Unknown"))
                lines.append(
                    f"- {space_name}\n"
                    f"\tID: {b['id']}\n"
                    f"\tTime: {format_datetime(b['enter'])} -> {format_datetime(b['leave'])}"
                )

            return [TextContent(type="text", text="\n\n".join(lines))]

        elif name == "seatsurfing_cancel_booking":
            c = get_client()
            booking_id = arguments["booking_id"]
            await c.delete_booking(booking_id)

            return [TextContent(
                type="text",
                text=f"Booking {booking_id} has been cancelled.",
            )]

        elif name == "seatsurfing_refresh_spaces":
            c = get_client()
            cache_data = await refresh_spaces_cache(c)

            total_spaces = sum(len(spaces) for spaces in cache_data["spaces"].values())
            lines = [f"Refreshed cache with {len(cache_data['locations'])} location(s) and {total_spaces} space(s):\n"]

            for loc in cache_data["locations"]:
                loc_spaces = cache_data["spaces"].get(loc["id"], [])
                lines.append(f"- {loc['name']}: {len(loc_spaces)} space(s)")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "seatsurfing_view_availability":
            c = get_client()
            location_id = arguments["location_id"]

            # Load spaces from cache
            cache_data = load_spaces_cache()
            if not cache_data or "spaces" not in cache_data:
                return [TextContent(
                    type="text",
                    text="No spaces cache found. Run seatsurfing_refresh_spaces first.",
                )]

            spaces = cache_data["spaces"].get(location_id, [])
            if not spaces:
                return [TextContent(
                    type="text",
                    text=f"No spaces found for location {location_id}. Check location_id or refresh cache.",
                )]

            # Check availability if times provided
            availability = {}
            time_info = ""
            if arguments.get("start_time") and arguments.get("end_time"):
                start_time = parse_datetime(arguments["start_time"])
                end_time = parse_datetime(arguments["end_time"])
                avail_data = await c.get_space_availability(location_id, start_time, end_time)
                availability = {s["id"]: s.get("available", False) for s in avail_data}
                time_info = f"Time: {format_datetime(start_time)} to {format_datetime(end_time)}\n"
            else:
                # No times: show all as unknown (mark as available for display)
                availability = {s["id"]: True for s in spaces}
                time_info = "(availability not checked - provide start_time and end_time)\n"

            # Get location name
            location_name = location_id
            for loc in cache_data.get("locations", []):
                if loc["id"] == location_id:
                    location_name = loc["name"]
                    break

            # Render list
            spaces_list = render_spaces_list(spaces, availability)

            header = (
                f"Location: {location_name}\n"
                f"{time_info}"
            )

            return [TextContent(type="text", text=header + "\n" + spaces_list)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def run_server():
    """Run the MCP server."""
    global client

    # Load config from file or environment variables
    config = load_config()
    url = get_credential("url", "SEATSURFING_URL", config)
    email = get_credential("email", "SEATSURFING_EMAIL", config)
    password = get_credential("password", "SEATSURFING_PASSWORD", config)
    organization_id = get_credential("organization_id", "SEATSURFING_ORG_ID", config)

    if url and email and password and organization_id:
        client = SeatsurfingClient(url)
        try:
            await client.login(email, password, organization_id)
        except Exception as e:
            print(f"Auto-login failed: {e}", file=sys.stderr)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
