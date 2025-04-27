import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

from utils.logging_config import get_logger, get_recent_logs, get_error_logs, get_log_statistics
from database.operations import get_db_connection

logger = get_logger(__name__)

def show():
    """Display the system logs page"""
    st.title("System Logs")
    
    try:
        # Sidebar options
        st.sidebar.header("Log Options")
        log_level = st.sidebar.selectbox(
            "Log Level",
            ["All", "INFO", "WARNING", "ERROR", "DEBUG"]
        )
        
        log_limit = st.sidebar.slider(
            "Number of logs to display",
            min_value=10,
            max_value=200,
            value=50,
            step=10
        )
        
        days_back = st.sidebar.slider(
            "Statistics for past days",
            min_value=1,
            max_value=30,
            value=7,
            step=1
        )
        
        # Create tabs for different log views
        tabs = st.tabs(["Log Overview", "Recent Logs", "Error Logs", "Log Search"])
        
        # Log overview tab
        with tabs[0]:
            show_log_overview(days_back)
        
        # Recent logs tab
        with tabs[1]:
            show_recent_logs(log_level, log_limit)
        
        # Error logs tab
        with tabs[2]:
            show_error_logs()
        
        # Log search tab
        with tabs[3]:
            show_log_search()
    
    except Exception as e:
        logger.error(f"Error displaying logs page: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

def show_log_overview(days_back):
    """Show log statistics and overview"""
    st.header("Log Overview")
    
    # Get log statistics
    stats = get_log_statistics(days=days_back)
    
    if not stats['level_counts']:
        st.info("No log data available for the selected time period.")
        return
    
    # Display log level distribution
    st.subheader("Log Level Distribution")
    
    # Create level distribution chart
    level_data = pd.DataFrame({
        "Log Level": list(stats['level_counts'].keys()),
        "Count": list(stats['level_counts'].values())
    })
    
    level_fig = px.bar(
        level_data,
        x="Log Level",
        y="Count",
        color="Log Level",
        color_discrete_map={
            "INFO": "blue",
            "WARNING": "orange",
            "ERROR": "red",
            "DEBUG": "green",
            "CRITICAL": "purple"
        },
        title=f"Log Level Distribution (Past {days_back} Days)"
    )
    
    st.plotly_chart(level_fig, use_container_width=True)
    
    # Display daily log counts
    st.subheader("Daily Log Activity")
    
    if stats['daily_counts']:
        # Prepare data for daily chart
        daily_data = []
        
        for day, level_counts in stats['daily_counts'].items():
            for level, count in level_counts.items():
                daily_data.append({
                    "Day": day,
                    "Log Level": level,
                    "Count": count
                })
        
        daily_df = pd.DataFrame(daily_data)
        
        if not daily_df.empty:
            # Sort days
            daily_df['Day'] = pd.to_datetime(daily_df['Day'])
            daily_df = daily_df.sort_values('Day')
            daily_df['Day'] = daily_df['Day'].dt.strftime('%Y-%m-%d')
            
            daily_fig = px.bar(
                daily_df,
                x="Day",
                y="Count",
                color="Log Level",
                color_discrete_map={
                    "INFO": "blue",
                    "WARNING": "orange",
                    "ERROR": "red",
                    "DEBUG": "green",
                    "CRITICAL": "purple"
                },
                title="Daily Log Activity by Level"
            )
            
            st.plotly_chart(daily_fig, use_container_width=True)
    else:
        st.info("No daily log data available.")
    
    # Display recent errors
    if stats['recent_errors']:
        st.subheader("Recent Errors")
        
        for error in stats['recent_errors']:
            timestamp = error['timestamp']
            if isinstance(timestamp, str):
                timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            
            formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            st.markdown(f"""
            <div style="padding: 10px; border-radius: 5px; background-color: rgba(255, 0, 0, 0.1); margin-bottom: 10px;">
                <b>Time:</b> {formatted_time}<br>
                <b>Module:</b> {error['module']}<br>
                <b>Error:</b> {error['message']}
            </div>
            """, unsafe_allow_html=True)
    
    # System health indicators
    st.subheader("System Health")
    
    # Calculate error rate
    total_logs = sum(stats['level_counts'].values())
    error_count = stats['level_counts'].get('ERROR', 0)
    error_rate = (error_count / total_logs) * 100 if total_logs > 0 else 0
    
    # Database stats
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA page_count")
    page_count = cursor.fetchone()[0]
    
    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]
    
    database_size_mb = (page_count * page_size) / (1024 * 1024)
    
    # Get table row counts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    table_counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        table_counts[table] = cursor.fetchone()[0]
    
    conn.close()
    
    # Display health metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Error Rate", 
            f"{error_rate:.2f}%",
            delta=None,
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            "Total Logs", 
            f"{total_logs:,}"
        )
    
    with col3:
        st.metric(
            "Database Size", 
            f"{database_size_mb:.2f} MB"
        )
    
    # Display table row counts
    st.subheader("Database Statistics")
    
    # Create table counts chart
    table_data = pd.DataFrame({
        "Table": list(table_counts.keys()),
        "Row Count": list(table_counts.values())
    })
    
    table_fig = px.bar(
        table_data,
        x="Table",
        y="Row Count",
        title="Database Table Row Counts"
    )
    
    st.plotly_chart(table_fig, use_container_width=True)

def show_recent_logs(level, limit):
    """Show recent logs with filtering options"""
    st.header("Recent Logs")
    
    # Get logs based on selected level
    if level == "All":
        logs = get_recent_logs(limit=limit)
    else:
        logs = get_recent_logs(level=level, limit=limit)
    
    if not logs:
        st.info(f"No {level} logs found.")
        return
    
    # Display logs
    for log in logs:
        # Format timestamp
        timestamp = log['timestamp']
        if isinstance(timestamp, str):
            timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        # Determine log level color
        if log['level'] == 'ERROR':
            level_color = 'red'
        elif log['level'] == 'WARNING':
            level_color = 'orange'
        elif log['level'] == 'INFO':
            level_color = 'blue'
        elif log['level'] == 'DEBUG':
            level_color = 'green'
        else:
            level_color = 'gray'
        
        # Create log entry display
        st.markdown(f"""
        <div style="padding: 10px; border-radius: 5px; background-color: rgba(0, 0, 0, 0.05); margin-bottom: 5px;">
            <span style="color: {level_color}; font-weight: bold;">{log['level']}</span> | 
            <span style="color: gray;">{formatted_time}</span> | 
            <span style="color: navy;">{log['module']}</span><br>
            <span>{log['message']}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Show details if available
        if log['details']:
            with st.expander("Details"):
                st.code(log['details'])

def show_error_logs():
    """Show only error logs"""
    st.header("Error Logs")
    
    # Get error logs
    error_logs = get_error_logs(limit=100)
    
    if not error_logs:
        st.success("No errors found! System is running smoothly.")
        return
    
    # Group errors by module
    module_errors = {}
    for log in error_logs:
        module = log['module']
        if module not in module_errors:
            module_errors[module] = []
        module_errors[module].append(log)
    
    # Display errors by module
    for module, logs in module_errors.items():
        with st.expander(f"{module} ({len(logs)} errors)"):
            for log in logs:
                # Format timestamp
                timestamp = log['timestamp']
                if isinstance(timestamp, str):
                    timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                
                formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
                st.markdown(f"""
                <div style="padding: 10px; border-radius: 5px; background-color: rgba(255, 0, 0, 0.1); margin-bottom: 10px;">
                    <b>Time:</b> {formatted_time}<br>
                    <b>Error:</b> {log['message']}
                </div>
                """, unsafe_allow_html=True)
                
                # Show details if available
                if log['details']:
                    with st.expander("Stack Trace"):
                        st.code(log['details'])

def show_log_search():
    """Show log search interface"""
    st.header("Log Search")
    
    # Search form
    search_query = st.text_input("Search logs", placeholder="Enter keywords to search...")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start date",
            value=datetime.datetime.now() - datetime.timedelta(days=7)
        )
    
    with col2:
        end_date = st.date_input(
            "End date",
            value=datetime.datetime.now()
        )
    
    search_level = st.multiselect(
        "Log levels",
        ["INFO", "WARNING", "ERROR", "DEBUG"],
        default=["INFO", "WARNING", "ERROR"]
    )
    
    search_module = st.text_input("Module name", placeholder="Leave empty for all modules")
    
    if st.button("Search Logs"):
        if search_query or search_level or search_module:
            search_results = search_logs(
                query=search_query,
                start_date=start_date,
                end_date=end_date,
                levels=search_level,
                module=search_module
            )
            
            if search_results:
                st.success(f"Found {len(search_results)} matching log entries")
                display_search_results(search_results)
            else:
                st.info("No logs found matching your search criteria.")
        else:
            st.warning("Please enter at least one search term.")

def search_logs(query, start_date, end_date, levels, module=None):
    """Search logs based on criteria"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build search query
        sql_query = """
            SELECT timestamp, level, module, message, details
            FROM logs
            WHERE date(timestamp) >= ? AND date(timestamp) <= ?
        """
        
        params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
        
        if levels:
            placeholders = ','.join(['?' for _ in levels])
            sql_query += f" AND level IN ({placeholders})"
            params.extend(levels)
        
        if module:
            sql_query += " AND module LIKE ?"
            params.append(f"%{module}%")
        
        if query:
            sql_query += " AND (message LIKE ? OR details LIKE ?)"
            params.append(f"%{query}%")
            params.append(f"%{query}%")
        
        sql_query += " ORDER BY timestamp DESC LIMIT 200"
        
        cursor.execute(sql_query, params)
        results = cursor.fetchall()
        conn.close()
        
        # Format results
        formatted_results = []
        for row in results:
            timestamp, level, module, message, details = row
            formatted_results.append({
                'timestamp': timestamp,
                'level': level,
                'module': module,
                'message': message,
                'details': details
            })
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error searching logs: {str(e)}", exc_info=True)
        st.error(f"Error searching logs: {str(e)}")
        return []

def display_search_results(results):
    """Display log search results"""
    # Group results by day
    results_by_day = {}
    
    for log in results:
        # Format timestamp
        timestamp = log['timestamp']
        if isinstance(timestamp, str):
            timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        day = timestamp.strftime('%Y-%m-%d')
        
        if day not in results_by_day:
            results_by_day[day] = []
        
        results_by_day[day].append(log)
    
    # Display results by day
    for day, day_logs in sorted(results_by_day.items(), reverse=True):
        with st.expander(f"{day} ({len(day_logs)} logs)", expanded=True if len(results_by_day) <= 3 else False):
            for log in day_logs:
                # Format timestamp
                timestamp = log['timestamp']
                if isinstance(timestamp, str):
                    timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                
                formatted_time = timestamp.strftime('%H:%M:%S')
                
                # Determine log level color
                if log['level'] == 'ERROR':
                    level_color = 'red'
                elif log['level'] == 'WARNING':
                    level_color = 'orange'
                elif log['level'] == 'INFO':
                    level_color = 'blue'
                elif log['level'] == 'DEBUG':
                    level_color = 'green'
                else:
                    level_color = 'gray'
                
                # Create log entry display
                st.markdown(f"""
                <div style="padding: 10px; border-radius: 5px; background-color: rgba(0, 0, 0, 0.05); margin-bottom: 5px;">
                    <span style="color: {level_color}; font-weight: bold;">{log['level']}</span> | 
                    <span style="color: gray;">{formatted_time}</span> | 
                    <span style="color: navy;">{log['module']}</span><br>
                    <span>{log['message']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Show details if available
                if log['details']:
                    with st.expander("Details"):
                        st.code(log['details'])
