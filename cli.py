#!/usr/bin/env python3
"""
Simple CLI for subdomain scanner - just scan domains and save to database.
Usage: python cli.py domains.txt
"""

import asyncio
import sys
from subdomain_scanner import SubdomainScanner, load_domains_from_file

def main():
    if len(sys.argv) != 2:
        print("Usage: python cli.py domains.txt")
        sys.exit(1)
    
    domains_file = sys.argv[1]
    domains = load_domains_from_file(domains_file)
    
    if not domains:
        print(f"Error: No domains loaded from {domains_file}")
        sys.exit(1)
    
    scanner = SubdomainScanner()
    
    async def run_scan():
        print(f"Scanning {len(domains)} domains...")
        summary = await scanner.scan_domains(domains)
        scanner.print_summary(summary)
        print("Results saved to scan_results.db")
        print("Export with: scanner.export_results(status_codes=[200], output_file='results.csv')")
    
    asyncio.run(run_scan())

if __name__ == "__main__":
    main()
