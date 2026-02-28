import pandas as pd
pd.set_option('display.max_rows', None)
dataframe = pd.read_excel("sqlite_database/food_emission.xlsx", sheet_name = "emissions_per_stage_full", header = 4)
mask = dataframe["Applicable Region"].str.contains('uk', case = False)

ukDataframe = dataframe[mask]
ukDataframe = ukDataframe[['Source Product Name', 'Applicable Region', 'Data Quality Score (lower score = better)', 'Cradle to Farm Gate', 'Packaging', 'Processing', 'Transport']]
search: str = 'Tomato'
mask = ukDataframe['Source Product Name'].str.contains(search, case = False)

print(ukDataframe[mask])

