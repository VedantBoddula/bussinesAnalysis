
from src.alert_history import initialize_alert_history, get_alert_history

initialize_alert_history()

history = get_alert_history()

if history.empty:
    print("No alerts recorded yet.")
else:
    print("\n========== ALERT HISTORY ==========\n")

    for _, alert in history.iterrows():
        print(f"Alert ID:   {alert['ID']}")
        print(f"Type:       {alert['Alert Type']}")
        print(f"Period:     {str(alert['Start Date'])[:10]} to {str(alert['End Date'])[:10]}")
        print(f"Status:     {alert['Status']}")
        print(f"Created At: {alert['Created At']}")

        summary = str(alert["Summary"]).replace("\\n", "\n")
        print(f"\nSummary:\n{summary}")
        print("\n" + "-" * 60)
