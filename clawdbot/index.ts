import type { ClawdbotPluginApi } from "clawdbot/plugin-sdk";
import { Type } from "@sinclair/typebox";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

// Config and cache paths
const CONFIG_PATH = join(homedir(), ".seatsurfing", "config.json");
const CACHE_PATH = join(homedir(), ".seatsurfing", "spaces.json");

// Session state
let accessToken: string | null = null;
let refreshToken: string | null = null;
let tokenExpiresAt = 0;
let baseUrl = "";

// Load config from file
function loadConfig(): Record<string, string> {
  try {
    if (existsSync(CONFIG_PATH)) {
      return JSON.parse(readFileSync(CONFIG_PATH, "utf-8"));
    }
  } catch {}
  return {};
}

// Load spaces cache
function loadSpacesCache(): Record<string, unknown> {
  try {
    if (existsSync(CACHE_PATH)) {
      return JSON.parse(readFileSync(CACHE_PATH, "utf-8"));
    }
  } catch {}
  return {};
}

// Save spaces cache
function saveSpacesCache(data: Record<string, unknown>): void {
  const dir = join(homedir(), ".seatsurfing");
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  writeFileSync(CACHE_PATH, JSON.stringify(data));
}

// Get credential from env or config
function getCredential(key: string, envVar: string): string {
  const config = loadConfig();
  return process.env[envVar] || config[key] || "";
}

// API request helper
async function apiRequest(
  method: string,
  endpoint: string,
  body?: Record<string, unknown>,
  authenticated = true
): Promise<Response> {
  const url = `${baseUrl}${endpoint}`;
  const headers: Record<string, string> = { "Content-Type": "application/json" };

  if (authenticated && accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const res = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(30000),
  });

  return res;
}

// Login to Seatsurfing
async function login(
  url: string,
  email: string,
  password: string,
  organizationId: string
): Promise<void> {
  baseUrl = url.replace(/\/$/, "");

  const res = await apiRequest(
    "POST",
    "/auth/login",
    { email, password, organizationId },
    false
  );

  if (!res.ok) {
    throw new Error(`Login failed: ${res.status} ${await res.text()}`);
  }

  const data = await res.json();
  accessToken = data.accessToken;
  refreshToken = data.refreshToken;
  tokenExpiresAt = Date.now() + 14 * 60 * 1000;
}

// Refresh token if needed
async function ensureAuthenticated(): Promise<void> {
  if (!accessToken) {
    throw new Error("Not authenticated - please login first");
  }

  if (Date.now() > tokenExpiresAt - 60000 && refreshToken) {
    const res = await apiRequest(
      "POST",
      "/auth/refresh",
      { refreshToken },
      false
    );

    if (!res.ok) {
      accessToken = null;
      refreshToken = null;
      throw new Error("Token refresh failed - please login again");
    }

    const data = await res.json();
    accessToken = data.accessToken;
    refreshToken = data.refreshToken;
    tokenExpiresAt = Date.now() + 14 * 60 * 1000;
  }
}

// Parse datetime to ISO format
function parseDateTime(input: string): string {
  if (input.includes("T") && input.length >= 16) return input;

  const formats = [
    /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})(?::(\d{2}))?$/,
    /^(\d{4})\/(\d{2})\/(\d{2}) (\d{2}):(\d{2})(?::(\d{2}))?$/,
  ];

  for (const fmt of formats) {
    const match = input.match(fmt);
    if (match) {
      const [, y, m, d, h, min, sec = "00"] = match;
      return `${y}-${m}-${d}T${h}:${min}:${sec}.000Z`;
    }
  }

  return input;
}

// Format datetime for display
function formatDateTime(iso: string): string {
  try {
    const dt = new Date(iso);
    return dt.toISOString().slice(0, 16).replace("T", " ");
  } catch {
    return iso;
  }
}

// Tools

function createLoginTool() {
  return {
    name: "seatsurfing_login",
    description:
      "Login to Seatsurfing. Required before other tools (unless auto-configured via ~/.seatsurfing/config.json or env vars).",
    parameters: Type.Object({
      url: Type.Optional(Type.String({ description: "Seatsurfing instance URL" })),
      email: Type.Optional(Type.String({ description: "Your email" })),
      password: Type.Optional(Type.String({ description: "Your password" })),
      organization_id: Type.Optional(Type.String({ description: "Organization ID" })),
    }),
    async execute(_id: string, params: Record<string, unknown>) {
      const url = String(params.url || getCredential("url", "SEATSURFING_URL"));
      const email = String(params.email || getCredential("email", "SEATSURFING_EMAIL"));
      const password = String(params.password || getCredential("password", "SEATSURFING_PASSWORD"));
      const orgId = String(params.organization_id || getCredential("organization_id", "SEATSURFING_ORG_ID"));

      if (!url) throw new Error("Seatsurfing URL is required");
      if (!email || !password) throw new Error("Email and password are required");
      if (!orgId) throw new Error("Organization ID is required");

      await login(url, email, password, orgId);

      await ensureAuthenticated();
      const res = await apiRequest("GET", "/user/me");
      const user = await res.json();

      return { content: [{ type: "text", text: `Logged in: ${user.email || "unknown"}` }] };
    },
  };
}

function createListLocationsTool() {
  return {
    name: "seatsurfing_list_locations",
    description: "List all locations (buildings/floors) where spaces can be booked.",
    parameters: Type.Object({}),
    async execute() {
      await ensureAuthenticated();
      const res = await apiRequest("GET", "/location/");
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const locations = await res.json();

      if (!locations.length) {
        return { content: [{ type: "text", text: "No locations found." }] };
      }

      const lines = locations.map((loc: { name: string; id: string }) => `${loc.name}\t${loc.id}`);
      return { content: [{ type: "text", text: lines.join("\n") }] };
    },
  };
}

function createListSpacesTool() {
  return {
    name: "seatsurfing_list_spaces",
    description: "List all spaces (desks/rooms) in a location.",
    parameters: Type.Object({
      location_id: Type.String({ description: "Location ID" }),
    }),
    async execute(_id: string, params: Record<string, unknown>) {
      const locationId = String(params.location_id);
      await ensureAuthenticated();
      const res = await apiRequest("GET", `/location/${locationId}/space/`);
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const spaces = await res.json();

      if (!spaces.length) {
        return { content: [{ type: "text", text: "No spaces found." }] };
      }

      const lines = spaces.map((s: { name: string; id: string }) => `${s.name}\t${s.id}`);
      return { content: [{ type: "text", text: lines.join("\n") }] };
    },
  };
}

function createCheckAvailabilityTool() {
  return {
    name: "seatsurfing_check_availability",
    description: "Check which spaces are available in a location for a time period.",
    parameters: Type.Object({
      location_id: Type.String({ description: "Location ID" }),
      start_time: Type.String({ description: "Start time (YYYY-MM-DD HH:MM)" }),
      end_time: Type.String({ description: "End time (YYYY-MM-DD HH:MM)" }),
    }),
    async execute(_id: string, params: Record<string, unknown>) {
      const locationId = String(params.location_id);
      const start = parseDateTime(String(params.start_time));
      const end = parseDateTime(String(params.end_time));

      await ensureAuthenticated();
      const res = await apiRequest(
        "GET",
        `/location/${locationId}/space/availability?enter=${encodeURIComponent(start)}&leave=${encodeURIComponent(end)}`
      );
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const spaces = await res.json();

      const available = spaces.filter((s: { available: boolean }) => s.available);
      const occupied = spaces.filter((s: { available: boolean }) => !s.available);

      const lines = [`AVAILABLE (${available.length}):`];
      for (const s of available) lines.push(`\t${s.name}\t${s.id}`);
      lines.push(`OCCUPIED (${occupied.length}):`);
      for (const s of occupied) lines.push(`\t${s.name}`);

      return { content: [{ type: "text", text: lines.join("\n") }] };
    },
  };
}

function createBookingTool() {
  return {
    name: "seatsurfing_create_booking",
    description: "Create a new booking for a space.",
    parameters: Type.Object({
      space_id: Type.String({ description: "Space ID to book" }),
      start_time: Type.String({ description: "Start time (YYYY-MM-DD HH:MM)" }),
      end_time: Type.String({ description: "End time (YYYY-MM-DD HH:MM)" }),
      subject: Type.Optional(Type.String({ description: "Optional booking reason" })),
    }),
    async execute(_id: string, params: Record<string, unknown>) {
      const spaceId = String(params.space_id);
      const start = parseDateTime(String(params.start_time));
      const end = parseDateTime(String(params.end_time));
      const subject = String(params.subject || "");

      await ensureAuthenticated();
      const res = await apiRequest("POST", "/booking/", {
        spaceId,
        enter: start,
        leave: end,
        subject,
        userEmail: "",
      });

      if (res.status !== 201) {
        const text = await res.text();
        throw new Error(`Booking failed: ${res.status} ${text}`);
      }

      const bookingId = res.headers.get("X-Object-ID") || "created";
      return { content: [{ type: "text", text: `Booked: ${bookingId}` }] };
    },
  };
}

function createListMyBookingsTool() {
  return {
    name: "seatsurfing_list_my_bookings",
    description: "List your upcoming bookings.",
    parameters: Type.Object({}),
    async execute() {
      await ensureAuthenticated();
      const res = await apiRequest("GET", "/booking/");
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const bookings = await res.json();

      if (!bookings.length) {
        return { content: [{ type: "text", text: "No upcoming bookings." }] };
      }

      const lines = bookings.map((b: { space?: { name: string }; spaceId?: string; enter: string; leave: string; id: string }) => {
        const spaceName = b.space?.name || b.spaceId || "?";
        return `${spaceName}\t${formatDateTime(b.enter)}-${formatDateTime(b.leave)}\t${b.id}`;
      });

      return { content: [{ type: "text", text: lines.join("\n") }] };
    },
  };
}

function createCancelBookingTool() {
  return {
    name: "seatsurfing_cancel_booking",
    description: "Cancel an existing booking by ID.",
    parameters: Type.Object({
      booking_id: Type.String({ description: "Booking ID to cancel" }),
    }),
    async execute(_id: string, params: Record<string, unknown>) {
      const bookingId = String(params.booking_id);
      await ensureAuthenticated();
      const res = await apiRequest("DELETE", `/booking/${bookingId}`);
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      return { content: [{ type: "text", text: `Cancelled: ${bookingId}` }] };
    },
  };
}

function createRefreshSpacesTool() {
  return {
    name: "seatsurfing_refresh_spaces",
    description: "Refresh the cached list of locations and spaces.",
    parameters: Type.Object({}),
    async execute() {
      await ensureAuthenticated();

      const locRes = await apiRequest("GET", "/location/");
      if (!locRes.ok) throw new Error(`Failed: ${locRes.status}`);
      const locations = await locRes.json();

      const spacesByLocation: Record<string, { id: string; name: string }[]> = {};
      for (const loc of locations) {
        const spaceRes = await apiRequest("GET", `/location/${loc.id}/space/`);
        if (spaceRes.ok) {
          const spaces = await spaceRes.json();
          spacesByLocation[loc.id] = spaces.map((s: { id: string; name: string }) => ({
            id: s.id,
            name: s.name,
          }));
        }
      }

      const cacheData = {
        updated_at: new Date().toISOString(),
        locations: locations.map((loc: { id: string; name: string }) => ({
          id: loc.id,
          name: loc.name,
        })),
        spaces: spacesByLocation,
      };

      saveSpacesCache(cacheData);

      const totalSpaces = Object.values(spacesByLocation).reduce((sum, arr) => sum + arr.length, 0);
      return {
        content: [{ type: "text", text: `Cache: ${locations.length} locations, ${totalSpaces} spaces` }],
      };
    },
  };
}

// Auto-login on load if credentials available
async function tryAutoLogin(): Promise<void> {
  const url = getCredential("url", "SEATSURFING_URL");
  const email = getCredential("email", "SEATSURFING_EMAIL");
  const password = getCredential("password", "SEATSURFING_PASSWORD");
  const orgId = getCredential("organization_id", "SEATSURFING_ORG_ID");

  if (url && email && password && orgId) {
    try {
      await login(url, email, password, orgId);
    } catch {
      // Silently fail - user can login manually
    }
  }
}

export default function register(api: ClawdbotPluginApi) {
  // Try auto-login in background
  tryAutoLogin();

  // Register all tools
  api.registerTool(createLoginTool());
  api.registerTool(createListLocationsTool());
  api.registerTool(createListSpacesTool());
  api.registerTool(createCheckAvailabilityTool());
  api.registerTool(createBookingTool());
  api.registerTool(createListMyBookingsTool());
  api.registerTool(createCancelBookingTool());
  api.registerTool(createRefreshSpacesTool());
}
