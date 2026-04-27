import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Multi-Stock Performance Analysis", page_icon="📈", layout="wide")

# ========================= Helper Functions =========================
@st.cache_data
def generate_mock_data(tickers, start_date, end_date):
    """Generate realistic mock stock data based on market characteristics"""
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    np.random.seed(42)
    
    # Realistic annual volatility for different stocks (approx)
    vol_dict = {
        'AAPL': 0.25, 'MSFT': 0.24, 'GOOGL': 0.28, 'AMZN': 0.32,
        'TSLA': 0.45, 'META': 0.35, 'NVDA': 0.40, 'JPM': 0.22
    }
    # Base starting prices
    start_price = {'AAPL': 150, 'MSFT': 300, 'GOOGL': 120, 'AMZN': 130,
                   'TSLA': 180, 'META': 250, 'NVDA': 450, 'JPM': 130}
    
    all_data = []
    for ticker in tickers:
        vol = vol_dict.get(ticker, 0.30)
        mu = 0.0006  # daily drift ~15% annualized
        n = len(dates)
        returns = np.random.normal(mu, vol / np.sqrt(252), n)
        price = start_price.get(ticker, 100) * np.exp(np.cumsum(returns))
        df = pd.DataFrame({
            'date': dates,
            'htick': ticker,
            'price': price,
            'daily_return': returns
        })
        all_data.append(df)
    df_all = pd.concat(all_data, ignore_index=True)
    df_all['cum_return'] = (1 + df_all['daily_return']).groupby(df_all['htick']).cumprod()
    return df_all

def calculate_metrics(df):
    """Compute key metrics"""
    metrics = []
    for ticker in df['htick'].unique():
        sub = df[df['htick'] == ticker].sort_values('date')
        sub = sub.dropna(subset=['daily_return'])
        if len(sub) == 0:
            continue
        total_ret = sub['cum_return'].iloc[-1] - 1
        ann_vol = sub['daily_return'].std() * np.sqrt(252) * 100
        # Max drawdown
        running_max = sub['cum_return'].cummax()
        drawdown = (sub['cum_return'] - running_max) / running_max
        max_dd = drawdown.min() * 100
        sharpe = (sub['daily_return'].mean() / sub['daily_return'].std()) * np.sqrt(252) if sub['daily_return'].std() != 0 else 0
        metrics.append({
            'Ticker': ticker,
            'Total Return (%)': total_ret * 100,
            'Annual Volatility (%)': ann_vol,
            'Max Drawdown (%)': max_dd,
            'Sharpe Ratio (annual)': sharpe,
            'Mean Daily Return (%)': sub['daily_return'].mean() * 100,
            'Min Daily Return (%)': sub['daily_return'].min() * 100,
            'Max Daily Return (%)': sub['daily_return'].max() * 100
        })
    return pd.DataFrame(metrics)

# ========================= Sidebar =========================
st.sidebar.header("📈 Stock Selection")
default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM"]
selected_tickers = st.sidebar.multiselect("Select stocks to compare", default_tickers, default=["AAPL", "GOOGL"])

custom_input = st.sidebar.text_input("Or enter custom tickers (comma separated)", placeholder="NVDA, JPM, TSLA")
if custom_input:
    custom_list = [t.strip().upper() for t in custom_input.split(',')]
    selected_tickers = list(set(selected_tickers + custom_list))
    selected_tickers.sort()

st.sidebar.markdown(f"**Selected:** {', '.join(selected_tickers)}")

st.sidebar.header("📅 Date Range")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-03-04"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2025-04-21"))

st.sidebar.header("📊 Display Options")
show_cumulative = st.sidebar.checkbox("📈 Cumulative Return", True)
show_volatility = st.sidebar.checkbox("📊 Volatility & Drawdown", True)
show_distribution = st.sidebar.checkbox("📉 Return Distribution", False)
show_correlation = st.sidebar.checkbox("🔗 Correlation Matrix", False)
show_sharpe = st.sidebar.checkbox("⚖️ Sharpe Ratio", True)
show_monthly = st.sidebar.checkbox("📅 Monthly Heatmap", False)
show_raw_price = st.sidebar.checkbox("💰 Price Trends", True)
show_raw_data = st.sidebar.checkbox("📋 Raw Data", False)

run_button = st.sidebar.button("🚀 Run Analysis", type="primary")

# ========================= Main Interface =========================
st.title("📊 Multi-Stock Performance Analysis")
st.write("Compare stock price trends and risk metrics (simulated data based on real market characteristics)")

with st.expander("ℹ️ About This App"):
    st.markdown("""
    - **Data Source:** Simulated realistic stock data (parameters derived from historical market statistics)
    - **Metrics:** Total return, annual volatility, max drawdown, Sharpe ratio, correlation, monthly heatmap
    - **Instructions:** Select stocks, choose date range, click **Run Analysis**
    """)

if run_button:
    if len(selected_tickers) == 0:
        st.error("❌ Please select at least one stock")
    else:
        with st.spinner("🔄 Generating stock data..."):
            df = generate_mock_data(selected_tickers, start_date, end_date)
        
        metrics_df = calculate_metrics(df)
        returns_pivot = df.pivot(index='date', columns='htick', values='daily_return').dropna()
        
        st.success(f"✅ Data generated for {len(selected_tickers)} stocks")
        
        st.markdown(f"""
        ---
        **Data Source:** Simulated market data (based on real volatility patterns)  
        **Access Date:** {datetime.now().strftime('%Y-%m-%d')}  
        **Period:** {start_date} to {end_date}  
        **Disclaimer:** For educational purposes only.
        ---
        """)
        
        # Best and worst performers
        best = metrics_df.loc[metrics_df['Total Return (%)'].idxmax()]
        worst = metrics_df.loc[metrics_df['Total Return (%)'].idxmin()]
        col1, col2 = st.columns(2)
        col1.success(f"🏆 **Best Performer:** {best['Ticker']}\n\n+{best['Total Return (%)']:.2f}%")
        col2.warning(f"📉 **Worst Performer:** {worst['Ticker']}\n\n{worst['Total Return (%)']:.2f}%")
        
        st.markdown("---")
        
        # ---------- Interactive Charts (Plotly) ----------
        if show_cumulative:
            st.subheader("📈 Cumulative Return Comparison")
            cum_df = df.pivot(index='date', columns='htick', values='cum_return')
            fig_cum = px.line(cum_df, title="Cumulative Return Over Time",
                              labels={"value": "Cumulative Return", "date": "Date"})
            fig_cum.update_layout(legend_title_text='Stock', hovermode='x unified')
            st.plotly_chart(fig_cum, use_container_width=True)
        
        if show_volatility:
            st.subheader("📊 Volatility Comparison")
            vol_fig = px.bar(metrics_df, x='Ticker', y='Annual Volatility (%)',
                             title='Annualized Volatility',
                             color='Annual Volatility (%)', color_continuous_scale='Blues')
            st.plotly_chart(vol_fig, use_container_width=True)
            
            st.subheader("📉 Maximum Drawdown")
            dd_fig = px.bar(metrics_df, x='Ticker', y='Max Drawdown (%)',
                            title='Maximum Drawdown (Worst Peak-to-Trough Decline)',
                            color='Max Drawdown (%)', color_continuous_scale='Reds')
            st.plotly_chart(dd_fig, use_container_width=True)
        
        if show_distribution:
            st.subheader("📉 Daily Return Distribution")
            returns_long = df[['date', 'htick', 'daily_return']].dropna()
            fig_box = px.box(returns_long, x='htick', y='daily_return',
                             title='Daily Return Distribution',
                             labels={'daily_return': 'Daily Return', 'htick': 'Stock'})
            st.plotly_chart(fig_box, use_container_width=True)
        
        if show_correlation and len(returns_pivot.columns) > 1:
            st.subheader("🔗 Return Correlation Matrix")
            corr = returns_pivot.corr()
            fig_corr = px.imshow(corr, text_auto=True, aspect='auto',
                                 color_continuous_scale='RdBu', zmin=-1, zmax=1,
                                 title='Correlation Matrix of Daily Returns')
            st.plotly_chart(fig_corr, use_container_width=True)
        
        if show_sharpe:
            st.subheader("⚖️ Sharpe Ratio (Annualized)")
            sharpe_fig = px.bar(metrics_df, x='Ticker', y='Sharpe Ratio (annual)',
                                title='Risk-Adjusted Return Comparison',
                                color='Sharpe Ratio (annual)', color_continuous_scale='Viridis')
            sharpe_fig.add_hline(y=0, line_dash="dash", line_color="black")
            st.plotly_chart(sharpe_fig, use_container_width=True)
            st.caption("Higher Sharpe Ratio indicates better risk-adjusted performance.")
        
        if show_monthly:
            st.subheader("📅 Monthly Return Heatmap")
            df['year_month'] = df['date'].dt.to_period('M')
            monthly = df.groupby(['htick', 'year_month'])['daily_return'].sum().unstack(level=0).fillna(0) * 100
            fig_month = px.imshow(monthly.T, text_auto=True, aspect='auto',
                                  color_continuous_scale='RdYlGn', title='Monthly Total Return (%)',
                                  labels={'x': 'Month', 'y': 'Stock', 'color': 'Return (%)'})
            st.plotly_chart(fig_month, use_container_width=True)
        
        if show_raw_price:
            st.subheader("💰 Price Trends")
            price_pivot = df.pivot(index='date', columns='htick', values='price')
            fig_price = px.line(price_pivot, title="Adjusted Close Price Comparison",
                                labels={"value": "Price ($)", "date": "Date"})
            fig_price.update_layout(legend_title_text='Stock')
            st.plotly_chart(fig_price, use_container_width=True)
        
        # Statistics Table
        st.subheader("📋 Key Statistics")
        display_metrics = metrics_df.copy()
        for col in ['Total Return (%)', 'Annual Volatility (%)', 'Max Drawdown (%)', 
                    'Mean Daily Return (%)', 'Min Daily Return (%)', 'Max Daily Return (%)']:
            display_metrics[col] = display_metrics[col].apply(lambda x: f"{x:.2f}")
        display_metrics['Sharpe Ratio (annual)'] = display_metrics['Sharpe Ratio (annual)'].apply(lambda x: f"{x:.3f}")
        st.dataframe(display_metrics, use_container_width=True)
        
        if show_raw_data:
            with st.expander("📋 Raw Data (first 100 rows)"):
                st.dataframe(df.head(100))
        
        # Automatic Analysis Summary
        st.markdown("---")
        st.subheader("📝 Analysis Summary")
        summary = f"""
        **Overall Performance:** Over the selected period, the average total return was {metrics_df['Total Return (%)'].mean():.2f}%. 
        {best['Ticker']} was the best performer (+{best['Total Return (%)']:.2f}%), while {worst['Ticker']} was the worst ({worst['Total Return (%)']:.2f}%).
        
        **Risk Assessment:** The average annual volatility was {metrics_df['Annual Volatility (%)'].mean():.2f}%. 
        Maximum drawdowns ranged from {metrics_df['Max Drawdown (%)'].min():.2f}% to {metrics_df['Max Drawdown (%)'].max():.2f}%.
        
        **Risk-Adjusted Returns:** The average Sharpe ratio was {metrics_df['Sharpe Ratio (annual)'].mean():.3f}. 
        A higher Sharpe ratio indicates better return per unit of risk.
        """
        st.markdown(summary)
        
        # Download buttons
        st.markdown("---")
        st.subheader("📥 Download Data")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            csv_raw = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Raw Data (CSV)", data=csv_raw,
                               file_name="stock_data.csv", mime="text/csv")
        with col_d2:
            csv_stats = metrics_df.to_csv(index=False).encode('utf-8')
            st.download_button("📊 Download Statistics (CSV)", data=csv_stats,
                               file_name="stock_statistics.csv", mime="text/csv")
else:
    st.info("👈 Select stocks, choose date range, then click **Run Analysis**")