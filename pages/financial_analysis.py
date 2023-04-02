#######################################
# ICSB Dashboard - Financial Analysis #
#######################################
# author:   jbetley
# version:  .99.021323

import dash
from dash import dcc, html, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash.dash_table import FormatTemplate
import plotly.express as px
import pandas as pd
import numpy as np
import os.path
import plotly.graph_objects as go

# import local functions
from .table_helpers import no_data_page, no_data_table
from .chart_helpers import loading_fig#, no_data_fig
from .subnav import subnav_finance
dash.register_page(__name__, path = '/financial_analysis', order=3)

@callback(
    Output('revenue-expenses-fig', 'figure'),
    Output('assets-liabilities-fig', 'figure'),
    Output('financial-position-table', 'children'),
    Output('financial-activities-table', 'children'),
    Output('radio-finance-analysis-content', 'children'),
    Output('radio-finance-analysis-display', 'style'),
    Output('finance-analysis-RandE-title', 'children'),
    Output('finance-analysis-AandL-title', 'children'),
    Output('finance-analysis-FP-title', 'children'),
    Output('finance-analysis-FA-title', 'children'),
    Output('financial-ratios-table', 'children'),
#    Output('audit-findings-table', 'children'),    # not currently displayed
    Output('per-student-table', 'children'),
    Output('financial-analysis-main-container', 'style'),
    Output('financial-analysis-empty-container', 'style'),
    Output('financial-analysis-no-data', 'children'),
    Input('dash-session', 'data'),
    Input('year-dropdown', 'value'),
    Input(component_id='radio-button-finance-analysis', component_property='value')
)
def update_financial_analysis_page(data, year, radio_value):
    if not data:
        raise PreventUpdate

    main_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_to_display = no_data_page('Financial Analysis')

    selected_year = int(year)
    max_display_years = 5
    
    school_index = pd.DataFrame.from_dict(data['0'])

    # NOTE: See financial_information.py for comments
    if school_index['Network'].values[0] != 'None':
        if radio_value == 'network-analysis':

            radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-analysis',
                        className='btn-group',
                        inputClassName='btn-check',
                        labelClassName='btn btn-outline-primary',
                        labelCheckedClassName='active',
                        options=[
                            {'label': 'School', 'value': 'school-analysis'},
                            {'label': 'Network', 'value': 'network-analysis'},
                        ],
                        value='network-analysis',
                    ),
                ],
                className='radio-group',
            )

        else:
            radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-analysis',
                        className='btn-group',
                        inputClassName='btn-check',
                        labelClassName='btn btn-outline-primary',
                        labelCheckedClassName='active',
                        options=[
                            {'label': 'School', 'value': 'school-analysis'},
                            {'label': 'Network', 'value': 'network-analysis'},
                        ],
                        value='school-analysis',
                    ),
                ],
                className='radio-group',
            )

        display_radio = {}

    else:

        radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-analysis',
                        className='btn-group',
                        inputClassName='btn-check',
                        labelClassName='btn btn-outline-primary',
                        labelCheckedClassName='active',
                        options=[],
                        value='',
                    ),
                ],
                className='radio-group',
            )

        display_radio = {'display': 'none'}

    if radio_value == 'network-analysis':
        finance_file = "data/F-" + school_index['Network'].values[0] + ".csv"
        RandE_title = 'Revenue and Expenses (' + school_index['Network'].values[0] + ')'
        AandL_title = 'Assets and Liabilities (' + school_index['Network'].values[0] + ')'
        FP_title = '2-Year Financial Position (' + school_index['Network'].values[0] + ')'
        FA_title = '2-Year Financial Activities (' + school_index['Network'].values[0] + ')'

    else:
        finance_file = "data/F-" + school_index['School Name'].values[0] + ".csv"

        # don't display school name in title if the school isn't part of a network
        if school_index['Network'].values[0] == 'None':
            RandE_title = 'Revenue and Expenses'
            AandL_title = 'Assets and Liabilities'
            FP_title = '2-Year Financial Position'
            FA_title = '2-Year Financial Activities'  
        else:
            RandE_title = 'Revenue and Expenses (' + school_index['School Name'].values[0] + ')'
            AandL_title = 'Assets and Liabilities (' + school_index['School Name'].values[0] + ')'
            FP_title = '2-Year Financial Position (' + school_index['School Name'].values[0] + ')'
            FA_title = '2-Year Financial Activities (' + school_index['School Name'].values[0] + ')'

    if os.path.isfile(finance_file):
        financial_data = pd.read_csv(finance_file)

        # NOTE: Drop partial year data - may eventually want to implement for Q4 data, but
        # the display quickly gets too confusing.
        if 'Q' in financial_data.columns[1]:
            financial_data = financial_data.drop(financial_data.columns[[1]],axis = 1)

        most_recent_finance_year = int(financial_data.columns[1])

        years_to_exclude = most_recent_finance_year - selected_year

        if years_to_exclude > 0:
            financial_data = financial_data.drop(financial_data.columns[1:years_to_exclude+1], axis=1)

        # if there are no columns or only one column ('Category'), then all tables and figs are empty
        if len(financial_data.columns) <= 1:
            financial_position_table = {}
            financial_activities_table = {}
            financial_ratios_table = {}
            per_student_table = {}

            revenue_expenses_fig = {}
            assets_liabilities_fig = {}
            main_container = {'display': 'none'}
            empty_container = {'display': 'block'}        

        else:

            color=['#98abc5','#7b6888','#6b486b','#a05d56','#d0743c','#ff8c00','#8a89a6']

            for col in financial_data.columns:
                financial_data[col]=pd.to_numeric(financial_data[col], errors='coerce').fillna(financial_data[col]).tolist()

            financial_data = financial_data.set_index(['Category'])
            financial_data.loc['Total Grants'] = financial_data.loc['State Grants'] + financial_data.loc['Federal Grants']
            financial_data.loc['Net Asset Position'] = financial_data.loc['Total Assets'] - financial_data.loc['Total Liabilities']
            financial_data.loc['Change in Net Assets'] = financial_data.loc['Operating Revenues'] - financial_data.loc['Operating Expenses']        

            financial_data = financial_data.reset_index()

            financial_data = financial_data.iloc[: , :(max_display_years+1)]

            # Duplicate data for figs - figs do not display missing years and
            # tables display missing years as blank
            financial_data_fig = financial_data.copy()

            # Network financial data typically lags behind school data by at
            # least a year. So we need to drop any column that doesn't have
            # at least 12 values not equal to 0 (the min to be valid).
            for c in financial_data_fig.columns:
                if len(financial_data_fig[financial_data_fig[c] == 0].index) > 31:
                    financial_data_fig.drop([c], inplace=True, axis=1)

            fig_years=financial_data_fig.columns.tolist()
            fig_years.pop(0)
            fig_years.reverse()

            ## Fig 1: Operating Revenue, Operating Expenses, & Change in
            # Net Assets (Net Income) show Operating Revenue and Expenses
            # as grouped bars and Change in Net Assets as line
            # https://stackoverflow.com/questions/65124833/plotly-how-to-combine-scatter-and-line-plots-using-plotly-express/65134290#65134290

            revenue_expenses_data = financial_data_fig[financial_data_fig['Category'].isin(['Operating Expenses', 'Operating Revenues'])]
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
                x = fig_years, 
                y= [c for c in revenue_expenses_data.columns],
                color_discrete_sequence=color,
                barmode='group',
            )

            # adjust the # of ticks based on max value
            # 1) gets the max value in the dataframe
            # 2) divides the max value by a 'step' value (adjust to increase/decrease of ticks)
            # 3) sends the proportionate value to 'round_nearest' function that:
            #   a. sets a baseline tick amount (50,000 or 500,000) based on the proportionate value
            #   b. and then calculates a multipler that is the result of proportionate value
            #   divided by the baseline tick amount
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
                font=dict(
                    family='Roboto, sans-serif',
                    color='#6783a9',
                    size=12
                    ),
                hovermode='x unified',
                showlegend=True,
                height=400,
                legend=dict(
                    orientation="h",
                    title='',
                    traceorder='reversed'
                    ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            revenue_expenses_bar_fig['data'][0]['hovertemplate']='Operating Revenues<br>$ %{y:,.2f}<extra></extra>'
            revenue_expenses_bar_fig['data'][1]['hovertemplate']='Operating Expenses<br>$ %{y:,.2f}<extra></extra>'

            # Get Change in Net Assets Value

            revenue_expenses_line_data = financial_data_fig[financial_data_fig['Category'].isin(['Change in Net Assets'])]
            revenue_expenses_line_data = revenue_expenses_line_data.reset_index(drop=True)

            revenue_expenses_line_data = revenue_expenses_line_data.replace('', 0,regex=True)

            cols=[i for i in revenue_expenses_line_data.columns if i not in ['Category']]
            for col in cols:
                revenue_expenses_line_data[col]=pd.to_numeric(revenue_expenses_line_data[col], errors='coerce')#.fillna(assets_liabilities_data[col]).tolist()

            revenue_expenses_line_data = revenue_expenses_line_data.iloc[:, ::-1]
            revenue_expenses_line_data.pop('Category')
            revenue_expenses_line_data = revenue_expenses_line_data.loc[:, :].values.flatten().tolist()
            
            revenue_expenses_line_fig = px.line(
                x=fig_years,
                y=revenue_expenses_line_data,
                markers=True,
                color_discrete_sequence=['#d0743c']
            )

            revenue_expenses_fig = go.Figure(data=revenue_expenses_line_fig.data + revenue_expenses_bar_fig.data,layout=revenue_expenses_bar_fig.layout)
            revenue_expenses_fig['data'][0]['showlegend']=True
            revenue_expenses_fig['data'][0]['name']='Change in Net Assets'
            revenue_expenses_fig['data'][0]['hovertemplate']='Change in Net Assets<br>$ %{y:,.2f}<extra></extra>'

            ## Fig 2: Assets + Liabilities per year bars and Net Asset Position as Line
            assets_liabilities_data = financial_data_fig[financial_data_fig['Category'].isin(['Total Assets', 'Total Liabilities'])]
            assets_liabilities_data=assets_liabilities_data.reset_index(drop=True)

            assets_liabilities_data = assets_liabilities_data.replace('', 0,regex=True)

            cols=[i for i in assets_liabilities_data.columns if i not in ['Category']]
            for col in cols:
                assets_liabilities_data[col]=pd.to_numeric(assets_liabilities_data[col], errors='coerce')
            
            # Reverse order of df (earliest -> latest) & move Category back to front
            assets_liabilities_data = assets_liabilities_data.iloc[:, ::-1]
            assets_liabilities_data.insert(0, 'Category', assets_liabilities_data.pop('Category'))
            
            # Transpose df (to group by 'Operating Revenue' & 'Operating Expenses)
            assets_liabilities_data = assets_liabilities_data.set_index('Category').T

            assets_liabilities_bar_fig = px.bar(
                data_frame = assets_liabilities_data,
                x=fig_years, 
                y = [c for c in assets_liabilities_data.columns],
                color_discrete_sequence=color,
                barmode='group',
            )

            max_val = assets_liabilities_data.melt().value.max()  # Gets highest value in df
            # divides value by step value (6) and rounds to nearest 50000/500000
            tick_val = round_nearest(max_val / step)

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
                legend=dict(
                    orientation="h",
                    title='',
                    traceorder='reversed'
                    ),  
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            assets_liabilities_bar_fig['data'][1]['hovertemplate']='Total Liabilities<br>$ %{y:,.2f}<extra></extra>'
            assets_liabilities_bar_fig['data'][0]['hovertemplate']='Total Assets<br>$ %{y:,.2f}<extra></extra>'

            # get Net Asset Position Value
            assets_liabilities_line_data=financial_data_fig.iloc[10].tolist()  
            assets_liabilities_line_data.pop(0)
            assets_liabilities_line_data.reverse()

            assets_liabilities_line_fig = px.line(
                x=fig_years,
                y=assets_liabilities_line_data,
                markers=True,
                color_discrete_sequence=['#d0743c']
            )

            assets_liabilities_fig = go.Figure(data=assets_liabilities_line_fig.data + assets_liabilities_bar_fig.data,layout=assets_liabilities_bar_fig.layout)

            assets_liabilities_fig['data'][0]['showlegend']=True
            assets_liabilities_fig['data'][0]['name']='Net Asset Position'
            assets_liabilities_fig['data'][0]['hovertemplate']='Net Asset Position<br>$ %{y:,.2f}<extra></extra>'

        ## Two Year Finance Tables (Financial Position and Financial Activities)
            # NOTE: Displaying partial data screws this all up, so probably best
            # to ignore partial data here

            # if 'Q' in financial_data.columns[1]:
            #     year = financial_data.columns[1][:4]
            #     quarter = financial_data.columns[1][4:]
            # else:
            #     quarter = ''

            previous_year = int(year) - 1
            previous_year_string = str(previous_year)

            # Display Category and Two Years of Data
            display_years = [year] + [previous_year_string]
            table_headers = ['Category'] + display_years

            # there may be columns with no or partial data at beginning or ending of dataframe,
            # this deletes any column where more than 80% of the columns values are == 0
            # (otherwise empty columns may have some data, eg., ADM)
            financial_data = financial_data.loc[:, (financial_data==0).mean() < .7]

            # if all of the years to display (+ Category) exist in (are a subset of) the dataframe,
            # filter the dataframe by the display header
            if set(table_headers).issubset(set(financial_data.columns)):
                financial_data = financial_data[table_headers]

            else:
                # identify the missing_year and the remaining_year and then add the missing_year as a blank
                # column to the dataframe either before or after remaining_year depending on which year
                # is less (earlier in time)
                missing_year = list(set(table_headers).difference(financial_data.columns))
                remaining_year = [e for e in table_headers if e not in ('Category', missing_year[0])]
                i = 1 if (int(missing_year[0]) < int(remaining_year[0])) else 0

                financial_data.insert(loc = i, column = missing_year[0], value = 0)
                financial_data = financial_data[table_headers]

            # Table 1: 2-Year Financial Position

            # get financial position data for applicable 2 year period
            financial_position_categories = ['Total Assets','Current Assets','Total Liabilities','Current Liabilities','Net Asset Position']
            financial_position_data = financial_data.loc[financial_data['Category'].isin(financial_position_categories)]

            # temporarily store and drop 'Category' column
            tmp_category = financial_position_data['Category']
            financial_position_data = financial_position_data.drop('Category', axis=1)

            # only calculate '% Change' if the number of columns with all zeros is
            # equal to 0 (e.g., all columns have nonzero values) force % formatting
            if financial_position_data.sum().eq(0).sum() == 0: 
                financial_position_data['% Change'] = (financial_position_data[display_years[0]] - financial_position_data[display_years[1]]).div(abs(financial_position_data[display_years[1]]))
                financial_position_data['% Change'] = pd.Series(["{0:.2f}%".format(val * 100) for val in financial_position_data['% Change']], index = financial_position_data.index)
            else:
                financial_position_data['% Change'] = 'N/A'

            # format numbers (since we are converting values to strings, we cannot vectorize,
            # need to iterate through each series)
            for year in display_years:
                financial_position_data[year] = pd.Series(['{:,.2f}'.format(val) for val in financial_position_data[year]], index = financial_position_data.index)

            # other clean-up for display purposes
            financial_position_data.replace('nan','0', inplace=True)
            financial_position_data.replace(['inf%', '0.00', '0.0', '0', np.inf, -np.inf], 'N/A', inplace=True)

            # reinsert Category column
            financial_position_data.insert(loc=0,column='Category',value = tmp_category)

            financial_position_table = [
                        dash_table.DataTable(
                            financial_position_data.to_dict('records'),
                            columns = [{'name': i, 'id': i} for i in financial_position_data.columns],
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
                                    'borderRight': '.5px solid #4682b4',
                                },
                                { # Kludge to get bottom header border to show in first column
                                    'if': {
                                        'filter_query': "{Category} eq 'Total Assets'"
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
                                    'borderRight': '.5px solid #4682b4',
                                    'borderBottom': '.5px solid #4682b4',
                                    'paddingLeft': '20px',
                                    'width': '40%'
                            },
                            ],
                        )
            ]

            # Table 2: 2-Year Financial Activities
            financial_activity_categories = ['Operating Revenues', 'Operating Expenses', 'Change in Net Assets']
            financial_activity_data = financial_data.loc[financial_data['Category'].isin(financial_activity_categories)]

            # temporarily store and drop 'Category' column
            tmp_category = financial_activity_data['Category']
            
            financial_activity_data = financial_activity_data.drop('Category', axis=1)

            # find percentage difference (df will have minimum of 1 column,
            # maximum of two columns) only calculates change if the number
            # of columns with all zeros is equal to 0 (e.g., all columns have nonzero values)
            if financial_activity_data.sum().eq(0).sum() == 0:
                financial_activity_data['% Change'] = (financial_activity_data[display_years[0]] - financial_activity_data[display_years[1]]).div(abs(financial_activity_data[display_years[1]]))
            else:
                financial_activity_data['% Change'] = 'N/A'
            
            # Force correct formats for display of df in datatable
            if financial_activity_data.sum().eq(0).sum() == 0:
                financial_activity_data['% Change'] = pd.Series(["{0:.2f}%".format(val * 100) for val in financial_activity_data['% Change']], index = financial_activity_data.index)

            # since we are converting values to strings, we need to iterate
            # through each series (cannot vectorize)
            for year in display_years:
                financial_activity_data[year] = pd.Series(['{:,.2f}'.format(val) for val in financial_activity_data[year]], index = financial_activity_data.index)

            # clean up for display
            financial_activity_data.replace('nan','0', inplace=True)
            financial_activity_data.replace(['inf%', '0.00', '0.0', '0', np.inf, -np.inf], 'N/A', inplace=True)

            # reinsert Category column
            financial_activity_data.insert(loc=0,column='Category',value = tmp_category)

            financial_activities_table = [
                            dash_table.DataTable(
                                financial_activity_data.to_dict('records'),
                                columns = [{'name': i, 'id': i} for i in financial_activity_data.columns],                                    
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
                                    { 
                                        'if': {
                                            'filter_query': "{Category} eq 'Operating Revenues'"
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

            # Table #3: Per-Student Expenditures

            # get per student data for applicable 2 year period
            per_student_categories = ['State Grants', 'Contributions and Donations', 'Operating Revenues', 'Operating Expenses', 'Change in Net Assets', 'ADM Average']
            per_student_data = financial_data.loc[financial_data['Category'].isin(per_student_categories)].copy()

            # change all cols to numeric except for Category
            for col in per_student_data.columns[1:]:
                per_student_data[col]=pd.to_numeric(per_student_data[col], errors='coerce')

            # temporarily store and drop 'Category' column
            tmp_category = per_student_data['Category']
            per_student_data = per_student_data.drop('Category', axis=1)

            # Financial information that includes State Grants but not ADM is
            # an indication of an error. If there is financial information that
            # does not include State Grants or ADM, it is likely Year 0

            # divide each row by the last row in the df (which should be ADM Average)
            per_student_data = per_student_data.div(per_student_data.iloc[len(per_student_data)-1])
            
            # calculate '% Change' if both years have non-zero values
            if per_student_data.sum().eq(0).sum() == 0:
                per_student_data['% Change'] = (per_student_data[display_years[0]] - per_student_data[display_years[1]]).div(abs(per_student_data[display_years[1]]))
            else:
                per_student_data['% Change'] = 'N/A'

            per_student_data = per_student_data.iloc[:-1] # drop last row (ADM Average) for display

            # Force correct format for display of df in datatable
            if per_student_data.sum().eq(0).sum() == 0:
                per_student_data['% Change'] = pd.Series(["{0:.2f}%".format(val * 100) for val in per_student_data['% Change']], index = per_student_data.index)

            # since we are converting values to strings, we need to iterate through each series (cannot vectorize)
            for year in display_years:
                per_student_data[year] = pd.Series(['{:,.2f}'.format(val) for val in per_student_data[year]], index = per_student_data.index)

            # clean up for display (this is lazy)
            per_student_data.replace('nan','0', inplace=True)
            per_student_data.replace(['inf%', 'nan%', '0.00', '0.0', '0', np.inf, -np.inf], 'N/A', inplace=True)

            # reinsert Category column
            per_student_data.insert(loc=0,column='Category',value = tmp_category)

            per_student_table = [
                            dash_table.DataTable(
                                per_student_data.to_dict('records'),
                                columns = [{'name': i, 'id': i} for i in per_student_data.columns],
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
                                            'filter_query': "{Category} eq 'State Grants'"
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

            # Table 4: Financial Ratios
            # Get financial ratios
            school_corp = school_index['Corporation ID'].values[0]
            
            financial_ratios_data = pd.read_csv(r'data/financial_ratios.csv', dtype=str)
            financial_ratios_data = financial_ratios_data.loc[financial_ratios_data['School Corporation'] == school_corp]

            # Networks do not have ratios- only way to tell if network finances
            # are being displayed is if the radio_value is equal to 'network-finance.'
            # So we show an empty table if 'network-finance' is being displayed.
            # We also show empty table if there are no rows in financial_ratios_data
            # (empty df) OR where there are no years of data in the dataframe that
            # match the years being displayed (the last condition is True if the
            # two lists share at least one item (e.g., at least one of the
            # table_headers are in the Years dataframe column)).

            if radio_value != 'network-finance' and (len(financial_ratios_data.index) != 0) and \
                not set(financial_ratios_data['Year'].tolist()).isdisjoint(table_headers):

                # drop unused columns, transpose and rename
                financial_ratios_data = financial_ratios_data.drop(columns=['Corporation Name','School Corporation'])
                financial_ratios_data = financial_ratios_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()

                # ensure data is adjusted to display from the selected year
                # if years_to_exclude > 0:
                #     financial_ratios_data = financial_ratios_data.drop(financial_ratios_data.columns[1:years_to_exclude], axis=1)

                # change all cols to numeric except for Category
                for col in financial_ratios_data.columns[1:]:
                    financial_ratios_data[col]=pd.to_numeric(financial_ratios_data[col], errors='coerce')

                # Form 9 data usually lags financial data by at least a year-
                # so not uncommon if current year is missing from ratios dataframe.
                # If missing, add a blank column with the missing year as header
                ratio_display = ['Category'] + display_years
                missing_year = list(sorted(set(ratio_display) - set(financial_ratios_data.columns.tolist())))
                if missing_year:
                    i = 1
                    for m in missing_year:
                        financial_ratios_data.insert(loc = i, column = m, value = 'N/A')
                        i+=1

                # Limit display to the same two years that are available for all other financial data
                financial_ratios_data = financial_ratios_data[ratio_display]

                # Force correct format for display of numeric (not N/A) columns in df
                for year in display_years:
                    if (financial_ratios_data[year] != 'N/A').any():
                        financial_ratios_data[year] = pd.Series(['{0:.2f}%'.format(val * 100) for val in financial_ratios_data[year]], index = financial_ratios_data.index)

        # ['Occupancy Ratio (Occupancy Expense / Total Revenue) = Measures
        # the percentage of total revenue used to occupy and maintain school
        # facilities. A school\'s occupancy ratio generally should be less than 25%.],
        # ['Human Capital Ratio (Personnel Expense / Total Revenue) = Measures
        # the percentage of total revenue used for payroll. A school\'s human
        # capital ratio should be less than 50%. A human capital ratio that is
        # significantly Higher than a school\'s instruction ratio may be a sign
        # that the school is \'top-heavy.\'],
        # ['Instruction Ratio (Instructional Expense + Instructional Staff Expense)
        # / Total Revenue) = Measures how much of a school\'s revenue is used to pay for instruction.]
        
        #   Ratios calculated from Form 9 data using 'process-form9.py':
        #   Total Revenue: Form 9 Section Codes 1 and 3
        #   Total Expenditures: Form 9 Section Codes 2 and 4
        #   Instructional Expense: Form 9 Object Codes 311, 312, and 313
        #   Instructional Staff Expense = Form 9 Object Codes between 110
        #   & 290, excluding 115, 120, 121, 149, and 150  
        #   Occupancy Expense = Form 9 Object Codes 411, 431, 441, 450,
        #   between 621 & 626, and between 710 & 720
        #   Personnel Expense = Form 9 Object Codes between 110 & 290

                # markdown_table = """|**Occupancy Expense** (Object Codes 411, 431, 441, 450,
                # between 621 & 626, and between 710 & 720)|
                # |:-----------:|
                # |divided by|
                # |**Total Revenue** (Form 9 Section Codes 1 and 3) |
                # """
                financial_ratios_table = [
                    # html.Div(
                    #     [          
                            html.Label('Financial Ratios', style=label_style),
                            html.P(''),
                            html.Div(
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
                                ),
                            ),
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
                                },
                            ),                            
                    #     ],
                    #     className = 'pretty_container six columns',
                    # )
                ]

            else:
                financial_ratios_table  = no_data_table('Financial Ratios')

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

    else:
        financial_position_table = {}
        financial_activities_table = {}
        financial_ratios_table = {}
        per_student_table = {}

        revenue_expenses_fig = {}
        assets_liabilities_fig = {}
        main_container = {'display': 'none'}
        empty_container = {'display': 'block'}       

    return revenue_expenses_fig, assets_liabilities_fig, financial_position_table,\
        financial_activities_table, radio_content, display_radio, RandE_title, \
        AandL_title, FP_title, FA_title, financial_ratios_table, per_student_table, \
        main_container, empty_container, no_data_to_display # audit_findings_table,

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

def layout():
    return html.Div(
                [

                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(subnav_finance(),className='tabs'),
                                ],
                                className='bare_container twelve columns'
                            ),
                        ],
                        className='row'
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id='radio-finance-analysis-content', children=[]),
                                ],
                                id = 'radio-button-finance-analysis',
                                ),
                        ],
                        id = 'radio-finance-analysis-display',
                    ),
                    html.Div(
                        [                    
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label(id='finance-analysis-RandE-title', style=label_style),                                    
                                            dcc.Graph(id='revenue-expenses-fig', figure = loading_fig(),config={'displayModeBar': False})
                                        ],
                                        className = 'pretty_container six columns'
                                    ),
                                    html.Div(
                                        [
                                            html.Label(id='finance-analysis-AandL-title', style=label_style),                                       
                                            dcc.Graph(id='assets-liabilities-fig', figure = loading_fig(),config={'displayModeBar': False})
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
                                            html.Label(id='finance-analysis-FP-title', style=label_style),                                      
                                            html.P(''),
                                            html.Div(id='financial-position-table')
                                        ],
                                        className = 'pretty_container six columns'
                                    ),
                                    html.Div(
                                        [
                                            html.Label(id='finance-analysis-FA-title', style=label_style),                                        
                                            html.P(''),
                                            html.Div(id='financial-activities-table')
                                        ],
                                        className = 'pretty_container six columns',
                                    ),
                                ],
                                className = 'row',
                            ),
                        # html.Div(
                            #     [   
                            #        
                            #         html.Div(
                            #             [
                                            
                            #                 html.P(''),
                            #                 html.Div(id='financial-ratios-table'),
                            #                 html.P(''),
                            #                 html.P('Source: IDOE Form 9 (hover over category for details).',
                            #                 style={
                            #                     'color': '#6783a9',
                            #                     'fontSize': 10,
                            #                     'marginLeft': '10px',
                            #                     'marginRight': '10px',
                            #                     'marginTop': '20px',
                            #                     'paddingTop': '5px',
                            #                     'borderTop': '.5px solid #c9d3e0',
                            #                     },
                            #                 ),
                            #             ],
                            #             className = 'pretty_container six columns'
                            #         ),
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
                                    html.Div(
                                        [                    
                                            html.Div(id='financial-ratios-table', children=[]),
                                        ],
                                        className = 'pretty_container six columns',                                        
                                    ),
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
                            ),
                        ],
                        id = 'financial-analysis-main-container',
                    ),
                    html.Div(
                        [
                            html.Div(id='financial-analysis-no-data'),
                        ],
                        id = 'financial-analysis-empty-container',
                    ),
                ],
                id='mainContainer',
                style={
                    'display': 'flex',
                    'flexDirection': 'column'
                }
            )