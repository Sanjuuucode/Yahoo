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

### Proposal 10.1: Bulk Ticker Upload & Multi-Stock Data Downloader

- **Date**: 2026-11-15
- **Status**: ✅ Approved & Implemented
- **Summary of Changes**:
  1. Added **Workflow Mode** selector in sidebar: toggle seamlessly between **"Single Ticker"** and **"Bulk Ticker Upload"**.
  2. Supported dual bulk input methods:
     - **File Uploader**: Reads `.csv` files (detecting `Ticker`, `Symbol`, or first column) and `.txt` files.
     - **Paste Tickers Directly**: Accepts comma, whitespace, semicolon, or newline-separated tickers with automatic deduplication.
  3. Integrated **Animated Batch Progress Bar** displaying `[X/Total] Fetching market data for SYMBOL...`.
  4. Implemented in-memory ZIP streaming (`zipfile` & `io.BytesIO`) delivering a clean `.zip` archive containing individual formatted CSVs for every stock without disk clutter.
  5. Implemented merged **Master Combined CSV** with an added `Ticker` column for multi-asset quantitative modeling and backtesting.
  6. Provided a 3-tab inspection suite for bulk runs:
     - **Batch Status Summary**: Real-time status, row counts, date bounds, latest close, and error reasons.
     - **Master Combined Preview**: Preview first 200 rows of merged master dataset.
     - **Individual Stock Inspector**: Interactive zoomable Altair price chart and data grid for any stock in the batch.

---

### Proposal 11.1: Server-Side Basket Data Storage & Input-Based Moving Average Stock Screener

- **Date**: 2026-11-15
- **Status**: ✅ Approved & Implemented
- **Summary of Changes**:
  1. Implemented **Server-Side Data Storage** repository at `./data/server_baskets/` storing master CSVs and metadata JSON files directly on the server filesystem.
  2. Built **Server Basket Ingestion & Management Engine**:
     - Pull and persist custom baskets with customizable names (e.g., `US_Tech_Leaders`, `Nifty_Leaders`).
     - Built-in templates for instant start (US Mega-Cap Tech, Nifty 50 Leaders) alongside custom paste and file upload.
     - Live server status badges displaying file path, ticker count, row count, and last sync timestamp.
     - One-click **🔄 Re-sync Server Data** to update server datasets with fresh Yahoo Finance prices.
     - One-click **🗑️ Delete Basket** to clean up server files.
  3. Integrated **Customizable Moving Average Screener (Input-Based)**:
     - MA Types: `SMA (Simple)` and `EMA (Exponential)`.
     - User inputs for **Short MA (Period 1)** and **Long MA (Period 2)** with real-time dynamic parameter recalculation.
     - 9 Screening strategies: Price > MA1, Price > MA2, Price < MA1, Price < MA2, Golden Cross, Death Cross, Strong Uptrend (Price > MA1 > MA2), and Near Support with user-defined percentage tolerance.
  4. Delivered **Screened Analytics & Verification Suite**:
     - Screener summary metrics (Total in Basket, Passed Filter, Pass Rate %, Applied Filter, Strategy).
     - Screened results table with a toggle to view only matching stocks or the complete basket.
     - **📥 Download Screener Results (CSV)** with full MA indicators and distance percentages.
     - **📈 Interactive Chart & MA Overlays**: Dual-line Altair overlay showing Price (blue), Short MA (amber dashed), and Long MA (purple solid) with hover tooltips.

---

### Proposal 12.1: Intelligent Yahoo Finance Ticker Formatter & Indian Exchange (.NS / .BO) Auto-Resolver

- **Date**: 2026-11-15
- **Status**: ✅ Approved & Implemented
- **Summary of Changes**:
  1. Built `format_ticker_yfin()` to format input stocks into valid Yahoo Finance ticker syntax:
     - Automatically appends `.NS` for NSE India (or `.BO` for BSE) to bare symbols like `HDFCBANK`, `RELIANCE`, `M&M`, `BAJAJ-AUTO`.
     - Intelligently skips double-suffixing on existing symbols (e.g. `TCS.NS` remains `TCS.NS`).
     - Normalizes benchmark index names (`NIFTY 50` / `NIFTY` -> `^NSEI`, `BANKNIFTY` -> `^NSEBANK`, `SENSEX` -> `^BSESN`).
  2. Enhanced `parse_tickers()`:
     - Handles CSV files where column header is `NIFTY 50` or other index names without breaking.
     - Supports `include_index` toggle to optionally pull the benchmark index alongside constituents.
  3. Integrated **Exchange Suffix** dropdown (`NSE India (.NS)`, `BSE India (.BO)`, `US / Direct`) across Bulk Ticker Upload and Screener modes.
  4. Added **Live Formatted Tickers Preview** displaying ticker badges formatted for Yahoo Finance before data fetching starts.

---

### Proposal 13.1: Visual Signal Markers & Condition Trigger Points on Screener Charts

- **Date**: 2026-11-15
- **Status**: ✅ Approved & Implemented
- **Summary of Changes**:
  1. Implemented historical condition evaluation engine across time series in the screener inspector, computing both event transitions (`trigger_series`) and state masks (`cond_series`).
  2. Layered color-coded, shaped Altair signal markers directly on top of the Price and MA trendlines:
     - 🟢 **Green Upward Triangles (`▲`)**: Bullish signals (Price > MA, Golden Cross, Strong Uptrend).
     - 🔴 **Red Downward Triangles (`▼`)**: Bearish signals (Price < MA, Death Cross).
     - 🟠 **Amber Target Dots (`●`)**: Support and pullback signals.
  3. Integrated **Interactive Hover Tooltips** displaying Trigger Date, Condition Met, Stock Price, Short MA, Long MA, and % Distance from both MAs.
  4. Added a real-time **Signal Summary Card** above the chart reporting total triggers in the period, total active days, and today's status (`✅ Condition Met Today` vs `❌ Condition Not Met Today`).
  5. Added **Display Controls**: Toggle to show/hide markers and radio to switch between `Trigger Dates Only (Breakouts / Crosses)` and `All Active Matching Days`.

---

### Proposal 14.1: Dynamic Dark and Light Theme Switcher

- **Date**: 2026-11-15
- **Status**: ✅ Approved & Implemented
- **Summary of Changes**:
  1. Added a **Theme Switcher** toggle (`🌙 Dark Mode` / `☀️ Light Mode`) at the top of the sidebar with session state persistence.
  2. Implemented dynamic CSS theming:
     - **Dark Mode**: TradingView-inspired `#0E1117` app canvas, `#161B22` sidebar, `#1E222D` cards with slate borders, and glowing accents.
     - **Light Mode**: Crisp `#FFFFFF` canvas, soft `#F8F9FA` sidebar, and slate `#1E293B` headings.
  3. Integrated `apply_chart_theme()` across all Altair charts (Line, Candlestick, Volume, and Screener MA Signal Overlays), automatically styling gridlines, axis typography, and canvas backgrounds to match the selected theme.

---

## 9. Proposed Changes (Pending Review)

*No pending changes at this moment. All requested features are implemented and active.*
