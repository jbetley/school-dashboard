#########################################
# ICSB Dashboard - Clean & Process Data #
#########################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     02/21/24

# TODO: Explore serverside disk caching for data loading

from typing import Tuple
import pandas as pd
import numpy as np
import itertools

from .globals import (
    grades,
    ethnicity,
    subgroup,
    discipline_categories,
    discipline_groups,
)

from .calculations import calculate_percentage

# filters tested (nsize) cols and proficiency calculations into
# separate dataframes, performs some cleanup, including a transposition,
# moving years to column headers and listing categories in their own
# columns and then cross-merging the two. variables change depending on
# whether we are analyzing a school or a corporation
def transpose_data(df, params):
    # First, determine whether df contains data for the charter school or
    # the  geo school corporation. A school corporation will always have the
    # same School and Corporation Name and School and Corporation ID.
    # a charter school that is not part of a network will have the same
    # School and Corporation Name, but different School and Corporation IDs.
    # a charter school that IS part of a network may have the same or different
    # School and Corporation ID, but will have a different School and Corporation
    # Name. So we check whether the two sets of columns are equivalent and if
    # both are, the data must belong to a school corporation.
    df = df.reset_index(drop=True)

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
    if params["type"] == "HS" or params["type"] == "AHS":
        tested_cols = "Total Tested|Cohort Count|Year"
        filter_cols = r"^Category|Graduation Rate$|AHS|Pass Rate$|Benchmark %|Below|Approaching|At|^Year$"
        substring_dict = {" Total Tested": "", "\|Cohort Count": "|Graduation"}

    else:
        tested_cols = "Total Tested|Test N|Year"
        filter_cols = r"School ID|Corporation ID|Corporation Name|Low Grade|High Grade|\|ELA Proficient %$|\|Math Proficient %$|IREAD Proficient %|^Year$"
        substring_dict = {" Total Tested": "", " Test N": ""}

    # Get Proficiency and Tested (N-Size) data by id in separate dataframe.
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
            c: str(c) + nsize_id  # "N-Size"
            for c in tested_data.columns
            if c not in ["Category"]
        }
    )

    tested_data = tested_data.fillna(value=np.nan)
    tested_data = tested_data.replace(0, np.nan)

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
    if params["type"] == "K8":
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

    # keep only those rows where substring is in Category
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
    if params["type"] == "K8":
        final_data = pd.concat(
            [final_data.reset_index(drop=True), other_rows.reset_index(drop=True)],
            axis=0,
        ).reset_index(drop=True)

    return final_data


def process_growth_data(
    data: pd.DataFrame, category: str
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
    # step 1: find the percentage of students with Adequate growth using
    # "Majority Enrolled" students (all available data) and the percentage
    # of students with Adequate growth using the set of students enrolled for
    # "162 Days" (a subset of available data)

    data_162 = data[data["Day 162"].str.contains("True|TRUE") == True]  #  == "True"]

    # grouby by relevant categories and count the values in the "ILEARNGrowth Level"
    # column (normalize gives us the relative frequencies (%) of the values)
    data = (
        data.groupby(["Test Year", category, "Subject"])["ILEARNGrowth Level"]
        .value_counts(normalize=True)
        .reset_index(name="Majority Enrolled")
    )

    data_162 = (
        data_162.groupby(["Test Year", category, "Subject"])["ILEARNGrowth Level"]
        .value_counts(normalize=True)
        .reset_index(name="162 Days")
    )

    # If the frequency of "Not Adequate Growth" == 1.0: then all ME and Day 162 values for that
    # category and subject were Not Adequate (e.g., 100% of the students in that category
    # were Not Adequate), meaning that 0% of students had adequate growth. So wherever
    # "Not Adequate Growth" == 1.0, we change "ILEARNGrowth Level" to "Adequate Growth"
    # and Majority Enrolled (or Day 162) to 0 (otherwise these values would disappear when
    # we get rid of the "ILEARNGrowth Level" column)

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
        data_162, how="left", on=["Test Year", category, "Subject"], suffixes=("", "_y")
    )

    data["Diff"] = data["162 Days"] - data["Majority Enrolled"]  # "Difference"

    # step 4: get into proper format for display as multi-header DataTable

    # create final category
    data["Category"] = data[category] + "|" + data["Subject"]

    # filter unneeded columns
    final_data = data.filter(
        regex=r"Test Year|Category|Majority Enrolled|162 Days|Diff",  # "Difference"
        axis=1,
    )

    # NOTE: Occasionally, the data will have an "Unknown" Category. No idea why, but
    # we need to get rid of it - easiest way would be to just drop any Categories
    # matching Unknown, but that won"t stop other random Categories from getting
    # through. So instead, we drop any Categories that don"t match categories in
    # the respective list

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
    fig_data = fig_data.pivot(index=["Test Year"], columns="Category")
    fig_data.columns = fig_data.columns.map(lambda x: "_".join(map(str, x)))

    # create table data
    table_data = final_data.copy()

    # Need specific column order. sort_index does not work
    cols = []
    yrs = list(set(table_data["Test Year"].to_list()))
    yrs.sort(reverse=True)
    for y in yrs:
        cols.append(str(y) + "162 Days")
        cols.append(str(y) + "Majority Enrolled")
        cols.append(str(y) + "Diff")  # "Difference"

    # pivot df from wide to long" add years to each column name; move year to
    # front of column name; sort and reset_index
    table_data = table_data.pivot(index=["Category"], columns="Test Year")

    table_data.columns = table_data.columns.map(lambda x: "".join(map(str, x)))
    table_data.columns = table_data.columns.map(lambda x: x[-4:] + x[:-4])
    table_data = table_data[cols]
    table_data = table_data.reset_index()

    return fig_data, table_data


def process_discipline_data(raw_data, year, school_id):
    # Drop years of data that have been excluded by the
    # selected year (are later than)
    # excluded_years = get_excluded_years(year)
    excluded_years = []

    excluded_academic_years = int(2024) - int(year)

    for i in range(excluded_academic_years):
        excluded_year = int(2024) - i
        excluded_years.append(excluded_year)

    if excluded_years:
        raw_data = raw_data[~raw_data["Year"].isin(excluded_years)]

    raw_data = raw_data.sort_values(by="Year", ascending=False)

    raw_data = raw_data.reset_index(drop=True)

    # Drop all columns for a Category if the value of "Total Tested" for
    # the Category for the school is null or 0 for the "school"
    drop_columns = []

    data = raw_data.copy()

    # convert from float to str while dropping the decimal
    data["School ID"] = data["School ID"].astype("Int64").astype("str")
    data["Corporation ID"] = data["Corporation ID"].astype("Int64").astype("str")

    # "Total Unique Students" is the number of unique students in the school
    #  for each category
    tested_cols = [
        col for col in data.columns.to_list() if "Students" in col
        and "Total Unique Students" not in col
                   ]

    # remove any decimals in N-Size cols
    for col in tested_cols:
        data[col] = data[col].astype(str).replace("\.0", "", regex=True)

    # for col in tested_cols:
    #     if (
    #         pd.to_numeric(data[col], errors="coerce").sum() != 0
    #         or ~data[col].isnull().all()
    #     ):
            
    #         category_col = tested_col.replace(" Unique Students", "")
    #         data = data.drop([col, category_col], axis=1)       
    #         matching_cols = data.columns[
    #             pd.Series(data.columns).str.startswith(col.split("Students")[0])
    #         ]

    #         drop_columns.append(matching_cols.tolist())

    # drop_all = [i for sub_list in drop_columns for i in sub_list]

    # print('DROPPED COLS')
    # print(drop_all)
    # data = data.drop(drop_all, axis=1).copy()

    # # k8 or hs data with excluded years and non-tested categories dropped
    # data = data.reset_index(drop=True)

    # Get a list of category columns
    # category_substrings = [x.replace(" Unique Students", "") for x in tested_cols]

    # drop the entire category if ("Tested" == 0 or NaN) or if
    # ("Tested" > 0 and "Total Proficient" is NaN. A "Total Proficient"
    # value of NaN means it was a "***" before being converted to numeric
    # we use sum/all because there could be one or many columns

    cols_to_drop = []

    for group in discipline_groups:
        
        group_total = "Total Unique Students|" + group
        
        for category in discipline_categories:

            unique_in_category = category + " Unique Students|" + group
            all_in_category = category + "|" + group

            all_result = all_in_category + " Percentage"
            unique_result = unique_in_category + " Percentage"

            data[all_result] = calculate_percentage(
                data[all_in_category], data[group_total]
            )
            
            data[unique_result] = calculate_percentage(
                data[unique_in_category], data[group_total]
            )

            # cols_to_drop.extend(all_in_category, unique_in_category)

        # if (
        #     pd.to_numeric(data[tested_col], errors="coerce").sum() == 0
        #     or pd.isna(data[tested_col]).all()
        # ) | (
        #     pd.to_numeric(data[tested_col], errors="coerce").sum() > 0
        #     and pd.isna(data[category_col]).all()
        # ):
        #     data = data.drop([tested_col, category_col], axis=1)

        # else:
        #     data[result_col] = calculate_percentage(
        #         data[category_col], data[tested_col]
        #     )

    print(data)
    filename99 = ("DISC_data.csv")
    data.to_csv(filename99, index=False)
    return data
