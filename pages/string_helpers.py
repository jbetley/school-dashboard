###################################################
# ICSB Dashboard - String Maninpulation Functions #
###################################################
# author:   jbetley
# version:  1.10
# date:     08/31/23

import pandas as pd
import numpy as np
import re
import textwrap
from typing import Tuple

from .load_data import ethnicity, subgroup, info_categories

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
    return '  <br>'.join(textwrap.wrap(s,width=width))

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

    # Use regex and beginning(^) and end-of-line ($) regex anchors to ensure exact matches only
    # NOTE: Using font-awesome circle icon.
    result = result.replace(["^DNMS$","Does Not Meet Expectations"],"<span style='font-size: 1em; color: #ea5545;'><i class='fa fa-circle center-icon'></i></span>", regex=True)
    result = result.replace(["^AS$","Approaches Expectations"],"<span style='font-size: 1em; color: #ede15b;'><i class='fa fa-circle center-icon'></i></span>", regex=True)
    result = result.replace(["^MS$","Meets Expectations"],"<span style='font-size: 1em; color: #87bc45;'><i class='fa fa-circle center-icon'></i></span>", regex=True)
    result = result.replace(["^ES$","Exceeds Expectations"],"<span style='font-size: 1em; color: #b33dc6;'><i class='fa fa-circle center-icon'></i></span>", regex=True)
    result = result.replace(["N/A","NA","No Rating",np.nan],"", regex=True)

    return result

def create_chart_label(data: pd.DataFrame) -> str:
    """
    Takes a dataframe of academic data and creates a chart label based on the columns

    Args:
        final_data (pd.DataFrame): dataframe of academic data

    Returns:
        label (str): chart label
    """

    data_columns = data.columns.tolist()

    if data.columns.str.contains("Total Graduation|Non Waiver Graduation").any() == True:
        label = "Comparison: Total/Non Waiver Graduation Rate" 
    
    else:

        if data.columns.str.contains("Graduation Rate").any() == True:
            if len([col for col in data_columns if any(substring for substring in ethnicity if substring in col)]) > 0:
                label = "Comparison: Graduation Rate by Ethnicity"
            
            elif len([col for col in data_columns if any(substring for substring in subgroup if substring in col)]) > 0:
                label = "Comparison: Graduation Rate by Subgroup"
            
            else:
                label = ""
    
        elif data.columns.str.contains("Proficient").any() == True:

            # pull subject from the first "subject" column using regex
            subject_columns = [c for c in data_columns if c not in ['School Name', 'Low Grade', 'High Grade']]
            label_subject = re.search(r"(?<=\|)(.*?)(?=\s)",subject_columns[0]).group() # type: ignore

            if len([col for col in data_columns if any(substring for substring in ethnicity if substring in col)]) > 0:
                label_category = " Proficiency by Ethnicity"

            elif len([col for col in data_columns if any(substring for substring in subgroup if substring in col)]) > 0:
                label_category = " Proficiency by Subgroup"               

            else:
                label_category = ""

            label = "Comparison: " + label_subject + label_category

        elif data.columns.str.contains("Benchmark").any() == True:
            
            if len([col for col in data_columns if any(substring for substring in ethnicity if substring in col)]) > 0:
                label = "Comparison: SAT At Benchmark by Ethnicity" 

            elif len([col for col in data_columns if any(substring for substring in subgroup if substring in col)]) > 0:
                label = "Comparison: SAT At Benchmark by Subgroup"

            elif len([col for col in data_columns if 'School Total' in col and "Benchmark" in col]) > 0:
                label = "Comparison: School Total SAT At Benchmark"

            else:
                label = ""

    return label
    
def create_school_label(data: pd.DataFrame) -> pd.Series:
    """
    Takes a dataframe of academic data and creates a label for each school including
    the school"s gradespan.

    Args:
        final_data (pd.DataFrame): dataframe of academic data

    Returns:
        label (str): school label with name and gradespan
    """

    label = data["School Name"] + " (" + data["Low Grade"].fillna("").astype(str) + \
        "-" + data["High Grade"].fillna("").astype(str) + ")"

    label = label.str.replace("\(-\)", "",regex=True)
    label = label.str.replace(".0","",regex=True)

    label = data["School Name"]

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

    if 'Low Grade' in data:
        data = data.drop(["Low Grade", "High Grade"], axis = 1)

    # shift the "School Name" column to the first position and replace
    # the values in "School Name" column with the school_names series
    data = data.drop("School Name", axis = 1)
    data["School Name"] = school_names

    first_column = data.pop("School Name")
    data.insert(0, "School Name", first_column)
    
    return data

def identify_missing_categories(school_data: pd.DataFrame, corporation_data: pd.DataFrame, comparison_data: pd.DataFrame, categories: list, corp_name: str) -> Tuple[pd.DataFrame, str, str]:
    """
    Processes several dataframes for display in comparison tables while tracking both schools that are missing data for 
    a particulary category (category_string) and schools that are missing data for all categories (school_string).

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
    categories = [c for c in categories if c not in ["School Name","Low Grade", "High Grade"]]
    all_categories = categories + info_categories

    school_name = school_data["School Name"].values[0]

    school_columns = [i for i in categories if i in school_data.columns]

    # TODO: Move the merge-y bits to separate merge function for K8 and use pure function to find strings

    # sort corp data by the school columns (this excludes any categories
    # not in the school data)
    corporation_data = corporation_data.loc[:, corporation_data.columns.isin(school_columns)].copy()

    # add the school corporation name
    corporation_data["School Name"] = corp_name

    # concatenate the school and corporation dataframes, filling empty values (e.g., Low and High Grade) with ""
    first_merge_data = pd.concat([school_data, corporation_data], sort=False).fillna("")

    # filter comparable schools
    comparison_data = comparison_data.loc[:, comparison_data.columns.isin(all_categories)].copy()

    # concatenate school/corp and comparison dataframes
    combined_data = pd.concat([first_merge_data,comparison_data])
    combined_data = combined_data.reset_index(drop=True)

    # make a copy (used for comparison purposes)
    final_data = combined_data.copy()

    # get a list of all of the Categories (each one a column)
    school_categories = [ele for ele in school_columns if ele not in info_categories]

    # test all school columns and drop any where all columns (proficiency data) is nan/null
    final_data = final_data.dropna(subset=school_categories, how="all")  

    # replace any blanks with NaN
    final_data = final_data.replace(r"^\s*$", np.nan, regex=True)

    # get the names of the schools that have no data by comparing the
    # column sets before and after the drop
    missing_schools = list(set(combined_data["School Name"]) - set(final_data["School Name"]))

    # Now comes the hard part. Get the names and categories of schools that
    # have data for some categories and not others. In the end we want
    # to build a list of schools that is made up of schools that are missing
    # all data + schools that are missing some data + what data they are
    # missing

    check_data = final_data.copy()
    # TODO: Need to figure out when LowGrade nad HighGrade are necessary and when to drop
    # TODO: and how the current logic works - cause it is inconsistent
    if check_data.columns.isin(["Low Grade","High Grade"]).any(): #"Low Grade" in check_data.columns or "High Grade" in check_data.columns:
        check_data = check_data.drop(["Low Grade","High Grade"], axis = 1)
        check_data = check_data.reset_index(drop=True)

    # get a list of the categories that are missing from selected school data and
    # strip everything following "|" delimeter for annotation
    # NOTE: this is doing a slightly different thing than the check_for_insufficient_n_size()
    # & check_for_no_data() functions (calculations.py), but may want to check at some point
    # to see which process is faster

    missing_categories = [i for i in categories if i not in check_data.columns]                
    missing_categories = [s.split("|")[0] for s in missing_categories]

    # get index and columns where there are null values (numpy array)
    idx, idy = np.where(pd.isnull(check_data))

    # np.where returns an index for each column, resulting in duplicate
    # indexes for schools missing multiple categories. But we only need one
    # unique value for each school that is missing data
    schools_with_missing = np.unique(idx, axis=0)

    schools_with_missing_list = []
    if schools_with_missing.size != 0:
        for i in schools_with_missing:

            schools_with_missing_name = check_data.iloc[i]["School Name"]

            # get missing categories as a list, remove everything
            # after the "|", and filter down to unique categories
            with_missing_categories = list(check_data.columns[idy])
            with_missing_categories = [s.split("|")[0] for s in with_missing_categories]
            unique__missing_categories = list(set(with_missing_categories))

            # create a list of ["School Name (Cat 1, Cat2)"]
            schools_with_missing_list.append(schools_with_missing_name + " (" + ", ".join(unique__missing_categories) + ")")

    else:
        schools_with_missing_list = []

    # create the string. Yes this is ugly, and i will probably fix it later, but
    # we need to make sure that all conditions match proper punctuation.
    if len(schools_with_missing_list) != 0:
        if len(schools_with_missing_list) > 1:

            schools_with_missing_string = ", ".join(schools_with_missing_list)
        else:
            schools_with_missing_string = schools_with_missing_list[0]

        if missing_schools:
            missing_schools = [i + " (All)" for i in missing_schools]
            school_string = ", ".join(list(map(str, missing_schools))) + "."
            school_string = schools_with_missing_string + ", " + school_string
        else:
            school_string = schools_with_missing_string + "."
    else:
        if missing_schools:
            missing_schools = [i + " (All)" for i in missing_schools]
            school_string = ", ".join(list(map(str, missing_schools))) + "."
        else:
            school_string = "None."

    # Create string for categories for which the selected school has
    # no data. These categories are not shown at all.
    if missing_categories:
        category_string = ", ".join(list(map(str, missing_categories))) + "."
    else:
        category_string = "None."

    return final_data, category_string, school_string

def identify_missing_categories_pure(raw_data: pd.DataFrame, categories: list) -> Tuple[pd.DataFrame, str, str]:
    """
    Processes several dataframes for display in comparison tables while tracking both schools that are missing data for 
    a particulary category (category_string) and schools that are missing data for all categories (school_string).

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
    subject_categories = [c for c in categories if c not in ["School Name","Low Grade", "High Grade"]]
    
    # all_categories = subject_categories + info_categories

    # school_name = raw_data["School Name"].values[0]

    school_columns = [i for i in subject_categories if i in raw_data.columns]

    # get a list of all of the Categories (each one a column)
    school_categories = [ele for ele in school_columns if ele not in info_categories]

    # test all school columns and drop any where all columns (proficiency data) is nan/null
    final_data = raw_data.dropna(subset=school_categories, how="all")  

    # replace any blanks with NaN
    final_data = final_data.replace(r"^\s*$", np.nan, regex=True)

    # get the names of the schools that have no data by comparing the
    # column sets before and after the drop
    missing_schools = list(set(raw_data["School Name"]) - set(final_data["School Name"]))

    # Now comes the hard part. Get the names and categories of schools that
    # have data for some categories and not others. In the end we want
    # to build a list of schools that is made up of schools that are missing
    # all data + schools that are missing some data + what data they are
    # missing

    check_data = raw_data.copy()

    if check_data.columns.isin(["Low Grade","High Grade"]).any():
        check_data = check_data.drop(["Low Grade","High Grade"], axis = 1)
        check_data = check_data.reset_index(drop=True)

    # get a list of the categories that are missing from selected school data and
    # strip everything following "|" delimeter for annotation
    # NOTE: this is doing a slightly different thing than the check_for_insufficient_n_size()
    # & check_for_no_data() functions (calculations.py), but may want to check at some point
    # to see which process is faster

    missing_categories = [i for i in subject_categories if i not in check_data.columns]                
    missing_categories = [s.split("|")[0] for s in missing_categories]

    # get index and columns where there are null values (numpy array)
    idx, idy = np.where(pd.isnull(check_data))

    # np.where returns an index for each column, resulting in duplicate
    # indexes for schools missing multiple categories. But we only need one
    # unique value for each school that is missing data
    schools_with_missing = np.unique(idx, axis=0)

    schools_with_missing_list = []
    if schools_with_missing.size != 0:
        for i in schools_with_missing:

            schools_with_missing_name = check_data.iloc[i]["School Name"]

            # get missing categories as a list, remove everything
            # after the "|", and filter down to unique categories
            with_missing_categories = list(check_data.columns[idy])
            with_missing_categories = [s.split("|")[0] for s in with_missing_categories]
            unique__missing_categories = list(set(with_missing_categories))

            # create a list of ["School Name (Cat 1, Cat2)"]
            schools_with_missing_list.append(schools_with_missing_name + " (" + ", ".join(unique__missing_categories) + ")")

    else:
        schools_with_missing_list = []

    # create the string. Yes this is ugly, and i will probably fix it later, but
    # we need to make sure that all conditions match proper punctuation.
    if len(schools_with_missing_list) != 0:
        if len(schools_with_missing_list) > 1:

            schools_with_missing_string = ", ".join(schools_with_missing_list)
        else:
            schools_with_missing_string = schools_with_missing_list[0]

        if missing_schools:
            missing_schools = [i + " (All)" for i in missing_schools]
            school_string = ", ".join(list(map(str, missing_schools))) + "."
            school_string = schools_with_missing_string + ", " + school_string
        else:
            school_string = schools_with_missing_string + "."
    else:
        if missing_schools:
            missing_schools = [i + " (All)" for i in missing_schools]
            school_string = ", ".join(list(map(str, missing_schools))) + "."
        else:
            school_string = "None."

    # Create string for categories for which the selected school has
    # no data. These categories are not shown at all.
    if missing_categories:
        category_string = ", ".join(list(map(str, missing_categories))) + "."
    else:
        category_string = "None."

    return final_data, category_string, school_string