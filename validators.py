import pandas as pd

def validate_excel(file_path):
    df = pd.read_excel(file_path)

    # Dummy logic: flag rows where 'Score' < 50
    if 'Score' in df.columns:
        df['Issue_Flag'] = df['Score'] < 50
    else:
        df['Issue_Flag'] = "Missing 'Score' column"

    return df
