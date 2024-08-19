##################################
# ICSB Dashboard - Print Layouts #
##################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     08/18/24

import dash
from dash import dcc, html, dash_table, Input, State, Output, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash.dash_table import FormatTemplate
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


from .globals import ethnicity, subgroup, max_display_years
from .load_data import (
    get_excluded_years,
    get_school_index,
    get_financial_data,
    get_financial_ratios,
    get_corp_demographic_data,
    get_school_demographic_data,
    get_adm,
    get_attendance_data,
    get_discipline_data,
)

from .calculations import round_nearest
from .process_data import process_discipline_data
from .calculate_metrics import calculate_financial_metrics
from .tables import no_data_page, no_data_table, create_financial_analysis_table
from .string_helpers import convert_to_svg_circle

from .charts import (
    loading_fig,
    no_data_fig_label,
    make_line_chart,
    make_demographics_bar_chart,
)
from .tables import (
    no_data_table,
    no_data_page,
    create_key_table,
    create_single_header_table,
)
from .layouts import create_line_fig_layout, create_two_fig_layout


# def create_print_layout(year: str, school_id: str, options: list) -> list:
#     print("Selected")
#     print(options)
#     about_layout = []
#     fininfo_layout = []
#     # all_container = {"display": "none"}
#     # about_container = {"display": "none"}
#     # fininfo_container = {"display": "none"}
#     # finmetrics_container = {"display": "none"}
#     # finanalysis_container = {"display": "none"}
#     # orgcompliance_container = {"display": "none"}
#     # academicinfo_container = {"display": "none"}
#     # academicmetrics_container = {"display": "none"}
#     # empty_container = {"display": "block"}

#     if "all" in options:
#         about_layout = create_about_layout(year, school_id)
#         fininfo_layout = create_fininfo_layout(year, school_id)
#         finmetrics_layout = create_finmetrics_layout(year, school_id)
#         finanalysis_layout = create_finanalysis_layout(year, school_id)
#         orgcompliance_layout = create_orgcompliance_layout(year, school_id)
#         academicinfo_layout = create_academicinfo_layout(year, school_id)
#         academicmetrics_layout = create_academicmetrics_layout(year, school_id)

#     else:
#         if "about" in options:
#             about_layout = create_about_layout(year, school_id)

#         if "fininfo" in options:
#             fininfo_layout = create_fininfo_layout(year, school_id)

#         if "finmetrics" in options:
#             finmetrics_layout = create_finmetrics_layout(year, school_id)

#         if "finanalysis" in options:
#             finanalysis_layout = create_finanalysis_layout(year, school_id)

#         if "orgcompliance" in options:
#             orgcompliance_layout = create_orgcompliance_layout(year, school_id)

#         if "academicinfo" in options:
#             academicinfo_layout = create_academicinfo_layout(year, school_id)

#         if "academicmetrics" in options:
#             academicmetrics_layout = create_academicmetrics_layout(year, school_id)


#     # level_one = print_layout[0]
#     # # print(print_layout[0][0][0])
#     # print(about_layout)

#     return about_layout


def create_about_layout(year: str, school_id: str) -> list:
    about_layout = []

    year_string = year
    year_numeric = int(year)

    selected_school = get_school_index(school_id)
    selected_school_type = selected_school["School Type"].values[0]

    attendance_rate_data = get_attendance_data(
        school_id, selected_school_type, year_string
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
        attendance_table = no_data_fig_label()
        attendance_fig = no_data_fig_label()

    if selected_school_type == "AHS":
        attendance_title = "Attendance Rate"
    else:
        attendance_title = "Attendance Rate and Chronic Absenteeism"

    demographic_data = get_school_demographic_data(school_id)
    demographic_data = demographic_data.loc[demographic_data["Year"] == year_numeric]

    if len(demographic_data.index) == 0:
        subgroup_fig = no_data_fig_label("Enrollment by Subgroup", 400)
        ethnicity_fig = no_data_fig_label("Enrollment by Ethnicity", 400)

    else:
        demographics_title = "Demographic Breakdown"

        corp_id = str(selected_school["GEO Corp"].values[0])
        corp_demographics = get_corp_demographic_data(corp_id)
        corp_demographics = corp_demographics.loc[
            corp_demographics["Year"] == year_numeric
        ]

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
                ),
            ]

            subgroup_merged_data = pd.concat([subgroup_school, subgroup_corp])

            subgroup_fig = make_demographics_bar_chart(subgroup_merged_data)

    about_layout = [
        html.Div(
            [
                html.Label(
                    attendance_title,
                    className="label__header",
                    style={"marginTop": "10px"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(attendance_table, style={"marginTop": "10px"}),
                            ],
                            className="pretty-container six columns",
                        ),
                        html.Div(
                            [
                                html.Div(attendance_fig),
                            ],
                            className="pretty-container six columns",
                        ),
                    ],
                    className="bare-container--flex--center twelve columns",
                ),
            ],
            className="bare-container--relative twelve columns",
        ),
        html.Div(
            [
                html.Label(
                    demographics_title,
                    className="label__header",
                    style={"marginTop": "10px"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Graph(
                                    figure=subgroup_fig,
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="pretty-container six columns",
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    figure=ethnicity_fig,
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="pretty-container six columns",
                        ),
                    ],
                    className="bare-container--flex--center twelve columns",
                ),
            ],
            className="bare-container--relative twelve columns",
        ),
    ]

    return about_layout


# c. Academic Information
def create_academicinfo_layout(year: str, school_id: str) -> list:
    pass
    # return academicinfo_layout


def create_academicmetrics_layout(year: str, school_id: str) -> list:
    pass
    # return academicmetrics_layout


def create_fininfo_layout(year: str, school_id: str) -> list:
    year_string = year
    year_numeric = int(year_string)
    selected_school = get_school_index(school_id)

    # If the selected school is a guest school, load dummy data (Schooly McSchoolface).
    if selected_school["Guest"].values[0] == "Y":
        school = "9999"

    financial_data = get_financial_data(school_id)

    table_title = "Financial Information"

    if len(financial_data.columns) <= 1 or financial_data.empty:
        fininfo_layout = []

    else:
        financial_data = financial_data.drop(["School ID", "School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        available_years = financial_data.columns.difference(
            ["Category"], sort=False
        ).tolist()

        available_years = [int(c[:4]) for c in available_years]
        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year - year_numeric

        if year_numeric < most_recent_finance_year:
            financial_data.drop(
                financial_data.columns[1 : (years_to_exclude + 1)], axis=1, inplace=True
            )

        if len(financial_data.columns) > 1:
            for col in financial_data.columns[1:]:
                financial_data[col] = pd.to_numeric(
                    financial_data[col], errors="coerce"
                )

            financial_data = financial_data.set_index(["Category"])
            financial_data.loc["Total Grants"] = (
                financial_data.loc["State Grants"]
                + financial_data.loc["Federal Grants"]
            )
            financial_data.loc["Net Asset Position"] = (
                financial_data.loc["Total Assets"]
                - financial_data.loc["Total Liabilities"]
            )
            financial_data.loc["Change in Net Assets"] = (
                financial_data.loc["Operating Revenues"]
                - financial_data.loc["Operating Expenses"]
            )

            financial_data = financial_data.reset_index()

            financial_data = financial_data.iloc[:, : (max_display_years + 1)]

            # sort Year cols in ascending order (ignore Category)
            financial_data = (
                financial_data.set_index("Category")
                .sort_index(ascending=True, axis=1)
                .reset_index()
            )

            string_years = financial_data.columns.tolist()
            string_years.pop(0)
            string_years.reverse()

            # remove audit and other indicator data (it is displayed on the financial metrics page)
            financial_data = financial_data.loc[
                : (financial_data["Category"] == "Audit Information").idxmax() - 1
            ]

            ordered_categories = [
                "Revenue",
                "State Grants",
                "Federal Grants",
                "Total Grants",
                "Contributions and Donations",
                "Student Fees",
                "Other Income",
                "Financial Position",
                "Total Assets",
                "Current Assets",
                "Total Liabilities",
                "Current Liabilities",
                "Net Asset Position",
                "Financial Activities",
                "Operating Revenues",
                "Operating Expenses",
                "Change in Net Assets",
                "Supplemental Information",
                "Unrestricted Net Assets",
                "Unrestricted Cash",
                "Principal Payments",
                "Interest Expense",
                "Lease/Mortgage Payments",
                "Depreciation/Amortization",
                "Enrollment Information",
                "September ADM",
                "February ADM",
                "ADM Average",
            ]

            financial_data = financial_data[
                financial_data["Category"].isin(ordered_categories)
            ]

            financial_data = financial_data.dropna(axis=1, how="all")
            financial_data = financial_data.set_index("Category")

            financial_data = financial_data.reindex(index=ordered_categories)
            financial_data = financial_data.reset_index()

            for year in string_years:
                financial_data[year] = pd.Series(
                    ["{:,.0f}".format(val) for val in financial_data[year]],
                    index=financial_data.index,
                )

            financial_data.replace(
                [0, "0", 0.0, "0.0", 0.00, "0.00", "nan", np.nan], "", inplace=True
            )

            year_headers = [i for i in financial_data.columns if i not in ["Category"]]

            table_size = len(financial_data.columns)

            if table_size == 2:
                col_width = "four"
                category_width = 55
            elif table_size == 3:
                col_width = "five"
                category_width = 50
            elif table_size == 4:
                col_width = "six"
                category_width = 40
            elif table_size == 5:
                col_width = "seven"
                category_width = 35
            elif table_size == 6:
                col_width = "eight"
                category_width = 30
            else:
                col_width = "ten"
                category_width = 25

            data_width = 100 - category_width
            year_width = data_width / (table_size - 1)

            pad_right = str(year_width / 3) + "%"

            class_name = "pretty-container " + col_width + " columns"

            fininfo_layout = [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(table_title, className="label__header"),
                                html.Div(
                                    dash_table.DataTable(
                                        financial_data.to_dict("records"),
                                        columns=[
                                            {"name": i, "id": i}
                                            for i in financial_data.columns
                                        ],
                                        style_data={
                                            "fontSize": "12px",
                                            "fontFamily": "Inter, sans-serif",
                                            "border": "none",
                                        },
                                        style_data_conditional=[
                                            {
                                                "if": {"row_index": "odd"},
                                                "backgroundColor": "#eeeeee",
                                            },
                                            {
                                                "if": {
                                                    "filter_query": "{Category} eq 'Revenue' || {Category} eq 'Financial Position' ||{Category} eq 'Financial Activities' || {Category} eq 'Supplemental Information' || {Category} eq 'Enrollment Information' || {Category} eq 'Audit Information'"
                                                },
                                                "paddingLeft": "10px",
                                                "text-decoration": "underline",
                                                "fontWeight": "bold",
                                            },
                                            {
                                                "if": {
                                                    "row_index": 0,
                                                    "column_id": "Category",
                                                },
                                                "borderTop": ".5px solid #6783a9",
                                            },
                                            {
                                                "if": {"state": "selected"},
                                                "backgroundColor": "rgba(112,128,144, .3)",
                                                "border": "thin solid silver",
                                            },
                                        ],
                                        style_header={
                                            "backgroundColor": "#ffffff",
                                            "border": "none",
                                            "borderBottom": ".5px solid #6783a9",
                                            "fontSize": "12px",
                                            "fontFamily": "Inter, sans-serif",
                                            "color": "#6783a9",
                                            "textAlign": "center",
                                            "fontWeight": "bold",
                                        },
                                        style_cell={
                                            "whiteSpace": "normal",
                                            "height": "auto",
                                            "textAlign": "center",
                                            "color": "#6783a9",
                                            "minWidth": "25px",
                                            "width": "25px",
                                            "maxWidth": "25px",
                                        },
                                        style_cell_conditional=[
                                            {
                                                "if": {"column_id": "Category"},
                                                "textAlign": "left",
                                                "fontWeight": "500",
                                                "paddingLeft": "20px",
                                                "width": str(category_width) + "%",
                                            },
                                        ]
                                        + [
                                            {
                                                "if": {"column_id": year},
                                                "textAlign": "right",
                                                "paddingRight": pad_right,
                                                "fontWeight": "500",
                                                "width": str(year_width) + "%",
                                            }
                                            for year in year_headers
                                        ],
                                        style_as_list_view=True,
                                    )
                                ),
                            ],
                            className=class_name,
                        ),
                    ],
                    className="bare-container--flex--center twelve columns",
                )
            ]

    return fininfo_layout


def create_finmetrics_layout(year: str, school_id: str) -> list:
    year_string = year
    year_numeric = int(year_string)
    selected_school = get_school_index(school_id)

    finmetrics_layout = []
    financial_indicators_table = []
    financial_metrics_table = []

    table_title = "Financial Accountability Metrics"

    financial_data = get_financial_data(school_id)

    # Financial Metrics
    if len(financial_data.columns) > 1 or ~financial_data.empty:
        financial_data = financial_data.drop(["School ID", "School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        available_years = financial_data.columns.difference(
            ["Category"], sort=False
        ).tolist()

        available_years = [int(c[:4]) for c in available_years]
        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year - year_numeric

        if year_numeric < most_recent_finance_year:
            financial_data.drop(
                financial_data.columns[1 : (years_to_exclude + 1)], axis=1, inplace=True
            )

        if (len(financial_data.columns) > 1) | (
            (len(financial_data.columns) == 2) and (financial_data.iloc[1][1] != "0")
        ):
            financial_data = (
                financial_data.set_index("Category")
                .sort_index(ascending=True, axis=1)
                .reset_index()
            )

            financial_indicators = financial_data[
                financial_data["Category"].str.startswith("2.1.")
            ].copy()

            financial_quarter = ""
            financial_quarter = (
                financial_data.columns[-1][5:]
                if len(financial_data.columns[-1]) > 4
                else ""
            )
            financial_data = financial_data.rename(
                columns=lambda x: str(x)[:4] if x != "Category" else x
            )

            for col in financial_data.columns:
                financial_data[col] = (
                    pd.to_numeric(financial_data[col], errors="coerce")
                    .fillna(financial_data[col])
                    .tolist()
                )

            financial_data = financial_data.set_index(["Category"])
            financial_data.loc["Total Grants"] = (
                financial_data.loc["State Grants"]
                + financial_data.loc["Federal Grants"]
            )
            financial_data.loc["Net Asset Position"] = (
                financial_data.loc["Total Assets"]
                - financial_data.loc["Total Liabilities"]
            )
            financial_data.loc["Change in Net Assets"] = (
                financial_data.loc["Operating Revenues"]
                - financial_data.loc["Operating Expenses"]
            )
            financial_data = financial_data.reset_index()

            for c in financial_data.columns:
                if len(financial_data[financial_data[c] == 0].index) > 31:
                    financial_data.drop([c], inplace=True, axis=1)

            financial_values = financial_data.loc[
                : (financial_data["Category"] == "Audit Information").idxmax() - 1
            ]

            financial_metrics = calculate_financial_metrics(financial_values)

            if len(financial_metrics.columns) != 0:
                metric_display_years = max_display_years * 2

                tmp_metric = financial_metrics["Metric"]
                financial_metrics = financial_metrics.drop("Metric", axis=1)

                if len(financial_metrics.columns) < metric_display_years:
                    metric_display_years = len(financial_metrics.columns)

                financial_metrics = financial_metrics.iloc[:, -metric_display_years:]

                financial_metrics.insert(loc=0, column="Metric", value=tmp_metric)

                financial_metrics = convert_to_svg_circle(financial_metrics)

                financial_metrics = financial_metrics.fillna("")

                for x in range(1, len(financial_metrics.columns), 2):
                    if financial_metrics.iat[3, x]:
                        financial_metrics.iat[3, x] = "{:.0%}".format(
                            financial_metrics.iat[3, x]
                        )
                    if financial_metrics.iat[9, x]:
                        financial_metrics.iat[9, x] = "{:,.2f}".format(
                            financial_metrics.iat[9, x]
                        )
                    if financial_metrics.iat[10, x]:
                        financial_metrics.iat[10, x] = "{:,.2f}".format(
                            financial_metrics.iat[10, x]
                        )

                if financial_quarter:
                    financial_metrics.columns.values[-2] = (
                        financial_metrics.columns.values[-2] + " " + financial_quarter
                    )

                headers = financial_metrics.columns.tolist()

                clean_headers = ["Rate" if "Rating" in c else c for c in headers]
                year_headers = [
                    i for i in headers if "Rating" not in i and "Metric" not in i
                ]
                rating_headers = [y for y in headers if "Rating" in y]

                table_size = len(financial_metrics.columns)

                if table_size <= 3:
                    col_width = "four"
                    category_width = 70
                elif table_size > 3 and table_size <= 4:
                    col_width = "six"
                    category_width = 35
                elif table_size >= 5 and table_size <= 8:
                    col_width = "seven"
                    category_width = 30
                elif table_size == 9:
                    col_width = "eight"
                    category_width = 25
                elif table_size >= 10:
                    col_width = "nine"
                    category_width = 20

                data_width = 100 - category_width
                data_col_width = data_width / (table_size - 1)
                rating_width = year_width = data_col_width
                rating_width = rating_width / 2

                class_name = "pretty-container " + col_width + " columns"

                print(class_name)
                financial_metrics_table = [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(table_title, className="label__header"),
                                    html.Div(
                                        dash_table.DataTable(
                                            financial_metrics.to_dict("records"),
                                            columns=[
                                                {
                                                    "name": col,
                                                    "id": headers[idx],
                                                    "presentation": "markdown",
                                                }
                                                if "Rate" in col
                                                else {"name": col, "id": headers[idx]}
                                                for (idx, col) in enumerate(
                                                    clean_headers
                                                )
                                            ],
                                            style_data={
                                                "fontSize": "12px",
                                                "border": "none",
                                                "fontFamily": "Inter, sans-serif",
                                            },
                                            style_data_conditional=[
                                                {
                                                    "if": {"row_index": "odd"},
                                                    "backgroundColor": "#eeeeee",
                                                },
                                                {
                                                    "if": {
                                                        "filter_query": "{Metric} eq 'Near Term' || {Metric} eq 'Long Term' || {Metric} eq 'Other Metrics'"
                                                    },
                                                    "paddingLeft": "10px",
                                                    "text-decoration": "underline",
                                                    "fontWeight": "bold",
                                                },
                                                {
                                                    "if": {"state": "selected"},
                                                    "backgroundColor": "rgba(112,128,144, .3)",
                                                    "border": "thin solid silver",
                                                },
                                            ],
                                            style_header={
                                                "height": "20px",
                                                "backgroundColor": "#ffffff",
                                                "border": "none",
                                                "borderBottom": ".5px solid #6783a9",
                                                "fontSize": "12px",
                                                "fontFamily": "Inter, sans-serif",
                                                "color": "#6783a9",
                                                "textAlign": "center",
                                                "fontWeight": "bold",
                                            },
                                            style_cell={
                                                "whiteSpace": "normal",
                                                "height": "auto",
                                                "textAlign": "center",
                                                "color": "#6783a9",
                                                "boxShadow": "0 0",
                                                "minWidth": "25px",
                                                "width": "25px",
                                                "maxWidth": "25px",
                                            },
                                            style_cell_conditional=[
                                                {
                                                    "if": {"column_id": "Metric"},
                                                    "textAlign": "left",
                                                    "paddingLeft": "20px",
                                                    "fontWeight": "500",
                                                    "width": str(category_width) + "%",
                                                },
                                            ]
                                            + [
                                                {
                                                    "if": {"column_id": year},
                                                    "textAlign": "center",
                                                    "fontWeight": "500",
                                                    "width": str(year_width) + "%",
                                                }
                                                for year in year_headers
                                            ]
                                            + [
                                                {
                                                    "if": {"column_id": rating},
                                                    "textAlign": "center",
                                                    "fontWeight": "500",
                                                    "width": str(rating_width) + "%",
                                                }
                                                for rating in rating_headers
                                            ],
                                            style_as_list_view=True,
                                            markdown_options={"html": True},
                                        )
                                    ),
                                ],
                                className=class_name,
                            ),
                        ],
                        className="bare-container--flex--center twelve columns",
                    )
                ]

            # Financial Indicators
            if len(financial_indicators.columns) > 1 or ~financial_indicators.empty:
                financial_indicators = financial_indicators.set_index(["Category"])

                indicator_display_years = max_display_years

                if len(financial_indicators.columns) < max_display_years:
                    indicator_display_years = len(financial_indicators.columns)

                financial_indicators = financial_indicators.iloc[
                    :, -indicator_display_years:
                ]
                financial_indicators = financial_indicators.reset_index()

                financial_indicators[["Standard", "Description"]] = (
                    financial_indicators["Category"].str.split("|", expand=True).copy()
                )
                financial_indicators = financial_indicators.drop(["Category"], axis=1)

                standard = financial_indicators["Standard"]
                description = financial_indicators["Description"]
                financial_indicators = financial_indicators.drop(
                    columns=["Standard", "Description"]
                )
                financial_indicators.insert(
                    loc=0, column="Description", value=description
                )
                financial_indicators.insert(loc=0, column="Standard", value=standard)

                financial_indicators = convert_to_svg_circle(financial_indicators)

                headers = financial_indicators.columns.tolist()
                year_headers = [
                    x for x in headers if "Description" not in x and "Standard" not in x
                ]

                financial_indicators_table = [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(
                                        "Other Financial Accountability Indicators",
                                        className="label__header",
                                    ),
                                    html.Div(
                                        dash_table.DataTable(
                                            financial_indicators.to_dict("records"),
                                            columns=[
                                                {
                                                    "name": col,
                                                    "id": headers[idx],
                                                    "presentation": "markdown",
                                                }
                                                if col in year_headers
                                                else {"name": col, "id": headers[idx]}
                                                for (idx, col) in enumerate(headers)
                                            ],
                                            style_data={
                                                "fontSize": "12px",
                                                "fontFamily": "Inter, sans-serif",
                                                "border": "none",
                                            },
                                            style_data_conditional=[
                                                {
                                                    "if": {"row_index": "odd"},
                                                    "backgroundColor": "#eeeeee",
                                                }
                                            ]
                                            + [
                                                {
                                                    "if": {"state": "selected"},
                                                    "backgroundColor": "rgba(112,128,144, .3)",
                                                    "border": "thin solid silver",
                                                }
                                            ]
                                            + [
                                                {
                                                    "if": {"column_id": year},
                                                    "textAlign": "center",
                                                    "fontWeight": "500",
                                                    "width": "8%",
                                                }
                                                for year in year_headers
                                            ],
                                            style_header={
                                                "height": "20px",
                                                "backgroundColor": "#ffffff",
                                                "border": "none",
                                                "borderBottom": ".5px solid #6783a9",
                                                "fontSize": "12px",
                                                "fontFamily": "Inter, sans-serif",
                                                "color": "#6783a9",
                                                "textAlign": "center",
                                                "fontWeight": "bold",
                                            },
                                            style_cell={
                                                "whiteSpace": "normal",
                                                "height": "auto",
                                                "textAlign": "center",
                                                "color": "#6783a9",
                                            },
                                            style_cell_conditional=[
                                                {
                                                    "if": {"column_id": "Standard"},
                                                    "textAlign": "center",
                                                    "fontWeight": "500",
                                                    "width": "7%",
                                                },
                                                {
                                                    "if": {"column_id": "Description"},
                                                    "width": "45%",
                                                    "textAlign": "Left",
                                                    "fontWeight": "500",
                                                    "paddingLeft": "20px",
                                                },
                                            ],
                                            markdown_options={"html": True},
                                        ),
                                    ),
                                ],
                                className="pretty-container eight columns",
                            ),
                        ],
                        className="bare-container--flex--center twelve columns",
                    )
                ]

    finmetrics_layout = [
        html.Div(
            [
                html.Div(financial_metrics_table),
                html.Div(financial_indicators_table),
            ]
        )
    ]

    return finmetrics_layout


def create_finanalysis_layout(year: str, school_id: str) -> list:
    year_string = year
    year_numeric = int(year_string)
    previous_year_numeric = year_numeric - 1

    selected_school = get_school_index(school_id)
    display_years = [str(previous_year_numeric)] + [year]

    financial_position_table = []  # type: list
    financial_activities_table = []  # type: list
    financial_ratios_table = []  # type: list
    per_student_table = []  # type: list
    revenue_expenses_fig = go.Figure()
    assets_liabilities_fig = go.Figure()

    RandE_title = "Revenue and Expenses"
    AandL_title = "Assets and Liabilities"
    FP_title = "2-Year Financial Position"
    FA_title = "2-Year Financial Activities"

    if selected_school["Guest"].values[0] == "Y":
        school = "9999"

    financial_data = get_financial_data(school)

    if len(financial_data.columns) > 1 or ~financial_data.empty:
        financial_data = financial_data.drop(["School ID", "School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        if "Q" in financial_data.columns[1]:
            financial_data = financial_data.drop(financial_data.columns[[1]], axis=1)

        available_years = financial_data.columns.difference(
            ["Category"], sort=False
        ).tolist()
        available_years = [int(c[:4]) for c in available_years]
        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year - year_numeric

        if year_numeric < most_recent_finance_year:
            financial_data.drop(
                financial_data.columns[1 : (years_to_exclude + 1)], axis=1, inplace=True
            )

        if len(financial_data.columns) > 1:
            color = ["#74a2d7", "#df8f2d"]

            for col in financial_data.columns:
                financial_data[col] = (
                    pd.to_numeric(financial_data[col], errors="coerce")
                    .fillna(financial_data[col])
                    .tolist()
                )

            financial_data = financial_data.set_index(["Category"])
            financial_data.loc["Total Grants"] = (
                financial_data.loc["State Grants"]
                + financial_data.loc["Federal Grants"]
            )
            financial_data.loc["Net Asset Position"] = (
                financial_data.loc["Total Assets"]
                - financial_data.loc["Total Liabilities"]
            )
            financial_data.loc["Change in Net Assets"] = (
                financial_data.loc["Operating Revenues"]
                - financial_data.loc["Operating Expenses"]
            )
            financial_data = financial_data.reset_index()

            financial_data = financial_data.iloc[:, : (max_display_years + 1)]

            financial_data_fig = financial_data.copy()

            for c in financial_data_fig.columns:
                if len(financial_data_fig[financial_data_fig[c] == 0].index) > 31:
                    financial_data_fig.drop([c], inplace=True, axis=1)

            string_fig_years = financial_data_fig.columns.tolist()
            string_fig_years.pop(0)
            string_fig_years.reverse()

            ## Fig 1: Operating Revenue, Operating Expenses, & Change in
            # Net Assets
            revenue_expenses_data = financial_data_fig[
                financial_data_fig["Category"].isin(
                    ["Operating Expenses", "Operating Revenues"]
                )
            ]
            revenue_expenses_data = revenue_expenses_data.reset_index(drop=True)

            for col in revenue_expenses_data.columns:
                revenue_expenses_data[col] = (
                    pd.to_numeric(revenue_expenses_data[col], errors="coerce")
                    .fillna(revenue_expenses_data[col])
                    .tolist()
                )

            revenue_expenses_data = revenue_expenses_data.iloc[:, ::-1]
            revenue_expenses_data.insert(
                0, "Category", revenue_expenses_data.pop("Category")
            )

            revenue_expenses_data = revenue_expenses_data.set_index("Category").T

            revenue_expenses_bar_fig = px.bar(
                data_frame=revenue_expenses_data,
                x=string_fig_years,
                y=[c for c in revenue_expenses_data.columns],
                color_discrete_sequence=color,
                barmode="group",
            )

            step = 6

            tick_val = round_nearest(revenue_expenses_data, step)

            revenue_expenses_bar_fig.update_xaxes(
                showline=False,
                linecolor="#a9a9a9",
                ticks="outside",
                tickcolor="#a9a9a9",
                title="",
            )
            revenue_expenses_bar_fig.update_yaxes(
                showgrid=True,
                gridcolor="#a9a9a9",
                title="",
                tickmode="linear",
                tick0=0,
                dtick=tick_val,
            )

            revenue_expenses_bar_fig.update_layout(
                margin=dict(l=40, r=40, t=40, b=60),
                font=dict(family="Inter, sans-serif", color="#6783a9", size=12),
                hovermode="x unified",
                showlegend=True,
                height=400,
                legend=dict(orientation="h", title="", traceorder="reversed"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            revenue_expenses_bar_fig["data"][0][
                "hovertemplate"
            ] = "Operating Revenues<br>$ %{y:,.2f}<extra></extra>"
            revenue_expenses_bar_fig["data"][1][
                "hovertemplate"
            ] = "Operating Expenses<br>$ %{y:,.2f}<extra></extra>"

            revenue_expenses_line_data = financial_data_fig[
                financial_data_fig["Category"].isin(["Change in Net Assets"])
            ]
            revenue_expenses_line_data = revenue_expenses_line_data.reset_index(
                drop=True
            )

            revenue_expenses_line_data = revenue_expenses_line_data.replace(
                "", 0, regex=True
            )

            cols = [
                i for i in revenue_expenses_line_data.columns if i not in ["Category"]
            ]

            for col in cols:
                revenue_expenses_line_data[col] = pd.to_numeric(
                    revenue_expenses_line_data[col], errors="coerce"
                )

            revenue_expenses_line_data = revenue_expenses_line_data.iloc[:, ::-1]
            revenue_expenses_line_data.pop("Category")
            revenue_expenses_line_data = (
                revenue_expenses_line_data.loc[:, :].values.flatten().tolist()
            )

            revenue_expenses_line_fig = px.line(
                x=string_fig_years,
                y=revenue_expenses_line_data,
                markers=True,
                color_discrete_sequence=["#75851b"],
            )

            revenue_expenses_fig = go.Figure(
                data=revenue_expenses_line_fig.data + revenue_expenses_bar_fig.data,
                layout=revenue_expenses_bar_fig.layout,
            )
            revenue_expenses_fig["data"][0]["showlegend"] = True
            revenue_expenses_fig["data"][0]["name"] = "Change in Net Assets"
            revenue_expenses_fig["data"][0][
                "hovertemplate"
            ] = "Change in Net Assets<br>$ %{y:,.2f}<extra></extra>"

            ## Fig 2: Assets + Liabilities per year bars and Net Asset Position as Line
            assets_liabilities_data = financial_data_fig[
                financial_data_fig["Category"].isin(
                    ["Total Assets", "Total Liabilities"]
                )
            ]
            assets_liabilities_data = assets_liabilities_data.reset_index(drop=True)

            assets_liabilities_data = assets_liabilities_data.replace("", 0, regex=True)

            cols = [i for i in assets_liabilities_data.columns if i not in ["Category"]]

            for col in cols:
                assets_liabilities_data[col] = pd.to_numeric(
                    assets_liabilities_data[col], errors="coerce"
                )

            assets_liabilities_data = assets_liabilities_data.iloc[:, ::-1]
            assets_liabilities_data.insert(
                0, "Category", assets_liabilities_data.pop("Category")
            )

            assets_liabilities_data = assets_liabilities_data.set_index("Category").T

            assets_liabilities_bar_fig = px.bar(
                data_frame=assets_liabilities_data,
                x=string_fig_years,
                y=[c for c in assets_liabilities_data.columns],
                color_discrete_sequence=color,
                barmode="group",
            )

            tick_val = round_nearest(assets_liabilities_data, step)

            assets_liabilities_bar_fig.update_xaxes(
                showline=False,
                linecolor="#a9a9a9",
                ticks="outside",
                tickcolor="#a9a9a9",
                title="",
            )
            assets_liabilities_bar_fig.update_yaxes(
                showgrid=True,
                gridcolor="#a9a9a9",
                title="",
                tickmode="linear",
                tick0=0,
                dtick=tick_val,
            )

            assets_liabilities_bar_fig.update_layout(
                margin=dict(l=40, r=40, t=40, b=60),
                font=dict(family="Inter, sans-serif", color="#6783a9", size=12),
                hovermode="x unified",
                legend=dict(orientation="h", title="", traceorder="reversed"),
                height=400,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            assets_liabilities_bar_fig["data"][1][
                "hovertemplate"
            ] = "Total Liabilities<br>$ %{y:,.2f}<extra></extra>"
            assets_liabilities_bar_fig["data"][0][
                "hovertemplate"
            ] = "Total Assets<br>$ %{y:,.2f}<extra></extra>"

            assets_liabilities_line_data = financial_data_fig.iloc[10].tolist()
            assets_liabilities_line_data.pop(0)
            assets_liabilities_line_data.reverse()

            assets_liabilities_line_fig = px.line(
                x=string_fig_years,
                y=assets_liabilities_line_data,
                markers=True,
                color_discrete_sequence=["#75851b"],
            )

            assets_liabilities_fig = go.Figure(
                data=assets_liabilities_line_fig.data + assets_liabilities_bar_fig.data,
                layout=assets_liabilities_bar_fig.layout,
            )

            assets_liabilities_fig["data"][0]["showlegend"] = True
            assets_liabilities_fig["data"][0]["name"] = "Net Asset Position"
            assets_liabilities_fig["data"][0][
                "hovertemplate"
            ] = "Net Asset Position<br>$ %{y:,.2f}<extra></extra>"

            ## Two Year Finance Tables (Financial Position and Financial Activities)
            default_headers = ["Category"] + display_years

            idx1 = financial_data.index[
                financial_data["Category"] == "ADM Average"
            ].values[0]
            idx2 = financial_data.index[
                financial_data["Category"] == "State Grants"
            ].values[0]

            financial_data = financial_data.loc[
                :, ~((financial_data.loc[idx1] == 0) | (financial_data.loc[idx2] == 0))
            ]

            if set(default_headers).issubset(set(financial_data.columns)):
                financial_data = financial_data[default_headers]

            else:
                missing_year = list(
                    set(default_headers).difference(financial_data.columns)
                )
                remaining_year = [
                    e for e in default_headers if e not in ("Category", missing_year[0])
                ]
                i = 1 if (int(missing_year[0]) < int(remaining_year[0])) else 0

                financial_data.insert(loc=i, column=missing_year[0], value=0)
                financial_data = financial_data[default_headers]

            financial_data = (
                financial_data.set_index("Category")
                .sort_index(ascending=True, axis=1)
                .reset_index()
            )

            # Table 1: 2-Year Financial Position
            financial_position_categories = [
                "Total Assets",
                "Current Assets",
                "Total Liabilities",
                "Current Liabilities",
                "Net Asset Position",
            ]
            financial_position_table = create_financial_analysis_table(
                financial_data, financial_position_categories
            )

            # Table 2: 2-Year Financial Activities
            financial_activity_categories = [
                "Operating Revenues",
                "Operating Expenses",
                "Change in Net Assets",
            ]
            financial_activities_table = create_financial_analysis_table(
                financial_data, financial_activity_categories
            )

            # Table #3: Per-Student Expenditures
            per_student_categories = [
                "State Grants",
                "Operating Revenues",
                "Operating Expenses",
                "Change in Net Assets",
                "ADM Average",
            ]
            per_student_table = create_financial_analysis_table(
                financial_data, per_student_categories
            )

            # Table 4: Financial Ratios
            school_corp = int(selected_school["Corporation ID"].values[0])
            financial_ratios_data = get_financial_ratios(school_corp)
            ratio_years = financial_ratios_data["Year"].astype(str).tolist()

            if (
                len(financial_ratios_data.index) > 0 and
                set(ratio_years).isdisjoint(default_headers)
            ):

                financial_ratios_data = financial_ratios_data.drop(
                    columns=["Corporation Name", "Corporation ID", "School ID"]
                )
                financial_ratios_data = (
                    financial_ratios_data.set_index("Year")
                    .T.rename_axis("Category")
                    .rename_axis(None, axis=1)
                    .reset_index()
                )

                financial_ratios_data.columns = financial_ratios_data.columns.astype(
                    str
                )

                for col in financial_ratios_data.columns[1:]:
                    financial_ratios_data[col] = pd.to_numeric(
                        financial_ratios_data[col], errors="coerce"
                    )

                default_df = pd.DataFrame(columns=default_headers)

                default_df["Category"] = financial_ratios_data["Category"]

                non_duplicate_cols = ["Category"] + [
                    i
                    for i in default_df.columns.to_list()
                    if i not in financial_ratios_data.columns.to_list()
                ]

                final_ratios_data = default_df.combine_first(
                    default_df[non_duplicate_cols].merge(financial_ratios_data, "left")
                )
                final_ratios_data = final_ratios_data[default_headers]

                final_ratios_data = final_ratios_data.fillna("N/A")

                for year in display_years:
                    if (final_ratios_data[year] != "N/A").any():
                        final_ratios_data[year] = pd.Series(
                            [
                                "{0:.2f}%".format(val * 100)
                                for val in final_ratios_data[year]
                            ],
                            index=final_ratios_data.index,
                        )

                financial_ratios_table = [
                    html.Label("Financial Ratios", className="label__header"),
                    html.P(""),
                    html.Div(
                        dash_table.DataTable(
                            data=final_ratios_data.to_dict("records"),
                            columns=[
                                {
                                    "name": i,
                                    "id": i,
                                    "type": "numeric",
                                    "format": FormatTemplate.percentage(2),
                                }
                                for i in final_ratios_data.columns
                            ],
                            style_data={
                                "fontSize": "11px",
                                "fontFamily": "Inter, sans-serif",
                            },
                            style_data_conditional=[
                                {
                                    "if": {
                                        "column_id": "Category",
                                    },
                                    "borderRight": ".5px solid #6783a9",
                                    "fontWeight": "600",
                                    "fontSize": "11px",
                                },
                                {
                                    "if": {
                                        "filter_query": "{Category} eq 'Occupancy Ratio'"
                                    },
                                    "borderTop": ".5px solid #6783a9",
                                },
                                {
                                    "if": {"state": "selected"},
                                    "backgroundColor": "rgba(112,128,144, .3)",
                                    "border": "thin solid silver",
                                },
                            ],
                            style_header={
                                "height": "20px",
                                "backgroundColor": "#ffffff",
                                "borderBottom": ".5px solid #6783a9",
                                "borderTop": "none",
                                "borderRight": "none",
                                "borderLeft": "none",
                                "fontSize": "12px",
                                "fontFamily": "Montserrat, sans-serif",
                                "color": "#6783a9",
                                "textAlign": "center",
                                "fontWeight": "bold",
                            },
                            style_header_conditional=[
                                {
                                    "if": {
                                        "column_id": "Category",
                                    },
                                    "borderRight": ".5px solid #6783a9",
                                    "borderBottom": ".5px solid #6783a9",
                                    "textAlign": "left",
                                },
                            ],
                            style_cell={
                                "border": "none",
                                "whiteSpace": "normal",
                                "height": "auto",
                                "textAlign": "center",
                                "color": "#6783a9",
                                "minWidth": "25px",
                                "width": "25px",
                                "maxWidth": "25px",
                            },
                            style_cell_conditional=[
                                {
                                    "if": {"column_id": "Category"},
                                    "textAlign": "left",
                                    "paddingLeft": "20px",
                                    "width": "40%",
                                }
                            ],
                        )
                    ),
                ]

    finanalysis_layout = [
        html.Div(
            [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label(RandE_title,
                                            className="label__header",
                                        ),
                                        dcc.Graph(
                                            figure=revenue_expenses_fig,
                                            config={
                                                "displayModeBar": False
                                            },
                                        ),
                                    ],
                                    className="pretty-container six columns",
                                ),
                                html.Div(
                                    [
                                        html.Label(
                                            AandL_title,
                                            className="label__header",
                                        ),
                                        dcc.Graph(
                                            figure=assets_liabilities_fig,
                                            config={
                                                "displayModeBar": False
                                            },
                                        ),
                                    ],
                                    className="pretty-container six columns",
                                ),
                            ],
                            className="bare-container--flex--nocenter twelve columns",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label(
                                            FP_title,
                                            className="label__header",
                                        ),
                                        html.P(""),
                                        html.Div(financial_position_table),
                                    ],
                                    className="pretty-container--left six columns",
                                ),
                                html.Div(
                                    [
                                        html.Label(
                                            FA_title,
                                            className="label__header",
                                        ),
                                        html.P(""),
                                        html.Div(financial_activities_table),
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
                                        html.Div(financial_ratios_table

                                            # children=[],
                                        ),
                                    ],
                                    className="pretty-container--left six columns",
                                ),
                                html.Div(
                                    [
                                        html.Label(
                                            "Revenues and Expenditures Per Student",
                                            className="label__header",
                                        ),
                                        html.P(""),
                                        html.Div(per_student_table),
                                    ],
                                    className="pretty-container six columns",
                                ),
                            ],
                            className="bare-container--flex twelve columns",
                        ),

            ],
        ),
    ]

    return finanalysis_layout


def create_orgcompliance_layout(year: str, school_id: str) -> list:
    selected_school = get_school_index(school_id)
    year_numeric = int(year)
    year_string = str(year_numeric)

    orgcompliance_layout = []

    if selected_school["Guest"].values[0] == "Y":
        school_id = "9999"

    financial_data = get_financial_data(school_id)

    if len(financial_data.columns) > 1 or ~financial_data.empty:
        if selected_school["Guest"].values[0] == "Y":
            table_title = "Organizational and Operational Accountability (SAMPLE DATA)"
        else:
            table_title = "Organizational and Operational Accountability"

        financial_data = financial_data.drop(["School ID", "School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        if "Q" in financial_data.columns[1]:
            if "Q4" in financial_data.columns[1]:
                financial_data = financial_data.rename(
                    columns={
                        c: c[:4]
                        for c in financial_data.columns
                        if c not in ["Category"]
                    }
                )

            else:
                financial_data = financial_data.drop(
                    financial_data.columns[[1]], axis=1
                )

        available_years = financial_data.columns.difference(
            ["Category"], sort=False
        ).tolist()
        available_years = [int(c[:4]) for c in available_years]
        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year - year_numeric

        if year_numeric < most_recent_finance_year:
            financial_data.drop(
                financial_data.columns[1 : (years_to_exclude + 1)], axis=1, inplace=True
            )

        if len(financial_data.columns) > 1:
            financial_data = financial_data.iloc[:, : (max_display_years + 1)]

            financial_data = (
                financial_data.set_index("Category")
                .sort_index(ascending=True, axis=1)
                .reset_index()
            )

            organizational_indicators = financial_data[
                financial_data["Category"].str.startswith("3.")
            ].copy()
            organizational_indicators[
                ["Standard", "Description"]
            ] = organizational_indicators["Category"].str.split("|", expand=True)

            organizational_indicators = organizational_indicators.drop(
                "Category", axis=1
            )
            standard = organizational_indicators["Standard"]
            description = organizational_indicators["Description"]
            organizational_indicators = organizational_indicators.drop(
                columns=["Standard", "Description"]
            )
            organizational_indicators.insert(
                loc=0, column="Description", value=description
            )
            organizational_indicators.insert(loc=0, column="Standard", value=standard)

            organizational_indicators = convert_to_svg_circle(organizational_indicators)

            headers = organizational_indicators.columns.tolist()
            year_headers = [
                x for x in headers if "Description" not in x and "Standard" not in x
            ]

            orgcompliance_layout = [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(table_title, className="label__header"),
                                dash_table.DataTable(
                                    organizational_indicators.to_dict("records"),
                                    columns=[
                                        {"name": i, "id": i, "presentation": "markdown"}
                                        if i in year_headers
                                        else {
                                            "name": i,
                                            "id": i,
                                        }
                                        for i in headers
                                    ],
                                    style_data={
                                        "fontSize": "12px",
                                        "border": "none",
                                        "fontFamily": "Inter, sans-serif",
                                    },
                                    style_data_conditional=[
                                        {
                                            "if": {"row_index": "odd"},
                                            "backgroundColor": "#eeeeee",
                                        }
                                    ]
                                    + [
                                        {
                                            "if": {"state": "selected"},
                                            "backgroundColor": "rgba(112,128,144, .3)",
                                            "border": "thin solid silver",
                                        }
                                    ]
                                    + [
                                        {
                                            "if": {"column_id": year},
                                            "textAlign": "center",
                                            "fontWeight": "500",
                                            "width": "5%",
                                        }
                                        for year in year_headers
                                    ],
                                    style_header={
                                        "height": "20px",
                                        "backgroundColor": "#ffffff",
                                        "border": "none",
                                        "borderBottom": ".5px solid #6783a9",
                                        "fontSize": "12px",
                                        "fontFamily": "Montserrat, sans-serif",
                                        "color": "#6783a9",
                                        "textAlign": "center",
                                        "fontWeight": "bold",
                                    },
                                    style_cell={
                                        "whiteSpace": "normal",
                                        "height": "auto",
                                        "textAlign": "center",
                                        "color": "#6783a9",
                                        "minWidth": "25px",
                                        "width": "25px",
                                        "maxWidth": "25px",
                                    },
                                    style_cell_conditional=[
                                        {
                                            "if": {"column_id": "Standard"},
                                            "textAlign": "Center",
                                            "fontWeight": "500",
                                            "width": "7%",
                                        },
                                        {
                                            "if": {"column_id": "Description"},
                                            "width": "50%",
                                            "textAlign": "Left",
                                            "fontWeight": "500",
                                        },
                                    ],
                                    markdown_options={"html": True},
                                ),
                            ],
                            className="pretty-container ten columns",
                        ),
                    ],
                    className="bare-container--flex--center twelve columns",
                ),
            ]

    return orgcompliance_layout
