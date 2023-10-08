###################################################
# ICSB Dashboard - Academic Information - Growth  #
###################################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.11
# date:     10/03/23

import dash
from dash import dcc, html, Input, Output, callback, State
from dash.exceptions import PreventUpdate
import pandas as pd

# import local functions
from pages.load_data import get_school_index, get_growth_data, get_excluded_years
from pages.process_data import process_growth_data
from pages.tables import no_data_page, create_growth_table
from pages.charts import make_growth_chart
from pages.layouts import create_growth_layout, create_radio_layout
from pages.subnav import subnav_academic_information

dash.register_page(__name__,  name = "Academic Growth", path = "/academic_information_growth", order=8)

# redirect url if school type is "HS" or "AHS"
@callback(
    Output("url", "href"),
    Input("charter-dropdown", "value"),
    Input("url", "href"),    
    prevent_initial_call=True
)
def redirect_hs(school: str, current_page: str):
    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]

    current_page = current_page.rsplit("/", 1)[-1]
    if current_page == "academic_information_growth" and (school_type == "HS" or school_type == "AHS"):
        return f"/academic_information"
    else:
        return dash.no_update

# Category
@callback(
    Output("academic-growth-category-radio", "options"),
    Output("academic-growth-category-radio","value"),
    Output("academic-growth-category-radio-container","style"),
    Input("charter-dropdown", "value"),    
    State("academic-growth-category-radio", "options"),
    State("academic-growth-category-radio", "value")  
)
def radio_category_selector(school: str, radio_category_options: list, radio_category_value: str):

    options_default = [
        {"label": "All Data", "value": "all"},
        {"label": "By Grade", "value": "grade"},
        {"label": "By Ethnicity", "value": "ethnicity"},
        {"label": "By Subgroup", "value": "subgroup"}
    ]

    # selected_school = get_school_index(school)
    # school_type = selected_school["School Type"].values[0]

    value_default = "all"

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
    Output("growth-grades-ela", "children"),
    Output("growth-grades-math", "children"),
    Output("growth-ethnicity-ela", "children"),
    Output("growth-ethnicity-math", "children"),
    Output("growth-subgroup-ela", "children"),
    Output("growth-subgroup-math", "children"),
    Output("academic-growth-main-growth-container", "style"),
    Output("academic-growth-empty-growth-container", "style"),
    Output("academic-growth-no-growth-data", "children"),
    Output("academic-growth-notes-string", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("academic-growth-category-radio", "value"),  
)
def update_academic_info_growth_page(school: str, year: str, radio_category: str):
    if not school:
        raise PreventUpdate

    # show 2019 instead of 2020 as 2020 has no academic data
    string_year = year
    selected_year_string = "2019" if string_year == "2020" else string_year
    selected_year_numeric = int(selected_year_string)

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]
    selected_school_id = int(selected_school["School ID"].values[0])

    # Radio buttons don't play nice
    if not radio_category:
        radio_category = "all"

    # default styles (all values empty - only empty_container displayed)
    growth_grades_ela = []
    growth_grades_math = []
    growth_ethnicity_ela = []
    growth_ethnicity_math = []
    growth_subgroup_ela = []
    growth_subgroup_math = []
    main_growth_container = {"display": "none"}
    empty_growth_container = {"display": "none"}

    academic_growth_notes_string = ""

    no_growth_data = no_data_page("No Data to Display.", "Academic Growth")

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

    excluded_years = get_excluded_years(selected_year_string)

    if excluded_years:
        growth_data = growth_data[~growth_data["Test Year"].isin(excluded_years)]

    if len(growth_data.index) == 0 or selected_school["Guest"].values[0] == "Y":

        main_growth_container = {"display": "none"}
        empty_growth_container = {"display": "block"}
        
    else:

        main_growth_container = {"display": "block"}

        empty_growth_container = {"display": "none"}

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

        growth_grades_ela = create_growth_layout(table_grades_growth_ela, fig_grades_growth_ela, label_grades_growth_ela)

        # grades growth math table/fig #3
        table_data_grades_growth_math= table_data_grades_growth[(table_data_grades_growth["Category"].str.contains("Math"))]
        growth_data_162_grades_math = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains("162")) & (fig_data_grades_growth.columns.str.contains("Math"))]
        growth_data_me_grades_math = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains("Majority Enrolled")) & (fig_data_grades_growth.columns.str.contains("Math"))]
        growth_data_162_grades_math.columns = growth_data_162_grades_math.columns.str.split("_").str[1]
        growth_data_me_grades_math.columns = growth_data_me_grades_math.columns.str.split("_").str[1]

        label_grades_growth_math = "Percentage of Students with Adequate Growth - by Grade (Math)"
        table_grades_growth_math = create_growth_table(table_data_grades_growth_math, label_grades_growth_math)
        fig_grades_growth_math = make_growth_chart(growth_data_me_grades_math, growth_data_162_grades_math, label_grades_growth_math)

        growth_grades_math = create_growth_layout(table_grades_growth_math, fig_grades_growth_math, label_grades_growth_math)

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

        growth_ethnicity_ela = create_growth_layout(table_ethnicity_growth_ela, fig_ethnicity_growth_ela, label_ethnicity_growth_ela)

        # ethnicity growth math table/fig #7
        table_data_ethnicity_growth_math = table_data_ethnicity_growth[(table_data_ethnicity_growth["Category"].str.contains("Math"))]
        growth_data_162_ethnicity_math = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains("162")) & (fig_data_ethnicity_growth.columns.str.contains("Math"))]
        growth_data_162_ethnicity_math.columns = growth_data_162_ethnicity_math.columns.str.split("_").str[1]
        growth_data_me_ethnicity_math = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains("Majority Enrolled")) & (fig_data_ethnicity_growth.columns.str.contains("Math"))]
        growth_data_me_ethnicity_math.columns = growth_data_me_ethnicity_math.columns.str.split("_").str[1]

        label_ethnicity_growth_math = "Percentage of Students with Adequate Growth - by Ethnicity (Math)"
        table_ethnicity_growth_math = create_growth_table(table_data_ethnicity_growth_math, label_ethnicity_growth_math)
        fig_ethnicity_growth_math = make_growth_chart(growth_data_me_ethnicity_math, growth_data_162_ethnicity_math, label_ethnicity_growth_math)

        growth_ethnicity_math = create_growth_layout(table_ethnicity_growth_math, fig_ethnicity_growth_math, label_ethnicity_growth_math)

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

        growth_subgroup_ela = create_growth_layout(table_subgroup_growth_ela, fig_subgroup_growth_ela, label_subgroup_growth_ela)

        # subgroup growth math table/fig #11
        table_data_subgroup_growth_math= table_data_subgroup_growth[(table_data_subgroup_growth["Category"].str.contains("Math"))]
        growth_data_162_subgroup_math = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains("162")) & (fig_data_subgroup_growth.columns.str.contains("Math"))]
        growth_data_162_subgroup_math.columns = growth_data_162_subgroup_math.columns.str.split("_").str[1]
        growth_data_me_subgroup_math = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains("Majority Enrolled")) & (fig_data_subgroup_growth.columns.str.contains("Math"))]
        growth_data_me_subgroup_math.columns = growth_data_me_subgroup_math.columns.str.split("_").str[1]

        label_subgroup_growth_math = "Percentage of Students with Adequate Growth - by Subgroup (Math)"
        table_subgroup_growth_math = create_growth_table(table_data_subgroup_growth_math, label_subgroup_growth_math)
        fig_subgroup_growth_math = make_growth_chart(growth_data_me_subgroup_math, growth_data_162_subgroup_math, label_subgroup_growth_math)

        growth_subgroup_math = create_growth_layout(table_subgroup_growth_math, fig_subgroup_growth_math, label_subgroup_growth_math)

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

    academic_growth_notes_string = "State growth data comes from IDOE's LINK. Identifying information \
        is scrubbed and data is aggregated before display. The calculation includes all students who were \
        enrolled in the selected school for the most number of days that student was enrolled in any school \
        over the entire school year (Majority Enrolled). This does not necessarily mean that the student was \
        enrolled in the school for an actual majority of the year (e.g., 82 days). This calculation thus includes \
        more students than previous year calculations which only included students who were enrolled in the \
        school for 162 Days. The 162 Day value is included in the tooltip of each table and chart for comparison purposes."

    return (
        growth_grades_ela, growth_grades_math, growth_ethnicity_ela, growth_ethnicity_math,
        growth_subgroup_ela, growth_subgroup_math, main_growth_container, empty_growth_container,
        no_growth_data, academic_growth_notes_string
    )

layout = html.Div (
# def layout():
#     return html.Div(
            [
            html.Div(
                [            
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
                ],
                id="growth-subnav-container",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(create_radio_layout("academic-growth", "category"),className="tabs"),

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
                                html.Div(id="growth-grades-ela", children=[]),
                                html.Div(id="growth-grades-math", children=[]),

                                html.Div(id="growth-ethnicity-ela", children=[]),
                                html.Div(id="growth-ethnicity-math", children=[]),

                                html.Div(id="growth-subgroup-ela", children=[]),
                                html.Div(id="growth-subgroup-math", children=[]),
                            ],
                            id = "academic-growth-main-growth-container",
                        ),
                        html.Div(
                            [
                                html.Div(id="academic-growth-no-growth-data"),
                            ],
                            id = "academic-growth-empty-growth-container",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Notes:", className="key-label__header"),
                                        html.P(""),
                                            html.P(id="academic-growth-notes-string",
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
    ],
    id="main-container",
)