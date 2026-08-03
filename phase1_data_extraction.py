# phase1_data_extraction.py
import pandas as pd

FILE_PATH = r"C:\Users\omark\Desktop\internship\1122_report.xlsx"

def load_status_df():
    df_off = pd.read_excel(FILE_PATH, sheet_name="Ignition OFF")
    df_off["Event time"] = pd.to_datetime(df_off["Event time"], errors="coerce")
    df_off = df_off.dropna(subset=["Event time"])
    df_off_sorted = df_off.sort_values(["Grouping", "Event time"])
    latest_ignition_off = df_off_sorted.groupby("Grouping").tail(1).reset_index(drop=True)

    df_on = pd.read_excel(FILE_PATH, sheet_name="Ignition ON")
    df_on["Event time"] = pd.to_datetime(df_on["Event time"], errors="coerce")
    df_on = df_on.dropna(subset=["Event time"])
    df_on_sorted = df_on.sort_values(["Grouping", "Event time"])
    latest_ignition_on = df_on_sorted.groupby("Grouping").tail(1).reset_index(drop=True)

    off_renamed = latest_ignition_off.rename(columns={
        "Event time": "last_off_time", "Location": "last_off_location"
    })[["Grouping", "last_off_time", "last_off_location"]]

    on_renamed = latest_ignition_on.rename(columns={
        "Event time": "last_on_time", "Location": "last_on_location"
    })[["Grouping", "last_on_time", "last_on_location"]]

    status_df = pd.merge(off_renamed, on_renamed, on="Grouping", how="outer")

    def infer_status(row):
        if pd.isna(row["last_off_time"]) and pd.isna(row["last_on_time"]):
            return "unknown"
        if pd.isna(row["last_off_time"]):
            return "on"
        if pd.isna(row["last_on_time"]):
            return "off"
        return "off" if row["last_off_time"] > row["last_on_time"] else "on"

    status_df["current_status"] = status_df.apply(infer_status, axis=1)
    return status_df