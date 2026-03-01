# This file implements pandads to read my data and return results based on research fields

import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

df = pd.read_csv('./data.csv')
pd.set_option('display.max_columns', None)

research_cols = ["research_field1", "research_field2", "research_field3", "research_field4", "research_field5", "research_field6"]

search_term = "labour"  # change as needed
mask = df[research_cols].apply(lambda col: col.str.contains(search_term, case=False, na=False)).any(axis=1)
foo = df[mask]

print(foo)

