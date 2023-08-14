##########################################
# ICSB Dashboard - Financial Information #
##########################################
# author:   jbetley
# version:  1.09
# date:     08/14/23

import dash
from dash import html, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np

from .load_data import max_display_years, get_school_index, get_financial_data
from .table_helpers import no_data_page
from .subnav import subnav_finance

dash.register_page(__name__, top_nav=True, path = "/financial_information", order=1)

@callback(
    Output("financial-information-table", "children"),
    Output("radio-finance-info-display", "style"),
    Output("radio-finance-info-content", "children"),
    Output("financial-information-main-container", "style"),
    Output("financial-information-empty-container", "style"),
    Output("financial-information-no-data", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input(component_id="radio-button-finance-info", component_property="value")
)
def update_financial_information_page(school: str, year: str, radio_value: str):
    if not school:
        raise PreventUpdate

    main_container = {"display": "block"}
    empty_container = {"display": "none"}
    no_data_to_display = no_data_page("Audited Financial Information")

    selected_year_string = year
    selected_year_numeric = int(selected_year_string)
    selected_school = get_school_index(school)

    # Displays either School or Network level financials, if a school is not
    # part of a network, no radio buttons are displayed at all. If a school
    # is part of a network, define and display radio button. Storing the radio
    # buttons in a variable ensures there is no flickering of the component as
    # it is drawn and then hidden - as the button variable has no content until
    # it also meets the display condition.
    if selected_school["Network"].values[0] != "None":
        if radio_value == "network-finance":

            radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id="radio-button-finance-info",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-primary",
                        labelCheckedClassName="active",
                        options=[
                            {"label": "School", "value": "school-finance"},
                            {"label": "Network", "value": "network-finance"},
                        ],
                        value="network-finance",
                        persistence=True,
                        persistence_type="local",
                    ),
                ],
                className="radio-group",
            )

        else:
            radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id="radio-button-finance-info",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-primary",
                        labelCheckedClassName="active",
                        options=[
                            {"label": "School", "value": "school-finance"},
                            {"label": "Network", "value": "network-finance"},
                        ],
                        value="school-finance",
                        persistence=True,
                        persistence_type="local",
                    ),
                ],
                className="radio-group",
            )
            
            radio_value = "school-metrics"
        
        display_radio = {}

    else:
        radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id="radio-button-finance-info",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-primary",
                        labelCheckedClassName="active",
                        options=[],
                        value="",
                        persistence=True,
                        persistence_type="local",
                    ),
                ],
                className="radio-group",
            )
        
        # radio_value defaults to school if "Network" value is None in school_index
        radio_value = "school-metrics"
        display_radio = {"display": "none"}

    if radio_value == "network-finance":
        
        network_id = selected_school["Network"].values[0]

        # network financial data
        if network_id != "None":
            financial_data = get_financial_data(network_id)

        else:
            financial_data = {}
        
        table_title = "Audited Financial Information (" + financial_data["School Name"][0] + ")"

    else:
        
        # school financial data
        financial_data = get_financial_data(school)

        # don't display the school name in table title if the school isn't part of a network
        if selected_school["Network"].values[0] == "None":
            table_title = "Audited Financial Information"
        else:
            table_title = "Audited Financial Information (" + financial_data["School Name"][0] + ")"

    if (len(financial_data.columns) <= 1 or financial_data.empty):

        financial_information_table = []
        main_container = {"display": "none"}
        empty_container = {"display": "block"}

    else:

        financial_data = financial_data.drop(["School ID","School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        # Financial data will almost always be more recent than academic
        # data. This is the only time we want do display "future" data,
        # that is data from a year more recent than the maximum dropdown
        # (academic) year. The first (most recent) column of the financial
        # data file is a string that will either be in the format "YYYY" or
        # "YYYY (Q#)", where Q# represents the quarter of the displayed
        # financial data (Q1, Q2, Q3, Q4). If "(Q#)" is not in the string,
        # it means the data in the column is audited data.
        available_years = financial_data.columns.difference(['Category'], sort=False).tolist()
        available_years = [int(c[:4]) for c in available_years]
        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year -  selected_year_numeric

        if selected_year_numeric < most_recent_finance_year:
            financial_data.drop(financial_data.columns[1:(years_to_exclude+1)], axis=1, inplace=True)

        if len(financial_data.columns) > 1:

            # change all cols to numeric except for Category
            for col in financial_data.columns[1:]:
                financial_data[col]=pd.to_numeric(financial_data[col], errors="coerce")

            # NOTE: there are certain calculated categories already in the df ("Total Grants",
            # "Net Asset Position", and "Change in Net Assets"). Rather than
            # rely on pre-calculated categories, we (re)calculate them from the 
            # underlying data: 1) "Total Grants" = "State Grants" + "Federal Grants";
            # 2) "Net Asset Position" = "Total Assets" - "Total Liabilities"; and
            # 3) "Change in Net Assets" = "Operating Revenues" - "Operating Expenses"
            # Because the rows already exist in the dataframe, we set Category as index
            # (so we can use .loc with the Category names):

            financial_data = financial_data.set_index(["Category"])
            financial_data.loc["Total Grants"] = financial_data.loc["State Grants"] + financial_data.loc["Federal Grants"]
            financial_data.loc["Net Asset Position"] = financial_data.loc["Total Assets"] - financial_data.loc["Total Liabilities"]
            financial_data.loc["Change in Net Assets"] = financial_data.loc["Operating Revenues"] - financial_data.loc["Operating Expenses"]

            # reset index, which shifts Category back to column one
            financial_data = financial_data.reset_index()

            # Ensure that only the "max_display_years" number of years worth of financial
            # data is displayed (add +1 to max_display_years to account for the category
            # column). To show all years of data, comment out this line.

            financial_data = financial_data.iloc[: , :(max_display_years+1)]

            string_years=financial_data.columns.tolist()
            string_years.pop(0)
            string_years.reverse()

            # remove audit and other indicator data (it is displayed on the financial metrics page)
            # financial_data = financial_data.drop(financial_data.index[41:])
            financial_data = financial_data.loc[:(financial_data["Category"] == "Audit Information").idxmax()-1]

            # Each column (year) in the df must have at least 12 values to be valid. To avoid the
            # situation where there is a column that only contains financial ratio data (e.g., 
            # when a school existed prior to being required to report financial data to ICSB),
            # drop any column where more than 31 rows contain empty strings (df has 43 total rows)
            for c in financial_data.columns:
                if len(financial_data[financial_data[c] == ""].index) > 31:
                    financial_data.drop([c], inplace=True, axis=1)

            # the following rows (financial categories) are not used and should be removed
            remove_categories = ["Administrative Staff", "Instructional Staff","Instructional and Support Staff","Non-Instructional Staff","Total Personnel Expenses",
                "Instructional & Support Staff", "Instructional Supplies","Management Fee","Insurance (Facility)","Electric and Gas",
                "Water and Sewer","Waste Disposal","Security Services","Repair and Maintenance","Occupancy Ratio","Human Capital Ratio",
                "Instruction Ratio"]

            financial_data = financial_data[~financial_data["Category"].isin(remove_categories)]

            financial_data = financial_data.dropna(axis=1, how="all")
            financial_data = financial_data.reset_index(drop=True)

            # Force correct format for display of df in datatable (accounting, no decimals, no "$")
            for year in string_years:
                financial_data[year] = pd.Series(["{:,.0f}".format(val) for val in financial_data[year]], index = financial_data.index)

            # clean file for display, replacing nan and 0.00 with ""
            financial_data.replace([0, "0", 0.0, "0.0",0.00,"0.00", "nan", np.nan], "", inplace=True)

            year_headers = [i for i in financial_data.columns if i not in ["Category"]]

            table_size = len(financial_data.columns)

            # force css column size depending on # of columns in dataframe
            if table_size == 2:
                col_width = "five"
                category_width = 55
            if table_size == 3:
                col_width = "six"
                category_width = 55
            if table_size > 3 and table_size <=8:
                col_width = "eight"
                category_width = 35
            elif table_size >= 9:
                col_width = "ten"
                category_width = 25
            elif table_size >= 10:
                col_width = "twelve"
                category_width = 15

            data_width = 100 - category_width
            year_width = data_width / (table_size - 1)

            class_name = "pretty_container " + col_width + " columns"

            financial_information_table = [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(table_title, className = "header_label"),
                                html.Div(
                                    dash_table.DataTable(
                                        financial_data.to_dict("records"),
                                        columns = [{"name": i, "id": i} for i in financial_data.columns],
                                        style_data={
                                            "fontSize": "12px",
                                            "fontFamily": "Jost, sans-serif",
                                            "border": "none"
                                        },
                                        style_data_conditional=[
                                            {
                                                "if": {
                                                    "row_index": "odd"
                                                },
                                                "backgroundColor": "#eeeeee",
                                            },
                                            {
                                                "if": {
                                                    "filter_query": "{Category} eq 'Revenue' || {Category} eq 'Financial Position' ||{Category} eq 'Financial Activities' || {Category} eq 'Supplemental Information' || {Category} eq 'Enrollment Information' || {Category} eq 'Audit Information'"
                                                },
                                                "paddingLeft": "10px",
                                                "text-decoration": "underline",
                                                "fontWeight": "bold"
                                            },
                                            {
                                                "if": {
                                                    "row_index": 0,
                                                    "column_id": "Category"
                                                },
                                                "borderTop": ".5px solid #6783a9"
                                            },
                                            {
                                                "if": {
                                                    "state": "selected"
                                                },
                                                "backgroundColor": "rgba(112,128,144, .3)",
                                                "border": "thin solid silver"
                                            }
                                        ],
                                        style_header={
                                            "backgroundColor": "#ffffff",
                                            "border": "none",
                                            "borderBottom": ".5px solid #6783a9",
                                            "fontSize": "12px",
                                            "fontFamily": "Jost, sans-serif",
                                            "color": "#6783a9",
                                            "textAlign": "center",
                                            "fontWeight": "bold"
                                        },
                                        style_cell={
                                            "whiteSpace": "normal",
                                            "height": "auto",
                                            "textAlign": "center",
                                            "color": "#6783a9",
                                            "minWidth": "25px", "width": "25px", "maxWidth": "25px"
                                        },
                                        style_cell_conditional=[
                                            {
                                                "if": {
                                                    "column_id": "Category"
                                                },
                                                "textAlign": "left",
                                                "fontWeight": "500",
                                                "paddingLeft": "20px",
                                                "width": str(category_width) + "%"
                                            },
                                        ] + [
                                            {
                                                "if": {
                                                    "column_id": year
                                                },
                                                "textAlign": "center",
                                                "fontWeight": "500",
                                                "width": str(year_width) + "%",
                                            } for year in year_headers
                                        ],
                                        style_as_list_view=True
                                    )
                                )
                            ],
                            className = class_name,
                        ),
                    ],
                    className = "bare_container_center twelve columns",
                )
            ]

        else:

            financial_information_table = []
            main_container = {"display": "none"}
            empty_container = {"display": "block"}

    return financial_information_table, display_radio,radio_content, \
        main_container, empty_container, no_data_to_display

def layout():
    return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(subnav_finance(),className="tabs"),
                            ],
                            className="bare_container_center twelve columns"
                        ),
                    ],
                    className="row"
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(id="radio-finance-info-content", children=[]),
                                            ],
                                            id = "radio-button-finance-info",
                                        ),
                                    ],
                                    id = "radio-finance-info-display",
                                ),
                            ],
                            className = "bare_container_center twelve columns",
                        ),
                    ],
                    className = "row",
                ),
                html.Div(
                    [
                        html.Div(id="financial-information-table", children=[]),
                    ],
                    id = "financial-information-main-container",
                ),
                html.Div(
                    [
                        html.Div(id="financial-information-no-data"),
                    ],
                    id = "financial-information-empty-container",
                ),
            ],
            id="mainContainer",
        )