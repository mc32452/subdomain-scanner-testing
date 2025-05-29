# 🔍 High-Concurrency Subdomain Scanner

A high-performance Python tool for scanning thousands of subdomains with async HTTP requests, intelligent caching, and comprehensive result tracking.

## 🚀 Features

- **High Concurrency**: Scan up to 80+ domains simultaneously using async HTTP
- **Intelligent Caching**: SQLite-based results storage with automatic skip of already-scanned valid domains
- **Full Redirect Tracking**: Captures complete redirect chains for 3xx responses
- **Content Snippets**: Extracts HTML snippets from 200 responses for soft-404 detection
- **Comprehensive Error Analysis**: Detailed categorization of connection timeouts, DNS failures, etc.
- **Incremental Scanning**: Only rescans failed/invalid results, saving time
- **Rich Output**: Beautiful progress bars and summary tables with error breakdown
- **Export Options**: CSV exports for successful, redirecting, or all results

## ⚠️ Understanding Scan Results

**High failure rates (90-95%) are COMPLETELY NORMAL for subdomain enumeration!**

### What "Failed to Scan" Means:

- **Connection Timeout**: Domain took too long to respond (likely offline/doesn't exist)
- **Read Timeout**: Server accepted connection but didn't send response (slow/overloaded)
- **Connection Error**: Network unreachable or connection refused (offline/blocked)
- **DNS Resolution**: Domain doesn't exist or DNS issues
- **SSL/TLS Errors**: Certificate problems or HTTPS configuration issues

### Expected Results:
- **Success Rate**: 5-10% is considered excellent for subdomain discovery
- **Failure Rate**: 90-95% is normal - most random subdomains don't exist
- **Focus**: The successful domains are your valuable findings!

## 📦 Installation

```bash
# Clone or download the files
cd subdomain-scanner-testing

# Install dependencies
pip install -r requirements.txt
```

## 📁 File Management

### Important Files to Keep
- `subdomain_scanner.py` - Main scanner engine
- `scan.py` - Scanning script
- `cli.py` - Command line interface
- `export_results.py` - Database export utility
- `README.md` - This documentation

### Files NOT to Upload/Transfer
- `scan_results.db` - Database file (can be large, contains local scan data)
- `subdomain_scanner.log` - Log files
- `*.csv` - CSV export files (regenerate as needed)

**Note**: Use `export_results.py` to export your scan data to CSV before transferring to a new system.

## 🎯 Quick Start

### Analyze Your Current Results

If you've already run a scan and want to understand the results:

```bash
# Analyze your current scan results database
python check_results.py

# Get detailed error breakdown
python analyze_results.py
```

### Option 1: Command Line Interface

```bash
# Basic scan
python cli.py example_domains.txt

# Scan with custom concurrency  
python cli.py example_domains.txt --concurrent 60

# Rescan only failed domains
python cli.py example_domains.txt --rescan-failed

# Export successful domains to CSV
python cli.py example_domains.txt --export-200

# Full example with all options
python cli.py example_domains.txt --concurrent 80 --rescan-failed --export-all
```

### Export Database Results

Export your scan results to CSV at any time (without running a new scan):

```bash
# Export all results to CSV
python export_results.py

# This creates 'corrected_results.csv' with all your past scan data
# Perfect for transferring results between systems or backup
```

### Option 2: Optimized Configurations

```bash
# Use pre-tuned configurations for different scenarios
python optimized_scanner.py

# Available configs:
# - aggressive: Fast scanning, higher failure rate
# - balanced: Moderate speed, better success rate  
# - conservative: Slower but more reliable
# - stealth: Very slow, minimal detection risk
```

### Option 2: Direct Python Usage

```python
import asyncio
from subdomain_scanner import SubdomainScanner, load_domains_from_file

async def main():
    # Load your domain list
    domains = load_domains_from_file("your_domains.txt")
    
    # Create scanner
    scanner = SubdomainScanner(max_concurrent=80)
    
    # Run scan
    summary = await scanner.scan_domains(domains)
    scanner.print_summary(summary)
    
    # Export results
    scanner.export_results(status_codes=[200], output_file="live_domains.json")

asyncio.run(main())
```

## 📊 Database Schema

Results are stored in SQLite with this optimized schema:

```sql
CREATE TABLE results (
    domain TEXT PRIMARY KEY,
    status_code INTEGER,
    redirect_chain TEXT,           -- JSON array of redirect steps
    snippet TEXT,                  -- First 2KB of HTML content (200s only)
    error_message TEXT,            -- Error details for failed requests
    last_checked TIMESTAMP,        -- When this domain was last scanned
    scan_duration_ms INTEGER       -- How long the scan took
);
```

## 🔧 Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_concurrent` | 80 | Maximum simultaneous HTTP connections |
| `db_path` | `scan_results.db` | SQLite database file location |
| `timeout` | 15s | HTTP request timeout |
| `max_redirects` | 10 | Maximum redirect chain length |
| `snippet_size` | 2048 | Characters to capture from 200 responses |

## 📈 Performance Optimization

### Intelligent Caching Strategy
- ✅ **Skip**: Domains with status 200 or 3xx (already successful)
- 🔄 **Rescan**: Only domains with errors, timeouts, or 4xx/5xx responses
- 📊 **Track**: Scan duration and timestamps for performance analysis

### HTTP Optimizations
- Connection pooling with keep-alive
- Automatic HTTP fallback for HTTPS failures
- Custom User-Agent and headers
- Semaphore-based concurrency control

## 📊 Example Output

```
🔍 Subdomain Scan Summary
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric                              ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Total domains scanned               │   847 │
│ New 200 responses added             │   312 │
│ New 3xx responses with redirect     │    89 │
│ Domains skipped (already cached)    │ 2,156 │
│ Domains failed or unreachable       │   446 │
│ Total scan duration                 │ 45.23 │
└─────────────────────────────────────┴───────┘
```

## 🎛️ Advanced Usage

### Selective Rescanning
```bash
# Only rescan domains that previously failed
python cli.py domains.txt --rescan-failed
```

### Custom Database Location
```bash
python cli.py domains.txt --db /path/to/custom.db
```

### Export Specific Results
```bash
# Export only successful domains
python cli.py domains.txt --export-200

# Export only redirecting domains  
python cli.py domains.txt --export-3xx

# Export everything
python cli.py domains.txt --export-all
```

### Programmatic Result Analysis
```python
import sqlite3
import json

# Connect to results database
conn = sqlite3.connect('scan_results.db')

# Find all live domains
cursor = conn.execute("SELECT domain, status_code FROM results WHERE status_code = 200")
live_domains = cursor.fetchall()

# Analyze redirect chains
cursor = conn.execute("SELECT domain, redirect_chain FROM results WHERE status_code BETWEEN 300 AND 399")
for domain, chain_json in cursor:
    chain = json.loads(chain_json)
    print(f"{domain}: {len(chain)} redirects")

conn.close()
```

## 🛠️ Troubleshooting

### Common Issues

1. **Too many connection errors**: Reduce `max_concurrent` to 40-60
2. **Slow scanning**: Check network connection and increase timeout
3. **Memory usage**: Process domains in smaller batches for large lists
4. **Database locks**: Ensure only one scanner instance runs at a time

### Logging

All errors and debug information are logged to:
- Console (INFO level and above)
- `subdomain_scanner.log` file (all levels)

## 📝 Domain List Format

Create a text file with one domain per line:
```
www.example.com
api.example.com  
admin.example.com
# Comments start with #
test.example.com
```

## 🔍 Soft 404 Detection

The scanner captures HTML snippets to help identify soft 404s:

```python
# Check for common soft 404 indicators in snippets
common_404_phrases = ["not found", "page not found", "404", "does not exist"]

conn = sqlite3.connect('scan_results.db')
cursor = conn.execute("SELECT domain, snippet FROM results WHERE status_code = 200")

for domain, snippet in cursor:
    if snippet and any(phrase in snippet.lower() for phrase in common_404_phrases):
        print(f"Potential soft 404: {domain}")
```

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the scanner!

## 📄 License

This project is open source and available under the MIT License.
