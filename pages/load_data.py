##############################################
# ICSB Dashboard - Database Queries (SQLite) #
##############################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     02/21/24

# Current data:
# ILEARN - 2023
# IREAD - 2023
# SAT - 2023
# ADM - 2023
# Demographics - 2024
# Financial - 2022 (Audited) / 2023 (Q4)
# Graduation Rate - 2022
import pandas as pd
import numpy as np
import re
from sqlalchemy import create_engine, text

from .calculations import calculate_percentage, conditional_fillna, calculate_difference

# NOTE: No K8 academic data exists for 2020

# global variables - yes, global variable bad.
max_display_years = 5

subject = ["Math", "ELA"]

info_categories = ["School Name", "Low Grade", "High Grade"]

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

grades = ["Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"]

grades_all = ["Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Total"]

grades_ordinal = ["3rd", "4th", "5th", "6th", "7th", "8th"]

# K8 Not yet included: 1.3.a, 1.3.b (Mission Specific)
# K8 Deprecated: 1.2.a, 1.2.b, 1.5.a, 1.5.b
# HS Depracted:  1.7.d, 1.7.e
# AHS Deprecated: 1.2.a, 1.2b
# AHS Not Calculated (K8 standards 1.4a & 1.4b)

metric_strings = {
    # AHS
    "1.1": [
        "The school received an A on under the State's Adult Accountability system.",
        "The school received an B on under the State's Adult Accountability system.",
        "The school received an C on under the State's Adult Accountability system.",
        "The school received an D on under the State's Adult Accountability system.",
    ],
    # AHS
    "1.3": [
        "Fifty percent (50%) or more of graduates achieved at least one CCR indicator.",
        "Between (36.8-49.9%) of graduates achieved at least one CCR indicator.",
        "Between (23.4-36.7%) of graduates achieved at least one CCR indicator.",
        "Less than (23.4%) of of graduates achieved at least one CCR indicator.",
    ],
    # same ratings as 1.1.b
    "1.1.a": [
        "Above the school corporation average.",
        "At or within one percent (1%) of the school corporation average.",
        "",
        "More than one percent (1%) below the school corporation average.",
    ],
    # combined 1.1.c and 1.1.d
    "1.1.c": [
        "More than ninety percent (90%) of the students eligible to return to the school re-enrolled the next year (85% re-enrolled year over year).",
        "Between eighty and ninety percent (80-90%) of the students eligible to return to the school re-enrolled the next year (75-85% re-enrolled year over year).",
        "Between seventy and eighty percent (70-80%) of the students eligible to return to the school re-enrolled the next year (70-75% re-enrolled year over year).",
        "Less than seventy percent (70%) of the students eligible to return to the school re-enrolled the next year (70% re-enrolled year over year).",
    ],
    "1.1.d": [
        "More than eighty-five percent (85%) of the students eligible to return to the school re-enrolled over time.",
        "Between seventy-five and eighty-five percent (75-85%) of the students eligible to return to the school re-enrolled over time.",
        "Between seventy and seventy-five percent (70-75%) of the students eligible to return to the school re-enrolled over time.",
        "Less than seventy percent (70%) of the students eligible to return to the school re-enrolled over time.",
    ],
    "1.4.a": [
        "Increase of more than five percent (5%) from the previous year.",
        "Increase of between two and five percent (2-5%) from the previous year.",
        "Less than a two percent (2%) increase from the previous year.",
        "Decrease from the previous school year.",
    ],
    "1.4.b": [
        "Increase of more than five percent (5%) from the previous year.",
        "Increase of between two and five percent (2-5%) from the previous year.",
        "Less than a two percent (2%) increase from the previous year.",
        "Decrease from the previous school year.",
    ],
    "1.4.c": [
        "Ten percent (10%) or higher than comparable public schools.",
        "Between two and ten percent (2-10%) higher than comparable schools.",
        "Between the same as and two percent (2%) higher than comparable schools.",
        "Less than comparable schools.",
    ],
    "1.4.d": [
        "Ten percent (10%) or higher than comparable public schools.",
        "Between two and ten percent (2-10%) higher than comparable schools.",
        "Between the same as and two percent (2%) higher than comparable schools.",
        "Less than comparable schools.",
    ],
    # same ratings as 1.4.f
    "1.4.e": [
        "More than eighty percent (80%).",
        "Between seventy and eighty percent (70-80%).",
        "Between sixty and seventy percent (60-70%).",
        "Less than sixty percent (60%).",
    ],
    "1.4.g": [
        "More than ninety percent (90%).",
        "Between eighty and ninety percent (80-90%).",
        "Between seventy and eighty percent (70-80%).",
        "Less than seventy percent (70%).",
    ],
    "1.5.c": [
        "The median SGP for all students is more than sixty (60).",
        "The median SGP for all students is between fifty (50) and sixty (60).",
        "The median SGP for all students is between thirty (30) and fifty (50).",
        "The median SGP for all students is less than thirty (30).",
    ],
    "1.5.d": [
        "The median SGP for all students is more than sixty (60).",
        "The median SGP for all students is between fifty (50) and sixty (60).",
        "The median SGP for all students is between thirty (30) and fifty (50).",
        "The median SGP for all students is less than thirty (30).",
    ],
    "1.6.a": [
        "Ten percent (10%) or higher than comparable public schools for the subgroup.",
        "Between two and ten percent (2-10%) higher than comparable schools for the subgroup.",
        "Between the same as and two percent (2%) higher than comparable schools for the subgroup.",
        "Less than comparable schools for the subgroup.",
    ],
    "1.6.b": [
        "Ten percent (10%) or higher than comparable public schools for the subgroup.",
        "Between two and ten percent (2-10%) higher than comparable schools for the subgroup.",
        "Between the same as and two percent (2%) higher than comparable schools for the subgroup.",
        "Less than comparable schools for the subgroup.",
    ],
    "1.6.c": [
        "Increase of more than five percent (5%) from the previous year for the subgroup.",
        "Increase of between two and five percent (2-5%) from the previous year.",
        "Less than a two percent (2%) increase from the previous year for the subgroup.",
        "Decrease from the previous school year for the subgroup.",
    ],
    "1.6.d": [
        "Increase of more than five percent (5%) from the previous year for the subgroup.",
        "Increase of between two and five percent (2-5%) from the previous year.",
        "Less than a two percent (2%) increase from the previous year for the subgroup.",
        "Decrease from the previous school year for the subgroup.",
    ],
    # combined 1.7.a and 1.7.b
    "1.7.a": [
        "Equal to or greater than the state average (than traditional public school(s)).",
        "Within five percent (5%) of the state average (of traditional public school(s)).",
        "Between six and fifteen percent (6-15%) below the state average (6-10% below traditional public school(s)).",
        "More than fifteen percent (15%) below the state average (10% below traditional public school(s)).",
    ],
    "1.7.b": [
        "Equal to or greater than traditional public school(s).",
        "Within five percent (5%) of traditional public school(s).",
        "Between six and ten percent (6-10%) below traditional public school(s).",
        "More than ten percent (10%) below traditional public school(s).",
    ],
    # same ratings as 1.7.d
    "1.7.c": [
        "Ninety-five percent (95%) or more.",
        "Between eighty-five and ninety-five percent (85-95%).",
        "Between seventy-five and eighty-five percent (75-85%).",
        "Less than seventy-five percent (75%).",
    ],
}

# NOTE: Consider moving engine instantiation to app.py
engine = create_engine("sqlite:///data/indiana_schools.db")

users = create_engine("sqlite:///users.db")

print("Database Engine Created . . .")


def run_query(q, *args):
    """
    Takes sql text query, gets query as a dataframe (read_sql is a convenience function
    wrapper around read_sql_query), and perform a variety of basic clean up functions
    If no data matches the query, an empty df is returned

    Args:
        q (string): a sqlalchemy "text" query 
        args (dict): a dict of query parameters
    Returns:
        pd.DataFrame: pandas dataframe of the query results
    """
    conditions = None

    with engine.connect() as conn:
        if args:
            conditions = args[0]

        df = pd.read_sql_query(q, conn, params=conditions)

        # sqlite column headers do not have spaces between words. But we need to display the column names,
        # so we have to do a bunch of str.replace to account for all conditions. May be a better way, but
        # this is pretty fast. Adding a space between any lowercase character and any uppercase/number
        # character takes care of most of it. The other replace functions catch edge cases.
        df.columns = df.columns.str.replace(r"([a-z])([A-Z1-9%])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace(
            r"([WADTO])([CATPB&])", r"\1 \2", regex=True
        )
        df.columns = df.columns.str.replace("EBRWand", "EBRW and") # better way to do this?    
        df.columns = df.columns.str.replace(r"([A])([a])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace(r"([1-9])([(])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace("or ", " or ")
        df.columns = df.columns.astype(str)

        return df

def get_current_year():
    """
    the most recent academic year of data according to the k8 ilearn
    data file

    Returns:
        int: an int representing the most recent year
    """    
    db = engine.raw_connection()
    cur = db.cursor()
    cur.execute(""" SELECT MAX(Year) FROM academic_data_k8 """)
    year = cur.fetchone()[0]
    db.close()

    return year

current_academic_year = get_current_year()

# Used to 
def get_network_count():
    """
    Helper function to dynamically count the number of network logins present
    in the users database (identified with a negative group_id values). used to
    determine the offset for creation of the charter dropdown in app.py. 

    Returns:
        int: the number of network logins
    """    
    db = users.raw_connection()
    cur = db.cursor()
    cur.execute(""" SELECT COUNT(groupid) FROM users WHERE groupid < 0 """)
    count = cur.fetchone()[0]
    count = count + 1
    db.close()

    return count

network_count = get_network_count()


def get_excluded_years(year: str) -> list:
    """
    "excluded years" is a list of year strings (format YYYY) of all years
    that are more recent than the selected year. it is used to filter data

    Args:
        year (str): a year string in format YYYY

    Returns:
        list: a list of year strings - all years more recent than selected year
    """

    excluded_years = []

    excluded_academic_years = int(current_academic_year) - int(year)

    for i in range(excluded_academic_years):
        excluded_year = int(current_academic_year) - i
        excluded_years.append(excluded_year)

    return excluded_years


def get_school_index(school_id):
    """
    returns school index information

    Args:
        school_id (string): a 4 digit number in string format

    Returns:
        pd.DataFrame: df of basic school information
    """    
    params = dict(id=school_id)

    q = text(
        """
        SELECT *
            FROM school_index
            WHERE school_index.SchoolID = :id
        """
    )

    return run_query(q, params)


def get_academic_dropdown_years(*args):
    """
    gets a list of all available years of academic proficiency data

    Args:
        school_id (string): a 4 digit number in string format
        school_type(string): K8, HS, AHS, or K12
    Returns:
        list: a list of integers representing years
    """     
    keys = ["id", "type"]
    params = dict(zip(keys, args))

    if params["type"] == "K8" or params["type"] == "K12":
        q = text(
            """ 
            SELECT DISTINCT	Year
            FROM academic_data_k8
            WHERE SchoolID = :id
        """
        )
    else:
        q = text(
            """
            SELECT DISTINCT	Year
            FROM academic_data_hs
            WHERE SchoolID = :id
        """
        )

    result = run_query(q, params)

    years = result["Year"].tolist()
    years.sort(reverse=True)

    return years


def get_academic_growth_dropdown_years(*args):
    """
    gets a list of all available years of academic growth data

    Args:
        school_id (string): a 4 digit number in string format

    Returns:
        list: a list of integers representing years
    """      
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT DISTINCT	TestYear
	        FROM growth_data
	        WHERE MajorityEnrolledSchoolID = :id
        """
    )

    result = run_query(q, params)

    years = result["Test Year"].tolist()
    years.sort(reverse=True)

    return years


def get_financial_dropdown_years(school_id, page):
    """
    gets a list of all available years of financial data - returns
    # a list of Year column names for each year for which ADM Average
    # for that year is greater than '0'

    Args:
        school_id (string): a 4 digit number in string format
        page(string): a string identifying the url for which the call
        is being made
    Returns:
        list: a list of integers representing years
    """       
    params = dict(id=school_id)
    q = text(
        """
        SELECT * 
        FROM financial_data 
        WHERE SchoolID = :id
    """
    )

    results = run_query(q, params)

    if len(results.columns) > 3:
        adm_index = results.index[results["Category"] == "ADM Average"].values[0]

        # for the financial analysis page, we skip years with
        # quarterly data (Q#) entirely (the "$" skips years with
        # a suffix).
        if page == "financial_analysis":
            results = results.filter(regex="^\d{4}$")
        else:
            # for all other pages, we want to display the quarterly
            # data, so we keep the year and just trim the Q# suffix
            # below
            results = results.filter(regex="^\d{4}")

        for col in results.columns:
            results[col] = pd.to_numeric(results[col], errors="coerce")

        mask = results.iloc[adm_index] > 0

        results = results.loc[:, mask]

        if page == "financial_analysis":
            years = [int(x) for x in results.columns.to_list()]
        else:
            years = [int(x[:4]) for x in results.columns.to_list()]
    else:
        years = []

    return years


def get_adm(corp_id):
    # Use this when there is no financial data - financial data will almost
    # always be more accurate, but some schools (Guests) don't have financial
    # data.

    params = dict(id=corp_id)

    q = text(
        """
        SELECT * 
        FROM adm_all 
        WHERE CorporationID = :id
    """
    )

    results = run_query(q, params)

    # NOTE: From 2016 - 2019  'SpringADM' & 'FallADM'; beginning with
    # 2019-20SY: "2019Fall Non Virtual ADM" & "2020Spring Non Virtual ADM"

    # drop "Virtual ADM"
    results = results.drop(
        list(
            results.filter(
                regex="Fall Virtual ADM|Spring Virtual ADM|Corporation ID|Name"
            )
        ),
        axis=1,
    )

    # Each adm average requires 2 columns (Fall and Spring). If there are an odd number of columns
    # after the above drop, that means that the last column is a Fall without a Spring, so
    # we store that column, drop it, and add it back later
    if (len(results.columns) % 2) != 0:
        last_col = pd.DataFrame()
        last_col_name = str(int(results.columns[-1][:4]) + 1)
        last_col[last_col_name] = results[results.columns[-1]]
        results = results.drop(results.columns[-1], axis=1)

    adm_columns = [c[:4] for c in results.columns if "Spring" in c]

    # make numbers
    for col in results:
        results[col] = pd.to_numeric(results[col], errors="coerce")

    # Average each group of 2 columns and use name of 2nd column (Spring) for result
    final = results.groupby(np.arange(len(results.columns)) // 2, axis=1).mean()
    final.columns = adm_columns

    if not last_col.empty:
        final[last_col_name] = last_col[last_col_name]

    return final


def get_school_dropdown_list():
    q = text(
        """
        SELECT SchoolName, SchoolID, SchoolType, GroupID
        FROM school_index """
    )

    with engine.connect() as conn:
        schools = pd.read_sql_query(q, conn)

    schools = schools.astype(str)

    return schools


def get_graduation_data():
    params = dict(id="")

    q = text(
        """
        SELECT
            Year,
            SUM("Total|Graduates") / SUM("Total|CohortCount") AS "State Graduation Average"
        FROM academic_data_hs
        WHERE SchoolType != "AHS"
        GROUP BY
            Year
        """
    )
    
    results = run_query(q, params)
    
    results = results.loc[::-1].reset_index(drop=True)

    # merge state_grad_average with corp_data
    results = (
        results.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    # rename columns and add state_grad average to corp df
    results = results.rename(
        columns={
            c: str(c) + "Corp"
            for c in results.columns
            if c not in ["Category"]
        }
    )

    return results


def get_gradespan(school_id, selected_year, all_years):
    # returns a list of grades for for which a school has numbers for both Tested
    # and Proficient students for the selected year (and all earlier years)
    # if no grades are found - returns an empty list
    params = dict(id=school_id)

    idx = all_years.index(int(selected_year))
    available_years = all_years[idx:]

    year_str = ", ".join([str(int(v)) for v in available_years])

    q = text(
        """
        SELECT "Grade3|ELATotalTested", "Grade4|ELATotalTested", "Grade5|ELATotalTested", "Grade6|ELATotalTested", "Grade7|ELATotalTested","Grade8|ELATotalTested",
            "Grade3|ELATotalProficient", "Grade4|ELATotalProficient", "Grade5|ELATotalProficient", "Grade6|ELATotalProficient", "Grade7|ELATotalProficient","Grade8|ELATotalProficient"
            FROM academic_data_k8
            WHERE SchoolID = :id AND Year IN ({})""".format(
            year_str
        )
    )

    result = run_query(q, params)

    # change '***' to nan
    for col in result.columns:
        result[col] = pd.to_numeric(result[col], errors="coerce")

    # change 0 to nan
    result.replace(0, np.nan, inplace=True)

    # drop those nas
    result = result.dropna(axis=1, how="all")

    # get a list of remaining grades (will be duplicates where both Tested and Proficient are
    # not nan or 0)
    regex = re.compile(r"\b\d\b")
    test_cols = [regex.search(i).group() for i in result.columns.tolist()]

    # remove unique items (where Tested and Proficient are not both numbers)
    dupe_cols = [i for i in test_cols if test_cols.count(i) > 1]

    # keep one of each item
    result = list(set(dupe_cols))

    result.sort()

    return result


def get_ethnicity(school_id, school_type, hs_category, subject_value, selected_year, all_years):
    # returns a list of ethnicities for which a school has numbers for both Tested
    # and Proficient students for the selected year (and all earlier years)

    params = dict(id=school_id)

    idx = all_years.index(int(selected_year))
    available_years = all_years[idx:]

    year_str = ", ".join([str(int(v)) for v in available_years])

    if school_type == "hs":
        if hs_category == "SAT":
            q = text(
                """
                SELECT "AmericanIndian|EBRWTotalTested", "Asian|EBRWTotalTested", "Black|EBRWTotalTested", "Hispanic|EBRWTotalTested", "Multiracial|EBRWTotalTested","NativeHawaiianorOtherPacificIslander|EBRWTotalTested", "White|EBRWTotalTested",
                    "AmericanIndian|EBRWAtBenchmark", "Asian|EBRWAtBenchmark", "Black|EBRWAtBenchmark", "Hispanic|EBRWAtBenchmark", "Multiracial|EBRWAtBenchmark","NativeHawaiianorOtherPacificIslander|EBRWAtBenchmark", "White|EBRWAtBenchmark"
                    FROM academic_data_hs
                    WHERE SchoolID = :id AND Year IN ({})""".format(
                    year_str
                )
            )

        else:
            q = text(
                """
                SELECT "AmericanIndian|CohortCount", "Asian|CohortCount", "Black|CohortCount", "Hispanic|CohortCount", "Multiracial|CohortCount","NativeHawaiianorOtherPacificIslander|CohortCount", "White|CohortCount",
                    "AmericanIndian|Graduates", "Asian|Graduates", "Black|Graduates", "Hispanic|Graduates", "Multiracial|Graduates","NativeHawaiianorOtherPacificIslander|Graduates", "White|Graduates"
                    FROM academic_data_hs
                    WHERE SchoolID = :id AND Year IN ({})""".format(
                    year_str
                )
            )

    else:
        # k8
        if subject_value == "IREAD":
            q = text(
                """
                SELECT "AmericanIndian|IREADTestN", "Asian|IREADTestN", "Black|IREADTestN", "Hispanic|IREADTestN", "Multiracial|IREADTestN","NativeHawaiianorOtherPacificIslander|IREADTestN", "White|IREADTestN",
                    "AmericanIndian|IREADPassN", "Asian|IREADPassN", "Black|IREADPassN", "Hispanic|IREADPassN", "Multiracial|IREADPassN","NativeHawaiianorOtherPacificIslander|IREADPassN", "White|IREADPassN"
                    FROM academic_data_k8
                    WHERE SchoolID = :id AND Year IN ({})""".format(
                    year_str
                )
            )
        else:

            q = text(
                """
                SELECT "AmericanIndian|ELATotalTested", "Asian|ELATotalTested", "Black|ELATotalTested", "Hispanic|ELATotalTested", "Multiracial|ELATotalTested","NativeHawaiianorOtherPacificIslander|ELATotalTested", "White|ELATotalTested",
                    "AmericanIndian|ELATotalProficient", "Asian|ELATotalProficient", "Black|ELATotalProficient", "Hispanic|ELATotalProficient", "Multiracial|ELATotalProficient","NativeHawaiianorOtherPacificIslander|ELATotalProficient", "White|ELATotalProficient"
                    FROM academic_data_k8
                    WHERE SchoolID = :id AND Year IN ({})""".format(
                    year_str
                )
            )

    result = run_query(q, params)

    for col in result.columns:
        result[col] = pd.to_numeric(result[col], errors="coerce")

    result.replace(0, np.nan, inplace=True)

    result = result.dropna(axis=1, how="all")

    test_cols = [item.split("|")[0] for item in result.columns.values]

    dupe_cols = [i for i in test_cols if test_cols.count(i) > 1]

    result = list(set(dupe_cols))

    return result


def get_subgroup(school_id, school_type, hs_category, subject_value, selected_year, all_years):
    # returns a list of subgroups for which a school has numbers for both Tested
    # and Proficient students for the selected year (and all earlier years)

    params = dict(id=school_id)

    idx = all_years.index(int(selected_year))
    available_years = all_years[idx:]

    year_str = ", ".join([str(int(v)) for v in available_years])

    if school_type == "hs":
        if hs_category == "SAT":
            q = text(
                """
                SELECT "PaidMeals|EBRWTotalTested", "FreeorReducedPriceMeals|EBRWTotalTested", "GeneralEducation|EBRWTotalTested", "SpecialEducation|EBRWTotalTested", "EnglishLanguageLearners|EBRWTotalTested","NonEnglishLanguageLearners|EBRWTotalTested",
                "PaidMeals|EBRWAtBenchmark", "FreeorReducedPriceMeals|EBRWAtBenchmark", "GeneralEducation|EBRWAtBenchmark", "SpecialEducation|EBRWAtBenchmark", "EnglishLanguageLearners|EBRWAtBenchmark","NonEnglishLanguageLearners|EBRWAtBenchmark"
                FROM academic_data_hs
                WHERE SchoolID = :id AND Year IN ({})""".format(
                    year_str
                )
            )

        else:
            q = text(
                """
                SELECT "PaidMeals|CohortCount", "FreeorReducedPriceMeals|CohortCount", "GeneralEducation|CohortCount", "SpecialEducation|CohortCount", "EnglishLanguageLearners|CohortCount","NonEnglishLanguageLearners|CohortCount",
                "PaidMeals|Graduates", "FreeorReducedPriceMeals|Graduates", "GeneralEducation|Graduates", "SpecialEducation|Graduates", "EnglishLanguageLearners|Graduates","NonEnglishLanguageLearners|Graduates"
                FROM academic_data_hs
                WHERE SchoolID = :id AND Year IN ({})""".format(
                    year_str
                )
            )

    else:
        # k8
        if subject_value == "IREAD":

            q = text(
                """
                SELECT "PaidMeals|IREADTestN", "FreeorReducedPriceMeals|IREADTestN", "GeneralEducation|IREADTestN", "SpecialEducation|IREADTestN", "EnglishLanguageLearners|IREADTestN","NonEnglishLanguageLearners|IREADTestN",
                    "PaidMeals|IREADPassN", "FreeorReducedPriceMeals|IREADPassN", "GeneralEducation|IREADPassN", "SpecialEducation|IREADPassN", "EnglishLanguageLearners|IREADPassN","NonEnglishLanguageLearners|IREADPassN"
                    FROM academic_data_k8
                    WHERE SchoolID = :id AND Year IN ({})""".format(
                    year_str
                )
            )

        else:

            q = text(
                """
                SELECT "PaidMeals|ELATotalTested", "FreeorReducedPriceMeals|ELATotalTested", "GeneralEducation|ELATotalTested", "SpecialEducation|ELATotalTested", "EnglishLanguageLearners|ELATotalTested","NonEnglishLanguageLearners|ELATotalTested",
                    "PaidMeals|ELATotalProficient", "FreeorReducedPriceMeals|ELATotalProficient", "GeneralEducation|ELATotalProficient", "SpecialEducation|ELATotalProficient", "EnglishLanguageLearners|ELATotalProficient","NonEnglishLanguageLearners|ELATotalProficient"
                    FROM academic_data_k8
                    WHERE SchoolID = :id AND Year IN ({})""".format(
                    year_str
                )
            )

    result = run_query(q, params)

    for col in result.columns:
        result[col] = pd.to_numeric(result[col], errors="coerce")

    result.replace(0, np.nan, inplace=True)

    result = result.dropna(axis=1, how="all")

    test_cols = [item.split("|")[0] for item in result.columns.values]

    dupe_cols = [i for i in test_cols if test_cols.count(i) > 1]

    result = list(set(dupe_cols))

    return result


def get_financial_data(school_id):
    params = dict(id=school_id)
    q = text(
        """
        SELECT * 
        FROM financial_data 
        WHERE SchoolID = :id
    """
    )
    return run_query(q, params)


def get_financial_ratios(corp_id):
    params = dict(id=corp_id)
    q = text(
        """
        SELECT * 
        FROM financial_ratios 
        WHERE CorporationID = :id
    """
    )
    return run_query(q, params)


def get_corp_demographic_data(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT *
            FROM demographic_data_corp
	        WHERE CorporationID = :id
        """
    )

    return run_query(q, params)


def get_school_demographic_data(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT *
            FROM demographic_data_school
	        WHERE SchoolID = :id
        """
    )

    return run_query(q, params)


def get_letter_grades(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT demographic_data.Year, demographic_data.StateGrade, demographic_data.FederalRating
            FROM demographic_data
	        WHERE CorporationID = :id
        """
    )

    return run_query(q, params)


def get_wida_student_data(stns):

    params = dict(id="")

    # when looking for a string value in a column, we need to wrap each
    # value in '', otherwise it will be interpreted as a column name
    stn_str ="'" + "', '".join([str(v) for v in stns]) + "'"

    q = text(
        """
        SELECT *
            FROM WIDA
            WHERE YEAR >= 2019 AND STN IN ({})""".format(
            stn_str
        )
    )

    results = run_query(q, params)
    results = results.sort_values(by="STN", ascending=False)

    return results


def get_iread_student_data(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT *
            FROM iread_student
	        WHERE SchoolID = :id AND TestYear > 2018
        """
    )

    results = run_query(q, params)
    results = results.sort_values(by="Test Year", ascending=False)

    results = results.rename(columns={"Test Year": "Year"})

    results["STN"] = results["STN"].astype(str)
    results["Year"] = results["Year"].astype(str)
    
    return results


def get_iread_stns(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT STN
            FROM iread_student
	        WHERE SchoolID = :id AND TestYear > 2018
        """
    )

    results = run_query(q, params)

    return results


def get_ilearn_stns(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT STN
            FROM ilearn_student
	        WHERE SchoolID = :id
        """
    )

    results = run_query(q, params)

    return results


# combines the above functions
def get_school_stns(school):

    ilearn_stns = get_ilearn_stns(school)
    ilearn_stns["STN"] = ilearn_stns["STN"].astype(str)

    # get student level IREAD data
    iread_stns = get_iread_stns(school)
    iread_stns["STN"] = iread_stns["STN"].astype(str)

    school_stns = pd.concat(
        [ilearn_stns, iread_stns], axis=0, ignore_index=True
    )

    return school_stns


def get_ilearn_student_data(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT *
            FROM ilearn_student
	        WHERE SchoolID = :id
        """
    )

    results = run_query(q, params)

    return results


def get_attendance_data(school_id, school_type, year):
    params = dict(id=school_id)

    # NOTE: AHS attendance data is stored in the hs table. K12 attendance
    # data is the same in both k8 and hs tables (it isn't broken out)
    if school_type == "K8":
        table = "academic_data_k8"
        id_type = "SchoolID"
    elif school_type == "HS" or school_type == "AHS" or \
        school_type == "K12":
        table = "academic_data_hs"
        id_type = "SchoolID"
    elif school_type == "corp_K8":
        table = "corporation_data_k8"
        id_type = "CorporationID"
    elif school_type == "corp_HS" or school_type == "corp_AHS" or \
        school_type == "corp_K12":
        table = "corporation_data_hs"
        id_type = "CorporationID"      
    elif school_type == "K12":
        return
    
    query_string  = """
        SELECT Year, AttendanceRate, StudentsChronicallyAbsent, TotalStudentCount
            FROM {}
	        WHERE {} = :id
        """.format(
        table, id_type
    )

    q = text(query_string)
  
    results = run_query(q, params)
    results = results.sort_values(by="Year", ascending=False)

    attendance_data = results[results["Attendance Rate"].notnull()]

    # replace empty strings with NaN
    attendance_data = attendance_data.replace(r'^\s*$', np.nan, regex=True)

    attendance_data["Chronic Absenteeism %"] = \
        calculate_percentage(attendance_data["Students Chronically Absent"], attendance_data["Total Student Count"])

    attendance_data = attendance_data.drop(["Students Chronically Absent","Total Student Count"], axis=1)

    excluded_years = get_excluded_years(year)
    if excluded_years:
        attendance_data = attendance_data[~attendance_data["Year"].isin(excluded_years)]
    
    attendance_rate = (
        attendance_data.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    attendance_rate = conditional_fillna(attendance_rate)

    # sort Year cols in ascending order (ignore Category)
    attendance_rate = (
        attendance_rate.set_index("Category")
        .sort_index(ascending=True, axis=1)
        .reset_index()
    )

    attendance_rate.columns = attendance_rate.columns.astype(str)

    for col in attendance_rate.columns:
        attendance_rate[col] = (
            pd.to_numeric(attendance_rate[col], errors="coerce")
            .fillna(attendance_rate[col])
            .tolist()
        )

    return attendance_rate


# Get k8 academic data for single school
def get_k8_school_academic_data(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT *
            FROM academic_data_k8
	        WHERE SchoolID = :id
        """
    )

    results = run_query(q, params)
    results = results.sort_values(by="Year", ascending=False)

    return results


# get k8 academic data for a list of schools
def get_selected_k8_school_academic_data(*args):
    keys = ["schools", "year"]
    params = dict(zip(keys, args))

    school_str = ", ".join([str(int(v)) for v in params["schools"]])

    q = text(
        """SELECT *
                FROM academic_data_k8
                WHERE Year = :year AND SchoolID IN ({})""".format(
            school_str
        )
    )

    results = run_query(q, params)

    return results


def get_k8_corporation_academic_data(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT *
	        FROM corporation_data_k8
	        WHERE CorporationID = (
		        SELECT GEOCorp
			        FROM school_index
			        WHERE SchoolID = :id)
        """
    )

    results = run_query(q, params)
    results = results.sort_values(by="Year", ascending=False)

    return results


# TODO: Combine this function
def get_hs_corporation_academic_data(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT *
	        FROM corporation_data_hs
	        WHERE CorporationID = (
		        SELECT GEOCorp
			        FROM school_index
			        WHERE SchoolID = :id)
        """
    )

    results = run_query(q, params)

    results = results.sort_values(by="Year")

    return results

###
# get corp_data by type
def get_corporation_academic_data(*args):
    keys = ["id","type"]
    params = dict(zip(keys, args))

    if params["type"] == "HS" or params["type"] == "AHS":
        table = "corporation_data_hs"
    else:
        table = "corporation_data_k8"

    q = text(
        """
        SELECT *
	        FROM {}
	        WHERE CorporationID = (
		        SELECT GEOCorp
			        FROM school_index
			        WHERE SchoolID = :id)""".format(table)
    )

    results = run_query(q, params)

    results = results.sort_values(by="Year")

    return results
###



def get_high_school_academic_data(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT *
            FROM academic_data_hs
	        WHERE SchoolID = :id
        """
    )

    return run_query(q, params)


# get hs academic data for a list of schools
def get_selected_hs_school_academic_data(*args):
    keys = ["schools", "year"]
    params = dict(zip(keys, args))

    school_str = ", ".join([str(int(v)) for v in params["schools"]])

    q = text(
        """SELECT *
                FROM academic_data_hs
                WHERE Year = :year AND SchoolID IN ({})""".format(
            school_str
        )
    )

    results = run_query(q, params)

    return results


def get_growth_data(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT *
	        FROM growth_data
	        WHERE MajorityEnrolledSchoolID = :id
        """
    )
    return run_query(q, params)


# "SchoolTotal|ELATotalTested" is a proxy for school size for k8 schools.
def get_school_coordinates(*args):
    keys = ["year", "type"]
    params = dict(zip(keys, args))

    if params["type"] == "HS":
        q = text(
            """
            SELECT Lat, Lon, SchoolID, SchoolName, HighGrade, LowGrade
                FROM academic_data_hs 
                WHERE Year = :year
        """
        )
    elif params["type"] == "AHS":
        q = text(
            """
            SELECT Lat, Lon, SchoolID, SchoolName, HighGrade, LowGrade
                FROM academic_data_hs 
                WHERE Year = :year and SchoolType = "AHS"
        """
        )
    else:
        q = text(
            """
            SELECT Lat, Lon, SchoolID, SchoolName, HighGrade, LowGrade, "Total|ELATotalTested"
                FROM academic_data_k8 
                WHERE Year = :year
        """
        )

    return run_query(q, params)


#TODO: Is this being used? ONCE for HS in SINGLE YEAR
#TODO: want to merge get_selected functions and remove this
def get_comparable_schools(*args):
    keys = ["schools", "year", "type"]
    params = dict(zip(keys, args))

    school_str = ", ".join([str(int(v)) for v in params["schools"]])

    if params["type"] == "HS":
        query_string = """
            SELECT *
                FROM academic_data_hs
                WHERE Year = :year AND SchoolID IN ({})""".format(
            school_str
        )

    elif params["type"] == "AHS":
        query_string = """
            SELECT *
                FROM academic_data_hs
                WHERE Year = :year AND SchoolType = "AHS" AND SchoolID IN ({})""".format(
            school_str
        )
    else:  # K8
        if params["year"] == "All":
            query_string = """
                SELECT *
                    FROM academic_data_k8
                    WHERE SchoolID IN ({})""".format(
                school_str
            )
        else:
            query_string = """
                SELECT *
                    FROM academic_data_k8
                    WHERE Year = :year AND SchoolID IN ({})""".format(
                school_str
            )

    q = text(query_string)

    return run_query(q, params)

# Gets all academic data and formats it for display
def get_all_the_data(*args):

    from .calculations import calculate_proficiency, recalculate_total_proficiency, \
        check_for_no_data, check_for_insufficient_n_size, conditional_fillna, \
        calculate_graduation_rate, calculate_sat_rate
    from .process_data import merge_high_school_data, transpose_data
    import itertools

    keys = ["schools", "type", "year", "page"]

    params = dict(zip(keys, args))

    # if length of school_id is > 1, then we are pulling data for a list
    # of schools (academic_analysis), otherwise one school (academic_info and
    # academic_metric)
    if len(params["schools"]) > 1:
        school_id = params["schools"][0]
        school_str = ", ".join([str(int(v)) for v in params["schools"]])
    else:
        school_id = params["schools"][0]
        school_str = params["schools"][0]

    # Get data for academic_information and academic_metrics
    # all data / all years for school(s) and school corporation
    if params["type"] == "K8":
        school_table = "academic_data_k8"
    else:
        school_table = "academic_data_hs"

        # elif params["type"] == "AHS":
        #     query_string = """
        #         SELECT *
        #             FROM {}
        #             WHERE SchoolType = "AHS" AND SchoolID IN ({})""".format(
        #         school_str, school_table
            
    query_string = """
        SELECT *
            FROM {}
            WHERE SchoolID IN ({})""".format(
        school_table, school_str
    )

    q = text(query_string)

###
    print(params)
###
    
    school_data = run_query(q, params)
    school_data = school_data.sort_values(by="Year", ascending=False)

    # get corp data (for academic_metrics and academic_analysis_single_year)
    # and add to dataframe
    corp_data = get_corporation_academic_data(params["schools"][0], params["type"])

    # add columns not in corp database
    corp_data["School ID"] = corp_data["Corporation ID"]
    corp_data["School Name"] = corp_data["Corporation Name"]

    # merge - result includes school, school corp, and comparable schools if
    # multiple school ids in the schools variable
    result = pd.concat([school_data,corp_data],axis=0)

    excluded_years = get_excluded_years(params["year"])
    if excluded_years:
        result = result[~result["Year"].isin(excluded_years)]

    # Drop all columns for a Category if the value of "Total Tested" for
    # the Category for the school is null or 0 for the "school"
    drop_columns = []

    data = result.copy()

    # convert from float to str while dropping the decimal
    data["School ID"] = data["School ID"].astype('Int64').astype('str')
    data["Corporation ID"] = data["Corporation ID"].astype('Int64').astype('str')

    if params["type"] == "K8":
        tested_cols = [col for col in data.columns.to_list() if "Total Tested" in col or "Test N" in col]
    else:
        tested_cols = [col for col in data.columns.to_list() if "Total Tested" in col or "Cohort Count" in col]

    for col in tested_cols:

        if ( 
            pd.to_numeric(data[data["School ID"] == school_id][col], errors="coerce").sum() == 0
            or data[data["School ID"] == school_id][col].isnull().all()
        ):

            if "Total Tested" in col:
                match_string = " Total Tested"
            else:
                if params["type"] == "K8":
                    match_string = " Test N"
                else:
                    match_string = "|Cohort Count"

            matching_cols = data.columns[
                pd.Series(data.columns).str.startswith(col.split(match_string)[0])
            ]

            drop_columns.append(matching_cols.tolist())

    drop_all = [i for sub_list in drop_columns for i in sub_list]

    data = data.drop(drop_all, axis=1).copy()

    # k8 or hs data with excluded years and non-tested categories dropped
    data = data.reset_index(drop=True)

    ## process High School data ##
    if params["type"] == "HS" or params["type"] == "AHS":
        processed_data = data.copy()

        # remove "EBRW and Math" columns
        processed_data = processed_data.drop(list(processed_data.filter(regex="EBRW and Math")), axis=1)

        # Calculate Grad Rate
        if "Total|Cohort Count" in processed_data.columns:
            processed_data = calculate_graduation_rate(processed_data)

        # Calculate SAT Rates #
        if "Total|EBRW Total Tested" in processed_data.columns:
            processed_data = calculate_sat_rate(processed_data)

        ## AHS data ##
        if params["type"] == "AHS":
            if "AHS|CCR" in processed_data.columns:
                processed_data["AHS|CCR"] = pd.to_numeric(processed_data["AHS|CCR"], errors="coerce")

            if "AHS|Grad All" in processed_data.columns:
                processed_data["AHS|Grad All"] = pd.to_numeric(
                    processed_data["AHS|Grad All"], errors="coerce"
                )

            if {"AHS|CCR", "AHS|Grad All"}.issubset(processed_data.columns):
                processed_data["CCR Percentage"] = processed_data["AHS|CCR"] / processed_data["AHS|Grad All"]

    ## process K8 data ##
    elif params["type"] == "K8": # or K12?
        processed_data = data.copy()

        # remove "ELA and Math" columns
        processed_data = processed_data.drop(list(processed_data.filter(regex="ELA and Math")), axis=1)

        processed_data = calculate_proficiency(processed_data)

        # In order for an apples to apples comparison between School Total Proficiency,
        # we need to recalculate it for the comparison schools using the same grade span
        # as the selected school. E.g., school is k-5, comparison school is k-8, we
        # recalculate comparison school totals using only grade k-5 data.
        comparison_data = processed_data.loc[
            processed_data["School ID"] != school_id
        ].copy()

        school_data = processed_data.loc[
            processed_data["School ID"] == school_id
        ].copy()

        revised_totals = recalculate_total_proficiency(
            comparison_data, school_data
        )

        processed_data = processed_data.set_index(["School ID","Year"])
        processed_data.update(revised_totals.set_index(["School ID","Year"]))

        # this is school, school corporation, and comparable school data
        processed_data = processed_data.reset_index()

# TODO: Test processed data here for null before sending through rest of flow
      
    # begin processing for specific pages
    if params["page"] == "analysis":
        if params["type"] == "HS" or params["type"] == "AHS":
            
            hs_data = processed_data.copy()
            
            # Need to check data again to see if anything is left after the above operations
            # if all columns in data other than the 1st (Year) are null then return empty df
            if hs_data.iloc[:, 1:].isna().all().all():
                analysis_data = pd.DataFrame()

            else:
                analysis_data = hs_data.filter(
                    regex=r"School ID|School Name|Corporation ID|Corporation Name|Graduation Rate$|Benchmark \%|^Year$",
                    axis=1,
                ).copy()

                analysis_data = analysis_data.drop(list(analysis_data.filter(regex="EBRW and Math")), axis=1)

                hs_cols = [c for c in analysis_data.columns if c not in ["School Name", "Corporation Name"]]
        
                # get index of rows where school_id matches selected school
                school_idx = analysis_data.index[analysis_data["School ID"] == school_id].tolist()[0]

                # force all to numeric (this removes '***' strings) - we
                # later use NaN as a proxy
                for col in hs_cols:
                    analysis_data[col] = pd.to_numeric(
                        analysis_data[col], errors="coerce"
                    )

                # drop all columns where the row at school_name_idx has a NaN value
                analysis_data = analysis_data.loc[:, ~hs_data.iloc[school_idx].isna()]                
        
        else:
            # K8 Analysis Data
            k8_data = processed_data.copy()
            
            analysis_data = k8_data.filter(
                regex=r"\|ELA Proficient %$|\|Math Proficient %$|IREAD Proficient %|^Year$|Low|High|School Name|School ID|Corporation ID",
                axis=1,
            )
            analysis_data = analysis_data.sort_values("Year").reset_index(drop=True)
            
            analysis_data = analysis_data[analysis_data.columns[~analysis_data.columns.str.contains(r"Female|Male")]]
            
            # Drop columns for all categories where the values are NaN
            school_idx = analysis_data.index[analysis_data["School ID"] == school_id].tolist()[0]
            analysis_data = analysis_data.loc[:, ~analysis_data.iloc[school_idx].isna()]

            # We don't want to get rid of "***" yet, but we also don't
            # want to pass through a dataframe that that is all "***" - so
            # we convert create a copy, coerce all of the academic columns
            # to numeric and check to see if the entire dataframe for NaN
            check_for_unchartable_data = analysis_data.copy()

            check_for_unchartable_data.drop(
                ["School Name", "School ID", "Low Grade", "High Grade", "Year"],
                axis=1,
                inplace=True,
            )

            for col in check_for_unchartable_data.columns:
                check_for_unchartable_data[col] = pd.to_numeric(
                    check_for_unchartable_data[col], errors="coerce"
                )

            if (
                (params["type"] == "K8" or params["type"] == "K12")
                and len(analysis_data.index) > 0
            ) and check_for_unchartable_data.isnull().all().all() == True:
                
                analysis_data = pd.DataFrame()
            else:

                return analysis_data
            # TODO: Return analysis data here and then in body- filter by year
            # TODO: and drop '***' - line 723 in analysis_single_year    

    elif params["page"] == "info" or params["page"] == "metrics":

        if params["type"] == "HS" or params["type"] == "AHS":
            
            # TODO: HS Metrics Data
            # TODO New HS has CorpID/Name is missing Low/High Grade - not sure that this matters
            from .calculate_metrics import calculate_adult_high_school_metrics, calculate_high_school_metrics

            corp_data = processed_data[processed_data["School ID"] == processed_data["Corporation ID"]].copy()
            school_data = processed_data[processed_data["School ID"] == school_id].copy()
            
            school_metrics_data = transpose_data(school_data,params)
            corp_metrics_data = transpose_data(corp_data,params)
            
            if params["type"] == "AHS":
                final_metric_data = calculate_adult_high_school_metrics(school_id, metric_data)

            elif params["type"] == "HS":

                # all_school_data.columns = all_school_data.columns.astype(str)
                # all_corp_data.columns = all_corp_data.columns.astype(str)

                # Add State Graduation Average to Corp DataFrame
                state_grad_average = get_graduation_data()

                corp_metrics_data = pd.concat(
                    [
                        corp_metrics_data.reset_index(drop=True),
                        state_grad_average.reset_index(drop=True),
                    ],
                    axis=0,
                ).reset_index(drop=True)

                # For the school calculation we duplicate the school"s Total Graduation rate and
                # rename it "State Grad Average" - when the difference is calculated
                # between the two data frames, the difference between the Total Graduation Rates
                # will be School minus Corportion and the difference between State Grad Average Rates
                # will be School minus State Average

# TODO: Why Are We Doing this?
                # If no Total Graduation Rate Category exists for a school, we add
                # a new row filled with nan (by enlargement)
                if "Total|Graduation Rate" not in school_metrics_data["Category"].values:

                    school_metrics_data.loc[len(school_metrics_data)] = np.nan
                    school_metrics_data.loc[
                        school_metrics_data.index[-1], "Category"
                    ] = "Total|Graduation Rate"

                duplicate_row = school_metrics_data[
                    school_metrics_data["Category"] == "Total|Graduation Rate"
                ].copy()
                duplicate_row["Category"] = "State Graduation Average"
                school_metrics_data = pd.concat(
                    [school_metrics_data, duplicate_row], axis=0, ignore_index=True
                )

                # Clean up and merge school and corporation dataframes
                year_cols = list(school_metrics_data.columns[:0:-1])
                year_cols = [c[0:4] for c in year_cols]  # keeps only YYYY part of string
                year_cols = list(set(year_cols))
                year_cols.sort()

                # last bit of cleanup is to drop "Corporation Name" Category from corp df
                corp_metrics_data = corp_metrics_data.drop(
                    corp_metrics_data.loc[corp_metrics_data["Category"] == "Corporation Name"].index
                ).reset_index(drop=True)

                # Create list of alternating columns
                # we technically do not need the Corporation N-Size at this point, but
                # we will keep it just in case. We drop it in the final df
                corp_cols = [e for e in corp_metrics_data.columns if "Corp" in e]
                cnsize_cols = [e for e in corp_metrics_data.columns if "CN-Size" in e]
                school_cols = [e for e in school_metrics_data.columns if "School" in e]
                snsize_cols = [e for e in school_metrics_data.columns if "SN-Size" in e]
                school_cols.sort()
                snsize_cols.sort()
                corp_cols.sort()
                cnsize_cols.sort()

                result_cols = [str(s) + "Diff" for s in year_cols]

                merged_cols = list(
                    itertools.chain(*zip(school_cols, snsize_cols, corp_cols, cnsize_cols))
                )
                merged_cols.insert(0, "Category")

                hs_merged_data = school_metrics_data.merge(corp_metrics_data, on="Category", how="left")
                hs_merged_data = hs_merged_data[merged_cols]

                # create temp dataframe to calculate differences between school
                # and corp proficiency
                tmp_category = school_metrics_data["Category"]
                school_metrics_data = school_metrics_data.drop("Category", axis=1)
                school_metrics_data = school_metrics_data.fillna(value=np.nan)
                
                corp_metrics_data = corp_metrics_data.drop("Category", axis=1)
                corp_metrics_data = corp_metrics_data.fillna(value=np.nan)
                
                filename38 = (
                        "banana_sch.csv"
                    )
                school_metrics_data.to_csv(filename38, index=False)

                filename39 = (
                        "banana_crp.csv"
                    )
                corp_metrics_data.to_csv(filename39, index=False)
                
                # calculate difference between two dataframes (for loop
                # not great - but still relatively fast)
                hs_results = pd.DataFrame()
                for y in year_cols:
                    hs_results[y] = calculate_difference(
                        school_metrics_data[y + "School"], corp_metrics_data[y + "Corp"]
                    )

                # filename17 = (
                #     "tootie.csv"
                # )
                # hs_results.to_csv(filename17, index=False)

                # Create final column order - dropping the corp avg and corp N-Size cols
                # (by not including them in the list) because we do not display them
                final_cols = list(itertools.chain(*zip(school_cols, snsize_cols, result_cols)))
                final_cols.insert(0, "Category")

                hs_results = hs_results.set_axis(result_cols, axis=1)
                hs_results.insert(loc=0, column="Category", value=tmp_category)

                final_hs_academic_data = hs_merged_data.merge(hs_results, on="Category", how="left")
                final_hs_academic_data = final_hs_academic_data[final_cols]

                final_hs_academic_data.columns = final_hs_academic_data.columns.str.replace(
                    "SN-Size", "N-Size", regex=True
                )

                print('HS Grad')
                filename7 = (
                    "puddy.csv"
                )
                final_hs_academic_data.to_csv(filename7, index=False)
                
                return final_hs_academic_data

                # final_metric_data = calculate_high_school_metrics(metric_data)




            #metric_data = metric_data.set_index("Category")
            # school_metric_data = school_metric_data.drop(["School ID","Corporation ID","Corporation Name"])
            # school_metric_data = school_metric_data.reset_index(drop=False)

            # corporation metric data (used to calculate difference)
            # corp_metric_data = metric_data.loc[:, metric_data.loc["School ID"] == metric_data.loc["Corporation ID"]]
            # corp_metric_data = corp_metric_data.drop(["Low Grade","High Grade","School ID"])
            # corp_metric_data = corp_metric_data.reset_index(drop=False)
            # # temporarily store Low and High Grade rows
            # print(final_hs_info_data)

        else:
            # TODO: New k8 info has Corp ID- not sure that this matters
            # K8 information data
            school_info_data = processed_data[processed_data["School ID"] == school_id]
            final_school_data = transpose_data(school_info_data,params)

            if params["page"] == "info":

                return final_school_data

            # TODO: THis belongs right before final data (in chart?)
            # result, no_data = check_for_no_data(result)
            # print(no_data)
            # insuf_string = check_for_insufficient_n_size(result)
            # print(insuf_string)
            # TODO: ADD BACK - WHERE?
                        
            else:   # academic_metrics
                corp_info_data = processed_data[processed_data["School ID"] == processed_data["Corporation ID"]]

                final_corp_data = transpose_data(corp_info_data,params)        
                
                corp_proficiency_cols = [col for col in final_corp_data.columns.to_list() if "Corp" in col]
                
                # School Proficiency and N-Size and Corp Profiency
                metric_data = pd.concat([final_school_data, final_corp_data[corp_proficiency_cols]], axis=1)
            
            # TODO: send back to main to calculate metrics 
                #calculate_k8_yearly_metrics # school
                #calculate_k8_comparison_metrics # both

                return metric_data




        #TODO:    
        # Once final_data is returned to main function, convert to fig data with the
        # following:
        # school_info_fig = final_data.copy()
        # school_info_fig = school_info_fig.filter(regex=r"School|Category", axis=1)
        # school_info_fig.columns = school_info_fig.columns.str.removesuffix("School")
        # school_info_fig = (
        #     school_info_fig.set_index("Category")
        #     .T.rename_axis("Year")
        #     .rename_axis(None, axis=1)
        #     .reset_index()
        # )
        #TODO:

    # elif params["page"] == "metric":


####                
                                

        
        # make a copy for k8_metric and k8_info data
        # TODO: K8 Metric Data


        ## K8 Information (table data) and Academic Metric data ##

        # # create new df with Total Tested and Test N (IREAD) values
        # data_tested = school_data.filter(
        #     regex="Total Tested|Test N|Year", axis=1
        # ).copy()

        # data_tested = (
        #     data_tested.set_index("Year")
        #     .T.rename_axis("Category")
        #     .rename_axis(None, axis=1)
        #     .reset_index()
        # )

        # data_tested = data_tested.rename(
        #     columns={
        #         c: str(c) + "N-Size"
        #         for c in data_tested.columns
        #         if c not in ["Category"]
        #     }
        # )

        # # clean up nulls and 0
        # data_tested = data_tested.fillna(value=np.nan)
        # data_tested = data_tested.replace(0, np.nan)

        # filter to remove columns used to calculate final proficiency




    #     metric_data = metric_data.filter(
    #         regex=r"School ID|Corporation ID|Corporation Name|Low Grade|High Grade|\|ELA Proficient %$|\|Math Proficient %$|IREAD Proficient %|^Year$",
    #         axis=1,
    #     )

    #     # transpose dataframes and clean headers
    #     metric_data.columns = metric_data.columns.astype(str)
        
    #     metric_data = (
    #         metric_data.set_index("Year")
    #         .T.rename_axis("Category")
    #         .rename_axis(None, axis=1)
    #         .reset_index()
    #     )

    #     # remove school_name row
    #     # metric_data = metric_data[
    #     #     metric_data["Category"].str.contains("School Name") == False
    #     # ]

    #     metric_data = metric_data.reset_index(drop=True)
    #     metric_data = metric_data.set_index("Category")

    #     # school metric and info data
    #     school_metric_data = metric_data.loc[:, metric_data.loc["School ID"] == school_id]
    #     school_metric_data = school_metric_data.drop(["School ID","Corporation ID","Corporation Name"])

    #     school_metric_data = school_metric_data.reset_index(drop=False)

    #     # corporation metric data (used to calculate difference)
    #     corp_metric_data = metric_data.loc[:, metric_data.loc["School ID"] == metric_data.loc["Corporation ID"]]
    #     corp_metric_data = corp_metric_data.drop(["Low Grade","High Grade","School ID"])
    #     corp_metric_data = corp_metric_data.reset_index(drop=False)

    #     # format school data -> "YYYYSchool", "YYYYN0Size","YYYYSchool", . . .

    #     school_metric_data = school_metric_data.rename(
    #         columns={
    #             c: str(c) + "School"
    #             for c in school_metric_data.columns
    #             if c not in ["Category"]
    #         }
    #     )

    #     # temporarily store Low and High Grade rows
    #     other_rows = school_metric_data[
    #         school_metric_data["Category"].str.contains(r"Low|High")
    #     ]

    #     # Merge Total Tested DF with Proficiency DF based on a cross
    #     # merge substring match

    #     # add new column with substring values and drop old Category column
    #     data_tested["Substring"] = data_tested["Category"].replace(
    #         {" Total Tested": "", " Test N": ""}, regex=True
    #     )

    #     data_tested = data_tested.drop("Category", axis=1)

    #     # this cross-merge and substring match process takes about .3s -
    #     # there must be a faster way
    #     final_data = school_metric_data.merge(data_tested, how="cross")

    #     # temporarily rename "English Learner" category because otherwise the
    #     # cross merge will match both "English" and "Non English"
    #     final_data = final_data.replace(
    #         {
    #             "Non English Language Learners": "Temp1",
    #             "English Language Learners": "Temp2",
    #         },
    #         regex=True,
    #     )

    #     # filter rows - keeping only those rows where a substring is in Category
    #     final_data = final_data[
    #         [a in b for a, b in zip(final_data["Substring"], final_data["Category"])]
    #     ]

    #     final_data = final_data.replace(
    #         {
    #             "Temp1": "Non English Language Learners",
    #             "Temp2": "English Language Learners",
    #         },
    #         regex=True,
    #     )

    #     final_data = final_data.drop("Substring", axis=1)
    #     final_data = final_data.reset_index(drop=True)

    #     # reorder columns for display
    #     school_cols = [e for e in final_data.columns if "School" in e]
    #     nsize_cols = [e for e in final_data.columns if "N-Size" in e]
    #     school_cols.sort()
    #     nsize_cols.sort()

    #     # alternate columns in the School,N-Size,School,N-Size . . . pattern
    #     final_cols = list(itertools.chain(*zip(school_cols, nsize_cols)))
    #     final_cols.insert(0, "Category")

    #     final_data = final_data[final_cols]

    #     # Add Low Grade, and High Grade rows back (missing cols will populate with NaN)
    #     final_data = pd.concat(
    #         [final_data.reset_index(drop=True), other_rows.reset_index(drop=True)],
    #         axis=0,
    #     ).reset_index(drop=True)

    #     # NOTE: final pre-calculated school K8 Metric data and final K8 info table data
    #     final_data = conditional_fillna(final_data)

    #     # TODO: THis belongs right before final data
    #     # result, no_data = check_for_no_data(result)
    #     # print(no_data)
    #     # insuf_string = check_for_insufficient_n_size(result)
    #     # print(insuf_string)
    #     # TODO: ADD BACK

    # # ### K8 Information (fig data)
    # #     school_info_fig = k8_data_calculated[k8_data_calculated["School ID"] == school_id].copy()

    # #     # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
    # #     school_info_fig = school_info_fig.filter(
    # #         regex=r"\|ELA Proficient %$|\|Math Proficient %$|IREAD Proficient %|^Year$|Low|High|School Name",
    # #         axis=1,
    # #     )
    # #     school_info_fig = school_info_fig.sort_values("Year").reset_index(drop=True)

    # #     # NOTE: final k8_info data for figs
    # #     school_info_fig = conditional_fillna(school_info_fig)



    #     ### K8 Analysis data
    #     # k8_analysis = k8_data_calculated.copy()
    #     # k8_analysis = k8_analysis.filter(
    #     #     regex=r"\|ELA Proficient %$|\|Math Proficient %$|IREAD Proficient %|^Year$|Low|High|School Name|School ID|Corporation ID",
    #     #     axis=1,
    #     # )
    #     # k8_analysis = k8_analysis.sort_values("Year").reset_index(drop=True)
        
    #     # k8_analysis = k8_analysis[k8_analysis.columns[~k8_analysis.columns.str.contains(r"Female|Male")]]
        
    #     # # Drop columns for all categories where the values are NaN
    #     # school_idx = k8_analysis.index[k8_analysis["School ID"] == school_id].tolist()[0]
    #     # k8_analysis = k8_analysis.loc[:, ~k8_analysis.iloc[school_idx].isna()]

    #     # # We don't want to get rid of "***" yet, but we also don't
    #     # # want to pass through a dataframe that that is all "***" - so
    #     # # we convert create a copy, coerce all of the academic columns
    #     # # to numeric and check to see if the entire dataframe for NaN
    #     # check_for_unchartable_data = k8_analysis.copy()

    #     # check_for_unchartable_data.drop(
    #     #     ["School Name", "School ID", "Low Grade", "High Grade", "Year"],
    #     #     axis=1,
    #     #     inplace=True,
    #     # )

    #     # for col in check_for_unchartable_data.columns:
    #     #     check_for_unchartable_data[col] = pd.to_numeric(
    #     #         check_for_unchartable_data[col], errors="coerce"
    #     #     )

    #     # if (
    #     #     (params["type"] == "K8" or params["type"] == "K12")
    #     #     and len(k8_analysis.index) > 0
    #     # ) and check_for_unchartable_data.isnull().all().all() == True:
            
    #     #     k8_analysis = pd.DataFrame()

    #     # # NOTE: Return here- filter by year and then drop '***' - line 723 in analysis_single_year




    return data

def get_year_over_year_data(*args):
    keys = ["school_id", "comp_list", "category", "year", "flag"]
    params = dict(zip(keys, args))

    school_str = ", ".join([str(int(v)) for v in params["comp_list"]])

    if params["flag"] == "sat":
        school_table = "academic_data_hs"
        corp_table = "corporation_data_hs"
        
        tested = params["category"] + " Total Tested"
        passed = params["category"] + " At Benchmark"
        result = params["category"] + " % At Benchmark"

        # if "School Total" - need to remove space
        if params["category"] == "Total|":
            tested = tested.replace("| ", "|")
            passed = passed.replace("| ", "|")
            result = result.replace("| ", "|")

    elif params["flag"] == "grad":
        school_table = "academic_data_hs"
        corp_table = "corporation_data_hs"        
        
        tested = params["category"] + "Cohort Count"
        passed = params["category"] + "Graduates"
        result = params["category"] + "Graduation Rate"

        # if "Total" - need to remove space
        if params["category"] == "Total|":
            tested = tested.replace("| ", "|")
            passed = passed.replace("| ", "|")
            result = result.replace("| ", "|")

    else:  # k8 categories
        school_table = "academic_data_k8"
        corp_table = "corporation_data_k8"

        if "IREAD" in params["category"]:
            tested = params["category"] + " Test N"
            passed = params["category"] + " Pass N"
            result = params["category"] + " Passed"
        else:
            tested = params["category"] + " Total Tested"
            passed = params["category"] + " Total Proficient"
            result = params["category"] + " Proficient"

    # Query strings (param must be passed in with spaces)
    passed_query = passed.replace(" ", "")
    tested_query = tested.replace(" ", "")

    school_query_str = (
        "Year, SchoolID, SchoolName, LowGrade, HighGrade, SchoolType, "
        + '"'
        + passed_query
        + '", "'
        + tested_query
        + '"'
    )

    corp_query_str = (
        "Year, CorporationName, LowGrade, HighGrade, "
        + '"'
        + passed_query
        + '", "'
        + tested_query
        + '"'
    )

    # School Data
    query_string1 = """
        SELECT {}
            FROM {}
	        WHERE SchoolID = :school_id
        """.format(
        school_query_str, school_table
    )

    q1 = text(query_string1)

    school_data = run_query(q1, params)

    # get school type and then drop column (this just gets the string
    # value with the highest frequency - avoids situations where a
    # specific year may not have a value)
    school_type = school_data["School Type"].value_counts().index.values[0]

    school_data = school_data.drop(["School Type"], axis=1)

    # track school name, school id, and gradespan separately
    school_info = school_data[["School Name", "School ID", "Low Grade", "High Grade"]]

    school_name = school_data["School Name"][0]

    school_data[school_name] = pd.to_numeric(
        school_data[passed], errors="coerce"
    ) / pd.to_numeric(school_data[tested], errors="coerce")

    school_data = school_data.drop(
        ["School Name", "Low Grade", "High Grade", passed, tested], axis=1
    )
    school_data = school_data.sort_values("Year").reset_index(drop=True)

    # drop rows (years) where the school has no data
    # if dataframe is empty after, just return empty df
    school_data = school_data[school_data[school_name].notna()]

    if len(school_data.columns) == 0:
        result = school_data

    else:
        # Corp Data
        query_string2 = """
            SELECT {}
                FROM {}
                WHERE CorporationID = (
                    SELECT GEOCorp
                        FROM school_index
                        WHERE SchoolID = :school_id)
            """.format(
            corp_query_str, corp_table
        )

        q2 = text(query_string2)

        corp_data = run_query(q2, params)

        corp_data[corp_data["Corporation Name"][0]] = pd.to_numeric(
            corp_data[passed], errors="coerce"
        ) / pd.to_numeric(corp_data[tested], errors="coerce")
        corp_data = corp_data.drop(
            ["Corporation Name", "Low Grade", "High Grade", passed, tested], axis=1
        )
        corp_data = corp_data.sort_values("Year").reset_index(drop=True)

        # Comparison School Data
        query_string3 = """
                SELECT {}
                    FROM {}
                    WHERE SchoolID IN ({})""".format(
            school_query_str, school_table, school_str
        )

        q3 = text(query_string3)

        comparable_schools_data = run_query(q3, params)

        comparable_schools_data[result] = pd.to_numeric(
            comparable_schools_data[passed], errors="coerce"
        ) / pd.to_numeric(comparable_schools_data[tested], errors="coerce")

        # Store information about each school in separate df
        comparable_schools_info = comparable_schools_data[
            ["School Name", "School ID", "Low Grade", "High Grade"]
        ]

        # combine school and comp indexs into a list of School Names and School IDs
        all_school_info = pd.concat(
            [school_info, comparable_schools_info], ignore_index=True
        )

        all_school_info = all_school_info.drop_duplicates(subset=["School ID"])
        all_school_info = all_school_info.reset_index(drop=True)

        comparable_schools_data = comparable_schools_data.pivot(
            index="Year", columns="School Name", values=result
        )
        comparable_schools_data = comparable_schools_data.reset_index()
        comparable_schools_data = comparable_schools_data.sort_values("Year")

        if len(comparable_schools_data.columns) == 0:
            result = pd.merge(school_data, corp_data, on="Year")
        else:
            # do not merge school corp data with adult high school set
            if school_type == "AHS":
                result = pd.merge(school_data, comparable_schools_data, on="Year")
            else:
                result = pd.merge(
                    pd.merge(school_data, corp_data, on="Year"),
                    comparable_schools_data,
                    on="Year",
                )

        # account for changes in the year
        excluded_years = get_excluded_years(params["year"])
        if excluded_years:
            result = result[~result["Year"].isin(excluded_years)]

    return result, all_school_info


def get_student_level_ilearn(school, subject):

    ilearn_student_all = get_ilearn_student_data(school)

    # will also be empty for guest schools
    if not ilearn_student_all.empty:

        iread_student_data = get_iread_student_data(school)

        ilearn_filtered = ilearn_student_all.filter(
            regex=rf"STN|Current Grade|Tested Grade|{subject}"
        )

        ilearn_filtered = ilearn_filtered.rename(
            columns={
                "Current Grade": "ILEARN Current Grade",
                "Tested Grade": "ILEARN Tested Grade",
            }
        )
        iread_student_data = iread_student_data.rename(
            columns={"Year": "Test Year"}
        )        
        ilearn_filtered["STN"] = ilearn_filtered["STN"].astype(str)

        school_all_student_data = pd.merge(
            iread_student_data, ilearn_filtered, on="STN"
        )

        category = subject + " Proficiency"

        school_all_student_data = school_all_student_data[["Test Year",
            "STN","Tested Grade","Status","Exemption Status","ILEARN Tested Grade", category]]

        all_student_data_nopass = school_all_student_data[school_all_student_data["Status"] == "Did Not Pass"]
        all_student_data_pass = school_all_student_data[school_all_student_data["Status"] == "Pass"]
        
        def find_prof(series):
            # get the count of students At or Above proficiency and divide by the total #
            # of students in the series (essentially calculating proficiency)
            return (
                ((series == "At Proficiency").sum() + (series == "Above Proficiency").sum()) / 
                series.value_counts().sum()
            )
        
        pass_proficiency = all_student_data_pass.groupby(by="Test Year")[category].apply(find_prof).reset_index(name="Proficiency")
        nopass_proficiency = all_student_data_nopass.groupby(by="Test Year")[category].apply(find_prof).reset_index(name="Proficiency")

        nopass_nsize = all_student_data_nopass["Test Year"].value_counts().reset_index(name="N-Size").rename(columns={"index": "Test Year"})
        pass_nsize = all_student_data_pass["Test Year"].value_counts().reset_index(name="N-Size").rename(columns={"index": "Test Year"})

        iread_ilearn_pass_final = pd.merge(pass_proficiency,pass_nsize, on="Test Year")
        iread_ilearn_nopass_final = pd.merge(nopass_proficiency,nopass_nsize, on="Test Year")

        pass_column_name = "Avg. " + subject + " Proficiency - Students Passing IREAD"
        iread_ilearn_pass_final = iread_ilearn_pass_final.rename(
            columns={
                "Proficiency": pass_column_name, 
                "Test Year": "Year",
                "N-Size": "N-Size (Pass IREAD)"                
            }
        )

        nopass_column_name = "Avg. " + subject + " Proficiency - Students not Passing IREAD"
        iread_ilearn_nopass_final = iread_ilearn_nopass_final.rename(
            columns={
                "Proficiency": nopass_column_name,
                "Test Year": "Year",
                "N-Size": "N-Size (Did Not Pass IREAD)"
            }
        )

        iread_ilearn_pass_final["Year"] = iread_ilearn_pass_final["Year"].astype(str)        
        iread_ilearn_nopass_final["Year"] = iread_ilearn_nopass_final["Year"].astype(str)

    return iread_ilearn_pass_final, iread_ilearn_nopass_final