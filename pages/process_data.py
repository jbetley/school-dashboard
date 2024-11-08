#########################################
# ICSB Dashboard - Clean & Process Data #
#########################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     09/06/24

from typing import Tuple
import pandas as pd
import numpy as np
import itertools
from toolz import interleave

from .globals import (
    grades,
    ethnicity,
    subgroup,
)

# from .calculations import calculate_percentage


def transpose_data(raw_df: pd.DataFrame, params):
    """
    Filters tested (nsize) cols and proficiency calculations into
    separate dataframes, performs some cleanup, including a transposition,
    moving years to column headers and listing categories in their own
    columns and then cross-merging the two. variables change depending on
    whether we are analyzing a school or a corporation

    Args:
    raw_df (pd.DataFrame): student level growth data
    params (dict): a variable dictionary of strings with keys:
                    "schools": a list of school ids
                    "type": the school type
                    "year": the selected year
                    "page": the selected page

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
    if params["type"] == "ahs":
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

    elif params["type"] == "hs":
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
    if params["type"] == "k8":
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

    # reorder columns for display
    school_cols = [e for e in merged_data.columns if name_id in e]
    nsize_cols = [e for e in merged_data.columns if nsize_id in e]

    school_cols.sort()
    nsize_cols.sort()

    final_cols = list(itertools.chain(*zip(school_cols, nsize_cols)))

    final_cols.insert(0, "Category")
    final_data = merged_data[final_cols]

    # Add Low and High Grade rows back to k8 data and
    # create df for information figs
    if params["type"] == "k8":
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
    # step 1: find the percentage of students with Adequate growth using
    # "Majority Enrolled" students (all available data) and the percentage
    # of students with Adequate growth using the set of students enrolled for
    # "162 Days" (a subset of available data)

    data_162 = data[data["Day 162"].str.contains("True|TRUE") == True]  #  == "True"]

    # grouby by relevant categories and count the values in the "ILEARNGrowth Level"
    # column (normalize gives us the relative frequencies (%) of the values)
    data = (
        data.groupby(["Year", category, "Subject"])["ILEARNGrowth Level"]
        .value_counts(normalize=True)
        .reset_index(name="Majority Enrolled")
    )

    data_162 = (
        data_162.groupby(["Year", category, "Subject"])["ILEARNGrowth Level"]
        .value_counts(normalize=True)
        .reset_index(name="162 Days")
    )

    # If the frequency of "Not Adequate Growth" == 1.0: then all ME and Day 162
    # values for that category and subject were Not Adequate (e.g., 100% of the
    # students in that category were Not Adequate), meaning that 0% of students
    # had adequate growth. So wherever "Not Adequate Growth" == 1.0, we change
    # "ILEARNGrowth Level" to "Adequate Growth" and Majority Enrolled (or Day
    # 162) to 0 (otherwise these values would disappear when we get rid of the
    # "ILEARNGrowth Level" column)

    mask = data["Majority Enrolled"] == 1.0
    data.loc[mask, "ILEARNGrowth Level"] = "Adequate Growth"
    data.loc[mask, "Majority Enrolled"] = 0

    mask_162 = data_162["162 Days"] == 1.0
    data_162.loc[mask_162, "ILEARNGrowth Level"] = "Adequate Growth"
    data_162.loc[mask_162, "162 Days"] = 0

    # drop all rows with "Not Adequate"
    data = data[data["ILEARNGrowth Level"].str.contains("Not Adequate") == False]
    data_162 = data_162[
        data_162["ILEARNGrowth Level"].str.contains("Not Adequate") == False
    ]

    # step 3: Merge data_162["162 Days"] column into 'data'- cols will likely
    # be of different length, so we need to key on Year, Subject, Category
    data = data.merge(
        data_162, how="left", on=["Year", category, "Subject"], suffixes=("", "_y")
    )

    data["Diff"] = data["162 Days"] - data["Majority Enrolled"]  # "Difference"

    # step 4: get into proper format for display as multi-header DataTable

    # create final category
    data["Category"] = data[category] + "|" + data["Subject"]

    # filter unneeded columns
    final_data = data.filter(
        regex=r"Year|Category|Majority Enrolled|162 Days|Diff",  # "Difference"
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
    fig_data = final_data.copy()
    fig_data = fig_data.drop("Diff", axis=1)  # "Difference"
    fig_data = fig_data.pivot(index=["Year"], columns="Category")
    fig_data.columns = fig_data.columns.map(lambda x: "_".join(map(str, x)))

    # create table data
    table_data = final_data.copy()

    # Need specific column order. sort_index does not work
    cols = []
    yrs = list(set(table_data["Year"].to_list()))
    yrs.sort(reverse=True)
    for y in yrs:
        cols.append(str(y) + "162 Days")
        cols.append(str(y) + "Majority Enrolled")
        cols.append(str(y) + "Diff")  # "Difference"

    # pivot df from wide to long" add years to each column name; move year to
    # front of column name; sort and reset_index
    table_data = table_data.pivot(index=["Category"], columns="Year")

    table_data.columns = table_data.columns.map(lambda x: "".join(map(str, x)))
    table_data.columns = table_data.columns.map(lambda x: x[-4:] + x[:-4])
    table_data = table_data[cols]
    table_data = table_data.reset_index()

    return fig_data, table_data


def process_discipline_data(data, category, demographic):
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
