
from src.alert_history import (
    initialize_alert_history,
    alert_exists,
    record_alert,
)

initialize_alert_history()

key = "test_sales_drop_2024-11-16_2024-11-22"

print("Exists before recording:", alert_exists(key))

record_alert(
    alert_key=key,
    alert_type="Sales Drop",
    start_date="2024-11-16",
    end_date="2024-11-22",
    summary="Test sales drop alert",
    status="sent",
)

print("Exists after recording:", alert_exists(key))
