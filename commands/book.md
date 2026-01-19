---
description: Quick book a space in Seatsurfing
---

# Book Command

Help the user book a space in Seatsurfing.

If $ARGUMENTS contains a space name and time, parse it and create the booking directly.
Otherwise, ask the user what they want to book and when.

Examples of valid arguments:
- "GPU Laptop 1 tomorrow 9am-5pm"
- "Muovi today 14:00-16:00"
- "desk 1.1 next monday 8:00-17:00"

Steps:
1. If no arguments, ask what space and when
2. Read the spaces cache from ~/.seatsurfing/spaces.json
   - If cache is empty or missing, call seatsurfing_refresh_spaces first
3. Match the requested space name against cached spaces (fuzzy match OK)
4. Check availability using seatsurfing_check_availability
5. Create the booking using seatsurfing_create_booking
6. Confirm the booking to the user

The cache contains space IDs and names, avoiding API calls to list_locations and list_spaces each time.
