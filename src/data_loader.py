import pandas as pd
from pathlib import Path


def load_data(file_path):
    data = pd.read_excel(file_path, sheet_name="Transactions")

    return data