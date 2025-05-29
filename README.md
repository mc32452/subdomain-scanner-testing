# 🔍 High-Concurrency Subdomain Scanner

A high-performance Python tool for scanning thousands of subdomains with async HTTP requests, intelligent caching, and comprehensive result tracking.

## 🚀 Features

- **High Concurrency**: Scan up to 80+ domains simultaneously using async HTTP
- **Intelligent Caching**: SQLite-based results storage with automatic skip of already-scanned valid domains
- **Full Redirect Tracking**: Captures complete redirect chains for 3xx responses
- **Content Snippets**: Extracts HTML snippets from 200 responses for soft-404 detection
- **Comprehensive Logging**: Detailed error logging and scan metrics
- **Incremental Scanning**: Only rescans failed/invalid results, saving time
- **Rich Output**: Beautiful progress bars and summary tables
- **Export Options**: JSON exports for successful, redirecting, or all results

## 📦 Installation

```bash
# Clone or download the files
cd subdomain-scanner-testing

# Install dependencies
pip install -r requirements.txt
```

## 🎯 Quick Start

### Option 1: Command Line Interface

```bash
# Basic scan
python cli.py example_domains.txt

# Scan with custom concurrency
python cli.py example_domains.txt --concurrent 60

# Rescan only failed domains
python cli.py example_domains.txt --rescan-failed

# Export successful domains to JSON
python cli.py example_domains.txt --export-200

# Full example with all options
python cli.py example_domains.txt --concurrent 80 --rescan-failed --export-all
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
