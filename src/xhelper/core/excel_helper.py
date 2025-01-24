import cmd
import os
from dataclasses import dataclass
from typing import Dict, Set
from collections import defaultdict

import pandas as pd

from xhelper.core.actions import do_files, do_save, do_quit, do_show, do_delete, do_rename, do_convert_sas_to_csv, do_xml_generation
from xhelper.core.dvg_remap import do_dvg_remap
from xhelper.utils import load_csv_files, load_csv_file


class ExcelHelper(cmd.Cmd):
    """
    Classe principale che estende cmd.Cmd e fornisce un'interfaccia a riga di comando
    per gestire colonne in più file CSV (o convertirle da SAS).
    """
    intro = 'Welcome to the excel column helper. Type help or ? to list commands.\n'
    prompt = '>>> '
    file = None  # Per compatibilità con cmd.Cmd, se si volesse reindirizzare l'output.

    folder_path: str
    """Path to the folder containing the files to operate on"""

    dvg_base_file_path: str
    """Path to the dvg base file to use for dvg remapping"""

    dvg_file: pd.DataFrame
    """Dvg base file loaded onto pandas dataframe"""

    modified: bool
    """Flag to check if files have been modified (for save on exit)"""

    sas_files: list[str]
    """List of SAS file names"""

    data: dict[str, pd.DataFrame]
    """Mapping of file names to their corresponding DataFrames"""

    column_locations: dict[str, set[str]]
    """Mapping of column names to set of files containing that column"""

    repeated_columns: set[str]
    """Set of column names that appear in more than one file"""

    # Assign imported methods to class
    do_files = do_files
    do_save = do_save
    do_quit = do_quit
    do_show = do_show
    do_delete = do_delete
    do_rename = do_rename
    do_convert = do_convert_sas_to_csv
    do_xml_generation = do_xml_generation
    do_dvg_remap = do_dvg_remap


    def __init__(self, folder_path: str, dvg_base_file_path: str):
        super().__init__()

        ## CLASS VARIABLES
        self.folder_path: str = folder_path
        self.dvg_file: pd.DataFrame = load_csv_file(dvg_base_file_path)
        self.dvg_base_file_path: str = dvg_base_file_path
        self.modified: bool = False
        # 1. Carica i file CSV
        self.data: dict[str,pd.DataFrame] = load_csv_files(folder_path)
        # 2. Cerca eventuali file SASs
        self.sas_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith('.sas7bdat')]

        # 3. Se non ci sono né CSV né SAS, esci
        if not self.data and not self.sas_files:
            print(f"\nNo CSV or SAS (.sas7bdat) files found in directory: {self.folder_path}.\nQuitting xhelper...")
            quit()

        # 4. Se ho dei file CSV caricati, proseguo con la mappatura
        if self.data:
            self.column_locations: dict[str, set[str]] = self.map_column_locations()
            self.repeated_columns: set[str] = self.find_repeated_columns()
            self.show_initial_summary()
        else:
            # Caso in cui NON ci siano file CSV ma ci siano file SAS
            # self.data è vuoto, quindi saltiamo la parte di mappatura e summary
            self.column_locations = {}
            self.repeated_columns = set()
            print(
                f"\nNo CSV files found, but {len(self.sas_files)} SAS file(s) detected in directory: {self.folder_path}.")
            print("Use the 'convert' command to convert SAS files to CSV if you wish to load them.\n")

    def map_column_locations(self) -> Dict[str, Set[str]]:
        """
        Crea una mappatura di ogni colonna ai file che la contengono.

        Returns:
            Dict[str, Set[str]]: Dizionario {colonna: set di nomi_file}
        """
        locations = defaultdict(set)
        for filename, df in self.data.items():
            for col in df.columns:
                locations[col].add(filename)
        return locations

    def find_repeated_columns(self) -> Set[str]:
        """
        Trova le colonne che appaiono in più di un file.

        Returns:
            set[str]: Insieme di colonne ripetute.
        """
        return {
            col for col, files in self.column_locations.items()
            if len(files) > 1
        }

    def show_initial_summary(self):
        """Mostra un riepilogo iniziale dei file caricati e delle colonne ripetute."""
        print(f"\nLoaded {len(self.data)} files from: {self.folder_path}")
        print(f"Found {len(self.repeated_columns)} columns that appear in multiple files:")

    def show_repeated_columns(self):
        """Visualizza tutte le colonne che appaiono in più file e la lista dei file relativi."""
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

    def show_all_columns(self):
        """Visualizza tutte le colonne di tutti i file e la relativa frequenza."""
        sorted_cols = sorted(
            self.column_locations.keys(),
            key=lambda col: len(self.column_locations[col]),
            reverse=True
        )
        for column in sorted_cols:
            files = self.column_locations[column]
            print(f"Column: '{column}' appears in {len(files)} files")

    def pre_cmd(self, line):
        """
        Hook method eseguito prima della gestione di ogni comando.
        Permette di intercettare righe vuote o di bloccare comandi se non ci sono dati caricati.
        """
        if not line.strip():
            return line

        # Se non ci sono file caricati, gli unici comandi consentiti sono 'quit' e 'help'
        parts = line.strip().split()
        if not self.data and parts and parts[0] not in ['quit', 'help']:
            print("\nNo files are currently loaded. Only 'quit' and 'help' commands are available.")
            return ''
        return line


