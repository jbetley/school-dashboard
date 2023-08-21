#########################################
# ICSB Dashboard - Clean & Process Data #
#########################################
# author:   jbetley
# version:  1.09
# date:     08/14/23

# TODO: Explore serverside disk caching for data loading
#https://community.plotly.com/t/the-value-of-the-global-variable-does-not-change-when-background-true-is-set-in-the-python-dash-callback/73835

# import time
from typing import Tuple
import pandas as pd
import numpy as np
import itertools

from .load_data import grades, ethnicity, subgroup, get_school_index, get_graduation_data
from .calculations import calculate_percentage, calculate_difference, calculate_proficiency, recalculate_total_proficiency, \
    calculate_graduation_rate, calculate_sat_rate, conditional_fillna, get_excluded_years

# NOTE: No K8 academic data exists for 2020
print("#### Loading Data. . . . . ####")

def get_attendance_data(data: pd.DataFrame, year: str) -> pd.DataFrame:

    excluded_years = get_excluded_years(year)

    demographic_data = data[~data["Year"].isin(excluded_years)]
    attendance_data = demographic_data[["Year", "Avg Attendance"]]

    # drop years with no data
    attendance_data = attendance_data[attendance_data["Avg Attendance"].notnull()]

    attendance_rate = (attendance_data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

    attendance_rate["Category"] =  attendance_rate["Category"].replace(["Avg Attendance"], "Attendance Rate")

    attendance_rate = conditional_fillna(attendance_rate)

    attendance_rate.columns = attendance_rate.columns.astype(str)

    for col in attendance_rate.columns:
        attendance_rate[col] = pd.to_numeric(attendance_rate[col], errors="coerce").fillna(attendance_rate[col]).tolist()

    return attendance_rate

def process_k8_academic_data(data: pd.DataFrame) -> pd.DataFrame:

    data = data.reset_index(drop = True)

    school_info = data[["School Name","Low Grade","High Grade"]].copy()

    # filter (and drop ELA and Math Subject Category)
    data = data.filter(regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",axis=1)
    data = data[data.columns[~data.columns.str.contains(r"ELA and Math")]]
    
    # NOTE: update is twice as fast as fillna?? (.015s vs .045s)
    data.update(data.apply(pd.to_numeric, errors="coerce"))
    
    # Drop all columns for a Category if the value of "Total Tested" for that Category is "0"
    # This method works even if data is inconsistent, e.g., where no data could be (and is)
    # alternately represented by NULL, None, or "0"
    tested_cols = data.filter(regex="Total Tested").columns.tolist()

    drop_columns=[]

    for col in tested_cols:
        if pd.to_numeric(data[col], errors="coerce").sum() == 0 or data[col].isnull().all():

            match_string = " Total Tested"
            matching_cols = data.columns[pd.Series(data.columns).str.startswith(col.split(match_string)[0])]
            drop_columns.append(matching_cols.tolist())   

    drop_all = [i for sub_list in drop_columns for i in sub_list]

    data = data.drop(drop_all, axis=1).copy()

    if len(data.columns) <= 1:
        
        final_data = pd.DataFrame()

    else:

        data_proficiency = calculate_proficiency(data)

        # separately calculate IREAD Proficiency
        if "IREAD Test N" in data.columns:
            data["IREAD Proficient %"] =  calculate_percentage(data["IREAD Pass N"],data["IREAD Test N"])
        
        # create new df with Total Tested and Test N (IREAD) values
        data_tested = data_proficiency.filter(regex="Total Tested|Test N|Year", axis=1).copy()
        data_tested = (data_tested.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())
        data_tested = data_tested.rename(columns={c: str(c)+"N-Size" for c in data_tested.columns if c not in ["Category"]})

        # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
        data_proficiency = data_proficiency.filter(regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Proficient %|^Year$", axis=1)

        # add School Name column back (school data has School Name column, corp data does not)
        if len(school_info.index) > 0:
            data_proficiency = pd.concat([data_proficiency, school_info], axis=1, join="inner")

        data_proficiency = data_proficiency.reset_index(drop=True)

        # transpose dataframes and clean headers    
        data_proficiency.columns = data_proficiency.columns.astype(str)
        data_proficiency = (data_proficiency.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())
        data_proficiency = data_proficiency[data_proficiency["Category"].str.contains("School Name") == False]
        data_proficiency = data_proficiency.reset_index(drop=True)
        data_proficiency = data_proficiency.rename(columns={c: str(c)+"School" for c in data_proficiency.columns if c not in ["Category"]})

        # temporarily store Low Grade, and High Grade rows
        other_rows = data_proficiency[data_proficiency["Category"].str.contains(r"Low|High")]

        # Merge Total Tested DF with Proficiency DF based on substring match

        # add new column with substring values and drop old Category column
        data_tested["Substring"] = data_tested["Category"].replace({" Total Tested": "", " Test N": ""}, regex=True)
        data_tested = data_tested.drop("Category", axis=1)

        # this cross-merge and substring match process takes about .3s - there must be a faster way
        # t20 = time.process_time()

        final_data = data_proficiency.merge(data_tested, how="cross")

        # Need to temporarily rename "English Learner" because otherwise it 
        # will match both "English" and "Non English"
        final_data = final_data.replace({"Non English Language Learners": "Temp1", "English Language Learners": "Temp2"}, regex=True)

        # Filter rows - keeping only those rows where a substring is in Category
        final_data = final_data[[a in b for a, b in zip(final_data["Substring"], final_data["Category"])]]

        final_data = final_data.replace({"Temp1": "Non English Language Learners", "Temp2": "English Language Learners"}, regex=True)      

        final_data = final_data.drop("Substring", axis=1)
        final_data = final_data.reset_index(drop=True)

        # reorder columns for display
        school_cols = [e for e in final_data.columns if "School" in e]
        nsize_cols = [e for e in final_data.columns if "N-Size" in e]
        school_cols.sort(reverse=True)
        nsize_cols.sort(reverse=True)

        final_cols = list(itertools.chain(*zip(school_cols, nsize_cols)))
        final_cols.insert(0, "Category")
        
        final_data = final_data[final_cols]
        
        # Add Low Grade, and High Grade rows back (missing cols will populate with NaN)
        # df"s should have different indexes, but just to be safe, we will reset them both
        # otherwise could remove the individual reset_index()
        final_data = pd.concat([final_data.reset_index(drop=True), other_rows.reset_index(drop=True)], axis=0).reset_index(drop=True)

        # print(f"Time to Cross Merge : " + str(time.process_time() - t20))    

    return final_data

def process_k8_corp_academic_data(corp_data: pd.DataFrame, school_data: pd.DataFrame) -> pd.DataFrame:

    if len(corp_data.index) == 0:
        corp_data = pd.DataFrame()
    
    else:
        corp_info = corp_data[["Corporation Name"]].copy()

        # Filter and clean the dataframe
        corp_data = corp_data.filter(regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",axis=1)

        # Drop "ELA and Math"
        corp_data = corp_data[corp_data.columns[~corp_data.columns.str.contains(r"ELA and Math")]].copy()

        for col in corp_data.columns:
            corp_data[col] = pd.to_numeric(corp_data[col], errors="coerce")

        # Drop all columns for a Category if the value of "Total Tested" for that Category is "0"
        # This method works even if data is inconsistent, e.g., where no data could be (and is)
        # alternately represented by NULL, None, or "0"
        tested_cols = corp_data.filter(regex="Total Tested").columns.tolist()

        drop_columns=[]
        for col in tested_cols:
            if pd.to_numeric(corp_data[col], errors="coerce").sum() == 0 or corp_data[col].isnull().all():

                match_string = " Total Tested"
                matching_cols = corp_data.columns[pd.Series(corp_data.columns).str.startswith(col.split(match_string)[0])]
                drop_columns.append(matching_cols.tolist())   

        drop_all = [i for sub_list in drop_columns for i in sub_list]

        corp_data = corp_data.drop(drop_all, axis=1).copy()

        corp_data = calculate_proficiency(corp_data)

        if "IREAD Pass N" in corp_data.columns:
            corp_data["IREAD Proficient %"] = pd.to_numeric(corp_data["IREAD Pass N"], errors="coerce") \
                / pd.to_numeric(corp_data["IREAD Test N"], errors="coerce")

            # If either Test or Pass category had a "***" value, the resulting value will be 
            # NaN - we want it to display "***", so we just fillna
            corp_data["IREAD Proficient %"] = corp_data["IREAD Proficient %"].fillna("***")

        # recalculate total proficiency numbers using only school grades
        corp_data = recalculate_total_proficiency(corp_data, school_data)        
        
        # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
        corp_data = corp_data.filter(regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Proficient %|^Year$", axis=1)

        # add School Name column back - school data has School Name column, corp data does not
        if len(corp_info.index) > 0:
            corp_data = pd.concat([corp_data, corp_info], axis=1, join="inner")

        corp_data = corp_data.reset_index(drop=True)

        # transpose dataframes and clean headers            
        corp_data = (corp_data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())
        corp_data = corp_data[corp_data["Category"].str.contains("School Name") == False]
        corp_data = corp_data.reset_index(drop=True)
        corp_data.columns = corp_data.columns.astype(str)

    return corp_data

def filter_high_school_academic_data(data: pd.DataFrame) -> pd.DataFrame:
    # NOTE: Drop columns without data. Generally, we want to keep "result" (e.g., "Graduates", "Pass N",
    # "Benchmark") columns with "0" values if the "tested" (e.g., "Cohort Count", "Total Tested",
    # "Test N") values are greater than "0". The data is pretty shitty as well, using blank, null,
    # and "0" interchangeably depending on the type. This makes it difficult to simply use dropna() or
    # masking with any() because they may erroneously drop a 0 value that we want to keep. So we need to
    # iterate through each tested category, if it is NaN or 0, we drop it and all associate categories.

    data = data.replace({"^": "***"})

    # school data: coerce to numeric but keep strings ("***")
    for col in data.columns:
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(data[col])

    # Drop: "Graduation Rate", "Percent Pass", "ELA and Math" (never need these)
    # Also Drop "Pass N" and "Test N" (Grade 10 ECA is no longer used)
    data = data[data.columns[~data.columns.str.contains(r"Graduation Rate|Percent Pass|ELA and Math|Test N|Pass N")]].copy()

    # Drop: all SAT related columns ("Approaching Benchmark", "At Benchmark", etc.)
    # for a Category if the value of "Total Tested" for that Category is "0"
    tested_cols = data.filter(regex="Total Tested|Cohort Count").columns.tolist() #|Test N").columns.tolist()
    drop_columns=[]

    for col in tested_cols:
        if pd.to_numeric(data[col], errors="coerce").sum() == 0 or data[col].isnull().all():

            if "Total Tested" in col:
                match_string = " Total Tested"
            elif "Cohort Count" in col:
                match_string = "|Cohort Count"
            # elif "Test N" in col:
            #     match_string = " Test N"

            matching_cols = data.columns[pd.Series(data.columns).str.startswith(col.split(match_string)[0])]
            drop_columns.append(matching_cols.tolist())   

    drop_all = [i for sub_list in drop_columns for i in sub_list]

    # ALT: data = data.loc[:,~data.columns.str.contains(drop_all, case=False)] 
    data = data.drop(drop_all, axis=1).copy()

    if len(data.columns) <= 1:
        
        data = pd.DataFrame()

    return data
    
def process_high_school_academic_data(data: pd.DataFrame, school: str) -> pd.DataFrame:

    school_information = get_school_index(school)

    # use these to determine if data belongs to school or corporation
    school_geo_code = school_information["GEO Corp"].values[0]

    school_type = school_information["School Type"].values[0]

    # All df at this point should have a minimum of eight cols (Year, Corporation ID,
    # Corporation Name, School ID, School Name, School Type, AHS|Grad, & All AHS|CCR). If
    # a df has eight or fewer cols, it means they have no data. Note this includes an AHS
    # because if they have no grad data then both AHS|Grad and AHS|CCR will be None.
    if (len(data.index) == 0) or (len(data.columns) <= 8) or (data.empty):

        final_data = pd.DataFrame()
    
    else:

         # Ensure geo_code is always at index 0
        data = data.reset_index(drop = True)
        data_geo_code = data["Corporation ID"][0]
        
        # it is "corp" data if "Corporation ID" is equal to the value of the school"s "GEO Corp".
        if data_geo_code == school_geo_code:
            school_info = data[["Corporation Name"]].copy()
        else:
            school_info = data[["School Name"]].copy()
            
            # school data: coerce, but keep strings ("***" and "^")
            for col in data.columns:
                data[col] = pd.to_numeric(data[col], errors="coerce").fillna(data[col])

        # Get "Total Tested" & "Cohort Count" (nsize) data and store in separate dataframe.
        data_tested = data.filter(regex="Total Tested|Cohort Count|Year", axis=1).copy()
        data_tested = (data_tested.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

        #TODO: remove CN-Size altogether
        # temp name N-Size cols in order to differentiate.
        if data_geo_code == school_geo_code:
            data_tested = data_tested.rename(columns={c: str(c)+"CN-Size" for c in data_tested.columns if c not in ["Category"]})
        else:
            data_tested = data_tested.rename(columns={c: str(c)+"SN-Size" for c in data_tested.columns if c not in ["Category"]})

        # Filter the proficiency df
        data = data.filter(regex=r"Cohort Count$|Graduates$|AHS|Benchmark|Total Tested|^Year$", axis=1)

        # remove "ELA and Math" columns (NOTE: Comment this out to retain "ELA and Math" columns)
        data = data.drop(list(data.filter(regex="ELA and Math")), axis=1)

        if data_geo_code == school_geo_code:

            # group corp dataframe by year and sum all rows for each category
            data = data.groupby(["Year"]).sum(numeric_only=True)
            
            # reverse order of rows (Year) and reset index to bring Year back as column
            data = data.loc[::-1].reset_index()

        # Calculate Grad Rate
        if "Total|Cohort Count" in data.columns:
            data = calculate_graduation_rate(data)

        # Calculate Non Waiver Grad Rate #
        # NOTE: In spring of 2020, SBOE waived the GQE requirement for students in the
        # 2020 cohort who where otherwise on schedule to graduate, so, for the 2020
        # cohort, there were no "waiver" graduates (which means no Non Waiver data).
        # so we replace 0 with NaN (to ensure a NaN result rather than 0)
        # if "Non Waiver|Cohort Count" in data.columns:
        # data = calculate_nonwaiver_graduation_rate(data)

        # Calculate SAT Rates #
        if "School Total|EBRW Total Tested" in data.columns:
            data = calculate_sat_rate(data)

        # Calculate AHS Only Data #
        # NOTE: All other values pulled from HS dataframe required for AHS calculations
        # should be addressed in this block        

        # CCR Rate
        if school_type == "AHS":

            if "AHS|CCR" in data.columns:
                data["AHS|CCR"] = pd.to_numeric(data["AHS|CCR"], errors="coerce")

            if "AHS|Grad All" in data.columns:                
                data["AHS|Grad All"] = pd.to_numeric(data["AHS|Grad All"], errors="coerce")

            if {"AHS|CCR","AHS|Grad All"}.issubset(data.columns):
                data["CCR Percentage"] = (data["AHS|CCR"] / data["AHS|Grad All"])

        # Need to check data again to see if anything is left after the above operations
        # if all columns in data other than the 1st (Year) are null then return empty df
        if data.iloc[:, 1:].isna().all().all():
            final_data = pd.DataFrame()
        
        else:

            data = data.filter(
                regex=r"^Category|Graduation Rate$|CCR Percentage|Pass Rate$|Benchmark %|Below|Approaching|At|^CCR Percentage|^Year$", # ^Strength of Diploma
                axis=1,
            )

            school_info = school_info.reset_index(drop=True)
            data = data.reset_index(drop=True)

            data = pd.concat([data, school_info], axis=1, join="inner")

            data.columns = data.columns.astype(str)

            data = (data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

            # State/Federal grade rows not used at this point
            data = data[data["Category"].str.contains("State Grade|Federal Rating|School Name") == False]

            if data_geo_code == school_geo_code:
                data = data.rename(columns={c: str(c)+"Corp" for c in data.columns if c not in ["Category"]})   
            else:
                data = data.rename(columns={c: str(c)+"School" for c in data.columns if c not in ["Category"]})  
            
            data = data.reset_index(drop=True)

            # make sure there are no lingering NoneTypes 
            data = data.fillna(value=np.nan)

            # Merge Total Tested DF with Proficiency DF based on substring match

            # add new column with substring values and drop old Category column
            data_tested["Substring"] = data_tested["Category"].replace({" Total Tested": "", "\|Cohort Count": " Graduation"}, regex=True)

            data_tested = data_tested.drop("Category", axis=1)

            # this cross-merge and substring match process takes about .3s - must be a faster way
            # t20 = time.process_time()

            final_data = data.merge(data_tested, how="cross")

            # keep only those rows where substring is in Category
            # Need to temporarily rename "English Learner" because otherwise it 
            # will match both "English" and "Non English"
            final_data = final_data.replace({"Non English Language Learners": "Temp1", "English Language Learners": "Temp2"}, regex=True)

            final_data = final_data[[a in b for a, b in zip(final_data["Substring"], final_data["Category"])]]
            
            final_data = final_data.replace({"Temp1": "Non English Language Learners", "Temp2": "English Language Learners"}, regex=True)             

            final_data = final_data.drop("Substring", axis=1)
            final_data = final_data.reset_index(drop=True)

            # reorder columns for display
            # NOTE: This final data keeps the Corp N-Size cols, which are not used
            # currently. We drop them later in the merge_high_school_data() step.
            if data_geo_code == school_geo_code:
                school_cols = [e for e in final_data.columns if "Corp" in e]
                nsize_cols = [e for e in final_data.columns if "CN-Size" in e]
            else:
                school_cols = [e for e in final_data.columns if "School" in e]
                nsize_cols = [e for e in final_data.columns if "SN-Size" in e]

            school_cols.sort(reverse=True)
            nsize_cols.sort(reverse=True)

            final_cols = list(itertools.chain(*zip(school_cols, nsize_cols)))

            final_cols.insert(0, "Category")
            final_data = final_data[final_cols]

    return final_data

def merge_high_school_data(all_school_data: pd.DataFrame, all_corp_data: pd.DataFrame) -> pd.DataFrame:

    all_school_data.columns = all_school_data.columns.astype(str)
    all_corp_data.columns = all_corp_data.columns.astype(str)

    # Add State Graduation Average to Corp DataFrame
    state_grad_average = get_graduation_data()
    state_grad_average = state_grad_average.loc[::-1].reset_index(drop=True)
    
    # merge state_grad_average with corp_data
    state_grad_average = (state_grad_average.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

    # rename columns and add state_grad average to corp df
    state_grad_average_corp = state_grad_average.rename(columns={c: str(c)+"Corp" for c in state_grad_average.columns if c not in ["Category"]})
    all_corp_data = pd.concat([all_corp_data.reset_index(drop=True), state_grad_average_corp.reset_index(drop=True)], axis=0).reset_index(drop=True)

    # For the school calculation we duplicate the school"s Total Graduation rate and
    # rename it "State Grad Average" - when the difference is calculated
    # between the two data frames, the difference between the Total Graduation Rates
    # will be School minus Corportion and the difference between State Grad Average Rates
    # will be School minus State Average

    # If no Total Graduation Rate Category exists for a school, we add it with all NaNs
    if "Total Graduation Rate" not in all_school_data["Category"].values:
        # add row of all nan (by enlargement) and set Category value
        all_school_data.loc[len(all_school_data)] = np.nan
        all_school_data.loc[all_school_data.index[-1],"Category"] = "Total Graduation Rate"

    duplicate_row = all_school_data[all_school_data["Category"] == "Total Graduation Rate"].copy()
    duplicate_row["Category"] = "State Graduation Average"
    all_school_data = pd.concat([all_school_data, duplicate_row], axis=0, ignore_index=True)

    # Clean up and merge school and corporation dataframes
    year_cols = list(all_school_data.columns[:0:-1])
    year_cols = [c[0:4] for c in year_cols]  # keeps only YYYY part of string]
    year_cols = list(set(year_cols))
    year_cols.sort(reverse=True)

    # last bit of cleanup is to drop "Corporation Name" Category from corp df
    all_corp_data = all_corp_data.drop(all_corp_data.loc[all_corp_data["Category"]=="Corporation Name"].index).reset_index(drop=True)

    # Create list of alternating columns
    # we technically do not need the Corporation N-Size at this point, but
    # we will keep it just in case. We drop it in the final df
    corp_cols = [e for e in all_corp_data.columns if "Corp" in e]
    cnsize_cols = [e for e in all_corp_data.columns if "CN-Size" in e]
    school_cols = [e for e in all_school_data.columns if "School" in e]
    snsize_cols = [e for e in all_school_data.columns if "SN-Size" in e]
    school_cols.sort(reverse=True)
    snsize_cols.sort(reverse=True) 
    corp_cols.sort(reverse=True)
    cnsize_cols.sort(reverse=True)

    result_cols = [str(s) + "Diff" for s in year_cols]

    merged_cols = list(itertools.chain(*zip(school_cols, snsize_cols, corp_cols, cnsize_cols)))
    merged_cols.insert(0, "Category")

    hs_merged_data = all_school_data.merge(all_corp_data, on="Category", how="left")
    hs_merged_data = hs_merged_data[merged_cols]

    tmp_category = all_school_data["Category"]
    all_school_data = all_school_data.drop("Category", axis=1)
    all_corp_data = all_corp_data.drop("Category", axis=1)

    # make sure there are no lingering NoneTypes to screw up the creation of hs_results
    all_school_data = all_school_data.fillna(value=np.nan)
    all_corp_data = all_corp_data.fillna(value=np.nan)

    # calculate difference between two dataframes
    # NOTE: yes a for-loop, but almost instantaneous
    hs_results = pd.DataFrame()
    for y in year_cols:
        hs_results[y] = calculate_difference(
            all_school_data[y + "School"], all_corp_data[y + "Corp"]
        )

    # Create final column order - dropping the corp avg and corp N-Size cols
    # (by not including them in the list) because we do not display them
    final_cols = list(itertools.chain(*zip(school_cols, snsize_cols, result_cols)))    
    final_cols.insert(0, "Category")    

    hs_results = hs_results.set_axis(result_cols, axis=1)
    hs_results.insert(loc=0, column="Category", value=tmp_category)

    final_hs_academic_data = hs_merged_data.merge(hs_results, on="Category", how="left")
    final_hs_academic_data = final_hs_academic_data[final_cols]

    final_hs_academic_data.columns = final_hs_academic_data.columns.str.replace("SN-Size", "N-Size", regex=True)

    return final_hs_academic_data

def process_growth_data(data: pd.DataFrame, category: str) -> Tuple[pd.DataFrame, pd.DataFrame]:

    # step 1: find the percentage of students with Adequate growth using
    # "Majority Enrolled" students (all available data) and the percentage
    # of students with Adequate growth using the set of students enrolled for
    # "162 Days" (a subset of available data)

    data_162 = data[data["Day 162"] == "TRUE"]

    data = data.groupby(["Test Year", category, "Subject"])["ILEARNGrowth Level"].value_counts(normalize=True).reset_index(name="Majority Enrolled")
    data_162 = data_162.groupby(["Test Year",category, "Subject"])["ILEARNGrowth Level"].value_counts(normalize=True).reset_index(name="162 Days")
    
    # step 3: add ME column to df and calculate difference
    data["162 Days"] = data_162["162 Days"]
    data["Difference"] = data["162 Days"] - data["Majority Enrolled"]

    # step 4: get into proper format for display as multi-header DataTable
    
    # create final category
    data["Category"] = data[category] + "|" + data["Subject"]
    
    # drop unused rows and columns
    data = data[data["ILEARNGrowth Level"].str.contains("Not Adequate") == False]
    data = data.drop([category, "Subject","ILEARNGrowth Level"], axis=1)

    # NOTE: Occasionally, the data will have an "Unknown" Category. No idea why, but
    # we need to get rid of it - easiest way would be to just drop any Categories
    # matching Unknown, but that won"t stop other random Categories from getting
    # through. So instead, we drop any Categories that don"t match categories in 
    # the respective list

    if category == "Grade Level":
        data = data[data["Category"].str.contains("|".join(grades))]

    elif category == "Ethnicity":
        data = data[data["Category"].str.contains("|".join(ethnicity))]

    elif category == "Socioeconomic Status" or category == "English Learner Status" or category == "Special Education Status":
        data = data[data["Category"].str.contains("|".join(subgroup))]

    # create fig data
    fig_data = data.copy()
    fig_data = fig_data.drop("Difference", axis=1)
    fig_data = fig_data.pivot(index=["Test Year"], columns="Category")
    fig_data.columns = fig_data.columns.map(lambda x: "_".join(map(str, x)))

    # create table data
    table_data = data.copy()

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