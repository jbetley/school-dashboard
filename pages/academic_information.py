#######################################################
# ICSB Dashboard - Academic Information - High School #
#######################################################
# author:   jbetley
# version:  1.11
# date:     10/03/23

import dash
from dash import dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd

# import local functions
from pages.load_data import ethnicity, subgroup, get_high_school_academic_data, get_school_index, get_excluded_years
from pages.process_data import process_high_school_academic_data, filter_high_school_academic_data
from pages.tables import no_data_page, create_multi_header_table_with_container, create_key_table
from pages.layouts import set_table_layout
from pages.subnav import subnav_academic_information

dash.register_page(__name__, path = "/academic_information",  top_nav=False,  order=6)

@callback(
    Output('subnav-content', 'href'),
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
    Output("academic-information-notes-string", "children"),
    Output("academic-information-notes-container", "style"),
    Output("subnav-container", "style"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
)
def update_academic_information_page(school: str, year: str):
    if not school:
        raise PreventUpdate

    # show 2019 instead of 2020 as 2020 has no academic data
    string_year = year
    selected_year_string = "2019" if string_year == "2020" else string_year
    selected_year_numeric = int(selected_year_string)

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]
    selected_school_id = int(selected_school["School ID"].values[0])

    # default styles (all values empty - only empty_container displayed)\
    hs_grad_overview_table = []
    hs_grad_ethnicity_table = []
    hs_grad_subgroup_table = []
    sat_overview_table = []
    sat_ethnicity_table = []
    sat_subgroup_table = []
    sat_cut_scores_table = []
    sat_table_container = {"display": "none"}
    grad_table_container = {"display": "none"}

    academic_information_notes_string = ""
    main_container = {"display": "none"}
    empty_container = {"display": "block"}
    subnav_container = {"display": "none"}
    academic_information_notes_container = {"display": "none"}    

    no_display_data = no_data_page("Academic Information")

    if selected_school_type == "K8" or selected_school_type == "K12":
        empty_container = {"display": "none"}
        main_container = {"display": "block"}
        subnav_container = {"display": "block"}

        location = "/info/proficiency"

        # NOTE: There is a special exception for Christel House South - prior to 2021,
        # CHS was a K12. From 2021 onwards, CHS is a K8, with the high school moving to
        # Christel House Watanabe Manual HS
    elif (selected_school_type == "HS" or selected_school_type == "AHS"
        or (selected_school_id == 5874 and selected_year_numeric < 2021)):

        location = "/academic_information"

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
                academic_information_notes_container = {"display": "block"} 
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

                    hs_grad_overview_table = create_multi_header_table_with_container(grad_overview,"Graduation Rate Overview")
                    hs_grad_overview_table = set_table_layout(hs_grad_overview_table, hs_grad_overview_table, grad_overview.columns)

                    grad_ethnicity = graduation_data[graduation_data["Category"].str.contains("|".join(ethnicity))]
                    grad_ethnicity = grad_ethnicity.dropna(axis=1,how="all")

                    hs_grad_ethnicity_table = create_multi_header_table_with_container(grad_ethnicity,"Graduation Rate by Ethnicity")
                    hs_grad_ethnicity_table = set_table_layout(hs_grad_ethnicity_table, hs_grad_ethnicity_table, grad_ethnicity.columns)

                    grad_subgroup = graduation_data[graduation_data["Category"].str.contains("|".join(subgroup))]
                    grad_subgroup = grad_subgroup.dropna(axis=1,how="all")

                    hs_grad_subgroup_table = create_multi_header_table_with_container(grad_subgroup,"Graduation Rate by Subgroup")
                    hs_grad_subgroup_table = set_table_layout(hs_grad_subgroup_table, hs_grad_subgroup_table, grad_subgroup.columns)

                # SAT Benchmark Table
                sat_table_data = all_hs_school_data[all_hs_school_data["Category"].str.contains("Benchmark %")].copy()

                if len(sat_table_data.columns) > 1 and len (sat_table_data.index) > 0:

                    sat_table_container = {"display": "block"}

                    sat_table_data["Category"] = (sat_table_data["Category"].str.replace("Benchmark %", "").str.strip())

                    sat_overview = sat_table_data[sat_table_data["Category"].str.contains("School Total")]
                    sat_overview = sat_overview.dropna(axis=1,how="all")

                    sat_overview_table = create_multi_header_table_with_container(sat_overview,"SAT Overview")
                    sat_overview_table = set_table_layout(sat_overview_table, sat_overview_table, sat_overview.columns)

                    sat_ethnicity = sat_table_data[sat_table_data["Category"].str.contains("|".join(ethnicity))]
                    sat_ethnicity = sat_ethnicity.dropna(axis=1,how="all")

                    sat_ethnicity_table = create_multi_header_table_with_container(sat_ethnicity,"SAT Benchmarks by Ethnicity")
                    sat_ethnicity_table = set_table_layout(sat_ethnicity_table, sat_ethnicity_table, sat_ethnicity.columns)

                    sat_subgroup = sat_table_data[sat_table_data["Category"].str.contains("|".join(subgroup))]
                    sat_subgroup = sat_subgroup.dropna(axis=1,how="all")

                    sat_subgroup_table = create_multi_header_table_with_container(sat_subgroup,"SAT Benchmarks by Subgroup")
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

        ahs_notes = "Adult High Schools enroll students who are over the age of 18, under credited, \
                    dropped out of high school for a variety of reasons, and are typically out of cohort from \
                    their original graduation year. Because graduation rate is calculated at the end of the school \
                    year regardless of the length of time a student is enrolled at a school, it is not comparable to \
                    the graduation rate of a traditional high school."

        hs_notes = "Beginning with the 2021-22 SY, SAT replaced ISTEP+ as the state mandated HS assessment. \
                    Beginning with the 2023 cohort all students in grade 11 will be required to take the assessment.\
                    Data Source: Indiana Department of Education Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)."

        if selected_school_type == "AHS":
            academic_information_notes_string = ahs_notes + " " + hs_notes
        else:
            academic_information_notes_string = hs_notes

    return (
        location, hs_grad_overview_table, hs_grad_ethnicity_table, hs_grad_subgroup_table, grad_table_container,
        sat_cut_scores_table, sat_overview_table, sat_ethnicity_table, sat_subgroup_table, sat_table_container,
        main_container, empty_container, no_display_data, academic_information_notes_string,
        academic_information_notes_container, subnav_container
    )

def layout():
    return html.Div(
        [
            html.Div(
                [            
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(subnav_academic_information(), className="tabs"),
                                ],
                                className="bare-container--flex--center twelve columns",
                            ),
                        ],
                        className="row",
                    ),
                    dcc.Location(id="subnav-content",  refresh="callback-nav"),
                ],
                id="subnav-container",
            ),                    
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
                                                html.Label("Graduation Rate", className="label__header", style = {"marginTop": "5px"}),
                                            ],
                                            className="bare-container--flex--center twelve columns",
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
                                                html.Label("SAT", className="label__header", style = {'marginTop': "20px"}),
                                        ],
                                            className="bare-container--flex--center twelve columns",
                                        ),
                                        html.Div(id="sat-cut-scores-table", children=[]),
                                        html.Div(id="sat-overview-table"),
                                        html.Div(id="sat-ethnicity-table"),
                                        html.Div(id="sat-subgroup-table"),
                                    ],
                                    id="sat-table-container",
                                ),
                                html.Div(
                                    [                                
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Label("Notes:", className="key-label__header"),
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
                                                    className = "pretty-container__key ten columns"
                                                ),
                                            ],
                                            className = "bare-container--flex--center twelve columns"
                                        ),
                                    ],
                                    id = "academic-information-notes-container",
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
    ],
    id="main-container",
)