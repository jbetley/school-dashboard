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
# from .load_data import 
from .calculations import calculate_percentage, calculate_difference, calculate_year_over_year, \
    set_academic_rating, recalculate_total_proficiency

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
    corp_id = int(selected_school['GEO Corp'].values[0])

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
        attendance_metrics.insert(loc = z, column = attendance_metrics.columns[y][0:4] + 'Diff', value = values)
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
    #       ('Diff') column, if there is an additional calculation required (e.g.,
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

    # separately calculate IREAD Proficiency
    if "IREAD Test N" in data.columns:
        data["IREAD Pass %"] =  calculate_percentage(data["IREAD Pass N"],data["IREAD Test N"])

    return data

### Dataframe Processing Functions ###
def process_k8_academic_data(data: pd.DataFrame, school: str) -> pd.DataFrame:

    data = data.reset_index(drop = True)

    # school data has School Name column, corp data does not
    if len(data.index) != 0:

        school_info = data[['School Name','Low Grade','High Grade']].copy()

        # filter (and drop ELA and Math Subject Category)
        data = data.filter(regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",axis=1)
        data = data[data.columns[~data.columns.str.contains(r'ELA and Math')]]
        
        # NOTE: update is twice as fast as fillna?? (.015s vs .045s)
        data.update(data.apply(pd.to_numeric, errors='coerce'))
        
        # Drop all columns for a Category if the value of 'Total Tested' for that Category is '0'
        # This method works even if data is inconsistent, e.g., where no data could be (and is)
        # alternately represented by NULL, None, or '0'
        tested_cols = data.filter(regex='Total Tested').columns.tolist()

        drop_columns=[]
        for col in tested_cols:
            if pd.to_numeric(data[col], errors='coerce').sum() == 0 or data[col].isnull().all():

                match_string = ' Total Tested'
                matching_cols = data.columns[pd.Series(data.columns).str.startswith(col.split(match_string)[0])]
                drop_columns.append(matching_cols.tolist())   

        drop_all = [i for sub_list in drop_columns for i in sub_list]

        data = data.drop(drop_all, axis=1).copy()

        # does not calculate IREAD proficiency
        data_proficiency = calculate_proficiency(data)

        # create new df with Total Tested and Test N (IREAD) values
        data_tested = data_proficiency.filter(regex='Total Tested|Test N|Year', axis=1).copy()
        data_tested = (data_tested.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())
        data_tested = data_tested.rename(columns={c: str(c)+'N-Size' for c in data_tested.columns if c not in ['Category']})

        # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
        data_proficiency = data_proficiency.filter(regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$", axis=1)

        # add School Name column back
        # school data has School Name column, corp data does not
        if len(school_info.index) > 0:
            data_proficiency = pd.concat([data_proficiency, school_info], axis=1, join="inner")

        data_proficiency = data_proficiency.reset_index(drop=True)

        # transpose dataframes and clean headers    
        data_proficiency.columns = data_proficiency.columns.astype(str)
        data_proficiency = (data_proficiency.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())
        data_proficiency = data_proficiency[data_proficiency["Category"].str.contains("School Name") == False]
        data_proficiency = data_proficiency.reset_index(drop=True)
        data_proficiency = data_proficiency.rename(columns={c: str(c)+'School' for c in data_proficiency.columns if c not in ['Category']})

        # temporarily store Low Grade, and High Grade rows
        other_rows = data_proficiency[data_proficiency['Category'].str.contains(r'Low|High')]

        # Merge Total Tested DF with Proficiency DF based on substring match

        # add new column with substring values and drop old Category column
        data_tested['Substring'] = data_tested['Category'].replace({" Total Tested": "", " Test N": ""}, regex=True)
        data_tested = data_tested.drop('Category', axis=1)

        # this cross-merge and substring match process takes about .3s
        # must be a faster way
        # t20 = time.process_time()

        final_data = data_proficiency.merge(data_tested, how='cross')

        # Need to temporarily rename 'English Learner' because otherwise it 
        # will match both 'English' and 'Non English'
        final_data = final_data.replace({"Non English Language Learners": "Temp1", "English Language Learners": "Temp2"}, regex=True)
        # final_data = final_data.replace('Non English Language Learners','Temp1', regex=True)
        # final_data = final_data.replace('English Language Learners','Temp2', regex=True)

        # Filter rows - keeping only those rows where a substring is in Category
        final_data = final_data[[a in b for a, b in zip(final_data['Substring'], final_data['Category'])]]

        final_data = final_data.replace({"Temp1": "Non English Language Learners", "Temp2": "English Language Learners"}, regex=True)
        # final_data = final_data.replace('Temp1', 'Non English Language Learners', regex=True)
        # final_data = final_data.replace('Temp2', 'English Language Learners', regex=True)        

        final_data = final_data.drop('Substring', axis=1)
        final_data = final_data.reset_index(drop=True)

        # reorder columns for display
        school_cols = [e for e in final_data.columns if 'School' in e]
        nsize_cols = [e for e in final_data.columns if 'N-Size' in e]
        school_cols.sort(reverse=True)
        nsize_cols.sort(reverse=True)

        final_cols = list(itertools.chain(*zip(school_cols, nsize_cols)))
        final_cols.insert(0, "Category")
        
        final_data = final_data[final_cols]
        
        # Add Low Grade, and High Grade rows back (missing cols will populate with NaN)
        # df's should have different indexes, but just to be safe, we will reset them both
        # otherwise could remove the individual reset_index()
        final_data = pd.concat([final_data.reset_index(drop=True), other_rows.reset_index(drop=True)], axis=0).reset_index(drop=True)

        # print(f'Time to Cross Merge : ' + str(time.process_time() - t20))    

    else:
    
        final_data = pd.DataFrame()

    return final_data

def process_k8_corp_academic_data(corp_data: pd.DataFrame, school_data: pd.DataFrame) -> pd.DataFrame:

    if len(corp_data.index) == 0:
        corp_data = pd.DataFrame()
    
    else:
        corp_info = corp_data[["Corporation Name"]].copy()

        # Filter and clean the dataframe
        corp_data = corp_data.filter(regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",axis=1)

        # Drop 'ELA and Math'
        corp_data = corp_data[corp_data.columns[~corp_data.columns.str.contains(r'ELA and Math')]].copy()

        for col in corp_data.columns:
            corp_data[col] = pd.to_numeric(corp_data[col], errors='coerce')

        # Drop all columns for a Category if the value of 'Total Tested' for that Category is '0'
        # This method works even if data is inconsistent, e.g., where no data could be (and is)
        # alternately represented by NULL, None, or '0'
        tested_cols = corp_data.filter(regex='Total Tested').columns.tolist()

        drop_columns=[]
        for col in tested_cols:
            if pd.to_numeric(corp_data[col], errors='coerce').sum() == 0 or corp_data[col].isnull().all():

                match_string = ' Total Tested'
                matching_cols = corp_data.columns[pd.Series(corp_data.columns).str.startswith(col.split(match_string)[0])]
                drop_columns.append(matching_cols.tolist())   

        drop_all = [i for sub_list in drop_columns for i in sub_list]

        corp_data = corp_data.drop(drop_all, axis=1).copy()

        corp_data = calculate_proficiency(corp_data)
        
        # recalculate total proficiency numbers using only school grades
        corp_data = recalculate_total_proficiency(corp_data, school_data)        
        
        if "IREAD Pass N" in corp_data.columns:
            corp_data["IREAD Pass %"] = pd.to_numeric(corp_data["IREAD Pass N"], errors="coerce") \
                / pd.to_numeric(corp_data["IREAD Test N"], errors="coerce")

            # If either Test or Pass category had a '***' value, the resulting value will be 
            # NaN - we want it to display '***', so we just fillna
            corp_data["IREAD Pass %"] = corp_data["IREAD Pass %"].fillna("***")

        # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
        corp_data = corp_data.filter(regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$", axis=1)

        # add School Name column back
        # school data has School Name column, corp data does not
        if len(corp_info.index) > 0:
            corp_data = pd.concat([corp_data, corp_info], axis=1, join="inner")

        corp_data = corp_data.reset_index(drop=True)

        # transpose dataframes and clean headers    
        corp_data.columns = corp_data.columns.astype(str)
        corp_data = (corp_data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())
        corp_data = corp_data[corp_data["Category"].str.contains("School Name") == False]
        corp_data = corp_data.reset_index(drop=True)

    return corp_data

def filter_high_school_academic_data(data: pd.DataFrame) -> pd.DataFrame:
    # NOTE: Drop columns without data. Generally, we want to keep 'result' (e.g., 'Graduates', 'Pass N',
    # 'Benchmark') columns with '0' values if the 'tested' (e.g., 'Cohort Count', 'Total Tested',
    # 'Test N') values are greater than '0'. The data is pretty shitty as well, using blank, null,
    # and '0' interchangeably depending on the type. This makes it difficult to simply use dropna() or
    # masking with any() because they may erroneously drop a 0 value that we want to keep. So we need to
    # iterate through each tested category, if it is NaN or 0, we drop it and all associate categories.

# TODO: Can move this SAT filtration (?) to its own function for all academic data because we
# TODO: DO the same thing with the school data
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

    else:
        data = pd.DataFrame()

    return data
    
def process_high_school_academic_data(data: pd.DataFrame, school: str) -> pd.DataFrame:

    school_information = get_school_index(school)

    # use these to determine if data belongs to school or corporation
    school_geo_code = school_information["GEO Corp"].values[0]

    # Ensure geo_code is always at index 0
    data = data.reset_index(drop = True)

    data_geo_code = data['Corporation ID'][0]

    school_type = school_information["School Type"].values[0]

    if len(data.index) > 0:
        
        # it is 'corp' data if 'Corporation ID' is equal to the value of the school's 'GEO Corp'.
        if data_geo_code == school_geo_code:
            school_info = data[["Corporation Name"]].copy()
        else:
            school_info = data[["School Name"]].copy()
            
            # school data: coerce, but keep strings ('***' and '^')
            for col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(data[col])

        # Get 'Total Tested' & 'Cohort Count' (nsize) data and store in separate dataframe.
        data_tested = data.filter(regex='Total Tested|Cohort Count|Year', axis=1).copy()
        data_tested = (data_tested.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

#TODO: remove CN-Size altogether
        # temp name N-Size cols in order to differentiate.
        if data_geo_code == school_geo_code:
            data_tested = data_tested.rename(columns={c: str(c)+'CN-Size' for c in data_tested.columns if c not in ['Category']})
        else:
            data_tested = data_tested.rename(columns={c: str(c)+'SN-Size' for c in data_tested.columns if c not in ['Category']})

        # Filter the proficiency df
        data = data.filter(regex=r"Cohort Count$|Graduates$|AHS|Benchmark|Total Tested|^Year$", axis=1)

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

        # Calculate SAT Rates #
        if "School Total|EBRW Total Tested" in data.columns:
            data = calculate_sat_rate(data)

        # Calculate AHS Only Data #
        # NOTE: All other values pulled from HS dataframe required for AHS calculations should go here        

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
            regex=r"^Category|Graduation Rate$|CCR Percentage|Pass Rate$|Benchmark %|Below|Approaching|At|^CCR Percentage|^Year$", # ^Strength of Diploma
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

        if data_geo_code == school_geo_code:
            data = data.rename(columns={c: str(c)+'Corp' for c in data.columns if c not in ['Category']})   
        else:
            data = data.rename(columns={c: str(c)+'School' for c in data.columns if c not in ['Category']})  
        
        data = data.reset_index(drop=True)

        # make sure there are no lingering NoneTypes 
        data = data.fillna(value=np.nan)

        # Merge Total Tested DF with Proficiency DF based on substring match

        # # temporarily store Graduation Rate data
        # grad_data = data[data['Category'].str.contains('Graduation Rate')]

        # add new column with substring values and drop old Category column
        data_tested['Substring'] = data_tested['Category'].replace({" Total Tested": "", "\|Cohort Count": " Graduation"}, regex=True)

        data_tested = data_tested.drop('Category', axis=1)

        # this cross-merge and substring match process takes about .3s - must be a faster way
        # t20 = time.process_time()

        final_data = data.merge(data_tested, how='cross')

        # keep only those rows where substring is in Category
        # Need to temporarily rename 'English Learner' because otherwise it 
        # will match both 'English' and 'Non English'
        final_data = final_data.replace({"Non English Language Learners": "Temp1", "English Language Learners": "Temp2"}, regex=True)
        # final_data = final_data.replace('Non English Language Learners','Temp1', regex=True)
        # final_data = final_data.replace('English Language Learners','Temp2', regex=True)

        final_data = final_data[[a in b for a, b in zip(final_data['Substring'], final_data['Category'])]]
        
        final_data = final_data.replace({"Temp1": "Non English Language Learners", "Temp2": "English Language Learners"}, regex=True)        
        # final_data = final_data.replace('Temp1', 'Non English Language Learners', regex=True)
        # final_data = final_data.replace('Temp2', 'English Language Learners', regex=True)         

        final_data = final_data.drop('Substring', axis=1)
        final_data = final_data.reset_index(drop=True)

        # reorder columns for display
        # NOTE: This final data keeps the Corp N-Size cols, which are not used
        # currently. We drop them later in the merge_high_school_data() step.
        if data_geo_code == school_geo_code:
            school_cols = [e for e in final_data.columns if 'Corp' in e]
            nsize_cols = [e for e in final_data.columns if 'CN-Size' in e]
        else:
            school_cols = [e for e in final_data.columns if 'School' in e]
            nsize_cols = [e for e in final_data.columns if 'SN-Size' in e]

        school_cols.sort(reverse=True)
        nsize_cols.sort(reverse=True)

        final_cols = list(itertools.chain(*zip(school_cols, nsize_cols)))


        final_cols.insert(0, "Category")
        final_data = final_data[final_cols]

    else:

        final_data = pd.DataFrame()

    return final_data

### Calculate Accountability Metrics ###

def merge_high_school_data(all_school_data: pd.DataFrame, all_corp_data: pd.DataFrame) -> pd.DataFrame:

    all_school_data.columns = all_school_data.columns.astype(str)
    all_corp_data.columns = all_corp_data.columns.astype(str)

    # Add State Graduation Average to Corp DataFrame
    state_grad_average = get_graduation_data()
    state_grad_average = state_grad_average.loc[::-1].reset_index(drop=True)
    
    # merge state_grad_average with corp_data
    state_grad_average = (state_grad_average.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

    # rename columns and add state_grad average to corp df
    state_grad_average_corp = state_grad_average.rename(columns={c: str(c)+'Corp' for c in state_grad_average.columns if c not in ['Category']})
    all_corp_data = pd.concat([all_corp_data.reset_index(drop=True), state_grad_average_corp.reset_index(drop=True)], axis=0).reset_index(drop=True)

    # For the school calculation we duplicate the school's Total Graduation rate and
    # rename it "State Grad Average" - when the difference is calculated
    # between the two data frames, the difference between the Total Graduation Rates
    # will be School minus Corportion and the difference between State Grad Average Rates
    # will be School minus State Average

    # If no Total Graduation Rate Category exists for a school, we add it with all NaNs
    if 'Total Graduation Rate' not in all_school_data['Category'].values:
        # add row of all nan (by enlargement) and set Category value
        all_school_data.loc[len(all_school_data)] = np.nan
        all_school_data.loc[all_school_data.index[-1],'Category'] = 'Total Graduation Rate'

    duplicate_row = all_school_data[all_school_data['Category'] == 'Total Graduation Rate'].copy()
    duplicate_row['Category'] = 'State Graduation Average'
    all_school_data = pd.concat([all_school_data, duplicate_row], axis=0, ignore_index=True)

    # Clean up and merge school and corporation dataframes
    year_cols = list(all_school_data.columns[:0:-1])
    year_cols = [c[0:4] for c in year_cols]  # keeps only YYYY part of string]
    year_cols = list(set(year_cols))
    year_cols.sort(reverse=True)

    # last bit of cleanup is to drop 'Corporation Name' Category from corp df
    all_corp_data = all_corp_data.drop(all_corp_data.loc[all_corp_data['Category']=='Corporation Name'].index).reset_index(drop=True)

    # Create list of alternating columns
    # we technically do not need the Corporation N-Size at this point, but
    # we will keep it just in case. We drop it in the final df
    corp_cols = [e for e in all_corp_data.columns if 'Corp' in e]
    cnsize_cols = [e for e in all_corp_data.columns if 'CN-Size' in e]
    school_cols = [e for e in all_school_data.columns if 'School' in e]
    snsize_cols = [e for e in all_school_data.columns if 'SN-Size' in e]
    school_cols.sort(reverse=True)
    snsize_cols.sort(reverse=True) 
    corp_cols.sort(reverse=True)
    cnsize_cols.sort(reverse=True)

    result_cols = [str(s) + "Diff" for s in year_cols]

    merged_cols = list(itertools.chain(*zip(school_cols, snsize_cols, corp_cols, cnsize_cols)))
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
    # NOTE: yes a for-loop, but almost instantaneous
    hs_results = pd.DataFrame()
    for y in year_cols:
        hs_results[y] = calculate_difference(
            all_school_data[y + "School"], all_corp_data[y + "Corp"]
        )

    # Create final column order
    # NOTE: We drop the corp avg and corp N-Size cols (by not including them in the list)
    # because we do not display them
    # final_cols = list(itertools.chain(*zip(school_cols, snsize_cols, corp_cols, cnsize_cols, result_cols)))
    final_cols = list(itertools.chain(*zip(school_cols, snsize_cols, result_cols)))    
    final_cols.insert(0, "Category")    

    hs_results = hs_results.set_axis(result_cols, axis=1)
    hs_results.insert(loc=0, column="Category", value=tmp_category)

    final_hs_academic_data = hs_merged_data.merge(hs_results, on="Category", how="left")
    final_hs_academic_data = final_hs_academic_data[final_cols]

    final_hs_academic_data.columns = final_hs_academic_data.columns.str.replace('SN-Size', 'N-Size', regex=True)
    print(final_hs_academic_data)

    return final_hs_academic_data

def calculate_high_school_metrics(merged_data: pd.DataFrame) -> pd.DataFrame:

    data = merged_data.copy()

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

    # NOTE: Strength of Diploma is not currently displayed
    strength_diploma = data[data["Category"] == "Strength of Diploma"]
    strength_diploma = strength_diploma[[col for col in strength_diploma.columns if "School" in col or "Category" in col]]
    strength_diploma.loc[strength_diploma["Category"] == "Strength of Diploma", "Category"] = "1.7.e The school's strength of diploma indicator."

    # combine dataframes and rename categories
    combined_grad_metrics = pd.concat([state_grad_metric, local_grad_metric], ignore_index=True)
    
    combined_grad_metrics.loc[combined_grad_metrics["Category"] == "State Graduation Average","Category",
    ] = "1.7.a 4 year graduation rate compared with the State average"
    
    combined_grad_metrics.loc[combined_grad_metrics["Category"] == "Total Graduation Rate", "Category",
    ] = "1.7.b 4 year graduation rate compared with school corporation average"

    combined_grad_metrics.loc[ combined_grad_metrics["Category"] == "Non Waiver Graduation Rate", "Category",
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

    # NOTE: different take on the for-loop- but still almost instantaneous
    # loops over dataframe calculating difference between col (Year) and col+2 (Previous Year)
    # and insert the result into the dataframe at every third index position
    z = 2
    x = 0
    num_loops = int((len(data.columns) - 2) / 2)
  
    for y in range(0, num_loops):
        values = calculate_year_over_year(data.iloc[:, x], data.iloc[:, x + 2])
        data.insert(loc = z, column = data.columns[x][0:4] + 'Diff', value = values)
        z+=3
        x+=3

    data.insert(loc=0, column="Category", value=category_header)
    data["Category"] = (data["Category"].str.replace(" Proficient %", "").str.strip())
    
    # Add first_year data back
    data[first_year.columns] = first_year

    # Create clean col lists - (YYYY + 'School') and (YYYY + 'Diff')
    school_years_cols = list(data.columns[1:])
    
    # thresholds for academic ratings
    years_limits = [0.05, 0.02, 0, 0]

    # Slightly different formula for this one:
    #   1) the loop 'for i in range(data.shape[1]-2, 1, -3)' counts backwards by -3,
    #   beginning with 2 minus the index of the last column in the dataframe
    #   ('data.shape[1]-2') to '1.' This ignores the last two columns which will always
    #   be "first year" data and "first year" n-size. These are indexes, so the
    #   loop stops at the third column (which has an index of 2);
    #   e.g., 12 col dataframe - from index 11 to 0 - we want to get rating of 9,6,3
    #   2) for each step, the code inserts a new column, at index 'i'. The column
    #   header is a string that is equal to 'the year (YYYY) part of the column
    #   string (attendance_data_metrics.columns[i-1])[:7 - 3]) + 'Rate' + 'i'
    #   (the value of 'i' doesn't matter other than to differentiate the columns) +
    #   the accountability value, a string returned by the set_academic_rating() function.
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
        for i in range(data.shape[1]-2, 1, -3)
    ]

    data = data.fillna("No Data")

    data.columns = data.columns.astype(str)

    # one last processing step is needed to ensure proper ratings. The set_academic_rating()
    # function assigns a rating based on the 'Diff' difference value (either year over year
    # or as compared to corp). For the year over year comparison it is possible to get a
    # rating of 'Approaches Standard' for a 'Diff' value of '0.00%' when the yearly ratings
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

def calculate_k8_comparison_metrics(school_data: pd.DataFrame, corp_data: pd.DataFrame, year: str) -> pd.DataFrame:

    excluded_years = get_excluded_years(year)

    if excluded_years:
        corp_data = corp_data.drop(columns = excluded_years)

    school_data.columns = school_data.columns.astype(str)
    corp_data.columns = corp_data.columns.astype(str)

    category_list = school_data['Category'].tolist() + ['Year']
    
    # keep only corp Category rows that match school Category rows
    corp_data = corp_data[corp_data['Category'].isin(category_list)]

    # TODO: ADD MALE/FEMALE TO CORP_k8 file
    # TODO: UNTIL THEN, NEED TO REMOVE IT FROM SCHOOL FILE OR THROWS OFF CALCULATIONS
    school_data = school_data[school_data["Category"].str.contains("Female|Male|Low|High") == False]

    # Clean up and merge school and corporation dataframes
    year_cols = list(school_data.columns[:0:-1])
    year_cols = [c[0:4] for c in year_cols]
    year_cols = list(set(year_cols))
    year_cols.sort(reverse=True)
    
    # add_suffix to year cols
    corp_data = (corp_data.set_index(["Category"]).add_suffix("Corp").reset_index())

    # Use column list to merge
    corp_cols = [e for e in corp_data.columns if 'Corp' in e]
    school_cols = [e for e in school_data.columns if 'School' in e]
    nsize_cols = [e for e in school_data.columns if 'N-Size' in e]
    school_cols.sort(reverse=True)
    corp_cols.sort(reverse=True)
    nsize_cols.sort(reverse=True)

    result_cols = [str(s) + "Diff" for s in year_cols]

    # temporarily place school and corp cols next to each other
    merged_cols = list(itertools.chain(*zip(school_cols, corp_cols, nsize_cols)))
    merged_cols.insert(0, "Category")

    merged_data = school_data.merge(corp_data, on="Category", how="left")
    merged_data = merged_data[merged_cols]

    school_data = school_data.reset_index(drop=True)

    tmp_category = school_data["Category"]
    school_data = school_data.drop("Category", axis=1)
    corp_data = corp_data.drop("Category", axis=1)

    k8_result = pd.DataFrame()
    for c in school_data.columns:
        c = c[0:4]
        k8_result[c + "Diff"] = calculate_difference(
            school_data[c + "School"], corp_data[c + "Corp"]
        )

    # organize headers
    final_cols = list(itertools.chain(*zip(school_cols, nsize_cols, result_cols)))
    final_cols.insert(0, "Category")

    k8_result = k8_result.set_axis(result_cols, axis=1)
    k8_result.insert(loc=0, column="Category", value=tmp_category)

    # merge and reorder cols
    final_k8_academic_data = merged_data.merge(k8_result, on="Category", how="left")

    final_k8_academic_data = final_k8_academic_data[final_cols]

    # NOTE: Pretty sure this is redundant as we add 'Proficient %; suffix to totals
    # above, then remove it here, then pass to academic_analysis page, and add it
    # back. But I tried to fix it once and broke everything. So I'm just gonna
    # leave it alone for now.
    final_k8_academic_data["Category"] = (final_k8_academic_data["Category"].str.replace(" Proficient %", "").str.strip())

    # rename IREAD Category
    final_k8_academic_data.loc[final_k8_academic_data["Category"] == "IREAD Pass %", "Category"] = "IREAD Proficiency (Grade 3 only)"

    # Add metric ratings. See get_attendance_metrics() for a description
    delta_limits = [0.1, 0.02, 0, 0]  
    [
        final_k8_academic_data.insert(
            i,
            str(final_k8_academic_data.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
            final_k8_academic_data.apply(
                lambda x: set_academic_rating(
                    x[final_k8_academic_data.columns[i - 1]], delta_limits, 1
                ),
                axis=1,
            ),
        )
        for i in range(final_k8_academic_data.shape[1], 1, -3)
    ]
 
    final_k8_academic_data = final_k8_academic_data.fillna("No Data")

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