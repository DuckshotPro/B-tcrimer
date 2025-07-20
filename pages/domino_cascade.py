
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from analysis.domino_cascade import DominoCascadeSystem
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Display domino cascade automation system"""
    st.title("🎯 Domino Cascade Investment System")
    st.markdown("**Start with $100 and watch it grow through automated cascading investments!**")
    
    # Initialize session state
    if 'cascade_system' not in st.session_state:
        st.session_state.cascade_system = None
    if 'cascade_running' not in st.session_state:
        st.session_state.cascade_running = False
    
    # Configuration section
    st.header("⚙️ Cascade Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        initial_capital = st.number_input(
            "Starting Capital ($)", 
            min_value=50.0, 
            max_value=10000.0, 
            value=100.0, 
            step=50.0
        )
    
    with col2:
        max_cycles = st.number_input(
            "Maximum Cycles", 
            min_value=1, 
            max_value=100, 
            value=20, 
            step=1
        )
    
    with col3:
        cycle_delay = st.selectbox(
            "Delay Between Cycles",
            [1, 5, 15, 30, 60, 120],
            index=2,
            format_func=lambda x: f"{x} minutes"
        )
    
    # Advanced settings
    with st.expander("🔧 Advanced Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            reinvest_rate = st.slider("Profit Reinvestment Rate", 0.5, 1.0, 0.8, 0.1)
            min_trade_size = st.number_input("Minimum Trade Size ($)", 5.0, 50.0, 10.0, 5.0)
        
        with col2:
            risk_tolerance = st.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"])
            auto_stop_loss = st.checkbox("Auto Stop-Loss", value=True)
    
    # Control buttons
    st.header("🎮 Cascade Control")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🚀 Start Cascade", disabled=st.session_state.cascade_running):
            # Initialize cascade system
            st.session_state.cascade_system = DominoCascadeSystem(initial_capital)
            st.session_state.cascade_system.reinvestment_rate = reinvest_rate
            st.session_state.cascade_system.min_trade_size = min_trade_size
            
            st.session_state.cascade_running = True
            st.success("Domino Cascade System Started!")
            st.rerun()
    
    with col2:
        if st.button("⏸️ Pause Cascade", disabled=not st.session_state.cascade_running):
            st.session_state.cascade_running = False
            st.warning("Cascade Paused")
            st.rerun()
    
    with col3:
        if st.button("🔄 Single Cycle"):
            if st.session_state.cascade_system is None:
                st.session_state.cascade_system = DominoCascadeSystem(initial_capital)
            
            with st.spinner("Executing cascade cycle..."):
                success = st.session_state.cascade_system.execute_cascade_cycle()
                if success:
                    st.success("Cycle completed!")
                else:
                    st.error("Cycle failed!")
            st.rerun()
    
    with col4:
        if st.button("💾 Save Results"):
            if st.session_state.cascade_system:
                success = st.session_state.cascade_system.save_cascade_to_db()
                if success:
                    st.success("Results saved!")
                else:
                    st.error("Save failed!")
    
    # Display current system status
    if st.session_state.cascade_system:
        st.header("📊 Current Status")
        
        summary = st.session_state.cascade_system.get_cascade_summary()
        
        if summary:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Current Capital", 
                    f"${summary['current_capital']:,.2f}",
                    f"${summary['current_capital'] - summary['initial_capital']:+,.2f}"
                )
            
            with col2:
                st.metric(
                    "Total Return", 
                    f"{summary['total_return_pct']:+.1f}%"
                )
            
            with col3:
                st.metric(
                    "Cycles Completed", 
                    summary['total_cycles']
                )
            
            with col4:
                st.metric(
                    "Win Rate", 
                    f"{summary['win_rate']:.1f}%"
                )
            
            # Progress towards million
            st.subheader("🎯 Progress to $1,000,000")
            
            progress = min(summary['current_capital'] / 1000000, 1.0)
            st.progress(progress)
            
            remaining = 1000000 - summary['current_capital']
            if remaining > 0:
                st.write(f"**${remaining:,.2f}** remaining to reach $1M target")
                
                if summary['estimated_cycles_to_million'] != float('inf'):
                    estimated_time = summary['estimated_cycles_to_million'] * cycle_delay
                    st.write(f"**Estimated time to $1M:** {estimated_time/60:.1f} hours ({summary['estimated_cycles_to_million']:.0f} cycles)")
            else:
                st.success("🎉 **CONGRATULATIONS! You've reached $1,000,000!** 🎉")
            
            # Capital growth chart
            st.subheader("📈 Capital Growth")
            
            if len(summary['cascade_history']) > 0:
                # Prepare data for chart
                chart_data = []
                for i, cycle in enumerate(summary['cascade_history']):
                    chart_data.append({
                        'Cycle': i + 1,
                        'Capital': cycle['ending_capital'],
                        'P&L': cycle['total_pnl'],
                        'Return %': cycle['return_pct']
                    })
                
                df = pd.DataFrame(chart_data)
                
                # Create dual-axis chart
                fig = go.Figure()
                
                # Capital line
                fig.add_trace(go.Scatter(
                    x=df['Cycle'],
                    y=df['Capital'],
                    mode='lines+markers',
                    name='Capital',
                    line=dict(color='green', width=3),
                    yaxis='y'
                ))
                
                # P&L bars
                colors = ['green' if pnl >= 0 else 'red' for pnl in df['P&L']]
                fig.add_trace(go.Bar(
                    x=df['Cycle'],
                    y=df['P&L'],
                    name='P&L per Cycle',
                    marker_color=colors,
                    yaxis='y2',
                    opacity=0.7
                ))
                
                fig.update_layout(
                    title="Capital Growth & P&L by Cycle",
                    xaxis_title="Cycle Number",
                    yaxis=dict(title="Capital ($)", side="left"),
                    yaxis2=dict(title="P&L ($)", side="right", overlaying="y"),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Recent trades table
                st.subheader("🔍 Recent Trades")
                
                if summary['cascade_history']:
                    latest_cycle = summary['cascade_history'][-1]
                    trades_data = []
                    
                    for trade in latest_cycle['trades']:
                        trades_data.append({
                            'Symbol': trade['symbol'],
                            'Position Size': f"${trade['position_size']:.2f}",
                            'Return': f"{trade['return_pct']:+.1f}%",
                            'P&L': f"${trade['pnl']:+.2f}",
                            'Result': "✅ Win" if trade['success'] else "❌ Loss"
                        })
                    
                    if trades_data:
                        st.dataframe(pd.DataFrame(trades_data), use_container_width=True)
        
        else:
            st.info("No cascade cycles completed yet. Click 'Single Cycle' to start!")
    
    else:
        st.info("Initialize the cascade system by clicking 'Start Cascade' or 'Single Cycle'")
    
    # Educational section
    with st.expander("📚 How Domino Cascade Works"):
        st.markdown("""
        ### The Domino Cascade Strategy
        
        **Concept:** Start small and let profits compound through automated reinvestment.
        
        **How it works:**
        1. **Initial Investment:** Start with your chosen amount (e.g., $100)
        2. **Smart Allocation:** AI analyzes market opportunities and allocates capital
        3. **Risk Management:** Position sizing based on confidence and risk levels
        4. **Profit Reinvestment:** Successful trades increase available capital
        5. **Cascade Effect:** Each cycle has more capital to work with
        
        **Key Features:**
        - 🤖 **Automated Trading:** AI-driven signal generation
        - 📊 **Progressive Allocation:** Higher confidence trades get more capital
        - 🛡️ **Risk Management:** Built-in stop-losses and position sizing
        - 🔄 **Compounding Effect:** Profits reinvested for exponential growth
        - 📈 **Performance Tracking:** Detailed analytics and reporting
        
        **Risk Warning:** Cryptocurrency trading involves significant risk. Past performance does not guarantee future results.
        """)
    
    # Performance simulation
    with st.expander("🎯 Performance Simulation"):
        st.subheader("Simulate Cascade Performance")
        
        sim_col1, sim_col2 = st.columns(2)
        
        with sim_col1:
            sim_capital = st.number_input("Simulation Capital", 50.0, 10000.0, 100.0, 50.0)
            sim_cycles = st.number_input("Simulation Cycles", 1, 50, 10, 1)
        
        with sim_col2:
            avg_return = st.slider("Average Return per Cycle (%)", 1.0, 20.0, 8.0, 0.5)
            win_rate = st.slider("Win Rate (%)", 50.0, 90.0, 70.0, 5.0)
        
        if st.button("Run Simulation"):
            # Simple Monte Carlo simulation
            results = []
            current = sim_capital
            
            for cycle in range(sim_cycles):
                # Simulate trade outcome
                if np.random.random() < (win_rate / 100):
                    # Win scenario
                    return_pct = np.random.normal(avg_return, avg_return * 0.3) / 100
                else:
                    # Loss scenario  
                    return_pct = -np.random.normal(avg_return * 0.5, avg_return * 0.2) / 100
                
                current *= (1 + return_pct)
                results.append(current)
            
            # Display results
            final_value = results[-1]
            total_return = (final_value / sim_capital - 1) * 100
            
            st.success(f"**Simulation Results:**")
            st.write(f"Final Value: ${final_value:,.2f}")
            st.write(f"Total Return: {total_return:+.1f}%")
            
            # Simple projection chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(1, sim_cycles + 1)),
                y=results,
                mode='lines+markers',
                name='Simulated Capital'
            ))
            fig.update_layout(
                title="Simulated Capital Growth",
                xaxis_title="Cycle",
                yaxis_title="Capital ($)"
            )
            st.plotly_chart(fig, use_container_width=True)
