import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="TSLA vs BYD Stock Comparison", layout="wide")
st.title("TSLA vs BYD: 1-Year Stock Comparison")
st.markdown("**Target user**: Retail investors | **Data source**: Yahoo Finance")

end_date = datetime.today()
start_date = end_date - timedelta(days=365)

@st.cache_data
def load_data():
    tsla = yf.download("TSLA", start=start_date, end=end_date, progress=False)["Adj Close"]
    byd = yf.download("1211.HK", start=start_date, end=end_date, progress=False)["Adj Close"]
    df = pd.DataFrame({"Tesla": tsla, "BYD": byd}).dropna()
    return df

df = load_data()

st.subheader("Price Trend")
fig_price = px.line(df, title="Adjusted Close Price Comparison")
st.plotly_chart(fig_price, use_container_width=True)

returns = df.pct_change().dropna()
st.subheader("Daily Return Distribution")
fig_hist = px.histogram(returns, barmode="overlay", opacity=0.6, title="Daily Return Distribution")
st.plotly_chart(fig_hist, use_container_width=True)

st.subheader("Risk Comparison (1 Year)")
risk_df = pd.DataFrame({
    "Stock": ["Tesla", "BYD"],
    "Annual Volatility (%)": [returns["Tesla"].std() * (252**0.5) * 100,
                              returns["BYD"].std() * (252**0.5) * 100],
    "Max Daily Loss (%)": [returns["Tesla"].min() * 100, returns["BYD"].min() * 100]
})
st.dataframe(risk_df.style.format("{:.2f}"))

st.info("Conclusion: Tesla has higher volatility, suitable for risk-tolerant investors; BYD is more stable.")
st.caption(f"Data accessed: {datetime.today().strftime('%Y-%m-%d')} | Educational purpose only")
