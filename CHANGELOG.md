# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-05-29

### Added
- Initial release of high-concurrency subdomain scanner
- Async HTTP scanning with configurable concurrency limits (default: 80)
- SQLite-based intelligent caching system
- Full redirect chain tracking and analysis
- Content snippet capture from successful responses
- CSV export functionality with human-readable redirect chains
- Rich terminal UI with progress bars and summary tables
- Comprehensive error logging and classification
- CLI interface with multiple export options
- Resume capability for interrupted large scans
- Support for both HTTPS and HTTP fallback
- Detailed scan metrics and performance tracking

### Features
- **High Performance**: Scan 1000+ domains in 10-15 seconds
- **Smart Caching**: Automatically skip domains with valid responses (200/3xx)
- **Redirect Analysis**: Track complete redirect chains with headers
- **Content Analysis**: Capture HTML snippets for soft 404 detection
- **Export Options**: Multiple CSV export formats for different use cases
- **Error Handling**: Comprehensive error classification and logging
- **Resume Support**: Skip already-scanned domains for large domain lists

### Technical Details
- Python 3.8+ support
- httpx for async HTTP requests
- rich for beautiful terminal output
- SQLite for persistent result storage
- Comprehensive test coverage
- Clean, documented codebase ready for contributions

### Use Cases
- Security research and bug bounty hunting
- Asset discovery and inventory management
- Subdomain monitoring and change detection
- Infrastructure analysis and mapping
- Cleanup of inactive subdomains
