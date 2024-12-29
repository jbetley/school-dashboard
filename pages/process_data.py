#########################################
# ICSB Dashboard - Clean & Process Data #
#########################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.16
# date:     12/19/24

from typing import Tuple
import pandas as pd
import numpy as np
from toolz import interleave
import itertools
from functools import reduce
from dash import html

from .globals import (
    grades,
    ethnicity,
    subgroup,
)

from .load_data import (
    get_ilearn_student_data,
    get_iread_student_data,
    get_excluded_years,
    get_school_coordinates,
)

from .calculations import (
    calculate_proficiency_manually,
    round_percentages,
    check_for_gradespan_overlap,
    calculate_comparison_school_list,
)
from .string_helpers import reorder_columns, natural_keys


def create_comparison_dropdown_list(
        school_id: str, year: str, existing_list: list, school_type: str
    ) -> Tuple[list, str, list]:
    """
    given a dataframe with Years as columns, drops columns with all nan
    and returns the most recent year with data.

    Args:
    school_id (str): selected school_id
    year (str): selected year
    existing_list (list): a list of currently selected school ids for comparison
        schools (or [])
    school_type (str): k8 or hs
    
    Returns:
        Tuple[
        school_options (list):
        input_warning (str):
        comparison_schools (list):
        ]
    """       
    numeric_year = int(year)

    # School ID, School Name, Lat & Lon
    schools_by_distance = get_school_coordinates(numeric_year, school_type)

    # Drop any school not testing at least 20 students (k8 only- probably
    # impacts ~20 schools). Using "Total|ELATotalTested" as a proxy for school size
    # We want to include the selected school regardless of its n-size
    if school_type == "k8":
        schools_by_distance["Total|ELA Total Tested"] = pd.to_numeric(
            schools_by_distance["Total|ELA Total Tested"], errors="coerce"
        )
        schools_by_distance = schools_by_distance[
            (schools_by_distance["Total|ELA Total Tested"] >= 20)
            | (schools_by_distance["School ID"] == int(school_id))
        ]

    # There is some time cost for running the dropdown selection function
    # (typically ~0.8 - 1.2s), so we want to exit out as early as possible if we
    # know it isn't necessary because the selected school didn't exist
    if int(school_id) not in schools_by_distance["School ID"].values:
        return [], [], []

    else:
        # NOTE: Before we do the distance check, we reduce the size of the
        # df by removing schools where there is no or only one grade overlap
        # between the comparison schools. The variable "overlap" is one less
        # than the the number of grades that we want as a minimum (a value of
        # "1" means a 2 grade overlap, "2" means 3 grade overlap, etc.).

        # AHS don't have a 'gradespan' in the technical sense
        if school_type != "ahs":
            schools_by_distance = check_for_gradespan_overlap(
                school_id, schools_by_distance
            )

        num_schools_to_display = 30

        comparison_list = calculate_comparison_school_list(
            school_id, schools_by_distance, num_schools_to_display
        )

        new_comparison_schools = [
            {"label": name, "value": id} for name, id in comparison_list.items()
        ]

        # value for number of default display selections and maximum
        # display selections (because of zero indexing, max should be
        # 1 less than actual desired number)
        default_num_to_display = 4
        max_num_to_display = 7

        # used to display message if the number of selections exceeds the max
        input_warning = None

        # there are three occasions when we want to reset the list: 1) there are
        # no values (existing_comparison_schools_list = []); 2) there are values,
        # but none of the existing values overlap with the new values; 3) there
        # are values, and there is an overlap, but the number of overlapping
        # schools is less than the total number of existing schools.
        # (3) should only occur when we have a K12 school selected and are switching
        # between "K8" and "HS" types where there is another K12 school in the
        # comparable school list. Because the K12 school is in both lists- when
        # the user switches, it is the only school that will be displayed. We don't
        # want this, so we reset. NOTE: Probably easier to just reset K12 display
        # every time the type changes, but I'm not quite sure how to track that
        # (value vs. state?)

        # at this point "existing_comparison_schools_list" is either [] (for no
        # schools selected) or a list of currently selected schools.
        # "new_comparison_schools_list" is a list of all of the schools matching
        # the current selection (which is triggered by a change in type from K8 to HS)

        new_comparison_schools_list = [d["value"] for d in new_comparison_schools]

        # count the number of schools shared by the two lists
        overlap = 0

        if not existing_list:
            overlap = 0

        else:
            for sch in new_comparison_schools_list:
                overlap += existing_list.count(sch)

        if (
            not existing_list
            or existing_list
            and (
                # isdisjoint returns True if there are no common items between the sets
                # there is an existing list, but there is no overlap (e.g., K8 to HS)
                set(existing_list).isdisjoint(new_comparison_schools_list) == True
                or
                # there is an existing list, and there is overlap, but the number of overlapping
                # schools is less than the length of all of the existing schools
                (
                    set(existing_list).isdisjoint(new_comparison_schools_list) == False
                    and overlap < len(existing_list)
                )
            )
        ):
            # If any of these are true, we reset options and values
            comparison_schools = [
                d["value"] for d in new_comparison_schools[:default_num_to_display]
            ]
            school_options = new_comparison_schools

        else:
            # if none of the above cases apply, we first test the length of
            # the existing list to make sure it hasn't exceeded max display

            if len(existing_list) > max_num_to_display:
                # if it does, we throw a warning, keep the selected values the same
                # and disable all of the options
                input_warning = html.P(
                    id="single-year-input-warning",
                    children="Limit reached (Maximum of "
                    + str(max_num_to_display + 1)
                    + " schools).",
                )

                comparison_schools = existing_list

                school_options = [
                    {
                        "label": option["label"],
                        "value": option["value"],
                        "disabled": True,
                    }
                    for option in new_comparison_schools
                ]

            else:
                # if it doesn't, we return the selected list and options.
                comparison_schools = existing_list

                school_options = [
                    {
                        "label": option["label"],
                        "value": option["value"],
                        "disabled": False,
                    }
                    for option in new_comparison_schools
                ]

        return school_options, input_warning, comparison_schools


def find_valid_year(data: pd.DataFrame) -> str:
    """
    given a dataframe with Years as columns names, drops columns with all nan
    and returns the most recent year with data.

    Args:
    data (pd.DataFrame): academic data

    Returns:
        most_recent_year (str): a string value of most recent year in YYYY format
    """    
    # Networks typically do not have Quarterly data, so
    # we do a quick check of the selected year against
    # valid years of data
    valid_data = data.dropna(axis=1)
    valid_years = [
        e
        for e in valid_data.columns
        if e not in ("School ID", "Category", "School Name")
    ]
    valid_years.sort(reverse=True)
    most_recent_year = valid_years[0]

    return most_recent_year


def remove_empty_cols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove columns from dataframe that are all NaN, null, or None.

    Args:
    df (pd.DataFrame): academic data

    Returns:
        data (pd.DataFrame): df with NaN, null, or None columns removed
    """
    data = df.copy()

    data = data.loc[
        :,
        ~data.where(data.astype(bool)).isna().all(axis=0),
    ]

    data = data.loc[:, ~(data.astype(str) == "None").all()]

    return data


def check_total_tested(
    df: pd.DataFrame, school_id: str, school_type: str
) -> pd.DataFrame:
    """
    Drop all columns for a Category if the value of "Total Tested" for
    the Category for the school is null or 0.
    NOTE: This is essentially the same as the check in "Calculate
    Proficiency"- at some point should combine.

    Args:
    raw_df (pd.DataFrame): academic data
    school_id (str): the SchoolID
    school_type (str): the school type

    Returns:
        data (pd.DataFrame): df with null/0 categories removed
    """
    drop_columns = []

    data = df.copy()

    data["School ID"] = data["School ID"].astype("Int64").astype("str")
    data["Corporation ID"] = data["Corporation ID"].astype("Int64").astype("str")

    if school_type == "k8":
        tested_cols = [
            col
            for col in data.columns.to_list()
            if "Total Tested" in col or "Test N" in col
        ]
    else:
        tested_cols = [
            col
            for col in data.columns.to_list()
            if "Total Tested" in col or "Cohort Count" in col
        ]

    for col in tested_cols:
        if (
            pd.to_numeric(
                data[data["School ID"] == school_id][col], errors="coerce"
            ).sum()
            == 0
            or data[data["School ID"] == school_id][col].isnull().all()
        ):
            if "Total Tested" in col:
                match_string = " Total Tested"
            else:
                if school_type == "k8":
                    match_string = " Test N"
                else:
                    match_string = "|Cohort Count"

            matching_cols = data.columns[
                pd.Series(data.columns).str.startswith(col.split(match_string)[0])
            ]

            drop_columns.append(matching_cols.tolist())

    drop_all = [i for sub_list in drop_columns for i in sub_list]

    data = data.drop(drop_all, axis=1).copy()

    data = data.reset_index(drop=True)

    return data


def transpose_data(raw_df: pd.DataFrame, school_type: str) -> pd.DataFrame:
    """
    Filters tested (nsize) cols and proficiency calculations into
    separate dataframes, performs some cleanup, including a transposition,
    moving years to column headers and listing categories in their own
    columns and then cross-merging the two. variables change depending on
    whether we are analyzing a school or a corporation

    Args:
    raw_df (pd.DataFrame): student level growth data
    school_type (str): the school type


    Returns:
        final_data (pd.DataFrame): processed and transposed dataframe
    """

    df = raw_df.copy()

    df = df.reset_index(drop=True)

    # First, determine whether df contains data for the charter school or
    # the geo school corporation. A school corporation will always have the
    # same School and Corporation Name and School and Corporation ID.
    # a charter school that is not part of a network will have the same
    # School and Corporation Name, but different School and Corporation IDs.
    # a charter school that IS part of a network may have the same or different
    # School and Corporation ID, but will have a different School and Corporation
    # Name. So we check whether the two sets of columns are equivalent and if
    # both are, the data must belong to a school corporation.
    if (
        (df["School ID"][0] == df["Corporation ID"][0])
        + (df["School Name"][0] == df["Corporation Name"][0])
    ) == 2:
        # NOTE: currently keeping record of N-Size data for both school and corp
        # although we do not currently use corp n-size
        nsize_id = "CN-Size"
        name_id = "Corp"
    else:
        nsize_id = "SN-Size"
        name_id = "School"

    # create dataframes with N-Size data for info/analysis pages
    if school_type == "ahs":
        # Three Graduation Rate measurements for AHS:
        #   Graduation to Enrollment =  AHS|Actual Graduates/ADM Average
        #   Grade 12 = AHS|Actual Graduates/AHS|Actual Enrollment
        #   Total (Cohort) = Total|Graduates/Total|Cohort Count

        # NOTE: CCR Percentage uses "|Count", grad rates use "|Cohort Count", SAT uses "Total Tested"
        tested_cols = "Total Tested|Cohort Count|Count|Year"
        filter_cols = r"^Category|CCR Percentage|Grade 12\|Graduation Rate|Total\|Graduation Rate|ADM Average|Graduation to Enrollment\|Graduation Rate|Benchmark \%|Below|Approaching|At|^Year$"
        substring_dict = {
            " Total Tested": "",
            "\|Cohort Count": "|Graduation",
            "\|Count": "",
        }

    elif school_type == "hs":
        tested_cols = "Total Tested|Cohort Count|Year"
        filter_cols = r"^Category|Graduation Rate$|AHS|Pass Rate$|Benchmark %|Below|Approaching|At|^Year$"
        substring_dict = {" Total Tested": "", "\|Cohort Count": "|Graduation"}

    else:
        tested_cols = "Total Tested|Test N|Year"
        filter_cols = r"School ID|Corporation ID|Corporation Name|Low Grade|High Grade|\|ELA Proficient %$|\|Math Proficient %$|IREAD Proficient %|^Year$"
        substring_dict = {" Total Tested": "", " Test N": ""}

    # We get proficiency and cohort/tested (N-Size) data in separate dataframes,
    # convert the n-size category names into a substring of the data category
    # names and then merge the two dataframes based on a substring match
    # e.g., use the substring dict to convert "Graduation to Enrollment|Cohort Count" to
    # the substring "Graduation to Enrollment|Graduation" which matches "Graduation to Enrollment|Graduation Rate"
    df.columns = df.columns.astype(str)

    tested_data = df.filter(regex=tested_cols, axis=1).copy()
    proficiency_data = df.filter(regex=filter_cols, axis=1).copy()

    tested_data = (
        tested_data.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    tested_data = tested_data.rename(
        columns={
            c: str(c) + nsize_id for c in tested_data.columns if c not in ["Category"]
        }
    )

    tested_data = tested_data.fillna(value=np.nan)
    tested_data = tested_data.replace(0, np.nan)

    if tested_data.empty:
        return tested_data

    # add new column with substring values and drop the original
    # Category column
    tested_data["Substring"] = tested_data["Category"].replace(
        substring_dict, regex=True
    )

    tested_data = tested_data.drop("Category", axis=1)

    proficiency_data = (
        proficiency_data.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    proficiency_data = proficiency_data.rename(
        columns={
            c: str(c) + name_id
            for c in proficiency_data.columns
            if c not in ["Category"]
        }
    )

    proficiency_data = proficiency_data.reset_index(drop=True)

    # temporarily store Low/High grade cols for K8
    if school_type == "k8":
        other_rows = proficiency_data[
            proficiency_data["Category"].str.contains(r"Low|High")
        ]

    proficiency_data = proficiency_data.fillna(value=np.nan)

    # Merge Total Tested DF with Proficiency DF based on substring match
    # NOTE: the cross-merge and substring match process takes about .3s,
    # is there a faster way?
    merged_data = proficiency_data.merge(tested_data, how="cross")

    # Need to temporarily rename "English Learner" because otherwise merge
    # will match both "English" and "Non English"
    merged_data = merged_data.replace(
        {
            "Non English Language Learners": "Temp1",
            "English Language Learners": "Temp2",
        },
        regex=True,
    )

    merged_data = merged_data[
        [a in b for a, b in zip(merged_data["Substring"], merged_data["Category"])]
    ]

    merged_data = merged_data.replace(
        {
            "Temp1": "Non English Language Learners",
            "Temp2": "English Language Learners",
        },
        regex=True,
    )

    merged_data = merged_data.drop("Substring", axis=1)
    merged_data = merged_data.reset_index(drop=True)

    # reorder and interleave columns
    final_cols = reorder_columns(merged_data, [name_id, nsize_id])

    final_data = merged_data[final_cols]

    # Add Low and High Grade rows back to k8 data and
    # create df for information figs
    if school_type == "k8":
        final_data = pd.concat(
            [final_data.reset_index(drop=True), other_rows.reset_index(drop=True)],
            axis=0,
        ).reset_index(drop=True)

    return final_data


def process_growth_data(
    df: pd.DataFrame, category: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process a dataframe with student levelgrowth data into two dataframes with
    aggregated data using both Majority Enrolled (ME) and 162-Day counts. primary
    difference between dataframes is table data has been pivoted from long to
    wide.

    Args:
    data (pd.DataFrame): student level growth data
    category (str): the category being processed

    Returns:
        table_data (pd.DataFrame): processed dataframe used to create table
        fig_data (pd.DataFrame): processed dataframe used to create fig
    """
    data = df.copy()

    # get nsize for each group
    nsize = data.value_counts(subset=["Year", category, "Subject"])
    nsize_df = nsize.reset_index()

    nsize_df.columns = ["Year", category, "Subject", "NSize"]

    # find the percentage of students with Adequate growth using
    # "Majority Enrolled" students- grouby by relevant categories and
    # count the values in the "ILEARNGrowth Level" column (normalize
    # gives us the relative frequencies (%) of the values)
    data = (
        data.groupby(["Year", category, "Subject"])["ILEARNGrowth Level"]
        .value_counts(normalize=True)
        .reset_index(name="Majority Enrolled")
    )

    # If the frequency of "Not Adequate Growth" == 1.0: then all values for that
    # category and subject were Not Adequate (e.g., 100% of the students in that
    # category were Not Adequate), meaning that 0% of students had adequate growth.
    # So wherever "Not Adequate Growth" == 1.0, we change "ILEARNGrowth Level" to
    # "Adequate Growth" and Majority Enrolled to 0 (otherwise these values would
    # disappear when we get rid of the "ILEARNGrowth Level" column)
    mask = data["Majority Enrolled"] == 1.0
    data.loc[mask, "ILEARNGrowth Level"] = "Adequate Growth"
    data.loc[mask, "Majority Enrolled"] = 0

    # drop all rows with "Not Adequate"
    data = data[data["ILEARNGrowth Level"].str.contains("Not Adequate") == False]

    # merge n-size values
    merged_data = pd.merge(
        data,
        nsize_df[["Year", category, "Subject", "NSize"]],
        on=["Year", category, "Subject"],
        how="left",
    )

    # create final category
    merged_data["Category"] = merged_data[category] + "|" + merged_data["Subject"]

    # filter unneeded columns
    final_data = merged_data.filter(
        regex=r"Year|Category|Majority Enrolled|NSize",
        axis=1,
    )

    # NOTE: Occasionally, the data will have an "Unknown" Category. No idea
    # why, but we need to get rid of it - easiest way would be to just drop
    # any Categories matching "Unknown", but that won't stop other random
    # Categories from getting through. So instead, we drop any Categories
    # that don't match categories in the respective list

    if category == "Grade Level":
        final_data = final_data[final_data["Category"].str.contains("|".join(grades))]

    elif category == "Ethnicity":
        final_data = final_data[
            final_data["Category"].str.contains("|".join(ethnicity))
        ]

    elif (
        category == "Socioeconomic Status"
        or category == "English Learner Status"
        or category == "Special Education Status"
    ):
        final_data = final_data[final_data["Category"].str.contains("|".join(subgroup))]

    # create fig data
    fig_data = final_data.drop("NSize", axis=1).copy()

    fig_data = fig_data.pivot(index=["Year"], columns="Category")
    fig_data.columns = fig_data.columns.map(lambda x: "_".join(map(str, x)))

    # create table data
    table_data = final_data.copy()

    # pivot df from wide to long" add years to each column name; move year to
    # front of column name; sort and reset_index
    table_data = table_data.pivot(index=["Category"], columns="Year")
    table_data.columns = table_data.columns.map(lambda x: "".join(map(str, x)))
    table_data.columns = table_data.columns.map(lambda x: x[-4:] + x[:-4])

    table_data = table_data.reset_index()

    return fig_data, table_data


def process_discipline_data(
    df: pd.DataFrame, category: str, demographic: str
) -> pd.DataFrame:
    """
    Drop all columns for a Category if the value of "Total Tested" for
    the Category for the school is null or 0.

    Args:
    raw_df (pd.DataFrame): academic data
    school_id (str): the SchoolID
    school_type (str): the school type

    Returns:
        data (pd.DataFrame): df with null/0 categories removed
    """

    data = df.copy()

    isOverall = False

    if demographic == "Overall":
        isOverall = True

    # annoyingly, there are two cases in which str.contains grabs two "categories"
    # instead of 1: "Homeless" also returns "Not Homeless" and "English Language Learner"
    # also returns "Non English Language Learner"- so we need to test and drop
    if category == "Homeless" or category == "English Language Learner":
        data = data[data.columns[~data.columns.str.contains(r"Not|Non")]]

    # The columns:

    # "Year"

    # e.g., In School Suspension|Male
    selected_category = category + "|" + demographic

    total_students = "Total Unique Students|Overall"

    # e.g., In School Suspension Unique Students|Male
    selected_category_unique = category + " Unique Students|" + demographic

    # e.g., Total Unique Students|Male
    category_students_unique = "Total Unique Students|" + demographic

    # e.g., In School Suspension (% of All Students)
    percentage_of_total = category + " (% of All Students)"

    # e.g., In School Suspension (% of Male Students)
    percentage_of_category = category + " (% of " + demographic + " Students)"

    # the "Overall" category is treated differently because it
    # doesn't have a separate Unique N-Size
    if isOverall:
        data[percentage_of_total] = data[selected_category_unique].div(
            data[total_students], axis=0
        )

    else:
        data[percentage_of_total] = data[selected_category_unique].div(
            data[total_students], axis=0
        )

        # percentage of the specific demographic (e.g., Male) that have
        # experienced and incident for a category
        data[percentage_of_category] = data[selected_category_unique].div(
            data[category_students_unique], axis=0
        )

    data = data.sort_values(by=["Year"], ascending=True)

    # All demographic categories have result_total, nsize_overall,
    # selected_category_unique, and selected category

    # e.g., In School Suspension (% of All Students)
    result_total = data[["Year", percentage_of_total]].copy()

    result_total_T = (
        result_total.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    # e.g., Total Unique Students|Overall
    nsize_overall = data[["Year", total_students]].copy()

    nsize_overall_T = (
        nsize_overall.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    nsize_overall_T = nsize_overall_T.drop("Category", axis=1)
    nsize_overall_T = nsize_overall_T.add_suffix("N-Size")

    # e.g., In School Suspension|Overall
    category_total = data[["Year", selected_category]].copy()

    category_total_T = (
        category_total.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    # e.g., In School Suspension Unique Students|Overall
    category_total_unique = data[["Year", selected_category_unique]].copy()

    category_total_unique_T = (
        category_total_unique.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    if isOverall:
        # temporarily store this to re-add after merge
        category_col = result_total_T["Category"]

        result_total_T = result_total_T.drop("Category", axis=1)
        result_total_T = result_total_T.add_suffix("School")

        category_total_T = category_total_T.drop("Category", axis=1)
        category_total_T = category_total_T.add_suffix("Incidents")

        category_total_unique_T = category_total_unique_T.drop("Category", axis=1)
        category_total_unique_T = category_total_unique_T.add_suffix(
            "Incidents (Unique)"
        )

        merged_data = pd.concat(
            [
                category_total_T,
                category_total_unique_T,
                result_total_T,
                nsize_overall_T,
            ],
            axis=1,
        )[
            list(
                interleave(
                    [
                        category_total_T,
                        category_total_unique_T,
                        result_total_T,
                        nsize_overall_T,
                    ]
                )
            )
        ]

    # all other demographic categories
    else:
        # isOverall will only have one row of data, everything else
        # will have two, so we need to duplicate this for each row.
        dupe_category_total_T = category_total_T.reindex(
            category_total_T.index.append(
                category_total_T.index[
                    category_total_T["Category"] == selected_category
                ]
            )
        ).sort_index()

        dupe_category_total_T = dupe_category_total_T.drop("Category", axis=1)
        dupe_category_total_T = dupe_category_total_T.add_suffix("Incidents")

        # duplicate row
        dupe_category_total_unique_T = category_total_unique_T.reindex(
            category_total_unique_T.index.append(
                category_total_unique_T.index[
                    category_total_unique_T["Category"] == selected_category_unique
                ]
            )
        ).sort_index()

        dupe_category_total_unique_T = dupe_category_total_unique_T.drop(
            "Category", axis=1
        )
        dupe_category_total_unique_T = dupe_category_total_unique_T.add_suffix(
            "Incidents (Unique)"
        )

        # In School Suspension (% of Male Students)
        results_category = data[["Year", percentage_of_category]].copy()

        results_category_T = (
            results_category.set_index("Year")
            .T.rename_axis("Category")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        # Total Unique Students|Male
        nsize_category = data[["Year", category_students_unique]].copy()

        nsize_category_T = (
            nsize_category.set_index("Year")
            .T.rename_axis("Category")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        nsize_category_T = nsize_category_T.drop("Category", axis=1)
        nsize_category_T = nsize_category_T.add_suffix("N-Size")

        # concatenate vertically
        results_final = pd.concat([result_total_T, results_category_T], axis=0)
        nsize_final = pd.concat([nsize_overall_T, nsize_category_T], axis=0)

        category_col = results_final["Category"]
        results_final = results_final.drop("Category", axis=1)
        results_final = results_final.add_suffix("School")

        merged_data = pd.concat(
            [
                dupe_category_total_T,
                dupe_category_total_unique_T,
                results_final,
                nsize_final,
            ],
            axis=1,
        )[
            list(
                interleave(
                    [
                        dupe_category_total_T,
                        dupe_category_total_unique_T,
                        results_final,
                        nsize_final,
                    ]
                )
            )
        ]

    merged_data.insert(0, "Category", category_col)

    return merged_data


def process_student_level_ilearn(
    school_id: str, subject: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads and processes student level data to create the average ELA
    and Math proficiency of students Passing and not Passing IREAD.

    Args:
    school_id (str): the SchoolID
    subject (str): "ELA" or "Math

    Returns:
        data (Tuple[pd.DataFrame, pd.DataFrame]): two dataframes Pass and No-Pass
    """
    ilearn_student_all = get_ilearn_student_data(school_id)

    # will also be empty for guest schools
    if ilearn_student_all.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )  # iread_ilearn_pass_final, iread_ilearn_nopass_final

    else:
        iread_student_data = get_iread_student_data(school_id)

        ilearn_filtered = ilearn_student_all.filter(
            regex=rf"STN|Current Grade|Tested Grade|{subject}"
        )

        ilearn_filtered = ilearn_filtered.rename(
            columns={
                "Current Grade": "ILEARN Current Grade",
                "Tested Grade": "ILEARN Tested Grade",
            }
        )
        iread_student_data = iread_student_data.rename(columns={"Year": "Test Year"})
        ilearn_filtered["STN"] = ilearn_filtered["STN"].astype(str)

        school_all_student_data = pd.merge(
            iread_student_data, ilearn_filtered, on="STN"
        )

        category = subject + " Proficiency"

        school_all_student_data = school_all_student_data[
            [
                "Test Year",
                "STN",
                "Tested Grade",
                "Status",
                "Exemption Status",
                "ILEARN Tested Grade",
                category,
            ]
        ]

        all_student_data_nopass = school_all_student_data[
            school_all_student_data["Status"] == "Did Not Pass"
        ]
        all_student_data_pass = school_all_student_data[
            school_all_student_data["Status"] == "Pass"
        ]

        pass_proficiency = (
            all_student_data_pass.groupby(by="Test Year")[category]
            .apply(calculate_proficiency_manually)
            .reset_index(name="Proficiency")
        )
        nopass_proficiency = (
            all_student_data_nopass.groupby(by="Test Year")[category]
            .apply(calculate_proficiency_manually)
            .reset_index(name="Proficiency")
        )

        nopass_nsize = (
            all_student_data_nopass["Test Year"]
            .value_counts()
            .reset_index(name="N-Size")
            .rename(columns={"index": "Test Year"})
        )
        pass_nsize = (
            all_student_data_pass["Test Year"]
            .value_counts()
            .reset_index(name="N-Size")
            .rename(columns={"index": "Test Year"})
        )

        iread_ilearn_pass_final = pd.merge(pass_proficiency, pass_nsize, on="Test Year")
        iread_ilearn_nopass_final = pd.merge(
            nopass_proficiency, nopass_nsize, on="Test Year"
        )

        pass_column_name = "Avg. " + subject + " Proficiency - Students Passing IREAD"
        iread_ilearn_pass_final = iread_ilearn_pass_final.rename(
            columns={
                "Proficiency": pass_column_name,
                "Test Year": "Year",
                "N-Size": "N-Size (Pass IREAD)",
            }
        )

        nopass_column_name = (
            "Avg. " + subject + " Proficiency - Students not Passing IREAD"
        )
        iread_ilearn_nopass_final = iread_ilearn_nopass_final.rename(
            columns={
                "Proficiency": nopass_column_name,
                "Test Year": "Year",
                "N-Size": "N-Size (Did Not Pass IREAD)",
            }
        )

        iread_ilearn_pass_final["Year"] = iread_ilearn_pass_final["Year"].astype(str)
        iread_ilearn_nopass_final["Year"] = iread_ilearn_nopass_final["Year"].astype(
            str
        )

        return iread_ilearn_pass_final, iread_ilearn_nopass_final


def process_2yr_ilearn_data(df: pd.DataFrame, year: str) -> pd.DataFrame:
    """
    Take a dataframe with ilearn proficiency data and calculates the
    proficiency of students who have been with the selected school for
    at least two years.

    Args:
    df (pd.DataFrame): ilearn proficiency data
    year (str): selected year

    Returns:
        final_data (pd.DataFrame): processed dataframe
    """

    data = df.copy()

    data = data[
        (data["ELA Proficiency"] != "Did Not Test")
        & (data["Math Proficiency"] != "Did Not Test")
    ]

    # sort by STN and Year and then shift STN up one - this shifts the
    # previous year STN up - so any row with matching STN's is a row where
    # the same student has been at the school for at least 2 years.
    data = data.sort_values(["STN", "Year"], ascending=[True, False])

    data["STN_shift"] = data["STN"].shift(-1)

    # Raw df also includes scale scores- which we aren't using here
    filtered_data = data.filter(
        regex=rf"Year|School ID|STN|STN_shift|ELA Proficiency|Math Proficiency"
    ).copy()

    filtered_data = filtered_data[filtered_data["STN"] == filtered_data["STN_shift"]]

    # NOTE: Not currently breaking down by proficiency category, so we change
    # "Above Proficiency" to "At Proficiency" to get final percentage of all
    # students who passed
    filtered_data = filtered_data.replace(
        {"Above Proficiency": "At Proficiency"}, regex=True
    )

    #  Calculate N-Size and Proficiency Percentage
    ela_data = (
        filtered_data.groupby("Year")["ELA Proficiency"]
        .value_counts()
        .reset_index(name="SN-Size")
    )
    ela_proficiency = (
        filtered_data.groupby("Year")["ELA Proficiency"]
        .value_counts(normalize=True)
        .reset_index(name="School")
    )
    ela_data["School"] = ela_proficiency["School"]

    ela_data = ela_data[(ela_data["ELA Proficiency"] == "At Proficiency")]

    ela_data = ela_data.replace({"At Proficiency": "ELA Proficiency"}, regex=True)
    ela_data = ela_data.rename(columns={"ELA Proficiency": "Proficiency"})

    math_data = (
        filtered_data.groupby("Year")["Math Proficiency"]
        .value_counts()
        .reset_index(name="SN-Size")
    )
    math_proficiency = (
        filtered_data.groupby("Year")["Math Proficiency"]
        .value_counts(normalize=True)
        .reset_index(name="School")
    )
    math_data["School"] = math_proficiency["School"]

    math_data = math_data[(math_data["Math Proficiency"] == "At Proficiency")]

    math_data = math_data.replace({"At Proficiency": "Math Proficiency"}, regex=True)
    math_data = math_data.rename(columns={"Math Proficiency": "Proficiency"})

    # merge
    merged_data = pd.concat([ela_data, math_data], axis=0)

    # drop excluded years
    excluded_years = get_excluded_years(year)

    if excluded_years:
        merged_data = merged_data[~merged_data["Year"].isin(excluded_years)]

    # reshape
    data_pivot = merged_data.pivot(
        index="Proficiency", columns="Year", values=["SN-Size", "School"]
    )
    data_pivot.columns = [f"{y}{x}" for x, y in data_pivot.columns.to_flat_index()]
    data_pivot = data_pivot.reset_index()
    data_pivot = data_pivot.rename(columns={"Proficiency": "Category"})

    data_pivot.loc[
        data_pivot["Category"] == "ELA Proficiency",
        "Category",
    ] = "1.4.e. Two year student proficiency in ELA."

    data_pivot.loc[
        data_pivot["Category"] == "Math Proficiency",
        "Category",
    ] = "1.4.f. Two year student proficiency in Math."

    # reorder and interleave columns
    final_cols = reorder_columns(data_pivot, ["School", "SN-Size"])

    final_data = data_pivot[final_cols]

    return final_data


def process_stacked_bar(
    df: pd.DataFrame,
    categories: list,
    subject: list,
    proficiency_rating: list,
    year: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Processes ilearn proficiency data to create 100% stacked bar charts for each
    category and subject. Also creates an "annotations" dataframe with missing
    and insufficient data by category.

    Args:
    df (pd.DataFrame): ilearn proficiency data
    categories (list): list of proficiency Categories
    subject (list): "ELA" & "Math
    proficiency_rating (list): list of proficiency ratings
    year (str): the selected year
    Returns:
        data (Tuple[pd.DataFrame, pd.DataFrame]): a dataframe of processed ILEARN proficiency
            data and a dataframe of "annotations"
    """
    data = df.copy()

    proficency_data = data.loc[data["Year"] == year].copy()

    proficency_data = proficency_data.dropna(axis=1)
    proficency_data = proficency_data.reset_index()

    for col in proficency_data.columns:
        proficency_data[col] = pd.to_numeric(proficency_data[col], errors="coerce")

    # this keeps ELA and Math as well, which we drop later
    proficency_data = proficency_data.filter(
        regex=r"ELA Below|ELA At|ELA Approaching|ELA Above|ELA Total|Math Below|Math At|Math Approaching|Math Above|Math Total",
        axis=1,
    )

    # create dataframe to hold fig annotations
    annotations = pd.DataFrame(columns=["Category", "Total Tested"])

    for c in categories:
        for s in subject:
            category_subject = c + "|" + s
            proficiency_columns = [
                category_subject + " " + x for x in proficiency_rating
            ]
            total_tested = category_subject + " " + "Total Tested"

            # We do not want categories that do not appear in the dataframe to
            # appear in a chart. However, we also do not want to lose sight of
            # critical data because of the way that IDOE determines insufficient
            # N-Size. There are three possible data configurations for each column:
            # 1) Total Tested > 0 and the sum of proficiency_rating(s) is > 0: the school
            #    has tested category and there is publicly available data [display]
            # 2) Total Tested AND sum of proficiency_rating(s) == 0: the school does not
            #    have data for the tested category [do not display, but 'may' want
            #    annotation as "Missing"]
            # 3) Total Tested > 0 and the sum of proficiency_rating(s) are == "NaN": the
            #    school has tested category but there is no publicly available data
            #    [do not display, but 'may' want annotation as "Insufficient N-size"

            # Neither (2) or (3) permit the creation of a valid or meaningful chart.
            # However, we do want to track which Category/Subject combinations meet
            # either condition (for figure annotation purposes).

            if total_tested in proficency_data.columns:
                # The following is true if: 1) there are any NaN values in the set
                # (one or more '***) or 2) the sum of all values is equal to 0 (no
                # data) or 0.0 (NaN's converted from '***' meaning insufficient data)
                # Can tell whether the annotation reflects insufficient n-size or
                # missing data by the value in Total Tested (will be 0 for missing)
                if (proficency_data[proficiency_columns].isna().sum().sum() > 0) or (
                    proficency_data[proficiency_columns].iloc[0].sum() == 0
                ):
                    # add the category and value of Total Tested to a df
                    annotation_category = proficiency_columns[0].split("|")[0]
                    annotations.loc[len(annotations.index)] = [
                        annotation_category + "|" + s,
                        proficency_data[total_tested].values[0],
                    ]

                    # clean up numbers and replace NaN with "None"
                    annotations["Total Tested"] = annotations["Total Tested"].fillna(0)
                    annotations["Total Tested"] = annotations["Total Tested"].astype(
                        int
                    )

                    # drop any columns in the (non-chartable) category from the df
                    all_proficiency_columns = proficiency_columns + [total_tested]

                    proficency_data = proficency_data.drop(
                        all_proficiency_columns, axis=1
                    )

                else:
                    # calculate percentage
                    proficency_data[proficiency_columns] = proficency_data[
                        proficiency_columns
                    ].divide(proficency_data[total_tested], axis="index")

                    # get a list of all values
                    row_list = proficency_data[proficiency_columns].values.tolist()

                    # round percentages using Largest Remainder Method
                    # to build the 100% stacked bar chart
                    rounded = round_percentages(row_list[0])

                    # add back to dataframe
                    rounded_percentages = pd.DataFrame([rounded])
                    rounded_percentages_cols = list(rounded_percentages.columns)
                    proficency_data[proficiency_columns] = rounded_percentages[
                        rounded_percentages_cols
                    ]

    return proficency_data, annotations


def process_iread_student_data(
    df_student: pd.DataFrame, iread_total: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Processes student level iread data and returns two dataframes for a
    plotly dash datatable and a plotly dash fig.

    Args:
    df_student (pd.DataFrame): student-level ilearn proficiency data
    iread_total (pd.DataFrame): total iread proficiency for school
    Returns:
        data (Tuple[pd.DataFrame, pd.DataFrame]): a dataframe of processed student level
         ilearn data for table and fig.
    """
    student_data = df_student.copy()

    # Group by Year and Period - get percentage passing and not passing
    student_pass = (
        student_data.groupby(["Year", "Test Period"])["Status"]
        .value_counts(normalize=True)
        .reset_index(name="Percent")
    )

    # There are potentially six rows for each year: 1) Spring Pass;
    # 2) Spring Did Not Pass; 3) Spring No Result; 4) Summer Pass;
    # 5) Summer Did Not Pass; 6) Summer No Result. However, if, for example,
    # all students were either Pass or Did Not Pass, the opposite row will
    # be missing- e.g., if all students Did Not Pass, there will not be a Pass
    # row for that year and period

    # The solution is to use pd.MultiIndex.from_product. This makes a MultiIndex
    # from the cartesian product of multiple iterables. That is, we get a multindex
    # of all possible combinations from columns by index.levels (in this case, "Year"
    # "Test Period", and "Status" passed to .reindex. Will get a ValueError: "cannot
    # handle a non-unique multi-index" when there are duplicated pairs in the passed
    # columns, so we remove any duplicates first.
    student_mask = student_pass.duplicated(["Year", "Test Period", "Status"])

    student_pass = student_pass[~student_mask].set_index(
        ["Year", "Test Period", "Status"]
    )

    student_pass = (
        student_pass.reindex(pd.MultiIndex.from_product(student_pass.index.levels))
        .fillna({"Test Period": "Summer", "Percent": 0})
        .reset_index()
    )

    # Filter to remove everything but Passing Students
    student_pass = student_pass[student_pass["Status"].str.startswith("Pass")]

    # Get count (nsize) for total # of Students Tested per year and period
    student_tested = (
        student_data.groupby(["Year", "Test Period"])["Status"]
        .count()
        .reset_index(name="N-Size")
    )

    # pivot to get Test Period as Column Name and Year as col value
    student_tested = (
        student_tested.pivot_table(
            index=["Year"], columns="Test Period", values="N-Size"
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )

    student_tested = student_tested.rename(
        columns={"Spring": "Spring N-Size", "Summer": "Summer N-Size"}
    )

    student_pass = student_pass.drop(["Status"], axis=1)

    final_student_pass = (
        student_pass.pivot_table(
            index=["Year"], columns="Test Period", values="Percent"
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )

    final_student_pass = final_student_pass.rename(
        columns={"Spring": "Spring Pass %", "Summer": "Summer Pass %"}
    )

    # merge student level data with school total
    iread_total = iread_total.filter(regex=r"School", axis=1).reset_index(drop=True)

    iread_total = iread_total.T.rename_axis("Year").reset_index()

    iread_total = iread_total.rename(columns={0: "Total|IREAD"})

    iread_total["Year"] = iread_total["Year"].str[:4]

    # IREAD Details fig
    final_fig_data = pd.merge(final_student_pass, iread_total, on=["Year"])

    final_fig_data = final_fig_data.rename(
        columns={
            "Total|IREAD": "School Total",
        }
    )

    # IREAD Details table
    table_data = final_fig_data.copy()

    # Combine passing and tested students
    table_data = table_data.merge(student_tested, on="Year", how="inner")

    table_cols = table_data.columns.tolist()

    # reorder columns (move "Total" to the end and then swap places of
    # "Summer" and "Spring N-Size")
    table_cols.append(table_cols.pop(table_cols.index("School Total")))
    table_cols[2], table_cols[-3] = (
        table_cols[-3],
        table_cols[2],
    )

    table_data = table_data[table_cols]

    # Other IREAD data
    if table_data.empty:
        final_fig_data = pd.DataFrame()
        final_table_data = pd.DataFrame()

    else:
        # Number of 2nd Graders Tested and 2nd Grader Proficiency
        grade2_count = student_data[student_data["Tested Grade"] == "Grade 2"]

        grade2_tested = (
            grade2_count.groupby(["Year", "Test Period", "Status"])["Tested Grade"]
            .value_counts()
            .reset_index(name="2nd Graders Tested")
        )

        grade2_proficiency = (
            grade2_count.groupby(["Year", "Test Period"])["Status"]
            .value_counts(normalize=True)
            .reset_index(name="2nd Graders Proficiency")
        )

        # Number of Exemptions Granted for Non-Pass Students
        exemption_count = student_data[student_data["Exemption Status"] == "Exemption"]

        exemptions = (
            exemption_count.groupby(["Year"])["Exemption Status"]
            .value_counts()
            .reset_index(name="No Pass (Exemption)")
        )

        # Number of Non-passing Students Advanced
        advance_no_pass_count = student_data[
            (student_data["Status"] == "Did Not Pass")
            & (student_data["Current Grade"] == "Grade 4")
        ]
        advance_no_pass = (
            advance_no_pass_count.groupby(["Year"])["Status"]
            .value_counts()
            .reset_index(name="No Pass (Advanced)")
        )

        # Number of Students Retained
        retained_count = student_data[
            (
                (student_data["Status"] == "Did Not Pass")
                & (student_data["Tested Grade"] == "Grade 3")
                & (student_data["Current Grade"] == "Grade 3")
            )
        ]
        retained = (
            retained_count.groupby(["Year"])["Status"]
            .value_counts()
            .reset_index(name="No Pass (Retained)")
        )

        # Merge iread table data
        dfs_to_merge = [
            table_data,
            grade2_tested,
            grade2_proficiency,
            exemptions,
            advance_no_pass,
            retained,
        ]

        merged = reduce(
            lambda left, right: pd.merge(
                left,
                right,
                on=["Year"],
                how="outer",
                suffixes=("", "_remove"),
            ),
            dfs_to_merge,
        )

        # select and order columns
        merged = merged[
            [
                "Year",
                "Spring Pass %",
                "Spring N-Size",
                "Summer Pass %",
                "Summer N-Size",
                "School Total",
                "2nd Graders Tested",
                "2nd Graders Proficiency",
                "No Pass (Exemption)",
                "No Pass (Advanced)",
                "No Pass (Retained)",
            ]
        ]

        final_table_data = (
            merged.set_index("Year")
            .T.rename_axis("Category")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        # format table data
        for col in final_table_data.columns[1:]:
            final_table_data[col] = pd.to_numeric(
                final_table_data[col], errors="coerce"
            )

        # NOTE: dataframes aren't built for row-wise operations, so if we need different
        # formatting for different rows, we have to do something grotesque like the following
        # start at 1 to again skip "Category" column
        for x in range(1, len(final_table_data.columns)):
            for i in range(0, len(final_table_data.index)):
                if (i == 0) | (i == 2) | (i == 4) | (i == 6) | (i == 14) | (i == 16):
                    if ~np.isnan(final_table_data.iat[i, x]):
                        final_table_data.iat[i, x] = "{:.2%}".format(
                            final_table_data.iat[i, x]
                        )
                elif (i == 11) | (i == 13):
                    final_table_data.iat[i, x] = "{:,.2f}".format(
                        final_table_data.iat[i, x]
                    )
                else:
                    final_table_data.iat[i, x] = "{:,.0f}".format(
                        final_table_data.iat[i, x]
                    )

        # replace Nan with "-"
        final_table_data = final_table_data.replace(
            {"nan": "\u2014", np.NaN: "\u2014"}, regex=True
        )

        return final_fig_data, final_table_data


def process_wida_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Takes raw wida data and processes data for display
    in plotly dash fig and table.

    Args:
    df (pd.DataFrame): wida data

    Returns:
        final_fig_data, final_table_data (Tuple[pd.DataFrame, pd.DataFrame]): two dfs
    """
    data = df.copy()

    # WIDA average per grade by year
    avg_per_grade = (
        data.groupby(["Year", "Tested Grade"])["Composite Overall Proficiency Level"]
        .mean()
        .reset_index(name="Average")
    )

    # WIDA total school average by year
    avg_total = (
        data.groupby(["Year"])["Composite Overall Proficiency Level"]
        .mean()
        .reset_index(name="Average")
    )

    # Drop data for AHS students
    avg_per_grade = avg_per_grade.loc[
        avg_per_grade["Tested Grade"] != "Grade 12+/Adult"
    ]

    # pivot to show average WIDA schore by grade (col) by year (row)
    breakdown_fig_data = (
        avg_per_grade.pivot_table(
            index=["Year"], columns="Tested Grade", values="Average"
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )

    # temporarily store and drop Year col
    breakdown_year_col = breakdown_fig_data["Year"]
    breakdown_fig_data = breakdown_fig_data.drop(["Year"], axis=1)

    # reindex and sort columns using only the numerical part
    breakdown_fig_data = breakdown_fig_data.reindex(
        sorted(breakdown_fig_data.columns, key=lambda x: float(x[6:])),
        axis=1,
    )

    # add Year col back
    breakdown_fig_data.insert(loc=0, column="Year", value=breakdown_year_col)

    # Add school Average to by year calcs
    final_fig_data = pd.merge(breakdown_fig_data, avg_total, on="Year")

    # should not have negative values, but bad data causes
    # them to appear from time to time
    final_fig_data[final_fig_data < 0] = np.NaN

    # Wida table
    breakdown_table_data = (
        breakdown_fig_data.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    ).copy()

    # Get N-Size for each grade for each year and add to table data
    school_nsize_data = (
        data.value_counts(["Tested Grade", "Year"])
        .reset_index()
        .rename(columns={0: "N-Size"})
    )
    breakdown_nsize = pd.merge(
        avg_per_grade,
        school_nsize_data,
        on=["Year", "Tested Grade"],
    )

    # put nsize data in same format as scores
    breakdown_nsize = breakdown_nsize.drop("Average", axis=1)

    breakdown_nsize = (
        breakdown_nsize.pivot_table(
            index=["Year"], columns="Tested Grade", values="N-Size"
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )

    # identify year columns to get totals (named Average to match
    # scores df col name)
    nsize_years = [c for c in breakdown_nsize.columns if "Grade" in c]
    breakdown_nsize["Average"] = breakdown_nsize[nsize_years].sum(axis=1)

    # sort nsize columns to match data dataframe (using natural sort)
    nsize_years.sort(key=natural_keys)
    nsize_columns_sorted = ["Year"] + nsize_years + ["Average"]
    breakdown_nsize = breakdown_nsize[nsize_columns_sorted]

    breakdown_nsize = (
        breakdown_nsize.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    # clean and format table data
    breakdown_nsize.columns = breakdown_nsize.columns.astype(str)
    breakdown_nsize.columns = ["Category"] + [
        str(col) + "N-Size" for col in breakdown_nsize.columns if "Category" not in col
    ]
    breakdown_table_data.columns = breakdown_table_data.columns.astype(str)
    breakdown_nsize.columns = ["Category"] + [
        str(col) + "School" for col in breakdown_nsize.columns if "Category" not in col
    ]

    for col in breakdown_table_data.columns[1:]:
        breakdown_table_data[col] = pd.to_numeric(
            breakdown_table_data[col], errors="coerce"
        )

    breakdown_table_data = breakdown_table_data.set_index("Category")

    breakdown_table_data = breakdown_table_data.applymap("{:.2f}".format)
    breakdown_table_data = breakdown_table_data.reset_index()

    breakdown_table_data = breakdown_table_data.replace(
        {"nan": "\u2014", np.NaN: "\u2014"}, regex=True
    )

    # merge nsize data into data to get into the format
    # expected by multi_table function
    # interweave columns and add category back
    data_columns = [e for e in breakdown_table_data.columns if "Category" not in e]
    nsize_columns = [e for e in breakdown_nsize.columns if "Category" not in e]
    final_columns = list(itertools.chain(*zip(data_columns, nsize_columns)))
    final_columns.insert(0, "Category")

    # merge and re-order using wida_final_columns
    final_table_data = pd.merge(breakdown_table_data, breakdown_nsize, on="Category")

    final_table_data = final_table_data[final_columns]

    return final_fig_data, final_table_data


def process_wida_to_iread_details(
    wida_df: pd.DataFrame, iread_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Takes raw wida and iread data and processes data for display
    in plotly dash table.

    Args:
    wida_df (pd.DataFrame): student wida data
    iread_df (pd.DataFrame): student iread data

    Returns:
        details_table_data (pd.DataFrame): dataframe with processed data
    """

    wida_data = wida_df.copy()
    iread_data = iread_df.copy()

    # all_stns = get_school_stns(school_id)

    wida_data["STN"] = wida_data["STN"].astype(str)

    # NOTE: For many schools the number of students (STNs) with
    # both IREAD and WIDA data will be small.
    wida_comp_data = wida_data[
        ["STN", "Year", "Composite Overall Proficiency Level"]
    ].copy()

    iread_comp_data = iread_data[
        ["STN", "Year", "Test Period", "Status", "Exemption Status"]
    ].copy()

    wida_comp_data["Year"] = wida_comp_data["Year"].astype(str)
    iread_comp_data["Year"] = iread_comp_data["Year"].astype(str)
    iread_comp_data["STN"] = iread_comp_data["STN"].astype(str)

    # matches all STNs with WIDA and IREAD scores from same year.
    # NOTE: This captures all students who took WIDA in the same year
    # that they took IREAD. It does not match students with a recorded
    # WIDA score either before or after a recorded IREAD score. While
    # we do not want to capture the latter, we do want to add those
    # students who has a prior year WIDA score. So we need to run two
    # merge operations, one on STN and YEAR (which captures same year
    # testers) and one just on STN where we search for any STN
    # matches where IREAD Tested Year is > than Max WIDA Tested Year
    current_match = pd.merge(iread_comp_data, wida_comp_data, on=["STN", "Year"])

    # need to differentiate between years when not merging on Year
    iread_comp_data = iread_comp_data.rename(columns={"Year": "IREAD Year"})
    wida_comp_data = wida_comp_data.rename(columns={"Year": "WIDA Year"})

    # find STNs where WIDA tested year < IREAD Year
    prior_match = pd.merge(iread_comp_data, wida_comp_data, on=["STN"])

    # Find Max WIDA Year value for each STN
    year_max = (
        prior_match.groupby(["STN"])["WIDA Year"].max().reset_index(name="WIDA Max")
    )

    # drop duplicates from the full data set (where the same STN can appear
    # up to 5 times) and merge with WIDA Max to add IREAD Year
    prior_match = prior_match.drop_duplicates(subset=["STN"], keep="last")
    year_max = pd.merge(year_max, prior_match, on=["STN"], how="left")

    # filter by STNs where IREAD Year is > then WIDA Max Year
    stn_to_add = year_max[
        year_max["IREAD Year"].astype(int) > year_max["WIDA Max"].astype(int)
    ]

    # Merge the prior and current testers into one df
    if stn_to_add.empty:
        details_data = current_match

    else:
        # change column names to match
        stn_to_add = stn_to_add.drop(["WIDA Max", "WIDA Year"], axis=1)
        stn_to_add = stn_to_add.rename(columns={"IREAD Year": "Year"})

        details_data = pd.concat([current_match, stn_to_add])

    if details_data.empty:
        details_table_data = pd.DataFrame()

    else:
        # Get WIDA Average by Year and Status (Pass/No Pass)
        details_avg = (
            details_data.groupby(["Year", "Status"])[
                "Composite Overall Proficiency Level"
            ]
            .mean()
            .reset_index(name="Average")
        )

        # Get N-Size for each Year and category (Pass/No Pass)
        details_nsize = (
            details_data.groupby("Year")["Status"]
            .value_counts()
            .reset_index(name="N-Size")
        )

        # Merge to add N-Size to WIDA Average df
        details_final = pd.merge(
            details_avg,
            details_nsize,
            on=["Year", "Status"],
        )

        details_nopass = details_final[details_final["Status"] == "Did Not Pass"]
        details_pass = details_final[details_final["Status"] == "Pass"]

        details_pass = details_pass.rename(
            columns={
                "Average": "Avg. WIDA for Students Passing IREAD",
                "N-Size": "# of WIDA Tested Students Passing IREAD",
            }
        )
        details_nopass = details_nopass.rename(
            columns={
                "Average": "Avg. WIDA for Students Not Passing IREAD",
                "N-Size": "# of WIDA Tested Students Not Passing IREAD",
            }
        )

        # prepare to combine
        details_nopass = details_nopass.drop(["Year", "Status"], axis=1)
        details_pass = details_pass.drop("Status", axis=1)
        details_pass = details_pass.reset_index(drop=True)
        details_nopass = details_nopass.reset_index(drop=True)

        details_table_data = pd.concat([details_pass, details_nopass], axis=1)

        for col in details_table_data.columns[1:]:
            details_table_data[col] = pd.to_numeric(
                details_table_data[col], errors="coerce"
            )

        details_nsize = details_table_data[
            "# of WIDA Tested Students Passing IREAD"
        ].fillna(0) + details_table_data[
            "# of WIDA Tested Students Not Passing IREAD"
        ].fillna(
            0
        )

        details_table_data["N-Size"] = details_nsize
        details_table_data["% of WIDA Tested Students Passing IREAD"] = (
            details_table_data["# of WIDA Tested Students Passing IREAD"]
            / details_nsize
        )

        details_table_data = details_table_data.drop(
            [
                "# of WIDA Tested Students Passing IREAD",
                "# of WIDA Tested Students Not Passing IREAD",
            ],
            axis=1,
        )

        details_table_data = details_table_data[
            [
                "Year",
                "% of WIDA Tested Students Passing IREAD",
                "Avg. WIDA for Students Passing IREAD",
                "Avg. WIDA for Students Not Passing IREAD",
                "N-Size",
            ]
        ]

        details_table_data = (
            details_table_data.set_index("Year")
            .T.rename_axis("Category")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        # table format
        for x in range(1, len(details_table_data.columns)):
            for i in range(0, len(details_table_data.index)):
                if i == 0:
                    if ~np.isnan(details_table_data.iat[i, x]):
                        details_table_data.iat[i, x] = "{:.2%}".format(
                            details_table_data.iat[i, x]
                        )
                elif (i == 1) | (i == 2):
                    details_table_data.iat[i, x] = "{:,.2f}".format(
                        details_table_data.iat[i, x]
                    )
                else:
                    details_table_data.iat[i, x] = "{:,.0f}".format(
                        details_table_data.iat[i, x]
                    )

        # replace Nan with "-"
        details_table_data = details_table_data.replace(
            {"nan": "\u2014", np.NaN: "\u2014"}, regex=True
        )

    return details_table_data
