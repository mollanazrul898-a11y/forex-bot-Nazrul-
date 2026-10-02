from datetime import datetime
import json
import time
import urllib.request

# ================= কনফিগারেশন =================
TELEGRAM_BOT_TOKEN = "8640559582:AAFm4Gl82i_IgRCrPypeOWPodiLwOgU0mD0"
TELEGRAM_CHAT_ID = "7003908550"

# ১০টি জনপ্রিয় ফরেক্স পেয়ার + গোল্ড (XAUUSD)
PAIRS = {
    "GOLD (XAUUSD)": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "CAD=X",
    "USDCHF": "CHF=X",
    "NZDUSD": "NZDUSD=X",
    "EURGBP": "EURGBP=X",
    "EURJPY": "EURJPY=X",
}

# টাইমফ্রেম কনফিগারেশন (Yahoo Finance Interval Code)
TIMEFRAMES = {
    "1Min (Scalping)": "1m",
    "5Min (Intraday)": "5m",
    "30Min (Swing)": "30m",
    "1Hour (Trend)": "60m",
}
# ===============================================


def send_telegram_message(text):
    """টেলিগ্রামে লাইভ সিগন্যাল পাঠানোর ফাংশন"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.getcode() == 200
    except Exception as e:
        print(f"Telegram Connection Error: {e}")
        return False


def fetch_price_data(ticker, interval):
    """Yahoo Finance থেকে লাইভ ক্যান্ডেলস্টিক ডাটা সংগ্রহ"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range=5d"
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            indicators = result["chart"]["result"][0]["indicators"]["quote"][0]
            closes = [c for c in indicators["close"] if c is not None]
            highs = [h for h in indicators["high"] if h is not None]
            lows = [l for l in indicators["low"] if l is not None]
            return closes, highs, lows
    except Exception:
        return None, None, None


def calculate_rsi(prices, period=14):
    """RSI (Relative Strength Index) হিসাবের অ্যালগরিদম"""
    if len(prices) < period + 1:
        return 50.0

    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(change if change > 0 else 0)
        losses.append(abs(change) if change < 0 else 0)

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calculate_ema(prices, period):
    """EMA (Exponential Moving Average) হিসাবের অ্যালগরিদম"""
    if len(prices) < period:
        return prices[-1]

    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period

    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema

    return ema


def calculate_atr(highs, lows, closes, period=14):
    """ATR (Average True Range) দিয়ে স্টপ লস ও টেক প্রফিট বের করা"""
    if len(closes) < period + 1:
        return 0.0010

    tr_list = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        tr_list.append(tr)

    return sum(tr_list[-period:]) / period


def run_bot():
    print("বট চালু হচ্ছে...")

    # কানেকশন ভেরিফিকেশন টেস্ট
    test = send_telegram_message(
        "🚀 <b>PRO AI FOREX SIGNAL BOT IS NOW LIVE!</b>\n\n"
        "📊 <b>Pairs:</b> Gold (XAUUSD) + 9 Major Forex Pairs\n"
        "⏱ <b>Timeframes:</b> 1m, 5m, 30m, 1h\n"
        "🧠 <b>Strategy:</b> AI Trend Multi-Confluence Engine"
    )

    if not test:
        print("❌ টেলিগ্রাম কানেকশন ব্যর্থ হয়েছে। টোকেনটি আবার পরীক্ষা করুন।")
        return

    print("✅ টেলিগ্রাম কানেকশন সফল! মার্কেট স্ক্যান করা হচ্ছে...\n")

    # সিগন্যাল ট্র্যাক রাখার জন্য মেমোরি
    last_signals = {
        pair: {tf: None for tf in TIMEFRAMES} for pair in PAIRS
    }

    while True:
        for pair_name, ticker in PAIRS.items():
            for tf_label, tf_code in TIMEFRAMES.items():
                closes, highs, lows = fetch_price_data(ticker, tf_code)

                if closes and len(closes) >= 50:
                    current_price = closes[-1]
                    rsi = calculate_rsi(closes)
                    ema_fast = calculate_ema(closes, 9)
                    ema_slow = calculate_ema(closes, 21)
                    ema_trend = calculate_ema(closes, 50)
                    atr = calculate_atr(highs, lows, closes)

                    signal = "NEUTRAL"

                    # AI Multi-Confluence Logic
                    # BUY: Fast EMA > Slow EMA + Price > Trend EMA + RSI Bullish Zone (52-68)
                    if (
                        ema_fast > ema_slow
                        and current_price > ema_trend
                        and 52 <= rsi <= 68
                    ):
                        signal = "STRONG BUY 🟢🟢"

                    # SELL: Fast EMA < Slow EMA + Price < Trend EMA + RSI Bearish Zone (32-48)
                    elif (
                        ema_fast < ema_slow
                        and current_price < ema_trend
                        and 32 <= rsi <= 48
                    ):
                        signal = "STRONG SELL 🔴🔴"

                    # নতুন এবং শক্তিশালী সিগন্যাল আসলেই কেবল টেলিগ্রামে পাঠাবে
                    if (
                        "STRONG" in signal
                        and last_signals[pair_name][tf_label] != signal
                    ):
                        last_signals[pair_name][tf_label] = signal

                        # ATR ভিত্তিক ডাইনামিক SL ও TP হিসাব
                        if "BUY" in signal:
                            sl = current_price - (atr * 1.5)
                            tp = current_price + (atr * 2.5)
                        else:
                            sl = current_price + (atr * 1.5)
                            tp = current_price - (atr * 2.5)

                        msg = (
                            f"🚨 <b>HIGH-ACCURACY AI SIGNAL</b> 🚨\n\n"
                            f"💱 <b>Pair:</b> {pair_name}\n"
                            f"⏱ <b>Timeframe:</b> {tf_label}\n"
                            f"🎯 <b>Signal:</b> {signal}\n\n"
                            f"💵 <b>Entry Price:</b> {current_price:.5f}\n"
                            f"🛑 <b>Stop Loss (SL):</b> {sl:.5f}\n"
                            f"🎯 <b>Take Profit (TP):</b> {tp:.5f}\n\n"
                            f"📊 <b>RSI Index:</b> {rsi}\n"
                            f"⏰ <b>Time:</b> <i>{datetime.now().strftime('%H:%M:%S')}</i>"
                        )

                        send_telegram_message(msg)
                        print(
                            f"[{datetime.now().strftime('%H:%M:%S')}] Signal Sent -> {pair_name} ({tf_label}): {signal}"
                        )

        time.sleep(20)  # প্রতি ২০ সেকেন্ড পর পর ১০টি পেয়ার এবং ৪টি টাইমফ্রেম রি-স্ক্যান করবে


if __name__ == "__main__":
    run_bot()
