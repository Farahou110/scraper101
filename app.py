from flask import Flask, render_template, redirect, url_for, flash, jsonify, request
from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv
import os
import statistics
from pathlib import Path
from scraper import scrape_real_data

# --- SETUP ---
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

mongo_uri = os.environ.get("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.get_default_database('commodity_price_tracker')

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# --- ROUTES ---

@app.route('/')
def home():
    """
    Landing Page: Shows available Categories.
    """
    # Get unique categories from the database
    categories = db.scrapped_items.distinct("category")
    # Ensure we have at least some defaults if DB is empty
    if not categories:
        categories = ['Food', 'Electronics', 'Machinery']
        
    # Calculate item counts for each category
    cat_data = []
    for cat in categories:
        count = db.scrapped_items.count_documents({"category": cat})
        cat_data.append({"name": cat, "count": count})

    return render_template('home.html', categories=cat_data)

@app.route('/category/<category_name>')
def category_dashboard(category_name):
    """
    The Dashboard: Shows items for a specific category.
    """
    # Pipeline: Group by Commodity -> Get Latest Prices
    pipeline = [
        {"$match": {"category": category_name}}, # Filter by Category
        {"$sort": {"created_at": -1}},
        {
            "$group": {
                "_id": {
                    "commodity": "$commodity_name",
                    "source": "$source"
                },
                "price": {"$first": "$price"},
                "doc": {"$first": "$$ROOT"}
            }
        },
        {
            "$group": {
                "_id": "$_id.commodity",
                "avg_price": {"$avg": "$price"},
                "min_price": {"$min": "$price"},
                "max_price": {"$max": "$price"},
                "sources": {"$push": "$_id.source"},
                "sample_doc": {"$first": "$doc"}
            }
        }
    ]

    results = list(db.scrapped_items.aggregate(pipeline))

    cards = []
    for item in results:
        doc = item['sample_doc']
        # Get previous average for trend (simplified)
        trend = 'stable' 
        
        cards.append({
            'name': item['_id'], 
            'avg_price': round(item['avg_price'], 0),
            'min_price': item['min_price'],
            'max_price': item['max_price'],
            'source_count': len(item['sources']),
            'sources_list': ", ".join(item['sources']),
            'unit': 'unit' 
        })

    return render_template('dashboard.html', items=cards, category=category_name)

@app.route('/api/details/<comm_name>')
def get_item_details(comm_name):
    """
    API: Returns data for Multi-Line Chart (Price vs Time per Seller)
    """
    # Fetch all history for this commodity
    data = list(db.scrapped_items.find(
        {"commodity_name": comm_name}
    ).sort("created_at", 1))
    
    if not data: return jsonify({'error': 'No data'})

    # 1. Prepare Multi-Line Graph Data
    # Structure: { "2025-12-01": { "Naivas": 100, "Jumia": 105 } }
    dates = sorted(list(set(row['created_at'].strftime('%Y-%m-%d') for row in data)))
    
    datasets = {}
    sources = ["Naivas", "Jumia"] # Explicitly tracking these two
    
    for source in sources:
        # Create a list of prices matching the sorted dates, using None for missing days
        prices = []
        source_data = [d for d in data if d['source'] == source]
        
        # Helper map for quick lookup
        date_price_map = {d['created_at'].strftime('%Y-%m-%d'): d['price'] for d in source_data}
        
        for date in dates:
            prices.append(date_price_map.get(date, None)) # None ensures gaps in line chart
            
        datasets[source] = prices

    # 2. Sources List (Latest details)
    latest_sources = []
    for source in sources:
        # Get latest entry
        latest = next((d for d in reversed(data) if d['source'] == source), None)
        if latest:
            latest_sources.append({
                'source': source,
                'price': latest['price'],
                'product_name': latest['product_name'],
                'date': latest['created_at']
            })

    return jsonify({
        'graph': {
            'labels': dates,
            'datasets': [
                {'label': 'Naivas', 'data': datasets['Naivas'], 'borderColor': '#ef4444', 'backgroundColor': '#ef4444'},
                {'label': 'Jumia', 'data': datasets['Jumia'], 'borderColor': '#f97316', 'backgroundColor': '#f97316'}
            ]
        },
        'sources': latest_sources
    })

@app.route('/scrape')
def trigger_scrape():
    try:
        count = scrape_real_data(db)
        flash(f"Scraped {count} items from Naivas & Jumia!", "success")
    except Exception as e:
        flash(f"Scraper Error: {str(e)}", "error")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)