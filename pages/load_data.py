##############################################
# ICSB Dashboard - Database Queries (SQLite) #
##############################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.13
# date:     02/01/24

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

from .calculations import calculate_percentage, conditional_fillna

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

# TODO: Move this to app? import engine? use a function to pull the table?
engine = create_engine("sqlite:///data/db_updated.db")

users = create_engine("sqlite:///users.db")

print("Database Engine Created . . .")


# Return Dataframe (read_sql is a convenience function wrapper around read_sql_query)
# If no data matches query, returns an empty dataframe
def run_query(q, *args):
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
    db = engine.raw_connection()
    cur = db.cursor()
    cur.execute(""" SELECT MAX(Year) FROM academic_data_k8 """)
    year = cur.fetchone()[0]
    db.close()

    return year


current_academic_year = get_current_year()


# Used to dynamically count the number of network logins (all of which have
# negative group_id values) so we know how far to offset group_id in determining
# the charter dropdown in app.py. Otherwise we would have to hardcode this
# value. we add one to the total to account for the admin login
def get_network_count():
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


# TODO: The next two functions are almost identical (difference is Q#s). Maybe consolidate?
def get_financial_info_dropdown_years(school_id):
    # Processes financial df and returns a list of Year column names for
    # each year for which ADM Average is greater than '0'

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

        results = results.filter(regex="^\d{4}")

        for col in results.columns:
            results[col] = pd.to_numeric(results[col], errors="coerce")

        mask = results.iloc[adm_index] > 0

        results = results.loc[:, mask]

        # trim excess info (Q#) if present
        years = [x[:4] for x in results.columns.to_list()]

    else:
        years = []

    return years


def get_financial_analysis_dropdown_years(school_id):
    # Processes financial df and returns a list of Year column names for
    # each year for which ADM Average is greater than '0'

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

        # adding '$' to the end of the regex skips (Q#) years
        results = results.filter(regex="^\d{4}$")

        for col in results.columns:
            results[col] = pd.to_numeric(results[col], errors="coerce")

        mask = results.iloc[adm_index] > 0

        results = results.loc[:, mask]

        years = results.columns.to_list()

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

    return run_query(q, params)


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


def get_ethnicity(school_id, school_type, hs_category, selected_year, all_years):
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


def get_subgroup(school_id, school_type, hs_category, selected_year, all_years):
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


# for school corporations, SchoolID and CorpID are the same
def get_demographic_data(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT *
            FROM demographic_data
	        WHERE CorporationID = :id
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
    # results = results.sort_values(by="Test Year", ascending=False)

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

#TODO: NOT USING THIS ANYMORE?
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


def get_year_over_year_data(*args):
    keys = ["school_id", "comp_list", "category", "year", "flag"]

    params = dict(zip(keys, args))

    school_str = ", ".join([str(int(v)) for v in params["comp_list"]])

    school_table = "academic_data_hs"
    corp_table = "corporation_data_hs"

    if params["flag"] == "sat":
        tested = params["category"] + " Total Tested"
        passed = params["category"] + " At Benchmark"
        result = params["category"] + " % At Benchmark"

        # if "School Total" - need to remove space
        if params["category"] == "Total|":
            tested = tested.replace("| ", "|")
            passed = passed.replace("| ", "|")
            result = result.replace("| ", "|")

    elif params["flag"] == "grad":
        tested = params["category"] + "Cohort Count"
        passed = params["category"] + "Graduates"
        result = params["category"] + "Graduation Rate"

        # if "Total" - need to remove space
        if params["category"] == "Total|":
            tested = tested.replace("| ", "|")
            passed = passed.replace("| ", "|")
            result = result.replace("| ", "|")

    else:  # k8 categories
        tested = params["category"] + " Total Tested"
        passed = params["category"] + " Total Proficient"
        result = params["category"] + " Proficient"

        school_table = "academic_data_k8"
        corp_table = "corporation_data_k8"

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