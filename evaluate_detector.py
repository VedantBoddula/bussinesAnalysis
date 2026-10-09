
from pathlib import Path
import pandas as pd

from src.data_loader import load_data
from src.preprocessing import (
    create_daily_data,
    create_category_data,
)
from src.anomaly_detector import (
    detect_overall_sales_drops,
    detect_overall_sales_spikes,
    detect_category_sales_spikes,
)

BASE_DIR = Path(__file__).resolve().parent

file_path = (
    BASE_DIR
    / "data"
    / "ecommerce_business_monitoring_dataset.xlsx"
)

data = load_data(file_path)

ground_truth = pd.read_excel(
    file_path,
    sheet_name="Ground_Truth",
)

daily_data = create_daily_data(data)
category_daily = create_category_data(data)

daily_data, candidate_drops = detect_overall_sales_drops(
    daily_data
)

daily_data, candidate_spikes = detect_overall_sales_spikes(
    daily_data
)

category_daily, category_spikes = detect_category_sales_spikes(
    category_daily
)

print("Known anomalies:", len(ground_truth))
print("Detected overall drops:", len(candidate_drops))
print("Detected overall spikes:", len(candidate_spikes))
print("Detected category spikes:", len(category_spikes))

print("\nKnown anomaly types:")
print(ground_truth["Anomaly_Type"].value_counts().to_string())


print("\n========== OVERALL SALES DROPS ==========")
if not candidate_drops.empty:
    print(candidate_drops.to_string(index=False))
else:
    print("No overall sales drops detected.")

print("\n========== OVERALL SALES SPIKES ==========")
if not candidate_spikes.empty:
    print(candidate_spikes.to_string(index=False))
else:
    print("No overall sales spikes detected.")

print("\n========== CATEGORY SALES SPIKES ==========")
if not category_spikes.empty:
    print(category_spikes.to_string(index=False))
else:
    print("No category sales spikes detected.")