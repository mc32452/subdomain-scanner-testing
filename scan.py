#!/usr/bin/env python3
"""
Simple subdomain scanner - one script to rule them all.
Usage: python scan.py domains.txt [concurrency]
"""

import asyncio
import sys
from subdomain_scanner import SubdomainScanner, load_domains_from_file

async def main():
    # Get domains file
    if len(sys.argv) < 2:
        print("Usage: python scan.py domains.txt [concurrency]")
        sys.exit(1)
    
    domains_file = sys.argv[1]
    concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    
    # Load domains
    domains = load_domains_from_file(domains_file)
    if not domains:
        print(f"❌ No domains loaded from {domains_file}")
        return
    
    print(f"🔍 Scanning {len(domains)} domains with {concurrency} concurrent connections")
    
    # Run scan
    scanner = SubdomainScanner(max_concurrent=concurrency)
    summary = await scanner.scan_domains(domains)
    scanner.print_summary(summary)
    
    print("✅ Scan complete. All results saved to scan_results.db")
    print("💾 Run again with new domains or higher concurrency to add more data")

if __name__ == "__main__":
    asyncio.run(main())
