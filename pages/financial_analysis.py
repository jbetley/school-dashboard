#######################################
# ICSB Dashboard - Financial Analysis #
#######################################
# author:   jbetley
# version:  1.10
# date:     09/10/23

import dash
from dash import dcc, html, dash_table, Input, State, Output, callback
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash.dash_table import FormatTemplate
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

from .load_data import max_display_years, get_school_index, get_financial_data, get_financial_ratios
from .tables import no_data_page, no_data_table, create_financial_analysis_table
from .charts import loading_fig
from .calculations import round_nearest
from .subnav import subnav_finance

dash.register_page(__name__, path = "/financial_analysis", order=3)

# Financial data type (school or network)
@callback(      
    Output("financial-analysis-radio", "options"),
    Output("financial-analysis-radio","value"),
    Output("financial-analysis-radio-container", "style"),
    Input("charter-dropdown", "value"),
    State("financial-analysis-radio", "value"),
)
def financial_analysis_radio_selector(school: str, finance_value_state: str):

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
        if finance_value_state == "network-finance" and selected_school["Network"].values[0] == "None":
            finance_value = value_default
        else:    
            finance_value = finance_value_state
    else:
        finance_value = value_default
            
    return finance_options, finance_value, radio_input_container


@callback(
    Output("revenue-expenses-fig", "figure"),
    Output("assets-liabilities-fig", "figure"),
    Output("financial-position-table", "children"),
    Output("financial-activities-table", "children"),
    Output("finance-analysis-RandE-title", "children"),
    Output("finance-analysis-AandL-title", "children"),
    Output("finance-analysis-FP-title", "children"),
    Output("finance-analysis-FA-title", "children"),
    Output("financial-ratios-table", "children"),
    Output("per-student-table", "children"),
    Output("financial-analysis-main-container", "style"),
    Output("financial-analysis-empty-container", "style"),
    Output("financial-analysis-no-data", "children"),
    Output("financial-analysis-notes-string", "children"),    
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input(component_id="financial-analysis-radio", component_property="value")
)
def update_financial_analysis_page(school: str, year: str, radio_value: str):
    if not school:
        raise PreventUpdate

    main_container = {"display": "block"}
    empty_container = {"display": "none"}
    no_data_to_display = no_data_page("Financial Analysis")

    selected_year_string = year
    selected_year_numeric = int(selected_year_string)
    previous_year_numeric = selected_year_numeric - 1
    
    selected_school = get_school_index(school)

    # ensure consistent data display throughout
    display_years = [str(previous_year_numeric)] + [year]
    
    if selected_school["Guest"].values[0] == "Y":
        financial_analysis_notes_string = "SAMPLE DATA"
    else:
        financial_analysis_notes_string = "Only the most recent years of audited data are shown."

    if radio_value == "network-finance":
        network_id = selected_school["Network"].values[0]
        
        if network_id != "None":
            financial_data = get_financial_data(network_id)
        else:
            financial_data = {}

        RandE_title = "Revenue and Expenses (" + financial_data["School Name"][0] + ")"
        AandL_title = "Assets and Liabilities (" + financial_data["School Name"][0] + ")"
        FP_title = "2-Year Financial Position (" + financial_data["School Name"][0] + ")"
        FA_title = "2-Year Financial Activities (" + financial_data["School Name"][0] + ")"

    else:
        
        financial_data = get_financial_data(school)

        if selected_school["Network"].values[0] == "None":
            RandE_title = "Revenue and Expenses"
            AandL_title = "Assets and Liabilities"
            FP_title = "2-Year Financial Position"
            FA_title = "2-Year Financial Activities"  
        else:
            RandE_title = "Revenue and Expenses (" + financial_data["School Name"][0] + ")"
            AandL_title = "Assets and Liabilities (" + financial_data["School Name"][0] + ")"
            FP_title = "2-Year Financial Position (" + financial_data["School Name"][0] + ")"
            FA_title = "2-Year Financial Activities (" + financial_data["School Name"][0] + ")"

    if (len(financial_data.columns) <= 1 or financial_data.empty):

        financial_position_table = []       # type: list
        financial_activities_table = []     # type: list
        financial_ratios_table = []         # type: list
        per_student_table = []              # type: list

        revenue_expenses_fig = go.Figure()
        assets_liabilities_fig = go.Figure()
        main_container = {"display": "none"}
        empty_container = {"display": "block"}

    else:

        # If Guest School - load dummy data
        if selected_school["Guest"].values[0] == "Y":
            financial_data = get_financial_data("9999")

        financial_data = financial_data.drop(["School ID","School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        # NOTE: drop partial year data (financial data with a "Q#" in column header).
        # may eventually want to implement for Q4 data, but the display quickly gets
        # too confusing with incomplete data.
        if "Q" in financial_data.columns[1]:
            financial_data = financial_data.drop(financial_data.columns[[1]],axis = 1)

        available_years = financial_data.columns.difference(['Category'], sort=False).tolist()
        available_years = [int(c[:4]) for c in available_years]
        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year -  selected_year_numeric

        if selected_year_numeric < most_recent_finance_year:
            financial_data.drop(financial_data.columns[1:(years_to_exclude+1)], axis=1, inplace=True)

        # if there are no columns or only one column ("Category"), then all tables and figs are empty
        if len(financial_data.columns) <= 1:
            financial_position_table = []
            financial_activities_table = []
            financial_ratios_table = []
            per_student_table = []

            revenue_expenses_fig = go.Figure()
            assets_liabilities_fig = go.Figure()
            main_container = {"display": "none"}
            empty_container = {"display": "block"}

        else:

            # NOTE: see chart_helpers.py for full list of colors
            color=["#74a2d7", "#df8f2d"]
            
            for col in financial_data.columns:
                financial_data[col]=pd.to_numeric(financial_data[col], errors="coerce").fillna(financial_data[col]).tolist()

            # see financial_information.py
            financial_data = financial_data.set_index(["Category"])
            financial_data.loc["Total Grants"] = financial_data.loc["State Grants"] + financial_data.loc["Federal Grants"]
            financial_data.loc["Net Asset Position"] = financial_data.loc["Total Assets"] - financial_data.loc["Total Liabilities"]
            financial_data.loc["Change in Net Assets"] = financial_data.loc["Operating Revenues"] - financial_data.loc["Operating Expenses"]        
            financial_data = financial_data.reset_index()

            financial_data = financial_data.iloc[: , :(max_display_years+1)]

            # tables display missing years as blank, figs do not display them at all so we need
            # a copy of the df at this point for figs.
            financial_data_fig = financial_data.copy()

            # Network financial data typically lags behind school data by at
            # least a year. So drop any column (year) that doesn't have at least 31
            # values not equal to 0 (the min # of values to be valid). this prevents
            # empty columns from being displayed
            for c in financial_data_fig.columns:
                if len(financial_data_fig[financial_data_fig[c] == 0].index) > 31:
                    financial_data_fig.drop([c], inplace=True, axis=1)

            string_fig_years = financial_data_fig.columns.tolist()
            string_fig_years.pop(0)
            string_fig_years.reverse()

            ## Fig 1: Operating Revenue, Operating Expenses, & Change in
            # Net Assets (Net Income) show Operating Revenue and Expenses
            # as grouped bars and Change in Net Assets as line
            revenue_expenses_data = financial_data_fig[financial_data_fig["Category"].isin(["Operating Expenses", "Operating Revenues"])]
            revenue_expenses_data = revenue_expenses_data.reset_index(drop=True)

            for col in revenue_expenses_data.columns:
                revenue_expenses_data[col]=pd.to_numeric(revenue_expenses_data[col], errors="coerce").fillna(revenue_expenses_data[col]).tolist()

            # Reverse order of df (earliest -> latest) & move Category back to front
            revenue_expenses_data = revenue_expenses_data.iloc[:, ::-1]
            revenue_expenses_data.insert(0, "Category", revenue_expenses_data.pop("Category"))
            
            # Transpose df (to group by "Operating Revenue" & "Operating Expenses)
            revenue_expenses_data = revenue_expenses_data.set_index("Category").T

            revenue_expenses_bar_fig = px.bar(
                data_frame = revenue_expenses_data,
                x = string_fig_years, 
                y= [c for c in revenue_expenses_data.columns],
                color_discrete_sequence=color,
                barmode="group",
            )

            # revenue and expense data can vary widely (from 5 to 7 figures) from school to
            # school and from year to year. Use round_nearest() to determine tick value
            # based on the max value in a dataframe.

            # NOTE: change "step" value to increase/decrease the total number of ticks
            step = 6

            tick_val = round_nearest(revenue_expenses_data, step)

            revenue_expenses_bar_fig.update_xaxes(showline=False, linecolor="#a9a9a9",ticks="outside", tickcolor="#a9a9a9", title="")
            revenue_expenses_bar_fig.update_yaxes(showgrid=True, gridcolor="#a9a9a9",title="", tickmode = "linear", tick0 = 0,dtick = tick_val)

            revenue_expenses_bar_fig.update_layout(
                margin=dict(l=40, r=40, t=40, b=60),
                font=dict(
                    family="Inter, sans-serif",
                    color="#6783a9",
                    size=12
                    ),
                hovermode="x unified",
                showlegend=True,
                height=400,
                legend=dict(
                    orientation="h",
                    title="",
                    traceorder="reversed"
                    ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            revenue_expenses_bar_fig["data"][0]["hovertemplate"]="Operating Revenues<br>$ %{y:,.2f}<extra></extra>"
            revenue_expenses_bar_fig["data"][1]["hovertemplate"]="Operating Expenses<br>$ %{y:,.2f}<extra></extra>"

            # Get Change in Net Assets Value
            revenue_expenses_line_data = financial_data_fig[financial_data_fig["Category"].isin(["Change in Net Assets"])]
            revenue_expenses_line_data = revenue_expenses_line_data.reset_index(drop=True)

            revenue_expenses_line_data = revenue_expenses_line_data.replace("", 0,regex=True)

            cols=[i for i in revenue_expenses_line_data.columns if i not in ["Category"]]

            for col in cols:
                revenue_expenses_line_data[col]=pd.to_numeric(revenue_expenses_line_data[col], errors="coerce")

            revenue_expenses_line_data = revenue_expenses_line_data.iloc[:, ::-1]
            revenue_expenses_line_data.pop("Category")
            revenue_expenses_line_data = revenue_expenses_line_data.loc[:, :].values.flatten().tolist()
            
            revenue_expenses_line_fig = px.line(
                x = string_fig_years,
                y = revenue_expenses_line_data,
                markers = True,
                color_discrete_sequence = ["#75851b"]
            )

            revenue_expenses_fig = go.Figure(data=revenue_expenses_line_fig.data + revenue_expenses_bar_fig.data,layout=revenue_expenses_bar_fig.layout)
            revenue_expenses_fig["data"][0]["showlegend"]=True
            revenue_expenses_fig["data"][0]["name"]="Change in Net Assets"
            revenue_expenses_fig["data"][0]["hovertemplate"]="Change in Net Assets<br>$ %{y:,.2f}<extra></extra>"

            ## Fig 2: Assets + Liabilities per year bars and Net Asset Position as Line
            assets_liabilities_data = financial_data_fig[financial_data_fig["Category"].isin(["Total Assets", "Total Liabilities"])]
            assets_liabilities_data=assets_liabilities_data.reset_index(drop=True)

            assets_liabilities_data = assets_liabilities_data.replace("", 0,regex=True)

            cols=[i for i in assets_liabilities_data.columns if i not in ["Category"]]

            for col in cols:
                assets_liabilities_data[col]=pd.to_numeric(assets_liabilities_data[col], errors="coerce")
            
            # Reverse order of df (earliest -> latest) & move Category back to front
            assets_liabilities_data = assets_liabilities_data.iloc[:, ::-1]
            assets_liabilities_data.insert(0, "Category", assets_liabilities_data.pop("Category"))
            
            # Transpose df (to group by "Operating Revenue" & "Operating Expenses)
            assets_liabilities_data = assets_liabilities_data.set_index("Category").T

            assets_liabilities_bar_fig = px.bar(
                data_frame = assets_liabilities_data,
                x = string_fig_years, 
                y = [c for c in assets_liabilities_data.columns],
                color_discrete_sequence=color,
                barmode="group",
            )
            
            tick_val = round_nearest(assets_liabilities_data, step)

            assets_liabilities_bar_fig.update_xaxes(showline=False, linecolor="#a9a9a9",ticks="outside", tickcolor="#a9a9a9", title="")
            assets_liabilities_bar_fig.update_yaxes(showgrid=True, gridcolor="#a9a9a9",title="", tickmode = "linear", tick0 = 0,dtick = tick_val)

            assets_liabilities_bar_fig.update_layout(
                margin=dict(l=40, r=40, t=40, b=60),
                font = dict(
                    family="Inter, sans-serif",
                    color="#6783a9",
                    size=12
                    ),
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    title="",
                    traceorder="reversed"
                    ),  
                height=400,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            assets_liabilities_bar_fig["data"][1]["hovertemplate"]="Total Liabilities<br>$ %{y:,.2f}<extra></extra>"
            assets_liabilities_bar_fig["data"][0]["hovertemplate"]="Total Assets<br>$ %{y:,.2f}<extra></extra>"

            # get Net Asset Position Value
            assets_liabilities_line_data=financial_data_fig.iloc[10].tolist()  
            assets_liabilities_line_data.pop(0)
            assets_liabilities_line_data.reverse()

            assets_liabilities_line_fig = px.line(
                x = string_fig_years,
                y = assets_liabilities_line_data,
                markers=True,
                color_discrete_sequence = ["#75851b"]
            )

            assets_liabilities_fig = go.Figure(data=assets_liabilities_line_fig.data + assets_liabilities_bar_fig.data,layout=assets_liabilities_bar_fig.layout)

            assets_liabilities_fig["data"][0]["showlegend"]=True
            assets_liabilities_fig["data"][0]["name"]="Net Asset Position"
            assets_liabilities_fig["data"][0]["hovertemplate"]="Net Asset Position<br>$ %{y:,.2f}<extra></extra>"

            ## Two Year Finance Tables (Financial Position and Financial Activities)

            # display years is a list of [CY, PY]
            default_headers = ["Category"] + display_years

            # there may be columns with no or partial data at beginning or ending of dataframe,
            # this deletes any column where more than 80% of the columns values are == 0
            # (otherwise empty columns may have some data, eg., ADM)
            # NOTE: This could probably be more precise (compare with that other wierd 31 algorithm).
            financial_data = financial_data.loc[:, (financial_data==0).mean() < .7]

            # if all of the years to display (+ Category) exist in (are a subset of) the dataframe,
            # filter the dataframe by the display header
            if set(default_headers).issubset(set(financial_data.columns)):
                financial_data = financial_data[default_headers]

            else:

                # identify the missing_year and the remaining_year and then add the missing_year as a blank
                # column to the dataframe either before or after remaining_year depending on which year
                # is earlier in time
                missing_year = list(set(default_headers).difference(financial_data.columns))
                remaining_year = [e for e in default_headers if e not in ("Category", missing_year[0])]
                i = 1 if (int(missing_year[0]) < int(remaining_year[0])) else 0

                financial_data.insert(loc = i, column = missing_year[0], value = 0)
                financial_data = financial_data[default_headers]

            # sort Year cols in ascending order (ignore Category)
            financial_data = financial_data.set_index('Category').sort_index(ascending=True, axis=1).reset_index()

            # Table 1: 2-Year Financial Position
            financial_position_categories = ["Total Assets","Current Assets","Total Liabilities","Current Liabilities","Net Asset Position"]
            financial_position_table = create_financial_analysis_table(financial_data, financial_position_categories) 
  
            # Table 2: 2-Year Financial Activities
            financial_activity_categories = ["Operating Revenues", "Operating Expenses", "Change in Net Assets"]
            financial_activities_table = create_financial_analysis_table(financial_data, financial_activity_categories) 
            
            # Table #3: Per-Student Expenditures
            per_student_categories = ["State Grants", "Operating Revenues", "Operating Expenses", "Change in Net Assets", "ADM Average"]
            per_student_table = create_financial_analysis_table(financial_data, per_student_categories) 

            # Table 4: Financial Ratios
            # cannot use create_analysis_table() function here because of need for special operations
            school_corp = int(selected_school["Corporation ID"].values[0])
            financial_ratios_data = get_financial_ratios(school_corp)
            ratio_years = financial_ratios_data["Year"].astype(str).tolist()

            # Networks do not have ratios- only way to tell if network finances
            # are being displayed is if the radio_value is equal to "network-finance."
            # So we show an empty table if "network-finance" is being displayed.
            # We also show empty table if there are no rows in financial_ratios_data
            # (empty df) OR where there are no years of data in the dataframe that
            # match the years being displayed (the last condition is True if the
            # two lists share at least one item (e.g., at least one of the
            # default_headers are in the Years dataframe column)).
           
            if radio_value != "network-finance" and (len(financial_ratios_data.index) != 0) and \
                not set(ratio_years).isdisjoint(default_headers):

                # drop unused columns, transpose and rename                
                financial_ratios_data = financial_ratios_data.drop(columns=["Corporation Name","Corporation ID"])
                financial_ratios_data = financial_ratios_data.set_index("Year").T.rename_axis("Category").rename_axis(None, axis=1).reset_index()

                financial_ratios_data.columns = financial_ratios_data.columns.astype(str)

                # change all cols to numeric except for Category
                for col in financial_ratios_data.columns[1:]:
                    financial_ratios_data[col]=pd.to_numeric(financial_ratios_data[col], errors="coerce")

                # # sort Year cols in ascending order (ignore Category)
                # financial_ratios_data = financial_ratios_data.set_index('Category').sort_index(ascending=True, axis=1).reset_index()

                # Create an empty df in the shape and order that we want (e.g., Category, YYYY, YYYY-1), use
                # combine_first to update all null elements in the empty df with a value in the same location
                # in the existing df and then merge 
                # https://stackoverflow.com/questions/56842140/pandas-merge-dataframes-with-shared-column-fillna-in-left-with-right
                
                default_df = pd.DataFrame(columns=default_headers)
                
                default_df["Category"] = financial_ratios_data["Category"]

                non_duplicate_cols = ["Category"] + [i for i in default_df.columns.to_list() if i not in financial_ratios_data.columns.to_list()]

                final_ratios_data = default_df.combine_first(default_df[non_duplicate_cols].merge(financial_ratios_data, "left"))
                final_ratios_data = final_ratios_data[default_headers]

                final_ratios_data = final_ratios_data.fillna("N/A")
                
                for year in display_years:
                    if (final_ratios_data[year] != "N/A").any():
                        final_ratios_data[year] = pd.Series(["{0:.2f}%".format(val * 100) for val in final_ratios_data[year]], index = final_ratios_data.index)

                financial_ratios_table = [
                    html.Label("Financial Ratios", className = "label__header"),
                    html.P(""),
                    html.Div(
                        dash_table.DataTable(
                            data = final_ratios_data.to_dict("records"),
                            columns = [{"name": i, "id": i, "type":"numeric","format": FormatTemplate.percentage(2)} for i in final_ratios_data.columns],
                            tooltip_data=[
                                {
                                "Category": {
                                    "value": "**Occupancy Ratio** measures the percentage of total revenue used to \
                                    occupy and maintain school facilities. A school\"s occupancy ratio generally \
                                    should be less than 25%. It is calculated as: **Occupancy Expense** (Form 9 Object\
                                    Codes 411, 431, 441, 450, between 621 & 626, and between 710 & 720) divided by \
                                    **Total Revenue** (Form 9 Section Codes 1 and 3)",
                                    "type": "markdown"},
                                },
                                {
                                "Category": {
                                    "value": "**Human Capital Ratio** measures the percentage of total revenue used \
                                    for payroll. A school\"s human capital ratio should be less than 50%. A human \
                                    capital ratio that is significantly Higher than a school\"s instruction ratio \
                                    may be a sign that the school has too many administrators. It is calculated as: \
                                    **Personnel Expense** (Form 9 Object Codes between 110 & 290) divided by **Total \
                                    Revenue** (Form 9 Section Codes 1 and 3)",
                                    "type": "markdown"},
                                },
                                {
                                "Category": {
                                    "value": "**Instruction Ratio** measures how much of a school\"s revenue is used \
                                    to pay for instruction. It is calculated as: **Instruction Expense** (Form 9 \
                                    Object Codes between 110 & 290- excluding 115, 120, 121, 149, and 150-311, 312, \
                                    and 313) divided by **Total Revenue** (Form 9 Section Codes 1 and 3)",
                                    "type": "markdown"},
                                },
                                {
                                "Category": {
                                    "value": "**Instructional Staff Ratio** measures how much of a school\'s revenue is used \
                                    to pay for instructional staff. It is calculated as: **Instructional Staff Expense** (Form 9 \
                                    Object Codes between 110, 115, 120, 150 and 290) divided by **Total Revenue** (Form 9 \
                                    Section Codes 1 and 3)",
                                    "type": "markdown"},
                                },                                
                            ],
                            css=[
                                {
                                    "selector": ".dash-table-tooltip",
                                    "rule": "background-color: grey; color: white; font-size: 10px"
                                }
                            ],
                            tooltip_duration=None,
                            style_data = {
                                "fontSize": "12px",
                                "fontFamily": "Inter, sans-serif",
                            },
                            style_data_conditional=[
                                {
                                    "if": {
                                        "column_id": "Category",
                                    },
                                    "borderRight": ".5px solid #6783a9",
                                },
                                {
                                    "if": {
                                        "filter_query": "{Category} eq 'Occupancy Ratio'"
                                    },
                                    "borderTop": ".5px solid #6783a9",
                                },
                                {
                                    "if": {
                                        "state": "selected"
                                    },
                                    "backgroundColor": "rgba(112,128,144, .3)",
                                    "border": "thin solid silver"
                                }                                
                            ],
                            style_header = {
                                "height": "20px",
                                "backgroundColor": "#ffffff",
                                "borderBottom": ".5px solid #6783a9",
                                "borderTop": "none",
                                "borderRight": "none",
                                "borderLeft": "none",                
                                "fontSize": "12px",
                                "fontFamily": "Inter, sans-serif",
                                "color": "#6783a9",
                                "textAlign": "center",
                                "fontWeight": "bold"
                            },
                            style_header_conditional = [
                                {
                                    "if": {
                                        "column_id": "Category",
                                    },
                                    "borderRight": ".5px solid #6783a9",
                                    "borderBottom": ".5px solid #6783a9",
                                    "textAlign": "left"
                                },
                            ],
                            style_cell = {
                                "border": "none",
                                "whiteSpace": "normal",
                                "height": "auto",
                                "textAlign": "center",
                                "color": "#6783a9",
                                "minWidth": "25px", "width": "25px", "maxWidth": "25px"
                            },
                            style_cell_conditional = [
                                {
                                    "if": {
                                        "column_id": "Category"
                                    },
                                    "textAlign": "left",
                                    "paddingLeft": "20px",
                                    "width": "40%"
                                }
                            ]
                        )
                    ),
                    html.P(""),
                    html.P("Source: IDOE Form 9 (hover over category for details).",
                    style={
                        "color": "#6783a9",
                        "fontSize": 10,
                        "marginLeft": "10px",
                        "marginRight": "10px",
                        "marginTop": "20px",
                        "paddingTop": "5px",
                        "borderTop": ".5px solid #c9d3e0",
                        },
                    ),
                ]
            else:
                financial_ratios_table  = no_data_table(["Financial Ratios"])

    return (
        revenue_expenses_fig, assets_liabilities_fig, financial_position_table,financial_activities_table,
        RandE_title, AandL_title, FP_title, FA_title, financial_ratios_table, per_student_table,
        main_container, empty_container, no_data_to_display, financial_analysis_notes_string
     )

def layout():
    return html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(subnav_finance(), className="tabs"),
                                ],
                            className="bare-container--flex--center twelve columns",
                            ),
                        ],
                        className="row"
                    ),
                    html.Hr(),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            dbc.RadioItems(
                                                id="financial-analysis-radio",
                                                className="btn-group",
                                                inputClassName="btn-check",
                                                labelClassName="btn btn-outline-primary",
                                                labelCheckedClassName="active",
                                                value=[],
                                                persistence=False,
                                                # persistence_type="memory",
                                            ),
                                        ],
                                        className="radio-group-finance",
                                    )
                                ],
                                className = "bare-container--flex--center twelve columns",
                            ),
                        ],
                        id = "financial-analysis-radio-container",
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
                                                html.Label("Notes:", className="key-label__header"),
                                                html.P(""),
                                                    html.P(id="financial-analysis-notes-string",
                                                        style={
                                                                "textAlign": "center",
                                                                "color": "#6783a9",
                                                                "fontSize": 12,
                                                                "marginLeft": "10px",
                                                                "marginRight": "10px",
                                                                "marginTop": "10px",
                                                        }
                                                    ),
                                            ],
                                            className = "pretty-container five columns",
                                        ),
                                    ],
                                    className = "bare-container--flex--center twelve columns"
                                ),                              
                                html.Div(
                                    [     
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Label(id="finance-analysis-RandE-title", className = "label__header"),                                    
                                                        dcc.Graph(id="revenue-expenses-fig", figure = loading_fig(),config={"displayModeBar": False})
                                                    ],
                                                    className = "pretty-container six columns"
                                                ),
                                                html.Div(
                                                    [
                                                        html.Label(id="finance-analysis-AandL-title", className = "label__header"),                                       
                                                        dcc.Graph(id="assets-liabilities-fig", figure = loading_fig(),config={"displayModeBar": False})
                                                    ],
                                                    className = "pretty-container six columns"
                                                )
                                            ],
                                            className="bare-container--flex--nocenter twelve columns",
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Label(id="finance-analysis-FP-title", className = "label__header"),                                      
                                                        html.P(""),
                                                        html.Div(id="financial-position-table")
                                                    ],
                                                    className = "pretty-container--left six columns"
                                                ),
                                                html.Div(
                                                    [
                                                        html.Label(id="finance-analysis-FA-title", className = "label__header"),                                        
                                                        html.P(""),
                                                        html.Div(id="financial-activities-table")
                                                    ],
                                                    className = "pretty-container six columns",
                                                ),
                                            ],
                                            className = "bare-container--flex twelve columns",
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [                    
                                                        html.Div(id="financial-ratios-table", children=[]),
                                                    ],
                                                    className = "pretty-container--left six columns",                                        
                                                ),
                                                html.Div(
                                                    [
                                                        html.Label("Revenues and Expenditures Per Student", className = "label__header"),
                                                        html.P(""),
                                                        html.Div(id="per-student-table")
                                                    ],
                                                    className = "pretty-container six columns",
                                                ),
                                            ],
                                            className = "bare-container--flex twelve columns",
                                        ),
                                    ],
                                    id = "financial-analysis-main-container",
                                ),
                            ]
                        ),                            
                    ]
                ),
                html.Div(
                    [
                        html.Div(id="financial-analysis-no-data"),
                    ],
                    id = "financial-analysis-empty-container",
                ),
            ],
            id="main-container"
        )