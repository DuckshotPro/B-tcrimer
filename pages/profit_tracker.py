
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from analysis.signal_generator import AutomatedSignalGenerator
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Display profit tracking dashboard"""
    st.title("💰 Profit Maximization Center")
    
    # Initialize signal generator
    signal_gen = AutomatedSignalGenerator()
    
    # Top opportunities section
    st.header("🚀 Top Trading Opportunities")
    
    with st.spinner("Analyzing market opportunities..."):
        opportunities = signal_gen.get_top_opportunities(limit=10)
    
    if opportunities:
        # Create opportunities table
        opp_data = []
        for opp in opportunities:
            opp_data.append({
                'Symbol': opp['symbol'],
                'Signal': f"{opp['signal']} {'🚀' if opp['signal'] == 'BUY' else '📉'}",
                'Confidence': f"{opp['confidence']:.1%}",
                'Expected Return': f"{opp['expected_return']:+.2f}%",
                'Risk Level': opp['risk_level'],
                'Tech Score': f"{opp['technical_score']:+.2f}",
                'AI Score': f"{opp['ml_score']:+.2f}",
                'Sentiment': f"{opp['sentiment_score']:+.2f}"
            })
        
        st.dataframe(pd.DataFrame(opp_data), use_container_width=True)
        
        # Show detailed analysis for selected opportunity
        if opp_data:
            selected_symbol = st.selectbox(
                "Select symbol for detailed analysis:",
                [opp['Symbol'] for opp in opp_data]
            )
            
            # Display detailed analysis
            selected_opp = next(opp for opp in opportunities if opp['symbol'] == selected_symbol)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Signal Strength", selected_opp['signal'])
                st.metric("Confidence Level", f"{selected_opp['confidence']:.1%}")
            
            with col2:
                st.metric("Expected Return", f"{selected_opp['expected_return']:+.2f}%")
                st.metric("Risk Level", selected_opp['risk_level'])
            
            with col3:
                # Calculate potential profit
                investment = st.number_input("Investment Amount ($)", value=1000, step=100)
                potential_profit = investment * (selected_opp['expected_return'] / 100)
                st.metric("Potential Profit", f"${potential_profit:+,.2f}")
    
    else:
        st.info("No strong trading opportunities detected at the moment. Market conditions may be sideways.")
    
    # Backtesting results section
    st.header("📊 Strategy Performance Analysis")
    
    # Get recent backtest results
    from analysis.backtesting import get_recent_backtests
    recent_backtests = get_recent_backtests(limit=10)
    
    if recent_backtests:
        # Performance summary
        total_returns = [b['total_return'] for b in recent_backtests]
        avg_return = sum(total_returns) / len(total_returns)
        best_return = max(total_returns)
        win_rate = len([r for r in total_returns if r > 0]) / len(total_returns) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Average Return", f"{avg_return:+.2f}%")
        
        with col2:
            st.metric("Best Return", f"{best_return:+.2f}%")
        
        with col3:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        with col4:
            profitable_strategies = len([b for b in recent_backtests if b['total_return'] > 0])
            st.metric("Profitable Strategies", f"{profitable_strategies}/{len(recent_backtests)}")
        
        # Performance chart
        fig = go.Figure()
        
        symbols = [b['symbol'] for b in recent_backtests]
        returns = [b['total_return'] for b in recent_backtests]
        colors = ['green' if r > 0 else 'red' for r in returns]
        
        fig.add_trace(go.Bar(
            x=symbols,
            y=returns,
            marker_color=colors,
            text=[f"{r:+.1f}%" for r in returns],
            textposition='outside'
        ))
        
        fig.update_layout(
            title="Strategy Performance by Symbol",
            xaxis_title="Symbol",
            yaxis_title="Return (%)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Profit projection section
    st.header("🎯 Profit Projections")
    
    col1, col2 = st.columns(2)
    
    with col1:
        initial_capital = st.number_input("Initial Capital ($)", value=10000, step=1000)
        target_return = st.slider("Target Monthly Return (%)", 1, 20, 8)
        months = st.slider("Time Horizon (months)", 1, 24, 12)
    
    with col2:
        # Calculate projections
        monthly_return = target_return / 100
        projected_value = initial_capital * ((1 + monthly_return) ** months)
        total_profit = projected_value - initial_capital
        
        st.metric("Projected Portfolio Value", f"${projected_value:,.2f}")
        st.metric("Total Projected Profit", f"${total_profit:+,.2f}")
        st.metric("ROI", f"{(total_profit / initial_capital) * 100:+.1f}%")
        
        # Show path to million
        if total_profit < 1000000:
            months_to_million = 0
            current_value = initial_capital
            while current_value < 1000000 and months_to_million < 120:  # Max 10 years
                current_value *= (1 + monthly_return)
                months_to_million += 1
            
            if months_to_million < 120:
                years = months_to_million // 12
                remaining_months = months_to_million % 12
                st.success(f"🚀 Path to $1M: {years} years, {remaining_months} months")
            else:
                st.info("💡 Consider increasing target returns or initial capital")
    
    # Compound growth visualization
    st.subheader("Compound Growth Visualization")
    
    # Calculate month-by-month growth
    growth_data = []
    current_value = initial_capital
    
    for month in range(months + 1):
        growth_data.append({
            'Month': month,
            'Portfolio Value': current_value,
            'Profit': current_value - initial_capital
        })
        current_value *= (1 + monthly_return)
    
    growth_df = pd.DataFrame(growth_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=growth_df['Month'],
        y=growth_df['Portfolio Value'],
        mode='lines+markers',
        name='Portfolio Value',
        line=dict(color='green', width=3)
    ))
    
    fig.add_hline(y=1000000, line_dash="dash", line_color="gold", 
                  annotation_text="$1M Target", annotation_position="top left")
    
    fig.update_layout(
        title="Portfolio Growth Projection",
        xaxis_title="Months",
        yaxis_title="Portfolio Value ($)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
