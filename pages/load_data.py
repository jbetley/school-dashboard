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
from .load_db import get_current_year, get_index, get_k8_school_academic_data, get_demographics, \
    get_high_school_academic_data, get_k8_corporation_academic_data, get_graduation_data, \
        get_high_school_corporation_academic_data, get_letter_grades, get_index
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

    corp_demographics = get_demographics(corp_id)
    school_demographics = get_demographics(school)
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
    
    grad_categories = ethnicity + subgroup + ["Total"]
    
    for g in grad_categories:
        new_col = g + " Graduation Rate"
        graduates = g + "|Graduates"
        cohort = g + "|Cohort Count"

        if cohort in data.columns:
            data[new_col] = calculate_percentage(data[graduates], data[cohort])

    return data

def calculate_nonwaiver_graduation_rate(data):
    data["Non Waiver|Cohort Count"] = pd.to_numeric(data["Non Waiver|Cohort Count"], errors="coerce")
    data["Total|Cohort Count"] = pd.to_numeric(data["Total|Cohort Count"], errors="coerce")

    data["Non Waiver Graduation Rate"] = (data["Non Waiver|Cohort Count"]/data["Total|Cohort Count"])
    data["Strength of Diploma"] = (data["Non Waiver|Cohort Count"] * 1.08)/data["Total|Cohort Count"]

    return data

def calculate_eca_rate(values):

    data = values.copy()
    
    eca_categories = ["Grade 10|ELA", "Grade 10|Math"]

    for e in eca_categories:
        new_col = e + " Pass Rate"
        passN = e + " Pass N"
        testN = e + " Test N"

        data[new_col] = calculate_percentage(data[passN], data[testN])
    
    return data

def calculate_sat_rate(values):

# TODO: Have a problem either here or in filter_function that is dropping NonEnglish Learners?
    data = values.copy()
    # print(data.T)
    sat_categories = ethnicity + subgroup + ["School Total"]
    sat_subject = ['EBRW','Math','Both']

    for ss in sat_subject:
        for sc in sat_categories:
            new_col = sc + "|" + ss + " Benchmark %"
            at_benchmark = sc + "|" + ss + " At Benchmark"
            approaching_benchmark = sc + "|" + ss + " Approaching Benchmark"
            below_benchmark = sc + "|" + ss + " Below Benchmark"
            total_tested = sc + "|" + ss + " Total Tested"

            if total_tested in data.columns:

                if data[total_tested].values[0] == 0:
                    print('DROPPED')
                    drop_columns = [new_col, at_benchmark, approaching_benchmark, below_benchmark, total_tested]
                    data = data.drop(drop_columns, axis=1)
                else:
                    data[new_col] = calculate_percentage(data[at_benchmark], data[total_tested])

    return data

def calculate_proficiency(values):

    data = values.copy()

    categories = ethnicity + subgroup + grades + ["School Total"]

    for s in subject:
        for c in categories:
            new_col = c + "|" + s + " Proficient %"
            proficient = c + "|" + s + " Total Proficient"
            tested = c + "|" + s + " Total Tested"

            if tested in data.columns:
                data[new_col] = calculate_percentage(data[proficient], data[tested])
    
    return data

### End Helper Functions ###


### Dataframe Formatting Functions ###
def process_k8_academic_data(all_data, year, school):
    
    school_information = get_index(school)

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
       
            # print(data.T)
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

def process_high_school_academic_data(all_data, year, school):

    school_information = get_index(school)

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
        if "Non Waiver|Cohort Count" in data.columns:
            data = calculate_nonwaiver_graduation_rate(data)

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

def calculate_adult_high_school_metrics(data, school):

    data.columns = data.columns.astype(str)

    # format for multi-header display
    data_columns = list(data.columns[:0:-1])
    data_columns.reverse()

    data = (data.set_index(["Category"]).add_suffix("School").reset_index())

    ccr_limits = [0.5, 0.499, 0.234]
    [
        data.insert(
            i,
            str(data_columns[i - 2]) + "Rate" + str(i),
            data.apply(
                lambda x: set_academic_rating(
                    x[data.columns[i - 1]], ccr_limits, 2
                ),
                axis=1,
            ),
        )
        for i in range(data.shape[1], 1, -1)
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
    data = pd.concat([ahs_state_grades, data])
    data = data.reset_index(drop=True)
    ahs_metric_nums = ["1.1.", "1.3."]
    data.insert(loc=0, column="Metric", value=ahs_metric_nums)

    return data

# TODO: Have not touched Yet
def calculate_high_school_metrics(all_school_data, all_corp_data, year, school):

    excluded_years = get_excluded_years(year)

    # all_corporation_data = get_high_school_corporation_academic_data(school)

    # corporation_data = all_corporation_data[~all_corporation_data["Year"].isin(excluded_years)]

    all_school_data.columns = all_school_data.columns.astype(str)
    all_corp_data.columns = all_corp_data.columns.astype(str)



    # school_data = all_school_data[~all_school_data["Year"].isin(excluded_years)].copy()

    school_type = school_data["School Type"].values[0]

    if len(school_data.index) != 0:
        corp_data = all_corp_data[~all_corp_data["Year"].isin(excluded_years)]

        # tmp remove text columns from dataframe
        school_info = school_data[["School Name"]].copy()

        # drop adult high schools (AHS) from Corp Average df
        corp_data = corp_data[corp_data["School Type"].str.contains("AHS") == False]

        # AHS- temporarily pull AHS specific values (CCR and GradAll)
        # where there is no corp equivalent.
        if school_type == "AHS":
            ahs_data = school_data.filter(regex=r"GradAll$|CCR$", axis=1)

        # keep only those columns used in calculations
        # SAT Categories: 'Total Tested', 'Below Benchmark', 'Approaching Benchmark',
        #   'At Benchmark', & 'Benchmark %'
        # Grade 10 ECA Categories: 'Pass N' and 'Test N'
        # Graduation Categories: 'Cohort Count' and 'Graduates'

        # temporary info column: School Type
        school_data = school_data.filter(regex=r"Cohort Count$|Graduates$|Pass N|Test N|Benchmark|Total Tested|^Year$", axis=1)
        corp_data = corp_data.filter(regex=r"Cohort Count$|Graduates$|Pass N|Test N|Benchmark|Total Tested|^Year$", axis=1)

        # remove 'ELA & Math' columns (NOTE: Comment this out to retain 'ELA & Math' columns)
        school_data = school_data.drop(list(school_data.filter(regex="ELA & Math")), axis=1)
        corp_data = corp_data.drop(list(corp_data.filter(regex="ELA & Math")), axis=1)

        # convert to numeric, but keep strings ('***')
        for col in school_data.columns:
            school_data[col] = pd.to_numeric(school_data[col], errors='coerce').fillna(school_data[col])
        
        for col in corp_data.columns:
            corp_data[col] = pd.to_numeric(corp_data[col], errors='coerce').fillna(corp_data[col])

        # mask returns a boolean series of columns where all values in cols
        # are not either NaN or 0
        # missing_mask = ~school_data.any()
        
        missing_mask = pd.isnull(school_data[school_data.columns]).all()
        missing_cols = school_data.columns[missing_mask].to_list()

        # opposite mask of above. keep only valid columns
        # valid_mask = school_data.any()

        valid_mask = ~pd.isnull(school_data[school_data.columns]).all()

        school_data = school_data[school_data.columns[valid_mask]]
        corp_data = corp_data[corp_data.columns[valid_mask]]

        # valid_mask returns a boolean series of columns where column
        # is true if any element in the column is not equal to null
        # valid_mask = ~pd.isnull(hs_school_data[hs_school_data.columns]).all()

        # # create list of columns with no data (used in loop below)
        # # missing_mask returns boolean series of columns where column
        # # is true if all elements in the column are equal to null
        # missing_mask = pd.isnull(hs_school_data[hs_school_data.columns]).all()
        # missing_cols = hs_school_data.columns[missing_mask].to_list()

        # use valid_mask keep only columns that have at least one value
        # hs_school_data = hs_school_data[hs_school_data.columns[valid_mask]]
        # corp_data = corp_data[corp_data.columns[valid_mask]]

        # NOTE: Coercing corp_data values to numeric has the effect
        # of converting all '***' (insufficient n-size) values to NaN.
        # Because we are manually calculating a corp average, a NaN means
        # the school has been removed from the average calculation.
        # Typically, this won't have a large effect as there are few
        # traditional public high schools with supressed data, but it
        # could still potentially skew the results.

    # Calculate Grad Rate
        # Do not convert school_corp_data values to numeric because the
        # function to calculate differences anticipates mixed dtypes.
        for col in corp_data.columns:
            corp_data[col] = pd.to_numeric(corp_data[col], errors="coerce")

        # group corp dataframe by year and sum all rows for each category
        corp_data = corp_data.groupby(["Year"]).sum(numeric_only=True)

        # reverse order of rows (Year) and reset index to bring Year back as column
        corp_data = corp_data.loc[::-1].reset_index()

        grad_categories = ethnicity + subgroup + ["Total"]
        for g in grad_categories:
            new_col = g + " Graduation Rate"
            graduates = g + "|Graduates"
            cohort = g + "|Cohort Count"

            if cohort in school_data.columns:
                school_data[new_col] = calculate_percentage(school_data[graduates], school_data[cohort])
                corp_data[new_col] = (corp_data[graduates] / corp_data[cohort])

    # Calculate ECA (Grade 10) rate

        # Use ECA data as calculated at the corporation level (from corporation_rates datafile).
        # NOTE: 'Due to suspension of assessments in 2019-2020, Grade 11 students were assessed
        # on ISTEP10 in 2020-2021' 'Results reflect first-time test takers in Grade 11 Cohort
        # (Graduation Year 2022). 'Results may not be comparable to past years due to assessment
        # of Grade 11'
        all_corp_rates = get_corporation_data(school)
        excluded_years = get_excluded_years(year)
        corp_rates = all_corp_rates[~all_corp_rates["Year"].isin(excluded_years)]

        # change values to numeric (again not school because function accounts for '***')
        for col in corp_rates.columns:
            corp_rates[col] = pd.to_numeric(corp_rates[col], errors="coerce")

        # NOTE: Special case for 2020 - corp_data exists for 2020 (e.g., grad rate),
        # but no data exists for 2020 in corp_rate_data - so there will always be a
        # mismatch - so need to take some additional steps

        # drop all non_matching years from hs_corp_rate_data
        corp_rates = corp_rates.loc[(corp_rates["Year"].isin(corp_data["Year"]))]

        # get missing year(s) in hs_corp_rate_data by comparing the difference
        # between two list sets: usually just 2020, because the only available
        # academic data for 2020 is grad data (corp_data).
        missing_year = list(sorted(set(corp_data["Year"].tolist())- set(corp_rates["Year"].tolist())))

        # reset index
        corp_rates = corp_rates.reset_index(drop=True)

        # if there is a missing year add new row to hs_corp_rate_data with all
        # blanks except for the year value add the year value to the 'Year'
        # column at last index (most recently added row)
        if missing_year:
            for y in missing_year:
                corp_rates = pd.concat(
                    [corp_rates, pd.DataFrame(np.nan, columns=corp_rates.columns, index=range(1))],
                    ignore_index=True,
                )
                corp_rates.at[corp_rates.index[-1], "Year"] = y

        corp_rates = corp_rates.sort_values(by="Year", ascending=False)
        corp_rates = corp_rates.reset_index(drop=True)

        # if none_categories includes 'Grade 10' - there is no ECA data available
        # # for the school for the selected Years
        eca_categories = ["Grade 10|ELA", "Grade 10|Math"]

        # checks to see if substring ('Grade 10') is in the list of missing cols
        if "Grade 10" not in "\t".join(missing_cols):
            for e in eca_categories:
                new_col = e + " Pass Rate"
                passN = e + " Pass N"
                testN = e + " Test N"

                school_data[new_col] = calculate_percentage(school_data[passN], school_data[testN])
                corp_data[new_col] = (corp_rates[passN] / corp_rates[testN])

    # SAT Data
        sat_categories = ethnicity + subgroup + ["School Total"]
        sat_subject = ['EBRW','Math','Both']

        for ss in sat_subject:
            for sc in sat_categories:
                new_col = sc + "|" + ss + " Benchmark %"
                at_benchmark = sc + "|" + ss + " At Benchmark"
                total_tested = sc + "|" + ss + " Total Tested"

                if total_tested in school_data.columns:
                    # Data sometimes has 0's where there should be nulls
                    # so we drop all columns for a category where the
                    # total tested # of students is = 0
                    if school_data[total_tested].values[0] == 0:
                        drop_columns = [new_col, at_benchmark, total_tested]
                        school_data = school_data.drop(drop_columns, axis=1)
                        corp_data = corp_data.drop(drop_columns, axis=1)
                    else:
                        school_data[new_col] = calculate_percentage(school_data[at_benchmark], school_data[total_tested])
                        corp_data[new_col] = (corp_data[at_benchmark] / corp_data[total_tested])

    # Non Waiver Grad Rate
        # if missing_cols includes 'Non Waiver' - there is no data available for the school
        # for the selected Years
        if "Non Waiver" not in "\t".join(missing_cols):

            # NOTE: In spring of 2020, SBOE waived the GQE requirement for students in the
            # 2020 cohort who where otherwise on schedule to graduate, so, for the 2020
            # cohort, there were no 'waiver' graduates (which means no Non Waiver data).
            # so we replace 0 with NaN (to ensure a NaN result rather than 0)
            corp_data["Non Waiver|Cohort Count"] = corp_data["Non Waiver|Cohort Count"].replace({"0": np.nan, 0: np.nan})

            corp_data["Non Waiver Graduation Rate"] = (corp_data["Non Waiver|Cohort Count"]/ corp_data["Total|Cohort Count"])
            corp_data["Strength of Diploma"] = (corp_data["Non Waiver|Cohort Count"] * 1.08) / corp_data["Total|Cohort Count"]

            school_data["Non Waiver|Cohort Count"] = pd.to_numeric(school_data["Non Waiver|Cohort Count"], errors="coerce")
            school_data["Total|Cohort Count"] = pd.to_numeric(school_data["Total|Cohort Count"], errors="coerce")

            school_data["Non Waiver Graduation Rate"] = (school_data["Non Waiver|Cohort Count"]/ school_data["Total|Cohort Count"])
            school_data["Strength of Diploma"] = (school_data["Non Waiver|Cohort Count"] * 1.08) / school_data["Total|Cohort Count"]

        # Calculate CCR Rate (AHS Only), add Year column and store in temporary dataframe
        # NOTE: All other values pulled from HS dataframe required for AHS calculations
        # should go here
        if school_type == "AHS":
            ahs_school_data = pd.DataFrame()
            ahs_school_data["Year"] = school_data["Year"]

            ahs_data["AHS|CCR"] = pd.to_numeric(ahs_data["AHS|CCR"], errors="coerce")
            ahs_data["AHS|GradAll"] = pd.to_numeric(ahs_data["AHS|GradAll"], errors="coerce")
            ahs_school_data["CCR Percentage"] = (ahs_data["AHS|CCR"] / ahs_data["AHS|GradAll"])

            ahs_metric_data = (ahs_school_data.copy())
            ahs_metric_data = ahs_metric_data.reset_index(drop=True)

        school_data = school_data.filter(
            regex=r"^Category|Graduation Rate$|Pass Rate$|Benchmark %|Below|Approaching|At|^CCR Percentage|Total Tested|^Year$", # ^Strength of Diploma
            axis=1,
        )
        
        corp_data = corp_data.filter(
            regex=r"^Category|Graduation Rate$|Pass Rate$|Benchmark %|Below|Approaching|At|Total Tested|^Year$", # ^Strength of Diploma
            axis=1,
        )

        # State Average Graduation Rate
        state_grad_rate = get_graduation_data()

        # # drop all other columns, invert rows (so most recent year at index [0]) & reset the index
        # state_grad_average = state_grad_average[["Year", "State_Grad_Average"]]
        state_grad_average = state_grad_rate.loc[::-1] #.reset_index(drop=True)

        # merge applicable years of grad_avg dataframe into hs_school df using an inner merge
        # and rename the column this merges data only where both dataframes share a common key,
        # in this case 'Year')
        corp_data = corp_data.merge(state_grad_average, on="Year", how="inner")
        
        corp_data = corp_data.rename(columns={"State_Grad_Average": "Average State Graduation Rate"})

        # duplicate 'Total Grad' row and name it 'State Average Graduation Rate'
        # for comparison purposes
        school_data["Average State Graduation Rate"] = school_data["Total Graduation Rate"]

        school_info = school_info.reset_index(drop=True)
        school_data = school_data.reset_index(drop=True)

        school_data = pd.concat([school_data, school_info], axis=1, join="inner")

        school_data.columns = school_data.columns.astype(str)
        corp_data.columns = corp_data.columns.astype(str)

        # calculate difference (+/-) between school and corp grad rates
        hs_num_years = len(school_data.index)

        # transpose dataframes and clean headers
        school_data = (school_data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

        # Keep category and all available years of data
        school_data = school_data.iloc[:, : (hs_num_years + 1)]

        corp_data = (corp_data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())
        corp_data = corp_data.iloc[:, : (hs_num_years + 1)]

        # State/Federal grade rows are used in 'about' page, but not here
        school_data = school_data[school_data["Category"].str.contains("State Grade|Federal Rating|School Name") == False]
        
        school_data = school_data.reset_index(drop=True)

        # get clean list of years
        hs_year_cols = list(school_data.columns[:0:-1])
        hs_year_cols.reverse()

        # add_suffix is applied to entire df. To hide columns we dont want renamed, set them as index and reset back after renaming.
        corp_data = (corp_data.set_index(["Category"]).add_suffix("Corp Average").reset_index())
        school_data = (school_data.set_index(["Category"]).add_suffix("School").reset_index())

        # have to do same things to ahs_data to be able to insert it back
        # into hs_data file even though there is no comparison data involved
        if school_type == "AHS":
            ahs_school_data = (
                ahs_school_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )
            ahs_school_data = ahs_school_data.iloc[:, : (hs_num_years + 1)]
            ahs_school_data = (
                ahs_school_data.set_index(["Category"])
                .add_suffix("School")
                .reset_index()
            )

        # Create list of alternating columns by year (School Value/Similar School Value)
        school_cols = list(school_data.columns[:0:-1])
        school_cols.reverse()

        corp_cols = list(corp_data.columns[:0:-1])
        corp_cols.reverse()

        result_cols = [str(s) + "+/-" for s in hs_year_cols]

        final_cols = list(
            itertools.chain(*zip(school_cols, corp_cols, result_cols))
        )
        final_cols.insert(0, "Category")

        merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
        merged_cols.insert(0, "Category")
        hs_merged_data = school_data.merge(
            corp_data, on="Category", how="left"
        )
        hs_merged_data = hs_merged_data[merged_cols]

        tmp_category = school_data["Category"]
        school_data = school_data.drop("Category", axis=1)
        corp_data = corp_data.drop("Category", axis=1)

        # make sure there are no lingering NoneTypes to screw up the creation of hs_results
        school_data = school_data.fillna(value=np.nan)
        corp_data = corp_data.fillna(value=np.nan)

        # calculate difference between two dataframes
        hs_results = pd.DataFrame()
        for y in hs_year_cols:
            hs_results[y] = calculate_difference(
                school_data[str(y) + "School"], corp_data[str(y) + "Corp Average"]
            )

        # add headers
        hs_results = hs_results.set_axis(result_cols, axis=1)
        hs_results.insert(loc=0, column="Category", value=tmp_category)

        final_hs_academic_data = hs_merged_data.merge(
            hs_results, on="Category", how="left"
        )
        final_hs_academic_data = final_hs_academic_data[final_cols]

        # If AHS - add CCR data to hs_data file
        if school_type == "AHS":
            final_hs_academic_data = pd.concat(
                [final_hs_academic_data, ahs_school_data], sort=False
            )
            final_hs_academic_data = final_hs_academic_data.reset_index(drop=True)

    else:
        final_hs_academic_data = pd.DataFrame()

    return final_hs_academic_data

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

