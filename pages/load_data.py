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
from .load_db import get_current_year, get_school_data, get_corporation_data, get_demographics
from .calculations import calculate_percentage, calculate_difference, calculate_year_over_year, \
    set_academic_rating

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

def get_excluded_years(year):
    # 'excluded years' is a list of YYYY strings (all years more
    # recent than selected year) that can be used to filter data
    # that should not be displayed
    excluded_years = []

    excluded_academic_years = int(current_academic_year) - int(year)

    for i in range(excluded_academic_years):
        excluded_year = int(current_academic_year) - i
        excluded_years.append(excluded_year)
    
    return excluded_years

def get_attendance_rate(data, year):

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
    corp_attendance_rate = get_attendance_rate(corp_demographics, year)
    school_attendance_rate = get_attendance_rate(school_demographics, year)    

    # school_attendance_rate = school_demographics[["Year", "Avg Attendance"]]
    # corp_attendance_rate = corp_demographics[["Year", "Avg Attendance"]]
    print(school_attendance_rate)
    print(corp_attendance_rate)

    # TODO: Refactor this to account for fact that stuff is done in get_attendance_rate
    attendance_merge = school_attendance_rate.merge(
        corp_attendance_rate, on="Year", how="left"
    )
    attendance_merge.columns = ['Year','School', 'Corp Average']

    # calculate difference
    attendance_merge['+/-'] = attendance_merge['School'].astype(float) - attendance_merge['Corp Average'].astype(float)
    
    # set year as index and unstack the dataframe,
    # unstack returns a series having a new level of column labels whose
    # inner-most level consists of the pivoted index ('Year') levels
    # use to_frame() to convert to df and then transpose
    attendance_merge = attendance_merge.set_index(['Year'])
    attendance_data = attendance_merge.unstack().to_frame().sort_index(level=1).T
    attendance_data.columns = attendance_data.columns.map(lambda x: f'{x[1]}{x[0]}')

    # reverse the order of the columns and add Category
    attendance_data = attendance_data[attendance_data.columns[::-1]]
    attendance_data.insert(0, "Category", "1.1.a. Attendance Rate")

    # save attendance_data to json
    # attendance_data_dict = attendance_data.to_dict(into=OrderedDict)
    # attendance_data_json = json.dumps(attendance_data_dict)

    # use the final data to calculate attendance data metrics
    attendance_data_metrics = attendance_data.copy()

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
        attendance_data_metrics.insert(
            i,
            str(attendance_data_metrics.columns[i - 1])[: 7 - 3]
            + "Rate"
            + str(i),
            attendance_data_metrics.apply(
                lambda x: set_academic_rating(
                    x[attendance_data_metrics.columns[i - 1]], attendance_limits, 3
                ),
                axis=1,
            ),
        )
        for i in range(attendance_data_metrics.shape[1], 1, -3)
    ]

    return attendance_data_metrics

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

        # convert to numeric, but keep strings ('***')
        for col in school_data:
            school_data[col] = pd.to_numeric(school_data[col], errors='coerce').fillna(school_data[col])

        # mask returns a boolean series of columns where all values in cols
        # are not either NaN or 0
        missing_mask = ~school_data.any()
        missing_cols = school_data.columns[missing_mask].to_list()

        # opposite mask of above. keep only valid columns
        valid_mask = school_data.any()
        school_data = school_data[school_data.columns[valid_mask]]

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

    # data = data[data["Category"] == "IREAD Pass %"]

    # if not data.empty:
        
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

def process_yearly_indicators(data):
    
    data.columns = data.columns.astype(str)
    
    category_header = data["Category"]
    data = data.drop("Category", axis=1)

    # temporarily store last column (first year of data chronologically) as
    # this is not used in first year-over-year calculation
    first_year = pd.DataFrame()
    first_year[data.columns[-1]] = data[data.columns[-1]]

    # loops over dataframe calculating difference between col (Year) and col+1 (Previous Year)
    # and inserts it into the dataframe every third index
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

def process_comparison_indicators(school_data, year, school):

    excluded_academic_years = int(current_academic_year) - int(year)

    # 'excluded years' is a list of YYYY strings (all years more
    # recent than selected year) that can be used to filter data
    # that should not be displayed
    excluded_years = []
    for i in range(excluded_academic_years):
        excluded_year = int(current_academic_year) - i
        excluded_years.append(excluded_year)

    all_corporation_data = get_corporation_data(school)
    
    corporation_data = all_corporation_data[~all_corporation_data["Year"].isin(excluded_years)]

    school_data.columns = school_data.columns.astype(str)
    corporation_data.columns = corporation_data.columns.astype(str)

    # convert to numeric, but keep strings ('***')
    for col in school_data:
        school_data[col] = pd.to_numeric(school_data[col], errors='coerce').fillna(school_data[col])

    # do not want to retain strings ('***') for corporation_data
    for col in corporation_data:
        corporation_data[col] = pd.to_numeric(corporation_data[col], errors='coerce')       

    # school_data = school_data.filter(
    #     regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",
    #     axis=1,
    # )
    corporation_data = corporation_data.filter(
        regex=r"Total Tested$|Total Proficient$|IREAD Pass N|IREAD Test N|Year",
        axis=1,
    )

    # missing_mask = ~school_data.any()
    # missing_cols = school_data.columns[missing_mask].to_list()

    # valid_mask = school_data.any()
    # school_data = school_data[school_data.columns[valid_mask]]

    # corporation_data = corporation_data[corporation_data.columns[valid_mask]]    

    # reset index as 'Year' for corp_rate data
    corporation_data = corporation_data.set_index("Year")

    # TODO: MOVE TO FUNCTION
    # iterate over (non missing) columns, calculate the average,
    # and store in a new column
    categories = ethnicity + subgroup + grades + ["School Total"]

    for s in subject:
        for c in categories:
            new_col = c + "|" + s + " Proficient %"
            proficient = c + "|" + s + " Total Proficient"
            tested = c + "|" + s + " Total Tested"

            corporation_data[new_col] = (
                corporation_data[proficient] / corporation_data[tested]
            )

    # replace 'Totals' with calculation taking the masking step into account
    # The masking step above removes grades from the corp_rate dataframe
    # that are not also in the school dataframe (e.g., if school only has data
    # for grades 3, 4, & 5, only those grades will remain in corp_rate df).
    # However, the 'Corporation Total' for proficiency in a subject is
    # calculated using ALL grades. So we need to recalculate the 'Corporation Total'
    # rate manually to ensure it includes only the included grades.
    adjusted_corporation_math_proficient = corporation_data.filter(
        regex=r"Grade.+?Math Total Proficient"
    )
    adjusted_corporation_math_tested = corporation_data.filter(
        regex=r"Grade.+?Math Total Tested"
    )

    corporation_data["School Total|Math Proficient %"] = adjusted_corporation_math_proficient.sum(axis=1) \
    / adjusted_corporation_math_tested.sum(axis=1)

    adjusted_corporation_ela_proficient = corporation_data.filter(regex=r"Grade.+?ELA Total Proficient")
    adjusted_corporation_ela_tested = corporation_data.filter(regex=r"Grade.+?ELA Total Tested")

    corporation_data["School Total|ELA Proficient %"] = adjusted_corporation_ela_proficient.sum(axis=1) \
        / adjusted_corporation_ela_tested.sum(axis=1)

    # use this to ensure corporation data has same categories
    # add Year to ensure it is retained as well
    column_list = school_data['Category'].tolist() + ['Year']

    # calculate IREAD Pass %
    if "IREAD Pass %" in column_list:
        
        corporation_data["IREAD Pass %"] = (corporation_data["IREAD Pass N"] / corporation_data["IREAD Test N"])

        # school_data["IREAD Pass %"] = pd.to_numeric(school_data["IREAD Pass N"], errors="coerce") \
        #     / pd.to_numeric(school_data["IREAD Test N"], errors="coerce")

        # If either Test or Pass category had a '***' value, the resulting value will be 
        # NaN - we want it to display '***', so we just fillna
        # school_data["IREAD Pass %"] = school_data["IREAD Pass %"].fillna("***")

        # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
        # school_data = school_data.filter(regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$",axis=1)
    
    corporation_data = corporation_data.filter(regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$",axis=1)

    # add School Name column back
    # school_data = pd.concat([school_data, school_info], axis=1, join="inner")

    # reset indexes
    # k8_school_data = k8_school_data.reset_index(drop=True)
    
    # no drop because index was previous set to year
    corporation_data = corporation_data.reset_index()

    # ensure columns headers are strings
    # k8_school_data.columns = k8_school_data.columns.astype(str)
    corporation_data.columns = corporation_data.columns.astype(str)
    
    # keep only corp columns that match school_columns
    corporation_data = corporation_data[corporation_data.columns.intersection(column_list)]

    # # freeze Corp Proficiency dataframe in current state for use in academic analysis page
    # academic_analysis_corp_dict = k8_corp_rate_data.to_dict()
    # k8_corp_data = k8_corp_rate_data.copy()

    # Ensure each df has same # of years - relies on each year having a single row
    # k8_num_years = len(k8_school_data.index)

    # # transpose dataframes and clean headers
    # k8_school_data = (
    #     k8_school_data.set_index("Year")
    #     .T.rename_axis("Category")
    #     .rename_axis(None, axis=1)
    #     .reset_index()
    # )

    #     # Keep category and all available years of data
    # k8_school_data = k8_school_data.iloc[:, : (k8_num_years + 1)]

    corporation_data = (corporation_data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

    # Keep category and all available years of data
    # k8_corp_data = k8_corp_data.iloc[:, : (k8_num_years + 1)]  

    # k8_school_data = k8_school_data[
    #     k8_school_data["Category"].str.contains("School Name") == False
    # ]

    # k8_school_data = k8_school_data.reset_index(drop=True)

    # reverse order of corp_data columns (ignoring 'Category') so current year is first and
    # get clean list of years
    k8_year_cols = list(school_data.columns[:0:-1])
    k8_year_cols.reverse()

    # add_suffix is applied to entire df. To hide columns we dont want\
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