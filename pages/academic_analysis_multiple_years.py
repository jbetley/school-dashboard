#######################################################
# ICSB Dashboard - Academic Analysis - Year over Year #
#######################################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     02/14/24

import dash
from dash import dcc, ctx, html, Input, Output, State, callback
from dash.exceptions import PreventUpdate
import pandas as pd

# import local functions
from .load_data import get_school_index, get_year_over_year_data, get_school_coordinates
from .tables import no_data_page
from .layouts import create_year_over_year_layout
from .calculations import check_for_gradespan_overlap, calculate_comparison_school_list

dash.register_page(
    __name__,
    name="Year over Year",
    path="/academic_analysis_multiple_year",
    top_nav=False,
    order=11,
)


# Set dropdown options for comparison schools
@callback(
    Output("analysis-multi-comparison-dropdown", "options"),
    Output("analysis-multi-input-warning", "children"),
    Output("analysis-multi-comparison-dropdown", "value"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("analysis-multi-comparison-dropdown", "value"),
    Input("analysis-type-radio", "value"),
)
def set_dropdown_options(
    school_id: str, year: str, comparison_schools: list, analysis_type_value: str
):
    string_year = year
    numeric_year = int(string_year)

    # clear the list of comparison_schools when a new school is
    # selected, otherwise comparison_schools will carry over
    input_trigger = ctx.triggered_id
    if input_trigger == "charter-dropdown":
        comparison_schools = []

    selected_school = get_school_index(school_id)
    school_type = selected_school["School Type"].values[0]

    # Get School ID, School Name, Lat & Lon for all schools in the set for selected year
    # SQL query depends on school type
    if school_type == "K12":
        if analysis_type_value == "hs":
            school_type = "HS"
        else:
            school_type = "K8"

    schools_by_distance = get_school_coordinates(numeric_year, school_type)

    # Drop any school not testing at least 20 students. "Total|ELATotalTested" is a proxy
    # for school size here (probably only impacts ~20 schools)
    # the second condition ensures that the school is retained if it exists
    if school_type == "K8":
        schools_by_distance = schools_by_distance[
            (schools_by_distance["Total|ELA Total Tested"] >= 20)
            | (schools_by_distance["School ID"] == int(school_id))
        ]

    # If school doesn't exist
    if int(school_id) not in schools_by_distance["School ID"].values:
        return [], [], []

    else:
        # NOTE: Before we do the distance check, we reduce the size of the df removing
        # schools where there is no or only one grade overlap between the comparison schools.
        # the variable "overlap" is one less than the the number of grades that we want as a
        # minimum (a value of "1" means a 2 grade overlap, "2" means 3 grade overlap, etc.).

        # Skip this step for AHS (don't have a 'gradespan' in the technical sense)
        if school_type != "AHS":
            schools_by_distance = check_for_gradespan_overlap(
                school_id, schools_by_distance
            )
 
        comparison_list = calculate_comparison_school_list(school_id, schools_by_distance, 20)

        # Set default display selections to all schools in the list
        default_options = [
            {"label": name, "value": id} for name, id in comparison_list.items()
        ]
        options = default_options

        # value for number of default display selections and maximum
        # display selections (because of zero indexing, max should be
        # 1 less than actual desired number)
        default_num_to_display = 4
        max_num_to_display = 7

        # used to display message if the number of selections exceeds the max
        input_warning = None

        # create list of comparison schools based on current school id,
        # test whether any of the school ids in the current_comparison_school list
        # are present in comparison_schools(the input). isdisjoint() returns True
        # if two sets don't have any common items between them. If False, we want
        # to replace comparison_schools with current_comparison_school list - note
        # this will also take care of the initial load because an empty list return False
        current_comparison_schools = [d["value"] for d in options]

        if not comparison_schools or (
            comparison_schools
            and not set(comparison_schools).isdisjoint(current_comparison_schools)
            == False
        ):
            comparison_schools = [d["value"] for d in options[:default_num_to_display]]

        else:
            if len(comparison_schools) > max_num_to_display:
                input_warning = html.P(
                    id="multi-year-input-warning",
                    children="Limit reached (Maximum of "
                    + str(max_num_to_display + 1)
                    + " schools).",
                )
                options = [
                    {
                        "label": option["label"],
                        "value": option["value"],
                        "disabled": True,
                    }
                    for option in default_options
                ]

        return options, input_warning, comparison_schools


@callback(
    Output("analysis-multi-dropdown-container", "style"),
    Output("year-over-year-grade", "children"),
    Output("year-over-year-hs", "children"),
    Output("k8-analysis-multi-main-container", "style"),
    Output("k8-analysis-multi-empty-container", "style"),
    Output("k8-analysis-multi-no-data", "children"),
    Output("hs-analysis-multi-main-container", "style"),
    Output("hs-analysis-multi-empty-container", "style"),
    Output("hs-analysis-multi-no-data", "children"),
    Output("multi-year-analysis-notes", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("analysis-type-radio", "value"),
    Input("analysis-multi-subject-radio", "value"),
    Input("analysis-multi-hs-group-radio", "value"),
    [Input("analysis-multi-comparison-dropdown", "value")],
    State("analysis-multi-subcategory-radio", "value"),
)
def update_academic_analysis_multiple_years(
    school: str,
    year: str,
    analysis_type_value: str,
    subject_radio_value: str,
    hs_group_radio_value: str,
    comparison_school_list: list,
    subcategory_radio_value: str,
):
    if not school:
        raise PreventUpdate

    string_year = year

    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]
    school_name = selected_school["School Name"].values[0]
    school_name = school_name.strip()

    # this radio button doesn't always play nice for some reason
    if not analysis_type_value:
        analysis_type_value = "k8"

    # default values (only empty container displayed)
    hs_analysis_multi_main_container = {"display": "none"}
    hs_analysis_multi_empty_container = {"display": "none"}
    k8_analysis_multi_main_container = {"display": "none"}
    k8_analysis_multi_empty_container = {"display": "block"}
    analysis_multi_dropdown_container = {"display": "none"}

    k8_analysis_multi_no_data = no_data_page(
        "No Data to Display.", "Comparison Data - K-8 Academic Data"
    )
    hs_analysis_multi_no_data = no_data_page(
        "No Data to Display.", "Comparison Data - High School Academic Data"
    )

    analysis__multi_notes_label = ""
    analysis__multi_notes_string = ""

    if (
        school_type == "HS"
        or school_type == "AHS"
        or (school_type == "K12" and analysis_type_value == "hs")
    ):
        k8_analysis_multi_empty_container = {"display": "none"}
        year_over_year_grade = []  # type:list

        analysis__multi_notes_label = "Comparison Data - High School"
        analysis__multi_notes_string = "Use this page to view SAT and Graduation Rate comparison data for all ethnicities, \
            and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
            the selected school. Up to eight (8) schools may be displayed at once."

        # get data for school (these labels are used to generate the message on the empty tables)
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

                label = "Year over Year Comparison (SAT At Benchmark) - " + category
                msg = ""

                year_over_year_hs_data, all_school_info = get_year_over_year_data(
                    school, comparison_school_list, category, string_year, "sat"
                )

            elif hs_group_radio_value == "Graduation Rate" or not hs_group_radio_value:
                if subcategory_radio_value:
                   
                    category = subcategory_radio_value + "|"
                else:
                    category = "Total|"

                label = "Year over Year Comparison (Graduation Rate) - " + category[:-1]
                msg = ""

                year_over_year_hs_data, all_school_info = get_year_over_year_data(
                    school, comparison_school_list, category, string_year, "grad"
                )

        else:
            year_over_year_hs_data = pd.DataFrame()

            if subcategory_radio_value == "No Data" or subcategory_radio_value == "":
                label = "Year over Year Comparison (" + hs_group_radio_value + ")"
                msg = "No Data for Selected School."
            else:
                label = (
                    "Year over Year Comparison ("
                    + hs_group_radio_value
                    + ") - "
                    + subcategory_radio_value[3:-5:]
                )
                msg = subcategory_radio_value + " for Selected School."

        if year_over_year_hs_data.empty:
            analysis_multi_dropdown_container = {"display": "none"}
            hs_analysis_multi_empty_container = {"display": "block"}
            year_over_year_hs = []

        else:
            hs_analysis_multi_main_container = {"display": "block"}
            hs_analysis_multi_empty_container = {"display": "none"}
            analysis_multi_dropdown_container = {"display": "block"}

            ## Create Year Over Year HS (SAT and Graduation Rate) Chart
            
            year_over_year_hs = create_year_over_year_layout(
                school, year_over_year_hs_data, all_school_info, label, msg
            )

    elif school_type == "K8" or (school_type == "K12" and analysis_type_value == "k8"):
        hs_analysis_multi_main_container = {"display": "none"}
        year_over_year_hs = []

        analysis__multi_notes_label = "Comparison Data - K-8"
        analysis__multi_notes_string = "Use this page to view ILEARN & IREAD proficiency comparison data for all grades, ethnicities, \
            and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
            the selected school. Up to eight (8) schools may be displayed at once."

        ## K8 Year Over Year Chart
        print(subject_radio_value)
        print(subcategory_radio_value)

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

                label = "Year over Year Comparison - " + category
                msg = ""

                year_over_year_k8_data, all_school_info = get_year_over_year_data(
                    school, comparison_school_list, category, string_year, "k8"
                )

            else:
                year_over_year_k8_data = pd.DataFrame()

                if subcategory_radio_value == "No Data" or subcategory_radio_value == "":
                    label = (
                        "Year over Year Comparison ("
                        + subcategory_radio_value
                        + "|"
                        + subject_radio_value
                        + ")"
                    )
                    msg = "No Data for Selected School."
                else:
                    label = (
                        "Year over Year Comparison ("
                        + subcategory_radio_value
                        + "|"
                        + subject_radio_value
                        + ") - "
                        + subcategory_radio_value[3:-5:]
                    )
                    msg = subcategory_radio_value + " for Selected School."

            if year_over_year_k8_data.empty:
                analysis_multi_dropdown_container = {"display": "none"}
                k8_analysis_multi_empty_container = {"display": "block"}
                year_over_year_grade = []

            else:
                k8_analysis_multi_main_container = {"display": "block"}
                k8_analysis_multi_empty_container = {"display": "none"}
                analysis_multi_dropdown_container = {"display": "block"}

                # all_school_info is a dataframe with school names and school ids,
                # it is used in the comparison_table function to identify the index
                # of the school by Id
                year_over_year_grade = create_year_over_year_layout(
                    school,
                    year_over_year_k8_data,
                    all_school_info,
                    label,
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

                label = "Year over Year Comparison - " + category
                msg = ""

                year_over_year_k8_data, all_school_info = get_year_over_year_data(
                    school, comparison_school_list, category, string_year, "k8"
                )

            else:
                year_over_year_k8_data = pd.DataFrame()

                if subcategory_radio_value == "No Data" or subcategory_radio_value == "":
                    label = (
                        "Year over Year Comparison ("
                        + subcategory_radio_value
                        + "|"
                        + subject_radio_value
                        + ")"
                    )
                    msg = "No Data for Selected School."
                else:
                    label = (
                        "Year over Year Comparison ("
                        + subcategory_radio_value
                        + "|"
                        + subject_radio_value
                        + ") - "
                        + subcategory_radio_value[3:-5:]
                    )
                    msg = subcategory_radio_value + " for Selected School."

            if year_over_year_k8_data.empty:
                analysis_multi_dropdown_container = {"display": "none"}
                k8_analysis_multi_empty_container = {"display": "block"}
                year_over_year_grade = []

            else:
                k8_analysis_multi_main_container = {"display": "block"}
                k8_analysis_multi_empty_container = {"display": "none"}
                analysis_multi_dropdown_container = {"display": "block"}

                # all_school_info is a dataframe with school names and school ids,
                # it is used in the comparison_table function to identify the index
                # of the school by Id
                year_over_year_grade = create_year_over_year_layout(
                    school,
                    year_over_year_k8_data,
                    all_school_info,
                    label,
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

    return (
        analysis_multi_dropdown_container,
        year_over_year_grade,
        year_over_year_hs,
        k8_analysis_multi_main_container,
        k8_analysis_multi_empty_container,
        k8_analysis_multi_no_data,
        hs_analysis_multi_main_container,
        hs_analysis_multi_empty_container,
        hs_analysis_multi_no_data,
        analysis__multi_notes,
    )


layout = html.Div(
    # def layout():
    #     return html.Div(
    [
        html.Div(
            [
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
                                            id="analysis-multi-comparison-dropdown",
                                            style={"fontSize": "1.1rem"},
                                            multi=True,
                                            clearable=False,
                                            className="comparison-dropdown-control",
                                        ),
                                        html.Div(id="analysis-multi-input-warning"),
                                    ],
                                    className="bare-container eight columns",
                                ),
                            ],
                            className="comparison-dropdown-row",
                        ),
                    ],
                    id="analysis-multi-dropdown-container",
                ),
                html.Div(
                    [
                        html.Div(id="year-over-year-grade", children=[]),
                        html.Div(
                            [
                                html.Div(id="multi-year-analysis-notes", children=[]),
                            ],
                            className="row",
                        ),
                    ],
                    id="k8-analysis-multi-main-container",
                    style={"display": "none"},
                ),
                html.Div(
                    [
                        html.Div(id="k8-analysis-multi-no-data"),
                    ],
                    id="k8-analysis-multi-empty-container",
                ),
                html.Div(
                    [
                        html.Div(id="year-over-year-hs", children=[]),
                    ],
                    id="hs-analysis-multi-main-container",
                    style={"display": "none"},
                ),
                html.Div(
                    [
                        html.Div(id="hs-analysis-multi-no-data"),
                    ],
                    id="hs-analysis-multi-empty-container",
                ),
            ],
            id="multi-academic-analysis-page",
        )
    ],
    id="main-container",
)
