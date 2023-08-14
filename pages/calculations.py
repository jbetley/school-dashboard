##########################################
# ICSB Dashboard - Calculation Functions #
##########################################
# author:   jbetley
# version:  1.09
# date:     08/14/23

import pandas as pd
import numpy as np
from typing import Tuple
import scipy.spatial as spatial

from .load_data import current_academic_year

def get_excluded_years(year: str) -> list:
    # "excluded years" is a list of year strings (format YYYY) of all years
    # that are more recent than the selected year. it is used to filter data
    excluded_years = []

    excluded_academic_years = int(current_academic_year) - int(year)

    for i in range(excluded_academic_years):
        excluded_year = int(current_academic_year) - i
        excluded_years.append(excluded_year)

    return excluded_years

def conditional_fillna(data: pd.DataFrame) -> pd.DataFrame:
    """
    conditional fillna based on column name using substrings to identify columns

    Args:
        data (pd.DataFrame): academic data dataframe

    Returns:
        pd.DataFrame: the same dataframe with the nan's filled
    """
    data.columns = data.columns.astype(str)

    fill_with_na = [i for i in data.columns if 'Rate' in i]
    data[fill_with_na] = data[fill_with_na].fillna(value="N/A")

    fill_with_dash = [i for i in data.columns if 'Diff' in i or 'Tested' in i or 'N-Size' in i]
    data[fill_with_dash] = data[fill_with_dash].fillna(value='\u2014') # em dash (—)

    fill_with_no_data = [i for i in data.columns if 'Rate' not in i or 'Diff' not in i or 'Tested' not in i]
    data[fill_with_no_data] = data[fill_with_no_data].fillna(value="No Data")

    return data


def calculate_graduation_rate(data: pd.DataFrame) -> pd.DataFrame:

    cohorts = data[data.columns[data.columns.str.contains(r"Cohort Count")]].columns.tolist()

    for cohort in cohorts:
        if cohort in data.columns:
            cat_sub = cohort.split("|Cohort Count")[0]
            data[cat_sub + " Graduation Rate"] = calculate_percentage(data[cat_sub + "|Graduates"], data[cohort])

    return data

# def calculate_strength_of_diploma(data: pd.DataFrame) -> pd.DataFrame:
#     data["Strength of Diploma"] = pd.to_numeric((data["Non Waiver|Cohort Count"] * 1.08)) \
#          / pd.to_numeric(data["Total|Cohort Count"])

#     return data

def calculate_sat_rate(data: pd.DataFrame) -> pd.DataFrame:

    tested = data[data.columns[data.columns.str.contains(r"Total Tested")]].columns.tolist()

    for test in tested:
        if test in data.columns:
            
            # get Category + Subject string
            cat_sub = test.split(" Total Tested")[0]
            data[cat_sub + " Benchmark %"] = calculate_percentage(data[cat_sub + " At Benchmark"], data[test])

    return data

# TODO: This is slow. Refactor
def calculate_proficiency(data: pd.DataFrame) -> pd.DataFrame:

# Calculates proficiency. If Total Tested == 0 or NaN or if Total Tested > 0, but Total Proficient is
# NaN, all associated columns are dropped

    # Get a list of all "Total Tested" columns except those for ELA & Math
    tested_categories = data[data.columns[data.columns.str.contains(r"Total Tested")]].columns.tolist()
    tested_categories = [i for i in tested_categories if "ELA and Math" not in i]

    for total_tested in tested_categories:
        if total_tested in data.columns:
            
            cat_sub = total_tested.split(" Total Tested")[0]
            total_proficient = cat_sub + " Total Proficient"
            proficiency = cat_sub + " Proficient %"

            # drop the entire category if ("Total Tested" == 0 or NaN) or if 
            # ("Total Tested" > 0 and "Total Proficient" is NaN. A "Total Proficient"
            # value of NaN means it was a "***" before being converted to numeric
            # we use sum/all because there could be one or many columns

            if (pd.to_numeric(data[total_tested], errors="coerce").sum() == 0 or pd.isna(data[total_tested]).all()) | \
                (pd.to_numeric(data[total_tested], errors="coerce").sum() > 0 and pd.isna(data[total_proficient]).all()):

                data = data.drop([total_tested, total_proficient], axis=1)
            else:
                data[proficiency] = calculate_percentage(data[total_proficient], data[total_tested])

    return data


def recalculate_total_proficiency(corp_data: pd.DataFrame, school_data: pd.DataFrame) -> pd.DataFrame:
    """
    In order for an apples to apples comparison between aggregated school corporation academic
    data and the academic data of the selected school, we need to recalculate Total School
    Proficiency for both Math and ELA using only the grade levels for which we have school
    data.

    Args:
        corp_data (pd.DataFrame):   aggregated academic data for the school corporation in which
                                    the school is located
        school_data (pd.DataFrame): school academic data

    Returns:
        pd.DataFrame: the corp_data dataframe after Total Proficiency is recalculated
    """

    school_grades = school_data.loc[school_data['Category'].str.contains(r"Grade.[345678]", regex=True), 'Category'].to_list()
    school_grades = [i.split('|')[0] for i in school_grades]
    school_grades = list(set(school_grades))

    math_prof = [e + '|Math Total Proficient' for e in school_grades]
    math_test = [e + '|Math Total Tested' for e in school_grades]
    ela_prof = [e + '|ELA Total Proficient' for e in school_grades]
    ela_test = [e + '|ELA Total Tested' for e in school_grades]

    adj_corp_math_prof = corp_data[corp_data.columns.intersection(math_prof)]
    adj_corp_math_test = corp_data[corp_data.columns.intersection(math_test)]
    adj_corp_ela_prof = corp_data[corp_data.columns.intersection(ela_prof)]
    adj_corp_ela_tst = corp_data[corp_data.columns.intersection(ela_test)]

    corp_data["School Total|Math Proficient %"] = adj_corp_math_prof.sum(axis=1) / adj_corp_math_test.sum(axis=1)
    corp_data["School Total|ELA Proficient %"] = adj_corp_ela_prof.sum(axis=1) / adj_corp_ela_tst.sum(axis=1)

    return corp_data

def calculate_percentage(numerator: str, denominator: str) -> np.ndarray: #[float|None|str]:
    """Incompatible return value type (got "ndarray[Any, dtype[Any]]
    Calculates a percentage given a numerator and a denominator, while accounting for two
    special case: a string representing insufficent n-size ('***') and certain conditions
    where a '0' value has a different result. The function does the following:
        1) When either the numerator or the denominator is equal to '***', the function returns '****'
        2) When either the numerator or the denominator is null/nan, the function returns 'None'
        3) When the numerator is null/nan, but the denominator is not, the function returns '0'
        4) if none of the above are true, the function divides the numerator by the denominator.
    Args:
        numerator (str): numerator (is a str to account for special cases)
        denominator (str): denominator (is a str to account for special cases)

    Returns:
        float|None|str: see conditions
    """
    return np.where(
        (numerator == "***") | (denominator == "***"),
        "***",
        np.where(
            pd.to_numeric(numerator, errors="coerce").isna() & pd.to_numeric(denominator, errors="coerce").isna(),
            None,
            np.where(
                pd.to_numeric(numerator, errors="coerce").isna(),
                0,
                pd.to_numeric(numerator, errors="coerce") / pd.to_numeric(denominator, errors="coerce"),
            ),
        ),
    )

def calculate_difference(value1: str, value2: str) -> np.ndarray:
    """
    Calculate the difference between two dataframes with specific mixed datatypes
    and conditions.

    Args:
        value1 (str): first value (is a str to account for special cases)
        value2 (str): second value (is a str to account for special cases)

    Returns:
        float|None|str: see conditions
    """

    return np.where(
        (value1 == "***") | (value2 == "***"),
        "***",
        np.where(
            pd.to_numeric(value1, errors="coerce").isna(),
            None,
            pd.to_numeric(value1, errors="coerce") - pd.to_numeric(value2, errors="coerce"),
        ),
    )

def calculate_year_over_year(current_year: pd.Series, previous_year: pd.Series) -> np.ndarray:
    """
    Calculates year_over_year differences, accounting for string representation ('***')
    of insufficent n-size (there is available data, but not enough of it to show under privacy laws).
        1) If both the current_year and previous_year values are '***' -> the result is '***'
        2) If the previous year is either NaN or '***' and the current_year is 0 (that is 0% of students
           were proficient) -> the result is '-***", which is a special flag used for accountability
           purposes (a '-***' is generally treated as a Did Not Meet Standard rather than a No Rating).
    Thus:
        if None in Either Column -> None
        if *** in either column -> ***
        if # -> subtract
        if first value = 0 and second value is *** -> -***
        if first value = 0 and second value is NaN -> -***

    Args:
        current_year (pd.Series): a series of current year values for all categories
        previous_year (pd.Series): a series of previous year values for all categories

    Returns:
        np.ndarray: Either the difference between the current and previous year values, None, 
        or a string ('***')
    """
    return np.where(
        (current_year == 0) & ((previous_year.isna()) | (previous_year == "***")), "-***",
        np.where(
            (current_year == "***") | (previous_year == "***"), "***",
            np.where(
                (pd.to_numeric(current_year, errors="coerce").isna()) & (pd.to_numeric(previous_year, errors="coerce").isna()), None,
                np.where(
                    (~pd.to_numeric(current_year, errors="coerce").isna()) & (pd.to_numeric(previous_year, errors="coerce").isna()), None,              
                    pd.to_numeric(current_year, errors="coerce") - pd.to_numeric(previous_year, errors="coerce"),
                ),
            ),
        ),
    )

def set_academic_rating(data: str|float|None, threshold: list, flag: int) -> str:
    """
    Takes a value (which may be of type str, float, or None), a list (consisting of
    floats defining the thresholds of the ratings), and an integer 'flag,' that tells the
    function which switch to use.

    Args:
        data (str|float|None): a Rating value
        threshold (list): a list of floats
        flag (int): a integer

    Returns:
        str: metric rating
    """

    # NOTE: The order of these operations matters

    # if data is a string
    if data == "***" or data == "No Grade":
        indicator = "NA"
        return indicator

    if data == "-***":
        indicator = "DNMS"
        return indicator

    # if data is NoneType
    if data is None:
        indicator = "NA"
        return indicator

    # letter_grade ratings (type string)
    if flag == 4:
        if data == threshold[0]:
            indicator = "ES"
        elif data == threshold[1]:
            indicator = "MS"
        elif data == threshold[2]:
            indicator = "AS"
        else:
            indicator = "DNMS"
        return indicator

    # numeric checks - ensure type is float
    data = float(data)

    # if data is NaN
    if np.isnan(data):
        indicator = "NA"
        return indicator

    # academic ratings (numeric)
    if flag == 1:
        if data >= threshold[0]:
            indicator = "ES"
        elif data > threshold[1]:
            indicator = "MS"
        elif data >= threshold[2]:
            indicator = "AS"
        elif data <= threshold[3]:
            indicator = "DNMS"

    # graduation rate ratings (numeric)
    if flag == 2:
        if data >= threshold[0]:
            indicator = "ES"
        elif data < threshold[0] and data >= threshold[1]:
            indicator = "MS"
        elif data < threshold[1] and data >= threshold[2]:
            indicator = "AS"
        else:
            indicator = "DNMS"

    # attendance rate ratings (numeric)
    if flag == 3:
        if data > threshold[0]:
            indicator = "ES"
        elif data < threshold[0] and data >= threshold[1]:
            indicator = "MS"
        else:
            indicator = "DNMS"

    return indicator

def round_nearest(data: pd.DataFrame, step: int) -> int:
    """
    Determine a tick value for a plotly chart based on the maximum value in a
    dataframe. The function divides the max valus by an arbitrarily determined 'step' value
    (which can be adjusted to increase/decrease of ticks). It then:
        a. sets a baseline tick amount (50,000 or 500,000) based on the proportionate value
        b. and then calculates a multipler that is the result of proportionate value
            divided by the baseline tick amount
    NOTE: Currently only used in finacial_analysis.py

    Args:
        data (pd.DataFrame): pandas dataframe
        step (int): the 'number' of ticks we ultimately want
    
    Returns:
        int: an integer representing the value of each tick
    """
    max_val = data.melt().value.max()
    
    x = max_val / step
    if x > 1000000:
        num=500000
    else:
        num=50000

    rnd = round(float(x)/num)
    multiplier = 1 if rnd < 1 else rnd
    tick = int(multiplier*num)

    return tick

def round_percentages(percentages: list) -> list:
    """
    https://github.com/simondo92/round-percentages
    Given an iterable of float percentages that add up to 100 (or decimals that add up
    to 1), round them to the nearest integer such that the integers
    also add up to 100. Uses the largest remainder method.

    E.g. round_percentages([13.626332, 47.989636, 9.596008, 28.788024])
    -> [14, 48, 9, 29]

    Args:
        percentages (list): a list of floats

    Returns:
        list: a list of integers, rounded to whole numbers, adding up to 100
    """
    # if numbers are in decimal format (e.g. .57, .90) then the sum
    # of the numbers should bet at or near (1). To be safe we test
    # to see if sum is less than 2. If it is, we multiply all of
    # the numbers in the list by 100 (e.g., 57, 90)
    if sum(percentages) < 2:
        percentages = [x * 100 for x in percentages]

    result = []
    sum_of_integer_parts = 0

    for index, percentage in enumerate(percentages):
        whole, fractional = str(float(percentage)).split(".")
        integer = int(whole)
        decimal = int(fractional)

        result.append([integer, decimal, index])
        sum_of_integer_parts += integer

    result.sort(key=lambda x: x[1], reverse=True)
    difference = 100 - sum_of_integer_parts

    for percentage in result:
        if difference == 0:
            break
        percentage[0] += 1
        difference -= 1

    # order by the original order
    result.sort(key=lambda x: x[2])

    # return just the percentage
    return [percentage[0] for percentage in result]

def check_for_no_data(data: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """
    Takes a dataframe, finds the Years where all values are '***', nan, or none
    and turns the results into a single string listing the year(s) meeting the condition

    Args:
        data (pd.DataFrame): dataframe of academic proficiency values

    Returns:
        data (pd.DataFrame) & string (str): a dataframe where the years of missing data (rows) have been dropped
        and a string of all years of missing data
        
    """

    # Identify and drop rows with no or insufficient data ('***' or NaN/None)
    tmp = data.copy()
    tmp = tmp.drop('School Name', axis=1)
    tmp = tmp.set_index('Year')

    # the nunique test will always be true for a single column (e.g., IREAD). so we
    # need to test one column dataframes separately
    if len(tmp.columns) == 1:

        # the safest way is to coerce all strings to numeric and then test for null
        tmp[tmp.columns[0]] = pd.to_numeric(tmp[tmp.columns[0]], errors='coerce')
        no_data_years = tmp.index[tmp[tmp.columns[0]].isnull()].values.tolist()
    
    else:
        no_data_years = tmp[tmp.apply(pd.Series.nunique, axis=1) == 1].index.values.tolist()

    if no_data_years:
        data = data[~data['Year'].isin(no_data_years)]
        
        if len(no_data_years) > 1:
            string = ', '.join(no_data_years) + '.'
        else:
            string = no_data_years[0] + '.'
    else:
        string =''                    

    return data, string

def check_for_insufficient_n_size(data: pd.DataFrame) -> str:
    """
    Takes a dataframe, finds the Categories and Years where the value is equal
    to '***'(insufficient n-size), and turns the results into a single string,
    grouped by year, where duplicates have one or more years in parenthesis.
    E.g., 'White (2021, 2022); Hispanic, Multiracial (2019)'
    NOTE: This turned out to be more complicated that I thought. The below solution
    seems overly convoluted, but works. Felt cute, may refactor later.

    Args:
        data(pd.DataFrame): dataframe of academic proficiency values

    Returns:
        string (str): A single string listing all years (rows) for which there is insufficient data
    """

    #  returns the indices of elements in a tuple of arrays where the condition is satisfied
    insufficient_n_size = np.where(data == '***')

    # creates a new dataframe from the respective indicies
    df = pd.DataFrame(np.column_stack(insufficient_n_size),columns=['Year','Category'])

    if len(df.index) > 0:
        # use map, in conjunction with mask, to replace the index values in the dataframes with the Year
        # and Category values
        df['Category'] = df['Category'].mask(df['Category'] >= 0, df['Category'].map(dict(enumerate(data.columns.tolist()))))
        df['Year'] = df['Year'].mask(df['Year'] >= 0, df['Year'].map(dict(enumerate(data['Year'].tolist()))))
        
        # strip everything after '|'
        df["Category"] = (df["Category"].str.replace('\|.*$', '', regex=True))

        # sort so earliest year is first
        df = df.sort_values(by=['Year'], ascending=True)

        # Shift the Year column one unit down then compare the shifted column with the
        # non-shifted one to create a boolean mask which can be used to identify the
        # boundaries between adjacent duplicate rows. then take the cumulative sum on
        # the boolean mask to identify the blocks of rows where the value stays the same
        c = df['Category'].ne(df['Category'].shift()).cumsum()

        # group the dataframe on the above identfied blocks and aggregate the Year column
        # using first and Message using .join
        df = df.groupby(c, as_index=False).agg({'Category': 'first', 'Year': ', '.join})    

        # then do the same thing for year
        y = df['Year'].ne(df['Year'].shift()).cumsum()
        df = df.groupby(y, as_index=False).agg({'Year': 'first', 'Category': ', '.join})   
        
        # reverse order of columns
        df = df[df.columns[::-1]]
        
        # add parentheses around year values
        df['Year'] = '(' + df['Year'].astype(str) + ')'

        # Finally combine all rows into a single string.
        int_string = [', '.join(val) for val in df.astype(str).values.tolist()]
        df_string = '; '.join(int_string) + '.'

        # clean up extra comma
        df_string = df_string.replace(", (", " (" )

    else:
        df_string = ''

    return df_string

def find_nearest(school_idx: pd.Index, data: pd.DataFrame) -> Tuple[np.ndarray,np.ndarray]:
    """
    Based on https://stackoverflow.com/q/43020919/190597
    https://stackoverflow.com/questions/45127141/find-the-nearest-point-in-distance-for-all-the-points-in-the-dataset-python
    https://stackoverflow.com/questions/43020919/scipy-how-to-convert-kd-tree-distance-from-query-to-kilometers-python-pandas
    https://kanoki.org/2020/08/05/find-nearest-neighbor-using-kd-tree/

    Used to find the [20] nearest schools to the selected school.
 
    Takes a dataframe of schools and their Lat and Lon coordinates and the index of the
    selected school within that list. Calculates the distances of all schools in the
    dataframe from the lat/lon coordinates of the selected school using the scipy.spatial
    KDTree method, which is reasonably quick.

    Args:
        school_idx (pd.Index): the dataFrame index of the selected school
        data (pd.DataFrame): a dataframe of schools and their lat/lon coordinates

    Returns:
        index (np.ndarray) & distance (np.ndarray): an array of dataframe indexes
        and an array of distances (in miles)
    """

    # number of schools to return (add 1 to account for the fact that the selected school
    # is included in the return set) - number needs to be high enough to ensure there are
    # enough left once non-comparable grades are filtered out.
    num_hits = 26

    # the radius of earth in miles. For kilometers use 6372.8 km
    R = 3959.87433 

    # as the selected school already exists in the 'data' df,
    # just pass in index and use that to find it
    for col in data.columns:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    
    phi = np.deg2rad(data['Lat'])
    theta = np.deg2rad(data['Lon'])
    data['x'] = R * np.cos(phi) * np.cos(theta)
    data['y'] = R * np.cos(phi) * np.sin(theta)
    data['z'] = R * np.sin(phi)

    tree = spatial.KDTree(data[['x', 'y','z']])

    # gets a list of the indexes and distances in the data tree that
    # match the [num_hits] number of 'nearest neighbor' schools
    distance, index = tree.query(data.iloc[school_idx][['x', 'y','z']], k = num_hits)

    return index, distance