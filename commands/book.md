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
2. Search for the space using seatsurfing_list_spaces
3. Check availability using seatsurfing_check_availability
4. Create the booking using seatsurfing_create_booking
5. Confirm the booking to the user
