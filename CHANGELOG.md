# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.16] - 2025-07-28

### Added
- **Secure Variables** - Enterprise-grade AES-256 encrypted storage for sensitive data (API keys, tokens, passwords)
  - Session-based authentication with configurable TTL
  - System keychain integration for password storage
  - Complete audit logging for compliance
  - Write-only storage model for maximum security
- **Log Sanitization** - Intelligent filtering of repetitive patterns from verbose logs
  - Fuzzy pattern matching with configurable thresholds
  - Automatic summarization of repetitive blocks
  - Sensitive data detection and warnings
  - Support for clipboard, files, and piped input
- **Enhanced CLI** - Extended pmcli with full CRUD operations
  - `pmcli list` - List all prompts
  - `pmcli copy <id>` - Copy prompt to clipboard
  - `pmcli show <id>` - Show prompt details
  - `pmcli delete <id>` - Delete prompt
  - `pmcli add` - Add new prompt
  - `pmcli var` - Manage variables
  - `pmcli svar` - Manage secure variables
  - `pmcli sanitize` - Clean repetitive logs

### Enhanced
- **Documentation** - Complete documentation for all new features
  - SECURE_VARIABLES.md - User guide for secure variables
  - LOG_SANITIZATION.md - Guide for log sanitization
  - docs/SECURITY_ARCHITECTURE.md - Technical security implementation
- **Browser Extension** - Added log sanitization integration
  - Right-click menu option to sanitize selected text
  - Automatic detection of verbose log content
  - One-click cleaning before prompt insertion

### Fixed
- pmcli now properly supports both Task-Master commands and basic CRUD operations
- Variable resolution now seamlessly integrates secure variables with regular variables

## [0.0.15] - 2025-07-20

### Added
- Multi-project support for Task-Master integration
- Browser extension with cross-platform support
- Project registry for managing multiple projects
- Context-aware prompt suggestions

## [0.0.14] - 2025-07-15

### Added
- Task-Master integration with automatic context extraction
- One-command project context copying with pmcli
- PRD location and requirements auto-filling

## [0.0.10] - 2025-07-01

### Added
- Initial release with core prompt management functionality
- Template system with variables
- Category and tag organization
- Usage analytics and tracking
- Basic CLI interface

## [0.0.1] - 2025-06-15

### Added
- Project inception
- Basic prompt storage and retrieval
- Simple variable substitution

[0.0.16]: https://github.com/your-username/promptManager/compare/v0.0.15...v0.0.16
[0.0.15]: https://github.com/your-username/promptManager/compare/v0.0.14...v0.0.15
[0.0.14]: https://github.com/your-username/promptManager/compare/v0.0.10...v0.0.14
[0.0.10]: https://github.com/your-username/promptManager/compare/v0.0.1...v0.0.10
[0.0.1]: https://github.com/your-username/promptManager/releases/tag/v0.0.1