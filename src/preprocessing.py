import pandas as pd


def create_daily_data(data):

    daily_data = data.groupby("Date").agg({
        "Quantity": "sum",
        "Sales": "sum",
        "Profit": "sum",
        "Order_ID": "count"
    }).reset_index()

    daily_data.rename(
        columns={"Order_ID": "Orders"},
        inplace=True
    )

    daily_data["Day"] = daily_data["Date"].dt.day_name()

    # Same weekday, previous 4 weeks baseline
    daily_data["Sales_4week_Avg"] = (
        daily_data
        .groupby("Day")["Sales"]
        .transform(lambda x: x.shift(1).rolling(4).mean())
    )

    daily_data["Quantity_4week_Avg"] = (
        daily_data
        .groupby("Day")["Quantity"]
        .transform(lambda x: x.shift(1).rolling(4).mean())
    )

    daily_data["Sales_Change_pct"] = (
        (daily_data["Sales"] - daily_data["Sales_4week_Avg"])
        / daily_data["Sales_4week_Avg"]
    ) * 100

    daily_data["Quantity_Change_pct"] = (
        (daily_data["Quantity"] - daily_data["Quantity_4week_Avg"])
        / daily_data["Quantity_4week_Avg"]
    ) * 100

    # Profit baseline
    daily_data["Profit_4week_Avg"] = (
        daily_data
        .groupby("Day")["Profit"]
        .transform(lambda x: x.shift(1).rolling(4).mean())
    )

    daily_data["Profit_Change_pct"] = (
        (daily_data["Profit"] - daily_data["Profit_4week_Avg"])
        / daily_data["Profit_4week_Avg"]
    ) * 100

    return daily_data


def create_region_data(data):

    region_daily = data.groupby(
        ["Date", "Region"]
    ).agg({
        "Sales": "sum",
        "Quantity": "sum",
        "Order_ID": "count"
    }).reset_index()

    region_daily.rename(
        columns={"Order_ID": "Orders"},
        inplace=True
    )

    # Create complete Date × Region grid
    all_dates = data["Date"].unique()
    all_regions = data["Region"].unique()

    complete_index = pd.MultiIndex.from_product(
        [all_dates, all_regions],
        names=["Date", "Region"]
    )

    region_daily = (
        region_daily
        .set_index(["Date", "Region"])
        .reindex(complete_index, fill_value=0)
        .reset_index()
    )

    region_daily["Day"] = (
        region_daily["Date"].dt.day_name()
    )

    # Same region + same weekday, previous 4 weeks
    region_daily["Same_Day_4week_Avg"] = (
        region_daily
        .groupby(["Region", "Day"])["Sales"]
        .transform(
            lambda x: x.shift(1).rolling(4).mean()
        )
    )

    region_daily["Same_Day_Change_pct"] = (
        (
            region_daily["Sales"]
            - region_daily["Same_Day_4week_Avg"]
        )
        / region_daily["Same_Day_4week_Avg"]
    ) * 100

    return region_daily


def create_product_data(data):

    product_daily = data.groupby(
        ["Date", "Product_Name"]
    ).agg({
        "Sales": "sum",
        "Quantity": "sum",
        "Profit": "sum",
        "Order_ID": "count"
    }).reset_index()

    product_daily.rename(
        columns={"Order_ID": "Orders"},
        inplace=True
    )

    # Create complete Date × Product grid
    all_dates = data["Date"].unique()
    all_products = data["Product_Name"].unique()

    complete_index = pd.MultiIndex.from_product(
        [all_dates, all_products],
        names=["Date", "Product_Name"]
    )

    product_daily = (
        product_daily
        .set_index(["Date", "Product_Name"])
        .reindex(complete_index, fill_value=0)
        .reset_index()
    )

    product_daily["Day"] = (
        product_daily["Date"].dt.day_name()
    )

    # Same product + same weekday, previous 4 weeks
    product_daily["Same_Day_4week_Avg"] = (
        product_daily
        .groupby(
            ["Product_Name", "Day"]
        )["Sales"]
        .transform(
            lambda x: x.shift(1).rolling(4).mean()
        )
    )

    product_daily["Sales_Change_pct"] = (
        (
            product_daily["Sales"]
            - product_daily["Same_Day_4week_Avg"]
        )
        / product_daily["Same_Day_4week_Avg"]
    ) * 100

    return product_daily


def create_category_data(data):

    category_daily = data.groupby(
        ["Date", "Category"]
    ).agg({
        "Sales": "sum",
        "Quantity": "sum",
        "Profit": "sum",
        "Order_ID": "count"
    }).reset_index()

    category_daily.rename(
        columns={"Order_ID": "Orders"},
        inplace=True
    )

    # Create complete Date × Category grid
    all_dates = data["Date"].unique()
    all_categories = data["Category"].unique()

    complete_index = pd.MultiIndex.from_product(
        [all_dates, all_categories],
        names=["Date", "Category"]
    )

    category_daily = (
        category_daily
        .set_index(["Date", "Category"])
        .reindex(complete_index, fill_value=0)
        .reset_index()
    )

    category_daily["Day"] = (
        category_daily["Date"].dt.day_name()
    )

    # Same category + same weekday, previous 4 weeks
    category_daily["Same_Day_4week_Avg"] = (
        category_daily
        .groupby(["Category", "Day"])["Sales"]
        .transform(
            lambda x: x.shift(1).rolling(4).mean()
        )
    )

    category_daily["Sales_Change_pct"] = (
        (
            category_daily["Sales"]
            - category_daily["Same_Day_4week_Avg"]
        )
        / category_daily["Same_Day_4week_Avg"]
    ) * 100

    category_daily["Quantity_4week_Avg"] = (
        category_daily
        .groupby(["Category", "Day"])["Quantity"]
        .transform(
            lambda x: x.shift(1).rolling(4).mean()
        )
    )

    category_daily["Quantity_Change_pct"] = (
        (
            category_daily["Quantity"]
            - category_daily["Quantity_4week_Avg"]
        )
        / category_daily["Quantity_4week_Avg"]
    ) * 100

    return category_daily