#!/usr/bin/env python3
"""
Display summary of receipt matrix report
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from receipt_matrix_report import load_customers, load_receipts, parse_date, get_customer_display_name
from collections import defaultdict

def main():
    print("=" * 80)
    print("RECEIPT MATRIX REPORT SUMMARY")
    print("=" * 80)
    print()
    
    # Load data
    customers_data = load_customers()
    receipts_data = load_receipts()
    
    # Calculate statistics
    total_receipts = sum(len(r) for r in receipts_data.values())
    unique_months = len(set((y, m) for (_, y, m), _ in receipts_data.items()))
    unique_customers = set(c for (c, _, _), _ in receipts_data.items())
    
    print(f"Total Customers: {len(customers_data)}")
    print(f"Total Receipts: {total_receipts}")
    print(f"Unique Customer/Month combinations: {len(receipts_data)}")
    print()
    
    # Group by year/month
    by_month = defaultdict(list)
    for (customer_key, year, month), receipts in receipts_data.items():
        by_month[(year, month)].append({
            'customer': customer_key,
            'receipts': receipts
        })
    
    # Display by month
    for (year, month) in sorted(by_month.keys()):
        entries = by_month[(year, month)]
        print(f"\n{'='*80}")
        print(f"Year: {year}, Month: {month:02d}")
        print(f"{'='*80}")
        print(f"{'Customer Name':<35} {'Count':<8} {'Receipt Numbers'}")
        print("-" * 80)
        
        # Sort by customer name
        entries_sorted = sorted(entries, key=lambda x: get_customer_display_name(customers_data, x['customer']))
        
        for entry in entries_sorted:
            customer_name = get_customer_display_name(customers_data, entry['customer'])
            count = len(entry['receipts'])
            receipt_nums = ', '.join([r['recipeNum'] for r in entry['receipts']]) if entry['receipts'] else 'NONE'
            print(f"{customer_name:<35} {count:<8} {receipt_nums}")
        
        # Show customers with NO receipts for this month
        missing_customers = []
        for cust_key in customers_data.keys():
            found = any(e['customer'] == cust_key for e in entries)
            if not found:
                missing_customers.append(get_customer_display_name(customers_data, cust_key))
        
        if missing_customers:
            print()
            print("MISSING RECEIPTS (customers with 0 receipts this month):")
            for cust in sorted(missing_customers):
                print(f"  - {cust}")
    
    print()
    print("=" * 80)
    print("Report saved to: E:\simulation_rentals\receipt_matrix_report.xlsx")
    print("=" * 80)

if __name__ == "__main__":
    main()
