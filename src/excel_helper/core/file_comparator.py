import pandas as pd
import os
from pathlib import Path
from excel_helper.utils import _write_txt_report
# ---------------------------------------------------------
#                  FUNZIONE DI CONFRONTO
# ---------------------------------------------------------


def compare_folders(folder1: str, folder2: str):
    """
    Confronta i file .csv presenti in due cartelle e:
      - Stampa a schermo eventuali differenze
      - Salva un file di testo ben formattato con sezioni e titoli ASCII.

    Parametri che confrontiamo (solo sulle differenze!):
      1) Colonne presenti solo in folder1 o solo in folder2.
      2) Differenze nel numero di righe.
      3) Mismatch di dtype.
      4) Se entrambi numeric, differenza di media (mean).
      5) Differenza nel numero di valori unici (unique).
    """

    # Lista in cui accumuliamo le stringhe di output
    output_lines = []

    # HEADER PRINCIPALE
    output_lines.append("======================================================================")
    output_lines.append("                     CSV FOLDER COMPARISON REPORT                     ")
    output_lines.append("======================================================================")
    output_lines.append(f"Folder1: {folder1}")
    output_lines.append(f"Folder2: {folder2}")
    output_lines.append("")

    # 1) Controllo directory
    if not os.path.isdir(folder1) or not os.path.isdir(folder2):
        msg = "ERRORE: Una delle cartelle specificate non è valida."
        output_lines.append(msg)
        _write_txt_report(output_lines)
        return

    # 2) Raccolta file .csv
    files_in_1 = {f for f in os.listdir(folder1) if f.lower().endswith('.csv')}
    files_in_2 = {f for f in os.listdir(folder2) if f.lower().endswith('.csv')}

    shared = sorted(files_in_1 & files_in_2)
    only_in_1 = sorted(files_in_1 - files_in_2)
    only_in_2 = sorted(files_in_2 - files_in_1)

    # 3) Riepilogo "macro"
    output_lines.append("------------------------------------------------------------------")
    output_lines.append(f"Shared files (N={len(shared)}): {shared}")
    output_lines.append(f"Only in folder1 (M={len(only_in_1)}): {only_in_1}")
    output_lines.append(f"Only in folder2 (X={len(only_in_2)}): {only_in_2}")
    output_lines.append("------------------------------------------------------------------\n")

    # 4) Confronto dettagliato dei file comuni
    for filename in shared:
        path1 = Path(folder1) / filename
        path2 = Path(folder2) / filename

        try:
            # low_memory=False per caricare tutto in memoria e ridurre DtypeWarning
            df1 = pd.read_csv(path1, low_memory=False)
            df2 = pd.read_csv(path2, low_memory=False)
        except Exception as e:
            output_lines.append(f"--- FILE '{filename}' ---")
            output_lines.append(f"  [ERRORE LETTURA] {e}")
            output_lines.append("")
            continue

        differences = []

        cols_1 = set(df1.columns)
        cols_2 = set(df2.columns)
        only_in_1_cols = sorted(cols_1 - cols_2)
        only_in_2_cols = sorted(cols_2 - cols_1)
        common_cols = sorted(cols_1 & cols_2)

        # 4.a) Colonne solo in una cartella
        if only_in_1_cols or only_in_2_cols:
            block = ["[COLUMNS]"]
            if only_in_1_cols:
                block.append(f"  - Columns only in folder1: {only_in_1_cols}")
            if only_in_2_cols:
                block.append(f"  - Columns only in folder2: {only_in_2_cols}")
            differences.append("\n".join(block))

        # 4.b) Numero di righe
        rows_1 = len(df1)
        rows_2 = len(df2)
        if rows_1 != rows_2:
            block = ["[ROWS]"]
            block.append(f"  - Different row count: folder1={rows_1}, folder2={rows_2} (diff={abs(rows_1 - rows_2)})")
            differences.append("\n".join(block))

        # 4.c) Confronto colonne comuni
        mismatch_report = []
        mean_report = []
        unique_report = []

        for col in common_cols:
            dtype1 = df1[col].dtype
            dtype2 = df2[col].dtype

            # c1) Mismatch di tipo
            if dtype1 != dtype2:
                mismatch_report.append(
                    f"  - Column '{col}' => dtype mismatch: folder1={dtype1}, folder2={dtype2}"
                )
                continue  # Se il dtype differisce, salto i confronti su media e unique

            # c2) Se numerica, differenza di media
            if pd.api.types.is_numeric_dtype(dtype1):
                mean1 = df1[col].mean(skipna=True)
                mean2 = df2[col].mean(skipna=True)
                mean_diff = mean1 - mean2
                if abs(mean_diff) > 1e-9:
                    mean_report.append(
                        f"  - Column '{col}' => different means: {mean1:.3f} vs {mean2:.3f} (diff={mean_diff:.3f})"
                    )

            # c3) Differenza nel numero di valori unici
            unique1 = df1[col].nunique(dropna=False)
            unique2 = df2[col].nunique(dropna=False)
            if unique1 != unique2:
                unique_report.append(
                    f"  - Column '{col}' => different unique counts: {unique1} vs {unique2} (diff={abs(unique1 - unique2)})"
                )

        # Se ci sono mismatch di dtype
        if mismatch_report:
            block = ["[DTYPE MISMATCH]"]
            block.extend(mismatch_report)
            differences.append("\n".join(block))

        # Se ci sono differenze di media
        if mean_report:
            block = ["[MEANS]"]
            block.extend(mean_report)
            differences.append("\n".join(block))

        # Se ci sono differenze nei unique
        if unique_report:
            block = ["[UNIQUES]"]
            block.extend(unique_report)
            differences.append("\n".join(block))

        # 4.d) Se abbiamo raccolto differenze, le aggiungiamo all'output
        if differences:
            output_lines.append(f"--- FILE '{filename}' ---")
            for d in differences:
                output_lines.append(d)
            output_lines.append("")  # riga vuota di separazione

    # 5) Salviamo il tutto su file .txt
    _write_txt_report(output_lines)
    # E stampiamo anche a schermo
    print("\n".join(output_lines))
