---
description: Refresh the spaces cache
---

# Refresh Command

Refresh the local cache of bookable locations and spaces from Seatsurfing.

Steps:
1. Call seatsurfing_refresh_spaces to fetch all locations and their spaces
2. Report to the user how many locations and spaces were cached
3. Show the last updated timestamp

The cache is stored at ~/.seatsurfing/spaces.json and is used by the book command for faster lookups.

Use this command when:
- New spaces have been added to Seatsurfing
- Spaces have been renamed or removed
- The cache file is missing or corrupted
