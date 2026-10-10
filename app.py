
import streamlit as st
import pandas as pd
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Business Metrics Monitor",
    page_icon="📊",
    layout="wide"
)

# Dashboard styling
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.08);
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📊 Business Metrics Anomaly Monitor")
st.caption(
    "Monitor business performance, investigate anomalies, "
    "and review automated alerts."
)

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Overview", "Sales Analytics", "Alert History"]
)

# Load transaction data
DATA_PATH = (
    Path(__file__).parent
    / "data"
    / "ecommerce_business_monitoring_dataset.xlsx"
)

@st.cache_data
def load_transactions(path):
    return pd.read_excel(path, sheet_name="Transactions")

try:
    df = load_transactions(DATA_PATH)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce")
    df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")

    df = df.dropna(subset=["Date", "Sales", "Profit", "Quantity"])

except Exception as error:
    st.error(f"Could not load transaction data: {error}")
    st.stop()

# Overview page
if page == "Overview":
    st.subheader("Business Overview")

    total_sales = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    total_orders = df["Order_ID"].nunique()
    total_units = df["Quantity"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Sales", f"₹{total_sales:,.0f}")
    col2.metric("Total Profit", f"₹{total_profit:,.0f}")
    col3.metric("Total Orders", f"{total_orders:,}")
    col4.metric("Units Sold", f"{total_units:,.0f}")

    st.divider()

    daily_sales = (
        df.groupby("Date", as_index=False)["Sales"]
        .sum()
        .sort_values("Date")
    )

    st.subheader("Daily Sales Trend")
    st.line_chart(
        daily_sales.set_index("Date")["Sales"],
        x_label="Date",
        y_label="Sales (₹)"
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Sales by Category")
        category_sales = (
            df.groupby("Category")["Sales"]
            .sum()
            .sort_values(ascending=False)
        )
        st.bar_chart(category_sales, horizontal=True)

    with right:
        st.subheader("Sales by Region")
        region_sales = (
            df.groupby("Region")["Sales"]
            .sum()
            .sort_values(ascending=False)
        )
        st.bar_chart(region_sales)

# Sales Analytics page
elif page == "Sales Analytics":
    st.subheader("Sales Analytics")

    categories = ["All"] + sorted(
        df["Category"].dropna().unique().tolist()
    )
    selected_category = st.selectbox("Select Category", categories)

    filtered_df = df.copy()

    if selected_category != "All":
        filtered_df = filtered_df[
            filtered_df["Category"] == selected_category
        ]

    daily = (
        filtered_df.groupby("Date", as_index=False)
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum"),
            Quantity=("Quantity", "sum")
        )
        .sort_values("Date")
    )

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Sales", f"₹{filtered_df['Sales'].sum():,.0f}")
    metric2.metric("Profit", f"₹{filtered_df['Profit'].sum():,.0f}")
    metric3.metric("Units Sold", f"{filtered_df['Quantity'].sum():,.0f}")

    st.subheader("Sales Over Time")
    st.line_chart(daily.set_index("Date")["Sales"])

    st.subheader("Profit Over Time")
    st.line_chart(daily.set_index("Date")["Profit"])

    with st.expander("View transaction data"):
        st.dataframe(filtered_df, use_container_width=True)

# Alert History page

elif page == "Alert History":
    st.subheader("Alert History")

    DB_PATH = Path(__file__).parent / "alert_history.db"

    if not DB_PATH.exists():
        st.info("No alert history database found yet. Run the monitoring pipeline first.")
    else:
        try:
            import sqlite3

            with sqlite3.connect(DB_PATH) as connection:
                tables = pd.read_sql_query(
                    "SELECT name FROM sqlite_master WHERE type='table'",
                    connection
                )["name"].tolist()

                if not tables:
                    st.info("The alert history database has no tables yet.")
                else:
                    history = pd.read_sql_query(
                        f'SELECT * FROM "{tables[0]}"',
                        connection
                    )

                    if history.empty:
                        st.info("No alerts recorded yet.")
                    else:
                        # Normalize column names for display
                        history.columns = [
                            column.replace("_", " ").title()
                            for column in history.columns
                        ]

                        st.metric("Total Recorded Alerts", len(history))

                        if "Alert Type" in history.columns:
                            alert_types = ["All"] + sorted(
                                history["Alert Type"].dropna().unique().tolist()
                            )
                            selected_type = st.selectbox(
                                "Filter by alert type",
                                alert_types
                            )

                            if selected_type != "All":
                                history = history[
                                    history["Alert Type"] == selected_type
                                ]

                        st.caption(f"Showing {len(history)} alert(s)")

                        for _, alert in history.iloc[::-1].iterrows():
                            alert_type = alert.get("Alert Type", "Alert")
                            start_date = str(alert.get("Start Date", "N/A"))[:10]
                            end_date = str(alert.get("End Date", "N/A"))[:10]
                            status = alert.get("Status", "Unknown")
                            summary = str(alert.get("Summary", "No summary available"))

                            with st.expander(
                                f"{alert_type} | {start_date} to {end_date}"
                            ):
                                st.write(f"**Status:** {status}")
                                st.write(f"**Alert ID:** {alert.get('Id', 'N/A')}")

                                st.markdown("**Business Summary**")
                                st.text(summary.replace("\\n", "\n"))

        except Exception as error:
            st.error(f"Could not read alert history: {error}")
