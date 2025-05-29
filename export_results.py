#!/usr/bin/env python3
"""
Database Export Utility for Subdomain Scanner

Export scan results to CSV for transfer to new systems or backup purposes.
This script exports the corrected status codes from the fixed scanner.

Usage:
    python export_results.py                    # Export all results to corrected_results.csv
    python export_results.py --output my.csv    # Export to custom filename
    python export_results.py --help             # Show help

Features:
- Exports all past scan results from the database
- Properly formatted redirect chains
- Status code summary
- No scanning required - just exports existing data
"""

import sqlite3
import csv
import json
import sys
import argparse
from pathlib import Path

def export_results_to_csv(db_path="scan_results.db", output_file="corrected_results.csv"):
    """Export results from database to CSV with redirect chain info"""
    
    print(f"🔍 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("""
        SELECT domain, status_code, redirect_chain, snippet, error_message
        FROM results 
        ORDER BY 
            CASE 
                WHEN status_code BETWEEN 200 AND 299 THEN 1
                WHEN status_code BETWEEN 300 AND 399 THEN 2
                WHEN status_code = 999 THEN 3
                ELSE 4
            END,
            domain
    """)
    
    print(f"📝 Creating CSV file: {output_file}")
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['domain', 'status_code', 'redirect_info'])
        
        count = 0
        for row in cursor.fetchall():
            domain, status_code, redirect_chain, snippet, error_message = row
            
            # Parse redirect chain
            redirect_info = ""
            if redirect_chain and redirect_chain != "[]":
                try:
                    chain = json.loads(redirect_chain)
                    if len(chain) > 1:
                        # Multiple redirects - show the chain
                        chain_parts = []
                        for hop in chain:
                            chain_parts.append(f"{hop['url']} ({hop['status_code']})")
                        redirect_info = " -> ".join(chain_parts)
                    elif len(chain) == 1:
                        # Single response (no redirects)
                        redirect_info = chain[0]['url']
                except:
                    redirect_info = "Error parsing redirect chain"
            elif error_message:
                redirect_info = f"Error: {error_message}"
            else:
                redirect_info = f"https://{domain}"
            
            writer.writerow([domain, status_code or "ERROR", redirect_info])
            count += 1
    
    conn.close()
    print(f"✅ Results exported to {output_file} ({count} domains)")
    
    # Print summary
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT status_code, COUNT(*) FROM results GROUP BY status_code ORDER BY status_code")
    print(f"\n📊 Status Code Summary:")
    for status_code, count in cursor.fetchall():
        if status_code:
            if 200 <= status_code <= 299:
                print(f"  {status_code} (Success): {count}")
            elif 300 <= status_code <= 399:
                print(f"  {status_code} (Redirect): {count}")
            elif status_code == 999:
                print(f"  {status_code} (Too many redirects): {count}")
            else:
                print(f"  {status_code}: {count}")
        else:
            print(f"  ERROR: {count}")
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export subdomain scanner database results to CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python export_results.py                    # Export all results to corrected_results.csv
  python export_results.py -o my_results.csv  # Export to custom filename
  python export_results.py --db custom.db     # Export from custom database file

This tool exports all your past scan results without running a new scan.
Perfect for backing up data or transferring results between systems.
        """
    )
    
    parser.add_argument(
        '--output', '-o', 
        default='corrected_results.csv',
        help='Output CSV filename (default: corrected_results.csv)'
    )
    
    parser.add_argument(
        '--database', '--db',
        default='scan_results.db', 
        help='Database file to export from (default: scan_results.db)'
    )
    
    args = parser.parse_args()
    
    # Check if database exists
    if not Path(args.database).exists():
        print(f"❌ Error: Database file '{args.database}' not found.")
        print(f"💡 Make sure you're in the correct directory and have run a scan first.")
        sys.exit(1)
    
    print(f"🚀 Exporting results from '{args.database}' to '{args.output}'")
    print(f"📁 This exports all your past scan data without running a new scan.\n")
    
    export_results_to_csv(args.database, args.output)
