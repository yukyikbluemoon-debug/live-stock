import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import altair as alt
import time
import json
from streamlit_lottie import st_lottie
from datetime import datetime, timedelta
import io
from streamlit_echarts import st_echarts
import plotly.graph_objects as go
import streamlit.components.v1 as components

# Page config
st.set_page_config(page_title="📈 แดชบอร์ดหุ้น Live", layout="wide")

# --- Splash Animation ---
def load_lottiefile(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

if "show_intro" not in st.session_state:
    st.session_state.show_intro = True

if st.session_state.show_intro:
    lottie_intro = load_lottiefile("Money Investment.json")
    splash = st.empty()
    with splash.container():
        st.markdown("<h1 style='text-align:center;'>ยินดีต้อนรับสู่แดชบอร์ดตลาดหุ้น !</h1>", unsafe_allow_html=True)
        st_lottie(lottie_intro, height=280, speed=1.0, loop=False)
        time.sleep(4)
    splash.empty()
    st.session_state.show_intro = False

# ชื่อแอป
st.header('''📈 แดชบอร์ดหุ้น Live''')

# =============================================================
# helper: แสดง metric พร้อม tooltip อธิบายความหมาย
# =============================================================
def metric_with_help(label: str, value, delta=None, help_text: str = ""):
    if delta is not None:
        st.metric(label=label, value=value, delta=delta, help=help_text)
    else:
        st.metric(label=label, value=value, help=help_text)

# คำอธิบายความหมายของแต่ละ metric
HELP = {
    "ราคา": (
        "💵 ราคาหุ้นปัจจุบัน (USD)\n\n"
        "ราคาล่าสุดที่มีการซื้อขายในตลาด\n"
        "• สีเขียว = ราคาขึ้นจากวันก่อน\n"
        "• สีแดง = ราคาลงจากวันก่อน"
    ),
    "pe_ratio": (
        "📊 อัตราส่วนราคาต่อกำไร (P/E Ratio)\n\n"
        "= ราคาหุ้น ÷ กำไรต่อหุ้น (EPS)\n\n"
        "บอกว่านักลงทุนยอมจ่ายกี่บาทต่อกำไร 1 บาท\n"
        "• P/E ต่ำ → หุ้นอาจถูก (Undervalued)\n"
        "• P/E สูง → คาดหวังการเติบโตสูง\n"
        "• ค่าเฉลี่ย S&P 500 ≈ 20–25"
    ),
    "eps": (
        "📈 กำไรต่อหุ้น (EPS — Earnings Per Share)\n\n"
        "= กำไรสุทธิ ÷ จำนวนหุ้นทั้งหมด\n\n"
        "บอกว่าบริษัทสร้างกำไรได้เท่าไหร่ต่อหุ้น 1 หุ้น\n"
        "• EPS สูงและเพิ่มขึ้นทุกปี = สัญญาณดี\n"
        "• EPS ติดลบ = บริษัทขาดทุน"
    ),
    "volume": (
        "📦 ปริมาณการซื้อขาย (Volume)\n\n"
        "จำนวนหุ้นที่ถูกซื้อ+ขายในวันนี้\n\n"
        "• สูงกว่าปกติ → มีเหตุการณ์สำคัญ / ความสนใจมาก\n"
        "• ต่ำ → ตลาดเงียบ ราคาอาจไม่น่าเชื่อถือนัก"
    ),
    "market_cap": (
        "🏦 มูลค่าตลาดรวม (Market Capitalization)\n\n"
        "= ราคาหุ้น × จำนวนหุ้นทั้งหมด\n\n"
        "บอกขนาดของบริษัท:\n"
        "• > $200B = Large Cap (ยักษ์ใหญ่)\n"
        "• $10B–$200B = Mid Cap\n"
        "• < $10B = Small Cap (เสี่ยงกว่า เติบโตเร็วกว่า)"
    ),
    "sector": (
        "🏷️ กลุ่มธุรกิจ (Sector)\n\n"
        "หมวดธุรกิจหลักของบริษัท เช่น\n"
        "• Technology = เทคโนโลยี\n"
        "• Healthcare = สุขภาพ\n"
        "• Financials = การเงิน-การธนาคาร\n"
        "• Energy = พลังงาน\n"
        "• Consumer Discretionary = สินค้าฟุ่มเฟือย"
    ),
    "high_52w": (
        "📈 ราคาสูงสุดใน 52 สัปดาห์ (52-Week High)\n\n"
        "ราคาสูงสุดที่หุ้นทำได้ใน 1 ปีที่ผ่านมา\n\n"
        "• ราคาปัจจุบันใกล้ 52W High → อยู่ในแนวโน้มขาขึ้น\n"
        "• ใช้เปรียบเทียบว่าราคาตอนนี้อยู่ตรงไหนของปีที่ผ่านมา"
    ),
    "low_52w": (
        "📉 ราคาต่ำสุดใน 52 สัปดาห์ (52-Week Low)\n\n"
        "ราคาต่ำสุดที่หุ้นทำได้ใน 1 ปีที่ผ่านมา\n\n"
        "• ราคาปัจจุบันใกล้ 52W Low → หุ้นอยู่ในแนวโน้มขาลง\n"
        "• บางครั้งถือเป็นโอกาสซื้อ แต่ต้องวิเคราะห์เหตุผลด้วย"
    ),
    "dividend_yield": (
        "💸 อัตราผลตอบแทนเงินปันผล (Dividend Yield)\n\n"
        "= เงินปันผลต่อปี ÷ ราคาหุ้น × 100%\n\n"
        "บอกว่าซื้อหุ้นนี้จะได้เงินปันผลกี่ % ต่อปี\n"
        "• 0% = ไม่จ่ายปันผล (นำกำไรไปลงทุนต่อ)\n"
        "• 2–4% = ปันผลดี มั่นคง\n"
        "• > 6% = ระวัง อาจไม่ยั่งยืน"
    ),
    "analyst_rating": (
        "🔮 คะแนนคำแนะนำนักวิเคราะห์ (Analyst Rating)\n\n"
        "ค่าเฉลี่ยจากนักวิเคราะห์หลายสำนัก:\n"
        "• 1.0 = Strong Buy (ซื้อแรงมาก)\n"
        "• 2.0 = Buy (ซื้อ)\n"
        "• 3.0 = Hold (ถือไว้)\n"
        "• 4.0 = Sell (ขาย)\n"
        "• 5.0 = Strong Sell (ขายด่วน)\n\n"
        "⚠️ ไม่ใช่การันตี ควรใช้ประกอบการตัดสินใจเท่านั้น"
    ),
    "normalized_price": (
        "📐 ราคาปรับมาตรฐาน (Normalized Price)\n\n"
        "ปรับราคาเริ่มต้นของทุกหุ้นให้เท่ากับ 1.0\n"
        "เพื่อเปรียบเทียบ % การเติบโตได้ยุติธรรม\n\n"
        "• 1.5 = ราคาขึ้น +50% จากจุดเริ่ม\n"
        "• 0.8 = ราคาลง -20% จากจุดเริ่ม"
    ),
    "portfolio_value": (
        "💰 มูลค่ารวมพอร์ตโฟลิโอ\n\n"
        "= Σ (ราคาปัจจุบัน × จำนวนหุ้น) ทุกตัว\n\n"
        "คือเงินทั้งหมดที่จะได้หากขายหุ้นทุกตัววันนี้"
    ),
    "portfolio_gain": (
        "📈 กำไร/ขาดทุนรวม (Total P&L)\n\n"
        "= มูลค่าปัจจุบัน − ต้นทุนรวม\n\n"
        "• สีเขียว = กำไร  |  สีแดง = ขาดทุน\n"
        "% แสดงผลตอบแทนรวมตั้งแต่วันที่ซื้อ"
    ),
    "invested_capital": (
        "🏦 เงินลงทุนทั้งหมด (Invested Capital)\n\n"
        "= Σ (ราคาที่ซื้อ × จำนวนหุ้น) ทุกตัว\n\n"
        "ต้นทุนรวมที่ใช้ซื้อหุ้นทั้งหมดในพอร์ต"
    ),
    "candlestick": (
        "🕯️ กราฟแท่งเทียน (Candlestick Chart)\n\n"
        "แต่ละแท่ง = ข้อมูลราคาใน 1 วัน:\n"
        "• เส้นบน = ราคาสูงสุด (High)\n"
        "• เส้นล่าง = ราคาต่ำสุด (Low)\n"
        "• กล่องสีเขียว = ราคาปิด > เปิด (ราคาขึ้น)\n"
        "• กล่องสีแดง = ราคาปิด < เปิด (ราคาลง)"
    ),
    "etf": (
        "📦 กองทุน ETF (Exchange-Traded Fund)\n\n"
        "กองทุนที่ซื้อขายในตลาดเหมือนหุ้น\n"
        "ลงทุนในหุ้นหลายตัวพร้อมกันในคราวเดียว\n\n"
        "• SPY / VOO = ติดตาม S&P 500 (หุ้นใหญ่ 500 ตัว)\n"
        "• QQQ = ติดตาม Nasdaq (เทคโนโลยี)\n"
        "• GLD = ติดตามราคาทองคำ\n"
        "• ความเสี่ยงต่ำกว่าหุ้นรายตัว เพราะกระจายการลงทุน"
    ),
    "peer_avg": (
        "📊 ค่าเฉลี่ยกลุ่ม (Peer Average)\n\n"
        "ค่าเฉลี่ยของหุ้นอื่นๆ ที่เลือกเปรียบเทียบ\n\n"
        "• เส้นสีแดง = หุ้นที่กำลังดู\n"
        "• เส้นสีเทา = ค่าเฉลี่ยของหุ้นที่เหลือ\n"
        "ใช้ดูว่าหุ้นนี้ทำได้ดีกว่าหรือแย่กว่ากลุ่ม"
    ),
}

# ดึงข้อมูลแบบ Live
@st.cache_data(ttl=3600)  # แคช 1 ชั่วโมง
def fetch_stock_details(ticker, period="1mo"):
    stock = yf.Ticker(ticker)
    info = stock.info
    details = {
        "price": info.get("regularMarketPrice", "N/A"),
        "change_pct": info.get("regularMarketChangePercent", 0),
        "market_cap": info.get("marketCap", "N/A"),
        "pe_ratio": info.get("trailingPE", "N/A"),
        "eps": info.get("trailingEps", "N/A"),
        "high_52w": info.get("fiftyTwoWeekHigh", "N/A"),
        "low_52w": info.get("fiftyTwoWeekLow", "N/A"),
        "volume": info.get("volume", "N/A"),
        "dividend_yield": info.get("dividendYield", "N/A"),
    }
    history = stock.history(period=period, interval="1d")[["Open", "High", "Low", "Close"]]
    return details, history

# กำหนดสัญลักษณ์หุ้นสำหรับแท็บเมตริก
symbols = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Google": "GOOG",
    "Meta": "META"
}

@st.cache_data(ttl=36000)  # แคช 10 ชั่วโมง
def fetch_metrics():
    metrics = []
    for name, symbol in symbols.items():
        try:
            info = yf.Ticker(symbol).info
            metrics.append({
                "บริษัท": name,
                "อัตราส่วน PE": info.get("trailingPE", "N/A"),
                "กำไรต่อหุ้น (EPS)": info.get("trailingEps", "N/A"),
                "คะแนนนักวิเคราะห์": info.get("recommendationMean", "N/A")  # 1=ซื้อแรง, 5=ขาย
            })
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล {name}: {e}")
    return pd.DataFrame(metrics)

# ดึงข่าว
@st.cache_data(ttl=21600)  # แคช 6 ชั่วโมง
def fetch_news(ticker):
    try:
        stock = yf.Ticker(ticker)
        return stock.news
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข่าว: {e}")
        return []

# แผงเปรียบเทียบหุ้นเพื่อน
def show_peer_analysis():
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

    horizon_map = {
        "1 เดือน": "1mo",
        "3 เดือน": "3mo",
        "6 เดือน": "6mo",
        "1 ปี": "1y",
        "5 ปี": "5y",
        "10 ปี": "10y",
        "20 ปี": "20y",
    }

    DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN", "TSLA", "META"]

    tickers = st.multiselect("เลือกหุ้นที่ต้องการเปรียบเทียบ", STOCKS, default=DEFAULT_TICKERS)
    horizon = st.selectbox("เลือกช่วงเวลา", list(horizon_map.keys()), index=2)

    if not tickers:
        st.info("กรุณาเลือกหุ้นเพื่อเปรียบเทียบ")
        st.stop()

    @st.cache_data(ttl=21600)  # แคช 6 ชั่วโมง
    def load_data(tickers, period):
        frames = []
        for ticker in tickers:
            try:
                df = yf.Ticker(ticker).history(period=period)[["Close"]]
                if not df.empty:
                    df.columns = [ticker]
                    frames.append(df)
            except:
                continue
        if frames:
            return pd.concat(frames, axis=1)
        else:
            return pd.DataFrame()

    data = load_data(tickers, horizon_map[horizon])

    if data.empty or data.isna().all().all():
        st.error("ไม่มีข้อมูลราคาที่ถูกต้องสำหรับการทำให้เป็นมาตรฐาน")
        st.stop()

    clean_data = data.dropna(axis=0, how="any")

    if clean_data.empty or clean_data.shape[0] < 2:
        st.error("ข้อมูลที่สะอาดไม่เพียงพอสำหรับการทำให้เป็นมาตรฐาน")
        st.stop()

    normalized = clean_data.div(clean_data.iloc[0])
    normalized.index.name = "วันที่"

    # --- กราฟเปรียบเทียบหุ้นเพื่อน ---
    st.altair_chart(
        alt.Chart(
            normalized.reset_index().melt(
                id_vars=["วันที่"], var_name="หุ้น", value_name="ราคาปรับมาตรฐาน"
            )
        )
        .mark_line()
        .encode(
            alt.X("วันที่:T"),
            alt.Y("ราคาปรับมาตรฐาน:Q").scale(zero=False),
            alt.Color("หุ้น:N"),
        )
        .properties(height=400),
        width="stretch"
    )

    # --- การ์ดราคาในส่วนที่ขยายได้ ---
    with st.expander("💵 ราคาปัจจุบันของบริษัทที่เลือก", expanded=True):
        for i in range(0, len(tickers), 4):
            row = st.columns(min(4, len(tickers) - i))
            for j, ticker in enumerate(tickers[i:i+4]):
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    price = info.get("currentPrice", "N/A")
                    change_pct = info.get("regularMarketChangePercent", 0.0)

                    hist = stock.history(period="1mo")["Close"]
                    sparkline_data = pd.DataFrame({"วันที่": hist.index, "ราคา": hist.values})

                    color = "green" if hist.iloc[-1] > hist.iloc[0] else "red"

                    with row[j].container(border=True):
                        st.metric(label=ticker, value=f"${price}", delta=f"{change_pct:.2f}%")

                        sparkline = (
                            alt.Chart(sparkline_data)
                            .mark_line(color=color)
                            .encode(
                                x=alt.X("วันที่:T", axis=None),
                                y=alt.Y("ราคา:Q", scale=alt.Scale(domain=[hist.min(), hist.max()]), axis=None)
                            )
                            .properties(height=100)
                        )
                        st.altair_chart(sparkline, width="stretch")
                except:
                    with row[j].container(border=True):
                        st.metric(label=ticker, value="N/A", delta="N/A")

    # --- กราฟเปรียบเทียบค่าเฉลี่ยเพื่อน ---
    if len(tickers) > 1:
        st.markdown("### รายบริษัท vs ค่าเฉลี่ยกลุ่ม")
        cols = st.columns(4)

        for i, ticker in enumerate(tickers):
            peers = normalized.drop(columns=[ticker])
            peer_avg = peers.mean(axis=1)

            plot_data = pd.DataFrame({
                "วันที่": normalized.index,
                ticker: normalized[ticker],
                "ค่าเฉลี่ยกลุ่ม": peer_avg,
            }).melt(id_vars=["วันที่"], var_name="ชุดข้อมูล", value_name="ราคา")

            chart = alt.Chart(plot_data).mark_line().encode(
                alt.X("วันที่:T"),
                alt.Y("ราคา:Q").scale(zero=False),
                alt.Color("ชุดข้อมูล:N", scale=alt.Scale(domain=[ticker, "ค่าเฉลี่ยกลุ่ม"], range=["red", "gray"])),
                alt.Tooltip(["วันที่", "ชุดข้อมูล", "ราคา"]),
            ).properties(title=f"{ticker} vs ค่าเฉลี่ยกลุ่ม", height=300)

            cell = cols[(i * 2) % 4].container(border=True)
            cell.altair_chart(chart, width="stretch")

            delta_data = pd.DataFrame({
                "วันที่": normalized.index,
                "ส่วนต่าง": normalized[ticker] - peer_avg,
            })

            chart = alt.Chart(delta_data).mark_area().encode(
                alt.X("วันที่:T"),
                alt.Y("ส่วนต่าง:Q").scale(zero=False),
            ).properties(title=f"{ticker} ลบค่าเฉลี่ยกลุ่ม", height=300)

            cell = cols[(i * 2 + 1) % 4].container(border=True)
            cell.altair_chart(chart, width="stretch")

    # แสดงข้อมูลดิบ
    st.markdown("## ข้อมูลดิบ")
    st.dataframe(data)


def next_saturday(start_date=None):
    if start_date is None:
        start_date = datetime.today()
    days_ahead = 5 - start_date.weekday()  # วันเสาร์ = 5
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


# เลย์เอาต์แท็บ
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 ราคา Live",
    "📉 แนวโน้มกลุ่ม",
    "📊 เมตริก",
    "📰 ข่าว",
    "⚡ พอร์ตโฟลิโอ",
    "⚙️ การตั้งค่าและข้อมูล"
])

with tab1:
    st.subheader("🔍 ค้นหาหุ้น")

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

    selected_ticker = st.selectbox("เลือกบริษัท", STOCKS)

    stock = yf.Ticker(selected_ticker)
    company_name = stock.info.get("longName", selected_ticker)
    st.markdown(f"## {company_name} ({selected_ticker})")

    horizon_map = {
        "1 เดือน": "1mo",
        "3 เดือน": "3mo",
        "6 เดือน": "6mo",
        "1 ปี": "1y",
        "5 ปี": "5y",
        "10 ปี": "10y",
        "20 ปี": "20y",
    }

    time_range = st.selectbox(
        "เลือกช่วงเวลา",
        list(horizon_map.keys()),
        index=1  # ค่าเริ่มต้น "3 เดือน"
    )

    # --- กราฟแนวโน้ม ---
    details, history = fetch_stock_details(selected_ticker, horizon_map[time_range])

    if not history.empty and {"Open", "High", "Low", "Close"}.issubset(history.columns):
        col_chart, col_metrics = st.columns([4, 1])

        with col_chart:
            fig = go.Figure()

            # แผนภูมิแท่งเทียน
            fig.add_trace(go.Candlestick(
                x=history.index,
                open=history["Open"],
                high=history["High"],
                low=history["Low"],
                close=history["Close"],
                name="แท่งเทียน",
                increasing_line_color='green',
                decreasing_line_color='red'
            ))

            # เส้นกราฟราคาปิด
            fig.add_trace(go.Scatter(
                x=history.index,
                y=history["Close"],
                mode="lines",
                name="ราคาปิด",
                line=dict(color="cyan", width=2)
            ))

            fig.update_layout(
                xaxis_title="วันที่",
                yaxis_title="ราคา",
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, width="stretch")

        with col_metrics.container(border=True):
            st.metric("💵 ราคา", f"${details['price']}", f"{details['change_pct']:.2f}%")
        with col_metrics.container(border=True):
            st.metric("📊 อัตราส่วน PE", details['pe_ratio'])
        with col_metrics.container(border=True):
            st.metric("📈 กำไรต่อหุ้น (EPS)", details['eps'])
    else:
        st.info("ไม่มีข้อมูลแท่งเทียนสำหรับช่วงเวลานี้")

    # --- การ์ดข้อมูลอื่นๆ ---
    row1 = st.columns(3)
    with row1[0].container(border=True):
        st.metric("📦 ปริมาณซื้อขาย", f"{details['volume']:,}")
    with row1[1].container(border=True):
        st.metric("🏦 มูลค่าตลาด", f"${details['market_cap']:,}" if details['market_cap'] != "N/A" else "N/A")
    with row1[2].container(border=True):
        st.metric("🏷️ กลุ่มธุรกิจ", stock.info.get("sector", "N/A"))

    row2 = st.columns(3)
    with row2[0].container(border=True):
        st.metric("📉 สูงสุด 52 สัปดาห์", f"${details['high_52w']}")
    with row2[1].container(border=True):
        st.metric("📉 ต่ำสุด 52 สัปดาห์", f"${details['low_52w']}")
    with row2[2].container(border=True):
        st.metric("💸 อัตราผลตอบแทนเงินปันผล", f"{details['dividend_yield']:.2%}" if details['dividend_yield'] != "N/A" else "N/A")


with tab2:
    show_peer_analysis()


with tab3:
    st.subheader("📊 เมตริกทางการเงินและมุมมองนักวิเคราะห์")

    metrics_df = fetch_metrics()
    metrics_df["คะแนนนักวิเคราะห์"] = pd.to_numeric(metrics_df["คะแนนนักวิเคราะห์"], errors="coerce")

    # กราฟเส้น: อัตราส่วน PE และ EPS
    fig_pe_eps = px.line(
        metrics_df.sort_values("กำไรต่อหุ้น (EPS)"),
        x="บริษัท", y=["อัตราส่วน PE", "กำไรต่อหุ้น (EPS)"],
        title="อัตราส่วน PE และ EPS แยกตามบริษัท", markers=True
    )
    st.plotly_chart(fig_pe_eps, width="stretch")

    # กราฟแท่ง: คะแนนนักวิเคราะห์
    fig_rating = px.bar(
        metrics_df.sort_values("คะแนนนักวิเคราะห์", na_position="last"),
        x="คะแนนนักวิเคราะห์", y="บริษัท",
        orientation="h",
        color="คะแนนนักวิเคราะห์",
        color_continuous_scale="RdYlGn_r",
        title="คะแนนคำแนะนำนักวิเคราะห์ (1=ซื้อแรง, 5=ขาย)"
    )
    st.plotly_chart(fig_rating, width="stretch")

    # มาตรวัดคะแนนนักวิเคราะห์
    st.subheader("🔮 มาตรวัดคะแนนนักวิเคราะห์")

    with st.expander("⚡ ดูคะแนนนักวิเคราะห์", expanded=True):
        for i in range(0, len(metrics_df), 4):
            cols = st.columns(4)
            for j, (_, row) in enumerate(metrics_df.iloc[i:i+4].iterrows()):
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
                                    {"range": [4, 5], "color": "red"}
                                ]
                            }
                        ))
                        fig.update_layout(height=250, margin=dict(t=20, b=20, l=10, r=10))
                        st.plotly_chart(fig, width="stretch", key=f"rating_{i}_{j}_{row['บริษัท']}")

    # ตารางข้อมูลทั้งหมด
    st.dataframe(metrics_df.set_index("บริษัท"))


with tab4:
    st.subheader("📰 ข่าวตลาดหุ้นทั่วไป")

    tickers = ["MSFT", "TSLA", "NVDA", "AMZN", "GOOG", "META"]
    all_news = []
    for ticker in tickers:
        items = fetch_news(ticker)
        if items:
            all_news.extend(items)

    if all_news:
        for item in all_news[:8]:
            content = item.get("content") or {}
            title = content.get("title", "ไม่มีหัวข้อข่าว") or "ไม่มีหัวข้อข่าว"
            summary = content.get("summary", "") or ""
            pubDate = content.get("pubDate", None)
            link = (content.get("canonicalUrl") or {}).get("url", None)
            thumbnail = (content.get("thumbnail") or {}).get("originalUrl", None)
            provider = (content.get("provider") or {}).get("displayName", "ไม่ทราบแหล่งข้อมูล")

            st.markdown(f"### {title}")

            if thumbnail:
                st.image(thumbnail, width=400)

            if summary:
                st.write(summary)

            if pubDate:
                st.caption(f"แหล่งข้อมูล: {provider} | เผยแพร่: {pubDate}")
            else:
                st.caption(f"แหล่งข้อมูล: {provider}")

            if link:
                st.markdown(f"[อ่านเพิ่มเติม]({link})")

            st.markdown("---")
    else:
        st.info("ขณะนี้ไม่มีข่าวให้แสดง")

@st.cache_data(ttl=300)
def get_current_price(ticker):
    """ดึงราคาปัจจุบันพร้อมแคชและจัดการข้อผิดพลาด"""
    try:
        df = yf.Ticker(ticker).history(period="1d", timeout=10)
        if not df.empty and "Close" in df.columns:
            return float(df["Close"].iloc[-1])
        return None
    except Exception:
        return None
with tab5:
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = []

    st.subheader("📁 ติดตามพอร์ตโฟลิโอ")
    st.caption("ติดตามการลงทุนและผลการดำเนินงานของคุณแบบเรียลไทม์")

    # อัปโหลดพอร์ตจาก CSV
    uploaded_file = st.file_uploader("📥 นำเข้าพอร์ตโฟลิโอ CSV", type=["csv"])
    if uploaded_file:
        try:
            imported_df = pd.read_csv(uploaded_file)
            # รองรับทั้ง CSV ภาษาไทย (export จากแอปนี้) และ CSV ภาษาอังกฤษ (เวอร์ชันเก่า)
            if "หุ้น" in imported_df.columns:
                ticker_col, detail_col = "หุ้น", "รายละเอียด"
            else:
                ticker_col, detail_col = "ASSET", "DETAIL"

            portfolio = []
            for _, row in imported_df.iterrows():
                try:
                    detail = str(row[detail_col])
                    qty = int(detail.split()[0])
                    buy_price = float(detail.split("@ $")[1])
                    portfolio.append({
                        "ticker": row[ticker_col],
                        "quantity": qty,
                        "buy_price": buy_price
                    })
                except Exception:
                    st.warning(f"ข้ามแถว {row[ticker_col]} — รูปแบบไม่ถูกต้อง")
            st.session_state.portfolio = portfolio
            st.success(f"นำเข้าพอร์ตโฟลิโอสำเร็จ! ({len(portfolio)} รายการ)")
            st.rerun()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

    # ฟอร์มเพิ่มสินทรัพย์ใหม่
    st.write("➕ เพิ่มสินทรัพย์ใหม่ในพอร์ตโฟลิโอ")

    tickers = [
                # === หุ้นขนาดใหญ่ (Large Cap) ===
        "AAPL", "ABBV", "ACN", "ADBE", "ADP", "AMD", "AMGN", "AMT", "AMZN", "APD",
        "AVGO", "AXP", "BA", "BK", "BKNG", "BMY", "BRK.B", "BSX", "C", "CAT", "CI",
        "CL", "CMCSA", "COST", "CRM", "CSCO", "CVX", "DE", "DHR", "DIS", "DUK",
        "ELV", "EOG", "EQR", "FDX", "GD", "GE", "GILD", "GOOG", "GOOGL", "HD",
        "HON", "HUM", "IBM", "ICE", "INTC", "ISRG", "JNJ", "JPM", "KO", "LIN",
        "LLY", "LMT", "LOW", "MA", "MCD", "MDLZ", "META", "MMC", "MO", "MRK",
        "MSFT", "NEE", "NFLX", "NKE", "NOW", "NVDA", "ORCL", "PEP", "PFE", "PG",
        "PLD", "PM", "PSA", "REGN", "RTX", "SBUX", "SCHW", "SLB", "SO", "SPGI",
        "T", "TJX", "TMO", "TSLA", "TXN", "UNH", "UNP", "UPS", "V", "VZ", "WFC",
        "WM", "WMT", "XOM",
        # === หุ้นเพิ่มเติม ===
        "ABNB", "AMAT", "APP", "AXON", "BDX", "BIIB", "BLK", "CEG", "CF", "CHTR",
        "COF", "COP", "CTAS", "DECK", "DG", "DHI", "DLTR", "DOV", "EA", "ECL",
        "ETN", "EW", "FAST", "FCX", "FICO", "FTNT", "GIS", "GPC", "GPN", "GRMN",
        "GS", "HAL", "HCA", "HES", "HIG", "HLT", "HPE", "HPQ", "HSY", "IQV",
        "IR", "IT", "ITW", "JCI", "KEY", "KEYS", "KHC", "KLAC", "KMB", "KMI",
        "KR", "LRCX", "LUV", "LVS", "LYB", "MAR", "MCO", "MELI", "MGM", "MPC",
        "MPWR", "MRO", "MS", "MU", "NEM", "NET", "NSC", "NTAP", "NUE", "O",
        "OKE", "ON", "PAYX", "PCAR", "PCG", "PH", "PKG", "PPG", "PRU", "PWR",
        "PYPL", "QCOM", "RCL", "RF", "RJF", "RL", "RMD", "ROK", "ROP", "ROST",
        "RSG", "SHW", "SNPS", "SPG", "SPOT", "SRE", "STT", "STX", "STZ", "SWK",
        "SYK", "SYY", "TMUS", "TROW", "TRV", "TSCO", "TTWO", "UAL", "URI", "USB",
        "VICI", "VLO", "VMC", "VRSK", "VRTX", "VST", "WAB", "WAT", "WBA", "WEC",
        "WELL", "WDC", "WYNN", "XEL", "YUM", "ZBH", "ZBRA", "ZTS",
        # === ETF - ดัชนีรวม ===
        "SPY", "VOO", "IVV", "VTI", "QQQ", "IWM", "DIA", "MDY", "IJH", "IJR",
        "VT", "ITOT", "SCHB", "SPTM",
        # === ETF - กลุ่มเทคโนโลยี ===
        "XLK", "VGT", "FTEC", "IGV", "SOXX", "SMH", "CIBR", "SKYY", "CLOU",
        "ARKK", "ARKQ", "ARKG", "ARKW", "ARKF", "ROBO", "BOTZ", "AIQ",
        # === ETF - พลังงาน / โภคภัณฑ์ ===
        "XLE", "VDE", "IYE", "OIH", "XOP", "GLD", "IAU", "SLV", "GDX", "GDXJ",
        "USO", "UNG", "DBC", "PDBC",
        # === ETF - การเงิน / อสังหาริมทรัพย์ ===
        "XLF", "VFH", "KBE", "KRE", "VNQ", "IYR", "SCHH",
        # === ETF - สุขภาพ ===
        "XLV", "VHT", "IYH", "IBB", "XBI",
        # === ETF - สินค้า / อุตสาหกรรม ===
        "XLP", "VDC", "XLI", "VIS", "XLB", "VAW",
        # === ETF - พันธบัตร ===
        "AGG", "BND", "TLT", "IEF", "SHY", "LQD", "HYG", "JNK", "TIP", "VTIP",
        "GOVT", "MUB", "BSV", "BIV", "BLV", "VCSH", "VCIT",
        # === ETF - ต่างประเทศ ===
        "VEA", "VWO", "EFA", "EEM", "IDEV", "IEMG", "EWJ", "EWZ", "EWU", "EWG",
        "EWC", "KWEB", "MCHI", "FXI", "INDA", "EWY", "EWT", "VGK", "VXUS",
        # === ETF - เงินปันผล ===
        "SCHD", "VYM", "DVY", "HDV", "SPHD", "DGRO", "VIG", "SDY", "NOBL",
        # === ETF - เลเวอเรจ ===
        "TQQQ", "SQQQ", "UPRO", "SPXU", "UVXY", "VXX", "SOXL", "SOXS",
        # === Bitcoin / Crypto ETF ===
        "IBIT", "FBTC", "BITB", "ARKB", "GBTC", "ETHA",
    ]

    with st.form("add_asset_form"):
        col1, col2, col3 = st.columns([2, 1, 1])
        ticker_input = col1.selectbox("ค้นหาหุ้น", tickers)
        quantity_input = col2.number_input("จำนวนหุ้น", min_value=1, step=1)
        buy_price_input = col3.number_input("ราคาซื้อ", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("➕ เพิ่มสินทรัพย์")

        if submitted and ticker_input:
            st.session_state.portfolio.append({
                "ticker": ticker_input,
                "quantity": quantity_input,
                "buy_price": buy_price_input
            })

    # --- ตารางพอร์ตโฟลิโอ ---
    def get_portfolio_df(portfolio):
        rows = []
        for asset in portfolio:
            ticker = yf.Ticker(asset["ticker"])
            try:
                current_price = ticker.history(period="1d")["Close"].iloc[-1]
            except:
                current_price = 0.0

            quantity = asset["quantity"]
            buy_price = asset["buy_price"]
            invested = quantity * buy_price
            value = quantity * current_price
            gain = value - invested
            gain_pct = (gain / invested) * 100 if invested else 0

            rows.append({
                "หุ้น": asset["ticker"],
                "ราคา": current_price,
                "มูลค่า": value,
                "กำไร/ขาดทุน": gain,
                "% กำไร/ขาดทุน": gain_pct,
                "รายละเอียด": f"{quantity} หุ้น @ ${buy_price:.2f}"
            })
        return pd.DataFrame(rows)

    df = get_portfolio_df(st.session_state.portfolio)

    # --- การ์ดสรุป ---
    total_invested = sum(asset["quantity"] * asset["buy_price"] for asset in st.session_state.portfolio)
    total_value = df["มูลค่า"].sum() if not df.empty else 0
    total_gain = total_value - total_invested
    gain_pct = (total_gain / total_invested) * 100 if total_invested else 0

    colA, colB, colC = st.columns(3)
    with colA.container(border=True):
        st.metric("💰 มูลค่ารวม", f"${total_value:.2f}")
    with colB.container(border=True):
        st.metric("📈 กำไร/ขาดทุนรวม", f"${total_gain:.2f}", f"{gain_pct:.2f}% ทั้งหมด")
    with colC.container(border=True):
        st.metric("🏦 เงินลงทุน", f"${total_invested:.2f}")

    # --- แผนภูมิ ---
    if not df.empty:
        st.markdown("### 📊 แผนภูมิพอร์ตโฟลิโอ")

        pie_data = [
            {"value": row["มูลค่า"], "name": row["หุ้น"]}
            for _, row in df.iterrows()
        ]

        options = {
            "title": {
                "text": "สัดส่วนพอร์ตโฟลิโอ",
                "left": "center",
                "textStyle": {"color": "#fff"},
            },
            "tooltip": {"trigger": "item"},
            "legend": {
                "orient": "vertical",
                "left": "left",
                "textStyle": {"color": "#fff"}
            },
            "series": [
                {
                    "name": "สัดส่วน",
                    "type": "pie",
                    "radius": "90%",
                    "data": pie_data,
                    "label": {
                        "show": True,
                        "position": "inside",
                        "formatter": "{b}: {d}%",
                        "color": "#fff",
                        "fontWeight": "bold",
                        "fontSize": 12
                    },
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": "rgba(0, 0, 0, 0.5)"
                        }
                    }
                }
            ]
        }

        st_echarts(options=options, height="300px")

        if not df.empty and "% กำไร/ขาดทุน" in df.columns:
            fig2 = px.bar(
                df,
                x="หุ้น",
                y="กำไร/ขาดทุน",
                color="กำไร/ขาดทุน",
                text=df["% กำไร/ขาดทุน"].apply(lambda x: f"{x:.2f}%"),
                title="กำไร/ขาดทุนแยกตามหุ้น"
            )
            st.plotly_chart(fig2, width="stretch")
        else:
            st.info("ไม่มีข้อมูลพอร์ตโฟลิโอสำหรับแสดงกราฟผลตอบแทน")

    # --- ตารางการถือครอง ---
    st.markdown("### การถือครองของคุณ")
    st.dataframe(df.style.format({
        "ราคา": "${:.2f}",
        "มูลค่า": "${:.2f}",
        "กำไร/ขาดทุน": "${:.2f}",
        "% กำไร/ขาดทุน": "{:.2f}%"
    }), width="stretch")

    # ดาวน์โหลดพอร์ตเป็น CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📤 ส่งออกพอร์ตโฟลิโอเป็น CSV",
        data=csv,
        file_name="portfolio.csv",
        mime="text/csv"
    )


with tab6:
    st.subheader("⚙️ การตั้งค่าและข้อมูล")

    col1, col2 = st.columns(2)

    # --- การ์ดตารางการบำรุงรักษา ---
    with col1:
        with st.container(border=True):
            st.markdown("### 🛠️ กำหนดการอัปเดตและบำรุงรักษา")
            with st.expander("📅 ดูปฏิทิน", expanded=False):
                components.html("""
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
                <style>
                  .flatpickr-calendar { background: #2c2c2c !important; color: #fff !important; border: 1px solid #444; font-family: 'Segoe UI', sans-serif; }
                  .flatpickr-day:hover { background: #666 !important; color: #fff !important; border-radius: 50% !important; }
                  .flatpickr-day { color: #fff !important; }
                  .flatpickr-day.saturday { background-color: #ff4b4b !important; color: white !important; border-radius: 50% !important; }
                  .flatpickr-weekday { color: #ccc !important; }
                  .flatpickr-months .flatpickr-month { color: #fff !important; }
                  .flatpickr-current-month input.cur-year { color: #ccc !important; }
                </style>
                <input id="calendar" type="text" readonly style="visibility:hidden; height:0;">
                <div id="calendar-container"></div>
                <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
                <script>
                  flatpickr("#calendar", {
                    inline: true, clickOpens: false, defaultDate: "2025-12-20",
                    onDayCreate: function(dObj, dStr, fp, dayElem) {
                      const date = new Date(dayElem.dateObj);
                      if (date.getDay() === 6) { dayElem.classList.add("saturday"); }
                    },
                    appendTo: document.getElementById("calendar-container")
                  });
                </script>
                """, height=330)

            upcoming = next_saturday().date()
            st.markdown(f"🔔 **การบำรุงรักษาครั้งต่อไป:** {upcoming.strftime('%A, %d %B %Y')}")

    # --- การ์ดการอัปเดตในอนาคต ---
    with col2:
        with st.container(border=True):
            st.markdown("### 🚀 การอัปเดตในอนาคต")
            st.write("""
            - สำหรับฟีเจอร์ AI ขั้นสูง ใช้ [Stockly.ai](https://stockly-ai.streamlit.app) ของเรา
            """)

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.markdown("### ⚡ สถานะแอป")
            st.markdown("""
            <div style="height:140px; display:flex; justify-content:center; align-items:center;">
              <a href="https://live-stock.betteruptime.com/" target="_blank">
                <img src="https://uptime.betterstack.com/status-badges/v1/monitor/196o6.svg"
                  alt="ป้ายสถานะ Uptime"
                  style="transform: scale(3); transform-origin: center;">
              </a>
            </div>
            """, unsafe_allow_html=True)

    with col4:
        with st.container(border=True):
            st.markdown("### 🤝 ร่วมมือกัน")
            st.markdown("""
            สนใจร่วมงานหรือจ้างงาน?

            - 📧 ติดต่อที่: anshkunwar3009@gmail.com
            - 🧠 ดูโปรเจกต์อื่น: [streamlit](https://share.streamlit.io/user/anshk1234)
            - 🌐 GitHub ของฉัน: [github](https://github.com/anshk1234)
            """)


# แถบด้านข้าง
symbols = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Google": "GOOG",
    "Meta": "META"
}

@st.cache_data(ttl=3600)  # แคช 1 ชั่วโมง
def get_daily_details(symbols):
    details = {}
    for name, ticker in symbols.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                open_price = hist["Open"].iloc[0]
                close_price = hist["Close"].iloc[0]
                change_pct = ((close_price - open_price) / open_price) * 100
                details[name] = {
                    "price": close_price,
                    "change_pct": change_pct
                }
        except Exception as e:
            st.warning(f"เกิดข้อผิดพลาดในการดึงข้อมูล {name}: {e}")
    return details

with st.sidebar:
    st.header("📈 ภาพรวมประจำวัน")
    details = get_daily_details(symbols)

    if details:
        best_stock = max(details, key=lambda x: details[x]["change_pct"])
        worst_stock = min(details, key=lambda x: details[x]["change_pct"])

        with st.container(border=True):
            st.markdown("### หุ้นที่ดีที่สุดวันนี้")
            st.markdown(f"**{best_stock}**")
            st.metric("💵 ราคา", f"${details[best_stock]['price']:.2f}", f"{details[best_stock]['change_pct']:.2f}%")

        with st.container(border=True):
            st.markdown("### หุ้นที่แย่ที่สุดวันนี้")
            st.markdown(f"**{worst_stock}**")
            st.metric("💵 ราคา", f"${details[worst_stock]['price']:.2f}", f"{details[worst_stock]['change_pct']:.2f}%")
    else:
        st.info("ไม่มีข้อมูลผลการดำเนินงานวันนี้")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🙌 เครดิต")
st.sidebar.markdown("""
- 👨‍💻 **พัฒนาโดย**: Ansh Kunwar
- 📊 **แหล่งข้อมูล**: [Yahoo Finance](https://finance.yahoo.com)
- 🖼️ **โลโก้**: Wikimedia Commons
- ⚙️ **เทคโนโลยีที่ใช้**: Streamlit + Plotly
- 🧠 **ซอร์สโค้ด**: [Github](https://github.com/anshk1234/live-stock-market-prices)
- 🌐 **ดูโปรเจกต์อื่น**: [streamlit.io/ansh kunwar](https://share.streamlit.io/user/anshk1234)
- 📧 **ติดต่อ**: anshkunwar3009@gmail.com
- แอปนี้ใช้สัญญาอนุญาต **Apache License 2.0**
""")

st.sidebar.markdown("<br><center>© 2025 แดชบอร์ดหุ้น Live</center>", unsafe_allow_html=True)

# ส่วนท้าย
st.markdown("<p style='text-align:center; color:white;'>© 2025 แดชบอร์ดหุ้น Live | ขับเคลื่อนโดย Yahoo Finance</p>", unsafe_allow_html=True)
