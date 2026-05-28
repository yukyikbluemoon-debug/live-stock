import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import altair as alt
import json
from datetime import datetime, timedelta
import io
from streamlit_echarts import st_echarts
import plotly.graph_objects as go
import streamlit.components.v1 as components

import numpy as np

# Page config
st.set_page_config(page_title="📈 แดชบอร์ดหุ้น Live", layout="wide")

# ------------------------------------------------------------------
# BUG FIX #1: Lottie splash — ใส่ try/except + ไม่ใช้ time.sleep()
# เดิม: crash ถ้าไม่มีไฟล์ json, sleep(4) บล็อก thread หลัก
# ------------------------------------------------------------------
if "show_intro" not in st.session_state:
    st.session_state.show_intro = True

if st.session_state.show_intro:
    try:
        from streamlit_lottie import st_lottie
        import time
        with open("Money Investment.json", "r", encoding="utf-8") as f:
            lottie_intro = json.load(f)
        splash = st.empty()
        with splash.container():
            st.markdown("<h1 style='text-align:center;'>ยินดีต้อนรับสู่แดชบอร์ดตลาดหุ้น !</h1>",
                        unsafe_allow_html=True)
            st_lottie(lottie_intro, height=280, speed=1.0, loop=False, key="intro_lottie")
            time.sleep(3)
        splash.empty()
    except Exception:
        pass  # ไม่มีไฟล์ Lottie หรือ library → ข้ามไปเลย ไม่ crash
    st.session_state.show_intro = False

st.header("📈 แดชบอร์ดหุ้น Live")

# ------------------------------------------------------------------
# BUG FIX #2: STOCKS list — นิยามครั้งเดียวระดับ module
# เดิม: copy-paste ซ้ำ 3 จุด (tab1, tab2, tab5) → แก้ที่เดียว
# ------------------------------------------------------------------
STOCKS = [
    # === หุ้นขนาดใหญ่ (Large Cap) ===
    "AAPL","ABBV","ACN","ADBE","ADP","AMD","AMGN","AMT","AMZN","APD",
    "AVGO","AXP","BA","BK","BKNG","BMY","BRK.B","BSX","C","CAT","CI",
    "CL","CMCSA","COST","CRM","CSCO","CVX","DE","DHR","DIS","DUK",
    "ELV","EOG","EQR","FDX","GD","GE","GILD","GOOG","GOOGL","HD",
    "HON","HUM","IBM","ICE","INTC","ISRG","JNJ","JPM","KO","LIN",
    "LLY","LMT","LOW","MA","MCD","MDLZ","META","MMC","MO","MRK",
    "MSFT","NEE","NFLX","NKE","NOW","NVDA","ORCL","PEP","PFE","PG",
    "PLD","PM","PSA","REGN","RTX","SBUX","SCHW","SLB","SO","SPGI",
    "T","TJX","TMO","TSLA","TXN","UNH","UNP","UPS","V","VZ","WFC",
    "WM","WMT","XOM",
    # === หุ้นเพิ่มเติม ===
    "ABNB","AMAT","APP","AXON","BDX","BIIB","BLK","CEG","CF","CHTR",
    "COF","COP","CTAS","DECK","DG","DHI","DLTR","DOV","EA","ECL",
    "ETN","EW","FAST","FCX","FICO","FTNT","GIS","GPC","GPN","GRMN",
    "GS","HAL","HCA","HES","HIG","HLT","HPE","HPQ","HSY","IQV",
    "IR","IT","ITW","JCI","KEY","KEYS","KHC","KLAC","KMB","KMI",
    "KR","LRCX","LUV","LVS","LYB","MAR","MCO","MELI","MGM","MPC",
    "MPWR","MRO","MS","MU","NEM","NET","NSC","NTAP","NUE","O",
    "OKE","ON","PAYX","PCAR","PCG","PH","PKG","PPG","PRU","PWR",
    "PYPL","QCOM","RCL","RF","RJF","RL","RMD","ROK","ROP","ROST",
    "RSG","SHW","SNPS","SPG","SPOT","SRE","STT","STX","STZ","SWK",
    "SYK","SYY","TMUS","TROW","TRV","TSCO","TTWO","UAL","URI","USB",
    "VICI","VLO","VMC","VRSK","VRTX","VST","WAB","WAT","WBA","WEC",
    "WELL","WDC","WYNN","XEL","YUM","ZBH","ZBRA","ZTS",
    # === ETF - ดัชนีรวม ===
    "SPY","VOO","IVV","VTI","QQQ","IWM","DIA","MDY","IJH","IJR",
    "VT","ITOT","SCHB","SPTM",
    # === ETF - กลุ่มเทคโนโลยี ===
    "XLK","VGT","FTEC","IGV","SOXX","SMH","CIBR","SKYY","CLOU",
    "ARKK","ARKQ","ARKG","ARKW","ARKF","ROBO","BOTZ","AIQ",
    # === ETF - พลังงาน / โภคภัณฑ์ ===
    "XLE","VDE","IYE","OIH","XOP","GLD","IAU","SLV","GDX","GDXJ",
    "USO","UNG","DBC","PDBC",
    # === ETF - การเงิน / อสังหาริมทรัพย์ ===
    "XLF","VFH","KBE","KRE","VNQ","IYR","SCHH",
    # === ETF - สุขภาพ ===
    "XLV","VHT","IYH","IBB","XBI",
    # === ETF - สินค้า / อุตสาหกรรม ===
    "XLP","VDC","XLI","VIS","XLB","VAW",
    # === ETF - พันธบัตร ===
    "AGG","BND","TLT","IEF","SHY","LQD","HYG","JNK","TIP","VTIP",
    "GOVT","MUB","BSV","BIV","BLV","VCSH","VCIT",
    # === ETF - ต่างประเทศ ===
    "VEA","VWO","EFA","EEM","IDEV","IEMG","EWJ","EWZ","EWU","EWG",
    "EWC","KWEB","MCHI","FXI","INDA","EWY","EWT","VGK","VXUS",
    # === ETF - เงินปันผล ===
    "SCHD","VYM","DVY","HDV","SPHD","DGRO","VIG","SDY","NOBL",
    # === ETF - เลเวอเรจ ===
    "TQQQ","SQQQ","UPRO","SPXU","UVXY","VXX","SOXL","SOXS",
    # === Bitcoin / Crypto ETF ===
    "IBIT","FBTC","BITB","ARKB","GBTC","ETHA",
]

HORIZON_MAP = {
    "1 เดือน": "1mo",
    "3 เดือน": "3mo",
    "6 เดือน": "6mo",
    "1 ปี":    "1y",
    "5 ปี":    "5y",
    "10 ปี":   "10y",
    "20 ปี":   "20y",
}

# ------------------------------------------------------------------
# BUG FIX #3: fetch_stock_details — ตรวจ N/A ก่อน format ทุก field
# เดิม: ไม่ตรวจ history ว่าง → KeyError; dividend_yield ไม่ตรวจ type
# ------------------------------------------------------------------
@st.cache_data(ttl=3600, max_entries=50)
def fetch_stock_details(ticker: str, period: str = "1mo"):
    """
    ดึงข้อมูลหุ้นทั้งหมดใน 1 ฟังก์ชัน + cache 1 ชั่วโมง
    รวม longName และ sector ไว้ด้วย — ไม่ต้องเรียก .info ซ้ำในที่อื่น
    จัดการ YFRateLimitError ด้วย exponential backoff สูงสุด 3 รอบ
    """
    import time as _time
    from yfinance.exceptions import YFRateLimitError

    empty_df  = pd.DataFrame(columns=["Open", "High", "Low", "Close"])
    empty_det = {
        "price": "N/A", "change_pct": 0.0, "market_cap": "N/A",
        "pe_ratio": "N/A", "eps": "N/A", "high_52w": "N/A",
        "low_52w": "N/A", "volume": "N/A", "dividend_yield": "N/A",
        "long_name": ticker, "sector": "N/A",
    }

    for attempt in range(3):
        try:
            stock = yf.Ticker(ticker)
            info  = stock.fast_info          # เร็วกว่า .info — ดึงเฉพาะ price fields
            # .info ยังต้องการสำหรับ PE/EPS/sector/longName — เรียกแค่ครั้งเดียวต่อ cache cycle
            full  = stock.info

            def safe_get(key, default="N/A"):
                val = full.get(key, default)
                return val if val is not None else default

            price      = info.last_price or safe_get("regularMarketPrice")
            prev_close = info.previous_close or safe_get("previousClose", 0.0)
            try:
                change_pct = ((float(price) - float(prev_close)) / float(prev_close) * 100) if prev_close else 0.0
            except Exception:
                change_pct = 0.0

            div_yield = safe_get("dividendYield")
            if not isinstance(div_yield, (int, float)):
                div_yield = "N/A"

            details = {
                "price":          round(float(price), 2) if isinstance(price, (int, float)) else "N/A",
                "change_pct":     round(change_pct, 2),
                "market_cap":     safe_get("marketCap"),
                "pe_ratio":       safe_get("trailingPE"),
                "eps":            safe_get("trailingEps"),
                "high_52w":       safe_get("fiftyTwoWeekHigh"),
                "low_52w":        safe_get("fiftyTwoWeekLow"),
                "volume":         safe_get("volume"),
                "dividend_yield": div_yield,
                "long_name":      safe_get("longName", ticker),
                "sector":         safe_get("sector", "N/A"),
            }

            cols_needed = {"Open", "High", "Low", "Close"}
            try:
                history = stock.history(period=period, interval="1d")
                if history.empty or not cols_needed.issubset(history.columns):
                    history = empty_df
                else:
                    history = history[list(cols_needed)]
            except YFRateLimitError:
                raise                          # re-raise เพื่อให้ backoff loop จัดการ
            except Exception:
                history = empty_df

            return details, history

        except YFRateLimitError:
            if attempt < 2:
                wait = 2 ** attempt            # 1s, 2s
                _time.sleep(wait)
                continue
            # ครบ 3 รอบแล้ว — แสดง warning ไม่ crash
            st.warning(f"⚠️ Yahoo Finance rate limit — ข้อมูล {ticker} อาจแสดงไม่ครบ กรุณารอสักครู่แล้ว refresh")
            return empty_det, empty_df

        except Exception as e:
            st.warning(f"ดึงข้อมูล {ticker} ไม่สำเร็จ: {e}")
            return empty_det, empty_df

    return empty_det, empty_df


# ------------------------------------------------------------------
# BUG FIX #4: get_current_price — cache + ตรวจ None ก่อนคืนค่า
# ใช้แทนการเรียก yf.Ticker().history() ตรงๆ ใน portfolio loop
# ------------------------------------------------------------------
@st.cache_data(ttl=300, max_entries=200)
def get_current_price(ticker: str) -> float | None:
    from yfinance.exceptions import YFRateLimitError
    try:
        fi = yf.Ticker(ticker).fast_info
        if fi.last_price:
            return round(float(fi.last_price), 2)
    except YFRateLimitError:
        return None   # silent — portfolio ยังแสดงได้ แค่ราคา N/A
    except Exception:
        pass
    return None


# ------------------------------------------------------------------
# Sidebar metrics — 7 หุ้นหลัก
# ------------------------------------------------------------------
SIDEBAR_SYMBOLS = {
    "Apple": "AAPL", "Microsoft": "MSFT", "Tesla": "TSLA",
    "NVIDIA": "NVDA", "Amazon": "AMZN", "Google": "GOOG", "Meta": "META",
}

@st.cache_data(ttl=3600)
def get_daily_details(sym_dict: dict) -> dict:
    """ดึงราคา 7 หุ้นใน batch request เดียว + จัดการ rate limit"""
    from yfinance.exceptions import YFRateLimitError
    tickers_list = list(sym_dict.values())
    names_list   = list(sym_dict.keys())
    details = {}
    try:
        raw = yf.download(
            tickers_list, period="2d", interval="1d",
            auto_adjust=True, progress=False, threads=False,  # threads=False ลด concurrent request
        )
        if raw.empty:
            return details
        close = raw["Close"]
        open_ = raw["Open"]
        for name, ticker in zip(names_list, tickers_list):
            try:
                c = float(close[ticker].dropna().iloc[-1])
                o = float(open_[ticker].dropna().iloc[-1])
                pct = ((c - o) / o * 100) if o else 0.0
                details[name] = {"price": round(c, 2), "change_pct": round(pct, 2)}
            except Exception:
                pass
    except YFRateLimitError:
        st.sidebar.warning("⚠️ Yahoo Finance rate limit — ข้อมูล sidebar อาจไม่อัปเดต")
    except Exception:
        pass
    return details


@st.cache_data(ttl=36000)
def fetch_metrics() -> pd.DataFrame:
    """ดึง PE/EPS/Rating ทั้ง 7 หุ้นใน Tickers batch — ลด round-trip"""
    symbols_list = list(SIDEBAR_SYMBOLS.values())
    names_list   = list(SIDEBAR_SYMBOLS.keys())
    rows = []
    try:
        batch = yf.Tickers(" ".join(symbols_list))
        for name, symbol in zip(names_list, symbols_list):
            try:
                info = batch.tickers[symbol].fast_info
                # fast_info ไม่มี PE/EPS ต้องใช้ .info แต่ cache ttl=10h ไม่บ่อย
                full = batch.tickers[symbol].info
                rows.append({
                    "บริษัท":             name,
                    "อัตราส่วน PE":       full.get("trailingPE", "N/A"),
                    "กำไรต่อหุ้น (EPS)":  full.get("trailingEps", "N/A"),
                    "คะแนนนักวิเคราะห์":  full.get("recommendationMean", "N/A"),
                })
            except Exception:
                rows.append({
                    "บริษัท": name,
                    "อัตราส่วน PE": "N/A",
                    "กำไรต่อหุ้น (EPS)": "N/A",
                    "คะแนนนักวิเคราะห์": "N/A",
                })
    except Exception as e:
        st.error(f"fetch_metrics error: {e}")
    return pd.DataFrame(rows)


@st.cache_data(ttl=21600)
def fetch_news(ticker: str) -> list:
    try:
        return yf.Ticker(ticker).news or []
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข่าว: {e}")
        return []


def next_saturday(start_date=None) -> datetime:
    # BUG FIX #5: เขียนใหม่ให้อ่านง่าย logic เดิมถูกต้องแต่สับสน
    if start_date is None:
        start_date = datetime.today()
    days_ahead = (5 - start_date.weekday()) % 7  # 5 = เสาร์
    if days_ahead == 0:
        days_ahead = 7  # ถ้าวันนี้เสาร์แล้ว ไปเสาร์หน้า
    return start_date + timedelta(days=days_ahead)


# ==================================================================
# TAB 2 — แนวโน้มกลุ่ม (Peer Analysis)
# ==================================================================
def show_peer_analysis():
    DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN", "TSLA", "META"]

    # เซฟ selection ใน session_state → ไม่หายเมื่อ switch tab
    if "peer_tickers" not in st.session_state:
        st.session_state.peer_tickers = DEFAULT_TICKERS
    if "peer_horizon" not in st.session_state:
        st.session_state.peer_horizon = "6 เดือน"

    tickers = st.multiselect(
        "เลือกหุ้นที่ต้องการเปรียบเทียบ",
        STOCKS,
        default=st.session_state.peer_tickers,
        key="peer_tickers_widget",
    )
    # sync กลับเข้า session_state ทุกครั้งที่ค่าเปลี่ยน
    if tickers != st.session_state.peer_tickers:
        st.session_state.peer_tickers = tickers

    horizon = st.selectbox(
        "เลือกช่วงเวลา",
        list(HORIZON_MAP.keys()),
        index=list(HORIZON_MAP.keys()).index(st.session_state.peer_horizon),
        key="peer_horizon_widget",
    )
    if horizon != st.session_state.peer_horizon:
        st.session_state.peer_horizon = horizon

    if not tickers:
        st.info("กรุณาเลือกหุ้นเพื่อเปรียบเทียบ")
        return

    @st.cache_data(ttl=21600)
    def load_peer_data(tickers_tuple: tuple, period: str) -> pd.DataFrame:
        """ดึงราคา Close ทุก ticker ใน batch request เดียว"""
        if not tickers_tuple:
            return pd.DataFrame()
        try:
            raw = yf.download(
                list(tickers_tuple), period=period, interval="1d",
                auto_adjust=True, progress=False, threads=False,  # threads=False ลด concurrent request
            )
            if raw.empty:
                return pd.DataFrame()
            # yf.download คืน MultiIndex columns เมื่อ > 1 ticker
            if isinstance(raw.columns, pd.MultiIndex):
                close = raw["Close"].copy()
            else:
                # ticker เดียว — columns แบน
                close = raw[["Close"]].copy()
                close.columns = list(tickers_tuple)
            return close
        except Exception:
            return pd.DataFrame()

    # tuple เพื่อให้ cache key hashable
    data = load_peer_data(tuple(tickers), HORIZON_MAP[horizon])

    if data.empty or data.isna().all().all():
        st.error("ไม่มีข้อมูลราคาสำหรับการทำให้เป็นมาตรฐาน")
        return

    clean_data = data.dropna(how="any")
    if clean_data.shape[0] < 2:
        st.error("ข้อมูลที่สะอาดไม่เพียงพอ")
        return

    normalized = clean_data.div(clean_data.iloc[0])
    normalized.index.name = "วันที่"

    st.altair_chart(
        alt.Chart(
            normalized.reset_index().melt(id_vars=["วันที่"], var_name="หุ้น", value_name="ราคาปรับมาตรฐาน")
        )
        .mark_line()
        .encode(
            alt.X("วันที่:T"),
            alt.Y("ราคาปรับมาตรฐาน:Q").scale(zero=False),
            alt.Color("หุ้น:N"),
        )
        .properties(height=400),
        use_container_width=True,
    )

    # ── sparkline cards ──
    # ดึงราคาจาก data ที่ load_peer_data โหลดมาแล้ว (ไม่ยิง HTTP ใหม่)
    # info เรียกครั้งเดียวต่อ ticker + cache 1 ชั่วโมง
    @st.cache_data(ttl=3600)
    def get_ticker_quote(ticker: str) -> dict:
        try:
            fi = yf.Ticker(ticker).fast_info   # fast_info เร็วกว่า .info มาก
            return {
                "price":      round(float(fi.last_price), 2) if fi.last_price else None,
                "prev_close": round(float(fi.previous_close), 2) if fi.previous_close else None,
            }
        except Exception:
            return {"price": None, "prev_close": None}

    with st.expander("💵 ราคาปัจจุบันของบริษัทที่เลือก", expanded=True):
        for i in range(0, len(tickers), 4):
            row = st.columns(min(4, len(tickers) - i))
            for j, ticker in enumerate(tickers[i : i + 4]):
                try:
                    quote = get_ticker_quote(ticker)
                    price = quote["price"]
                    prev  = quote["prev_close"]
                    change_pct = ((price - prev) / prev * 100) if price and prev else 0.0

                    # ใช้ data ที่โหลดมาแล้วแทนยิง HTTP ใหม่
                    if ticker in data.columns:
                        hist  = data[ticker].dropna()
                        color = "green" if hist.iloc[-1] > hist.iloc[0] else "red"
                        sparkline_data = pd.DataFrame({"วันที่": hist.index, "ราคา": hist.values})
                        with row[j].container(border=True):
                            st.metric(label=ticker,
                                      value=f"${price}" if price else "N/A",
                                      delta=f"{change_pct:.2f}%")
                            st.altair_chart(
                                alt.Chart(sparkline_data)
                                .mark_line(color=color)
                                .encode(
                                    x=alt.X("วันที่:T", axis=None),
                                    y=alt.Y("ราคา:Q",
                                            scale=alt.Scale(domain=[float(hist.min()), float(hist.max())]),
                                            axis=None),
                                )
                                .properties(height=100),
                                use_container_width=True,
                            )
                    else:
                        with row[j].container(border=True):
                            st.metric(label=ticker, value="N/A", delta="N/A")
                except Exception:
                    with row[j].container(border=True):
                        st.metric(label=ticker, value="N/A", delta="N/A")

    if len(tickers) > 1:
        st.markdown("### รายบริษัท vs ค่าเฉลี่ยกลุ่ม")
        cols = st.columns(4)
        for i, ticker in enumerate(tickers):
            peers    = normalized.drop(columns=[ticker])
            peer_avg = peers.mean(axis=1)
            plot_data = pd.DataFrame({
                "วันที่": normalized.index,
                ticker:       normalized[ticker],
                "ค่าเฉลี่ยกลุ่ม": peer_avg,
            }).melt(id_vars=["วันที่"], var_name="ชุดข้อมูล", value_name="ราคา")

            chart = (
                alt.Chart(plot_data)
                .mark_line()
                .encode(
                    alt.X("วันที่:T"),
                    alt.Y("ราคา:Q").scale(zero=False),
                    alt.Color("ชุดข้อมูล:N", scale=alt.Scale(
                        domain=[ticker, "ค่าเฉลี่ยกลุ่ม"], range=["red", "gray"]
                    )),
                    alt.Tooltip(["วันที่", "ชุดข้อมูล", "ราคา"]),
                )
                .properties(title=f"{ticker} vs ค่าเฉลี่ยกลุ่ม", height=300)
            )
            cols[(i * 2) % 4].container(border=True).altair_chart(chart, use_container_width=True)

            delta_chart = (
                alt.Chart(
                    pd.DataFrame({"วันที่": normalized.index, "ส่วนต่าง": normalized[ticker] - peer_avg})
                )
                .mark_area()
                .encode(alt.X("วันที่:T"), alt.Y("ส่วนต่าง:Q").scale(zero=False))
                .properties(title=f"{ticker} ลบค่าเฉลี่ยกลุ่ม", height=300)
            )
            cols[(i * 2 + 1) % 4].container(border=True).altair_chart(delta_chart, use_container_width=True)

    # ------------------------------------------------------------------
    # CANDLESTICK + EMA + TRENDLINES section
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🕯️ กราฟแท่งเทียน + EMA + แนวรับ/แนวต้าน")
    st.caption("เลือกหุ้นและตัวเลือกที่ต้องการแสดงบนกราฟ")

    @st.cache_data(ttl=3600)
    def load_candle_data(ticker: str, period: str) -> pd.DataFrame:
        try:
            df = yf.Ticker(ticker).history(period=period, interval="1d")
            if df.empty:
                return pd.DataFrame()
            df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
            df.index = pd.to_datetime(df.index)
            return df
        except Exception:
            return pd.DataFrame()

    def calc_ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()

    def calc_support(df: pd.DataFrame, window: int = 20) -> float:
        """แนวรับ = ค่าต่ำสุดของ Low ใน rolling window ช่วงท้าย"""
        if df.empty or len(df) < window:
            return float(df["Low"].min()) if not df.empty else 0.0
        return float(df["Low"].rolling(window).min().dropna().iloc[-1])

    def calc_trendline(df: pd.DataFrame, col: str = "Close", last_n: int = 60):
        """
        คำนวณ Linear regression ผ่านจุดสูงสุด (Downtrend) หรือต่ำสุด (Uptrend)
        คืน (x0, y0, x1, y1) ในหน่วย index int สำหรับ plotly shape
        """
        import numpy as np
        sub = df[col].tail(last_n)
        if len(sub) < 10:
            return None
        x = np.arange(len(sub))
        y = sub.values
        # Uptrend line — ผ่านจุดต่ำสุด (local minima)
        up_idx   = [i for i in range(1, len(y)-1) if y[i] <= y[i-1] and y[i] <= y[i+1]]
        # Downtrend line — ผ่านจุดสูงสุด (local maxima)
        dn_idx   = [i for i in range(1, len(y)-1) if y[i] >= y[i-1] and y[i] >= y[i+1]]
        results = {}
        for label, idx_list in [("up", up_idx), ("dn", dn_idx)]:
            if len(idx_list) < 2:
                results[label] = None
                continue
            xi = np.array(idx_list)
            yi = y[xi]
            m, b = np.polyfit(xi, yi, 1)
            x_start = int(xi[0])
            x_end   = len(sub) - 1
            y_start = m * x_start + b
            y_end   = m * x_end   + b
            # แปลง index กลับเป็น datetime
            dates = sub.index
            results[label] = {
                "x0": dates[x_start], "y0": float(y_start),
                "x1": dates[x_end],   "y1": float(y_end),
            }
        return results

    # ── ตัวเลือก ──
    candle_ticker = st.selectbox(
        "เลือกหุ้นสำหรับกราฟแท่งเทียน",
        tickers,
        key="candle_ticker",
    )
    candle_horizon = st.selectbox(
        "ช่วงเวลา",
        list(HORIZON_MAP.keys()),
        index=list(HORIZON_MAP.keys()).index("6 เดือน"),
        key="candle_horizon",
    )

    # ── Tooltip descriptions ──
    TT = {
        "ema20":   ("EMA 20 | ค่าเฉลี่ยเคลื่อนที่ Exponential 20 วัน "
                    "| ตอบสนองไวต่อราคา ใช้จับแนวโน้มระยะสั้น "
                    "| ราคาเหนือ EMA20 = momentum ขาขึ้น / ใต้ = ขาลง"),
        "ema50":   ("EMA 50 | ค่าเฉลี่ยเคลื่อนที่ Exponential 50 วัน "
                    "| แนวโน้มระยะกลาง 2-3 เดือน "
                    "| Golden Cross: EMA20 ตัด EMA50 ขึ้น = สัญญาณซื้อ "
                    "| Death Cross: EMA20 ตัด EMA50 ลง = สัญญาณขาย"),
        "ema100":  ("EMA 100 | ค่าเฉลี่ยเคลื่อนที่ Exponential 100 วัน "
                    "| แนวโน้มระยะยาว ~5 เดือน "
                    "| มักใช้เป็นแนวรับ/แนวต้านขนาดใหญ่"),
        "uptrend": ("Uptrend Line | เส้นตรง Linear Regression ผ่านจุด Low ต่ำสุด 60 แท่ง "
                    "| แสดงทิศทางขาขึ้น "
                    "| ราคาสัมผัสเส้นนี้ = Buy Zone "
                    "| ราคาทะลุลงมา = สัญญาณเตือน"),
        "dntrend": ("Downtrend Line | เส้นตรง Linear Regression ผ่านจุด High สูงสุด 60 แท่ง "
                    "| แสดงทิศทางขาลง "
                    "| ราคาสัมผัสเส้นนี้ = Sell Zone "
                    "| ราคาทะลุขึ้นไป = Breakout สัญญาณบวก"),
        "sup":     ("Support Level | ราคาต่ำสุดของ Low ใน 20 แท่งล่าสุด "
                    "| โซนที่แรงซื้อมักเข้ามา ราคามักเด้งกลับ "
                    "| ถ้าหลุดลงไป Support กลายเป็น Resistance"),
        "res":     ("Resistance Level | ราคาสูงสุดของ High ใน 20 แท่งล่าสุด "
                    "| โซนที่แรงขายมักเข้ามา ราคามักย่อกลับ "
                    "| ถ้าทะลุขึ้นไปได้ Resistance กลายเป็น Support"),
        "bb":      ("Bollinger Bands (20 period, 2sigma) "
                    "| Upper=SMA20+2xSD  Mid=SMA20  Lower=SMA20-2xSD "
                    "| ราคาแตะ Upper = Overbought | ราคาแตะ Lower = Oversold "
                    "| Bands แคบ = กำลังสะสมพลัง | Bands กว้าง = ความผันผวนสูง"),
        "rsi":     ("RSI (14 วัน) | วัด momentum 0-100 "
                    "| RSI > 70 = Overbought | RSI < 30 = Oversold | RSI = 50 = สมดุล "
                    "| Divergence: ราคาทำ High ใหม่แต่ RSI ไม่ทำ = สัญญาณพลิกกลับ"),
        "vwap":    ("VWAP | ราคาเฉลี่ยถ่วงน้ำหนักด้วยปริมาณซื้อขาย "
                    "| Benchmark หลักของสถาบันและ day trader "
                    "| เหนือ VWAP = แรงซื้อครองตลาด | ใต้ VWAP = แรงขายครองตลาด"),
    }
    # ── Checkbox row 1: EMA + Trend ──
    st.markdown("**📈 Moving Average & Trend**")
    col_opts = st.columns(6)
    show_ema20  = col_opts[0].checkbox("EMA 20",         value=True,  key="ema20",   help=TT["ema20"])
    show_ema50  = col_opts[1].checkbox("EMA 50",         value=True,  key="ema50",   help=TT["ema50"])
    show_ema100 = col_opts[2].checkbox("EMA 100",        value=False, key="ema100",  help=TT["ema100"])
    show_up     = col_opts[3].checkbox("Uptrend Line",   value=True,  key="uptrend", help=TT["uptrend"])
    show_dn     = col_opts[4].checkbox("Downtrend Line", value=True,  key="dntrend", help=TT["dntrend"])
    show_vwap   = col_opts[5].checkbox("VWAP",           value=False, key="vwap",    help=TT["vwap"])

    # ── Checkbox row 2: Support/Resistance + BB + RSI ──
    st.markdown("**📊 Support / Resistance / Oscillator**")
    col_opts2 = st.columns(6)
    show_sup    = col_opts2[0].checkbox("Support Level",   value=True,  key="support", help=TT["sup"])
    show_res    = col_opts2[1].checkbox("Resistance Level",value=True,  key="resist",  help=TT["res"])
    show_bb     = col_opts2[2].checkbox("Bollinger Bands", value=True,  key="bb",      help=TT["bb"])
    show_rsi    = col_opts2[3].checkbox("RSI (14)",        value=True,  key="rsi",     help=TT["rsi"])
    _unused2    = col_opts2[4].empty()
    _unused3    = col_opts2[5].empty()

    cdf = load_candle_data(candle_ticker, HORIZON_MAP[candle_horizon])

    if cdf.empty:
        st.warning(f"ไม่มีข้อมูล OHLC สำหรับ {candle_ticker}")
    else:
        # ── Helper functions ──
        def calc_resistance(df: pd.DataFrame, window: int = 20) -> float:
            if df.empty or len(df) < window:
                return float(df["High"].max()) if not df.empty else 0.0
            return float(df["High"].rolling(window).max().dropna().iloc[-1])

        def calc_bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
            sma   = series.rolling(window).mean()
            std   = series.rolling(window).std()
            upper = sma + num_std * std
            lower = sma - num_std * std
            return upper, sma, lower

        def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
            delta = series.diff()
            gain  = delta.clip(lower=0).rolling(period).mean()
            loss  = (-delta.clip(upper=0)).rolling(period).mean()
            rs    = gain / loss.replace(0, float("nan"))
            return 100 - (100 / (1 + rs))

        def calc_vwap(df: pd.DataFrame) -> pd.Series:
            typical = (df["High"] + df["Low"] + df["Close"]) / 3
            cum_vol = df["Volume"].cumsum()
            cum_tp  = (typical * df["Volume"]).cumsum()
            return cum_tp / cum_vol.replace(0, float("nan"))

        last_close = float(cdf["Close"].iloc[-1])

        # ── คำนวณ indicators ──
        sup_level = calc_support(cdf)
        res_level = calc_resistance(cdf)
        bb_upper, bb_mid, bb_lower = calc_bollinger(cdf["Close"])
        rsi_series = calc_rsi(cdf["Close"])
        vwap_series = calc_vwap(cdf)

        # ── กำหนด domain ตาม subplot ที่เปิดอยู่ ──
        # แกน y1=candle, y2=volume, y3=RSI
        has_rsi = show_rsi
        if has_rsi:
            candle_domain = [0.40, 1.0]
            vol_domain    = [0.25, 0.37]
            rsi_domain    = [0.0,  0.22]
        else:
            candle_domain = [0.25, 1.0]
            vol_domain    = [0.0,  0.20]
            rsi_domain    = [0.0,  0.0]

        # ── สร้างกราฟหลัก ──
        fig_c = go.Figure()

        # 1. แท่งเทียน
        fig_c.add_trace(go.Candlestick(
            x=cdf.index,
            open=cdf["Open"], high=cdf["High"],
            low=cdf["Low"],   close=cdf["Close"],
            name="OHLC",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            increasing_fillcolor="#26a69a",
            decreasing_fillcolor="#ef5350",
            yaxis="y1",
        ))

        # 2. EMA lines
        ema_cfg = [
            (show_ema20,  20,  "#FFD700", "EMA 20"),
            (show_ema50,  50,  "#FF8C00", "EMA 50"),
            (show_ema100, 100, "#FF4500", "EMA 100"),
        ]
        for enabled, span, color, lbl in ema_cfg:
            if enabled and len(cdf) >= span:
                fig_c.add_trace(go.Scatter(
                    x=cdf.index, y=calc_ema(cdf["Close"], span),
                    mode="lines", name=lbl,
                    line=dict(color=color, width=1.5),
                    yaxis="y1",
                    hovertemplate=f"{lbl}: %{{y:.2f}}<extra></extra>",
                ))

        # 3. Bollinger Bands — ใส่ fill ระหว่าง upper/lower
        if show_bb:
            fig_c.add_trace(go.Scatter(
                x=cdf.index, y=bb_upper,
                mode="lines", name="BB Upper",
                line=dict(color="rgba(150,150,255,0.7)", width=1, dash="dot"),
                yaxis="y1",
                hovertemplate="BB Upper: %{y:.2f}<extra></extra>",
            ))
            fig_c.add_trace(go.Scatter(
                x=cdf.index, y=bb_mid,
                mode="lines", name="BB Mid (SMA20)",
                line=dict(color="rgba(150,150,255,0.5)", width=1),
                yaxis="y1",
                hovertemplate="BB Mid: %{y:.2f}<extra></extra>",
            ))
            fig_c.add_trace(go.Scatter(
                x=cdf.index, y=bb_lower,
                mode="lines", name="BB Lower",
                fill="tonexty",
                fillcolor="rgba(100,100,200,0.07)",
                line=dict(color="rgba(150,150,255,0.7)", width=1, dash="dot"),
                yaxis="y1",
                hovertemplate="BB Lower: %{y:.2f}<extra></extra>",
            ))

        # 4. VWAP
        if show_vwap:
            fig_c.add_trace(go.Scatter(
                x=cdf.index, y=vwap_series,
                mode="lines", name="VWAP",
                line=dict(color="#E040FB", width=1.5, dash="dashdot"),
                yaxis="y1",
                hovertemplate="VWAP: %{y:.2f}<extra></extra>",
            ))

        # 5. Support & Resistance hlines
        if show_sup:
            fig_c.add_hline(
                y=sup_level, yref="y1",
                line=dict(color="#00BFFF", width=1.5, dash="dot"),
                annotation_text=f"Support ${sup_level:.2f}",
                annotation_position="bottom right",
                annotation_font_color="#00BFFF",
            )
        if show_res:
            fig_c.add_hline(
                y=res_level, yref="y1",
                line=dict(color="#FF69B4", width=1.5, dash="dot"),
                annotation_text=f"Resistance ${res_level:.2f}",
                annotation_position="top right",
                annotation_font_color="#FF69B4",
            )

        # 6. Trendlines
        trend_n = min(60, len(cdf))
        trends = calc_trendline(cdf, last_n=trend_n)
        if trends:
            if show_up and trends.get("up"):
                t = trends["up"]
                fig_c.add_shape(type="line",
                    x0=t["x0"], y0=t["y0"], x1=t["x1"], y1=t["y1"],
                    yref="y1", xref="x",
                    line=dict(color="#00FF7F", width=1.5, dash="dash"),
                )
                fig_c.add_annotation(x=t["x1"], y=t["y1"], yref="y1",
                    text="Uptrend", font=dict(color="#00FF7F", size=11),
                    showarrow=False, xanchor="left")
            if show_dn and trends.get("dn"):
                t = trends["dn"]
                fig_c.add_shape(type="line",
                    x0=t["x0"], y0=t["y0"], x1=t["x1"], y1=t["y1"],
                    yref="y1", xref="x",
                    line=dict(color="#FF6B6B", width=1.5, dash="dash"),
                )
                fig_c.add_annotation(x=t["x1"], y=t["y1"], yref="y1",
                    text="Downtrend", font=dict(color="#FF6B6B", size=11),
                    showarrow=False, xanchor="left")

        # 7. Volume bar
        fig_c.add_trace(go.Bar(
            x=cdf.index, y=cdf["Volume"],
            name="Volume",
            marker_color=["#26a69a" if c >= o else "#ef5350"
                          for c, o in zip(cdf["Close"], cdf["Open"])],
            yaxis="y2", opacity=0.45,
            hovertemplate="Vol: %{y:,.0f}<extra></extra>",
        ))

        # 8. RSI subplot
        if show_rsi:
            fig_c.add_trace(go.Scatter(
                x=cdf.index, y=rsi_series,
                mode="lines", name="RSI (14)",
                line=dict(color="#F48024", width=1.5),
                yaxis="y3",
                hovertemplate="RSI: %{y:.1f}<extra></extra>",
            ))
            # โซน overbought/oversold
            fig_c.add_hrect(y0=70, y1=100, yref="y3",
                fillcolor="rgba(239,83,80,0.08)", line_width=0)
            fig_c.add_hrect(y0=0, y1=30, yref="y3",
                fillcolor="rgba(38,166,154,0.08)", line_width=0)
            for level, color, label in [(70, "rgba(239,83,80,0.5)", "OB 70"),
                                        (30, "rgba(38,166,154,0.5)", "OS 30")]:
                fig_c.add_hline(y=level, yref="y3",
                    line=dict(color=color, width=1, dash="dot"),
                    annotation_text=label,
                    annotation_font_color=color,
                    annotation_position="left",
                )

        # ── Layout ──
        height = 700 if show_rsi else 580
        fig_c.update_layout(
            title=dict(text=f"{candle_ticker} — Technical Analysis", font=dict(size=16)),
            template="plotly_dark",
            height=height,
            xaxis=dict(rangeslider=dict(visible=False), type="date",
                       domain=[0, 1]),
            yaxis=dict(title="ราคา ($)", domain=candle_domain,
                       showgrid=True, gridcolor="rgba(255,255,255,0.07)"),
            yaxis2=dict(title="Volume", domain=vol_domain, showgrid=False),
            yaxis3=dict(title="RSI", domain=rsi_domain,
                        range=[0, 100], showgrid=True,
                        gridcolor="rgba(255,255,255,0.07)") if show_rsi else {},
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, font=dict(size=11)),
            margin=dict(l=10, r=10, t=60, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
        )

        st.plotly_chart(fig_c, use_container_width=True)

        # ── ตาราง Summary ──
        with st.expander("📋 สรุปตัวชี้วัดทั้งหมด ณ ปัจจุบัน", expanded=False):
            summary_rows = []

            # EMA
            for span, lbl in [(20, "EMA 20"), (50, "EMA 50"), (100, "EMA 100")]:
                if len(cdf) >= span:
                    val  = float(calc_ema(cdf["Close"], span).iloc[-1])
                    diff = (last_close - val) / val * 100
                    summary_rows.append({
                        "ตัวชี้วัด": lbl,
                        "ค่า": f"${val:.2f}",
                        "vs ราคาปัจจุบัน": f"{diff:+.2f}%",
                        "สัญญาณ": "🟢 เหนือ" if last_close > val else "🔴 ใต้",
                        "ความหมาย": "Momentum ขาขึ้น" if last_close > val else "Momentum ขาลง",
                    })

            # Bollinger
            if show_bb:
                bb_u = float(bb_upper.dropna().iloc[-1])
                bb_m = float(bb_mid.dropna().iloc[-1])
                bb_l = float(bb_lower.dropna().iloc[-1])
                bb_pos = (last_close - bb_l) / (bb_u - bb_l) * 100 if (bb_u - bb_l) > 0 else 50
                bb_sig = "🔴 Overbought" if bb_pos > 80 else ("🟢 Oversold" if bb_pos < 20 else "⚪ กลาง")
                summary_rows.append({
                    "ตัวชี้วัด": "BB Position",
                    "ค่า": f"{bb_pos:.1f}%",
                    "vs ราคาปัจจุบัน": f"Upper:${bb_u:.2f} / Lower:${bb_l:.2f}",
                    "สัญญาณ": bb_sig,
                    "ความหมาย": "ตำแหน่งราคาใน BB (0%=Lower, 100%=Upper)",
                })

            # Support / Resistance
            if show_sup:
                dist = (last_close - sup_level) / sup_level * 100
                summary_rows.append({
                    "ตัวชี้วัด": "Support",
                    "ค่า": f"${sup_level:.2f}",
                    "vs ราคาปัจจุบัน": f"+{dist:.2f}% เหนือ",
                    "สัญญาณ": "🔵 แนวรับ",
                    "ความหมาย": "ราคาต่ำสุด 20 แท่ง — โซนซื้อ",
                })
            if show_res:
                dist = (res_level - last_close) / last_close * 100
                summary_rows.append({
                    "ตัวชี้วัด": "Resistance",
                    "ค่า": f"${res_level:.2f}",
                    "vs ราคาปัจจุบัน": f"-{dist:.2f}% ต่ำกว่า",
                    "สัญญาณ": "🩷 แนวต้าน",
                    "ความหมาย": "ราคาสูงสุด 20 แท่ง — โซนขาย",
                })

            # RSI
            if show_rsi:
                rsi_val = float(rsi_series.dropna().iloc[-1])
                rsi_sig = ("🔴 Overbought" if rsi_val > 70
                           else "🟢 Oversold" if rsi_val < 30
                           else "⚪ Neutral")
                summary_rows.append({
                    "ตัวชี้วัด": "RSI (14)",
                    "ค่า": f"{rsi_val:.1f}",
                    "vs ราคาปัจจุบัน": "-",
                    "สัญญาณ": rsi_sig,
                    "ความหมาย": ">70 แพงเกิน | <30 ถูกเกิน | 50=สมดุล",
                })

            # VWAP
            if show_vwap:
                vwap_val = float(vwap_series.dropna().iloc[-1])
                dist = (last_close - vwap_val) / vwap_val * 100
                summary_rows.append({
                    "ตัวชี้วัด": "VWAP",
                    "ค่า": f"${vwap_val:.2f}",
                    "vs ราคาปัจจุบัน": f"{dist:+.2f}%",
                    "สัญญาณ": "🟢 เหนือ VWAP" if last_close > vwap_val else "🔴 ใต้ VWAP",
                    "ความหมาย": "เหนือ=แรงซื้อครอง | ใต้=แรงขายครอง",
                })

            if summary_rows:
                st.dataframe(
                    pd.DataFrame(summary_rows).set_index("ตัวชี้วัด"),
                    use_container_width=True,
                )

    # ------------------------------------------------------------------
    st.markdown("## ข้อมูลดิบ")
    st.dataframe(data)


# ==================================================================
# MAIN TABS
# ==================================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 ราคา Live", "📉 แนวโน้มกลุ่ม", "📊 เมตริก",
    "📰 ข่าว", "⚡ พอร์ตโฟลิโอ", "⚙️ การตั้งค่าและข้อมูล",
])

# ------------------------------------------------------------------
# TAB 1 — ราคา Live
# ------------------------------------------------------------------
with tab1:
    st.subheader("🔍 ค้นหาหุ้น")
    selected_ticker = st.selectbox("เลือกบริษัท", STOCKS)

    time_range = st.selectbox("เลือกช่วงเวลา", list(HORIZON_MAP.keys()), index=1)
    # fetch_stock_details มี cache — ไม่ยิง HTTP ซ้ำ + ดึง longName/sector ในครั้งเดียว
    details, history = fetch_stock_details(selected_ticker, HORIZON_MAP[time_range])
    company_name = details.get("long_name", selected_ticker)
    st.markdown(f"## {company_name} ({selected_ticker})")

    if not history.empty and {"Open", "High", "Low", "Close"}.issubset(history.columns):
        col_chart, col_metrics = st.columns([4, 1])
        with col_chart:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=history.index,
                open=history["Open"], high=history["High"],
                low=history["Low"],   close=history["Close"],
                name="แท่งเทียน",
                increasing_line_color="green", decreasing_line_color="red",
            ))
            fig.add_trace(go.Scatter(
                x=history.index, y=history["Close"],
                mode="lines", name="ราคาปิด",
                line=dict(color="cyan", width=2),
            ))
            fig.update_layout(
                xaxis_title="วันที่", yaxis_title="ราคา",
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_metrics.container(border=True):
            st.metric("💵 ราคา", f"${details['price']}", f"{details['change_pct']:.2f}%")
        with col_metrics.container(border=True):
            st.metric("📊 อัตราส่วน PE", details["pe_ratio"])
        with col_metrics.container(border=True):
            st.metric("📈 กำไรต่อหุ้น (EPS)", details["eps"])
    else:
        st.info("ไม่มีข้อมูลแท่งเทียนสำหรับช่วงเวลานี้")

    row1 = st.columns(3)
    vol = details["volume"]
    with row1[0].container(border=True):
        st.metric("📦 ปริมาณซื้อขาย", f"{vol:,}" if isinstance(vol, (int, float)) else "N/A")
    with row1[1].container(border=True):
        mc = details["market_cap"]
        st.metric("🏦 มูลค่าตลาด", f"${mc:,}" if isinstance(mc, (int, float)) else "N/A")
    with row1[2].container(border=True):
        st.metric("🏷️ กลุ่มธุรกิจ", details.get("sector", "N/A"))

    row2 = st.columns(3)
    with row2[0].container(border=True):
        st.metric("📈 สูงสุด 52 สัปดาห์", f"${details['high_52w']}")
    with row2[1].container(border=True):
        st.metric("📉 ต่ำสุด 52 สัปดาห์", f"${details['low_52w']}")
    with row2[2].container(border=True):
        # BUG FIX #6: dividend_yield — ตรวจ type ก่อน format ไม่ crash
        dy = details["dividend_yield"]
        dy_str = f"{dy:.2%}" if isinstance(dy, (int, float)) else "N/A"
        st.metric("💸 อัตราผลตอบแทนเงินปันผล", dy_str)


# ------------------------------------------------------------------
# TAB 2 — แนวโน้มกลุ่ม
# ------------------------------------------------------------------
with tab2:
    show_peer_analysis()


# ------------------------------------------------------------------
# TAB 3 — เมตริก
# ------------------------------------------------------------------
with tab3:
    st.subheader("📊 เมตริกทางการเงินและมุมมองนักวิเคราะห์")
    metrics_df = fetch_metrics()
    metrics_df["คะแนนนักวิเคราะห์"] = pd.to_numeric(metrics_df["คะแนนนักวิเคราะห์"], errors="coerce")

    fig_pe_eps = px.line(
        metrics_df.sort_values("กำไรต่อหุ้น (EPS)"),
        x="บริษัท", y=["อัตราส่วน PE", "กำไรต่อหุ้น (EPS)"],
        title="อัตราส่วน PE และ EPS แยกตามบริษัท", markers=True,
    )
    st.plotly_chart(fig_pe_eps, use_container_width=True)

    fig_rating = px.bar(
        metrics_df.sort_values("คะแนนนักวิเคราะห์", na_position="last"),
        x="คะแนนนักวิเคราะห์", y="บริษัท", orientation="h",
        color="คะแนนนักวิเคราะห์", color_continuous_scale="RdYlGn_r",
        title="คะแนนคำแนะนำนักวิเคราะห์ (1=ซื้อแรง, 5=ขาย)",
    )
    st.plotly_chart(fig_rating, use_container_width=True)

    st.subheader("🔮 มาตรวัดคะแนนนักวิเคราะห์")
    with st.expander("⚡ ดูคะแนนนักวิเคราะห์", expanded=True):
        for i in range(0, len(metrics_df), 4):
            cols = st.columns(4)
            for j, (_, row) in enumerate(metrics_df.iloc[i : i + 4].iterrows()):
                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"### {row['บริษัท']}")
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=row["คะแนนนักวิเคราะห์"],
                            title={"text": "คะแนนนักวิเคราะห์"},
                            gauge={
                                "axis": {"range": [1, 5]},
                                "steps": [
                                    {"range": [1, 2], "color": "green"},
                                    {"range": [2, 3], "color": "lightgreen"},
                                    {"range": [3, 4], "color": "orange"},
                                    {"range": [4, 5], "color": "red"},
                                ],
                            },
                        ))
                        fig.update_layout(height=250, margin=dict(t=20, b=20, l=10, r=10))
                        # BUG FIX #7: key ใช้ index row แทนชื่อบริษัท → ไม่ crash ถ้าชื่อซ้ำ
                        st.plotly_chart(fig, use_container_width=True, key=f"gauge_{i}_{j}")

    st.dataframe(metrics_df.set_index("บริษัท"))


# ------------------------------------------------------------------
# TAB 4 — ข่าว
# ------------------------------------------------------------------
with tab4:
    st.subheader("📰 ข่าวตลาดหุ้นทั่วไป")
    news_tickers = ["MSFT", "TSLA", "NVDA", "AMZN", "GOOG", "META"]
    all_news = []
    for t in news_tickers:
        all_news.extend(fetch_news(t))

    if all_news:
        for item in all_news[:8]:
            content   = item.get("content") or {}
            title     = content.get("title", "ไม่มีหัวข้อข่าว") or "ไม่มีหัวข้อข่าว"
            summary   = content.get("summary", "") or ""
            pubDate   = content.get("pubDate")
            link      = (content.get("canonicalUrl") or {}).get("url")
            thumbnail = (content.get("thumbnail") or {}).get("originalUrl")
            provider  = (content.get("provider") or {}).get("displayName", "ไม่ทราบแหล่งข้อมูล")

            st.markdown(f"### {title}")
            if thumbnail:
                st.image(thumbnail, width=400)
            if summary:
                st.write(summary)
            cap = f"แหล่งข้อมูล: {provider}"
            if pubDate:
                cap += f" | เผยแพร่: {pubDate}"
            st.caption(cap)
            if link:
                st.markdown(f"[อ่านเพิ่มเติม]({link})")
            st.markdown("---")
    else:
        st.info("ขณะนี้ไม่มีข่าวให้แสดง")


# ------------------------------------------------------------------
# TAB 5 — พอร์ตโฟลิโอ
# BUG FIX #8: เซฟพอร์ตลง session_state + JSON file (persist ข้าม session)
# BUG FIX #9: get_portfolio_df ใช้ get_current_price (cached) ไม่ยิง HTTP ทุก row
# BUG FIX #10: CSV import ใช้ try/except ต่อ row + รองรับ format หลากหลาย
# ------------------------------------------------------------------
PORTFOLIO_FILE = "portfolio_data.json"

def load_portfolio_from_file() -> list:
    try:
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_portfolio_to_file(portfolio: list):
    try:
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(portfolio, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"บันทึกพอร์ตไม่สำเร็จ: {e}")

if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_portfolio_from_file()

with tab5:
    st.subheader("📁 ติดตามพอร์ตโฟลิโอ")
    st.caption("ข้อมูลเซฟอัตโนมัติในไฟล์ JSON — ไม่หายเมื่อ refresh")

    # --- นำเข้า CSV ---
    uploaded_file = st.file_uploader("📥 นำเข้าพอร์ตโฟลิโอ CSV", type=["csv"])
    if uploaded_file:
        try:
            imported_df = pd.read_csv(uploaded_file)
            col_map = {}
            if "หุ้น" in imported_df.columns:
                col_map = {"ticker": "หุ้น", "detail": "รายละเอียด"}
            elif "ASSET" in imported_df.columns:
                col_map = {"ticker": "ASSET", "detail": "DETAIL"}
            else:
                st.error("ไม่พบคอลัมน์ 'หุ้น' หรือ 'ASSET' ใน CSV")

            if col_map:
                new_portfolio, failed = [], []
                for _, r in imported_df.iterrows():
                    try:
                        detail    = str(r[col_map["detail"]])
                        qty       = int(detail.split()[0])
                        buy_price = float(detail.split("@ $")[1].split()[0])
                        new_portfolio.append({
                            "ticker":   str(r[col_map["ticker"]]).strip().upper(),
                            "quantity": qty,
                            "buy_price": buy_price,
                        })
                    except Exception:
                        failed.append(str(r.get(col_map["ticker"], "?")))

                st.session_state.portfolio = new_portfolio
                save_portfolio_to_file(new_portfolio)
                st.success(f"นำเข้าสำเร็จ {len(new_portfolio)} รายการ")
                if failed:
                    st.warning(f"ข้ามแถวที่ parse ไม่ได้: {', '.join(failed)}")
                st.rerun()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

    # --- ฟอร์มเพิ่ม ---
    st.write("➕ เพิ่มสินทรัพย์ใหม่ในพอร์ตโฟลิโอ")
    with st.form("add_asset_form"):
        col1, col2, col3 = st.columns([2, 1, 1])
        ticker_input   = col1.selectbox("ค้นหาหุ้น", STOCKS)
        quantity_input = col2.number_input("จำนวนหุ้น", min_value=1, step=1)
        buy_price_input = col3.number_input("ราคาซื้อ", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("➕ เพิ่มสินทรัพย์")
        if submitted and ticker_input:
            st.session_state.portfolio.append({
                "ticker":    ticker_input,
                "quantity":  quantity_input,
                "buy_price": buy_price_input,
            })
            save_portfolio_to_file(st.session_state.portfolio)

    # --- สร้าง DataFrame พอร์ต (ใช้ cached price) ---
    def get_portfolio_df(portfolio: list) -> pd.DataFrame:
        rows = []
        for asset in portfolio:
            current_price = get_current_price(asset["ticker"]) or 0.0
            qty       = asset["quantity"]
            buy_price = asset["buy_price"]
            invested  = qty * buy_price
            value     = qty * current_price
            gain      = value - invested
            gain_pct  = (gain / invested * 100) if invested else 0.0
            rows.append({
                "หุ้น":         asset["ticker"],
                "ราคา":         current_price,
                "มูลค่า":       value,
                "กำไร/ขาดทุน":  gain,
                "% กำไร/ขาดทุน": gain_pct,
                "รายละเอียด":   f"{qty} หุ้น @ ${buy_price:.2f}",
            })
        return pd.DataFrame(rows)

    df = get_portfolio_df(st.session_state.portfolio)

    total_invested = sum(a["quantity"] * a["buy_price"] for a in st.session_state.portfolio)
    total_value    = df["มูลค่า"].sum() if not df.empty else 0.0
    total_gain     = total_value - total_invested
    gain_pct_total = (total_gain / total_invested * 100) if total_invested else 0.0

    colA, colB, colC = st.columns(3)
    with colA.container(border=True):
        st.metric("💰 มูลค่ารวม", f"${total_value:.2f}")
    with colB.container(border=True):
        st.metric("📈 กำไร/ขาดทุนรวม", f"${total_gain:.2f}", f"{gain_pct_total:.2f}% ทั้งหมด")
    with colC.container(border=True):
        st.metric("🏦 เงินลงทุน", f"${total_invested:.2f}")

    if not df.empty:
        st.markdown("### 📊 แผนภูมิพอร์ตโฟลิโอ")
        pie_data = [{"value": r["มูลค่า"], "name": r["หุ้น"]} for _, r in df.iterrows()]
        options = {
            "title":  {"text": "สัดส่วนพอร์ตโฟลิโอ", "left": "center", "textStyle": {"color": "#fff"}},
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "vertical", "left": "left", "textStyle": {"color": "#fff"}},
            "series": [{
                "name": "สัดส่วน", "type": "pie", "radius": "90%", "data": pie_data,
                "label": {"show": True, "position": "inside", "formatter": "{b}: {d}%",
                          "color": "#fff", "fontWeight": "bold", "fontSize": 12},
                "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0,
                                            "shadowColor": "rgba(0,0,0,0.5)"}},
            }],
        }
        st_echarts(options=options, height="300px")

        fig2 = px.bar(
            df, x="หุ้น", y="กำไร/ขาดทุน",
            color="กำไร/ขาดทุน",
            text=df["% กำไร/ขาดทุน"].apply(lambda x: f"{x:.2f}%"),
            title="กำไร/ขาดทุนแยกตามหุ้น",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### การถือครองของคุณ")
    st.dataframe(
        df.style.format({
            "ราคา": "${:.2f}", "มูลค่า": "${:.2f}",
            "กำไร/ขาดทุน": "${:.2f}", "% กำไร/ขาดทุน": "{:.2f}%",
        }),
        use_container_width=True,
    )

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button("📤 ส่งออกพอร์ตโฟลิโอเป็น CSV", csv_bytes, "portfolio.csv", "text/csv")


# ------------------------------------------------------------------
# TAB 6 — การตั้งค่า
# ------------------------------------------------------------------
with tab6:
    st.subheader("⚙️ การตั้งค่าและข้อมูล")
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 🛠️ กำหนดการอัปเดตและบำรุงรักษา")
            with st.expander("📅 ดูปฏิทิน", expanded=False):
                components.html("""
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
                <style>
                  .flatpickr-calendar{background:#2c2c2c!important;color:#fff!important;border:1px solid #444;font-family:'Segoe UI',sans-serif}
                  .flatpickr-day:hover{background:#666!important;color:#fff!important;border-radius:50%!important}
                  .flatpickr-day{color:#fff!important}
                  .flatpickr-day.saturday{background-color:#ff4b4b!important;color:white!important;border-radius:50%!important}
                  .flatpickr-weekday{color:#ccc!important}
                  .flatpickr-months .flatpickr-month{color:#fff!important}
                  .flatpickr-current-month input.cur-year{color:#ccc!important}
                </style>
                <input id="calendar" type="text" readonly style="visibility:hidden;height:0;">
                <div id="calendar-container"></div>
                <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
                <script>
                  flatpickr("#calendar",{
                    inline:true,clickOpens:false,defaultDate:"2025-12-20",
                    onDayCreate:function(dObj,dStr,fp,dayElem){
                      if(new Date(dayElem.dateObj).getDay()===6) dayElem.classList.add("saturday");
                    },
                    appendTo:document.getElementById("calendar-container")
                  });
                </script>
                """, height=330)
            upcoming = next_saturday().date()
            st.markdown(f"🔔 **การบำรุงรักษาครั้งต่อไป:** {upcoming.strftime('%A, %d %B %Y')}")

    with col2:
        with st.container(border=True):
            st.markdown("### 🚀 การอัปเดตในอนาคต")
            st.write("สำหรับฟีเจอร์ AI ขั้นสูง ใช้ [Stockly.ai](https://stockly-ai.streamlit.app) ของเรา")

    col3, col4 = st.columns(2)
    with col3:
        with st.container(border=True):
            st.markdown("### ⚡ สถานะแอป")
            st.markdown("""
            <div style="height:140px;display:flex;justify-content:center;align-items:center;">
              <a href="https://live-stock.betteruptime.com/" target="_blank">
                <img src="https://uptime.betterstack.com/status-badges/v1/monitor/196o6.svg"
                     alt="ป้ายสถานะ Uptime" style="transform:scale(3);transform-origin:center;">
              </a>
            </div>""", unsafe_allow_html=True)

    with col4:
        with st.container(border=True):
            st.markdown("### 🤝 ร่วมมือกัน")
            st.markdown("""
            สนใจร่วมงานหรือจ้างงาน?
            - 📧 ติดต่อที่: anshkunwar3009@gmail.com
            - 🧠 ดูโปรเจกต์อื่น: [streamlit](https://share.streamlit.io/user/anshk1234)
            - 🌐 GitHub ของฉัน: [github](https://github.com/anshk1234)
            """)


# ------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------
with st.sidebar:
    st.header("📈 ภาพรวมประจำวัน")
    details_sidebar = get_daily_details(SIDEBAR_SYMBOLS)

    if details_sidebar:
        best  = max(details_sidebar, key=lambda x: details_sidebar[x]["change_pct"])
        worst = min(details_sidebar, key=lambda x: details_sidebar[x]["change_pct"])
        with st.container(border=True):
            st.markdown("### หุ้นที่ดีที่สุดวันนี้")
            st.markdown(f"**{best}**")
            st.metric("💵 ราคา",
                      f"${details_sidebar[best]['price']:.2f}",
                      f"{details_sidebar[best]['change_pct']:.2f}%")
        with st.container(border=True):
            st.markdown("### หุ้นที่แย่ที่สุดวันนี้")
            st.markdown(f"**{worst}**")
            st.metric("💵 ราคา",
                      f"${details_sidebar[worst]['price']:.2f}",
                      f"{details_sidebar[worst]['change_pct']:.2f}%")
    else:
        st.info("ไม่มีข้อมูลผลการดำเนินงานวันนี้")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🙌 เครดิต")
st.sidebar.markdown("""
- 👨‍💻 **พัฒนาโดย**: Ansh Kunwar
- 📊 **แหล่งข้อมูล**: [Yahoo Finance](https://finance.yahoo.com)
- ⚙️ **เทคโนโลยีที่ใช้**: Streamlit + Plotly
- 🧠 **ซอร์สโค้ด**: [Github](https://github.com/anshk1234/live-stock-market-prices)
- แอปนี้ใช้สัญญาอนุญาต **Apache License 2.0**
""")
st.sidebar.markdown("<br><center>© 2025 แดชบอร์ดหุ้น Live</center>", unsafe_allow_html=True)

st.markdown("<p style='text-align:center;color:white;'>© 2025 แดชบอร์ดหุ้น Live | ขับเคลื่อนโดย Yahoo Finance</p>",
            unsafe_allow_html=True)
