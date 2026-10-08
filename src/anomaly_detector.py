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