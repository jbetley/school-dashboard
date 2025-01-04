##################################################
# ICSB Dashboard - Academic Analysis - Multi-Year #
##################################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.16
# date:     12/29/24

import dash
from dash import dcc, ctx, html, Input, Output, State, callback
from dash.exceptions import PreventUpdate
import pandas as pd

from .globals import color
from .load_data import get_school_index, get_multiyear_data
from .process_data import create_comparison_dropdown_list
from .tables import create_empty_page_layout
from .layouts import create_multiyear_layout
from .string_helpers import generate_colors

dash.register_page(
    __name__,
    name="Multi-Year Analysis",
    path="/academic_analysis_multiyear",
    top_nav=False,
    order=11,
)


# comparison schools dropdown
@callback(
    Output("analysis-multiyear-comparison-dropdown", "options"),
    Output("analysis-multiyear-input-warning", "children"),
    Output("analysis-multiyear-comparison-dropdown", "value"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("analysis-multiyear-comparison-dropdown", "value"),
    Input("academic-type-radio", "value"),
)
def set_dropdown_options(
    school_id: str, year: str, comparison_schools: list, academic_type_value: str
):
    string_year = year
    numeric_year = int(string_year)

    # clear the list of comparison_schools when a new school is
    # selected (or when a K12 school switches from HS to K8 or
    # vice versa) to prevent comparison_schools from carrying over
    # when school is changed
    input_trigger = ctx.triggered_id
    if input_trigger == "charter-dropdown" or input_trigger == "academic-type-radio":
        comparison_schools = []

    selected_school = get_school_index(school_id)
    school_type = selected_school["School Type"].values[0]

    # CHS exception (see app.py)
    if int(school_id) == 5874 and numeric_year < 2021:
        school_type = "k12"

    if school_type == "k12":
        if academic_type_value == "hs":
            school_type = "hs"
        else:
            school_type = "k8"

    school_options, input_warning, comparison_schools = create_comparison_dropdown_list(
        school_id, year, comparison_schools, academic_type_value
        )

    return school_options, input_warning, comparison_schools


@callback(
    Output("trace-color-state-multiyear", "data"),
    Output("analysis-multiyear-dropdown-container", "style"),
    Output("linechart-year-over-year-grade", "children"),
    Output("linechart-year-over-year-hs", "children"),
    Output("k8-analysis-multiyear-main-container", "style"),
    Output("k8-analysis-multiyear-empty-container", "style"),
    Output("k8-analysis-multiyear-no-data", "children"),
    Output("hs-analysis-multiyear-main-container", "style"),
    Output("hs-analysis-multiyear-empty-container", "style"),
    Output("hs-analysis-multiyear-no-data", "children"),
    Output("multiyear-analysis-notes", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("academic-type-radio", "value"),
    Input("analysis-multiyear-subject-radio", "value"),
    Input("analysis-multiyear-hs-group-radio", "value"),
    [Input("analysis-multiyear-comparison-dropdown", "value")],
    Input("trace-color-state-multiyear", "data"),
    State("analysis-multiyear-subcategory-radio", "value"),
)
def update_academic_analysis_multiyear(
    school: str,
    year: str,
    academic_type_value: str,
    subject_radio_value: str,
    hs_group_radio_value: str,
    comparison_school_list: list,
    trace_color_state: dict,
    subcategory_radio_value: str,
):
    if not school:
        raise PreventUpdate

    string_year = year

    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]

    # CHS exception (see app.py)
    if int(school) == 5874 and int(year) < 2021:
        school_type = "k12"

    school_name = selected_school["School Name"].values[0]
    school_name = school_name.strip()

    # for some reason, this radio button doesn't
    # always play nice
    if not academic_type_value:
        academic_type_value = "k8"

    if not trace_color_state:
        trace_color_state = {}
        trace_colors = {}

    # default values (only empty container displayed)
    hs_analysis_multi_main_container = {"display": "none"}
    hs_analysis_multi_empty_container = {"display": "none"}
    k8_analysis_multi_main_container = {"display": "none"}
    k8_analysis_multi_empty_container = {"display": "block"}
    analysis_multi_dropdown_container = {"display": "none"}

    k8_analysis_multi_no_data = create_empty_page_layout(
        "Comparison Data - K-8 Academic Data", "No Data to Display."
    )
    hs_analysis_multi_no_data = create_empty_page_layout(
        "Comparison Data - High School Academic Data", "No Data to Display."
    )

    analysis__multi_notes_label = ""
    analysis__multi_notes_string = ""

    ## Multi-Year HS (SAT and Graduation Rate) Chart
    if (
        school_type == "hs"
        or school_type == "ahs"
        or (school_type == "k12" and academic_type_value == "hs")
    ):
        k8_analysis_multi_empty_container = {"display": "none"}
        multiyear_grade = []  # type: list

        analysis__multi_notes_label = "Comparison Data - High School"
        analysis__multi_notes_string = "Use this page to view SAT and Graduation Rate comparison data for all ethnicities, \
            and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
            the selected school. Up to eight (8) schools may be displayed at once."

        # labels are used to generate message on empty tables
        if (
            subcategory_radio_value != "No Subgroup Data"
            and subcategory_radio_value != "No Race/Ethnicity Data"
            and subcategory_radio_value != "No Data"
        ):
            if hs_group_radio_value == "SAT":
                if subcategory_radio_value:
                    category = subcategory_radio_value + "|" + subject_radio_value

                else:
                    category = "Total|EBRW"

                label = "Multi-Year Comparison (SAT At Benchmark) - " + category
                msg = ""

                multiyear_hs_data, all_school_info = get_multiyear_data(
                    school, comparison_school_list, category, string_year, "sat"
                )

            elif hs_group_radio_value == "Graduation Rate" or not hs_group_radio_value:
                if subcategory_radio_value:
                    category = subcategory_radio_value + "|"
                else:
                    category = "Total|"

                label = "Multi-Year Comparison (Graduation Rate) - " + category[:-1]
                msg = ""

                multiyear_hs_data, all_school_info = get_multiyear_data(
                    school, comparison_school_list, category, string_year, "grad"
                )

        else:
            multiyear_hs_data = pd.DataFrame()

            if subcategory_radio_value == "No Data" or subcategory_radio_value == "":
                label = "Multi-Year Comparison (" + hs_group_radio_value + ")"
                msg = "No Data for Selected School."
            else:
                label = (
                    "Multi-Year Comparison ("
                    + hs_group_radio_value
                    + ") - "
                    + subcategory_radio_value[3:-5:]
                )
                msg = subcategory_radio_value + " for Selected School."

        if multiyear_hs_data.empty:
            analysis_multi_dropdown_container = {"display": "none"}
            hs_analysis_multi_empty_container = {"display": "block"}
            multiyear_hs = []
            trace_colors = {}

        else:
            hs_analysis_multi_main_container = {"display": "block"}
            hs_analysis_multi_empty_container = {"display": "none"}
            analysis_multi_dropdown_container = {"display": "block"}

            trace_colors = generate_colors(
                multiyear_hs_data, trace_color_state, color, school_name
            )

            multiyear_hs = create_multiyear_layout(
                school, multiyear_hs_data, all_school_info, label, trace_colors, msg
            )

    elif school_type == "k8" or (school_type == "k12" and academic_type_value == "k8"):
        hs_analysis_multi_main_container = {"display": "none"}
        multiyear_hs = []

        analysis__multi_notes_label = "Comparison Data - K-8"
        analysis__multi_notes_string = "Use this page to view ILEARN & IREAD proficiency comparison data for all grades, ethnicities, \
            and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
            the selected school. Up to eight (8) schools may be displayed at once."

        ## K8 Multi-Year Chart
        if subject_radio_value == "IREAD":
            if (
                subcategory_radio_value != "No Subgroup Data"
                and subcategory_radio_value != "No Race/Ethnicity Data"
                and subcategory_radio_value != "No Data"
            ):
                if subcategory_radio_value:
                    category = subcategory_radio_value + "|" + subject_radio_value
                else:
                    category = "Total|IREAD"

                label = "Multi-Year Comparison - " + category
                msg = ""

                multiyear_k8_data, all_school_info = get_multiyear_data(
                    school, comparison_school_list, category, string_year, "k8"
                )

            else:
                multiyear_k8_data = pd.DataFrame()

                if (
                    subcategory_radio_value == "No Data"
                    or subcategory_radio_value == ""
                ):
                    label = (
                        "Multi-Year Comparison ("
                        + subcategory_radio_value
                        + "|"
                        + subject_radio_value
                        + ")"
                    )
                    msg = "No Data for Selected School."
                else:
                    label = (
                        "Multi-Year Comparison ("
                        + subcategory_radio_value
                        + "|"
                        + subject_radio_value
                        + ") - "
                        + subcategory_radio_value[3:-5:]
                    )
                    msg = subcategory_radio_value + " for Selected School."

            if multiyear_k8_data.empty:
                analysis_multi_dropdown_container = {"display": "none"}
                k8_analysis_multi_empty_container = {"display": "block"}
                multiyear_grade = []

            else:
                k8_analysis_multi_main_container = {"display": "block"}
                k8_analysis_multi_empty_container = {"display": "none"}
                analysis_multi_dropdown_container = {"display": "block"}

                # all_school_info is a dataframe with school names and school ids,
                # it is used in the comparison_table function to identify the index
                # of the school by Id
                trace_colors = generate_colors(
                    multiyear_k8_data, trace_color_state, color, school_name
                )

                multiyear_grade = create_multiyear_layout(
                    school,
                    multiyear_k8_data,
                    all_school_info,
                    label,
                    trace_colors,
                    subcategory_radio_value,
                )

        else:
            if (
                subcategory_radio_value != "No Subgroup Data"
                and subcategory_radio_value != "No Race/Ethnicity Data"
                and subcategory_radio_value != "No Data"
            ):
                if subcategory_radio_value:
                    category = subcategory_radio_value + "|" + subject_radio_value
                else:
                    category = "Total|ELA"

                label = "Multi-Year Comparison - " + category
                msg = ""

                multiyear_k8_data, all_school_info = get_multiyear_data(
                    school, comparison_school_list, category, string_year, "k8"
                )

            else:
                multiyear_k8_data = pd.DataFrame()

                if (
                    subcategory_radio_value == "No Data"
                    or subcategory_radio_value == ""
                ):
                    label = (
                        "Multi-Year Comparison ("
                        + subcategory_radio_value
                        + "|"
                        + subject_radio_value
                        + ")"
                    )
                    msg = "No Data for Selected School."
                else:
                    label = (
                        "Multi-Year Comparison ("
                        + subcategory_radio_value
                        + "|"
                        + subject_radio_value
                        + ") - "
                        + subcategory_radio_value[3:-5:]
                    )
                    msg = subcategory_radio_value + " for Selected School."

            if multiyear_k8_data.empty:
                analysis_multi_dropdown_container = {"display": "none"}
                k8_analysis_multi_empty_container = {"display": "block"}
                multiyear_grade = []

            else:
                k8_analysis_multi_main_container = {"display": "block"}
                k8_analysis_multi_empty_container = {"display": "none"}
                analysis_multi_dropdown_container = {"display": "block"}

                # all_school_info is a dataframe with school names and school ids,
                # it is used in the comparison_table function to identify the index
                # of the school by Id

                trace_colors = generate_colors(
                    multiyear_k8_data, trace_color_state, color, school_name
                )

                multiyear_grade = create_multiyear_layout(
                    school,
                    multiyear_k8_data,
                    all_school_info,
                    label,
                    trace_colors,
                    subcategory_radio_value,
                )

    analysis__multi_notes = [
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            analysis__multi_notes_label, className="key-label__header"
                        ),
                        html.P(""),
                        html.P(
                            analysis__multi_notes_string,
                            style={
                                "textAlign": "Left",
                                "color": "#6783a9",
                                "fontSize": "1.2rem",
                                "margin": "10px",
                            },
                        ),
                    ],
                    className="pretty-container__key seven columns",
                )
            ],
            className="bare-container--flex--center twelve columns",
        )
    ]

    trace_color_state = trace_colors

    return (
        trace_color_state,
        analysis_multi_dropdown_container,
        multiyear_grade,
        multiyear_hs,
        k8_analysis_multi_main_container,
        k8_analysis_multi_empty_container,
        k8_analysis_multi_no_data,
        hs_analysis_multi_main_container,
        hs_analysis_multi_empty_container,
        hs_analysis_multi_no_data,
        analysis__multi_notes,
    )


def layout():
    return html.Div(
        [
            html.Div(
                [
                    # dict used to store {school:color} to ensure consistency
                    dcc.Store(
                        id="trace-color-state-multiyear", storage_type="memory", data={}
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                "Add or Remove Schools: ",
                                                className="comparison-dropdown-label",
                                            ),
                                        ],
                                        className="bare-container two columns",
                                    ),
                                    html.Div(
                                        [
                                            dcc.Dropdown(
                                                id="analysis-multiyear-comparison-dropdown",
                                                style={"fontSize": "1.1rem"},
                                                multi=True,
                                                clearable=False,
                                                className="comparison-dropdown-control",
                                            ),
                                            html.Div(
                                                id="analysis-multiyear-input-warning"
                                            ),
                                        ],
                                        className="bare-container eight columns",
                                    ),
                                ],
                                className="comparison-dropdown-row",
                            ),
                        ],
                        id="analysis-multiyear-dropdown-container",
                    ),
                    html.Div(
                        [
                            html.Div(id="linechart-year-over-year-grade", children=[]),
                            html.Div(
                                [
                                    html.Div(
                                        id="multiyear-analysis-notes", children=[]
                                    ),
                                ],
                                className="row",
                            ),
                        ],
                        id="k8-analysis-multiyear-main-container",
                        style={"display": "none"},
                    ),
                    html.Div(
                        [
                            html.Div(id="k8-analysis-multiyear-no-data"),
                        ],
                        id="k8-analysis-multiyear-empty-container",
                    ),
                    html.Div(
                        [
                            html.Div(id="linechart-year-over-year-hs", children=[]),
                        ],
                        id="hs-analysis-multiyear-main-container",
                        style={"display": "none"},
                    ),
                    html.Div(
                        [
                            html.Div(id="hs-analysis-multiyear-no-data"),
                        ],
                        id="hs-analysis-multiyear-empty-container",
                    ),
                ],
                id="multiyear-academic-analysis-page",
            )
        ],
        id="main-container",
    )
