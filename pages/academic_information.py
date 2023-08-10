#########################################
# ICSB Dashboard - Academic Information #
#########################################
# author:   jbetley
# version:  1.08
# date:     08/01/23
#
# TODO: Add Total Tested to Proficiency Bar Charts

import dash
from dash import dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import re

# import local functions
from .table_helpers import no_data_page, no_data_table, create_academic_info_table, \
    create_growth_table, set_table_layout, create_basic_info_table
from .chart_helpers import no_data_fig_label, make_stacked_bar, make_growth_chart
from .calculations import round_percentages
from .subnav import subnav_academic
from .load_data import ethnicity, subgroup, subject, grades_all, grades_ordinal, get_excluded_years, \
    process_k8_academic_data, get_attendance_data, process_high_school_academic_data, filter_high_school_academic_data, \
    process_growth_data  
from .load_db import get_k8_school_academic_data, get_high_school_academic_data, get_demographic_data, get_school_index, \
    get_growth_data

dash.register_page(__name__, top_nav=True, path="/academic_information", order=4)

@callback(
    Output("k8-grade-table", "children"),
    Output("k8-grade-ela-fig", "children"),
    Output("k8-grade-math-fig", "children"),
    Output("k8-ethnicity-table", "children"),
    Output("k8-ethnicity-ela-fig", "children"),
    Output("k8-ethnicity-math-fig", "children"),
    Output("k8-subgroup-table", "children"),
    Output("k8-subgroup-ela-fig", "children"),
    Output("k8-subgroup-math-fig", "children"),
    Output("k8-other-table", "children"),
    Output("k8-table-container", "style"),
    Output("hs-grad-overview-table", "children"),
    Output("hs-grad-ethnicity-table", "children"),
    Output("hs-grad-subgroup-table", "children"),
    Output("sat-overview-table", "children"),
    Output("sat-ethnicity-table", "children"),
    Output("sat-subgroup-table", "children"),
    Output("hs-table-container", "style"),
    Output("academic-information-main-container", "style"),
    Output("academic-information-empty-container", "style"),
    Output("academic-information-no-data", "children"),
    Output("table-grades-growth-ela-container", "children"),
    Output("table-grades-growth-math-container", "children"),
    Output("table-ethnicity-growth-ela-container", "children"),
    Output("table-ethnicity-growth-math-container", "children"),
    Output("table-subgroup-growth-ela-container", "children"),
    Output("table-subgroup-growth-math-container", "children"),
    Output("fig-grade-growth-ela", "children"),
    Output("fig-grade-sgp-ela", "children"),
    Output("fig-grade-growth-math", "children"),
    Output("fig-grade-sgp-math", "children"),
    Output("fig-ethnicity-growth-ela", "children"),
    Output("fig-ethnicity-sgp-ela", "children"),
    Output("fig-ethnicity-growth-math", "children"),
    Output("fig-ethnicity-sgp-math", "children"),
    Output("fig-subgroup-growth-ela", "children"),
    Output("fig-subgroup-sgp-ela", "children"),
    Output("fig-subgroup-growth-math", "children"),
    Output("fig-subgroup-sgp-math", "children"),        
    Output("state-growth-main-container", "style"),
    Output("state-growth-empty-container", "style"),    
    Output("state-growth-no-data", "children"),
    # Output("growth-values-table", "children"),    
    # Output("growth-values-table-container", "style"),
    Output("academic-information-notes-string", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input(component_id="radio-button-academic-info", component_property="value")
)
def update_academic_information_page(school: str, year: str, radio_value: str):
    if not school:
        raise PreventUpdate

    # show 2019 instead of 2020 as 2020 has no academic data
    string_year = year
    selected_year_string = "2019" if string_year == "2020" else string_year
    selected_year_numeric = int(selected_year_string)

    excluded_years = get_excluded_years(selected_year_string)

    # default styles
    main_container = {"display": "block"}
    k8_table_container = {"display": "block"}
    hs_table_container = {"display": "block"}
    empty_container = {"display": "none"}
    no_data_to_display = no_data_page("Academic Proficiency")
    
    state_growth_main_container = {"display": "block"}
    state_growth_empty_container = {"display": "none"}   
    no_state_growth_data_to_display = no_data_page("Indiana State Growth Calculations")

    # growth_values_table = [html.Img(src="assets/growth_table.jpg", hidden=True)]
    # growth_values_table_container = {"display": "none"}

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]
    selected_school_id = int(selected_school["School ID"].values[0])

    ## Proficiency Tables
    if radio_value == "proficiency":

        # set growth tables to null
        table_grades_growth_ela_container = {}
        table_grades_growth_math_container = {}
        table_ethnicity_growth_ela_container = {}
        table_ethnicity_growth_math_container = {}
        table_subgroup_growth_ela_container = {}
        table_subgroup_growth_math_container = {}

        fig_grade_growth_ela = {}
        fig_grade_sgp_ela = {}
        fig_grade_growth_math = {}
        fig_grade_sgp_math = {}
        fig_ethnicity_growth_ela = {}
        fig_ethnicity_sgp_ela = {}
        fig_ethnicity_growth_math = {}
        fig_ethnicity_sgp_math = {}
        fig_subgroup_growth_ela = {}
        fig_subgroup_sgp_ela = {}
        fig_subgroup_growth_math = {}
        fig_subgroup_sgp_math = {}    
        state_growth_main_container = {"display": "none"}
        state_growth_empty_container = {"display": "none"}   
     
        if (selected_school_type == "K8" or selected_school_type == "K12"):

            # if K8, hide HS tables (except for CHS prior to 2021 when it was a K12)
            if selected_school_type == "K8" and not (selected_school_id == 5874 and selected_year_numeric < 2021):
                
                hs_grad_overview_table = {}
                hs_grad_ethnicity_table = {}
                hs_grad_subgroup_table = {}
                sat_overview_table = {}
                sat_ethnicity_table = {}
                sat_subgroup_table = {}                  
                hs_table_container = {"display": "none"}

            # get all years of data
            raw_k8_school_data = get_k8_school_academic_data(school)
            
            # filter out years of data later than the selected year
            if excluded_years:
                selected_raw_k8_school_data = raw_k8_school_data[~raw_k8_school_data["Year"].isin(excluded_years)].copy()
            else:
                selected_raw_k8_school_data = raw_k8_school_data.copy()

            if len(selected_raw_k8_school_data.index) == 0:

                # school type is K8 or K12, but there is no k8 data (may still be 9-12 data)
                k8_grade_table = {}
                k8_ethnicity_table = {}
                k8_subgroup_table = {}
                k8_other_table = {}
                k8_grade_ela_fig = {}
                k8_grade_math_fig = {}
                k8_ethnicity_ela_fig = {}
                k8_ethnicity_math_fig = {}
                k8_subgroup_ela_fig = {}
                k8_subgroup_math_fig = {}
                k8_table_container = {"display": "none"}               
                
                # This section displays K8 tables for both K8 and K12 schools. If the 
                # selected school is K8 and it has no data, then we display full
                # no_data_page fig. If the selected school is a K12, we go to the next
                # check and if it has no HS data either, then no_data_fig will also
                # be displayed.

                if selected_school_type == "K8":

                    main_container = {"display": "none"}
                    empty_container = {"display": "block"}

            else:                    

                all_k8_school_data = process_k8_academic_data(selected_raw_k8_school_data)

                if all_k8_school_data.empty:

                    k8_grade_table = {}
                    k8_ethnicity_table = {}
                    k8_subgroup_table = {}
                    k8_other_table = {}
                    k8_grade_ela_fig = {}
                    k8_grade_math_fig = {}
                    k8_ethnicity_ela_fig = {}
                    k8_ethnicity_math_fig = {}
                    k8_subgroup_ela_fig = {}
                    k8_subgroup_math_fig = {}
                    k8_table_container = {"display": "none"}               
                    
                    # This section displays K8 tables for both K8 and K12 schools. If the 
                    # selected school is K8 and it has no data, then we display full
                    # no_data_page fig. If the selected school is a K12, we go to the next
                    # check and if it has no HS data either, then no_data_fig will also
                    # be displayed.

                    if selected_school_type == "K8":

                        main_container = {"display": "none"}
                        empty_container = {"display": "block"}

                else:

                    all_k8_school_data = all_k8_school_data.fillna("No Data")
                    all_k8_school_data = (all_k8_school_data.set_index(["Category"]).add_suffix("School").reset_index())

                    all_k8_school_data.columns = all_k8_school_data.columns.str.replace(r"School$", "", regex=True)

                    all_k8_school_data["Category"] = (all_k8_school_data["Category"].str.replace(" Proficient %", "").str.strip())

                    all_k8_school_data.loc[all_k8_school_data["Category"] == "IREAD", "Category"] = "IREAD Proficiency (Grade 3)"

                    grades_iread = grades_all + ["IREAD Proficiency (Grade 3)"]

                    years_by_grade = all_k8_school_data[all_k8_school_data["Category"].str.contains("|".join(grades_iread))]

                    k8_grade_table = create_academic_info_table(years_by_grade,"Proficiency by Grade")
                    k8_grade_table = set_table_layout(k8_grade_table, k8_grade_table, years_by_grade.columns)

                    years_by_subgroup = all_k8_school_data[all_k8_school_data["Category"].str.contains("|".join(subgroup))]

                    k8_subgroup_table = create_academic_info_table(years_by_subgroup,"Proficiency by Subgroup")
                    k8_subgroup_table = set_table_layout(k8_subgroup_table, k8_subgroup_table, years_by_subgroup.columns)

                    years_by_ethnicity = all_k8_school_data[all_k8_school_data["Category"].str.contains("|".join(ethnicity))]

                    k8_ethnicity_table = create_academic_info_table(years_by_ethnicity,"Proficiency by Ethnicity")
                    k8_ethnicity_table = set_table_layout(k8_ethnicity_table, k8_ethnicity_table, years_by_ethnicity.columns)

                    # Attendance rate
                    school_demographic_data = get_demographic_data(school)
                    attendance_rate = get_attendance_data(school_demographic_data, selected_year_string)

                    if len(attendance_rate.index) != 0:
                        k8_other_table = create_basic_info_table(attendance_rate,"Attendance Data") 
                    else:
                        k8_other_table = no_data_table("Attendance Data")

                    k8_other_table = set_table_layout(k8_other_table, k8_other_table, attendance_rate.columns)
                    
                    ## Proficiency Breakdown ##
                    proficiency_data = selected_raw_k8_school_data.copy()

                    # NOTE: IDOE's raw proficency data is annoyingly inconsistent. In some cases missing
                    # data is blank and in other cases it is represented by "0." So we need to be extra
                    # careful in interpreting what is missing from what is just inconsistenly recorded

                    school_k8_proficiency_data = proficiency_data.loc[proficiency_data["Year"] == selected_year_numeric]

                    school_k8_proficiency_data = school_k8_proficiency_data.dropna(axis=1)
                    school_k8_proficiency_data = school_k8_proficiency_data.reset_index()

                    for col in school_k8_proficiency_data.columns:
                        school_k8_proficiency_data[col] = pd.to_numeric(school_k8_proficiency_data[col], errors="coerce")

                    # Filter needed categories (this captures ELA&Math as well, which we drop later)

                    school_k8_proficiency_data = school_k8_proficiency_data.filter(
                        regex=r"ELA Below|ELA At|ELA Approaching|ELA Above|ELA Total|Math Below|Math At|Math Approaching|Math Above|Math Total",
                        axis=1,
                    )

                    all_proficiency_data = school_k8_proficiency_data.copy()
                    
                    proficiency_rating = ["Below Proficiency", "Approaching Proficiency", "At Proficiency", "Above Proficiency"]
                
                    # NOTE: This may seem kludgy, but runs consistently around .15s
                    # for each category, create a proficiency_columns list of columns using the strings in
                    # "proficiency_rating" and then divide each column by "Total Tested"
                    categories = grades_all + ethnicity + subgroup

                    # create dataframe to hold annotations (categories & missing data)
                    # NOTE: Annotations are currently not used
                    annotations = pd.DataFrame(columns= ["Category","Total Tested","Status"])

                    for c in categories:
                        for s in subject:
                            category_subject = c + "|" + s
                            proficiency_columns = [category_subject + " " + x for x in proficiency_rating]
                            total_tested = category_subject + " " + "Total Tested"

                            # We do not want categories that do not appear in the dataframe, there are
                            # three possible data configurations for each column:
                            # 1) Total Tested > 0 and the sum of proficiency_rating(s) is > 0: the school
                            #    has tested category and there is publicly available data [display]
                            # 2) Total Tested > 0 and the sum of proficiency_rating(s) are == "NaN": the
                            #    school has tested category but there is no publicly available data
                            #    (insufficient N-size) [do not display]
                            # 3) Total Tested AND sum of proficiency_rating(s) == 0: the school does not
                            #    have data for the tested category [do not display]

                            # Neither (2) nor (3) should be displayed. However, we do want to
                            # track which Category/Subject combinations meet either condition
                            # (for figure annotation purposes). So we use a little trick. The
                            # sum of a series of "0" values is 0 (a numpy.int64). The sum of a
                            # series of "NaN" values is also 0.0 (but the value is a float because
                            # numpy treats NaN as a numpy.float64). While either value returns True
                            # when tested if the value is 0, we can test the "type" of the result (using
                            # np.integer and np.floating) to distinguish between them.

                            if total_tested in all_proficiency_data.columns:

                                if all_proficiency_data[proficiency_columns].iloc[0].sum() == 0:

                                    # if the value is a float, the measured values were NaN, which
                                    # means they were converted "***", and thus "insufficient data"
                                    if isinstance(all_proficiency_data[proficiency_columns].iloc[0].sum(), np.floating):
                                        annotations.loc[len(annotations.index)] = [proficiency_columns[0],all_proficiency_data[total_tested].values[0],"Insufficient"]

                                    # if the value is an integer, the measured values were 0, which
                                    # means "missing data"
                                    elif isinstance(all_proficiency_data[proficiency_columns].iloc[0].sum(), np.integer):

                                        # Only add to annotations if it is a non "Grade" category.
                                        # this is to account for IDOE's shitty data practices- sometimes
                                        # missing grades are blank (the correct way) and sometimes the
                                        # columns are filled with 0. So if everything is 0 AND it is a Grade
                                        # category, we assume it is just IDOE's fucked up data entry
                                        if ~all_proficiency_data[proficiency_columns].columns.str.contains("Grade").any():
                                            annotations.loc[len(annotations.index)] = [proficiency_columns[0],all_proficiency_data[total_tested].values[0],"Missing"]

                                    # either way, drop all columns related to the category from the df
                                    all_proficiency_columns = proficiency_columns + [total_tested]

                                    all_proficiency_data = all_proficiency_data.drop(all_proficiency_columns, axis=1)

                                else:
                                    # calculate percentage
                                    all_proficiency_data[proficiency_columns] = all_proficiency_data[proficiency_columns].divide(
                                        all_proficiency_data[total_tested], axis="index"
                                    )

                                    # get a list of all values
                                    row_list = all_proficiency_data[proficiency_columns].values.tolist()

                                    # round percentages using Largest Remainder Method
                                    rounded = round_percentages(row_list[0])

                                    # add back to dataframe
                                    rounded_percentages = pd.DataFrame([rounded])
                                    rounded_percentages_cols = list(rounded_percentages.columns)
                                    all_proficiency_data[proficiency_columns] = rounded_percentages[rounded_percentages_cols]

                    # drop columns used for calculation that we dont want to chart (keeping Total Tested)
                    all_proficiency_data.drop(list(all_proficiency_data.filter(regex="Total Proficient|ELA and Math")),
                        axis=1,
                        inplace=True,
                    )

                    # Replace Grade X with ordinal number (e.g., Grade 4 = 4th)
                    all_proficiency_data = all_proficiency_data.rename(columns=lambda x: re.sub("(Grade )(\d)", "\\2th", x))

                    # all use "th" suffix except for 3rd - so we need to specially treat "3""
                    all_proficiency_data.columns = [x.replace("3th", "3rd") for x in all_proficiency_data.columns.to_list()]

                    all_proficiency_data = (all_proficiency_data.T.rename_axis("Category").rename_axis(None, axis=1).reset_index())

                    # split Grade column into two columns and rename what used to be the index
                    all_proficiency_data[["Category", "Proficiency"]] = all_proficiency_data["Category"].str.split("|", expand=True)

                    all_proficiency_data.rename(columns={0: "Percentage"}, inplace=True)

                    all_proficiency_data = all_proficiency_data[all_proficiency_data["Category"] != "index"]

                    ela_title = selected_year_string + " ELA Proficiency Breakdown"
                    math_title = selected_year_string + " Math Proficiency Breakdown"

                    # ELA by Grade
                    grade_annotations = annotations.loc[annotations["Category"].str.contains("Grade")]

                    grade_ela_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(grades_ordinal)
                        & all_proficiency_data["Proficiency"].str.contains("ELA")
                    ]

                    if not grade_ela_fig_data.empty:
                        k8_grade_ela_fig = make_stacked_bar(grade_ela_fig_data,ela_title)
                    else:
                        k8_grade_ela_fig = no_data_fig_label(ela_title, 100)

                    # Math by Grade
                    grade_math_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(grades_ordinal)
                        & all_proficiency_data["Proficiency"].str.contains("Math")
                    ]

                    if not grade_math_fig_data.empty:
                        k8_grade_math_fig = make_stacked_bar(grade_math_fig_data,math_title)
                    else:
                        k8_grade_math_fig = no_data_fig_label(math_title, 100)

                    # ELA by Ethnicity
                    ethnicity_annotations = annotations.loc[annotations["Category"].str.contains("Ethnicity")]

                    ethnicity_ela_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(ethnicity)
                        & all_proficiency_data["Proficiency"].str.contains("ELA")
                    ]

                    if not ethnicity_ela_fig_data.empty:
                        k8_ethnicity_ela_fig = make_stacked_bar(ethnicity_ela_fig_data,ela_title)
                    else:
                        k8_ethnicity_ela_fig = no_data_fig_label(ela_title, 100)

                    # Math by Ethnicity
                    ethnicity_math_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(ethnicity)
                        & all_proficiency_data["Proficiency"].str.contains("Math")
                    ]

                    if not ethnicity_math_fig_data.empty:
                        k8_ethnicity_math_fig = make_stacked_bar(ethnicity_math_fig_data,math_title)
                    else:
                        k8_ethnicity_math_fig = no_data_fig_label(math_title, 100)

                    # ELA by Subgroup
                    subgroup_annotations = annotations.loc[annotations["Category"].str.contains("Subgroup")]

                    subgroup_ela_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(subgroup)
                        & all_proficiency_data["Proficiency"].str.contains("ELA")
                    ]

                    if not subgroup_ela_fig_data.empty:
                        k8_subgroup_ela_fig = make_stacked_bar(subgroup_ela_fig_data,ela_title)
                    else:
                        k8_subgroup_ela_fig = no_data_fig_label(ela_title, 100)

                    # Math by Subgroup
                    subgroup_math_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(subgroup)
                        & all_proficiency_data["Proficiency"].str.contains("Math")
                    ]

                    if not subgroup_math_fig_data.empty:
                        k8_subgroup_math_fig = make_stacked_bar(subgroup_math_fig_data,math_title)
                    else:

                        k8_subgroup_math_fig = no_data_fig_label(math_title, 100)

        else:
            # school type is not K8 or K12
            k8_grade_table = {}
            k8_ethnicity_table = {}
            k8_subgroup_table = {}
            k8_other_table = {}
            k8_table_container = {"display": "none"}

            k8_grade_ela_fig = {}
            k8_grade_math_fig = {}
            k8_ethnicity_ela_fig = {}
            k8_ethnicity_math_fig = {}
            k8_subgroup_ela_fig = {}
            k8_subgroup_math_fig = {}

        # NOTE: There is a special exception for Christel House South - prior to 2021,
        # CHS was a K12. From 2021 onwards, CHS is a K8, with the high school moving to
        # Christel House Watanabe Manual HS
        if (selected_school_type == "HS" or selected_school_type == "AHS" or selected_school_type == "K12"
            or (selected_school_id == 5874 and selected_year_numeric < 2021)):

            # load HS academic data
            raw_hs_school_data = get_high_school_academic_data(school)

            # exclude years later than the selected year
            if excluded_years:
                selected_raw_hs_school_data = raw_hs_school_data[~raw_hs_school_data["Year"].isin(excluded_years)].copy()
            else:
                selected_raw_hs_school_data = raw_hs_school_data.copy()

            if len(selected_raw_hs_school_data.index) == 0:

                # selected type is HS, AHS, K12, or CHS < 2021, but there is no data
                hs_grad_overview_table = {}
                hs_grad_ethnicity_table = {}
                hs_grad_subgroup_table = {}
                sat_overview_table = {}
                sat_ethnicity_table = {}
                sat_subgroup_table = {}        
                hs_table_container = {"display": "none"}                

            else:

                selected_raw_hs_school_data = filter_high_school_academic_data(selected_raw_hs_school_data)
                all_hs_school_data = process_high_school_academic_data(selected_raw_hs_school_data, school)

                if all_hs_school_data.empty:

                    # df is empty after being processed
                    hs_grad_overview_table = {}
                    hs_grad_ethnicity_table = {}
                    hs_grad_subgroup_table = {}
                    sat_overview_table = {}
                    sat_ethnicity_table = {}
                    sat_subgroup_table = {}        
                    hs_table_container = {"display": "none"}
                
                else:
                    # Graduation Rate Tables ("Strength of Diploma" in data, but not currently displayed)
                    grad_overview_categories = ["Total", "Non Waiver", "State Average"]

                    if selected_school_type == "AHS":
                        grad_overview_categories.append("CCR Percentage")

                    all_hs_school_data.columns = all_hs_school_data.columns.astype(str)

                    # Graduation Rate Tables
                    graduation_data = all_hs_school_data[all_hs_school_data["Category"].str.contains("Graduation")].copy()
                    graduation_data["Category"] = (graduation_data["Category"].str.replace("Graduation Rate", "").str.strip())

                    grad_overview = graduation_data[graduation_data["Category"].str.contains("|".join(grad_overview_categories))]
                    grad_overview = grad_overview.dropna(axis=1,how="all")

                    hs_grad_overview_table = create_academic_info_table(grad_overview,"Graduation Rate Overview")
                    hs_grad_overview_table = set_table_layout(hs_grad_overview_table, hs_grad_overview_table, grad_overview.columns)

                    grad_ethnicity = graduation_data[graduation_data["Category"].str.contains("|".join(ethnicity))]
                    grad_ethnicity = grad_ethnicity.dropna(axis=1,how="all")

                    hs_grad_ethnicity_table = create_academic_info_table(grad_ethnicity,"Graduation Rate by Ethnicity")
                    hs_grad_ethnicity_table = set_table_layout(hs_grad_ethnicity_table, hs_grad_ethnicity_table, grad_ethnicity.columns)
                    
                    grad_subgroup = graduation_data[graduation_data["Category"].str.contains("|".join(subgroup))]
                    grad_subgroup = grad_subgroup.dropna(axis=1,how="all")

                    hs_grad_subgroup_table = create_academic_info_table(grad_subgroup,"Graduation Rate by Subgroup")
                    hs_grad_subgroup_table = set_table_layout(hs_grad_subgroup_table, hs_grad_subgroup_table, grad_subgroup.columns)
                
                    # SAT Benchmark Tables
                    sat_table_data = all_hs_school_data[all_hs_school_data["Category"].str.contains("Benchmark %")].copy()
                    sat_table_data["Category"] = (sat_table_data["Category"].str.replace("Benchmark %", "").str.strip())

                    sat_overview = sat_table_data[sat_table_data["Category"].str.contains("School Total")]
                    sat_overview = sat_overview.dropna(axis=1,how="all")

                    sat_overview_table = create_academic_info_table(sat_overview,"SAT Overview")
                    sat_overview_table = set_table_layout(sat_overview_table, sat_overview_table, sat_overview.columns) 
                    
                    sat_ethnicity = sat_table_data[sat_table_data["Category"].str.contains("|".join(ethnicity))]
                    sat_ethnicity = sat_ethnicity.dropna(axis=1,how="all")

                    sat_ethnicity_table = create_academic_info_table(sat_ethnicity,"SAT Benchmarks by Ethnicity")
                    sat_ethnicity_table = set_table_layout(sat_ethnicity_table, sat_ethnicity_table, sat_ethnicity.columns) 
                    
                    sat_subgroup = sat_table_data[sat_table_data["Category"].str.contains("|".join(subgroup))]
                    sat_subgroup = sat_subgroup.dropna(axis=1,how="all")

                    sat_subgroup_table = create_academic_info_table(sat_subgroup,"SAT Benchmarks by Subgroup")
                    sat_subgroup_table = set_table_layout(sat_subgroup_table, sat_subgroup_table, sat_subgroup.columns)

    elif radio_value =="growth":
    # Growth Tab #

        # set all proficiency tables to null and containers to display: none
        hs_grad_overview_table = {}
        hs_grad_ethnicity_table = {}
        hs_grad_subgroup_table = {}
        sat_overview_table = {}
        sat_ethnicity_table = {}
        sat_subgroup_table = {}        
        hs_table_container = {"display": "none"}

        k8_grade_table = {}
        k8_ethnicity_table = {}
        k8_subgroup_table = {}
        k8_other_table = {}
        k8_table_container = {"display": "none"}

        k8_grade_ela_fig = {}
        k8_grade_math_fig = {}
        k8_ethnicity_ela_fig = {}
        k8_ethnicity_math_fig = {}
        k8_subgroup_ela_fig = {}
        k8_subgroup_math_fig = {}

        main_container = {"display": "none"}
        empty_container = {"display": "none"}

        # State Growth Data

        # NOTE: "162-Days" means a student was enrolled at the school where they were assigned for at least
        # 162 days. "Majority Enrolled" is misleading. It actually means "Greatest Number of Days." So the actual
        # number of days could easily be less than 82 if, for example, a student transferred a few times, or
        # was out of the system for most of the year. "Tested School" is where the student actually took the
        # test. IDOE uses "Majority Enrolled" for their calculations

        # ICSB growth metrics need to be updated, currently say:
        #   Percentage of students achieving “typical” or “high” growth on the state assessment in ELA/Math
        #   Median SGP of students achieving "adequate and sufficient growth" on the state assessment in ELA/Math

        # NOTE: Growth data shows: byGrade, byEthnicity, bySES, byEL Status, & by Sped Status
        # Also avaiable (but not shown): Homeless Status and High Ability Status

        # dataset is all students who are coded as "Majority Enrolled" at the school
        growth_data = get_growth_data(school)

        # filter out years of data later than the selected year
        if excluded_years:
            growth_data = growth_data[~growth_data["Test Year"].isin(excluded_years)]

        if len(growth_data.index) > 0:
            
            # growth_values_table = [html.Img(src="assets/growth_table.jpg", hidden=False)]
            # growth_values_table_container = {"display": "block"}

            # NOTE: This calculates the difference between the count of Majority Enrolled and 162-Day students by Year
            # counts_growth = growth_data.groupby("Test Year")["Test Year"].count().reset_index(name = "Count (Majority Enrolled)")
            # counts_growth_162 = growth_data_162.groupby("Test Year")["Test Year"].count().reset_index(name = "Count (162 Days)")

            # counts_growth["School Name"] = selected_school["School Name"].values[0]
            # counts_growth["Count (162 Days)"] = counts_growth_162["Count (162 Days)"]
            # counts_growth["Difference"] = counts_growth["Count (Majority Enrolled)"] - counts_growth["Count (162 Days)"]
            # diff_threshold = abs(len(growth_data.index) - len(growth_data_162.index))
            # print(f"Percentage difference: " + str(diff_threshold / len(growth_data.index)))

            # Percentage of students achieving "Adequate Growth"
            fig_data_grades_growth, table_data_grades_growth = process_growth_data(growth_data,"Grade Level","growth")
            fig_data_ethnicity_growth, table_data_ethnicity_growth = process_growth_data(growth_data,"Ethnicity","growth")
            fig_data_ses_growth, table_data_ses_growth = process_growth_data(growth_data,"Socioeconomic Status","growth")
            fig_data_el_growth, table_data_el_growth = process_growth_data(growth_data,"English Learner Status","growth")
            fig_data_sped_growth, table_data_sped_growth = process_growth_data(growth_data,"Special Education Status","growth")

            # Median SGP for "all" students
            fig_data_grades_sgp, table_data_grades_sgp = process_growth_data(growth_data,"Grade Level","sgp")
            fig_data_ethnicity_sgp, table_data_ethnicity_sgp = process_growth_data(growth_data,"Ethnicity","sgp")
            fig_data_ses_sgp, table_data_ses_sgp = process_growth_data(growth_data,"Socioeconomic Status","sgp")
            fig_data_el_sgp, table_data_el_sgp = process_growth_data(growth_data,"English Learner Status","sgp")
            fig_data_sped_sgp, table_data_sped_sgp = process_growth_data(growth_data,"Special Education Status","sgp")

            # combine subgroups
            table_data_subgroup_growth = pd.concat([table_data_ses_growth, table_data_el_growth, table_data_sped_growth])
            fig_data_subgroup_growth = pd.concat([fig_data_ses_growth, fig_data_el_growth, fig_data_sped_growth], axis=1)

            table_data_subgroup_sgp = pd.concat([table_data_ses_sgp, table_data_el_sgp, table_data_sped_sgp])
            fig_data_subgroup_sgp = pd.concat([fig_data_ses_sgp, fig_data_el_sgp, fig_data_sped_sgp], axis=1)
            
            # Growth tables

            # by grade
            table_data_grades_growth_ela = table_data_grades_growth[(table_data_grades_growth["Category"].str.contains("ELA"))]
            table_data_grades_growth_math= table_data_grades_growth[(table_data_grades_growth["Category"].str.contains("Math"))]                    
            table_data_grades_sgp_ela = table_data_grades_sgp[(table_data_grades_sgp["Category"].str.contains("ELA"))]                    
            table_data_grades_sgp_math = table_data_grades_sgp[(table_data_grades_sgp["Category"].str.contains("Math"))]

            table_grades_growth_ela = create_growth_table("Percentage of Students with Adequate Growth - by Grade (ELA)", table_data_grades_growth_ela,"growth")
            table_grades_sgp_ela = create_growth_table("Median SGP - All Students By Grade (ELA)", table_data_grades_sgp_ela,"sgp")

            table_grades_growth_ela_container = set_table_layout(table_grades_growth_ela, table_grades_sgp_ela, table_data_grades_growth.columns)

            table_grades_growth_math = create_growth_table("Percentage of Students with Adequate Growth - by Grade (Math)", table_data_grades_growth_math,"growth")
            table_grades_sgp_math = create_growth_table("Median SGP - All Students By Grade (Math)", table_data_grades_sgp_math,"sgp")

            table_grades_growth_math_container = set_table_layout(table_grades_growth_math, table_grades_sgp_math, table_data_grades_growth.columns)

            # by ethnicity
            table_data_ethnicity_growth_ela = table_data_ethnicity_growth[(table_data_ethnicity_growth["Category"].str.contains("ELA"))]
            table_data_ethnicity_growth_math= table_data_ethnicity_growth[(table_data_ethnicity_growth["Category"].str.contains("Math"))]                    
            table_data_ethnicity_sgp_ela = table_data_ethnicity_sgp[(table_data_ethnicity_sgp["Category"].str.contains("ELA"))]                    
            table_data_ethnicity_sgp_math = table_data_ethnicity_sgp[(table_data_ethnicity_sgp["Category"].str.contains("Math"))]

            table_ethnicity_growth_ela = create_growth_table("Percentage of Students with Adequate Growth - by Ethnicity (ELA)", table_data_ethnicity_growth_ela,"growth")
            table_ethnicity_sgp_ela = create_growth_table("Median SGP - All Students By Ethnicity (ELA)", table_data_ethnicity_sgp_ela,"sgp")

            table_ethnicity_growth_ela_container = set_table_layout(table_ethnicity_growth_ela, table_ethnicity_sgp_ela, table_data_ethnicity_growth.columns)

            table_ethnicity_growth_math = create_growth_table("Percentage of Students with Adequate Growth - by Ethnicity (Math)", table_data_ethnicity_growth_math,"growth")
            table_ethnicity_sgp_math = create_growth_table("Median SGP - All Students By Ethnicity (Math)", table_data_ethnicity_sgp_math,"sgp")

            table_ethnicity_growth_math_container = set_table_layout(table_ethnicity_growth_math, table_ethnicity_sgp_math, table_data_ethnicity_growth.columns)

            # by subgroup
            table_data_subgroup_growth_ela = table_data_subgroup_growth[(table_data_subgroup_growth["Category"].str.contains("ELA"))]
            table_data_subgroup_growth_math= table_data_subgroup_growth[(table_data_subgroup_growth["Category"].str.contains("Math"))]                    
            table_data_subgroup_sgp_ela = table_data_subgroup_sgp[(table_data_subgroup_sgp["Category"].str.contains("ELA"))]                    
            table_data_subgroup_sgp_math = table_data_subgroup_sgp[(table_data_subgroup_sgp["Category"].str.contains("Math"))]

            table_subgroup_growth_ela = create_growth_table("Percentage of Students with Adequate Growth - by Ethnicity (ELA)", table_data_subgroup_growth_ela,"growth")
            table_subgroup_sgp_ela = create_growth_table("Median SGP - All Students By Ethnicity (ELA)", table_data_subgroup_sgp_ela,"sgp")

            table_subgroup_growth_ela_container = set_table_layout(table_subgroup_growth_ela, table_subgroup_sgp_ela, table_data_subgroup_growth.columns)

            table_subgroup_growth_math = create_growth_table("Percentage of Students with Adequate Growth - by Ethnicity (Math)", table_data_subgroup_growth_math,"growth")
            table_subgroup_sgp_math = create_growth_table("Median SGP - All Students By Ethnicity (Math)", table_data_subgroup_sgp_math,"sgp")

            table_subgroup_growth_math_container = set_table_layout(table_subgroup_growth_math, table_subgroup_sgp_math, table_data_subgroup_growth.columns)

        ## Growth figures (NOTE: Currently only displaying Majority Enrolled Data)

        #TODO: Add 162 in tooltip
            # Growth by Grade (Both ME and 162)
            growth_data_162_grades_ela = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains("162")) & (fig_data_grades_growth.columns.str.contains("ELA"))]
            growth_data_162_grades_math = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains("162")) & (fig_data_grades_growth.columns.str.contains("Math"))]
            growth_data_me_grades_ela = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains("Majority Enrolled")) & (fig_data_grades_growth.columns.str.contains("ELA"))]
            growth_data_me_grades_math = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains("Majority Enrolled")) & (fig_data_grades_growth.columns.str.contains("Math"))]
            
            growth_data_162_grades_ela.columns = growth_data_162_grades_ela.columns.str.split("_").str[1]
            growth_data_162_grades_math.columns = growth_data_162_grades_math.columns.str.split("_").str[1]
            growth_data_me_grades_ela.columns = growth_data_me_grades_ela.columns.str.split("_").str[1]
            growth_data_me_grades_math.columns = growth_data_me_grades_math.columns.str.split("_").str[1]

            # Growth by Ethnicity (Both ME and 162)
            growth_data_162_ethnicity_ela = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains("162")) & (fig_data_ethnicity_growth.columns.str.contains("ELA"))]
            growth_data_162_ethnicity_math = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains("162")) & (fig_data_ethnicity_growth.columns.str.contains("Math"))]
            growth_data_me_ethnicity_ela = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains("Majority Enrolled")) & (fig_data_ethnicity_growth.columns.str.contains("ELA"))]
            growth_data_me_ethnicity_math = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains("Majority Enrolled")) & (fig_data_ethnicity_growth.columns.str.contains("Math"))]
            
            growth_data_162_ethnicity_ela.columns = growth_data_162_ethnicity_ela.columns.str.split("_").str[1]
            growth_data_162_ethnicity_math.columns = growth_data_162_ethnicity_math.columns.str.split("_").str[1]
            growth_data_me_ethnicity_ela.columns = growth_data_me_ethnicity_ela.columns.str.split("_").str[1]
            growth_data_me_ethnicity_math.columns = growth_data_me_ethnicity_math.columns.str.split("_").str[1]
    
            # Growth by Subgroup (Both ME and 162)                     
            growth_data_162_subgroup_ela = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains("162")) & (fig_data_subgroup_growth.columns.str.contains("ELA"))]
            growth_data_162_subgroup_math = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains("162")) & (fig_data_subgroup_growth.columns.str.contains("Math"))]
            growth_data_me_subgroup_ela = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains("Majority Enrolled")) & (fig_data_subgroup_growth.columns.str.contains("ELA"))]
            growth_data_me_subgroup_math = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains("Majority Enrolled")) & (fig_data_subgroup_growth.columns.str.contains("Math"))]
            
            growth_data_162_subgroup_ela.columns = growth_data_162_subgroup_ela.columns.str.split("_").str[1]
            growth_data_162_subgroup_math.columns = growth_data_162_subgroup_math.columns.str.split("_").str[1]
            growth_data_me_subgroup_ela.columns = growth_data_me_subgroup_ela.columns.str.split("_").str[1]
            growth_data_me_subgroup_math.columns = growth_data_me_subgroup_math.columns.str.split("_").str[1]

            # SGP by Grade (Both ME and 162)
            sgp_data_162_grades_ela = fig_data_grades_sgp.loc[:,(fig_data_grades_sgp.columns.str.contains("162")) & (fig_data_grades_sgp.columns.str.contains("ELA"))]
            sgp_data_162_grades_math = fig_data_grades_sgp.loc[:,(fig_data_grades_sgp.columns.str.contains("162")) & (fig_data_grades_sgp.columns.str.contains("Math"))]
            sgp_data_me_grades_ela = fig_data_grades_sgp.loc[:,(fig_data_grades_sgp.columns.str.contains("Majority Enrolled")) & (fig_data_grades_sgp.columns.str.contains("ELA"))]
            sgp_data_me_grades_math = fig_data_grades_sgp.loc[:,(fig_data_grades_sgp.columns.str.contains("Majority Enrolled")) & (fig_data_grades_sgp.columns.str.contains("Math"))]
            
            sgp_data_162_grades_ela.columns = sgp_data_162_grades_ela.columns.str.split("_").str[1]
            sgp_data_162_grades_math.columns = sgp_data_162_grades_math.columns.str.split("_").str[1]
            sgp_data_me_grades_ela.columns = sgp_data_me_grades_ela.columns.str.split("_").str[1]
            sgp_data_me_grades_math.columns = sgp_data_me_grades_math.columns.str.split("_").str[1]

            # SGP by Ethnicity (Both ME and 162)
            sgp_data_162_ethnicity_ela = fig_data_ethnicity_sgp.loc[:,(fig_data_ethnicity_sgp.columns.str.contains("162")) & (fig_data_ethnicity_sgp.columns.str.contains("ELA"))]
            sgp_data_162_ethnicity_math = fig_data_ethnicity_sgp.loc[:,(fig_data_ethnicity_sgp.columns.str.contains("162")) & (fig_data_ethnicity_sgp.columns.str.contains("Math"))]
            sgp_data_me_ethnicity_ela = fig_data_ethnicity_sgp.loc[:,(fig_data_ethnicity_sgp.columns.str.contains("Majority Enrolled")) & (fig_data_ethnicity_sgp.columns.str.contains("ELA"))]
            sgp_data_me_ethnicity_math = fig_data_ethnicity_sgp.loc[:,(fig_data_ethnicity_sgp.columns.str.contains("Majority Enrolled")) & (fig_data_ethnicity_sgp.columns.str.contains("Math"))]
            
            sgp_data_162_ethnicity_ela.columns = sgp_data_162_ethnicity_ela.columns.str.split("_").str[1]
            sgp_data_162_ethnicity_math.columns = sgp_data_162_ethnicity_math.columns.str.split("_").str[1]
            sgp_data_me_ethnicity_ela.columns = sgp_data_me_ethnicity_ela.columns.str.split("_").str[1]
            sgp_data_me_ethnicity_math.columns = sgp_data_me_ethnicity_math.columns.str.split("_").str[1]

            # SGP by Subgroup (Both ME and 162)                     
            sgp_data_162_subgroup_ela = fig_data_subgroup_sgp.loc[:,(fig_data_subgroup_sgp.columns.str.contains("162")) & (fig_data_subgroup_sgp.columns.str.contains("ELA"))]
            sgp_data_162_subgroup_math = fig_data_subgroup_sgp.loc[:,(fig_data_subgroup_sgp.columns.str.contains("162")) & (fig_data_subgroup_sgp.columns.str.contains("Math"))]
            sgp_data_me_subgroup_ela = fig_data_subgroup_sgp.loc[:,(fig_data_subgroup_sgp.columns.str.contains("Majority Enrolled")) & (fig_data_subgroup_sgp.columns.str.contains("ELA"))]
            sgp_data_me_subgroup_math = fig_data_subgroup_sgp.loc[:,(fig_data_subgroup_sgp.columns.str.contains("Majority Enrolled")) & (fig_data_subgroup_sgp.columns.str.contains("Math"))]
            
            sgp_data_162_subgroup_ela.columns = sgp_data_162_subgroup_ela.columns.str.split("_").str[1]
            sgp_data_162_subgroup_math.columns = sgp_data_162_subgroup_math.columns.str.split("_").str[1]
            sgp_data_me_subgroup_ela.columns = sgp_data_me_subgroup_ela.columns.str.split("_").str[1]
            sgp_data_me_subgroup_math.columns = sgp_data_me_subgroup_math.columns.str.split("_").str[1]

            label_grade_growth_ela="Percentage of Students Achieving Adequate Growth in ELA by Grade"
            fig_grade_growth_ela = make_growth_chart(growth_data_me_grades_ela, growth_data_162_grades_ela, label_grade_growth_ela)

            label_grade_sgp_ela ="Median SGP in ELA by Grade"
            fig_grade_sgp_ela = make_growth_chart(sgp_data_me_grades_ela, sgp_data_162_grades_ela, label_grade_sgp_ela)

            label_grade_growth_math ="Percentage of Students Achieving Adequate Growth in Math by Grade"
            fig_grade_growth_math = make_growth_chart(growth_data_me_grades_math, growth_data_162_grades_math, label_grade_growth_math)

            label_grade_sgp_math ="Median SGP in Math by Grade"
            fig_grade_sgp_math = make_growth_chart(sgp_data_me_grades_math, sgp_data_162_grades_math, label_grade_sgp_math)            

            label_ethnicity_growth_ela="Percentage of Students Achieving Adequate Growth in ELA by Ethnicity"
            fig_ethnicity_growth_ela = make_growth_chart(growth_data_me_ethnicity_ela, growth_data_162_ethnicity_ela, label_ethnicity_growth_ela)

            label_ethnicity_sgp_ela ="Median SGP in ELA by Ethnicity"
            fig_ethnicity_sgp_ela = make_growth_chart(sgp_data_me_ethnicity_ela, sgp_data_162_ethnicity_ela, label_ethnicity_sgp_ela)

            label_ethnicity_growth_math ="Percentage of Students Achieving Adequate Growth in Math by Ethnicity"
            fig_ethnicity_growth_math = make_growth_chart(growth_data_me_ethnicity_math, growth_data_162_ethnicity_math, label_ethnicity_growth_math)

            label_ethnicity_sgp_math ="Median SGP in Math by Ethnicity"
            fig_ethnicity_sgp_math = make_growth_chart(sgp_data_me_ethnicity_math, sgp_data_162_ethnicity_math, label_ethnicity_sgp_math)

            label_subgroup_growth_ela="Percentage of Students Achieving Adequate Growth in ELA by Subgroup"
            fig_subgroup_growth_ela = make_growth_chart(growth_data_me_subgroup_ela, growth_data_162_subgroup_ela, label_subgroup_growth_ela)

            label_subgroup_sgp_ela ="Median SGP in ELA by Subgroup"
            fig_subgroup_sgp_ela = make_growth_chart(sgp_data_me_subgroup_ela, sgp_data_162_subgroup_ela, label_subgroup_sgp_ela)

            label_subgroup_growth_math ="Percentage of Students Achieving Adequate Growth in Math by Subgroup"
            fig_subgroup_growth_math = make_growth_chart(growth_data_me_subgroup_math, growth_data_162_subgroup_math, label_subgroup_growth_math)

            label_subgroup_sgp_math ="Median SGP in Math by Subgroup"
            fig_subgroup_sgp_math = make_growth_chart(sgp_data_me_subgroup_math, sgp_data_162_subgroup_math, label_subgroup_sgp_math)

        else:

            table_grades_growth_ela_container = {}
            table_grades_growth_math_container = {}
            table_ethnicity_growth_ela_container = {}
            table_ethnicity_growth_math_container = {}
            table_subgroup_growth_ela_container = {}
            table_subgroup_growth_math_container = {}

            fig_grade_growth_ela = {}
            fig_grade_sgp_ela = {}
            fig_grade_growth_math = {}
            fig_grade_sgp_math = {}
            fig_ethnicity_growth_ela = {}
            fig_ethnicity_sgp_ela = {}
            fig_ethnicity_growth_math = {}
            fig_ethnicity_sgp_math = {}
            fig_subgroup_growth_ela = {}
            fig_subgroup_sgp_ela = {}
            fig_subgroup_growth_math = {}
            fig_subgroup_sgp_math = {}                        

            state_growth_main_container = {"display": "none"}
            state_growth_empty_container = {"display": "block"}

            # NOTE: The above code shows median SGP for all students, the following code would give us median
            # sgp for students achieving adequate growth. What is the value of using this metric instead?
            # adequate_growth_data = growth_data[growth_data["ILEARNGrowth Level"] == "Adequate Growth"]
            # median_sgp_adequate = adequate_growth_data.groupby(["Test Year","Grade Level", "Subject"])["ILEARNGrowth Percentile"].median()
            # adequate_growth_data_162 = growth_data_162[growth_data_162["ILEARNGrowth Level"] == "Adequate Growth"]
            # median_sgp_adequate_162 = adequate_growth_data_162.groupby(["Test Year","Grade Level", "Subject"])["ILEARNGrowth Percentile"].median()

    else:
        # this should only trigger if radio_value is somehow anything other than proficiency or growth

        # growth
        table_grades_growth_ela_container = {}
        table_grades_growth_math_container = {}
        table_ethnicity_growth_ela_container = {}
        table_ethnicity_growth_math_container = {}
        table_subgroup_growth_ela_container = {}
        table_subgroup_growth_math_container = {}

        fig_grade_growth_ela = {}
        fig_grade_sgp_ela = {}
        fig_grade_growth_math = {}
        fig_grade_sgp_math = {}
        fig_ethnicity_growth_ela = {}
        fig_ethnicity_sgp_ela = {}
        fig_ethnicity_growth_math = {}
        fig_ethnicity_sgp_math = {}
        fig_subgroup_growth_ela = {}
        fig_subgroup_sgp_ela = {}
        fig_subgroup_growth_math = {}
        fig_subgroup_sgp_math = {}    
        state_growth_main_container = {"display": "none"}
        state_growth_empty_container = {"display": "none"}   

        # proficiency
        hs_grad_overview_table = {}
        hs_grad_ethnicity_table = {}
        hs_grad_subgroup_table = {}
        sat_overview_table = {}
        sat_ethnicity_table = {}
        sat_subgroup_table = {}        
        hs_table_container = {"display": "none"}

        k8_grade_table = {}
        k8_ethnicity_table = {}
        k8_subgroup_table = {}
        k8_other_table = {}
        k8_table_container = {"display": "none"}

        k8_grade_ela_fig = {}
        k8_grade_math_fig = {}
        k8_ethnicity_ela_fig = {}
        k8_ethnicity_math_fig = {}
        k8_subgroup_ela_fig = {}
        k8_subgroup_math_fig = {}

        main_container = {"display": "none"}
        empty_container = {"display": "block"}

    if radio_value == "proficiency":
        if selected_school_type == "AHS":
            academic_information_notes_string = "Adult High Schools enroll students who are over the age of 18, under credited, \
                dropped out of high school for a variety of reasons, and are typically out of cohort from \
                their original graduation year. Because graduation rate is calculated at the end of the school \
                year regardless of the length of time a student is enrolled at a school, it is not comparable to \
                the graduation rate of a traditional high school."
            
        elif (selected_school_type == "K8" or selected_school_type == "K12" or selected_school_type == "HS"):
            academic_information_notes_string = "There are a number of factors that make it difficult to make valid and reliable \
                comparisons between test scores from 2019 to 2022. For example, ILEARN was administered for \
                the first time during the 2018-19 SY and represented an entirely new type and mode of \
                assessment (adaptive and online-only). No State assessment was administered  in 2020 because \
                of the Covid-19 pandemic. Finally, the 2019 data set includes only students  who attended the \
                testing school for 162 days, while the 2021 and 2022 data sets included all tested students. \
                Data Source: Indiana Department of Education Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)."
        else:
            academic_information_notes_string = ""

    if radio_value == "growth":
        academic_information_notes_string = "State growth data comes from IDOE's LINK. Identifying information is scrubbed and data is aggregated \
            Federal Growth Data comes from IDOE's School Report Card Summaries of Federal Growth indicators. \
            While the data represented here is an accurate representation of the data present in the Summaries, \
            it has not been otherwise reconciled with the raw data used to produce the Summaries. It is presented \
            here for informational purposes only."

    return (
        k8_grade_table, k8_grade_ela_fig, k8_grade_math_fig, k8_ethnicity_table, k8_ethnicity_ela_fig, k8_ethnicity_math_fig,
        k8_subgroup_table, k8_subgroup_ela_fig, k8_subgroup_math_fig, k8_other_table, k8_table_container, hs_grad_overview_table,
        hs_grad_ethnicity_table, hs_grad_subgroup_table, sat_overview_table, sat_ethnicity_table, sat_subgroup_table, 
        hs_table_container, main_container, empty_container, no_data_to_display, table_grades_growth_ela_container, table_grades_growth_math_container,
        table_ethnicity_growth_ela_container, table_ethnicity_growth_math_container, table_subgroup_growth_ela_container, 
        table_subgroup_growth_math_container, fig_grade_growth_ela, fig_grade_sgp_ela, fig_grade_growth_math, fig_grade_sgp_math,
        fig_ethnicity_growth_ela, fig_ethnicity_sgp_ela, fig_ethnicity_growth_math, fig_ethnicity_sgp_math, fig_subgroup_growth_ela,
        fig_subgroup_sgp_ela, fig_subgroup_growth_math, fig_subgroup_sgp_math,state_growth_main_container,
        state_growth_empty_container, no_state_growth_data_to_display, academic_information_notes_string
    ) # growth_values_table, growth_values_table_container,

def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(subnav_academic(), className="tabs"),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                ],
                className="row",
            ),
            html.Div(
                [    
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label("Notes:", className="header_label"),
                                    html.P(""),
                                        html.P(id="academic-information-notes-string",
                                            style={
                                                    "textAlign": "Left",
                                                    "color": "#6783a9",
                                                    "fontSize": 12,
                                                    "marginLeft": "10px",
                                                    "marginRight": "10px",
                                                    "marginTop": "10px",
                                            }
                                        ),
                                ],
                                className = "pretty_container seven columns"
                            ),
                        ],
                        className = "bare_container_center twelve columns"
                    ),
                ],
                className = "row",
            ),
            # html.Div(
            #     [                     
            #         html.Div(
            #             [                             
            #                 html.Div(id="growth-values-table"),
            #             ],
            #             className = "bare_container_center twelve columns"
            #         ),
            #     ],
            #     id="growth-values-table-container",
            # ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    dbc.RadioItems(
                                        id="radio-button-academic-info",
                                        className="btn-group",
                                        inputClassName="btn-check",
                                        labelClassName="btn btn-outline-primary",
                                        labelCheckedClassName="active",
                                        options=[
                                            {"label": "Proficiency", "value": "proficiency"},
                                            {"label": "Growth", "value": "growth"},
                                        ],
                                        value="proficiency",
                                        persistence=True,
                                        persistence_type="local",
                                    ),
                                ],
                                className="radio-group",
                            ),
                        ],
                        className = "bare_container_center twelve columns",
                    ),
                ],
                className = "row",
            ),
            html.Div(
                [
                dcc.Loading(
                    id="loading",
                    type="circle",
                    fullscreen = True,
                    style={
                        "position": "absolute",
                        "align-self": "center",
                        "background-color": "#F2F2F2",
                        },
                    children=[
                    html.Div(
                        [
                            html.Div(id="k8-grade-table", children=[]),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-grade-ela-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="k8-grade-math-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(id="k8-ethnicity-table", children=[]),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-ethnicity-ela-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="k8-ethnicity-math-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(id="k8-subgroup-table", children=[]),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-subgroup-ela-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="k8-subgroup-math-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(id="k8-other-table", children=[]),
                        ],
                        id="k8-table-container",
                    ),
                    html.Div(
                        [
                            html.Div(id="hs-grad-overview-table"),
                            html.Div(id="hs-grad-ethnicity-table"),
                            html.Div(id="hs-grad-subgroup-table"),
                            html.Div(id="sat-overview-table"),
                            html.Div(id="sat-ethnicity-table"),
                            html.Div(id="sat-subgroup-table"),
                        ],
                        id="hs-table-container",
                    ),
                    ]),
                ],
                id = "academic-information-main-container",
            ),
            html.Div(
                [
                    html.Div(id="academic-information-no-data"),
                ],
                id = "academic-information-empty-container",
            ),            
            html.Div(
                [
                    html.Div(id="table-grades-growth-ela-container", children=[]),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="fig-grade-growth-ela", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),
                            html.Div(
                                [                            
                                    html.Div(id="fig-grade-sgp-ela", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),                            
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(id="table-grades-growth-math-container", children=[]),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="fig-grade-growth-math", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),
                            html.Div(
                                [                            
                                    html.Div(id="fig-grade-sgp-math", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),                            
                        ],
                        className="bare_container_center twelve columns",
                    ),                    
                    html.Div(id="table-ethnicity-growth-ela-container", children=[]),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="fig-ethnicity-growth-ela", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),
                            html.Div(
                                [                            
                                    html.Div(id="fig-ethnicity-sgp-ela", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),                            
                        ],
                        className="bare_container_center twelve columns",
                    ),                         
                    html.Div(id="table-ethnicity-growth-math-container", children=[]),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="fig-ethnicity-growth-math", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),
                            html.Div(
                                [                            
                                    html.Div(id="fig-ethnicity-sgp-math", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),                            
                        ],
                        className="bare_container_center twelve columns",
                    ),                         
                    html.Div(id="table-subgroup-growth-ela-container", children=[]),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="fig-subgroup-growth-ela", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),
                            html.Div(
                                [                            
                                    html.Div(id="fig-subgroup-sgp-ela", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),                            
                        ],
                        className="bare_container_center twelve columns",
                    ),                         
                    html.Div(id="table-subgroup-growth-math-container", children=[]),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="fig-subgroup-growth-math", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),
                            html.Div(
                                [                            
                                    html.Div(id="fig-subgroup-sgp-math", children=[]),
                                ],
                                className="pretty_container six columns",
                            ),                            
                        ],
                        className="bare_container_center twelve columns",
                    ),                         
                ],
                id = "state-growth-main-container",
            ),
            html.Div(
                [
                    html.Div(id="state-growth-no-data"),
                ],
                id = "state-growth-empty-container",
            ),
        ],
        id="mainContainer",
    )