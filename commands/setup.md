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

After saving, confirm to the user that their credentials are saved and they can now use the booking commands.
