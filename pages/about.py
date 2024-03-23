#######################################
# ICSB Dashboard - About/Demographics #
#######################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     02/21/24

import dash
from dash import dcc, html, dash_table, Input, Output, callback
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import numpy as np

from .globals import (
    ethnicity,
    subgroup,
    max_display_years
)
from .load_data import (
    current_academic_year,
    get_school_index,
    get_financial_data,
    get_corp_demographic_data,
    get_school_demographic_data,
    get_adm,
    get_attendance_data
)
from .charts import loading_fig, no_data_fig_label, make_line_chart, make_demographics_bar_chart
from .tables import no_data_table, no_data_page, create_key_table, create_single_header_table
from .layouts import create_line_fig_layout


dash.register_page(__name__, path="/about", order=0, top_nav=True)

@callback(
    Output("update-table", "children"),
    Output("enroll-title", "children"),
    Output("enroll-table", "children"),
    Output("adm-fig", "figure"),
    Output("attendance-layout", "children"),
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
    attendance_layout= []

    # NOTE: first load of any plotly object is very slow
    adm_fig = px.line()
    ethnicity_fig = px.bar()
    subgroup_fig = px.bar()

    main_container = {"display": "none"}
    empty_container = {"display": "block"}
    no_data_to_display = no_data_page(
        "No Data to Display", "School Enrollment & Demographics"
    )

    # see full color list in charts.py
    linecolor = ["#df8f2d"]

    # Using both school and corp demographic data files because some charter schools
    # share Corp IDs:
    #   Christel House Watanabe Manual High School (school id: 9709) and
    #   Christel House Academy South (school id: 5874) share corp_id: 9380

    # Get data for enrollment table, and subgroup/ethnicity demographic figs (single year)
    # demographic_data = get_corp_demographic_data(school_corp_id)
    demographic_data = get_school_demographic_data(selected_school_id)

    demographic_data = demographic_data.loc[
        demographic_data["Year"] == selected_year_numeric
    ]

    # Updates Table - Right Now hardcoded - may want to add to DB
    update_table_label = ""
    update_table_dict = {
        "Date": [
            "01.26.24",
            "01.31.24",
            "02.03.24",
            "02.05.24",
            "02.10.24",
            "02.11.24",
            "02.14.24",
            "02.20.24"
        ],
        "Update": [
            "Added 2023 IREAD data to Information page.",
            "Added historical Chronic Absenteeism and Attendance data.",
            "Added IREAD breakdowns to Information and Analysis pages.",
            "Added 2023 graduation rate data.",
            "Added student level WIDA and IREAD data to Information page.",
            "Added WIDA to IREAD and IREAD to ILEARN analysis to Information page.",
            "Updated financial data to include 2023 audits when available.",
            "Release version 1.15"
        ],
    }

    update_table_df = pd.DataFrame(update_table_dict)

    first_column_width = 15
    update_table = create_key_table(
        update_table_df, update_table_label, first_column_width
    )

    if len(demographic_data.index) == 0:
        enroll_table = no_data_table("No Data to Display", enroll_title, "six")
        subgroup_fig = no_data_fig_label("Enrollment by Subgroup", 400)
        ethnicity_fig = no_data_fig_label("Enrollment by Ethnicity", 400)

    else:
        main_container = {"display": "block"}
        empty_container = {"display": "none"}

        # Enrollment table
        corp_id = str(selected_school["GEO Corp"].values[0])

        corp_demographics = get_corp_demographic_data(corp_id)
        corp_demographics = corp_demographics.loc[
            corp_demographics["Year"] == selected_year_numeric
        ]

        enrollment_filter = demographic_data.filter(
            regex=r"^Grade \d{1}|[1-9]\d{1}$;|^Pre-K$|^Kindergarten$|^Total Enrollment$",
            axis=1,
        )
        enrollment_filter = enrollment_filter[
            [c for c in enrollment_filter if c not in ["Total Enrollment"]]
            + ["Total Enrollment"]
        ]

        # drop columns with no data
        enrollment_filter = enrollment_filter.loc[:, (~enrollment_filter.isin([np.nan, 0, "0"])).all()]

        enrollment = enrollment_filter.T
        enrollment.rename(columns={enrollment.columns[0]: "Enrollment"}, inplace=True)
        enrollment.rename(index={"Total Enrollment": "Total"}, inplace=True)

        if selected_school_type == "AHS":
            sum = enrollment["Enrollment"].astype(int).sum()
            school_enrollment = pd.DataFrame(columns=["index", "Enrollment"])
            school_enrollment.loc[0] = ["Adults", sum]
            school_enrollment.loc[1] = ["Total", sum]

        else:
            school_enrollment = enrollment.reset_index()

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
        ethnicity_school = demographic_data.loc[
            :,
            (demographic_data.columns.isin(ethnicity))
            | (demographic_data.columns.isin(["Corporation Name", "Total Enrollment"])),
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
        subgroup_school = demographic_data.loc[
            :,
            (demographic_data.columns.isin(subgroup))
            | (demographic_data.columns.isin(["Corporation Name", "Total Enrollment"])),
        ]

        if not subgroup_school.empty:
            subgroup_corp = corp_demographics.loc[
                :,
                (corp_demographics.columns.isin(subgroup))
                | (
                    corp_demographics.columns.isin(
                        ["Corporation Name", "Total Enrollment"]
                    )
                )
            ]

            subgroup_merged_data = pd.concat([subgroup_school, subgroup_corp])

            subgroup_fig = make_demographics_bar_chart(subgroup_merged_data)

    # ADM Values
    # NOTE: Usually we don't use Quarterly data, however, by Q3 ADM data is
    # known for the year. So we check the first data column and if ADM Avg
    # has data we use it. If there is no financial_data, we use IDOE's
    # adm file instead. It usually lags behind the adm average in the financial
    # data table.

    financial_data = get_financial_data(school)

    if financial_data.empty:
        # NOTE: This is a backstop for when there is no financial data or where there are no
        # adm values in financial data ("guest" schools for example). This pulls data from a
        # separate 'adm' table which is typically very accurate for past years, but not as
        # accurate for current years.

        adm_values = get_adm(int(selected_school["Corporation ID"].values[0]))

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

    # file exists, but there is no adm data
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
        excluded_academic_years = current_academic_year - selected_year_numeric

        excluded_years = []

        for i in range(excluded_academic_years):
            excluded_year = current_academic_year - i
            excluded_years.append(str(excluded_year))

        # if the display year is less than current year
        # drop columns where year matches any years in "excluded years" list
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
        )

    ## Attendance Rate & Chronic Absenteeism
    attendance_rate_data = get_attendance_data(
        selected_school_id, selected_school_type, selected_year_string
    )

    if len(attendance_rate_data.index) > 0 and len(attendance_rate_data.columns) > 1:

        attendance_table = create_single_header_table(
            attendance_rate_data, "Attendance"
        )

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
    if selected_school_type == "AHS":
        attendance_title = "Attendance Rate"
    else:
        attendance_title = "Attendance Rate and Chronic Absenteeism"

    attendance_layout = create_line_fig_layout(attendance_table, attendance_fig, attendance_title)

    return (
        update_table,
        enroll_title,
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
                            html.Div(id="update-table", children=[]),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label(
                                                id="enroll-title",
                                                className="label__header",
                                            ),
                                            html.Div(id="enroll-table"),
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
                                        id="attendance-layout",
                                        children=[],
                                    ),
                                ],
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
