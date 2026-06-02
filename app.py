from flask import Flask, jsonify, render_template, request, session
import yfinance as yf
import os
import random
import time
import sqlite3
import hashlib
import requests
import traceback
from datetime import datetime, timedelta
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
print(">>> APP IMPORTED SUCCESSFULLY")

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tradelearn.db")
DB_INITIALIZED = False
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
NEWS_CACHE_TTL = 20 * 60
news_cache = {"timestamp": 0, "items": []}
MARKET_OVERVIEW_CACHE = {"timestamp": 0, "data": {}}
MARKET_CALENDAR_CACHE = {"timestamp": 0, "events": []}

def init_db():
    """Initialize SQLite database for users and quizzes."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            cash REAL DEFAULT 10000.00,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            streak INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            shares INTEGER NOT NULL,
            UNIQUE(user_id, ticker),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            action TEXT NOT NULL,
            shares INTEGER NOT NULL,
            price REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS learning_progress (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            chapter_id INTEGER NOT NULL,
            completed INTEGER DEFAULT 0,
            completed_at TIMESTAMP,
            UNIQUE(user_id, chapter_id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answer_selected TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            xp_earned INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            achievement_type TEXT NOT NULL,
            achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, achievement_type),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_challenges (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            challenge_type TEXT NOT NULL,
            target_value INTEGER NOT NULL,
            current_value INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            date DATE NOT NULL,
            xp_reward INTEGER NOT NULL,
            UNIQUE(user_id, challenge_type, date),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_streaks (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            streak_type TEXT NOT NULL,
            current_streak INTEGER DEFAULT 0,
            last_activity_date DATE,
            best_streak INTEGER DEFAULT 0,
            UNIQUE(user_id, streak_type),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            favorite INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            position_order INTEGER DEFAULT 0,
            UNIQUE(user_id, ticker),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            goal_type TEXT NOT NULL,
            title TEXT NOT NULL,
            target_value REAL NOT NULL,
            current_value REAL DEFAULT 0,
            unit TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE,
            theme TEXT DEFAULT 'dark',
            notifications INTEGER DEFAULT 1,
            email_updates INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

    migrate_watchlist_schema()

def migrate_watchlist_schema():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE watchlist ADD COLUMN category TEXT DEFAULT 'General'")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE watchlist ADD COLUMN favorite INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

user_state = {
    "cash": 10000.00,
    "portfolio": {},
    "trades": [],
    "xp": 0,
    "level": 1,
    "streak": 1,
    "last_login": datetime.now().isoformat(),
    "session_start": time.time()
}

ASSET_DATABASE = {
    "AAPL": {"base": 190, "volatility": 2.5, "name": "Apple Inc.", "sector": "Technology"},
    "TSLA": {"base": 240, "volatility": 4.0, "name": "Tesla Inc.", "sector": "Automotive"},
    "NVDA": {"base": 875, "volatility": 3.5, "name": "NVIDIA Corporation", "sector": "Technology"},
    "MSFT": {"base": 415, "volatility": 2.0, "name": "Microsoft Corporation", "sector": "Technology"},
    "GOOGL": {"base": 140, "volatility": 2.2, "name": "Alphabet Inc.", "sector": "Technology"},
    "AMZN": {"base": 185, "volatility": 2.8, "name": "Amazon.com Inc.", "sector": "E-commerce"},
    "META": {"base": 350, "volatility": 3.2, "name": "Meta Platforms Inc.", "sector": "Technology"},
    "AMD": {"base": 165, "volatility": 3.8, "name": "Advanced Micro Devices", "sector": "Technology"},
    "BTC": {"base": 42000, "volatility": 5.0, "name": "Bitcoin", "sector": "Cryptocurrency"},
    "ETH": {"base": 2250, "volatility": 4.5, "name": "Ethereum", "sector": "Cryptocurrency"},
    "SOL": {"base": 140, "volatility": 6.0, "name": "Solana", "sector": "Cryptocurrency"},
    "DOGE": {"base": 0.15, "volatility": 7.0, "name": "Dogecoin", "sector": "Cryptocurrency"}
}

SEARCH_MAPPING = {
    "apple": "AAPL",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "nvidia corp": "NVDA",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "amd": "AMD",
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "dogecoin": "DOGE",
    "doge": "DOGE"
}

INTEGRATE_LEARNING_CURRICULUM = [
    {
        "id": 1,
        "title": "Introduction to Stocks",
        "description": "Learn what stocks are and how they represent ownership in companies.",
        "content": "A stock is a share of ownership in a company. When you buy stock, you become a partial owner and can benefit from the company's growth.",
        "xp_reward": 50
    },
    {
        "id": 2,
        "title": "Market Orders",
        "description": "Understand how to place buy and sell orders in the stock market.",
        "content": "A market order is an instruction to buy or sell a security at the current market price. It executes immediately but at whatever price is available.",
        "xp_reward": 50
    },
    {
        "id": 3,
        "title": "Supply and Demand",
        "description": "Learn how supply and demand affect stock prices.",
        "content": "Stock prices move based on supply and demand. More buyers than sellers drives prices up; more sellers than buyers drives prices down.",
        "xp_reward": 50
    },
    {
        "id": 4,
        "title": "ETFs Explained",
        "description": "Discover what Exchange Traded Funds are and how they differ from individual stocks.",
        "content": "An ETF (Exchange Traded Fund) is a basket of securities (stocks, bonds, etc.) that trades like a single stock. ETFs offer instant diversification.",
        "xp_reward": 50
    },
    {
        "id": 5,
        "title": "Diversification",
        "description": "Understand why spreading investments across multiple assets reduces risk.",
        "content": "Diversification means not putting all your money in one asset. By owning multiple stocks and sectors, you reduce the impact of any single stock declining.",
        "xp_reward": 75
    },
    {
        "id": 6,
        "title": "Risk Management",
        "description": "Learn essential strategies to protect your investments.",
        "content": "Risk management includes setting position sizes, using stop-losses, and maintaining a cash reserve. Never invest money you can't afford to lose.",
        "xp_reward": 75
    },
    {
        "id": 7,
        "title": "Technical Analysis Basics",
        "description": "Introduction to reading and interpreting price charts.",
        "content": "Technical analysis uses historical price and volume data to predict future movements. Common patterns include support/resistance, trends, and reversals.",
        "xp_reward": 75
    },
    {
        "id": 8,
        "title": "Candlestick Charts",
        "description": "Learn to read candlestick chart patterns and what they reveal.",
        "content": "Candlesticks show open, high, low, and close prices for a time period. Green candles show upward movement; red shows downward movement.",
        "xp_reward": 75
    },
    {
        "id": 9,
        "title": "Trading Psychology",
        "description": "Master the mental aspects of successful trading and investing.",
        "content": "Trading psychology covers managing emotions like fear and greed. Successful traders stick to their strategy even during market volatility.",
        "xp_reward": 100
    },
    {
        "id": 10,
        "title": "Cryptocurrency Basics",
        "description": "Understand blockchain technology and how cryptocurrencies work.",
        "content": "Cryptocurrencies are digital assets secured by cryptography. Bitcoin was the first; thousands now exist. They operate independently of government or banks.",
        "xp_reward": 100
    },
    {
        "id": 11,
        "title": "Portfolio Rebalancing",
        "description": "Learn when and how to adjust your portfolio allocation.",
        "content": "Rebalancing means selling winners and buying losers to maintain your target allocation. This locks in profits and maintains risk levels.",
        "xp_reward": 75
    },
    {
        "id": 12,
        "title": "Reading Financial Statements",
        "description": "Analyze income statements, balance sheets, and cash flow statements.",
        "content": "Financial statements show a company's health. The P/E ratio, debt levels, and cash flow are key metrics to evaluate before investing.",
        "xp_reward": 100
    }
]

INTEGRATE_QUIZ_DATABASE = [
    {
        "id": 1,
        "category": "beginner",
        "question": "What is a stock?",
        "options": [
            "Ownership in a company",
            "A loan from a bank",
            "Cryptocurrency token",
            "Insurance contract"
        ],
        "correct": 0,
        "xp_reward": 25
    },
    {
        "id": 2,
        "category": "beginner",
        "question": "What does 'diversification' mean?",
        "options": [
            "Investing in one stock only",
            "Spreading investments across multiple assets",
            "Trading every day",
            "Buying at the lowest price only"
        ],
        "correct": 1,
        "xp_reward": 25
    },
    {
        "id": 3,
        "category": "beginner",
        "question": "What is a market order?",
        "options": [
            "Buy at a specific price limit",
            "Sell all shares at once",
            "Buy or sell immediately at current price",
            "Wait for price to change"
        ],
        "correct": 2,
        "xp_reward": 25
    },
    {
        "id": 4,
        "category": "intermediate",
        "question": "What does P/E ratio measure?",
        "options": [
            "Price divided by Earnings",
            "Profit per Employee",
            "Price per Equity share",
            "Percentage Equity"
        ],
        "correct": 0,
        "xp_reward": 50
    },
    {
        "id": 5,
        "category": "intermediate",
        "question": "What indicates a bear market?",
        "options": [
            "Prices rising 20% or more",
            "Prices falling 20% or more",
            "No price movement",
            "High trading volume only"
        ],
        "correct": 1,
        "xp_reward": 50
    },
    {
        "id": 6,
        "category": "trading",
        "question": "What is a stop-loss order?",
        "options": [
            "An order to buy more shares",
            "An order to sell if price falls to a level",
            "An order to hold shares forever",
            "A penalty for losing money"
        ],
        "correct": 1,
        "xp_reward": 50
    },
    {
        "id": 7,
        "category": "trading",
        "question": "What does 'going long' mean?",
        "options": [
            "Holding a position for a long time",
            "Buying stock and profiting if it rises",
            "Shorting and hoping for price drops",
            "Buying options on futures"
        ],
        "correct": 1,
        "xp_reward": 50
    },
    {
        "id": 8,
        "category": "crypto",
        "question": "What is blockchain?",
        "options": [
            "A bank account for crypto",
            "A distributed ledger technology",
            "An exchange for trading crypto",
            "A wallet for storing crypto"
        ],
        "correct": 1,
        "xp_reward": 50
    },
    {
        "id": 9,
        "category": "crypto",
        "question": "What was the first cryptocurrency?",
        "options": [
            "Ethereum",
            "Bitcoin",
            "Dogecoin",
            "Solana"
        ],
        "correct": 1,
        "xp_reward": 50
    }
]

price_history = {ticker: [] for ticker in ASSET_DATABASE}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_database():
    """Ensure the SQLite database and tables exist before the first request."""
    global DB_INITIALIZED
    if DB_INITIALIZED:
        return
    try:
        init_db()
        DB_INITIALIZED = True
    except Exception:
        traceback.print_exc()
        raise


@app.before_request
def before_request():
    ensure_database()


def create_user(username, email, password):
    password_hash = hash_password(password)
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, password_hash))
        conn.commit()
        user_id = c.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def find_user_by_username(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row


def find_user_by_id(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row


def verify_password(stored_hash, password_attempt):
    return stored_hash == hash_password(password_attempt)


def build_trade_history_from_rows(rows):
    history = []
    for row in rows:
        action = row.get("action", "")
        prefix = "Buy" if action == "buy" else "Sell"
        history.append(f"{prefix} {row.get('shares', 0)} {row.get('ticker')} @ ${float(row.get('price', 0)):.2f}")
    return history


def calculate_portfolio_from_trades(trades):
    holdings = {}
    for trade in trades:
        ticker = trade.get("ticker")
        if not ticker:
            continue

        action = trade.get("action")
        shares = int(trade.get("shares", 0))
        price = float(trade.get("price", 0))

        if action == "buy":
            current = holdings.get(ticker, {"shares": 0, "avgCost": 0.0})
            total_shares = current["shares"] + shares
            total_cost = (current["shares"] * current["avgCost"]) + (shares * price)
            holdings[ticker] = {
                "shares": total_shares,
                "avgCost": round(total_cost / total_shares, 2) if total_shares else 0.0
            }
        elif action == "sell":
            current = holdings.get(ticker)
            if not current:
                continue
            current["shares"] -= shares
            if current["shares"] <= 0:
                holdings.pop(ticker, None)
            else:
                holdings[ticker] = current
    return holdings


def load_user_state_from_db(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    user = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        conn.close()
        return None

    trades = c.execute(
        "SELECT ticker, action, shares, price, timestamp FROM trades WHERE user_id = ? ORDER BY timestamp ASC",
        (user_id,),
    ).fetchall()
    conn.close()

    holdings = calculate_portfolio_from_trades([dict(row) for row in trades])
    portfolio_value = round(sum(generate_realistic_price(ticker) * values["shares"] for ticker, values in holdings.items()), 2)

    return {
        "authenticated": True,
        "cash": round(float(user["cash"] or 0), 2),
        "portfolio": holdings,
        "xp": int(user["xp"] or 0),
        "level": int(user["level"] or 1),
        "streak": int(user["streak"] or 1),
        "tradeHistory": build_trade_history_from_rows([dict(row) for row in trades]),
        "portfolio_value": portfolio_value,
    }


def update_user_stats(user_id, cash=None, xp=None, level=None, streak=None):
    conn = get_db_connection()
    c = conn.cursor()

    updates = []
    params = []

    if cash is not None:
        updates.append("cash = ?")
        params.append(round(float(cash), 2))
    if xp is not None:
        updates.append("xp = ?")
        params.append(int(xp))
    if level is not None:
        updates.append("level = ?")
        params.append(int(level))
    if streak is not None:
        updates.append("streak = ?")
        params.append(int(streak))

    if not updates:
        conn.close()
        return

    params.append(user_id)
    c.execute(
        f"UPDATE users SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        params,
    )
    conn.commit()
    conn.close()


def sync_portfolio_rows(user_id, portfolio):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM portfolio WHERE user_id = ?", (user_id,))

    for ticker, position in portfolio.items():
        shares = int(position.get("shares", 0))
        if shares <= 0:
            continue
        c.execute(
            "INSERT INTO portfolio (user_id, ticker, shares) VALUES (?, ?, ?)",
            (user_id, ticker, shares),
        )

    conn.commit()
    conn.close()


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return render_template("login.html", error="Please log in to continue.")
        return f(*args, **kwargs)
    return decorated_function


def fuzzy_search(query):
    query_lower = query.lower().strip()

    if not query_lower:
        return []

    results = []
    query_upper = query.lower().upper()

    if query_upper in ASSET_DATABASE:
        results.append((query_upper, ASSET_DATABASE[query_upper]))
        return results

    if query_lower in SEARCH_MAPPING:
        ticker = SEARCH_MAPPING[query_lower]
        results.append((ticker, ASSET_DATABASE[ticker]))
        return results

    for search_key, ticker in SEARCH_MAPPING.items():
        if query_lower in search_key:
            results.append((ticker, ASSET_DATABASE[ticker]))

    for ticker, info in ASSET_DATABASE.items():
        if query_upper in ticker:
            results.append((ticker, info))

    for ticker, info in ASSET_DATABASE.items():
        if query_lower in info["name"].lower():
            results.append((ticker, info))

    seen = set()
    unique_results = []
    for item in results:
        ticker = item[0]
        if ticker not in seen:
            seen.add(ticker)
            unique_results.append(item)

    return unique_results[:10]


def get_asset_info(ticker):
    ticker = ticker.upper()
    return ASSET_DATABASE.get(ticker, {"base": 100, "volatility": 2.0, "name": ticker})


def generate_realistic_price(ticker):
    info = get_asset_info(ticker)
    base = info["base"]
    volatility = info["volatility"]
    change = random.gauss(0, volatility / 100 * base)
    price = base + change
    price = max(price, base * 0.8)
    return round(price, 2)


def generate_chart_data(ticker, points=25):
    info = get_asset_info(ticker)
    base = info["base"]
    volatility = info["volatility"]
    data = []
    current = base
    for _ in range(points):
        current += random.gauss(0, volatility / 10)
        current = max(current, base * 0.7)
        data.append(round(current, 2))
    return data


def calculate_portfolio_value():
    total = 0
    for ticker, shares in user_state["portfolio"].items():
        price = generate_realistic_price(ticker)
        total += price * shares
    return round(total, 2)


def safe_json_response(data, status_code=200):
    try:
        return jsonify(data), status_code
    except Exception:
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500

def fetch_external_market_news():
    now = time.time()
    if news_cache["items"] and now - news_cache["timestamp"] < NEWS_CACHE_TTL:
        return news_cache["items"]

    news_items = []
    if NEWS_API_KEY:
        try:
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": "stocks OR ETFs OR technology OR AI OR economy OR markets OR cryptocurrency",
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 20,
                    "apiKey": NEWS_API_KEY,
                },
                timeout=12,
            )
            payload = response.json()
            if payload.get("status") == "ok":
                for article in payload.get("articles", []):
                    if not article.get("title"):
                        continue
                    news_items.append({
                        "title": article.get("title"),
                        "summary": article.get("description") or article.get("content") or "Latest market news and themes.",
                        "source": article.get("source", {}).get("name", "News"),
                        "timestamp": article.get("publishedAt", ""),
                        "url": article.get("url", "#"),
                        "image": article.get("urlToImage") or "https://via.placeholder.com/400x240?text=Market+News",
                    })
        except Exception:
            news_items = []

    if not news_items:
        news_items = [
            {
                "title": "Tech Stocks Rally as AI Demand Surges",
                "summary": "Major technology companies see significant gains as artificial intelligence adoption accelerates across industries.",
                "source": "MarketWatch",
                "timestamp": "2 hours ago",
                "url": "#",
                "image": "https://via.placeholder.com/400x240?text=AI+Rally"
            },
            {
                "title": "Federal Reserve Signals Rate Pause",
                "summary": "The Fed indicates it may hold interest rates steady in upcoming meetings amid cooling inflation data.",
                "source": "Reuters",
                "timestamp": "4 hours ago",
                "url": "#",
                "image": "https://via.placeholder.com/400x240?text=Fed+Update"
            },
            {
                "title": "Electric Vehicle Sales Hit Record High",
                "summary": "EV manufacturers report strong quarterly sales as consumer adoption continues to grow globally.",
                "source": "Bloomberg",
                "timestamp": "6 hours ago",
                "url": "#",
                "image": "https://via.placeholder.com/400x240?text=EV+Growth"
            },
        ]

    news_cache["items"] = news_items
    news_cache["timestamp"] = now
    return news_items

def fetch_market_overview_data():
    now = time.time()
    if MARKET_OVERVIEW_CACHE["data"] and now - MARKET_OVERVIEW_CACHE["timestamp"] < 120:
        return MARKET_OVERVIEW_CACHE["data"]

    overview = []
    indices = {
        "SPY": "S&P 500",
        "QQQ": "Nasdaq 100",
        "DIA": "Dow Jones",
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum"
    }
    for ticker, label in indices.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1d", interval="15m")
            if df.empty:
                df = stock.history(period="5d", interval="1h")
            price = round(df["Close"].iloc[-1], 2)
            prev = float(df["Close"].iloc[0]) if len(df) > 0 else price
            change = round((price - prev) / prev * 100, 2) if prev else 0
            overview.append({
                "ticker": ticker,
                "name": label,
                "price": price,
                "change": change,
                "trend": "up" if change >= 0 else "down"
            })
        except Exception:
            overview.append({
                "ticker": ticker,
                "name": label,
                "price": round(random.uniform(100, 500), 2),
                "change": round(random.uniform(-2.5, 2.5), 2),
                "trend": "up"
            })

    MARKET_OVERVIEW_CACHE["data"] = overview
    MARKET_OVERVIEW_CACHE["timestamp"] = now
    return overview

def fetch_market_insights_data():
    sectors = {}
    for ticker, info in ASSET_DATABASE.items():
        sector = info.get("sector", "General")
        sectors.setdefault(sector, []).append(generate_realistic_price(ticker))

    sector_performance = []
    for sector, values in sectors.items():
        avg = sum(values) / len(values)
        sector_performance.append({
            "sector": sector,
            "performance": round((avg / (avg * 0.98) - 1) * 100, 2)
        })

    insights = {
        "fear_and_greed": {
            "score": random.randint(25, 75),
            "signal": random.choice(["Neutral", "Greed", "Fear"])
        },
        "market_sentiment": random.choice(["Bullish", "Mixed", "Cautious"]),
        "volatility_index": round(random.uniform(12, 28), 2),
        "volume_analysis": {
            "average_volume_change": round(random.uniform(-9, 12), 2),
            "active_sectors": random.sample(list(sectors.keys()), min(3, len(sectors)))
        },
        "sector_performance": sector_performance
    }
    return insights

def fetch_market_calendar_data():
    now = time.time()
    if MARKET_CALENDAR_CACHE["events"] and now - MARKET_CALENDAR_CACHE["timestamp"] < 300:
        return MARKET_CALENDAR_CACHE["events"]

    base = datetime.now()
    events = []
    sample_events = [
        ("Earnings Report", "AAPL"),
        ("Federal CPI Release", "Economy"),
        ("ETF Rebalance Announcement", "QQQ"),
        ("Cryptocurrency Regulation Update", "Crypto"),
        ("Tech Conference Keynote", "AI"),
        ("GDP Growth Estimate", "Economy")
    ]
    for i in range(6):
        event_name, symbol = sample_events[i % len(sample_events)]
        event_date = (base + timedelta(days=i + 1)).strftime("%b %d")
        events.append({
            "title": event_name,
            "symbol": symbol,
            "date": event_date,
            "description": f"Upcoming {event_name.lower()} for {symbol}.",
            "category": "Earnings" if "Earnings" in event_name else "Economic"
        })

    MARKET_CALENDAR_CACHE["events"] = events
    MARKET_CALENDAR_CACHE["timestamp"] = now
    return events

def get_user_settings(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    row = c.execute(
        "SELECT theme, notifications, email_updates FROM user_settings WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row:
        settings = {
            "theme": row["theme"],
            "notifications": bool(row["notifications"]),
            "email_updates": bool(row["email_updates"])
        }
        conn.close()
        return settings

    c.execute(
        "INSERT INTO user_settings (user_id, theme, notifications, email_updates) VALUES (?, ?, ?, ?)",
        (user_id, "dark", 1, 0),
    )
    conn.commit()
    conn.close()
    return {"theme": "dark", "notifications": True, "email_updates": False}

def save_user_settings(user_id, theme=None, notifications=None, email_updates=None):
    conn = get_db_connection()
    c = conn.cursor()
    row = c.execute("SELECT id FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()
    if not row:
        c.execute(
            "INSERT INTO user_settings (user_id, theme, notifications, email_updates) VALUES (?, ?, ?, ?)",
            (user_id, theme or "dark", int(bool(notifications)), int(bool(email_updates)))
        )
    else:
        updates = []
        params = []
        if theme is not None:
            updates.append("theme = ?")
            params.append(theme)
        if notifications is not None:
            updates.append("notifications = ?")
            params.append(int(bool(notifications)))
        if email_updates is not None:
            updates.append("email_updates = ?")
            params.append(int(bool(email_updates)))
        if updates:
            params.append(user_id)
            c.execute(f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?", params)
    conn.commit()
    conn.close()


def change_username(user_id, new_username):
    if not new_username:
        return False, "Username cannot be empty"
    existing = find_user_by_username(new_username)
    if existing and existing["id"] != user_id:
        return False, "Username already taken"
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET username = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_username, user_id),
    )
    conn.commit()
    conn.close()
    if session.get("user_id") == user_id:
        session["username"] = new_username
    return True, None


def change_password(user_id, current_password, new_password):
    if not new_password:
        return False, "Password cannot be empty"
    user = find_user_by_id(user_id)
    if not user or not verify_password(user["password_hash"], current_password):
        return False, "Current password is incorrect"
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (hash_password(new_password), user_id),
    )
    conn.commit()
    conn.close()
    return True, None


def reset_user_progress(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET cash = 10000.0, xp = 0, level = 1, streak = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (user_id,),
    )
    c.execute("DELETE FROM trades WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM portfolio WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def soft_delete_user_account(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    deleted_username = f"deleted_user_{user_id}"
    deleted_email = f"deleted_{user_id}@apexvest.local"
    c.execute(
        "UPDATE users SET username = ?, email = ?, password_hash = ?, cash = 0, xp = 0, level = 1, streak = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (deleted_username, deleted_email, hash_password("deleted"), user_id),
    )
    c.execute("DELETE FROM trades WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM portfolio WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_user_badges(user_id):
    achievements = get_user_achievements(user_id)
    badge_count = len(achievements)
    badges = [
        {"name": "Rising Learner", "description": "Completed your first lesson"},
        {"name": "Trader's Edge", "description": "Completed your first trade"}
    ]
    if badge_count >= 5:
        badges.append({"name": "Momentum Builder", "description": "Earned 5 achievements"})
    if badge_count >= 10:
        badges.append({"name": "Market Explorer", "description": "Collected 10 achievements"})
    if badge_count >= 20:
        badges.append({"name": "Portfolio Architect", "description": "Built a diversified portfolio"})
    return badges

FLASHCARDS = [
    {"front": "What does ETF stand for?", "back": "Exchange Traded Fund"},
    {"front": "What is a stop-loss order?", "back": "An order to sell if price falls to a certain level."},
    {"front": "Why diversify your portfolio?", "back": "To reduce risk from any one investment."},
    {"front": "What is market capitalization?", "back": "A company's share price multiplied by its number of shares."},
    {"front": "What is a bear market?", "back": "A market where prices are generally falling."},
    {"front": "What is a bull market?", "back": "A market where prices are generally rising."},
    {"front": "What is liquidity?", "back": "How quickly an asset can be bought or sold."},
    {"front": "What does volatility measure?", "back": "How much and how quickly prices move."},
    {"front": "What is fundamental analysis?", "back": "Evaluating a company by its financial statements and business model."},
    {"front": "What is technical analysis?", "back": "Using historical price and volume data to identify trends."}
]

def load_flashcards():
    return FLASHCARDS

LESSONS = [
    {
        "title": "What is investing?",
        "content": "Investing means using money today to build more money tomorrow. When you invest, you choose a plan so your money can grow over months and years instead of being spent right away.",
        "highlights": [
            "Investing is different from saving: saving keeps your money safe while investing helps it grow.",
            "Stocks represent ownership in a company, while ETFs are baskets of many stocks.",
            "The best investing goal is steady progress over time, not quick luck."
        ],
        "example": "Think about a company you already like. If that company grows over the next few years, your investment may also grow.",
        "challenge": "Pick one stock you're curious about and think why it might be a good long-term choice."
    },
    {
        "title": "Stocks vs ETFs",
        "content": "Stocks are pieces of one company, and ETFs are groups of stocks bundled together. ETFs can be easier for beginners because one investment gives you access to many companies.",
        "highlights": [
            "One stock can move up or down fast based on news about that company.",
            "An ETF spreads your money over several companies so one drop doesn't hurt as much.",
            "ETFs are useful when you want broad market exposure without choosing every stock yourself."
        ],
        "example": "Buying an ETF for technology can feel safer than buying just one tech stock, because it includes lots of companies.",
        "challenge": "Find one stock and one ETF that both include a company you use every day."
    },
    {
        "title": "Diversification",
        "content": "Diversification means spreading your investments across different companies, industries, or types of assets. It helps reduce the risk of losing a lot of money on one single investment.",
        "highlights": [
            "Putting all your cash in one stock is risky because that company's troubles affect your whole investment.",
            "A mix of industries can keep your portfolio steadier when one part of the market dips.",
            "Diversification is not a guarantee, but it helps protect your progress."
        ],
        "example": "If you have some money in a tech stock and some in a consumer goods ETF, one may rise while the other falls.",
        "challenge": "List three different kinds of companies or industries you could include in a beginner portfolio."
    },
    {
        "title": "Risk and reward",
        "content": "Investing always has risk. Some investments can grow quickly, but they can also drop quickly. The smartest investors balance risk with careful planning.",
        "highlights": [
            "Higher rewards usually come with higher risk.",
            "Stable companies usually offer smoother growth but slower gains.",
            "Think about your goals before choosing a risky or safe investment."
        ],
        "example": "A new startup might promise big gains, but a well-known brand can be easier to understand and handle.",
        "challenge": "Choose one high-risk idea and one lower-risk idea, then compare why each feels different to you."
    },
    {
        "title": "Long-term thinking",
        "content": "Successful investing is often about patience. Prices go up and down, but staying focused on your long-term target makes it easier to avoid reactionary trading.",
        "highlights": [
            "Short-term price swings are normal and do not always mean the investment is bad.",
            "Compound growth works best when you stay invested for years.",
            "Review your plan, but do not panic when the market moves."
        ],
        "example": "If you invest today and leave it alone, you can benefit from years of growth and reinvested gains.",
        "challenge": "Write down one long-term goal you want your virtual portfolio to reach."
    },
    {
        "title": "Building confidence",
        "content": "Practice makes investing easier. Use your virtual cash to test ideas, learn from mistakes, and build the skills you need before using real money.",
        "highlights": [
            "Every trade teaches you something, even if it does not make money.",
            "Track your decisions so you can review what worked and what did not.",
            "Good investing comes from learning and patience, not from guessing."
        ],
        "example": "Try buying a small number of shares and then check how the stock behaves over several days.",
        "challenge": "After your next trade, note why you bought or sold and what you want to learn from it."
    },
    {
        "title": "Understanding fees",
        "content": "Fees and costs can reduce your earnings. The less you pay in fees, the more of your gains you keep. Always be aware of the charges you may face.",
        "highlights": [
            "Some brokers charge commissions or small fees for trades.",
            "ETFs often have management fees that slowly reduce returns.",
            "Choosing low-cost investments helps more of your money stay invested."
        ],
        "example": "If two ETFs give the same growth but one has lower fees, the cheaper one keeps more profit in your pocket.",
        "challenge": "Look for one example of a low-cost ETF and one example of a higher-cost investment."
    },
    {
        "title": "Compound growth",
        "content": "Compound growth happens when earnings are reinvested and then generate their own earnings. Over time, this can make a small return become much bigger.",
        "highlights": [
            "Money grows faster when profits are reinvested.",
            "The longer you stay invested, the stronger compounding becomes.",
            "Small, steady gains add up more than a single big win."
        ],
        "example": "A $100 investment that grows by 5% each year becomes much larger after several years than just one quick gain.",
        "challenge": "Imagine today's virtual cash growing over 5 years and think how patience helps your total value."
    }
]

QUIZ = [
    {
        "q": "What does ETF stand for?",
        "opts": ["Exchange Traded Fund", "Electronic Tax Form", "Equity Transfer"],
        "answer": 0,
        "hint": "The first word is a common investing term for a market product.",
        "explanation": "ETF means Exchange Traded Fund. It is a basket of assets traded like a single stock. ETFs make it easier to own many companies at once."
    },
    {
        "q": "What is a bull market?",
        "opts": ["Zero trading volume", "Prices rising", "Prices falling"],
        "answer": 1,
        "hint": "Think of the animal that charges upward.",
        "explanation": "A bull market means prices are generally rising. It is a positive market environment where many investors feel confident."
    },
    {
        "q": "Why diversify your portfolio?",
        "opts": ["To avoid learning", "To lower risk", "To make taxes higher"],
        "answer": 1,
        "hint": "Diversify means spread your money around.",
        "explanation": "Diversifying spreads risk across different investments. That way, one company falling does not hurt your entire portfolio as much."
    },
    {
        "q": "What is a dividend?",
        "opts": ["A trading fee", "A type of loan", "A company payout to shareholders"],
        "answer": 2,
        "hint": "It is money paid back to owners of the company.",
        "explanation": "A dividend is a company payout to shareholders from profits. Some companies pay dividends regularly as a reward for owning their stock."
    },
    {
        "q": "What does market cap measure?",
        "opts": ["Daily profit", "Company size", "Broker fee"],
        "answer": 1,
        "hint": "It is based on share price times the number of shares.",
        "explanation": "Market cap measures company size by multiplying stock price by total shares outstanding. It helps compare companies by scale."
    },
    {
        "q": "Why is cash important in investing?",
        "opts": ["Because it always grows", "For chance and safety", "To avoid all risk"],
        "answer": 1,
        "hint": "Cash gives you flexibility and protection.",
        "explanation": "Cash is important because it helps you take opportunities and cover surprises without selling investments at the wrong time."
    },
    {
        "q": "What does portfolio mean?",
        "opts": ["A loan agreement", "A group of investments", "A bank account"],
        "answer": 1,
        "hint": "It is a collection of what you own.",
        "explanation": "A portfolio is a group of investments you own together. It shows your overall financial picture."
    },
    {
        "q": "What is a good investing habit?",
        "opts": ["Ignore fees", "Review performance regularly", "Trade every hour"],
        "answer": 1,
        "hint": "Smart investors check results without overtrading.",
        "explanation": "Reviewing performance regularly helps you understand what is working and what is not. It is better than trading too often."
    },
    {
        "q": "What is a stop-loss order?",
        "opts": ["A request to buy at a lower price", "A request to sell to limit losses", "A dividend payment"],
        "answer": 1,
        "hint": "It helps protect you from losing too much.",
        "explanation": "A stop-loss order is a sell request triggered at a certain price to limit losses. It is a risk-management tool."
    },
    {
        "q": "What is a blue-chip stock?",
        "opts": ["A small startup", "A large stable company", "A high-risk penny stock"],
        "answer": 1,
        "hint": "Think of established companies with a strong reputation.",
        "explanation": "A blue-chip stock is a large, stable company known for reliable performance. These stocks are often less risky than smaller companies."
    },
    {
        "q": "What does a broker do?",
        "opts": ["Provides investment advice and executes trades", "Insures your portfolio", "Guarantees returns"],
        "answer": 0,
        "hint": "A broker helps you buy and sell investments.",
        "explanation": "A broker executes trades for investors and may offer guidance. They do not guarantee returns or insure your portfolio."
    },
    {
        "q": "Why keep an emergency fund?",
        "opts": ["To pay for surprises without selling investments", "To spend more on trading", "To avoid taxes"],
        "answer": 0,
        "hint": "It helps you handle unexpected costs safely.",
        "explanation": "An emergency fund keeps you from selling investments at a bad time when unexpected expenses happen. It provides financial safety."
    },
    {
        "q": "Which action helps compound growth?",
        "opts": ["Withdraw dividends immediately", "Reinvest earnings", "Only trade during market peaks"],
        "answer": 1,
        "hint": "Compound growth works when you let earnings stay invested.",
        "explanation": "Reinvesting earnings helps compound growth because your money earns on top of itself over time."
    },
    {
        "q": "What is a bear market?",
        "opts": ["Prices rising quickly", "Prices falling steadily", "No companies are trading"],
        "answer": 1,
        "hint": "Think of the opposite of a bull market.",
        "explanation": "A bear market means prices are falling steadily. It often happens when investors are worried about the economy."
    },
    {
        "q": "What is an index fund?",
        "opts": ["A fund that follows a market index", "A bank savings account", "A type of loan"],
        "answer": 0,
        "hint": "It tracks a group of companies, not one.",
        "explanation": "An index fund invests in many companies that match a market index. It is a passive way to track broad market performance."
    },
    {
        "q": "What does liquidity mean?",
        "opts": ["How quickly you can buy or sell", "How expensive an investment is", "How popular a company is"],
        "answer": 0,
        "hint": "Liquid means easy to move.",
        "explanation": "Liquidity is how quickly an asset can be bought or sold without changing its price too much. Cash and large stocks are usually more liquid."
    },
    {
        "q": "What is volatility?",
        "opts": ["How often prices change", "A company’s size", "A type of stock"],
        "answer": 0,
        "hint": "It measures ups and downs.",
        "explanation": "Volatility describes how much and how quickly prices move up and down. High volatility means bigger swings."
    },
    {
        "q": "What is an expense ratio?",
        "opts": ["The yearly cost of owning a fund", "The amount of profit made", "The fee to buy a stock"],
        "answer": 0,
        "hint": "It is a percentage charged by a fund.",
        "explanation": "Expense ratio is the annual cost to manage a fund, such as an ETF. Lower expense ratios keep more money working for you."
    },
    {
        "q": "What is an IPO?",
        "opts": ["When a company sells stock to the public for the first time", "When a company pays a dividend", "When a stock is split"],
        "answer": 0,
        "hint": "It is the first time shares are offered.",
        "explanation": "IPO stands for Initial Public Offering. It is when a private company becomes public by selling stock to investors."
    },
    {
        "q": "What does a stock split do?",
        "opts": ["Increases the number of shares while reducing price per share", "Doubles investor returns", "Removes a company from the market"],
        "answer": 0,
        "hint": "Share count goes up but value stays similar.",
        "explanation": "A stock split increases the number of shares and lowers the price per share. The company’s total value stays the same."
    },
    {
        "q": "What is a market order?",
        "opts": ["Buy or sell immediately at current price", "Buy at a specific lower price", "Sell only after one week"],
        "answer": 0,
        "hint": "It happens right away.",
        "explanation": "A market order buys or sells a stock immediately at the current price. It is useful when execution speed matters."
    },
    {
        "q": "What is a limit order?",
        "opts": ["Trade only if the price reaches a set level", "Trade immediately at any price", "Avoid trading fees"],
        "answer": 0,
        "hint": "You choose the price you want.",
        "explanation": "A limit order buys or sells only at a specific price or better. It gives you more price control than a market order."
    },
    {
        "q": "Why is long-term thinking important?",
        "opts": ["It helps ignore short-term ups and downs", "It ensures instant profit", "It avoids saving money"],
        "answer": 0,
        "hint": "Investing is not a sprint.",
        "explanation": "Long-term thinking helps investors stay focused through market swings. It lets compound growth work and reduces the impact of short-term volatility."
    },
    {
        "q": "Why should you track your investments?",
        "opts": ["To understand what is working", "To avoid taxes", "To spend more money"],
        "answer": 0,
        "hint": "Learning is part of investing.",
        "explanation": "Tracking helps you see which investments are doing well and which need review. It supports smarter decision-making."
    },
    {
        "q": "What is an asset allocation?",
        "opts": ["Distributing money across stocks, bonds, and cash", "Buying a single stock", "Saving in a piggy bank"],
        "answer": 0,
        "hint": "It means choosing different asset types.",
        "explanation": "Asset allocation means spreading money across different investment types. It helps balance risk and return."
    },
    {
        "q": "What does P/E ratio measure?",
        "opts": ["Company price relative to earnings", "Daily share volume", "Annual dividend amount"],
        "answer": 0,
        "hint": "P/E compares price and profits.",
        "explanation": "P/E ratio shows how much investors pay for each dollar of earnings. It can help compare company value."
    },
    {
        "q": "What is dollar-cost averaging?",
        "opts": ["Investing the same amount regularly", "Buying only when prices drop", "Selling every month"],
        "answer": 0,
        "hint": "It spreads buying over time.",
        "explanation": "Dollar-cost averaging means investing a fixed amount on a schedule. It reduces the risk of buying all at once."
    },
    {
        "q": "What is a bond?",
        "opts": ["A loan to a company or government", "A type of stock", "A bank account feature"],
        "answer": 0,
        "hint": "It pays interest.",
        "explanation": "A bond is a loan investors give to companies or governments. They receive interest and return of principal later."
    },
    {
        "q": "What is dividend yield?",
        "opts": ["Dividends divided by share price", "The number of shares owned", "The amount of cash in your account"],
        "answer": 0,
        "hint": "It shows income relative to price.",
        "explanation": "Dividend yield is the annual dividend payment divided by the stock price. It helps compare income from different stocks."
    },
    {
        "q": "Why is an emergency fund not the same as investments?",
        "opts": ["It is for short-term needs, not growth", "It always pays more interest", "It guarantees higher returns"],
        "answer": 0,
        "hint": "Emergency money is safety money.",
        "explanation": "An emergency fund is cash kept safe for surprises. Investments are meant for long-term growth, not immediate spending."
    },
    {
        "q": "What is rebalancing?",
        "opts": ["Adjusting your holdings to keep a target mix", "Buying as many stocks as possible", "Holding only one investment"],
        "answer": 0,
        "hint": "It keeps your portfolio balanced.",
        "explanation": "Rebalancing means selling some investments and buying others to restore your planned allocation. It helps manage risk."
    },
    {
        "q": "What is a penny stock?",
        "opts": ["A low-priced, high-risk stock", "A share of a major company", "A type of government bond"],
        "answer": 0,
        "hint": "It is cheap but risky.",
        "explanation": "A penny stock is a very low-priced stock that often has high risk and low liquidity. It is usually not a good choice for beginners."
    },
    {
        "q": "What is a blue-chip company known for?",
        "opts": ["Stability and reputation", "Fast growth only", "No dividends"],
        "answer": 0,
        "hint": "It is often large and trusted.",
        "explanation": "A blue-chip company is known for stability, strong performance, and a solid reputation. It is often a reliable long-term investment."
    },
    {
        "q": "Why should you avoid trading too often?",
        "opts": ["Because frequent trades can hurt returns", "Because it is illegal", "Because it always guarantees loss"],
        "answer": 0,
        "hint": "More trades mean more costs.",
        "explanation": "Trading too often can increase fees and taxes, and it is hard to beat the market with constant trades. Patience can help returns."
    },
    {
        "q": "What is a company’s sector?",
        "opts": ["The industry group it belongs to", "The stock price range", "The number of shareholders"],
        "answer": 0,
        "hint": "It describes the company’s business type.",
        "explanation": "A sector is the part of the economy a company operates in, like technology, healthcare, or consumer goods."
    },
    {
        "q": "What is a financial goal?",
        "opts": ["A specific target for your money", "A type of investment fee", "A stock trading strategy"],
        "answer": 0,
        "hint": "It is what you are saving or investing for.",
        "explanation": "A financial goal is a clear target like saving for college, a car, or a future retirement. Goals help guide investing decisions."
    },
    {
        "q": "How does inflation affect money?",
        "opts": ["It reduces buying power over time", "It makes money worth more", "It only affects banks"],
        "answer": 0,
        "hint": "Prices generally rise.",
        "explanation": "Inflation means prices go up, so the same amount of money buys less over time. Investing can help protect against inflation."
    },
    {
        "q": "What is a profit target?",
        "opts": ["A price at which you plan to sell for gain", "The cost of buying a stock", "A fee paid to brokers"],
        "answer": 0,
        "hint": "It is a selling goal.",
        "explanation": "A profit target is the price at which you plan to sell an investment to take gains. It helps make decisions more disciplined."
    },
    {
        "q": "What does holding period mean?",
        "opts": ["How long you keep an investment", "The number of shares you own", "The date you buy a stock"],
        "answer": 0,
        "hint": "It is the time you hold a position.",
        "explanation": "The holding period is how long you keep an investment before selling it. Longer periods often reduce short-term risk."
    },
    {
        "q": "What is a market index?",
        "opts": ["A benchmark of many stocks", "A single stock company", "A type of savings account"],
        "answer": 0,
        "hint": "It tracks the market.",
        "explanation": "A market index measures the performance of a group of stocks, like the S&P 500 or Nasdaq. Investors use it to compare results."
    },
    {
        "q": "What is active investing?",
        "opts": ["Picking investments yourself", "Buying only index funds", "Holding cash forever"],
        "answer": 0,
        "hint": "You make decisions directly.",
        "explanation": "Active investing means choosing individual stocks or funds based on research. It can offer opportunity but often requires more effort."
    },
    {
        "q": "What is passive investing?",
        "opts": ["Following a market index", "Trading every day", "Borrowing to buy more stocks"],
        "answer": 0,
        "hint": "It is a hands-off approach.",
        "explanation": "Passive investing means buying index funds or ETFs that track the market. It usually costs less and is easier to maintain."
    },
    {
        "q": "What is a management fee?",
        "opts": ["The cost of running a fund", "A penalty for selling stocks", "A reward for investors"],
        "answer": 0,
        "hint": "Funds charge it to manage your money.",
        "explanation": "A management fee is the yearly cost charged by fund managers. Lower fees mean more of your investment stays in the account."
    },
    {
        "q": "Why research a company before buying its stock?",
        "opts": ["To understand its business and risks", "To avoid using the internet", "To pay more fees"],
        "answer": 0,
        "hint": "Knowing the company helps you decide.",
        "explanation": "Research helps you understand whether a company is healthy, growing, and worth investing in. It reduces the chances of bad surprises."
    },
    {
        "q": "What is a safe investing mindset?",
        "opts": ["Focus on learning and long-term habits", "Expect quick riches", "Only trade when friends do"],
        "answer": 0,
        "hint": "It is calm and patient.",
        "explanation": "A safe investing mindset focuses on learning, planning, and staying patient rather than chasing fast wins."
    },
    {
        "q": "What is a stock quote?",
        "opts": ["The current price of a stock", "A company’s slogan", "A forecast of your profit"],
        "answer": 0,
        "hint": "It shows the latest price.",
        "explanation": "A stock quote is the current market price of a stock. It updates during trading hours."
    },
    {
        "q": "Why do people invest in ETFs?",
        "opts": ["Because they offer instant diversification", "Because they are free", "Because they guarantee no loss"],
        "answer": 0,
        "hint": "ETFs group many assets together.",
        "explanation": "People invest in ETFs because they can own many stocks or bonds at once, making diversification easier."
    },
    {
        "q": "What is portfolio value?",
        "opts": ["The total worth of all your investments", "The number of trades you made", "The fees you paid"],
        "answer": 0,
        "hint": "It is the sum of your holdings.",
        "explanation": "Portfolio value is the total amount your investments are worth at current prices."
    },
    {
        "q": "What is a trading fee?",
        "opts": ["A cost paid to buy or sell investments", "A type of dividend", "The investment return"],
        "answer": 0,
        "hint": "It is a transaction cost.",
        "explanation": "Trading fees are costs charged when buying or selling investments. Keeping fees low helps your returns."
    },
    {
        "q": "What is a cash reserve?",
        "opts": ["Money kept available for emergencies or opportunities", "Always invested money", "A loan from a bank"],
        "answer": 0,
        "hint": "It is your backup cash.",
        "explanation": "A cash reserve is money kept safe and available in case you need it quickly. It helps prevent selling investments at the wrong time."
    },
    {
        "q": "What is a goal timeline?",
        "opts": ["When you plan to reach a financial goal", "The hours the stock market is open", "A type of investment vehicle"],
        "answer": 0,
        "hint": "It puts a date on your goal.",
        "explanation": "A goal timeline is the schedule for when you want to reach a saving or investing target."
    },
    {
        "q": "What is learning from mistakes useful for?",
        "opts": ["Improving your future decisions", "Avoiding all risk forever", "Getting rich quickly"],
        "answer": 0,
        "hint": "Mistakes help you learn.",
        "explanation": "Learning from mistakes helps you make better investing choices over time."
    },
    {
        "q": "What is a reward banner in a quiz?",
        "opts": ["A message that celebrates a streak", "A type of dividend", "A stock price alert"],
        "answer": 0,
        "hint": "It appears when you do well.",
        "explanation": "A reward banner celebrates a successful streak or achievement in the quiz, making learning feel more fun."
    },
    {
        "q": "Which is the best first step for a beginner investor?",
        "opts": ["Learn the basics and start small", "Buy the most popular stock", "Ignore research"],
        "answer": 0,
        "hint": "Start with knowledge.",
        "explanation": "A good first step is learning the basics and investing small amounts while you build confidence."
    },
    {
        "q": "What does long-term planning help with?",
        "opts": ["Staying calm during market swings", "Making instant profits", "Avoiding taxes completely"],
        "answer": 0,
        "hint": "It helps you stay steady.",
        "explanation": "Long-term planning helps you stay calm during market ups and downs and focus on your goals."
    },
    {
        "q": "What is a company earnings report?",
        "opts": ["A summary of company profits and performance", "A request for a loan", "A type of investment fee"],
        "answer": 0,
        "hint": "It tells investors how the business did.",
        "explanation": "An earnings report shares a company’s profits, revenue, and important updates. Investors use it to evaluate performance."
    },
    {
        "q": "Why should you compare investments before choosing one?",
        "opts": ["To understand risk, return, and cost", "To avoid all taxes", "To make trading faster"],
        "answer": 0,
        "hint": "Comparison helps you choose more carefully.",
        "explanation": "Comparing investments helps you choose those that fit your goals, risk tolerance, and budget. It prevents impulsive choices."
    },
    {
        "q": "What is the main purpose of a savings goal?",
        "opts": ["To guide how much and how long you save", "To trade more often", "To avoid keeping cash"],
        "answer": 0,
        "hint": "It helps plan your money.",
        "explanation": "A savings goal guides how much you need to save and helps keep your money focused on a real objective."
    },
    {
        "q": "What does patience in investing usually lead to?",
        "opts": ["Stronger long-term returns", "Faster instant profits", "No market exposure"],
        "answer": 0,
        "hint": "Slow and steady often wins in investing.",
        "explanation": "Patience in investing is often rewarded over the long term as markets recover and growth compounds."
    },
    {
        "q": "What is a smart way to learn about investing?",
        "opts": ["Study, practice, and ask questions", "Always copy someone else", "Trade only after winning once"],
        "answer": 0,
        "hint": "Good learning comes from effort.",
        "explanation": "A smart way to learn is to study the basics, practice with small amounts, and keep asking questions about what you don’t understand."
    }
]

ACHIEVEMENT_DEFINITIONS = {
    "first_trade": {"name": "First Trade", "description": "Complete your first trade", "xp_bonus": 50},
    "first_lesson": {"name": "First Lesson", "description": "Complete your first lesson", "xp_bonus": 50},
    "first_quiz": {"name": "First Quiz", "description": "Complete your first quiz", "xp_bonus": 50},
    "first_profit": {"name": "First Profit", "description": "Make your first profitable trade", "xp_bonus": 75},
    "level_5": {"name": "Level 5", "description": "Reach level 5", "xp_bonus": 100},
    "level_10": {"name": "Level 10", "description": "Reach level 10", "xp_bonus": 200},
    "diversified": {"name": "Diversified Investor", "description": "Hold 5 different stocks", "xp_bonus": 150}
}

DAILY_CHALLENGE_DEFINITIONS = {
    "buy_stock": {"name": "Buy a Stock", "description": "Buy at least 1 stock", "target": 1, "xp_reward": 25},
    "complete_lesson": {"name": "Complete a Lesson", "description": "Complete at least 1 lesson", "target": 1, "xp_reward": 30},
    "earn_xp": {"name": "Earn XP", "description": "Earn 100 XP", "target": 100, "xp_reward": 50},
    "make_trades": {"name": "Make Trades", "description": "Make 3 trades", "target": 3, "xp_reward": 40},
    "complete_quiz": {"name": "Complete a Quiz", "description": "Complete at least 1 quiz", "target": 1, "xp_reward": 25}
}

def check_and_award_achievement(user_id, achievement_type):
    """Check if user has achievement, award if not, return True if newly awarded"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if already achieved
    existing = c.execute(
        "SELECT id FROM achievements WHERE user_id = ? AND achievement_type = ?",
        (user_id, achievement_type)
    ).fetchone()
    
    if existing:
        conn.close()
        return False
    
    # Award achievement
    c.execute(
        "INSERT INTO achievements (user_id, achievement_type) VALUES (?, ?)",
        (user_id, achievement_type)
    )
    conn.commit()
    conn.close()
    
    return True

def get_user_achievements(user_id):
    """Get all achievements for a user"""
    conn = get_db_connection()
    c = conn.cursor()
    
    achievements = c.execute(
        "SELECT achievement_type, achieved_at FROM achievements WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    
    conn.close()
    
    return [{"type": row["achievement_type"], "achieved_at": row["achieved_at"]} for row in achievements]

def check_diversified_achievement(user_id):
    """Check if user holds 5 or more different stocks"""
    conn = get_db_connection()
    c = conn.cursor()
    
    holdings = c.execute(
        "SELECT COUNT(DISTINCT ticker) FROM portfolio WHERE user_id = ? AND shares > 0",
        (user_id,)
    ).fetchone()
    
    conn.close()
    
    count = holdings[0] if holdings else 0
    return count >= 5

def check_profit_achievement(user_id):
    """Check if user has made a profitable trade"""
    conn = get_db_connection()
    c = conn.cursor()
    
    trades = c.execute(
        "SELECT ticker, action, shares, price FROM trades WHERE user_id = ? ORDER BY timestamp ASC",
        (user_id,)
    ).fetchall()
    
    conn.close()
    
    if not trades:
        return False
    
    holdings = calculate_portfolio_from_trades([dict(row) for row in trades])
    
    for ticker, position in holdings.items():
        if position["shares"] > 0:
            current_price = generate_realistic_price(ticker)
            if current_price > position["avgCost"]:
                return True
    
    return False

def get_today_date():
    """Get today's date in YYYY-MM-DD format"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

def initialize_daily_challenges(user_id):
    """Initialize daily challenges for a user if they don't exist for today"""
    from datetime import datetime
    today = get_today_date()
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if challenges already exist for today
    existing = c.execute(
        "SELECT COUNT(*) FROM daily_challenges WHERE user_id = ? AND date = ?",
        (user_id, today)
    ).fetchone()
    
    if existing[0] > 0:
        conn.close()
        return
    
    # Create challenges for today
    for challenge_type, definition in DAILY_CHALLENGE_DEFINITIONS.items():
        c.execute(
            "INSERT INTO daily_challenges (user_id, challenge_type, target_value, current_value, completed, date, xp_reward) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, challenge_type, definition["target"], 0, 0, today, definition["xp_reward"])
        )
    
    conn.commit()
    conn.close()

def update_daily_challenge(user_id, challenge_type, increment=1):
    """Update daily challenge progress, return True if newly completed"""
    from datetime import datetime
    today = get_today_date()
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get current challenge
    challenge = c.execute(
        "SELECT current_value, target_value, completed FROM daily_challenges WHERE user_id = ? AND challenge_type = ? AND date = ?",
        (user_id, challenge_type, today)
    ).fetchone()
    
    if not challenge:
        conn.close()
        return False
    
    if challenge["completed"]:
        conn.close()
        return False
    
    # Update progress
    new_value = challenge["current_value"] + increment
    is_completed = new_value >= challenge["target_value"]
    
    c.execute(
        "UPDATE daily_challenges SET current_value = ?, completed = ? WHERE user_id = ? AND challenge_type = ? AND date = ?",
        (new_value, 1 if is_completed else 0, user_id, challenge_type, today)
    )
    
    conn.commit()
    conn.close()
    
    return is_completed

def get_daily_challenges(user_id):
    """Get all daily challenges for a user"""
    from datetime import datetime
    today = get_today_date()
    conn = get_db_connection()
    c = conn.cursor()
    
    # Initialize challenges if needed
    initialize_daily_challenges(user_id)
    
    challenges = c.execute(
        "SELECT challenge_type, target_value, current_value, completed, xp_reward FROM daily_challenges WHERE user_id = ? AND date = ?",
        (user_id, today)
    ).fetchall()
    
    conn.close()
    
    challenge_details = []
    for challenge in challenges:
        definition = DAILY_CHALLENGE_DEFINITIONS.get(challenge["challenge_type"], {})
        challenge_details.append({
            "type": challenge["challenge_type"],
            "name": definition.get("name", challenge["challenge_type"]),
            "description": definition.get("description", ""),
            "target": challenge["target_value"],
            "current": challenge["current_value"],
            "completed": bool(challenge["completed"]),
            "xp_reward": challenge["xp_reward"]
        })
    
    return challenge_details

def update_streak(user_id, streak_type):
    """Update user streak for a specific activity type"""
    from datetime import datetime, timedelta
    today = get_today_date()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get current streak
    streak = c.execute(
        "SELECT current_streak, last_activity_date, best_streak FROM user_streaks WHERE user_id = ? AND streak_type = ?",
        (user_id, streak_type)
    ).fetchone()
    
    if not streak:
        # Create new streak
        c.execute(
            "INSERT INTO user_streaks (user_id, streak_type, current_streak, last_activity_date, best_streak) VALUES (?, ?, ?, ?, ?)",
            (user_id, streak_type, 1, today, 1)
        )
        conn.commit()
        conn.close()
        return 1
    
    current_streak = streak["current_streak"]
    last_date = streak["last_activity_date"]
    best_streak = streak["best_streak"]
    
    if last_date == today:
        # Already updated today, no change
        conn.close()
        return current_streak
    elif last_date == yesterday:
        # Consecutive day, increment streak
        new_streak = current_streak + 1
        if new_streak > best_streak:
            best_streak = new_streak
    else:
        # Streak broken, reset to 1
        new_streak = 1
    
    c.execute(
        "UPDATE user_streaks SET current_streak = ?, last_activity_date = ?, best_streak = ? WHERE user_id = ? AND streak_type = ?",
        (new_streak, today, best_streak, user_id, streak_type)
    )
    conn.commit()
    conn.close()
    
    return new_streak

def get_user_streaks(user_id):
    """Get all streaks for a user"""
    conn = get_db_connection()
    c = conn.cursor()
    
    streaks = c.execute(
        "SELECT streak_type, current_streak, best_streak FROM user_streaks WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    
    conn.close()
    
    streak_details = {}
    for streak in streaks:
        streak_details[streak["streak_type"]] = {
            "current": streak["current_streak"],
            "best": streak["best_streak"]
        }
    
    return streak_details

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            return render_template("signup.html", error="All fields are required.")

        user_id = create_user(username, email, password)
        if not user_id:
            return render_template("signup.html", error="Username or email already taken.")

        session["user_id"] = user_id
        session["username"] = username
        return render_template("index.html")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("login.html", error="Provide username and password.")

        user = find_user_by_username(username)
        if not user or not verify_password(user["password_hash"], password):
            return render_template("login.html", error="Invalid credentials.")

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        
        # Update login streak
        update_streak(user["id"], "login")
        
        return render_template("index.html")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("is_guest", None)
    session.pop("guest_cash", None)
    session.pop("guest_xp", None)
    session.pop("guest_level", None)
    session.pop("guest_portfolio", None)
    return render_template("index.html")


@app.route("/guest")
def guest_login():
    """Start a guest session with temporary state"""
    import uuid
    session["user_id"] = f"guest_{uuid.uuid4().hex[:8]}"
    session["username"] = "Guest"
    session["is_guest"] = True
    session["guest_cash"] = 10000.0
    session["guest_xp"] = 0
    session["guest_level"] = 1
    session["guest_portfolio"] = {}
    return render_template("index.html")


@app.route("/api/guest/convert", methods=["POST"])
def convert_guest_to_account():
    """Convert guest session to permanent account"""
    if not session.get("is_guest"):
        return safe_json_response({"error": "Not a guest session"}, 400)
    
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        if not username or not email or not password:
            return safe_json_response({"error": "All fields are required"}, 400)
        
        # Check if username or email already exists
        if find_user_by_username(username):
            return safe_json_response({"error": "Username already taken"}, 400)
        
        # Create new user with guest data
        user_id = create_user(username, email, password)
        if not user_id:
            return safe_json_response({"error": "Email already taken"}, 400)
        
        # Transfer guest data to new user
        guest_cash = session.get("guest_cash", 10000.0)
        guest_xp = session.get("guest_xp", 0)
        guest_level = session.get("guest_level", 1)
        guest_portfolio = session.get("guest_portfolio", {})
        
        # Update user with guest data
        update_user_stats(user_id, cash=guest_cash, xp=guest_xp, level=guest_level)
        
        # Sync portfolio
        sync_portfolio_rows(user_id, guest_portfolio)
        
        # Convert session to regular user
        session["user_id"] = user_id
        session["username"] = username
        session["is_guest"] = False
        session.pop("guest_cash", None)
        session.pop("guest_xp", None)
        session.pop("guest_level", None)
        session.pop("guest_portfolio", None)
        
        return safe_json_response({
            "status": "success",
            "user_id": user_id,
            "username": username,
            "cash": guest_cash,
            "xp": guest_xp,
            "level": guest_level,
            "message": "Account created successfully! Your guest progress has been saved."
        })
    except Exception as e:
        return safe_json_response({"error": f"Conversion failed: {str(e)}"}, 500)


def _get_stock_history(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="1d", interval="5m")
    if df.empty:
        df = stock.history(period="5d", interval="1h")
    return stock, df


@app.route("/stock/<ticker>")
def stock(ticker):
    try:
        ticker = ticker.upper()
        stock_obj, df = _get_stock_history(ticker)

        if df.empty:
            return jsonify({"error": "Invalid ticker or no recent data available."})

        price = round(df["Close"].iloc[-1], 2)
        prices = [round(v, 2) for v in df["Close"].tolist()]
        info = getattr(stock_obj, "info", {}) or {}
        name = info.get("longName") or info.get("shortName") or ticker

        prev_close = info.get("previousClose")
        change = None
        if prev_close:
            change = round((price - prev_close) / prev_close * 100, 2)
        else:
            change = round((price - df["Close"].iloc[0]) / df["Close"].iloc[0] * 100, 2)

        return jsonify({
            "ticker": ticker,
            "name": name,
            "price": price,
            "change": change,
            "open": round(df["Open"].iloc[-1], 2),
            "high": round(df["High"].max(), 2),
            "low": round(df["Low"].min(), 2),
            "chart": prices
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/lesson/<int:lesson_id>")
def lesson(lesson_id):
    if 0 <= lesson_id < len(LESSONS):
        return jsonify(LESSONS[lesson_id])
    return jsonify({"error": "Lesson not found."})


@app.route("/lessons")
def lessons():
    return jsonify(LESSONS)


@app.route("/quiz/<int:question_id>")
def quiz(question_id):
    if 0 <= question_id < len(QUIZ):
        return jsonify(QUIZ[question_id])
    return jsonify({"error": "Question not found."})


@app.route("/quizzes")
def quizzes():
    return jsonify(QUIZ)


@app.route("/api/search", methods=["GET"])
def search_universal():
    try:
        query = request.args.get("q", "").strip()
        if not query or len(query) < 1:
            return safe_json_response({"results": [], "status": "empty"})

        results = []
        # Asset search
        assets = fuzzy_search(query)
        for ticker, info in assets:
            results.append({
                "type": "asset",
                "ticker": ticker,
                "name": info["name"],
                "sector": info.get("sector", ""),
                "price": generate_realistic_price(ticker)
            })

        # Lesson search
        for lesson in LESSONS:
            if query.lower() in lesson["title"].lower() or query.lower() in lesson["content"].lower():
                results.append({
                    "type": "lesson",
                    "title": lesson["title"],
                    "snippet": lesson["description"] if "description" in lesson else lesson["content"][:120],
                    "lesson_id": LESSONS.index(lesson)
                })

        # Quiz search
        for question in INTEGRATE_QUIZ_DATABASE:
            if query.lower() in question["question"].lower():
                results.append({
                    "type": "quiz",
                    "question": question["question"],
                    "quiz_id": question["id"]
                })

        # News search (using cached headlines)
        news_items = fetch_external_market_news()
        for item in news_items:
            if query.lower() in item["title"].lower() or query.lower() in item["summary"].lower():
                results.append({
                    "type": "news",
                    "title": item["title"],
                    "summary": item["summary"],
                    "source": item["source"],
                    "url": item["url"]
                })

        return safe_json_response({"results": results[:30], "status": "success"})
    except Exception:
        return safe_json_response({"error": "Search failed", "status": "error"}, 500)


@app.route("/api/recommended")
def get_recommended_stocks():
    try:
        recommended_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "AMD"]
        recommended = [{
            "ticker": ticker,
            "name": ASSET_DATABASE[ticker]["name"],
            "sector": ASSET_DATABASE[ticker].get("sector", ""),
            "price": generate_realistic_price(ticker),
            "change": round(random.uniform(-5, 5), 2)
        } for ticker in recommended_tickers if ticker in ASSET_DATABASE]
        return safe_json_response({"recommended": recommended, "status": "success"})
    except Exception:
        return safe_json_response({"error": "Failed to fetch recommendations", "status": "error"}, 500)


@app.route("/api/market/overview")
def get_market_overview():
    try:
        return safe_json_response({"overview": fetch_market_overview_data(), "status": "success"})
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch market overview: {str(e)}", "status": "error"}, 500)


@app.route("/api/market/trending")
def get_market_trending():
    try:
        assets = []
        for ticker, info in ASSET_DATABASE.items():
            assets.append({
                "ticker": ticker,
                "name": info["name"],
                "sector": info.get("sector", ""),
                "price": generate_realistic_price(ticker),
                "change": round(random.uniform(-6, 6), 2),
                "volume": int(random.uniform(500000, 2500000))
            })
        trending_stocks = sorted([a for a in assets if a["ticker"] not in ["BTC", "ETH", "SOL", "DOGE"]], key=lambda x: -x["volume"])[:5]
        trending_crypto = sorted([a for a in assets if a["ticker"] in ["BTC", "ETH", "SOL", "DOGE"]], key=lambda x: -x["volume"])[:4]
        trending_etfs = [
            {"ticker": "SPY", "name": "SPDR S&P 500 ETF", "price": generate_realistic_price("AAPL"), "change": round(random.uniform(-2, 2), 2), "volume": 1800000},
            {"ticker": "QQQ", "name": "Invesco QQQ Trust", "price": generate_realistic_price("NVDA"), "change": round(random.uniform(-2, 2), 2), "volume": 1500000}
        ]
        gainers = sorted(assets, key=lambda x: -x["change"])[:5]
        losers = sorted(assets, key=lambda x: x["change"])[:5]
        most_active = sorted(assets, key=lambda x: -x["volume"])[:5]
        return safe_json_response({
            "stocks": trending_stocks,
            "etfs": trending_etfs,
            "crypto": trending_crypto,
            "gainers": gainers,
            "losers": losers,
            "most_active": most_active,
            "status": "success"
        })
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch trending market data: {str(e)}", "status": "error"}, 500)


@app.route("/api/market/insights")
def get_market_insights():
    try:
        return safe_json_response({"insights": fetch_market_insights_data(), "status": "success"})
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch market insights: {str(e)}", "status": "error"}, 500)


@app.route("/api/market/calendar")
def get_market_calendar():
    try:
        return safe_json_response({"events": fetch_market_calendar_data(), "status": "success"})
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch market calendar: {str(e)}", "status": "error"}, 500)


@app.route("/api/asset/<ticker>/details")
def get_asset_details(ticker):
    try:
        ticker = ticker.upper()
        info = ASSET_DATABASE.get(ticker, {"name": ticker, "sector": "General", "base": 100, "volatility": 2.0})
        price = generate_realistic_price(ticker)
        notes = []
        if info.get("sector") == "Technology":
            notes.append("Tech companies often move quickly with earnings and product announcements.")
        if info.get("sector") == "Cryptocurrency":
            notes.append("Crypto markets are highly volatile and sensitive to regulatory news.")
        if info.get("sector") == "Automotive":
            notes.append("Automotive stocks are influenced by supply chains, consumer demand, and EV adoption.")
        chart = generate_chart_data(ticker, points=60)
        return safe_json_response({
            "ticker": ticker,
            "name": info["name"],
            "sector": info.get("sector", "General"),
            "price": price,
            "change": round(random.uniform(-5, 5), 2),
            "overview": f"{info['name']} is a leading company in the {info.get('sector', 'market')} sector.",
            "description": f"{info['name']} is included in the platform as an educational asset that illustrates key investing themes.",
            "industry": info.get("sector", "General"),
            "notes": notes,
            "chart": chart,
            "details": {
                "market_cap": f"${round(price * 1000000000)}",
                "pe_ratio": round(random.uniform(15, 45), 2),
                "beta": round(random.uniform(0.8, 1.8), 2)
            },
            "status": "success"
        })
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch asset details: {str(e)}", "status": "error"}, 500)


@app.route("/api/flashcards")
def get_flashcards():
    try:
        return safe_json_response({"flashcards": load_flashcards(), "status": "success"})
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch flashcards: {str(e)}", "status": "error"}, 500)


@app.route("/api/leaderboard")
def get_leaderboard():
    """Get leaderboard rankings"""
    try:
        leaderboard_type = request.args.get("type", "xp")
        conn = get_db_connection()
        c = conn.cursor()
        users = c.execute(
            "SELECT id, username, xp, level, cash FROM users ORDER BY xp DESC LIMIT 20"
        ).fetchall()
        leaderboard = []
        for idx, user in enumerate(users):
            portfolio_value = float(user["cash"] or 0)
            achievements_count = c.execute(
                "SELECT COUNT(*) FROM achievements WHERE user_id = ?",
                (user["id"],)
            ).fetchone()[0]
            leaderboard.append({
                "rank": idx + 1,
                "username": user["username"],
                "xp": int(user["xp"] or 0),
                "level": int(user["level"] or 1),
                "portfolio_value": portfolio_value,
                "achievements_count": achievements_count
            })
        conn.close()
        if not leaderboard:
            leaderboard = [
                {"rank": 1, "username": "ApexLearner", "xp": 710, "level": 8, "portfolio_value": 14200.50, "achievements_count": 5},
                {"rank": 2, "username": "MarketMaven", "xp": 640, "level": 7, "portfolio_value": 13650.10, "achievements_count": 4},
                {"rank": 3, "username": "BullRunner", "xp": 580, "level": 6, "portfolio_value": 12100.75, "achievements_count": 4}
            ]
        if leaderboard_type == "level":
            leaderboard = sorted(leaderboard, key=lambda x: -x["level"])
        elif leaderboard_type == "achievements":
            leaderboard = sorted(leaderboard, key=lambda x: -x["achievements_count"])
        return safe_json_response({"leaderboard": leaderboard, "status": "success"})
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch leaderboard: {str(e)}", "status": "error"}, 500)


@app.route("/leaderboard")
def leaderboard_page():
    """Render leaderboard page"""
    return render_template("leaderboard.html")


@app.route("/api/weekly-challenges")
def get_weekly_challenges():
    try:
        weekly = [
            {"title": "Complete 5 lessons", "description": "Work through five lessons in the learning center.", "xp_reward": 120},
            {"title": "Earn 500 XP", "description": "Collect 500 XP from quizzes, lessons, and trades.", "xp_reward": 180},
            {"title": "Make 10 trades", "description": "Practice trading with ten orders this week.", "xp_reward": 150}
        ]
        return safe_json_response({"weekly_challenges": weekly, "status": "success"})
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch weekly challenges: {str(e)}", "status": "error"}, 500)


@app.route("/api/monthly-challenges")
def get_monthly_challenges():
    try:
        monthly = [
            {"title": "Reach Level 10", "description": "Level up to 10 before the month ends.", "xp_reward": 300},
            {"title": "Build a diversified portfolio", "description": "Hold at least 5 different assets in your portfolio.", "xp_reward": 250},
            {"title": "Complete all beginner lessons", "description": "Finish the full beginner learning track.", "xp_reward": 220}
        ]
        return safe_json_response({"monthly_challenges": monthly, "status": "success"})
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch monthly challenges: {str(e)}", "status": "error"}, 500)


@app.route("/api/goals", methods=["GET", "POST"])
def manage_goals():
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)
    if is_guest or not user_id:
        return safe_json_response({"goals": [], "is_guest": is_guest, "status": "success"})
    try:
        conn = get_db_connection()
        c = conn.cursor()
        if request.method == "GET":
            goals = c.execute(
                "SELECT id, goal_type, title, target_value, current_value, unit, completed FROM goals WHERE user_id = ?",
                (user_id,)
            ).fetchall()
            conn.close()
            return safe_json_response({"goals": [dict(row) for row in goals], "status": "success"})
        data = request.get_json() or {}
        title = data.get("title", "")
        goal_type = data.get("goal_type", "savings")
        target_value = float(data.get("target_value", 0))
        unit = data.get("unit", "USD")
        if not title or target_value <= 0:
            conn.close()
            return safe_json_response({"error": "Invalid goal data", "status": "error"}, 400)
        c.execute(
            "INSERT INTO goals (user_id, goal_type, title, target_value, current_value, unit) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, goal_type, title, target_value, 0, unit)
        )
        conn.commit()
        conn.close()
        return safe_json_response({"status": "success", "message": "Goal created"})
    except Exception as e:
        return safe_json_response({"error": f"Failed to manage goals: {str(e)}", "status": "error"}, 500)


@app.route("/api/settings", methods=["GET", "POST"])
def handle_settings():
    """Handle user settings"""
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)
    if is_guest or not user_id:
        return safe_json_response({"settings": {}, "is_guest": is_guest, "status": "success"})
    try:
        if request.method == "GET":
            settings = get_user_settings(user_id)
            profile = find_user_by_id(user_id)
            return safe_json_response({"settings": settings, "username": profile["username"], "status": "success"})
        data = request.get_json() or {}
        theme = data.get("theme")
        notifications = data.get("notifications")
        email_updates = data.get("email_updates")
        save_user_settings(user_id, theme=theme, notifications=notifications, email_updates=email_updates)
        return safe_json_response({"status": "success", "message": "Settings saved"})
    except Exception as e:
        return safe_json_response({"error": f"Settings operation failed: {str(e)}", "status": "error"}, 500)


@app.route("/api/settings/username", methods=["POST"])
def update_username():
    user_id = session.get("user_id")
    if session.get("is_guest") or not user_id:
        return safe_json_response({"error": "Login required for username change", "status": "error"}, 401)
    data = request.get_json() or {}
    new_username = data.get("username", "").strip()
    success, message = change_username(user_id, new_username)
    if not success:
        return safe_json_response({"error": message, "status": "error"}, 400)
    return safe_json_response({"status": "success", "message": "Username updated"})


@app.route("/api/settings/password", methods=["POST"])
def update_password():
    user_id = session.get("user_id")
    if session.get("is_guest") or not user_id:
        return safe_json_response({"error": "Login required for password change", "status": "error"}, 401)
    data = request.get_json() or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    success, message = change_password(user_id, current_password, new_password)
    if not success:
        return safe_json_response({"error": message, "status": "error"}, 400)
    return safe_json_response({"status": "success", "message": "Password updated"})


@app.route("/api/settings/reset", methods=["POST"])
def reset_account_progress():
    user_id = session.get("user_id")
    if session.get("is_guest") or not user_id:
        return safe_json_response({"error": "Login required to reset progress", "status": "error"}, 401)
    try:
        reset_user_progress(user_id)
        return safe_json_response({"status": "success", "message": "Account progress has been reset."})
    except Exception as e:
        return safe_json_response({"error": f"Reset failed: {str(e)}", "status": "error"}, 500)


@app.route("/api/settings/delete", methods=["POST"])
def delete_account():
    user_id = session.get("user_id")
    if session.get("is_guest") or not user_id:
        return safe_json_response({"error": "Guest accounts cannot be deleted", "status": "error"}, 400)
    try:
        soft_delete_user_account(user_id)
        session.clear()
        return safe_json_response({"status": "success", "message": "Your account has been removed."})
    except Exception as e:
        return safe_json_response({"error": f"Delete failed: {str(e)}", "status": "error"}, 500)


@app.route("/api/profile")
def get_user_profile():
    """Get user profile data"""
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)
    if is_guest or not user_id:
        return safe_json_response({"profile": {}, "is_guest": is_guest, "status": "success"})
    try:
        conn = get_db_connection()
        c = conn.cursor()
        user = c.execute(
            "SELECT username, email, xp, level, cash, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        if not user:
            conn.close()
            return safe_json_response({"error": "User not found", "status": "error"}, 404)
        achievements = get_user_achievements(user_id)
        streaks = get_user_streaks(user_id)
        portfolio_count = c.execute(
            "SELECT COUNT(*) FROM portfolio WHERE user_id = ? AND shares > 0",
            (user_id,)
        ).fetchone()[0]
        trade_count = c.execute(
            "SELECT COUNT(*) FROM trades WHERE user_id = ?",
            (user_id,)
        ).fetchone()[0]
        conn.close()
        profile = {
            "username": user["username"],
            "email": user["email"],
            "xp": int(user["xp"] or 0),
            "level": int(user["level"] or 1),
            "cash": float(user["cash"] or 0),
            "created_at": user["created_at"],
            "achievements_count": len(achievements),
            "portfolio_count": portfolio_count,
            "trade_count": trade_count,
            "streaks": streaks,
            "avatar": f"https://api.dicebear.com/6.x/identicon/svg?seed={user['username']}",
            "badges": get_user_badges(user_id)
        }
        return safe_json_response({"profile": profile, "status": "success"})
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch profile: {str(e)}", "status": "error"}, 500)


@app.route("/profile")
def profile_page():
    """Render profile page"""
    return render_template("profile.html")


@app.route("/settings")
def settings_page():
    """Render settings page"""
    return render_template("settings.html")


@app.route("/api/learning/<int:chapter_id>")
def get_learning_chapter(chapter_id):
    try:
        chapter = next((c for c in INTEGRATE_LEARNING_CURRICULUM if c["id"] == chapter_id), None)
        if not chapter:
            return safe_json_response({"error": "Chapter not found", "status": "error"}, 404)
        return safe_json_response({"chapter": chapter, "status": "success"})
    except Exception:
        return safe_json_response({"error": "Failed to fetch chapter", "status": "error"}, 500)


@app.route("/api/quiz")
def get_quiz_questions():
    try:
        category = request.args.get("category", None)
        if category:
            questions = [q for q in INTEGRATE_QUIZ_DATABASE if q["category"] == category]
        else:
            questions = INTEGRATE_QUIZ_DATABASE
        shuffled = random.sample(questions, min(10, len(questions)))
        return safe_json_response({"questions": shuffled, "total_available": len(questions), "status": "success"})
    except Exception:
        return safe_json_response({"error": "Failed to fetch questions", "status": "error"}, 500)


@app.route("/api/quiz/check", methods=["POST"])
def check_quiz_answer():
    try:
        data = request.get_json()
        question_id = data.get("question_id")
        answer_index = data.get("answer_index")
        question = next((q for q in INTEGRATE_QUIZ_DATABASE if q["id"] == question_id), None)
        if not question:
            return safe_json_response({"error": "Question not found", "status": "error"}, 404)
        is_correct = answer_index == question["correct"]
        xp_earned = question["xp_reward"] if is_correct else 0
        if is_correct:
            user_state["xp"] += xp_earned
            user_state["level"] = 1 + (user_state["xp"] // 100)
            user_id = session.get("user_id")
            if user_id:
                user = find_user_by_id(user_id)
                if user:
                    new_xp = int(user["xp"] or 0) + xp_earned
                    new_level = 1 + (new_xp // 100)
                    update_user_stats(user_id, xp=new_xp, level=new_level)
                    
                    # Check for first quiz achievement
                    check_and_award_achievement(user_id, "first_quiz")
                    
                    # Check for level achievements
                    if new_level >= 5:
                        check_and_award_achievement(user_id, "level_5")
                    if new_level >= 10:
                        check_and_award_achievement(user_id, "level_10")
                    
                    # Update daily challenges
                    update_daily_challenge(user_id, "complete_quiz")
                    update_daily_challenge(user_id, "earn_xp", xp_earned)
        return safe_json_response({
            "is_correct": is_correct,
            "correct_answer": question["correct"],
            "xp_earned": xp_earned,
            "total_xp": user_state["xp"],
            "level": user_state["level"],
            "explanation": f"The correct answer is: {question['options'][question['correct']]}",
            "status": "success"
        })
    except Exception:
        return safe_json_response({"error": "Check failed", "status": "error"}, 500)


@app.route("/api/learning/complete/<int:chapter_id>", methods=["POST"])
def complete_learning_chapter(chapter_id):
    try:
        chapter = next((c for c in INTEGRATE_LEARNING_CURRICULUM if c["id"] == chapter_id), None)
        if not chapter:
            return safe_json_response({"error": "Chapter not found", "status": "error"}, 404)
        xp_reward = chapter["xp_reward"]
        user_state["xp"] += xp_reward
        user_state["streak"] += 1
        user_state["level"] = 1 + (user_state["xp"] // 100)
        user_id = session.get("user_id")
        if user_id:
            user = find_user_by_id(user_id)
            if user:
                new_xp = int(user["xp"] or 0) + xp_reward
                new_streak = int(user["streak"] or 0) + 1
                new_level = 1 + (new_xp // 100)
                update_user_stats(user_id, xp=new_xp, level=new_level, streak=new_streak)
                
                # Check for first lesson achievement
                check_and_award_achievement(user_id, "first_lesson")
                
                # Check for level achievements
                if new_level >= 5:
                    check_and_award_achievement(user_id, "level_5")
                if new_level >= 10:
                    check_and_award_achievement(user_id, "level_10")
                
                # Update daily challenges
                update_daily_challenge(user_id, "complete_lesson")
                update_daily_challenge(user_id, "earn_xp", xp_reward)
                
                # Update learning streak
                update_streak(user_id, "learning")
        return safe_json_response({
            "status": "success",
            "chapter_id": chapter_id,
            "xp_earned": xp_reward,
            "total_xp": user_state["xp"],
            "level": user_state["level"],
            "streak": user_state["streak"],
            "message": f"Chapter complete! +{xp_reward} XP"
        })
    except Exception:
        return safe_json_response({"error": "Failed to complete chapter", "status": "error"}, 500)


@app.route("/api/user")
def get_user_state():
    is_guest = session.get("is_guest", False)
    
    if is_guest:
        # Return guest state from session
        return safe_json_response({
            "authenticated": True,
            "is_guest": True,
            "username": "Guest",
            "cash": session.get("guest_cash", 10000.0),
            "portfolio": session.get("guest_portfolio", {}),
            "xp": session.get("guest_xp", 0),
            "level": session.get("guest_level", 1),
            "streak": 0,
            "tradeHistory": [],
            "portfolio_value": session.get("guest_cash", 10000.0)
        })
    
    user_id = session.get("user_id")
    if user_id:
        persisted = load_user_state_from_db(user_id)
        if persisted is None:
            return safe_json_response({"authenticated": False, "error": "User not found"}, 404)
        persisted["is_guest"] = False
        return safe_json_response(persisted)

    return safe_json_response({
        "authenticated": False,
        "is_guest": False,
        "cash": round(user_state["cash"], 2),
        "portfolio": user_state["portfolio"],
        "xp": user_state["xp"],
        "level": user_state["level"],
        "streak": user_state["streak"],
        "tradeHistory": user_state["trades"],
        "portfolio_value": calculate_portfolio_value()
    })


@app.route("/api/user/save", methods=["POST"])
def save_user_state():
    user_id = session.get("user_id")
    if not user_id:
        return safe_json_response({"error": "Authentication required"}, 401)

    payload = request.get_json(silent=True) or {}
    portfolio = payload.get("portfolio") or {}
    cash = payload.get("cash")
    xp = payload.get("xp")
    level = payload.get("level")
    streak = payload.get("streak")

    if cash is not None:
        cash = round(float(cash), 2)
    if xp is not None:
        xp = int(xp)
        level = 1 + (xp // 100)
    if level is not None:
        level = int(level)
    if streak is not None:
        streak = int(streak)

    update_user_stats(user_id, cash=cash, xp=xp, level=level, streak=streak)
    sync_portfolio_rows(user_id, portfolio)

    updated = load_user_state_from_db(user_id)
    if updated is None:
        return safe_json_response({"error": "Failed to save user state"}, 500)
    return safe_json_response({"status": "success", **updated})


@app.route("/api/price/<ticker>")
def get_price(ticker):
    try:
        ticker = ticker.upper()
        if ticker not in ASSET_DATABASE:
            return safe_json_response({"error": f"Asset {ticker} not found", "status": "error"}, 404)
        asset_info = get_asset_info(ticker)
        price = generate_realistic_price(ticker)
        user_shares = 0
        user_cash = None
        user_id = session.get("user_id")
        if user_id:
            conn = get_db_connection()
            c = conn.cursor()
            user = c.execute("SELECT cash FROM users WHERE id = ?", (user_id,)).fetchone()
            portfolio_row = c.execute("SELECT shares FROM portfolio WHERE user_id = ? AND ticker = ?", (user_id, ticker)).fetchone()
            conn.close()
            user_cash = float(user["cash"] or 0) if user else None
            user_shares = int(portfolio_row["shares"] or 0) if portfolio_row else 0

        return safe_json_response({
            "ticker": ticker,
            "name": asset_info["name"],
            "price": price,
            "user_cash": user_cash if user_cash is not None else round(user_state["cash"], 2),
            "user_shares": user_shares,
            "status": "success"
        })
    except Exception:
        return safe_json_response({
            "ticker": ticker.upper(),
            "price": get_asset_info(ticker)["base"],
            "status": "fallback",
            "error": "Using cached price"
        })


@app.route("/api/chart/<ticker>")
def get_chart(ticker):
    try:
        ticker = ticker.upper()
        if ticker not in ASSET_DATABASE:
            return safe_json_response({"error": "Asset not found"}, 404)
        chart_data = generate_chart_data(ticker, points=30)
        return safe_json_response({"ticker": ticker, "data": chart_data, "status": "success"})
    except Exception:
        return safe_json_response({"data": [100] * 30, "status": "fallback", "error": "Using default chart"}, 500)


@app.route("/api/trade/<action>/<ticker>/<int:shares>")
def trade(action, ticker, shares):
    try:
        is_guest = session.get("is_guest", False)
        ticker = ticker.upper()
        action = action.lower()
        if ticker not in ASSET_DATABASE:
            return safe_json_response({"error": "Invalid ticker"}, 400)
        if shares <= 0:
            return safe_json_response({"error": "Shares must be positive"}, 400)

        price = generate_realistic_price(ticker)
        total_cost = round(price * shares, 2)
        
        # Handle guest trading (session-based, no DB)
        if is_guest:
            guest_cash = session.get("guest_cash", 10000.0)
            guest_portfolio = session.get("guest_portfolio", {})
            guest_xp = session.get("guest_xp", 0)
            guest_level = session.get("guest_level", 1)
            
            if action == "buy":
                if guest_cash < total_cost:
                    return safe_json_response({
                        "error": f"Insufficient cash. Need ${total_cost:.2f}, have ${guest_cash:.2f}",
                        "status": "error"
                    }, 400)
                guest_cash -= total_cost
                guest_portfolio[ticker] = guest_portfolio.get(ticker, 0) + shares
                guest_xp += 25
            elif action == "sell":
                if guest_portfolio.get(ticker, 0) < shares:
                    return safe_json_response({
                        "error": f"Insufficient shares. Have {guest_portfolio.get(ticker, 0)}, trying to sell {shares}",
                        "status": "error"
                    }, 400)
                guest_cash += total_cost
                guest_portfolio[ticker] -= shares
                if guest_portfolio[ticker] == 0:
                    del guest_portfolio[ticker]
                guest_xp += 25
            else:
                return safe_json_response({"error": "Invalid action"}, 400)
            
            guest_level = 1 + (guest_xp // 100)
            
            # Update session
            session["guest_cash"] = guest_cash
            session["guest_portfolio"] = guest_portfolio
            session["guest_xp"] = guest_xp
            session["guest_level"] = guest_level
            
            return safe_json_response({
                "status": "success",
                "action": action,
                "ticker": ticker,
                "shares": shares,
                "price": price,
                "cash": guest_cash,
                "xp_gained": 25,
                "total_xp": guest_xp,
                "level": guest_level,
                "portfolio": guest_portfolio,
                "is_guest": True
            })
        
        # Regular user trading (DB-based)
        user_id = session.get("user_id")

        if user_id:
            conn = get_db_connection()
            c = conn.cursor()
            user = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if user is None:
                conn.close()
                return safe_json_response({"error": "User not found"}, 404)

            current_cash = float(user["cash"] or 0)
            trades = c.execute(
                "SELECT ticker, action, shares, price FROM trades WHERE user_id = ? ORDER BY timestamp ASC",
                (user_id,),
            ).fetchall()
            holdings = calculate_portfolio_from_trades([dict(row) for row in trades])

            if action == "buy":
                if current_cash < total_cost:
                    conn.close()
                    return safe_json_response({
                        "error": f"Insufficient cash. Need ${total_cost:.2f}, have ${current_cash:.2f}",
                        "status": "error"
                    }, 400)
                new_cash = round(current_cash - total_cost, 2)
                new_xp = int(user["xp"] or 0) + 25
                new_level = 1 + (new_xp // 100)
                c.execute(
                    "INSERT INTO trades (user_id, ticker, action, shares, price) VALUES (?, ?, ?, ?, ?)",
                    (user_id, ticker, action, shares, price),
                )
            elif action == "sell":
                current_position = holdings.get(ticker)
                if not current_position or current_position["shares"] < shares:
                    conn.close()
                    return safe_json_response({
                        "error": f"Insufficient shares. Have {current_position['shares'] if current_position else 0}, trying to sell {shares}",
                        "status": "error"
                    }, 400)
                new_cash = round(current_cash + total_cost, 2)
                new_xp = int(user["xp"] or 0) + 25
                new_level = 1 + (new_xp // 100)
                c.execute(
                    "INSERT INTO trades (user_id, ticker, action, shares, price) VALUES (?, ?, ?, ?, ?)",
                    (user_id, ticker, action, shares, price),
                )
            else:
                conn.close()
                return safe_json_response({"error": "Invalid action"}, 400)

            trades = c.execute(
                "SELECT ticker, action, shares, price FROM trades WHERE user_id = ? ORDER BY timestamp ASC",
                (user_id,),
            ).fetchall()
            holdings = calculate_portfolio_from_trades([dict(row) for row in trades])
            c.execute(
                "UPDATE users SET cash = ?, xp = ?, level = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_cash, new_xp, new_level, user_id),
            )
            conn.commit()
            conn.close()
            sync_portfolio_rows(user_id, holdings)
            
            # Check for achievements after trade
            check_and_award_achievement(user_id, "first_trade")
            if check_profit_achievement(user_id):
                check_and_award_achievement(user_id, "first_profit")
            if check_diversified_achievement(user_id):
                check_and_award_achievement(user_id, "diversified")
            
            # Update daily challenges
            update_daily_challenge(user_id, "buy_stock")
            update_daily_challenge(user_id, "make_trades")
            
            # Update trading streak
            update_streak(user_id, "trading")
            
            updated = load_user_state_from_db(user_id)
            return safe_json_response({
                "status": "success",
                "action": action,
                "ticker": ticker,
                "shares": shares,
                "price": price,
                "cash": updated["cash"],
                "xp_gained": 25,
                "total_xp": updated["xp"],
                "level": updated["level"],
                "portfolio": updated["portfolio"],
                "tradeHistory": updated["tradeHistory"],
            })

        if action == "buy":
            if user_state["cash"] < total_cost:
                return safe_json_response({
                    "error": f"Insufficient cash. Need ${total_cost:.2f}, have ${user_state['cash']:.2f}",
                    "status": "error"
                }, 400)
            user_state["cash"] -= total_cost
            user_state["portfolio"][ticker] = user_state["portfolio"].get(ticker, 0) + shares
            user_state["xp"] += 25
        elif action == "sell":
            if user_state["portfolio"].get(ticker, 0) < shares:
                return safe_json_response({
                    "error": f"Insufficient shares. Have {user_state['portfolio'].get(ticker, 0)}, trying to sell {shares}",
                    "status": "error"
                }, 400)
            user_state["cash"] += total_cost
            user_state["portfolio"][ticker] -= shares
            if user_state["portfolio"][ticker] == 0:
                del user_state["portfolio"][ticker]
            user_state["xp"] += 25
        else:
            return safe_json_response({"error": "Invalid action"}, 400)

        user_state["level"] = 1 + (user_state["xp"] // 100)
        user_state["trades"].append({
            "ticker": ticker,
            "action": action,
            "shares": shares,
            "price": price,
            "timestamp": datetime.now().isoformat()
        })
        return safe_json_response({
            "status": "success",
            "action": action,
            "ticker": ticker,
            "shares": shares,
            "price": price,
            "cash": user_state["cash"],
            "xp_gained": 25,
            "total_xp": user_state["xp"],
            "level": user_state["level"]
        })
    except ValueError:
        return safe_json_response({"error": "Invalid input"}, 400)
    except Exception as e:
        return safe_json_response({"error": f"Trade failed: {str(e)}", "status": "error"}, 500)


@app.route("/api/streaks")
def get_streaks():
    """Get user's streaks"""
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)
    
    if is_guest or not user_id:
        return safe_json_response({
            "streaks": {},
            "is_guest": is_guest,
            "status": "success"
        })
    
    try:
        streaks = get_user_streaks(user_id)
        return safe_json_response({
            "streaks": streaks,
            "status": "success"
        })
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch streaks: {str(e)}", "status": "error"}, 500)


@app.route("/api/watchlist", methods=["GET", "POST", "DELETE"])
def handle_watchlist():
    """Handle watchlist operations"""
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)
    
    if is_guest or not user_id:
        return safe_json_response({
            "watchlist": [],
            "is_guest": is_guest,
            "status": "success"
        })
    
    try:
        if request.method == "GET":
            conn = get_db_connection()
            c = conn.cursor()
            
            watchlist = c.execute(
                "SELECT ticker, added_at, position_order FROM watchlist WHERE user_id = ? ORDER BY position_order ASC",
                (user_id,)
            ).fetchall()
            
            conn.close()
            
            watchlist_items = []
            for item in watchlist:
                ticker = item["ticker"]
                if ticker in ASSET_DATABASE:
                    watchlist_items.append({
                        "ticker": ticker,
                        "name": ASSET_DATABASE[ticker]["name"],
                        "price": generate_realistic_price(ticker),
                        "added_at": item["added_at"],
                        "position_order": item["position_order"]
                    })
            
            return safe_json_response({
                "watchlist": watchlist_items,
                "status": "success"
            })
        
        elif request.method == "POST":
            data = request.get_json() or {}
            ticker = data.get("ticker", "").upper()
            
            if not ticker or ticker not in ASSET_DATABASE:
                return safe_json_response({"error": "Invalid ticker", "status": "error"}, 400)
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # Check if already in watchlist
            existing = c.execute(
                "SELECT id FROM watchlist WHERE user_id = ? AND ticker = ?",
                (user_id, ticker)
            ).fetchone()
            
            if existing:
                conn.close()
                return safe_json_response({"error": "Already in watchlist", "status": "error"}, 400)
            
            # Get max position order
            max_order = c.execute(
                "SELECT MAX(position_order) FROM watchlist WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            
            next_order = (max_order[0] or 0) + 1
            
            c.execute(
                "INSERT INTO watchlist (user_id, ticker, position_order) VALUES (?, ?, ?)",
                (user_id, ticker, next_order)
            )
            
            conn.commit()
            conn.close()
            
            return safe_json_response({
                "status": "success",
                "message": f"{ticker} added to watchlist"
            })
        
        elif request.method == "DELETE":
            data = request.get_json() or {}
            ticker = data.get("ticker", "").upper()
            
            if not ticker:
                return safe_json_response({"error": "Ticker required", "status": "error"}, 400)
            
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
                (user_id, ticker)
            )
            
            conn.commit()
            conn.close()
            
            return safe_json_response({
                "status": "success",
                "message": f"{ticker} removed from watchlist"
            })
    
    except Exception as e:
        return safe_json_response({"error": f"Watchlist operation failed: {str(e)}", "status": "error"}, 500)


@app.route("/api/watchlist/reorder", methods=["POST"])
def reorder_watchlist():
    """Reorder watchlist items"""
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)
    
    if is_guest or not user_id:
        return safe_json_response({"error": "Not authenticated", "status": "error"}, 401)
    
    try:
        data = request.get_json() or {}
        tickers = data.get("tickers", [])
        
        if not tickers:
            return safe_json_response({"error": "Tickers required", "status": "error"}, 400)
        
        conn = get_db_connection()
        c = conn.cursor()
        
        for index, ticker in enumerate(tickers):
            c.execute(
                "UPDATE watchlist SET position_order = ? WHERE user_id = ? AND ticker = ?",
                (index, user_id, ticker.upper())
            )
        
        conn.commit()
        conn.close()
        
        return safe_json_response({
            "status": "success",
            "message": "Watchlist reordered"
        })
    except Exception as e:
        return safe_json_response({"error": f"Reorder failed: {str(e)}", "status": "error"}, 500)


@app.route("/api/news")
def get_market_news():
    """Get market news with caching"""
    try:
        page = int(request.args.get("page", 1))
        page_size = min(10, max(5, int(request.args.get("page_size", 8))))
        all_items = fetch_external_market_news()
        start = (page - 1) * page_size
        paged = all_items[start:start + page_size]
        return safe_json_response({
            "news": paged,
            "page": page,
            "page_size": page_size,
            "total": len(all_items),
            "status": "success"
        })
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch news: {str(e)}", "status": "error"}, 500)


@app.route("/api/analytics")
def get_portfolio_analytics():
    """Get portfolio analytics"""
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)
    
    if is_guest or not user_id:
        return safe_json_response({
            "analytics": {},
            "is_guest": is_guest,
            "status": "success"
        })
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get user cash
        user = c.execute("SELECT cash FROM users WHERE id = ?", (user_id,)).fetchone()
        cash = float(user["cash"] or 0) if user else 0
        
        # Get portfolio
        portfolio = c.execute("SELECT ticker, shares FROM portfolio WHERE user_id = ?", (user_id,)).fetchall()
        
        # Get trades for performance calculation
        trades = c.execute(
            "SELECT ticker, action, shares, price, timestamp FROM trades WHERE user_id = ? ORDER BY timestamp ASC",
            (user_id,)
        ).fetchall()
        
        conn.close()
        
        # Calculate portfolio value and allocation
        portfolio_value = cash
        allocation = {}
        holdings = {}
        
        for item in portfolio:
            ticker = item["ticker"]
            shares = item["shares"]
            price = generate_realistic_price(ticker)
            value = shares * price
            portfolio_value += value
            holdings[ticker] = {"shares": shares, "value": value, "price": price}
            
            # Get sector
            sector = ASSET_DATABASE.get(ticker, {}).get("sector", "Other")
            allocation[sector] = allocation.get(sector, 0) + value
        
        # Calculate profit metrics
        total_invested = 0
        total_current = 0
        best_performer = {"ticker": None, "profit_pct": -999}
        worst_performer = {"ticker": None, "profit_pct": 999}
        
        for ticker, holding in holdings.items():
            # Calculate average cost from trades
            total_shares = 0
            total_cost = 0
            for trade in trades:
                if trade["ticker"] == ticker:
                    if trade["action"] == "buy":
                        total_shares += trade["shares"]
                        total_cost += trade["shares"] * trade["price"]
                    elif trade["action"] == "sell":
                        total_shares -= trade["shares"]
            
            if total_shares > 0:
                avg_cost = total_cost / total_shares
                current_value = holding["value"]
                profit = current_value - total_cost
                profit_pct = (profit / total_cost) * 100 if total_cost > 0 else 0
                
                total_invested += total_cost
                total_current += current_value
                
                if profit_pct > best_performer["profit_pct"]:
                    best_performer = {"ticker": ticker, "profit_pct": profit_pct}
                if profit_pct < worst_performer["profit_pct"]:
                    worst_performer = {"ticker": ticker, "profit_pct": profit_pct}
        
        total_profit = total_current - total_invested
        total_profit_pct = (total_profit / total_invested) * 100 if total_invested > 0 else 0
        
        # Generate performance chart data (mock)
        performance_chart = []
        for i in range(30):
            performance_chart.append(portfolio_value * (0.9 + (i * 0.01) / 30))
        
        analytics = {
            "portfolio_value": portfolio_value,
            "total_profit": total_profit,
            "profit_percentage": total_profit_pct,
            "best_performer": best_performer,
            "worst_performer": worst_performer,
            "allocation": allocation,
            "performance_chart": performance_chart,
            "holdings": holdings
        }
        
        return safe_json_response({
            "analytics": analytics,
            "status": "success"
        })
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch analytics: {str(e)}", "status": "error"}, 500)


@app.route("/api/daily-challenges")
def get_daily_challenges_endpoint():
    """Get user's daily challenges"""
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)
    
    if is_guest or not user_id:
        return safe_json_response({
            "challenges": [],
            "is_guest": is_guest,
            "status": "success"
        })
    
    try:
        challenges = get_daily_challenges(user_id)
        return safe_json_response({
            "challenges": challenges,
            "status": "success"
        })
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch daily challenges: {str(e)}", "status": "error"}, 500)


@app.route("/api/daily-challenges/update", methods=["POST"])
def update_daily_challenge_endpoint():
    """Update daily challenge progress"""
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)
    
    if is_guest or not user_id:
        return safe_json_response({
            "updated": False,
            "status": "success"
        })
    
    try:
        data = request.get_json() or {}
        challenge_type = data.get("challenge_type", "")
        increment = data.get("increment", 1)
        
        if not challenge_type:
            return safe_json_response({"error": "Challenge type required", "status": "error"}, 400)
        
        newly_completed = update_daily_challenge(user_id, challenge_type, increment)
        
        # Award XP if newly completed
        total_xp_bonus = 0
        if newly_completed:
            definition = DAILY_CHALLENGE_DEFINITIONS.get(challenge_type, {})
            xp_reward = definition.get("xp_reward", 0)
            total_xp_bonus += xp_reward
            
            # Update user XP
            user = find_user_by_id(user_id)
            if user:
                new_xp = int(user["xp"] or 0) + xp_reward
                new_level = 1 + (new_xp // 100)
                update_user_stats(user_id, xp=new_xp, level=new_level)
        
        return safe_json_response({
            "updated": True,
            "newly_completed": newly_completed,
            "xp_bonus": total_xp_bonus,
            "status": "success"
        })
    except Exception as e:
        return safe_json_response({"error": f"Failed to update challenge: {str(e)}", "status": "error"}, 500)


@app.route("/api/achievements")
def get_achievements():
    """Get user's achievements"""
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)
    
    if is_guest or not user_id:
        return safe_json_response({
            "achievements": [],
            "is_guest": is_guest,
            "status": "success"
        })
    
    try:
        achievements = get_user_achievements(user_id)
        achievement_details = []
        for ach in achievements:
            definition = ACHIEVEMENT_DEFINITIONS.get(ach["type"], {})
            achievement_details.append({
                "type": ach["type"],
                "name": definition.get("name", ach["type"]),
                "description": definition.get("description", ""),
                "xp_bonus": definition.get("xp_bonus", 0),
                "achieved_at": ach["achieved_at"]
            })
        
        return safe_json_response({
            "achievements": achievement_details,
            "status": "success"
        })
    except Exception as e:
        return safe_json_response({"error": f"Failed to fetch achievements: {str(e)}", "status": "error"}, 500)


@app.route("/api/achievements/check", methods=["POST"])
def check_achievements():
    """Check for new achievements after an action"""
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)
    
    if is_guest or not user_id:
        return safe_json_response({
            "new_achievements": [],
            "status": "success"
        })
    
    try:
        data = request.get_json() or {}
        action = data.get("action", "")
        new_achievements = []
        
        # Check achievements based on action
        if action == "trade":
            if check_and_award_achievement(user_id, "first_trade"):
                new_achievements.append("first_trade")
            if check_profit_achievement(user_id) and check_and_award_achievement(user_id, "first_profit"):
                new_achievements.append("first_profit")
            if check_diversified_achievement(user_id) and check_and_award_achievement(user_id, "diversified"):
                new_achievements.append("diversified")
        elif action == "lesson":
            if check_and_award_achievement(user_id, "first_lesson"):
                new_achievements.append("first_lesson")
        elif action == "quiz":
            if check_and_award_achievement(user_id, "first_quiz"):
                new_achievements.append("first_quiz")
        elif action == "level_up":
            user = find_user_by_id(user_id)
            if user:
                level = int(user["level"] or 1)
                if level >= 5 and check_and_award_achievement(user_id, "level_5"):
                    new_achievements.append("level_5")
                if level >= 10 and check_and_award_achievement(user_id, "level_10"):
                    new_achievements.append("level_10")
        
        # Award XP bonuses for new achievements
        total_xp_bonus = 0
        for ach_type in new_achievements:
            definition = ACHIEVEMENT_DEFINITIONS.get(ach_type, {})
            xp_bonus = definition.get("xp_bonus", 0)
            total_xp_bonus += xp_bonus
        
        if total_xp_bonus > 0:
            user = find_user_by_id(user_id)
            if user:
                new_xp = int(user["xp"] or 0) + total_xp_bonus
                new_level = 1 + (new_xp // 100)
                update_user_stats(user_id, xp=new_xp, level=new_level)
        
        achievement_details = []
        for ach_type in new_achievements:
            definition = ACHIEVEMENT_DEFINITIONS.get(ach_type, {})
            achievement_details.append({
                "type": ach_type,
                "name": definition.get("name", ach_type),
                "description": definition.get("description", ""),
                "xp_bonus": definition.get("xp_bonus", 0)
            })
        
        return safe_json_response({
            "new_achievements": achievement_details,
            "total_xp_bonus": total_xp_bonus,
            "status": "success"
        })
    except Exception as e:
        return safe_json_response({"error": f"Achievement check failed: {str(e)}", "status": "error"}, 500)


@app.route("/api/reward/<int:amount>")
def reward(amount):
    try:
        if amount <= 0 or amount > 500:
            return safe_json_response({"error": "Invalid reward amount"}, 400)
        user_state["xp"] += amount
        user_state["streak"] += 1
        user_state["level"] = 1 + (user_state["xp"] // 100)
        user_id = session.get("user_id")
        if user_id:
            user = find_user_by_id(user_id)
            if user:
                new_xp = int(user["xp"] or 0) + amount
                new_streak = int(user["streak"] or 0) + 1
                new_level = 1 + (new_xp // 100)
                update_user_stats(user_id, xp=new_xp, level=new_level, streak=new_streak)
        return safe_json_response({
            "status": "success",
            "xp_gained": amount,
            "total_xp": user_state["xp"],
            "level": user_state["level"],
            "streak": user_state["streak"]
        })
    except Exception:
        return safe_json_response({"error": "Reward failed", "status": "error"}, 500)


@app.route("/api/quiz/<int:points>/<is_correct>")
def process_quiz_result(points, is_correct):
    try:
        is_correct_bool = is_correct.lower() == "true"
        if not is_correct_bool:
            return safe_json_response({"status": "incorrect", "feedback": "Not quite! Try again."})
        if points <= 0 or points > 100:
            points = 50
        user_state["xp"] += points
        user_state["level"] = 1 + (user_state["xp"] // 100)
        user_id = session.get("user_id")
        if user_id:
            user = find_user_by_id(user_id)
            if user:
                new_xp = int(user["xp"] or 0) + points
                new_level = 1 + (new_xp // 100)
                update_user_stats(user_id, xp=new_xp, level=new_level)
        return safe_json_response({
            "status": "correct",
            "xp_gained": points,
            "total_xp": user_state["xp"],
            "level": user_state["level"],
            "feedback": f"Correct! +{points} XP"
        })
    except Exception:
        return safe_json_response({"error": "Quiz processing failed", "status": "error"}, 500)


@app.route("/api/assets")
def list_assets():
    try:
        assets = [{
            "ticker": ticker,
            "name": info["name"],
            "price": generate_realistic_price(ticker)
        } for ticker, info in ASSET_DATABASE.items()]
        return safe_json_response({"assets": assets, "status": "success"})
    except Exception:
        return safe_json_response({"error": "Failed to fetch assets", "status": "error"}, 500)


@app.errorhandler(404)
def not_found(e):
    return safe_json_response({"error": "Endpoint not found"}, 404)


@app.errorhandler(500)
def server_error(e):
    return safe_json_response({"error": "Internal server error"}, 500)


if __name__ == "__main__":
    try:
        print(">>> APP STARTING")
        ensure_database()
        port = int(os.environ.get("PORT", 10000))
        print("APP STARTING SUCCESSFULLY")
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception:
        traceback.print_exc()
        raise
