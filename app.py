from flask import Flask, render_template, redirect, url_for, flash, jsonify, request
from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv
import os
import statistics
from datetime import datetime
from pathlib import Path
from scraper import scrape_real_data, scrape_single_item

# --- SETUP ---
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

mongo_uri = os.environ.get("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.get_default_database('chakula_db')

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# --- ROUTES ---

@app.route('/')
def home():
    """Landing Page"""
    return render_template('home.html')

@app.route('/dashboard')
def dashboard_categories():
    """Category Hub"""
    categories = db.scrapped_items.distinct("category") or ['Food', 'Home']
    cat_data = [{"name": c, "count": db.scrapped_items.count_documents({"category": c})} for c in categories]
    return render_template('categories.html', categories=cat_data)

@app.route('/category/<category_name>')
def category_dashboard(category_name):
    """
    Dashboard: Shows cards with Cheapest Price highlighted.
    """
    pipeline = [
        {"$match": {"category": category_name}},
        {"$sort": {"price": 1}}, # Sort cheapest first to pick best deal
        
        {
            "$group": {
                "_id": "$commodity_name",
                "cheapest_price": {"$first": "$price"},
                "cheapest_source": {"$first": "$source"},
                "avg_price": {"$avg": "$price"},
                "max_price": {"$max": "$price"},
                "sources": {"$addToSet": "$source"},
                "doc": {"$first": "$$ROOT"}
            }
        }
    ]
    results = list(db.scrapped_items.aggregate(pipeline))
    
    cards = []
    for item in results:
        cards.append({
            'name': item['_id'], 
            'cheapest_price': item['cheapest_price'],
            'cheapest_source': item['cheapest_source'],
            'avg_price': round(item['avg_price'], 0),
            'max_price': item['max_price'],
            'source_count': len(item['sources']),
            'sources_list': ", ".join(item['sources'])
        })
    return render_template('dashboard.html', items=cards, category=category_name)

# --- ACTIONS ---

@app.route('/scrape-dashboard')
def scrape_dashboard_action():
    try:
        count = scrape_real_data(db)
        flash(f"Updated! Scraped {count} prices from Naivas, Jumia & Carrefour.", "success")
    except Exception as e:
        flash(f"Update failed: {str(e)}", "error")
    return redirect(url_for('dashboard_categories'))

@app.route('/check-specific-item', methods=['GET', 'POST'])
def check_specific_item():
    if request.method == 'POST':
        item_name = request.form.get('item_name')
        if not item_name:
            flash("Please enter an item name", "error")
            return redirect(url_for('check_specific_item'))

        count = scrape_single_item(db, item_name, ['Naivas', 'Jumia', 'Carrefour'])
        
        if count > 0:
            return redirect(url_for('search_results', q=item_name))
        else:
            flash(f"Could not find '{item_name}'.", "error")
            return redirect(url_for('check_specific_item'))

    return render_template('check_item.html')



@app.route('/search-results')
def search_results():
    query = request.args.get('q', '').strip()
    
    # 1. Fetch ALL history for this item (sorted by date)
   
    history = list(db.live_searches.find({"search_term": query}).sort("created_at", 1))
    
    if not history: 
        return redirect(url_for('check_specific_item'))

    # 2. Get the "Current" (Latest) status for the list view
    # We organize by source to show the most recent price from each shop
    latest_by_source = {}
    for entry in history:
        latest_by_source[entry['source']] = entry
    
    current_results = list(latest_by_source.values())
    
    # 3. Calculate Stats
    prices = [r['price'] for r in current_results]
    stats = {
        'min': min(prices), 
        'max': max(prices),
        'avg': round(sum(prices)/len(prices), 2),
        'best': min(current_results, key=lambda x: x['price'])
    }

    
    # Get all unique dates from the history
    dates = sorted(list(set(row['created_at'].strftime('%Y-%m-%d') for row in history)))
    
    datasets = []
    colors = {'Naivas': '#ef4444', 'Jumia': '#f97316', 'Carrefour': '#3b82f6'}
    
    for source in ['Naivas', 'Jumia', 'Carrefour']:
        # Filter history for just this supermarket
        source_data = [d for d in history if d['source'] == source]
        
        # Create a lookup map: Date -> Price
        price_map = {d['created_at'].strftime('%Y-%m-%d'): d['price'] for d in source_data}
        
        # Create the data array. N/A if date is missing 
        data_points = [price_map.get(date, None) for date in dates]
        
        
        if any(p is not None for p in data_points):
            datasets.append({
                'label': source,
                'data': data_points,
                'borderColor': colors.get(source, '#ccc'),
                'backgroundColor': colors.get(source, '#ccc'),
                'fill': False,
                'tension': 0.1
            })

    # pass graph object to frontend
    graph_data = {
        'labels': dates,
        'datasets': datasets
    }

    return render_template('search_result.html', query=query, items=current_results, stats=stats, graph=graph_data)



@app.route('/api/subscribe', methods=['POST'])
def subscribe_alert():
    data = request.json
    item_name = data.get('item_name')
    target_price = data.get('target_price')
    
    if not item_name or not target_price: return jsonify({'error': 'Missing data'}), 400

    db.alerts.update_one(
        {"item_name": item_name},
        {"$set": {"target_price": float(target_price), "active": True, "created_at": datetime.utcnow()}},
        upsert=True
    )
    return jsonify({'status': 'success', 'message': 'Alert set!'})

# --- PROFILE & ALERTS VIEW ---

@app.route('/profile')
def profile():
    user = {"name": "Guest User", "email": "user@example.com"}
    
    my_alerts = list(db.alerts.find({"active": True}))
    notifications = []
    watching = []

    for alert in my_alerts:
        # Check against LATEST scrapped data
        latest = db.scrapped_items.find_one(
            {"commodity_name": {"$regex": alert['item_name'], "$options": "i"}},
            sort=[("created_at", -1)]
        )
        
        item_data = {"item": alert['item_name'], "target": alert['target_price'], "current": "N/A", "status": "Pending"}
        
        if latest:
            item_data['current'] = f"KSh {latest['price']}"
            if latest['price'] <= alert['target_price']:
                notifications.append({
                    "title": f"Price Drop: {alert['item_name']}",
                    "message": f"Found at {latest['source']} for KSh {latest['price']}!",
                    "is_offer": True
                })
                item_data['status'] = "Target Met! 🎉"
            else:
                item_data['status'] = "Price too high"
        
        watching.append(item_data)

    return render_template('notifications.html', user=user, notifications=notifications, watching=watching)

# --- DASHBOARD GRAPH API ---

@app.route('/api/details/<comm_name>')
def get_item_details(comm_name):
    # Fetch history
    data = list(db.scrapped_items.find({"commodity_name": comm_name}).sort("created_at", 1))
    
    if not data: 
        return jsonify({'error': 'No data'})
    
    # --- FIX: Convert ObjectId to string for JSON serialization ---
    for doc in data:
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
    # --------------------------------------------------------------
    
    dates = sorted(list(set(row['created_at'].strftime('%Y-%m-%d') for row in data)))
    datasets = {}
    
    # Configure colors for 3 stores
    colors = {'Naivas': '#ef4444', 'Jumia': '#f97316', 'Carrefour': '#3b82f6'}
    
    for source in ["Naivas", "Jumia", "Carrefour"]:
        prices = []
        source_data = {d['created_at'].strftime('%Y-%m-%d'): d['price'] for d in data if d['source'] == source}
        for date in dates: 
            prices.append(source_data.get(date, None))
        
        datasets[source] = {
            'label': source,
            'data': prices,
            'borderColor': colors.get(source, '#ccc'),
            'backgroundColor': colors.get(source, '#ccc')
        }

    return jsonify({
        'graph': {
            'labels': dates,
            'datasets': list(datasets.values())
        },
        'sources': data[-15:] 
    })

# --- INVENTORY ---
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if request.method == 'POST':
        db.inventory.insert_one({
            "name": request.form.get('name'),
            "quantity": int(request.form.get('quantity')),
            "price": float(request.form.get('price')),
            "date_added": datetime.utcnow()
        })
        return redirect(url_for('inventory'))
    items = list(db.inventory.find().sort("date_added", -1))
    return render_template('inventory.html', items=items)

if __name__ == '__main__':
    app.run(debug=True, port=5000)