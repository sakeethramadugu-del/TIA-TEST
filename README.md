# ApexVest Academy

ApexVest Academy is a friendly learning app for teens who want to practice investing without any real money.

## What this app does

- Shows stock prices and charts for companies like Apple, Microsoft, and Tesla.
- Lets you buy and sell virtual shares using pretend cash.
- Tracks your portfolio, experience points (XP), and activity history.
- Includes simple lessons and quiz questions to help you learn.
- Works in your browser with a clean, easy layout.

## How to use it

1. Open the app in your web browser.
2. Choose a stock symbol like `AAPL`, `MSFT`, or `TSLA`.
3. Use the Buy or Sell controls to practice trading with virtual cash.
4. Read the lessons to learn key investing ideas.
5. Answer quiz questions to earn XP and grow your score.
6. Watch your portfolio update as you trade.

## Why this is useful

- Practice investing without risk.
- Learn important concepts like saving, diversification, and long-term growth.
- Build confidence before using real money.
- Make learning more fun with quizzes and rewards.

## Starting the app

If you want to run the app yourself, follow these steps:

1. Open a terminal or command prompt.
2. Go to this project folder.
3. Install the required Python packages:

```bash
pip install -r requirements.txt
```

4. Start the app:

```bash
python app.py
```

5. Open this address in your browser on the same machine:

```text
http://127.0.0.1:10000
```

6. To open the app from another device on the same network, use the host machine IP address:

```text
http://<YOUR_COMPUTER_IP>:10000
```

> If you want users on a different internet connection to access it, run the app on a server with a public IP address or use a tunnel service like `ngrok`.

## Helpful tips

- Start with a small amount of shares when you buy.
- Check the chart to see how the stock price moves.
- Use the lessons first if you are new to investing.
- Try different stocks to learn how the market works.

## Technical note (optional)

The app uses Python and a library called `yfinance` to get stock price data. You do not need to know these details to use the app.
