import argparse
import os
from xhelper import ExcelHelper
from xhelper import compare_folders

def main():
    parser = argparse.ArgumentParser(
        description="Process CSV files to manage columns that appear in multiple files"
    )
    parser.add_argument(
        '-f', '--folders',
        nargs='+',   # Permette uno o più percorsi
        help="One or two folder paths."
    )
    parser.add_argument(
        "-dvg", "--dvg-base-file",
        help = "Base file to use for dvg remapping"
    )
    args = parser.parse_args()

    # Se l'utente non specifica cartelle, errore
    if not args.folders:
        print("Error: no directory path entered. Please use '-h' flag to display help menu.")
        return 1

    if args.dvg_base_file:
        if not os.path.isfile(args.dvg_base_file):
            print("Error: dvg base file provided does not exist.")
            return 1

    # Se passiamo esattamente DUE cartelle, facciamo la comparazione
    if len(args.folders) == 2:
        folder1, folder2 = args.folders
        compare_folders(folder1, folder2)
        return 0  # Fine immediata dopo aver mostrato i risultati

    # Altrimenti, se passiamo UNA sola cartella, eseguiamo la logica preesistente
    elif len(args.folders) == 1:
        folder = args.folders[0]
        if not os.path.isdir(folder):
            print("Error: provided path is not a valid directory, exiting.")
            return 1

        xh = ExcelHelper(folder, dvg_base_file_path=args.dvg_base_file)
        xh.cmdloop()
    else:
        # Caso in cui l'utente abbia passato più di 2 cartelle
        print("Error: please provide either 1 or 2 folder paths (not more).")
        return 1

