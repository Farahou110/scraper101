from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import random
from pathlib import Path

    


mongo_uri ="mongodb://localhost:27017/"



client = MongoClient(mongo_uri)
db = client.get_default_database('commodity_price_tracker')

# Clear existing data (Optional - comment out if you want to keep data)
db.prices.delete_many({})
print("🗑️  Cleared old data.")

# Sample Data to Generate
counties = ["Nairobi", "Mombasa", "Kisumu", "Nakuru"]
sources = ["Jumia", "Naivas", "Carrefour"]

commodities = [
    {"name": "Milk", "cat": "dairy", "unit": "500ml", "base": 60, "brands": ["Brookside", "Tuzo", "Fresha"]},
    {"name": "Sugar", "cat": "pantry", "unit": "1kg", "base": 150, "brands": ["Kabras", "Nutrameal", "Mumias"]},
    {"name": "Maize Meal", "cat": "cereals", "unit": "2kg", "base": 200, "brands": ["Jogoo", "Pembe", "Soko"]},
    {"name": "Cooking Oil", "cat": "pantry", "unit": "1L", "base": 300, "brands": ["Fresh Fri", "Rina", "Golden Fry"]},
]

# Generate History (Last 10 days)
records = []
today = datetime.utcnow()

print("🌱 Generating data...")

for i in range(10): # For past 10 days
    date = today - timedelta(days=i)
    
    for county in counties:
        for item in commodities:
            for source in sources:
                # Pick a random specific brand to simulate "Quality"
                brand = random.choice(item['brands'])
                full_name = f"{brand} {item['name']} {item['unit']}"
                
                # Randomize price slightly based on base price
                price = item['base'] + random.uniform(-20, 20)
                
                record = {
                    'commodity_name': item['name'],
                    'product_name': full_name,
                    'category': item['cat'],
                    'unit': item['unit'],
                    'county_name': county,
                    'price': round(price, 2),
                    'source': source,
                    'created_at': date
                }
                records.append(record)

# Insert all at once
if records:
    db.prices.insert_many(records)
    print(f"✅ Successfully inserted {len(records)} price records!")
    print("🚀 Run 'python app.py' to see your dashboard.")