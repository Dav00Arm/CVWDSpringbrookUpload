import pandas as pd
import re
from datetime import datetime
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import threading
import logging
import traceback
import pandas as pd
import re


def get_date_suffix():
    """Return MMDD fixed with 25 as the day part (hardcoded)."""
    return datetime.now().strftime('%m%d%y')


def clean_meter_id(meter_id):
    """Remove all non-digit characters from Meter ID."""
    return re.sub(r'\D', '', str(meter_id))


def load_data(export_file, rni_file):
    """Load and return Export and RNI DataFrames."""
    try:
        export_df = pd.read_csv(export_file)
        rni_df = pd.read_csv(rni_file)
    except FileNotFoundError as e:
        raise SystemExit(f"File not found: {e.filename}")
    return export_df, rni_df


def preprocess_data(export_df, rni_df):
    """Clean and prepare dataframes for merging."""
    rni_df['Meter ID'] = rni_df['Meter ID'].apply(clean_meter_id)

    export_df['SerialNumber'] = export_df['SerialNumber'].astype(str)
    rni_df['Meter ID'] = rni_df['Meter ID'].astype(str)

    export_df = export_df.drop(columns=['Latitude', 'Longitude'], errors='ignore')
    return export_df, rni_df


def merge_data(export_df, rni_df):
    """Merge export and RNI dataframes on Meter ID."""
    merged = export_df.merge(
        rni_df[['Meter ID', 'FlexNet ID', 'Latitude', 'Longitude']],
        left_on='SerialNumber',
        right_on='Meter ID',
        how='inner'
    )
    merged['MXUID'] = merged['FlexNet ID'].fillna(0).astype(int)
    return merged


def format_final_df(merged_df):
    """Format the final dataframe with selected and cleaned columns."""
    final_df = merged_df[[
        'MeterConID', 'Meter ID', 'MXUID', 'RegisterId', 'RouteNumber', 'Latitude', 'Longitude', 'Location'
    ]]

    final_df['RouteNumber'] = final_df['RouteNumber'].apply(lambda x: f'S{x}' if 'S' not in str(x) else str(x))
    final_df['RegisterId'] = final_df['RegisterId'].fillna('-')
    final_df['Location'] = final_df['Location'].fillna('NA')
    final_df['MeterConID'] = final_df['MeterConID'].apply(lambda x: str(x).zfill(10))
    return final_df


def save_to_csv(df, filename):
    """Save DataFrame to CSV."""
    df.to_csv(filename, index=False)
    print(f"{filename} is ready! Download the file and upload to Springbrook.")


def main(export_file, rni_file):
    date_suffix = get_date_suffix()
    export_df, rni_df = load_data(export_file, rni_file)
    export_df, rni_df = preprocess_data(export_df, rni_df)
    merged_df = merge_data(export_df, rni_df)
    final_df = format_final_df(merged_df)
    final_filename = f"SpringbrookUpload{date_suffix}.csv"
    save_to_csv(final_df, final_filename)


