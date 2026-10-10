
import pandas as pd


def safe_percentage_change(actual, baseline):
    """Return percentage change safely when the baseline is zero or missing."""
    if pd.isna(baseline) or baseline == 0:
        return None

    return ((actual - baseline) / baseline) * 100


def explain_event(
    start_date,
    end_date,
    daily_data,
    product_daily,
    region_daily,
):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    daily_data = daily_data.copy()
    product_daily = product_daily.copy()
    region_daily = region_daily.copy()

    # Ensure dates use a consistent datetime format
    for dataframe in (daily_data, product_daily, region_daily):
        dataframe["Date"] = pd.to_datetime(dataframe["Date"])

    # -------------------------
    # 1. Overall event impact
    # -------------------------

    event_overall = daily_data[
        daily_data["Date"].between(start_date, end_date)
    ]

    event_sales = event_overall["Sales"].sum()
    baseline_sales = event_overall["Sales_4week_Avg"].sum()

    event_quantity = event_overall["Quantity"].sum()
    baseline_quantity = event_overall["Quantity_4week_Avg"].sum()

    overall_metrics = {
        "Event_Sales": event_sales,
        "Baseline_Sales": baseline_sales,
        "Sales_Change_pct": safe_percentage_change(
            event_sales, baseline_sales
        ),
        "Event_Quantity": event_quantity,
        "Baseline_Quantity": baseline_quantity,
        "Quantity_Change_pct": safe_percentage_change(
            event_quantity, baseline_quantity
        ),
        "Event_Start_Date": start_date,
        "Event_End_Date": end_date,
        "Duration_Days": (end_date - start_date).days + 1,
        "Sales_Difference": event_sales - baseline_sales,
    }

    # -------------------------
    # 2. Product-level analysis
    # -------------------------

    event_product_rows = product_daily[
        product_daily["Date"].between(start_date, end_date)
    ]

    event_products = (
        event_product_rows.groupby("Product_Name")
        .agg(
            Event_Sales=("Sales", "sum"),
            Event_Quantity=("Quantity", "sum"),
            Event_Profit=("Profit", "sum"),
            Baseline_Sales=("Same_Day_4week_Avg", "sum"),
        )
        .reset_index()
    )

    event_products["Sales_Loss"] = (
        event_products["Baseline_Sales"] - event_products["Event_Sales"]
    )

    loss_contributors = event_products[
        event_products["Sales_Loss"] > 0
    ].copy()

    total_positive_loss = loss_contributors["Sales_Loss"].sum()

    if total_positive_loss > 0:
        loss_contributors["Loss_Contribution_pct"] = (
            loss_contributors["Sales_Loss"] / total_positive_loss
        ) * 100
    else:
        loss_contributors["Loss_Contribution_pct"] = 0.0

    loss_contributors = loss_contributors.sort_values(
        "Sales_Loss", ascending=False
    ).reset_index(drop=True)

    # -------------------------
    # 3. Region-level analysis
    # -------------------------

    event_region_rows = region_daily[
        region_daily["Date"].between(start_date, end_date)
    ]

    event_regions = (
        event_region_rows.groupby("Region")
        .agg(
            Event_Sales=("Sales", "sum"),
            Event_Quantity=("Quantity", "sum"),
            Event_Orders=("Orders", "sum"),
            Baseline_Sales=("Same_Day_4week_Avg", "sum"),
        )
        .reset_index()
    )

    event_regions["Sales_Change_pct"] = event_regions.apply(
        lambda row: safe_percentage_change(
            row["Event_Sales"], row["Baseline_Sales"]
        ),
        axis=1,
    )

    event_regions["Sales_Loss"] = (
        event_regions["Baseline_Sales"] - event_regions["Event_Sales"]
    )

    event_regions = event_regions.sort_values(
        "Sales_Loss", ascending=False
    ).reset_index(drop=True)

    # -------------------------
    # 4. Regional classification
    # -------------------------

    valid_region_changes = event_regions["Sales_Change_pct"].dropna()

    if valid_region_changes.empty:
        regional_assessment = "Insufficient baseline data"

    else:
        declining_regions = (valid_region_changes < 0).sum()
        total_regions = len(valid_region_changes)

        region_decline_pct = (
            declining_regions / total_regions
        ) * 100

        if region_decline_pct >= 80:
            regional_assessment = "Broad-based regional decline"

        elif region_decline_pct >= 50:
            regional_assessment = "Widespread regional decline"

        else:
            regional_assessment = "Region-concentrated decline"

    return (
        overall_metrics,
        loss_contributors,
        event_regions,
        regional_assessment,
    )
