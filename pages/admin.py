import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="admin_autorefresh")

# File paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ORDERS_FILE = os.path.join(BASE_DIR, "orders.json")
MENU_FILE = os.path.join(BASE_DIR, "menu.json")
FEEDBACK_FILE = os.path.join(BASE_DIR, "feedback.json")

# Page settings
st.set_page_config(page_title="Admin Panel", layout="wide")
st.markdown("""
    <style>
        body {
            background: linear-gradient(to right, #1e3c72, #2a5298);
            font-family: 'Segoe UI', sans-serif;
        }
        .order-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 1.2rem;
            border-radius: 15px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.2);
            margin-bottom: 2rem;
            color: #fff;
        }
        .order-header {
            font-size: 1.3rem;
            font-weight: bold;
        }
        .status {
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 8px;
        }
        .Pending { background: #facc15; color: #000; }
        .Preparing { background: #3b82f6; }
        .Ready { background: #10b981; }
        .Completed { background: #a3a3a3; }
        .Cancelled { background: #ef4444; }
        .item-line {
            margin-left: 10px;
        }
        button:hover {
            transform: scale(1.03);
            transition: 0.2s ease-in-out;
        }
        button:active {
            transform: scale(0.98);
        }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ Admin Panel - Order Management")

# Toast function
def toast(message: str, duration=3000):
    st.markdown(f"""
        <script>
        const toast = document.createElement("div");
        toast.textContent = "{message}";
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #323232;
            color: white;
            padding: 12px 24px;
            border-radius: 10px;
            font-size: 15px;
            z-index: 9999;
            animation: fadein 0.3s, fadeout 0.3s ease {duration / 1000 - 0.3}s;
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), {duration});
        </script>
    """, unsafe_allow_html=True)

# Load/save JSON
def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# Load data
menu = load_json(MENU_FILE, {})
orders = load_json(ORDERS_FILE, [])
feedbacks = load_json(FEEDBACK_FILE, [])

# Floating alert for pending orders
pending_count = sum(1 for o in orders if o['status'] == 'Pending')
if pending_count:
    st.markdown(f"""
    <div style="position:fixed; top:20px; right:20px; z-index:1000;">
        <div style="background:#ef4444; color:white; padding:10px 20px; border-radius:20px;">
            🔔 {pending_count} Pending Orders
        </div>
    </div>
    """, unsafe_allow_html=True)

# Status progress bar
def status_progress(current_status):
    steps = ["Pending", "Preparing", "Ready", "Completed"]
    index = steps.index(current_status) if current_status in steps else 0
    st.markdown(
        f"""
        <div style="display: flex; gap: 10px; margin-bottom: 10px;">
            {"".join([
                f"<div style='flex:1; padding:5px 10px; background:{'#10b981' if i<=index else '#6b7280'}; color:white; text-align:center; border-radius:5px'>{step}</div>"
                for i, step in enumerate(steps)
            ])}
        </div>
        """, unsafe_allow_html=True
    )

# Filtering and sorting
sort_option = st.selectbox("📊 Sort orders by:", ["Newest", "Oldest", "Pending First", "Completed First"])
table_filter = st.text_input("🔍 Filter by Table Number")

if table_filter:
    orders = [o for o in orders if o.get("table") == table_filter]

if sort_option == "Pending First":
    orders.sort(key=lambda x: x["status"] != "Pending")
elif sort_option == "Completed First":
    orders.sort(key=lambda x: x["status"] != "Completed")
elif sort_option == "Oldest":
    orders = sorted(orders, key=lambda x: x["timestamp"])
else:
    orders = sorted(orders, key=lambda x: x["timestamp"], reverse=True)

# Display orders
if not orders:
    st.info("📭 No orders yet.")
else:
    for idx, order in reversed(list(enumerate(orders))):
        table = order.get("table", "?")
        timestamp = order.get("timestamp", "N/A")
        status = order.get("status", "Pending")
        items = order.get("items", {})

        st.markdown(f"<div class='order-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='order-header'>🪑 Table {table} <span class='status {status}'>{status}</span></div>", unsafe_allow_html=True)
        st.caption(f"🕒 {timestamp}")
        status_progress(status)
        st.markdown("#### 🧾 Ordered Items")

        total = 0
        for name, details in items.items():
            qty = details.get("quantity", 0)
            price = details.get("price", 0)
            subtotal = price * qty
            total += subtotal
            st.markdown(f"<div class='item-line'>🍽️ {name} x {qty} = ₹{subtotal}</div>", unsafe_allow_html=True)

        st.markdown(f"**💰 Total: ₹{total}**")

        st.markdown("---")
        new_status = st.selectbox("Change Status", [status] + [s for s in ["Pending", "Preparing", "Ready", "Completed"] if s != status], key=f"status_{idx}")
        if new_status != status and st.button("✅ Update", key=f"update_{idx}"):
            with st.spinner("🔄 Updating..."):
                orders[idx]["status"] = new_status
                save_json(ORDERS_FILE, orders)
                toast(f"✅ Status changed to {new_status}")
                st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Cancel Order", key=f"cancel_{idx}"):
                orders[idx]["status"] = "Cancelled"
                save_json(ORDERS_FILE, orders)
                toast("❌ Order cancelled")
                st.rerun()
        with col2:
            if status == "Completed" and st.button("🗑️ Delete", key=f"delete_{idx}"):
                orders.pop(idx)
                save_json(ORDERS_FILE, orders)
                toast("🗑️ Order deleted")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# CSV Report
if st.button("📥 Download Daily Report (CSV)"):
    df = pd.DataFrame([{
        "Table": o["table"],
        "Time": o["timestamp"],
        "Status": o["status"],
        "Total": sum(item["price"] * item["quantity"] for item in o["items"].values())
    } for o in orders])
    st.download_button("📄 Download CSV", df.to_csv(index=False), "orders_report.csv", "text/csv")

# Feedback Viewer
st.markdown("---")
st.subheader("📝 Customer Feedback")

if not feedbacks:
    st.info("No feedback received yet.")
else:
    for i, fb in enumerate(reversed(feedbacks)):
        table = fb.get("table", "Unknown")
        message = fb.get("message", "No message")
        timestamp = fb.get("timestamp", "Unknown")

        st.markdown(f"""
            <div style='padding:1rem; background:#f59e0b20; border-left: 5px solid #f59e0b; margin-bottom:1rem; border-radius:8px; color:white;'>
                <strong>🪑 Table {table}</strong><br>
                <div style='font-size: 0.9rem; color: #9ca3af;'>🕒 {timestamp}</div>
                <div style='margin-top: 0.5rem;'>{message}</div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Delete Feedback", key=f"del_feedback_{i}"):
            feedbacks.pop(len(feedbacks) - 1 - i)
            save_json(FEEDBACK_FILE, feedbacks)
            toast("🗑️ Feedback deleted")
            st.rerun()