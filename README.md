# 🥬 **AI-Powered Commodity Price Tracker**
This is an intelligent market intelligence platform that tracks and compares real-time commodity prices across major Kenyan retailers (**Naivas**, **Jumia**, **Carrefour**).

Unlike traditional scrapers, this system uses **Google Gemini AI** to "read" e-commerce websites like a human, ensuring high accuracy even when website layouts change. It provides live price comparisons, historical trend analysis, and personalized price alerts.



## ✨ Key Features

### 🔍 Live AI Search
- **On-Demand Scraping:** Search for *any* item (e.g., "Cooking Oil 3L"), and the AI agent will instantly visit multiple supermarkets to find the current price.
- **Smart Matching:** Gemini AI filters out irrelevant results and standardizes product names (e.g., matching "Fresh Fri" across different stores).

### 📊 Comparative Analytics
- **Multi-Store Graphing:** Visualize price history on an interactive **Line Chart**, comparing retailers side-by-side to spot trends.
- **Best Deal Highlighter:** The dashboard automatically calculates the average market price and flags the cheapest retailer for every item.

### 🔔 Smart Notifications
- **Price Watch:** Click the **Bell Icon** on any product to set a "Target Price."
- **Alerts:** The system monitors prices and notifies you (via the Profile page) as soon as an item drops below your target.

### 📦 Seller Inventory
- A dedicated module for retailers to digitally manage their stock levels, unit prices, and total asset value.

### 🎨 Modern UI
- **Dark Mode:** Fully supported dark/light theme toggle.
- **Responsive:** Built with Tailwind CSS for a seamless experience on mobile and desktop.

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Database:** MongoDB (NoSQL)
- **AI Engine:** Google Gemini 2.5 Flash
- **Scraper:** Selenium WebDriver (Headless Chrome)
- **Frontend:** HTML5, Jinja2, Tailwind CSS, Chart.js

---

## 🚀 Getting Started

### Prerequisites
1.  **Python 3.10+** installed.
2.  **Google Chrome** browser installed (for Selenium).
3.  A **MongoDB Connection String** (Local or Atlas).
4.  A **Google Gemini API Key** (Get it at [Google AI Studio](https://aistudio.google.com/)).

### Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/Farahou110/scraper101.git]
    
    ```

2.  **Create Virtual Environment**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Create a `.env` file in the root folder:
    ```env
    MONGO_URI=mongodb://localhost:27017/
    GEMINI_API_KEY=your_gemini_api_key_here
    ```

### Running the App

1.  **Start the Server**
    ```bash
    python app.py
    ```
2.  **Open in Browser**
    Visit: `http://localhost:8080`

---

## 📂 Project Structure

```text
chakula-flask/
├── app.py                 # Main Flask application & Routes
├── scraper.py             # Selenium + Gemini AI scraping logic
├── requirements.txt       # Project dependencies
├── .env                   # Configuration secrets
├── static/
│   ├── css/
│   │   └── style.css      # Custom styles & Tailwind imports
│   └── js/
│       └── main.js        # Chart logic & Notification handling
└── templates/
    ├── base.html          # Main layout (Nav, Footer, Theme)
    ├── home.html          # Landing page
    ├── dashboard.html     # Category view & item cards
    ├── check_item.html    # Search input page
    ├── search_result.html # Live scrape results & graph
    ├── notifications.html # User profile & alerts
    ├── inventory.html     # Seller stock management
    └── categories.html    # Category selection hub
