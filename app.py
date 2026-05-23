import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# ── 頁面設定 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="《小鹿信箱》物流查詢",
    page_icon="📦",
    layout="centered",
)

# ── 自訂樣式（支援深色 / 淺色主題） ───────────────────────────────────────────
st.markdown("""
<style>
    /* ── 字體 ── */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', 'PingFang TC', 'Microsoft JhengHei', sans-serif;
    }

    /* ── CSS 變數：淺色預設 ── */
    :root {
        --bg-card:      #ffffff;
        --bg-stat:      #f8fafc;
        --border:       #e2e8f0;
        --border-inner: #f1f5f9;
        --text-title:   #1a1a2e;
        --text-sub:     #6b7280;
        --text-body:    #334155;
        --text-label:   #94a3b8;
        --text-missing: #cbd5e1;
        --shadow:       0 1px 4px rgba(0,0,0,0.06);
    }

    /* ── CSS 變數：深色覆寫 ── */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-card:      #1e2130;
            --bg-stat:      #252840;
            --border:       #353a55;
            --border-inner: #2d3148;
            --text-title:   #e8eaf6;
            --text-sub:     #9ea3c0;
            --text-body:    #c5c9e0;
            --text-label:   #6b7280;
            --text-missing: #4a4f6a;
            --shadow:       0 1px 6px rgba(0,0,0,0.3);
        }
    }

    /* ── 標題 ── */
    .main-title { text-align: center; padding: 2rem 0 1.2rem 0; }
    .main-title h1 {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--text-title);
        letter-spacing: -0.5px;
        margin-bottom: 0.3rem;
    }
    .main-title p {
        color: var(--text-sub);
        font-size: 0.95rem;
    }

    /* ── Streamlit input 覆寫（移除白色 div 問題，直接美化原生 input） ── */
    div[data-testid="stTextInput"] {
        margin: 0.5rem 0 1.5rem 0;
    }
    div[data-testid="stTextInput"] > div > div > input {
        border: 2px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        color: var(--text-body) !important;
        background: var(--bg-card) !important;
        box-shadow: var(--shadow) !important;
        transition: border-color 0.2s;
    }
    /* 處理 Focus 狀態 outline */
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stTextInput"] > div > div > input:focus {
        border-color: #C5A482 !important;
        box-shadow: 0 0 0 3px rgba(197,164,130,0.15) !important;
        outline: none !important;
    }

    /* ── 統計卡 ── */
    .stat-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
    .stat-card {
        flex: 1;
        background: var(--bg-stat);
        border: 1.5px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .stat-card .num {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text-title);
    }
    .stat-card .lbl {
        font-size: 0.78rem;
        color: var(--text-label);
        margin-top: 2px;
    }

    /* ── 結果標題 ── */
    .result-header {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-sub);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--border-inner);
    }

    /* ── 商品卡片 ── */
    .order-card {
        background: var(--bg-card);
        border: 1.5px solid var(--border);
        border-radius: 14px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
    }
    .order-card .product-name {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--text-title);
        margin-bottom: 0.8rem;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid var(--border-inner);
    }
    .order-card .info-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.6rem 1rem;
    }
    .order-card .info-item label {
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--text-label);
        text-transform: uppercase;
        letter-spacing: 0.6px;
        display: block;
        margin-bottom: 2px;
    }
    .order-card .info-item span {
        font-size: 0.88rem;
        color: var(--text-body);
        font-weight: 500;
    }
    .order-card .info-item span.missing {
        color: var(--text-missing);
        font-style: italic;
    }

    /* ── 狀態徽章 ── */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 99px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-done    { background: #dcfce7; color: #16a34a; }
    .badge-shipped { background: #dbeafe; color: #2563eb; }
    .badge-pending { background: #fef9c3; color: #ca8a04; }

    /* ── 公告資訊列 ── */
    .meta-strip {
        display: flex;
        justify-content: center;
        gap: 1.2rem;
        margin: 0.8rem 0 1.8rem 0;
        flex-wrap: wrap;
    }
    .meta-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: var(--bg-stat);
        border: 1.5px solid var(--border);
        border-radius: 99px;
        padding: 0.35rem 1rem;
        font-size: 0.88rem;
        color: var(--text-body);
        font-weight: 500;
    }
    .meta-chip .chip-icon {
        font-size: 0.95rem;
    }
    .meta-chip .chip-label {
        color: var(--text-label);
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.4px;
    }
    .meta-chip .chip-value {
        color: var(--text-title);
        font-weight: 700;
    }

    /* ── 送出按鈕 ── */
    div[data-testid="stButton"] button {
        width: 100% !important;
        height: 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        background: linear-gradient(135deg, #C5A482 0%, #b48353 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(197,164,130,0.35) !important;
        transition: opacity 0.2s, box-shadow 0.2s, transform 0.1s !important;
        margin-top: 0.1rem !important;
    }
    div[data-testid="stButton"] button:hover {
        opacity: 0.92 !important;
        box-shadow: 0 6px 20px rgba(197,164,130,0.5) !important;
        transform: translateY(-1px) !important;
    }
    div[data-testid="stButton"] button:active {
        opacity: 1 !important;
        transform: translateY(0px) !important;
        box-shadow: 0 2px 8px rgba(197,164,130,0.3) !important;
    }

    /* ── 隱藏 Streamlit 預設元素 ── */
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── 讀取 Google Sheets 資料 ────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="總表", usecols=[0, 1, 2, 3, 4, 5, 6], ttl=0)
    df.columns = ["購買日期", "購買人", "商品名稱", "物流單號", "包裹重量", "運回日期", "狀態"]
    return df

@st.cache_data(ttl=60)
def load_meta():
    conn = st.connection("gsheets", type=GSheetsConnection)
    meta = conn.read(worksheet="總表", usecols=[8], nrows=1, ttl=0)
    cols = meta.columns.tolist()
    next_date = str(cols[0]).strip() if len(cols) > 0 else "—"
    return next_date

# ── 輔助函式 ──────────────────────────────────────────────────────────────────
def is_valid(val) -> bool:
    if val is None:
        return False
    if isinstance(val, float) and pd.isna(val):
        return False
    return str(val).strip() not in ("", "nan", "NaN")

def render_value(val, suffix="") -> str:
    if not is_valid(val):
        return '<span class="missing">—</span>'
    return f'<span>{val}{suffix}</span>'

def parse_date(val):
    """將 yyyy/mm/dd 字串解析為 Python date 物件，解析失敗回傳 None。"""
    if not is_valid(val):
        return None
    try:
        return pd.to_datetime(str(val).strip(), format="%Y/%m/%d").date()
    except Exception:
        return None

def is_checked(val) -> bool:
    """判斷 Google Sheets 核取方塊是否已勾選（勾選為 1.0，未勾選為 0.0）。"""
    return val == 1.0

def get_badge(val) -> str:
    """
    依運回日期決定徽章狀態：
      - 無日期          → "" （不顯示徽章）
      - 日期 ≤ 今日     → "已運回"
      - 日期 > 今日     → "待運回"
    """
    parsed = parse_date(val)
    if parsed is None:
        return ""
    return "已運回" if parsed <= date.today() else "待運回"

# ── 主畫面 ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-title">
    <h1>📦《小鹿信箱》</h1>
    <h3>物流狀態查詢</h3>
    <p>輸入購買人姓名，查詢您的商品狀態</p>
</div>
""", unsafe_allow_html=True)

# ── 公告資訊列（下次運回時間） ─────────────────────────────────────────────────
try:
    next_date = load_meta()
except Exception:
    next_date = "讀取失敗"

st.markdown(f"""
<div class="meta-strip">
    <div class="meta-chip">
        <span class="chip-icon">🗓️</span>
        <span class="chip-label">下次運回</span>
        <span class="chip-value">{next_date}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 輸入框（全寬）
name_input = st.text_input(
    "購買人姓名",
    placeholder="請輸入您的姓名…",
    label_visibility="collapsed",
    key="name_input_field",
)
# 送出按鈕（全寬，在輸入框正下方）
submitted = st.button("🔍 查詢", use_container_width=True)

# 按下送出或直接按 Enter（name_input 有值）都觸發查詢
active_name = name_input.strip() if (submitted or name_input.strip()) else ""

if not active_name:
    st.stop()

# ── 查詢資料 ──────────────────────────────────────────────────────────────────
try:
    df = load_data()
except Exception as e:
    st.error(f"❌ 無法讀取資料：{e}")
    st.stop()

keyword = active_name.lower()
result = df[df["購買人"].astype(str).str.strip().str.lower() == keyword].copy()

if result.empty:
    st.warning(f"找不到「{active_name}」的相關紀錄，請確認姓名是否正確。")
    st.stop()

# ── 徽章欄、排序 ─────────────────────────────────────────────────────────────
# 徽章：先依運回日期計算，再以「狀態」核取方塊覆寫為「已寄出」
result["_badge"] = result.apply(
    lambda row: "已寄出" if is_checked(row["狀態"]) else get_badge(row["運回日期"]),
    axis=1,
)

# 共用：購買日期 datetime 欄
result["_購買日期_sort"] = pd.to_datetime(
    result["購買日期"].astype(str).str.strip(), format="%Y/%m/%d", errors="coerce"
)
# 運回日期 datetime 欄（僅已運回群組使用）
result["_運回日期_sort"] = pd.to_datetime(
    result["運回日期"].astype(str).str.strip(), format="%Y/%m/%d", errors="coerce"
)

# 分組排序後合併：
#   已運回 / 已寄出  → 依運回日期升冪
#   其餘             → 待運回 → 無日期；同狀態內依購買日期升冪
df_arrived = (
    result[result["_badge"].isin(["已運回", "已寄出"])]
    .sort_values("_運回日期_sort", ascending=True)
)

_pending_order = {"待運回": 0, "": 1}
df_pending = result[~result["_badge"].isin(["已運回", "已寄出"])].copy()
df_pending["_pending_sort"] = df_pending["_badge"].map(_pending_order)
df_pending = df_pending.sort_values(
    by=["_pending_sort", "_購買日期_sort"],
    ascending=[True, True],
)

result = pd.concat([df_arrived, df_pending], ignore_index=True)

# ── 修正 3：下次運回重量 ──────────────────────────────────────────────────────
def weight_float(val) -> float:
    if not is_valid(val):
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def date_matches_next(val, next_date_str: str) -> bool:
    """運回日期字串與 next_date 字串是否為同一天。"""
    d1 = parse_date(val)
    d2 = parse_date(next_date_str)
    if d1 is None or d2 is None:
        return False
    return d1 == d2

# ── 統計摘要 ──────────────────────────────────────────────────────────────────
total    = len(result)
arrived  = (result["_badge"] == "已運回").sum()
shipped  = (result["_badge"] == "已寄出").sum()
pending  = (result["_badge"] == "待運回").sum()

next_shipment_weight = result.loc[
    result["運回日期"].apply(lambda v: date_matches_next(v, next_date)),
    "包裹重量"
].apply(weight_float).sum()

st.markdown(f"""
<div class="stat-row">
    <div class="stat-card">
        <div class="num">{total}</div>
        <div class="lbl">總筆數</div>
    </div>
    <div class="stat-card">
        <div class="num" style="color:#16a34a">{arrived}</div>
        <div class="lbl">已運回</div>
    </div>
    <div class="stat-card">
        <div class="num" style="color:#2563eb">{shipped}</div>
        <div class="lbl">已寄出</div>
    </div>
    <div class="stat-card">
        <div class="num" style="color:#ca8a04">{pending}</div>
        <div class="lbl">待運回</div>
    </div>
    <div class="stat-card">
        <div class="num">{next_shipment_weight:.2f}</div>
        <div class="lbl">下次運回重量 (kg)</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 商品列表 ──────────────────────────────────────────────────────────────────
st.markdown(f'<div class="result-header">共找到 {total} 筆商品</div>', unsafe_allow_html=True)

for _, row in result.iterrows():
    _b = row["_badge"]
    if _b == "已運回":
        badge = '<span class="badge badge-done">已運回</span>'
    elif _b == "已寄出":
        badge = '<span class="badge badge-shipped">已寄出</span>'
    elif _b == "待運回":
        badge = '<span class="badge badge-pending">待運回</span>'
    else:
        badge = ""
    st.markdown(f"""
    <div class="order-card">
        <div class="product-name">{row['商品名稱']} &nbsp; {badge}</div>
        <div class="info-grid">
            <div class="info-item">
                <label>購買日期</label>
                {render_value(row['購買日期'])}
            </div>
            <div class="info-item">
                <label>運回日期</label>
                {render_value(row['運回日期'])}
            </div>
            <div class="info-item">
                <label>包裹重量</label>
                {render_value(row['包裹重量'], ' kg')}
            </div>
            <div class="info-item" style="grid-column: span 3;">
                <label>物流單號</label>
                {render_value(row['物流單號'])}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)