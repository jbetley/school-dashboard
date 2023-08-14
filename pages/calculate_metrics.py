########################################
# ICSB Dashboard - Metric Calculations #
########################################
# author:   jbetley
# version:  1.09
# date:     08/14/23

import pandas as pd
import numpy as np
import itertools

from .load_data import get_school_index, get_demographic_data, get_letter_grades
from .process_data import get_attendance_data
from .calculations import calculate_year_over_year, set_academic_rating, conditional_fillna, calculate_difference, \
    get_excluded_years

def calculate_attendance_metrics(school: str, year: str) -> pd.DataFrame:
    """
    Gets attendance data (df) for school and school corporation, calculates the
    year over year difference using calculate_year_over_year than adds a Rating
    using set_academic_rating

    Args:
        school (str): a school ID number
        year (str): the selected year

    Returns:
        pd.DataFrame: a dataframe with School, Diff, & Rate columns for each year
    """
    selected_school = get_school_index(school)    
    corp_id = int(selected_school["GEO Corp"].values[0])

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
        attendance_metrics.insert(loc = z, column = attendance_metrics.columns[y][0:4] + "Diff", value = values)
        y+=3
        z+=3

    attendance_metrics.insert(loc=0, column="Category", value="1.1.a. Attendance Rate")

    attendance_limits = [
        0,
        -0.01,
        -0.01,
    ]

    # NOTE: Calculates and adds an accountability rating ("MS", "DNMS", "N/A", etc)
    # as a new column to existing dataframe:
    #   1) the loop ("for i in range(attendance_data_metrics.shape[1], 1, -3)")
    #   counts backwards by -3, beginning with the index of the last column in
    #   the dataframe ("attendance_data_metrics.shape[1]") to "1" (actually "2"
    #   as range does not include the last number). These are indexes, so the
    #   loop stops at the third column (which has an index of 2);
    #   2) for each step, the code inserts a new column, at index "i". The column
    #   header is a string that is equal to "the year (YYYY) part of the column
    #   string (attendance_data_metrics.columns[i-1])[:7 - 3]) + "Rate" + "i"
    #   (the value of "i" doesn"t matter other than to differentiate the columns) +
    #   the accountability value, a string returned by the set_academic_rating() function.
    #   3) the set_academic_rating() function calculates an "accountability rating"
    #   ("MS", "DNMS", "N/A", etc) taking as args:
    #       i) the "value" to be rated. this will be from the "School" column, if
    #       the value itself is rated (e.g., iread performance), or the difference
    #       ("Diff") column, if there is an additional calculation required (e.g.,
    #       year over year or compared to corp);
    #       ii) a list of the threshold "limits" to be used in the calculation; and
    #       iii) an integer "flag" which tells the function which calculation to use.
    
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

    # drop corp rates
    attendance_metrics = attendance_metrics.loc[:, ~attendance_metrics.columns.str.contains("Corp")]
    
    return attendance_metrics

def calculate_k8_yearly_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a dataframe of school academic data and calculates the proficiency difference
    between successive years and the assigns an academic rating to each year.

    Args:
        data (pd.DataFrame): school proficiency data

    Returns:
        pd.DataFrame: a dataframe with School, Diff, & Rate columns for each year
    """
    data.columns = data.columns.astype(str)
    
    # drop low/high grade rows
    data = data[(data["Category"] != "Low Grade") & (data["Category"] != "High Grade")]
    
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
        data.insert(loc = z, column = data.columns[x][0:4] + "Diff", value = values)
        z+=3
        x+=3

    data.insert(loc=0, column="Category", value=category_header)
    data["Category"] = (data["Category"].str.replace(" Proficient %", "").str.strip())
    
    # Add first_year data back
    data[first_year.columns] = first_year

    # Create clean col lists - (YYYY + "School") and (YYYY + "Diff")
    school_years_cols = list(data.columns[1:])
    
    # thresholds for academic ratings
    years_limits = [0.05, 0.02, 0, 0]

    # Slightly different formula for this one:
    #   1) the loop "for i in range(data.shape[1]-2, 1, -3)" counts backwards by -3,
    #   beginning with 2 minus the index of the last column in the dataframe
    #   ("data.shape[1]-2") to "1." This ignores the last two columns which will always
    #   be "first year" data and "first year" n-size. These are indexes, so the
    #   loop stops at the third column (which has an index of 2);
    #   e.g., 12 col dataframe - from index 11 to 0 - we want to get rating of 9,6,3
    #   2) for each step, the code inserts a new column, at index "i". The column
    #   header is a string that is equal to "the year (YYYY) part of the column
    #   string (attendance_data_metrics.columns[i-1])[:7 - 3]) + "Rate" + "i"
    #   (the value of "i" doesn"t matter other than to differentiate the columns) +
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
    data = conditional_fillna(data)

    data.columns = data.columns.astype(str)

    # one last processing step is needed to ensure proper ratings. The set_academic_rating()
    # function assigns a rating based on the "Diff" difference value (either year over year
    # or as compared to corp). For the year over year comparison it is possible to get a
    # rating of "Approaches Standard" for a "Diff" value of "0.00%" when the yearly ratings
    # are both "0". There is no case where we want a school to receive anything other
    # than a "DNMS" for a 0% proficiency. However, the set_academic_rating() function does
    # not have access to the values used to calculate the difference value (so it cannot
    # tell if a 0 value is the result of a 0 proficiency). So we need to manually replace
    # any rating in the Rating column with "DMNS" where the School proficiency value is "0.00%."

    # because we are changing the value of one column based on the value of another (paired)
    # column, the way we do this is to create a list of tuples (a list of year and rating
    # column pairs), e.g., [("2022School", "2022Rating3")], and then iterate over the column pair

    # NOTE: the zip function stops at the end of the shortest list which automatically drops
    # the single "Initial Year" column from the list. It returns an empty list if
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
    """
    Take a school and corp dataframe (and year string), calculates the differences between the two for
    each proficiency Category, and then assigns an academic rating for each category for each year.

    Args:
        school_data (pd.DataFrame): school proficiency data
        corp_data (pd.DataFrame): school corporation proficiency data
        year (str): selected school year

    Returns:
        pd.DataFrame: dataframe with School, Tested, Diff, and Rate columns for each year
    """
    excluded_years = get_excluded_years(year)

    # NOTE: using difference() reverses the order of the columns which would normally
    # be an issue, except that in this case we are manually organizing the columns (merged_cols)
    if excluded_years:
        corp_data = corp_data[corp_data.columns.difference(excluded_years)]

    school_data.columns = school_data.columns.astype(str)
    corp_data.columns = corp_data.columns.astype(str)

    category_list = school_data["Category"].tolist() + ["Year"]
    
    # keep only corp Category rows that match school Category rows
    corp_data = corp_data[corp_data["Category"].isin(category_list)]

    school_data = school_data[school_data["Category"].str.contains("Low|High") == False]

    # Clean up and merge school and corporation dataframes
    year_cols = list(school_data.columns[:0:-1])
    year_cols = [c[0:4] for c in year_cols]
    year_cols = list(set(year_cols))
    year_cols.sort(reverse=True)
    
    # add_suffix to year cols
    corp_data = (corp_data.set_index(["Category"]).add_suffix("Corp").reset_index())

    # Use column list to merge
    corp_cols = [e for e in corp_data.columns if "Corp" in e]
    school_cols = [e for e in school_data.columns if "School" in e]
    nsize_cols = [e for e in school_data.columns if "N-Size" in e]
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

    # reorganize headers
    final_cols = list(itertools.chain(*zip(school_cols, nsize_cols, result_cols)))
    final_cols.insert(0, "Category")

    k8_result = k8_result.set_axis(result_cols, axis=1)
    k8_result.insert(loc=0, column="Category", value=tmp_category)

    # merge and reorder cols
    final_k8_academic_data = merged_data.merge(k8_result, on="Category", how="left")

    final_k8_academic_data = final_k8_academic_data[final_cols]
    
    # NOTE: Pretty sure this is redundant as we add "Proficient %; suffix to totals
    # above, then remove it here, then pass to academic_analysis page, and add it
    # back. But I tried to fix it once and broke everything. So I"m just gonna
    # leave it alone for now.
    final_k8_academic_data["Category"] = (final_k8_academic_data["Category"].str.replace(" Proficient %", "").str.strip())

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

    final_k8_academic_data = conditional_fillna(final_k8_academic_data)

    return final_k8_academic_data

def calculate_high_school_metrics(merged_data: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a school dataframe and assigns an academic rating for each category for each year.

    Args:
    merged_data (pd.DataFrame): school proficiency data

    Returns:
        pd.DataFrame: dataframe with School, Tested, Diff, and Rate columns for each year
    """
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

    combined_grad_metrics = conditional_fillna(combined_grad_metrics)
    
    return combined_grad_metrics

def calculate_adult_high_school_metrics(school: str, data: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a school dataframe and school ID string and assigns an academic rating
    for each category for each year.

    Args:
        school_data (pd.DataFrame): adult high school academic data
        year (str): selected school year

    Returns:
        pd.DataFrame: dataframe with School and Rate columns for each year
    """
    # AHS metrics is such a small subset of all metrics, instead of pulling in the
    # entire HS DF, we just pull the three datapoints we need directly from the DB.

    if len(data.index) > 0:
        data.columns = data.columns.astype(str)

        data["CCR Percentage"] = pd.to_numeric(data["AHS|CCR"]) / pd.to_numeric(data["AHS|Grad All"])
        
        ahs_data = data [["Year", "CCR Percentage"]]

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
    """
    Takes a school dataframe and an academic rating for iread proficiency
    for each year.

    Args:
        school_data (pd.DataFrame): school academic data

    Returns:
        pd.DataFrame: dataframe with School,Tested, Diff, and Rate columns for each year
    """    
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

    data = conditional_fillna(data)
    data.columns = data.columns.astype(str)

    return data

def calculate_financial_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a dataframe of float values and returns the same dataframe with one
    extra 'Rating' column for each year of data. Ratings are calculated based
    on specific thresholds according to ICSB Accountability System (MS, DNMS, or N/A (or null)) 
    NOTE: This was refactored (03.01.23) to use vectorized operations. Not sure
    that the refactored version is easier to comprehend than the previous
    loop version. it is also longer.

    Args:
        data (pd.DataFrame): a DataFrame object with a Category column and a variable
        number of year columns.

    Returns:
        final_grid (pd.DataFrame): a DataFrame object with additional 'Rating' columns
    """

    # Some schools have 'pre-opening' financial activity before the school
    # begins to operate and receive state/federal grants. The below code
    # ignores all columns (years) where the value in the State Grant column
    # is equal to '0'. Any pre-opening data will be lost

    # NOTE: A more precise fix would be to keep all columns (including those with
    # no value in grant columns), but ignore/except (N/A) any calculation that requires
    # either grant revenue or adm. Need to test

    operating_data = data.loc[:,~(data.iloc[1]==0)].copy()

    # If school only has opening year data, the slice above will drop it, resulting in a single
    # column df ('Category')
    if len(operating_data.columns) <=1:

        final_grid = pd.DataFrame()

    else:

        cols = [i for i in operating_data.columns if i not in ['Category']]

        for col in cols:
            operating_data[col] = pd.to_numeric(operating_data[col], errors='coerce')

        # transpose financial information
        metrics = (
            operating_data.set_index("Category")
            .T.rename_axis("Year")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        # create a dataframe for the financial metric table
        metric_grid = pd.DataFrame()

        # Current Ratio calculation
        metric_grid['Current Ratio'] = metrics['Current Assets']/metrics['Current Liabilities']
        
        # returns true if 'Current Ratio' is > 1.1 or > 1 and CY > PY 
        def ratio_metric_calc(cur,diff):
            return 'MS' if ((cur > 1.1) | ((cur > 1) & (diff == True))) else 'DNMS'
        
        # The vectorized way to run calculations between different rows of the
        # same column is to shift a copy of the column either up or down using
        # shift. Shift(-1) moves the column up one row. Shift(1) moves the column
        # down one row. In some cases, this causes the calculated value to be offset by
        # the amount of the shift. For display purposes, we need to account for this by
        # shifting the calculated column up by the amount of the original shift
        metric_grid['Current Ratio Previous'] = metric_grid['Current Ratio'].shift(-1)

        metric_grid['Current Ratio Trend'] = \
            metric_grid['Current Ratio'] > metric_grid['Current Ratio Previous']
        
        metric_grid['Current Ratio Metric'] = \
            metric_grid.apply(lambda x: ratio_metric_calc(x['Current Ratio'], x['Current Ratio Trend']), axis=1)

        # Day's Cash calculation
        metric_grid['Days Cash on Hand'] = \
            metrics['Unrestricted Cash'] / ((metrics['Operating Expenses'] - metrics['Depreciation/Amortization'])/365)

        # returns true if day's cash is > 45 or >= 30 and CY > PY
        def days_cash_metric_calc(cur,diff):
            return 'MS' if ((cur > 45) | ((cur >= 30) & (diff == True))) else 'DNMS'
    
        metric_grid['Days Cash Previous'] = metric_grid['Days Cash on Hand'].shift(-1)
        metric_grid['Days Cash Trend'] = metric_grid['Days Cash on Hand'] > metric_grid['Days Cash Previous']
        
        metric_grid['Days Cash Metric'] = \
            metric_grid.apply(lambda x: days_cash_metric_calc(x['Days Cash on Hand'], x['Days Cash Trend']), axis=1)

        # Annual Enrollment Change calculation
        metric_grid['Annual Enrollment Change'] = \
            (metrics['ADM Average'].shift(1) - metrics['ADM Average']) / metrics['ADM Average']
        
        # See above, because we used a shift down in the above calculation, we have to shift the
        # row back up post calculation
        metric_grid['Annual Enrollment Change'] = metric_grid['Annual Enrollment Change'].shift(-1)
        metric_grid['Annual Enrollment Change Metric'] = \
            metric_grid['Annual Enrollment Change'].apply(lambda x: 'MS' if (x > -0.1) else 'DNMS')    

        # if the result is NaN (no calculation is possible), the Metric should be N/A
        metric_grid.loc[metric_grid['Annual Enrollment Change'].isnull(), 'Annual Enrollment Change Metric'] = 'N/A'

        # Primary Reserve Ratio calculation
        metric_grid['Primary Reserve Ratio'] = metrics['Unrestricted Net Assets'] / metrics['Operating Expenses']
        metric_grid['Primary Reserve Ratio Metric'] = \
            metric_grid['Primary Reserve Ratio'].apply(lambda x: 'MS' if (x > 0.25) else 'DNMS')

        # Change in Net Assets Margin/Aggregated Three-Year Margin
        metric_grid['Change in Net Assets Margin'] = metrics['Change in Net Assets'] / metrics['Operating Revenues'] 
        metric_grid['Aggregated Three-Year Margin'] = (
            metrics['Change in Net Assets'] + metrics['Change in Net Assets'].shift() + metrics['Change in Net Assets'].shift(2)
            ) / (
            metrics['Operating Revenues'] + metrics['Operating Revenues'].shift() + metrics['Operating Revenues'].shift(2)
            )

        metric_grid['Aggregated Three-Year Margin'] = metric_grid['Aggregated Three-Year Margin'].shift(-2)

        # create temporary columns for calculations include values from previous year
        metric_grid['AgMar Previous'] = metric_grid['Aggregated Three-Year Margin'].shift(-1)
        metric_grid['AgMar Previous 2'] = metric_grid['Aggregated Three-Year Margin'].shift(-2)
        metric_grid['AgMar Trend'] = (
            (metric_grid['Aggregated Three-Year Margin'] > metric_grid['AgMar Previous']) &
            (metric_grid['AgMar Previous'] > metric_grid['AgMar Previous 2']))

        # A school meets standard if: Aggregated Three-Year Margin is positive and the most
        # recent year Change in Net Assets Margin is positive; or Aggregated Three-Year Margin
        # is greater than -1.5%, the trend is positive for the last two years, and Change in Net
        # Assets Margin for the most recent year is positive. For schools in their first and
        # second year of operation, the cumulative Change in Net Assets Margin must be positive.
        def asset_margin_calc(chcur,agcur,diff):
            return 'MS' if (
                ((chcur > 0) & (agcur > 0)) | 
                (((chcur > 0) & (agcur > .015)) & (diff == True))
            ) else 'DNMS'

        metric_grid['Aggregated Three-Year Margin Metric'] = \
            metric_grid.apply(lambda x: asset_margin_calc(x['Change in Net Assets Margin'], x['Aggregated Three-Year Margin'],x['AgMar Trend']), axis=1)
        
        metric_grid['Change in Net Assets Margin Metric'] = \
            metric_grid.apply(lambda x: asset_margin_calc(x['Change in Net Assets Margin'], x['Aggregated Three-Year Margin'],x['AgMar Trend']), axis=1)
        
        # if value is NaN (no calculation is possible), the Metric should be N/A
        metric_grid.loc[metric_grid['Aggregated Three-Year Margin'].isnull(), 'Aggregated Three-Year Margin Metric'] = 'N/A'

        # in the dataframe, each row is a year, with earliest years at the end. In YR 1 and Y2
        # CHNM Metric is 'MS' if the cumulative value of CHNM is > 0 (positive)
        if metric_grid.loc[metric_grid.index[-1],'Change in Net Assets Margin'] > 0:
            metric_grid.loc[metric_grid.index[-1], 'Change in Net Assets Margin Metric'] = 'MS'
        else:
            metric_grid.loc[metric_grid.index[-1], 'Change in Net Assets Margin Metric'] = 'DNMS'
        
        # CHNM Metric is 'MS' if first + second year value is > 0
        # Only test if there are at least 2 years of data
        if len(metric_grid.index) >= 2:
            if (metric_grid.loc[metric_grid.index[-1],'Change in Net Assets Margin'] + metric_grid.loc[metric_grid.index[-2],'Change in Net Assets Margin']) > 0:
                metric_grid.loc[metric_grid.index[-2],'Change in Net Assets Margin Metric'] = 'MS'
            else:
                metric_grid.loc[metric_grid.index[-2], 'Change in Net Assets Margin Metric'] = 'DNMS'

        # Debt to Asset Ratio
        metric_grid['Debt to Asset Ratio'] = metrics['Total Liabilities'] / metrics['Total Assets']
        metric_grid['Debt to Asset Ratio Metric'] = \
            metric_grid['Debt to Asset Ratio'].apply(lambda x: 'MS' if (x < 0.9) else 'DNMS')    

        # Cash Flow and Multi-Year Cash Flow
        metric_grid['Cash Flow'] = metrics['Unrestricted Cash'].shift() - metrics['Unrestricted Cash']
        metric_grid['Cash Flow'] = metric_grid['Cash Flow'].shift(-1)

        # the YR1 value of 'Cash Flow' is equal to the YR1 value of 'Unrestricted Cash'
        metric_grid.loc[len(metric_grid['Cash Flow'])-1,'Cash Flow'] = metrics['Unrestricted Cash'].iloc[-1]

        metric_grid['Multi-Year Cash Flow'] = metrics['Unrestricted Cash'].shift(2) - metrics['Unrestricted Cash']
        metric_grid['Multi-Year Cash Flow'] = metric_grid['Multi-Year Cash Flow'].shift(-2)

        # A school meets standard if both CY Multi-Year Cash Flow and One Year Cash Flow
        # are positive and one out of the two previous One Year Cash Flows are positive
        # For schools in the first two years of operation, both years must have a positive
        # Cash Flow (for purposes of calculating Cash Flow, the school's Year 0 balance is
        # assumed to be zero).

        # NOTE: I am positive there is a more pythonic way to do this, but I'm too tired
        # to figure it out, maybe later
        for i in range(len(metric_grid['Cash Flow'])-2):
            
            # get current year value
            current_year_cash = metric_grid.loc[i,'Cash Flow']
            
            # determine if two previous years are greater than zero (TRUE or FALSE)
            previous_year_cash = metric_grid.loc[i+1,'Cash Flow'] > 0
            second_previous_year_cash = metric_grid.loc[i+2,'Cash Flow'] > 0

            # school meets standard if current year Cash Flow value and current
            # year Multi-Year Cash Flow value are positive and at least one of 
            # the previous two years are positive. converting a boolean to int
            # results in either 0 (false) or 1 (true). when added together, a
            #  value of 1 or 2 means one or both years were positive
            if (metric_grid.loc[i]['Multi-Year Cash Flow'] > 0) & (current_year_cash > 0) & \
                ((int(previous_year_cash) + int(second_previous_year_cash)) >= 1):
                
                metric_grid.loc[i,'Cash Flow Metric'] = 'MS'
                metric_grid.loc[i,'Multi-Year Cash Flow Metric'] = 'MS'

            else:
                metric_grid.loc[i,'Multi-Year Cash Flow Metric'] = 'DNMS'
                metric_grid.loc[i,'Cash Flow Metric'] = 'DNMS'

        # A school meets standard if Cash Flow is positive in first two years (see above)
        if metric_grid.loc[metric_grid.index[-1],'Cash Flow'] > 0:
            metric_grid.loc[metric_grid.index[-1], 'Cash Flow Metric'] = 'MS'
        else:
            metric_grid.loc[metric_grid.index[-1],'Cash Flow Metric'] = 'DNMS'

        # Metric is 'MS' if first + second year value is > 0
        # Only test if there are at least 2 years of data
        if len(metric_grid.index) >= 2:        
            if (metric_grid.loc[metric_grid.index[-1],'Cash Flow'] > 0) & (metric_grid.loc[metric_grid.index[-2],'Cash Flow'] > 0):
                metric_grid.loc[metric_grid.index[-2],'Cash Flow Metric'] = 'MS'
            else:
                metric_grid.loc[metric_grid.index[-2],'Cash Flow Metric'] = 'DNMS'

        # if Multi-Year Cash Flow is NaN (no calculation is possible), Multi-Year Cash Flow Metric should be N/A
        metric_grid.loc[metric_grid['Multi-Year Cash Flow'].isnull(), 'Multi-Year Cash Flow Metric'] = 'N/A'

        # Debt Service Coverage Ratio
        metric_grid['Debt Service Coverage Ratio'] = \
            (metrics['Change in Net Assets'] + metrics['Lease/Mortgage Payments'] + metrics['Depreciation/Amortization'] + metrics['Interest Expense']) / (metrics['Lease/Mortgage Payments'] + metrics['Principal Payments'] + metrics['Interest Expense'])

        metric_grid['Debt Service Coverage Ratio Metric'] = \
            metric_grid['Debt Service Coverage Ratio'].apply(lambda x: 'MS' if (x > 1) else 'DNMS')    
        
        # Drop all temporary (calculation) columns
        metric_grid = metric_grid.drop(columns=['Days Cash Previous','Days Cash Trend','Current Ratio Previous','Current Ratio Trend','AgMar Previous','AgMar Previous 2','AgMar Trend'], axis=1)

        metric_grid['Year'] = metrics['Year']

        # Transpose Again
        metric_grid = (
            metric_grid.set_index("Year")
            .T.rename_axis("Category")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        # A very specific sort function
        # Because this is for display, we need to manually reorder the columns
        def sort_financial_metrics(column: pd.Series) -> pd.Series:
            reorder = [
                'Current Ratio','Current Ratio Metric',
                'Days Cash on Hand','Days Cash Metric',
                'Annual Enrollment Change', 'Annual Enrollment Change Metric',
                'Primary Reserve Ratio', 'Primary Reserve Ratio Metric',
                'Change in Net Assets Margin', 'Change in Net Assets Margin Metric',
                'Aggregated Three-Year Margin', 'Aggregated Three-Year Margin Metric',
                'Debt to Asset Ratio', 'Debt to Asset Ratio Metric',
                'Cash Flow', 'Cash Flow Metric',
                'Multi-Year Cash Flow', 'Multi-Year Cash Flow Metric',
                'Debt Service Coverage Ratio', 'Debt Service Coverage Ratio Metric',
            ]
            
            cat = pd.Categorical(column, categories=reorder, ordered=True)
            
            return pd.Series(cat)

        metric_grid_sorted = metric_grid.sort_values(by='Category', key=sort_financial_metrics)

        final_grid = pd.DataFrame()

        # Restructure dataframe so that every other row (Metrics) become columns
        # https://stackoverflow.com/questions/36181622/moving-every-other-row-to-a-new-column-and-group-pandas-python
        all_cols = [i for i in metric_grid_sorted if i not in ['Category']]

        for col in all_cols:
            final_grid[col] = metric_grid_sorted[col].iloc[::2].values
            final_grid[col + 'Rating'] = metric_grid_sorted[col].iloc[1::2].values
    
        # Add the Categories Back without the Metric Rows
        new_cols = pd.DataFrame()
        new_cols['Category'] = metric_grid_sorted['Category']
        new_cols = new_cols[~new_cols['Category'].str.contains("Metric")]
        new_cols = new_cols.reset_index()

        final_grid.insert(0, "Category", new_cols['Category'])

        # Remove years String from Rating Columns
        final_grid.columns = final_grid.columns.str.replace(r'\d{4}Rating', 'Rating', regex=True)

        # Add new rows for 'Near Term|Long Term' titles
        # NOTE: it baffles me why this is so complicated 
        # add row between existing indexes, sort and then reset
        final_grid.loc[3.5,'Category'] = 'Long Term'
        final_grid = final_grid.sort_index().reset_index(drop=True)
        
        # because this is the first row, we use indexing: setting with enlargement
        final_grid.loc[-1, 'Category'] = 'Near Term'
        final_grid.index = final_grid.index + 1
        final_grid = final_grid.sort_index() 
        final_grid = final_grid.rename(columns = {'Category': 'Metric'})

        # convert all values to numeric
        year_cols = [i for i in final_grid.columns if i not in ['Metric','Rating']]

        # Add integer to Rating columns (needed for dash data_table in order to distinguish columns)
        final_grid.columns = [f'{x} {i}' if x in 'Rating' else f'{x}' for i, x in enumerate(final_grid.columns, 1)]
    
        # force year columns to numeric and round
        for col in year_cols:
            final_grid[col] = pd.to_numeric(final_grid[col], errors='coerce').round(2)

    return final_grid