from pathlib import Path

from src.data_loader import load_data
from src.preprocessing import (
    create_daily_data,
    create_region_data,
    create_product_data
)
from src.anomaly_detector import detect_overall_sales_drops
from src.explainer import explain_event


# -------------------------
# 1. Load data
# -------------------------

BASE_DIR = Path(__file__).resolve().parent

file_path = (
    BASE_DIR
    / "data"
    / "ecommerce_business_monitoring_dataset.xlsx"
)

data = load_data(file_path)

print("Data loaded successfully!")
print("Rows:", len(data))


# -------------------------
# 2. Prepare datasets
# -------------------------

daily_data = create_daily_data(data)

region_daily = create_region_data(data)

product_daily = create_product_data(data)

print("Daily data:", daily_data.shape)
print("Region data:", region_daily.shape)
print("Product data:", product_daily.shape)


# -------------------------
# 3. Detect anomalies
# -------------------------

daily_data, candidate_events = (
    detect_overall_sales_drops(daily_data)
)

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
        product_explanation,
        region_explanation,
        regional_assessment
    ) = explain_event(
        start_date,
        end_date,
        daily_data,
        product_daily,
        region_daily
    )

    print("\nEvent:")
    print(start_date, "to", end_date)

    print("\nOverall metrics:")
    print(overall_metrics)

    print("\nTop product contributors:")
    print(
        product_explanation[
            [
                "Product_Name",
                "Sales_Loss",
                "Loss_Contribution_pct"
            ]
        ].head(10)
    )

    print("\nRegional impact:")
    print(
        region_explanation[
            [
                "Region",
                "Sales_Change_pct",
                "Sales_Loss"
            ]
        ]
    )

    print("\nAssessment:")
    print(regional_assessment)