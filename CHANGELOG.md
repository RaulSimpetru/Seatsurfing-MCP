# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-01-19

### Changed

- Reduced token usage in MCP tool responses (concise output format)
- Reduced cache file size (removed unused spatial data, compact JSON)

## [1.1.0] - 2026-01-19

### Added

- Spaces cache (`~/.seatsurfing/spaces.json`) for faster booking lookups
- `seatsurfing_refresh_spaces` tool to update cached locations and spaces
- `seatsurfing_view_availability` tool to list spaces grouped by availability status
- `/seatsurfing:refresh` command to refresh spaces cache
- `/seatsurfing:availability` command to view availability for a time period

### Changed

- Setup command now automatically refreshes spaces cache after saving credentials
- Book command now uses cached space data instead of API calls

## [1.0.0] - 2025-01-19

### Added

- MCP server for Seatsurfing REST API integration
- Authentication with email, password, and organization ID
- Auto-login on startup when credentials are configured
- Config file support (`~/.seatsurfing/config.json`) for cross-platform credential storage
- Environment variable support (`SEATSURFING_URL`, `SEATSURFING_EMAIL`, `SEATSURFING_PASSWORD`, `SEATSURFING_ORG_ID`)

#### MCP Tools

- `seatsurfing_login` - Authenticate with Seatsurfing
- `seatsurfing_list_locations` - List all available locations
- `seatsurfing_list_spaces` - List spaces in a location
- `seatsurfing_check_availability` - Check space availability for a time period
- `seatsurfing_create_booking` - Create a new booking with optional subject
- `seatsurfing_list_my_bookings` - List user's upcoming bookings
- `seatsurfing_cancel_booking` - Cancel an existing booking

#### Claude Code Plugin

- `/seatsurfing:setup` - Interactive credential configuration
- `/seatsurfing:book` - Quick booking command
- `/seatsurfing:my-bookings` - List bookings command
- `/seatsurfing:cancel` - Cancel booking command

[Unreleased]: https://github.com/RaulSimpetru/Seatsurfing-MCP/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/RaulSimpetru/Seatsurfing-MCP/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/RaulSimpetru/Seatsurfing-MCP/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/RaulSimpetru/Seatsurfing-MCP/releases/tag/v1.0.0
