import pandas as pd
import os
from pathlib import Path
import shlex
import datetime
import random
import pyreadstat
import csv


def do_show(self, arg):
    """
    Show details about columns.

    Usage:
      show all              - Show all columns
      show rep              - Show all columns that appear in multiple files.
      show col 'name'       - Show details about a specific column
    """
    try:
        args = shlex.split(arg)
    except ValueError as e:
        print(f"\nError parsing arguments: {e}")
        return

    if not args:
        print("\nPlease use command 'help show' for usage information")
        return

    if args[0] == 'rep':
        self.show_repeated_columns()
    elif args[0] == 'all':
        self.show_all_columns()
    elif args[0] == 'col' and len(args) > 1:
        column_name = args[1]
        if column_name in self.column_locations:
            files = self.column_locations[column_name]
            print(f"\nColumn '{column_name}' appears in {len(files)} files:")
            for file in files:
                print(f"  - {file}")
        else:
            print(f"\nColumn '{column_name}' not found in any file.")
    else:
        print("\nInvalid show command. Use 'help show' for usage information.")

def do_files(self, arg):
    """
    Show detailed information about loaded files.

    Usage:
        files         - Show basic file information (rows, columns, shared vs unique columns)
        files detail  - Show detailed file information including specific column names
    """
    if not self.data:
        print("\nNo files currently loaded.")
        return

    args = arg.split()

    total_rows = sum(len(df) for df in self.data.values())
    total_columns = sum(len(df.columns) for df in self.data.values())

    print(f"\nFolder: {self.folder_path}")
    print(f"Total files loaded: {len(self.data)}")
    print(f"Total rows across all files: {total_rows:,}")
    print(f"Total columns across all files: {total_columns:,}")
    print("\nFiles:")

    if args and args[0] == 'detail':
        # Vista dettagliata con nomi delle colonne
        for filename, df in self.data.items():
            print(f"\n{filename}:")
            print(f"  Rows: {len(df):,}")
            print(f"  Columns ({len(df.columns)}):")
            repeated = [col for col in df.columns if col in self.repeated_columns]
            unique = [col for col in df.columns if col not in self.repeated_columns]
            if repeated:
                print("  Shared columns:")
                for col in repeated:
                    count = len(self.column_locations[col])
                    print(f"    - {col} (appears in {count} files)")
            if unique:
                print("  Unique columns:")
                for col in unique:
                    print(f"    - {col}")
    else:
        # Vista di base
        for filename, df in self.data.items():
            shared = sum(1 for col in df.columns if col in self.repeated_columns)
            unique = len(df.columns) - shared
            print(f"\n{filename}:")
            print(f"  Rows: {len(df):,}")
            print(f"  Columns: {len(df.columns):,} total ({shared} shared, {unique} unique)")

def do_rename(self, arg):
    """
    Rename a column in all files where it appears.

    Usage:
        rename 'old name' 'new_name'
    """
    try:
        args = shlex.split(arg)
    except ValueError as e:
        print(f"\nError parsing arguments: {e}")
        return

    if len(args) != 2:
        print("\nUsage: rename 'old_name' 'new_name'")
        return

    old_name, new_name = args

    # 1) Verifica che la colonna old_name esista
    if old_name not in self.column_locations:
        print(f"\nColumn '{old_name}' not found in any file!")
        return

    # 2) Verifica se il new_name esiste già in una o più tabelle
    if new_name in self.column_locations:
        print(f"\nWarning: Column '{new_name}' already exists in one or more files.")
        print("This may lead to duplicate columns or data overwrite. Operation aborted.")
        return

    files_modified = []
    for filename in self.column_locations[old_name]:
        df = self.data[filename]
        df.rename(columns={old_name: new_name}, inplace=True)
        files_modified.append(filename)

    print(f"\nRenamed column '{old_name}' to '{new_name}' in {len(files_modified)} files:")
    for file in files_modified:
        print(f"  - {file}")

    # Aggiorna la mappatura
    self.column_locations[new_name] = self.column_locations.pop(old_name)
    if old_name in self.repeated_columns:
        self.repeated_columns.remove(old_name)
        self.repeated_columns.add(new_name)

    self.modified = True

def do_delete(self, arg):
    """
    Delete a column from all files where it appears.

    Usage:
        delete 'column_name'
    """
    try:
        args = shlex.split(arg)
    except ValueError as e:
        print(f"Error parsing arguments: {e}")
        return

    if not args:
        print("Usage: delete 'column_name'")
        return

    col_to_del = args[0]

    if col_to_del not in self.column_locations:
        print(f"Column '{col_to_del}' not found in any file!")
        return

    files_modified = []
    for filename in self.column_locations[col_to_del]:
        df = self.data[filename]
        df.drop(columns=[col_to_del], inplace=True)
        files_modified.append(filename)

    print(f"\nDeleted column '{col_to_del}' from {len(files_modified)} files:")
    for file in files_modified:
        print(f"  - {file}")

    # Aggiorna la mappatura
    del self.column_locations[col_to_del]
    self.repeated_columns.discard(col_to_del)
    self.modified = True

def do_save(self, arg):
    """
    Save changes to all modified files.

    Usage:
        save
    """
    if not self.modified:
        print("No changes to save!")
        return

    saved_files = []
    errors = []
    for filename, df in self.data.items():
        try:
            file_path = Path(self.folder_path) / filename
            df.to_csv(file_path, index=False)
            saved_files.append(filename)
        except Exception as e:
            errors.append((filename, str(e)))

    if saved_files:
        print(f"\nSuccessfully saved {len(saved_files)} files:")
        for file in saved_files:
            print(f"  - {file}")

    if errors:
        print("\nErrors occurred while saving:")
        for filename, error in errors:
            print(f"  - {filename}: {error}")

    self.modified = False

def do_convert(self, arg):
    """
    Convert all .sas7bdat files in the folder to .csv.

    Usage:
        convert
    """
    sas_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith('.sas7bdat')]

    if not sas_files:
        print(f"No .sas7bdat files found in {self.folder_path}.")
        return

    output_folder = Path(self.folder_path) / "converted_csv"
    output_folder.mkdir(exist_ok=True)

    print(f"Found {len(sas_files)} .sas7bdat files. Starting conversion...")

    for sas_file in sas_files:
        try:
            sas_path = Path(self.folder_path) / sas_file
            csv_file_name = sas_file.replace('.sas7bdat', '.csv')
            csv_path = output_folder / csv_file_name

            # Legge il file SAS
            df, meta = pyreadstat.read_sas7bdat(sas_path)

            # Salva come CSV
            df.to_csv(csv_path, index=False)
            print(f"✓ Converted: {sas_file} -> {csv_file_name}")

        except Exception as e:
            print(f"✗ Error converting {sas_file}: {e}")

    print(f"All files have been processed. Converted CSVs are in {output_folder}.")

def do_quit(self, arg):
    """
    Exit the program. Will prompt to save if there are unsaved changes.

    Usage:
        quit
    """
    if self.modified:
        while True:
            save = input("You have unsaved changes. Save before quitting? (y/n): ").lower()
            if save == 'y':
                self.do_save("")
                break
            elif save == 'n':
                break
            else:
                print("Please enter 'y' or 'n'.")
    print("\nThanks for using xhelper, goodbye!")
    return True

def do_xml_generation(self, arg):
    """
    Generate a CSV report about all columns across the loaded files.

    Usage:
        xml_generation

    Description:
        Creates a CSV with the following columns:
        1. Name:        The column name
        2. N_Files:     How many files the column appears in
        3. Files:       List of file names (comma-separated)
        4. Dtype:       List of datatypes found, e.g. "int,float,str"
        5. Mean:        Mean (only if column is numeric)
        6. CountUnique: Number of unique values (NaN/None excluded)
        7. Values:      If non-numeric, list all unique values (comma-separated).
                        If numeric, list 5 random values from the unique set.

    Notes:
    - NaN/None are excluded from unique counts and values listing.
    - Tries to auto-convert object columns to numeric if possible, to detect numeric values.
    """
    if not self.data:
        print("\nNo data is currently loaded. Cannot generate CSV.")
        return

    # 1) Nome del file di output con timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"xml_generation_{timestamp}.csv"

    # 2) Intestazione CSV
    header = ["Name", "N_Files", "Files", "Dtype", "Mean", "CountUnique", "Values"]

    # 3) Raccogliamo i dati riga per riga
    rows = []

    # 4) Iteriamo su tutte le colonne conosciute da self.column_locations
    #    (che mappa col -> set di file)
    all_columns = sorted(self.column_locations.keys())
    for col in all_columns:
        name_col = col
        files_for_col = self.column_locations[col]
        n_files = len(files_for_col)
        files_str = ",".join(sorted(files_for_col))

        # -----------------------------------------------------
        # Raccogliamo TUTTI i valori della colonna (di TUTTI i file)
        # e tentiamo una conversione numerica se possibile
        # -----------------------------------------------------
        all_values = []
        for filename in files_for_col:
            serie = self.data[filename][col]

            # (3) Riconoscimento automatico del tipo
            # Proviamo a convertire la serie in numerico
            # (inplace no, facciamo una serie temporanea)
            try:
                numeric_ser = pd.to_numeric(serie, errors='coerce')
                # Se dopo la conversione la maggior parte dei valori non è NaN,
                # allora supponiamo che la colonna sia numerica.
                # Altrimenti, meglio tenere i valori originali.
                count_non_nan = numeric_ser.notna().sum()
                if count_non_nan >= (0.5 * len(serie)):
                    # Almeno metà sono numeri validi
                    all_values.extend(numeric_ser.tolist())
                else:
                    # Teniamo la serie come string/oggetto
                    all_values.extend(serie.tolist())
            except Exception:
                # Se ci sono problemi, la lasciamo com'è
                all_values.extend(serie.tolist())

        # Filtriamo fuori i None e i NaN
        filtered_values = [x for x in all_values if pd.notnull(x)]

        # -----------------------------------------------------
        # 4) Determinare i dtypes "effettivi" tra questi valori
        #    (tipi Python, es. int, float, str, ecc.)
        # -----------------------------------------------------
        dtypes_set = set(type(x) for x in filtered_values)
        dtypes_str = ",".join(sorted(t.__name__ for t in dtypes_set))

        # -----------------------------------------------------
        # 5) Mean: se TUTTI i valori sono int o float, calcoliamo la media
        # -----------------------------------------------------
        # (2) e (3) comportano che siamo già stati furbi e convertito i numeri
        # Se trova str o bool, salta la media
        is_entirely_numeric = dtypes_set.issubset({int, float})
        if is_entirely_numeric and filtered_values:
            numeric_values = [v for v in filtered_values
                              if isinstance(v, (int, float))]
            if numeric_values:
                mean_val = sum(numeric_values) / len(numeric_values)
                mean_str = f"{mean_val:.3f}"
            else:
                mean_str = ""
        else:
            mean_str = ""

        # -----------------------------------------------------
        # 6) CountUnique: n. di valori unici (senza None/NaN)
        # -----------------------------------------------------
        unique_values = set(filtered_values)
        count_unique_str = str(len(unique_values))

        # -----------------------------------------------------
        # 7) Values:
        #    Se numerica => 5 random values
        #    Altrimenti => elenco completo di unique
        #    (Tronchiamo se è troppo lungo, volendo)
        # -----------------------------------------------------
        if is_entirely_numeric:
            numeric_values = sorted(unique_values)
            sample_size = min(5, len(numeric_values))
            sample_vals = random.sample(numeric_values, sample_size) if sample_size else []
            values_str = ",".join(str(x) for x in sorted(sample_vals))
        else:
            # Colonna non numerica
            str_values = [str(v) for v in unique_values]
            str_values_sorted = sorted(str_values)
            # Se vuoi troncare:
            # big_str = ",".join(str_values_sorted)
            # values_str = big_str[:5000]  # max 5000 caratteri, ad esempio
            values_str = ",".join(str_values_sorted)

        # Costruiamo la riga finale
        row = [
            name_col,  # Name
            str(n_files),  # N_Files
            files_str,  # Files
            dtypes_str,  # Dtype
            mean_str,  # Mean
            count_unique_str,  # CountUnique
            values_str  # Values
        ]
        rows.append(row)

    # -----------------------------------------------------
    # Salviamo i risultati in un CSV
    # -----------------------------------------------------
    try:
        with open(output_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            writer.writerows(rows)
        print(f"\nXML-generation CSV successfully saved as: {output_filename}")
        print(f"Generated {len(rows)} rows (one per unique column).")
    except Exception as e:
        print(f"\nError while writing the CSV file: {e}")