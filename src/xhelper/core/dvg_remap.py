import os

import pandas as pd

from xhelper import core
def do_dvg_remap(self: "core.excel_helper.ExcelHelper", arg):
    """
    1. map column name (question) -> subset number
    2. map (subset, dvg_value) -> string
    3. substitute dvg_value in db:
        col_name -> subset number -> dvg_value -> string
    """

    output_dir = "transformed_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    dvg_df = self.dvg_file
    structure_df = self.data["dbstructure.csv"]

    # 1.  DCM_name, Question (DVG_NAME) -> DVG_SUBSET_NM
    col_subset_mapping = {}
    for _, row in structure_df.iterrows():
        if pd.notna(row['DVG_SUBSET_NM']):
            col_subset_mapping[(row['DCM_name'], row['Question'])] = row['DVG_SUBSET_NM']

    # 2. DCM_name, DVG_NAME, DVG_SUBSET, DVG_VALUE -> DVG_LVALUE
    val_mapping = {}
    for _, row in dvg_df.iterrows():
        key = (row['DVG_NAME'], row['DVG_SUBSET_NM'], str(row['DVG_VAL']))
        val_mapping[key] = row['DVG_LVAL']

    print(col_subset_mapping)
    print(" ")
    print(val_mapping)

    #Join this maps so that we have:
    # DCM_NAME, DVG_NAME (colonna), DVG_VAL -> DVG_LVAL


    for name, df in self.data.items():
        if name in ['dbstructure.csv', 'dvg.csv']:
            continue

        transformed_df = df.copy()
        # Process each column that needs transformation
        # Make sure to check also for the name of the DCM
        for col in transformed_df.columns:
            if col in col_subset_mapping:
                print(f"Column {col} in file {name} has been updated")
                subset = col_subset_mapping[col]

                def map_value(x):
                    if pd.isna(x):
                        return x
                    key_loc = (name, col, subset, str(x))
                    return val_mapping.get(key_loc)

                transformed_df[col] = transformed_df[col].apply(map_value)
                output_path = os.path.join(output_dir, name)
                transformed_df.to_csv(output_path, index=False)

    return
