import pandas as pd


def explain_event(start_date, end_date, daily_data, product_daily, region_daily):

    # Convert dates to datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # -------------------------
    # 1. Overall event impact
    # -------------------------

    event_overall = daily_data[
        (daily_data["Date"] >= start_date) & (daily_data["Date"] <= end_date)
    ]

    event_sales = event_overall["Sales"].sum()
    baseline_sales = event_overall["Sales_4week_Avg"].sum()

    event_quantity = event_overall["Quantity"].sum()
    baseline_quantity = event_overall["Quantity_4week_Avg"].sum()

    # Temporary baseline period
    # for product and region analysis

    overall_metrics = {
        "Event_Sales": event_sales,
        "Baseline_Sales": baseline_sales,
        "Sales_Change_pct": ((event_sales - baseline_sales) / baseline_sales) * 100,
        "Event_Quantity": event_quantity,
        "Baseline_Quantity": baseline_quantity,
        "Quantity_Change_pct": (
            (event_quantity - baseline_quantity) / baseline_quantity
        )
        * 100,
    }

    # -------------------------
    # 2. Product-level analysis
    # -------------------------

    event_products = (
        product_daily[
            (product_daily["Date"] >= start_date) & (product_daily["Date"] <= end_date)
        ]
        .groupby("Product_Name")
        .agg(
            Event_Sales=("Sales", "sum"),
            Event_Quantity=("Quantity", "sum"),
            Event_Profit=("Profit", "sum"),
        )
        .reset_index()
    )

    baseline_products = (
        product_daily[
            (product_daily["Date"] >= start_date) & (product_daily["Date"] <= end_date)
        ]
        .groupby("Product_Name")
        .agg(Baseline_Sales=("Same_Day_4week_Avg", "sum"))
        .reset_index()
    )

    event_products = event_products.merge(
        baseline_products, on="Product_Name", how="left"
    )

    event_products["Sales_Loss"] = (
        event_products["Baseline_Sales"] - event_products["Event_Sales"]
    )

    # Only products that actually lost sales
    loss_contributors = event_products[event_products["Sales_Loss"] > 0].copy()

    total_positive_loss = loss_contributors["Sales_Loss"].sum()

    if total_positive_loss > 0:
        loss_contributors["Loss_Contribution_pct"] = (
            loss_contributors["Sales_Loss"] / total_positive_loss
        ) * 100
    else:
        loss_contributors["Loss_Contribution_pct"] = 0

    loss_contributors = loss_contributors.sort_values("Sales_Loss", ascending=False)

    # -------------------------
    # 3. Region-level analysis
    # -------------------------

    event_regions = (
        region_daily[
            (region_daily["Date"] >= start_date) & (region_daily["Date"] <= end_date)
        ]
        .groupby("Region")
        .agg(
            Event_Sales=("Sales", "sum"),
            Event_Quantity=("Quantity", "sum"),
            Event_Orders=("Orders", "sum"),
        )
        .reset_index()
    )

    baseline_regions = (
        region_daily[
            (region_daily["Date"] >= start_date) & (region_daily["Date"] <= end_date)
        ]
        .groupby("Region")
        .agg(Baseline_Sales=("Same_Day_4week_Avg", "sum"))
        .reset_index()
    )

    event_regions = event_regions.merge(baseline_regions, on="Region", how="left")

    event_regions["Sales_Change_pct"] = (
        (event_regions["Event_Sales"] - event_regions["Baseline_Sales"])
        / event_regions["Baseline_Sales"]
    ) * 100

    event_regions["Sales_Loss"] = (
        event_regions["Baseline_Sales"] - event_regions["Event_Sales"]
    )

    event_regions = event_regions.sort_values("Sales_Loss", ascending=False)

    # -------------------------
    # 4. Regional classification
    # -------------------------

    declining_regions = (event_regions["Sales_Change_pct"] < 0).sum()

    total_regions = len(event_regions)

    region_decline_pct = (declining_regions / total_regions) * 100

    if region_decline_pct >= 80:
        regional_assessment = "Broad-based regional decline"

    elif region_decline_pct >= 50:
        regional_assessment = "Widespread regional decline"

    else:
        regional_assessment = "Region-concentrated decline"

    return (overall_metrics, loss_contributors, event_regions, regional_assessment)
