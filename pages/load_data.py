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
import itertools
from .load_db import get_current_year, get_school_index, get_k8_school_academic_data, get_demographic_data, \
    get_high_school_academic_data, get_k8_corporation_academic_data, get_graduation_data, \
        get_high_school_corporation_academic_data, get_letter_grades, get_adult_high_school_metric_data
from .calculations import calculate_percentage, calculate_difference, calculate_year_over_year, \
    set_academic_rating

pd.set_option('display.max_rows', None)

## Load Data Files ##
print("#### Loading Data. . . . . ####")

# NOTE: No K8 academic data exists for 2020
school_index = pd.read_csv(r"data/school_index.csv", dtype=str)
school_academic_data_k8 = pd.read_csv(r"data/school_data_k8.csv", dtype=str)
all_academic_data_hs = pd.read_csv(r"data/academic_data_hs.csv", dtype=str)
all_academic_data_k8 = pd.read_csv(r"data/academic_data_k8.csv", dtype=str)
corporation_rates = pd.read_csv(r"data/corporate_rates.csv", dtype=str)
all_demographic_data = pd.read_csv(r"data/demographic_data.csv", dtype=str)

# TODO: NEED FINANCIAL RATIOS
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
    "Free or Reduced Price Meals",
    "English Language Learners",
    "Non English Language Learners",
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

### Start Helper Functions ###

def get_excluded_years(year):
    # 'excluded years' is a list of year strings (format YYYY) of all years
    # that are more recent than the selected year. it is used to filter data
    excluded_years = []

    excluded_academic_years = int(current_academic_year) - int(year)

    for i in range(excluded_academic_years):
        excluded_year = int(current_academic_year) - i
        excluded_years.append(excluded_year)
    
    return excluded_years

def get_attendance_data(data, year):

    excluded_years = get_excluded_years(year)

    demographic_data = data[~data["Year"].isin(excluded_years)]
    attendance_data = demographic_data[["Year", "Avg Attendance"]]

    # drop years with no data
    attendance_data = attendance_data[attendance_data['Avg Attendance'].notnull()]

    attendance_rate = (attendance_data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

    attendance_rate['Category'] =  attendance_rate['Category'].replace(['Avg Attendance'], 'Attendance Rate')

    attendance_rate = attendance_rate.fillna('No Data')

    attendance_rate.columns = attendance_rate.columns.astype(str)

    for col in attendance_rate.columns:
        attendance_rate[col] = pd.to_numeric(attendance_rate[col], errors='coerce').fillna(attendance_rate[col]).tolist()

    return attendance_rate

def get_attendance_metrics(school, year):

    selected_school = school_index.loc[school_index["School ID"] == school]
    corp_id = selected_school['GEO Corp'].values[0]

    corp_demographics = get_demographic_data(corp_id)
    school_demographics = get_demographic_data(school)
    corp_attendance_rate = get_attendance_data(corp_demographics, year)
    school_attendance_rate = get_attendance_data(school_demographics, year)    

    corp_attendance_rate = (corp_attendance_rate.set_index(["Category"]).add_suffix("Corp Avg").reset_index())
    school_attendance_rate = (school_attendance_rate.set_index(["Category"]).add_suffix("School").reset_index())
    school_attendance_rate = school_attendance_rate.drop("Category", axis=1)
    corp_attendance_rate = corp_attendance_rate.drop("Category", axis=1)

    # concat the two df's and reorder so that the columns alternate
    attendance_metrics = pd.concat([school_attendance_rate, corp_attendance_rate], axis=1)
    reordered_cols = list(sum(zip(school_attendance_rate.columns, corp_attendance_rate.columns), ()))
    attendance_metrics = attendance_metrics[reordered_cols]

    # loops over dataframe calculating difference between a pair of columns, inserts the result in
    # the following column, and then skips over the calculated columns to the next pair
    y = 0
    z = 2
    end = int(len(attendance_metrics.columns)/2)

    for x in range(0, end):
        values = calculate_year_over_year(attendance_metrics.iloc[:, y], attendance_metrics.iloc[:, y + 1])
        attendance_metrics.insert(loc = z, column = attendance_metrics.columns[y][0:4] + '+/-', value = values)
        y+=3
        z+=3

    attendance_metrics.insert(loc=0, column="Category", value='1.1.a. Attendance Rate')

    # threshold limits for rating calculations
    attendance_limits = [
        0,
        -0.01,
        -0.01,
    ]

    # NOTE: Calculates and adds an accountability rating ('MS', 'DNMS', 'N/A', etc)
    # as a new column to existing dataframe:
    #   1) the loop ('for i in range(attendance_data_metrics.shape[1], 1, -3)')
    #   counts backwards by -3, beginning with the index of the last column in
    #   the dataframe ('attendance_data_metrics.shape[1]') to '1' (actually '2'
    #   as range does not include the last number). These are indexes, so the
    #   loop stops at the third column (which has an index of 2);
    #   2) for each step, the code inserts a new column, at index 'i'. The column
    #   header is a string that is equal to 'the year (YYYY) part of the column
    #   string (attendance_data_metrics.columns[i-1])[:7 - 3]) + 'Rating' + 'i'
    #   (the value of 'i' doesn't matter other than to differentiate the columns) +
    #   the accountability value, a string returned by the set_academic_rating() function.
    #   3) the set_academic_rating() function calculates an 'accountability rating'
    #   ('MS', 'DNMS', 'N/A', etc) taking as args:
    #       i) the 'value' to be rated. this will be from the 'School' column, if
    #       the value itself is rated (e.g., iread performance), or the difference
    #       ('+/-') column, if there is an additional calculation required (e.g.,
    #       year over year or compared to corp);
    #       ii) a list of the threshold 'limits' to be used in the calculation; and
    #       iii) an integer 'flag' which tells the function which calculation to use.
    [
        attendance_metrics.insert(
            i,
            str(attendance_metrics.columns[i - 1])[: 7 - 3]
            + "Rate"
            + str(i),
            attendance_metrics.apply(
                lambda x: set_academic_rating(
                    x[attendance_metrics.columns[i - 1]], attendance_limits, 3
                ),
                axis=1,
            ),
        )
        for i in range(attendance_metrics.shape[1], 1, -3)
    ]

    return attendance_metrics

def calculate_graduation_rate(values):
    
    data = values.copy()

    cohorts = data[data.columns[data.columns.str.contains(r'Cohort Count')]].columns.tolist()

    for cohort in cohorts:
        if cohort in data.columns:
            # get Category + Subject string
            cat_sub = cohort.split('|Cohort Count')[0]
            data[cat_sub + " Graduation Rate"] = calculate_percentage(data[cat_sub + "|Graduates"], data[cohort])

    # NOTE: Orig Code
    # grad_categories = ethnicity + subgroup + ["Total"]
    
    # for g in grad_categories:
    #     new_col = g + " Graduation Rate"
    #     graduates = g + "|Graduates"
    #     cohort = g + "|Cohort Count"

    #     if cohort in data.columns:
    #         data[new_col] = calculate_percentage(data[graduates], data[cohort])

    return data

def calculate_strength_of_diploma(data):
    # NOTE: Not Currently Used
    data["Strength of Diploma"] = pd.to_numeric((data["Non Waiver|Cohort Count"] * 1.08)) \
         / pd.to_numeric(data["Total|Cohort Count"])

    return data

def calculate_eca_rate(values):
    data = values.copy()

    tested = data[data.columns[data.columns.str.contains(r'Test N')]].columns.tolist()

    for test in tested:
        if test in data.columns:
            # get Category + Subject string
            cat_sub = test.split(' Test N')[0]
            data[cat_sub + " Pass Rate"] = calculate_percentage(data[cat_sub + " Pass N"], data[test])

    # NOTE: Original Code
    # eca_categories = ["Grade 10|ELA", "Grade 10|Math"]

    # for e in eca_categories:
    #     new_col = e + " Pass Rate"
    #     passN = e + " Pass N"
    #     testN = e + " Test N"

    #     data[new_col] = calculate_percentage(data[passN], data[testN])
    
    return data

def calculate_sat_rate(values):
# NOTE: All nulls should have already been filtered out by filter_high_school_academic_data()
    data = values.copy()

    tested = data[data.columns[data.columns.str.contains(r'Total Tested')]].columns.tolist()

    for test in tested:
        if test in data.columns:
            
            # get Category + Subject string
            cat_sub = test.split(' Total Tested')[0]
            data[cat_sub + ' Benchmark %'] = calculate_percentage(data[cat_sub + ' At Benchmark'], data[test])

    ## NOTE: Original Code
    # sat_categories = ethnicity + subgroup + ["School Total"]
    # sat_subject = ['EBRW','Math','Both']

    # for ss in sat_subject:
    #     for sc in sat_categories:
    #         new_col = sc + "|" + ss + " Benchmark %"
    #         at_benchmark = sc + "|" + ss + " At Benchmark"
    #         total_tested = sc + "|" + ss + " Total Tested"

    #         if total_tested in data.columns:
    #             data[new_col] = calculate_percentage(data[at_benchmark], data[total_tested])

    return data

# TODO: This is slow. Refactor
import time

def calculate_proficiency(values):
    t2 = time.process_time()
# Calculates proficiency. If Total Tested == 0 or NaN or if Total Tested > 0, but Total Proficient is
# NaN, all associated columns are dropped
    data = values.copy()

    # Get a list of all 'Total Tested' columns except those for ELA & Math
    tested_categories = data[data.columns[data.columns.str.contains(r'Total Tested')]].columns.tolist()
    tested_categories = [i for i in tested_categories if 'ELA and Math' not in i]

    for total_tested in tested_categories:
        if total_tested in data.columns:
            
            cat_sub = total_tested.split(' Total Tested')[0]
            total_proficient = cat_sub + ' Total Proficient'
            proficiency = cat_sub + ' Proficient %'

            # drop the entire category if ('Total Tested' == 0 or NaN) or if 
            # ('Total Tested' > 0 and 'Total Proficient' is NaN. A 'Total Proficient'
            # value of NaN means it was a '***' before being converted to numeric
            # we use sum/all because there could be one or many columns
            if (data[total_tested].sum() == 0 or pd.isna(data[total_tested]).all()) | \
                (data[total_tested].sum() > 0 and pd.isna(data[total_proficient]).all()):

                data = data.drop([total_tested, total_proficient], axis=1)
            else:
                data[proficiency] = calculate_percentage(data[total_proficient], data[total_tested])

    process_prof = time.process_time() - t2
    print(f'Time to calculate proficiency: ' + str(process_prof))

    return data

### End Helper Functions ###

### Dataframe Formatting Functions ###
def process_k8_academic_data(all_data, year, school):
    
    school_information = get_school_index(school)

    # use these to determine if data belongs to school or corporation
    school_geo_code = school_information["GEO Corp"].values[0]
    data_geo_code = all_data['Corporation ID'][0]

    excluded_years = get_excluded_years(year)

    if excluded_years:
        data = all_data[~all_data["Year"].isin(excluded_years)].copy()
    else:
        data = all_data.copy()

    # school data has School Name column, corp data does not
    if len(data.index) != 0:

        # it is 'corp' data where the value of 'Corporation ID' in the df is equal
        # to the value of the school's 'GEO Corp'.
        if data_geo_code == school_geo_code:
            school_info = data[["Corporation Name"]].copy()

            # corporation data: coerce strings ('***' and '^') to NaN (for
            # both masking and groupby.sum() purposes)
            for col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
       
        else:
       
            school_info = data[["School Name"]].copy()
            
            # school data: coerce, but keep strings ('***' and '^')
            for col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(data[col])

        # NOTE: Apparently we cannot filter columns by substring with SQLite because
        # it does not allow dynamic SQL - so we filter here
        data = data.filter(regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",axis=1)

        if "School Total|ELA Total Tested" in data.columns:

            data = calculate_proficiency(data)

        if "IREAD Pass N" in data.columns:
            data["IREAD Pass %"] = pd.to_numeric(data["IREAD Pass N"], errors="coerce") \
                / pd.to_numeric(data["IREAD Test N"], errors="coerce")

            # If either Test or Pass category had a '***' value, the resulting value will be 
            # NaN - we want it to display '***', so we just fillna
            data["IREAD Pass %"] = data["IREAD Pass %"].fillna("***")

        # re-calculate and replace total Math & ELA proficiency values using only the
        # grades for which the school has data (after the masking step above). This
        # ensures an apples to apples comparison with traditional school corporations.
        if data_geo_code == school_geo_code:
            adjusted_total_math_proficient = data.filter(regex=r"Grade.+?Math Total Proficient")
            adjusted_total_math_tested = data.filter(regex=r"Grade.+?Math Total Tested")

            data["School Total|Math Proficient %"] = adjusted_total_math_proficient.sum(axis=1) \
                / adjusted_total_math_tested.sum(axis=1)

            adjusted_total_ela_proficient = data.filter(regex=r"Grade.+?ELA Total Proficient")
            adjusted_total_ela_tested = data.filter(regex=r"Grade.+?ELA Total Tested")
            data["School Total|ELA Proficient %"] = adjusted_total_ela_proficient.sum(axis=1) \
                / adjusted_total_ela_tested.sum(axis=1)

        # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
        data = data.filter(regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$", axis=1)

        # add School Name column back
        # school data has School Name column, corp data does not
        if len(school_info.index) > 0:
            data = pd.concat([data, school_info], axis=1, join="inner")

        data = data.reset_index(drop=True)  #TODO: NEED THIS ONE?

        # transpose dataframes and clean headers    
        data.columns = data.columns.astype(str)
        data = (data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())
        data = data[data["Category"].str.contains("School Name") == False]
        data = data.reset_index(drop=True)

    else:
    
        data = pd.DataFrame()

    return data

def filter_high_school_academic_data(data):
# Iterates over all 'Total Tested' columns - if the value of 'Total Tested' for a
# particular 'Category' and 'Subject' (e.g., 'Multiracial|Math) is 0, drop all
# columns (e.g., 'Approaching Benchmark', 'At Benchmark', etc.) for that 'Category'
# and 'Subject'
    if len(data) > 0:
        data = data.replace({"^": "***"})

        # school data: coerce to numeric but keep strings ('***')
        for col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(data[col])

        # Separate SAT data categories and Other data categories into separate dfs
        sat_data = data[data.columns[data.columns.str.contains(r'Year|Benchmark|Total Tested')]].copy()
        other_data = data[data.columns[~data.columns.str.contains(r'Benchmark|Total Tested')]].copy()
        
        # clean SAT data
        tested_cols = sat_data.filter(like='Total Tested').columns.tolist()
        drop_columns=[]
        for col in tested_cols:
            if sat_data[col].values[0] == 0:
                matching_cols = sat_data.columns[pd.Series(sat_data.columns).str.startswith(col.split(' Total')[0])]
                drop_columns.append(matching_cols.tolist())                     

        drop_all = [i for sub_list in drop_columns for i in sub_list]

        sat_data = sat_data.drop(drop_all, axis=1).copy()

        # clean 'other' data
        # NOTE: Need to do this separately because we want to keep '0' values for SAT
        # Categories with Tested students.
        valid_column_mask = other_data.any()
        # valid_mask = ~pd.isnull(data[data.columns]).all()        

        other_data = other_data[other_data.columns[valid_column_mask]]
        
        final_data = other_data.merge(sat_data, how = 'outer')
    
    else:
        final_data = pd.DataFrame()

    return final_data
    
def process_high_school_academic_data(all_data, year, school):

    school_information = get_school_index(school)

    # use these to determine if data belongs to school or corporation
    school_geo_code = school_information["GEO Corp"].values[0]
    data_geo_code = all_data['Corporation ID'][0]

    excluded_years = get_excluded_years(year)

    if excluded_years:
        data = all_data[~all_data["Year"].isin(excluded_years)].copy()
    else:
        data = all_data.copy()

    school_type = data["School Type"].values[0]

    if len(data.index) != 0:
        # We identify 'corp' data where the value of 'Corporation ID' in the df is equal
        # to the value of the school's 'GEO Corp'.
        if data_geo_code == school_geo_code:
            school_info = data[["Corporation Name"]].copy()
        else:
            school_info = data[["School Name"]].copy()
            
            # school data: coerce, but keep strings ('***' and '^')
            for col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(data[col])

        # Categories to keep: 'Total Tested', 'Below Benchmark', 'Approaching Benchmark', 'At Benchmark', & 'Benchmark %' (SAT);
        #   'Pass N' & 'Test N' (Grade 10 ECA); 'Cohort Count' & 'Graduates' (Graduation Rate); 'AHS|CCR' & 'AHS|Grad All' (AHS Grad Rate)
        data = data.filter(regex=r"Cohort Count$|Graduates$|AHS|Pass N|Test N|Benchmark|Total Tested|^Year$", axis=1)

        # remove 'ELA and Math' columns (NOTE: Comment this out to retain 'ELA and Math' columns)
        data = data.drop(list(data.filter(regex="ELA and Math")), axis=1)

        # mask of valid columns only
        # valid_mask = data.any()
        # valid_mask = ~pd.isnull(data[data.columns]).all()
        # data = data[data.columns[valid_mask]]

        if data_geo_code == school_geo_code:

            # group corp dataframe by year and sum all rows for each category
            data = data.groupby(["Year"]).sum(numeric_only=True)
            # reverse order of rows (Year) and reset index to bring Year back as column
            data = data.loc[::-1].reset_index()

        # Calculate Grad Rate
        if "Total|Cohort Count" in data.columns:
            data = calculate_graduation_rate(data)

        # Calculate Non Waiver Grad Rate #
        # NOTE: In spring of 2020, SBOE waived the GQE requirement for students in the
        # 2020 cohort who where otherwise on schedule to graduate, so, for the 2020
        # cohort, there were no 'waiver' graduates (which means no Non Waiver data).
        # so we replace 0 with NaN (to ensure a NaN result rather than 0)
        # if "Non Waiver|Cohort Count" in data.columns:
        #     data = calculate_nonwaiver_graduation_rate(data)

        # Calculate ECA (Grade 10) Rate #
        if "Grade 10|ELA Test N" in data.columns:
            data = calculate_eca_rate(data)

        # Calculate SAT Rates #
        if "School Total|EBRW Total Tested" in data.columns:
            data = calculate_sat_rate(data)

        # Calculate AHS Only Data #
        # NOTE: All other values pulled from HS dataframe required for AHS calculations should go here        

        # CCR Rate #
        if school_type == "AHS":

            if 'AHS|CCR' in data.columns:
                data["AHS|CCR"] = pd.to_numeric(data["AHS|CCR"], errors="coerce")

            if 'AHS|Grad All' in data.columns:                
                data["AHS|Grad All"] = pd.to_numeric(data["AHS|Grad All"], errors="coerce")

            if {'AHS|CCR','AHS|Grad All'}.issubset(data.columns):
                data["CCR Percentage"] = (data["AHS|CCR"] / data["AHS|Grad All"])

        # Prepare final dataframe #

        # filter
        data = data.filter(
            regex=r"^Category|Graduation Rate$|CCR Percentage|Pass Rate$|Benchmark %|Below|Approaching|At|^CCR Percentage|Total Tested|^Year$", # ^Strength of Diploma
            axis=1,
        )

        school_info = school_info.reset_index(drop=True)
        data = data.reset_index(drop=True)

        data = pd.concat([data, school_info], axis=1, join="inner")

        data.columns = data.columns.astype(str)

        # transpose dataframes and clean headers
        data = (data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

        # State/Federal grade rows not used
        data = data[data["Category"].str.contains("State Grade|Federal Rating|School Name") == False]
        
        data = data.reset_index(drop=True)

        # make sure there are no lingering NoneTypes 
        data = data.fillna(value=np.nan)

    else:

        data = pd.DataFrame()

    return data


### Calculate Accountability Metrics ###

def calculate_adult_high_school_metrics(school):
    # AHS metrics is such a small subset of all metrics, instead of pulling in entire HS DF, we just pull the three
    # datapoints we need directly from the DB.

    data = get_adult_high_school_metric_data(school)

    if len(data) > 0:
        data.columns = data.columns.astype(str)

        data["CCR Percentage"] = pd.to_numeric(data["AHS|CCR"]) / pd.to_numeric(data["AHS|Grad All"])
        
        ahs_data = data [['Year', 'CCR Percentage']]

        # transpose dataframe and clean headers
        ahs_data = (ahs_data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())
            
        # format for multi-header display
        ahs_data.columns = ahs_data.columns.astype(str)
        data_columns = list(ahs_data.columns[:0:-1])
        data_columns.reverse()

        ahs_data = (ahs_data.set_index(["Category"]).add_suffix("School").reset_index())

        ccr_limits = [0.5, 0.499, 0.234]
        [
            ahs_data.insert(
                i,
                str(data_columns[i - 2]) + "Rate" + str(i),
                ahs_data.apply(
                    lambda x: set_academic_rating(
                        x[ahs_data.columns[i - 1]], ccr_limits, 2
                    ),
                    axis=1,
                ),
            )
            for i in range(ahs_data.shape[1], 1, -1)
        ]

        school_letter_grades = get_letter_grades(school)
        school_letter_grades = (school_letter_grades.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

        # strip second row (Federal Rating)
        ahs_state_grades = school_letter_grades.iloc[0:1, :]

        ahs_state_grades.columns = ahs_state_grades.columns.astype(str)
        ahs_state_grades = (ahs_state_grades.set_index(["Category"]).add_suffix("School").reset_index())

        # ensure state_grades df contains same years of data as ahs_metric_cols
        ahs_state_grades = ahs_state_grades.loc[:,ahs_state_grades.columns.str.contains("|".join(data_columns + ["Category"]))]

        letter_grade_limits = ["A", "B", "C", "D", "F"]

        [
            ahs_state_grades.insert(
                i,
                str(data_columns[i - 2]) + "Rate" + str(i),
                ahs_state_grades.apply(
                    lambda x: set_academic_rating(
                        x[ahs_state_grades.columns[i - 1]],
                        letter_grade_limits,
                        4,
                    ),
                    axis=1,
                ),
            )
            for i in range(ahs_state_grades.shape[1], 1, -1)
        ]

        # concatenate and add metric column
        ahs_data = pd.concat([ahs_state_grades, ahs_data])
        ahs_data = ahs_data.reset_index(drop=True)
        ahs_metric_nums = ["1.1.", "1.3."]
        ahs_data.insert(loc=0, column="Metric", value=ahs_metric_nums)
    
    else:
        ahs_data = pd.DataFrame()

    return ahs_data

def merge_high_school_data(all_school_data, all_corp_data, year):

    all_school_data.columns = all_school_data.columns.astype(str)
    all_corp_data.columns = all_corp_data.columns.astype(str)

    # Add State Graduation Average to both dataframes
    state_grad_average = get_graduation_data()
    state_grad_average = state_grad_average.loc[::-1].reset_index(drop=True)
    
    # add to corp data by transposing, mirroring the columns, dropping the 'Year' row, and
    # concatenating together
    state_grad_average = state_grad_average.T.reset_index()
    state_grad_average = state_grad_average.drop(0)
    state_grad_average.columns = all_corp_data.columns
    all_corp_data = pd.concat([all_corp_data, state_grad_average], axis=0, ignore_index=True)

    # add to school data by making a copy, renaming the category, and concatenating
    duplicate_row = all_school_data[all_school_data['Category'] == 'Total Graduation Rate']
    duplicate_row['Category'] = 'State Graduation Average'
    all_school_data = pd.concat([all_school_data, duplicate_row], axis=0, ignore_index=True)

    # Clean up and merge school and corporation dataframes

    year_cols = list(all_school_data.columns[:0:-1])
    year_cols.reverse()

    all_corp_data = (all_corp_data.set_index(["Category"]).add_suffix("Corp Average").reset_index())
    all_school_data = (all_school_data.set_index(["Category"]).add_suffix("School").reset_index())

    # last bit of cleanup is to drop 'Corporation Name' Category from corp df
    # all_corp_data = all_corp_data[all_corp_data['Category'] != 'Corporation Name']
    all_corp_data = all_corp_data.drop(all_corp_data.loc[all_corp_data['Category']=='Corporation Name'].index).reset_index(drop=True)

    # Create list of alternating columns by year
    school_cols = list(all_school_data.columns[:0:-1])
    school_cols.reverse()

    corp_cols = list(all_corp_data.columns[:0:-1])
    corp_cols.reverse()

    result_cols = [str(s) + "+/-" for s in year_cols]

    final_cols = list(itertools.chain(*zip(school_cols, corp_cols, result_cols)))
    final_cols.insert(0, "Category")

    merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
    merged_cols.insert(0, "Category")
    hs_merged_data = all_school_data.merge(all_corp_data, on="Category", how="left")
    hs_merged_data = hs_merged_data[merged_cols]

    tmp_category = all_school_data["Category"]
    all_school_data = all_school_data.drop("Category", axis=1)
    all_corp_data = all_corp_data.drop("Category", axis=1)

    # make sure there are no lingering NoneTypes to screw up the creation of hs_results
    all_school_data = all_school_data.fillna(value=np.nan)
    all_corp_data = all_corp_data.fillna(value=np.nan)

    # calculate difference between two dataframes
    hs_results = pd.DataFrame()

    for y in year_cols:
        hs_results[y] = calculate_difference(
            all_school_data[y + "School"], all_corp_data[y + "Corp Average"]
        )

    # add headers
    hs_results = hs_results.set_axis(result_cols, axis=1)
    hs_results.insert(loc=0, column="Category", value=tmp_category)

    final_hs_academic_data = hs_merged_data.merge(hs_results, on="Category", how="left")
    final_hs_academic_data = final_hs_academic_data[final_cols]

    return final_hs_academic_data

def calculate_high_school_metrics(merged_data):

    data = merged_data.copy()

    data.columns = data.columns.str.replace(r"Corp Average", "Average")

    grad_limits_state = [0, 0.05, 0.15, 0.15]

    state_grad_metric = data.loc[data["Category"] == "State Graduation Average"]

    [
        state_grad_metric.insert(
            i,
            str(state_grad_metric.columns[i - 1])[: 7 - 3]
            + "Rate"
            + str(i),
            state_grad_metric.apply(
                lambda x: set_academic_rating(
                    x[state_grad_metric.columns[i - 1]],
                    grad_limits_state,
                    2,
                ),
                axis=1,
            ),
        )
        for i in range(state_grad_metric.shape[1], 1, -3)
    ]

    grad_limits_local = [0, 0.05, 0.10, 0.10]
    local_grad_metric = data[data["Category"].isin(["Total Graduation Rate", "Non Waiver Graduation Rate"])]

    [
        local_grad_metric.insert(
            i,
            str(local_grad_metric.columns[i - 1])[: 7 - 3]
            + "Rate"
            + str(i),
            local_grad_metric.apply(
                lambda x: set_academic_rating(
                    x[local_grad_metric.columns[i - 1]],
                    grad_limits_local,
                    2,
                ),
                axis=1,
            ),
        )
        for i in range(local_grad_metric.shape[1], 1, -3)
    ]

    strength_diploma = data[data["Category"] == "Strength of Diploma"]
    strength_diploma = strength_diploma[[col for col in strength_diploma.columns if "School" in col or "Category" in col]]

    # NOTE: Strength of Diploma is not currently displayed
    strength_diploma.loc[strength_diploma["Category"] == "Strength of Diploma", "Category"] = "1.7.e The school's strength of diploma indicator."

    # combine dataframes and rename categories
    combined_grad_metrics = pd.concat([state_grad_metric, local_grad_metric], ignore_index=True)
    combined_grad_metrics.loc[combined_grad_metrics["Category"] == "Average State Graduation Rate","Category",
    ] = "1.7.a 4 year graduation rate compared with the State average"
    combined_grad_metrics.loc[combined_grad_metrics["Category"] == "Total Graduation Rate", "Category",
    ] = "1.7.b 4 year graduation rate compared with school corporation average"

    combined_grad_metrics.loc[ combined_grad_metrics["Category"] == "Non-Waiver Graduation Rate", "Category",
    ] = "1.7.b 4 year non-waiver graduation rate  with school corporation average"

    return combined_grad_metrics

def calculate_k8_yearly_metrics(data):
    
    data.columns = data.columns.astype(str)
    
    category_header = data["Category"]
    data = data.drop("Category", axis=1)

    # temporarily store last column (first year of data chronologically) as
    # this is not used in first year-over-year calculation
    first_year = pd.DataFrame()
    first_year[data.columns[-1]] = data[data.columns[-1]]

    # loops over dataframe calculating difference between col (Year) and col+1 (Previous Year)
    # and insert the result into the dataframe at every third index position
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

    # for the year_over_year df, drop the 'Rating' column for the last year_data column
    # and rename it - we don't use last Rating column becase we cannot calculate a 'year
    # over year'calculation for the baseline (first) year
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

def calculate_k8_comparison_metrics(school_data, year, school):

    # TODO: Instead of passing school_data, should we just recalculate it?
    # TODO: will change error handling if the initial check as to whether there is data or not is in function

    excluded_years = get_excluded_years(year)

    all_corporation_data = get_k8_corporation_academic_data(school)
    
    corporation_data = all_corporation_data[~all_corporation_data["Year"].isin(excluded_years)].copy()

    school_data.columns = school_data.columns.astype(str)
    corporation_data.columns = corporation_data.columns.astype(str)

    # convert to numeric, but keep strings ('***')
    for col in school_data:
        school_data[col] = pd.to_numeric(school_data[col], errors='coerce').fillna(school_data[col])

    # do not want to retain strings ('***') for corporation_data
    for col in corporation_data:
        corporation_data[col] = pd.to_numeric(corporation_data[col], errors='coerce')       
    
    corporation_data = corporation_data.filter(regex=r"Total Tested$|Total Proficient$|IREAD Pass N|IREAD Test N|Year",
        axis=1,
    )

    # reset index as 'Year' for corp_rate data
    corporation_data = corporation_data.set_index("Year")

    # iterate over (non missing) columns, calculate the average,
    # and store in a new column
    corporation_data = calculate_proficiency(corporation_data)

    # replace 'Totals' with calculation taking the masking step into account
    # The masking step above removes grades from the corp_rate dataframe
    # that are not also in the school dataframe (e.g., if school only has data
    # for grades 3, 4, & 5, only those grades will remain in corp_rate df).
    # However, the 'Corporation Total' for proficiency in a subject is
    # calculated using ALL grades. So we need to recalculate the 'Corporation Total'
    # rate manually to ensure it includes only the included grades.
    adjusted_corporation_math_proficient = corporation_data.filter(regex=r"Grade.+?Math Total Proficient")
    adjusted_corporation_math_tested = corporation_data.filter(regex=r"Grade.+?Math Total Tested")

    corporation_data["School Total|Math Proficient %"] = adjusted_corporation_math_proficient.sum(axis=1) \
    / adjusted_corporation_math_tested.sum(axis=1)

    adjusted_corporation_ela_proficient = corporation_data.filter(regex=r"Grade.+?ELA Total Proficient")
    adjusted_corporation_ela_tested = corporation_data.filter(regex=r"Grade.+?ELA Total Tested")

    corporation_data["School Total|ELA Proficient %"] = adjusted_corporation_ela_proficient.sum(axis=1) \
        / adjusted_corporation_ela_tested.sum(axis=1)

    # ensure corp data has same categories as school data
    column_list = school_data['Category'].tolist() + ['Year']

    # calculate IREAD Pass %
    if "IREAD Pass %" in column_list:
        
        corporation_data["IREAD Pass %"] = (corporation_data["IREAD Pass N"] / corporation_data["IREAD Test N"])

    corporation_data = corporation_data.filter(regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$",axis=1)
    
    # no drop because index was previous set to year
    corporation_data = corporation_data.reset_index()

    # ensure columns headers are strings
    corporation_data.columns = corporation_data.columns.astype(str)
    
    # keep only corp columns that match school_columns
    corporation_data = corporation_data[corporation_data.columns.intersection(column_list)]

    corporation_data = (corporation_data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

    # reverse order of corp_data columns (ignoring 'Category') so current year is first and
    # get clean list of years
    k8_year_cols = list(school_data.columns[:0:-1])
    k8_year_cols.reverse()

    # add_suffix is applied to entire df. To hide columns we dont want
    # renamed, set it as index and reset back after renaming.
    corporation_data = (corporation_data.set_index(["Category"]).add_suffix("Corp Proficiency").reset_index())
    school_data = (school_data.set_index(["Category"]).add_suffix("School").reset_index())

    school_cols = list(school_data.columns[:0:-1])
    school_cols.reverse()

    corp_cols = list(corporation_data.columns[:0:-1])
    corp_cols.reverse()

    result_cols = [str(s) + "+/-" for s in k8_year_cols]

    final_cols = list(itertools.chain(*zip(school_cols, corp_cols, result_cols)))

    final_cols.insert(0, "Category")

    merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
    merged_cols.insert(0, "Category")

    merged_data = school_data.merge(corporation_data, on="Category", how="left")
    merged_data = merged_data[merged_cols]

    tmp_category = school_data["Category"]
    school_data = school_data.drop("Category", axis=1)
    corporation_data = corporation_data.drop("Category", axis=1)

    k8_result = pd.DataFrame()

    for c in school_data.columns:
        c = c[0:4]  # keeps only YYYY part of string
        k8_result[c + "+/-"] = calculate_difference(
            school_data[c + "School"], corporation_data[c + "Corp Proficiency"]
        )

    # add headers
    k8_result = k8_result.set_axis(result_cols, axis=1)
    k8_result.insert(loc=0, column="Category", value=tmp_category)

    # combined merged (school and corp) and result dataframes and reorder
    # (according to result columns)
    final_k8_academic_data = merged_data.merge(k8_result, on="Category", how="left")

    final_k8_academic_data = final_k8_academic_data[final_cols]

    # NOTE: Pretty sure this is redundant as we add 'Proficient %; suffix to totals
    # above, then remove it here, then pass to academic_analysis page, and add it
    # back. But I tried to fix it once and broke everything. So I'm just gonna
    # leave it alone for now.
    final_k8_academic_data["Category"] = (final_k8_academic_data["Category"].str.replace(" Proficient %", "").str.strip())

    # rename IREAD Category
    final_k8_academic_data.loc[final_k8_academic_data["Category"] == "IREAD Pass %", "Category"] = "IREAD Proficiency (Grade 3 only)"

    return final_k8_academic_data

def calculate_iread_metrics(data):
    
    iread_limits = [0.9, 0.8, 0.7, 0.7] 

    data = (data.set_index(["Category"]).add_suffix("School").reset_index())

    [
        data.insert(
            i,
            str(data.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
            data.apply(
                lambda x: set_academic_rating(
                    x[data.columns[i - 1]], iread_limits, 1
                ),
                axis=1,
            ),
        )
        for i in range(data.shape[1], 1, -1)
    ]

    data = data.fillna("No Data")
    data.columns = data.columns.astype(str)

    return data

