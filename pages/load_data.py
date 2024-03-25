##############################################
# ICSB Dashboard - Database Queries (SQLite) #
##############################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     02/21/24

# NOTE: No K8 academic data exists for 2020

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

from .calculations import (
    calculate_percentage, conditional_fillna, calculate_proficiency,
    recalculate_total_proficiency, conditional_fillna, calculate_graduation_rate,
    calculate_sat_rate
)

from .process_data import transpose_data

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

    # NOTE: From 2016 - 2019  "SpringADM" & "FallADM"; beginning with
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

    # Each adm average requires 2 columns (Fall and Spring). If there are an
    # odd number of columns after the above drop, that means that the last
    # column is a Fall without a Spring, so we store that column, drop it,
    # and add it back later
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

    # change "***" to nan
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

    else:   # k8

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


# combination the above two functions
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


# Calculates AHS State Graduation Average for all Years as
# a substitute for corp_data
def get_ahs_averages():
    params = dict(id="")
    q = text (
        """
        SELECT *
            FROM academic_data_hs
            WHERE SchoolType = "AHS"
        """
    )

    results = run_query(q, params)

    drop_cols = ["School Name", "School Type", "Lat", "Lon"]
    results = results.drop(drop_cols, axis=1)

    non_sum_cols = ["Year", "School ID", "Corporation ID", "Corporation Name", "Low Grade", "High Grade"]
    sum_cols = [c for c in results.columns if c not in non_sum_cols]

    for col in sum_cols:
        results[col] = pd.to_numeric(results[col], errors="coerce")

    # create a dict for agg()
    column_map = {col: "first" for col in non_sum_cols}
    column_map2 = {col: "sum" for col in sum_cols}
    column_map3 = {"Attendance Rate": "mean"}
    group_cols = {**column_map, **column_map2, **column_map3}

    final_results = results.groupby(["Year"], as_index=False).agg(group_cols)
    
    final_results["Corporation Name"] = "AHS State Average"
    final_results["Corporation ID"] = 9999
    final_results["School ID"] = 9999

    final_results = final_results.sort_values(by="Year")

    return final_results


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
    attendance_data = attendance_data.replace(r"^\s*$", np.nan, regex=True)

    # Chronic Absenteeism isn't used for AHS
    if school_type != "corp_AHS" and school_type != "AHS":
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


# NOTE: "SchoolTotal|ELATotalTested" is a proxy for school
# size for k8 schools.
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


# filename99 = ("analysis-data.csv")
# analysis_data.to_csv(filename99, index=False)
    
# Where all the magic happens
# Gets all the academic data and formats it for display
def get_academic_data(*args):
    """Where the magic happens. Gets academic data for school, geo school corporation,
    and comparable schools, if relevant, and formats it for tables and figs depending
    on the requesting page.

    Args:
    schools (list): list of school IDs
    type (str): school type ("K8","K12","HS","AHS")
    year (str): selected year
    page (str): page from which data is requested

    Returns:
        data: pd.DataFrame
    """
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

    query_string = """
        SELECT *
            FROM {}
            WHERE SchoolID IN ({})""".format(
        school_table, school_str
    )

    q = text(query_string)
    
    school_data = run_query(q, params)

    # get corp data (for academic_metrics and academic_analysis_single_year)
    # and add to dataframe
    if params["type"] == "AHS":
        corp_data = get_ahs_averages()
    else:
        corp_data = get_corporation_academic_data(params["schools"][0], params["type"])

    # add columns not in corp database
    corp_data["School ID"] = corp_data["Corporation ID"]
    corp_data["School Name"] = corp_data["Corporation Name"]

    # merge - result includes school, school corp, and comparable schools if
    # multiple school ids in the schools variable
    raw_merged_data = pd.concat([school_data,corp_data],axis=0)

    # Drop years of data that have been excluded by the
    # selected year (are later than)
    excluded_years = get_excluded_years(params["year"])
    
    if excluded_years:
        raw_merged_data = raw_merged_data[~raw_merged_data["Year"].isin(excluded_years)]
 
    raw_merged_data = raw_merged_data.sort_values(by="Year", ascending=False)
    
    raw_merged_data = raw_merged_data.reset_index(drop=True)

    # Drop all columns for a Category if the value of "Total Tested" for
    # the Category for the school is null or 0 for the "school"
    drop_columns = []

    data = raw_merged_data.copy()

    # convert from float to str while dropping the decimal
    data["School ID"] = data["School ID"].astype("Int64").astype("str")
    data["Corporation ID"] = data["Corporation ID"].astype("Int64").astype("str")

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

    # process HS data
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

        # process additional AHS only data
        if params["type"] == "AHS":
            
            if "AHS|CCR" in processed_data.columns:
                processed_data["AHS|CCR"] = pd.to_numeric(processed_data["AHS|CCR"], errors="coerce")

            if "AHS|Grad All" in processed_data.columns:
                processed_data["AHS|Grad All"] = pd.to_numeric(
                    processed_data["AHS|Grad All"], errors="coerce"
                )

            if {"AHS|CCR", "AHS|Grad All"}.issubset(processed_data.columns):
                processed_data["CCR Percentage"] = processed_data["AHS|CCR"] / processed_data["AHS|Grad All"]
        
    # process K8 data
    elif params["type"] == "K8": 

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

    # if all columns in data other than the 1st (Year) are null
    # then return empty df

#TODO: Check this test - make better
    if processed_data.iloc[:, 1:].isna().all().all():
        
        return pd.DataFrame()

    else:

        ## data for academic_analysis_single_page
        ## TODO eventually add multipage analysis data
        if params["page"] == "analysis":

            if params["type"] == "HS" or params["type"] == "AHS":

                hs_data = processed_data.copy()

                analysis_data = hs_data.filter(
                    regex=r"School ID|School Name|Low Grade|High Grade|Corporation ID|Corporation Name|Graduation Rate$|Benchmark \%|^Year$",
                    axis=1,
                ).copy()

                analysis_data = analysis_data.drop(list(analysis_data.filter(regex="EBRW and Math")), axis=1)

                hs_cols = [c for c in analysis_data.columns if c not in ["School Name", "Corporation Name"]]

                # get index of rows where school_id matches selected school
                school_idx = analysis_data.index[analysis_data["School ID"] == school_id].tolist()[0]

                # force all to numeric (this removes "***" strings) - we
                # later use NaN as a proxy
                for col in hs_cols:
                    analysis_data[col] = pd.to_numeric(
                        analysis_data[col], errors="coerce"
                    )

                # drop all columns where the row at school_name_idx has a NaN value
                analysis_data = analysis_data.loc[:, ~hs_data.iloc[school_idx].isna()]                

                return analysis_data
            
            else:

                k8_data = processed_data.copy()
                
                analysis_data = k8_data.filter(
                    regex=r"\|ELA Proficient %$|\|Math Proficient %$|IREAD Proficient %|^Year$|Low|High|School Name|School ID|Corporation ID",
                    axis=1,
                )
                analysis_data = analysis_data.sort_values("Year").reset_index(drop=True)
                
                analysis_data = analysis_data[analysis_data.columns[~analysis_data.columns.str.contains(r"Female|Male")]]

                # filename77 = ("analysis_data1.csv")
                # analysis_data.to_csv(filename77, index=False)
                # filename77 = ("analysis_data2.csv")
                # analysis_data.to_csv(filename77, index=False)

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

                # one last check
                if (
                    (params["type"] == "K8" or params["type"] == "K12")
                    and len(analysis_data.index) > 0
                ) and check_for_unchartable_data.isnull().all().all() == True:
                    
                    analysis_data = pd.DataFrame()

                    return analysis_data
                
                else:

                     return analysis_data

        ## data for academic_information and academic_metrics pages
        elif params["page"] == "info" or params["page"] == "metrics":

            corp_data = processed_data[processed_data["School ID"] == processed_data["Corporation ID"]].copy()
            school_data = processed_data[processed_data["School ID"] == school_id].copy()

            # No corp_data is used and school_data limited to single metric (CCR)
            if params["type"] == "AHS" and params["page"] == "metrics":
                    
                # AHS metric data is extremely limited atm
                school_metric_data = school_data[["Year","AHS|CCR", "AHS|Grad All"]]

                return school_metric_data
            
            elif params["type"] == "HS":

                corp_data = processed_data[processed_data["School ID"] == processed_data["Corporation ID"]].copy()
                school_data = processed_data[processed_data["School ID"] == school_id].copy()

                school_metrics_data = transpose_data(school_data,params)
                corp_metrics_data = transpose_data(corp_data,params)

                # Remove N-Size columns from corp dataframe
                corp_metrics_data = corp_metrics_data.filter(regex=r"Category|Corp", axis=1)

                ## HS data for academic_information
                if params["page"] == "info":
                    return school_metrics_data
                
                else:
                    # add state graduation average to corp df
                    state_grad_average = get_graduation_data()

                    corp_metrics_data = pd.concat(
                        [
                            corp_metrics_data.reset_index(drop=True),
                            state_grad_average.reset_index(drop=True),
                        ],
                        axis=0,
                    ).reset_index(drop=True)

                    # for the school calculation we duplicate the school's Total
                    # Graduation rate values and rename the first column ("Category")
                    # to "State Grad Average" - for the corporation df, Total Graduation
                    # is equal to the Corp Average and State Grade Average is the
                    # Stat Average. So when the difference is calculated
                    # between the two data frames, Total Graduation Rate is the diff
                    # between school total and corp total and "State Average" is the
                    # diff between school total and state average

                    # for this to work, we need to make sure the school has a "Total
                    # Graduation Rate" Category- if is missing, we add a new row filled
                    # with nan (by enlargement)
                    if "Total|Graduation Rate" not in school_metrics_data["Category"].values:

                        school_metrics_data.loc[len(school_metrics_data)] = np.nan
                        
                        school_metrics_data.loc[
                            school_metrics_data.index[-1], "Category"
                        ] = "Total|Graduation Rate"

                    duplicate_row = school_metrics_data[
                        school_metrics_data["Category"] == "Total|Graduation Rate"
                    ].copy()

                    duplicate_row["Category"] = "State Graduation Average"

                    # NOTE: Need to declare an explicit type here because there is a
                    # bug in "pandas-stubs" that causes mypy to mark code as 
                    # "unreachable" following a pd.concat with Iterable[None]. See:
                    # https://stackoverflow.com/questions/78156640/why-is-visual-studio-code-saying-my-code-in-unreachable-after-using-the-pandas-c
                    # NOTE: trying and failing to suppress this warning by adding 
                    # 'disable_error_code = "annotation-unchecked"' to mypy.ini. but kept
                    # getting errors. So here it stays
                    # https://stackoverflow.com/questions/74578185/suppress-mypy-notes
                    merged_dataframes:list[pd.DataFrame] = [school_metrics_data, duplicate_row]
                    
                    school_metrics_data = pd.concat(merged_dataframes, axis=0, ignore_index=True)
                    
                    # Corp -State Grad Rate should equal State Grad Rate
                    # Corp - Total Grad Rate and Nonwaiver Grad Rate should equal corp totals
                    # School - Both State and Total Grad Rate should equal school total grad rate
                    # School - Nonwaiver = school

                    # calcs = School (Grad) - Corp (State) = State Grad Avg diff
                    #       = School (Grad) - Corp (Total) = Corp Grad Avg diff
                    #       = School (NonW) - Corp 

                    # add corp data to df
                    
                    corp_proficiency_cols = [col for col in corp_metrics_data.columns.to_list() if "Corp" in col]
                    merged_data = pd.concat([school_metrics_data, corp_metrics_data[corp_proficiency_cols]], axis=1)

                    # NOTE: at the moment HS metrics only include Total Graduation Rate,
                    # Non Waiver Graduation Rate, and State Graduation Average

                    # clean up and filter
                    merged_data = merged_data.replace({
                        "Total|Graduation Rate": "Total Graduation Rate",
                        "Non Waiver|Graduation Rate": "Non Waiver Graduation Rate"}, regex=False)

                    hs_categories =["Total Graduation Rate","Non Waiver Graduation Rate","State Graduation Average"]
                    metric_data = merged_data[merged_data["Category"].str.contains("|".join(hs_categories))]

                    metric_data = metric_data.reset_index(drop=True)

                    print(metric_data)
                    return metric_data

            else:

                school_info_data = processed_data[processed_data["School ID"] == school_id]
                final_school_data = transpose_data(school_info_data,params)

                # K8 information data
                if params["page"] == "info":
                    return final_school_data

                # TODO: Where does this belong? In the chart? or in academic_info.py
                # TODO: right before the information is sent to the chart? or in
                # TODO: the layout? 
                # result, no_data = check_for_no_data(result)
                # print(no_data)
                # insuf_string = check_for_insufficient_n_size(result)
                # print(insuf_string)

                # K8 academic_metrics data    
                else:

                    corp_info_data = processed_data[processed_data["School ID"] == processed_data["Corporation ID"]]

                    final_corp_data = transpose_data(corp_info_data,params)        


                    corp_proficiency_cols = [col for col in final_corp_data.columns.to_list() if "Corp" in col]
                    
                    # School Proficiency and N-Size and Corp Profiency
                    metric_data = pd.concat([final_school_data, final_corp_data[corp_proficiency_cols]], axis=1)

                    return metric_data

# TODO: Do we need a default on error?
    # return data

# TODO: Eventually merge into get_academic_data()
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