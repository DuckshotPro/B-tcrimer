#!/usr/bin/env python3
"""
Vercel entry point for B-TCRimer Streamlit app
"""
import os
import sys
import subprocess

# Set environment variables for Streamlit
os.environ.setdefault('STREAMLIT_SERVER_PORT', '8501')
os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')
os.environ.setdefault('STREAMLIT_SERVER_ENABLE_CORS', 'false')
os.environ.setdefault('STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION', 'false')

def handler(request):
    """Vercel handler function"""
    # Start Streamlit app
    cmd = [sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.port', '8501', '--server.address', '0.0.0.0']
    
    # Run the Streamlit app
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
        },
        'body': 'Streamlit app is starting...'
    }

if __name__ == "__main__":
    # For local development
    import app