---
description: Configure Seatsurfing credentials
---

# Setup Command

Help the user configure their Seatsurfing credentials.

Use AskUserQuestion to collect:
1. Seatsurfing URL (e.g., https://seatsurfing.example.com)
2. Email address
3. Password
4. Organization ID (found in browser dev tools or admin settings)

Then write these to a config file at ~/.seatsurfing/config.json using the Write tool:

```json
{
  "url": "...",
  "email": "...",
  "password": "...",
  "organization_id": "..."
}
```

Create the ~/.seatsurfing directory if it doesn't exist.

After saving:
1. Call seatsurfing_login to verify the credentials work
2. Call seatsurfing_refresh_spaces to pre-fetch all locations and spaces
3. Confirm to the user that their credentials are saved and spaces cache is populated

The spaces cache at ~/.seatsurfing/spaces.json enables faster booking by avoiding repeated API calls.
