######################
# Financial Analysis #
######################
# author:   jbetley
# rev:     06.29.22
# https://stackoverflow.com/questions/65124833/plotly-how-to-combine-scatter-and-line-plots-using-plotly-express/65134290#65134290

from dash import dcc, html, dash_table, Input, Output
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from app import app

# np.warnings.filterwarnings('ignore')


# Rounds y-axis ticks to nearest 50000/50000
def round_nearest(x):
    if x > 1000000:
        num = 500000
    else:
        num = 50000
    return int(round(float(x) / num) * num)


## Callback ##
@app.callback(
    Output("revenue-expenses-fig", "figure"),
    Output("assets-liabilities-fig", "figure"),
    Output("financial-position-table", "children"),
    Output("financial-activities-table", "children"),
    Output("audit-findings-table", "children"),
    Output("per-student-table", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("dash-session", "data"),
)
def update_final_page(school, year, data):
    if not school:
        raise PreventUpdate

    selected_year = str(year)

    finance_analysis = pd.DataFrame.from_dict(data["1"])
    finance_analysis = finance_analysis.iloc[:, ::-1]  # flip dataframe back to normal
    finance_analysis.index = finance_analysis.index.astype(int)  # convert index to int

    # if dataframe is empty, return empty tables/figs
    if len(finance_analysis.index) == 0:
        revenue_expenses_fig = assets_liabilities_fig = {
            "layout": {
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "annotations": [
                    {
                        "text": "No Data to Display",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {
                            "size": 16,
                            "color": "#6783a9",
                            "family": "Roboto, sans-serif",
                        },
                    }
                ],
            }
        }

        financial_position_table = (
            financial_activities_table
        ) = audit_findings_table = per_student_table = [
            dash_table.DataTable(
                columns=[
                    {"id": "emptytable", "name": "No Data to Display"},
                ],
                style_header={
                    "fontSize": "14px",
                    "border": "none",
                    "textAlign": "center",
                    "color": "#6783a9",
                    "fontFamily": "Roboto, sans-serif",
                },
            )
        ]

        return (
            revenue_expenses_fig,
            assets_liabilities_fig,
            financial_position_table,
            financial_activities_table,
            audit_findings_table,
            per_student_table,
        )

    else:
        color = [
            "#98abc5",
            "#8a89a6",
            "#7b6888",
            "#6b486b",
            "#a05d56",
            "#d0743c",
            "#ff8c00",
        ]

        for col in finance_analysis.columns:
            finance_analysis[col] = (
                pd.to_numeric(finance_analysis[col], errors="coerce")
                .fillna(finance_analysis[col])
                .tolist()
            )

        years = finance_analysis.columns.tolist()
        years.pop(0)
        years.reverse()

        #### Financial Analysis

        # Fig 1: Operating Revenue, Operating Expenses, & Change in Net Assets (Net Income)

        revenue_expenses_data = finance_analysis[
            finance_analysis["Category"].isin(
                ["Operating Expenses", "Operating Revenue"]
            )
        ]
        revenue_expenses_data = revenue_expenses_data.reset_index(drop=True)

        for col in revenue_expenses_data.columns:
            revenue_expenses_data[col] = (
                pd.to_numeric(revenue_expenses_data[col], errors="coerce")
                .fillna(revenue_expenses_data[col])
                .tolist()
            )

        # Reverse order of df (earliest -> latest) & move Category back to front
        revenue_expenses_data = revenue_expenses_data.iloc[:, ::-1]
        revenue_expenses_data.insert(
            0, "Category", revenue_expenses_data.pop("Category")
        )

        # Transpose df (to group by 'Operating Revenue' & 'Operating Expenses)
        revenue_expenses_data = revenue_expenses_data.set_index("Category").T

        # Show Operating Revenue and Expenses as grouped bars
        revenue_expenses_bar_fig = px.bar(
            data_frame=revenue_expenses_data,
            x=years,
            y=[c for c in revenue_expenses_data.columns],
            color_discrete_sequence=color,
            barmode="group",
        )

        # Adjust # of ticks based on total value (adjust '6' to increase/decrease # of ticks)

        max_val = revenue_expenses_data.melt().value.max()  # Gets highest value in df
        tick_val = round_nearest(
            max_val / 6
        )  # divides value by 6 and rounds to neared 50000/500000

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
            font=dict(family="Roboto, sans-serif", color="#6783a9", size=12),
            hovermode="x unified",
            showlegend=True,
            height=400,
            legend_title="",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        revenue_expenses_bar_fig["data"][0][
            "hovertemplate"
        ] = "Operating Revenue<br>$ %{y:,.2f}<extra></extra>"
        revenue_expenses_bar_fig["data"][1][
            "hovertemplate"
        ] = "Operating Expenses<br>$ %{y:,.2f}<extra></extra>"

        # Get Change in Net Assets Value
        revenue_expenses_line_data = finance_analysis.iloc[14].tolist()
        revenue_expenses_line_data.pop(0)
        revenue_expenses_line_data.reverse()

        revenue_expenses_line_fig = px.line(
            x=years,
            y=revenue_expenses_line_data,
            markers=True,
            color_discrete_sequence=["#d0743c"],
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

        #### Fig 2: Assets + Liabilities per year bars and Net Asset Position as Line

        assets_liabilities_data = finance_analysis[
            finance_analysis["Category"].isin(["Total Assets", "Total Liabilities"])
        ]
        assets_liabilities_data = assets_liabilities_data.reset_index(drop=True)

        for col in assets_liabilities_data.columns:
            assets_liabilities_data[col] = (
                pd.to_numeric(assets_liabilities_data[col], errors="coerce")
                .fillna(assets_liabilities_data[col])
                .tolist()
            )

        # Reverse order of df (earliest -> latest) & move Category back to front
        assets_liabilities_data = assets_liabilities_data.iloc[:, ::-1]
        assets_liabilities_data.insert(
            0, "Category", assets_liabilities_data.pop("Category")
        )

        # Transpose df (to group by 'Operating Revenue' & 'Operating Expenses)
        assets_liabilities_data = assets_liabilities_data.set_index("Category").T

        assets_liabilities_bar_fig = px.bar(
            data_frame=assets_liabilities_data,
            x=years,
            y=[c for c in assets_liabilities_data.columns],
            color_discrete_sequence=color,
            barmode="group",
        )

        max_val = assets_liabilities_data.melt().value.max()  # Gets highest value in df
        tick_val = round_nearest(
            max_val / 6
        )  # divides value by 6 and rounds to neared 50000/500000

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
            font=dict(family="Roboto, sans-serif", color="#6783a9", size=12),
            hovermode="x unified",
            showlegend=True,
            height=400,
            legend_title="",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        assets_liabilities_bar_fig["data"][1][
            "hovertemplate"
        ] = "Total Liabilities<br>$ %{y:,.2f}<extra></extra>"
        assets_liabilities_bar_fig["data"][0][
            "hovertemplate"
        ] = "Total Assets<br>$ %{y:,.2f}<extra></extra>"

        # Get Net Asset Position Value
        assets_liabilities_line_data = finance_analysis.iloc[10].tolist()
        assets_liabilities_line_data.pop(0)
        assets_liabilities_line_data.reverse()

        assets_liabilities_line_fig = px.line(
            x=years,
            y=assets_liabilities_line_data,
            markers=True,
            color_discrete_sequence=["#d0743c"],
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

        #### Year over Year comparison tables
        # Financial Position and Financial Activities tables require at least 2 years of financial data (CY, PY)
        # Audit findings table requires one year of data
        # Revenue/Expense table requires one year of data, but % Change will be N/A unless there are 2 years

        ## Get df headers (years) and filter to two most recent (or single if only one year of data)
        num_years = years
        num_years.reverse()
        num_years = num_years[:2]

        # If only one year of data, return financial position and financial activities tables will have no data
        if len(num_years) == 1:
            financial_position_table = financial_activities_table = [
                dash_table.DataTable(
                    columns=[
                        {"id": "emptytable", "name": "No Data to Display"},
                    ],
                    style_header={
                        "fontSize": "14px",
                        "border": "none",
                        "textAlign": "center",
                        "color": "#6783a9",
                        "fontFamily": "Roboto, sans-serif",
                    },
                )
            ]

        else:
            # Find values for each year (num_years[0] & num_years[1]) by matching category and add to two element list
            total_assets = [
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Total Assets"])
                ][num_years[0]].values[0],
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Total Assets"])
                ][num_years[1]].values[0],
            ]
            current_assets = [
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Current Assets"])
                ][num_years[0]].values[0],
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Current Assets"])
                ][num_years[1]].values[0],
            ]
            total_liabilities = [
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Total Liabilities"])
                ][num_years[0]].values[0],
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Total Liabilities"])
                ][num_years[1]].values[0],
            ]
            current_liabilities = [
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Current Liabilities"])
                ][num_years[0]].values[0],
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Current Liabilities"])
                ][num_years[1]].values[0],
            ]
            net_asset_position = [
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Net Asset Position"])
                ][num_years[0]].values[0],
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Net Asset Position"])
                ][num_years[1]].values[0],
            ]
            operating_revenue = [
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Operating Revenue"])
                ][num_years[0]].values[0],
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Operating Revenue"])
                ][num_years[1]].values[0],
            ]
            operating_expenses = [
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Operating Expenses"])
                ][num_years[0]].values[0],
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Operating Expenses"])
                ][num_years[1]].values[0],
            ]
            change_net_assets = [
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Change in Net Assets"])
                ][num_years[0]].values[0],
                finance_analysis.loc[
                    finance_analysis["Category"].isin(["Change in Net Assets"])
                ][num_years[1]].values[0],
            ]

            #### Financial Position Table

            financial_position = [
                [
                    "Total Assets",
                    "{:,.2f}".format(total_assets[0]),
                    "{:,.2f}".format(total_assets[1]),
                    "{:.2%}".format(
                        (total_assets[0] - total_assets[1]) / abs(total_assets[1])
                    ),
                ],
                [
                    "Current Assets",
                    "{:,.2f}".format(current_assets[0]),
                    "{:,.2f}".format(current_assets[1]),
                    "{:.2%}".format(
                        (current_assets[0] - current_assets[1]) / abs(current_assets[1])
                    ),
                ],
                [
                    "Total Liabilities",
                    "{:,.2f}".format(total_liabilities[0]),
                    "{:,.2f}".format(total_liabilities[1]),
                    "{:.2%}".format(
                        (total_liabilities[0] - total_liabilities[1])
                        / abs(total_liabilities[1])
                    ),
                ],
                [
                    "Current Liabilities",
                    "{:,.2f}".format(current_liabilities[0]),
                    "{:,.2f}".format(current_liabilities[1]),
                    "{:.2%}".format(
                        (current_liabilities[0] - current_liabilities[1])
                        / abs(current_liabilities[1])
                    ),
                ],
                [
                    "Net Asset Position",
                    "{:,.2f}".format(net_asset_position[0]),
                    "{:,.2f}".format(net_asset_position[1]),
                    "{:.2%}".format(
                        (net_asset_position[0] - net_asset_position[1])
                        / abs(net_asset_position[1])
                    ),
                ],
            ]

            financial_position_keys = ["Financial Position"] + num_years + ["% Change"]
            financial_position_data = [
                dict(zip(financial_position_keys, l)) for l in financial_position
            ]

            financial_position_table = [
                dash_table.DataTable(
                    data=financial_position_data,
                    columns=[{"name": i, "id": i} for i in financial_position_keys],
                    style_data={
                        "fontSize": "12px",
                        "border": "none",
                        "fontFamily": "Roboto, sans-serif",
                    },
                    style_data_conditional=[
                        {
                            "if": {
                                "column_id": "Financial Position",
                            },
                            "borderRight": ".5px solid #4682b4",
                        },
                        {  # Kludge to get bottom header border to show in first column
                            "if": {
                                "filter_query": '{Financial Position} eq "Total Assets"'
                            },
                            "borderTop": ".5px solid #4682b4",
                        },
                    ],
                    style_header={
                        "height": "20px",
                        "backgroundColor": "#ffffff",
                        "borderBottom": ".5px solid #6783a9",
                        "fontSize": "12px",
                        "fontFamily": "Roboto, sans-serif",
                        "color": "#6783a9",
                        "textAlign": "center",
                        "fontWeight": "700",
                        "border": "none",
                    },
                    style_header_conditional=[
                        {
                            "if": {
                                "column_id": "Financial Position",
                            },
                            "borderRight": ".5px solid #6783a9",
                            "borderBottom": ".5px solid #6783a9",
                            "textAlign": "left",
                        },
                    ],
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
                            "if": {"column_id": "Financial Position"},
                            "textAlign": "left",
                            "borderRight": ".5px solid #4682b4",
                            "borderBottom": ".5px solid #4682b4",
                            "paddingLeft": "20px",
                            "width": "40%",
                        },
                    ],
                )
            ]

            #### Financial Activities Table

            financial_activities = [
                [
                    "Operating Revenue",
                    "{:,.2f}".format(operating_revenue[0]),
                    "{:,.2f}".format(operating_revenue[1]),
                    "{:.2%}".format(
                        (operating_revenue[0] - operating_revenue[1])
                        / abs(operating_revenue[1])
                    ),
                ],
                [
                    "Operating Expenses",
                    "{:,.2f}".format(operating_expenses[0]),
                    "{:,.2f}".format(operating_expenses[1]),
                    "{:.2%}".format(
                        (operating_expenses[0] - operating_expenses[1])
                        / abs(operating_expenses[1])
                    ),
                ],
                [
                    "Change in Net Assets",
                    "{:,.2f}".format(change_net_assets[0]),
                    "{:,.2f}".format(change_net_assets[1]),
                    "{:.2%}".format(
                        (change_net_assets[0] - change_net_assets[1])
                        / abs(change_net_assets[1])
                    ),
                ],
            ]

            financial_activities_keys = (
                ["Financial Activities"] + num_years + ["% Change"]
            )
            financial_activities_data = [
                dict(zip(financial_activities_keys, l)) for l in financial_activities
            ]

            financial_activities_table = [
                dash_table.DataTable(
                    data=financial_activities_data,
                    columns=[{"name": i, "id": i} for i in financial_activities_keys],
                    style_data={
                        "fontSize": "12px",
                        "border": "none",
                        "fontFamily": "Roboto, sans-serif",
                    },
                    style_data_conditional=[
                        {
                            "if": {
                                "column_id": "Financial Activities",
                            },
                            "borderRight": ".5px solid #6783a9",
                        },
                        {
                            "if": {
                                "filter_query": '{Financial Activities} eq "Operating Revenue"'
                            },
                            "borderTop": ".5px solid #6783a9",
                        },
                    ],
                    style_header={
                        "height": "20px",
                        "backgroundColor": "#ffffff",
                        "borderBottom": ".5px solid #6783a9",
                        "fontSize": "12px",
                        "fontFamily": "Roboto, sans-serif",
                        "color": "#6783a9",
                        "textAlign": "center",
                        "fontWeight": "700",
                        "border": "none",
                    },
                    style_header_conditional=[
                        {
                            "if": {
                                "column_id": "Financial Activities",
                            },
                            "borderRight": ".5px solid #6783a9",
                            "borderBottom": ".5px solid #6783a9",
                            "textAlign": "left",
                        },
                    ],
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
                            "if": {"column_id": "Financial Activities"},
                            "textAlign": "left",
                            "borderRight": ".5px solid #6783a9",
                            "borderBottom": ".5px solid #6783a9",
                            "paddingLeft": "20px",
                            "width": "40%",
                        },
                    ],
                )
            ]

        # One year of data sufficient for audit findings and per student tables (max is two)

        #### Audit Findings Table

        audit_find = finance_analysis[
            finance_analysis["Category"].str.startswith(("Audit is", "Audit includes"))
        ]

        audit_find = audit_find.iloc[:, :3]  # display only up to first 2 years
        audit_find = audit_find.fillna(
            "N/A"
        )  # pandas automatically interprets 'N/A' as NaN - so need to force back to N/A
        audit_find.rename(columns={"Category": "Federal Audit Findings"}, inplace=True)

        audit_findings_table = [
            dash_table.DataTable(
                data=audit_find.to_dict("records"),
                columns=[{"name": i, "id": i} for i in audit_find.columns],
                # data = audit_findings_data,
                # columns = [{'name': i, 'id': i} for i in audit_findings_keys],
                style_data={
                    "fontSize": "12px",
                    "border": "none",
                    "fontFamily": "Roboto, sans-serif",
                },
                style_data_conditional=[
                    {
                        "if": {
                            "column_id": "Federal Audit Findings",
                        },
                        "borderRight": ".5px solid #6783a9",
                    },
                    {  # Kludge to get bottom header border to show in first column
                        "if": {
                            "filter_query": '{Federal Audit Findings} eq "Audit is free of findings of material weakness"'
                        },
                        "borderTop": ".5px solid #6783a9",
                    },
                ],
                style_header={
                    "height": "20px",
                    "backgroundColor": "#ffffff",
                    "borderBottom": ".5px solid #6783a9",
                    "fontSize": "12px",
                    "fontFamily": "Roboto, sans-serif",
                    "color": "#6783a9",
                    "textAlign": "center",
                    "fontWeight": "700",
                    "border": "none",
                },
                style_header_conditional=[
                    {
                        "if": {
                            "column_id": "Federal Audit Findings",
                        },
                        "borderRight": ".5px solid #6783a9",
                        "borderBottom": ".5px solid #6783a9",
                        "textAlign": "left",
                    },
                ],
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
                        "if": {"column_id": "Federal Audit Findings"},
                        "textAlign": "left",
                        "borderRight": ".5px solid #6783a9",
                        "borderBottom": ".5px solid #6783a9",
                        "paddingLeft": "20px",
                        "width": "70%",
                    },
                ],
            )
        ]

        #### Revenue/Expense per Student Table

        # create list of lists with 1st row definitions
        per_student = [
            ["State Grants"],
            ["Grants & Contributions"],
            ["Operating Revenue"],
            ["Operating Expenses"],
            ["Change in Net Assets"],
        ]

        # range is either (0,1) or (0,2) - so loops once (CY) or twice (CY & PY)
        for i in range(0, len(num_years)):
            state_grants = finance_analysis.loc[
                finance_analysis["Category"].isin(["State Grants"])
            ][num_years[i]].values[0]
            other_income = finance_analysis.loc[
                finance_analysis["Category"].isin(["Other Income"])
            ][num_years[i]].values[0]
            operating_revenue = finance_analysis.loc[
                finance_analysis["Category"].isin(["Operating Revenue"])
            ][num_years[i]].values[0]
            operating_expenses = finance_analysis.loc[
                finance_analysis["Category"].isin(["Operating Expenses"])
            ][num_years[i]].values[0]
            change_net_assets = finance_analysis.loc[
                finance_analysis["Category"].isin(["Change in Net Assets"])
            ][num_years[i]].values[0]
            adm_average = finance_analysis.loc[
                finance_analysis["Category"].isin(["ADM Average"])
            ][num_years[i]].values[0]

            per_student[0].append(float(state_grants / adm_average))
            per_student[1].append(float(other_income / adm_average))
            per_student[2].append(float(operating_revenue / adm_average))
            per_student[3].append(float(operating_expenses / adm_average))
            per_student[4].append(float(change_net_assets / adm_average))

        # calculate percentage change if 2 years of data
        if len(num_years) > 1:
            state_grant_change = (per_student[0][1] - per_student[0][2]) / abs(
                per_student[0][2]
            )
            other_income_change = (per_student[1][1] - per_student[1][2]) / abs(
                per_student[1][2]
            )
            operating_revenue_change = (per_student[2][1] - per_student[2][2]) / abs(
                per_student[2][2]
            )
            operating_expenses_change = (per_student[3][1] - per_student[3][2]) / abs(
                per_student[3][2]
            )
            change_net_assets_change = (per_student[4][1] - per_student[4][2]) / abs(
                per_student[4][2]
            )

            per_student[0].append(state_grant_change)
            per_student[1].append(other_income_change)
            per_student[2].append(operating_revenue_change)
            per_student[3].append(operating_expenses_change)
            per_student[4].append(change_net_assets_change)

            # format each list for display
            for i, x in enumerate(per_student):
                x[1] = f"{x[1]:,.2f}"
                x[2] = f"{x[2]:,.2f}"
                x[3] = f"{x[3]:,.2%}"

        # if single year of data, change is N/A
        else:
            for i in range(0, 5):
                per_student[i].append("N/A")

            # format CY of each list for display
            for i, x in enumerate(per_student):
                x[1] = f"{x[1]:,.2f}"

        per_student_keys = ["Revenue/Expense per Student"] + num_years + ["% Change"]
        per_student_data = [dict(zip(per_student_keys, l)) for l in per_student]

        per_student_table = [
            dash_table.DataTable(
                data=per_student_data,
                columns=[{"name": i, "id": i} for i in per_student_keys],
                style_data={
                    "fontSize": "12px",
                    "border": "none",
                    "fontFamily": "Roboto, sans-serif",
                },
                style_data_conditional=[
                    {
                        "if": {
                            "column_id": "Revenue/Expense per Student",
                        },
                        "borderRight": ".5px solid #6783a9",
                    },
                    {  # Kludge to get bottom header border to show in first column
                        "if": {
                            "filter_query": '{Revenue/Expense per Student} eq "State Grants"'
                        },
                        "borderTop": ".5px solid #6783a9",
                    },
                ],
                style_header={
                    "height": "20px",
                    "backgroundColor": "#ffffff",
                    "borderBottom": ".5px solid #6783a9",
                    "fontSize": "12px",
                    "fontFamily": "Roboto, sans-serif",
                    "color": "#6783a9",
                    "textAlign": "center",
                    "fontWeight": "700",
                    "border": "none",
                },
                style_header_conditional=[
                    {
                        "if": {
                            "column_id": "Revenue/Expense per Student",
                        },
                        "borderRight": ".5px solid #6783a9",
                        "borderBottom": ".5px solid #6783a9",
                        "textAlign": "left",
                    },
                ],
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
                        "if": {"column_id": "Revenue/Expense per Student"},
                        "textAlign": "left",
                        "borderRight": ".5px solid #6783a9",
                        "borderBottom": ".5px solid #6783a9",
                        "paddingLeft": "20px",
                        "width": "40%",
                    },
                ],
            )
        ]

        return (
            revenue_expenses_fig,
            assets_liabilities_fig,
            financial_position_table,
            financial_activities_table,
            audit_findings_table,
            per_student_table,
        )


#### Layout

label_style = {
    "height": "20px",
    "backgroundColor": "#6783a9",
    "fontSize": "12px",
    "fontFamily": "Roboto, sans-serif",
    "color": "#ffffff",
    "textAlign": "center",
    "fontWeight": "bold",
    "paddingBottom": "5px",
    "paddingTop": "5px",
}

layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Revenue and Expenses", style=label_style),
                        dcc.Graph(
                            id="revenue-expenses-fig",
                            figure={},
                            config={"displayModeBar": False},
                        ),
                    ],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [
                        html.Label("Assets and Liabilities", style=label_style),
                        dcc.Graph(
                            id="assets-liabilities-fig",
                            figure={},
                            config={"displayModeBar": False},
                        ),
                    ],
                    className="pretty_container six columns",
                ),
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div(
                    [html.Div(id="financial-position-table")],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [html.Div(id="financial-activities-table")],
                    className="pretty_container six columns",
                ),
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div(
                    [html.Div(id="audit-findings-table")],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [html.Div(id="per-student-table")],
                    className="pretty_container six columns",
                ),
            ],
            className="row",
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
