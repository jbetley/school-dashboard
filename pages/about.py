#######################################
# ICSB Dashboard - About/Demographics #
#######################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.16
# date:     12/29/24

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
from dash.exceptions import PreventUpdate

# import dash_ag_grid as dag
import plotly.express as px
import pandas as pd
import numpy as np

from .globals import (
    ethnicity,
    subgroup,
    max_display_years,
    discipline_groups,
    discipline_categories,
)
from .load_data import (
    get_excluded_years,
    get_school_index,
    get_financial_data,
    get_corp_demographic_data,
    get_school_demographic_data,
    get_adm_data,
    get_attendance_data,
    get_discipline_data,
    current_academic_year,
)

from .clean_data import clean_adm_data, clean_discipline_data
from .process_data import process_discipline_data

from .charts import (
    loading_fig,
    no_data_fig_label,
    make_line_chart,
    make_demographics_bar_chart,
)
from .tables import (
    create_key_table,
    create_simple_table,
    create_discipline_table,
    create_empty_table_layout,
    create_empty_page_layout,
)

from .layouts import create_line_fig_layout


dash.register_page(__name__, path="/about", order=0, top_nav=True)


# Discipline Dropdown
@callback(
    Output("discipline-demographic-dropdown", "options"),
    [Input("application-state", "children")],  # dummy input
)
def set_discipline_demographic_dropdown_options(app_state):
    discipline_demographic_options = [
        {"label": name, "value": name} for name in discipline_groups
    ]
    return discipline_demographic_options


# Sets the default value to the first value in discipline category list
@callback(
    Output("discipline-demographic-dropdown", "value"),
    Input("discipline-demographic-dropdown", "options"),
)
def set_discipline_demographic_dropdown_value(discipline_demographic_options):
    return discipline_demographic_options[0]["value"]


@callback(
    Output("discipline-category-dropdown", "options"),
    [Input("application-state", "children")],  # dummy input
)
def set_discipline_category_dropdown_options(app_state):
    discipline_category_options = [
        {"label": name, "value": name} for name in discipline_categories
    ]
    return discipline_category_options


# Sets the default value to the first value in discipline category list
@callback(
    Output("discipline-category-dropdown", "value"),
    Input("discipline-category-dropdown", "options"),
)
def set_discipline_category_dropdown_value(discipline_category_options):
    return discipline_category_options[0]["value"]


# Update Discipline Layout
@callback(
    Output("linechart-discipline-layout", "children"),
    Input("discipline-demographic-dropdown", "value"),
    Input("discipline-category-dropdown", "value"),
    Input("year-dropdown", "value"),
    State("charter-dropdown", "value"),
)
def update_discipline_layout(
    discipline_demographic, discipline_category, year_value, school_state
):
    if year_value == None:
        year_value = current_academic_year

    raw_discipline_data = get_discipline_data(school_state)

    discipline_data_clean = clean_discipline_data(
        raw_discipline_data, discipline_demographic, discipline_category, year_value
    )

    processed_discipline_data = process_discipline_data(
        discipline_data_clean, discipline_category, discipline_demographic
    )

    discipline_table = create_discipline_table(processed_discipline_data)

    # a little pre-processing to remove superflous columns
    incidents = discipline_category + "|" + discipline_demographic
    unique_students = discipline_category + " Unique Students|" + discipline_demographic
    discipline_fig_data = raw_discipline_data[["Year", incidents, unique_students]]

    discipline_fig_data.columns = discipline_fig_data.columns.str.replace(
        discipline_category + " Unique Students", "Unique Students", regex=False
    )
    discipline_fig_data.columns = discipline_fig_data.columns.str.replace(
        discipline_category, "Incidents", regex=False
    )

    discipline_fig = make_line_chart(discipline_fig_data)
    discipline_layout = create_line_fig_layout(discipline_table, discipline_fig, "")

    return discipline_layout


@callback(
    Output("update-table", "children"),
    Output("enroll-title", "children"),
    # Output("tst-grid", "children"),
    Output("enroll-table", "children"),
    Output("adm-fig", "figure"),
    Output("linechart-attendance-layout", "children"),
    Output("ethnicity-title", "children"),
    Output("ethnicity-fig", "figure"),
    Output("subgroup-title", "children"),
    Output("subgroup-fig", "figure"),
    Output("about-main-container", "style"),
    Output("about-empty-container", "style"),
    Output("about-no-data", "children"),
    Input("year-dropdown", "value"),
    Input("charter-dropdown", "value"),
)
def update_about_page(year: str, school: str):
    if not school:
        raise PreventUpdate

    selected_year_string = year
    selected_year_numeric = int(selected_year_string)
    previous_year_numeric = selected_year_numeric - 1
    previous_year_string = str(previous_year_numeric)

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]
    selected_school_id = int(selected_school["School ID"].values[0])

    year_title = previous_year_string + "-" + selected_year_string[-2:]
    enroll_title = "Enrollment " + "(" + year_title + ")"
    ethnicity_title = "Enrollment by Ethnicity " + "(" + year_title + ")"
    subgroup_title = "Enrollment by Subgroup " + "(" + year_title + ")"

    update_table = []
    enroll_table = []
    attendance_layout = []

    # use this flag to determine if the selected school is a traditional
    # public school instead of a charter public school- it impacts how
    # we utilize the "Corporation Name" value
    isTradSchool = False

    adm_fig = px.line()
    ethnicity_fig = px.bar()
    subgroup_fig = px.bar()

    main_container = {"display": "none"}
    empty_container = {"display": "block"}
    no_data_to_display = create_empty_page_layout(
        "School Enrollment & Demographics", "No Data to Display"
    )

    # see full color list in globals.py
    linecolor = ["#df8f2d"]

    update_table_label = ""
    update_table_dict = {
        "Date": ["08.16.24", "12.10.24", "12.10.24"],
        "Update": [
            "Added 2024 Chronic Absenteeism.",
            "Added Adult Accountability Metrics (beta).",
            "Added 2019 - 23 Discipline Data.",
        ],
    }

    update_table_df = pd.DataFrame(update_table_dict)

    first_column_width = 15
    update_table = create_key_table(
        update_table_df, update_table_label, first_column_width
    )

    # Get data for enrollment table, and subgroup/ethnicity demographic figs (single year)
    school_demographics_all = get_school_demographic_data(selected_school_id)

    school_demographics = school_demographics_all.loc[
        school_demographics_all["Year"] == selected_year_numeric
    ].copy()

    if len(school_demographics.index) == 0:
        enroll_table = create_empty_table_layout(
            enroll_title, "No Data to Display", "six"
        )
        subgroup_fig = no_data_fig_label("Enrollment by Subgroup", 400)
        ethnicity_fig = no_data_fig_label("Enrollment by Ethnicity", 400)

    else:
        main_container = {"display": "block"}
        empty_container = {"display": "none"}

        # Enrollment table
        corp_id = str(selected_school["GEO Corp"].values[0])

        corp_demographics_all = get_corp_demographic_data(corp_id)

        corp_demographics = corp_demographics_all.loc[
            corp_demographics_all["Year"] == selected_year_numeric
        ].copy()

        # when loading a traditional public school, "Corporation
        # Name" will be the same for both the school and the corp, so
        # we need to replace the school's "Corporation Name" values
        # with the school's "School Name" value
        school_demographics.reset_index(drop=True, inplace=True)
        corp_demographics.reset_index(drop=True, inplace=True)

        if (
            school_demographics["Corporation Name"].values[0]
            == corp_demographics["Corporation Name"].values[0]
        ):
            isTradSchool = True

            school_demographics.loc[0, "Corporation Name"] = school_demographics[
                "School Name"
            ].values[0]

        enrollment_filter = school_demographics.filter(
            regex=r"^Grade \d{1}|[1-9]\d{1}$;|^Pre-K$|^Kindergarten$|^Total Enrollment$",
            axis=1,
        )
        enrollment_filter = enrollment_filter[
            [c for c in enrollment_filter if c not in ["Total Enrollment"]]
            + ["Total Enrollment"]
        ]

        enrollment_filter = enrollment_filter.loc[
            :, (~enrollment_filter.isin([np.nan, 0, "0"])).all()
        ]

        enrollment = enrollment_filter.T
        enrollment.rename(columns={enrollment.columns[0]: "Enrollment"}, inplace=True)
        enrollment.rename(index={"Total Enrollment": "Total"}, inplace=True)

        school_enrollment = enrollment.reset_index()

        # NOTE: Testing Dash-Ag Grid
        # columnTypes = {
        #     "stringColumn": {"filter": False, "editable": False},
        #     "numberColumn": {"filter": False, "editable": False},
        # }

        # columnDefs = [
        #     {"field": "index", "headerName": "", "type": "stringColumn", "resizable": False},
        #     {"field": "Enrollment", "type": "numberColumn", "resizable": False},
        # ]

        # grid = dag.AgGrid(
        #     id="tst-grid",
        #     rowData=school_enrollment.to_dict("records"),
        #     columnDefs=columnDefs,
        #     columnSize="sizeToFit",
        #     dashGridOptions={
        #         'columnTypes': columnTypes,
        #         # "headerHeight": 0,
        #         "animateRows": False,
        #         "domLayout": "autoHeight"
        #     },
        #     style={"width": "100%"}
        # )

        enroll_table = [
            dash_table.DataTable(
                school_enrollment.to_dict("records"),
                columns=[{"name": i, "id": i} for i in school_enrollment.columns],
                style_data={
                    "fontSize": "12px",
                    "fontFamily": "Inter, sans-serif",
                    "border": "none",
                },
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "#eeeeee"},
                    {
                        "if": {
                            "column_id": "index",
                        },
                        "borderRight": ".5px solid #6783a9",
                    },
                    {
                        "if": {"filter_query": "{index} eq 'Total'"},
                        "borderTop": ".5px solid #6783a9",
                    },
                    {
                        "if": {"state": "selected"},
                        "backgroundColor": "rgba(112,128,144, .3)",
                        "border": "thin solid silver",
                    },
                ],
                style_header={
                    "display": "none",
                    "border": "none",
                },
                style_cell={
                    "whiteSpace": "normal",
                    "height": "auto",
                    "textAlign": "center",
                    "color": "#6783a9",
                },
            )
        ]

        # Enrollment by ethnicity fig
        ethnicity_school = school_demographics.loc[
            :,
            (school_demographics.columns.isin(ethnicity))
            | (
                school_demographics.columns.isin(
                    ["Corporation Name", "Total Enrollment"]
                )
            ),
        ]

        if not ethnicity_school.empty:
            ethnicity_corp = corp_demographics.loc[
                :,
                (corp_demographics.columns.isin(ethnicity))
                | (
                    corp_demographics.columns.isin(
                        ["Corporation Name", "Total Enrollment"]
                    )
                ),
            ]

            ethnicity_school = ethnicity_school.rename(
                columns={
                    "Native Hawaiian or Other Pacific Islander": "Pacific Islander"
                }
            )

            ethnicity_corp = ethnicity_corp.rename(
                columns={
                    "Native Hawaiian or Other Pacific Islander": "Pacific Islander"
                }
            )

            ethnicity_data = pd.concat([ethnicity_school, ethnicity_corp])

            ethnicity_fig = make_demographics_bar_chart(ethnicity_data)

        # Enrollment by subgroup fig
        subgroup_school = school_demographics.loc[
            :,
            (school_demographics.columns.isin(subgroup))
            | (
                school_demographics.columns.isin(
                    ["Corporation Name", "Total Enrollment"]
                )
            ),
        ]

        if not subgroup_school.empty:
            subgroup_corp = corp_demographics.loc[
                :,
                (corp_demographics.columns.isin(subgroup))
                | (
                    corp_demographics.columns.isin(
                        ["Corporation Name", "Total Enrollment"]
                    )
                ),
            ]

            subgroup_merged_data = pd.concat([subgroup_school, subgroup_corp])

            subgroup_fig = make_demographics_bar_chart(subgroup_merged_data)

    ## ADM Values ##
    # We don't normally use Quarterly data, however, by Q3 ADM data is known
    # for the year. So we check the first data column and if ADM Avg has data we
    # use it. If there is no financial_data, we use IDOE's adm- get_adm()- file which
    # lags behind. It is typically very accurate for past years, but not as
    # accurate for current years.
    financial_data = get_financial_data(school)

    # adm is calculated at corp level so not available for traditional schools-
    # so we use demographic data (Total Enrollment) as a proxy
    if isTradSchool:
        values = school_demographics_all["Total Enrollment"].astype(float).tolist()

        adm_values = pd.DataFrame(
            [values], columns=school_demographics_all["Year"].tolist()
        )
        adm_values.columns = adm_values.columns.astype(str)

    elif financial_data.empty:
        raw_adm = get_adm_data(int(selected_school["Corporation ID"].values[0]))
        adm_values = clean_adm_data(raw_adm)

    else:
        financial_data = financial_data.drop(["School ID", "School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        available_years = financial_data.columns.difference(
            ["Category"], sort=False
        ).tolist()
        available_years = [int(c[:4]) for c in available_years]

        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year - selected_year_numeric

        if selected_year_numeric < most_recent_finance_year:
            financial_data.drop(
                financial_data.columns[1 : (years_to_exclude + 1)], axis=1, inplace=True
            )

        if len(financial_data.columns) <= 1:
            adm_fig = no_data_fig_label("Average Daily Membership History", 400)

        else:
            # ADM chart
            adm_values = financial_data[
                financial_data["Category"].str.contains("ADM Average")
            ]
            adm_values = adm_values.drop("Category", axis=1)
            adm_values = adm_values.reset_index(drop=True)

            for col in adm_values.columns:
                adm_values[col] = pd.to_numeric(adm_values[col], errors="coerce")

            adm_values = adm_values.loc[:, (adm_values != 0).any(axis=0)]

            adm_values = adm_values[adm_values.columns[::-1]]

    if int(adm_values.sum(axis=1).values[0]) == 0:
        adm_fig = no_data_fig_label("Average Daily Membership History", 400)
        main_container = {"display": "block"}
        empty_container = {"display": "none"}

    else:
        # ADM dataset can be longer than five years (maximum display), so
        # need to filter both the selected year (the year to display) and the
        # total # of years
        operating_years_by_adm = len(adm_values.columns)

        # if number of available years exceeds year_limit, drop excess columns (years)
        if operating_years_by_adm > max_display_years:
            adm_values = adm_values.drop(
                columns=adm_values.columns[
                    : (operating_years_by_adm - max_display_years)
                ],
                axis=1,
            )

        # "excluded years" is a list of YYYY strings (all years more
        # recent than selected year) that can be used to filter data
        # that should not be displayed
        excluded_years = get_excluded_years(selected_year_string)

        # if the display year is less than current year
        # drop columns where year matches any years in "excluded years" list
        # because we are checking against column names this time, we first
        # need to convert the list to strings
        excluded_years = [str(y) for y in excluded_years]

        if excluded_years:
            adm_values = adm_values.loc[
                :, ~adm_values.columns.str.contains("|".join(excluded_years))
            ]

        # strip (Q#) suffix
        adm_values.columns = adm_values.columns.str[:4]

        # turn single row dataframe into two lists (column headers and data)
        adm_data = adm_values.iloc[0].tolist()
        years = adm_values.columns.tolist()

        # create chart
        # NOTE: At some point integrate this into existing charting functions
        adm_fig = px.line(
            x=years,
            y=adm_data,
            markers=True,
            color_discrete_sequence=linecolor,
        )
        adm_fig.update_traces(mode="markers+lines", hovertemplate=None)
        adm_fig["data"][0]["showlegend"] = True
        adm_fig["data"][0]["name"] = "ADM Average"
        adm_fig.update_yaxes(title="", showgrid=True, gridcolor="#b0c4de")
        adm_fig.update_xaxes(ticks="outside", tickcolor="#b0c4de", title="")

        adm_fig.update_layout(
            margin=dict(l=40, r=40, t=40, b=40),
            font=dict(family="Inter, sans-serif", color="#6783a9", size=12),
            hovermode="x unified",
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.45
            ),
        )

    ## Attendance Rate & Chronic Absenteeism
    attendance_rate_data = get_attendance_data(
        selected_school_id, selected_school_type, selected_year_string
    )

    if len(attendance_rate_data.index) > 0 and len(attendance_rate_data.columns) > 1:
        attendance_table = create_simple_table(attendance_rate_data, "Attendance")

        attendance_fig_data = (
            attendance_rate_data.set_index("Category")
            .T.rename_axis("Year")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        attendance_fig = make_line_chart(attendance_fig_data)

    else:
        # bit of a hack - ensures empty containers look the same
        attendance_table = no_data_fig_label()
        attendance_fig = no_data_fig_label()

    # do not display Chronic Absenteeism for AHS - it isn't
    # an accurate representation for the model.
    if selected_school_type == "ahs":
        attendance_title = "Attendance Rate"
    else:
        attendance_title = "Attendance Rate and Chronic Absenteeism"

    attendance_layout = create_line_fig_layout(
        attendance_table, attendance_fig, attendance_title
    )

    return (
        update_table,
        enroll_title,
        # grid,
        enroll_table,
        adm_fig,
        attendance_layout,
        ethnicity_title,
        ethnicity_fig,
        subgroup_title,
        subgroup_fig,
        main_container,
        empty_container,
        no_data_to_display,
    )


def layout():
    return html.Div(
        [
            dcc.Loading(
                id="loading",
                type="circle",
                fullscreen=True,
                style={
                    "position": "absolute",
                    "alignSelf": "center",
                    "backgroundColor": "#F2F2F2",
                },
                children=[
                    html.Div(
                        [
                            html.Div(""),
                            html.Div(
                                id="update-table", children=[]
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label(
                                                id="enroll-title",
                                                className="label__header",
                                            ),
                                            # html.Div(id="tst-grid"),
                                            html.Div(id="enroll-table"),
                                            html.P(""),
                                            html.P(
                                                "Demographic data comes from the DOE-PE (Pupil Enrollment), DOE-LM (Language Minority and Immigrant Students), \
                                                   and DOE-SE (Special Education) reports submitted by schools in October and December. ADM is collected from the \
                                                   DOE-ME (Membership) report, which is now submitted in October (historically September) and February. Due to the \
                                                   differing reporting periods, demographic data and ADM data does not always align.",
                                                style={
                                                    "color": "#6783a9",
                                                    "fontSize": 10,
                                                    "textAlign": "left",
                                                    "marginLeft": "10px",
                                                    "marginRight": "10px",
                                                    "marginTop": "20px",
                                                    "paddingTop": "5px",
                                                    "borderTop": ".5px solid #c9d3e0",
                                                },
                                            ),
                                        ],
                                        className="pretty-container six columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Label(
                                                "Average Daily Membership History",
                                                className="label__header",
                                            ),
                                            dcc.Graph(
                                                id="adm-fig",
                                                figure=loading_fig(),
                                                config={"displayModeBar": False},
                                            ),
                                        ],
                                        className="pretty-container six columns",
                                    ),
                                ],
                                className="bare-container--flex twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label(
                                                id="subgroup-title",
                                                className="label__header",
                                            ),
                                            dcc.Graph(
                                                id="subgroup-fig",
                                                figure=loading_fig(),
                                                config={"displayModeBar": False},
                                            ),
                                        ],
                                        className="pretty-container six columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Label(
                                                id="ethnicity-title",
                                                className="label__header",
                                            ),
                                            dcc.Graph(
                                                id="ethnicity-fig",
                                                figure=loading_fig(),
                                                config={"displayModeBar": False},
                                            ),
                                        ],
                                        className="pretty-container six columns",
                                    ),
                                ],
                                className="bare-container--flex--center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        id="linechart-attendance-layout",
                                        children=[],
                                    ),
                                ],
                                className="pagebreak-after",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label(
                                                "Discipline Data (beta)",
                                                className="label__header",
                                                style={"marginTop": "20px"},
                                            ),
                                        ],
                                        className="bare-container--center twelve columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Label(
                                                                "Select Demographic:"
                                                            ),
                                                        ],
                                                        className="discipline-dropdown-label",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="discipline-demographic-dropdown",
                                                        multi=False,
                                                        clearable=False,
                                                        className="discipline-demographic-dropdown-control",
                                                    ),
                                                ],
                                                className="bare-discipline-container--slim three-half columns",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Label(
                                                                "Select Category:"
                                                            ),
                                                        ],
                                                        className="discipline-dropdown-label",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="discipline-category-dropdown",
                                                        multi=False,
                                                        clearable=False,
                                                        className="discipline-category-dropdown-control",
                                                    ),
                                                ],
                                                className="bare-discipline-container--slim three columns",
                                            ),
                                        ],
                                        className="bare-container--nocenter twelve columns",
                                    ),
                                    html.Div(
                                        id="linechart-discipline-layout",
                                        children=[],
                                    ),
                                ],
                                className="bare-container--center twelve columns",
                            ),
                        ],
                        id="about-main-container",
                    )
                ],
            ),
            html.Div(
                [
                    html.Div(id="about-no-data"),
                ],
                id="about-empty-container",
            ),
        ],
        id="main-container",
    )
