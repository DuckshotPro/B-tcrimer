"""
Professional financial UI components for cryptocurrency analysis platform.
Provides Bloomberg Terminal-style cards and widgets.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
from utils.themes import get_financial_colors

def create_portfolio_card(title: str, value: str, change: str, change_percent: float, 
                         icon: str = "📊", help_text: str = None):
    """Create a professional portfolio performance card"""
    
    # Determine color based on performance
    if change_percent > 0:
        card_class = "profit-card"
        trend_icon = "↗️"
        trend_color = "#10B981"
    elif change_percent < 0:
        card_class = "loss-card" 
        trend_icon = "↘️"
        trend_color = "#EF4444"
    else:
        card_class = "neutral-card"
        trend_icon = "→"
        trend_color = "#F59E0B"
    
    st.markdown(f"""
    <div class="{card_class} animate-slide-in">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.2rem;">{icon}</span>
                <span style="font-size: 0.9rem; opacity: 0.9; font-weight: 500;">{title}</span>
            </div>
            <span style="font-size: 1.1rem;">{trend_icon}</span>
        </div>
        
        <div style="margin-bottom: 0.5rem;">
            <div style="font-size: 2rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                {value}
            </div>
        </div>
        
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.875rem; opacity: 0.9;">{change}</span>
            <span style="font-size: 0.875rem; font-weight: 600;">
                {change_percent:+.2f}%
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_trading_signal_card(symbol: str, signal: str, confidence: float, 
                              price: float, target: float = None, stop_loss: float = None):
    """Create a trading signal card with actionable information"""
    
    # Signal styling
    signal_styles = {
        'BUY': ('signal-buy', '🟢', '#10B981'),
        'SELL': ('signal-sell', '🔴', '#EF4444'), 
        'HOLD': ('signal-hold', '🟡', '#F59E0B')
    }
    
    signal_class, signal_icon, signal_color = signal_styles.get(signal.upper(), signal_styles['HOLD'])
    
    st.markdown(f"""
    <div class="financial-card animate-slide-in">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <h3 style="margin: 0; font-size: 1.25rem; font-weight: 700;">{symbol}</h3>
                <p style="margin: 0; font-size: 0.875rem; color: var(--text-secondary);">
                    ${price:,.2f}
                </p>
            </div>
            <div style="text-align: right;">
                <span class="{signal_class}">{signal_icon} {signal}</span>
                <div style="margin-top: 0.25rem; font-size: 0.75rem; color: var(--text-secondary);">
                    Confidence: {confidence:.1%}
                </div>
            </div>
        </div>
        
        {f'''
        <div style="display: flex; justify-content: space-between; font-size: 0.875rem;">
            <div>
                <span style="color: var(--text-secondary);">Target:</span>
                <span style="color: var(--bull-green); font-weight: 600;">${target:,.2f}</span>
            </div>
            <div>
                <span style="color: var(--text-secondary);">Stop:</span>
                <span style="color: var(--bear-red); font-weight: 600;">${stop_loss:,.2f}</span>
            </div>
        </div>
        ''' if target and stop_loss else ''}
    </div>
    """, unsafe_allow_html=True)

def create_market_overview_card(data: Dict[str, Any]):
    """Create comprehensive market overview card"""
    
    total_market_cap = data.get('total_market_cap', 0)
    market_change = data.get('market_change_24h', 0)
    bitcoin_dominance = data.get('bitcoin_dominance', 0)
    active_cryptos = data.get('active_cryptocurrencies', 0)
    
    st.markdown(f"""
    <div class="financial-card animate-slide-in">
        <h3 style="margin: 0 0 1.5rem 0; font-size: 1.25rem; font-weight: 700; color: var(--text-primary);">
            🌍 Global Market Overview
        </h3>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
            <div>
                <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.25rem;">
                    Total Market Cap
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                    ${total_market_cap/1e12:.2f}T
                </div>
                <div style="font-size: 0.75rem; color: {'var(--bull-green)' if market_change >= 0 else 'var(--bear-red)'};">
                    {market_change:+.2f}% (24h)
                </div>
            </div>
            
            <div>
                <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.25rem;">
                    Bitcoin Dominance
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                    {bitcoin_dominance:.1f}%
                </div>
                <div style="font-size: 0.75rem; color: var(--text-secondary);">
                    {active_cryptos:,} active coins
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_price_chart(symbol: str, prices: List[float], timestamps: List[str], 
                      volume: List[float] = None, height: int = 400):
    """Create professional financial price chart"""
    
    colors = get_financial_colors()
    
    # Determine if price is up or down
    price_change = prices[-1] - prices[0] if len(prices) > 1 else 0
    color = colors['bull'] if price_change >= 0 else colors['bear']
    
    fig = go.Figure()
    
    # Price line
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=prices,
        mode='lines',
        name=f'{symbol} Price',
        line=dict(color=color, width=3),
        fill='tonexty' if len(prices) > 1 else None,
        fillcolor=f'rgba{tuple(list(int(color[i:i+2], 16) for i in (1, 3, 5)) + [0.1])}',
        hovertemplate=f'<b>{symbol}</b><br>Price: $%{{y:,.2f}}<br>Time: %{{x}}<extra></extra>'
    ))
    
    # Volume bars (if provided)
    if volume:
        fig.add_trace(go.Bar(
            x=timestamps,
            y=volume,
            name='Volume',
            marker_color=colors['volume'],
            opacity=0.3,
            yaxis='y2',
            hovertemplate='Volume: %{y:,.0f}<extra></extra>'
        ))
    
    # Professional styling
    fig.update_layout(
        title=dict(
            text=f'<b>{symbol} Price Chart</b>',
            font=dict(size=18, family='Inter', color='var(--text-primary)'),
            x=0.02
        ),
        xaxis=dict(
            title='Time',
            gridcolor='rgba(128, 128, 128, 0.2)',
            showspikes=True,
            spikecolor=colors['primary'],
            spikethickness=1
        ),
        yaxis=dict(
            title='Price ($)',
            gridcolor='rgba(128, 128, 128, 0.2)',
            tickformat='$,.2f'
        ),
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False
        ) if volume else None,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter'),
        hovermode='x unified',
        height=height,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Add range selector
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1h", step="hour", stepmode="backward"),
                    dict(count=24, label="24h", step="hour", stepmode="backward"),
                    dict(count=7, label="7d", step="day", stepmode="backward"),
                    dict(count=30, label="30d", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=False),
            type="date"
        )
    )
    
    return fig

def create_sentiment_gauge(sentiment_score: float, title: str = "Market Sentiment"):
    """Create a professional sentiment gauge"""
    
    colors = get_financial_colors()
    
    # Determine color based on sentiment
    if sentiment_score > 0.6:
        gauge_color = colors['bull']
        sentiment_text = "Bullish"
    elif sentiment_score < 0.4:
        gauge_color = colors['bear'] 
        sentiment_text = "Bearish"
    else:
        gauge_color = colors['neutral']
        sentiment_text = "Neutral"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = sentiment_score * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 18, 'family': 'Inter'}},
        delta = {'reference': 50, 'suffix': '%'},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': gauge_color, 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(239, 68, 68, 0.2)'},
                {'range': [40, 60], 'color': 'rgba(245, 158, 11, 0.2)'},
                {'range': [60, 100], 'color': 'rgba(16, 185, 129, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "var(--text-primary)", 'family': 'Inter'},
        height=300
    )
    
    return fig

def create_performance_summary(portfolio_data: Dict[str, Any]):
    """Create comprehensive performance summary"""
    
    total_value = portfolio_data.get('total_value', 0)
    total_pnl = portfolio_data.get('total_pnl', 0)
    total_pnl_percent = portfolio_data.get('total_pnl_percent', 0)
    daily_pnl = portfolio_data.get('daily_pnl', 0)
    win_rate = portfolio_data.get('win_rate', 0)
    sharpe_ratio = portfolio_data.get('sharpe_ratio', 0)
    
    st.markdown(f"""
    <div class="financial-card animate-slide-in">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <h3 style="margin: 0; font-size: 1.25rem; font-weight: 700;">
                📊 Performance Summary
            </h3>
            <span style="font-size: 0.875rem; color: var(--text-secondary);">
                Last updated: Just now
            </span>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1.5rem;">
            <div style="text-align: center; padding: 1rem; background: var(--bg-secondary); border-radius: 8px;">
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                    PORTFOLIO VALUE
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                    ${total_value:,.2f}
                </div>
            </div>
            
            <div style="text-align: center; padding: 1rem; background: var(--bg-secondary); border-radius: 8px;">
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                    TOTAL P&L
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: {'var(--bull-green)' if total_pnl >= 0 else 'var(--bear-red)'};">
                    ${total_pnl:+,.2f}
                </div>
                <div style="font-size: 0.875rem; font-weight: 600; color: {'var(--bull-green)' if total_pnl_percent >= 0 else 'var(--bear-red)'};">
                    {total_pnl_percent:+.2f}%
                </div>
            </div>
            
            <div style="text-align: center; padding: 1rem; background: var(--bg-secondary); border-radius: 8px;">
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                    DAILY P&L
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: {'var(--bull-green)' if daily_pnl >= 0 else 'var(--bear-red)'};">
                    ${daily_pnl:+,.2f}
                </div>
            </div>
            
            <div style="text-align: center; padding: 1rem; background: var(--bg-secondary); border-radius: 8px;">
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                    WIN RATE
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                    {win_rate:.1%}
                </div>
            </div>
            
            <div style="text-align: center; padding: 1rem; background: var(--bg-secondary); border-radius: 8px;">
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                    SHARPE RATIO
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                    {sharpe_ratio:.2f}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_loading_card(title: str = "Loading...", message: str = "Fetching latest data..."):
    """Create professional loading card with animation"""
    
    st.markdown(f"""
    <div class="financial-card animate-pulse">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="width: 40px; height: 40px; border: 3px solid var(--primary-color); 
                        border-top: 3px solid transparent; border-radius: 50%; animation: spin 1s linear infinite;">
            </div>
            <div>
                <h4 style="margin: 0; font-size: 1.1rem; color: var(--text-primary);">{title}</h4>
                <p style="margin: 0; font-size: 0.875rem; color: var(--text-secondary);">{message}</p>
            </div>
        </div>
    </div>
    
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """, unsafe_allow_html=True)