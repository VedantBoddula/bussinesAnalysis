
from pathlib import Path

import pandas as pd

from src.data_loader import load_data
from src.preprocessing import create_daily_data, create_category_data, create_product_data
from src.anomaly_detector import (
    detect_overall_sales_drops,
    detect_overall_sales_spikes,
    detect_category_sales_spikes,
    detect_product_sales_spikes
)

BASE_DIR = Path(__file__).resolve().parent
file_path = BASE_DIR / "data" / "ecommerce_business_monitoring_dataset.xlsx"

data = load_data(file_path)
ground_truth = pd.read_excel(file_path, sheet_name="Ground_Truth")


daily_data = create_daily_data(data)
category_daily = create_category_data(data)

# Detect product-level sales spikes
product_daily = create_product_data(data)



print("\n========== PRODUCT BASELINE DIAGNOSTICS ==========")

# Examine the Smart LED TV's recent daily history
check_product = 'Smart LED TV 43"'
check_date = pd.Timestamp("2024-10-31")

tv_history = product_daily[
    (product_daily["Product_Name"] == check_product)
    & (product_daily["Date"] <= check_date)
].sort_values("Date")

print("\nRecent TV history:")
print(
    tv_history.tail(35)[
        [
            "Date",
            "Sales",
            "Quantity",
            "Same_Day_4week_Avg",
            "Sales_Change_pct",
        ]
    ].to_string(index=False)
)

# Check how often product baselines are zero
print("\nBaseline statistics:")
print(
    product_daily["Same_Day_4week_Avg"]
    .describe(percentiles=[0.25, 0.50, 0.75, 0.90, 0.95])
)

zero_baseline_pct = (
    product_daily["Same_Day_4week_Avg"].eq(0).mean() * 100
)
print(f"\nZero baseline rows: {zero_baseline_pct:.2f}%")

# Check the distribution of product sales changes
print("\nSales change statistics:")
print(
    product_daily["Sales_Change_pct"]
    .replace([float("inf"), float("-inf")], float("nan"))
    .dropna()
    .describe(percentiles=[0.50, 0.90, 0.95, 0.99])
)

product_daily, product_spikes = detect_product_sales_spikes(
    product_daily
)


print("\n========== PRODUCT SPIKE SUMMARY ==========")

print("Total candidate events:", len(product_spikes))

if not product_spikes.empty:
    print("\nEvents by duration:")
    print(
        product_spikes["Duration"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nEvents by product:")
    print(
        product_spikes["Product_Name"]
        .value_counts()
        .to_string()
    )

print("\n========== PRODUCT SALES SPIKES ==========")

if not product_spikes.empty:
    print(product_spikes.to_string(index=False))
else:
    print("No product sales spikes detected.")


# Inspect the top product spike candidates
if not product_spikes.empty:
    top_spikes = product_spikes.head(10)

    for _, spike in top_spikes.iterrows():
        product = spike["Product_Name"]
        start_date = spike["Start_Date"]
        end_date = spike["End_Date"]

        details = product_daily[
            (product_daily["Product_Name"] == product)
            & (product_daily["Date"] >= start_date)
            & (product_daily["Date"] <= end_date)
        ]

        print(f"\nProduct: {product}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(
            details[
                [
                    "Date",
                    "Sales",
                    "Same_Day_4week_Avg",
                    "Sales_Change_pct",
                    "Quantity",
                ]
            ].to_string(index=False)
        )



print("\n========== INSPECT LARGEST PRODUCT SPIKE ==========")

check_date = pd.Timestamp("2024-10-31")
check_product = 'Smart LED TV 43"'

raw_spike = data.copy()
raw_spike["Date"] = pd.to_datetime(raw_spike["Date"])

raw_spike = raw_spike[
    (raw_spike["Date"] == check_date)
    & (raw_spike["Product_Name"] == check_product)
]

print("Transaction count:", len(raw_spike))
print(
    raw_spike[
        ["Order_ID", "Date", "Product_Name", "Quantity", "Sales", "Profit"]
    ].to_string(index=False)
)

print("\nTotal quantity:", raw_spike["Quantity"].sum())
print("Total sales:", raw_spike["Sales"].sum())
print("Total profit:", raw_spike["Profit"].sum())




print("\n========== TV SALES BASELINE CHECK ==========")

tv_history = product_daily[
    (product_daily["Product_Name"] == check_product)
    & (product_daily["Date"] <= check_date)
].sort_values("Date")

print(
    tv_history.tail(6)[
        [
            "Date",
            "Sales",
            "Same_Day_4week_Avg",
            "Sales_Change_pct",
            "Quantity",
        ]
    ].to_string(index=False)
)


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



print("\n========== PRODUCT SALES DISTRIBUTION ==========")

sold_days = product_daily[product_daily["Sales"] > 0].copy()

product_stats = (
    sold_days.groupby("Product_Name")
    .agg(
        Active_Days=("Sales", "count"),
        Median_Daily_Sales=("Sales", "median"),
        P90_Daily_Sales=("Sales", lambda x: x.quantile(0.90)),
        Max_Daily_Sales=("Sales", "max"),
        Median_Quantity=("Quantity", "median"),
    )
    .sort_values("Max_Daily_Sales", ascending=False)
)

print(product_stats.to_string())

print("\n========== TV SALES VALIDATION ==========")

tv_stats = product_stats.loc['Smart LED TV 43"']
print(tv_stats)