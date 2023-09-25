#######################################################
# ICSB Dashboard - Academic Information - Proficiency #
#######################################################
# author:   jbetley (james@jamesbetley.com)
# version:  1.11
# date:     10/03/23

import dash
from dash import dcc, html, Input, Output, callback, State
from dash.exceptions import PreventUpdate
import numpy as np
import pandas as pd
import re

# import local functions
from pages.load_data import ethnicity, subgroup, subject, grades_all, grades_ordinal, get_k8_school_academic_data, \
    get_high_school_academic_data, get_demographic_data, get_school_index, get_excluded_years
from pages.process_data import process_k8_academic_data, get_attendance_data, process_high_school_academic_data, \
    filter_high_school_academic_data
from pages.tables import no_data_page, no_data_table, create_multi_header_table_with_container, create_key_table, \
    create_single_header_table, create_multi_header_table
from pages.charts import no_data_fig_label, make_stacked_bar, make_line_chart
from pages.layouts import set_table_layout, create_line_fig_layout, create_radio_layout
from pages.calculations import round_percentages, conditional_fillna

from pages.subnav import subnav_academic_information

dash.register_page(__name__, top_nav=False,  order=7)

# Proficiency School Type (applies only to K12 schools)
@callback(      
    Output("academic-proficiency-type-radio", "options"),
    Output("academic-proficiency-type-radio","value"),
    Output('academic-proficiency-type-radio-container', 'style'),
    Output("hidden-proficiency", "children"),
    Input("current-proficiency-page", "href"),
    Input("charter-dropdown", "value"),
    Input("academic-proficiency-type-radio", "value"),
    State("academic-proficiency-type-radio", "value"),
)
def radio_type_selector(current_page: str, school: str, radio_type_value: str, radio_type_state: str):

    current_page = current_page.rsplit("/", 1)[-1]

    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]

    if school_type == "K12" and current_page == "proficiency":
        radio_input_container = {'display': 'block'}

        type_options = [
            {"label": "K-8", "value": "k8"},
            {"label": "High School", "value": "hs"}        
        ]

        # could check values against dictionary, but its far simpler to use a static list
        # if any(d['label'] == 'k8' or d['label'] == 'hs' for d in a):
        if radio_type_state in ["k8","hs"]:
            type_value = radio_type_state
        else:
            type_value = "k8"

    else:

        radio_input_container = {'display': 'none'}
        type_options = []
        type_value = ""

    return type_options, type_value, radio_input_container, current_page

# Proficiency Category
@callback(
    Output("academic-proficiency-category-radio", "options"),
    Output("academic-proficiency-category-radio","value"),
    Output("academic-proficiency-category-radio-container","style"),
    Input("charter-dropdown", "value"),
    Input("academic-proficiency-type-radio", "value"),
    State("academic-proficiency-category-radio", "options"),
    State("academic-proficiency-category-radio", "value")  
)
def radio_category_selector(school: str, radio_type: str, radio_category_options: list, radio_category_value: str):

    options_default = [
        {"label": "All Data", "value": "all"},
        {"label": "By Grade", "value": "grade"},
        {"label": "By Ethnicity", "value": "ethnicity"},
        {"label": "By Subgroup", "value": "subgroup"}
    ]
    
    value_default = "all"

    if radio_type == "hs":
        category_value = ""
        category_options = []
        category_container = {"display": "none"}
    
    else:                
        if radio_category_value: 
            category_value = radio_category_value
        else:
            category_value = value_default

        if radio_category_options:
            category_options = radio_category_options
        else:
            category_options = options_default

        category_container = {"display": "block"}

    return category_options, category_value, category_container

# Main
@callback(
    Output('redirect-proficiency-content', 'href'),
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
    Output("k12-grad-overview-table", "children"),
    Output("k12-grad-ethnicity-table", "children"),
    Output("k12-grad-subgroup-table", "children"),
    Output("k12-grad-table-container", "style"),
    Output("k12-sat-cut-scores-table", "children"),
    Output("k12-sat-overview-table", "children"),
    Output("k12-sat-ethnicity-table", "children"),
    Output("k12-sat-subgroup-table", "children"),
    Output("k12-sat-table-container", "style"),
    Output("academic-proficiency-main-container", "style"),
    Output("academic-proficiency-empty-container", "style"),
    Output("academic-proficiency-no-data", "children"),
    Output("academic-proficiency-notes-string", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input(component_id="academic-proficiency-type-radio", component_property="value"),
    Input(component_id="academic-proficiency-category-radio", component_property="value"),
)
def update_academic_proficiency_page(school: str, year: str, radio_type: str, radio_category: str):
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

    if not radio_type:
        radio_type = "k8"

    if not radio_category:
        radio_category = "all"

    # default styles (all values empty - only empty_container displayed)\
    k12_grad_overview_table = []
    k12_grad_ethnicity_table = []
    k12_grad_subgroup_table = []
    k12_sat_overview_table = []
    k12_sat_ethnicity_table = []
    k12_sat_subgroup_table = []
    k12_sat_cut_scores_table = []
    k12_sat_table_container = {"display": "none"}
    k12_grad_table_container = {"display": "none"}

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

    academic_proficiency_notes_string = ""
    main_container = {"display": "none"}
    empty_container = {"display": "block"}

    no_display_data = no_data_page("Academic Proficiency")

    # HS and AHS do not have proficiency data

    if selected_school_type == "HS" or selected_school_type == "AHS" or \
            (selected_school_id == 5874 and selected_year_numeric < 2021):
        
        location = "/academic_information"

    else:

        # NOTE: This is not ideal, as we are having to load hs data and layout twice because of
        # K12 schools having both proficiency and HS data and HS/AHS only having HS data
        if selected_school_type == "K12" and radio_type == "hs":

            location = "/info/proficiency"

            # load HS academic data
            selected_raw_hs_school_data = get_high_school_academic_data(school)

            excluded_years = get_excluded_years(selected_year_string)

            # exclude years later than the selected year
            if excluded_years:
                selected_raw_hs_school_data = selected_raw_hs_school_data[~selected_raw_hs_school_data["Year"].isin(excluded_years)]

            if len(selected_raw_hs_school_data.index) > 0:

                selected_raw_hs_school_data = filter_high_school_academic_data(selected_raw_hs_school_data)

                all_hs_school_data = process_high_school_academic_data(selected_raw_hs_school_data, school)

                if not all_hs_school_data.empty:

                    main_container = {"display": "block"}
                    empty_container = {"display": "none"}
                    # radio_input_container = {'display': 'block'} # show k8/hs radio group

                    # Graduation Rate Tables ("Strength of Diploma" in data, but not currently displayed)
                    grad_overview_categories = ["Total", "Non Waiver", "State Average"]

                    if selected_school_type == "AHS":
                        grad_overview_categories.append("CCR Percentage")

                    all_hs_school_data.columns = all_hs_school_data.columns.astype(str)

                    # Graduation Rate Tables
                    graduation_data = all_hs_school_data[all_hs_school_data["Category"].str.contains("Graduation")].copy()

                    if len(graduation_data.columns) > 1 and len (graduation_data.index) > 0:

                        k12_grad_table_container = {"display": "block"}

                        graduation_data["Category"] = (graduation_data["Category"].str.replace("Graduation Rate", "").str.strip())

                        grad_overview = graduation_data[graduation_data["Category"].str.contains("|".join(grad_overview_categories))]
                        grad_overview = grad_overview.dropna(axis=1,how="all")

                        k12_grad_overview_table = create_multi_header_table_with_container(grad_overview,"Graduation Rate Overview")
                        k12_grad_overview_table = set_table_layout(k12_grad_overview_table, k12_grad_overview_table, grad_overview.columns)

                        grad_ethnicity = graduation_data[graduation_data["Category"].str.contains("|".join(ethnicity))]
                        grad_ethnicity = grad_ethnicity.dropna(axis=1,how="all")

                        k12_grad_ethnicity_table = create_multi_header_table_with_container(grad_ethnicity,"Graduation Rate by Ethnicity")
                        k12_grad_ethnicity_table = set_table_layout(k12_grad_ethnicity_table, k12_grad_ethnicity_table, grad_ethnicity.columns)

                        grad_subgroup = graduation_data[graduation_data["Category"].str.contains("|".join(subgroup))]
                        grad_subgroup = grad_subgroup.dropna(axis=1,how="all")

                        k12_grad_subgroup_table = create_multi_header_table_with_container(grad_subgroup,"Graduation Rate by Subgroup")
                        k12_grad_subgroup_table = set_table_layout(k12_grad_subgroup_table, k12_grad_subgroup_table, grad_subgroup.columns)

                    # SAT Benchmark Table
                    k12_sat_table_data = all_hs_school_data[all_hs_school_data["Category"].str.contains("Benchmark %")].copy()

                    if len(k12_sat_table_data.columns) > 1 and len (k12_sat_table_data.index) > 0:

                        k12_sat_table_container = {"display": "block"}

                        k12_sat_table_data["Category"] = (k12_sat_table_data["Category"].str.replace("Benchmark %", "").str.strip())

                        k12_sat_overview = k12_sat_table_data[k12_sat_table_data["Category"].str.contains("School Total")]
                        k12_sat_overview = k12_sat_overview.dropna(axis=1,how="all")

                        k12_sat_overview_table = create_multi_header_table_with_container(k12_sat_overview,"SAT Overview")
                        k12_sat_overview_table = set_table_layout(k12_sat_overview_table, k12_sat_overview_table, k12_sat_overview.columns)

                        k12_sat_ethnicity = k12_sat_table_data[k12_sat_table_data["Category"].str.contains("|".join(ethnicity))]
                        k12_sat_ethnicity = k12_sat_ethnicity.dropna(axis=1,how="all")

                        k12_sat_ethnicity_table = create_multi_header_table_with_container(k12_sat_ethnicity,"SAT Benchmarks by Ethnicity")
                        k12_sat_ethnicity_table = set_table_layout(k12_sat_ethnicity_table, k12_sat_ethnicity_table, k12_sat_ethnicity.columns)

                        k12_sat_subgroup = k12_sat_table_data[k12_sat_table_data["Category"].str.contains("|".join(subgroup))]
                        k12_sat_subgroup = k12_sat_subgroup.dropna(axis=1,how="all")

                        k12_sat_subgroup_table = create_multi_header_table_with_container(k12_sat_subgroup,"SAT Benchmarks by Subgroup")
                        k12_sat_subgroup_table = set_table_layout(k12_sat_subgroup_table, k12_sat_subgroup_table, k12_sat_subgroup.columns)

                        # SAT Cut-Score Table
                        # https://www.in.gov/sboe/files/2021-2022-k12-sat-Standard-Setting-SBOE-Review.pdf
                        k12_sat_cut_scores_label = "SAT Proficiency Cut Scores (2021 - 22)"
                        k12_sat_cut_scores_dict = {
                            "Content Area": ["Mathematics", "Evidenced-Based Reading and Writing"],
                            "Below College-Ready Benchmark": ["200 - 450", "200 - 440"],
                            "Approaching College-Ready Benchmark": ["460 - 520", "450 - 470"],
                            "At College-Ready Benchmark": ["530 - 800", "480 - 800"]
                        }

                        k12_sat_cut_scores = pd.DataFrame(k12_sat_cut_scores_dict)
                        k12_sat_cut_scores_table = create_key_table(k12_sat_cut_scores, k12_sat_cut_scores_label)

                    academic_proficiency_notes_string = "Beginning with the 2021-22 SY, SAT replaced ISTEP+ as the state mandated HS assessment. \
                        Beginning with the 2023 cohort all students in grade 11 will be required to take the assessment.\
                        Data Source: Indiana Department of Education Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)."

        elif (selected_school_type == "K8" or selected_school_type == "K12" or \
            (selected_school_id == 5874 and selected_year_numeric >= 2021)) and radio_type == "k8":
            # CHS PRE REORG WHERE DOES THE =/=> GO?

            location = "/info/proficiency"

            selected_raw_k8_school_data = get_k8_school_academic_data(school)

            excluded_years = get_excluded_years(selected_year_string)

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

                    ela_grade_table = create_multi_header_table(years_by_grade_ela)

                    # by Grade Year over Year Line Chart
                    ela_grade_fig_data = year_over_year_data.filter(regex = r"^Grade \d\|ELA|IREAD|^School Name$|^Year$",axis=1)
                    ela_grade_line_fig = make_line_chart(ela_grade_fig_data)

                    proficiency_grades_ela = create_line_fig_layout(ela_grade_table, ela_grade_line_fig, "ELA By Grade")

                    # by Subgroup Table
                    years_by_subgroup_ela = all_k8_school_data[(all_k8_school_data["Category"].str.contains("|".join(subgroup)) & all_k8_school_data["Category"].str.contains("ELA"))]

                    ela_subgroup_table = create_multi_header_table(years_by_subgroup_ela)

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

                    ela_ethnicity_table = create_multi_header_table(years_by_ethnicity_ela)

                    # by Ethnicity Year over Year Line Chart
                    ela_ethnicity_fig_data = year_over_year_data.loc[:, (year_over_year_data.columns.isin(categories_ela_ethnicity)) | \
                            (year_over_year_data.columns.isin(["School Name","Year"]))]
                    ela_ethnicity_line_fig = make_line_chart(ela_ethnicity_fig_data)

                    proficiency_ethnicity_ela = create_line_fig_layout(ela_ethnicity_table, ela_ethnicity_line_fig, "ELA By Ethnicity")

                ## Math

                    # by Grade Table
                    years_by_grade_math = all_k8_school_data[(all_k8_school_data["Category"].str.contains("|".join(grades_all)) & all_k8_school_data["Category"].str.contains("Math"))]

                    math_grade_table = create_multi_header_table(years_by_grade_math)

                    # by Grade Year over Year Line Chart
                    math_grade_fig_data = year_over_year_data.filter(regex = r"^Grade \d\|Math|^School Name$|^Year$",axis=1)
                    math_grade_line_fig = make_line_chart(math_grade_fig_data)

                    proficiency_grades_math = create_line_fig_layout(math_grade_table, math_grade_line_fig, "Math By Grade")

                    # by Subgroup Table
                    years_by_subgroup_math = all_k8_school_data[(all_k8_school_data["Category"].str.contains("|".join(subgroup)) & all_k8_school_data["Category"].str.contains("Math"))]

                    math_subgroup_table = create_multi_header_table(years_by_subgroup_math)

                    # by Subgroup Year over Year Line Chart
                    math_subgroup_fig_data = year_over_year_data.loc[:, (year_over_year_data.columns.isin(categories_math_subgroup)) | \
                            (year_over_year_data.columns.isin(["School Name","Year"]))]
                    math_subgroup_line_fig = make_line_chart(math_subgroup_fig_data)

                    proficiency_subgroup_math = create_line_fig_layout(math_subgroup_table, math_subgroup_line_fig, "Math By Subgroup")

                    # by Ethnicity
                    years_by_ethnicity_math = all_k8_school_data[(all_k8_school_data["Category"].str.contains("|".join(ethnicity)) & all_k8_school_data["Category"].str.contains("Math"))]

                    math_ethnicity_table = create_multi_header_table(years_by_ethnicity_math)

                    # by Ethnicity Year over Year Line Chart
                    math_ethnicity_fig_data = year_over_year_data.loc[:, (year_over_year_data.columns.isin(categories_math_ethnicity)) | \
                            (year_over_year_data.columns.isin(["School Name","Year"]))]
                    math_ethnicity_line_fig = make_line_chart(math_ethnicity_fig_data)

                    proficiency_ethnicity_math = create_line_fig_layout(math_ethnicity_table, math_ethnicity_line_fig, "Math By Ethnicity")

                    # Attendance rate
                    school_demographic_data = get_demographic_data(school)

                    attendance_rate = get_attendance_data(school_demographic_data, selected_year_string)

                    if len(attendance_rate.index) > 0:
                        attendance_table = create_single_header_table(attendance_rate,"Attendance Data")
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

            academic_proficiency_notes_string = "There are a number of factors that make it difficult to make \
                valid and reliable comparisons between test scores from 2019 to 2022. For example, ILEARN was \
                administered for the first time during the 2018-19 SY and represented an entirely new type and \
                mode of assessment (adaptive and online-only). No State assessment was administered in 2020 because \
                of the Covid-19 pandemic. Finally, the 2019 data set includes only students  who attended the \
                testing school for 162 days, while the 2021 and 2022 data sets included all tested students."

    return (location,
        proficiency_grades_ela, ela_grade_bar_fig, proficiency_ela_grades_container,
        proficiency_ethnicity_ela, ela_ethnicity_bar_fig, proficiency_ela_ethnicity_container,
        proficiency_subgroup_ela, ela_subgroup_bar_fig, proficiency_ela_subgroup_container,
        proficiency_grades_math, math_grade_bar_fig, proficiency_math_grades_container,
        proficiency_ethnicity_math, math_ethnicity_bar_fig, proficiency_math_ethnicity_container,
        proficiency_subgroup_math, math_subgroup_bar_fig, proficiency_math_subgroup_container,
        attendance_table, k8_table_container,
        k12_grad_overview_table, k12_grad_ethnicity_table, k12_grad_subgroup_table, k12_grad_table_container,
        k12_sat_cut_scores_table, k12_sat_overview_table, k12_sat_ethnicity_table, k12_sat_subgroup_table,
        k12_sat_table_container, main_container, empty_container, no_display_data, academic_proficiency_notes_string
    )

def layout():
    return html.Div(
        [
            dcc.Location(id="current-proficiency-page", refresh=False),
            html.Div(id="hidden-proficiency", style={"display": "none"}),
            dcc.Location(id="redirect-proficiency-content",  refresh="callback-nav"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(subnav_academic_information(), id="subnav-academic", className="tabs"),
                        ],
                        className="bare-container--flex--center twelve columns",
                    ),
                ],
                className="row",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(create_radio_layout("academic-proficiency", "type"),className="tabs"),

                        ],
                        className = "bare-container--flex--center twelve columns",
                    ),
                ],
                className = "row",
            ),            
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(create_radio_layout("academic-proficiency", "category"),className="tabs"),

                        ],
                        className = "bare-container--flex--center twelve columns",
                    ),
                ],
                className = "row",
            ),
            html.Hr(className = "line_bottom"),
            html.Div(
                [
                dcc.Loading(
                    id="loading",
                    type="circle",
                    fullscreen = True,
                    style={
                        "position": "absolute",
                        "alignSelf": "center",
                        "backgroundColor": "#F2F2F2",
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
                                                                className="pretty-container--close--top six columns",
                                                    ),
                                                ],
                                                className="bare-container--flex--center twelve columns",
                                            ),
                                        ],
                                        id="proficiency-ela-grades-container",
                                        className="pagebreak-after",
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
                                                                className="pretty-container--close--top six columns",
                                                    ),
                                                ],
                                                className="bare-container--flex--center twelve columns",
                                            ),
                                        ],
                                        id="proficiency-ela-ethnicity-container",
                                        className="pagebreak-after",
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
                                                                className="pretty-container--close--top six columns",
                                                    ),
                                                ],
                                                className="bare-container--flex--center twelve columns",
                                            ),
                                        ],
                                        id="proficiency-ela-subgroup-container",
                                        className="pagebreak-after",
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
                                                                className="pretty-container--close--top six columns",
                                                    ),
                                                ],
                                                className="bare-container--flex--center twelve columns",
                                            ),
                                        ],
                                        id="proficiency-math-grades-container",
                                        className="pagebreak-after",
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
                                                                className="pretty-container--close--top six columns",
                                                    ),
                                                ],
                                                className="bare-container--flex--center twelve columns",
                                            ),
                                        ],
                                        id="proficiency-math-ethnicity-container",
                                        className="pagebreak-after",
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
                                                                className="pretty-container--close--top six columns",
                                                    ),
                                                ],
                                                className="bare-container--flex--center twelve columns",
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
                                                html.Label("Graduation Rate", className="label__header", style = {"marginTop": "20px"}),
                                            ],
                                            className="bare-container--flex--center twelve columns",                                    
                                        ),
                                        html.Div(id="k12-grad-overview-table"),
                                        html.Div(id="k12-grad-ethnicity-table"),
                                        html.Div(id="k12-grad-subgroup-table"),
                                    ],
                                    id="k12-grad-table-container",
                                ),
                                html.Div(
                                    [                                
                                        html.Div(
                                            [
                                                html.Label("SAT", className="label__header", style = {'marginTop': "20px"}),
                                        ],
                                            className="bare-container--flex--center twelve columns",                                    
                                        ),                                        
                                        html.Div(id="k12-sat-cut-scores-table", children=[]),
                                        html.Div(id="k12-sat-overview-table"),
                                        html.Div(id="k12-sat-ethnicity-table"),
                                        html.Div(id="k12-sat-subgroup-table"),
                                    ],
                                    id="k12-sat-table-container",
                                ),
                            ],
                            id = "academic-proficiency-main-container",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Notes:", className="key-label__header"),
                                        html.P(""),
                                            html.P(id="academic-proficiency-notes-string",
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
                                    className = "pretty-container__key ten columns"
                                ),
                            ],
                            className = "bare-container--flex--center twelve columns"
                        ),                    
                    ],
                ),
            ],
        ),
        html.Div(
            [
                html.Div(id="academic-proficiency-no-data"),
            ],
            id = "academic-proficiency-empty-container",
        ),
    ],
    id="main-container",
)
