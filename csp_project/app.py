from flask import Flask, jsonify, render_template, request, session
import yfinance as yf
import os
import random
import time
import sqlite3
import hashlib
from datetime import datetime, timedelta
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================
DATABASE_FILE = "tradelearn.db"

def init_db():
    """Initialize SQLite database for users and quizzes."""
    conn = sqlite3.connect(DATABASE_FILE)
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

    conn.commit()
    conn.close()

init_db()

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
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


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
        return render_template("index.html")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return render_template("index.html")


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
def search_stocks():
    try:
        query = request.args.get("q", "").strip()
        if not query or len(query) < 1:
            return safe_json_response({"results": [], "status": "empty"})

        results = fuzzy_search(query)
        formatted_results = []
        for item in results:
            ticker, info = item
            formatted_results.append({
                "ticker": ticker,
                "name": info["name"],
                "sector": info.get("sector", ""),
                "price": generate_realistic_price(ticker)
            })

        return safe_json_response({"results": formatted_results, "status": "success"})
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


@app.route("/api/learning")
def get_learning_curriculum():
    try:
        return safe_json_response({"chapters": INTEGRATE_LEARNING_CURRICULUM, "total_chapters": len(INTEGRATE_LEARNING_CURRICULUM), "status": "success"})
    except Exception:
        return safe_json_response({"error": "Failed to fetch curriculum", "status": "error"}, 500)


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
    user_id = session.get("user_id")
    if user_id:
        persisted = load_user_state_from_db(user_id)
        if persisted is None:
            return safe_json_response({"authenticated": False, "error": "User not found"}, 404)
        return safe_json_response(persisted)

    return safe_json_response({
        "authenticated": False,
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
        ticker = ticker.upper()
        action = action.lower()
        if ticker not in ASSET_DATABASE:
            return safe_json_response({"error": "Invalid ticker"}, 400)
        if shares <= 0:
            return safe_json_response({"error": "Shares must be positive"}, 400)

        price = generate_realistic_price(ticker)
        total_cost = round(price * shares, 2)
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
