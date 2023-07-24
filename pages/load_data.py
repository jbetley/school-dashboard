############################################
# ICSB Dashboard - Data & Global Variables #
############################################
# author:   jbetley
# version:  1.03
# date:     5/22/23

# TODO: Explore serverside disk caching for data loading
#https://community.plotly.com/t/the-value-of-the-global-variable-does-not-change-when-background-true-is-set-in-the-python-dash-callback/73835

from typing import Tuple
import pandas as pd
import numpy as np
import itertools
from .load_db import get_current_year, get_school_index, get_k8_school_academic_data, get_demographic_data, \
    get_high_school_academic_data, get_k8_corporation_academic_data, get_graduation_data, \
        get_hs_corporation_academic_data, get_letter_grades, get_adult_high_school_metric_data
from .calculations import calculate_percentage, calculate_difference, calculate_year_over_year, \
    set_academic_rating

pd.set_option('display.max_rows', None)

## Load Data Files ##
print("#### Loading Data. . . . . ####")

# NOTE: No K8 academic data exists for 2020

# global integers
current_academic_year = get_current_year()
max_display_years = 5

# global strings
subject = ["Math", "ELA"]

info_categories = ['School Name','Low Grade','High Grade']

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

### Helper Functions ###

def get_excluded_years(year: str) -> list:
    # 'excluded years' is a list of year strings (format YYYY) of all years
    # that are more recent than the selected year. it is used to filter data
    excluded_years = []

    excluded_academic_years = int(current_academic_year) - int(year)

    for i in range(excluded_academic_years):
        excluded_year = int(current_academic_year) - i
        excluded_years.append(excluded_year)

    return excluded_years

def get_attendance_data(data: pd.DataFrame, year: str) -> pd.DataFrame:

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

def get_attendance_metrics(school: str, year: str) -> pd.DataFrame:

    selected_school = get_school_index(school)    
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

def calculate_graduation_rate(values: pd.DataFrame) -> pd.DataFrame:
    
    data = values.copy()

    cohorts = data[data.columns[data.columns.str.contains(r'Cohort Count')]].columns.tolist()

    for cohort in cohorts:
        if cohort in data.columns:
            cat_sub = cohort.split('|Cohort Count')[0]
            data[cat_sub + " Graduation Rate"] = calculate_percentage(data[cat_sub + "|Graduates"], data[cohort])

    return data

def calculate_strength_of_diploma(data: pd.DataFrame) -> pd.DataFrame:
    # NOTE: Not Currently Used
    data["Strength of Diploma"] = pd.to_numeric((data["Non Waiver|Cohort Count"] * 1.08)) \
         / pd.to_numeric(data["Total|Cohort Count"])

    return data

def calculate_eca_rate(values: pd.DataFrame) -> pd.DataFrame:
    data = values.copy()

    tested = data[data.columns[data.columns.str.contains(r'Test N')]].columns.tolist()

    for test in tested:
        if test in data.columns:
            cat_sub = test.split(' Test N')[0]
            data[cat_sub + " Pass Rate"] = calculate_percentage(data[cat_sub + " Pass N"], data[test])
    
    return data

def calculate_sat_rate(values: pd.DataFrame) -> pd.DataFrame:
# NOTE: All nulls should have already been filtered out by filter_high_school_academic_data()
    data = values.copy()

    tested = data[data.columns[data.columns.str.contains(r'Total Tested')]].columns.tolist()

    for test in tested:
        if test in data.columns:
            
            # get Category + Subject string
            cat_sub = test.split(' Total Tested')[0]
            data[cat_sub + ' Benchmark %'] = calculate_percentage(data[cat_sub + ' At Benchmark'], data[test])

    return data

# TODO: This is slow. Refactor
import time

def calculate_proficiency(values: pd.DataFrame) -> pd.DataFrame:

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

            if (pd.to_numeric(data[total_tested], errors='coerce').sum() == 0 or pd.isna(data[total_tested]).all()) | \
                (pd.to_numeric(data[total_tested], errors='coerce').sum() > 0 and pd.isna(data[total_proficient]).all()):

                data = data.drop([total_tested, total_proficient], axis=1)
            else:
                data[proficiency] = calculate_percentage(data[total_proficient], data[total_tested])
  
    return data

### End Helper Functions ###

### Dataframe Processing Functions ###
def process_k8_academic_data(data: pd.DataFrame, year: str, school: str) -> pd.DataFrame:

    school_information = get_school_index(school)

    # use these to determine if data belongs to school or corporation
    school_geo_code = school_information["GEO Corp"].values[0]

    # Ensure geo_code is always at index 0
    data = data.reset_index(drop = True)

    data_geo_code = data['Corporation ID'][0]

    # school data has School Name column, corp data does not
    if len(data.index) != 0:

        # it is 'corp' data where the value of 'Corporation ID' in the df is equal
        # to the value of the school's 'GEO Corp'.
        if data_geo_code == school_geo_code:
            school_info = data[["Corporation Name"]].copy()

            # Filter and clean the dataframe
            data = data.filter(regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",axis=1)

            # Drop 'ELA and Math'
            data = data[data.columns[~data.columns.str.contains(r'ELA and Math')]].copy()

            # corporation data: coerce strings ('***' and '^') to NaN (for
            # both masking and groupby.sum() purposes)
            for col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
       
        else:
       
            school_info = data[['School Name','Low Grade','High Grade']].copy()

            # school data: coerce, but keep strings ('***' and '^')

            data = data.filter(regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",axis=1)
            
            # Drop 'ELA and Math'
            data = data[data.columns[~data.columns.str.contains(r'ELA and Math')]]
            
            t4 = time.process_time()

            # NOTE: update is twice as fast as fillna?? (.35s vs .6s)
            # for col in data.columns:
            #     data[col] = pd.to_numeric(data[col], errors='coerce').fillna(data[col])
            data.update(data.apply(pd.to_numeric, errors='coerce'))
         
            print(f'Time to update: ' + str(time.process_time() - t4))
        
        # Filter and clean the dataframe
        data = data.filter(regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",axis=1)
        
        # Drop 'ELA and Math'
        data = data[data.columns[~data.columns.str.contains(r'ELA and Math')]].copy()
      
        # Drop all columns for a Category if the value of 'Total Tested' for that Category is '0'
        # This method works even if data is inconsistent, e.g., where no data could be (and is)
        # alternately represented by NULL, None, or '0'
        tested_cols = data.filter(regex='Total Tested').columns.tolist()

        # TODO: Can i use this for the proficiency shite in academic info too?
        drop_columns=[]
        for col in tested_cols:
            if pd.to_numeric(data[col], errors='coerce').sum() == 0 or data[col].isnull().all():

                match_string = ' Total Tested'
                matching_cols = data.columns[pd.Series(data.columns).str.startswith(col.split(match_string)[0])]
                drop_columns.append(matching_cols.tolist())   

        drop_all = [i for sub_list in drop_columns for i in sub_list]

        data = data.drop(drop_all, axis=1).copy()

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

def filter_high_school_academic_data(data: pd.DataFrame) -> pd.DataFrame:
    # NOTE: Drop columns without data. Generally, we want to keep 'result' (e.g., 'Graduates', 'Pass N',
    # 'Benchmark') columns with '0' values if the 'tested' (e.g., 'Cohort Count', 'Total Tested',
    # 'Test N') values are greater than '0'. The data is pretty shitty as well, using blank, null,
    # and '0' interchangeably depending on the type. This makes it difficult to simply use dropna() or
    # masking with any() because they may erroneously drop a 0 value that we want to keep. So we need to
    # iterate through each tested category, if it is NaN or 0, we drop it and all associate categories.

# TODO: Just move this filtration to its own function for all academic data
    if len(data.index) > 0:
        data = data.replace({"^": "***"})

        # school data: coerce to numeric but keep strings ('***')
        for col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(data[col])

        # Drop: 'Graduation Rate', 'Percent Pass', 'ELA and Math' (never need these)
        data = data[data.columns[~data.columns.str.contains(r'Graduation Rate|Percent Pass|ELA and Math')]].copy()

        # Drop: all SAT related columns ('Approaching Benchmark', 'At Benchmark', etc.)
        # for a Category if the value of 'Total Tested' for that Category is '0'
        # sat_tested_cols = data.filter(like='Total Tested').columns.tolist()

        tested_cols = data.filter(regex='Total Tested|Cohort Count|Test N').columns.tolist()

        drop_columns=[]

        for col in tested_cols:
            if pd.to_numeric(data[col], errors='coerce').sum() == 0 or data[col].isnull().all():

                if 'Total Tested' in col:
                    match_string = ' Total Tested'
                elif 'Cohort Count' in col:
                    match_string = '|Cohort Count'
                elif 'Test N' in col:
                    match_string = ' Test N'

                matching_cols = data.columns[pd.Series(data.columns).str.startswith(col.split(match_string)[0])]
                drop_columns.append(matching_cols.tolist())   

        drop_all = [i for sub_list in drop_columns for i in sub_list]

        # ALT: data = data.loc[:,~data.columns.str.contains(drop_all, case=False)] 
        data = data.drop(drop_all, axis=1).copy()

        final_data = data.copy()

    else:
        final_data = pd.DataFrame()

    return final_data
    
def process_high_school_academic_data(data: pd.DataFrame, year: str, school: str) -> pd.DataFrame:

    school_information = get_school_index(school)

    # use these to determine if data belongs to school or corporation
    school_geo_code = school_information["GEO Corp"].values[0]

    # Ensure geo_code is always at index 0
    data = data.reset_index(drop = True)

    data_geo_code = data['Corporation ID'][0]

    school_type = school_information["School Type"].values[0]

    if len(data.index) > 0:
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
        # data = calculate_nonwaiver_graduation_rate(data)

        # Calculate ECA (Grade 10) Rate #
        if "Grade 10|ELA Test N" in data.columns:
            data = calculate_eca_rate(data)

        # Calculate SAT Rates #
        if "School Total|EBRW Total Tested" in data.columns:
            data = calculate_sat_rate(data)

        # Calculate AHS Only Data #
        # NOTE: All other values pulled from HS dataframe required for AHS calculations should go here        
        # print(data.T)
        # CCR Rate
        if school_type == "AHS":

            if 'AHS|CCR' in data.columns:
                data["AHS|CCR"] = pd.to_numeric(data["AHS|CCR"], errors="coerce")

            if 'AHS|Grad All' in data.columns:                
                data["AHS|Grad All"] = pd.to_numeric(data["AHS|Grad All"], errors="coerce")

            if {'AHS|CCR','AHS|Grad All'}.issubset(data.columns):
                data["CCR Percentage"] = (data["AHS|CCR"] / data["AHS|Grad All"])

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

def calculate_adult_high_school_metrics(school: str, data: pd.DataFrame) -> pd.DataFrame:
    # AHS metrics is such a small subset of all metrics, instead of pulling in the
    # entire HS DF, we just pull the three datapoints we need directly from the DB.

    if len(data.index) > 0:
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

def merge_high_school_data(all_school_data: pd.DataFrame, all_corp_data: pd.DataFrame, year: str) -> pd.DataFrame:

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
    # If a school doesn't have a 'Total Graduation Rate' row, we need to create it
    if 'Total Graduation Rate' not in all_school_data['Category'].values:
        # add row of all nan (by enlargement) and set Category value
        all_school_data.loc[len(all_school_data)] = np.nan
        all_school_data.loc[all_school_data.index[-1],'Category'] = 'Total Graduation Rate'

    duplicate_row = all_school_data[all_school_data['Category'] == 'Total Graduation Rate'].copy()
    duplicate_row['Category'] = 'State Graduation Average'
    all_school_data = pd.concat([all_school_data, duplicate_row], axis=0, ignore_index=True)

    # Clean up and merge school and corporation dataframes

    year_cols = list(all_school_data.columns[:0:-1])
    year_cols.reverse()

    all_corp_data = (all_corp_data.set_index(["Category"]).add_suffix("Corp Average").reset_index())
    all_school_data = (all_school_data.set_index(["Category"]).add_suffix("School").reset_index())

    # last bit of cleanup is to drop 'Corporation Name' Category from corp df

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

def calculate_high_school_metrics(merged_data: pd.DataFrame) -> pd.DataFrame:

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

def calculate_k8_yearly_metrics(data: pd.DataFrame) -> pd.DataFrame:
    
    data.columns = data.columns.astype(str)
    
    # drop low/high grade rows
    data = data[(data["Category"] != 'Low Grade') & (data["Category"] != 'High Grade')]
    
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

    # print(data)
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
    # are both '0'. There is no case where we want a school to receive anything other
    # than a 'DNMS' for a 0% proficiency. However, the set_academic_rating() function does
    # not have access to the values used to calculate the difference value (so it cannot
    # tell if a 0 value is the result of a 0 proficiency). So we need to manually replace
    # any rating in the Rating column with 'DMNS' where the School proficiency value is '0.00%.'

    # because we are changing the value of one column based on the value of another (paired)
    # column, the way we do this is to create a list of tuples (a list of year and rating
    # column pairs), e.g., [('2022School', '2022Rating3')], and then iterate over the column pair

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

def calculate_k8_comparison_metrics(school_data: pd.DataFrame, year: str, school: str) -> pd.DataFrame:

    # TODO: Instead of passing school_data, should we just recalculate it?
    # TODO: will change error handling if the initial check as to whether there is data or not is in function
    # TODO: Whichever way is faster, make sure both hs/ahs and k8 are the same
    excluded_years = get_excluded_years(year)

    all_corporation_data = get_k8_corporation_academic_data(school)
    
    corporation_data = all_corporation_data[~all_corporation_data["Year"].isin(excluded_years)].copy()

    school_data.columns = school_data.columns.astype(str)
    corporation_data.columns = corporation_data.columns.astype(str)

    for col in school_data:
        school_data[col] = pd.to_numeric(school_data[col], errors='coerce').fillna(school_data[col])

    # do not want to retain strings ('***') for corporation_data
    for col in corporation_data:
        corporation_data[col] = pd.to_numeric(corporation_data[col], errors='coerce')       

    # reset index as 'Year' for corp_rate data
    corporation_data = corporation_data.set_index("Year")

    # iterate over (non missing) columns, calculate the average,
    # and store in a new column
    corporation_data = calculate_proficiency(corporation_data)

    # Drop 'ELA and Math'
    # corporation_data = corporation_data[corporation_data.columns[~corporation_data.columns.str.contains(r'ELA and Math')]]

    # Corporation 'School Total' is calculates using all grades. We need to recalculate it using only the
    # grades that are served by the school - this is messy because we need Total Proficient/Total Tested
    # for both ELA and Math for all matching grades and those specific columns do not exist in the school df

    school_grades = school_data.loc[school_data['Category'].str.contains(r"Grade.[345678]", regex=True), 'Category'].to_list()
    school_grades = [i.split('|')[0] for i in school_grades]
    school_grades = list(set(school_grades))

    math_prof = [e + '|Math Total Proficient' for e in school_grades]
    math_test = [e + '|Math Total Tested' for e in school_grades]
    ela_prof = [e + '|ELA Total Proficient' for e in school_grades]
    ela_test = [e + '|ELA Total Tested' for e in school_grades]

    adj_corp_math_prof = corporation_data[corporation_data.columns.intersection(math_prof)]
    adj_corp_math_test = corporation_data[corporation_data.columns.intersection(math_test)]
    adj_corp_ela_prof = corporation_data[corporation_data.columns.intersection(ela_prof)]
    adj_corp_ela_tst = corporation_data[corporation_data.columns.intersection(ela_test)]

    corporation_data["School Total|Math Proficient %"] = adj_corp_math_prof.sum(axis=1) / adj_corp_math_test.sum(axis=1)
    corporation_data["School Total|ELA Proficient %"] = adj_corp_ela_prof.sum(axis=1) / adj_corp_ela_tst.sum(axis=1)

    column_list = school_data['Category'].tolist() + ['Year']
        
    # calculate IREAD Pass %
    if "IREAD Pass %" in column_list:
        
        corporation_data["IREAD Pass %"] = (corporation_data["IREAD Pass N"] / corporation_data["IREAD Test N"])

    # no drop because index was previous set to year
    corporation_data = corporation_data.reset_index()

    # ensure columns headers are strings
    corporation_data.columns = corporation_data.columns.astype(str)
    
    # keep only corp columns that match school_columns
    corporation_data = corporation_data[corporation_data.columns.intersection(column_list)]

    # TODO: ADD MALE/FEMALE TO CORP_k8 file
    # TODO: UNTIL THEN, NEED TO REMOVE IT FROM SCHOOL FILE OR THROWS OFF CALCULATIONS
    # TODO: DO WE NEED LOW GRADE HIGH GRADE IN SCHOOL FILE?
    school_data = school_data[school_data["Category"].str.contains("Female|Male") == False]

    corporation_data = corporation_data.filter(regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$",axis=1)

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

def process_growth_data(data: pd.DataFrame, category: str, calculation: str) -> Tuple[pd.DataFrame, pd.DataFrame]:

    # step 1: find the percentage of students with Adequate growth using
    # 'Majority Enrolled' students (all available data) and the percentage
    # of students with Adequate growth using the set of students enrolled for
    # '162 Days' (a subset of available data)

    data_162 = data[data['Day 162'] == 'TRUE']

    if calculation == 'growth':
        data = data.groupby(['Test Year', category, 'Subject'])['ILEARNGrowth Level'].value_counts(normalize=True).reset_index(name='Majority Enrolled')
        data_162 = data_162.groupby(['Test Year',category, 'Subject'])['ILEARNGrowth Level'].value_counts(normalize=True).reset_index(name='162 Days')
    
    elif calculation == 'sgp':
        data = data.groupby(['Test Year', category, 'Subject'])['ILEARNGrowth Percentile'].median().reset_index(name='Majority Enrolled')
        data_162 = data_162.groupby(['Test Year', category, 'Subject'])['ILEARNGrowth Percentile'].median().reset_index(name='162 Days')
    
    # step 3: add ME column to df and calculate difference
    data['162 Days'] = data_162['162 Days']
    data['Difference'] = data['162 Days'] - data['Majority Enrolled']

    # step 4: get into proper format for display as multi-header DataTable
    
    # create final category
    data['Category'] = data[category] + "|" + data['Subject']
    
    # drop unused rows and columns
    if calculation == 'growth':
        data = data[data["ILEARNGrowth Level"].str.contains("Not Adequate") == False]
        data = data.drop([category, 'Subject','ILEARNGrowth Level'], axis=1)

    elif calculation == 'sgp':
        data = data.drop([category, 'Subject'], axis=1)

    # create fig data
    fig_data = data.copy()
    fig_data = fig_data.drop('Difference', axis=1)
    fig_data = fig_data.pivot(index=['Test Year'], columns='Category')
    fig_data.columns = fig_data.columns.map(lambda x: '_'.join(map(str, x)))

    # create table data
    table_data = data.copy()

    # Need specific column order. sort_index does not work
    cols = []
    yrs = list(set(table_data['Test Year'].to_list()))
    yrs.sort(reverse=True)
    for y in yrs:
        cols.append(str(y) + '162 Days')
        cols.append(str(y) + 'Majority Enrolled')
        cols.append(str(y) + 'Difference')


    # pivot df from wide to long' add years to each column name; move year to
    # front of column name; sort and reset_index
    table_data = table_data.pivot(index=['Category'], columns='Test Year')

    table_data.columns = table_data.columns.map(lambda x: ''.join(map(str, x)))
    table_data.columns = table_data.columns.map(lambda x: x[-4:] + x[:-4])
    table_data = table_data[cols]
    table_data = table_data.reset_index()

    return fig_data, table_data



def calculate_iread_metrics(data: pd.DataFrame) -> pd.DataFrame:
    
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