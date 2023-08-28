#########################################
# ICSB Dashboard - Academic Information #
#########################################
# author:   jbetley
# version:  1.09
# date:     08/14/23

import dash
from dash import dcc, html, Input, Output, callback, State, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import re

# import local functions
from .load_data import ethnicity, subgroup, subject, grades_all, grades_ordinal, get_k8_school_academic_data, \
    get_high_school_academic_data, get_demographic_data, get_school_index, get_growth_data
from .process_data import process_k8_academic_data, get_attendance_data, process_high_school_academic_data, \
    filter_high_school_academic_data, process_growth_data
from .table_helpers import no_data_page, no_data_table, create_academic_info_table, create_key_table, \
    create_growth_table, set_table_layout, create_basic_info_table, create_growth_table_and_fig, create_simple_academic_info_table, \
    create_line_fig_layout
from .chart_helpers import no_data_fig_label, make_stacked_bar, make_growth_chart, make_line_chart
from .calculations import round_percentages, conditional_fillna, get_excluded_years
from .subnav import subnav_academic

dash.register_page(__name__, top_nav=True, path="/academic_information", order=4)

# https://community.plotly.com/t/can-persistence-be-used-to-clear-cached-memory-from-previous-user-sessions/60370

# Sub sub navigation buttons
#   IF AHS or HS - No Type or Category Buttons displayed
#   If K8 - Radio Type Display & Basic Radio Category Display
#   If K12 - Radio Type Display With Additional -> Proficiency/Growth/High School

# Type - and display check
@callback(      
    Output("radio-type-input", "options"),
    Output("radio-type-input","value"),
    Output('radio-input-container', 'style'),
    Input("charter-dropdown", "value"),
    State("radio-type-input", "value"),
)
def radio_type_selector(school: str, radio_type_value: str):

    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]

    value_default = "proficiency"
    
    if school_type == "K8":
        options_default = [
            {"label": "Proficiency", "value": "proficiency"},
            {"label": "Growth", "value": "growth"},
        ]

    else:
        options_default = [
            {"label": "Proficiency", "value": "proficiency"},
            {"label": "Growth", "value": "growth"},
            {"label": "High School", "value": "highschool"}        
        ]

    type_options = options_default

    if radio_type_value:
        type_value = radio_type_value
    else:
        type_value = value_default

    if school_type == "HS" or school_type == "AHS":
        radio_input_container = {'display': 'none'}
    else:
        radio_input_container = {'display': 'block'}
            
    return type_options, type_value, radio_input_container

# Category
@callback(
    Output("radio-category-input", "options"),
    Output("radio-category-input","value"),
    Input("radio-type-input", "value"),
    State("radio-category-input", "options"),
    State("radio-category-input", "value")  
)
def radio_category_selector(radio_type: str, radio_category_options: list, radio_category_value: str):

    options_default = [
        {"label": "All Data", "value": "all"},
        {"label": "By Grade", "value": "grade"},
        {"label": "By Ethnicity", "value": "ethnicity"},
        {"label": "By Subgroup", "value": "subgroup"}
    ]
    value_default = "all"

    if not ctx.triggered:
        raise PreventUpdate()
    
    else:
        if ctx.triggered_id == 'radio-type-input':

            if radio_type == "growth" or radio_type == "proficiency":
                if radio_category_value:
                    category_value = radio_category_value
                else:
                    category_value = value_default

                if radio_category_options:
                    category_options = radio_category_options
                else:
                    category_options = options_default

            else:   # highschool
                category_value = ""
                category_options = []
    
    return category_options, category_value

# Main
@callback(
    Output("proficiency-grades-ela", "children"),
    Output("ela-grade-bar-fig", "children"),
    Output("proficiency-ela-grades-container", "style"),
    Output("proficiency-ethnicity-ela", "children"),
    Output("ela-ethnicity-bar-fig", "children"),
    Output("proficiency-ela-ethnicity-container", "style"),
    Output("proficiency-subgroup-ela", "children"),
    Output("ela-subgroup-bar-fig", "children"),
    Output("proficiency-ela-subgroup-container", "style"),
    Output("proficiency-grades-math", "children"),
    Output("math-grade-bar-fig", "children"),
    Output("proficiency-math-grades-container", "style"),
    Output("proficiency-ethnicity-math", "children"),
    Output("math-ethnicity-bar-fig", "children"),
    Output("proficiency-math-ethnicity-container", "style"),
    Output("proficiency-subgroup-math", "children"),
    Output("math-subgroup-bar-fig", "children"),
    Output("proficiency-math-subgroup-container", "style"),
    Output("attendance-table", "children"),
    Output("k8-table-container", "style"),
    Output("hs-grad-overview-table", "children"),
    Output("hs-grad-ethnicity-table", "children"),
    Output("hs-grad-subgroup-table", "children"),
    Output("grad-table-container", "style"),
    Output("sat-cut-scores-table", "children"),
    Output("sat-overview-table", "children"),
    Output("sat-ethnicity-table", "children"),
    Output("sat-subgroup-table", "children"),
    Output("sat-table-container", "style"),
    Output("academic-information-main-container", "style"),
    Output("academic-information-empty-container", "style"),
    Output("academic-information-no-data", "children"),
    Output("growth-grades-ela", "children"),
    Output("growth-grades-math", "children"),
    Output("growth-ethnicity-ela", "children"),
    Output("growth-ethnicity-math", "children"),
    Output("growth-subgroup-ela", "children"),
    Output("growth-subgroup-math", "children"),
    Output("academic-information-main-growth-container", "style"),
    Output("academic-information-empty-growth-container", "style"),
    Output("academic-information-no-growth-data", "children"),
    Output("academic-information-notes-string", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input(component_id="radio-type-input", component_property="value"),
    Input(component_id="radio-category-input", component_property="value"),  
)
def update_academic_information_page(school: str, year: str, radio_type: str, radio_category: str):
    if not school:
        raise PreventUpdate

    # show 2019 instead of 2020 as 2020 has no academic data
    string_year = year
    selected_year_string = "2019" if string_year == "2020" else string_year
    selected_year_numeric = int(selected_year_string)

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]
    selected_school_id = int(selected_school["School ID"].values[0])
    selected_school_name = selected_school["School Name"].values[0]

    excluded_years = get_excluded_years(selected_year_string)

    # Radio buttons don't play nice
    if not radio_type:
        radio_type = "proficiency"

    if not radio_category:
        radio_category = "all"

    # default styles (all values empty - only empty_container displayed)\
    growth_grades_ela = []
    growth_grades_math = []
    growth_ethnicity_ela = []
    growth_ethnicity_math = []
    growth_subgroup_ela = []
    growth_subgroup_math = []
    main_growth_container = {"display": "none"}
    empty_growth_container = {"display": "none"}

    # proficiency
    hs_grad_overview_table = []
    hs_grad_ethnicity_table = []
    hs_grad_subgroup_table = []
    sat_overview_table = []
    sat_ethnicity_table = []
    sat_subgroup_table = []
    sat_cut_scores_table = []
    sat_table_container = {"display": "none"}
    grad_table_container = {"display": "none"}

    proficiency_grades_ela = []
    ela_grade_bar_fig = []
    proficiency_ethnicity_ela = []
    ela_ethnicity_bar_fig = []
    proficiency_subgroup_ela = []
    ela_subgroup_bar_fig = []
    proficiency_grades_math = []
    math_grade_bar_fig = []
    proficiency_ethnicity_math = []
    math_ethnicity_bar_fig = []
    proficiency_subgroup_math = []
    math_subgroup_bar_fig = []
    proficiency_ela_grades_container = {"display": "none"}
    proficiency_ela_ethnicity_container = {"display": "none"}
    proficiency_ela_subgroup_container = {"display": "none"}
    proficiency_math_grades_container = {"display": "none"}
    proficiency_math_ethnicity_container = {"display": "none"}
    proficiency_math_subgroup_container = {"display": "none"}

    attendance_table = []
    k8_table_container = {"display": "none"}

    academic_information_notes_string = ""
    main_container = {"display": "none"}
    empty_container = {"display": "block"}

    no_display_data = no_data_page("Academic Proficiency")
    no_growth_data = no_data_page("Academic Growth")

    # NOTE: There is a special exception for Christel House South - prior to 2021,
    # CHS was a K12. From 2021 onwards, CHS is a K8, with the high school moving to
    # Christel House Watanabe Manual HS
    if (selected_school_type == "HS" or selected_school_type == "AHS" or selected_school_type == "K12"
        or (selected_school_id == 5874 and selected_year_numeric < 2021)):

        # load HS academic data
        selected_raw_hs_school_data = get_high_school_academic_data(school)

        # exclude years later than the selected year
        if excluded_years:
            selected_raw_hs_school_data = selected_raw_hs_school_data[~selected_raw_hs_school_data["Year"].isin(excluded_years)]

        if len(selected_raw_hs_school_data.index) > 0:

            selected_raw_hs_school_data = filter_high_school_academic_data(selected_raw_hs_school_data)

            all_hs_school_data = process_high_school_academic_data(selected_raw_hs_school_data, school)

            if not all_hs_school_data.empty:

                main_container = {"display": "block"}
                empty_container = {"display": "none"}

                # Graduation Rate Tables ("Strength of Diploma" in data, but not currently displayed)
                grad_overview_categories = ["Total", "Non Waiver", "State Average"]

                if selected_school_type == "AHS":
                    grad_overview_categories.append("CCR Percentage")

                all_hs_school_data.columns = all_hs_school_data.columns.astype(str)

                # Graduation Rate Tables
                graduation_data = all_hs_school_data[all_hs_school_data["Category"].str.contains("Graduation")].copy()

                if len(graduation_data.columns) > 1 and len (graduation_data.index) > 0:

                    grad_table_container = {"display": "block"}

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

                # SAT Benchmark Table
                sat_table_data = all_hs_school_data[all_hs_school_data["Category"].str.contains("Benchmark %")].copy()

                if len(sat_table_data.columns) > 1 and len (sat_table_data.index) > 0:

                    sat_table_container = {"display": "block"}

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

                    # SAT Cut-Score Table
                    # https://www.in.gov/sboe/files/2021-2022-SAT-Standard-Setting-SBOE-Review.pdf
                    sat_cut_scores_label = "SAT Proficiency Cut Scores (2021 - 22)"
                    sat_cut_scores_dict = {
                        "Content Area": ["Mathematics", "Evidenced-Based Reading and Writing"],
                        "Below College-Ready Benchmark": ["200 - 450", "200 - 440"],
                        "Approaching College-Ready Benchmark": ["460 - 520", "450 - 470"],
                        "At College-Ready Benchmark": ["530 - 800", "480 - 800"]
                    }

                    sat_cut_scores = pd.DataFrame(sat_cut_scores_dict)
                    sat_cut_scores_table = create_key_table(sat_cut_scores, sat_cut_scores_label)

    if (selected_school_type == "K8" or selected_school_type == "K12"):

        # If school is K12, we have already loaded HS data, so we just skip the K8 data
        if radio_type == "highschool":
            k8_table_container = {"display": "none"}

        # Proficiency Page
        elif radio_type == "proficiency":

            main_growth_container = {"display": "none"}
            empty_growth_container = {"display": "none"}
            sat_table_container = {"display": "none"}
            grad_table_container = {"display": "none"}

            selected_raw_k8_school_data = get_k8_school_academic_data(school)

            if excluded_years:
                selected_raw_k8_school_data = selected_raw_k8_school_data[~selected_raw_k8_school_data["Year"].isin(excluded_years)]

            if len(selected_raw_k8_school_data.index) > 0:

                all_k8_school_data = process_k8_academic_data(selected_raw_k8_school_data)

                if not all_k8_school_data.empty:

                    k8_table_container = {"display": "block"}
                    main_container = {"display": "block"}
                    empty_container = {"display": "none"}

                    all_k8_school_data = conditional_fillna(all_k8_school_data)

                    all_k8_school_data = (all_k8_school_data.set_index(["Category"]).add_suffix("School").reset_index())

                    all_k8_school_data.columns = all_k8_school_data.columns.str.replace(r"School$", "", regex=True)

                    all_k8_school_data["Category"] = (all_k8_school_data["Category"].str.replace(" Proficient %", "").str.strip())

                    all_k8_school_data.loc[all_k8_school_data["Category"] == "IREAD", "Category"] = "IREAD Proficiency (Grade 3)"

                    # Reformat data for multi-year line charts
                    year_over_year_data = all_k8_school_data.loc[:,~all_k8_school_data.columns.str.contains('N-Size')].copy()

                    year_over_year_data = year_over_year_data.set_index("Category")
                    year_over_year_data.columns = year_over_year_data.columns.str[:4]

                    year_over_year_data = year_over_year_data.reset_index()

                    year_over_year_data = year_over_year_data.set_index("Category").T.rename_axis("Year").rename_axis(None, axis=1).reset_index()
                    year_over_year_data["School Name"] = selected_school_name

                    year_over_year_data = year_over_year_data.rename(columns = {"Native Hawaiian or Other Pacific Islander|ELA Proficient %": "Pacific Islander|ELA Proficient %"})

                ## ELA
                    # by Grade Table
                    years_by_grade_ela = all_k8_school_data[ \
                        (all_k8_school_data["Category"].str.contains("|".join(grades_all)) & \
                            all_k8_school_data["Category"].str.contains("ELA")) | \
                        (all_k8_school_data["Category"] == "IREAD Proficiency (Grade 3)")]

                    ela_grade_table = create_simple_academic_info_table(years_by_grade_ela)

                    # by Grade Year over Year Line Chart
                    ela_grade_fig_data = year_over_year_data.filter(regex = r"^Grade \d\|ELA|IREAD|^School Name$|^Year$",axis=1)
                    ela_grade_line_fig = make_line_chart(ela_grade_fig_data)

                    proficiency_grades_ela = create_line_fig_layout(ela_grade_table, ela_grade_line_fig, "ELA By Grade")

                    # by Subgroup Table
                    years_by_subgroup_ela = all_k8_school_data[(all_k8_school_data["Category"].str.contains("|".join(subgroup)) & all_k8_school_data["Category"].str.contains("ELA"))]

                    ela_subgroup_table = create_simple_academic_info_table(years_by_subgroup_ela)

                    # get column lists for each subject/category combination
                    categories_ela_subgroup = []
                    categories_math_subgroup = []
                    for s in subgroup:
                        categories_ela_subgroup.append(s + "|" + "ELA")
                        categories_math_subgroup.append(s + "|" + "Math")

                    categories_ela_ethnicity = []
                    categories_math_ethnicity = []
                    for e in ethnicity:
                        categories_ela_ethnicity.append(e + "|" + "ELA")
                        categories_math_ethnicity.append(e + "|" + "Math")

                    # by Subgroup Year over Year Line Chart
                    ela_subgroup_fig_data = year_over_year_data.loc[:, (year_over_year_data.columns.isin(categories_ela_subgroup)) | \
                            (year_over_year_data.columns.isin(["School Name","Year"]))]
                    ela_subgroup_line_fig = make_line_chart(ela_subgroup_fig_data)

                    proficiency_subgroup_ela = create_line_fig_layout(ela_subgroup_table, ela_subgroup_line_fig, "ELA By Subgroup")

                    # by Ethnicity
                    years_by_ethnicity_ela = all_k8_school_data[(all_k8_school_data["Category"].str.contains("|".join(ethnicity)) & all_k8_school_data["Category"].str.contains("ELA"))]

                    ela_ethnicity_table = create_simple_academic_info_table(years_by_ethnicity_ela)

                    # by Ethnicity Year over Year Line Chart
                    ela_ethnicity_fig_data = year_over_year_data.loc[:, (year_over_year_data.columns.isin(categories_ela_ethnicity)) | \
                            (year_over_year_data.columns.isin(["School Name","Year"]))]
                    ela_ethnicity_line_fig = make_line_chart(ela_ethnicity_fig_data)

                    proficiency_ethnicity_ela = create_line_fig_layout(ela_ethnicity_table, ela_ethnicity_line_fig, "ELA By Ethnicity")

               ## Math

                    # by Grade Table
                    years_by_grade_math = all_k8_school_data[(all_k8_school_data["Category"].str.contains("|".join(grades_all)) & all_k8_school_data["Category"].str.contains("Math"))]

                    math_grade_table = create_simple_academic_info_table(years_by_grade_math)

                    # by Grade Year over Year Line Chart
                    math_grade_fig_data = year_over_year_data.filter(regex = r"^Grade \d\|Math|^School Name$|^Year$",axis=1)
                    math_grade_line_fig = make_line_chart(math_grade_fig_data)

                    proficiency_grades_math = create_line_fig_layout(math_grade_table, math_grade_line_fig, "Math By Grade")

                    # by Subgroup Table
                    years_by_subgroup_math = all_k8_school_data[(all_k8_school_data["Category"].str.contains("|".join(subgroup)) & all_k8_school_data["Category"].str.contains("Math"))]

                    math_subgroup_table = create_simple_academic_info_table(years_by_subgroup_math)

                    # by Subgroup Year over Year Line Chart
                    math_subgroup_fig_data = year_over_year_data.loc[:, (year_over_year_data.columns.isin(categories_math_subgroup)) | \
                            (year_over_year_data.columns.isin(["School Name","Year"]))]
                    math_subgroup_line_fig = make_line_chart(math_subgroup_fig_data)

                    proficiency_subgroup_math = create_line_fig_layout(math_subgroup_table, math_subgroup_line_fig, "Math By Subgroup")

                    # by Ethnicity
                    years_by_ethnicity_math = all_k8_school_data[(all_k8_school_data["Category"].str.contains("|".join(ethnicity)) & all_k8_school_data["Category"].str.contains("Math"))]

                    math_ethnicity_table = create_simple_academic_info_table(years_by_ethnicity_math)

                    # by Ethnicity Year over Year Line Chart
                    math_ethnicity_fig_data = year_over_year_data.loc[:, (year_over_year_data.columns.isin(categories_math_ethnicity)) | \
                            (year_over_year_data.columns.isin(["School Name","Year"]))]
                    math_ethnicity_line_fig = make_line_chart(math_ethnicity_fig_data)

                    proficiency_ethnicity_math = create_line_fig_layout(math_ethnicity_table, math_ethnicity_line_fig, "Math By Ethnicity")

                    # Attendance rate
                    school_demographic_data = get_demographic_data(school)

                    attendance_rate = get_attendance_data(school_demographic_data, selected_year_string)

                    if len(attendance_rate.index) > 0:
                        attendance_table = create_basic_info_table(attendance_rate,"Attendance Data")
                    else:
                        attendance_table = no_data_table(["Attendance Data"])

                    attendance_table = set_table_layout(attendance_table, attendance_table, attendance_rate.columns)

                ## Proficiency breakdown data for stacked bar charts
                    # NOTE: IDOE's raw proficency data is annoyingly inconsistent. In some cases missing
                    # data is blank and in other cases it is represented by "0." So we need to be extra
                    # careful in interpreting what is missing from what is just inconsistenly recorded

                    all_proficiency_data = selected_raw_k8_school_data.loc[selected_raw_k8_school_data["Year"] == selected_year_numeric].copy()

                    all_proficiency_data = all_proficiency_data.dropna(axis=1)
                    all_proficiency_data = all_proficiency_data.reset_index()

                    for col in all_proficiency_data.columns:
                        all_proficiency_data[col] = pd.to_numeric(all_proficiency_data[col], errors="coerce")

                    # this keeps ELA and Math as well, which we drop later
                    all_proficiency_data = all_proficiency_data.filter(
                        regex=r"ELA Below|ELA At|ELA Approaching|ELA Above|ELA Total|Math Below|Math At|Math Approaching|Math Above|Math Total",
                        axis=1,
                    )

                    proficiency_rating = ["Below Proficiency", "Approaching Proficiency", "At Proficiency", "Above Proficiency"]

                    # create dataframe to hold annotations (categories & missing data)
                    # NOTE: Annotations are currently not used
                    annotations = pd.DataFrame(columns= ["Category","Total Tested","Status"])

                    # NOTE: This may seem kludgy, but runs consistently around .15s
                    # for each category, create a proficiency_columns list of columns using the strings in
                    # "proficiency_rating" and then divide each column by "Total Test
                    categories = grades_all + ethnicity + subgroup

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

                    bar_fig_title = "Proficiency Breakdown (" + selected_year_string + ")"

                    # ELA by Grade - Current Year
                    grade_annotations = annotations.loc[annotations["Category"].str.contains("Grade")]

                    grade_ela_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(grades_ordinal)
                        & all_proficiency_data["Proficiency"].str.contains("ELA")
                    ]

                    if not grade_ela_fig_data.empty:
                        ela_grade_bar_fig = make_stacked_bar(grade_ela_fig_data, bar_fig_title)
                    else:
                        ela_grade_bar_fig = no_data_fig_label(bar_fig_title, 100)

                    # Math by Grade - Current Year
                    grade_math_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(grades_ordinal)
                        & all_proficiency_data["Proficiency"].str.contains("Math")
                    ]

                    if not grade_math_fig_data.empty:
                        math_grade_bar_fig = make_stacked_bar(grade_math_fig_data, bar_fig_title)
                    else:
                        math_grade_bar_fig = no_data_fig_label(bar_fig_title, 100)

                    # ELA by Ethnicity - Current Year
                    ethnicity_annotations = annotations.loc[annotations["Category"].str.contains("Ethnicity")]

                    ethnicity_ela_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(ethnicity)
                        & all_proficiency_data["Proficiency"].str.contains("ELA")
                    ]

                    if not ethnicity_ela_fig_data.empty:
                        ela_ethnicity_bar_fig = make_stacked_bar(ethnicity_ela_fig_data, bar_fig_title)
                    else:
                        ela_ethnicity_bar_fig = no_data_fig_label(bar_fig_title, 100)

                    # Math by Ethnicity - Current Year
                    ethnicity_math_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(ethnicity)
                        & all_proficiency_data["Proficiency"].str.contains("Math")
                    ]

                    if not ethnicity_math_fig_data.empty:
                        math_ethnicity_bar_fig = make_stacked_bar(ethnicity_math_fig_data, bar_fig_title)
                    else:
                        math_ethnicity_bar_fig = no_data_fig_label(bar_fig_title, 100)

                    # ELA by Subgroup - Current Year
                    subgroup_annotations = annotations.loc[annotations["Category"].str.contains("Subgroup")]

                    subgroup_ela_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(subgroup)
                        & all_proficiency_data["Proficiency"].str.contains("ELA")
                    ]

                    if not subgroup_ela_fig_data.empty:
                        ela_subgroup_bar_fig = make_stacked_bar(subgroup_ela_fig_data, bar_fig_title)
                    else:
                        ela_subgroup_bar_fig = no_data_fig_label(bar_fig_title, 100)

                    # Math by Subgroup - Current Year
                    subgroup_math_fig_data = all_proficiency_data[
                        all_proficiency_data["Category"].isin(subgroup)
                        & all_proficiency_data["Proficiency"].str.contains("Math")
                    ]

                    if not subgroup_math_fig_data.empty:
                        math_subgroup_bar_fig = make_stacked_bar(subgroup_math_fig_data, bar_fig_title)
                    else:
                        math_subgroup_bar_fig = no_data_fig_label(bar_fig_title, 100)

# Maybe Maybe Maybe
            # if radio_category == "total":
            #     proficiency_ela_grades_container = {"display": "block"}
            #     proficiency_math_grades_container = {"display": "block"}
            #     proficiency_ethnicity_math = []
            #     math_ethnicity_bar_fig = []
            #     proficiency_subgroup_math = []
            #     math_subgroup_bar_fig = []
            #     proficiency_ethnicity_ela = []
            #     ela_ethnicity_bar_fig = []
            #     proficiency_subgroup_ela = []
            #     ela_subgroup_bar_fig = []

            if radio_category == "grade":
                proficiency_ela_grades_container = {"display": "block"}
                proficiency_math_grades_container = {"display": "block"}
                proficiency_ethnicity_math = []
                math_ethnicity_bar_fig = []
                proficiency_subgroup_math = []
                math_subgroup_bar_fig = []
                proficiency_ethnicity_ela = []
                ela_ethnicity_bar_fig = []
                proficiency_subgroup_ela = []
                ela_subgroup_bar_fig = []
            elif radio_category == "ethnicity":
                proficiency_ela_ethnicity_container = {"display": "block"}
                proficiency_math_ethnicity_container = {"display": "block"}
                proficiency_grades_ela = []
                ela_grade_bar_fig = []
                proficiency_subgroup_ela = []
                ela_subgroup_bar_fig = []
                proficiency_grades_math = []
                math_grade_bar_fig = []
                proficiency_subgroup_math = []
                math_subgroup_bar_fig = []
            elif radio_category == "subgroup":
                proficiency_ela_subgroup_container = {"display": "block"}
                proficiency_math_subgroup_container = {"display": "block"}
                proficiency_grades_ela = []
                ela_grade_bar_fig = []
                proficiency_ethnicity_ela = []
                ela_ethnicity_bar_fig = []
                proficiency_grades_math = []
                math_grade_bar_fig = []
                proficiency_ethnicity_math = []
                math_ethnicity_bar_fig = []
            elif radio_category == "all":
                proficiency_ela_grades_container = {"display": "block"}
                proficiency_math_grades_container = {"display": "block"}
                proficiency_ela_ethnicity_container = {"display": "block"}
                proficiency_math_ethnicity_container = {"display": "block"}
                proficiency_ela_subgroup_container = {"display": "block"}
                proficiency_math_subgroup_container = {"display": "block"}
            else:
                proficiency_grades_ela = []
                ela_grade_bar_fig = []
                proficiency_ethnicity_ela = []
                ela_ethnicity_bar_fig = []
                proficiency_subgroup_ela = []
                ela_subgroup_bar_fig = []
                proficiency_grades_math = []
                math_grade_bar_fig = []
                proficiency_ethnicity_math = []
                math_ethnicity_bar_fig = []
                proficiency_subgroup_math = []
                math_subgroup_bar_fig = []

        elif radio_type == "growth":

            main_container = {"display": "none"}

            # State Growth Data
            # NOTE: "162-Days" means a student was enrolled at the school where they were assigned for at least
            # 162 days. "Majority Enrolled" is misleading. It actually means "Greatest Number of Days." So the actual
            # number of days could be less than half of the year (82) if, for example, a student transferred a few
            # times, or was out of the system for most of the year. "Tested School" is where the student actually took
            # the test. IDOE uses "Majority Enrolled" for their calculations. So we do the same here.

            # ICSB growth metrics need to be updated, currently say:
            #   Percentage of students achieving “typical” or “high” growth on the state assessment in ELA/Math
            #   Median SGP of students achieving "adequate and sufficient growth" on the state assessment in ELA/Math

            # NOTE: Growth data shows: byGrade, byEthnicity, bySES, byEL Status, & by Sped Status
            # Also available in the data, but not currently shown: Homeless Status and High Ability Status

            # all students who are coded as "Majority Enrolled" at the school
            growth_data = get_growth_data(school)

            if excluded_years:
                growth_data = growth_data[~growth_data["Test Year"].isin(excluded_years)]

            if len(growth_data.index) > 0:

                main_growth_container = {"display": "block"}

                empty_growth_container = {"display": "none"}
                empty_container = {"display": "none"}

                # Percentage of students achieving "Adequate Growth"
                fig_data_grades_growth, table_data_grades_growth = process_growth_data(growth_data,"Grade Level")
                fig_data_ethnicity_growth, table_data_ethnicity_growth = process_growth_data(growth_data,"Ethnicity")
                fig_data_ses_growth, table_data_ses_growth = process_growth_data(growth_data,"Socioeconomic Status")
                fig_data_el_growth, table_data_el_growth = process_growth_data(growth_data,"English Learner Status")
                fig_data_sped_growth, table_data_sped_growth = process_growth_data(growth_data,"Special Education Status")

                # combine subgroups
                table_data_subgroup_growth = pd.concat([table_data_ses_growth, table_data_el_growth, table_data_sped_growth])
                fig_data_subgroup_growth = pd.concat([fig_data_ses_growth, fig_data_el_growth, fig_data_sped_growth], axis=1)

            ## By grade

                # grades growth ela table/fig #1
                table_data_grades_growth_ela = table_data_grades_growth[(table_data_grades_growth["Category"].str.contains("ELA"))]
                growth_data_162_grades_ela = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains("162")) & (fig_data_grades_growth.columns.str.contains("ELA"))]
                growth_data_162_grades_ela.columns = growth_data_162_grades_ela.columns.str.split("_").str[1]
                growth_data_me_grades_ela = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains("Majority Enrolled")) & (fig_data_grades_growth.columns.str.contains("ELA"))]
                growth_data_me_grades_ela.columns = growth_data_me_grades_ela.columns.str.split("_").str[1]

                label_grades_growth_ela="Percentage of Students with Adequate Growth - by Grade (ELA)"
                table_grades_growth_ela = create_growth_table(table_data_grades_growth_ela,label_grades_growth_ela)
                fig_grades_growth_ela = make_growth_chart(growth_data_me_grades_ela, growth_data_162_grades_ela, label_grades_growth_ela)

                growth_grades_ela = create_growth_table_and_fig(table_grades_growth_ela, fig_grades_growth_ela, label_grades_growth_ela)

                # grades growth math table/fig #3
                table_data_grades_growth_math= table_data_grades_growth[(table_data_grades_growth["Category"].str.contains("Math"))]
                growth_data_162_grades_math = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains("162")) & (fig_data_grades_growth.columns.str.contains("Math"))]
                growth_data_me_grades_math = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains("Majority Enrolled")) & (fig_data_grades_growth.columns.str.contains("Math"))]
                growth_data_162_grades_math.columns = growth_data_162_grades_math.columns.str.split("_").str[1]
                growth_data_me_grades_math.columns = growth_data_me_grades_math.columns.str.split("_").str[1]

                label_grades_growth_math = "Percentage of Students with Adequate Growth - by Grade (Math)"
                table_grades_growth_math = create_growth_table(table_data_grades_growth_math, label_grades_growth_math)
                fig_grades_growth_math = make_growth_chart(growth_data_me_grades_math, growth_data_162_grades_math, label_grades_growth_math)

                growth_grades_math = create_growth_table_and_fig(table_grades_growth_math, fig_grades_growth_math, label_grades_growth_math)

            ## By ethnicity

                # ethnicity growth ela table/fig #5
                table_data_ethnicity_growth_ela = table_data_ethnicity_growth[(table_data_ethnicity_growth["Category"].str.contains("ELA"))]
                growth_data_162_ethnicity_ela = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains("162")) & (fig_data_ethnicity_growth.columns.str.contains("ELA"))]
                growth_data_162_ethnicity_ela.columns = growth_data_162_ethnicity_ela.columns.str.split("_").str[1]
                growth_data_me_ethnicity_ela = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains("Majority Enrolled")) & (fig_data_ethnicity_growth.columns.str.contains("ELA"))]
                growth_data_me_ethnicity_ela.columns = growth_data_me_ethnicity_ela.columns.str.split("_").str[1]

                label_ethnicity_growth_ela = "Percentage of Students with Adequate Growth - by Ethnicity (ELA)"
                table_ethnicity_growth_ela = create_growth_table(table_data_ethnicity_growth_ela, label_ethnicity_growth_ela)
                fig_ethnicity_growth_ela = make_growth_chart(growth_data_me_ethnicity_ela, growth_data_162_ethnicity_ela, label_ethnicity_growth_ela)

                growth_ethnicity_ela = create_growth_table_and_fig(table_ethnicity_growth_ela, fig_ethnicity_growth_ela, label_ethnicity_growth_ela)

                # ethnicity growth math table/fig #7
                table_data_ethnicity_growth_math = table_data_ethnicity_growth[(table_data_ethnicity_growth["Category"].str.contains("Math"))]
                growth_data_162_ethnicity_math = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains("162")) & (fig_data_ethnicity_growth.columns.str.contains("Math"))]
                growth_data_162_ethnicity_math.columns = growth_data_162_ethnicity_math.columns.str.split("_").str[1]
                growth_data_me_ethnicity_math = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains("Majority Enrolled")) & (fig_data_ethnicity_growth.columns.str.contains("Math"))]
                growth_data_me_ethnicity_math.columns = growth_data_me_ethnicity_math.columns.str.split("_").str[1]

                label_ethnicity_growth_math = "Percentage of Students with Adequate Growth - by Ethnicity (Math)"
                table_ethnicity_growth_math = create_growth_table(table_data_ethnicity_growth_math, label_ethnicity_growth_math)
                fig_ethnicity_growth_math = make_growth_chart(growth_data_me_ethnicity_math, growth_data_162_ethnicity_math, label_ethnicity_growth_math)

                growth_ethnicity_math = create_growth_table_and_fig(table_ethnicity_growth_math, fig_ethnicity_growth_math, label_ethnicity_growth_math)

            ## By subgroup

                # subgroup growth ela table/fig #9
                table_data_subgroup_growth_ela = table_data_subgroup_growth[(table_data_subgroup_growth["Category"].str.contains("ELA"))]
                growth_data_162_subgroup_ela = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains("162")) & (fig_data_subgroup_growth.columns.str.contains("ELA"))]
                growth_data_162_subgroup_ela.columns = growth_data_162_subgroup_ela.columns.str.split("_").str[1]
                growth_data_me_subgroup_ela = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains("Majority Enrolled")) & (fig_data_subgroup_growth.columns.str.contains("ELA"))]
                growth_data_me_subgroup_ela.columns = growth_data_me_subgroup_ela.columns.str.split("_").str[1]

                label_subgroup_growth_ela = "Percentage of Students with Adequate Growth - by Subgroup (ELA)"
                table_subgroup_growth_ela = create_growth_table(table_data_subgroup_growth_ela, label_subgroup_growth_ela)
                fig_subgroup_growth_ela = make_growth_chart(growth_data_me_subgroup_ela, growth_data_162_subgroup_ela, label_subgroup_growth_ela)

                growth_subgroup_ela = create_growth_table_and_fig(table_subgroup_growth_ela, fig_subgroup_growth_ela, label_subgroup_growth_ela)

                # subgroup growth math table/fig #11
                table_data_subgroup_growth_math= table_data_subgroup_growth[(table_data_subgroup_growth["Category"].str.contains("Math"))]
                growth_data_162_subgroup_math = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains("162")) & (fig_data_subgroup_growth.columns.str.contains("Math"))]
                growth_data_162_subgroup_math.columns = growth_data_162_subgroup_math.columns.str.split("_").str[1]
                growth_data_me_subgroup_math = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains("Majority Enrolled")) & (fig_data_subgroup_growth.columns.str.contains("Math"))]
                growth_data_me_subgroup_math.columns = growth_data_me_subgroup_math.columns.str.split("_").str[1]

                label_subgroup_growth_math = "Percentage of Students with Adequate Growth - by Subgroup (Math)"
                table_subgroup_growth_math = create_growth_table(table_data_subgroup_growth_math, label_subgroup_growth_math)
                fig_subgroup_growth_math = make_growth_chart(growth_data_me_subgroup_math, growth_data_162_subgroup_math, label_subgroup_growth_math)

                growth_subgroup_math = create_growth_table_and_fig(table_subgroup_growth_math, fig_subgroup_growth_math, label_subgroup_growth_math)

                if radio_category == "grade":
                    growth_ethnicity_ela = []
                    growth_ethnicity_math = []
                    growth_subgroup_ela = []
                    growth_subgroup_math = []
                elif radio_category == "ethnicity":
                    growth_grades_ela = []
                    growth_grades_math = []
                    growth_subgroup_ela = []
                    growth_subgroup_math = []
                elif radio_category == "subgroup":
                    growth_grades_ela = []
                    growth_grades_math = []
                    growth_ethnicity_ela = []
                    growth_ethnicity_math = []
                elif radio_category == "all":
                    pass
                else:
                    growth_grades_ela = []
                    growth_grades_math = []
                    growth_ethnicity_ela = []
                    growth_ethnicity_math = []
                    growth_subgroup_ela = []
                    growth_subgroup_math = []

    if radio_type == "proficiency":
        academic_information_notes_string = "There are a number of factors that make it difficult to make \
            valid and reliable comparisons between test scores from 2019 to 2022. For example, ILEARN was \
            administered for the first time during the 2018-19 SY and represented an entirely new type and \
            mode of assessment (adaptive and online-only). No State assessment was administered in 2020 because \
            of the Covid-19 pandemic. Finally, the 2019 data set includes only students  who attended the \
            testing school for 162 days, while the 2021 and 2022 data sets included all tested students."

    if radio_type == "growth":
        academic_information_notes_string = "State growth data comes from IDOE's LINK. Identifying information \
            is scrubbed and data is aggregated before display. The calculation includes all students who were \
            enrolled in the selected school for the most number of days that student was enrolled in any school \
            over the entire school year (Majority Enrolled). This does not necessarily mean that the student was \
            enrolled in the school for an actual majority of the year (e.g., 82 days). This calculation thus includes \
            more students than previous year calculations which only included students who were enrolled in the \
            school for 162 Days. The 162 Day value is included in the tooltip of each table and chart for comparison purposes."

    ahs_notes = "Adult High Schools enroll students who are over the age of 18, under credited, \
                dropped out of high school for a variety of reasons, and are typically out of cohort from \
                their original graduation year. Because graduation rate is calculated at the end of the school \
                year regardless of the length of time a student is enrolled at a school, it is not comparable to \
                the graduation rate of a traditional high school."

    hs_notes = "Beginning with the 2021-22 SY, SAT replaced ISTEP+ as the state mandated HS assessment. \
                Beginning with the 2023 cohort all students in grade 11 will be required to take the assessment.\
                Data Source: Indiana Department of Education Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)."

    if radio_type == "highschool":
        if selected_school_type == "AHS":
            academic_information_notes_string = ahs_notes + " " + hs_notes
        else:
            academic_information_notes_string = hs_notes

    return (
        proficiency_grades_ela, ela_grade_bar_fig, proficiency_ela_grades_container,
        proficiency_ethnicity_ela, ela_ethnicity_bar_fig, proficiency_ela_ethnicity_container,
        proficiency_subgroup_ela, ela_subgroup_bar_fig, proficiency_ela_subgroup_container,
        proficiency_grades_math, math_grade_bar_fig, proficiency_math_grades_container,
        proficiency_ethnicity_math, math_ethnicity_bar_fig, proficiency_math_ethnicity_container,
        proficiency_subgroup_math, math_subgroup_bar_fig, proficiency_math_subgroup_container,
        attendance_table, k8_table_container,
        hs_grad_overview_table, hs_grad_ethnicity_table, hs_grad_subgroup_table, grad_table_container,
        sat_cut_scores_table, sat_overview_table, sat_ethnicity_table, sat_subgroup_table, sat_table_container,
        main_container, empty_container, no_display_data,
        growth_grades_ela, growth_grades_math, growth_ethnicity_ela, growth_ethnicity_math,
        growth_subgroup_ela, growth_subgroup_math, main_growth_container, empty_growth_container,
        no_growth_data, academic_information_notes_string
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
            html.Hr(),
            html.Div(
                [            
                    html.Div(
                        [
                            html.Div(
                                [
                                    dbc.RadioItems(
                                        id="radio-type-input",
                                        className="btn-group",
                                        inputClassName="btn-check",
                                        labelClassName="btn btn-outline-primary",
                                        labelCheckedClassName="active",
                                        value=[],
                                        persistence=False,
                                        # persistence_type="memory",
                                    ),
                                ],
                                className="radio-group-academic",
                            )
                        ],
                        className = "bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    dbc.RadioItems(
                                        id="radio-category-input",
                                        className="btn-group",
                                        inputClassName="btn-check",
                                        labelClassName="btn btn-outline-primary",
                                        labelCheckedClassName="active",
                                        value=[],
                                        persistence=False,
                                        # persistence_type="memory",
                                    ),
                                ],
                                className="radio-group-academic",
                            )
                        ],
                        className = "bare_container_center twelve columns",
                    ),
                ],
                id = "radio-input-container",
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
                                            html.Div(id="proficiency-grades-ela", children=[]),
                                            html.Div(
                                                [
                                                    html.Div(
                                                                [
                                                                    html.Div(id="ela-grade-bar-fig"),
                                                                ],
                                                                className="pretty_close_top_container six columns",
                                                    ),
                                                ],
                                                className="bare_container_center twelve columns",
                                            ),
                                        ],
                                        id="proficiency-ela-grades-container",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="proficiency-ethnicity-ela", children=[]),
                                            html.Div(
                                                [
                                                    html.Div(
                                                                [
                                                                    html.Div(id="ela-ethnicity-bar-fig"),
                                                                ],
                                                                className="pretty_close_top_container six columns",
                                                    ),
                                                ],
                                                className="bare_container_center twelve columns",
                                            ),
                                        ],
                                        id="proficiency-ela-ethnicity-container",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="proficiency-subgroup-ela", children=[]),
                                            html.Div(
                                                [
                                                    html.Div(
                                                                [
                                                                    html.Div(id="ela-subgroup-bar-fig"),
                                                                ],
                                                                className="pretty_close_top_container six columns",
                                                    ),
                                                ],
                                                className="bare_container_center twelve columns",
                                            ),
                                        ],
                                        id="proficiency-ela-subgroup-container",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="proficiency-grades-math", children=[]),
                                            html.Div(
                                                [
                                                    html.Div(
                                                                [
                                                                    html.Div(id="math-grade-bar-fig"),
                                                                ],
                                                                className="pretty_close_top_container six columns",
                                                    ),
                                                ],
                                                className="bare_container_center twelve columns",
                                            ),
                                        ],
                                        id="proficiency-math-grades-container",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="proficiency-ethnicity-math", children=[]),
                                            html.Div(
                                                [
                                                    html.Div(
                                                                [
                                                                    html.Div(id="math-ethnicity-bar-fig"),
                                                                ],
                                                                className="pretty_close_top_container six columns",
                                                    ),
                                                ],
                                                className="bare_container_center twelve columns",
                                            ),
                                        ],
                                        id="proficiency-math-ethnicity-container",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="proficiency-subgroup-math", children=[]),
                                            html.Div(
                                                [
                                                    html.Div(
                                                                [
                                                                    html.Div(id="math-subgroup-bar-fig"),
                                                                ],
                                                                className="pretty_close_top_container six columns",
                                                    ),
                                                ],
                                                className="bare_container_center twelve columns",
                                            ),
                                        ],
                                        id="proficiency-math-subgroup-container",
                                    ),
                                        html.Div(id="attendance-table", children=[]),
                                    ],
                                    id="k8-table-container",
                                ),
                                html.Div(
                                    [
                                html.Div(
                                    [                                        
                                        html.Label("Graduation Rate", className="header_label", style = {"marginTop": "5px"}),
                                    ],
                                    className="bare_container_center twelve columns",                                    
                                ),
                                        html.Div(id="hs-grad-overview-table"),
                                        html.Div(id="hs-grad-ethnicity-table"),
                                        html.Div(id="hs-grad-subgroup-table"),
                                    ],
                                    id="grad-table-container",
                                ),
                                html.Div(
                                    [                                
                                html.Div(
                                    [
                                        html.Label("SAT", className="header_label", style = {'marginTop': "20px"}),
                                   ],
                                    className="bare_container_center twelve columns",                                    
                                ),                                        
                                        html.Div(id="sat-cut-scores-table", children=[]),
                                        html.Div(id="sat-overview-table"),
                                        html.Div(id="sat-ethnicity-table"),
                                        html.Div(id="sat-subgroup-table"),
                                    ],
                                    id="sat-table-container",
                                ),
                            ],
                            id = "academic-information-main-container",
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            [
                html.Div(id="academic-information-no-data"),
            ],
            id = "academic-information-empty-container",
        ),
        html.Div(
            [
                html.Div(id="growth-grades-ela", children=[]),
                html.Div(id="growth-grades-math", children=[]),

                html.Div(id="growth-ethnicity-ela", children=[]),
                html.Div(id="growth-ethnicity-math", children=[]),

                html.Div(id="growth-subgroup-ela", children=[]),
                html.Div(id="growth-subgroup-math", children=[]),
            ],
            id = "academic-information-main-growth-container",
        ),
        html.Div(
            [
                html.Div(id="academic-information-no-growth-data"),
            ],
            id = "academic-information-empty-growth-container",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Notes:", className="key_header_label"),
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
                    className = "pretty_key_container ten columns"
                ),
            ],
            className = "bare_container_center twelve columns"
        ),
    ],
    id="mainContainer",
)