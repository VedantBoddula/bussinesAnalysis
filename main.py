from pathlib import Path 

from src.data_loader import load_data
from src.preprocessing import (
    create_daily_data,
    create_region_data,
    create_product_data
)
from src.anomaly_detector import (
    detect_overall_sales_drops,
    detect_overall_sales_spikes
)
from src.explainer import explain_event
from src.summary_generator import generate_summary
from src.email_alert import send_email_alert



# -------------------------
# 1. Load data
# -------------------------

BASE_DIR = Path(__file__).resolve().parent

file_path = (
    BASE_DIR
    / "data"
    / "ecommerce_business_monitoring_dataset.xlsx"
)

data = load_data(file_path)

print("Data loaded successfully!")
print("Rows:", len(data))


# -------------------------
# 2. Prepare datasets
# -------------------------

daily_data = create_daily_data(data)

region_daily = create_region_data(data)

product_daily = create_product_data(data)

print("Daily data:", daily_data.shape)
print("Region data:", region_daily.shape)
print("Product data:", product_daily.shape)


# -------------------------
# 3. Detect anomalies
# -------------------------

daily_data, candidate_events = (
    detect_overall_sales_drops(daily_data)
)

daily_data, candidate_spikes = (
    detect_overall_sales_spikes(daily_data)
)

print("\nCandidate spike events:")
print(candidate_spikes)

print("\nCandidate events:")
print(candidate_events)


# -------------------------
# 4. Explain one detected event
# -------------------------

if not candidate_events.empty:

    first_event = candidate_events.iloc[0]

    start_date = first_event["Start_Date"]
    end_date = first_event["End_Date"]

    (    
        overall_metrics,
        loss_contributors,
        event_regions,
        regional_assessment
    ) = explain_event(
        start_date,
        end_date,
        daily_data,
        product_daily,
        region_daily
    )

    summary = generate_summary(
        start_date,
        end_date,
        overall_metrics,
        loss_contributors,
        event_regions,
        regional_assessment
    )

    print("\nBusiness Summary:")
    print(summary)

    subject = (
        f"Business Alert: Sales Drop | "
        f"{start_date.date()} to {end_date.date()}"
    )

    send_email_alert(
        subject=subject,
        body=summary
    )


    

    