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
    # info_categories
)
# from .load_data import (
#     get_school_index,
#     get_graduation_data
# )
# from .calculations import (
#     calculate_difference,
#     calculate_proficiency,
#     recalculate_total_proficiency,
#     calculate_graduation_rate,
#     calculate_sat_rate,
#     conditional_fillna
# )

# def process_k8_analysis_data(
#     data: pd.DataFrame, school_id: str
# ) -> pd.DataFrame:
#     """
#     Perform various operations on a dataframe returning with ILEARN/IREAD
#     data for the selected school. Used on academic_analysis page.

#     Args:
#         data (pd.DataFrame): ilearn/iread data
#         school_id (str): a four digit school number as a string
#     Returns:
#         pd.DataFrame: processed dataframe
#     """
#     data = data.reset_index(drop=True)

#     school_idx = data.index[data["School ID"] == np.int64(school_id)].tolist()[0]

#     school_info = data[["School Name", "School ID", "Low Grade", "High Grade"]].copy()

#     # filter
#     data = data.filter(
#         regex=r"Total Tested$|Total Proficient$|IREAD Pass N|IREAD Test N|Year|ELA and Math",
#         axis=1,
#     )
#     data = data[data.columns[~data.columns.str.contains(r"Female|Male")]]

#     # Drop columns for all categories where the values are NaN
#     data = data.loc[:, ~data.iloc[school_idx].isna()]

#     if len(data.index) < 1:
#         final_data = pd.DataFrame()

#     else:
#         calculated_data = calculate_proficiency(data)
        
#         # Add School Name/School ID back. We can do this because the index hasn't changed in
#         # data_proficiency, so it will still match with school_info
#         if len(school_info.index) > 0:
#             combined_data = pd.concat(
#                 [school_info, calculated_data], axis=1, join="inner"
#             )

#             # In order for an apples to apples comparison between School Total Proficiency,
#             # we need to recalculate it for the comparison schools using the same grade span
#             # as the selected school. E.g., school is k-5, comparison school is k-8, we
#             # recalculate comparison school totals using only grade k-5 data.

#             comparison_data = combined_data.loc[
#                 combined_data["School ID"] != np.int64(school_id)
#             ].copy()
#             school_data = combined_data.loc[
#                 combined_data["School ID"] == np.int64(school_id)
#             ].copy()

#             revised_school_totals = recalculate_total_proficiency(
#                 comparison_data, school_data
#             )

#             # replace current school total with revised data
#             comparison_data["Total|Math Proficient %"] = (
#                 comparison_data["School ID"]
#                 .map(
#                     revised_school_totals.set_index("School ID")[
#                         "Total|Math Proficient %"
#                     ]
#                 )
#                 .fillna(comparison_data["Total|Math Proficient %"])
#             )
#             comparison_data["Total|ELA Proficient %"] = (
#                 comparison_data["School ID"]
#                 .map(
#                     revised_school_totals.set_index("School ID")[
#                         "Total|ELA Proficient %"
#                     ]
#                 )
#                 .fillna(comparison_data["Total|ELA Proficient %"])
#             )

#             final_data = pd.concat([school_data, comparison_data])

#         # filter to remove columns used to calculate proficiency %
#         final_data = final_data.filter(
#             regex=r"\|ELA Proficient %$|\|Math Proficient %$|IREAD Proficient %|^Year|School Name|School ID|High Grade|Low Grade",
#             axis=1,
#         )

#         final_data = final_data.reset_index(drop=True)

#         final_data.columns = final_data.columns.astype(str)

#     return final_data

# def process_k8_info_data(data: pd.DataFrame) -> pd.DataFrame:
#     """
#     Process a dataframe with ILEARN/IREAD data including N-Size. Includes additional
#     formatting. Used on academic_information and academic_metrics pages.

#     Args:
#         data (pd.DataFrame): ilearn/iread data

#     Returns:
#         pd.DataFrame: removes categories with no data/calculates proficiency
#     """
#     data = data.reset_index(drop=True)

#     school_info = data[["School Name", "Low Grade", "High Grade"]].copy()

#     # filter (and drop ELA and Math Subject Category)
#     data = data.filter(
#         regex=r"Total Tested$|Total Proficient$|IREAD Pass N|IREAD Test N|Year",
#         axis=1,
#     )
#     data = data[data.columns[~data.columns.str.contains(r"ELA and Math")]]

#     # Drop all columns for a Category if the value of "Total Tested" for
#     # that Category is "0." This method works even if data is inconsistent,
#     # e.g., where no data could be (and is) alternately represented by NULL,
#     # None, or "0"
#     tested_cols = data.filter(regex="Total Tested").columns.tolist()

#     drop_columns = []

#     for col in tested_cols:
#         if (
#             pd.to_numeric(data[col], errors="coerce").sum() == 0
#             or data[col].isnull().all()
#         ):
#             match_string = " Total Tested"
#             matching_cols = data.columns[
#                 pd.Series(data.columns).str.startswith(col.split(match_string)[0])
#             ]
#             drop_columns.append(matching_cols.tolist())

#     drop_all = [i for sub_list in drop_columns for i in sub_list]

#     data = data.drop(drop_all, axis=1).copy()

#     if len(data.columns) <= 1:
#         final_data = pd.DataFrame()

#     else:
#         data_proficiency = calculate_proficiency(data)

#         # create new df with Total Tested and Test N (IREAD) values
#         data_tested = data_proficiency.filter(
#             regex="Total Tested|Test N|Year", axis=1
#         ).copy()

#         data_tested = (
#             data_tested.set_index("Year")
#             .T.rename_axis("Category")
#             .rename_axis(None, axis=1)
#             .reset_index()
#         )

#         data_tested = data_tested.rename(
#             columns={
#                 c: str(c) + "N-Size"
#                 for c in data_tested.columns
#                 if c not in ["Category"]
#             }
#         )

#         # Get rid of None types and replace 0's with NaN for tested values
#         # ensures eventual correct formatting to "-"
#         data_tested = data_tested.fillna(value=np.nan)
#         data_tested = data_tested.replace(0, np.nan)

#         # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
#         data_proficiency = data_proficiency.filter(
#             regex=r"\|ELA Proficient %$|\|Math Proficient %$|IREAD Proficient %|^Year$",
#             axis=1,
#         )

#         # add School Name column back (school data has School Name column,
#         # corp data does not)
#         if len(school_info.index) > 0:
#             data_proficiency = pd.concat(
#                 [data_proficiency, school_info], axis=1, join="inner"
#             )

#         data_proficiency = data_proficiency.reset_index(drop=True)

#         # transpose dataframes and clean headers
#         data_proficiency.columns = data_proficiency.columns.astype(str)
        
#         data_proficiency = (
#             data_proficiency.set_index("Year")
#             .T.rename_axis("Category")
#             .rename_axis(None, axis=1)
#             .reset_index()
#         )

#         data_proficiency = data_proficiency[
#             data_proficiency["Category"].str.contains("School Name") == False
#         ]

#         data_proficiency = data_proficiency.reset_index(drop=True)
#         data_proficiency = data_proficiency.rename(
#             columns={
#                 c: str(c) + "School"
#                 for c in data_proficiency.columns
#                 if c not in ["Category"]
#             }
#         )

#         # temporarily store Low Grade, and High Grade rows
#         other_rows = data_proficiency[
#             data_proficiency["Category"].str.contains(r"Low|High")
#         ]

#         # Merge Total Tested DF with Proficiency DF based on substring match

#         # add new column with substring values and drop old Category column
#         data_tested["Substring"] = data_tested["Category"].replace(
#             {" Total Tested": "", " Test N": ""}, regex=True
#         )

#         data_tested = data_tested.drop("Category", axis=1)

#         # this cross-merge and substring match process takes about .3s -
#         # there must be a faster way
#         final_data = data_proficiency.merge(data_tested, how="cross")

#         # Need to temporarily rename "English Learner" because otherwise it
#         # will match both "English" and "Non English"
#         final_data = final_data.replace(
#             {
#                 "Non English Language Learners": "Temp1",
#                 "English Language Learners": "Temp2",
#             },
#             regex=True,
#         )

#         # Filter rows - keeping only those rows where a substring is in Category
#         final_data = final_data[
#             [a in b for a, b in zip(final_data["Substring"], final_data["Category"])]
#         ]

#         final_data = final_data.replace(
#             {
#                 "Temp1": "Non English Language Learners",
#                 "Temp2": "English Language Learners",
#             },
#             regex=True,
#         )

#         final_data = final_data.drop("Substring", axis=1)
#         final_data = final_data.reset_index(drop=True)

#         # reorder columns for display
#         school_cols = [e for e in final_data.columns if "School" in e]
#         nsize_cols = [e for e in final_data.columns if "N-Size" in e]
#         school_cols.sort()
#         nsize_cols.sort()

#         final_cols = list(itertools.chain(*zip(school_cols, nsize_cols)))
#         final_cols.insert(0, "Category")

#         final_data = final_data[final_cols]

#         # Add Low Grade, and High Grade rows back (missing cols will populate with NaN)
#         # df's should have different indexes, but just to be safe, we will reset them both
#         # otherwise could remove the individual reset_index()
#         final_data = pd.concat(
#             [final_data.reset_index(drop=True), other_rows.reset_index(drop=True)],
#             axis=0,
#         ).reset_index(drop=True)

#         # replace NaN with specific values based on column name
#         final_data = conditional_fillna(final_data)

#     return final_data


# def process_k8_corp_academic_data(
#     corp_data: pd.DataFrame, school_data: pd.DataFrame
# ) -> pd.DataFrame:
#     """
#     Perform various operations on a dataframe with ILEARN/IREAD data at corporation
#     level (aggregated)

#     Args:
#         corp_data (pd.DataFrame): ilearn/iread data for local school corporation
#         school_data (pd.DataFrame): ilearn/iread data for selected school

#     Returns:
#         pd.DataFrame: processed dataframe
#     """
#     if len(corp_data.index) == 0:
#         corp_data = pd.DataFrame()

#     else:
#         corp_info = corp_data[["Corporation Name", "Corporation ID"]].copy()

#         # Filter and clean the dataframe
#         corp_data = corp_data.filter(
#             regex=r"Corporation ID|Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",
#             axis=1,
#         )

#         # Drop "ELA and Math"
#         corp_data = corp_data[
#             corp_data.columns[~corp_data.columns.str.contains(r"ELA and Math")]
#         ].copy()

#         for col in corp_data.columns:
#             corp_data[col] = pd.to_numeric(corp_data[col], errors="coerce")

#         # Drop all columns for a Category if the value of "Total Tested" for that Category is "0"
#         # This method works even if data is inconsistent, e.g., where no data could be (and is)
#         # alternately represented by NULL, None, or "0"
#         tested_cols = corp_data.filter(regex="Total Tested").columns.tolist()

#         drop_columns = []
#         for col in tested_cols:
#             if (
#                 pd.to_numeric(corp_data[col], errors="coerce").sum() == 0
#                 or corp_data[col].isnull().all()
#             ):
#                 match_string = " Total Tested"
#                 matching_cols = corp_data.columns[
#                     pd.Series(corp_data.columns).str.startswith(
#                         col.split(match_string)[0]
#                     )
#                 ]
#                 drop_columns.append(matching_cols.tolist())

#         drop_all = [i for sub_list in drop_columns for i in sub_list]

#         corp_data = corp_data.drop(drop_all, axis=1).copy()

#         corp_data = calculate_proficiency(corp_data)

#         if "IREAD Pass N" in corp_data.columns:
#             corp_data["IREAD Proficient %"] = pd.to_numeric(
#                 corp_data["IREAD Pass N"], errors="coerce"
#             ) / pd.to_numeric(corp_data["IREAD Test N"], errors="coerce")

#             # If either Test or Pass category had a "***" value, the resulting value will be
#             # NaN - we want it to display "***", so we just fillna
#             corp_data["IREAD Proficient %"] = corp_data["IREAD Proficient %"].fillna(
#                 "***"
#             )

#         # align Name and ID
#         corp_data = corp_data.rename(
#             columns={"Corporation Name": "School Name", "Corporation ID": "School ID"}
#         )

#         # recalculate total proficiency numbers using only school grades
#         # after transposing so school categories are column headers
#         school_grade_data = school_data.copy()
#         school_grade_data = (
#             school_grade_data.set_index("Category")
#             .T.rename_axis("Year")
#             .rename_axis(None, axis=1)
#             .reset_index()
#         )

#         revised_corp_totals = recalculate_total_proficiency(
#             corp_data, school_grade_data
#         )

#         # replace current school total with revised data
#         corp_data["Total|ELA Proficient %"] = revised_corp_totals[
#             "Total|ELA Proficient %"
#         ].values
#         corp_data["Total|Math Proficient %"] = revised_corp_totals[
#             "Total|Math Proficient %"
#         ].values

#         # filter to remove columns used to calculate the final proficiency (Total
#         # Tested and Total Proficient)
#         corp_data = corp_data.filter(
#             regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Proficient %|^Year$",
#             axis=1,
#         )

#         # add School Name column back - school data has School Name column, corp data does not
#         if len(corp_info.index) > 0:
#             corp_data = pd.concat([corp_data, corp_info], axis=1, join="inner")

#         corp_data = corp_data.reset_index(drop=True)

#         # transpose dataframes and clean headers
#         corp_data = (
#             corp_data.set_index("Year")
#             .T.rename_axis("Category")
#             .rename_axis(None, axis=1)
#             .reset_index()
#         )
#         corp_data = corp_data[
#             corp_data["Category"].str.contains("School Name") == False
#         ]
#         corp_data = corp_data.reset_index(drop=True)

#         # sort Year cols in ascending order (ignore Category)
#         corp_data = (
#             corp_data.set_index("Category")
#             .sort_index(ascending=True, axis=1)
#             .reset_index()
#         )

#         corp_data.columns = corp_data.columns.astype(str)

#     return corp_data


# def filter_high_school_academic_data(data: pd.DataFrame) -> pd.DataFrame:
#     """
#     Process a dataframe with grad rate/sat data. Used for Academic Information and
#     # Metrics only. Drop columns without data. Generally, we want to keep "result"
#     # (e.g., "Graduates", "Pass N", "Benchmark") columns with "0" values if the
#     # "tested" (e.g., "Cohort Count", "Total Tested", "Test N") values are greater
#     # than "0". The data is pretty shitty as well, using blank, null, and "0"
#     # interchangeably depending on the type. This makes it difficult to simply use
#     # dropna() or masking with any() because they may erroneously drop a 0 value
#     # that we want to keep. So we need to iterate through each tested category,
#     # if it is NaN or 0, we drop it and all associate categories.

#     Args:
#         data (pd.DataFrame): grad rate/sat data

#     Returns:
#         pd.DataFrame: removes categories with no data/calculates grad rate/benchmark
#         proficiency
#     """

#     data = data.replace({"^": "***"})

#     # school data: coerce to numeric but keep strings ("***")
#     for col in data.columns:
#         data[col] = pd.to_numeric(data[col], errors="coerce").fillna(data[col])

#     # Drop: "Graduation Rate", "Percent Pass", "ELA and Math" (never need these)
#     # Also Drop "Pass N" and "Test N" (Grade 10 ECA is no longer used)
#     data = data[
#         data.columns[
#             ~data.columns.str.contains(
#                 r"Graduation Rate|Percent Pass|ELA and Math|Test N|Pass N"
#             )
#         ]
#     ].copy()

#     # Get N-Size for all categories with data

#     # Drop: all SAT and Grad Rate related columns ("Total Tested|Cohort Count)
#     # for a Category if the value of "Cohort Count" or "Total Tested" for that Category is "0"
#     tested_cols = data.filter(regex="Total Tested|Cohort Count").columns.tolist()
#     drop_columns = []

#     for col in tested_cols:
#         if (
#             pd.to_numeric(data[col], errors="coerce").sum() == 0
#             or data[col].isnull().all()
#         ):
#             if "Total Tested" in col:
#                 match_string = " Total Tested"
#             elif "Cohort Count" in col:
#                 match_string = "|Cohort Count"

#             matching_cols = data.columns[
#                 pd.Series(data.columns).str.startswith(col.split(match_string)[0])
#             ]
#             drop_columns.append(matching_cols.tolist())

#     drop_all = [i for sub_list in drop_columns for i in sub_list]

#     data = data.drop(drop_all, axis=1).copy()

#     if len(data.columns) <= 1:
#         data = pd.DataFrame()

#     return data


# def process_high_school_academic_data(
#     data: pd.DataFrame, school_id: str
# ) -> pd.DataFrame:
#     """
#     Perform various operations on a dataframe with graduation rate and SAT data.

#     Args:
#         data (pd.DataFrame): grad rate/sat data
#         school_id (str): a four digit school number as a string

#     Returns:
#         pd.DataFrame: removes categories with no data/calculates grad rate/benchmark
#         proficiency
#     """
#     school_information = get_school_index(school_id)

#     # use these to determine if data belongs to school or corporation
#     school_geo_code = school_information["GEO Corp"].values[0]

#     school_type = school_information["School Type"].values[0]

#     # All df at this point should have a minimum of eight cols (Year, Corporation ID,
#     # Corporation Name, School ID, School Name, School Type, AHS|Grad, & All AHS|CCR). If
#     # a df has eight or fewer cols, it means they have no data. Note this includes an AHS
#     # because if they have no grad data then both AHS|Grad and AHS|CCR will be None.
#     if (len(data.index) == 0) or (len(data.columns) <= 8) or (data.empty):
#         final_data = pd.DataFrame()

#     else:
#         # Ensure geo_code is always at index 0
#         data = data.reset_index(drop=True)
#         data_geo_code = data["Corporation ID"][0]

#         # it is "corp" data if "Corporation ID" is equal to the value of the school"s
#         # "GEO Corp".
#         if data_geo_code == school_geo_code:
#             school_info = data[["Corporation Name"]].copy()
#         else:
#             school_info = data[["School Name"]].copy()

#             # school data: coerce, but keep strings ("***" and "^")
#             for col in data.columns:
#                 data[col] = pd.to_numeric(data[col], errors="coerce").fillna(data[col])

#         # Get "Total Tested" & "Cohort Count" (nsize) data and store in separate dataframe.
#         data_tested = data.filter(regex="Total Tested|Cohort Count|Year", axis=1).copy()
#         data_tested = (
#             data_tested.set_index("Year")
#             .T.rename_axis("Category")
#             .rename_axis(None, axis=1)
#             .reset_index()
#         )

#         # NOTE: Currently do not use CN-Size (Corp N-Size) for anything, but leaving
#         # here just in case.
#         if data_geo_code == school_geo_code:
#             data_tested = data_tested.rename(
#                 columns={
#                     c: str(c) + "CN-Size"
#                     for c in data_tested.columns
#                     if c not in ["Category"]
#                 }
#             )
#         else:
#             data_tested = data_tested.rename(
#                 columns={
#                     c: str(c) + "SN-Size"
#                     for c in data_tested.columns
#                     if c not in ["Category"]
#                 }
#             )

#         # Filter the proficiency df
#         data = data.filter(
#             regex=r"Cohort Count$|Graduates$|AHS|Benchmark|Total Tested|^Year$", axis=1
#         )

#         # remove "ELA and Math" columns #TODO: Check, EBRW?
#         data = data.drop(list(data.filter(regex="EBRW and Math")), axis=1)

#         if data_geo_code == school_geo_code:
#             # group corp dataframe by year and sum all rows for each category
#             data = data.groupby(["Year"]).sum(numeric_only=True)

#             data = data.reset_index()

#         # Calculate Grad Rate
#         if "Total|Cohort Count" in data.columns:
#             data = calculate_graduation_rate(data)

#         # Calculate SAT Rates #
#         if "Total|EBRW Total Tested" in data.columns:
#             data = calculate_sat_rate(data)

#         # Calculate AHS Only Data #
#         # NOTE: All other values pulled from HS dataframe required for AHS calculations
#         # should be addressed in this block

#         # CCR Rate
#         if school_type == "AHS":
#             if "AHS|CCR" in data.columns:
#                 data["AHS|CCR"] = pd.to_numeric(data["AHS|CCR"], errors="coerce")

#             if "AHS|Grad All" in data.columns:
#                 data["AHS|Grad All"] = pd.to_numeric(
#                     data["AHS|Grad All"], errors="coerce"
#                 )

#             if {"AHS|CCR", "AHS|Grad All"}.issubset(data.columns):
#                 data["CCR Percentage"] = data["AHS|CCR"] / data["AHS|Grad All"]

#         # Need to check data again to see if anything is left after the above operations
#         # if all columns in data other than the 1st (Year) are null then return empty df
#         if data.iloc[:, 1:].isna().all().all():
#             final_data = pd.DataFrame()

#         else:
#             data = data.filter(
#                 regex=r"^Category|Graduation Rate$|CCR Percentage|Pass Rate$|Benchmark %|Below|Approaching|At|^CCR Percentage|^Year$",  # ^Strength of Diploma
#                 axis=1,
#             )

#             school_info = school_info.reset_index(drop=True)
#             data = data.reset_index(drop=True)

#             data = pd.concat([data, school_info], axis=1, join="inner")

#             data.columns = data.columns.astype(str)

#             data = (
#                 data.set_index("Year")
#                 .T.rename_axis("Category")
#                 .rename_axis(None, axis=1)
#                 .reset_index()
#             )

#             # State/Federal grade rows not used at this point
#             data = data[
#                 data["Category"].str.contains("State Grade|Federal Rating|School Name")
#                 == False
#             ]

#             if data_geo_code == school_geo_code:
#                 data = data.rename(
#                     columns={
#                         c: str(c) + "Corp"
#                         for c in data.columns
#                         if c not in ["Category"]
#                     }
#                 )
#             else:
#                 data = data.rename(
#                     columns={
#                         c: str(c) + "School"
#                         for c in data.columns
#                         if c not in ["Category"]
#                     }
#                 )

#             data = data.reset_index(drop=True)

#             # make sure there are no lingering NoneTypes
#             data = data.fillna(value=np.nan)

#             # Merge Total Tested DF with Proficiency DF based on substring match

#             # add new column with substring values and drop old Category column
#             data_tested["Substring"] = data_tested["Category"].replace(
#                 {" Total Tested": "", "\|Cohort Count": "|Graduation"}, regex=True
#             )

#             data_tested = data_tested.drop("Category", axis=1)

#             # NOTE: the cross-merge and substring match process takes about .3s,
#             # is there a faster way?
#             final_data = data.merge(data_tested, how="cross")

#             # keep only those rows where substring is in Category
#             # Need to temporarily rename "English Learner" because otherwise it
#             # will match both "English" and "Non English"
#             final_data = final_data.replace(
#                 {
#                     "Non English Language Learners": "Temp1",
#                     "English Language Learners": "Temp2",
#                 },
#                 regex=True,
#             )

#             final_data = final_data[
#                 [
#                     a in b
#                     for a, b in zip(final_data["Substring"], final_data["Category"])
#                 ]
#             ]

#             final_data = final_data.replace(
#                 {
#                     "Temp1": "Non English Language Learners",
#                     "Temp2": "English Language Learners",
#                 },
#                 regex=True,
#             )

#             final_data = final_data.drop("Substring", axis=1)
#             final_data = final_data.reset_index(drop=True)

#             # reorder columns for display
#             # NOTE: This final data keeps the Corp N-Size cols, which are not used
#             # currently. We drop them later in the merge_high_school_data() step.
#             if data_geo_code == school_geo_code:
#                 school_cols = [e for e in final_data.columns if "Corp" in e]
#                 nsize_cols = [e for e in final_data.columns if "CN-Size" in e]
#             else:
#                 school_cols = [e for e in final_data.columns if "School" in e]
#                 nsize_cols = [e for e in final_data.columns if "SN-Size" in e]

#             school_cols.sort()
#             nsize_cols.sort()

#             final_cols = list(itertools.chain(*zip(school_cols, nsize_cols)))

#             final_cols.insert(0, "Category")
#             final_data = final_data[final_cols]

#     return final_data


# def process_comparable_high_school_academic_data(raw_data: pd.DataFrame) -> pd.DataFrame:
#     """
#     Perform various operations on a dataframe with graduation rate/SAT data for display
#     in charts and tables on the academic analysis pages.

#     Args:
#         raw_data (pd.DataFrame): grad rate/sat data

#     Returns:
#         pd.DataFrame: removes categories with no data and calculates grad rate & benchmark proficiency
#     """

#     # All df at this point should have a minimum of eight cols (Year, Corporation ID,
#     # Corporation Name, School ID, School Name, School Type, AHS|Grad, & All AHS|CCR). If
#     # a df has eight or fewer cols, it means they have no data. Note this includes an AHS
#     # because if they have no grad data then both AHS|Grad and AHS|CCR will be None.
#     if (len(raw_data.index) == 0) or (len(raw_data.columns) <= 8) or (raw_data.empty):
#         data = pd.DataFrame()

#     else:
#         school_info = raw_data[["School Name", "School ID"]].copy()
#         school_type = raw_data["School Type"].values[0]

#         # school data: coerce, but keep strings ("***" and "^")
#         for col in raw_data.columns:
#             raw_data[col] = pd.to_numeric(raw_data[col], errors="coerce").fillna(
#                 raw_data[col]
#             )

#         data = raw_data.filter(
#             regex=r"Cohort Count$|Graduates$|AHS|At Benchmark|Total Tested|Year|Low Grade|High Grade",
#             axis=1,
#         ).copy()

#         # Calculate Grad Rate

#         # NOTE: In spring of 2020, SBOE waived the GQE requirement for students in the
#         # 2020 cohort who where otherwise on schedule to graduate, so, for the 2020
#         # cohort, there were no "waiver" graduates (which means no Non Waiver data).
#         # so we replace 0 with NaN (to ensure a NaN result rather than 0)
#         if "Total|Cohort Count" in data.columns:
#             data = calculate_graduation_rate(data)

#         # Calculate SAT Rates #
#         if "Total|EBRW Total Tested" in data.columns:

#             # NOTE: Currently not displaying EBRW and Math
#             data = data.drop(list(data.filter(regex="EBRW and Math")), axis=1)

#             data = calculate_sat_rate(data)

#         # Calculate AHS Only Data #
#         # NOTE: Any other values that exist in the HS dataframe and that are required
#         # for AHS calculations should be addressed in this block

#         # CCR Rate
#         if school_type == "AHS":
#             if "AHS|CCR" in data.columns:
#                 data["AHS|CCR"] = pd.to_numeric(data["AHS|CCR"], errors="coerce")

#             if "AHS|Grad All" in data.columns:
#                 data["AHS|Grad All"] = pd.to_numeric(
#                     data["AHS|Grad All"], errors="coerce"
#                 )

#             if {"AHS|CCR", "AHS|Grad All"}.issubset(data.columns):
#                 data["CCR Percentage"] = data["AHS|CCR"] / data["AHS|Grad All"]

#         # Need to check data again to see if anything is left after the above operations
#         # if all columns in data other than the 1st (Year) are null then return empty df

#         if data.iloc[:, 1:].isna().all().all():
#             data = pd.DataFrame()

#         else:
#             data = data.filter(
#                 regex=r"Graduation Rate$|CCR Percentage|Benchmark \%|^CCR Percentage|^Year$|Low Grade|High Grade",
#                 axis=1,
#             )

#             school_info = school_info.reset_index(drop=True)
#             data = data.reset_index(drop=True)

#             data = pd.concat([data, school_info], axis=1, join="inner")

#             data.columns = data.columns.astype(str)

#             data = (
#                 data.set_index("Year")
#                 .T.rename_axis("Category")
#                 .rename_axis(None, axis=1)
#                 .reset_index()
#             )

#             data = data.reset_index(drop=True)

#             data = data.fillna(value=np.nan)

#     return data


# filters tested (nsize) cols and proficiency calculations into
# separate dataframes, performs some cleanup, including a transposition,
# moving years to column headers and listing categories in their own
# columns and then cross-merging the two. variables change depending on
# whether we are analyzing a school or a corporation
def transpose_data(df,params):

    # Determine whether df is of charter school or school corporation.
    # Need to check both. Generally the Name and IDs will be the same for a
    # school corporation, while a charter will have different IDs. However,
    # in the event that a charter does have the same ID as the corp, it will
    # have different Names- so we need both tests to be true to be sure the
    # dataframe belonds to a corporation.
    # NOTE: currently keeping record of N-Size data for both school and corp
    # although we do not currently use corp n-size
    if ((df["School ID"] == df["Corporation ID"]) & 
        (df["School Name"] == df["Corporation Name"])).sum() > 1:

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
            c: str(c) + nsize_id #"N-Size"
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
        [
            a in b
            for a, b in zip(merged_data["Substring"], merged_data["Category"])
        ]
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


# def merge_high_school_data(
#     all_school_data: pd.DataFrame, all_corp_data: pd.DataFrame
# ) -> pd.DataFrame:
#     """
#     Perform various operations on two dataframes, selected school and local school corporaiton
#     and ultimately merge them

#     Args:
#     all_school_data (pd.DataFrame): school data
#     all_corp_data (pd.DataFrame): corp data

#     Returns:
#         final_hs_academic_data (pd.DataFrame): processed dataframe
#     """
#     all_school_data.columns = all_school_data.columns.astype(str)
#     all_corp_data.columns = all_corp_data.columns.astype(str)

#     # Add State Graduation Average to Corp DataFrame
#     state_grad_average_corp = get_graduation_data()

#     all_corp_data = pd.concat(
#         [
#             all_corp_data.reset_index(drop=True),
#             state_grad_average_corp.reset_index(drop=True),
#         ],
#         axis=0,
#     ).reset_index(drop=True)

#     # For the school calculation we duplicate the school"s Total Graduation rate and
#     # rename it "State Grad Average" - when the difference is calculated
#     # between the two data frames, the difference between the Total Graduation Rates
#     # will be School minus Corportion and the difference between State Grad Average Rates
#     # will be School minus State Average

#     # If no Total Graduation Rate Category exists for a school, we add it with all NaNs
#     if "Total Graduation Rate" not in all_school_data["Category"].values:
        
#         # add row of all nan (by enlargement) and set Category value
#         all_school_data.loc[len(all_school_data)] = np.nan
#         all_school_data.loc[
#             all_school_data.index[-1], "Category"
#         ] = "Total Graduation Rate"

#     duplicate_row = all_school_data[
#         all_school_data["Category"] == "Total Graduation Rate"
#     ].copy()
#     duplicate_row["Category"] = "State Graduation Average"
#     all_school_data = pd.concat(
#         [all_school_data, duplicate_row], axis=0, ignore_index=True
#     )

#     # Clean up and merge school and corporation dataframes
#     year_cols = list(all_school_data.columns[:0:-1])
#     year_cols = [c[0:4] for c in year_cols]  # keeps only YYYY part of string
#     year_cols = list(set(year_cols))
#     year_cols.sort()

#     # last bit of cleanup is to drop "Corporation Name" Category from corp df
#     all_corp_data = all_corp_data.drop(
#         all_corp_data.loc[all_corp_data["Category"] == "Corporation Name"].index
#     ).reset_index(drop=True)

#     # Create list of alternating columns
#     # we technically do not need the Corporation N-Size at this point, but
#     # we will keep it just in case. We drop it in the final df
#     corp_cols = [e for e in all_corp_data.columns if "Corp" in e]
#     cnsize_cols = [e for e in all_corp_data.columns if "CN-Size" in e]
#     school_cols = [e for e in all_school_data.columns if "School" in e]
#     snsize_cols = [e for e in all_school_data.columns if "SN-Size" in e]
#     school_cols.sort()
#     snsize_cols.sort()
#     corp_cols.sort()
#     cnsize_cols.sort()

#     result_cols = [str(s) + "Diff" for s in year_cols]

#     merged_cols = list(
#         itertools.chain(*zip(school_cols, snsize_cols, corp_cols, cnsize_cols))
#     )
#     merged_cols.insert(0, "Category")

#     hs_merged_data = all_school_data.merge(all_corp_data, on="Category", how="left")
#     hs_merged_data = hs_merged_data[merged_cols]
    
#     tmp_category = all_school_data["Category"]
#     all_school_data = all_school_data.drop("Category", axis=1)
#     all_corp_data = all_corp_data.drop("Category", axis=1)

#     all_school_data = all_school_data.fillna(value=np.nan)
#     all_corp_data = all_corp_data.fillna(value=np.nan)

#     # calculate difference between two dataframes (for loop
#     # not great - but still relatively fast)
#     hs_results = pd.DataFrame()
#     for y in year_cols:
#         hs_results[y] = calculate_difference(
#             all_school_data[y + "School"], all_corp_data[y + "Corp"]
#         )
                
#     # Create final column order - dropping the corp avg and corp N-Size cols
#     # (by not including them in the list) because we do not display them
#     final_cols = list(itertools.chain(*zip(school_cols, snsize_cols, result_cols)))
#     final_cols.insert(0, "Category")

#     hs_results = hs_results.set_axis(result_cols, axis=1)
#     hs_results.insert(loc=0, column="Category", value=tmp_category)

#     final_hs_academic_data = hs_merged_data.merge(hs_results, on="Category", how="left")
#     final_hs_academic_data = final_hs_academic_data[final_cols]

#     final_hs_academic_data.columns = final_hs_academic_data.columns.str.replace(
#         "SN-Size", "N-Size", regex=True
#     )

#     return final_hs_academic_data


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

    data["Difference"] = data["162 Days"] - data["Majority Enrolled"]

    # step 4: get into proper format for display as multi-header DataTable

    # create final category
    data["Category"] = data[category] + "|" + data["Subject"]

    # filter unneeded columns
    final_data = data.filter(
        regex=r"Test Year|Category|Majority Enrolled|162 Days|Difference",
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
    fig_data = fig_data.drop("Difference", axis=1)
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
        cols.append(str(y) + "Difference")

    # pivot df from wide to long" add years to each column name; move year to
    # front of column name; sort and reset_index
    table_data = table_data.pivot(index=["Category"], columns="Test Year")

    table_data.columns = table_data.columns.map(lambda x: "".join(map(str, x)))
    table_data.columns = table_data.columns.map(lambda x: x[-4:] + x[:-4])
    table_data = table_data[cols]
    table_data = table_data.reset_index()

    return fig_data, table_data


# def merge_schools(
#     school_data: pd.DataFrame,
#     corporation_data: pd.DataFrame,
#     comparison_data: pd.DataFrame,
#     categories: list,
#     corp_name: str,
# ) -> pd.DataFrame:
#     """
#     Takes three dataframes of school academic data, drops Categories not tested by the
#     school and merges them.

#     Args:
#         school_data (pd.DataFrame): academic data from the selected school
#         corporation_data (pd.DataFrame): academic data from the school corporation
#         where the school is located
#         comparison_data (pd.DataFrame): academic data from comparable schools (may
#         or may not be in school corp)
#         categories (list): a list of academic categories
#         corp_name (str): the name of the school corporation

#     Returns:
#         final_data (pd.DataFrame): all dataframes cleaned up and combined
#     """
#     categories = [
#         c for c in categories if c not in ["School Name", "Low Grade", "High Grade"]
#     ]
#     all_categories = categories + info_categories

#     school_columns = [i for i in categories if i in school_data.columns]

#     # sort corp data by the school columns (this excludes any categories
#     # not in the school data)
#     corporation_data = corporation_data.loc[
#         :, corporation_data.columns.isin(school_columns)
#     ].copy()

#     # add the school corporation name
#     corporation_data["School Name"] = corp_name

#     # concatenate the school and corporation dataframes, filling empty values (e.g., Low and High Grade) with ""
#     first_merge_data = pd.concat([school_data, corporation_data], sort=False).fillna("")

#     comparison_data = comparison_data.loc[
#         :, comparison_data.columns.isin(all_categories)
#     ].copy()

#     # concatenate school/corp and comparison dataframes
#     combined_data = pd.concat([first_merge_data, comparison_data])
#     combined_data = combined_data.reset_index(drop=True)

#     return combined_data
