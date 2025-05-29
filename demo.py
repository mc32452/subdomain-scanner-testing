#!/usr/bin/env python3
"""
Demo script showing basic usage of the subdomain scanner.
"""

import asyncio
from subdomain_scanner import SubdomainScanner, load_domains_from_file

async def demo():
    """Run a demo scan with sample domains."""
    print("🔍 Subdomain Scanner Demo")
    print("=" * 50)
    
    # Load sample domains
    domains = load_domains_from_file("sample_domains.txt")
    print(f"Loaded {len(domains)} domains for scanning")
    
    # Create scanner with moderate concurrency for demo
    scanner = SubdomainScanner(max_concurrent=20)
    
    # Run scan
    print("\nStarting scan...")
    summary = await scanner.scan_domains(domains)
    
    # Display results
    scanner.print_summary(summary)
    
    # Export successful domains
    scanner.export_results(status_codes=[200], output_file="demo_successful.csv")
    
    print("\n✅ Demo completed! Check demo_successful.csv for results.")

if __name__ == "__main__":
    asyncio.run(demo())
