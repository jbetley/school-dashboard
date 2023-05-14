######################################
# ICSB Dashboard - Financial Metrics #
######################################
# author:   jbetley
# version:  1.02.051023

import dash
from dash import html, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
import os.path

# import local functions
from .calculations import calculate_metrics
from .table_helpers import no_data_page, get_svg_circle, create_key
from .subnav import subnav_finance

dash.register_page(__name__, path='/financial_metrics', order=2)

@callback(
    Output('financial-metrics-table', 'children'),
    Output('radio-finance-metrics-content', 'children'),
    Output('radio-finance-metrics-display', 'style'),
    Output('financial-indicators-table', 'children'),
    Output('financial-metrics-definitions-table', 'children'),
    Output('financial-metrics-main-container', 'style'),
    Output('financial-metrics-empty-container', 'style'),
    Output('financial-metrics-no-data', 'children'),      
    Input('dash-session', 'data'),
    Input('year-dropdown', 'value'),
    Input(component_id='radio-button-finance-metrics', component_property='value')
)
def update_financial_metrics(data,year,radio_value):
    if not data:
         raise PreventUpdate

    main_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_to_display = no_data_page('Financial Metrics')

    selected_year = int(year)

    max_display_years = 5

    school_index = pd.DataFrame.from_dict(data['0'])

    # NOTE: See financial_information.py for comments
    if school_index['Network'].values[0] != 'None':
        if radio_value == 'network-metrics':
            radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-metrics',
                        className='btn-group',
                        inputClassName='btn-check',
                        labelClassName='btn btn-outline-primary',
                        labelCheckedClassName='active',
                        options=[
                            {'label': 'School', 'value': 'school-metrics'},
                            {'label': 'Network', 'value': 'network-metrics'},
                        ],
                        value='network-metrics',
                    ),
                ],
                className='radio-group',
            )

        else:
            radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-metrics',
                        className='btn-group',
                        inputClassName='btn-check',
                        labelClassName='btn btn-outline-primary',
                        labelCheckedClassName='active',
                        options=[
                            {'label': 'School', 'value': 'school-metrics'},
                            {'label': 'Network', 'value': 'network-metrics'},
                        ],
                        value='school-metrics',
                    ),
                ],
                className='radio-group',
            )

        display_radio = {}

    else:
        radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-metrics',
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

    if radio_value == 'network-metrics':
        finance_file = 'data/F-' + school_index['Network'].values[0] + '.csv'
        table_title = 'Financial Accountability Metrics (' + school_index['Network'].values[0] + ')'
    else:
        finance_file = 'data/F-' + school_index['School Name'].values[0] + '.csv'
        
        # don't display school name in title if the school isn't part of a network
        if school_index['Network'].values[0] == 'None':
            table_title = 'Financial Accountability Metrics'
        else:
            table_title = 'Financial Accountability Metrics (' + school_index['School Name'].values[0] + ')'

    if os.path.isfile(finance_file):
        financial_data = pd.read_csv(finance_file)
        
        # in order for metrics to be calculated properly, we need
        # to temporarily store and remove the (Q#) part of string
        financial_quarter = ''
        financial_quarter = financial_data.columns[1][5:] if len(financial_data.columns[1]) > 4 else ''
        financial_data = financial_data.rename(columns = lambda x : str(x)[:4] if x != 'Category' else x)

        most_recent_finance_year = int(financial_data.columns[1])

        years_to_exclude = most_recent_finance_year - selected_year
        
        current_academic_year = int(data['15']['current_academic_year'])

        if selected_year < current_academic_year:
            financial_data.drop(financial_data.columns[1:years_to_exclude+1], axis=1, inplace=True)

        # create_empty_table() if file exists, but has no financial data, or
        # if file exists and has one year of data, but does not have
        # a value for any State Grants (the school is in Pre-Opening)

        # NOTE: To show schools in Pre-Opening year, remove the 'or' condition
        # (also need to modify the financial metric calculation function)
        
        if (len(financial_data.columns) <= 1) | ((len(financial_data.columns) == 2) and (financial_data.iloc[1][1] == '0')):
                financial_metrics_table = {}
                financial_indicators_table = {}
                financial_metrics_definitions_table = {}
                main_container = {'display': 'none'}
                empty_container = {'display': 'block'}
        else:

            for col in financial_data.columns:
                financial_data[col]=pd.to_numeric(financial_data[col], errors='coerce').fillna(financial_data[col]).tolist()

            # see financial_information.py
            financial_data = financial_data.set_index(['Category'])
            financial_data.loc['Total Grants'] = financial_data.loc['State Grants'] + financial_data.loc['Federal Grants']
            financial_data.loc['Net Asset Position'] = financial_data.loc['Total Assets'] - financial_data.loc['Total Liabilities']
            financial_data.loc['Change in Net Assets'] = financial_data.loc['Operating Revenues'] - financial_data.loc['Operating Expenses']        
            financial_data = financial_data.reset_index()

            # Ensure only 'max_display_years' (currently 5) of financial data
            # is displayed (add +1 to max_display_years to account for the
            # category column). To show all financial data, comment out this
            # line. This may cause unexpected errors elsewhere.
            financial_data = financial_data.iloc[: , :(max_display_years+1)]

            # remove audit and other indicator data (it is displayed on the financial metrics page)
            financial_values = financial_data.drop(financial_data.index[41:])

            # Release The Hounds!
            financial_metrics = calculate_metrics(financial_values)
            
            # convert ratings to colored circles
            financial_metrics = get_svg_circle(financial_metrics)

            financial_metrics = financial_metrics.fillna('')

            # Force correct format for display of df in datatable
            for x in range(1,len(financial_metrics.columns),2):
                if financial_metrics.iat[3,x]:
                    financial_metrics.iat[3,x] = '{:.0%}'.format(financial_metrics.iat[3,x])
                if financial_metrics.iat[9,x]:
                    financial_metrics.iat[9,x] = '{:,.2f}'.format(financial_metrics.iat[9,x])
                if financial_metrics.iat[10,x]:
                    financial_metrics.iat[10,x] = '{:,.2f}'.format(financial_metrics.iat[10,x])

            # Add financial quarter back to financial header for display purposes (if partial
            # year is being displayed)
            if int(financial_metrics.columns[1]) > current_academic_year:
                financial_metrics = financial_metrics.rename(columns={financial_metrics.columns[1]: financial_metrics.columns[1] + financial_quarter})

            headers = financial_metrics.columns.tolist()

            # input: table_size
            # output: col_width, category_width, rating_width, and year_width, (difference_width, corporation_width)
            # Problem: variable number of return items. table_size adjustments are differente between financial
            # metrics table and academic metrics table

            clean_headers = []
            for i, x in enumerate (headers):
                if 'Rating' in x:
                    clean_headers.append('Rate')
                else:
                    clean_headers.append(x)

            year_headers = [i for i in headers if 'Rating' not in i and 'Metric' not in i]
            rating_headers = [y for y in headers if 'Rating' in y]

            # determines the col_width class and width of the category
            # column based on the size on the dataframe
            table_size = len(financial_metrics.columns)

            if table_size <= 3:
                col_width = 'four'
                category_width = 70
            if table_size > 3 and table_size <=4:
                col_width = 'six'
                category_width = 35
            elif table_size >= 5 and table_size <= 8:
                col_width = 'six'
                category_width = 30
            elif table_size == 9:
                col_width = 'seven'
                category_width = 30
            elif table_size >= 10 and table_size <= 13:
                col_width = 'eight'
                category_width = 25
            elif table_size > 13 and table_size <=17:
                col_width = 'nine'
                category_width = 15
            elif table_size > 17:
                col_width = 'ten'
                category_width = 15

            # this splits column width evenly for all columns other than 'Category'
            data_width = 100 - category_width
            data_col_width = data_width / (table_size - 1)
            rating_width = year_width = data_col_width
            rating_width = rating_width / 2

            class_name = 'pretty_container ' + col_width + ' columns'

            financial_metrics_table = [
                html.Div(
                    [                
                        html.Div(
                            [
                                html.Label(table_title, className='header_label'),
                                html.Div(
                                    dash_table.DataTable(
                                        financial_metrics.to_dict('records'),
                                        columns=[
                                            {'name': col,'id': headers[idx], 'presentation': 'markdown'}
                                            if 'Rate' in col
                                            else {'name': col, 'id': headers[idx]}
                                            for (idx, col) in enumerate(clean_headers)
                                        ],                                            
                                        style_data={
                                            'fontSize': '11px',
                                            'border': 'none',
                                            'fontFamily': 'Jost, sans-serif',
                                        },
                                        style_data_conditional=
                                        [
                                            {
                                                'if': {
                                                    'row_index': 'odd'
                                                },
                                                'backgroundColor': '#eeeeee',
                                            },
                                            {
                                                'if': {
                                                    'filter_query': "{Metric} eq 'Near Term' || {Metric} eq 'Long Term' || {Metric} eq 'Other Metrics'"
                                                },
                                                'paddingLeft': '10px',
                                                'text-decoration': 'underline',
                                                'fontWeight': 'bold'
                                            },
                                        ],
                                        style_header={
                                            'height': '20px',
                                            'backgroundColor': '#ffffff',
                                            'border': 'none',
                                            'borderBottom': '.5px solid #6783a9',
                                            'fontSize': '12px',
                                            'fontFamily': 'Jost, sans-serif',
                                            'color': '#6783a9',
                                            'textAlign': 'center',
                                            'fontWeight': 'bold'
                                        },
                                        style_cell={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'textAlign': 'center',
                                            'color': '#6783a9',
                                            'boxShadow': '0 0',
                                        },
                                        style_cell_conditional=[
                                            {
                                                'if': {
                                                    'column_id': 'Metric'
                                                },
                                                'textAlign': 'left',
                                                'paddingLeft': '20px',                                                
                                                'fontWeight': '500',
                                                'width': str(category_width) + '%'
                                            },
                                        ] + [
                                            {
                                                'if': {
                                                    'column_id': year
                                                },
                                                'textAlign': 'center',
                                                'fontWeight': '500',
                                                'width': str(year_width) + '%',
                                            } for year in year_headers
                                        ] + [  
                                            {
                                                'if': {
                                                    'column_id': rating
                                                },
                                                'textAlign': 'center',
                                                'fontWeight': '500',                                                
                                                'width': str(rating_width) + '%',
                                            } for rating in rating_headers
                                        ],
                                        style_as_list_view=True,
                                        markdown_options={'html': True},
                                    )
                                )
                            ],
                            className = class_name,
                        ),
                    ],
                    className = 'bare_container twelve columns',
                )
            ]

            # Financial Indicators
            financial_indicators = financial_data[financial_data['Category'].str.startswith('2.1.')].copy()

            # Networks do not have financial indicators
            if len(financial_indicators.columns) <= 1 or financial_indicators.empty:
                financial_indicators_table = no_data_page('Financial Indicators')

            else:
                financial_indicators[['Standard','Description']] = financial_indicators['Category'].str.split('|', expand=True).copy()

                # reorder and clean up dataframe
                financial_indicators = financial_indicators.drop('Category', axis=1)
                standard = financial_indicators['Standard']
                description = financial_indicators['Description']
                financial_indicators = financial_indicators.drop(columns=['Standard','Description'])
                financial_indicators.insert(loc=0, column='Description', value = description)
                financial_indicators.insert(loc=0, column='Standard', value = standard)

                # convert ratings to colored circles
                financial_indicators = get_svg_circle(financial_indicators)

                headers = financial_indicators.columns.tolist()
                year_headers = [x for x in headers if 'Description' not in x and 'Standard' not in x]

                financial_indicators_table = [
                        html.Div(
                            [             
                                html.Div(
                                    [
                                        html.Label('Other Financial Accountability Indicators', className='header_label'),
                                        html.Div(
                                            dash_table.DataTable(
                                                financial_indicators.to_dict('records'),
                                                columns=[
                                                    {'name': col,'id': headers[idx], 'presentation': 'markdown'}
                                                    if col in year_headers
                                                    else {'name': col, 'id': headers[idx]}
                                                    for (idx, col) in enumerate(headers)
                                                ],                                                   
                                                style_data={
                                                    'fontSize': '12px',
                                                    'fontFamily': 'Jost, sans-serif',
                                                    'border': 'none'
                                                },
                                                style_data_conditional=
                                                [
                                                    {
                                                        'if': {
                                                            'row_index': 'odd'
                                                        },
                                                        'backgroundColor': '#eeeeee',
                                                    },
                                                ] + [
                                                    {
                                                        'if': {
                                                            'column_id': year
                                                        },
                                                        'textAlign': 'center',
                                                        'fontWeight': '500',
                                                        'width': '8%',
                                                    } for year in year_headers
                                                ],
                                                style_header={
                                                    'height': '20px',
                                                    'backgroundColor': '#ffffff',
                                                    'border': 'none',
                                                    'borderBottom': '.5px solid #6783a9',
                                                    'fontSize': '12px',
                                                    'fontFamily': 'Jost, sans-serif',
                                                    'color': '#6783a9',
                                                    'textAlign': 'center',
                                                    'fontWeight': 'bold'
                                                },
                                                style_cell={
                                                    'whiteSpace': 'normal',
                                                    'height': 'auto',
                                                    'textAlign': 'center',
                                                    'color': '#6783a9',
                                                    # 'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                                                },
                                                style_cell_conditional=[
                                                    {
                                                        'if': {
                                                            'column_id': 'Standard'
                                                        },
                                                        'textAlign': 'center',
                                                        'fontWeight': '500',
                                                        'width': '7%',
                                                    },
                                                    {
                                                        'if': {
                                                            'column_id': 'Description'
                                                        },
                                                        'width': '45%',
                                                        'textAlign': 'Left',
                                                        'fontWeight': '500',
                                                        'paddingLeft': '20px',
                                                    },
                                                ],
                                                markdown_options={'html': True},                                                
                                            ),
                                        ),
                                    ],
                                    className = 'pretty_container eight columns',
                                ),
                            ],
                            className = 'bare_container twelve columns',
                        )
                    ]
            
            # Financial Metric Definitions
            # NOTE: Explore better styling- Markdown or Images
            # http://www.latex2png.com/
            # https://stackoverflow.com/questions/70205486/clickable-hyperlinks-in-plotly-dash-datatable
            # https://stackoverflow.com/questions/66583063/how-to-add-hyperlink-in-column-field-of-dash-datatable

            financial_metrics_definitions_data = [
                ['Current Ratio = Current Assets ÷ Current Liabilities','Current Ratio is greater than 1.1; or is between 1.0 and 1.1 and the one-year trend is not negative.'],
                ['Days Cash on Hand = Unrestricted Cash ÷ ((Operating Expenses - Depreciation Expense) ÷ 365)','School has greater than 45 unrestricted days cash; or between 30 - 45 unrestricted days cash and the one-year trend is not negative.'],
                ['Annual Enrollment Change = (Current Year ADM - Previous Year ADM) ÷ Previous Year ADM','Annual Enrollment Change increases or shows a current year decrease of less than 10%.'],
                ['Primary Reserve Ratio = Unrestricted Net Assets ÷ Operating Expenses','Primary Reserve Ratio is greater than .25.'],
                ['Change in Net Assets Margin = (Operating Revenues - Operating Expenses) ÷ Operating Revenues ; Aggregated 3-Year Margin = (3 Year Operating Revenues - 3 Year Operating Expense) ÷ 3 Year Operating Revenues','Aggregated Three-Year Margin is positive and the most recent year Change in Net Assets Margin is positive; or Aggregated Three-Year Margin is greater than -1.5%, the trend is positive for the last two years, and Change in Net Assets Margin for the most recent year is positive. For schools in their first and second year of operation, the cumulative Change in Net Assets Margin must be positive.'],
                ['Debt to Asset Ratio = Total Liabilities ÷ Total Assets','Debt to Asset Ratio is less than 0.9.'],
                ['One Year Cash Flow = Recent Year Total Cash - Previous Year Total Cash; Multi-Year Cash Flow = Recent Year Total Cash - Two Years Previous Total Cash','Multi-Year Cash Flow is positive and One Year Cash Flow is positive in two out of three years, including the most recent year. For schools in the first two years of operation, both years must have a positive Cash Flow (for purposes of calculating Cash Flow, the school\'s Year 0 balance is assumed to be zero).'],
                ['Debt Service Coverage Ratio = (Change in Net Assets + Depreciation/Amortization Expense + Interest Expense + Rent/Lease Expense) ÷ (Principal Payments + Interest Expense + Rent/Lease Expense)','Debt Service Coverage Ratio is greater than or equal to 1.0.']
            ]

            financial_metrics_definitions_keys = ['Calculation','Requirement to Meet Standard']
            financial_metrics_definitions_dict = [dict(zip(financial_metrics_definitions_keys, l)) for l in financial_metrics_definitions_data ]

            financial_metrics_definitions_table = [
                html.Div(
                    [             
                        html.Div(
                            [
                            html.Label('Accountability Metrics Definitions & Requirements', className='header_label'),
                            html.Div(
                                dash_table.DataTable(
                                    data = financial_metrics_definitions_dict,
                                    columns = [{'name': i, 'id': i} for i in financial_metrics_definitions_keys],
                                    style_data={
                                        'fontSize': '12px',
                                        'border': 'none',
                                        'fontFamily': 'Jost, sans-serif',
                                    },
                                    style_data_conditional=[
                                        {
                                            'if': {
                                                'row_index': 'odd'
                                            },
                                            'backgroundColor': '#eeeeee',
                                        },
                                        {
                                            'if': {
                                                'row_index': 0,
                                                'column_id': 'Calculation'
                                            },
                                            'borderTop': '.75px solid rgb(103,131,169)'
                                        },
                                    ],
                                    style_header={
                                        'backgroundColor': '#ffffff',
                                        'fontSize': '12px',
                                        'fontFamily': 'Jost, sans-serif',
                                        'color': '#6783a9',
                                        'textAlign': 'center',
                                        'fontWeight': 'bold',
                                        'text-decoration': 'none',
                                        'borderBottom': '.75px solid rgb(103,131,169)'                    
                                    },
                                    style_cell={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'textAlign': 'left',
                                        'color': '#6783a9',
                                    },
                                    style_cell_conditional=[
                                        {
                                            'if': {
                                                'column_id': 'Calculation'
                                            },
                                            'width': '50%',
                                            'fontWeight': 'bold'
                                        },
                                    ],
                                    style_as_list_view=True
                                        ),
                                    ),
                                ],
                                className = 'pretty_container eight columns',
                            ),
                        ],
                        className = 'bare_container twelve columns',
                    )
                ]
    else:
        financial_metrics_table = {}
        financial_indicators_table = {}
        financial_metrics_definitions_table = {}
        main_container = {'display': 'none'}
        empty_container = {'display': 'block'}

    return financial_metrics_table, radio_content, display_radio, \
        financial_indicators_table, financial_metrics_definitions_table, \
        main_container, empty_container, no_data_to_display

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
                                html.Div(
                                    [
                                        html.Label('Key', className = 'header_label'),
                                        html.Div(create_key()),
                                    ],
                                    className = 'pretty_container six columns'
                                ),
                            ],
                            className = 'bare_container twelve columns'
                        ),
                    ],
                    className = 'row',
                ),
                html.Div(
                    [                
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(id='radio-finance-metrics-content', children=[]),
                                            ],
                                            id = 'radio-button-finance-metrics',
                                        ),
                                    ],
                                    id = 'radio-finance-metrics-display',
                                ),
                            ],
                            className = 'bare_container twelve columns',
                        ),
                    ],
                    className = 'row',
                ),
                html.Div(
                    [                      
                        html.Div(id='financial-metrics-table', children=[]),
                        html.Div(id='financial-indicators-table', children=[]),
                        html.Div(id='financial-metrics-definitions-table', children=[]),
                    ],
                    id = 'financial-metrics-main-container',
                ),
                html.Div(
                    [
                        html.Div(id='financial-metrics-no-data'),
                    ],
                    id = 'financial-metrics-empty-container',
                ),                            
            ],
            id='mainContainer'
        )