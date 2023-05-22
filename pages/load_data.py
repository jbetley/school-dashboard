############################################
# ICSB Dashboard - Data & Global Variables #
############################################
# author:   jbetley
# version:  1.03
# date:     5/22/23

# TODO: Explore serverside disk caching for data loading
#https://community.plotly.com/t/the-value-of-the-global-variable-does-not-change-when-background-true-is-set-in-the-python-dash-callback/73835

import pandas as pd

## Load Data Files ##
print("#### Loading Data. . . . . ####")

# NOTE: No K8 academic data exists for 2020
school_index = pd.read_csv(r"data/school_index.csv", dtype=str)
school_academic_data_k8 = pd.read_csv(r"data/school_data_k8.csv", dtype=str)
all_academic_data_hs = pd.read_csv(r"data/academic_data_hs.csv", dtype=str)
all_academic_data_k8 = pd.read_csv(r"data/academic_data_k8.csv", dtype=str)
corporation_rates = pd.read_csv(r"data/corporate_rates.csv", dtype=str)
all_demographic_data = pd.read_csv(r"data/demographic_data.csv", dtype=str)
financial_ratios = pd.read_csv(r'data/financial_ratios.csv', dtype=str)

# global integers
current_academic_year = int(school_academic_data_k8["Year"].unique().max())
max_display_years = 5

# global strings
subject = ["Math", "ELA"]

ethnicity = [
    "American Indian",
    "Asian",
    "Black",
    "Hispanic",
    "Multiracial",
    "Native Hawaiian or Other Pacific Islander",
    "White",
]

subgroup = [
    "Special Education",
    "General Education",
    "Paid Meals",
    "Free/Reduced Price Meals",
    "English Language Learners",
    "Non-English Language Learners",
]

grades = [
    "Grade 3",
    "Grade 4",
    "Grade 5",
    "Grade 6",
    "Grade 7",
    "Grade 8"
]

grades_all = [
    "Grade 3",
    "Grade 4",
    "Grade 5",
    "Grade 6",
    "Grade 7",
    "Grade 8",
    'Total',
    'IREAD Pass %'
]

grades_ordinal = [
    '3rd',
    '4th',
    '5th',
    '6th',
    '7th',
    '8th'
]