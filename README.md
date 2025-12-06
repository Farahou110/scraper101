# 🥬 AI-Powered Commodity Price Tracker

**This is a smart market dashboard that tracks and compares real-time food prices across major Kenyan supermarkets (Naivas, Jumia, ).

Unlike traditional scrapers that break when websites change, this project uses **Selenium** for navigation and **Google Gemini AI** to intelligently read and extract product data from the screen, making it highly robust and low-maintenance.

![Dashboard Screenshot](https://via.placeholder.com/800x400?text=Chakula+Bei+Dashboard)

## ✨ Features

- **🤖 AI-Powered Scraping:** Uses Google Gemini 1.5/2.5 Flash to "read" websites like a human, extracting product names, prices, and units even if HTML structures change.
- **📊 Comparative Dashboard:** View average prices, price ranges (min/max), and trends across different retailers.
- **📈 Interactive Charts:** Click any item to see a multi-line history graph comparing specific vendors (e.g., Naivas vs. Jumia) over time.
- **🌓 Dark Mode:** Fully responsive UI with a built-in dark/light theme toggle.
- **🔍 Category-Based Navigation:** Browse items by categories like Food, Electronics, and Machinery.
- **🛒 Multi-Source:** Currently configured to track **Naivas** and **Jumia**, with structure ready for Carrefour, Quickmart, and Chandarana.

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Database:** MongoDB (NoSQL for flexible schema)
- **AI Engine:** Google Gemini API (Generative AI)
- **Scraper:** Selenium WebDriver (Headless Chrome)
- **Frontend:** HTML5, Tailwind CSS, Chart.js

## 🚀 Prerequisites

Before you begin, ensure you have:
1.  **Python 3.8+** installed.
2.  **Google Chrome** installed (for the scraper).
3.  A **MongoDB Connection String** (Local `mongodb://localhost:27017` or MongoDB Atlas).
4.  A **Google Gemini API Key** (Get one for free at [Google AI Studio](https://aistudio.google.com/)).

## 📦 Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/yourusername/chakula-bei.git](https://github.com/yourusername/chakula-bei.git)
    cd chakula-bei
    ```

2.  **Create a Virtual Environment**
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

4.  **Configure Environment Variables**
    Create a `.env` file in the root directory and add your keys:
    ```env
    # Database (Use your local or cloud URI)
    MONGO_URI=mongodb://localhost:27017/commodity_price_tracker

    # AI Key for Scraping
    GEMINI_API_KEY=your_actual_gemini_api_key_here
    ```

## 🏃‍♂️ Running the Application

1.  **Start the Flask Server**
    ```bash
    python app.py
    ```

2.  **Access the Dashboard**
    Open your browser and go to: `http://localhost:8080`

3.  **Populate Data**
    - The dashboard will be empty initially.
    - Click the **"Run AI Scraper ✨"** button in the top right navigation.
    - *Note: The scraper takes about 1-2 minutes to browse the sites and analyze data with AI. Check your terminal for progress logs.*

