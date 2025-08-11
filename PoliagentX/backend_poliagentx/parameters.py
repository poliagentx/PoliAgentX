import pandas as pd
import tempfile
import os

def save_parameters_to_excel(parameters):
    df_params = pd.DataFrame(parameters)

    # Create a temp file that persists after closing (delete=False)
    temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)

    try:
        df_params.to_excel(temp_file.name, index=False)
        temp_path = temp_file.name
    finally:
        temp_file.close()  # Close the file so other processes can access it

    return temp_path
