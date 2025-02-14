import pandas as pd
from pathlib import Path
from typing import Dict
import os
import datetime


def load_csv_files(folder_path) -> Dict[str, pd.DataFrame]:
        """
        Carica i file CSV dalla cartella specificata.

        Returns:
            Dict[str, pd.DataFrame]: Dizionario {nome_file: DataFrame},
                                     or empty {}
        """
        data = {}
        csv_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.csv')]

        if not csv_files:
            return data  # Ritorna dizionario vuoto se non trova CSV

        print("\nLoading CSV files...")
        for file in csv_files:
            try:
                file_path = Path(folder_path) / file
                df = pd.read_csv(filepath_or_buffer=file_path, parse_dates=True)
                data[file] = df
                print(f"✓ Loaded: {file} ({len(df.columns)} columns, {len(df)} rows)")
            except Exception as e:
                print(f"✗ Error loading {file}: {e}")
        return data

def load_csv_file(file_path: str) -> pd.DataFrame:
    df = {}
    try:
        df = pd.read_csv(file_path, parse_dates=True, keep_default_na=False, na_values='')
        print(f"✓ Loaded: {file_path} ({len(df.columns)} columns, {len(df)} rows)")
    except Exception as e:
        print(f"✗ Error loading {file_path}: {e}")
    return df



def _write_txt_report(lines):
    """Scrive il report in un file .txt con data e ora nel nome, senza codici ANSI."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_name = f"compare_result_{timestamp}.txt"
    try:
        with open(txt_name, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
        print(f"\nReport also saved to '{txt_name}'")
    except Exception as e:
        print(f"Error writing TXT file '{txt_name}': {e}")