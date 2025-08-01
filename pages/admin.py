import streamlit as st
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="admin_autorefresh")

# File paths
ORDERS_FILE = os.path.join(os.path.dirname(_file_), "..", "orders.json")
MENU_FILE = os.path.join(os.path.dirname(_file_), "..", "menu.json")

# Page settings
st.set_page_config(page_title="Admin Panel", layout="wide")
st.markdown("""
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
        }
        .order-card {
            background: #ffffff10;
            padding: 1.2rem;
            border-radius: 15px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.1);
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

# Load JSON safely
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

# Track new orders
if "order_count" not in st.session_state:
    st.session_state.order_count = len(orders)

if len(orders) > st.session_state.order_count:
    toast("📦 New order received!")
    st.session_state.order_count = len(orders)

status_flow = ["Pending", "Preparing", "Ready", "Completed"]

# Display each order
if not orders:
    st.info("📭 No orders yet.")
else:
    for idx, order in reversed(list(enumerate(orders))):
        table = order.get("table", "?")
        timestamp = order.get("timestamp", "N/A")
        status = order.get("status", "Pending")
        items = order.get("items", {})

        with st.container():
            st.markdown(f"<div class='order-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='order-header'>🪑 Table {table} <span class='status {status}'>{status}</span></div>", unsafe_allow_html=True)
            st.caption(f"🕒 {timestamp}")
            st.markdown("#### 🧾 Ordered Items")

            total = 0
            for name, details in items.items():
                qty = details.get("quantity", 0)
                price = details.get("price", 0)
                subtotal = price * qty
                total += subtotal
                st.markdown(f"<div class='item-line'>🍽️ {name} x {qty} = ₹{subtotal}</div>", unsafe_allow_html=True)

            st.markdown(f"*💰 Total: ₹{total}*")

            st.markdown("---")
            new_status = st.selectbox("Change Status", [status] + [s for s in status_flow if s != status], key=f"status_{idx}")
            if new_status != status and st.button("✅ Update", key=f"update_{idx}"):
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

# Feedback Viewer Section
FEEDBACK_FILE = os.path.join(os.path.dirname(_file_), "..", "feedback.json")
feedbacks = load_json(FEEDBACK_FILE, [])

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
            <div style='padding:1rem; margin-bottom:1rem; background:#1f2937; border-radius:10px; color:white;'>
                <strong>🪑 Table {table}</strong>  
                <div style='font-size: 0.9rem; color: #9ca3af;'>🕒 {timestamp}</div>
                <div style='margin-top: 0.5rem;'>{message}</div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Delete Feedback", key=f"del_feedback_{i}"):
            feedbacks.pop(len(feedbacks) - 1 - i)  # Correct reverse index
            save_json(FEEDBACK_FILE, feedbacks)
            toast("🗑️ Feedback deleted")
            st.rerun()
