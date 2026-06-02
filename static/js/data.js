export const startingCash = 10000;

export const goal = {
    target: 15000,
    rewardXP: 100,
    description: "Reach $15,000 total assets and earn bonus XP."
};

export const levels = [
    { threshold: 0, title: "Rookie" },
    { threshold: 100, title: "Apprentice" },
    { threshold: 300, title: "Trader" },
    { threshold: 600, title: "Investor" },
    { threshold: 1000, title: "Market Pro" }
];

export const lessons = [
    {
        title: "What is investing?",
        content: "Investing means using money today to build more money tomorrow. When you invest, you choose a plan so your money can grow over months and years instead of being spent right away.",
        highlights: [
            "Investing is different from saving: saving keeps your money safe while investing helps it grow.",
            "Stocks represent ownership in a company, while ETFs are baskets of many stocks.",
            "The best investing goal is steady progress over time, not quick luck."
        ],
        example: "Think about a company you already like. If that company grows over the next few years, your investment may also grow.",
        challenge: "Pick one stock you're curious about and think why it might be a good long-term choice."
    },
    {
        title: "Stocks vs ETFs",
        content: "Stocks are pieces of one company, and ETFs are groups of stocks bundled together. ETFs can be easier for beginners because one investment gives you access to many companies.",
        highlights: [
            "One stock can move up or down fast based on news about that company.",
            "An ETF spreads your money over several companies so one drop doesn't hurt as much.",
            "ETFs are useful when you want broad market exposure without choosing every stock yourself."
        ],
        example: "Buying an ETF for technology can feel safer than buying just one tech stock, because it includes lots of companies.",
        challenge: "Find one stock and one ETF that both include a company you use every day."
    },
    {
        title: "Diversification",
        content: "Diversification means spreading your investments across different companies, industries, or types of assets. It helps reduce the risk of losing a lot of money on one single investment.",
        highlights: [
            "Putting all your cash in one stock is risky because that company's troubles affect your whole investment.",
            "A mix of industries can keep your portfolio steadier when one part of the market dips.",
            "Diversification is not a guarantee, but it helps protect your progress."
        ],
        example: "If you have some money in a tech stock and some in a consumer goods ETF, one may rise while the other falls.",
        challenge: "List three different kinds of companies or industries you could include in a beginner portfolio."
    },
    {
        title: "Risk and reward",
        content: "Investing always has risk. Some investments can grow quickly, but they can also drop quickly. The smartest investors balance risk with careful planning.",
        highlights: [
            "Higher rewards usually come with higher risk.",
            "Stable companies usually offer smoother growth but slower gains.",
            "Think about your goals before choosing a risky or safe investment."
        ],
        example: "A new startup might promise big gains, but a well-known brand can be easier to understand and handle.",
        challenge: "Choose one high-risk idea and one lower-risk idea, then compare why each feels different to you."
    },
    {
        title: "Long-term thinking",
        content: "Successful investing is often about patience. Prices go up and down, but staying focused on your long-term target makes it easier to avoid reactionary trading.",
        highlights: [
            "Short-term price swings are normal and do not always mean the investment is bad.",
            "Compound growth works best when you stay invested for years.",
            "Review your plan, but do not panic when the market moves."
        ],
        example: "If you invest today and leave it alone, you can benefit from years of growth and reinvested gains.",
        challenge: "Write down one long-term goal you want your virtual portfolio to reach."
    },
    {
        title: "Building confidence",
        content: "Practice makes investing easier. Use your virtual cash to test ideas, learn from mistakes, and build the skills you need before using real money.",
        highlights: [
            "Every trade teaches you something, even if it does not make money.",
            "Track your decisions so you can review what worked and what did not.",
            "Good investing comes from learning and patience, not from guessing."
        ],
        example: "Try buying a small number of shares and then check how the stock behaves over several days.",
        challenge: "After your next trade, note why you bought or sold and what you want to learn from it."
    },
    {
        title: "Understanding fees",
        content: "Fees and costs can reduce your earnings. The less you pay in fees, the more of your gains you keep. Always be aware of the charges you may face.",
        highlights: [
            "Some brokers charge commissions or small fees for trades.",
            "ETFs often have management fees that slowly reduce returns.",
            "Choosing low-cost investments helps more of your money stay invested."
        ],
        example: "If two ETFs give the same growth but one has lower fees, the cheaper one keeps more profit in your pocket.",
        challenge: "Look for one example of a low-cost ETF and one example of a higher-cost investment."
    },
    {
        title: "Compound growth",
        content: "Compound growth happens when earnings are reinvested and then generate their own earnings. Over time, this can make a small return become much bigger.",
        highlights: [
            "Money grows faster when profits are reinvested.",
            "The longer you stay invested, the stronger compounding becomes.",
            "Small, steady gains add up more than a single big win."
        ],
        example: "A $100 investment that grows by 5% each year becomes much larger after several years than just one quick gain.",
        challenge: "Imagine today's virtual cash growing over 5 years and think how patience helps your total value."
    }
];

export const quizQuestions = [
    {
        q: "What does ETF stand for?",
        opts: ["Exchange Traded Fund", "Electronic Tax Form", "Equity Transfer"],
        answer: 0,
        hint: "The first word is a common investing term for a market product.",
        explanation: "ETF means Exchange Traded Fund. It is a basket of assets traded like a single stock. ETFs make it easier to own many companies at once."
    },
    {
        q: "What is a bull market?",
        opts: ["Zero trading volume", "Prices rising", "Prices falling"],
        answer: 1,
        hint: "Think of the animal that charges upward.",
        explanation: "A bull market means prices are generally rising. It is a positive market environment where many investors feel confident."
    },
    {
        q: "Why diversify your portfolio?",
        opts: ["To avoid learning", "To lower risk", "To make taxes higher"],
        answer: 1,
        hint: "Diversify means spread your money around.",
        explanation: "Diversifying spreads risk across different investments. That way, one company falling does not hurt your entire portfolio as much."
    },
    {
        q: "What is a dividend?",
        opts: ["A trading fee", "A type of loan", "A company payout to shareholders"],
        answer: 2,
        hint: "It is money paid back to owners of the company.",
        explanation: "A dividend is a company payout to shareholders from profits. Some companies pay dividends regularly as a reward for owning their stock."
    },
    {
        q: "What does market cap measure?",
        opts: ["Daily profit", "Company size", "Broker fee"],
        answer: 1,
        hint: "It is based on share price times the number of shares.",
        explanation: "Market cap measures company size by multiplying stock price by total shares outstanding. It helps compare companies by scale."
    },
    {
        q: "Why is cash important in investing?",
        opts: ["Because it always grows", "For chance and safety", "To avoid all risk"],
        answer: 1,
        hint: "Cash gives you flexibility and protection.",
        explanation: "Cash is important because it helps you take opportunities and cover surprises without selling investments at the wrong time."
    },
    {
        q: "What does portfolio mean?",
        opts: ["A loan agreement", "A group of investments", "A bank account"],
        answer: 1,
        hint: "It is a collection of what you own.",
        explanation: "A portfolio is a group of investments you own together. It shows your overall financial picture."
    },
    {
        q: "What is a good investing habit?",
        opts: ["Ignore fees", "Review performance regularly", "Trade every hour"],
        answer: 1,
        hint: "Smart investors check results without overtrading.",
        explanation: "Reviewing performance regularly helps you understand what is working and what is not. It is better than trading too often."
    },
    {
        q: "What is a stop-loss order?",
        opts: ["A request to buy at a lower price", "A request to sell to limit losses", "A dividend payment"],
        answer: 1,
        hint: "It helps protect you from losing too much.",
        explanation: "A stop-loss order is a sell request triggered at a certain price to limit losses. It is a risk-management tool."
    },
    {
        q: "What is a blue-chip stock?",
        opts: ["A small startup", "A large stable company", "A high-risk penny stock"],
        answer: 1,
        hint: "Think of established companies with a strong reputation.",
        explanation: "A blue-chip stock is a large, stable company known for reliable performance. These stocks are often less risky than smaller companies."
    },
    {
        q: "What does a broker do?",
        opts: ["Provides investment advice and executes trades", "Insures your portfolio", "Guarantees returns"],
        answer: 0,
        hint: "A broker helps you buy and sell investments.",
        explanation: "A broker executes trades for investors and may offer guidance. They do not guarantee returns or insure your portfolio."
    },
    {
        q: "Why keep an emergency fund?",
        opts: ["To pay for surprises without selling investments", "To spend more on trading", "To avoid taxes"],
        answer: 0,
        hint: "It helps you handle unexpected costs safely.",
        explanation: "An emergency fund keeps you from selling investments at a bad time when unexpected expenses happen. It provides financial safety."
    },
    {
        q: "Which action helps compound growth?",
        opts: ["Withdraw dividends immediately", "Reinvest earnings", "Only trade during market peaks"],
        answer: 1,
        hint: "Compound growth works when you let earnings stay invested.",
        explanation: "Reinvesting earnings helps compound growth because your money earns on top of itself over time."
    },
    {
        q: "What is a bear market?",
        opts: ["Prices rising quickly", "Prices falling steadily", "No companies are trading"],
        answer: 1,
        hint: "Think of the opposite of a bull market.",
        explanation: "A bear market means prices are falling steadily. It often happens when investors are worried about the economy."
    },
    {
        q: "What is an index fund?",
        opts: ["A fund that follows a market index", "A bank savings account", "A type of loan"],
        answer: 0,
        hint: "It tracks a group of companies, not one.",
        explanation: "An index fund invests in many companies that match a market index. It is a passive way to track broad market performance."
    },
    {
        q: "What does liquidity mean?",
        opts: ["How quickly you can buy or sell", "How expensive an investment is", "How popular a company is"],
        answer: 0,
        hint: "Liquid means easy to move.",
        explanation: "Liquidity is how quickly an asset can be bought or sold without changing its price too much. Cash and large stocks are usually more liquid."
    },
    {
        q: "What is volatility?",
        opts: ["How often prices change", "A company’s size", "A type of stock"],
        answer: 0,
        hint: "It measures ups and downs.",
        explanation: "Volatility describes how much and how quickly prices move up and down. High volatility means bigger swings."
    },
    {
        q: "What is an expense ratio?",
        opts: ["The yearly cost of owning a fund", "The amount of profit made", "The fee to buy a stock"],
        answer: 0,
        hint: "It is a percentage charged by a fund.",
        explanation: "Expense ratio is the annual cost to manage a fund, such as an ETF. Lower expense ratios keep more money working for you."
    },
    {
        q: "What is an IPO?",
        opts: ["When a company sells stock to the public for the first time", "When a company pays a dividend", "When a stock is split"],
        answer: 0,
        hint: "It is the first time shares are offered.",
        explanation: "IPO stands for Initial Public Offering. It is when a private company becomes public by selling stock to investors."
    },
    {
        q: "What does a stock split do?",
        opts: ["Increases the number of shares while reducing price per share", "Doubles investor returns", "Removes a company from the market"],
        answer: 0,
        hint: "Share count goes up but value stays similar.",
        explanation: "A stock split increases the number of shares and lowers the price per share. The company’s total value stays the same."
    },
    {
        q: "What is a market order?",
        opts: ["Buy or sell immediately at current price", "Buy at a specific lower price", "Sell only after one week"],
        answer: 0,
        hint: "It happens right away.",
        explanation: "A market order buys or sells a stock immediately at the current price. It is useful when execution speed matters."
    },
    {
        q: "What is a limit order?",
        opts: ["Trade only if the price reaches a set level", "Trade immediately at any price", "Avoid trading fees"],
        answer: 0,
        hint: "You choose the price you want.",
        explanation: "A limit order buys or sells only at a specific price or better. It gives you more price control than a market order."
    },
    {
        q: "Why is long-term thinking important?",
        opts: ["It helps ignore short-term ups and downs", "It ensures instant profit", "It avoids saving money"],
        answer: 0,
        hint: "Investing is not a sprint.",
        explanation: "Long-term thinking helps investors stay focused through market swings. It lets compound growth work and reduces the impact of short-term volatility."
    },
    {
        q: "Why should you track your investments?",
        opts: ["To understand what is working", "To avoid taxes", "To spend more money"],
        answer: 0,
        hint: "Learning is part of investing.",
        explanation: "Tracking helps you see which investments are doing well and which need review. It supports smarter decision-making."
    },
    {
        q: "What is an asset allocation?",
        opts: ["Distributing money across stocks, bonds, and cash", "Buying a single stock", "Saving in a piggy bank"],
        answer: 0,
        hint: "It means choosing different asset types.",
        explanation: "Asset allocation means spreading money across different investment types. It helps balance risk and return."
    },
    {
        q: "What does P/E ratio measure?",
        opts: ["Company price relative to earnings", "Daily share volume", "Annual dividend amount"],
        answer: 0,
        hint: "P/E compares price and profits.",
        explanation: "P/E ratio shows how much investors pay for each dollar of earnings. It can help compare company value."
    },
    {
        q: "What is dollar-cost averaging?",
        opts: ["Investing the same amount regularly", "Buying only when prices drop", "Selling every month"],
        answer: 0,
        hint: "It spreads buying over time.",
        explanation: "Dollar-cost averaging means investing a fixed amount on a schedule. It reduces the risk of buying all at once."
    },
    {
        q: "What is a bond?",
        opts: ["A loan to a company or government", "A type of stock", "A bank account feature"],
        answer: 0,
        hint: "It pays interest.",
        explanation: "A bond is a loan investors give to companies or governments. They receive interest and return of principal later."
    },
    {
        q: "What is dividend yield?",
        opts: ["Dividends divided by share price", "The number of shares owned", "The amount of cash in your account"],
        answer: 0,
        hint: "It shows income relative to price.",
        explanation: "Dividend yield is the annual dividend payment divided by the stock price. It helps compare income from different stocks."
    },
    {
        q: "Why is an emergency fund not the same as investments?",
        opts: ["It is for short-term needs, not growth", "It always pays more interest", "It guarantees higher returns"],
        answer: 0,
        hint: "Emergency money is safety money.",
        explanation: "An emergency fund is cash kept safe for surprises. Investments are meant for long-term growth, not immediate spending."
    },
    {
        q: "What is rebalancing?",
        opts: ["Adjusting your holdings to keep a target mix", "Buying as many stocks as possible", "Holding only one investment"],
        answer: 0,
        hint: "It keeps your portfolio balanced.",
        explanation: "Rebalancing means selling some investments and buying others to restore your planned allocation. It helps manage risk."
    },
    {
        q: "What is a penny stock?",
        opts: ["A low-priced, high-risk stock", "A share of a major company", "A type of government bond"],
        answer: 0,
        hint: "It is cheap but risky.",
        explanation: "A penny stock is a very low-priced stock that often has high risk and low liquidity. It is usually not a good choice for beginners."
    },
    {
        q: "What is a blue-chip company known for?",
        opts: ["Stability and reputation", "Fast growth only", "No dividends"],
        answer: 0,
        hint: "It is often large and trusted.",
        explanation: "A blue-chip company is known for stability, strong performance, and a solid reputation. It is often a reliable long-term investment."
    },
    {
        q: "Why should you avoid trading too often?",
        opts: ["Because frequent trades can hurt returns", "Because it is illegal", "Because it always guarantees loss"],
        answer: 0,
        hint: "More trades mean more costs.",
        explanation: "Trading too often can increase fees and taxes, and it is hard to beat the market with constant trades. Patience can help returns."
    },
    {
        q: "What is a company’s sector?",
        opts: ["The industry group it belongs to", "The stock price range", "The number of shareholders"],
        answer: 0,
        hint: "It describes the company’s business type.",
        explanation: "A sector is the part of the economy a company operates in, like technology, healthcare, or consumer goods."
    },
    {
        q: "What is a financial goal?",
        opts: ["A specific target for your money", "A type of investment fee", "A stock trading strategy"],
        answer: 0,
        hint: "It is what you are saving or investing for.",
        explanation: "A financial goal is a clear target like saving for college, a car, or a future retirement. Goals help guide investing decisions."
    },
    {
        q: "How does inflation affect money?",
        opts: ["It reduces buying power over time", "It makes money worth more", "It only affects banks"],
        answer: 0,
        hint: "Prices generally rise.",
        explanation: "Inflation means prices go up, so the same amount of money buys less over time. Investing can help protect against inflation."
    },
    {
        q: "What is a profit target?",
        opts: ["A price at which you plan to sell for gain", "The cost of buying a stock", "A fee paid to brokers"],
        answer: 0,
        hint: "It is a selling goal.",
        explanation: "A profit target is the price at which you plan to sell an investment to take gains. It helps make decisions more disciplined."
    },
    {
        q: "What does holding period mean?",
        opts: ["How long you keep an investment", "The number of shares you own", "The date you buy a stock"],
        answer: 0,
        hint: "It is the time you hold a position.",
        explanation: "The holding period is how long you keep an investment before selling it. Longer periods often reduce short-term risk."
    },
    {
        q: "What is a market index?",
        opts: ["A benchmark of many stocks", "A single stock company", "A type of savings account"],
        answer: 0,
        hint: "It tracks the market.",
        explanation: "A market index measures the performance of a group of stocks, like the S&P 500 or Nasdaq. Investors use it to compare results."
    },
    {
        q: "What is active investing?",
        opts: ["Picking investments yourself", "Buying only index funds", "Holding cash forever"],
        answer: 0,
        hint: "You make decisions directly.",
        explanation: "Active investing means choosing individual stocks or funds based on research. It can offer opportunity but often requires more effort."
    },
    {
        q: "What is passive investing?",
        opts: ["Following a market index", "Trading every day", "Borrowing to buy more stocks"],
        answer: 0,
        hint: "It is a hands-off approach.",
        explanation: "Passive investing means buying index funds or ETFs that track the market. It usually costs less and is easier to maintain."
    },
    {
        q: "What is a management fee?",
        opts: ["The cost of running a fund", "A penalty for selling stocks", "A reward for investors"],
        answer: 0,
        hint: "Funds charge it to manage your money.",
        explanation: "A management fee is the yearly cost charged by fund managers. Lower fees mean more of your investment stays in the account."
    },
    {
        q: "Why research a company before buying its stock?",
        opts: ["To understand its business and risks", "To avoid using the internet", "To pay more fees"],
        answer: 0,
        hint: "Knowing the company helps you decide.",
        explanation: "Research helps you understand whether a company is healthy, growing, and worth investing in. It reduces the chances of bad surprises."
    },
    {
        q: "What is a rebalance reminder?",
        opts: ["A signal to adjust your portfolio mix", "A message from your bank", "A fee notice"],
        answer: 0,
        hint: "It is about keeping your plan balanced.",
        explanation: "A rebalance reminder is a note to review your portfolio and make sure your asset mix still matches your goals."
    },
    {
        q: "What is a good first step in investing?",
        opts: ["Learn the basics and start small", "Buy the most expensive stock", "Copy a friend’s trades"],
        answer: 0,
        hint: "Start with knowledge and small amounts.",
        explanation: "A good first step is learning the basics, making a plan, and investing carefully with small amounts."
    },
    {
        q: "What is a sector ETF?",
        opts: ["An ETF focused on one industry", "A bank account for trading", "A loan from a broker"],
        answer: 0,
        hint: "It targets one part of the market.",
        explanation: "A sector ETF invests in companies from one industry, like technology or healthcare. It lets you focus on a specific area."
    },
    {
        q: "What is a long-term goal?",
        opts: ["A plan for money in several years", "A quick profit target", "A daily trading rule"],
        answer: 0,
        hint: "It looks ahead years, not days.",
        explanation: "A long-term goal is something you want to achieve with money over years, such as buying a house or saving for retirement."
    },
    {
        q: "Why is learning from mistakes useful?",
        opts: ["It helps you improve over time", "It guarantees you will lose money", "It means you should stop investing"],
        answer: 0,
        hint: "Mistakes are part of the learning process.",
        explanation: "Learning from mistakes helps you make better choices in the future. It is a key part of growing as an investor."
    },
    {
        q: "What is a dividend reinvestment plan?",
        opts: ["Using dividends to buy more shares", "Paying a fee to sell stocks", "Saving dividends as cash only"],
        answer: 0,
        hint: "It keeps money working for you.",
        explanation: "A dividend reinvestment plan automatically uses dividends to buy more shares, helping your investment grow through compounding."
    },
    {
        q: "What is a target price?",
        opts: ["A goal price for a stock", "The highest possible stock value", "A fixed bank rate"],
        answer: 0,
        hint: "It is a future price estimate.",
        explanation: "A target price is an estimate of where a stock could be worth in the future. Analysts use it to help set goals."
    },
    {
        q: "What is risk tolerance?",
        opts: ["How much ups and downs you can handle", "The same as your age", "A type of investment fee"],
        answer: 0,
        hint: "It is about your comfort with uncertainty.",
        explanation: "Risk tolerance is how much volatility you can accept in your investments without panicking or selling too soon."
    },
    {
        q: "What is a stock’s ticker symbol?",
        opts: ["A short code for the stock", "The company’s slogan", "The CEO’s name"],
        answer: 0,
        hint: "It is the symbol used on exchanges.",
        explanation: "A ticker symbol is a short code used to identify a stock, such as AAPL for Apple or TSLA for Tesla."
    },
    {
        q: "What is a financial glossary useful for?",
        opts: ["Understanding investing terms", "Keeping track of passwords", "Finding grocery deals"],
        answer: 0,
        hint: "It explains words you need to know.",
        explanation: "A financial glossary helps you understand investing language and avoid confusion when learning about markets."
    },
    {
        q: "What is a holding period return?",
        opts: ["The profit earned while holding an investment", "The expense ratio of a fund", "The number of shares owned"],
        answer: 0,
        hint: "It measures actual gain over time.",
        explanation: "Holding period return is the gain or loss you earn while keeping an investment for a set time."
    },
    {
        q: "What is a stock quote?",
        opts: ["The current price of a stock", "A company’s slogan", "A forecast of your profit"],
        answer: 0,
        hint: "It shows the latest price.",
        explanation: "A stock quote is the current market price of a stock. It updates during trading hours."
    },
    {
        q: "Why do people invest in ETFs?",
        opts: ["Because they offer instant diversification", "Because they are free", "Because they guarantee no loss"],
        answer: 0,
        hint: "ETFs group many assets together.",
        explanation: "People invest in ETFs because they can own many stocks or bonds at once, making diversification easier."
    },
    {
        q: "What is portfolio value?",
        opts: ["The total worth of all your investments", "The number of trades you made", "The fees you paid"],
        answer: 0,
        hint: "It is the sum of your holdings.",
        explanation: "Portfolio value is the total amount your investments are worth at current prices."
    },
    {
        q: "What is a trading fee?",
        opts: ["A cost paid to buy or sell investments", "A type of dividend", "The investment return"],
        answer: 0,
        hint: "It is a transaction cost.",
        explanation: "Trading fees are costs charged when buying or selling investments. Keeping fees low helps your returns."
    },
    {
        q: "What is a cash reserve?",
        opts: ["Money kept available for emergencies or opportunities", "Always invested money", "A loan from a bank"],
        answer: 0,
        hint: "It is your backup cash.",
        explanation: "A cash reserve is money kept safe and available in case you need it quickly. It helps prevent selling investments at the wrong time."
    },
    {
        q: "What is a portfolio remix?",
        opts: ["Another term for portfolio rebalancing", "A type of dividend", "A stock price announcement"],
        answer: 0,
        hint: "It means adjusting your holdings.",
        explanation: "A portfolio remix is when you adjust your investment mix to keep it aligned with your goals."
    },
    {
        q: "What is a financial goal timeline?",
        opts: ["The schedule for when you want goals achieved", "The stock exchange hours", "The due date for a loan"],
        answer: 0,
        hint: "It says when you want to reach a goal.",
        explanation: "A financial goal timeline sets the time frame for achieving savings or investment targets, like short-term or long-term goals."
    },
    {
        q: "What is the main advantage of investing early?",
        opts: ["More time for compound growth", "Instant profits", "No risk"],
        answer: 0,
        hint: "Time is one of the investor’s best advantages.",
        explanation: "Investing early gives your money more time to grow through compound returns, which can make a big difference over years."
    },
    {
        q: "What does a quiz streak reward encourage?",
        opts: ["Consistency and good answers", "Buying more shares", "Selling every trade"],
        answer: 0,
        hint: "It is about doing well repeatedly.",
        explanation: "A quiz streak reward encourages learning consistently and answering several questions correctly in a row."
    },
    {
        q: "What is a safe investing mindset?",
        opts: ["Focus on learning and long-term habits", "Expect quick riches", "Only trade when friends do"],
        answer: 0,
        hint: "It is calm and patient.",
        explanation: "A safe investing mindset focuses on learning, planning, and staying patient rather than chasing fast wins."
    }
];

export const tips = [
    "Start with companies you understand and follow their products.",
    "A long-term strategy often beats trying to time daily moves.",
    "Keep some cash safe for opportunities or emergencies.",
    "Investing regularly can help your money grow over time.",
    "Research before you buy and avoid chasing hype."
];

export const glossaryItems = [
    { term: "Stock", definition: "A share of ownership in one company." },
    { term: "ETF", definition: "A collection of stocks or bonds sold as one investment." },
    { term: "Dividend", definition: "A payout companies give shareholders from profits." },
    { term: "Diversification", definition: "Spreading investments to reduce risk." }
];
