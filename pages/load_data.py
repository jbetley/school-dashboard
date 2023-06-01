############################################
# ICSB Dashboard - Data & Global Variables #
############################################
# author:   jbetley
# version:  1.03
# date:     5/22/23

# TODO: Explore serverside disk caching for data loading
#https://community.plotly.com/t/the-value-of-the-global-variable-does-not-change-when-background-true-is-set-in-the-python-dash-callback/73835

import pandas as pd
import numpy as np
from .load_db import get_current_year, get_school_data
from .calculations import calculate_percentage, set_academic_rating, calculate_year_over_year

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
current_academic_year = get_current_year()

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

def process_academic_data(school, year):
    
    all_data = get_school_data(school)

    excluded_academic_years = int(current_academic_year) - int(year)

    # 'excluded years' is a list of YYYY strings (all years more
    # recent than selected year) that can be used to filter data
    # that should not be displayed
    excluded_years = []
    for i in range(excluded_academic_years):
        excluded_year = int(current_academic_year) - i
        excluded_years.append(excluded_year)
    
    school_data = all_data[~all_data["Year"].isin(excluded_years)]

    if len(school_data.index) != 0:
        school_info = school_data[["School Name"]].copy()

        # NOTE: Apparently we cannot filter columns by substring with SQLite because
        # it does not allow dynamic SQL - so we filter here
        school_data = school_data.filter(
            regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",
            axis=1,
        )

        # missing_mask returns boolean series of columns where column
        # is true if all elements in the column are equal to null
        # TODO: Need to drop columns with all 0 or 0.0 (as strings)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        school_data = school_data.fillna(0.0)
        school_data.loc[:, (school_data != 0).any(axis=0)]
        school_data.loc[:, (school_data != 0.0).any(axis=0)]
        print(school_data.T)

        
        print(school_data['Native Hawaiian or Other Pacific Islander|ELA Total Proficient'][0])

        # TODO: This is str
        print(type(school_data['Native Hawaiian or Other Pacific Islander|ELA Total Proficient'][1]))
        
        # TODO: This is float
        print(type(school_data['Native Hawaiian or Other Pacific Islander|ELA Total Tested'][0]))
        missing_mask = pd.isnull(school_data[school_data.columns]).all()
        missing_cols = school_data.columns[missing_mask].to_list()

        # now drop em
        school_data = school_data.dropna(axis=1, how='all')

        categories = ethnicity + subgroup + grades + ["School Total"]

        for s in subject:
            for c in categories:
                new_col = c + "|" + s + " Proficient %"
                proficient = c + "|" + s + " Total Proficient"
                tested = c + "|" + s + " Total Tested"

                if proficient not in missing_cols:
                    school_data[new_col] = calculate_percentage(
                        school_data[proficient], school_data[tested]
                    )

        if "IREAD Pass N" in school_data:
            
            school_data["IREAD Pass %"] = pd.to_numeric(
                school_data["IREAD Pass N"], errors="coerce"
            ) / pd.to_numeric(school_data["IREAD Test N"], errors="coerce")

            # If either Test or Pass category had a '***' value, the resulting value will be 
            # NaN - we want it to display '***', so we just fillna
            school_data["IREAD Pass %"] = school_data["IREAD Pass %"].fillna("***")

        # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
        school_data = school_data.filter(
            regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$",
            axis=1,
        )

        # add School Name column back
        school_data = pd.concat([school_data, school_info], axis=1, join="inner")

        school_data = school_data.reset_index(drop=True)
                            
        school_data.columns = school_data.columns.astype(str)

        # transpose dataframes and clean headers
        school_data = (
            school_data.set_index("Year")
            .T.rename_axis("Category")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        # school_data = school_data.fillna("No Data")

        school_data = school_data[school_data["Category"].str.contains("School Name") == False]
        
        final_data = school_data.reset_index(drop=True)
    else:
        final_data = pd.DataFrame()

    return final_data

def process_iread_data(data):

    iread_data = data[data["Category"] == "IREAD Pass %"]
    data = data.drop(data[data["Category"] == "IREAD Pass %"].index)

    if not iread_data.empty:
        
        iread_limits = [0.9, 0.8, 0.7, 0.7] 
        
        iread_data = (
            iread_data.set_index(["Category"])
            .add_suffix("School")
            .reset_index()
        )

        [
            iread_data.insert(
                i,
                str(iread_data.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
                iread_data.apply(
                    lambda x: set_academic_rating(
                        x[iread_data.columns[i - 1]], iread_limits, 1
                    ),
                    axis=1,
                ),
            )
            for i in range(iread_data.shape[1], 1, -1)
        ]

    iread_data = iread_data.fillna("No Data")
    iread_data.columns = iread_data.columns.astype(str)

def process_yearly_indicators(data):
    
    data.columns = data.columns.astype(str)
    
    category_header = data["Category"]
    data = data.drop("Category", axis=1)

    # temporarily store last column (first year of data chronologically) as
    # this is not used in first year-over-year calculation
    first_year = pd.DataFrame()
    first_year[data.columns[-1]] = data[data.columns[-1]]

    # calculate year over year values
    # loops over dataframe calculating difference between col and col+1 and inserts it
    # into the dataframe
    z = 1
    x = 0
    for y in range(0, (len(data.columns)-1)):
        values = calculate_year_over_year(data.iloc[:, x], data.iloc[:, x + 1])
        data.insert(loc = z, column = data.columns[x] + '+/-', value = values)
        z+=2
        x+=2
    
    data.columns = [i + 'School' if '+/-' not in i else i for i in data.columns]

    data.insert(loc=0, column="Category", value=category_header)
    data["Category"] = (data["Category"].str.replace(" Proficient %", "").str.strip())
    
    # Add first_year data back
    data[first_year.columns] = first_year

    # Create clean col lists - (YYYY + 'School') and (YYYY + '+/-')
    school_years_cols = list(data.columns[1:])
    
    # thresholds for academic ratings
    years_limits = [0.05, 0.02, 0, 0]

    [
        data.insert(
            i,
            str(data.columns[i - 1])[: 7 - 3]
            + "Rate"
            + str(i),
            data.apply(
                lambda x: set_academic_rating(
                    x[data.columns[i - 1]], years_limits, 1
                ),
                axis=1,
            ),
        )
        for i in range(data.shape[1], 1, -2)
    ]

    data = data.fillna("No Data")

    data.columns = data.columns.astype(str)

    # for the year_over_year df, drop the 'Rating' column for the last year_data column and rename it -
    # we don't use last Rating column becase we cannot calculate a 'year over year'calculation for the first year -
    # it is just the baseline

    data = data.iloc[:, :-2]
    data.columns.values[-1] = (data.columns.values[-1] + " (Initial Data Year)")

    # one last processing step is needed to ensure proper ratings. The set_academic_rating()
    # function assigns a rating based on the '+/-' difference value (either year over year
    # or as compared to corp). For the year over year comparison it is possible to get a
    # rating of 'Approaches Standard' for a '+/-' value of '0.00%' when the yearly ratings
    # are both '0'; and there is no case where we want a school to receive anything other
    # than a 'DNMS' for a 0% proficiency. However, the set_academic_rating() function does
    # not have access to the values used to calculate the difference value (so it cannot
    # tell if a 0 value is the result of a 0 proficiency). So we need to manually replace
    # any rating in the Rating column with 'DMNS' where the School proficiency value is '0.00%.'

    # because we are changing the value of one column based on the value of another (paired)
    # column, the way we do this is to create a list of tuples (a list of year and rating
    # column pairs), e.g., [('2022School', '2022Rating3')], and then iterate over the column pair

    # create the list of tuples
    # NOTE: the zip function stops at the end of the shortest list which automatically drops
    # the single 'Initial Year' column from the list. It returns an empty list if
    # school_years_cols only contains the Initial Year columns (because rating_cols will be empty)
    rating_cols = list(col for col in data.columns if "Rate" in col)
    col_pair = list(zip(school_years_cols, rating_cols))

    # iterate over list of tuples, if value in first item in pair is zero,
    # change the second value in pair to DNMS
    if col_pair:
        for k, v in col_pair:
            data[v] = np.where(
                data[k] == 0, "DNMS", data[v]
            )

    return data