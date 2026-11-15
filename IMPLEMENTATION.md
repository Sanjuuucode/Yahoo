# Implementation Guide & Plan of Action (Simple English)

Welcome to the **Yahoo Finance Data Downloader**! This document explains everything about how this tool works, how to use it, and our step-by-step plan of action in simple, straightforward English.

---

## 🔒 Review & Approval Protocol (User-First Workflow)

**Rule for all future changes:**
Before any direct code changes or executions are performed:
1. **Write the Plan First**: Any proposed plan of action, file modifications, and expected behavior will be written right here in `IMPLEMENTATION.md` under **Section 8: Proposed Changes (Pending Review)** in simple English.
2. **Review & Approval**: You review the written proposal first.
3. **Execution**: No code in `yfin.py` or any other file will be modified until you explicitly give your approval to proceed.

---

## 1. What Does This App Do?

This app is a visual web tool built using **Streamlit**, **yfinance**, and **Altair**. It allows you to:
1. Type in any stock, cryptocurrency, or index symbol from around the world.
2. Click a button to get the latest historical price data.
3. See dynamic price charts (Line & Candlestick), high/low prices, and trading volume.
4. Click a button to download all that data as a clean **CSV file** that opens smoothly in **Microsoft Excel** or Google Sheets.

---

## 2. Quick Start: How to Use It in 3 Easy Steps

Here is the exact action plan to get your data:

```text
Step 1: Choose your stock (Sidebar on the left)
        Default is "AAPL" (Apple). You can type any stock like "RELIANCE.NS" or "MSFT".
        Choose your date range (e.g. 1 Year) and interval (e.g. Daily).
        │
        ▼
Step 2: Click the "▶️ Execute & Fetch Data" button
        The app connects to Yahoo Finance and pulls down the data in 1-2 seconds.
        │
        ▼
Step 3: Click the "📥 Download as CSV" button
        The button is right at the top next to the stock name (and also above the data table).
        Your browser instantly downloads the file to your computer.
```

---

## 3. How to Run the App on Your Computer

1. Open your terminal or PowerShell.
2. Go to your folder:
   ```powershell
   cd d:\sanjeevan\JoshiQuants\Code
   ```
3. Start the app:
   ```powershell
   python -m streamlit run yfin.py
   ```
4. Your browser will automatically open to `http://localhost:8501`.

---

## 4. Why We Added the "Execute" and "Download" Buttons

In the initial draft, there was no separate execute button (it ran automatically on every keystroke), and the download button was way down below the charts, making it easy to miss.

### What is improved:
1. **Clear "Execute" Button**:
   - There is a bright primary button called **"▶️ Execute & Fetch Data"** in the sidebar.
   - There is also a welcome button called **"🚀 Execute & Fetch Data Now"** in the center of the screen when you first open the app.
   - You are now in full control of when data is fetched.
2. **Prominent "Download CSV" Buttons**:
   - **Top Button**: Sits right at the very top next to the stock name and current price. You can download immediately without scrolling.
   - **Bottom Button**: Sits directly above the data table so you can inspect the numbers and download right there.

---

## 5. Technical Plan of Action: What Happens Behind the Scenes

Here is what the code in `yfin.py` does step-by-step:

### Phase 1: Reading Your Choices
- The app reads what ticker you entered.
- It makes sure letters are capitalized (for example, converting `aapl` to `AAPL`).
- It checks if you chose a preset time (like `1y`) or a custom start and end date.

### Phase 2: Connecting to Yahoo Finance Safely
- The app contacts Yahoo Finance using the `yfinance` library.
- **Smart Caching**: It remembers the data for 5 minutes (`@st.cache_data`). If you click around or change display settings, it doesn't waste time re-downloading the same data from the internet.

### Phase 3: Cleaning the Data for Excel
- Real stock data from Yahoo often includes confusing timezone text (like `-05:00`). When opened in Excel, this often breaks date formatting.
- The app automatically strips away timezone tags so Excel recognizes every date normally.
- If you don't need dividend and stock split numbers, the app can hide them so your CSV file stays clean.

### Phase 4: Showing Key Numbers and Interactive Dynamic Charts
- The app calculates:
  - **Latest Close Price** and how much it went up or down compared to yesterday.
  - **Highest Price** and **Lowest Price** over your chosen period.
  - **Total Volume** (how many shares were traded).
- **Dynamic Chart Scaling (`zero=False`)**:
  - The chart automatically zooms right into the stock's actual low and high price range (`[Min Price - 5%, Max Price + 5%]`), ensuring price curves are never flat.
  - You have three interactive tabs:
    1. **📉 Price Trend (Line)**: Blue price line with interactive zoom, pan, and hover tooltips.
    2. **🕯️ Candlestick Chart**: Professional green and red trading candlesticks with high/low wicks.
    3. **📊 Trading Volume**: Volume bars colored green for up-days and red for down-days.

### Phase 5: Generating and Delivering the CSV
- When you click **"📥 Download as CSV"**, the app turns the table into CSV text directly in memory.
- It gives the file a descriptive name like `AAPL_1d_1y.csv`.
- Your browser saves it straight to your **Downloads** folder. No temporary junk files are left on your hard drive.

---

## 6. Helpful Tips & Simple Troubleshooting

| What you want to do | How to do it |
| :--- | :--- |
| **Download Indian Stocks (NSE/BSE)** | Add `.NS` for National Stock Exchange or `.BO` for Bombay Stock Exchange. Example: `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`. |
| **Download Market Indices** | Put a `^` symbol in front. Example: `^NSEI` (Nifty 50), `^BSESN` (Sensex), `^GSPC` (S&P 500). |
| **Download Crypto** | Add `-USD`. Example: `BTC-USD`, `ETH-USD`. |
| **Intraday Data (1-minute or 5-minute bars)** | Yahoo Finance only keeps 1-minute data for the last **7 days**, and other intraday data for **60 days**. If you select `1m`, make sure your period is `5d` or less. |
| **"No data returned" Warning** | Check if the ticker is spelled correctly, or if the market was closed on the dates selected. |

---

## 7. Future Plan of Action (Course Roadmap)

As you progress through your **JoshiQuants** coursework, here is the plan of action for expanding this tool:
1. **Technical Indicators**:
   - Moving Averages (20-day, 50-day, 200-day SMA/EMA).
   - Relative Strength Index (RSI).
2. **Multi-Stock Downloader**:
   - Download multiple stocks at once in a single CSV or ZIP file.
3. **Broker API Integration**:
   - Connect to Indian broker APIs (Kotak Neo, Breeze) for live tick feeds and order execution.

---

## 8. Change Log & Implemented Proposals

### Proposal 8.1: Round All Price Values to 2 Decimal Places & Clean Dates

- **Date**: 2026-11-15
- **Status**: ✅ Approved & Implemented
- **Summary of Changes**:
  1. **Prices Rounded to 2 Decimals**: `Open`, `High`, `Low`, `Close`, and `Adj Close` are explicitly rounded to 2 decimal places (`.round(2)`), fixing values like `348.2454` to `348.25`.
  2. **Column Display Formatting**: Configured `st.column_config.NumberColumn(format="%.2f")` so that every price column displays strictly with 2 decimal places (e.g. `345` displays as `345.00`).
  3. **Clean Date Formatting**: Removed `00:00:00` from daily/weekly/monthly dates so dates display cleanly as `YYYY-MM-DD` (e.g., `2026-11-11` instead of `2026-11-11 00:00:00`).
  4. **Summary Statistics**: The `.describe()` table is rounded to 2 decimal places.
  5. **Clean CSV Export**: The downloaded CSV automatically inherits both the 2-decimal numbers and the clean dates.

---

### Proposal 9.1: Add a 0 to 100 Progress Bar During Data Fetching

- **Date**: 2026-11-15
- **Status**: ✅ Approved & Implemented
- **Summary of Changes**:
  1. Integrated an animated `st.progress` bar directly into `run_fetch()` in `yfin.py`.
  2. The bar steps from 0% -> 15% (connecting) -> 35% (downloading candles) -> 60% (date sanitization & 2-decimal rounding) -> 85% (building analytics) -> 100% (ready).
  3. Once finished, the bar smoothly clears itself and reveals the charts and CSV download buttons.

---

### Proposal 9.2: Create `requirements.txt` for the Application

- **Date**: 2026-11-15
- **Status**: ✅ Approved & Implemented
- **Summary of Changes**:
  1. Created `requirements.txt` in the root workspace directory with the required application packages:
     - `streamlit>=1.35.0`
     - `yfinance>=0.2.38`
     - `pandas>=2.0.0`
     - `altair>=5.0.0`
  2. Documented the role of each library for seamless installation and deployment.

---

## 9. Proposed Changes (Pending Review)

*No pending changes at this moment. All requested features are implemented and active.*
