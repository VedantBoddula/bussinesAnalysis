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