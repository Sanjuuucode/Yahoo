import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import time
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Yahoo Finance Data Downloader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling for a modern look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #6c757d;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .step-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #e9ecef;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# App Title
st.markdown('<div class="main-header">📈 Yahoo Finance Data Downloader</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Fetch market data from Yahoo Finance, visualize trends, and download clean CSV files.</div>', unsafe_allow_html=True)

# Initialize Session State
if "data_loaded" not in st.session_state:
    st.session_state["data_loaded"] = False
if "df" not in st.session_state:
    st.session_state["df"] = None
if "ticker_info" not in st.session_state:
    st.session_state["ticker_info"] = None
if "ticker_name" not in st.session_state:
    st.session_state["ticker_name"] = "AAPL"
if "csv_filename" not in st.session_state:
    st.session_state["csv_filename"] = "market_data.csv"

# Sidebar - Settings & Inputs
st.sidebar.header("⚙️ Step 1: Configure Settings")

# Ticker input
default_ticker = "AAPL"
ticker_input = st.sidebar.text_input(
    "Ticker Symbol",
    value=st.session_state["ticker_name"] if st.session_state["ticker_name"] else default_ticker,
    help="Enter any Yahoo Finance ticker (e.g., AAPL, MSFT, TSLA, RELIANCE.NS, ^NSEI, BTC-USD)"
).strip().upper()

# Quick market suggestions
with st.sidebar.expander("💡 Common Ticker Examples"):
    st.markdown("""
    - **US Stocks**: `AAPL`, `MSFT`, `GOOGL`, `AMZN`, `NVDA`, `TSLA`
    - **Indian Stocks (NSE/BSE)**: `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`, `INFY.BO`
    - **Indices**: `^GSPC` (S&P 500), `^NSEI` (Nifty 50), `^BSESN` (Sensex)
    - **Crypto / FX**: `BTC-USD`, `ETH-USD`, `EURUSD=X`, `INR=X`
    """)

# Date range selection mode
date_mode = st.sidebar.radio(
    "Date Selection Method",
    options=["Preset Period", "Custom Date Range"],
    index=0
)

preset_period = None
start_date = None
end_date = None

if date_mode == "Preset Period":
    preset_period = st.sidebar.selectbox(
        "Period",
        options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
        index=5  # Default to 1y
    )
else:
    col_d1, col_d2 = st.sidebar.columns(2)
    with col_d1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=365))
    with col_d2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    if start_date > end_date:
        st.sidebar.error("Start date must be before end date!")

# Interval selection
interval_options = ["1d", "1wk", "1mo", "1h", "30m", "15m", "5m", "1m"]
interval = st.sidebar.selectbox(
    "Data Interval",
    options=interval_options,
    index=0,
    help="Note: Intraday intervals (1m to 1h) have limited historical range on Yahoo Finance (e.g. 1m max ~7 days, 5m/15m/1h max ~60 days)."
)

# Additional options
st.sidebar.subheader("Additional Options")
remove_tz = st.sidebar.checkbox("Strip Timezone from Dates", value=True, help="Removes timezone offset so Excel opens timestamps cleanly.")
keep_actions = st.sidebar.checkbox("Include Dividends & Stock Splits", value=True)

# Fetch data function with caching
@st.cache_data(ttl=300, show_spinner=False)
def load_stock_data(symbol: str, mode: str, period: str, start, end, interval_val: str):
    ticker_obj = yf.Ticker(symbol)
    if mode == "Preset Period":
        data = ticker_obj.history(period=period, interval=interval_val, auto_adjust=False)
    else:
        s_str = start.strftime("%Y-%m-%d") if isinstance(start, (datetime, pd.Timestamp)) else str(start)
        # Yahoo Finance end date is exclusive; add 1 day so end date is included
        e_adj = end + timedelta(days=1)
        e_str = e_adj.strftime("%Y-%m-%d") if isinstance(e_adj, (datetime, pd.Timestamp)) else str(e_adj)
        data = ticker_obj.history(start=s_str, end=e_str, interval=interval_val, auto_adjust=False)
    
    info = {}
    try:
        info = ticker_obj.info or {}
    except Exception:
        info = {}
        
    return data, info

# Step 2: Execute Button in Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🚀 Step 2: Run & Fetch")
execute_sidebar = st.sidebar.button("▶️ Execute & Fetch Data", type="primary", width="stretch")

# Function to run the fetch action with an animated 0 to 100 progress bar
def run_fetch():
    if not ticker_input:
        st.error("Please enter a valid ticker symbol first.")
        return

    progress_bar = st.progress(0, text="Initiating connection...")
    try:
        progress_bar.progress(15, text=f"Connecting to Yahoo Finance for {ticker_input}...")
        time.sleep(0.1)

        progress_bar.progress(35, text="Fetching historical price records...")
        raw_df, raw_info = load_stock_data(ticker_input, date_mode, preset_period, start_date, end_date, interval)

        progress_bar.progress(60, text="Sanitizing dates & rounding prices to 2 decimals...")
        if raw_df is not None and not raw_df.empty:
            # Strip timezone if requested
            if remove_tz and hasattr(raw_df.index, 'tz') and raw_df.index.tz is not None:
                raw_df.index = raw_df.index.tz_localize(None)

            # Filter actions if requested
            if not keep_actions:
                cols_to_drop = [c for c in ["Dividends", "Stock Splits", "Capital Gains"] if c in raw_df.columns]
                if cols_to_drop:
                    raw_df = raw_df.drop(columns=cols_to_drop)

            # Round all price columns to 2 decimal places
            price_cols = [c for c in ["Open", "High", "Low", "Close", "Adj Close", "Dividends"] if c in raw_df.columns]
            raw_df[price_cols] = raw_df[price_cols].round(2)

            # Format index dates cleanly (remove 00:00:00 on daily/weekly/monthly data)
            if isinstance(raw_df.index, pd.DatetimeIndex):
                if interval in ["1d", "5d", "1wk", "1mo", "3mo"]:
                    raw_df.index = raw_df.index.strftime("%Y-%m-%d")
                else:
                    raw_df.index = raw_df.index.strftime("%Y-%m-%d %H:%M:%S")
            raw_df.index.name = "Date"

            date_tag = preset_period if date_mode == "Preset Period" else f"{start_date}_to_{end_date}"

            progress_bar.progress(85, text="Building charts & analytics...")
            time.sleep(0.1)

            st.session_state["df"] = raw_df
            st.session_state["ticker_info"] = raw_info
            st.session_state["ticker_name"] = ticker_input
            st.session_state["csv_filename"] = f"{ticker_input}_{interval}_{date_tag}.csv"
            st.session_state["data_loaded"] = True

            progress_bar.progress(100, text="Data successfully loaded!")
            time.sleep(0.25)
            progress_bar.empty()
        else:
            progress_bar.empty()
            st.session_state["df"] = None
            st.session_state["data_loaded"] = False
            st.warning(f"⚠️ No data returned for ticker '{ticker_input}'. Please check the symbol and date interval.")
    except Exception as e:
        progress_bar.empty()
        st.session_state["df"] = None
        st.session_state["data_loaded"] = False
        st.error(f"Error fetching data: {e}")

# Trigger fetch if sidebar button clicked
if execute_sidebar:
    run_fetch()

# Main Display Area
df = st.session_state.get("df")
ticker_info = st.session_state.get("ticker_info") or {}
active_ticker = st.session_state.get("ticker_name", "AAPL")
csv_filename = st.session_state.get("csv_filename", f"{active_ticker}_data.csv")

# If no data has been loaded yet, show welcome card with Execute button
if not st.session_state.get("data_loaded") or df is None:
    st.info("👋 **Welcome to the Yahoo Finance Data Downloader!**")
    
    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
        st.markdown("""
        ### How to use this app:
        1. **Select Ticker & Dates**: Check the configuration options on the left sidebar (default: `AAPL`).
        2. **Execute**: Click the **Execute & Fetch Data** button below (or in the sidebar).
        3. **Download CSV**: Click the **Download as CSV** button to save the file to your computer.
        """)
    with col_w2:
        st.markdown("<br>", unsafe_allow_html=True)
        main_execute_btn = st.button("🚀 Execute & Fetch Data Now", type="primary", width="stretch")
        if main_execute_btn:
            run_fetch()
            st.rerun()

# If data is loaded, render results and prominent download buttons
if st.session_state.get("data_loaded") and df is not None and not df.empty:
    company_name = ticker_info.get("shortName") or ticker_info.get("longName") or active_ticker
    currency = ticker_info.get("currency", "")
    sector = ticker_info.get("sector", "")
    summary = f"{currency} • {sector}" if sector else currency

    # TOP ACTION BAR: Company Name on Left + Big Download Button on Right
    top_col_info, top_col_btn = st.columns([3, 1])
    with top_col_info:
        st.subheader(f"{company_name} ({active_ticker})")
        if summary:
            st.caption(summary)
    with top_col_btn:
        csv_buffer = df.to_csv(index=True)
        st.download_button(
            label="📥 Download as CSV",
            data=csv_buffer,
            file_name=csv_filename,
            mime="text/csv",
            type="primary",
            width="stretch",
            key="download_csv_top",
            help="Click here to download this data as a CSV file to your computer"
        )
        st.caption(f"Ready: **{csv_filename}** ({len(df)} rows)")

    st.markdown("---")

    # Metrics row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    latest_close = df["Close"].iloc[-1]
    prev_close = df["Close"].iloc[-2] if len(df) > 1 else latest_close
    diff = latest_close - prev_close
    pct_diff = (diff / prev_close) * 100 if prev_close != 0 else 0

    with m_col1:
        st.metric("Latest Close", f"{latest_close:,.2f} {currency}", f"{diff:+,.2f} ({pct_diff:+.2f}%)")
    with m_col2:
        st.metric("Period High", f"{df['High'].max():,.2f} {currency}")
    with m_col3:
        st.metric("Period Low", f"{df['Low'].min():,.2f} {currency}")
    with m_col4:
        st.metric("Total Volume", f"{df['Volume'].sum():,.0f}")

    st.markdown("---")

    # Visualizations
    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📉 Price Trend (Line)", "🕯️ Candlestick Chart", "📊 Trading Volume"])
    
    # Prepare data for Altair
    chart_df = df.reset_index()
    date_col = chart_df.columns[0]
    
    # Dynamic price bounds: y-axis zooms into the actual price range so the chart is NEVER flat
    p_min = float(df["Low"].min() if "Low" in df.columns else df["Close"].min())
    p_max = float(df["High"].max() if "High" in df.columns else df["Close"].max())
    p_range = p_max - p_min
    padding = p_range * 0.05 if p_range > 0 else max(1.0, p_min * 0.02)
    y_domain = [max(0.0, p_min - padding), p_max + padding]

    with chart_tab1:
        if len(df) <= 1:
            st.info("ℹ️ Only 1 data point returned for this period. Showing table view below.")
        else:
            line_chart = (
                alt.Chart(chart_df)
                .mark_line(color="#2962FF", strokeWidth=2)
                .encode(
                    x=alt.X(f"{date_col}:T", title="Date"),
                    y=alt.Y("Close:Q", title=f"Price ({currency})", scale=alt.Scale(domain=y_domain, zero=False)),
                    tooltip=[
                        alt.Tooltip(f"{date_col}:T", title="Date", format="%Y-%m-%d %H:%M" if ("h" in interval or "m" in interval) else "%Y-%m-%d"),
                        alt.Tooltip("Open:Q", title="Open", format=",.2f"),
                        alt.Tooltip("High:Q", title="High", format=",.2f"),
                        alt.Tooltip("Low:Q", title="Low", format=",.2f"),
                        alt.Tooltip("Close:Q", title="Close", format=",.2f"),
                        alt.Tooltip("Volume:Q", title="Volume", format=",.0f"),
                    ]
                )
                .properties(height=420)
                .interactive()
            )
            st.altair_chart(line_chart, width="stretch")

    with chart_tab2:
        if len(df) <= 1:
            st.info("ℹ️ Candlestick chart requires at least 2 data points.")
        else:
            open_close_color = alt.condition(
                "datum.Open <= datum.Close",
                alt.value("#089981"),  # TradingView green
                alt.value("#f23645")   # TradingView red
            )
            
            rule = (
                alt.Chart(chart_df)
                .mark_rule()
                .encode(
                    x=alt.X(f"{date_col}:T", title="Date"),
                    y=alt.Y("Low:Q", title=f"Price ({currency})", scale=alt.Scale(domain=y_domain, zero=False)),
                    y2=alt.Y2("High:Q"),
                    color=open_close_color
                )
            )
            
            bar = (
                alt.Chart(chart_df)
                .mark_bar()
                .encode(
                    x=alt.X(f"{date_col}:T"),
                    y=alt.Y("Open:Q"),
                    y2=alt.Y2("Close:Q"),
                    color=open_close_color,
                    tooltip=[
                        alt.Tooltip(f"{date_col}:T", title="Date", format="%Y-%m-%d %H:%M" if ("h" in interval or "m" in interval) else "%Y-%m-%d"),
                        alt.Tooltip("Open:Q", title="Open", format=",.2f"),
                        alt.Tooltip("High:Q", title="High", format=",.2f"),
                        alt.Tooltip("Low:Q", title="Low", format=",.2f"),
                        alt.Tooltip("Close:Q", title="Close", format=",.2f"),
                        alt.Tooltip("Volume:Q", title="Volume", format=",.0f"),
                    ]
                )
            )
            candlestick = (rule + bar).properties(height=420).interactive()
            st.altair_chart(candlestick, width="stretch")

    with chart_tab3:
        vol_chart = (
            alt.Chart(chart_df)
            .mark_bar()
            .encode(
                x=alt.X(f"{date_col}:T", title="Date"),
                y=alt.Y("Volume:Q", title="Volume"),
                color=alt.condition(
                    "datum.Open <= datum.Close",
                    alt.value("#089981"),
                    alt.value("#f23645")
                ),
                tooltip=[
                    alt.Tooltip(f"{date_col}:T", title="Date", format="%Y-%m-%d %H:%M" if ("h" in interval or "m" in interval) else "%Y-%m-%d"),
                    alt.Tooltip("Volume:Q", title="Volume", format=",.0f"),
                ]
            )
            .properties(height=320)
            .interactive()
        )
        st.altair_chart(vol_chart, width="stretch")

    # Historical Data Table & Secondary Download Button
    st.subheader("📋 Historical Data Preview")
    
    table_col1, table_col2 = st.columns([1, 3])
    with table_col1:
        st.download_button(
            label="📥 Download as CSV",
            data=csv_buffer,
            file_name=csv_filename,
            mime="text/csv",
            type="primary",
            width="stretch",
            key="download_csv_bottom"
        )
    with table_col2:
        st.caption(f"Click the button to download the entire table as **{csv_filename}**")

    # Configure columns so every price column displays strictly with 2 decimals
    col_configs = {
        col: st.column_config.NumberColumn(format="%.2f")
        for col in ["Open", "High", "Low", "Close", "Adj Close", "Dividends"]
        if col in df.columns
    }
    if "Volume" in df.columns:
        col_configs["Volume"] = st.column_config.NumberColumn(format="%d")

    # Display Dataframe with latest first
    st.dataframe(
        df.sort_index(ascending=False),
        column_config=col_configs,
        width="stretch"
    )

    # Summary statistics expander
    with st.expander("📊 View Summary Statistics"):
        st.dataframe(df.describe().round(2).T, width="stretch")

st.markdown("---")
st.caption("Built with Streamlit & yfinance | JoshiQuants")
