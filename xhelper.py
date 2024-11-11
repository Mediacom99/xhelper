import cmd
import pandas as pd
import os
from typing import Dict, Set
import argparse
from collections import defaultdict
from pathlib import Path
import shlex


class ExcelHelper(cmd.Cmd):
    intro = 'Welcome to the excel column helper. Type help or ? to list commands.\n'
    prompt = '>>> '
    file = None

    def __init__ (self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self.modified = False
        self.data = self.load_csv_files()
        if not self.data:
            print(f"\nNo CSV files found in given directory: {self.folder_path}.\nQuitting xhelper...")
            quit()
        self.column_locations = self.map_column_locations()
        self.repeated_columns = self.find_repeated_columns()
        self.show_initial_summary()
    
    
    def map_column_locations(self) -> Dict[str, Set[str]]:
        """Create a mapping of each column to the files that contain it."""
        locations = defaultdict(set)
        for filename, df in self.data.items():
            for col in df.columns:
                locations[col].add(filename)
        return locations
    

    def load_csv_files(self) -> Dict[str, pd.DataFrame]:
        data = {}
        csv_files = [f for f in os.listdir(self.folder_path) if f.endswith('.csv')]
        if not csv_files:
            return data
    
        print("\nLoading CSV files...")
        for file in csv_files:
            try:
                file_path = Path(self.folder_path) / file 
                df = pd.read_csv(filepath_or_buffer=file_path, parse_dates=True)
                data[file] = df
                print(f"✓ Loaded: {file} ({len(df.columns)} columns, {len(df)} rows)")
            except Exception as e:
                print(f"✗ Error loading {file}: {e}")
        return data

    def show_initial_summary(self):
        """Show summary of loaded files and repeated columns."""
        print(f"\nLoaded {len(self.data)} files from: {self.folder_path}")
        print(f"Found {len(self.repeated_columns)} columns that appear in multiple files:")
        #self.show_repeated_columns()

    def show_repeated_columns(self):
        """Display All Columns That Appear In Multiple Files And Their Locations."""
        if not self.repeated_columns:
            print("\nNo columns appear in multiple files.")
            return
        sorted_cols = sorted(
            self.repeated_columns,
            key=lambda col: len(self.column_locations[col]),
            reverse=True
        )
        for column in sorted_cols:
            files = self.column_locations[column]
            print(f"\nColumn: '{column}' appears in {len(files)} files:")
            for file in files:
                print(f"  - {file}")
        return

    def show_all_columns(self):
        """Display All Columns That Appear In Multiple Files And Their Locations."""
        sorted_cols = sorted(
            self.column_locations.keys(),
            key=lambda col: len(self.column_locations[col]),
            reverse=True
        )
        for column in sorted_cols:
            files = self.column_locations[column]
            print(f"Column: '{column}' appears in {len(files)} files")
        return

    def find_repeated_columns(self) -> Set[str]:
        """Find columns that appear in multiple files."""
        return {col for col, files in self.column_locations.items() 
                if len(files) > 1}

    def pre_cmd(self, line):
        """Hook method executed before command processing."""
        if not line.strip():
            return line
            
        if not self.data and line.split()[0] not in ['quit', 'help']:
            print("\nNo files are currently loaded. Only 'quit' and 'help' commands are available.")
            return ''
        return line

    
    def do_show(self, arg):
        """Show details about columns.
        Usage: 
          show all  - Show all columns
          show rep  - Show all columns that appear in multiple files.
          show col 'name'  - Show details about a specific column"""
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
        elif args[0] == 'col' and args[1] != '':
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
        """Show detailed information about loaded files.
        Usage: 
            files         - Show basic file information
            files detail  - Show detailed file information including column names"""
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
            # Detailed view with column names
            for filename, df in self.data.items():
                print(f"\n{filename}:")
                print(f"  Rows: {len(df):,}")
                print(f"  Columns ({len(df.columns)}):")
                # Group columns by whether they appear in multiple files
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
            # Basic view
            for filename, df in self.data.items():
                shared = sum(1 for col in df.columns if col in self.repeated_columns)
                unique = len(df.columns) - shared
                print(f"\n{filename}:")
                print(f"  Rows: {len(df):,}")
                print(f"  Columns: {len(df.columns):,} total ({shared} shared, {unique} unique)")



    def do_rename(self, arg):
        """Rename a column in all files where it appears.
        Usage: rename 'old name' 'new_name'"""
        try:
            # Use shlex.split() to handle quoted strings as single arguments
            args = shlex.split(arg)
        except ValueError as e:
            print(f"\nError parsing arguments: {e}")
            return

        if len(args) != 2:
            print("\nUsage: rename old_name new_name")
            return
        
        old_name, new_name = args
        if old_name not in self.column_locations:
            print(f"\nColumn '{old_name}' not found in any file!")
            return

        files_modified = []
        for filename in self.column_locations[old_name]:
            df = self.data[filename]
            df.rename(columns={old_name: new_name}, inplace=True)
            files_modified.append(filename)

        print(f"\nRenamed column '{old_name}' to '{new_name}' in {len(files_modified)} files:")
        for file in files_modified:
            print(f"  - {file}")

        # Update our tracking
        self.column_locations[new_name] = self.column_locations.pop(old_name)
        if old_name in self.repeated_columns:
            self.repeated_columns.remove(old_name)
            self.repeated_columns.add(new_name)
        self.modified = True
    
    
    def do_delete(self, arg):
        """Delete a column from all files where it appears.
        Usage: delete column_name"""
        try:
            args = shlex.split(arg)
        except ValueError as e:
            print(f"Error parsing arguments: {e}")
            return

        if not arg:
            print("Usage: delete 'column name'")
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

        # Update our tracking
        del self.column_locations[col_to_del]
        self.repeated_columns.discard(col_to_del)
        self.modified = True
    
    
    def do_save(self, arg):
        """Save changes to all modified files"""
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


    def do_quit(self, arg):
        """Exit the program. Will prompt to save if there are unsaved changes."""
        if self.modified:
            while True:
                save = input("You have unsaved changes. Save before quitting? (y/n): ").lower()
                if save == 'y':
                    self.do_save("")
                    break
                elif save == 'n':
                    break
        print("\nThanks for using xhelper, goodbye!")
        return True



def main():
    parser = argparse.ArgumentParser(description="Process CSV files to manage columns that appear in multiple files")
    parser.add_argument('-f', "--folder", help="Folder containing CSV files to process")
    args = parser.parse_args()
    
    if args.folder is None:
        print("Error: no directory path entered. Please use '-h' flag to display help menu")
        return 1
    
    if not os.path.isdir(args.folder):
        print("Error: provided path is not a valid directory, exiting.")
        return 1
    
    xh = ExcelHelper(args.folder)
    xh.cmdloop()

if __name__ == '__main__':
    print("xhelper is starting...")
    main()
