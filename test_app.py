import streamlit as st

st.title("Test Application")
st.write("This is a simple test application without database dependencies.")

st.header("Static Content")
st.write("If you can see this text, the basic Streamlit functionality is working correctly.")

# Simple widgets
st.subheader("Interactive Elements")
name = st.text_input("Enter your name")
if name:
    st.write(f"Hello, {name}!")

option = st.selectbox("Choose an option", ["Option 1", "Option 2", "Option 3"])
st.write(f"You selected: {option}")

st.subheader("Data Display")
import pandas as pd
import numpy as np

# Create some test data
df = pd.DataFrame({
    'Date': pd.date_range(start='2023-01-01', periods=10),
    'Value': np.random.randn(10).cumsum()
})

st.dataframe(df)
st.line_chart(df.set_index('Date'))

st.success("Test app loaded successfully!")