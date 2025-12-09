import time
import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# --- CONFIGURATION ---
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Use the model available to your account
    model = genai.GenerativeModel('gemini-2.5-flash')

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def ask_gemini(page_text, item_name, supermarket):
    print(f"🤖 Gemini is scanning {supermarket} for '{item_name}'...")
    
    # UPDATED PROMPT: Asks for a LIST of items
    prompt = f"""
    I have text from the {supermarket} website search results for "{item_name}".
    Find ALL products that match the user's search query, specifically matching the name and quantity/unit if specified.
    
    Return ONLY a JSON object with a key "items" containing a list of matching products.
    
    Each item in the list must have:
    - "product_name": The full specific name (e.g. "Festive Bread 600g")
    - "price": The numeric price (e.g. 65)
    - "description": Short description
    - "unit": Estimate the unit (e.g. "600g")
    - "location": "{supermarket}"
    
    RULES:
    1. Include multiple brands if they match the search (e.g. if searching "Bread 600g", return Festive, Supaloaf, Broadways).
    2. Ignore ads or unrelated items (e.g. ignore "400g" if searching for "600g" unless it's the only option).
    3. Limit to the top 5 most relevant matches.
    4. If nothing found, return an empty list for "items".
    
    PAGE TEXT:
    {page_text[:25000]}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        print(f"⚠️ Gemini Error: {e}")
        return {"items": []}

def process_site_search(driver, db, search_term, source, url_template, collection_name='live_searches'):
    """Helper to scrape a single site"""
    try:
        # URL ENCODING: Replace spaces with + or %20 based on site
        if source == "Naivas":
            query = search_term.replace(" ", "+")
        else:
            query = search_term.replace(" ", "%20")
            
        url = url_template.format(query=query)
        print(f"[{source}] Visiting: {url}")
        
        driver.get(url)
        time.sleep(5) # Wait for JS to load results
        
        body = driver.find_element("tag name", "body").text
        data = ask_gemini(body, search_term, source)
        
        saved_count = 0
        
        # Loop through the list of items found
        if data and 'items' in data and isinstance(data['items'], list):
            for item in data['items']:
                if item.get('product_name') != "N/A" and item.get('price', 0) > 0:
                    record = {
                        'search_term': search_term, 
                        'commodity_name': search_term,
                        'product_name': item['product_name'],
                        'price': float(item['price']),
                        'source': source,
                        'category': 'General',
                        'description': item.get('description', ''),
                        'unit': item.get('unit', 'Unit'),
                        'created_at': datetime.utcnow()
                    }
                    db[collection_name].insert_one(record)
                    print(f"✅ FOUND: {source} | {item['product_name']} @ {item['price']}")
                    saved_count += 1
        
        if saved_count > 0:
            return True
        else:
            print(f"⚠️ {source}: No match for {search_term}")
            
    except Exception as e:
        print(f"❌ Failed {source}: {e}")
    return False

def scrape_single_item(db, search_term, targets=None):
    """LIVE SEARCH: Scrapes a specific item on demand."""
    driver = get_driver()
    results_count = 0
    
    if not targets:
        targets = ['Naivas', 'Jumia', 'Carrefour']   
    
    try:
        # 1. Naivas (Updated URL)
        if 'Naivas' in targets:
            if process_site_search(driver, db, search_term, "Naivas", "https://naivas.online/search?term={query}"): 
                results_count += 1
        
        # 2. Jumia (Standard URL)
        if 'Jumia' in targets:
            if process_site_search(driver, db, search_term, "Jumia", "https://www.jumia.co.ke/catalog/?q={query}"): 
                results_count += 1
        
        # 3. Carrefour (Updated URL)
        if 'Carrefour' in targets:
            if process_site_search(driver, db, search_term, "Carrefour", "https://www.carrefour.ke/mafken/en/search?keyword={query}"): 
                results_count += 1
                
    finally:
        driver.quit()
        
    return results_count

def scrape_real_data(db):
    """DASHBOARD UPDATE: Scrapes fixed list from ALL supermarkets."""
    driver = get_driver()
    
    commodities = [
        {'name': 'Fresh Milk 500ml', 'category': 'Food'},
        {'name': 'Sugar 1kg', 'category': 'Food'},
        {'name': 'Maize Meal 2kg', 'category': 'Food'},
        {'name': 'Wheat Flour 2kg', 'category': 'Food'},
    #     {'name': 'Cooking Oil 1L', 'category': 'Food'},
    #     {'name': 'Rice 2kg', 'category': 'Food'},
    #     {'name': 'White Bread 600g', 'category': 'Food'}, 
    #     {'name': 'Table Salt 1kg', 'category': 'Food'},
    #     {'name': 'Toilet Paper 4 Pack', 'category': 'Home'},
    #     {'name': 'Bathing Soap', 'category': 'Home'},
    #     {'name': 'Toothpaste', 'category': 'Home'}
                ]
    
    count = 0
    try:
        for item in commodities:
            search_term = item['name']
            
            # 1. Naivas
            if process_site_search(driver, db, search_term, "Naivas", "https://naivas.online/search?term={query}", 'scrapped_items'): count += 1
            
            # 2. Jumia
            if process_site_search(driver, db, search_term, "Jumia", "https://www.jumia.co.ke/catalog/?q={query}", 'scrapped_items'): count += 1
            
            # 3. Carrefour
            if process_site_search(driver, db, search_term, "Carrefour", "https://www.carrefour.ke/mafken/en/search?keyword={query}", 'scrapped_items'): count += 1
            
            time.sleep(3)
    finally:
        driver.quit()
    return count