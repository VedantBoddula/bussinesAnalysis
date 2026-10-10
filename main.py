from pathlib import Path 
import pandas as pd

from src.data_loader import load_data
from src.preprocessing import (
    create_daily_data,
    create_region_data,
    create_product_data,
    create_category_data
    
)
from src.anomaly_detector import (
    detect_overall_sales_drops,
    detect_overall_sales_spikes,
    detect_category_sales_spikes
)
from src.explainer import explain_event
from src.summary_generator import (
    generate_summary,
    generate_category_spike_summary,
)
from src.alert_history import initialize_alert_history, send_alert_once



# -------------------------
# 1. Load data
# -------------------------

BASE_DIR = Path(__file__).resolve().parent
initialize_alert_history()

file_path = (
    BASE_DIR
    / "data"
    / "ecommerce_business_monitoring_dataset.xlsx"
)

data = load_data(file_path)

print("Data loaded successfully!")
print("Rows:", len(data))

ground_truth = pd.read_excel(
    file_path,
    sheet_name="Ground_Truth"
)

print("\nGround Truth:")
print(ground_truth.to_string(index=False))


# -------------------------
# 2. Prepare datasets
# -------------------------

daily_data = create_daily_data(data)
region_daily = create_region_data(data)
product_daily = create_product_data(data)
category_daily = create_category_data(data)


print("Daily data:", daily_data.shape)
print("Region data:", region_daily.shape)
print("Product data:", product_daily.shape)
print("Category data:", category_daily.shape)


# -------------------------
# 3. Detect anomalies
# -------------------------

daily_data, candidate_events = (
    detect_overall_sales_drops(daily_data)
)

daily_data, candidate_spikes = (
    detect_overall_sales_spikes(daily_data)
)

category_daily, category_spikes = (
    detect_category_sales_spikes(category_daily)
)

print("\nCategory-level spike candidates:")
print(category_spikes.to_string(index=False))


# Investigate the largest category spike

# -------------------------
# Investigate and summarize the largest category spike
# -------------------------

if not category_spikes.empty:

    top_spike = category_spikes.iloc[0]

    category_name = top_spike["Category"]
    start_date = top_spike["Start_Date"]
    end_date = top_spike["End_Date"]

    # Get daily records for the selected category and period
    event_data = category_daily.loc[
        (category_daily["Category"] == category_name)
        & (category_daily["Date"].between(start_date, end_date))
    ]

    print("\nLargest Category Spike Investigation:")
    print(
        event_data[
            [
                "Date",
                "Category",
                "Sales",
                "Same_Day_4week_Avg",
                "Sales_Change_pct",
                "Quantity",
                "Quantity_4week_Avg",
                "Quantity_Change_pct",
            ]
        ].to_string(index=False)
    )

    # Calculate actual and baseline sales for the whole event
    actual_sales = event_data["Sales"].sum()
    baseline_sales = event_data["Same_Day_4week_Avg"].sum()

    # Generate the business summary
    category_summary = generate_category_spike_summary(
        category=category_name,
        start_date=start_date,
        end_date=end_date,
        avg_sales_change=top_spike["Avg_Sales_Change"],
        avg_quantity_change=top_spike["Avg_Quantity_Change"],
        actual_sales=actual_sales,
        baseline_sales=baseline_sales,
    )

    print("\nCategory Spike Business Summary:")
    print(category_summary)

    # Send category-spike email alert
    subject = (
        f"Business Alert: Category Sales Spike | "
        f"{category_name} | "
        f"{start_date.date()} to {end_date.date()}"
    )

    alert_key = (
    f"category_spike_{category_name}_"
    f"{start_date.date()}_{end_date.date()}"
)

    send_alert_once(
        alert_key=alert_key,
        alert_type="Category Sales Spike",
        start_date=start_date,
        end_date=end_date,
        subject=subject,
        summary=category_summary,
    )
print("\nCandidate spike events:")
print(candidate_spikes)

print("\nCandidate events:")
print(candidate_events)


# -------------------------
# 4. Explain one detected event
# -------------------------

if not candidate_events.empty:

    first_event = candidate_events.iloc[0]

    start_date = first_event["Start_Date"]
    end_date = first_event["End_Date"]

    (    
        overall_metrics,
        loss_contributors,
        event_regions,
        regional_assessment
    ) = explain_event(
        start_date,
        end_date,
        daily_data,
        product_daily,
        region_daily
    )

    summary = generate_summary(
        start_date,
        end_date,
        overall_metrics,
        loss_contributors,
        event_regions,
        regional_assessment
    )

    print("\nBusiness Summary:")
    print(summary)

    subject = (
        f"Business Alert: Sales Drop | "
        f"{start_date.date()} to {end_date.date()}"
    )

    alert_key = (
    f"overall_sales_drop_"
    f"{start_date.date()}_{end_date.date()}"
)

    send_alert_once(
        alert_key=alert_key,
        alert_type="Overall Sales Drop",
        start_date=start_date,
        end_date=end_date,
        subject=subject,
        summary=summary,
    )

    