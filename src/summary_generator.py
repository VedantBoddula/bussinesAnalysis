def generate_summary(
    start_date,
    end_date,
    overall_metrics,
    product_contributors,
    regional_impact,
    regional_assessment
):
    sales_change = overall_metrics["Sales_Change_pct"]

    if sales_change <= -30:
        event_type = "Sales Drop"
    elif sales_change >= 30:
        event_type = "Sales Spike"
    else:
        event_type = "Sales Change"

    summary = (
        f"Business Alert: {event_type}\n"
        f"Period: {start_date.date()} to {end_date.date()}\n"
        f"Sales changed by {sales_change:.1f}% compared with the baseline.\n"
    )

    if product_contributors is not None and not product_contributors.empty:
        top_product = product_contributors.iloc[0]["Product_Name"]

        summary += (
            f"Main product contributor: {top_product}.\n"
        )

    summary += (
        f"Regional assessment: {regional_assessment}."
    )

    return summary
    