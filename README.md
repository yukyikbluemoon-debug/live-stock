# 📈 Stockly — Live Stock Market Dashboard

A real-time stock market dashboard built with **Streamlit** and **yfinance**, offering live prices, historical comparisons, analyst ratings, financial news, and personal portfolio tracking — all in one place.
---
v2.0-unofficial

# 📈 แดชบอร์ดหุ้น Live — เอกสารประกอบโปรเจกต์

> **เวอร์ชัน:** 2.0 (ปรับปรุง)  
> **เทคโนโลยี:** Python · Streamlit · yfinance · Plotly · Altair  
> **แหล่งข้อมูล:** Yahoo Finance API  

---

## สารบัญ

1. [ภาพรวมแอปพลิเคชัน](#ภาพรวม)
2. [โครงสร้างแท็บ](#โครงสร้างแท็บ)
3. [Bug ที่พบและการแก้ไข](#bug-ที่พบและการแก้ไข)
4. [การปรับปรุงประสิทธิภาพ](#การปรับปรุงประสิทธิภาพ)
5. [ฟีเจอร์กราฟแท่งเทียน](#ฟีเจอร์กราฟแท่งเทียน)
6. [โครงสร้าง Cache](#โครงสร้าง-cache)
7. [วิธีรันแอป](#วิธีรันแอป)

---

## ภาพรวม

แดชบอร์ดหุ้น Live เป็นแอปพลิเคชัน Streamlit สำหรับติดตามราคาหุ้นแบบเรียลไทม์
ครอบคลุมหุ้น Large Cap, ETF, และ Crypto ETF มากกว่า 300 รายการ
พร้อมระบบพอร์ตโฟลิโอส่วนตัวที่บันทึกข้อมูลไม่หายเมื่อ refresh

---

## โครงสร้างแท็บ

### แท็บ 1 — 📈 ราคา Live
- เลือกหุ้นจากรายการกว่า 300 รายการ
- กราฟแท่งเทียน (Candlestick) + เส้นราคาปิด
- เลือกช่วงเวลาได้ตั้งแต่ 1 เดือน ถึง 20 ปี
- แสดง PE Ratio, EPS, Volume, Market Cap, Sector, 52-Week High/Low, Dividend Yield

### แท็บ 2 — 📉 แนวโน้มกลุ่ม
- เปรียบเทียบหลายหุ้นพร้อมกันด้วยกราฟ Normalized Price
- การ์ดราคาพร้อม Sparkline แต่ละหุ้น
- กราฟ รายบริษัท vs ค่าเฉลี่ยกลุ่ม
- **กราฟแท่งเทียนขั้นสูง** พร้อม EMA / Trendline / Support (ดูหัวข้อด้านล่าง)
- **เซฟการเลือกหุ้นและช่วงเวลาใน session** — ไม่หายเมื่อ switch tab

### แท็บ 3 — 📊 เมตริก
- กราฟ PE Ratio และ EPS เปรียบเทียบ 7 บริษัทหลัก
- กราฟ Bar คะแนนนักวิเคราะห์ (1 = ซื้อแรง, 5 = ขาย)
- มาตรวัด Gauge แต่ละบริษัท

### แท็บ 4 — 📰 ข่าว
- ดึงข่าวล่าสุดจาก Yahoo Finance 6 หุ้นหลัก
- แสดงหัวข้อ, สรุป, รูปภาพ, แหล่งที่มา, และลิงก์

### แท็บ 5 — ⚡ พอร์ตโฟลิโอ
- เพิ่มหุ้นพร้อมจำนวนและราคาซื้อ
- **บันทึกลงไฟล์ JSON อัตโนมัติ** — ไม่หายเมื่อ refresh
- นำเข้า/ส่งออก CSV
- แผนภูมิวงกลม (ECharts) และกราฟกำไร/ขาดทุน
- สรุปมูลค่ารวม, กำไร/ขาดทุนรวม, เงินลงทุนทั้งหมด

### แท็บ 6 — ⚙️ การตั้งค่า
- ปฏิทินกำหนดการบำรุงรักษา
- สถานะ Uptime ของแอป
- ข้อมูลการติดต่อและ Credit

---

## Bug ที่พบและการแก้ไข

### 🔴 ความรุนแรงสูง — พังหรือข้อมูลหาย

#### Bug #1: Lottie Animation Crash
| | รายละเอียด |
|---|---|
| **ปัญหา** | ไม่มี `try/except` — ถ้าไม่มีไฟล์ `Money Investment.json` แอปพังทันที |
| **แก้ไข** | ห่อทั้งบล็อกด้วย `try/except Exception: pass` — ไม่มีไฟล์ก็ข้ามไปเลย |

#### Bug #2: Portfolio ข้อมูลหายทุก Reload
| | รายละเอียด |
|---|---|
| **ปัญหา** | เก็บเฉพาะใน `st.session_state` — พอ refresh หรือ session หมดอายุ ข้อมูลหายหมด |
| **แก้ไข** | บันทึกลง `portfolio_data.json` ทุกครั้งที่มีการเปลี่ยนแปลง และโหลดกลับเมื่อเริ่มต้น |

```python
# โหลดตอนเริ่ม
if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_portfolio_from_file()

# บันทึกทุกครั้งที่แก้ไข
save_portfolio_to_file(st.session_state.portfolio)
```

#### Bug #3: HTTP Request ท่วมใน Portfolio Loop
| | รายละเอียด |
|---|---|
| **ปัญหา** | `get_portfolio_df()` เรียก `yf.Ticker().history()` ทุก row ทุกครั้งที่ re-render |
| **แก้ไข** | ใช้ `get_current_price()` ที่มี `@st.cache_data(ttl=300, max_entries=200)` |

#### Bug #4: `fetch_stock_details()` ไม่ตรวจ N/A
| | รายละเอียด |
|---|---|
| **ปัญหา** | ไม่ตรวจ `None` ก่อนใช้งาน — `dividend_yield` format crash ถ้า yfinance คืน string |
| **แก้ไข** | เพิ่ม `safe_get()` helper และตรวจ `isinstance(dy, (int, float))` ก่อน format |

---

### 🟡 ความรุนแรงกลาง — ใช้งานยากหรือ crash บางกรณี

#### Bug #5: STOCKS List ซ้ำ 3 จุด
| | รายละเอียด |
|---|---|
| **ปัญหา** | Copy-paste รายการหุ้นซ้ำในแท็บ 1, 2, 5 — แก้ที่เดียวไม่พอ ต้องแก้ 3 จุด |
| **แก้ไข** | ย้ายขึ้นเป็น constant ระดับ module ชื่อ `STOCKS` ใช้ร่วมกันทุกที่ |

#### Bug #6: CSV Import Brittle
| | รายละเอียด |
|---|---|
| **ปัญหา** | `detail.split("@ $")[1]` — crash ถ้า format ไม่ตรง เช่น ราคาเป็น `1,234.56` |
| **แก้ไข** | ใส่ `try/except` ต่อ row + รายงาน row ที่ parse ไม่ได้แยกต่างหาก |

#### Bug #7: Gauge Widget Key ซ้ำ
| | รายละเอียด |
|---|---|
| **ปัญหา** | `key=f"rating_{i}_{j}_{row['บริษัท']}"` — ถ้าชื่อบริษัทซ้ำเกิด `DuplicateWidgetID` |
| **แก้ไข** | เปลี่ยนเป็น `key=f"gauge_{i}_{j}"` ใช้ index แทนชื่อ |

---

### 🟢 ความรุนแรงต่ำ — ไม่กระทบการใช้งานหลัก

#### Bug #8: `time.sleep(4)` บล็อก Thread
| | รายละเอียด |
|---|---|
| **ปัญหา** | Streamlit เป็น single-thread ต่อ session — sleep บล็อกทุก interaction |
| **แก้ไข** | ทั้งบล็อก Lottie อยู่ใน `try/except` — ถ้าไม่มีไฟล์จะข้ามทั้งหมดทันที |

#### Bug #9: `next_saturday()` อ่านยาก
| | รายละเอียด |
|---|---|
| **ปัญหา** | Logic ถูกต้องแต่สับสน — `days_ahead = 5 - weekday()` อ่านไม่ออก |
| **แก้ไข** | เขียนใหม่ด้วย `(5 - weekday()) % 7` พร้อม comment อธิบาย |

---

### 🔵 Bug เพิ่มเติม — แนวโน้มกลุ่ม ไม่เซฟ Selection

| | รายละเอียด |
|---|---|
| **ปัญหา** | `multiselect` ใช้ `default=DEFAULT_TICKERS` ตายตัว — switch tab แล้วค่าหายทุกครั้ง |
| **แก้ไข** | เซฟใน `st.session_state.peer_tickers` และ `st.session_state.peer_horizon` |

```python
if "peer_tickers" not in st.session_state:
    st.session_state.peer_tickers = DEFAULT_TICKERS

tickers = st.multiselect(
    "เลือกหุ้น",
    STOCKS,
    default=st.session_state.peer_tickers,
    key="peer_tickers_widget",
)
if tickers != st.session_state.peer_tickers:
    st.session_state.peer_tickers = tickers
```

---

## การปรับปรุงประสิทธิภาพ

### ลด HTTP Request

| จุด | เดิม | ใหม่ | Request ที่ประหยัด |
|---|---|---|---|
| Sidebar 7 หุ้น | Loop 7 request แยก | `yf.download()` batch เดียว | ลด 6 request |
| Peer sparkline | `.info` + `.history()` ต่อ card | `fast_info` + ใช้ data ที่โหลดไว้แล้ว | ลด ~2N request |
| Peer price data | Loop N request แยก | `yf.download()` batch เดียว | ลด N-1 request |
| fetch_metrics | Loop 7 `.info` แยก | `yf.Tickers()` batch | รวม session |

### ควบคุม RAM

```python
# กำหนด max_entries ป้องกัน cache สะสมไม่มีที่สิ้นสุด
@st.cache_data(ttl=3600, max_entries=50)
def fetch_stock_details(...): ...

@st.cache_data(ttl=300, max_entries=200)
def get_current_price(...): ...
```

### ใช้ `fast_info` แทน `.info`

```python
# เดิม — ดึง metadata เต็ม ~50 fields
info = yf.Ticker(ticker).info

# ใหม่ — ดึงเฉพาะราคา เร็วกว่า 3–5 เท่า
fi = yf.Ticker(ticker).fast_info
price = fi.last_price
```

### `import numpy` ระดับ Module

```python
# เดิม — import ซ้ำทุกครั้งที่เรียกฟังก์ชัน
def show_peer_analysis():
    ...
    import numpy as np  # ← ใน loop

# ใหม่ — import ครั้งเดียวตอนเริ่มต้น
import numpy as np  # ← บนสุดของไฟล์
```

---

## ฟีเจอร์กราฟแท่งเทียน

อยู่ใน **แท็บ 2 — แนวโน้มกลุ่ม** เลื่อนลงด้านล่างหลังกราฟเปรียบเทียบ

### ตัวชี้วัดที่แสดง

| ตัวชี้วัด | สี | คำอธิบาย |
|---|---|---|
| EMA 20 | 🟡 เหลือง | Exponential Moving Average 20 วัน — แนวโน้มระยะสั้น |
| EMA 50 | 🟠 ส้ม | Exponential Moving Average 50 วัน — แนวโน้มระยะกลาง |
| EMA 100 | 🔴 แดง | Exponential Moving Average 100 วัน — แนวโน้มระยะยาว |
| Uptrend Line | 🟢 เขียวด่าง | Linear regression ผ่านจุด Low — เส้นแนวรับ |
| Downtrend Line | 🔴 แดงด่าง | Linear regression ผ่านจุด High — เส้นแนวต้าน |
| Support Level | 🔵 ฟ้าจุด | ค่าต่ำสุดของ Low ใน 20 แท่งล่าสุด |
| Volume | แดง/เขียว | Bar chart ปริมาณการซื้อขายด้านล่างกราฟ |

### วิธีคำนวณ EMA

```
EMA(วันนี้) = ราคา(วันนี้) × k + EMA(เมื่อวาน) × (1 - k)
โดยที่ k = 2 / (span + 1)
```

### วิธีคำนวณ Trendline

```
1. หาจุด Local Minima (Uptrend) หรือ Local Maxima (Downtrend)
   ในช่วง 60 แท่งล่าสุด
2. ทำ Linear Regression ผ่านจุดเหล่านั้น
3. ลากเส้นจากจุดแรก → จุดสุดท้ายของข้อมูล
```

### ตาราง EMA Summary

กด expander **"📋 ค่า EMA และ Support ปัจจุบัน"** เพื่อดู:
- ค่า EMA ณ วันล่าสุด
- % ห่างของราคาปัจจุบันจาก EMA
- สัญญาณ 🟢 อยู่เหนือ / 🔴 อยู่ใต้

---

## โครงสร้าง Cache

| ฟังก์ชัน | TTL | Max Entries | หมายเหตุ |
|---|---|---|---|
| `fetch_stock_details` | 1 ชั่วโมง | 50 | OHLC + ข้อมูลหุ้น |
| `get_current_price` | 5 นาที | 200 | ราคาล่าสุดสำหรับพอร์ต |
| `get_daily_details` | 1 ชั่วโมง | — | Sidebar 7 หุ้น (batch) |
| `fetch_metrics` | 10 ชั่วโมง | — | PE/EPS/Rating |
| `fetch_news` | 6 ชั่วโมง | — | ข่าวรายหุ้น |
| `load_peer_data` | 6 ชั่วโมง | — | ราคากลุ่ม (batch) |
| `load_candle_data` | 1 ชั่วโมง | — | OHLC สำหรับแท่งเทียน |
| `get_ticker_quote` | 1 ชั่วโมง | — | fast_info ราคา+prev_close |

---

## วิธีรันแอป

### ติดตั้ง Dependencies

```bash
pip install streamlit yfinance pandas plotly altair \
            streamlit-echarts streamlit-lottie numpy
```

### รันแอป

```bash
streamlit run app.py
```

### ไฟล์ที่เกี่ยวข้อง

```
📁 โปรเจกต์
├── app.py                    # ไฟล์หลัก
├── portfolio_data.json       # ข้อมูลพอร์ตโฟลิโอ (สร้างอัตโนมัติ)
└── Money Investment.json     # ไฟล์ Lottie Animation (optional)
```

> **หมายเหตุ:** ไฟล์ `portfolio_data.json` จะถูกสร้างอัตโนมัติเมื่อเพิ่มหุ้นครั้งแรก  
> ไฟล์ `Money Investment.json` เป็น optional — ถ้าไม่มีแอปยังทำงานได้ปกติ

---

*เอกสารนี้อัปเดตพร้อมกับ app.py เวอร์ชัน 2.0*
---

Original
🔗 **Live App:** [live-stock-market-dashboard.streamlit.app](https://live-stock-market-dashboard.streamlit.app)

---

## Features

- **Live Stock Prices** — Fetch real-time price data for any publicly listed company using its ticker symbol.
- **Company Comparison** — Compare the historical performance of multiple companies on a single interactive chart.
- **Metrics & Analyst Ratings** — View key financial metrics and aggregated analyst buy/sell/hold recommendations.
- **Daily Market News** — Stay up to date with the latest stock market news relevant to your selected tickers.
- **Personal Portfolio** — Track your own investments, monitor gains/losses, and visualize your portfolio allocation.

---

## Tech Stack

| Library | Purpose |
|---|---|
| [Streamlit](https://streamlit.io/) | Web app framework |
| [yfinance](https://github.com/ranaroussi/yfinance) | Live & historical stock data |
| [Pandas](https://pandas.pydata.org/) | Data manipulation |
| [Plotly](https://plotly.com/python/) | Interactive charts |
| [Altair](https://altair-viz.github.io/) | Declarative visualizations |
| [streamlit-lottie](https://github.com/andfanilo/streamlit-lottie) | Lottie animations |
| [streamlit-echarts](https://github.com/andfanilo/streamlit-echarts) | ECharts-based visualizations |

---

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/anshk1234/live-stock-market-prices.git
cd live-stock-market-prices

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run "stock dashboard.py"
```

The app will open in your browser at `http://localhost:8501`.

---

## Project Structure

```
live-stock-market-prices/
├── stock dashboard.py      # Main Streamlit application
├── Money Investment.json   # Portfolio / investment data
├── requirements.txt        # Python dependencies
├── .streamlit/             # Streamlit configuration
└── LICENSE                 # Apache 2.0 License
```

---

## License

This project is licensed under the [Apache 2.0 License](./LICENSE).

---

> If you find this project useful, please consider giving it a ⭐ on GitHub!
