---
description: Configure Seatsurfing credentials
---

# Setup Command

Help the user configure their Seatsurfing credentials.

## Steps

1. **Check if config exists and is valid**
   - Do not print `~/.seatsurfing/config.json`: it holds a password or token. Check only which keys have a value, for example with a short script that prints each key and whether it is set
   - It is complete with: url, email, and either api_token or both password and organization_id
   - If all fields have non-placeholder values, skip to step 4 (verification)

2. **If config is missing or incomplete, create template and open it**
   - Create `~/.seatsurfing/` directory if needed
   - Ask how the user signs in to Seatsurfing (use AskUserQuestion: "Email and password" / "SSO button")
   - Email and password: write this template to `~/.seatsurfing/config.json`:
   ```json
   {
   	"url": "https://seatsurfing.example.com",
   	"email": "your-email@example.com",
   	"password": "your-password",
   	"organization_id": "your-org-id-from-browser-dev-tools"
   }
   ```
   - SSO button: Seatsurfing refuses password login for SSO accounts, so write this template instead:
   ```json
   {
   	"url": "https://seatsurfing.example.com",
   	"email": "your-email@example.com",
   	"api_token": "token-of-a-service-account"
   }
   ```
     Tell the user the token comes from a Seatsurfing admin: a service account (read/write) with bookings admin rights, then "Generate token" on that account. Bookings are made for the email in the file. The token can book and cancel for anyone, so it must stay private.
   - Restrict the file to the user on macOS/Linux: `chmod 600 ~/.seatsurfing/config.json`
   - Open the file in the user's editor using Bash:
     - Windows: `start "" "%USERPROFILE%\.seatsurfing\config.json"`
     - macOS/Linux: `open ~/.seatsurfing/config.json` or `xdg-open ~/.seatsurfing/config.json`
   - Tell the user to edit the file with their real credentials and save it. Never ask for the password or token in chat
   - Password setup only: the organization_id is the `organization.id` in the JSON at `<url>/auth/org/<hostname of the url>`

3. **Wait for user confirmation**
   - Ask the user to confirm when they have saved the file (use AskUserQuestion with options like "Done editing" / "Need help finding org ID")

4. **Verify credentials**
   - Call seatsurfing_login to verify the credentials work
   - If login fails, tell the user to check their config file and try again
   - Call seatsurfing_refresh_spaces to pre-fetch all locations and spaces
   - Confirm success to the user

The spaces cache at ~/.seatsurfing/spaces.json enables faster booking by avoiding repeated API calls.
