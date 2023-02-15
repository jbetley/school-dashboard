#######################################
# ICSB Dashboard - Financial Analysis #
#######################################
# author:   jbetley
# rev:     10.31.22

from dash import dcc, html, dash_table, Input, Output
from dash.exceptions import PreventUpdate
from dash.dash_table import FormatTemplate
import plotly.express as px
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go

from app import app

@app.callback(
    Output('revenue-expenses-fig', 'figure'),
    Output('assets-liabilities-fig', 'figure'),
    Output('financial-position-table', 'children'),
    Output('financial-activities-table', 'children'),
    Output('financial-ratios-table', 'children'),
#    Output('audit-findings-table', 'children'),
    Output('per-student-table', 'children'),
    Input('dash-session', 'data')
)
def update_about_page(data):
    if not data:
        raise PreventUpdate

    empty_table = [
            dash_table.DataTable(
                columns = [
                    {'id': 'emptytable', 'name': 'No Data to Display'},
                ],
                style_header={
                    'fontSize': '16px',
                    'border': 'none',
                    'backgroundColor': '#ffffff',
                    'paddingTop': '15px',                    
                    'verticalAlign': 'center',
                    'textAlign': 'center',
                    'color': '#6783a9',
                    'fontFamily': 'Roboto, sans-serif',
                },
            )
        ]
    # financial_info_json
    if not data['6']:  
    
        revenue_expenses_fig = assets_liabilities_fig = {
            'layout': {
                'xaxis': {
                    'visible': False
                },
                'yaxis': {
                    'visible': False
                },
                'annotations': [
                    {
                        'text': 'No Data to Display',
                        'xref': 'paper',
                        'yref': 'paper',
                        'showarrow': False,
                        'font': {
                            'size': 16,
                            'color': '#6783a9',
                            'family': 'Roboto, sans-serif'
                        }
                    }
                ]
            }
        }

        financial_position_table = financial_activities_table = financial_ratios_table = per_student_table = empty_table

        return revenue_expenses_fig, assets_liabilities_fig, financial_position_table, financial_activities_table, financial_ratios_table, per_student_table # audit_findings_table,

    else:

        # financial_info_json
        json_data = json.loads(data['6'])
        finance_analysis = pd.DataFrame.from_dict(json_data)

#        color=['#98abc5','#8a89a6','#7b6888','#6b486b','#a05d56','#d0743c','#ff8c00']
        color=['#98abc5','#7b6888','#6b486b','#a05d56','#d0743c','#ff8c00','#8a89a6']

        for col in finance_analysis.columns:
            finance_analysis[col]=pd.to_numeric(finance_analysis[col], errors='coerce').fillna(finance_analysis[col]).tolist()

        years=finance_analysis.columns.tolist()
        years.pop(0)
        years.reverse()

        # Financial Analysis

        # Fig 1: Operating Revenue, Operating Expenses, & Change in Net Assets (Net Income)
        # show Operating Revenue and Expenses as grouped bars and Change in Net Assets as line
        # https://stackoverflow.com/questions/65124833/plotly-how-to-combine-scatter-and-line-plots-using-plotly-express/65134290#65134290
        
        revenue_expenses_data = finance_analysis[finance_analysis['Category'].isin(['Operating Expenses', 'Operating Revenues'])]
        revenue_expenses_data = revenue_expenses_data.reset_index(drop=True)

        for col in revenue_expenses_data.columns:
            revenue_expenses_data[col]=pd.to_numeric(revenue_expenses_data[col], errors='coerce').fillna(revenue_expenses_data[col]).tolist()

        # Reverse order of df (earliest -> latest) & move Category back to front
        revenue_expenses_data = revenue_expenses_data.iloc[:, ::-1]
        revenue_expenses_data.insert(0, 'Category', revenue_expenses_data.pop('Category'))
        
        # Transpose df (to group by 'Operating Revenue' & 'Operating Expenses)
        revenue_expenses_data = revenue_expenses_data.set_index('Category').T
        
        revenue_expenses_bar_fig = px.bar(
            data_frame = revenue_expenses_data,
            x = years, 
            y= [c for c in revenue_expenses_data.columns],
            color_discrete_sequence=color,
            barmode='group',
        )

        # adjust the # of ticks based on max value
        # 1) gets the max value in the dataframe
        # 2) divides the max value by a 'step' value (set to six - adjust this # to increase/decrease # of ticks)
        # 2) sends the proportionate value to 'round_nearest' function that:
        #   a. sets a baseline tick amount (50,000 or 500,000) based on the proportionate value
        #   b. and then calculates a multipler that is the result of proportionate value divided by the baseline tick amount

        max_val = revenue_expenses_data.melt().value.max()
        step = 6

        def round_nearest(x):
            if x > 1000000:
                num=500000
            else:
                num=50000
            rnd = round(float(x)/num)
            multiplier = 1 if rnd < 1 else rnd
            tick = int(multiplier*num)            
            return tick

        tick_val = round_nearest(max_val / step)

        revenue_expenses_bar_fig.update_xaxes(showline=False, linecolor='#a9a9a9',ticks='outside', tickcolor='#a9a9a9', title='')
        revenue_expenses_bar_fig.update_yaxes(showgrid=True, gridcolor='#a9a9a9',title='', tickmode = 'linear', tick0 = 0,dtick = tick_val)

        revenue_expenses_bar_fig.update_layout(
            margin=dict(l=40, r=40, t=40, b=60),
            font = dict(
                family='Roboto, sans-serif',
                color='#6783a9',
                size=12
                ),
            hovermode='x unified',
            showlegend=True,
            height=400,
            legend_title='',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        revenue_expenses_bar_fig['data'][0]['hovertemplate']='Operating Revenues<br>$ %{y:,.2f}<extra></extra>'
        revenue_expenses_bar_fig['data'][1]['hovertemplate']='Operating Expenses<br>$ %{y:,.2f}<extra></extra>'

        # Get Change in Net Assets Value

        revenue_expenses_line_data = finance_analysis[finance_analysis['Category'].isin(['Change in Net Assets'])]
        revenue_expenses_line_data = revenue_expenses_line_data.reset_index(drop=True)

        revenue_expenses_line_data = revenue_expenses_line_data.replace('', 0,regex=True)

        cols=[i for i in revenue_expenses_line_data.columns if i not in ['Category']]
        for col in cols:
            revenue_expenses_line_data[col]=pd.to_numeric(revenue_expenses_line_data[col], errors='coerce')#.fillna(assets_liabilities_data[col]).tolist()

        # for col in revenue_expenses_line_data.columns:
        #     revenue_expenses_line_data[col]=pd.to_numeric(revenue_expenses_line_data[col], errors='coerce') #.fillna(tst[col]).tolist()

        revenue_expenses_line_data = revenue_expenses_line_data.iloc[:, ::-1]
        revenue_expenses_line_data.pop('Category')
        revenue_expenses_line_data = revenue_expenses_line_data.loc[:, :].values.flatten().tolist()
        
        revenue_expenses_line_fig = px.line(
            x=years,
            y=revenue_expenses_line_data,
            markers=True,
            color_discrete_sequence=['#d0743c']
        )

        revenue_expenses_fig = go.Figure(data=revenue_expenses_line_fig.data + revenue_expenses_bar_fig.data,layout=revenue_expenses_bar_fig.layout)
        revenue_expenses_fig['data'][0]['showlegend']=True
        revenue_expenses_fig['data'][0]['name']='Change in Net Assets'
        revenue_expenses_fig['data'][0]['hovertemplate']='Change in Net Assets<br>$ %{y:,.2f}<extra></extra>'

        # Fig 2: Assets + Liabilities per year bars and Net Asset Position as Line
        assets_liabilities_data = finance_analysis[finance_analysis['Category'].isin(['Total Assets', 'Total Liabilities'])]
        assets_liabilities_data=assets_liabilities_data.reset_index(drop=True)

        assets_liabilities_data = assets_liabilities_data.replace('', 0,regex=True)

        cols=[i for i in assets_liabilities_data.columns if i not in ['Category']]
        for col in cols:
            assets_liabilities_data[col]=pd.to_numeric(assets_liabilities_data[col], errors='coerce')#.fillna(assets_liabilities_data[col]).tolist()
        
        # Reverse order of df (earliest -> latest) & move Category back to front
        assets_liabilities_data = assets_liabilities_data.iloc[:, ::-1]
        assets_liabilities_data.insert(0, 'Category', assets_liabilities_data.pop('Category'))
        
        # Transpose df (to group by 'Operating Revenue' & 'Operating Expenses)
        assets_liabilities_data = assets_liabilities_data.set_index('Category').T

        assets_liabilities_bar_fig = px.bar(
            data_frame = assets_liabilities_data,
            x = years, 
            y= [c for c in assets_liabilities_data.columns],
            color_discrete_sequence=color,
            barmode='group',
        )

        max_val = assets_liabilities_data.melt().value.max()  # Gets highest value in df
        tick_val = round_nearest(max_val / step)       # divides value by step value (6) and rounds to nearest 50000/500000

        assets_liabilities_bar_fig.update_xaxes(showline=False, linecolor='#a9a9a9',ticks='outside', tickcolor='#a9a9a9', title='')
        assets_liabilities_bar_fig.update_yaxes(showgrid=True, gridcolor='#a9a9a9',title='', tickmode = 'linear', tick0 = 0,dtick = tick_val)

        assets_liabilities_bar_fig.update_layout(
            margin=dict(l=40, r=40, t=40, b=60),
            font = dict(
                family='Roboto, sans-serif',
                color='#6783a9',
                size=12
                ),
            hovermode='x unified',
            showlegend=True,
            height=400,
            legend_title='',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        assets_liabilities_bar_fig['data'][1]['hovertemplate']='Total Liabilities<br>$ %{y:,.2f}<extra></extra>'
        assets_liabilities_bar_fig['data'][0]['hovertemplate']='Total Assets<br>$ %{y:,.2f}<extra></extra>'

        # Get Net Asset Position Value
        assets_liabilities_line_data=finance_analysis.iloc[10].tolist()  
        assets_liabilities_line_data.pop(0)
        assets_liabilities_line_data.reverse()

        assets_liabilities_line_fig = px.line(
            x=years,
            y=assets_liabilities_line_data,
            markers=True,
            color_discrete_sequence=['#d0743c']
        )

        assets_liabilities_fig = go.Figure(data=assets_liabilities_line_fig.data + assets_liabilities_bar_fig.data,layout=assets_liabilities_bar_fig.layout)

        assets_liabilities_fig['data'][0]['showlegend']=True
        assets_liabilities_fig['data'][0]['name']='Net Asset Position'
        assets_liabilities_fig['data'][0]['hovertemplate']='Net Asset Position<br>$ %{y:,.2f}<extra></extra>'

        # Year over Year comparison tables
        # Financial Position and Financial Activities tables require at least 2 years of financial data (CY, PY)
        # Audit findings table requires one year of data
        # Revenue/Expense table requires one year of data, but % Change will be N/A unless there are 2 years
        
        # Get df headers (years) and filter to two most recent (or single if only one year of data)
        two_year = years
        two_year.reverse()
        two_year = two_year[:2]

        # If only one year of data, financial position and financial activities tables will have no data
        if len(two_year) == 1:

            financial_position_table = financial_activities_table = empty_table

        else:

            # TODO: This whole section is stupidly drafted
            # Refactor using per_student code below?

            # add back zeros to df for calculation purposes
            finance_analysis = finance_analysis.replace('', 0)

            # Find values for each year (two_year[0] & two_year[1]) by matching category and add to two element list
            total_assets = [finance_analysis.loc[finance_analysis['Category'].isin(['Total Assets'])][two_year[0]].values[0],finance_analysis.loc[finance_analysis['Category'].isin(['Total Assets'])][two_year[1]].values[0]]
            current_assets = [finance_analysis.loc[finance_analysis['Category'].isin(['Current Assets'])][two_year[0]].values[0],finance_analysis.loc[finance_analysis['Category'].isin(['Current Assets'])][two_year[1]].values[0]]
            total_liabilities = [finance_analysis.loc[finance_analysis['Category'].isin(['Total Liabilities'])][two_year[0]].values[0],finance_analysis.loc[finance_analysis['Category'].isin(['Total Liabilities'])][two_year[1]].values[0]]
            current_liabilities = [finance_analysis.loc[finance_analysis['Category'].isin(['Current Liabilities'])][two_year[0]].values[0],finance_analysis.loc[finance_analysis['Category'].isin(['Current Liabilities'])][two_year[1]].values[0]]
            net_asset_position = [finance_analysis.loc[finance_analysis['Category'].isin(['Net Asset Position'])][two_year[0]].values[0],finance_analysis.loc[finance_analysis['Category'].isin(['Net Asset Position'])][two_year[1]].values[0]]
            operating_revenue = [finance_analysis.loc[finance_analysis['Category'].isin(['Operating Revenues'])][two_year[0]].values[0],finance_analysis.loc[finance_analysis['Category'].isin(['Operating Revenues'])][two_year[1]].values[0]]
            operating_expenses = [finance_analysis.loc[finance_analysis['Category'].isin(['Operating Expenses'])][two_year[0]].values[0],finance_analysis.loc[finance_analysis['Category'].isin(['Operating Expenses'])][two_year[1]].values[0]]
            change_net_assets = [finance_analysis.loc[finance_analysis['Category'].isin(['Change in Net Assets'])][two_year[0]].values[0],finance_analysis.loc[finance_analysis['Category'].isin(['Change in Net Assets'])][two_year[1]].values[0]]

            # # Accounts for missing data (as a result of the DF being cleaned for display in index.py)
            # total_assets = [0 if x=='' else x for x in total_assets]
            # current_assets = [0 if x=='' else x for x in current_assets]
            # total_liabilities = [0 if x=='' else x for x in total_liabilities]
            # current_liabilities = [0 if x=='' else x for x in current_liabilities]
            # net_asset_position = [0 if x=='' else x for x in net_asset_position]
            # operating_revenue = [0 if x=='' else x for x in operating_revenue]
            # operating_expenses = [0 if x=='' else x for x in operating_expenses]
            # change_net_assets = [0 if x=='' else x for x in change_net_assets]

            financial_position = [
                ['Total Assets', '{:,.2f}'.format(total_assets[0]), '{:,.2f}'.format(total_assets[1]), '{:.2%}'.format((total_assets[0] - total_assets[1]) / abs(total_assets[1]))],
                ['Current Assets', '{:,.2f}'.format(current_assets[0]), '{:,.2f}'.format(current_assets[1]), '{:.2%}'.format((current_assets[0] - current_assets[1]) / abs(current_assets[1]))],
                ['Total Liabilities', '{:,.2f}'.format(total_liabilities[0]), '{:,.2f}'.format(total_liabilities[1]), '{:.2%}'.format((total_liabilities[0] - total_liabilities[1]) / abs(total_liabilities[1]))],
                ['Current Liabilities', '{:,.2f}'.format(current_liabilities[0]), '{:,.2f}'.format(current_liabilities[1]), '{:.2%}'.format((current_liabilities[0] - current_liabilities[1]) / abs(current_liabilities[1]))],
                ['Net Asset Position', '{:,.2f}'.format(net_asset_position[0]), '{:,.2f}'.format(net_asset_position[1]), '{:.2%}'.format((net_asset_position[0] - net_asset_position[1]) / abs(net_asset_position[1]))]
            ]

            financial_position_keys = ['Financial Position'] + two_year + ['% Change']
            financial_position_data = [dict(zip(financial_position_keys, l)) for l in financial_position]

            financial_position_table = [
                        dash_table.DataTable(
                            data = financial_position_data,
                            columns = [{'name': i, 'id': i} for i in financial_position_keys],
                            style_data={
                                'fontSize': '12px',
                                'border': 'none',
                                'fontFamily': 'Roboto, sans-serif',
                            },
                            style_data_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Financial Position',
                                    },
                                    'borderRight': '.5px solid #4682b4',
                                },
                                { # Kludge to get bottom header border to show in first column
                                    'if': {
                                        'filter_query': "{Financial Position} eq 'Total Assets'"
                                    },
                                    'borderTop': '.5px solid #4682b4',
                                },
                            ],
                            style_header={
                                'height': '20px',
                                'backgroundColor': '#ffffff',
                                'border': 'none',
                                'borderBottom': '.5px solid #6783a9',
                                'fontSize': '12px',
                                'fontFamily': 'Roboto, sans-serif',
                                'color': '#6783a9',
                                'textAlign': 'center',
                                'fontWeight': 'bold'
                            },
                            style_header_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Financial Position',
                                    },
                                    'borderRight': '.5px solid #6783a9',
                                    'borderBottom': '.5px solid #6783a9',
                                    'textAlign': 'left'
                                },
                            ],
                            style_cell={
                                'whiteSpace': 'normal',
                                'height': 'auto',
                                'textAlign': 'center',
                                'color': '#6783a9',
                                'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                            },
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Financial Position'
                                    },
                                    'textAlign': 'left',
                                    'borderRight': '.5px solid #4682b4',
                                    'borderBottom': '.5px solid #4682b4',
                                    'paddingLeft': '20px',
                                    'width': '40%'
                            },
                            ],
                        )
            ]

            financial_activities = [
                ['Operating Revenues', '{:,.2f}'.format(operating_revenue[0]), '{:,.2f}'.format(operating_revenue[1]), '{:.2%}'.format((operating_revenue[0] - operating_revenue[1]) / abs(operating_revenue[1]))],
                ['Operating Expenses', '{:,.2f}'.format(operating_expenses[0]), '{:,.2f}'.format(operating_expenses[1]), '{:.2%}'.format((operating_expenses[0] - operating_expenses[1]) / abs(operating_expenses[1]))],
                ['Change in Net Assets', '{:,.2f}'.format(change_net_assets[0]), '{:,.2f}'.format(change_net_assets[1]), '{:.2%}'.format((change_net_assets[0] - change_net_assets[1]) / abs(change_net_assets[1]))]
            ]

            financial_activities_keys = ['Financial Activities'] + two_year + ['% Change']
            financial_activities_data = [dict(zip(financial_activities_keys, l)) for l in financial_activities]

            financial_activities_table = [
                            dash_table.DataTable(
                                data = financial_activities_data,
                                columns = [{'name': i, 'id': i} for i in financial_activities_keys],
                                style_data={
                                    'fontSize': '12px',
                                    'border': 'none',
                                    'fontFamily': 'Roboto, sans-serif',
                                },
                                style_data_conditional=[
                                    {
                                        'if': {
                                            'column_id': 'Financial Activities',
                                        },
                                        'borderRight': '.5px solid #6783a9',
                                    },
                                    { 
                                        'if': {
                                            'filter_query': "{Financial Activities} eq 'Operating Revenues'"
                                        },
                                        'borderTop': '.5px solid #6783a9',
                                    },
                                ],
                                style_header={
                                    'height': '20px',
                                    'backgroundColor': '#ffffff',
                                    'border': 'none',
                                    'borderBottom': '.5px solid #6783a9',
                                    'fontSize': '12px',
                                    'fontFamily': 'Roboto, sans-serif',
                                    'color': '#6783a9',
                                    'textAlign': 'center',
                                    'fontWeight': 'bold'
                                },
                                style_header_conditional=[
                                    {
                                        'if': {
                                            'column_id': 'Financial Activities',
                                        },
                                        'borderRight': '.5px solid #6783a9',
                                        'borderBottom': '.5px solid #6783a9',
                                        'textAlign': 'left'
                                    },
                                ],
                                style_cell={
                                    'whiteSpace': 'normal',
                                    'height': 'auto',
                                    'textAlign': 'center',
                                    'color': '#6783a9',
                                    'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                                },
                                style_cell_conditional=[
                                    {
                                        'if': {
                                            'column_id': 'Financial Activities'
                                        },
                                        'textAlign': 'left',
                                        'borderRight': '.5px solid #6783a9',
                                        'borderBottom': '.5px solid #6783a9',
                                        'paddingLeft': '20px',
                                        'width': '40%'
                                },
                                ],
                            )
            ]

        # financial ratios

        ratios = ['Occupancy Ratio','Human Capital Ratio','Instruction Ratio']
        financial_ratios_data = finance_analysis[finance_analysis['Category'].isin(ratios)]
        
        # TODO: TEST THIS - is checking first value in first column is null
        if pd.isnull(financial_ratios_data.iat[0,1]):
            financial_ratios_table  = empty_table

        else:
            # display total number of display years + 1 (for category column)

            ratio_display = (len(two_year)+1)
            financial_ratios_data = financial_ratios_data.iloc[: , :ratio_display]

        # ['Occupancy Ratio (Occupancy Expense / Total Revenue) = Measures the percentage of total revenue used to occupy and maintain school facilities. A school\'s occupancy ratio generally should be less than 25%.],
        # ['Human Capital Ratio (Personnel Expense / Total Revenue) = Measures the percentage of total revenue used for payroll. A school\'s human capital ratio should be less than 50%. A human capital ratio that is significantly Higher than a school\'s instruction ratio may be a sign that the school is \'top-heavy.\'],
        # ['Instruction Ratio (Instructional Expense + Instructional Staff Expense) / Total Revenue) = Measures how much of a school\'s revenue is used to pay for instruction.]
        
        #   Ratios calculated from Form 9 data using 'process-form9.py':
        #   Total Revenue: Form 9 Section Codes 1 and 3
        #   Total Expenditures: Form 9 Section Codes 2 and 4
        #   Instructional Expense: Form 9 Object Codes 311, 312, and 313
        #   Instructional Staff Expense = Form 9 Object Codes between 110 & 290, excluding 115, 120, 121, 149, and 150  
        #   Occupancy Expense = Form 9 Object Codes 411, 431, 441, 450, between 621 & 626, and between 710 & 720
        #   Personnel Expense = Form 9 Object Codes between 110 & 290

        # TODO: ADD 'per-pupil' % for each category?

            # markdown_table = """|**Occupancy Expense** (Object Codes 411, 431, 441, 450, between 621 & 626, and between 710 & 720)|
            # |:-----------:|
            # |divided by|
            # |**Total Revenue** (Form 9 Section Codes 1 and 3) |
            # """
            financial_ratios_table = [
                        dash_table.DataTable(
                            data = financial_ratios_data.to_dict('records'),
                            columns = [{'name': i, 'id': i, 'type':'numeric','format': FormatTemplate.percentage(2)} for i in financial_ratios_data.columns],
                            tooltip_data=[
                                {
                                'Category': {
            #                        'value': markdown_table,
                                    'value': '**Occupancy Expense** (Form 9 Object Codes 411, 431, 441, 450, between 621 & 626, and between 710 & 720) \
                                     divided by **Total Revenue** (Form 9 Section Codes 1 and 3)',
                                     'type': 'markdown'},
                                },
                                {
                                'Category': {
                                    'value': '**Personnel Expense** (Form 9 Object Codes between 110 & 290) divided by **Total Revenue** (Form 9 Section Codes 1 and 3)',
                                    'type': 'markdown'},
                                },
                                {
                                'Category': {
                                    'value': '**Instruction Expense** (Form 9 Object Codes between 110 & 290- excluding 115, 120, 121, 149, and 150- \
                                    311, 312, and 313) divided by **Total Revenue** (Form 9 Section Codes 1 and 3)',
                                    'type': 'markdown'},
                                },
                            ],
                            css=[
                                {
                                    'selector': '.dash-table-tooltip',
                                    'rule': 'background-color: grey; color: white; font-size: 10px'
                                }
                            ],
                            tooltip_duration=None,
                            style_data={
                                'fontSize': '12px',
                                'border': 'none',
                                'fontFamily': 'Roboto, sans-serif',
                            },
                            style_data_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category',
                                    },
                                    'borderRight': '.5px solid #6783a9',
                                },
                                { # Kludge to get bottom header border to show in first column
                                    'if': {
                                        'filter_query': "{Category} eq 'Occupancy Ratio'"
                                    },
                                    'borderTop': '.5px solid #6783a9',
                                },
                            ],
                            style_header={
                                'height': '20px',
                                'backgroundColor': '#ffffff',
                                'borderBottom': '.5px solid #6783a9',
                                'fontSize': '12px',
                                'fontFamily': 'Roboto, sans-serif',
                                'color': '#6783a9',
                                'textAlign': 'center',
                                'fontWeight': '700',
                                'border': 'none'
                            },
                            style_header_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category',
                                    },
                                    'borderRight': '.5px solid #6783a9',
                                    'borderBottom': '.5px solid #6783a9',
                                    'textAlign': 'left'
                                },
                            ],
                            style_cell={
                                'whiteSpace': 'normal',
                                'height': 'auto',
                                'textAlign': 'center',
                                'color': '#6783a9',
                                'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                            },
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'borderRight': '.5px solid #6783a9',
                                    'borderBottom': '.5px solid #6783a9',
                                    'paddingLeft': '20px',
                                    'width': '40%'
                                },
                            ],
                        )
        ]

        # # federal_audit_findings_json
        # if not data['9']:
        #     audit_findings_table = [
        #             dash_table.DataTable(
        #             columns = [
        #                 {'id': 'emptytable', 'name': 'No Data to Display'},
        #             ],
        #             style_header={
        #                 'fontSize': '14px',
        #                 'border': 'none',
        #                 'textAlign': 'center',
        #                 'color': '#6783a9',
        #                 'fontFamily': 'Roboto, sans-serif',
        #             },
        #         )
        #     ]

        # else:

        #     # federal_audit_findings_json            
        #     json_data = json.loads(data['9'])
        #     audit_findings = pd.DataFrame.from_dict(json_data)

        #     audit_findings_table = [
        #                     dash_table.DataTable(
        #                         data = audit_findings.to_dict('records'),
        #                         columns = [{'name': i, 'id': i} for i in audit_findings.columns],
        #                         style_data={
        #                             'fontSize': '12px',
        #                             'border': 'none',
        #                             'fontFamily': 'Roboto, sans-serif',
        #                         },
        #                         style_data_conditional=[
        #                             {
        #                                 'if': {
        #                                     'column_id': 'Federal Audit Findings',
        #                                 },
        #                                 'borderRight': '.5px solid #6783a9',
        #                             },
        #                             { # Kludge to get bottom header border to show in first column
        #                                 'if': {
        #                                     'filter_query': "{Federal Audit Findings} eq 'Audit is free of findings of material weakness'"
        #                                 },
        #                                 'borderTop': '.5px solid #6783a9',
        #                             },
        #                         ],
        #                         style_header={
        #                             'height': '20px',
        #                             'backgroundColor': '#ffffff',
        #                             'borderBottom': '.5px solid #6783a9',
        #                             'fontSize': '12px',
        #                             'fontFamily': 'Roboto, sans-serif',
        #                             'color': '#6783a9',
        #                             'textAlign': 'center',
        #                             'fontWeight': '700',
        #                             'border': 'none'
        #                         },
        #                         style_header_conditional=[
        #                             {
        #                                 'if': {
        #                                     'column_id': 'Federal Audit Findings',
        #                                 },
        #                                 'borderRight': '.5px solid #6783a9',
        #                                 'borderBottom': '.5px solid #6783a9',
        #                                 'textAlign': 'left'
        #                             },
        #                         ],
        #                         style_cell={
        #                             'whiteSpace': 'normal',
        #                             'height': 'auto',
        #                             'textAlign': 'center',
        #                             'color': '#6783a9',
        #                             'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
        #                         },
        #                         style_cell_conditional=[
        #                             {
        #                                 'if': {
        #                                     'column_id': 'Federal Audit Findings'
        #                                 },
        #                                 'textAlign': 'left',
        #                                 'borderRight': '.5px solid #6783a9',
        #                                 'borderBottom': '.5px solid #6783a9',
        #                                 'paddingLeft': '20px',
        #                                 'width': '70%'
        #                         },
        #                         ],
        #                     )
        #     ]

        # Revenue/Expense per student table
        per_student = [
            ['State Grants'],
            ['Grants & Contributions'],
            ['Operating Revenues'],
            ['Operating Expenses'],
            ['Change in Net Assets']
        ]

        # change all cols to numeric except for Category
        for col in finance_analysis.columns[1:]:
            finance_analysis[col]=pd.to_numeric(finance_analysis[col], errors='coerce')

        # get per student data for applicable 2 year period
        per_student_categories = ['State Grants', 'Contributions and Donations', 'Operating Revenues', 'Operating Expenses', 'Change in Net Assets', 'ADM Average']
        per_student_data = finance_analysis.loc[finance_analysis['Category'].isin(per_student_categories)]
        per_student_data = per_student_data.iloc[:, 0:len(two_year)+1]

        # temporarily store and drop 'Category' column
        tmp_category = per_student_data['Category']
        per_student_data.drop('Category', inplace=True, axis=1)

        # divide each row by the last row in the df (which should be ADM Average)
        per_student_data = per_student_data.div(per_student_data.iloc[len(per_student_data)-1])
        
        # calculate % Change (if there are two years of data)
        if len(two_year) > 1:
            per_student_data['% Change'] = (per_student_data[two_year[0]] - per_student_data[two_year[1]]).div(abs(per_student_data[two_year[1]]))
        else:
            per_student_data['% Change'] = 'N/A'

        # # range is either (0,1) or (0,2) - so loops once (CY) or twice (CY & PY)
        # for i in range(0,len(two_year)):

        #     state_grants = finance_analysis.loc[finance_analysis['Category'].isin(['State Grants'])][two_year[i]].values[0]
        #     other_income = finance_analysis.loc[finance_analysis['Category'].isin(['Other Income'])][two_year[i]].values[0]
        #     operating_revenue = finance_analysis.loc[finance_analysis['Category'].isin(['Operating Revenues'])][two_year[i]].values[0]
        #     operating_expenses = finance_analysis.loc[finance_analysis['Category'].isin(['Operating Expenses'])][two_year[i]].values[0]
        #     change_net_assets = finance_analysis.loc[finance_analysis['Category'].isin(['Change in Net Assets'])][two_year[i]].values[0]

        #     # adm_average = finance_analysis.loc[finance_analysis['Category'].isin(['ADM Average'])][two_year[i]].values[0]
        #     # if adm_average == '':
        #     #      adm_average = finance_analysis.loc[finance_analysis['Category'].isin(['February Count'])][two_year[i]].values[0]
        #     #      if adm_average == '':
        #     #         adm_average = finance_analysis.loc[finance_analysis['Category'].isin(['September Count'])][two_year[i]].values[0]
        #     # adm_average = float(adm_average)

        #     # get all adm values as a series
        #     adm_average = finance_analysis[finance_analysis['Category'].isin(['ADM Average', 'February Count','September Count'])][two_year[i]]
            
        #     # reverse order (so most recent count is first)
        #     adm_average = adm_average.iloc[::-1]
            
        #     adm_average.replace('', np.nan, inplace=True)

        #     # find the first valid index (first non-nan)
        #     adm_average = adm_average.loc[adm_average.first_valid_index()]

        #     per_student[0].append(float(state_grants/adm_average))
        #     per_student[1].append(float(other_income/adm_average))
        #     per_student[2].append(float(operating_revenue/adm_average))
        #     per_student[3].append(float(operating_expenses/adm_average))
        #     per_student[4].append(float(change_net_assets/adm_average))

        # # calculate percentage change if 2 years of data
        # if len(two_year) > 1:

        #     state_grant_change = (per_student[0][1] - per_student[0][2]) / abs(per_student[0][2])
        #     other_income_change = (per_student[1][1] - per_student[1][2]) / abs(per_student[1][2])
        #     operating_revenue_change = (per_student[2][1] - per_student[2][2]) / abs(per_student[2][2])
        #     operating_expenses_change = (per_student[3][1] - per_student[3][2]) / abs(per_student[3][2])
        #     change_net_assets_change = (per_student[4][1] - per_student[4][2]) / abs(per_student[4][2])

        #     per_student[0].append(state_grant_change)
        #     per_student[1].append(other_income_change)
        #     per_student[2].append(operating_revenue_change)
        #     per_student[3].append(operating_expenses_change)
        #     per_student[4].append(change_net_assets_change)

        #     print(per_student)
        #     # format each list for display
        #     for i, x in enumerate(per_student):
        #         x[1] = f'{x[1]:,.2f}'
        #         x[2] = f'{x[2]:,.2f}'
        #         x[3] = f'{x[3]:,.2%}'

        # # if single year of data, change is N/A
        # else:

        #     for i in range(0,5):
        #         per_student[i].append('N/A')
        
        #     # format CY of each list for display
        #     for i, x in enumerate(per_student):
        #         x[1] = f'{x[1]:,.2f}'

        # # TODO: Still doesnt work with '%' formatting (minor issue)
        # per_student = [[x.replace('nan','N/A') for x in l] for l in per_student]
        # per_student = [[x.replace('inf','N/A') for x in l] for l in per_student]
        
        # per_student_keys = ['Revenue/Expense per Student'] + two_year + ['% Change']
        # per_student_data = [dict(zip(per_student_keys, l)) for l in per_student]

        # print(per_student_data)

        per_student_data.rename(columns={'Category':'Revenue/Expense per Student'}, inplace=True)
        per_student_data = per_student_data.iloc[:-1] # drop last row
        
        # Force correct format for display of df in datatable
        # since we are converting values to strings, we need to iterate through each series (cannot vectorize)
        # TODO: Better way to do this?
        for year in two_year:
            per_student_data[year] = pd.Series(['{:,.2f}'.format(val) for val in per_student_data[year]], index = per_student_data.index)
        per_student_data['% Change'] = pd.Series(["{0:.2f}%".format(val * 100) for val in per_student_data['% Change']], index = per_student_data.index)

        # replace inf (divide by zero) and '0' with N/A
        #per_student_data.replace([np.inf, -np.inf, 0], 'N/A', inplace=True)
        # TODO: Confirm that this works post formatting (because everythin is now a string)
        per_student_data.replace(['inf%', '0.00'], 'N/A', inplace=True)

        # reinsert Category column
        per_student_data.insert(loc=0,column='Category',value = tmp_category)

        per_student_table = [
                        dash_table.DataTable(
                            # data = per_student_data,
                            # columns = [{'name': i, 'id': i} for i in per_student_keys],
                            per_student_data.to_dict('records'),
                            columns = [{'name': i, 'id': i} for i in per_student_data.columns],
                            #columns = [{'name': i, 'id': i, 'type':'numeric','format': FormatTemplate.money(2)} for i in per_student_data.columns],
                            style_data={
                                'fontSize': '12px',
                                'border': 'none',
                                'fontFamily': 'Roboto, sans-serif',
                            },
                            style_data_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Revenue/Expense per Student',
                                    },
                                    'borderRight': '.5px solid #6783a9',
                                },
                                { # Kludge to get bottom header border to show in first column
                                    'if': {
                                        'filter_query': "{Revenue/Expense per Student} eq 'State Grants'"
                                    },
                                    'borderTop': '.5px solid #6783a9',
                                },
                            ],
                            style_header={
                                'height': '20px',
                                'backgroundColor': '#ffffff',
                                'borderBottom': '.5px solid #6783a9',
                                'fontSize': '12px',
                                'fontFamily': 'Roboto, sans-serif',
                                'color': '#6783a9',
                                'textAlign': 'center',
                                'fontWeight': '700',
                                'border': 'none'
                            },
                            style_header_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Revenue/Expense per Student',
                                    },
                                    'borderRight': '.5px solid #6783a9',
                                    'borderBottom': '.5px solid #6783a9',
                                    'textAlign': 'left'
                                },
                            ],
                            style_cell={
                                'whiteSpace': 'normal',
                                'height': 'auto',
                                'textAlign': 'center',
                                'color': '#6783a9',
                                'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                            },
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Revenue/Expense per Student'
                                    },
                                    'textAlign': 'left',
                                    'borderRight': '.5px solid #6783a9',
                                    'borderBottom': '.5px solid #6783a9',
                                    'paddingLeft': '20px',
                                    'width': '40%'
                            },
                            ],
                        )        
        ]

        return revenue_expenses_fig, assets_liabilities_fig, financial_position_table, financial_activities_table, financial_ratios_table, per_student_table # audit_findings_table,

# Layout

label_style = {
    'height': '20px',
    'backgroundColor': '#6783a9',
    'fontSize': '12px',
    'fontFamily': 'Roboto, sans-serif',
    'color': '#ffffff',
    'textAlign': 'center',
    'fontWeight': 'bold',
    'paddingBottom': '5px',
    'paddingTop': '5px'
}

layout = html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label('Revenue and Expenses', style=label_style),
                                    dcc.Graph(id='revenue-expenses-fig', figure={},config={'displayModeBar': False})
                                ],
                                className = 'pretty_container six columns'
                            ),
                            html.Div(
                                [
                                    html.Label('Assets and Liabilities', style=label_style),
                                    dcc.Graph(id='assets-liabilities-fig', figure={},config={'displayModeBar': False})
                                ],
                                className = 'pretty_container six columns'
                            )
                        ],
                        className='row'
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label('2-Year Financial Position', style=label_style),
                                    html.P(''),
                                    html.Div(id='financial-position-table')
                                ],
                                className = 'pretty_container six columns'
                            ),
                            html.Div(
                                [
                                    html.Label('2-Year Financial Activities', style=label_style),
                                    html.P(''),
                                    html.Div(id='financial-activities-table')
                                ],
                                className = 'pretty_container six columns',
                            ),
                        ],
                        className = 'row',
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label('Financial Ratios', style=label_style),
                                    html.P(''),
                                    html.Div(id='financial-ratios-table'),
                                    html.P(''),
                                    html.P('Source: IDOE Form 9 (hover over category for details).',
                                    style={
                                        'color': '#6783a9',
                                        'fontSize': 10,
                                        'marginLeft': '10px',
                                        'marginRight': '10px',
                                        'marginTop': '20px',
                                        'paddingTop': '5px',
                                        'borderTop': '.5px solid #c9d3e0',
                                        },# style={'color': '#6783a9', 'fontSize': 10})
                                    ),
                                ],
                                className = 'pretty_container six columns'
                            ),
                            # html.Div(
                            #     [
                            #         html.Label('Federal Audit Findings', style=label_style),
                            #         html.P(''),
                            #         html.Div(id='audit-findings-table')
                            #     ],
                            #     className = 'pretty_container six columns'
                            # ),
                            html.Div(
                                [
                                    html.Label('Per Student Revenues and Expenditures', style=label_style),
                                    html.P(''),
                                    html.Div(id='per-student-table')
                                ],
                                className = 'pretty_container six columns',
                            ),
                        ],
                        className = 'row',
                    )
                ]
            )

if __name__ == '__main__':
    app.run_server(debug=True)