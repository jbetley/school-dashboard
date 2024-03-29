########################################
# ICSB Dashboard - Metric Calculations #
########################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     02/21/24

import pandas as pd
import numpy as np
import itertools
from typing import Tuple

from .load_data import (
    get_school_index,
    get_attendance_data
)

from .calculations import (
    calculate_year_over_year,
    set_academic_rating,
    conditional_fillna,
    calculate_difference
)


def calculate_attendance_metrics(school: str, school_type: str, year: str) -> pd.DataFrame:
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

    corp_type = "corp_" + school_type

    school_attendance_rate = get_attendance_data(school, school_type, year)

    corp_attendance_rate = get_attendance_data(corp_id, corp_type, year)

    corp_attendance_rate = (
        corp_attendance_rate.set_index(["Category"])
        .add_suffix("Corp Avg")
        .reset_index()
    )
    school_attendance_rate = (
        school_attendance_rate.set_index(["Category"])
        .add_suffix("School")
        .reset_index()
    )
    school_attendance_rate = school_attendance_rate.drop("Category", axis=1)
    corp_attendance_rate = corp_attendance_rate.drop("Category", axis=1)

    # concat the two df's and reorder so that the columns alternate
    attendance_metrics = pd.concat(
        [school_attendance_rate, corp_attendance_rate], axis=1
    )
    reordered_cols = list(
        sum(zip(school_attendance_rate.columns, corp_attendance_rate.columns), ())
    )

    attendance_metrics = attendance_metrics[reordered_cols]

    # loops over dataframe calculating difference between a pair of columns, inserts the result in
    # the following column, and then skips over the calculated columns to the next pair
    y = 0
    z = 2
    end = int(len(attendance_metrics.columns) / 2)

    for x in range(0, end):
        values = calculate_year_over_year(
            attendance_metrics.iloc[:, y], attendance_metrics.iloc[:, y + 1]
        )
        attendance_metrics.insert(
            loc=z, column=attendance_metrics.columns[y][0:4] + "Diff", value=values
        )
        y += 3
        z += 3

    attendance_metrics.insert(loc=0, column="Category",  value=["1.1.a. Attendance Rate", "(Chronic Absenteeism %)"])

    # drop corp rates
    attendance_metrics = attendance_metrics.loc[
        :, ~attendance_metrics.columns.str.contains("Corp")
    ]

    attendance_limits = [0, -0.01]

    # Calculates and adds an accountability rating ("MS", "DNMS", "N/A", etc)
    # as a new column for each measured value using a reverse loop:

    #   1) the loop ("for i in range(attendance_data_metrics.shape[1], 1, -2)")
    #   counts backwards by 2, from a number equal to the length of the columns
    #   (attendance_data_metrics.shape[1]) to 1. These are indexes, so the
    #   loop stops at the third column (which has an index of 2);
    #   2) for each step, the code inserts a new column, at index "i". The column
    #   header is a string that is equal to "the year (YYYY) part of the column
    #   string  + "Rate" + "i" (the value of "i" doesn"t matter other than to
    #   differentiate the columns) + the accountability value, which is a string
    #   returned by the set_academic_rating() function. Note that we have to subtract
    #   1 from the column to be tested (to account for 0 based indexing)
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
            str(attendance_metrics.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
            attendance_metrics.apply(
                lambda x: set_academic_rating(
                    x[attendance_metrics.columns[i - 1]], attendance_limits, 3
                ),
                axis=1,
            ),
        )
        for i in range(attendance_metrics.shape[1], 1, -2)
    ]

    # NOTE: Currently, chronic absenteeism is not officially in the
    # accountability system- we are calculating it above (using the
    # attendance threshold) but removing the rate for now. comment out 
    # or remove the next two lines to add rating back
    rate_cols = [col for col in attendance_metrics.columns if "Rate" in col]
    attendance_metrics.loc[attendance_metrics["Category"] == "(Chronic Absenteeism %)", rate_cols] = 'NA'
    
    return attendance_metrics


def calculate_values(data: pd.DataFrame, year: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
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

    # copies of school and corp data for comparison dataframe (school to corp)
    school_comparison_data = data.filter(regex="Category|School|N-Size", axis=1).copy()
    corp_comparison_data = data.filter(regex="Category|Corp", axis=1).copy()

    # store and drop Category column temporarily for calculations
    category_column = data["Category"]
    data = data.drop("Category", axis=1)

    # school data for year over year dataframe
    year_over_year_data = data.filter(regex="School|N-Size", axis=1).copy()
    
    # Calculate Year over Year Values #

    # Two columns for each year - [School, N-Size]; years are ascending. We want calculate
    # the difference between the second to last column (the school column for the most recent Year) and
    # the fourth from last column (the school column for the most recent previous year) and continue doing
    # so as long as we have a two-year pair. That is, given a dataframe with cols: ['2019School', '2019N-Size',
    # '2021School', '2021N-Size', '2022School', '2022N-Size', '2023School', '2023N-Size'], we want 3 loops:
    # 2023School - 2022School; 2022School - 2021School; & 2021School - 2019School. As 2019School does not have
    # a previous year, we stop at that point. We calculate the # of loops by: length of the columns minus 2 (for
    # the initial School, N-Size pair) divided by 2.

    # The following loops over the dataframe from back to front, calculating the difference between col (Year)
    # and col - 2 (Previous Year) and inserting the result at the last position col[-1] and then every 3rd index
    # position prior.

    # NOTE: Vectorize using shift() and then insert result at proper index?
    # Could do, but would require reworking calculate_year_over_year() - so leave in loop for now
    # shifted_data = data.shift(2, axis=1)
    # result_data = calculate_year_over_year(data,shifted_data)
    # len 8: Want 7-5; 5-3; 3-1 -> insert result at 8,5,3

    len_cols = len(year_over_year_data.columns)

    num_pairs = int((len_cols - 2) / 2)
    end = len_cols - 2  # begin at second to last column

    for y in range(0, num_pairs):
        values = calculate_year_over_year(year_over_year_data.iloc[:, end], year_over_year_data.iloc[:, end - 2])
        year_over_year_data.insert(loc=end + 2, column=year_over_year_data.columns[end][0:4] + "Diff", value=values)
        end -= 2

    year_over_year_data.insert(loc=0, column="Category", value=category_column)
    year_over_year_data["Category"] = year_over_year_data["Category"].str.replace(" Proficient %", "").str.strip()

    # Calculate Comparison Values #

    # Clean up and merge school and corporation dataframes
    year_cols = list(school_comparison_data.columns[:0:-1])
    year_cols = [c[0:4] for c in year_cols]
    year_cols = list(set(year_cols))
    year_cols.sort()

    # Use column list to merge
    corp_cols = [e for e in corp_comparison_data.columns if "Corp" in e]
    school_cols = [e for e in school_comparison_data.columns if "School" in e]
    nsize_cols = [e for e in school_comparison_data.columns if "N-Size" in e]
    school_cols.sort()
    corp_cols.sort()
    nsize_cols.sort()

    result_cols = [str(s) + "Diff" for s in year_cols]

    # temporarily place school and corp cols next to each other
    merged_cols = list(itertools.chain(*zip(school_cols, corp_cols, nsize_cols)))
    merged_cols.insert(0, "Category")

    # merge school and corp data
    merged_comparison_data = school_comparison_data.merge(corp_comparison_data, on="Category", how="left")
    merged_comparison_data = merged_comparison_data[merged_cols]

    # check to see if data is HS or K8
    if school_comparison_data["Category"].str.contains("Graduation").any():
        is_high_school = True
    else:
        is_high_school = False

    # tmp drop Category Column to calculate difference
    school_comparison_data = school_comparison_data.drop("Category", axis=1)
    # school_comparison_data = school_comparison_data.fillna(value=np.nan)

    corp_comparison_data = corp_comparison_data.drop("Category", axis=1)
    # corp_comparison_data = corp_comparison_data.fillna(value=np.nan)
    
    # calculate difference between two dataframes (using a for loop
    # is not ideal, but we need to use row-wise calculations)
    comparison_result = pd.DataFrame()

    # slightly different difference calculation for HS vs K8
    if is_high_school:

        for c in year_cols:
            comparison_result[c + "Diff"] = calculate_difference(
                school_comparison_data[c + "School"], corp_comparison_data[c + "Corp"]
            )
            
    else:

        for c in school_comparison_data.columns:
            c = c[0:4]
            comparison_result[c + "Diff"] = calculate_difference(
                school_comparison_data[c + "School"], corp_comparison_data[c + "Corp"]
            )
 
    # Create final column order
    final_cols = list(itertools.chain(*zip(school_cols, nsize_cols, result_cols)))
    final_cols.insert(0, "Category")

    comparison_result = comparison_result.set_axis(result_cols, axis=1)

    # category_column = category_column.reset_index(drop=True)
    comparison_result.insert(loc=0, column="Category", value=category_column)
    
    # merge and reorder cols
    comparison_data = merged_comparison_data.merge(comparison_result, on="Category", how="left")

    comparison_data = comparison_data[final_cols]

    # TODO: Test removal of this
    # comparison_data = conditional_fillna(comparison_data)

    return year_over_year_data, comparison_data


def calculate_metrics(year_over_year_data: pd.DataFrame, comparison_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Takes a dataframe of school academic data and calculates the proficiency difference
    between successive years and the assigns an academic rating to each year.

    Args:
        data (pd.DataFrame): school proficiency data

    Returns:
        pd.DataFrame: a dataframe with School, Diff, & Rate columns for each year
    """
    
    # Calculate Year over Year Values and Metrics
    
    year_over_year_cols = list(year_over_year_data.columns[1:])

    # thresholds for academic rating
    year_over_year_limits = [0.05, 0.02, 0]

    # see note in calculate_attendance_metrics()
    [
        year_over_year_data.insert(
            i + 1,
            str(year_over_year_data.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
            year_over_year_data.apply(
                lambda x: set_academic_rating(x[year_over_year_data.columns[i]], year_over_year_limits, 1),
                axis=1,
            ),
        )
        for i in range(year_over_year_data.shape[1] - 1, 4, -3)
    ]

    year_over_year_data = conditional_fillna(year_over_year_data)

    year_over_year_data.columns = year_over_year_data.columns.astype(str)

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
    rating_cols = list(col for col in year_over_year_data.columns if "Rate" in col)
    col_pair = list(zip(year_over_year_cols, rating_cols))

    # iterate over list of tuples, if value in first item in pair is zero,
    # change the second value in pair to DNMS
    if col_pair:
        for k, v in col_pair:
            year_over_year_data[v] = np.where(year_over_year_data[k] == 0, "DNMS", year_over_year_data[v])

    # Calculate Comparison Metrics
    
    # delta limits for ilearn
    comparison_limits = [0.1, 0.02, 0]

    [
        comparison_data.insert(
            i + 1,
            str(comparison_data.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
            comparison_data.apply(
                lambda x: set_academic_rating(
                    x[comparison_data.columns[i]], comparison_limits, 1
                ),
                axis=1,
            ),
        )
        for i in range(comparison_data.shape[1] - 1, 2, -3)
    ]

    comparison_data = conditional_fillna(comparison_data)

    return year_over_year_data, comparison_data


def calculate_high_school_metrics(merged_data: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a school dataframe and assigns an academic rating for each category for each year.

    Args:
    merged_data (pd.DataFrame): school proficiency data

    Returns:
        pd.DataFrame: dataframe with School, Tested, Diff, and Rate columns for each year
    """
    data = merged_data.copy()

    grad_limits_state = [0, -0.05, -0.15]
    state_grad_metric = data.loc[data["Category"] == "State Graduation Average"]

    [
        state_grad_metric.insert(
            i + 1,
            str(state_grad_metric.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
            state_grad_metric.apply(
                lambda x: set_academic_rating(
                    x[state_grad_metric.columns[i]], grad_limits_state, 2
                ),
                axis=1,
            ),
        )
        for i in range(state_grad_metric.shape[1] - 1, 1, -3)
    ]

    grad_limits_local = [0, -0.05, -0.10]
    local_grad_metric = data[
        data["Category"].isin(["Total Graduation Rate", "Non Waiver Graduation Rate"])
    ]

    [
        local_grad_metric.insert(
            i + 1,
            str(local_grad_metric.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
            local_grad_metric.apply(
                lambda x: set_academic_rating(
                    x[local_grad_metric.columns[i]], grad_limits_local, 2
                ),
                axis=1,
            ),
        )
        for i in range(local_grad_metric.shape[1] - 1, 1, -3)
    ]

    # NOTE: Strength of Diploma is not currently displayed
    strength_diploma = data[data["Category"] == "Strength of Diploma"]
    strength_diploma = strength_diploma[
        [
            col
            for col in strength_diploma.columns
            if "School" in col or "Category" in col
        ]
    ]
    strength_diploma.loc[
        strength_diploma["Category"] == "Strength of Diploma", "Category"
    ] = "1.7.e The school's strength of diploma indicator."

    # combine dataframes and rename categories
    combined_grad_metrics = pd.concat(
        [state_grad_metric, local_grad_metric], ignore_index=True
    )

    combined_grad_metrics.loc[
        combined_grad_metrics["Category"] == "State Graduation Average",
        "Category",
    ] = "1.7.a 4 year graduation rate compared with the State average"

    combined_grad_metrics.loc[
        combined_grad_metrics["Category"] == "Total Graduation Rate",
        "Category",
    ] = "1.7.b 4 year graduation rate compared with school corporation average"

    combined_grad_metrics.loc[
        combined_grad_metrics["Category"] == "Non Waiver Graduation Rate",
        "Category",
    ] = "1.7.b 4 year non-waiver graduation rate  with school corporation average"

    combined_grad_metrics = conditional_fillna(combined_grad_metrics)

    return combined_grad_metrics


def calculate_adult_high_school_metrics(values: pd.DataFrame) -> pd.DataFrame:
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
    data = values.copy()

    if len(data.index) > 0:
        data.columns = data.columns.astype(str)

        data["CCR Percentage"] = pd.to_numeric(data["AHS|CCR"]) / pd.to_numeric(
            data["AHS|Grad All"]
        )

        ahs_data = data[["Year", "CCR Percentage"]]

        # transpose dataframe and clean headers
        ahs_data = (
            ahs_data.set_index("Year")
            .T.rename_axis("Category")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        # reorder year columns and apply to df headers
        data_columns = list(ahs_data.columns[:0:-1])
        data_columns.sort()
        ahs_data.columns = ["Category"] + data_columns

        ahs_data = ahs_data.set_index(["Category"]).add_suffix("School").reset_index()

        # see calculate_year_over_year() for a description.
        ccr_limits = [0.5, 0.499, 0.234]
        [
            ahs_data.insert(
                i,
                str(ahs_data.columns[i - 1][:4]) + "Rate" + str(i),
                ahs_data.apply(
                    lambda x: set_academic_rating(
                        x[ahs_data.columns[i - 1]], ccr_limits, 2
                    ),
                    axis=1,
                ),
            )
            for i in range(ahs_data.shape[1], 1, -1)
        ]

        # NOTE: State Letter Grades are no longer used. so
        # we create a 1 row dataframe using ahs_data cols,
        # set category to "State Grade", set value to "No Data",
        # and set Rate to "".
        ahs_data_cols = ahs_data.columns.tolist()

        state_grades = pd.DataFrame(columns=ahs_data_cols,index=range(1)) 

        for col in state_grades.columns:
            if "Category" in col:
                state_grades[col] = "State Grade"
            if "School" in col:
                state_grades[col] = "No Data"
            if "Rate" in col:
                state_grades[col] = ""      

        # NOTE: former letter grade code just in case
        # # Letter grades are  stored in demographics table
        # # using Corp (not School) ID. so we need to convert
        # selected_school = get_school_index(school)
        # selected_corp_id = selected_school["Corporation ID"].values[0]

        # school_letter_grades = get_letter_grades(selected_corp_id)
        # school_letter_grades = (
        #     school_letter_grades.set_index("Year")
        #     .T.rename_axis("Category")
        #     .rename_axis(None, axis=1)
        #     .reset_index()
        # )

        # # strip second row (Federal Rating) - for now
        # ahs_state_grades = school_letter_grades.iloc[0:1, :]

        # # sort Year cols in ascending order (ignore Category)
        # ahs_state_grades = (
        #     ahs_state_grades.set_index("Category")
        #     .sort_index(ascending=True, axis=1)
        #     .reset_index()
        # )

        # null_years = ["2023", "2022"]
        # for n in null_years:
        #     if n in ahs_state_grades.columns:
        #         ahs_state_grades[n] = "No Grade"

        # ahs_state_grades = (
        #     ahs_state_grades.set_index(["Category"]).add_suffix("School").reset_index()
        # )

        # # drop any cols (years) that aren't in CCR data
        # ahs_state_grades = ahs_state_grades[
        #     ahs_state_grades.columns.intersection(ahs_data.columns)
        # ]

        # letter_grade_limits = ["A", "B", "C", "D", "F"]
        # [
        #     ahs_state_grades.insert(
        #         i,
        #         str(ahs_state_grades.columns[i - 1][:4]) + "Rate" + str(i),
        #         ahs_state_grades.apply(
        #             lambda x: set_academic_rating(
        #                 x[ahs_state_grades.columns[i - 1]], letter_grade_limits, 4
        #             ),
        #             axis=1,
        #         ),
        #     )
        #     for i in range(ahs_state_grades.shape[1], 1, -1)
        # ]

        # concatenate and add metric column
        ahs_data = pd.concat([state_grades, ahs_data])
        ahs_data = ahs_data.reset_index(drop=True)
        ahs_metric_nums = ["1.1.", "1.3."]
        ahs_data.insert(loc=0, column="Metric", value=ahs_metric_nums)

        ahs_data = ahs_data.fillna("No Data")

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

    # IREAD data has already been run through the comparison_metric() function (in order to calculate
    # the difference from school corporation). However, the IREAD rating is calculated on the School's
    # proficiency and not on the difference, so we need to recalculate the metrics in order to get
    # accurate ratings.
    data = data[data.columns.drop(list(data.filter(regex="Rate")))]

    # another slight variation left as an exercise for the reader
    [
        data.insert(
            i - 1,
            str(data.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
            data.apply(
                lambda x: set_academic_rating(x[data.columns[i - 3]], iread_limits, 1),
                axis=1,
            ),
        )
        for i in range(data.shape[1], 1, -3)
    ]

    data = conditional_fillna(data)
    data.columns = data.columns.astype(str)

    return data


def calculate_financial_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a dataframe of float values and returns the same dataframe with one
    extra 'Rating' column for each year of data. Ratings are calculated based
    on specific thresholds according to ICSB Accountability System (MS, DNMS,
    or N/A (or null)). The calculations use all years of available data (later
    truncated in body of financial_metrics.py to display a maximum of 5 years)
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
    state_grant_idx = data.index[
        data["Category"].str.contains("State Grants")
    ].tolist()[0]
    operating_data = data.loc[:, ~(data.iloc[state_grant_idx] == 0)].copy()

    if len(operating_data.columns) <= 1:
        final_grid = pd.DataFrame()

    else:
        cols = [i for i in operating_data.columns if i not in ["Category"]]

        for col in cols:
            operating_data[col] = pd.to_numeric(operating_data[col], errors="coerce")

        # transpose financial information
        metric_data = (
            operating_data.set_index("Category")
            .T.rename_axis("Year")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        # NOTE: After transposition, row data is in descending order, from earliest year at row_index 0
        # to latest row at row_index -1. All subsequent operations reflect this order.

        # The vectorized way to run calculations between different rows of the
        # same column is to shift a copy of the column either up or down using
        # shift. shift(-1) moves the column up one row. Shift(1) moves the column
        # down one row.  A shift value of 1 should be used in this case (descending).
        # If the columns are in ascending order, use a shift value of -1
        # NOTE: if switch to ascending order, uncomment the next block AND flip the
        # arithmetic operation of any modified (e.g., -1 becomes +1)
        # shift_value = -1  # ascending
        shift_value = 1  # descending

        # create a dataframe for the financial metric table
        metric_grid = pd.DataFrame()

        # Current Ratio calculation
        metric_grid["Current Ratio"] = (
            metric_data["Current Assets"] / metric_data["Current Liabilities"]
        )

        # returns true if 'Current Ratio' is > 1.1 or > 1 and CY > PY
        def ratio_metric_calc(cur, diff):
            return "MS" if ((cur > 1.1) | ((cur > 1) & (diff == True))) else "DNMS"

        metric_grid["Current Ratio Trend"] = metric_grid["Current Ratio"] > metric_grid[
            "Current Ratio"
        ].shift(shift_value)

        metric_grid["Current Ratio Metric"] = metric_grid.apply(
            lambda x: ratio_metric_calc(x["Current Ratio"], x["Current Ratio Trend"]),
            axis=1,
        )

        # Day's Cash calculation
        metric_grid["Days Cash on Hand"] = metric_data["Unrestricted Cash"] / (
            (
                metric_data["Operating Expenses"]
                - metric_data["Depreciation/Amortization"]
            )
            / 365
        )

        # returns true if day's cash is > 45 or >= 30 and CY > PY
        def days_cash_metric_calc(cur, diff):
            return "MS" if ((cur > 45) | ((cur >= 30) & (diff == True))) else "DNMS"

        metric_grid["Days Cash Trend"] = metric_grid["Days Cash on Hand"] > metric_grid[
            "Days Cash on Hand"
        ].shift(shift_value)

        metric_grid["Days Cash Metric"] = metric_grid.apply(
            lambda x: days_cash_metric_calc(
                x["Days Cash on Hand"], x["Days Cash Trend"]
            ),
            axis=1,
        )

        # Annual Enrollment Change calculation
        metric_grid["Annual Enrollment Change"] = (
            metric_data["ADM Average"] - metric_data["ADM Average"].shift(shift_value)
        ) / metric_data["ADM Average"].shift(shift_value)

        metric_grid["Annual Enrollment Change Metric"] = metric_grid[
            "Annual Enrollment Change"
        ].apply(lambda x: "MS" if (x > -0.1) else "DNMS")

        # if the result is NaN (no calculation is possible), the Metric should be N/A
        metric_grid.loc[
            metric_grid["Annual Enrollment Change"].isnull(),
            "Annual Enrollment Change Metric",
        ] = "N/A"

        # Primary Reserve Ratio calculation
        metric_grid["Primary Reserve Ratio"] = (
            metric_data["Unrestricted Net Assets"] / metric_data["Operating Expenses"]
        )
        metric_grid["Primary Reserve Ratio Metric"] = metric_grid[
            "Primary Reserve Ratio"
        ].apply(lambda x: "MS" if (x > 0.25) else "DNMS")

        # Change in Net Assets Margin/Aggregated Three-Year Margin
        metric_grid["Change in Net Assets Margin"] = (
            metric_data["Change in Net Assets"] / metric_data["Operating Revenues"]
        )

        metric_grid["Aggregated Three-Year Margin"] = (
            metric_data["Change in Net Assets"]
            + metric_data["Change in Net Assets"].shift(shift_value)
            + metric_data["Change in Net Assets"].shift(shift_value + 1)
        ) / (
            metric_data["Operating Revenues"]
            + metric_data["Operating Revenues"].shift(shift_value)
            + metric_data["Operating Revenues"].shift(shift_value + 1)
        )

        metric_grid["AgMar Trend"] = (
            metric_grid["Aggregated Three-Year Margin"]
            > metric_grid["Aggregated Three-Year Margin"].shift(shift_value)
        ) & (
            metric_grid["Aggregated Three-Year Margin"].shift(shift_value)
            > metric_grid["Aggregated Three-Year Margin"].shift(shift_value + 1)
        )

        # A school meets standard if: Aggregated Three-Year Margin is positive and the most
        # recent year Change in Net Assets Margin is positive; or Aggregated Three-Year Margin
        # is greater than -1.5%, the trend is positive for the last two years, and Change in Net
        # Assets Margin for the most recent year is positive. For schools in their first and
        # second year of operation, the cumulative Change in Net Assets Margin must be positive.
        def asset_margin_calc(chcur, agcur, diff):
            return (
                "MS"
                if (
                    ((chcur > 0) & (agcur > 0))
                    | (((chcur > 0) & (agcur > -0.015)) & (diff == True))
                )
                else "DNMS"
            )

        metric_grid["Aggregated Three-Year Margin Metric"] = metric_grid.apply(
            lambda x: asset_margin_calc(
                x["Change in Net Assets Margin"],
                x["Aggregated Three-Year Margin"],
                x["AgMar Trend"],
            ),
            axis=1,
        )

        metric_grid["Change in Net Assets Margin Metric"] = metric_grid.apply(
            lambda x: asset_margin_calc(
                x["Change in Net Assets Margin"],
                x["Aggregated Three-Year Margin"],
                x["AgMar Trend"],
            ),
            axis=1,
        )

        # if value is NaN (no calculation is possible), the Metric should be N/A
        metric_grid.loc[
            metric_grid["Aggregated Three-Year Margin"].isnull(),
            "Aggregated Three-Year Margin Metric",
        ] = "N/A"

        # Remember, each row is a year, with earliest years at the top (lower row index). In YR 1 and Y2
        # CHNM Metric is 'MS' if the cumulative value of CHNM is > 0 (positive). We use shift_value -1
        # to account for zero-based indexing to get first year value

        if (
            metric_grid.loc[
                metric_grid.index[shift_value - 1], "Change in Net Assets Margin"
            ]
            > 0
        ):
            metric_grid.loc[
                metric_grid.index[shift_value - 1], "Change in Net Assets Margin Metric"
            ] = "MS"
        else:
            metric_grid.loc[
                metric_grid.index[shift_value - 1], "Change in Net Assets Margin Metric"
            ] = "DNMS"

        # CHNM Metric is 'MS' if first + second year value is > 0
        # Only test if there are at least 2 years of data
        if len(metric_grid.index) >= 2:
            if (
                metric_grid.loc[
                    metric_grid.index[shift_value - 1], "Change in Net Assets Margin"
                ]
                + metric_grid.loc[
                    metric_grid.index[shift_value], "Change in Net Assets Margin"
                ]
            ) > 0:
                metric_grid.loc[
                    metric_grid.index[shift_value], "Change in Net Assets Margin Metric"
                ] = "MS"
            else:
                metric_grid.loc[
                    metric_grid.index[shift_value], "Change in Net Assets Margin Metric"
                ] = "DNMS"

        # Debt to Asset Ratio
        metric_grid["Debt to Asset Ratio"] = (
            metric_data["Total Liabilities"] / metric_data["Total Assets"]
        )
        metric_grid["Debt to Asset Ratio Metric"] = metric_grid[
            "Debt to Asset Ratio"
        ].apply(lambda x: "MS" if (x < 0.9) else "DNMS")

        # Cash Flow and Multi-Year Cash Flow
        metric_grid["Cash Flow"] = metric_data["Unrestricted Cash"] - metric_data[
            "Unrestricted Cash"
        ].shift(shift_value)

        # the YR1 value of 'Cash Flow' is equal to the YR1 value of 'Unrestricted Cash'
        metric_grid.loc[shift_value - 1, "Cash Flow"] = metric_data[
            "Unrestricted Cash"
        ].iloc[shift_value - 1]

        # 'Multi-Year Cash Flow' is equal to CY Cash - 2YR Previous Cash
        metric_grid["Multi-Year Cash Flow"] = metric_data[
            "Unrestricted Cash"
        ] - metric_data["Unrestricted Cash"].shift(shift_value + 1)

        # A school meets standard if both CY Multi-Year Cash Flow and One Year Cash Flow
        # are positive and one out of the two previous One Year Cash Flows are positive
        # For schools in the first two years of operation, both years must have a positive
        # Cash Flow (for purposes of calculating Cash Flow, the school's Year 0 balance is
        # assumed to be zero).

        # NOTE: Once again, remember that the current year is at the highest index (end) of
        # the df - so we loop from back to front - because we need at least 3 years of data
        # for the first test, we stop the loop when i == 1 (the second to last item in the
        # loop)
        for i in range(len(metric_grid["Cash Flow"]) - 1, 1, -1):
            
            # get current year value
            current_year_cash = metric_grid.loc[i, "Cash Flow"]

            previous_year_cash = metric_grid.loc[i - 1, "Cash Flow"] > 0
            second_previous_year_cash = metric_grid.loc[i - 2, "Cash Flow"] > 0

            # school meets standard if current year Cash Flow value and current
            # year Multi-Year Cash Flow value are positive and at least one of
            # the previous two years are positive. converting a boolean to int
            # results in either 0 (false) or 1 (true). when added together, a
            #  value of 1 or 2 means one or both years were positive
            if (
                (metric_grid.loc[i]["Multi-Year Cash Flow"] > 0)
                & (current_year_cash > 0)
                & ((int(previous_year_cash) + int(second_previous_year_cash)) >= 1)
            ):
                metric_grid.loc[i, "Cash Flow Metric"] = "MS"
                metric_grid.loc[i, "Multi-Year Cash Flow Metric"] = "MS"

            else:
                metric_grid.loc[i, "Multi-Year Cash Flow Metric"] = "DNMS"
                metric_grid.loc[i, "Cash Flow Metric"] = "DNMS"

        # A school meets standard if Cash Flow is positive in first year (see above)
        if metric_grid.loc[metric_grid.index[shift_value - 1], "Cash Flow"] > 0:
            metric_grid.loc[
                metric_grid.index[shift_value - 1], "Cash Flow Metric"
            ] = "MS"
        else:
            metric_grid.loc[
                metric_grid.index[shift_value - 1], "Cash Flow Metric"
            ] = "DNMS"

        # A school meets standard if first + second year value is > 0
        # Only test if there are at least 2 years of data
        if len(metric_grid.index) >= 2:
            if (
                metric_grid.loc[metric_grid.index[shift_value - 1], "Cash Flow"] > 0
            ) & (metric_grid.loc[metric_grid.index[shift_value], "Cash Flow"] > 0):
                metric_grid.loc[
                    metric_grid.index[shift_value], "Cash Flow Metric"
                ] = "MS"
            else:
                metric_grid.loc[
                    metric_grid.index[shift_value], "Cash Flow Metric"
                ] = "DNMS"

        # if Multi-Year Cash Flow is NaN (no calculation is possible), Multi-Year Cash Flow Metric should be N/A
        metric_grid.loc[
            metric_grid["Multi-Year Cash Flow"].isnull(), "Multi-Year Cash Flow Metric"
        ] = "N/A"

        # Debt Service Coverage Ratio
        metric_grid["Debt Service Coverage Ratio"] = (
            metric_data["Change in Net Assets"]
            + metric_data["Lease/Mortgage Payments"]
            + metric_data["Depreciation/Amortization"]
            + metric_data["Interest Expense"]
        ) / (
            metric_data["Lease/Mortgage Payments"]
            + metric_data["Principal Payments"]
            + metric_data["Interest Expense"]
        )

        metric_grid["Debt Service Coverage Ratio Metric"] = metric_grid[
            "Debt Service Coverage Ratio"
        ].apply(lambda x: "MS" if (x > 1) else "DNMS")

        # Drop all temporary (calculation) columns
        metric_grid = metric_grid.drop(
            columns=["Days Cash Trend", "Current Ratio Trend", "AgMar Trend"], axis=1
        )

        metric_grid["Year"] = metric_data["Year"]

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
                "Current Ratio",
                "Current Ratio Metric",
                "Days Cash on Hand",
                "Days Cash Metric",
                "Annual Enrollment Change",
                "Annual Enrollment Change Metric",
                "Primary Reserve Ratio",
                "Primary Reserve Ratio Metric",
                "Change in Net Assets Margin",
                "Change in Net Assets Margin Metric",
                "Aggregated Three-Year Margin",
                "Aggregated Three-Year Margin Metric",
                "Debt to Asset Ratio",
                "Debt to Asset Ratio Metric",
                "Cash Flow",
                "Cash Flow Metric",
                "Multi-Year Cash Flow",
                "Multi-Year Cash Flow Metric",
                "Debt Service Coverage Ratio",
                "Debt Service Coverage Ratio Metric",
            ]

            cat = pd.Categorical(column, categories=reorder, ordered=True)

            return pd.Series(cat)

        metric_grid_sorted = metric_grid.sort_values(
            by="Category", key=sort_financial_metrics
        )

        final_grid = pd.DataFrame()

        # Restructure dataframe so that every other row (Metrics) become columns
        # https://stackoverflow.com/questions/36181622/moving-every-other-row-to-a-new-column-and-group-pandas-python
        all_cols = [i for i in metric_grid_sorted if i not in ["Category"]]

        for col in all_cols:
            final_grid[col] = metric_grid_sorted[col].iloc[::2].values
            final_grid[col + "Rating"] = metric_grid_sorted[col].iloc[1::2].values

        # Add the Categories Back without the Metric Rows
        new_cols = pd.DataFrame()
        new_cols["Category"] = metric_grid_sorted["Category"]
        new_cols = new_cols[~new_cols["Category"].str.contains("Metric")]
        new_cols = new_cols.reset_index()

        final_grid.insert(0, "Category", new_cols["Category"])

        # Remove years String from Rating Columns
        final_grid.columns = final_grid.columns.str.replace(
            r"\d{4}Rating", "Rating", regex=True
        )

        # Add new rows for 'Near Term|Long Term' titles
        # NOTE: it baffles me why this is so complicated
        # add row between existing indexes, sort and then reset
        final_grid.loc[3.5, "Category"] = "Long Term"
        final_grid = final_grid.sort_index().reset_index(drop=True)

        # because this is the first row, we use indexing: setting with enlargement
        final_grid.loc[-1, "Category"] = "Near Term"
        final_grid.index = final_grid.index + 1
        final_grid = final_grid.sort_index()
        final_grid = final_grid.rename(columns={"Category": "Metric"})

        # convert all values to numeric
        year_cols = [i for i in final_grid.columns if i not in ["Metric", "Rating"]]

        # Add integer to Rating columns (needed for dash data_table in order to distinguish columns)
        final_grid.columns = [
            f"{x} {i}" if x in "Rating" else f"{x}"
            for i, x in enumerate(final_grid.columns, 1)
        ]

        # force year columns to numeric and round
        for col in year_cols:
            final_grid[col] = pd.to_numeric(final_grid[col], errors="coerce").round(2)

    return final_grid
