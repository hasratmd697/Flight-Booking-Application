"""
Script to update the CSV files with business and first class fares.
This ensures future database imports will have the correct fares.
"""

import csv
import random
import os

def update_csv_fares(input_file, output_file):
    """Update a flight CSV file with business and first class fares where missing."""
    
    rows = []
    updated_count = 0
    
    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        for row in reader:
            economy_fare = float(row.get('economy_fare', 0) or 0)
            business_fare = row.get('business_fare', '').strip()
            first_fare = row.get('first_fare', '').strip()
            
            updated = False
            
            # Update business fare if missing
            if not business_fare and economy_fare > 0:
                multiplier = random.uniform(2.5, 3.5)
                row['business_fare'] = str(round(economy_fare * multiplier))
                updated = True
            
            # Update first fare if missing
            if not first_fare and economy_fare > 0:
                multiplier = random.uniform(4.0, 6.0)
                row['first_fare'] = str(round(economy_fare * multiplier))
                updated = True
            
            if updated:
                updated_count += 1
            
            rows.append(row)
    
    # Write updated data back to file
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return updated_count, len(rows)

def main():
    # Update domestic flights
    domestic_file = './Data/domestic_flights.csv'
    if os.path.exists(domestic_file):
        updated, total = update_csv_fares(domestic_file, domestic_file)
        print(f"Domestic flights: Updated {updated} out of {total} rows")
    
    # Update international flights
    international_file = './Data/international_flights.csv'
    if os.path.exists(international_file):
        updated, total = update_csv_fares(international_file, international_file)
        print(f"International flights: Updated {updated} out of {total} rows")
    
    print("\nCSV files have been updated with business and first class fares.")

if __name__ == "__main__":
    main()
