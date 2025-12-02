import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.title("Simple Fullstack Demo")

# Health check
try:
    r = requests.get(f"{BACKEND_URL}/health", timeout=2)
    st.success(f"Backend status: {r.json()}")
except Exception as e:
    st.error(f"Could not reach backend at {BACKEND_URL}: {e}")

st.header("Items")

name = st.text_input("New item name")

if st.button("Add item") and name:
    resp = requests.post(f"{BACKEND_URL}/items", json={"name": name})
    if resp.ok:
        st.success(f"Created item: {resp.json()}")
    else:
        st.error(f"Error: {resp.status_code} - {resp.text}")

if st.button("Refresh items"):
    pass  # just forces a rerun

# Always display current items
resp = requests.get(f"{BACKEND_URL}/items")
if resp.ok:
    items = resp.json()
    if items:
        st.write("Current items:")
        st.table(items)
    else:
        st.info("No items yet.")
else:
    st.error(f"Error fetching items: {resp.status_code} - {resp.text}")