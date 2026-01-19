---
description: Configure Seatsurfing credentials
---

# Setup Command

Help the user configure their Seatsurfing credentials.

## Steps

1. **Check if config exists and is valid**
   - Read `~/.seatsurfing/config.json`
   - Check if it contains valid values for: url, email, password, organization_id
   - If all fields have non-placeholder values, skip to step 4 (verification)

2. **If config is missing or incomplete, create template and open it**
   - Create `~/.seatsurfing/` directory if needed
   - Write this template to `~/.seatsurfing/config.json`:
   ```json
   {
   	"url": "https://seatsurfing.example.com",
   	"email": "your-email@example.com",
   	"password": "your-password",
   	"organization_id": "your-org-id-from-browser-dev-tools"
   }
   ```
   - Open the file in the user's editor using Bash:
     - Windows: `start "" "%USERPROFILE%\.seatsurfing\config.json"`
     - macOS/Linux: `open ~/.seatsurfing/config.json` or `xdg-open ~/.seatsurfing/config.json`
   - Tell the user to edit the file with their real credentials and save it
   - Tell them the organization_id can be found in browser dev tools (Network tab) when using Seatsurfing

3. **Wait for user confirmation**
   - Ask the user to confirm when they have saved the file (use AskUserQuestion with options like "Done editing" / "Need help finding org ID")

4. **Verify credentials**
   - Call seatsurfing_login to verify the credentials work
   - If login fails, tell the user to check their config file and try again
   - Call seatsurfing_refresh_spaces to pre-fetch all locations and spaces
   - Confirm success to the user

The spaces cache at ~/.seatsurfing/spaces.json enables faster booking by avoiding repeated API calls.
