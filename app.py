
import streamlit as st
import pandas as pd
from pathlib import Path

from src.preprocessing import (
    create_daily_data,
    create_region_data,
    create_product_data,
    create_category_data
)

from src.anomaly_detector import (
    detect_overall_sales_drops,
    detect_overall_sales_spikes,
    detect_category_sales_spikes,
    detect_product_sales_spikes,
    detect_profit_margin_drops,
    detect_regional_sales_drops
)

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
    [
        "Overview",
        "Sales Analytics",
        "Anomaly Detection",
        "Alert History"
    ]
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



# Anomaly Detection page
elif page == "Anomaly Detection":
    st.subheader("Anomaly Detection")
    st.caption(
        "Identify unusual business activity using historical sales patterns."
    )

    with st.spinner("Analyzing business data..."):
        daily_data = create_daily_data(df)
        region_daily = create_region_data(df)
        product_daily = create_product_data(df)
        category_daily = create_category_data(df)

        _, sales_drops = detect_overall_sales_drops(daily_data)
        _, sales_spikes = detect_overall_sales_spikes(daily_data)
        _, category_spikes = detect_category_sales_spikes(category_daily)
        _, product_spikes = detect_product_sales_spikes(product_daily)
        _, margin_drops = detect_profit_margin_drops(category_daily)
        _, regional_drops = detect_regional_sales_drops(region_daily)

    events = []

    def add_events(data, anomaly_type, scope_column=None):
        for _, event in data.iterrows():
            row = {
                "Anomaly Type": anomaly_type,
                "Start Date": pd.to_datetime(event["Start_Date"]),
                "End Date": pd.to_datetime(event["End_Date"]),
                "Duration (days)": int(event["Duration"]),
                "Scope": (
                    str(event[scope_column])
                    if scope_column and scope_column in event.index
                    else "Overall Business"
                )
            }

            if "Avg_Sales_Change" in event.index:
                row["Sales Change (%)"] = round(
                    event["Avg_Sales_Change"], 1
                )

            if "Avg_Quantity_Change" in event.index:
                row["Quantity Change (%)"] = round(
                    event["Avg_Quantity_Change"], 1
                )

            if "Avg_Margin_Drop_pp" in event.index:
                row["Margin Drop (pp)"] = round(
                    event["Avg_Margin_Drop_pp"], 1
                )

            events.append(row)

    add_events(sales_drops, "Overall Sales Drop")
    add_events(sales_spikes, "Overall Sales Spike")
    add_events(category_spikes, "Category Sales Spike", "Category")
    add_events(product_spikes, "Product Sales Spike", "Product_Name")
    add_events(margin_drops, "Profit Margin Drop", "Category")
    add_events(regional_drops, "Regional Sales Drop", "Region")

    if not events:
        st.success("No anomalies were detected with the current rules.")
    else:
        results = pd.DataFrame(events).sort_values(
            "Start Date", ascending=False
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Detected Events", len(results))

        with col2:
            st.metric(
                "Anomaly Types",
                results["Anomaly Type"].nunique()
            )

        st.divider()

        anomaly_types = ["All"] + sorted(
            results["Anomaly Type"].unique().tolist()
        )

        selected_anomaly = st.selectbox(
            "Filter by anomaly type",
            anomaly_types
        )

        filtered_results = results.copy()

        if selected_anomaly != "All":
            filtered_results = filtered_results[
                filtered_results["Anomaly Type"] == selected_anomaly
            ]

        st.caption(f"Showing {len(filtered_results)} detected event(s)")

        st.dataframe(
            filtered_results,
            use_container_width=True,
            hide_index=True
        )

        with st.expander("How does anomaly detection work?"):
            st.write(
                "The monitor compares business metrics with historical "
                "baselines and applies the detection rules defined in "
                "the anomaly detector module. Detected events are "
                "candidates for investigation, not proof of a business problem."
            )


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
