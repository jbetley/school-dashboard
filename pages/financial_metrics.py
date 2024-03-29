######################################
# ICSB Dashboard - Financial Metrics #
######################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     03/25/24

import dash
from dash import html, dash_table, Input, State, Output, callback
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd

from .globals import max_display_years
from .load_data import get_school_index, get_financial_data
from .calculate_metrics import calculate_financial_metrics
from .tables import no_data_page, no_data_table, create_proficiency_key
from .string_helpers import convert_to_svg_circle

dash.register_page(__name__, top_nav=True, path="/financial_metrics", order=2)


# Financial data type (school or network)
@callback(
    Output("financial-metrics-radio", "options"),
    Output("financial-metrics-radio", "value"),
    Output("financial-metrics-radio-container", "style"),
    Input("charter-dropdown", "value"),
    State("financial-metrics-radio", "value"),
)
def radio_finance_info_selector(school: str, finance_value_state: str):
    selected_school = get_school_index(school)

    value_default = "school-finance"
    finance_value = value_default

    if selected_school["Network"].values[0] == "None":
        finance_options = []
        radio_input_container = {"display": "none"}

    else:
        finance_options = [
            {"label": "School", "value": "school-finance"},
            {"label": "Network", "value": "network-finance"},
        ]
        radio_input_container = {"display": "block"}

    if finance_value_state:
        # when changing dropdown from a school with network to one without, we need to reset state
        if (
            finance_value_state == "network-finance"
            and selected_school["Network"].values[0] == "None"
        ):
            finance_value = value_default
        else:
            finance_value = finance_value_state
    else:
        finance_value = value_default

    return finance_options, finance_value, radio_input_container


@callback(
    Output("financial-metrics-table", "children"),
    Output("financial-indicators-table", "children"),
    Output("financial-indicators-container", "style"),
    Output("financial-metrics-definitions-table", "children"),
    Output("financial-metrics-main-container", "style"),
    Output("financial-metrics-empty-container", "style"),
    Output("financial-metrics-no-data", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input(component_id="financial-metrics-radio", component_property="value"),
)
def update_financial_metrics(school: str, year: str, radio_value: str):
    if not school:
        raise PreventUpdate

    selected_year_string = year
    selected_year_numeric = int(selected_year_string)
    selected_school = get_school_index(school)

    financial_indicators_container = {"display": "block"}
    main_container = {"display": "block"}
    empty_container = {"display": "none"}
    no_data_to_display = no_data_page("No Data to Display.", selected_year_string + " Financial Metrics")

    if radio_value == "network-finance":
        network_id = selected_school["Network"].values[0]

        if network_id != "None":
            financial_data = get_financial_data(network_id)
        else:
            financial_data = {}

        table_title = (
            selected_year_string + " Financial Accountability Metrics ("
            + financial_data["School Name"][0]
            + ")"
        )

    else:
        # NOTE: If the selected school is a guest school, load dummy data (Schooly McSchoolface).
        if selected_school["Guest"].values[0] == "Y":
            school = "9999"

        financial_data = get_financial_data(school)

        # don't display school name in title if the school isn't part of a network
        if selected_school["Network"].values[0] == "None":
            if selected_school["Guest"].values[0] == "Y":
                table_title = selected_year_string + " Financial Accountability (SAMPLE DATA)"
            else:
                table_title = selected_year_string + " Financial Accountability Metrics"
        else:
            table_title = (
                selected_year_string + " Financial Accountability Metrics ("
                + financial_data["School Name"][0]
                + ")"
            )

    # Financial Metrics
    if len(financial_data.columns) <= 1 or financial_data.empty:
        financial_metrics_table = no_data_table(
            "No Data to Display.", selected_year_string + " Financial Metrics"
        )
        financial_indicators_table = no_data_table(
            "No Data to Display.", selected_year_string + " Financial Indicators"
        )

        # if no data, show no data page
        financial_indicators_container = {"display": "none"}
        main_container = {"display": "none"}
        empty_container = {"display": "block"}

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

        # create empty table if, after dropping excluded years, df has no financial
        # data, or file exists and has one year of data, but does not have a value for
        # State Grants (because the school is in Pre-Opening)
        # NOTE: To show schools in Pre-Opening year, remove the "or" condition
        # (you would also need to modify the financial metric calculation function, so
        # maybe think twice (or three times) before doing this)
        if (len(financial_data.columns) <= 1) | (
            (len(financial_data.columns) == 2) and (financial_data.iloc[1][1] == "0")
        ):
            financial_metrics_table = no_data_table(
                "No Data to Display.", selected_year_string + " Financial Metrics"
            )
            financial_indicators_table = no_data_table(
                "No Data to Display.", selected_year_string + " Financial Indicators"
            )

            financial_indicators_container = {"display": "none"}
            main_container = {"display": "none"}
            empty_container = {"display": "block"}

        else:
            # sort Year cols in ascending order (ignore Category)
            financial_data = (
                financial_data.set_index("Category")
                .sort_index(ascending=True, axis=1)
                .reset_index()
            )

            # pull out financial indicators
            financial_indicators = financial_data[
                financial_data["Category"].str.startswith("2.1.")
            ].copy()

            # in order for metrics to be calculated properly, we need
            # to temporarily store and remove the (Q#) part of string
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

            # see financial_information.py
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

            # Each column (year) in the df must have at least 12 values to be valid. To avoid the
            # situation where there is a column that only contains financial ratio or ADM data,
            # drop any column where more than 31 rows contain empty strings (df has 43 total rows)
            for c in financial_data.columns:
                if len(financial_data[financial_data[c] == 0].index) > 31:
                    financial_data.drop([c], inplace=True, axis=1)

            # remove audit and other indicator data (it is displayed on the financial metrics page)
            financial_values = financial_data.loc[
                : (financial_data["Category"] == "Audit Information").idxmax() - 1
            ]

            # Release The Hounds!
            # NOTE: We use all years of data to calculate metrics because several metrics (e.g. ATYM and MYCF)
            # require multiple prior years of data to properly calculate.
            financial_metrics = calculate_financial_metrics(financial_values)

            # Catches edge case where school has empty df _after_ the metric calculation
            if len(financial_metrics.columns) == 0:
                financial_metrics_table = []
                financial_indicators_table = []
                financial_metrics_definitions_table = []
                financial_indicators_container = {"display": "none"}
                main_container = {"display": "none"}
                empty_container = {"display": "block"}

            else:
                # Once metrics are calculated, we limit the maximum number of years
                # displayed to max_display_years. Because we have added a new Rating
                # column for each year, we need to multiply max by 2. To show all
                # available financial metric data, comment out this line
                metric_display_years = max_display_years * 2

                # drop "Metric" (category) column
                tmp_metric = financial_metrics["Metric"]
                financial_metrics = financial_metrics.drop("Metric", axis=1)

                if len(financial_metrics.columns) < metric_display_years:
                    metric_display_years = len(financial_metrics.columns)

                # because the years are ascending, we count from (keep) the end of the df
                # up to metric_display_years # of columns.
                financial_metrics = financial_metrics.iloc[:, -metric_display_years:]

                # add back "Metric" column
                financial_metrics.insert(loc=0, column="Metric", value=tmp_metric)

                # convert ratings to purty colored circles
                financial_metrics = convert_to_svg_circle(financial_metrics)

                financial_metrics = financial_metrics.fillna("")

                # Force correct format for display of df in datatable
                # this must be done after any pandas operations, because it
                # changes all of the values to strings
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

                # add quarter (Q#) back to header (current year only) if one exists
                if financial_quarter:
                    financial_metrics.columns.values[-2] = (
                        financial_metrics.columns.values[-2] + " " + financial_quarter
                    )

                headers = financial_metrics.columns.tolist()

                # determine # of columns and width of category column for display

                clean_headers = ["Rate" if "Rating" in c else c for c in headers]
                year_headers = [
                    i for i in headers if "Rating" not in i and "Metric" not in i
                ]
                rating_headers = [y for y in headers if "Rating" in y]

                # determines the col_width class and width of the category
                # column based on the size on the dataframe
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

                # this splits column width evenly for all columns other than "Category"
                data_width = 100 - category_width
                data_col_width = data_width / (table_size - 1)
                rating_width = year_width = data_col_width
                rating_width = rating_width / 2

                class_name = "pretty-container " + col_width + " columns"

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
            # Networks do not have financial indicators
            if (
                len(financial_indicators.columns) <= 1
                or financial_indicators.empty
                or radio_value == "network-finance"
            ):
                financial_indicators_table = []
                financial_indicators_container = {"display": "none"}

            else:
                # keep up to max years of data
                financial_indicators = financial_indicators.set_index(["Category"])

                indicator_display_years = max_display_years

                if len(financial_indicators.columns) < max_display_years:
                    indicator_display_years = len(financial_indicators.columns)

                financial_indicators = financial_indicators.iloc[
                    :, -indicator_display_years:
                ]
                financial_indicators = financial_indicators.reset_index()

                # split category and cleanup
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

        # Financial Metric Definitions - Currently this is always displayed
        # NOTE: At some point would like to style this better. Markdown or dmc Table?
        # (see Academic Metrics tooltips)
        financial_metrics_definitions_data = [
            [
                "Current Ratio = Current Assets ÷ Current Liabilities",
                "Current Ratio is greater than 1.1; or is between 1.0 and 1.1 and the one-year trend is not negative.",
            ],
            [
                "Days Cash on Hand = Unrestricted Cash ÷ ((Operating Expenses - Depreciation Expense) ÷ 365)",
                "School has greater than 45 unrestricted days cash; or between 30 - 45 unrestricted days cash and the one-year trend is not negative.",
            ],
            [
                "Annual Enrollment Change = (Current Year ADM - Previous Year ADM) ÷ Previous Year ADM",
                "Annual Enrollment Change increases or shows a current year decrease of less than 10%.",
            ],
            [
                "Primary Reserve Ratio = Unrestricted Net Assets ÷ Operating Expenses",
                "Primary Reserve Ratio is greater than .25.",
            ],
            [
                "Change in Net Assets Margin = (Operating Revenues - Operating Expenses) ÷ Operating Revenues ; Aggregated 3-Year Margin = (3 Year Operating Revenues - 3 Year Operating Expense) ÷ 3 Year Operating Revenues",
                "Aggregated Three-Year Margin is positive and the most recent year Change in Net Assets Margin is positive; or Aggregated Three-Year Margin is greater than -1.5%, the trend is positive for the last two years, and Change in Net Assets Margin for the most recent year is positive. For schools in their first and second year of operation, the cumulative Change in Net Assets Margin must be positive.",
            ],
            [
                "Debt to Asset Ratio = Total Liabilities ÷ Total Assets",
                "Debt to Asset Ratio is less than 0.9.",
            ],
            [
                "One Year Cash Flow = Recent Year Total Cash - Previous Year Total Cash; Multi-Year Cash Flow = Recent Year Total Cash - Two Years Previous Total Cash",
                'Multi-Year Cash Flow is positive and One Year Cash Flow is positive in two out of three years, including the most recent year. For schools in the first two years of operation, both years must have a positive Cash Flow (for purposes of calculating Cash Flow, the school"s Year 0 balance is assumed to be zero).',
            ],
            [
                "Debt Service Coverage Ratio = (Change in Net Assets + Depreciation/Amortization Expense + Interest Expense + Rent/Lease Expense) ÷ (Principal Payments + Interest Expense + Rent/Lease Expense)",
                "Debt Service Coverage Ratio is greater than or equal to 1.0.",
            ],
        ]

        financial_metrics_definitions_keys = [
            "Calculation",
            "Requirement to Meet Standard",
        ]
        financial_metrics_definitions_dict = [
            dict(zip(financial_metrics_definitions_keys, l))
            for l in financial_metrics_definitions_data
        ]

        financial_metrics_definitions_table = [
            html.Label(
                "Accountability Metrics Definitions & Requirements",
                className="label__header",
            ),
            html.Div(
                dash_table.DataTable(
                    data=financial_metrics_definitions_dict,
                    columns=[
                        {"name": i, "id": i} for i in financial_metrics_definitions_keys
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
                            "if": {"row_index": 0, "column_id": "Calculation"},
                            "borderTop": ".75px solid rgb(103,131,169)",
                        },
                        {
                            "if": {"state": "selected"},
                            "backgroundColor": "rgba(112,128,144, .3)",
                            "border": "thin solid silver",
                        },
                    ],
                    style_header={
                        "backgroundColor": "#ffffff",
                        "fontSize": "12px",
                        "fontFamily": "Inter, sans-serif",
                        "color": "#6783a9",
                        "textAlign": "center",
                        "fontWeight": "bold",
                        "text-decoration": "none",
                        "borderTop": "none",
                        "borderBottom": ".75px solid rgb(103,131,169)",
                    },
                    style_cell={
                        "whiteSpace": "normal",
                        "height": "auto",
                        "textAlign": "left",
                        "color": "#6783a9",
                    },
                    style_cell_conditional=[
                        {
                            "if": {"column_id": "Calculation"},
                            "width": "50%",
                            "fontWeight": "bold",
                        },
                    ],
                    style_as_list_view=True,
                ),
            ),
        ]

    return (
        financial_metrics_table,
        financial_indicators_table,
        financial_indicators_container,
        financial_metrics_definitions_table,
        main_container,
        empty_container,
        no_data_to_display
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
                                    html.Label("Key", className="label__header"),
                                    html.Div(create_proficiency_key()),
                                ],
                                className="pretty-container six columns",
                            ),
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
                            html.Div(
                                [
                                    dbc.RadioItems(
                                        id="financial-metrics-radio",
                                        className="btn-group",
                                        inputClassName="btn-check",
                                        labelClassName="btn btn-outline-primary",
                                        labelCheckedClassName="active",
                                        value=[],
                                        persistence=False,
                                    ),
                                ],
                                className="radio-group-finance",
                            )
                        ],
                        className="bare-container--flex--center twelve columns",
                    ),
                ],
                id="financial-metrics-radio-container",
            ),
            html.Div(
                [
                    html.Div(id="financial-metrics-table", children=[]),
                    html.Div(
                        [
                            html.Div(id="financial-indicators-table", children=[]),
                        ],
                        id="financial-indicators-container",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        id="financial-metrics-definitions-table",
                                        children=[],
                                    ),
                                ],
                                className="pretty-container eight columns",
                            ),
                        ],
                        className="bare-container--flex--center twelve columns",
                    ),
                ],
                id="financial-metrics-main-container",
            ),
            html.Div(
                [
                    html.Div(id="financial-metrics-no-data"),
                ],
                id="financial-metrics-empty-container",
            ),
        ],
        id="main-container",
    )