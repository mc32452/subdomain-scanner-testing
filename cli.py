#!/usr/bin/env python3
"""
Command Line Interface for High-Concurrency Subdomain Scanner

This script provides a command-line interface for scanning large lists of subdomains
to determine their online status, redirect chains, and content snippets.

Usage:
    python cli.py domains.txt [options]

Example:
    python cli.py domains.txt --concurrent 60 --export-200

Author: Subdomain Scanner Contributors
License: MIT
"""

import asyncio
import argparse
from subdomain_scanner import SubdomainScanner, load_domains_from_file
from rich.console import Console

def main():
    parser = argparse.ArgumentParser(description='High-Concurrency Subdomain Scanner')
    parser.add_argument('domains_file', help='Path to file containing domains (one per line)')
    parser.add_argument('--concurrent', '-c', type=int, default=80, 
                       help='Maximum concurrent connections (default: 80)')
    parser.add_argument('--db', '-d', default='scan_results.db', 
                       help='SQLite database path (default: scan_results.db)')
    parser.add_argument('--rescan-failed', '-r', action='store_true',
                       help='Rescan domains that previously failed')
    parser.add_argument('--export-200', action='store_true',
                       help='Export domains with 200 status to successful_domains.csv')
    parser.add_argument('--export-3xx', action='store_true', 
                       help='Export domains with 3xx status to redirecting_domains.csv')
    parser.add_argument('--export-all', action='store_true',
                       help='Export all results to all_results.csv')
    
    args = parser.parse_args()
    
    console = Console()
    
    # Load domains from file
    domains = load_domains_from_file(args.domains_file)
    if not domains:
        console.print(f"[red]Error: No domains loaded from {args.domains_file}[/red]")
        return
    
    # Create scanner
    scanner = SubdomainScanner(db_path=args.db, max_concurrent=args.concurrent)
    
    async def run_scan():
        console.print(f"[bold blue]🚀 Starting scan of {len(domains)} domains...[/bold blue]")
        
        # Run scan
        summary = await scanner.scan_domains(domains, rescan_failed=args.rescan_failed)
        scanner.print_summary(summary)
        
        # Export results if requested
        if args.export_200:
            scanner.export_results(status_codes=[200], output_file="successful_domains.csv")
        
        if args.export_3xx:
            scanner.export_results(status_codes=[301, 302, 303, 307, 308], output_file="redirecting_domains.csv")
        
        if args.export_all:
            scanner.export_results(output_file="all_results.csv")
        
        console.print("[green]✅ Scan completed![/green]")
    
    # Run the async scan
    asyncio.run(run_scan())

if __name__ == "__main__":
    main()
