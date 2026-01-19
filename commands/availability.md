---
description: View space availability for a location
---

# Availability Command

Show all spaces in a location grouped by availability status.

If $ARGUMENTS contains a location name and time range, use those.
Otherwise, ask the user which location and time period to check.

Examples:
- "tomorrow 9am-5pm"
- "next monday afternoon"
- "today 2pm-4pm"

Steps:
1. Read spaces cache from ~/.seatsurfing/spaces.json
   - If cache is empty, call seatsurfing_refresh_spaces first
2. Parse location and time from arguments
3. Call seatsurfing_view_availability with location_id, start_time, end_time
4. Display the availability list

Output shows:
- AVAILABLE: spaces that can be booked
- OCCUPIED: spaces already booked
