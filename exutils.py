import pandas as pd
import argparse
import os
from pathlib import Path
from collections import Counter

# Loads each file into its own dataframe, returns a collection of dataframes
def load_excel_files(folder_path):

    # List of xlsx files in folder_path
    excel_files = list(Path(folder_path).glob('*.csv'))
    
    if not excel_files:
        print(f"No excel files found in {folder_path}")
        return
    
    dfs = {} # We hold all files as a dictionary of the type: <file name> <-> <associated .xlsx file>
    for file in excel_files:
        try: 
            dfs[file.name] = pd.read_csv(filepath_or_buffer=file, parse_dates=True)
            print(f"Loaded excel file: {file.name}")
        except Exception as e:
            print(f"Error loading {file.name}: {e}")
            dfs[file.name] = {} # Either this or we return
            
    return dfs

#Print all unique column names and the counter of files with column with same name
def get_columns_name(data):
    all_columns = []
    unique_cols = []
    for df in data:
        for col_name, series in data[df].items():
            all_columns.append(col_name)
            
    col_counts = Counter(all_columns)

    print("Available unique columns:")
    for column, count in sorted(col_counts.items()):
        unique_cols.append(column)
        if count > 1:
            print(f"- {column} (appears in {count} files)")
        else:
            print(f"- {column}")
    return unique_cols


# Program entry point
# This main function sucks as fuck, should not use those loop like that
def main():
    parser = argparse.ArgumentParser(description = "Process excel files to delete/rename columns")
    parser.add_argument('-f', "--folder", help = "Folder containing excel files to process")
    args = parser.parse_args()

    if args.folder is None:
        print("Error: no directory path entered. Please use '-h' flag to display help menu")
        return 1
    else:
        if not os.path.isdir(args.folder):
            print("Error: provided path is not a valid directory, exiting.")
            return
    print("Folder path:", args.folder)

    data = load_excel_files(args.folder)

    all_columns = get_columns_name(data) #TODO should remove extension from filename

    # FIXME: handle this better, not breaking everytime something goes wrong

    while True:
        target_col = input("\nEnter column name to process (or 'quit' to exit): ").strip()
        if target_col.lower() == 'quit':
            return
        if target_col not in all_columns:
            print("Column not found in any file!")
            continue
        else:
            break
        

    # Get action to perform on that column
    while True:
        save_action = input("\nChoose action (rename/delete): ")
        if save_action not in ['rename', 'delete']:
            print("Invalid action. Please choose 'rename' or 'delete'")
            continue
        else:
            if save_action == 'rename':
                new_col_name = input("\nEnter new column name: ").strip()
                if new_col_name == '': break;
                for df in data:
                    for col_name, _ in data[df].items():
                        if col_name == target_col:
                            data[df].rename(columns={col_name: new_col_name}, inplace=True)
                            print(f"Renamed column {col_name} in {df}")
                break
            elif save_action == 'delete':
                for df in data:
                    for col_name, _ in data[df].items():
                        if col_name == target_col:
                            data[df].drop(columns=[target_col], inplace=True)
                            print(f"Dropped column {col_name} in {df}")
                break

    # Decide whether to save the current state by overwriting the modified files.
    while True:
        save_action = input("\nDo you want to save the current state ? Y/N ").strip()
        if save_action == 'Y':
            for df in data:
                try:
                    file_path = Path(args.folder) / df
                    data[df].to_csv(path_or_buf=file_path, index=False)
                    print(f"Saved changes to {df}")
                except Exception as e:
                    print(f"Error saving {df}: {e}")
            break
        elif save_action == 'N':
            print("Exiting without saving current state!")
            break # I could add another loop so that if the user does not want to save he can go back to choosing another column and so on
        else:
            continue

if __name__ == "__main__":
 main()

