---
description: Cancel a Seatsurfing booking
---

# Cancel Command

Help the user cancel a booking.

If $ARGUMENTS contains a booking ID, cancel it directly.
Otherwise:
1. List the user's bookings using seatsurfing_list_my_bookings
2. Ask which booking they want to cancel
3. Cancel it using seatsurfing_cancel_booking
4. Confirm the cancellation
