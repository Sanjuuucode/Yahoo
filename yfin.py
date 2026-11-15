import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import time
import re
import os
import io
import json
import zipfile
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Yahoo Finance Data Downloader & Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Base Server Storage Directory
SERVER_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "server_baskets")

def ensure_server_storage():
    os.makedirs(SERVER_STORAGE_DIR, exist_ok=True)

# ==============================================================================
# THEME CONFIGURATION & DYNAMIC CSS
# ==============================================================================
THEME_DARK = "🌙 Dark Mode"
THEME_LIGHT = "☀️ Light Mode"

# Native Streamlit theme palettes. CSS alone cannot restyle Streamlit's built-in
# widgets (inputs, radios, alerts, header), so we switch the real theme instead.
NATIVE_THEMES = {
    True: {
        "theme.base": "dark",
        "theme.primaryColor": "#2962FF",
        "theme.backgroundColor": "#0E1117",
        "theme.secondaryBackgroundColor": "#161B22",
        "theme.textColor": "#E0E3EB",
    },
    False: {
        "theme.base": "light",
        "theme.primaryColor": "#2962FF",
        "theme.backgroundColor": "#FFFFFF",
        "theme.secondaryBackgroundColor": "#F8F9FA",
        "theme.textColor": "#1E293B",
    },
}

def apply_native_theme(dark: bool) -> bool:
    """Set Streamlit's theme options; return True if anything changed."""
    changed = False
    for option, value in NATIVE_THEMES[dark].items():
        if st.get_option(option) != value:
            st._config.set_option(option, value)
            changed = True
    return changed

if "app_theme" not in st.session_state:
    st.session_state["app_theme"] = THEME_DARK

# Sidebar Theme Switcher at the very top (keyed so its state survives reruns)
theme_choice = st.sidebar.radio(
    "🎨 Theme Mode",
    options=[THEME_DARK, THEME_LIGHT],
    key="app_theme",
    horizontal=True,
    help="Toggle between TradingView dark terminal mode and crisp light mode."
)
is_dark = (theme_choice == THEME_DARK)
# The theme is sent to the browser at the start of each run, so after a change
# rerun once immediately for the new palette to take effect.
if apply_native_theme(is_dark):
    st.rerun()

# Dynamic Theme-Based CSS
if is_dark:
    st.markdown("""
    <style>
        .stApp {
            background-color: #0E1117;
            color: #E0E3EB;
        }
        [data-testid="stSidebar"] {
            background-color: #161B22;
            border-right: 1px solid #30363D;
        }
        [data-testid="stSidebar"] * {
            color: #E0E3EB;
        }
        .main-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            color: #8B949E;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }
        .step-card {
            background-color: #1E222D;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid #2A2E39;
            margin-bottom: 15px;
            color: #F0F6FC;
        }
        .server-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            background-color: rgba(46, 125, 50, 0.25);
            color: #81C784;
            border: 1px solid #2E7D32;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .ticker-pill {
            display: inline-block;
            background-color: #1E293B;
            color: #60A5FA;
            border: 1px solid #3B82F6;
            padding: 2px 8px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.85rem;
            margin: 2px;
        }
        [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
        }
        [data-testid="stMetricLabel"] {
            color: #9CA3AF !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            border-bottom-color: #30363D;
        }
        .stDataFrame {
            border-radius: 6px;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp {
            background-color: #FFFFFF;
            color: #1E293B;
        }
        [data-testid="stSidebar"] {
            background-color: #F8F9FA;
            border-right: 1px solid #E9ECEF;
        }
        .main-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            color: #64748B;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }
        .step-card {
            background-color: #F8F9FA;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid #E9ECEF;
            margin-bottom: 15px;
            color: #1E293B;
        }
        .server-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            background-color: #E8F5E9;
            color: #2E7D32;
            border: 1px solid #A5D6A7;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .ticker-pill {
            display: inline-block;
            background-color: #E3F2FD;
            color: #0D47A1;
            border: 1px solid #90CAF9;
            padding: 2px 8px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.85rem;
            margin: 2px;
        }
    </style>
    """, unsafe_allow_html=True)

# Helper function to apply theme styling to Altair charts
def apply_chart_theme(chart, is_dark_mode: bool):
    grid_c = "#2A2E39" if is_dark_mode else "#E2E8F0"
    label_c = "#9CA3AF" if is_dark_mode else "#475569"
    title_c = "#F3F4F6" if is_dark_mode else "#1E293B"
    return chart.configure_axis(
        gridColor=grid_c,
        labelColor=label_c,
        titleColor=title_c
    ).configure_view(strokeWidth=0)

# App Title
st.markdown('<div class="main-header">📈 Yahoo Finance Data Downloader & Screener</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Download historical market data, persist stock baskets on server, and screen stocks with custom Moving Averages.</div>', unsafe_allow_html=True)

# ==============================================================================
# YAHOO FINANCE TICKER FORMATTER & INDEX MAPPINGS
# ==============================================================================
INDEX_MAPPINGS = {
    "NIFTY 50": "^NSEI",
    "NIFTY50": "^NSEI",
    "NIFTY": "^NSEI",
    "NIFTY 500": "^CRSLDX",
    "NIFTY500": "^CRSLDX",
    "NIFTY BANK": "^NSEBANK",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
    "BSE SENSEX": "^BSESN",
    "NIFTY IT": "^CNXIT",
    "S&P 500": "^GSPC",
    "SP500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW": "^DJI"
}

def format_ticker_yfin(symbol: str, default_suffix: str = ".NS", include_index_benchmarks: bool = True) -> str:
    sym = symbol.strip().upper()
    if not sym:
        return ""
    
    if sym in INDEX_MAPPINGS:
        return INDEX_MAPPINGS[sym] if include_index_benchmarks else ""

    if sym.startswith("^"):
        return sym

    if any(sym.endswith(sfx) for sfx in [".NS", ".BO", "=X", ".L", ".AX", ".TO", ".HK"]):
        return sym

    if "-" in sym and any(c in sym for c in ["USD", "USDT", "INR", "EUR", "BTC", "ETH"]):
        return sym

    if default_suffix and default_suffix != "None / Direct":
        clean_sfx = default_suffix if default_suffix.startswith(".") else f".{default_suffix}"
        return f"{sym}{clean_sfx}"

    return sym

def parse_tickers(pasted_text: str = "", file_obj = None, default_suffix: str = ".NS", include_index: bool = False):
    raw_tokens = []
    if file_obj is not None:
        try:
            fname = file_obj.name.lower()
            if fname.endswith(".csv"):
                file_df = pd.read_csv(file_obj)
                matched_col = None
                
                for col in file_df.columns:
                    col_clean = str(col).strip().lower()
                    if col_clean in ["ticker", "symbol", "symbols", "tickers", "stock", "stocks", "equity", "company", "constituent"]:
                        matched_col = col
                        break
                
                if matched_col is None:
                    first_header = str(file_df.columns[0]).strip().upper()
                    if first_header in INDEX_MAPPINGS and include_index:
                        raw_tokens.append(INDEX_MAPPINGS[first_header])
                    matched_col = file_df.columns[0]
                
                raw_tokens.extend(file_df[matched_col].dropna().astype(str).tolist())
            else:
                content = file_obj.read().decode("utf-8", errors="ignore")
                raw_tokens = re.split(r"[,\s;\n\r]+", content)
        except Exception as e:
            st.sidebar.error(f"Error reading file: {e}")
    elif pasted_text:
        raw_tokens = re.split(r"[,\s;\n\r]+", pasted_text)

    cleaned = []
    seen = set()
    for token in raw_tokens:
        clean_raw = token.strip().upper().strip("\"'[]")
        if not clean_raw:
            continue
        
        formatted_sym = format_ticker_yfin(clean_raw, default_suffix=default_suffix, include_index_benchmarks=include_index)
        if formatted_sym and formatted_sym not in seen:
            cleaned.append(formatted_sym)
            seen.add(formatted_sym)
            
    return cleaned

# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
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

if "bulk_data_loaded" not in st.session_state:
    st.session_state["bulk_data_loaded"] = False
if "bulk_results" not in st.session_state:
    st.session_state["bulk_results"] = {}
if "bulk_errors" not in st.session_state:
    st.session_state["bulk_errors"] = {}
if "bulk_zip_bytes" not in st.session_state:
    st.session_state["bulk_zip_bytes"] = None
if "bulk_combined_csv" not in st.session_state:
    st.session_state["bulk_combined_csv"] = None
if "bulk_total_count" not in st.session_state:
    st.session_state["bulk_total_count"] = 0
if "bulk_date_tag" not in st.session_state:
    st.session_state["bulk_date_tag"] = "1y"

if "active_basket_name" not in st.session_state:
    st.session_state["active_basket_name"] = None
if "screener_basket_dfs" not in st.session_state:
    st.session_state["screener_basket_dfs"] = {}
if "screener_meta" not in st.session_state:
    st.session_state["screener_meta"] = {}
if "screener_ran" not in st.session_state:
    st.session_state["screener_ran"] = False

# ==============================================================================
# HELPER FUNCTIONS: SERVER-SIDE BASKET STORAGE
# ==============================================================================
def list_server_baskets():
    ensure_server_storage()
    baskets = []
    for fname in os.listdir(SERVER_STORAGE_DIR):
        if fname.endswith(".csv"):
            bname = fname[:-4]
            csv_path = os.path.join(SERVER_STORAGE_DIR, fname)
            meta_path = os.path.join(SERVER_STORAGE_DIR, f"{bname}_meta.json")
            meta = {}
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass
            mtime = os.path.getmtime(csv_path)
            dt_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            baskets.append({
                "name": bname,
                "csv_path": csv_path,
                "meta_path": meta_path,
                "last_modified": dt_str,
                "tickers": meta.get("tickers", []),
                "ticker_count": meta.get("ticker_count", 0),
                "interval": meta.get("interval", "1d"),
                "date_tag": meta.get("date_tag", "1y"),
                "total_rows": meta.get("total_rows", 0)
            })
    return sorted(baskets, key=lambda x: x["name"])

def save_basket_to_server(basket_name: str, dfs_dict: dict, interval_val: str, date_tag: str):
    ensure_server_storage()
    safe_name = re.sub(r"[^\w\-]", "_", basket_name.strip())
    if not safe_name:
        safe_name = "default_basket"
    
    combined_list = []
    for sym, df_item in dfs_dict.items():
        if df_item is not None and not df_item.empty:
            m_df = df_item.reset_index()
            if "Ticker" not in m_df.columns:
                m_df.insert(0, "Ticker", sym)
            combined_list.append(m_df)
            
    if not combined_list:
        return False, "No valid data to store on server."
        
    master_df = pd.concat(combined_list, ignore_index=True)
    csv_path = os.path.join(SERVER_STORAGE_DIR, f"{safe_name}.csv")
    master_df.to_csv(csv_path, index=False)
    
    meta_path = os.path.join(SERVER_STORAGE_DIR, f"{safe_name}_meta.json")
    meta = {
        "name": safe_name,
        "ticker_count": len(dfs_dict),
        "tickers": list(dfs_dict.keys()),
        "interval": interval_val,
        "date_tag": date_tag,
        "total_rows": len(master_df),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    return True, safe_name

def load_basket_from_server(basket_name: str):
    ensure_server_storage()
    safe_name = re.sub(r"[^\w\-]", "_", basket_name.strip())
    csv_path = os.path.join(SERVER_STORAGE_DIR, f"{safe_name}.csv")
    meta_path = os.path.join(SERVER_STORAGE_DIR, f"{safe_name}_meta.json")
    if not os.path.exists(csv_path):
        return None, {}, "Basket file not found on server."
    try:
        master_df = pd.read_csv(csv_path)
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        
        dfs_dict = {}
        if "Ticker" in master_df.columns:
            for sym, group in master_df.groupby("Ticker"):
                g_df = group.drop(columns=["Ticker"]).copy()
                if "Date" in g_df.columns:
                    g_df["Date"] = g_df["Date"].astype(str)
                    g_df.set_index("Date", inplace=True)
                dfs_dict[sym] = g_df
        return dfs_dict, meta, None
    except Exception as e:
        return None, {}, f"Error loading server basket: {e}"

def delete_basket_from_server(basket_name: str):
    ensure_server_storage()
    safe_name = re.sub(r"[^\w\-]", "_", basket_name.strip())
    csv_path = os.path.join(SERVER_STORAGE_DIR, f"{safe_name}.csv")
    meta_path = os.path.join(SERVER_STORAGE_DIR, f"{safe_name}_meta.json")
    deleted = False
    if os.path.exists(csv_path):
        os.remove(csv_path)
        deleted = True
    if os.path.exists(meta_path):
        os.remove(meta_path)
    return deleted

# Core Fetch data function with caching
@st.cache_data(ttl=300, show_spinner=False)
def load_stock_data(symbol: str, mode: str, period: str, start, end, interval_val: str):
    ticker_obj = yf.Ticker(symbol)
    if mode == "Preset Period":
        data = ticker_obj.history(period=period, interval=interval_val, auto_adjust=False)
    else:
        s_str = start.strftime("%Y-%m-%d") if isinstance(start, (datetime, pd.Timestamp)) else str(start)
        e_adj = end + timedelta(days=1)
        e_str = e_adj.strftime("%Y-%m-%d") if isinstance(e_adj, (datetime, pd.Timestamp)) else str(e_adj)
        data = ticker_obj.history(start=s_str, end=e_str, interval=interval_val, auto_adjust=False)
    
    info = {}
    try:
        info = ticker_obj.info or {}
    except Exception:
        info = {}
        
    return data, info

# Shared Data Sanitization & Formatting Function
def clean_stock_df(raw_df: pd.DataFrame, interval_val: str, remove_tz_flag: bool = True, keep_actions_flag: bool = True):
    if raw_df is None or raw_df.empty:
        return None
    cleaned_df = raw_df.copy()
    
    if remove_tz_flag and hasattr(cleaned_df.index, 'tz') and cleaned_df.index.tz is not None:
        cleaned_df.index = cleaned_df.index.tz_localize(None)

    if not keep_actions_flag:
        cols_to_drop = [c for c in ["Dividends", "Stock Splits", "Capital Gains"] if c in cleaned_df.columns]
        if cols_to_drop:
            cleaned_df = cleaned_df.drop(columns=cols_to_drop)

    price_cols = [c for c in ["Open", "High", "Low", "Close", "Adj Close", "Dividends"] if c in cleaned_df.columns]
    cleaned_df[price_cols] = cleaned_df[price_cols].round(2)

    if isinstance(cleaned_df.index, pd.DatetimeIndex):
        if interval_val in ["1d", "5d", "1wk", "1mo", "3mo"]:
            cleaned_df.index = cleaned_df.index.strftime("%Y-%m-%d")
        else:
            cleaned_df.index = cleaned_df.index.strftime("%Y-%m-%d %H:%M:%S")
    cleaned_df.index.name = "Date"
    return cleaned_df

# ==============================================================================
# SIDEBAR NAVIGATION & SETTINGS
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Step 1: Mode Selection")
app_mode = st.sidebar.radio(
    "Workflow Mode",
    options=["Single Ticker", "Bulk Ticker Upload", "📈 Moving Average Screener"],
    index=0,
    help="Single Ticker: detailed analysis for one stock.\nBulk Ticker Upload: batch download clean datasets.\nMoving Average Screener: store baskets on server and screen with customizable MAs."
)

date_mode = "Preset Period"
preset_period = "1y"
start_date = None
end_date = None
interval = "1d"
remove_tz = True
keep_actions = True

ticker_input = "AAPL"
detected_tickers = []

if app_mode == "Single Ticker":
    raw_single_input = st.sidebar.text_input(
        "Ticker Symbol",
        value=st.session_state["ticker_name"] if st.session_state["ticker_name"] else "AAPL",
        help="Enter any Yahoo Finance ticker (e.g., AAPL, RELIANCE.NS, NIFTY 50, BTC-USD)"
    ).strip().upper()

    ticker_input = format_ticker_yfin(raw_single_input, default_suffix="", include_index_benchmarks=True)
    if ticker_input != raw_single_input:
        st.sidebar.caption(f"Resolved to Yahoo Finance symbol: **`{ticker_input}`**")

    with st.sidebar.expander("💡 Common Ticker Examples"):
        st.markdown("""
        - **US Stocks**: `AAPL`, `MSFT`, `GOOGL`, `AMZN`, `NVDA`, `TSLA`
        - **Indian Stocks (NSE/BSE)**: `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`, `INFY.BO`
        - **Indices**: `^GSPC` (S&P 500), `^NSEI` (Nifty 50), `^BSESN` (Sensex)
        - **Crypto / FX**: `BTC-USD`, `ETH-USD`, `EURUSD=X`, `INR=X`
        """)

    st.sidebar.subheader("📅 Date & Interval")
    date_mode = st.sidebar.radio("Date Selection Method", options=["Preset Period", "Custom Date Range"], index=0, key="single_date_mode")
    if date_mode == "Preset Period":
        preset_period = st.sidebar.selectbox("Period", options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], index=5, key="single_preset")
    else:
        col_d1, col_d2 = st.sidebar.columns(2)
        with col_d1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=365), key="single_start")
        with col_d2:
            end_date = st.date_input("End Date", value=datetime.now(), key="single_end")

    interval = st.sidebar.selectbox("Data Interval", options=["1d", "1wk", "1mo", "1h", "30m", "15m", "5m", "1m"], index=0, key="single_interval")
    st.sidebar.subheader("🛠️ Additional Options")
    remove_tz = st.sidebar.checkbox("Strip Timezone from Dates", value=True, key="single_tz")
    keep_actions = st.sidebar.checkbox("Include Dividends & Stock Splits", value=True, key="single_act")

    st.sidebar.markdown("---")
    execute_sidebar = st.sidebar.button("▶️ Execute & Fetch Data", type="primary", width="stretch")

elif app_mode == "Bulk Ticker Upload":
    bulk_input_source = st.sidebar.radio("Input Source", options=["Upload File (.csv / .txt)", "Paste Tickers Directly"], index=0)
    
    exchange_suffix_opt = st.sidebar.selectbox(
        "Exchange Suffix (for bare symbols)",
        options=["NSE India (.NS)", "BSE India (.BO)", "US / Direct (No suffix)"],
        index=0,
        help="Automatically appends .NS for Indian NSE stocks (e.g. HDFCBANK -> HDFCBANK.NS)."
    )
    selected_sfx = ".NS" if "NSE" in exchange_suffix_opt else (".BO" if "BSE" in exchange_suffix_opt else "")
    include_idx = st.sidebar.checkbox("Include Index Benchmark (^NSEI) if detected", value=False)

    if bulk_input_source == "Upload File (.csv / .txt)":
        uploaded_file = st.sidebar.file_uploader("Upload Ticker File", type=["csv", "txt"], help="Upload CSV or TXT file.")
        if uploaded_file is not None:
            detected_tickers = parse_tickers(file_obj=uploaded_file, default_suffix=selected_sfx, include_index=include_idx)
            st.sidebar.success(f"Loaded **{len(detected_tickers)}** ticker(s) in Yahoo Finance style.")
    else:
        sample_default = "HDFCBANK, RELIANCE, ICICIBANK, SBIN, TCS, INFY, M&M, BAJAJ-AUTO"
        pasted_text = st.sidebar.text_area("Paste Tickers", value=sample_default, help="Separate symbols with commas, spaces, or lines.")
        detected_tickers = parse_tickers(pasted_text=pasted_text, default_suffix=selected_sfx, include_index=include_idx)
        st.sidebar.info(f"Detected **{len(detected_tickers)}** ticker(s).")

    st.sidebar.subheader("📅 Date & Interval")
    date_mode = st.sidebar.radio("Date Selection Method", options=["Preset Period", "Custom Date Range"], index=0, key="bulk_date_mode")
    if date_mode == "Preset Period":
        preset_period = st.sidebar.selectbox("Period", options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], index=5, key="bulk_preset")
    else:
        col_d1, col_d2 = st.sidebar.columns(2)
        with col_d1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=365), key="bulk_start")
        with col_d2:
            end_date = st.date_input("End Date", value=datetime.now(), key="bulk_end")

    interval = st.sidebar.selectbox("Data Interval", options=["1d", "1wk", "1mo", "1h", "30m", "15m", "5m", "1m"], index=0, key="bulk_interval")
    st.sidebar.subheader("🛠️ Additional Options")
    remove_tz = st.sidebar.checkbox("Strip Timezone from Dates", value=True, key="bulk_tz")
    keep_actions = st.sidebar.checkbox("Include Dividends & Stock Splits", value=True, key="bulk_act")

    st.sidebar.markdown("---")
    execute_sidebar = st.sidebar.button("▶️ Execute Bulk Fetch", type="primary", width="stretch")

else:
    st.sidebar.subheader("🗄️ Step 2: Server Basket Source")
    existing_baskets = list_server_baskets()
    basket_options = [b["name"] for b in existing_baskets]

    screener_source = st.sidebar.radio(
        "Basket Action",
        options=["Select Stored Server Basket", "Pull New Basket to Server"],
        index=0 if basket_options else 1
    )

    selected_basket_name = None
    new_basket_name = "Nifty_Leaders"
    screener_tickers = []

    if screener_source == "Select Stored Server Basket":
        if basket_options:
            selected_basket_name = st.sidebar.selectbox("Choose Stored Basket", options=basket_options, index=0)
            curr_b = next((b for b in existing_baskets if b["name"] == selected_basket_name), None)
            if curr_b:
                st.sidebar.caption(f"📁 **{curr_b['ticker_count']}** stocks • Updated: {curr_b['last_modified']}")
        else:
            st.sidebar.warning("No baskets stored on server yet. Please switch to 'Pull New Basket to Server'.")
    else:
        new_basket_name = st.sidebar.text_input("New Basket Name", value="Nifty_50").strip()
        
        scr_exchange_sfx = st.sidebar.selectbox(
            "Exchange Suffix (for bare symbols)",
            options=["NSE India (.NS)", "BSE India (.BO)", "US / Direct (No suffix)"],
            index=0,
            key="scr_sfx"
        )
        scr_sfx_val = ".NS" if "NSE" in scr_exchange_sfx else (".BO" if "BSE" in scr_exchange_sfx else "")
        scr_include_idx = st.sidebar.checkbox("Include Index Benchmark (^NSEI) if detected", value=False, key="scr_inc_idx")

        template_choice = st.sidebar.selectbox(
            "Select Basket Source",
            options=["Nifty 50 Full Basket", "US Mega-Cap Tech", "Upload CSV / TXT File", "Paste Custom Tickers"]
        )

        if template_choice == "Nifty 50 Full Basket":
            raw_nifty50 = [
                "HDFCBANK", "RELIANCE", "ICICIBANK", "SBIN", "BAJFINANCE", "BHARTIARTL", "BSE", "HINDALCO", 
                "TCS", "INFY", "M&M", "LT", "MARUTI", "SHRIRAMFIN", "AXISBANK", "KOTAKBANK", "INDIGO", 
                "APOLLOHOSP", "GRASIM", "EICHERMOT", "SUNPHARMA", "ADANIPORTS", "TITAN", "BEL", "HCLTECH", 
                "BAJAJ-AUTO", "TMPV", "ADANIENT", "HINDUNILVR", "TATASTEEL", "ITC", "TECHM", "JSWSTEEL", 
                "ULTRACEMCO", "ONGC", "COALINDIA", "TRENT", "DRREDDY", "JIOFIN", "HDFCLIFE", "NTPC", 
                "ASIANPAINT", "CIPLA", "MAXHEALTH", "POWERGRID", "NESTLEIND", "SBILIFE", "BAJAJFINSV", "TATACONSUM"
            ]
            screener_tickers = [format_ticker_yfin(s, scr_sfx_val, scr_include_idx) for s in raw_nifty50]
            st.sidebar.caption(f"Ready: **{len(screener_tickers)}** Nifty 50 stocks in Yahoo Finance style.")

        elif template_choice == "US Mega-Cap Tech":
            raw_tech = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "AMD", "INTC"]
            screener_tickers = [format_ticker_yfin(s, "", False) for s in raw_tech]
            st.sidebar.caption(f"Ready: **{len(screener_tickers)}** US tech stocks.")

        elif template_choice == "Upload CSV / TXT File":
            up_f = st.sidebar.file_uploader("Upload File (.csv / .txt)", type=["csv", "txt"], key="scr_file")
            if up_f is not None:
                screener_tickers = parse_tickers(file_obj=up_f, default_suffix=scr_sfx_val, include_index=scr_include_idx)
                st.sidebar.success(f"Parsed **{len(screener_tickers)}** tickers in Yahoo Finance style.")
        else:
            s_paste = st.sidebar.text_area("Paste Tickers", value="HDFCBANK, RELIANCE, TCS, INFY, SBIN, M&M, BAJAJ-AUTO", key="scr_paste")
            screener_tickers = parse_tickers(pasted_text=s_paste, default_suffix=scr_sfx_val, include_index=scr_include_idx)

        st.sidebar.markdown("**Timeframe for Server Storage:**")
        preset_period = st.sidebar.selectbox("Period", options=["6mo", "1y", "2y", "5y"], index=1, key="scr_preset")
        interval = st.sidebar.selectbox("Interval", options=["1d", "1wk"], index=0, key="scr_interval")

    st.sidebar.markdown("---")
    st.sidebar.subheader("📐 Step 3: Moving Average Inputs")
    ma_type = st.sidebar.selectbox("MA Calculation Type", options=["SMA (Simple)", "EMA (Exponential)"], index=0)
    col_ma1, col_ma2 = st.sidebar.columns(2)
    with col_ma1:
        ma1_period = st.sidebar.number_input("Short MA (Period 1)", min_value=2, max_value=500, value=20, step=1)
    with col_ma2:
        ma2_period = st.sidebar.number_input("Long MA (Period 2)", min_value=2, max_value=500, value=50, step=1)

    screening_condition = st.sidebar.selectbox(
        "Screening Condition",
        options=[
            f"Price > Short MA ({ma1_period})",
            f"Price > Long MA ({ma2_period})",
            f"Price < Short MA ({ma1_period})",
            f"Price < Long MA ({ma2_period})",
            f"Golden Cross: Short MA ({ma1_period}) > Long MA ({ma2_period})",
            f"Death Cross: Short MA ({ma1_period}) < Long MA ({ma2_period})",
            f"Strong Uptrend: Price > MA1 > MA2",
            f"Near Support: Price within ±X% of Long MA ({ma2_period})",
            f"Near Support: Price within ±X% of Short MA ({ma1_period})"
        ],
        index=0
    )

    tolerance_pct = 2.0
    if "Near Support" in screening_condition:
        tolerance_pct = st.sidebar.slider("Tolerance (±%)", min_value=0.5, max_value=10.0, value=2.0, step=0.5)

    execute_sidebar = False

# ==============================================================================
# SINGLE TICKER FETCH LOGIC
# ==============================================================================
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
            clean_df = clean_stock_df(raw_df, interval, remove_tz, keep_actions)
            date_tag = preset_period if date_mode == "Preset Period" else f"{start_date}_to_{end_date}"

            progress_bar.progress(85, text="Building charts & analytics...")
            time.sleep(0.1)

            st.session_state["df"] = clean_df
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

# ==============================================================================
# BULK TICKER FETCH LOGIC
# ==============================================================================
def run_bulk_fetch(ticker_list: list):
    if not ticker_list:
        st.error("No valid ticker symbols found. Please upload a file or paste tickers.")
        return

    total = len(ticker_list)
    progress_bar = st.progress(0, text=f"Initiating bulk fetch for {total} stocks...")
    date_tag = preset_period if date_mode == "Preset Period" else f"{start_date}_to_{end_date}"

    successful_dfs = {}
    errors = {}
    combined_rows = []

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, sym in enumerate(ticker_list):
            pct = int(((idx) / total) * 100)
            progress_bar.progress(pct, text=f"[{idx+1}/{total}] Fetching market data for {sym}...")

            try:
                raw_df, _ = load_stock_data(sym, date_mode, preset_period, start_date, end_date, interval)
                if raw_df is not None and not raw_df.empty:
                    c_df = clean_stock_df(raw_df, interval, remove_tz, keep_actions)
                    successful_dfs[sym] = c_df

                    csv_bytes = c_df.to_csv(index=True)
                    safe_sym_file = sym.replace("^", "").replace(":", "_")
                    zip_file.writestr(f"{safe_sym_file}_{interval}_{date_tag}.csv", csv_bytes)

                    m_df = c_df.reset_index()
                    m_df.insert(0, "Ticker", sym)
                    combined_rows.append(m_df)
                else:
                    errors[sym] = "No data returned (invalid ticker or closed market range)"
            except Exception as e:
                errors[sym] = str(e)

            time.sleep(0.04)

    progress_bar.progress(100, text=f"Batch complete! Processed {total} stocks.")
    time.sleep(0.2)
    progress_bar.empty()

    combined_csv_str = ""
    if combined_rows:
        master_df = pd.concat(combined_rows, ignore_index=True)
        combined_csv_str = master_df.to_csv(index=False)

    zip_buffer.seek(0)

    st.session_state["bulk_results"] = successful_dfs
    st.session_state["bulk_errors"] = errors
    st.session_state["bulk_zip_bytes"] = zip_buffer.getvalue()
    st.session_state["bulk_combined_csv"] = combined_csv_str
    st.session_state["bulk_data_loaded"] = True
    st.session_state["bulk_total_count"] = total
    st.session_state["bulk_date_tag"] = date_tag

if app_mode in ["Single Ticker", "Bulk Ticker Upload"] and execute_sidebar:
    if app_mode == "Single Ticker":
        run_fetch()
    else:
        run_bulk_fetch(detected_tickers)

# ==============================================================================
# MAIN DISPLAY AREA: SINGLE TICKER MODE
# ==============================================================================
if app_mode == "Single Ticker":
    df = st.session_state.get("df")
    ticker_info = st.session_state.get("ticker_info") or {}
    active_ticker = st.session_state.get("ticker_name", "AAPL")
    csv_filename = st.session_state.get("csv_filename", f"{active_ticker}_data.csv")

    if not st.session_state.get("data_loaded") or df is None:
        st.info("👋 **Welcome to the Yahoo Finance Data Downloader!**")
        col_w1, col_w2 = st.columns([2, 1])
        with col_w1:
            st.markdown("""
            ### How to use Single Mode:
            1. **Select Ticker & Dates**: Check configuration options in the left sidebar (default: `AAPL`).
            2. **Execute**: Click the **Execute & Fetch Data** button below (or in the sidebar).
            3. **Download CSV**: Click **Download as CSV** to save the clean dataset directly to your computer.
            """)
        with col_w2:
            st.markdown("<br>", unsafe_allow_html=True)
            main_execute_btn = st.button("🚀 Execute & Fetch Data Now", type="primary", width="stretch")
            if main_execute_btn:
                run_fetch()
                st.rerun()

    if st.session_state.get("data_loaded") and df is not None and not df.empty:
        company_name = ticker_info.get("shortName") or ticker_info.get("longName") or active_ticker
        currency = ticker_info.get("currency", "")
        sector = ticker_info.get("sector", "")
        summary = f"{currency} • {sector}" if sector else currency

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

        chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📉 Price Trend (Line)", "🕯️ Candlestick Chart", "📊 Trading Volume"])
        chart_df = df.reset_index()
        date_col = chart_df.columns[0]
        
        p_min = float(df["Low"].min() if "Low" in df.columns else df["Close"].min())
        p_max = float(df["High"].max() if "High" in df.columns else df["Close"].max())
        p_range = p_max - p_min
        padding = p_range * 0.05 if p_range > 0 else max(1.0, p_min * 0.02)
        y_domain = [max(0.0, p_min - padding), p_max + padding]

        line_color_single = "#38BDF8" if is_dark else "#2962FF"

        with chart_tab1:
            if len(df) <= 1:
                st.info("ℹ️ Only 1 data point returned for this period.")
            else:
                line_chart = (
                    alt.Chart(chart_df)
                    .mark_line(color=line_color_single, strokeWidth=2)
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
                st.altair_chart(apply_chart_theme(line_chart, is_dark), width="stretch")

        with chart_tab2:
            if len(df) <= 1:
                st.info("ℹ️ Candlestick chart requires at least 2 data points.")
            else:
                open_close_color = alt.condition("datum.Open <= datum.Close", alt.value("#089981"), alt.value("#F23645"))
                rule = alt.Chart(chart_df).mark_rule().encode(
                    x=alt.X(f"{date_col}:T", title="Date"),
                    y=alt.Y("Low:Q", title=f"Price ({currency})", scale=alt.Scale(domain=y_domain, zero=False)),
                    y2=alt.Y2("High:Q"),
                    color=open_close_color
                )
                bar = alt.Chart(chart_df).mark_bar().encode(
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
                candlestick_chart = (rule + bar).properties(height=420).interactive()
                st.altair_chart(apply_chart_theme(candlestick_chart, is_dark), width="stretch")

        with chart_tab3:
            vol_chart = alt.Chart(chart_df).mark_bar().encode(
                x=alt.X(f"{date_col}:T", title="Date"),
                y=alt.Y("Volume:Q", title="Volume"),
                color=alt.condition("datum.Open <= datum.Close", alt.value("#089981"), alt.value("#F23645")),
                tooltip=[
                    alt.Tooltip(f"{date_col}:T", title="Date", format="%Y-%m-%d %H:%M" if ("h" in interval or "m" in interval) else "%Y-%m-%d"),
                    alt.Tooltip("Volume:Q", title="Volume", format=",.0f"),
                ]
            ).properties(height=320).interactive()
            st.altair_chart(apply_chart_theme(vol_chart, is_dark), width="stretch")

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

        col_configs = {
            col: st.column_config.NumberColumn(format="%.2f")
            for col in ["Open", "High", "Low", "Close", "Adj Close", "Dividends"]
            if col in df.columns
        }
        if "Volume" in df.columns:
            col_configs["Volume"] = st.column_config.NumberColumn(format="%d")

        st.dataframe(df.sort_index(ascending=False), column_config=col_configs, width="stretch")

        with st.expander("📊 View Summary Statistics"):
            st.dataframe(df.describe().round(2).T, width="stretch")

# ==============================================================================
# MAIN DISPLAY AREA: BULK TICKER UPLOAD MODE
# ==============================================================================
elif app_mode == "Bulk Ticker Upload":
    bulk_results = st.session_state.get("bulk_results", {})
    bulk_errors = st.session_state.get("bulk_errors", {})
    bulk_zip_bytes = st.session_state.get("bulk_zip_bytes")
    bulk_combined_csv = st.session_state.get("bulk_combined_csv")
    bulk_date_tag = st.session_state.get("bulk_date_tag", "1y")
    is_bulk_loaded = st.session_state.get("bulk_data_loaded", False)

    if not is_bulk_loaded:
        st.info("📦 **Bulk Ticker Downloader: Fast Multi-Stock Market Data Extraction**")
        b_col1, b_col2 = st.columns([2, 1])
        with b_col1:
            st.markdown("""
            ### How to use Bulk Mode:
            1. **Choose Tickers**: Upload a `.csv` / `.txt` file or paste a list of tickers in the sidebar.
            2. **Yahoo Finance Auto-Style**: Bare symbols (e.g. `HDFCBANK`, `RELIANCE`) are automatically resolved with `.NS` suffix.
            3. **Execute**: Click **Execute Bulk Fetch** to pull data for all stocks in one run.
            4. **Download**: Get an organized **ZIP archive** with individual CSVs, or a single **Combined Master CSV**.
            """)
        with b_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if detected_tickers:
                st.success(f"✅ Ready to fetch **{len(detected_tickers)}** ticker(s) in Yahoo Finance style")
                bulk_main_btn = st.button("🚀 Execute Bulk Fetch Now", type="primary", width="stretch")
                if bulk_main_btn:
                    run_bulk_fetch(detected_tickers)
                    st.rerun()
            else:
                st.warning("👈 Please enter or upload tickers in the sidebar first.")

        if detected_tickers:
            st.markdown("---")
            st.subheader(f"📋 Formatted Yahoo Finance Tickers ({len(detected_tickers)} symbols)")
            st.markdown("All bare symbols are formatted with proper exchange suffixes:")
            p_html = "".join([f'<span class="ticker-pill">{t}</span>' for t in detected_tickers[:50]])
            if len(detected_tickers) > 50:
                p_html += f" ... <em>(and {len(detected_tickers) - 50} more)</em>"
            st.markdown(p_html, unsafe_allow_html=True)

    if is_bulk_loaded:
        success_count = len(bulk_results)
        error_count = len(bulk_errors)
        total_count = success_count + error_count
        total_rows = sum(len(df) for df in bulk_results.values())

        top_bulk_info, top_bulk_btn1, top_bulk_btn2 = st.columns([2, 1, 1])
        with top_bulk_info:
            st.subheader(f"📦 Bulk Extraction Complete")
            st.caption(f"Successfully processed **{success_count} of {total_count}** stocks • Total **{total_rows:,}** rows")

        with top_bulk_btn1:
            if bulk_zip_bytes:
                zip_filename = f"bulk_market_data_{interval}_{bulk_date_tag}.zip"
                st.download_button(
                    label="📦 Download All (ZIP)",
                    data=bulk_zip_bytes,
                    file_name=zip_filename,
                    mime="application/zip",
                    type="primary",
                    width="stretch",
                    key="download_bulk_zip",
                    help="Download a single ZIP containing clean CSVs for every stock"
                )
                st.caption(f"Ready: **{zip_filename}**")

        with top_bulk_btn2:
            if bulk_combined_csv:
                master_filename = f"master_combined_{interval}_{bulk_date_tag}.csv"
                st.download_button(
                    label="📄 Combined Master CSV",
                    data=bulk_combined_csv,
                    file_name=master_filename,
                    mime="text/csv",
                    width="stretch",
                    key="download_bulk_combined",
                    help="Download one single merged CSV file with all stocks and a 'Ticker' column"
                )
                st.caption(f"Ready: **{master_filename}**")

        st.markdown("---")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Requested", f"{total_count}")
        with m2:
            st.metric("Successful", f"{success_count}")
        with m3:
            st.metric("Failed / Empty", f"{error_count}")
        with m4:
            st.metric("Combined Rows", f"{total_rows:,}")

        st.markdown("---")

        b_tab1, b_tab2, b_tab3 = st.tabs(["📋 Batch Status Summary", "📊 Master Combined Preview", "🔍 Individual Stock Inspector"])

        with b_tab1:
            summary_records = []
            for sym, df_item in bulk_results.items():
                first_date = df_item.index[0] if len(df_item) > 0 else "-"
                last_date = df_item.index[-1] if len(df_item) > 0 else "-"
                latest_p = float(df_item["Close"].iloc[-1]) if len(df_item) > 0 else 0.0
                summary_records.append({
                    "Ticker": sym,
                    "Status": "✅ Success",
                    "Rows": len(df_item),
                    "Start Date": str(first_date),
                    "End Date": str(last_date),
                    "Latest Close": latest_p,
                    "Remarks": "Downloaded cleanly"
                })
            for sym, err in bulk_errors.items():
                summary_records.append({
                    "Ticker": sym,
                    "Status": "❌ Failed",
                    "Rows": 0,
                    "Start Date": "-",
                    "End Date": "-",
                    "Latest Close": 0.0,
                    "Remarks": err
                })

            summary_df = pd.DataFrame(summary_records)
            st.dataframe(
                summary_df,
                column_config={
                    "Latest Close": st.column_config.NumberColumn(format="%.2f"),
                    "Rows": st.column_config.NumberColumn(format="%d")
                },
                width="stretch"
            )

        with b_tab2:
            if bulk_combined_csv:
                st.caption("Showing the first 200 rows of the combined master dataset:")
                preview_master = pd.read_csv(io.StringIO(bulk_combined_csv), nrows=200)
                col_configs_master = {
                    col: st.column_config.NumberColumn(format="%.2f")
                    for col in ["Open", "High", "Low", "Close", "Adj Close", "Dividends"]
                    if col in preview_master.columns
                }
                if "Volume" in preview_master.columns:
                    col_configs_master["Volume"] = st.column_config.NumberColumn(format="%d")
                st.dataframe(preview_master, column_config=col_configs_master, width="stretch")

        with b_tab3:
            if bulk_results:
                selected_sym = st.selectbox("Select a stock to inspect:", options=list(bulk_results.keys()), index=0)
                inspected_df = bulk_results[selected_sym]
                st.write(f"### {selected_sym} Overview ({len(inspected_df)} rows)")
                
                chart_inspected = inspected_df.reset_index()
                d_col = chart_inspected.columns[0]
                p_min = float(inspected_df["Low"].min() if "Low" in inspected_df.columns else inspected_df["Close"].min())
                p_max = float(inspected_df["High"].max() if "High" in inspected_df.columns else inspected_df["Close"].max())
                p_pad = (p_max - p_min) * 0.05 if (p_max - p_min) > 0 else max(1.0, p_min * 0.02)

                insp_line_color = "#38BDF8" if is_dark else "#2962FF"
                insp_chart = (
                    alt.Chart(chart_inspected)
                    .mark_line(color=insp_line_color, strokeWidth=2)
                    .encode(
                        x=alt.X(f"{d_col}:T", title="Date"),
                        y=alt.Y("Close:Q", title="Price", scale=alt.Scale(domain=[max(0.0, p_min - p_pad), p_max + p_pad], zero=False)),
                        tooltip=[alt.Tooltip(f"{d_col}:T", title="Date"), alt.Tooltip("Close:Q", title="Close", format=",.2f"), alt.Tooltip("Volume:Q", title="Volume", format=",.0f")]
                    )
                    .properties(height=350)
                    .interactive()
                )
                st.altair_chart(apply_chart_theme(insp_chart, is_dark), width="stretch")
                st.dataframe(inspected_df.sort_index(ascending=False), width="stretch")

# ==============================================================================
# MAIN DISPLAY AREA: MOVING AVERAGE SCREENER (SERVER-STORED BASKETS)
# ==============================================================================
else:
    st.markdown('<div class="server-badge">🟢 Server-Side Storage Enabled: <code>./data/server_baskets/</code></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if screener_source == "Pull New Basket to Server":
        st.subheader("📥 Pull Market Data & Store Basket on Server")
        st.markdown("""
        Upload or paste stocks with bare names (e.g. `HDFCBANK`, `RELIANCE`, `TCS`). The system automatically transforms them into Yahoo Finance style (`HDFCBANK.NS`, `RELIANCE.NS`) and permanently persists the dataset on the server filesystem.
        """)

        col_pull1, col_pull2 = st.columns([2, 1])
        with col_pull1:
            st.info(f"Basket Name: **`{new_basket_name}`** • Tickers to Pull: **{len(screener_tickers)}** symbols")
        with col_pull2:
            pull_save_btn = st.button("💾 Pull & Store on Server Now", type="primary", width="stretch")

        if screener_tickers:
            st.markdown(f"**Yahoo Finance Resolved Tickers ({len(screener_tickers)} symbols):**")
            p_html = "".join([f'<span class="ticker-pill">{t}</span>' for t in screener_tickers[:50]])
            if len(screener_tickers) > 50:
                p_html += f" ... <em>(and {len(screener_tickers) - 50} more)</em>"
            st.markdown(p_html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        if pull_save_btn:
            if not screener_tickers:
                st.error("Please provide at least one valid ticker symbol.")
            else:
                progress_bar = st.progress(0, text=f"Pulling data for {len(screener_tickers)} stocks...")
                temp_dfs = {}
                date_tag = preset_period
                
                for idx, sym in enumerate(screener_tickers):
                    pct = int(((idx) / len(screener_tickers)) * 100)
                    progress_bar.progress(pct, text=f"[{idx+1}/{len(screener_tickers)}] Fetching {sym} from Yahoo Finance...")
                    try:
                        r_df, _ = load_stock_data(sym, "Preset Period", preset_period, None, None, interval)
                        if r_df is not None and not r_df.empty:
                            clean_d = clean_stock_df(r_df, interval, True, True)
                            temp_dfs[sym] = clean_d
                    except Exception as e:
                        pass
                    time.sleep(0.04)

                progress_bar.progress(90, text="Saving master dataset to server filesystem...")
                ok, saved_name = save_basket_to_server(new_basket_name, temp_dfs, interval, date_tag)
                progress_bar.progress(100, text="Done!")
                time.sleep(0.2)
                progress_bar.empty()

                if ok:
                    st.success(f"🎉 Successfully stored basket **`{saved_name}`** with **{len(temp_dfs)}** stocks on server!")
                    st.session_state["active_basket_name"] = saved_name
                    st.session_state["screener_basket_dfs"] = temp_dfs
                    st.session_state["screener_meta"] = {"name": saved_name, "ticker_count": len(temp_dfs), "interval": interval}
                    st.rerun()
                else:
                    st.error(f"Failed to save basket to server: {saved_name}")

    active_bname = selected_basket_name if screener_source == "Select Stored Server Basket" else st.session_state.get("active_basket_name")
    
    if active_bname and (st.session_state.get("active_basket_name") != active_bname or not st.session_state.get("screener_basket_dfs")):
        with st.spinner(f"Loading '{active_bname}' from server storage..."):
            loaded_dfs, loaded_meta, err_msg = load_basket_from_server(active_bname)
            if loaded_dfs:
                st.session_state["active_basket_name"] = active_bname
                st.session_state["screener_basket_dfs"] = loaded_dfs
                st.session_state["screener_meta"] = loaded_meta
            elif err_msg:
                st.error(err_msg)

    loaded_basket_dfs = st.session_state.get("screener_basket_dfs", {})
    loaded_meta = st.session_state.get("screener_meta", {})
    curr_active_name = st.session_state.get("active_basket_name")

    if curr_active_name and loaded_basket_dfs:
        srv_col1, srv_col2, srv_col3 = st.columns([3, 1, 1])
        with srv_col1:
            st.subheader(f"📊 Active Server Basket: `{curr_active_name}`")
            updated_time = loaded_meta.get("updated_at", "Stored")
            st.caption(f"💾 File: `data/server_baskets/{curr_active_name}.csv` • **{len(loaded_basket_dfs)}** stocks • Updated: {updated_time}")

        with srv_col2:
            resync_btn = st.button("🔄 Re-sync Server Data", help="Fetch the latest Yahoo Finance closing prices and update server storage.")
            if resync_btn:
                with st.spinner("Re-syncing latest data from Yahoo Finance..."):
                    updated_dfs = {}
                    scr_tickers = list(loaded_basket_dfs.keys())
                    p_bar = st.progress(0)
                    for i, s in enumerate(scr_tickers):
                        p_bar.progress(int((i / len(scr_tickers)) * 100), text=f"Syncing {s}...")
                        try:
                            r_df, _ = load_stock_data(s, "Preset Period", loaded_meta.get("date_tag", "1y"), None, None, loaded_meta.get("interval", "1d"))
                            if r_df is not None and not r_df.empty:
                                updated_dfs[s] = clean_stock_df(r_df, loaded_meta.get("interval", "1d"), True, True)
                        except Exception:
                            pass
                    save_basket_to_server(curr_active_name, updated_dfs, loaded_meta.get("interval", "1d"), loaded_meta.get("date_tag", "1y"))
                    st.session_state["screener_basket_dfs"] = updated_dfs
                    p_bar.empty()
                    st.success("Server data refreshed!")
                    st.rerun()

        with srv_col3:
            del_btn = st.button("🗑️ Delete Basket", help="Remove this basket file from server storage.")
            if del_btn:
                delete_basket_from_server(curr_active_name)
                st.session_state["active_basket_name"] = None
                st.session_state["screener_basket_dfs"] = {}
                st.session_state["screener_meta"] = {}
                st.success(f"Basket '{curr_active_name}' deleted from server.")
                st.rerun()

        st.markdown("---")

        calc_type_name = "SMA" if "SMA" in ma_type else "EMA"
        screener_rows = []
        enriched_stock_dfs = {}

        for sym, stock_df in loaded_basket_dfs.items():
            if stock_df is None or len(stock_df) < 5:
                continue

            calc_df = stock_df.copy()
            close_s = calc_df["Close"]

            if calc_type_name == "SMA":
                calc_df["MA1"] = close_s.rolling(window=int(ma1_period), min_periods=1).mean().round(2)
                calc_df["MA2"] = close_s.rolling(window=int(ma2_period), min_periods=1).mean().round(2)
            else:
                calc_df["MA1"] = close_s.ewm(span=int(ma1_period), adjust=False).mean().round(2)
                calc_df["MA2"] = close_s.ewm(span=int(ma2_period), adjust=False).mean().round(2)

            enriched_stock_dfs[sym] = calc_df

            latest_close = float(close_s.iloc[-1])
            ma1_latest = float(calc_df["MA1"].iloc[-1])
            ma2_latest = float(calc_df["MA2"].iloc[-1])

            dist_ma1 = round(((latest_close - ma1_latest) / ma1_latest) * 100, 2) if ma1_latest > 0 else 0.0
            dist_ma2 = round(((latest_close - ma2_latest) / ma2_latest) * 100, 2) if ma2_latest > 0 else 0.0

            matched = False
            if "Price > Short MA" in screening_condition:
                matched = (latest_close > ma1_latest)
            elif "Price > Long MA" in screening_condition:
                matched = (latest_close > ma2_latest)
            elif "Price < Short MA" in screening_condition:
                matched = (latest_close < ma1_latest)
            elif "Price < Long MA" in screening_condition:
                matched = (latest_close < ma2_latest)
            elif "Golden Cross" in screening_condition:
                matched = (ma1_latest > ma2_latest)
            elif "Death Cross" in screening_condition:
                matched = (ma1_latest < ma2_latest)
            elif "Strong Uptrend" in screening_condition:
                matched = (latest_close > ma1_latest and ma1_latest > ma2_latest)
            elif f"Price within ±X% of Long MA ({ma2_period})" in screening_condition:
                matched = (abs(dist_ma2) <= tolerance_pct)
            elif f"Price within ±X% of Short MA ({ma1_period})" in screening_condition:
                matched = (abs(dist_ma1) <= tolerance_pct)

            screener_rows.append({
                "Ticker": sym,
                "Status": "✅ Match" if matched else "❌ No Match",
                "Close": latest_close,
                f"MA1 ({ma1_period})": ma1_latest,
                f"MA2 ({ma2_period})": ma2_latest,
                "% Dist MA1": dist_ma1,
                "% Dist MA2": dist_ma2,
                "Volume": int(stock_df["Volume"].iloc[-1]) if "Volume" in stock_df.columns else 0,
                "_matched": matched
            })

        results_df = pd.DataFrame(screener_rows)
        matched_df = results_df[results_df["_matched"]].copy().drop(columns=["_matched"])
        all_display_df = results_df.copy().drop(columns=["_matched"])

        total_screened = len(results_df)
        total_matched = len(matched_df)
        pass_rate = round((total_matched / total_screened) * 100, 1) if total_screened > 0 else 0.0

        sm1, sm2, sm3, sm4 = st.columns(4)
        with sm1:
            st.metric("Total in Basket", f"{total_screened}")
        with sm2:
            st.metric("Passed Filter", f"{total_matched}", f"{pass_rate}%")
        with sm3:
            st.metric("Filter Applied", f"{calc_type_name} ({ma1_period}, {ma2_period})")
        with sm4:
            st.metric("Strategy", screening_condition.split(":")[0])

        st.markdown("---")

        sc_tab1, sc_tab2, sc_tab3 = st.tabs([
            "📋 Screener Results Table", 
            "📈 Interactive Chart & MA Overlays", 
            "💾 Manage Server Baskets"
        ])

        with sc_tab1:
            t_col_filter, t_col_btn = st.columns([2, 1])
            with t_col_filter:
                show_only_matches = st.checkbox("Show only matching stocks", value=True)
            with t_col_btn:
                csv_export_df = matched_df if show_only_matches else all_display_df
                csv_bytes = csv_export_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Screener Results (CSV)",
                    data=csv_bytes,
                    file_name=f"screener_{curr_active_name}_{calc_type_name}_{ma1_period}_{ma2_period}.csv",
                    mime="text/csv",
                    type="primary",
                    width="stretch"
                )

            view_table = matched_df if show_only_matches else all_display_df
            st.dataframe(
                view_table,
                column_config={
                    "Close": st.column_config.NumberColumn(format="%.2f"),
                    f"MA1 ({ma1_period})": st.column_config.NumberColumn(format="%.2f"),
                    f"MA2 ({ma2_period})": st.column_config.NumberColumn(format="%.2f"),
                    "% Dist MA1": st.column_config.NumberColumn(format="%.2f%%"),
                    "% Dist MA2": st.column_config.NumberColumn(format="%.2f%%"),
                    "Volume": st.column_config.NumberColumn(format="%d")
                },
                width="stretch"
            )

        with sc_tab2:
            inspect_options = list(matched_df["Ticker"]) if len(matched_df) > 0 else list(loaded_basket_dfs.keys())
            if inspect_options:
                target_stock = st.selectbox("Select stock to inspect with MA Overlays:", options=inspect_options, index=0)
                inspect_stock_df = enriched_stock_dfs[target_stock].reset_index()
                d_col = inspect_stock_df.columns[0]

                st.write(f"### {target_stock} Price & Moving Average Signals")

                c_close = inspect_stock_df["Close"]
                c_ma1 = inspect_stock_df["MA1"]
                c_ma2 = inspect_stock_df["MA2"]

                dist_ma1_hist = ((c_close - c_ma1) / c_ma1) * 100
                dist_ma2_hist = ((c_close - c_ma2) / c_ma2) * 100

                cond_series = pd.Series(False, index=inspect_stock_df.index)
                marker_color = "#00C853"
                marker_shape = "triangle-up"
                marker_label = screening_condition.split(":")[0]

                if "Price > Short MA" in screening_condition:
                    cond_series = (c_close > c_ma1)
                    marker_color = "#00C853"
                    marker_shape = "triangle-up"
                elif "Price > Long MA" in screening_condition:
                    cond_series = (c_close > c_ma2)
                    marker_color = "#00C853"
                    marker_shape = "triangle-up"
                elif "Price < Short MA" in screening_condition:
                    cond_series = (c_close < c_ma1)
                    marker_color = "#FF1744"
                    marker_shape = "triangle-down"
                elif "Price < Long MA" in screening_condition:
                    cond_series = (c_close < c_ma2)
                    marker_color = "#FF1744"
                    marker_shape = "triangle-down"
                elif "Golden Cross" in screening_condition:
                    cond_series = (c_ma1 > c_ma2)
                    marker_color = "#00C853"
                    marker_shape = "triangle-up"
                elif "Death Cross" in screening_condition:
                    cond_series = (c_ma1 < c_ma2)
                    marker_color = "#FF1744"
                    marker_shape = "triangle-down"
                elif "Strong Uptrend" in screening_condition:
                    cond_series = (c_close > c_ma1) & (c_ma1 > c_ma2)
                    marker_color = "#00C853"
                    marker_shape = "triangle-up"
                elif f"Price within ±X% of Long MA ({ma2_period})" in screening_condition:
                    cond_series = (dist_ma2_hist.abs() <= tolerance_pct)
                    marker_color = "#FF6D00"
                    marker_shape = "circle"
                elif f"Price within ±X% of Short MA ({ma1_period})" in screening_condition:
                    cond_series = (dist_ma1_hist.abs() <= tolerance_pct)
                    marker_color = "#FF6D00"
                    marker_shape = "circle"

                prev_cond = cond_series.shift(1, fill_value=False)
                trigger_series = cond_series & (~prev_cond)

                trigger_count = int(trigger_series.sum())
                active_count = int(cond_series.sum())
                current_active = bool(cond_series.iloc[-1]) if len(cond_series) > 0 else False

                if is_dark:
                    card_border = "#2E7D32" if current_active else "#B71C1C"
                    card_bg = "rgba(46, 125, 50, 0.2)" if current_active else "rgba(183, 28, 28, 0.2)"
                    text_stat_color = "#81C784" if current_active else "#E57373"
                else:
                    card_border = "#2E7D32" if current_active else "#C62828"
                    card_bg = "#E8F5E9" if current_active else "#FFEBEE"
                    text_stat_color = "#2E7D32" if current_active else "#C62828"

                st.markdown(f"""
                <div style="background-color: {card_bg}; border: 1px solid {card_border}; border-radius: 8px; padding: 10px 16px; margin-bottom: 15px;">
                    <strong>🎯 Signal Summary for {target_stock}:</strong> 
                    Screening condition triggered <strong>{trigger_count} times</strong> in this period 
                    (active on <strong>{active_count} of {len(inspect_stock_df)}</strong> trading days) • 
                    Current Status: <strong style="color: {text_stat_color};">{'✅ Condition Met Today' if current_active else '❌ Condition Not Met Today'}</strong>
                </div>
                """, unsafe_allow_html=True)

                col_ctrl1, col_ctrl2 = st.columns([1, 2])
                with col_ctrl1:
                    show_markers = st.checkbox("📌 Point Out Condition Matches on Chart", value=True)
                with col_ctrl2:
                    if show_markers:
                        marker_mode = st.radio(
                            "Highlight Frequency:",
                            options=["Trigger Dates Only (Breakouts / Crosses)", "All Active Matching Days"],
                            horizontal=True,
                            index=0
                        )

                p_min = float(inspect_stock_df["Low"].min() if "Low" in inspect_stock_df.columns else inspect_stock_df["Close"].min())
                p_max = float(inspect_stock_df["High"].max() if "High" in inspect_stock_df.columns else inspect_stock_df["Close"].max())
                p_pad = (p_max - p_min) * 0.05 if (p_max - p_min) > 0 else max(1.0, p_min * 0.02)
                y_bounds = [max(0.0, p_min - p_pad), p_max + p_pad]

                chart_line_c = "#38BDF8" if is_dark else "#2962FF"

                price_line = (
                    alt.Chart(inspect_stock_df)
                    .mark_line(color=chart_line_c, strokeWidth=2)
                    .encode(
                        x=alt.X(f"{d_col}:T", title="Date"),
                        y=alt.Y("Close:Q", title="Price", scale=alt.Scale(domain=y_bounds, zero=False)),
                        tooltip=[
                            alt.Tooltip(f"{d_col}:T", title="Date"),
                            alt.Tooltip("Close:Q", title="Close Price", format=",.2f"),
                            alt.Tooltip("MA1:Q", title=f"{calc_type_name} {ma1_period}", format=",.2f"),
                            alt.Tooltip("MA2:Q", title=f"{calc_type_name} {ma2_period}", format=",.2f")
                        ]
                    )
                )

                ma1_line = (
                    alt.Chart(inspect_stock_df)
                    .mark_line(color="#FF9800", strokeWidth=1.5, strokeDash=[4, 2])
                    .encode(
                        x=alt.X(f"{d_col}:T"),
                        y=alt.Y("MA1:Q")
                    )
                )

                ma2_line = (
                    alt.Chart(inspect_stock_df)
                    .mark_line(color="#A855F7" if is_dark else "#9C27B0", strokeWidth=1.5)
                    .encode(
                        x=alt.X(f"{d_col}:T"),
                        y=alt.Y("MA2:Q")
                    )
                )

                chart_layers = [price_line, ma1_line, ma2_line]

                if show_markers:
                    selected_mask = trigger_series if "Trigger Dates Only" in marker_mode else cond_series
                    signal_df = inspect_stock_df[selected_mask].copy()
                    
                    if not signal_df.empty:
                        signal_df["Condition_Name"] = marker_label
                        signal_df["Dist_MA1_Display"] = dist_ma1_hist[selected_mask].round(2).astype(str) + "%"
                        signal_df["Dist_MA2_Display"] = dist_ma2_hist[selected_mask].round(2).astype(str) + "%"

                        markers_layer = (
                            alt.Chart(signal_df)
                            .mark_point(
                                shape=marker_shape,
                                size=150,
                                filled=True,
                                color=marker_color,
                                stroke="#FFFFFF" if is_dark else "#000000",
                                strokeWidth=1.2
                            )
                            .encode(
                                x=alt.X(f"{d_col}:T"),
                                y=alt.Y("Close:Q"),
                                tooltip=[
                                    alt.Tooltip(f"{d_col}:T", title="Trigger Date"),
                                    alt.Tooltip("Condition_Name:N", title="Condition Met"),
                                    alt.Tooltip("Close:Q", title="Price at Signal", format=",.2f"),
                                    alt.Tooltip("MA1:Q", title=f"{calc_type_name} {ma1_period}", format=",.2f"),
                                    alt.Tooltip("MA2:Q", title=f"{calc_type_name} {ma2_period}", format=",.2f"),
                                    alt.Tooltip("Dist_MA1_Display:N", title="% Dist from MA1"),
                                    alt.Tooltip("Dist_MA2_Display:N", title="% Dist from MA2")
                                ]
                            )
                        )
                        chart_layers.append(markers_layer)

                combined_chart = alt.layer(*chart_layers).properties(height=420).interactive()
                st.altair_chart(apply_chart_theme(combined_chart, is_dark), width="stretch")

                marker_icon = "🟢 ▲" if marker_shape == "triangle-up" else ("🔴 ▼" if marker_shape == "triangle-down" else "🟠 ●")
                st.caption(f"🔵 **Close Price** | 🟠 **{calc_type_name} {ma1_period}** (dashed) | 🟣 **{calc_type_name} {ma2_period}** (solid) | {marker_icon} **Condition Met Marker** ({marker_label})")

        with sc_tab3:
            st.subheader("📁 Server Baskets Storage (`./data/server_baskets/`)")
            all_baskets = list_server_baskets()
            if all_baskets:
                basket_table = [{
                    "Basket Name": b["name"],
                    "Stock Count": b["ticker_count"],
                    "Interval": b["interval"],
                    "Timeframe": b["date_tag"],
                    "Total Rows": b["total_rows"],
                    "Last Updated": b["last_modified"],
                    "File Path": b["csv_path"]
                } for b in all_baskets]
                st.dataframe(pd.DataFrame(basket_table), width="stretch")
            else:
                st.info("No baskets stored on server yet.")

    elif not curr_active_name and screener_source == "Select Stored Server Basket":
        st.info("👈 Please select or create a server basket from the sidebar to start screening.")

st.markdown("---")
st.caption("Built with Streamlit & yfinance | JoshiQuants")
