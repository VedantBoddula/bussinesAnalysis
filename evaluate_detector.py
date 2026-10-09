
from pathlib import Path

import pandas as pd

from src.data_loader import load_data
from src.preprocessing import create_daily_data, create_category_data
from src.anomaly_detector import (
    detect_overall_sales_drops,
    detect_overall_sales_spikes,
    detect_category_sales_spikes,
)

BASE_DIR = Path(__file__).resolve().parent
file_path = BASE_DIR / "data" / "ecommerce_business_monitoring_dataset.xlsx"

data = load_data(file_path)
ground_truth = pd.read_excel(file_path, sheet_name="Ground_Truth")

daily_data = create_daily_data(data)
category_daily = create_category_data(data)


print("\n========== INVESTIGATE A008 ==========")

print("\nProduct names containing 'Air Fryer':")
print(
    data.loc[
        data["Product_Name"].str.contains(
            "Air Fryer", case=False, na=False
        ),
        "Product_Name",
    ].unique()
)

print("\nAll transactions on the A008 dates:")
a008_start = pd.Timestamp("2024-11-11")
a008_end = pd.Timestamp("2024-11-12")

a008_dates = data[
    pd.to_datetime(data["Date"]).between(a008_start, a008_end)
]

print("Transaction rows:", len(a008_dates))
print("\nProducts sold on these dates:")
print(
    a008_dates.groupby("Product_Name").agg(
        Sales=("Sales", "sum"),
        Quantity=("Quantity", "sum"),
        Orders=("Order_ID", "count"),
    ).sort_values("Sales", ascending=False).to_string()
)


print("\n========== AIR FRYER SALES HISTORY ==========")

air_fryer_data = data[
    data["Product_Name"].str.contains(
        "Air Fryer", case=False, na=False
    )
].copy()

air_fryer_data["Date"] = pd.to_datetime(air_fryer_data["Date"])

air_fryer_daily = air_fryer_data.groupby("Date").agg(
    Sales=("Sales", "sum"),
    Quantity=("Quantity", "sum"),
    Orders=("Order_ID", "count"),
)

print(
    air_fryer_daily.loc[
        air_fryer_daily.index.to_series().between(
            pd.Timestamp("2024-11-01"),
            pd.Timestamp("2024-11-20"),
        ).to_numpy()
    ].to_string()
)

print("\n========== INVESTIGATE A014 ==========")

a014_start = pd.Timestamp("2025-11-24")
a014_end = pd.Timestamp("2025-11-25")

cols = [
    "Date",
    "Sales",
    "Quantity",
    "Profit",
    "Same_Day_4week_Avg",
    "Sales_Change_pct",
    "Quantity_Change_pct",
]

print(
    daily_data.loc[
        daily_data["Date"].between(a014_start, a014_end),
        [col for col in cols if col in daily_data.columns],
    ].to_string(index=False)
)

print("\nOverall transactions during A014:")
print(
    data.loc[
        pd.to_datetime(data["Date"]).between(a014_start, a014_end)
    ].groupby("Date").agg(
        Sales=("Sales", "sum"),
        Quantity=("Quantity", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order_ID", "count"),
    ).to_string()
)

_, candidate_drops = detect_overall_sales_drops(daily_data)
_, candidate_spikes = detect_overall_sales_spikes(daily_data)
_, category_spikes = detect_category_sales_spikes(category_daily)


def overlaps(start1, end1, start2, end2):
    return start1 <= end2 and start2 <= end1


def evaluate_events(known, detected, detector_name, allowed_types):
    print(f"\n========== {detector_name} ==========")

    relevant = known[known["Anomaly_Type"].isin(allowed_types)]
    matched_ids = set()

    for _, event in relevant.iterrows():
        matches = detected[
            detected.apply(
                lambda row: overlaps(
                    pd.Timestamp(event["Start_Date"]),
                    pd.Timestamp(event["End_Date"]),
                    pd.Timestamp(row["Start_Date"]),
                    pd.Timestamp(row["End_Date"]),
                ),
                axis=1,
            )
        ]

        if "Category" in detected.columns:
            if pd.notna(event["Affected_Category"]) and event["Affected_Category"] != "All":
                matches = matches[matches["Category"] == event["Affected_Category"]]

        if not matches.empty:
            matched_ids.add(event["Anomaly_ID"])
            print(f"MATCH: {event['Anomaly_ID']} - {event['Anomaly_Type']}")
            print(
                f"  Known dates: {event['Start_Date']} to {event['End_Date']}"
            )
            print(
                f"  Detected dates: "
                f"{matches[['Start_Date', 'End_Date']].to_dict('records')}"
            )
        else:
            print(f"MISSED: {event['Anomaly_ID']} - {event['Anomaly_Type']}")

    print(f"\nKnown events in scope: {len(relevant)}")
    print(f"Known events matched: {len(matched_ids)}")
    print(f"Known events missed: {len(relevant) - len(matched_ids)}")


evaluate_events(
    ground_truth,
    candidate_drops,
    "OVERALL SALES DROPS",
    ["Overall Sales Drop"],
)

evaluate_events(
    ground_truth,
    candidate_spikes,
    "OVERALL SALES SPIKES",
    ["Unusual Sales Spike"],
)

evaluate_events(
    ground_truth,
    category_spikes,
    "CATEGORY SALES SPIKES",
    ["Product Sales Spike"],
)