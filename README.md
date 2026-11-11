# Seatsurfing MCP

A Claude Code plugin for booking desks and rooms in [Seatsurfing](https://seatsurfing.app/) - the open-source desk sharing and room booking solution for hybrid workplaces.

## Features

- List locations and spaces
- Check availability for specific time slots
- Create and cancel bookings
- View your upcoming bookings
- Auto-login with saved credentials

## Installation

### As a Claude Code Plugin (Recommended)

```bash
# Add the marketplace
/plugin marketplace add RaulSimpetru/Seatsurfing-MCP

# Install the plugin
/plugin install seatsurfing@seatsurfing-mcp-marketplace
```

### Using Claude Code CLI

```bash
claude mcp add seatsurfing \
	-e SEATSURFING_URL=https://seatsurfing.example.com \
	-e SEATSURFING_EMAIL=you@example.com \
	-e SEATSURFING_PASSWORD=yourpass \
	-e SEATSURFING_ORG_ID=your-org-uuid \
	-- uvx seatsurfing-mcp
```

### Using Claude Desktop

Add to your config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "seatsurfing": {
      "command": "uvx",
      "args": ["seatsurfing-mcp"],
      "env": {
        "SEATSURFING_URL": "https://seatsurfing.example.com",
        "SEATSURFING_EMAIL": "you@example.com",
        "SEATSURFING_PASSWORD": "yourpass",
        "SEATSURFING_ORG_ID": "your-org-uuid"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

## Configuration

### Option 1: Setup Command (Plugin only)

Run the setup command and follow the prompts:

```
/seatsurfing:setup
```

This saves your credentials to `~/.seatsurfing/config.json` and works across all platforms.

### Option 2: Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SEATSURFING_URL` | Yes | Base URL of your Seatsurfing instance |
| `SEATSURFING_EMAIL` | Yes | Your login email |
| `SEATSURFING_PASSWORD` | Password login | Your password |
| `SEATSURFING_ORG_ID` | Password login | Your organization UUID |
| `SEATSURFING_API_TOKEN` | SSO accounts | API token of a service account, used instead of password and organization |

The config file uses the keys `url`, `email`, `password`, `organization_id` and `api_token`.

### SSO accounts (API token)

Seatsurfing refuses password login for accounts that sign in through an SSO provider, and it has no SSO login for command-line tools. For those accounts use an API token:

1. A Seatsurfing admin creates a user of type "Service account (read/write)" and gives it a role with bookings admin rights.
2. On that account, "Generate token". The token is shown once.
3. Put the token in `api_token` (or `SEATSURFING_API_TOKEN`) together with `url` and your own `email`.

Bookings are created for your email, "my bookings" lists yours, and the plugin refuses to cancel a booking that is not yours. The token itself can book and cancel for anyone in the organization, so keep it private.

### Finding Your Organization ID

Only needed for password login. Open `<your Seatsurfing URL>/auth/org/<hostname of that URL>` in a browser; the `id` inside `organization` is your organization ID.

## Usage

### Slash Commands (Plugin)

| Command | Description |
|---------|-------------|
| `/seatsurfing:setup` | Configure your credentials |
| `/seatsurfing:book` | Book a space |
| `/seatsurfing:my-bookings` | List your upcoming bookings |
| `/seatsurfing:cancel` | Cancel a booking |

### MCP Tools

| Tool | Description |
|------|-------------|
| `seatsurfing_login` | Login to Seatsurfing |
| `seatsurfing_list_locations` | List all locations |
| `seatsurfing_list_spaces` | List spaces in a location |
| `seatsurfing_check_availability` | Check space availability |
| `seatsurfing_create_booking` | Create a new booking |
| `seatsurfing_list_my_bookings` | List your bookings |
| `seatsurfing_cancel_booking` | Cancel a booking |

### Examples

Just tell Claude what you need:

- "Book me a desk tomorrow from 9am to 5pm"
- "What's available next Monday afternoon?"
- "Show me my bookings"
- "Cancel my Friday booking"

## Installing from Source

```bash
# Clone the repository
git clone https://github.com/RaulSimpetru/Seatsurfing-MCP.git
cd Seatsurfing-MCP

# Install with uv
uv sync

# Or with pip
pip install -e .
```

## Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in dev mode
pip install -e ".[dev]"

# Run locally
seatsurfing-mcp
```

## Troubleshooting

### "Not authenticated" error
Make sure all four environment variables are set correctly, including `SEATSURFING_ORG_ID`.

### Can't connect to Seatsurfing
- Check that the URL is correct (no trailing `/ui/`)
- Make sure your server is reachable
- Try the URL in a browser first

### 400 Bad Request on login
You're probably missing the `SEATSURFING_ORG_ID`. See "Finding Your Organization ID" above.

## Using Clawdbot

Seatsurfing can also be used with [Clawdbot](https://clawd.bot) to book desks via Telegram, Signal, Discord, and other channels.

### Installation

```bash
# Copy the plugin to clawdbot extensions
cp -r clawdbot ~/.clawdbot/extensions/seatsurfing

# Install dependencies
cd ~/.clawdbot/extensions/seatsurfing && npm install

# Enable the plugin
clawdbot plugins enable seatsurfing

# Restart the gateway
clawdbot gateway restart
```

### Configuration

The plugin uses the same credentials as the MCP server from `~/.seatsurfing/config.json` or environment variables.

## Requirements

- Python 3.10+
- A Seatsurfing instance with API access
- Claude Code, Claude Desktop, or Clawdbot

## License

MIT
