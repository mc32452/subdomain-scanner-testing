#!/usr/bin/env python3
"""
High-Concurrency Subdomain Scanner

A fast, efficient Python tool for scanning large lists of subdomains to determine
their online status, redirect chains, and content snippets. Built with async/await
for high performance and intelligent caching to avoid redundant scans.

Author: Subdomain Scanner Contributors
License: MIT
"""

import asyncio
import csv
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import httpx
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('subdomain_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SubdomainScanner:
    """
    High-performance subdomain scanner with async HTTP requests and intelligent caching.
    
    Features:
    - Concurrent scanning with configurable limits
    - SQLite-based result caching to avoid redundant scans
    - Full redirect chain tracking
    - Content snippet capture for analysis
    - Comprehensive error logging and reporting
    
    Args:
        db_path (str): Path to SQLite database file
        max_concurrent (int): Maximum concurrent HTTP connections
    """
    def __init__(self, db_path: str = "scan_results.db", max_concurrent: int = 80):
        self.db_path = db_path
        self.max_concurrent = max_concurrent
        self.console = Console()
        self.init_database()
        
        # Counters for summary
        self.new_200s = 0
        self.new_3xxs = 0
        self.failed_scans = 0
        self.skipped_domains = 0
        
    def init_database(self):
        """Initialize SQLite database with optimized schema"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                domain TEXT PRIMARY KEY,
                status_code INTEGER,
                redirect_chain TEXT,
                snippet TEXT,
                error_message TEXT,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_duration_ms INTEGER
            )
        """)
        
        # Create indexes for faster lookups
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status_code ON results(status_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_last_checked ON results(last_checked)")
        conn.commit()
        conn.close()
        
    def get_cached_domains(self) -> Set[str]:
        """Get domains that already have successful results (200 or 3xx)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT domain FROM results 
            WHERE status_code BETWEEN 200 AND 399
        """)
        cached = {row[0] for row in cursor.fetchall()}
        conn.close()
        logger.info(f"Found {len(cached)} domains already cached with valid responses")
        return cached
        
    def get_failed_domains(self) -> Set[str]:
        """Get domains that failed or have no valid response for retry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT domain FROM results 
            WHERE status_code IS NULL 
               OR status_code < 200 
               OR status_code >= 400
               OR error_message IS NOT NULL
        """)
        failed = {row[0] for row in cursor.fetchall()}
        conn.close()
        logger.info(f"Found {len(failed)} domains with failed/invalid responses for retry")
        return failed
        
    async def fetch_with_redirects(self, client: httpx.AsyncClient, domain: str, semaphore: asyncio.Semaphore) -> Optional[Dict]:
        """Fetch a domain with full redirect chain tracking"""
        async with semaphore:
            start_time = time.time()
            url = f"https://{domain}"
            
            try:
                # Use manual redirect following for better control
                redirect_chain = []
                current_url = url
                max_redirects = 10
                redirect_count = 0
                
                while redirect_count < max_redirects:
                    try:
                        response = await client.get(
                            current_url,
                            follow_redirects=False,
                            timeout=15.0,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (compatible; SubdomainScanner/1.0)',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                            }
                        )
                        
                        redirect_chain.append({
                            'url': current_url,
                            'status_code': response.status_code,
                            'headers': dict(response.headers)
                        })
                        
                        # Check if this is a redirect
                        if 300 <= response.status_code < 400:
                            location = response.headers.get('location')
                            if location:
                                # Handle relative URLs
                                if location.startswith('/'):
                                    parsed = urlparse(current_url)
                                    current_url = f"{parsed.scheme}://{parsed.netloc}{location}"
                                elif location.startswith('http'):
                                    current_url = location
                                else:
                                    # Relative to current path
                                    parsed = urlparse(current_url)
                                    current_url = f"{parsed.scheme}://{parsed.netloc}/{location}"
                                redirect_count += 1
                                continue
                        
                        # Final response - extract snippet if 200
                        snippet = ""
                        if response.status_code == 200:
                            try:
                                content = await response.aread()
                                text_content = content.decode('utf-8', errors='ignore')
                                # Extract first 2048 characters, clean up whitespace
                                snippet = ' '.join(text_content[:2048].split())
                            except Exception as e:
                                logger.warning(f"Failed to read content for {domain}: {e}")
                        
                        duration_ms = int((time.time() - start_time) * 1000)
                        
                        return {
                            'domain': domain,
                            'status_code': response.status_code,
                            'redirect_chain': json.dumps(redirect_chain),
                            'snippet': snippet,
                            'error_message': None,
                            'scan_duration_ms': duration_ms
                        }
                        
                    except httpx.ConnectError as e:
                        # Try HTTP if HTTPS fails
                        if current_url.startswith('https://'):
                            logger.info(f"HTTPS failed for {domain}, trying HTTP...")
                            current_url = current_url.replace('https://', 'http://')
                            continue
                        else:
                            raise e
                
                # Too many redirects
                duration_ms = int((time.time() - start_time) * 1000)
                return {
                    'domain': domain,
                    'status_code': None,
                    'redirect_chain': json.dumps(redirect_chain),
                    'snippet': "",
                    'error_message': f"Too many redirects (>{max_redirects})",
                    'scan_duration_ms': duration_ms
                }
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"Failed to scan {domain}: {error_msg}")
                
                return {
                    'domain': domain,
                    'status_code': None,
                    'redirect_chain': "[]",
                    'snippet': "",
                    'error_message': error_msg,
                    'scan_duration_ms': duration_ms
                }
    
    def save_result(self, result: Dict):
        """Save scan result to database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO results(
                domain, status_code, redirect_chain, snippet, error_message, 
                last_checked, scan_duration_ms
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (
            result['domain'],
            result['status_code'],
            result['redirect_chain'],
            result['snippet'],
            result['error_message'],
            result['scan_duration_ms']
        ))
        conn.commit()
        conn.close()
        
        # Update counters
        if result['status_code'] == 200:
            self.new_200s += 1
        elif result['status_code'] and 300 <= result['status_code'] < 400:
            self.new_3xxs += 1
        elif result['error_message'] or not result['status_code']:
            self.failed_scans += 1
    
    async def scan_domains(self, domains: List[str], rescan_failed: bool = False) -> Dict:
        """Main scanning function with progress tracking"""
        start_time = time.time()
        
        # Filter domains based on cache
        cached_domains = self.get_cached_domains()
        
        if rescan_failed:
            failed_domains = self.get_failed_domains()
            domains_to_scan = [d for d in domains if d in failed_domains or d not in cached_domains]
            self.console.print(f"[yellow]Rescanning {len(failed_domains)} failed domains and {len([d for d in domains if d not in cached_domains])} new domains[/yellow]")
        else:
            domains_to_scan = [d for d in domains if d not in cached_domains]
        
        self.skipped_domains = len(domains) - len(domains_to_scan)
        
        if not domains_to_scan:
            self.console.print("[green]All domains already cached with valid responses![/green]")
            return self.get_scan_summary(start_time)
        
        self.console.print(f"[blue]Scanning {len(domains_to_scan)} domains with {self.max_concurrent} concurrent connections[/blue]")
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Configure HTTP client with optimizations
        limits = httpx.Limits(max_keepalive_connections=100, max_connections=200)
        timeout = httpx.Timeout(15.0, connect=10.0)
        
        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            # Create progress bar
            with Progress() as progress:
                task = progress.add_task("[cyan]Scanning domains...", total=len(domains_to_scan))
                
                # Create tasks for all domains
                tasks = [
                    self.fetch_with_redirects(client, domain, semaphore)
                    for domain in domains_to_scan
                ]
                
                # Process in batches to avoid overwhelming the system
                batch_size = 200
                for i in range(0, len(tasks), batch_size):
                    batch = tasks[i:i + batch_size]
                    results = await asyncio.gather(*batch, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(f"Task failed with exception: {result}")
                            self.failed_scans += 1
                        elif result:
                            self.save_result(result)
                        
                        progress.update(task, advance=1)
        
        return self.get_scan_summary(start_time)
    
    def get_scan_summary(self, start_time: float) -> Dict:
        """Generate scan summary"""
        total_time = time.time() - start_time
        
        summary = {
            'total_scanned': self.new_200s + self.new_3xxs + self.failed_scans,
            'new_200s': self.new_200s,
            'new_3xxs': self.new_3xxs,
            'failed_scans': self.failed_scans,
            'skipped_domains': self.skipped_domains,
            'scan_duration': total_time
        }
        
        return summary
    
    def print_summary(self, summary: Dict):
        """Print formatted scan summary"""
        table = Table(title="🔍 Subdomain Scan Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        
        table.add_row("Total domains scanned", str(summary['total_scanned']))
        table.add_row("New 200 responses added", str(summary['new_200s']))
        table.add_row("New 3xx responses with redirect chains", str(summary['new_3xxs']))
        table.add_row("Domains skipped (already cached)", str(summary['skipped_domains']))
        table.add_row("Domains failed or unreachable", str(summary['failed_scans']))
        table.add_row("Total scan duration", f"{summary['scan_duration']:.2f} seconds")
        
        self.console.print(table)
    
    def export_results(self, status_codes: List[int] = None, output_file: str = "results.csv") -> Dict:
        """Export results to CSV file"""
        conn = sqlite3.connect(self.db_path)
        
        if status_codes:
            placeholders = ','.join('?' * len(status_codes))
            query = f"SELECT * FROM results WHERE status_code IN ({placeholders})"
            cursor = conn.execute(query, status_codes)
        else:
            cursor = conn.execute("SELECT * FROM results")
        
        results = []
        for row in cursor.fetchall():
            # Parse redirect chain for better CSV formatting
            redirect_chain_readable = ""
            if row[2]:  # redirect_chain column
                try:
                    chain = json.loads(row[2])
                    if chain:
                        # Create simplified chain: URL (status) -> URL (status)
                        redirect_chain_readable = ' -> '.join([
                            f"{step['url']} ({step['status_code']})" for step in chain
                        ])
                except json.JSONDecodeError:
                    redirect_chain_readable = "Parse error"
            
            # Truncate snippet for CSV readability
            snippet = row[3] if row[3] else ""
            if snippet and len(snippet) > 200:
                snippet = snippet[:200] + '...'
            
            results.append({
                'domain': row[0],
                'status_code': row[1],
                'redirect_chain': redirect_chain_readable,
                'snippet': snippet,
                'error_message': row[4],
                'last_checked': row[5],
                'scan_duration_ms': row[6]
            })
        
        conn.close()
        
        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if results:
                fieldnames = ['domain', 'status_code', 'redirect_chain', 'snippet', 'error_message', 'last_checked', 'scan_duration_ms']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        
        self.console.print(f"[green]Exported {len(results)} results to {output_file}[/green]")
        return {'exported_count': len(results), 'file': output_file}

def load_domains_from_file(file_path: str) -> List[str]:
    """Load domains from a text file (one per line)"""
    domains = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                domain = line.strip()
                if domain and not domain.startswith('#'):
                    domains.append(domain)
    except FileNotFoundError:
        logger.error(f"Domain file not found: {file_path}")
        return []
    
    logger.info(f"Loaded {len(domains)} domains from {file_path}")
    return domains

async def main():
    """Main function with example usage"""
    # Example domain list - replace with your actual domains
    example_domains = [
        "www.example.com",
        "api.example.com", 
        "admin.example.com",
        "test.example.com",
        "staging.example.com",
        "dev.example.com",
        "blog.example.com",
        "shop.example.com",
        "mail.example.com",
        "ftp.example.com"
    ]
    
    # You can also load from file:
    # domains = load_domains_from_file("domains.txt")
    
    scanner = SubdomainScanner(max_concurrent=80)
    
    # Run initial scan
    console = Console()
    console.print("[bold blue]🚀 Starting subdomain scan...[/bold blue]")
    
    summary = await scanner.scan_domains(example_domains)
    scanner.print_summary(summary)
    
    # Export successful results
    scanner.export_results(status_codes=[200], output_file="successful_domains.json")
    scanner.export_results(status_codes=[301, 302, 303, 307, 308], output_file="redirecting_domains.json")
    
    console.print("[green]✅ Scan completed! Check the generated files for results.[/green]")

if __name__ == "__main__":
    asyncio.run(main())
