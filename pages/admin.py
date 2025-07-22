import streamlit as st
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Debug: show file paths
st.markdown(f"**Current file:** `{__file__}`")
st.markdown(f"**Absolute path:** `{os.path.abspath(__file__)}`")

# Resolve project root (e.g. if this file is in /pages)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MENU_FILE = os.path.join(ROOT_DIR, "menu.json")
ORDERS_FILE = os.path.join(ROOT_DIR, "orders.json")

st.markdown(f"**Menu file path:** `{MENU_FILE}`")
st.markdown(f"**Orders file path:** `{ORDERS_FILE}`")

# Load menu
if os.path.exists(MENU_FILE):
    with open(MENU_FILE, "r") as f:
        menu = json.load(f)
else:
    st.error(f"❌ Menu file not found at {MENU_FILE}")
    st.stop()

# Load orders
if os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)
else:
    orders = []

# Auto-refresh
st_autorefresh(interval=5000, key="admin_autorefresh")

st.title("🛠️ Admin Panel - Order Management")
st.subheader("📦 All Orders")
changed = False

for idx, order in reversed(list(enumerate(orders))):
    st.markdown(f"### Table {order['table']} — {order['status']} — 🕒 {order['timestamp']}")
    for name, item in order["items"].items():
        st.markdown(f"- {name} x {item['quantity']} = ₹{item['price'] * item['quantity']}")

    col1, col2, col3 = st.columns(3)
    with col1:
        if order["status"] == "Pending" and st.button("👨‍🍳 Mark Preparing", key=f"prep-{idx}"):
            orders[idx]["status"] = "Preparing"
            changed = True
    with col2:
        if order["status"] == "Preparing" and st.button("✅ Complete", key=f"comp-{idx}"):
            orders[idx]["status"] = "Completed"
            changed = True
    with col3:
        if order["status"] not in ["Completed", "Cancelled"] and st.button("❌ Cancel", key=f"cancel-{idx}"):
            orders[idx]["status"] = "Cancelled"
            changed = True
    st.markdown("---")

if changed:
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)
    st.success("✅ Order status updated.")
    st.rerun()
