import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("股票半年回報率分析")

# User input for stock symbol
symbol = st.text_input("請輸入股票代碼 (例如: AAPL)", "AAPL")

if st.button("分析"):
    # Fetch data
    stock = yf.Ticker(symbol)
    half_year_df = stock.history(period="max", interval="6mo")

    if half_year_df.empty:
        st.error("無法獲取股票數據。請確認股票代碼是否正確。")
    else:
        half_year_df = half_year_df.dropna()

        # Extract data for May-Oct (October) and Nov-Apr (April) periods
        may_oct_df = half_year_df[half_year_df.index.month == 10]
        nov_apr_df = half_year_df[half_year_df.index.month == 4]

        # Set index to year
        may_oct_df.index = may_oct_df.index.year
        may_oct_df.index.name = "Year"
        nov_apr_df.index = nov_apr_df.index.year
        nov_apr_df.index.name = "Year"

        # Keep only the 'Close' column
        may_oct_df = pd.DataFrame(may_oct_df, columns=["Close"])
        nov_apr_df = pd.DataFrame(nov_apr_df, columns=["Close"])

        # Merge the two DataFrames on Year
        inner_joined_df = may_oct_df.merge(
            nov_apr_df,
            how="inner",
            left_index=True,
            right_index=True,
            suffixes=("_MayOct", "_NovApr")
        )

        # Calculate statistics for May-Oct
        may_oct_returns = inner_joined_df["Close_MayOct"]
        may_oct_wins = (may_oct_returns > 0).sum()
        may_oct_losses = (may_oct_returns < 0).sum()
        may_oct_total = len(may_oct_returns)
        may_oct_win_rate = may_oct_wins / may_oct_total if may_oct_total > 0 else 0
        may_oct_mean = may_oct_returns.mean() * 100
        may_oct_std = may_oct_returns.std() * 100

        # Calculate statistics for Nov-Apr
        nov_apr_returns = inner_joined_df["Close_NovApr"]
        nov_apr_wins = (nov_apr_returns > 0).sum()
        nov_apr_losses = (nov_apr_returns < 0).sum()
        nov_apr_total = len(nov_apr_returns)
        nov_apr_win_rate = nov_apr_wins / nov_apr_total if nov_apr_total > 0 else 0
        nov_apr_mean = nov_apr_returns.mean() * 100
        nov_apr_std = nov_apr_returns.std() * 100

        # Prepare data for plotting
        df = inner_joined_df.reset_index()
        df_melt = pd.melt(
            df,
            id_vars='Year',
            value_vars=['Close_MayOct', 'Close_NovApr'],
            var_name='Category',
            value_name='Return'
        )
        df_melt["Return"] = df_melt["Return"] * 100

        company_name = stock.info.get('longName', 'Company name not found')

        # Rename categories to clearer Chinese labels
        df_melt['Category'] = df_melt['Category'].map({
            'Close_MayOct': '5月至10月',
            'Close_NovApr': '11月至4月'
        })

        # Create grouped bar chart
        fig = px.bar(
            df_melt,
            x='Year',
            y='Return',
            color='Category',
            barmode='group',
            text='Return',
            labels={
                "Year": "年份",
                "Return": "半年回報率 (%)",
                "Category": "分類"
            },
            title=f"{company_name} 5月至10月 vs 11月至4月 半年回報率比較"
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(
            height=600,
            title_x=0.5,
            yaxis_tickformat=".2f"
        )

        # Display the chart
        st.plotly_chart(fig, use_container_width=True)

        # Display statistics
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("5月至10月 統計:")
            st.write(f"平均回報率: {may_oct_mean:.2f}%")
            st.write(f"標準差 (波幅率): {may_oct_std:.2f}%")
            st.write(f"獲勝期數: {may_oct_wins}")
            st.write(f"虧損期數: {may_oct_losses}")
            st.write(f"勝率: {may_oct_win_rate:.2%}")

        with col2:
            st.subheader("11月至4月 統計:")
            st.write(f"平均回報率: {nov_apr_mean:.2f}%")
            st.write(f"標準差 (波幅率): {nov_apr_std:.2f}%")
            st.write(f"獲勝期數: {nov_apr_wins}")
            st.write(f"虧損期數: {nov_apr_losses}")
            st.write(f"勝率: {nov_apr_win_rate:.2%}")
