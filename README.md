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
| `SEATSURFING_PASSWORD` | Yes | Your password |
| `SEATSURFING_ORG_ID` | Yes | Your organization UUID |

### Finding Your Organization ID

1. Open your Seatsurfing web app
2. Open browser Developer Tools (F12)
3. Go to the Network tab
4. Login and look at the POST request to `/auth/login`
5. The `organizationId` is in the request payload

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

## Requirements

- Python 3.10+
- A Seatsurfing instance with API access
- Claude Code or Claude Desktop

## License

MIT
