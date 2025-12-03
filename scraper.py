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

# Setup
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def ask_gemini(page_text, search_term, supermarket):
    print(f"🤖 Analyzing {supermarket} for '{search_term}'...")
    
    prompt = f"""
    I have search results from {supermarket} for "{search_term}".
    Find the product that BEST matches both the NAME and the SIZE/UNIT.
    
    Return JSON:
    - "product_name": Full name found (e.g. "Kabras Sugar 1kg")
    - "price": Number only (e.g. 200)
    - "description": Short detail
    
    If no exact match for the size/unit is found, return "N/A" for product_name.
    
    PAGE TEXT:
    {page_text[:20000]}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception:
        return {"product_name": "N/A", "price": 0}

def scrape_real_data(db):
    driver = get_driver()
    
    # Updated List: Items + Specific Measures
    commodities = [
        # Food
        {'name': 'Sugar', 'unit': '1kg', 'category': 'Food'},
        {'name': 'Maize Meal', 'unit': '2kg', 'category': 'Food'},
        {'name': 'Wheat Flour', 'unit': '2kg', 'category': 'Food'},
        {'name': 'Cooking Oil', 'unit': '1L', 'category': 'Food'},
        {'name': 'Milk', 'unit': '500ml', 'category': 'Food'},
        {'name': 'Salt', 'unit': '1kg', 'category': 'Food'},
        # Electronics (Examples for testing)
        {'name': 'Extension Cable', 'unit': '4 way', 'category': 'Electronics'},
        {'name': 'Dry Iron', 'unit': 'Box', 'category': 'Electronics'},
        # Machinery/Hardware (Examples)
        {'name': 'Padlock', 'unit': 'Medium', 'category': 'Machinery'},
        {'name': 'Hammer', 'unit': 'Claw', 'category': 'Machinery'}
    ]
    
    count = 0
    try:
        for item in commodities:
            # Construct strict search term: Name + Unit
            search_term = f"{item['name']} {item['unit']}"
            
            # 1. Naivas
            process_site(driver, db, item, search_term, "Naivas", 
                        "https://naivas.online/search?q={query}")
            
            # 2. Jumia
            process_site(driver, db, item, search_term, "Jumia", 
                        "https://www.jumia.co.ke/catalog/?q={query}")
            
            count += 2
            time.sleep(3) # Rate limit pause

    finally:
        driver.quit()
    return count

def process_site(driver, db, item, search_term, source, url_template):
    try:
        driver.get(url_template.format(query=search_term))
        time.sleep(5)
        
        body = driver.find_element("tag name", "body").text
        data = ask_gemini(body, search_term, source)
        
        if data and data.get('product_name') != "N/A" and data.get('price') > 0:
            record = {
                'commodity_name': item['name'], # Grouping Name (e.g. Sugar)
                'product_name': data['product_name'], # Actual Name (e.g. Kabras Sugar 1kg)
                'price': float(data['price']),
                'source': source,
                'category': item['category'],
                'unit': item['unit'],
                'description': data.get('description', ''),
                'created_at': datetime.utcnow()
            }
            db.scrapped_items.insert_one(record)
            print(f"✅ SAVED: {source} - {data['product_name']} @ {data['price']}")
    except Exception as e:
        print(f"❌ Failed {source}: {e}")