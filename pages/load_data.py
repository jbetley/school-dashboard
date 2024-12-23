##############################################
# ICSB Dashboard - Database Queries (SQLite) #
##############################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.16
# date:     12/10/24

# TODO: Separate database call from processing for all functions
# NOTE: No K8 academic data exists for 2020

# Current data:
# ILEARN & ILEARN Student - 2024
# IREAD & IREAD Student - 2024
# SAT - 2024
# ADM - 2024
# Attendance Rate - 2023
# Chronic Absenteeism - 2024
# Demographics - 2024 (except SPED/ELL)
# Financial - 2023 (Audited) / 2024(Q4)
# Graduation Rate - 2023

import pandas as pd
import numpy as np
import re
from sqlalchemy import create_engine, text

from .calculations import (
    calculate_percentage,
    conditional_fillna,
)

# NOTE: Considering moving engine instantiation to app.py
engine = create_engine("sqlite:///data/indiana_schools.db")
users = create_engine("sqlite:///users.db")

print("Database Engine Created . . .")


def run_query(q, *args):
    """
    Takes sql text query, gets query as a dataframe (read_sql is a
    convenience function wrapper around read_sql_query), and perform
    a variety of basic clean up functions. If no data matches the query,
    an empty df is returned

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

        # NOTE: Is there a better way to do this?

        # sqlite column headers do not have spaces between words. But we need to
        # display the column names, so we have to do a bunch of str.replace to
        # account for all conditions. May be a better way, but this is pretty fast.
        # Adding a space between any lowercase character and any uppercase/number
        # character takes care of most of it. The other replace functions catch edge cases.
        df.columns = df.columns.str.replace(r"([a-z])([A-Z1-9%])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace(
            r"([WADTO])([CATPB&])", r"\1 \2", regex=True
        )

        df.columns = df.columns.str.replace("EBRWand", "EBRW and")
        df.columns = df.columns.str.replace("Freeand", "Free and")
        df.columns = df.columns.str.replace("Outof", "Out of")

        # the above is adding a space to NonWaiver- so we need to remove it
        df.columns = df.columns.str.replace("Non Waiver", "NonWaiver")
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

    if params["type"] == "k8" or params["type"] == "k12":
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
    # for that year is greater than 0

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

    # NOTE: Testing using "years with data" instead of "years
    # with ADM" which captures pre-opening years with "0"
    # State Grant data.
    results = results.dropna(axis=1, how="all")

    year_list = results.columns.tolist()

    year_list = [
        e for e in year_list if e not in ("School ID", "Category", "School Name")
    ]

    if len(results) > 0:
        if page == "financial_analysis":
            # only keep Q4 data, if Q1-Q3 data exists, we drop the entire column
            if "Q4" in "\t".join(year_list):
                year_list = [int(e[:4]) for e in year_list]

            else:
                year_list = [int(e) for e in year_list if "(Q" not in e]
        else:
            year_list = [int(e[:4]) for e in year_list]
    else:
        year_list = []

    return year_list


def get_adm_data(corp_id):
    # financial data will almost always be more accurate, but
    # some schools (Guests) don't have financial data and this
    # is an adequate substitute.

    params = dict(id=corp_id)

    q = text(
        """
        SELECT * 
        FROM adm_all
        WHERE CorporationID = :id
    """
    )

    results = run_query(q, params)

    return results


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
        columns={c: str(c) + "Corp" for c in results.columns if c not in ["Category"]}
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

    # change "***" & 0 to nan and drop
    for col in result.columns:
        result[col] = pd.to_numeric(result[col], errors="coerce")

    result.replace(0, np.nan, inplace=True)

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


def get_ethnicity(
    school_id, school_type, hs_category, subject_value, selected_year, all_years
):
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


def get_subgroup(
    school_id, school_type, hs_category, subject_value, selected_year, all_years
):
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

    else:  # k8
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
        SELECT Year, StateGrade, FederalRating
            FROM demographic_data_corp
	        WHERE CorporationID = :id
        """
    )

    return run_query(q, params)


def get_wida_student_data(stns):
    params = dict(id="")

    # when looking for a string value in a column, we need to wrap each
    # value in '', otherwise it will be interpreted as a column name
    stn_str = "'" + "', '".join([str(v) for v in stns]) + "'"

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


def get_discipline_data(*args):
    keys = ["id"]
    params = dict(zip(keys, args))

    q = text(
        """
        SELECT *
            FROM discipline
	        WHERE SchoolID = :id
        """
    )

    results = run_query(q, params)

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


# combination the above two functions
def get_school_stns(school):
    ilearn_stns = get_ilearn_stns(school)
    ilearn_stns["STN"] = ilearn_stns["STN"].astype(str)

    # get student level IREAD data
    iread_stns = get_iread_stns(school)
    iread_stns["STN"] = iread_stns["STN"].astype(str)

    school_stns = pd.concat([ilearn_stns, iread_stns], axis=0, ignore_index=True)

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


# Calculates State graduation average for all ahs for
# all years (as a substitute for state or corp avg)
def get_ahs_averages():
    params = dict(id="")
    q = text(
        """
        SELECT *
            FROM academic_data_hs
            WHERE SchoolType = "AHS"
        """
    )

    results = run_query(q, params)

    return results


def get_attendance_data(school_id, school_type, year):
    params = dict(id=school_id)

    # NOTE: AHS attendance data is stored in the hs table. K12 attendance
    # data is the same in both k8 and hs tables (it isn't broken out)
    if school_type == "k8":
        table = "academic_data_k8"
        id_type = "SchoolID"
    elif school_type == "hs" or school_type == "ahs" or school_type == "k12":
        table = "academic_data_hs"
        id_type = "SchoolID"
    elif school_type == "corp_k8":
        table = "corporation_data_k8"
        id_type = "CorporationID"
    elif (
        school_type == "corp_hs"
        or school_type == "corp_ahs"
        or school_type == "corp_k12"
    ):
        table = "corporation_data_hs"
        id_type = "CorporationID"
    elif school_type == "k12":
        return

    query_string = """
        SELECT Year, AttendanceRate, StudentsChronicallyAbsent, TotalStudentCount
            FROM {}
	        WHERE {} = :id
        """.format(
        table, id_type
    )

    q = text(query_string)

    results = run_query(q, params)
    results = results.sort_values(by="Year", ascending=False)

    # replace empty strings and "None" with NaN and drop any
    # rows where both values are NaN
    attendance_data = results.replace(r"^\s*$", np.nan, regex=True)
    attendance_data = attendance_data.fillna(value=np.nan)
    attendance_data = attendance_data.dropna(
        how="all", subset=["Attendance Rate", "Students Chronically Absent"]
    )

    # Chronic Absenteeism isn't used for AHS
    if school_type != "corp_ahs" and school_type != "ahs":
        attendance_data["Chronic Absenteeism %"] = calculate_percentage(
            attendance_data["Students Chronically Absent"],
            attendance_data["Total Student Count"],
        )

    attendance_data = attendance_data.drop(
        ["Students Chronically Absent", "Total Student Count"], axis=1
    )

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


# k8 academic data for single school
def get_proficiency_data(*args):
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


def get_corporation_academic_data(*args):
    keys = ["id", "type"]
    params = dict(zip(keys, args))

    if params["type"] == "hs" or params["type"] == "ahs":
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
                    WHERE SchoolID = :id)""".format(
            table
        )
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

    results = run_query(q, params)

    results = results.rename(columns={"Test Year": "Year"})

    return results


# NOTE: Using "SchoolTotal|ELATotalTested" as a proxy for school
# size for k8 schools.
def get_school_coordinates(*args):
    keys = ["year", "type"]
    params = dict(zip(keys, args))

    if params["type"] == "hs":
        q = text(
            """
            SELECT Lat, Lon, SchoolID, SchoolName, HighGrade, LowGrade
                FROM academic_data_hs 
                WHERE Year = :year
        """
        )
    elif params["type"] == "ahs":
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


# Where all the magic happens. Gets academic data and
# formats it for display. NOTE: This needs to be separated
# and refactored.
def get_academic_data(*args):
    """Where the magic happens. Gets academic data for school, geo school corporation,
    and comparable schools, if relevant, and formats it for tables and figs depending
    on the requesting page.

    Args:
    schools (list): list of school IDs
    type (str): school type ("k8","k12","hs","ahs")
    year (str): selected year
    page (str): page from which data is requested

    Returns:
        data: pd.DataFrame
    """
    keys = ["schools", "type"]

    params = dict(zip(keys, args))

    # if length of school_id is > 1, then we are pulling data for a list
    # of schools (academic_analysis), otherwise one school (academic_info and
    # academic_metric)
    if len(params["schools"]) > 1:
        school_str = ", ".join([str(int(v)) for v in params["schools"]])

    else:
        school_str = params["schools"][0]

    # Get data for academic_information and academic_metrics
    # all data / all years for school(s) and school corporation
    if params["type"] == "k8":
        school_table = "academic_data_k8"
    else:
        school_table = "academic_data_hs"

    query_string = """
        SELECT *
            FROM {}
            WHERE SchoolID IN ({})""".format(
        school_table, school_str
    )

    q = text(query_string)

    results = run_query(q, params)

    return results


# TODO: merge into get_academic_data() (currently only used
# TODO: in multiyear academic data) - unfortunately thats a lot of differences
# NOTE: Primary difference is multiyear data column names are school
# names and index is Year - values are proficiency. in get_academic_data,
# columns are YYYYSchool, YYYYN-Size, YYYYDiff, index is Category and
# values are proficiency, nsize, diff, and rating
def get_multiyear_data(*args):
    keys = ["school_id", "comp_list", "category", "year", "flag"]
    params = dict(zip(keys, args))

    if len(params["comp_list"]) >= 1:
        school_str = ", ".join([str(int(v)) for v in params["comp_list"]])
    else:
        school_str = params["school_id"]

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

    # TODO: Currently, the chart defaults to whatever category has data
    # TODO: if a year is selected where the category that is selected
    # TODO: has no data. Need to change this to show empty chart if
    # TODO: a category is selected with no data for a particular year.
    # TODO: I suspect this is in the navigation logic [DOH]

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

        # drop excluded years
        excluded_years = get_excluded_years(params["year"])

        if excluded_years:
            comparable_schools_data = comparable_schools_data[
                ~comparable_schools_data["Year"].isin(excluded_years)
            ]

        # NOTE: IPS keeps changing school names slightly. Which is irritating
        # when building chart traces. To ensure name consistency, we take
        # the school names from the most recent year and ensure that all other
        # School Name's same (matching on School ID)
        name_check = comparable_schools_data[
            comparable_schools_data["Year"] == int(params["year"])
        ][["School ID", "School Name"]]

        name_check = name_check.set_index("School ID")

        comparable_schools_data["School Name"] = comparable_schools_data[
            "School ID"
        ].map(name_check["School Name"])

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
            if school_type == "ahs":
                result = pd.merge(school_data, comparable_schools_data, on="Year")
            else:
                result = pd.merge(
                    pd.merge(school_data, corp_data, on="Year"),
                    comparable_schools_data,
                    on="Year",
                )

    return result, all_school_info
