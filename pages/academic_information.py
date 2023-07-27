#########################################
# ICSB Dashboard - Academic Information #
#########################################
# author:   jbetley
# version:  1.07
# date:     07/25/23

import dash
from dash import dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import re
import os

# import local functions
from .table_helpers import no_data_page, no_data_table, hidden_table, create_academic_info_table, get_svg_circle, \
    create_growth_table, set_table_layout
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
    Output("hs-eca-table", "children"),
    Output("hs-table-container", "style"),
    Output("academic-information-main-container", "style"),
    Output("academic-information-empty-container", "style"),
    Output("academic-information-no-data", "children"),
    Output("k8-overall-indicators", "children"),
    Output("hs-overall-indicators", "children"),
    Output("combined-indicators", "children"),
    Output("enrollment-indicators", "children"),
    Output("subgroup-grades", "children"),
    Output("k8-academic-achievement", "children"),
    Output("hs-academic-achievement", "children"),
    Output("k8-academic-progress", "children"),
    Output("hs-academic-progress", "children"),
    Output("closing-achievement-gap", "children"),
    Output("graduation-rate-indicator", "children"),
    Output("strength-of-diploma-indicator", "children"),
    Output("ela-progress-indicator", "children"),
    Output("absenteeism-indicator", "children"),
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
    Output("federal-growth-main-container", "style"),
    Output("federal-growth-empty-container", "style"),
    Output("federal-growth-no-data", "children"),
    Output("state-growth-main-container", "style"),
    Output("state-growth-empty-container", "style"),    
    Output("state-growth-no-data", "children"),
    Output("growth-values-table", "children"),    
    Output("growth-values-table-container", "style"),
    Output("academic-information-notes-string", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input(component_id="radio-button-academic-info", component_property="value")
)
def update_academic_information_page(school: str, year: str, radio_value:str):
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
    
    federal_growth_main_container = {"display": "block"}
    federal_growth_empty_container = {"display": "none"}
    no_federal_growth_data_to_display = no_data_page("Federal Growth Calculations")
    
    state_growth_main_container = {"display": "block"}
    state_growth_empty_container = {"display": "none"}   
    no_state_growth_data_to_display = no_data_page("Indiana State Growth Calculations")

    growth_values_table = [html.Img(src="assets/growth_table.jpg", hidden=True)]
    growth_values_table_container = {"display": "none"}

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]
    selected_school_id = int(selected_school["School ID"].values[0])

    ## Proficiency Tables ##
    if radio_value == "proficiency":

        # growth tables to null
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

        k8_overall_indicators = {}
        hs_overall_indicators = {}
        combined_indicators = {}
        enrollment_indicators = {}
        subgroup_grades = {}
        k8_academic_achievement = {}
        hs_academic_achievement = {}
        k8_academic_progress = {}
        hs_academic_progress = {}
        closing_achievement_gap = {}
        graduation_rate_indicator = {}
        strength_of_diploma_indicator = {}
        ela_progress_indicator = {}
        absenteeism_indicator = {}
        federal_growth_main_container = {"display": "none"}
        federal_growth_empty_container = {"display": "none"}
     
        if (selected_school_type == "K8" or selected_school_type == "K12"):

            # if K8, hide HS tables (except for CHS prior to 2021 when it was a K12)
            if selected_school_type == "K8" and not (selected_school_id == 5874 and selected_year_numeric < 2021):
                hs_grad_overview_table = {}
                hs_grad_ethnicity_table = {}
                hs_grad_subgroup_table = {}
                sat_overview_table = {}
                sat_ethnicity_table = {}
                sat_subgroup_table = {}                  
                hs_eca_table = {}
                hs_table_container = {"display": "none"}

            # get all years of data
            raw_k8_school_data = get_k8_school_academic_data(school)
            
            # filter out years of data later than the selected year
            if excluded_years:
                selected_raw_k8_school_data = raw_k8_school_data[~raw_k8_school_data["Year"].isin(excluded_years)].copy()
            else:
                selected_raw_k8_school_data = raw_k8_school_data.copy()
            
            if len(selected_raw_k8_school_data.index) > 0:
            
                all_k8_school_data = process_k8_academic_data(selected_raw_k8_school_data, selected_year_string, school)

                all_k8_school_data = all_k8_school_data.fillna("No Data")
                all_k8_school_data = (all_k8_school_data.set_index(["Category"]).add_suffix("School").reset_index())

                all_k8_school_data.columns = all_k8_school_data.columns.str.replace(r"School$", "", regex=True)

                all_k8_school_data["Category"] = (all_k8_school_data["Category"].str.replace(" Proficient %", "").str.strip())

                all_k8_school_data.loc[all_k8_school_data["Category"] == "IREAD Pass %", "Category"] = "IREAD Proficiency (Grade 3 only)"

                # reverse column order of year columns
                # yrs = [i for i in all_k8_school_data.columns if "Category" not in i]
                # all_k8_school_data = all_k8_school_data[list(all_k8_school_data.columns[:1]) + yrs[::-1]]

                years_by_grade = all_k8_school_data[all_k8_school_data["Category"].str.contains("|".join(grades_all))]

                if not years_by_grade.empty:
                    k8_grade_table = create_academic_info_table(years_by_grade,"Proficiency by Grade","proficiency")
                
                else:
                    k8_grade_table = no_data_table("Proficiency by Grade")

                years_by_subgroup = all_k8_school_data[all_k8_school_data["Category"].str.contains("|".join(subgroup))]

                if not years_by_subgroup.empty:            
                    k8_subgroup_table = create_academic_info_table(years_by_subgroup,"Proficiency by Subgroup","proficiency")
                else:
                    k8_subgroup_table = no_data_table("Proficiency by Subgroup")

                years_by_ethnicity = all_k8_school_data[all_k8_school_data["Category"].str.contains("|".join(ethnicity))]

                if not years_by_ethnicity.empty:            
                    k8_ethnicity_table = create_academic_info_table(years_by_ethnicity,"Proficiency by Ethnicity","proficiency")
                else:
                    k8_ethnicity_table = no_data_table("Proficiency by Ethnicity")

                # Attendance rate
                school_demographic_data = get_demographic_data(school)
                attendance_rate = get_attendance_data(school_demographic_data, selected_year_string)

                if len(attendance_rate.index) == 0:
                    k8_other_table = no_data_table("Attendance Data")
                else:
                    k8_other_table = create_academic_info_table(attendance_rate,"Attendance Data","proficiency")

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
                
                proficiency_rating = [
                    "Below Proficiency",
                    "Approaching Proficiency",
                    "At Proficiency",
                    "Above Proficiency"
                ]

                # NOTE: This may seem kludgy, but runs consistently around .15s
                # for each category, create a proficiency_columns list of columns using the strings in
                # "proficiency_rating" and then divide each column by "Total Tested"
                categories = grades_all + ethnicity + subgroup

                # create dataframe to hold annotations (Categories missing data)
                # Annotations are currently not used
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

                # drop all remaining columns used for calculation that we dont want to chart
                all_proficiency_data.drop(list(all_proficiency_data.filter(regex="Total\||Total Proficient|ELA and Math")),
                    axis=1,
                    inplace=True,
                )

                # Replace Grade X with ordinal number (e.g., Grade 4 = 4th)
                all_proficiency_data = all_proficiency_data.rename(columns=lambda x: re.sub("(Grade )(\d)", "\\2th", x))

                # all use "th" suffix except for 3rd - so we need to specially treat "3""
                all_proficiency_data.columns = [x.replace("3th", "3rd") for x in all_proficiency_data.columns.to_list()]

                # transpose df
                all_proficiency_data = (
                    all_proficiency_data.T.rename_axis("Category")
                    .rename_axis(None, axis=1)
                    .reset_index()
                )

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
                # school type is K8 or K12, but there is no data
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

        # NOTE: There is a special exception here for Christel House South - prior to 2021,
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

            if len(selected_raw_hs_school_data.index) > 0:

                selected_raw_hs_school_data = filter_high_school_academic_data(selected_raw_hs_school_data)
                all_hs_school_data = process_high_school_academic_data(selected_raw_hs_school_data, selected_year_string, school)

                # Graduation Rate
                grad_overview_categories = [
                    "Total",
                    "Non Waiver",
                    "State Average"
                    # "Strength of Diploma",    # Not currently displayed
                ]

                if selected_school_type == "AHS":
                    grad_overview_categories.append("CCR Percentage")

                all_hs_school_data.columns = all_hs_school_data.columns.astype(str)

                eca_data = all_hs_school_data[all_hs_school_data["Category"].str.contains("Grade 10")].copy()
                eca_data = eca_data.dropna(axis=1,how="all")
                
                if len(eca_data.columns) > 1:       
                    hs_eca_table = create_academic_info_table(eca_data,"End of Course Assessments","proficiency")            
                else:
                    hs_eca_table = no_data_table("End of Course Assessments")

                # Graduation Rate Tables
                graduation_data = all_hs_school_data[all_hs_school_data["Category"].str.contains("Graduation")].copy()

                # drop "Graduation Rate" from all "Category" rows and remove whitespace
                graduation_data["Category"] = (graduation_data["Category"].str.replace("Graduation Rate", "").str.strip())

                grad_overview = graduation_data[graduation_data["Category"].str.contains("|".join(grad_overview_categories))]
                grad_overview = grad_overview.dropna(axis=1,how="all")

                if len(grad_overview.columns) > 1:
                    hs_grad_overview_table = create_academic_info_table(grad_overview,"Graduation Rate Overview","proficiency")
                else:
                    hs_grad_overview_table = no_data_table("Graduation Rate Overview")

                grad_ethnicity = graduation_data[graduation_data["Category"].str.contains("|".join(ethnicity))]
                grad_ethnicity = grad_ethnicity.dropna(axis=1,how="all")

                if len(grad_ethnicity.columns) > 1:                
                    hs_grad_ethnicity_table = create_academic_info_table(grad_ethnicity,"Graduation Rate by Ethnicity","proficiency")
                else:
                    hs_grad_ethnicity_table = no_data_table("Graduation Rate by Ethnicity")

                grad_subgroup = graduation_data[graduation_data["Category"].str.contains("|".join(subgroup))]
                grad_subgroup = grad_subgroup.dropna(axis=1,how="all")

                if len(grad_subgroup.columns) > 1:
                    hs_grad_subgroup_table = create_academic_info_table(grad_subgroup,"Graduation Rate by Subgroup","proficiency")
                else:
                    hs_grad_subgroup_table = no_data_table("Graduation Rate by Subgroup")

                # SAT Benchmark Tables
                sat_table_data = all_hs_school_data[all_hs_school_data["Category"].str.contains("Benchmark %")].copy()

                # drop "Graduation Rate" from all "Category" rows and remove whitespace
                sat_table_data["Category"] = (sat_table_data["Category"].str.replace("Benchmark %", "").str.strip())

                sat_overview = sat_table_data[sat_table_data["Category"].str.contains("School Total")]
                sat_overview = sat_overview.dropna(axis=1,how="all")

                if len(sat_overview.columns) > 1:
                    sat_overview_table = create_academic_info_table(sat_overview,"SAT Overview","proficiency")
                else:
                    sat_overview_table = no_data_table("SAT Overview")

                sat_ethnicity = sat_table_data[sat_table_data["Category"].str.contains("|".join(ethnicity))]
                sat_ethnicity = sat_ethnicity.dropna(axis=1,how="all")

                if len(sat_ethnicity.columns) > 1:
                    sat_ethnicity_table = create_academic_info_table(sat_ethnicity,"SAT Benchmarks by Ethnicity","proficiency")
                else:
                    sat_ethnicity_table = no_data_table("SAT Benchmarks by Ethnicity")

                sat_subgroup = sat_table_data[sat_table_data["Category"].str.contains("|".join(subgroup))]
                sat_subgroup = sat_subgroup.dropna(axis=1,how="all")

                if len(sat_subgroup.columns) > 1:                
                    sat_subgroup_table = create_academic_info_table(sat_subgroup,"SAT Benchmarks by Subgroup","proficiency")
                else:
                    sat_subgroup_table = no_data_table("SAT Benchmarks by Subgroup")

            else:
                # selected type is HS, AHS, K12, or CHS < 2021, but there is no data
                hs_grad_overview_table = {}
                hs_grad_ethnicity_table = {}
                hs_grad_subgroup_table = {}
                sat_overview_table = {}
                sat_ethnicity_table = {}
                sat_subgroup_table = {}        
                hs_eca_table = {}
                hs_table_container = {"display": "none"}
                
                main_container = {"display": "none"}
                empty_container = {"display": "block"}      

    elif radio_value =="growth":

    # Growth Tab #

        # if "Growth" Tab is selected, set all proficiency tables to null
        # and containers to display: none
        hs_grad_overview_table = {}
        hs_grad_ethnicity_table = {}
        hs_grad_subgroup_table = {}
        sat_overview_table = {}
        sat_ethnicity_table = {}
        sat_subgroup_table = {}        
        hs_eca_table = {}
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

        # Percentage of students achieving “typical” or “high” growth on the state assessment in ELA/Math
        # Median SGP of students achieving "adequate and sufficient growth" on the state assessment in ELA/Math

            # ILEARNGrowthLevel / TestYear / GradeLevel / Subject
            # group by Year, Subject and Grade Level?
            # Also: Ethnicity, Socio Economic Status Category, English Learner Status Category, Special Ed Status Category
            # Homeless Status Category, High Ability Status Category    

        # dataset is all students who are coded as "Majority Enrolled" at the school
        all_growth_data = get_growth_data(school)

        # filter out years of data later than the selected year
        if excluded_years:
            growth_data = all_growth_data[~all_growth_data["Test Year"].isin(excluded_years)].copy()
        else:
            growth_data = all_growth_data.copy()

        if len(growth_data.index) > 0:
            
            growth_values_table = [html.Img(src="assets/growth_table.jpg", hidden=False)]
            growth_values_table_container = {"display": "block"}

            # NOTE: This calculates the student difference
            # find the difference between the count of Majority Enrolled and 162-Day students by Year
            # counts_growth = growth_data.groupby("Test Year")["Test Year"].count().reset_index(name = "Count (Majority Enrolled)")
            # counts_growth_162 = growth_data_162.groupby("Test Year")["Test Year"].count().reset_index(name = "Count (162 Days)")

            # counts_growth["School Name"] = selected_school["School Name"].values[0]
            # counts_growth["Count (162 Days)"] = counts_growth_162["Count (162 Days)"]
            # counts_growth["Difference"] = counts_growth["Count (Majority Enrolled)"] - counts_growth["Count (162 Days)"]

            # print("Count Difference")
            # print(counts_growth)

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
            
            # Tables

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

        ## Figures

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

            # TODO: Do we want to limit to median SGP for those students achieving "Adequate Growth"?
            # # median SGP for students achieving "Adequate Growth" grouped by Year, Grade, and Subject
            # adequate_growth_data = growth_data[growth_data["ILEARNGrowth Level"] == "Adequate Growth"]
            # median_sgp_adequate = adequate_growth_data.groupby(["Test Year","Grade Level", "Subject"])["ILEARNGrowth Percentile"].median()
            # adequate_growth_data_162 = growth_data_162[growth_data_162["ILEARNGrowth Level"] == "Adequate Growth"]
            # median_sgp_adequate_162 = adequate_growth_data_162.groupby(["Test Year","Grade Level", "Subject"])["ILEARNGrowth Percentile"].median()

        # Federal Growth #

        # NOTE: Currently have a single year of growth data (2022). Therefore unless
        # the selected year is 2022, we show an empty table.
        if selected_year_string == "2022":
            # NOTE: This data sucks ass. It originates from an excel file that has a mishmash of small
            # tables with different headers and varying columns and rows. Data is different for different
            # grade configurations, and, to add insult to injury, sometimes tables are present with null
            # values and other times the tables are just missing. So we pull the data out by specific rows
            # in order to avoid column index errors when pandas tries to read it in all at once.
            
            # NOTE: the original excel files (format: "2022ReportCardSummary86855593ALL") are in even
            # worse shape with tables arranged horizontally and a liberal use of Merge Columns. There 
            # is a utility file ("_growthFileScrape.py") that converts these original files to a flattened
            # csv with all tables arranged vertically and missing tables represented by empty rows.
            # Unfortunately,it still has variable and unrelated columns, so we need to pull each individual
            # table out by row using iloc (e.g., growth_data.iloc[0:10]). Eventually we need to put
            # all this crap into a database.

            growth_file = "data/growth_data" + school + ".csv"
            
            # Adult high schools and new charter schools do not have growth data.
            # First check if there is a growth data file. There will either be a
            # file with data or there will not be a file. There will never be an
            # empty growth data file.
            if os.path.isfile(growth_file):

                # get all tables. Because there are variable columns, we set a fixed
                # range equal to the maximum number of columns
                growth_data = pd.read_csv(growth_file,header = None,names=range(8))

                # Global cleaning of growth data
                growth_data = growth_data.replace({
                    "English/Lang. Arts": "ELA",
                    "Mathematics": "Math",
                    "Sugroup": "Subgroup",
                    "Hispanic Ethnicity": "Hispanic",
                    "Elementary/Middle School Overall Weight and Points:": "Overall",
                    "High School Overall Weight and Points:": "Overall"
                    })

                # remove excess spaces between "(" and ")"
                growth_data = growth_data.replace(r"\s+(?=[^(\)]*\))","", regex=True)

                # remove extra space between number and "%"
                growth_data = growth_data.replace(r"(?<=\d) +(?=%)","", regex=True)                

                # Get individual tables one by one because tables have variable
                # number of columns

                def replace_header(data: pd.DataFrame) -> pd.DataFrame:
                    """ Takes a Pandas Dataframe, replaces header with first row, and
                        drops all nan columns
                    Args:
                        data (pd.Dataframe): Pandas dataframe

                    Returns:
                        pd.Dataframe: returns the same dataframe first row headers and
                        no NaN columns
                    """
                    data.columns = data.iloc[0].tolist()
                    data = data[1:]
                    data = data.dropna(axis=1, how="all")

                    return data
        
                ## k8 growth indicators ##
                k8_overall_indicators_data = growth_data.iloc[0:10].copy()

                if not k8_overall_indicators_data.isnull().all().all():
                    
                    k8_overall_indicators_data = replace_header(k8_overall_indicators_data)

                    # Drop rows where there are zero points and No Rating
                    k8_overall_indicators_data = k8_overall_indicators_data.loc[~((k8_overall_indicators_data["Points"] == "0.00") & \
                        (k8_overall_indicators_data["Rating"] == "No Rating"))]
                    
                    # replace metrics with svg circles
                    k8_overall_indicators_data = get_svg_circle(k8_overall_indicators_data)
                
                    k8_overall_indicators = create_academic_info_table(k8_overall_indicators_data,"Elementary/Middle Growth Summary","growth")
                else:
                    k8_overall_indicators = hidden_table()

                ## hs growth indicators ##
                hs_overall_indicators_data = growth_data.iloc[10:20].copy()

                if not hs_overall_indicators_data.isnull().all().all():

                    hs_overall_indicators_data = replace_header(hs_overall_indicators_data)

                    hs_overall_indicators_data = hs_overall_indicators_data.loc[~((hs_overall_indicators_data["Points"] == "0.00") & \
                        (hs_overall_indicators_data["Rating"] == "No Rating"))]
                    
                    hs_overall_indicators_data = get_svg_circle(hs_overall_indicators_data)

                    hs_overall_indicators = create_academic_info_table(hs_overall_indicators_data,"High School Growth Summary","growth")
                else:
                    hs_overall_indicators = hidden_table()

                ## combined growth indicators ##
                combined_indicators_data = growth_data.iloc[20:24].copy()

                if not combined_indicators_data.isnull().all().all():

                    # drop empty columns and add headers
                    combined_indicators_data = combined_indicators_data.dropna(axis=1, how="all")
                    combined_indicators_data.columns = ["Category","Weighted Points"]
                    
                    combined_indicators_data = get_svg_circle(combined_indicators_data)

                    combined_indicators = create_academic_info_table(combined_indicators_data,"Combined Growth Summary","growth")
                else:
                    combined_indicators = hidden_table()

                ## enrollment indicators ##
                enrollment_indicators_data = growth_data.iloc[24:27].copy()

                if not enrollment_indicators_data.isnull().all().all():
                    
                    enrollment_indicators_data = replace_header(enrollment_indicators_data)

                    # some tables, including enrollment_indicators_data, have a Grades 3-8 row
                    # and a Grades 9-12 row regardless of whether the school has data for both.
                    # So either check second row for "0" (as in this case) or NaN and remove if true.
                    if enrollment_indicators_data.iloc[1,1] == "0":
                        enrollment_indicators_data = enrollment_indicators_data.iloc[:1]        

                    # rename first column
                    enrollment_indicators_data = enrollment_indicators_data.rename(columns={enrollment_indicators_data.columns[0]: "Grade Span"})
                    
                    enrollment_indicators = create_academic_info_table(enrollment_indicators_data,"Enrollment Indicators","growth")
                else:
                    enrollment_indicators = hidden_table()

                ## subgroup grades indicators ##
                subgroup_grades_data = growth_data.iloc[27:33].copy()

                if not subgroup_grades_data.isnull().all().all():
                    
                    subgroup_grades_data = replace_header(subgroup_grades_data)

                    # subgroup_grades_data is two tables side by side with the same column headers.
                    # We use groupby() to unpivot & combine the duplicate columns, and then reorder
                    # the columns
                    subgroup_grades_data = subgroup_grades_data.groupby(subgroup_grades_data.columns.values, axis=1).agg(lambda x: x.values.tolist()).sum().apply(pd.Series).T
                    subgroup_grades_data = subgroup_grades_data[["Subgroup", "Points", "Rating"]]

                    subgroup_grades_data = subgroup_grades_data.loc[~((subgroup_grades_data["Points"] == "0") & \
                        (subgroup_grades_data["Rating"] == "No Rating"))]

                    subgroup_grades_data = get_svg_circle(subgroup_grades_data)
                    
                    subgroup_grades = create_academic_info_table(subgroup_grades_data,"Subgroup Grades","growth")
                else:
                    subgroup_grades = hidden_table()

                ## k8 academic achievement indicators ##
                k8_academic_achievement_data = growth_data.iloc[34:37].copy()

                if not k8_academic_achievement_data.iloc[1:,1:].isnull().all().all():

                    k8_academic_achievement_data = replace_header(k8_academic_achievement_data)

                    k8_academic_achievement = create_academic_info_table(k8_academic_achievement_data,"Elementary/Middle Academic Achievement","growth")
                else:
                    k8_academic_achievement = hidden_table()

                ## hs academic achievement indicators ##
                hs_academic_achievement_data = growth_data.iloc[38:41].copy()

                # skip 1st column and 1st row in determining whether all cols are null
                if not hs_academic_achievement_data.iloc[1:,1:].isna().all().all():

                    hs_academic_achievement_data = replace_header(hs_academic_achievement_data)

                    hs_academic_achievement = create_academic_info_table(hs_academic_achievement_data,"High School Academic Achievement","growth")
            
                else:
                    hs_academic_achievement = hidden_table()

                ## k8 academic progress indicators ##
                k8_academic_progress_data = growth_data.iloc[42:45].copy()

                if not k8_academic_progress_data.iloc[1:,1:].isna().all().all():

                    k8_academic_progress_data = replace_header(k8_academic_progress_data)

                    k8_academic_progress = create_academic_info_table(k8_academic_progress_data,"Elementary/Middle Progress Indicators","growth")
                else:
                    k8_academic_progress = hidden_table()

                ## hs academic progress indicators ##
                hs_academic_progress_data = growth_data.iloc[46:49].copy()

                if not hs_academic_progress_data.iloc[1:,1:].isna().all().all():

                    hs_academic_progress_data = replace_header(hs_academic_progress_data)

                    hs_academic_progress = create_academic_info_table(hs_academic_progress_data,"High School Progress Indicators","growth")
                else:
                    hs_academic_progress = hidden_table()

                ## closing achievement gap indicators ##
                closing_achievement_gap_data = growth_data.iloc[50:53].copy()

                if not closing_achievement_gap_data.iloc[1:,1:].isna().all().all():

                    closing_achievement_gap_data = replace_header(closing_achievement_gap_data)

                    closing_achievement_gap = create_academic_info_table(closing_achievement_gap_data,"Closing the Achievement Gap","growth")
        
                else:
                    closing_achievement_gap = hidden_table()

                ## graduation rate indicator ##
                graduation_rate_indicator_data = growth_data.iloc[53:55].copy()

                if not graduation_rate_indicator_data.isnull().all().all():

                    graduation_rate_indicator_data = replace_header(graduation_rate_indicator_data)

                    graduation_rate_indicator = create_academic_info_table(graduation_rate_indicator_data,"Graduation Rate Indicator","growth")
                else:
                    graduation_rate_indicator = hidden_table()

                ## strength of diploma indicator ##
                strength_of_diploma_indicator_data = growth_data.iloc[55:57].copy()

                if not strength_of_diploma_indicator_data.isnull().all().all():

                    strength_of_diploma_indicator_data = replace_header(strength_of_diploma_indicator_data)
                    
                    strength_of_diploma_indicator = create_academic_info_table(strength_of_diploma_indicator_data,"Strength of Diploma Indicator","growth")
                else:
                    strength_of_diploma_indicator = hidden_table()

                ## ela progress indicators ##
                ela_progress_indicator_data = growth_data.iloc[57:60].copy()

                if not ela_progress_indicator_data.iloc[1:,1:].isna().all().all():

                    ela_progress_indicator_data = replace_header(ela_progress_indicator_data)

                    # drops second row by index (Grade 9-12) if all value columns are NaN
                    if ela_progress_indicator_data.loc[[59]].isna().sum().sum() >=3:
                        ela_progress_indicator_data = ela_progress_indicator_data.iloc[:1]

                    ela_progress_indicator = create_academic_info_table(ela_progress_indicator_data,"Progress in Achieving English Language Proficiency Indicator","growth")
                else:
                    ela_progress_indicator = hidden_table()

                ## chronic absenteeism indicators ##
                absenteeism_indicator_data = growth_data.iloc[60:64].copy()

                if not absenteeism_indicator_data.iloc[1:,1:].isna().all().all():

                    absenteeism_indicator_data = replace_header(absenteeism_indicator_data)

                    if absenteeism_indicator_data.loc[[62]].isna().sum().sum() >=3:
                        absenteeism_indicator_data = absenteeism_indicator_data.iloc[:1]

                    absenteeism_indicator = create_academic_info_table(absenteeism_indicator_data,"Addressing Chronic Absenteeism Indicator","growth")
                else:
                    absenteeism_indicator = hidden_table()

            else:
                # its 2022 but there is no federal growth data
                k8_overall_indicators = {}
                hs_overall_indicators = {}
                combined_indicators = {}
                enrollment_indicators = {}
                subgroup_grades = {}
                k8_academic_achievement = {}
                hs_academic_achievement = {}
                k8_academic_progress = {}
                hs_academic_progress = {}
                closing_achievement_gap = {}
                graduation_rate_indicator = {}
                strength_of_diploma_indicator = {}
                ela_progress_indicator = {}
                absenteeism_indicator = {}
                federal_growth_main_container = {"display": "none"}
                federal_growth_empty_container = {"display": "block"}

        else:
            # its not 2022
            k8_overall_indicators = {}
            hs_overall_indicators = {}
            combined_indicators = {}
            enrollment_indicators = {}
            subgroup_grades = {}
            k8_academic_achievement = {}
            hs_academic_achievement = {}
            k8_academic_progress = {}
            hs_academic_progress = {}
            closing_achievement_gap = {}
            graduation_rate_indicator = {}
            strength_of_diploma_indicator = {}
            ela_progress_indicator = {}
            absenteeism_indicator = {}
            federal_growth_main_container = {"display": "none"}
            federal_growth_empty_container = {"display": "block"}
    else:
        # this should only trigger if radio_value somehow gets broken

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

        k8_overall_indicators = {}
        hs_overall_indicators = {}
        combined_indicators = {}
        enrollment_indicators = {}
        subgroup_grades = {}
        k8_academic_achievement = {}
        hs_academic_achievement = {}
        k8_academic_progress = {}
        hs_academic_progress = {}
        closing_achievement_gap = {}
        graduation_rate_indicator = {}
        strength_of_diploma_indicator = {}
        ela_progress_indicator = {}
        absenteeism_indicator = {}
        federal_growth_main_container = {"display": "none"}
        federal_growth_empty_container = {"display": "none"}

        # proficiency
        hs_grad_overview_table = {}
        hs_grad_ethnicity_table = {}
        hs_grad_subgroup_table = {}
        sat_overview_table = {}
        sat_ethnicity_table = {}
        sat_subgroup_table = {}        
        hs_eca_table = {}
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

    # Add notes string based on school type
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
        hs_grad_ethnicity_table, hs_grad_subgroup_table, sat_overview_table, sat_ethnicity_table, sat_subgroup_table, hs_eca_table,
        hs_table_container, main_container, empty_container, no_data_to_display, k8_overall_indicators, hs_overall_indicators,
        combined_indicators, enrollment_indicators, subgroup_grades, k8_academic_achievement, hs_academic_achievement,
        k8_academic_progress, hs_academic_progress, closing_achievement_gap, graduation_rate_indicator, strength_of_diploma_indicator,
        ela_progress_indicator, absenteeism_indicator, table_grades_growth_ela_container, table_grades_growth_math_container,
        table_ethnicity_growth_ela_container, table_ethnicity_growth_math_container, table_subgroup_growth_ela_container, 
        table_subgroup_growth_math_container, fig_grade_growth_ela, fig_grade_sgp_ela, fig_grade_growth_math, fig_grade_sgp_math,
        fig_ethnicity_growth_ela, fig_ethnicity_sgp_ela, fig_ethnicity_growth_math, fig_ethnicity_sgp_math, fig_subgroup_growth_ela,
        fig_subgroup_sgp_ela, fig_subgroup_growth_math, fig_subgroup_sgp_math, federal_growth_main_container,
        federal_growth_empty_container, no_federal_growth_data_to_display, state_growth_main_container,
        state_growth_empty_container, no_state_growth_data_to_display, growth_values_table, growth_values_table_container,
        academic_information_notes_string
    )

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
            html.Div(
                [                     
                    html.Div(
                        [                             
                            html.Div(id="growth-values-table"),
                        ],
                        className = "bare_container_center twelve columns"
                    ),
                ],
                id="growth-values-table-container",
            ),
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
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-grade-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
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
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-ethnicity-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
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
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-subgroup-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
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
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-other-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                        ],
                        id="k8-table-container",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-grad-overview-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-grad-ethnicity-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-grad-subgroup-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="sat-overview-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="sat-ethnicity-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="sat-subgroup-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),                            
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-eca-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
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
            html.Div(
                [
                
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="k8-overall-indicators"),
                                ],
                                className="pretty_container five columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="hs-overall-indicators"),
                                ],
                                className="pretty_container five columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="combined-indicators"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="enrollment-indicators"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="subgroup-grades"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [                                  
                            html.Div(
                                [
                                    html.Div(id="k8-academic-achievement"),
                                ],
                                className="pretty_container six columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),                                      
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="hs-academic-achievement"),
                                ],
                                className="pretty_container six columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="k8-academic-progress"),
                                ],
                                className="pretty_container five columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [                                                                
                            html.Div(
                                [
                                    html.Div(id="hs-academic-progress"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [        
                            html.Div(
                                [
                                    html.Div(id="closing-achievement-gap"),
                                ],
                                className="pretty_container six columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="graduation-rate-indicator"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="strength-of-diploma-indicator"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="ela-progress-indicator"),
                                ],
                                className="pretty_container five columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="absenteeism-indicator"),
                                ],
                                className="pretty_container five columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                ],
                id = "federal-growth-main-container",
            ),
            html.Div(
                [
                    html.Div(id="federal-growth-no-data"),
                ],
                id = "federal-growth-empty-container",
            ),
        ],
        id="mainContainer",
    )