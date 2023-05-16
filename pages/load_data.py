"""
ICSB Dashboard - Data Files
"""
import pandas as pd

import time
start_load = time.time()
school_index = pd.read_csv(r"data/school_index.csv", dtype=str)
school_academic_data_k8 = pd.read_csv(r"data/school_data_k8.csv", dtype=str)
all_academic_data_k8 = pd.read_csv(r'data/academic_data_k8.csv', dtype=str)
all_academic_data_hs = pd.read_csv(r"data/academic_data_hs.csv", dtype=str)
corporation_rates = pd.read_csv(r"data/corporate_rates.csv", dtype=str)
all_demographic_data = pd.read_csv(r"data/demographic_data.csv", dtype=str)
financial_ratios = pd.read_csv(r'data/financial_ratios.csv', dtype=str)
end_load = time.time()
print(f'Time to load data files: ' + str(end_load - start_load))

# all_academic_data_k8.to_parquet('tst.parquet', engine='fastparquet')