from flask import Flask, render_template, redirect, url_for, flash, jsonify, request
from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv
import os
import statistics
from datetime import datetime
from pathlib import Path
from scraper import scrape_real_data, scrape_single_item

# --- NEW IMPORTS FOR AUTH ---
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

# --- SETUP ---
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

mongo_uri = os.environ.get("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.get_default_database('chakula_db')

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# --- AUTH SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Class for Flask-Login
class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.name = user_doc['name']
        self.email = user_doc['email']
        self.role = user_doc.get('role', 'buyer') # buyer or seller

@login_manager.user_loader
def load_user(user_id):
    user_doc = db.users.find_one({"_id": ObjectId(user_id)})
    if user_doc:
        return User(user_doc)
    return None

# --- AUTH ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role') # 'buyer' or 'seller'

        if db.users.find_one({"email": email}):
            flash("Email already exists. Please login.", "error")
            return redirect(url_for('register'))

        # Secure Password Hashing
        hashed_password = generate_password_hash(password)
        
        db.users.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password,
            "role": role,
            "created_at": datetime.utcnow()
        })
        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_doc = db.users.find_one({"email": email})
        
        if user_doc and check_password_hash(user_doc['password'], password):
            user = User(user_doc)
            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password.", "error")
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# --- CORE ROUTES (Modified for Auth) ---

@app.route('/')
def home():
    categories = db.scrapped_items.distinct("category") or ['Food', 'Home']
    cat_data = [{"name": c, "count": db.scrapped_items.count_documents({"category": c})} for c in categories]
    return render_template('home.html', categories=cat_data)

@app.route('/dashboard')
def dashboard_categories():
    categories = db.scrapped_items.distinct("category") or ['Food', 'Home']
    cat_data = [{"name": c, "count": db.scrapped_items.count_documents({"category": c})} for c in categories]
    return render_template('categories.html', categories=cat_data)

@app.route('/category/<category_name>')
def category_dashboard(category_name):
    # (Same pipeline as before)
    pipeline = [
        {"$match": {"category": category_name}},
        {"$sort": {"price": 1}},
        {
            "$group": {
                "_id": "$commodity_name",
                "cheapest_price": {"$first": "$price"},
                "cheapest_source": {"$first": "$source"},
                "avg_price": {"$avg": "$price"},
                "max_price": {"$max": "$price"},
                "sources": {"$addToSet": "$source"},
                "source_count": {"$sum": 1}
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
            'source_count': item['source_count'],
            'sources_list': ", ".join(item['sources'])
        })
    return render_template('dashboard.html', items=cards, category=category_name)

# --- PROTECTED ACTIONS ---

@app.route('/scrape-dashboard')
@login_required  # Only logged in users can trigger scrape
def scrape_dashboard_action():
    try:
        count = scrape_real_data(db)
        flash(f"Updated! Scraped {count} prices.", "success")
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
    # (Same graph logic as before)
    query = request.args.get('q', '').strip()
    history = list(db.live_searches.find({"search_term": query}).sort("created_at", 1))
    
    if not history: return redirect(url_for('check_specific_item'))

    latest_by_source = {}
    for entry in history: latest_by_source[entry['source']] = entry
    current_results = list(latest_by_source.values())
    
    prices = [r['price'] for r in current_results]
    stats = {
        'min': min(prices), 'max': max(prices),
        'avg': round(sum(prices)/len(prices), 2),
        'best': min(current_results, key=lambda x: x['price'])
    }

    # Graph Data Prep
    dates = sorted(list(set(row['created_at'].strftime('%Y-%m-%d') for row in history)))
    datasets = []
    colors = {'Naivas': '#ef4444', 'Jumia': '#f97316', 'Carrefour': '#3b82f6'}
    for source in ['Naivas', 'Jumia', 'Carrefour']:
        source_data = [d for d in history if d['source'] == source]
        price_map = {d['created_at'].strftime('%Y-%m-%d'): d['price'] for d in source_data}
        data_points = [price_map.get(date, None) for date in dates]
        if any(p is not None for p in data_points):
            datasets.append({
                'label': source, 'data': data_points,
                'borderColor': colors.get(source, '#ccc'),
                'backgroundColor': colors.get(source, '#ccc'),
                'fill': False, 'tension': 0.1
            })

    graph_data = {'labels': dates, 'datasets': datasets}
    return render_template('search_result.html', query=query, items=current_results, stats=stats, graph=graph_data)

# --- PROTECTED USER FEATURES ---

@app.route('/api/subscribe', methods=['POST'])
@login_required # Must be logged in to subscribe
def subscribe_alert():
    data = request.json
    item_name = data.get('item_name')
    target_price = data.get('target_price')
    
    db.alerts.update_one(
        {"item_name": item_name, "user_id": current_user.id}, # Link to specific user
        {"$set": {"target_price": float(target_price), "active": True, "created_at": datetime.utcnow()}},
        upsert=True
    )
    return jsonify({'status': 'success', 'message': 'Alert set!'})

@app.route('/profile')
@login_required
def profile():
    # Fetch ONLY this user's alerts
    my_alerts = list(db.alerts.find({"user_id": current_user.id, "active": True}))
    notifications = []
    watching = []

    for alert in my_alerts:
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

    return render_template('notifications.html', user=current_user, notifications=notifications, watching=watching)

@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    # Only Sellers can access
    if current_user.role != 'seller':
        flash("Access Denied. Only Sellers can manage inventory.", "error")
        return redirect(url_for('profile'))

    if request.method == 'POST':
        db.inventory.insert_one({
            "user_id": current_user.id, # Link to this seller
            "name": request.form.get('name'),
            "quantity": int(request.form.get('quantity')),
            "price": float(request.form.get('price')),
            "date_added": datetime.utcnow()
        })
        return redirect(url_for('inventory'))

    items = list(db.inventory.find({"user_id": current_user.id}).sort("date_added", -1))
    return render_template('inventory.html', items=items)

@app.route('/api/details/<comm_name>')
def get_item_details(comm_name):
    
    data = list(db.scrapped_items.find({"commodity_name": comm_name}).sort("created_at", 1))
    if not data: return jsonify({'error': 'No data'})
    for doc in data: doc['_id'] = str(doc['_id']) # Fix ObjectId error
    
    dates = sorted(list(set(row['created_at'].strftime('%Y-%m-%d') for row in data)))
    datasets = {}
    colors = {'Naivas': '#ef4444', 'Jumia': '#f97316', 'Carrefour': '#3b82f6'}
    for source in ["Naivas", "Jumia", "Carrefour"]:
        prices = []
        source_data = {d['created_at'].strftime('%Y-%m-%d'): d['price'] for d in data if d['source'] == source}
        for date in dates: prices.append(source_data.get(date, None))
        datasets[source] = {'label': source, 'data': prices, 'borderColor': colors.get(source, '#ccc'), 'backgroundColor': colors.get(source, '#ccc')}

    return jsonify({'graph': {'labels': dates, 'datasets': list(datasets.values())}, 'sources': data[-15:]})

if __name__ == '__main__':
    app.run(debug=True, port=5000)