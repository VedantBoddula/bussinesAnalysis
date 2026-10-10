def generate_summary(
    start_date,
    end_date,
    overall_metrics,
    product_contributors,
    regional_impact,
    regional_assessment,
):

    sales_change = overall_metrics["Sales_Change_pct"]

    # Determine event type
    if sales_change <= -30:
        event_type = "Sales Drop"
    elif sales_change >= 30:
        event_type = "Sales Spike"
    else:
        event_type = "Sales Change"

    # Calculate total sales loss
    
    sales_difference = (
        overall_metrics["Event_Sales"]
        - overall_metrics["Baseline_Sales"]
    )

    if sales_difference < 0:
        impact_text = (
            f"Estimated sales loss: ₹{abs(sales_difference):,.2f}"
        )
    elif sales_difference > 0:
        impact_text = (
            f"Estimated additional sales: ₹{sales_difference:,.2f}"
        )
    else:
        impact_text = "Sales were equal to the baseline."


    summary = (
        f"Business Alert: {event_type}\n"
        f"Period: {start_date.date()} to {end_date.date()}\n"
        f"Sales changed by {sales_change:.1f}% compared with the baseline.\n"
        f"{impact_text}\n"
    )

    # Top 3 product contributors
    if product_contributors is not None and not product_contributors.empty:

        top_products = product_contributors.head(3)

        summary += "\nTop product contributors:\n"

        for _, row in top_products.iterrows():
            summary += (
                f"- {row['Product_Name']}: "
                f"₹{row['Sales_Loss']:,.2f} loss "
                f"({row['Loss_Contribution_pct']:.1f}%)\n"
            )

    # Most affected region
    if regional_impact is not None and not regional_impact.empty:

        top_region = regional_impact.iloc[0]

        summary += (
            f"\nMost affected region: {top_region['Region']} "
            f"({top_region['Sales_Change_pct']:.1f}% change)\n"
        )

    summary += f"Regional assessment: {regional_assessment}."

    return summary



def generate_category_spike_summary(
    category,
    start_date,
    end_date,
    avg_sales_change,
    avg_quantity_change,
    actual_sales,
    baseline_sales,
):
    summary = (
        "Business Alert: Category Sales Spike\n"
        f"Category: {category}\n"
        f"Period: {start_date.date()} to {end_date.date()}\n\n"
        f"Sales increased by {avg_sales_change:.1f}% "
        "compared with the baseline.\n"
        f"Quantity increased by {avg_quantity_change:.1f}% "
        "compared with the baseline.\n\n"
        f"Actual sales: ₹{actual_sales:,.2f}\n"
        f"Baseline sales: ₹{baseline_sales:,.2f}\n\n"
        f"Explanation: {category} sales and quantity were "
        "significantly higher than their usual levels over this period."
    )

    return summary
