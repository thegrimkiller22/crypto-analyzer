import ccxt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from ta.momentum import RSIIndicator
from ta.trend import MACD
import time

def fetch_crypto_data(symbol, timeframe, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            exchange = ccxt.binance()  # Replace with your desired exchange
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            retries += 1
            print(f"Error fetching data (Attempt {retries}/{max_retries}): {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying
    print("Failed to fetch data after multiple attempts.")
    return None

def calculate_technical_indicators(data):
    # Calculate RSI
    rsi_indicator = RSIIndicator(data['Close'], window=14)
    data['RSI'] = rsi_indicator.rsi()

    # Calculate MACD
    macd_indicator = MACD(data['Close'], window_slow=26, window_fast=12, window_sign=9)
    data['MACD'] = macd_indicator.macd()
    data['MACD_Signal'] = macd_indicator.macd_signal()

    # Calculate Moving Average
    data['MA'] = data['Close'].rolling(window=44).mean()

    return data

def generate_chart(data, symbol):
    fig = go.Figure(data=[
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name='Candlestick'),
        go.Scatter(x=data.index, y=data['MA'], mode='lines', name='Moving Average'),
        go.Scatter(x=data[data['Indicator'] == 'Buy'].index, y=data[data['Indicator'] == 'Buy']['Close'],
                   mode='markers', name='Buy', marker=dict(color='green', symbol='triangle-up', size=10)),
        go.Scatter(x=data[data['Indicator'] == 'Sell'].index, y=data[data['Indicator'] == 'Sell']['Close'],
                   mode='markers', name='Sell', marker=dict(color='red', symbol='triangle-down', size=10))
    ])
    fig.update_layout(title=f"{symbol} Crypto Price with Buy/Sell Indicators", xaxis_rangeslider_visible=False)
    return fig

def main():
    st.title("Real-Time Crypto Chart with Buy/Sell Indicators")

    crypto_symbol = st.text_input("Enter cryptocurrency symbol (e.g., BTC/USDT)", "BTC/USDT")
    update_interval = st.slider("Update Interval (seconds)", 10, 300, 60)

    crypto_data = fetch_crypto_data(crypto_symbol, "1h")  # Adjust timeframe as needed
    if crypto_data is None:
        st.error("Failed to fetch data. Please try again later.")
        return

    crypto_data = calculate_technical_indicators(crypto_data)

    crypto_data['Indicator'] = 'Hold'
    crypto_data.loc[(crypto_data['RSI'] < 30) & (crypto_data['MACD'] > crypto_data['MACD_Signal']), 'Indicator'] = 'Buy'
    crypto_data.loc[(crypto_data['RSI'] > 70) & (crypto_data['MACD'] < crypto_data['MACD_Signal']), 'Indicator'] = 'Sell'

    chart = generate_chart(crypto_data, crypto_symbol)
    st.plotly_chart(chart)

if __name__ == "__main__":
    main()
