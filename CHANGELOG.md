# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2025-07-10

### BREAKING CHANGES
- Changed integration domain from `rucaptcha` to `captcha_balance`
- Renamed directory from `custom_components/rucaptcha/` to `custom_components/captcha_balance/`
- Updated GitHub repository URLs
- Existing installations require migration (remove old, install new)

## [1.1.0] - 2025-07-10

### Added
- Support for both RuCaptcha and 2Captcha services
- Service selection during setup
- Dynamic sensor naming based on selected service
- Options flow for reconfiguration
- Retry logic with exponential backoff
- Dynamic icons based on balance level
- Device registry support
- Enhanced error handling

## [1.0.0] - 2025-07-09

### Added
- Initial release of RuCaptcha Home Assistant integration
- Balance monitoring sensor with 1-minute update interval
- Configuration flow for easy setup
- Support for RuCaptcha API key authentication
- Error handling for API failures
- HACS compatibility