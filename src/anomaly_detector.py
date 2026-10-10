import pandas as pd


def detect_overall_sales_drops(daily_data):

    daily_data = daily_data.copy()

    # A day is considered a soft drop signal if
    # either Sales OR Quantity falls by 30% or more
    daily_data["Overall_Drop_Signal_Soft"] = (
        (daily_data["Sales_Change_pct"] <= -30)
        |
        (daily_data["Quantity_Change_pct"] <= -30)
    )

    # Create groups of consecutive drop days
    daily_data["Soft_Drop_Group"] = (
        daily_data["Overall_Drop_Signal_Soft"]
        != daily_data["Overall_Drop_Signal_Soft"].shift()
    ).cumsum()

    # Aggregate consecutive drop days into candidate events
    candidate_events = (
        daily_data[
            daily_data["Overall_Drop_Signal_Soft"]
        ]
        .groupby("Soft_Drop_Group")
        .agg(
            Start_Date=("Date", "min"),
            End_Date=("Date", "max"),
            Duration=("Date", "count"),
            Avg_Sales_Change=("Sales_Change_pct", "mean"),
            Avg_Quantity_Change=("Quantity_Change_pct", "mean")
        )
        .sort_values(
            ["Duration", "Start_Date"],
            ascending=[False, True]
        )
    )

    # Keep events lasting at least 3 days
    # with average sales decline of at least 30%
    candidate_events = candidate_events[
        (candidate_events["Duration"] >= 3)
        &
        (candidate_events["Avg_Sales_Change"] <= -30)
    ].copy()

    return daily_data, candidate_events


def detect_overall_sales_spikes(daily_data):

    daily_data = daily_data.copy()

    
    # A spike requires a meaningful sales increase
    # and no significant decline in quantity
    daily_data["Overall_Spike_Signal_Soft"] = (
        (daily_data["Sales_Change_pct"] >= 30)
        & (daily_data["Quantity_Change_pct"] >= 0)
    )

    # Group consecutive spike days
    daily_data["Soft_Spike_Group"] = (
        daily_data["Overall_Spike_Signal_Soft"]
        != daily_data["Overall_Spike_Signal_Soft"].shift()
    ).cumsum()

    # Aggregate candidate events
    candidate_spikes = (
        daily_data[daily_data["Overall_Spike_Signal_Soft"]]
        .groupby("Soft_Spike_Group")
        .agg(
            Start_Date=("Date", "min"),
            End_Date=("Date", "max"),
            Duration=("Date", "count"),
            Avg_Sales_Change=("Sales_Change_pct", "mean"),
            Avg_Quantity_Change=("Quantity_Change_pct", "mean")
        )
    )

    # Require at least two days and positive average changes
    candidate_spikes = candidate_spikes[
        (candidate_spikes["Duration"] >= 2)
        & (candidate_spikes["Avg_Sales_Change"] >= 30)
        & (candidate_spikes["Avg_Quantity_Change"] > 0)
    ].sort_values(
        ["Duration", "Start_Date"],
        ascending=[False, True]
    )

    return daily_data, candidate_spikes

def detect_category_sales_spikes(category_daily):

    category_daily = category_daily.copy()

    # Flag unusually high sales or quantity
    category_daily["Spike_Signal"] = (
        (category_daily["Sales_Change_pct"] >= 50)
        & (category_daily["Quantity_Change_pct"] >= 30)
        & (category_daily["Same_Day_4week_Avg"] >= 5000)
        & (category_daily["Quantity_4week_Avg"] >= 3)
)

    # Group consecutive spike days separately for each category
    category_daily = category_daily.sort_values(
        ["Category", "Date"]
    ).copy()

    category_daily["Spike_Group"] = (
        category_daily.groupby("Category")["Spike_Signal"]
        .transform(
            lambda x: (x != x.shift()).cumsum()
        )
    )

    candidate_spikes = (
        category_daily[category_daily["Spike_Signal"]]
        .groupby(["Category", "Spike_Group"])
        .agg(
            Start_Date=("Date", "min"),
            End_Date=("Date", "max"),
            Duration=("Date", "count"),
            Avg_Sales_Change=("Sales_Change_pct", "mean"),
            Avg_Quantity_Change=("Quantity_Change_pct", "mean")
        )
        .reset_index()
    )

    # Require at least two consecutive days
    candidate_spikes = candidate_spikes[
        candidate_spikes["Duration"] >= 2
    ].sort_values(
        by=["Duration", "Avg_Sales_Change"],
        ascending=[False, False]
    )

    return category_daily, candidate_spikes




def detect_product_sales_spikes(product_daily):
    product_daily = product_daily.copy()

    # Require meaningful sales and quantity baselines
    product_daily["Is_Spike"] = (
        (product_daily["Same_Day_4week_Avg"] >= 5000)
        & (product_daily["Sales"] >= 15000)
        & (product_daily["Quantity"] >= 3)
        & (
            product_daily["Sales"]
            >= product_daily["Same_Day_4week_Avg"] * 2
        )
        & (product_daily["Quantity_4week_Avg"] > 0)
        & (
            product_daily["Quantity"]
            >= product_daily["Quantity_4week_Avg"] * 1.5
        )
    )

    # Sort by product and date
    product_daily = product_daily.sort_values(
        ["Product_Name", "Date"]
    ).copy()

    # Group consecutive spike days for each product
    product_daily["Spike_Group"] = (
        product_daily.groupby("Product_Name")["Is_Spike"]
        .transform(lambda x: (x != x.shift()).cumsum())
    )

    spike_days = product_daily[
        product_daily["Is_Spike"]
    ].copy()

    columns = [
        "Product_Name",
        "Spike_Group",
        "Start_Date",   
        "End_Date",
        "Duration",
        "Avg_Sales_Change",
    ]

    if spike_days.empty:
        return product_daily, pd.DataFrame(columns=columns)

    # Combine consecutive spike days into events
    candidate_spikes = (
        spike_days.groupby(["Product_Name", "Spike_Group"])
        .agg(
            Start_Date=("Date", "min"),
            End_Date=("Date", "max"),
            Duration=("Date", "count"),
            Avg_Sales_Change=("Sales_Change_pct", "mean"),
        )
        .reset_index()
    )

    # Keep events lasting at least two days
    candidate_spikes = candidate_spikes[
        candidate_spikes["Duration"] >= 2
    ].copy()

    candidate_spikes = (
        candidate_spikes.sort_values(
            "Avg_Sales_Change", ascending=False
        ).reset_index(drop=True)
    )

    return product_daily, candidate_spikes



def detect_profit_margin_drops(category_daily):

    category_daily = category_daily.copy()

    # Flag days where margin drops by at least 5 percentage points
    category_daily["Is_Margin_Drop"] = (
        (category_daily["Sales"] >= 3000)
        & (category_daily["Profit_Margin_4week_Avg"] >= 5)
        & (category_daily["Margin_Drop_pp"] <= -5)
    )

    category_daily = category_daily.sort_values(
        ["Category", "Date"]
    ).copy()

    # Group consecutive flagged days within each category
    category_daily["Margin_Group"] = (
        category_daily.groupby("Category")["Is_Margin_Drop"]
        .transform(lambda x: (x != x.shift()).cumsum())
    )

    margin_days = category_daily[
        category_daily["Is_Margin_Drop"]
    ].copy()

    columns = [
        "Category",
        "Start_Date",
        "End_Date",
        "Duration",
        "Avg_Margin_Drop_pp"
    ]

    if margin_days.empty:
        return category_daily, pd.DataFrame(columns=columns)

    candidate_events = (
        margin_days.groupby(["Category", "Margin_Group"])
        .agg(
            Start_Date=("Date", "min"),
            End_Date=("Date", "max"),
            Duration=("Date", "count"),
            Avg_Margin_Drop_pp=("Margin_Drop_pp", "mean")
        )
        .reset_index()
    )

    # Keep events lasting at least 2 consecutive days
    candidate_events = candidate_events[
        candidate_events["Duration"] >= 2
    ].copy()

    candidate_events = candidate_events.sort_values(
        "Avg_Margin_Drop_pp"
    ).reset_index(drop=True)

    return category_daily, candidate_events





def detect_regional_sales_drops(region_daily):
    region_daily = region_daily.copy()
    region_daily = region_daily.sort_values(
        ["Region", "Date"]
    ).copy()

    # Measure the average sales change over a 3-day window
    region_daily["Rolling_3day_Change_pct"] = (
        region_daily.groupby("Region")["Same_Day_Change_pct"]
        .transform(lambda x: x.rolling(3, min_periods=3).mean())
    )

    # Require a meaningful historical baseline and current sales
    region_daily["Regional_Drop_Signal"] = (
        (region_daily["Rolling_3day_Change_pct"] <= -30)
        & (region_daily["Same_Day_4week_Avg"] >= 5000)
        & (region_daily["Sales"] >= 3000)
    )

    region_daily["Drop_Group"] = (
        region_daily.groupby("Region")["Regional_Drop_Signal"]
        .transform(lambda x: (x != x.shift()).cumsum())
    )

    candidate_events = (
        region_daily[region_daily["Regional_Drop_Signal"]]
        .groupby(["Region", "Drop_Group"])
        .agg(
            Start_Date=("Date", "min"),
            End_Date=("Date", "max"),
            Duration=("Date", "count"),
            Avg_Sales_Change=("Rolling_3day_Change_pct", "mean"),
        )
        .reset_index()
    )

    candidate_events = candidate_events[
        candidate_events["Duration"] >= 2
    ].copy()

    candidate_events = candidate_events.sort_values(
        ["Duration", "Avg_Sales_Change"],
        ascending=[False, True],
    ).reset_index(drop=True)

    return region_daily, candidate_events

