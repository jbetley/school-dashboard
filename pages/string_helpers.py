###################################################
# ICSB Dashboard - String Maninpulation Functions #
###################################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     02/21/24

import pandas as pd
import numpy as np
import re
import textwrap
from typing import Tuple

from .globals import (
    ethnicity,
    subgroup,
    info_categories
)


# helper function for natural_keys
def atoi(text):
    return int(text) if text.isdigit() else text


# NOTE: function to provide natural sorting
# https://stackoverflow.com/questions/5967500/how-to-correctly-sort-a-string-with-a-number-inside
def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]


def customwrap(s: str, width: int = 16) -> str:
    """
    Creates wrapped text using html tags based on the specified width.
    Adds two spaces before <br> to ensure the words at the end of each
    break have the same spacing as 'ticksuffix' in make_stacked_bar()

    Args:
        s (str): a string
        width (int, optional): the desired maximum width of the string. Defaults to 16.

    Returns:
        string (str)
    """
    return "  <br>".join(textwrap.wrap(s, width=width))


def convert_to_svg_circle(val: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a Dataframe and replaces text with svg circles coded certain colors
    based on the text. See:
    https://stackoverflow.com/questions/19554834/how-to-center-a-circle-in-an-svg
    https://stackoverflow.com/questions/65778593/insert-shape-in-dash-datatable
    https://community.plotly.com/t/adding-markdown-image-in-dashtable/53894/2

    Args:
        val (pd.Dataframe): Pandas dataframe with metric Rating columns

    Returns:
        pd.Dataframe: returns the same dataframe with svg circles in place of text
    """
    result = val.copy()

    # NOTE: Using font-awesome circle icon to replace string ratings.
    result = result.replace(
        ["^DNMS$", "Does Not Meet Expectations"],
        "<span style='font-size: 1em; color: #ea5545;'><i class='fa fa-circle center-icon'></i></span>",
        regex=True,
    )
    result = result.replace(
        ["^AS$", "Approaches Expectations"],
        "<span style='font-size: 1em; color: #F5A30F;'><i class='fa fa-circle center-icon'></i></span>",
        regex=True,
    )
    result = result.replace(
        ["^MS$", "Meets Expectations"],
        "<span style='font-size: 1em; color: #87bc45;'><i class='fa fa-circle center-icon'></i></span>",
        regex=True,
    )
    result = result.replace(
        ["^ES$", "Exceeds Expectations"],
        "<span style='font-size: 1em; color: #0D9FE1;'><i class='fa fa-circle center-icon'></i></span>",
        regex=True,
    )
    result = result.replace(["N/A", "NA", "No Rating", np.nan], "", regex=True)

    return result


def create_chart_label(data: pd.DataFrame) -> str:
    """
    Takes a dataframe of academic data and creates a chart label based on the column content

    Args:
        final_data (pd.DataFrame): dataframe of academic data

    Returns:
        label (str): chart label
    """

    data_columns = data.columns.tolist()

    if data.columns.str.contains("Total\|Graduation|Non Waiver").any() == True:
        label = "Comparison: Total/Non Waiver Graduation Rate"

    else:
        if data.columns.str.contains("Graduation Rate").any() == True:
            if (
                len(
                    [
                        col
                        for col in data_columns
                        if any(substring for substring in ethnicity if substring in col)
                    ]
                )
                > 0
            ):
                label = "Comparison: Graduation Rate by Ethnicity"

            elif (
                len(
                    [
                        col
                        for col in data_columns
                        if any(substring for substring in subgroup if substring in col)
                    ]
                )
                > 0
            ):
                label = "Comparison: Graduation Rate by Subgroup"

            else:
                label = ""

        elif data.columns.str.contains("Proficient").any() == True:
            # pull subject from the first "subject" column using regex
            subject_columns = [
                c
                for c in data_columns
                if c not in ["School Name", "School ID", "Low Grade", "High Grade"]
            ]
            label_subject = re.search(r"(?<=\|)(.*?)(?=\s)", subject_columns[0]).group()  # type: ignore

            if (
                len(
                    [
                        col
                        for col in data_columns
                        if any(substring for substring in ethnicity if substring in col)
                    ]
                )
                > 0
            ):
                label_category = " Proficiency by Ethnicity"

            elif (
                len(
                    [
                        col
                        for col in data_columns
                        if any(substring for substring in subgroup if substring in col)
                    ]
                )
                > 0
            ):
                label_category = " Proficiency by Subgroup"

            else:
                label_category = ""

            label = "Comparison: " + label_subject + label_category

        elif data.columns.str.contains("Benchmark").any() == True:
            if (
                len(
                    [
                        col
                        for col in data_columns
                        if any(substring for substring in ethnicity if substring in col)
                    ]
                )
                > 0
            ):
                if data.columns.str.contains("EBRW").any():
                    label = "Comparison: SAT At Benchmark by Ethnicity (EBRW)"
                else:
                    label = "Comparison: SAT At Benchmark by Ethnicity (Math)"

            elif (
                len(
                    [
                        col
                        for col in data_columns
                        if any(substring for substring in subgroup if substring in col)
                    ]
                )
                > 0
            ):
                if data.columns.str.contains("EBRW").any():
                    label = "Comparison: SAT At Benchmark by Subgroup (EBRW)"
                else:
                    label = "Comparison: SAT At Benchmark by Subgroup (Math)"

            elif (
                len(
                    [
                        col
                        for col in data_columns
                        if "Total" in col and "Benchmark" in col
                    ]
                )
                > 0
            ):
                label = "Comparison: School Total SAT At Benchmark"

            else:
                label = ""

    return label


def create_school_label(data: pd.DataFrame) -> pd.Series:
    """
    Takes a dataframe of academic data and creates a label for each school, merging school name
    and grade span. Used by the combine_school_name_and_grade_levels() function and by certain
    comparison tables.

    Args:
        final_data (pd.DataFrame): dataframe of academic data

    Returns:
        label (pd.Series): a series of labels one for each school
    """

    label = data[["School Name", "Low Grade", "High Grade"]].copy()

    # Add low/high grades to school name
    label.loc[label["Low Grade"] == 13, "School Name"] = label["School Name"] + " (AHS)"
    label.loc[label["Low Grade"] != 13, "School Name"] = (
        label["School Name"]
        + " ("
        + label["Low Grade"].fillna("").astype(str)
        + "-"
        + label["High Grade"].fillna("").astype(str)
        + ")"
    )

    label = label.replace("\(-\)", "", regex=True)

    # escape "." because want to replace literal ".0" and not anychar + "0"
    label = label.replace("\.0", "", regex=True)

    label = label.drop(["Low Grade", "High Grade"], axis=1)

    return label


def combine_school_name_and_grade_levels(data: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a series that merges school name and grade spans and drops the
    grade span columns from the dataframe (they are not charted)

    Args:
        data (pd.DataFrame): dataframe of academic data

    Returns:
        data (pd.DataFrame): dataframe
    """
    school_names = create_school_label(data)

    if "Low Grade" in data:
        data = data.drop(["Low Grade", "High Grade"], axis=1)

    # shift the "School Name" column to the first position and replace
    # the values in "School Name" column with the school_names series
    data = data.drop("School Name", axis=1)
    data["School Name"] = school_names

    first_column = data.pop("School Name")
    data.insert(0, "School Name", first_column)

    return data


def identify_missing_categories(
    raw_data: pd.DataFrame, tested_categories: list
) -> Tuple[pd.DataFrame, str, str]:
    """
    Processes several dataframes for display in comparison tables while tracking both schools
    that are missing data for a particulary category (category_string) and schools that are
    missing data for all categories (school_string).

    Args:
        school_data (pd.DataFrame): academic data from the selected school
        corporation_data (pd.DataFrame): academic data from the school corporation where the school is located
        comparison_data (pd.DataFrame): academic data from comparable schools (may or may not be in school corp)
        categories (list): a list of academic categories
        corp_name (str): the name of the school corporation

    Returns:
        Tuple[
            final_data (pd.DataFrame): all dataframes cleaned up and combined
            category_string (str): a string of categories for which the selected school has no data.
            school_string (str): a string of schools which have no data
        ]
    """

    subject_categories = [
        c
        for c in tested_categories
        if c not in ["School Name", "Low Grade", "High Grade"]
    ]
    school_columns = [i for i in subject_categories if i in raw_data.columns]
    school_categories = [ele for ele in school_columns if ele not in info_categories]

    # test all school columns and drop any where all columns (proficiency data) is nan/null
    final_data = raw_data.dropna(subset=school_categories, how="all")
    final_data = final_data.replace(r"^\s*$", np.nan, regex=True)

    # get the names of the schools that have no data by comparing the column sets before
    # and after the drop - we use this later to clean up the school_string
    missing_schools = list(
        set(raw_data["School Name"]) - set(final_data["School Name"])
    )

    # Get the names and categories of schools that have data for some categories and not others.
    # In the end we want  a list of schools that is made up of schools that are missing all data
    # + schools that are missing some data + what data they are missing

    check_data = raw_data.copy()

    if check_data.columns.isin(["Low Grade", "High Grade"]).any():
        check_data = check_data.drop(["Low Grade", "High Grade"], axis=1)
        check_data = check_data.reset_index(drop=True)

    # get a list of the categories that are missing from selected school data and
    # strip everything following "|" delimeter for annotation
    missing_categories = [i for i in subject_categories if i not in check_data.columns]
    missing_categories = [s.split("|")[0] for s in missing_categories]

    category_string = ", ".join(missing_categories)

    # get index and columns where there are null values (each are a numpy array)
    idx, idy = np.where(pd.isnull(check_data))

    # create a list of lists of each School Name/Category combination using x and y indexes
    with_missing_list = []
    for i in range(0, idx.size):
        with_missing_list.append(
            [check_data.iloc[idx[i]]["School Name"], check_data.columns[idy[i]]]
        )

    # NOTE: in the following for loop, head represents the first element of each list (the
    # School Name), while *tail represents the remaining items in the list (using
    # iterable unpacking). The asterisk means that the tail variable captures “all
    # remaining iterable values” that are not captured by the head variables. setdefault()
    # is used to set "head" as the default value of the dict key. if the key is present, a
    # value is returned (tail). if there is no value, it simply adds the key ([head])
    # as the default value. Extend adds the list as a single value to the dict entry,
    # so we end up with: {School Name: [School Name, Category1, Category2], ...}
    # we then create a list of the values of the dictionary

    missing_dict = {}  # type: dict
    for head, *tail in with_missing_list:
        missing_dict.setdefault(head, [head]).extend(tail)

    schools_with_missing_list = list(missing_dict.values())

    all_schools_with_missing = []

    # iterate over the sublists and create strings for each school in the
    # format: School (Missing Category, Missing Category). If the school
    # is in the list of schools missing all data (missing_schools), we
    # sub in word (All) for the list of missing categories
    if schools_with_missing_list:
        for sch in schools_with_missing_list:
            clean_sch = [s.split("|")[0] for s in sch]

            if clean_sch[:1][0] in missing_schools:
                school_string = clean_sch[:1][0] + " (All)"
            else:
                school_string = clean_sch[:1][0] + " (" + ", ".join(clean_sch[1:]) + ")"

            all_schools_with_missing.append(school_string)

        school_string = ", ".join(all_schools_with_missing)

    else:
        school_string = "None"
        category_string = "None"

    # proper punctuation is very important
    school_string = school_string + "."
    category_string = category_string + "."

    return final_data, category_string, school_string
