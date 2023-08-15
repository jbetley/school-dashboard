###################
# Print Dashboard #
###################
# author:   jbetley
# rev:     10.31.22

import dash
from dash import html, dash_table, Input, Output, callback
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign
from dash.exceptions import PreventUpdate
import json
import pandas as pd
import numpy as np

# from app import app
# np.warnings.filterwarnings('ignore')
# dash.register_page(__name__, top_nav=True, order=8)

## Callback ##
@callback(
    Output('ptable-financial-information', 'children'),
    Output('ptable-financial-metrics', 'children'),
    Output('ptable-financial-indicators', 'children'),
    Output('ptable-container-11ab', 'children'),
    Output('pdisplay-attendance', 'style'),
    Output('ptable-container-11cd', 'children'),
    Output('ptable-container-14ab', 'children'),
    Output('ptable-container-14cd', 'children'),
    Output('ptable-container-14ef', 'children'),
    Output('ptable-container-14g', 'children'),
    Output('ptable-container-15abcd', 'children'),
    Output('ptable-container-16ab', 'children'),
    Output('ptable-container-16cd', 'children'),
    Output('pdisplay-k8-metrics', 'style'),
    Output('ptable-container-17ab', 'children'),
    Output('ptable-container-17cd', 'children'),
    Output('pdisplay-hs-metrics', 'style'),
    Output('ptable-container-ahs-113', 'children'),
    Output('ptable-container-ahs-1214', 'children'),    
    Output('pdisplay-ahs-metrics', 'style'),
    Output('ptable-container-empty', 'children'),
    Output('pdisplay-empty-table', 'style'),
    Output('ptable-org-compliance', 'children'),
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    Input('dash-session', 'data')
)
def update_about_page(school, year, data):
    if not school:
        raise PreventUpdate

    empty_table =[
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

    # Index
    school_index = pd.DataFrame.from_dict(data['0'])

    # Financial Information & Metrics
    if not data['6']:

        table_financial_information = table_financial_metrics = table_financial_indicators = empty_table

    else:

        # financial_info_json
        json_data = json.loads(data['6'])
        finance_data = pd.DataFrame.from_dict(json_data)

        remove_categories = ['Administrative Staff', 'Instructional Staff','Non-Instructional Staff','Total Personnel Expenses',
            'Instructional & Support Staff', 'Instructional Supplies','Management Fee','Insurance (Facility)','Electric & Gas',
            'Water & Sewage','Waste Disposal','Security Services','Maintenance/Repair','Occupancy Ratio','Human Capital Ratio',
            'Instruction Ratio']

        finance_data = finance_data[~finance_data['Category'].isin(remove_categories)]

        table_financial_information = [
                dash_table.DataTable(
                    finance_data.to_dict('records'),
                    columns = [{'name': i, 'id': i, 'type':'numeric','format': FormatTemplate.money(2)} for i in finance_data.columns],
                    style_data={
                        'fontSize': '12px',
                        'fontFamily': 'Roboto, sans-serif',
                        'border': 'none'
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
                                'filter_query': "{Category} eq 'Revenue' || {Category} eq 'Financial Position' || {Category} eq 'Financial Activities' || {Category} eq 'Supplemental Information' || {Category} eq 'Enrollment Information' || {Category} eq 'Audit Information'"
                            },
                            'paddingLeft': '10px',
                            'text-decoration': 'underline',
                            'fontWeight': 'bold'
                        },
                        {   # Not sure why this is necessary, but it is to ensure first col header has border
                            'if': {
                                'row_index': 0,
                                'column_id': 'Category'
                            },
                            'borderTop': '.5px solid #6783a9'
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
                            'fontWeight': '500',
                            'paddingLeft': '20px',
                            'width': '20%'
                        },
                    ],
                    style_as_list_view=True
                )
        ]
  
        # financial_metrics_json
        json_data = json.loads(data['7'])
        financial_metrics_data = pd.DataFrame.from_dict(json_data)
        
        headers = financial_metrics_data.columns.tolist()

        clean_headers = []
        for i, x in enumerate (headers):
            if 'Rating' in x:
                clean_headers.append('Rating')
            else:
                clean_headers.append(x)

        remove_categories = ['Other Metrics', 'Instruction Ratio','Human Capitol Ratio','Occupancy Ratio']

        financial_metrics_data = financial_metrics_data[~financial_metrics_data['Metric'].isin(remove_categories)]

        table_financial_metrics = [
                dash_table.DataTable(
                financial_metrics_data.to_dict('records'),
                columns=[{
                    'name': col,
                    'id': headers[idx]
                    } for (idx, col) in enumerate(clean_headers)],
                style_data={
                    'fontSize': '12px',
                    'border': 'none',
                    'fontFamily': 'Roboto, sans-serif',
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
                ] +
                [
                    {
                        'if': {
                            'filter_query': "{{{col}}} = 'DNMS'".format(col=col),
                            'column_id': col
                        },
                        'backgroundColor': '#b44655',
                        'fontWeight': 'bold',
                        'color': 'white',
                        'borderBottom': 'solid 1px white',
                    } for col in financial_metrics_data.columns
                ] +
                [
                    {
                        'if': {
                            'filter_query': "{{{col}}} = 'MS'".format(col=col),
                            'column_id': col
                        },
                        'backgroundColor': '#81b446',
                        'fontWeight': 'bold',
                        'color': 'white',
                        'borderBottom': 'solid 1px white',
                    } for col in financial_metrics_data.columns
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
                            'column_id': 'Metric'
                        },
                        'textAlign': 'left',
                        'fontWeight': '500',
                        'paddingLeft': '20px',
                        'width': '20%'
                    },
                    {
                        'if': {
                            'column_id': ['Rating 1','Rating 2','Rating 3','Rating 4','Rating 5']
                        },
                        'width': '6%'
                    },
                ],
                style_as_list_view=True
            )
        ]

        # financial_indicators_json
        json_data = json.loads(data['8'])
        financial_indicators_data = pd.DataFrame.from_dict(json_data)

        table_financial_indicators = [
                        dash_table.DataTable(
                        financial_indicators_data.to_dict('records'),
                        columns = [{'name': i, 'id': i} for i in financial_indicators_data.columns],
                    style_data={
                        'fontSize': '12px',
                        'fontFamily': 'Roboto, sans-serif',
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
                    ] +
                    [
                        {
                            'if': {
                                'filter_query': "{{{col}}} = 'DNMS'".format(col=col),
                                'column_id': col
                            },
                            'backgroundColor': '#b44655',
                            'fontWeight': 'bold',
                            'color': 'white',
                            'borderBottom': 'solid 1px white',
                            'borderRight': 'solid 1px white',
                        } for col in financial_indicators_data.columns
                    ] +
                    [
                        {
                            'if': {
                                'filter_query': "{{{col}}} = 'MS'".format(col=col),
                                'column_id': col
                            },
                            'backgroundColor': '#81b446',
                            'fontWeight': 'bold',
                            'color': 'white',
                            'position': 'relative',
                            'borderBottom': 'solid 1px white',
                            'borderRight': 'solid 1px white',
                        } for col in financial_indicators_data.columns
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
                                'column_id': 'Standard'
                            },
                            'textAlign': 'center',
                            'fontWeight': '500',
                            'width': '7%'
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
                )
            ]

## Academic Metrics
    table_style = {
        'fontSize': '11px',
        'border': 'none',
        'fontFamily': 'Open Sans, sans-serif',
    }

    table_cell = {
        'whiteSpace': 'normal',
        'height': 'auto',
        'textAlign': 'center',
        'color': '#6783a9',
        'boxShadow': '0 0',
        'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
    }

    # Functions
    
    def createTable(label, data):
    # Make tables given data and label
    # could very possibly be less complicated than it is, or maybe not
    # but this has got to be for another day

        cols = data.columns
        table_size = len(cols)

        if len(data.index) == 0 or table_size == 1:
            table = [
                html.Div(
                    [
                        html.Label(label, style=label_style),
                        html.Div(
                            dash_table.DataTable(
                                columns = [
                                    {'id': 'emptytable', 'name': 'No Data to Display'},
                                ],
                                style_header={
                                    'fontSize': '14px',
                                    'border': 'none',
                                    'textAlign': 'center',
                                    'color': '#6783a9',
                                    'fontFamily': 'Open Sans, sans-serif',
                                },
                            )
                        )
                    ],
                    className = 'pretty_container ten columns'
                )
            ]

        else:

            if table_size == 2:
                col_width = 'eight'
                category_width = 70
            if table_size > 2 and table_size <=4:
                col_width = 'eight'
                category_width = 35
            elif table_size >= 5 and table_size <= 9:
                col_width = 'eight'
                category_width = 30
            elif table_size >= 10 and table_size <= 15:
                col_width = 'twelve'
                category_width = 15
            elif table_size >= 16:
                col_width = 'twelve'
                category_width = 15
            
            year_headers = [y for y in data.columns.tolist() if 'School' in y]
            rating_headers = [y for y in data.columns.tolist() if 'Rating' in y]
            difference_headers = [y for y in data.columns.tolist() if '+/-' in y]
            corporation_headers = [y for y in data.columns.tolist() if 'Rate' in y or 'Avg' in y] # Gets cols with 'Rate' and 'Avg' in header

            # splits column width, other than for 'Category' column, evenly
            # can finesse this by splitting data_width into unequal values for each
            # 'data' category, e.g.:
            #   rating_width = data_col_width + (data_col_width * .1)
            #   remaining_width = data_width - rating_width
            #   remaining_col_width = remaining_width / (table_size - 1)

            data_width = 100 - category_width
            data_col_width = data_width / (table_size - 1)
            rating_width = year_width = difference_width = corporation_width = data_col_width

            class_name = 'pretty_container ' + col_width + ' columns'

            headers = data.columns.tolist()

            table_cell_conditional = [
                {
                    'if': {
                        'column_id': 'Category'
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
            ]  + [
                {   'if': {
                    'column_id': rating
                },
                    'textAlign': 'center',
                    'fontWeight': '600',
                    'width': str(rating_width) + '%'
                } for rating in rating_headers
            ]  + [
                {   'if': {
                    'column_id': difference
                },
                    'textAlign': 'center',
                    'fontWeight': '500',
                    'width': str(difference_width) + '%'
                } for difference in difference_headers
            ]  + [
                {   'if': {
                    'column_id': corporation
                },
                    'textAlign': 'center',
                    'fontWeight': '500',
                    'width': str(corporation_width) + '%'
                } for corporation in corporation_headers
            ]

            table_data_conditional =  [
                {
                    'if': {
                        'row_index': 'odd'
                    },
                    'backgroundColor': '#eeeeee',
                }
            ] + [
                {
                    'if': {
                        'filter_query': '{{{col}}} = "DNMS"'.format(col=col),
                        'column_id': col
                    },
                    'backgroundColor': '#e56565',
                    'color': 'white',
                } for col in cols
            ] + [
                {
                    'if': {
                        'filter_query': '{{{col}}} = "AS"'.format(col=col),
                        'column_id': col
                    },
                    'backgroundColor': '#ddd75a',
                    'color': 'white',
                } for col in cols
            ] + [
                {
                    'if': {
                        'filter_query': '{{{col}}} = "ES"'.format(col=col),
                        'column_id': col
                    },
                    'backgroundColor': '#b29600',
                    'color': 'white',
                } for col in cols
            ] + [
                {
                    'if': {
                        'filter_query': '{{{col}}} = "MS"'.format(col=col),
                        'column_id': col
                    },
                    'backgroundColor': '#75b200',
                    'color': 'white',
                } for col in cols
            ]

            data['Category'] = data['Category'].map(lambda x: x.split('|')[0])

            ## multi-level headers
            # get list of +/- columns (used by datatable filter_query' to ID columns for color formatting)

    ## TODO: Most likely do not need the IF statement. There will never be a table_size of 1 (would be empty table)
            if table_size >= 2:
                format_cols = [k for k in headers if '+/-' in k or 'Rating' in k]

                name_cols = [['Category','']]
            
                for item in headers:
                    if item.startswith('20'):
                        if 'Rating' in item:
                            item = item[:10]
                        
                        name_cols.append([item[:4],item[4:]])

                #### NOTE: The next two two styling blocks add border to header_index:1
                # For single bottom line: comment out blocks, comment out style_header_conditional in table declaration,
                # and uncomment style_as_list in table declaration

                table_header = {
                    'backgroundColor': '#ffffff',
                    'fontSize': '11px',
                    'fontFamily': 'Roboto, sans-serif',
                    'color': '#6783a9',
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'border': 'none'     
                }

                table_header_conditional = [
                    {
                        'if': {
                            'column_id': year,
                            'header_index': 1,
                        },
                        'borderLeft': '.5px solid #b2bdd4',
                        'borderTop': '.5px solid #b2bdd4',
                        'borderBottom': '.5px solid #b2bdd4',
                    } for year in year_headers
                ] + [
                    {   'if': {
                        'column_id': corporation,
                        'header_index': 1,
                    },
                        'borderTop': '.5px solid #b2bdd4',
                        'borderBottom': '.5px solid #b2bdd4',
                } for corporation in corporation_headers
                ]  + [
                    {   'if': {
                        'column_id': rating,
                        'header_index': 1,
                    },
                        'borderTop': '.5px solid #b2bdd4',
                        'borderBottom': '.5px solid #b2bdd4',
                } for rating in rating_headers
                ]  + [
                    {   'if': {
                        'column_id': difference,
                        'header_index': 1,
                    },
                        'borderTop': '.5px solid #b2bdd4',
                        'borderBottom': '.5px solid #b2bdd4',
                } for difference in difference_headers
                ] + [
                    # Two options:
                    #   1) use 'headers[-1]' and 'borderRight' for each subheader to have full border
                    #   2) use 'headers[1]' and 'borderLeft' to leave first and last columns open on right and left
                    {   'if': {
                        'column_id': headers[-1],
                    #    'column_id': headers[1],
                        'header_index': 1,
                    },
                    'borderRight': '.5px solid #b2bdd4',
                    }
                ]

                # formatting logic is different for multi-header table
                table_data_conditional = [
                    {
                        'if': {
                            'row_index': 'odd'
                        },
                        'backgroundColor': '#eeeeee'
                    }
                ] + [
                    {
                        'if': {
                        'filter_query': '{{{col}}} = "DNMS"'.format(col=col),
                        'column_id': col
                        },
                        'backgroundColor': '#e56565',
                        'color': 'white',
                        'boxShadow': 'inset 0px 0px 0px 1px white'
                    } for col in cols
                ] + [
                    {
                        'if': {
                        'filter_query': '{{{col}}} = "AS"'.format(col=col),
                        'column_id': col
                        },
                        'backgroundColor': '#ddd75a',
                        'color': 'white',
                        'boxShadow': 'inset 0px 0px 0px 1px white'
                    } for col in cols
                ] + [
                    {
                        'if': {
                        'filter_query': '{{{col}}} = "ES"'.format(col=col),
                        'column_id': col
                        },
                        'backgroundColor': '#b29600',
                        'color': 'white',
                        'boxShadow': 'inset 0px 0px 0px 1px white'
                    } for col in cols
                ] + [
                    {
                        'if': {
                        'filter_query': '{{{col}}} = "MS"'.format(col=col),
                        'column_id': col
                        },
                        'backgroundColor': '#75b200',
                        'color': 'white',
                        'boxShadow': 'inset 0px 0px 0px 1px white'
                    } for col in cols
                ] + [
                    {
                        'if': {
                            'filter_query': '{{{col}}} = "NA"'.format(col=col),
                            'column_id': col
                        },
                        'backgroundColor': '#9a9a9a',
                        'color': 'white',
                        'boxShadow': 'inset 0px 0px 0px 1px white',
                    } for col in cols
                ] + [
                    {
                        'if': {
                            'column_id': headers[-1],
                        },
                        'borderRight': '.5px solid #b2bdd4',
                    },
                ] + [
                    {
                        'if': {
                            'row_index': 0
                        },
                        'paddingTop': '5px'
                    }
                ] + [
                    {
                        'if': {
                            'row_index': len(data)-1
                        },
                        'borderBottom': '.5px solid #b2bdd4',
                    }
                ] + [
                    {
                        'if': {
                            'column_id': 'Category',
                        },
                        'borderRight': '.5px solid #b2bdd4',
                        'borderBottom': 'none',                
                    },
                ] + [ 
                    {
                        'if': {
                            'column_id': rating,
                        },
                        'borderRight': '.5px solid #b2bdd4',
                    } for rating in rating_headers                
                ] + [ 
                    {
                        'if': {
                            'filter_query': '{{{col}}} < 0'.format(col=col),
                            'column_id': col
                        },                        
                        'fontWeight': 'bold',
                        'color': '#b44655',
                        'fontSize': '10px',
                    } for col in format_cols
                ] + [ 
                    {
                        'if': {
                            'filter_query': '{{{col}}} = "-***"'.format(col=col),
                            'column_id': col
                        },                        
                        'fontWeight': 'bold',
                        'color': '#b44655',
                        'fontSize': '10px',
                    } for col in format_cols
                ] + [
                    {
                        'if': {
                            'filter_query': '{{{col}}} > 0'.format(col=col),
                            'column_id': col
                        },
                        'fontWeight': 'bold',
                        'color': '#81b446',
                        'fontSize': '10px',
                    } for col in format_cols
                ]

                table = [
                    html.Div(
                        [
                            html.Label(label, style=label_style),
                            html.Div(
                                dash_table.DataTable(
                                    data.to_dict('records'),
                                    columns=[
                                            {
                                                'name': col,
                                                'id': headers[idx],
                                                'type':'numeric',
                                                'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
                                            } for (idx, col) in enumerate(name_cols)
                                        ],
                                    style_data = table_style,
                                    style_data_conditional = table_data_conditional,
                                    style_header = table_header,
                                    style_header_conditional = table_header_conditional,
                                    style_cell = table_cell,
                                    style_cell_conditional = table_cell_conditional,
                                    merge_duplicate_headers=True,
                                    #style_as_list_view=True
                                )
                            )
                        ],
                        className = class_name
                    )
                ]

            ## TODO: IS THIS NEEDED? WHEN WOULD IT TRIGGER?
            else:
                print ('TRIGGERED!!!')
                # headers
                clean_headers = []
                for i, x in enumerate (headers):
                    if 'Rating' in x:
                        clean_headers.append('Rating')
                    else:
                        clean_headers.append(x)

                table_header = {
                    'backgroundColor': '#ffffff',
                    'fontSize': '11px',
                    'fontFamily': 'Roboto, sans-serif',
                    'color': '#6783a9',
                    'textAlign': 'center',
                    'fontWeight': 'bold'            
                }

                table = [
                    html.Div(
                        [
                            html.Label(label, style=label_style),
                            html.Div(
                                dash_table.DataTable(
                                    data.to_dict('records'),
                                    columns=[{
                                        'name': col, 
                                        'id': headers[idx],
                                        'type':'numeric',
                                        'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)                                    
                                        #'format': FormatTemplate.percentage(2)
                                        } for (idx, col) in enumerate(clean_headers)],
                                    style_data = table_style,
                                    style_data_conditional = table_data_conditional,
                                    style_header = table_header,
                                    style_cell = table_cell,
                                    style_cell_conditional = table_cell_conditional,
                                    style_as_list_view=True
                                )
                            )
                        ],
                        className = class_name
                    )
                ]

        return table

    # Display tables either side by side or on individual rows depending on # of columns
    def setLayout(table1, table2, cols):

        # Can force single table layout by passing same table twice
        if table1 == table2:

            table_layout = [
                    html.Div(
                        table1,
                        className = 'bare_container twelve columns',
                    )
            ]
        else:
            if len(cols) >= 4:

                table_layout = [
                        html.Div(
                            table1,
                            className = 'bare_container twelve columns',
                        ),
                        html.Div(
                            table2,
                            className = 'bare_container twelve columns',
                        ),
                ]

            else:

                table_layout = [
                        html.Div(
                            [
                                table1[0],
                                table2[0],
                            ],
                            className = 'bare_container twelve columns',
                        ),
                ]

        return table_layout

    # create empty table with custom label
    def emptyTable(label):

        empty_table = [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(label, style=label_style),
                                    html.Div(
                                        dash_table.DataTable(
                                            columns = [
                                                {'id': 'emptytable', 'name': 'No Data to Display'},
                                            ],
                                            style_header={
                                                'fontSize': '14px',
                                                'border': 'none',
                                                'textAlign': 'center',
                                                'color': '#6783a9',
                                                'fontFamily': 'Open Sans, sans-serif',
                                            },
                                        ),
                                    ),
                                ],
                                className = 'pretty_container eight columns'
                            ),
                        ],
                        className = 'bare_container twelve columns',
                    )
        ]

        return empty_table
    # End Functions

    #### Academic Metrics

    display_attendance = display_k8_metrics = display_hs_metrics = display_ahs_metrics = {}
    
    # used if no data at all available
    table_container_empty = {}
    display_empty_table = {'display': 'none'}

    # Adult High School Academic Metrics
    if school_index['School Type'].values[0] == 'AHS':
        table_container_11cd = table_container_14ab = table_container_14cd = table_container_14ef = \
            table_container_14g = table_container_15abcd = table_container_16ab = table_container_16cd = {}
        display_k8_metrics = {'display': 'none'}

        table_container_17ab = table_container_17cd = {}
        display_hs_metrics = {'display': 'none'}

        if data['22']:
             
            json_data = json.loads(data['22'])
            metric_ahs_113_data = pd.DataFrame.from_dict(json_data)

            metric_ahs_113_data['Category'] = metric_ahs_113_data['Metric'] + ' ' + metric_ahs_113_data['Category']
            
            metric_ahs_113_data.drop('Metric', inplace=True, axis=1)

            metric_ahs_113_label = 'Adult High School Accountability Metrics 1.1 & 1.3'
            table_ahs_113 = createTable(metric_ahs_113_label, metric_ahs_113_data)
            table_container_ahs_113 = setLayout(table_ahs_113, table_ahs_113, metric_ahs_113_data.columns)

            # NOTE: Placeholder (Adult Accountability Metrics 1.2.a, 1.2.b, 1.4.a, & 1.4.b)
            all_cols = metric_ahs_113_data.columns.tolist()
            simple_cols = [x for x in all_cols if not x.endswith('+/-')]

            ahs_nocalc_empty = pd.DataFrame(columns = simple_cols)

            ahs_nocalc_dict = {
                'Category': ['1.2.a. Students graduate from high school in 4 years.', 
                        '1.2.b. Students enrolled in grade 12 graduate within the school year being assessed.',
                        '1.4.a. Students who graduate achieve proficiency on state assessments in English/Language Arts.',
                        '1.4.b.Students who graduate achieve proficiency on state assessments in Math.'
                    ]
                }
            ahs_no_calc = pd.DataFrame(ahs_nocalc_dict)

            metric_ahs_1214_data = pd.concat([ahs_nocalc_empty, ahs_no_calc], ignore_index = True)
            metric_ahs_1214_data.reset_index()
            
            for h in metric_ahs_1214_data.columns:
                if 'Rating' in h:
                    metric_ahs_1214_data[h].fillna(value='NA', inplace=True)
                else:
                    metric_ahs_1214_data[h].fillna(value='No Data', inplace=True)
            
            metric_ahs_1214_label = 'Adult Accountability Metrics 1.2.a, 1.2.b, 1.4.a, & 1.4.b (Not Calculated)'
            table_ahs_1214 = createTable(metric_ahs_1214_label, metric_ahs_1214_data)
            table_container_ahs_1214 = setLayout(table_ahs_1214, table_ahs_1214, metric_ahs_1214_data.columns)

        else:
            # AHS - 'No Data to Display'
            table_container_ahs_113 = table_container_ahs_1214 = {}
            display_ahs_metrics = {'display': 'none'}
            table_container_empty = emptyTable('Adult High School Accountability Metrics')
            display_empty_table = {}
    
    # K8, K12, & High School Accountability Metrics
    else:   

        table_container_ahs_113 = table_container_ahs_1214 = {}
        display_ahs_metrics = {'display': 'none'}

        # High School Academic Metrics
        if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'K12':
        
            # if HS only, no K8 data (other than potentiall attendance- container_11ab)
            if school_index['School Type'].values[0] == 'HS':
                table_container_11cd = table_container_14ab = table_container_14cd = table_container_14ef = table_container_14g = \
                    table_container_15abcd = table_container_16ab = table_container_16cd = {}
                display_k8_metrics = {'display': 'none'}

            # hs_metrics_data_json
            if data['20']:

                json_data = json.loads(data['20'])
                combined_grad_metrics_data = pd.DataFrame.from_dict(json_data)

                metric_17ab_label = 'High School Accountability Metrics 1.7.a & 1.7.b'
                table_17ab = createTable(metric_17ab_label, combined_grad_metrics_data)
                table_container_17ab = setLayout(table_17ab, table_17ab, combined_grad_metrics_data.columns)

                # NOTE: Placeholder data (High School Accountability Metrics 1.7.c & 1.7.d)
                all_cols = combined_grad_metrics_data.columns.tolist()
                simple_cols = [x for x in all_cols if (not x.endswith('+/-') and not x.endswith('Avg'))]

### TODO: ADD STRENGTH OF DIPLOMA INDICATOR  

                grad_metrics_empty = pd.DataFrame(columns = simple_cols)

                grad_metrics_dict = {
                    'Category': ['1.7.c. The percentage of students entering Grade 12 at beginning of year who graduated', '1.7.d. The percentage of graduating students planning to pursue collge or career.']
                }
                grad_metrics = pd.DataFrame(grad_metrics_dict)

                metric_17cd_data = pd.concat([grad_metrics_empty, grad_metrics], ignore_index = True)
                metric_17cd_data.reset_index()

                for h in metric_17cd_data.columns:
                    if 'Rating' in h:
                        metric_17cd_data[h].fillna(value='NA', inplace=True)
                    else:
                        metric_17cd_data[h].fillna(value='No Data', inplace=True)
                
                metric_17cd_label = 'High School Accountability Metrics 1.7.c & 1.7.d'
                table_17cd = createTable(metric_17cd_label, metric_17cd_data)
                table_container_17cd = setLayout(table_17cd, table_17cd, metric_17cd_data.columns)

            else:

                # HS - 'No Data to Display'                
                table_container_17ab = table_container_17cd = {}
                display_hs_metrics = {'display': 'none'}
                table_container_empty = emptyTable('Academic Accountability Metrics')
                display_empty_table = {}
                    
        # K8 Academic Metrics (for K8 and K12 schools)
        if school_index['School Type'].values[0] == 'K8' or school_index['School Type'].values[0] == 'K12':

            # if schooltype is K8, hide HS table
            if school_index['School Type'].values[0] == 'K8':

                table_container_17ab = table_container_17cd = {}
                display_hs_metrics = {'display': 'none'}
                        
            if (data['17'] and data['18']):

                # k8_combined_metrics_delta_json
                json_data = json.loads(data['17'])
                combined_delta = pd.DataFrame.from_dict(json_data)

                # k8_metrics_delta_json
                json_data = json.loads(data['18'])
                combined_years = pd.DataFrame.from_dict(json_data)
                
                ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
                status = ['Special Education','General Education','Paid Meals','Free/Reduced Price Meals','English Language Learners','Non-English Language Learners']
                grades = ['Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8','Total','IREAD Pass %']
                subgroup = ethnicity + status

                metric_14a_data = combined_years[(combined_years['Category'].str.contains('|'.join(grades))) & (combined_years['Category'].str.contains('ELA'))]
                metric_14a_label = ['1.4a Grade level proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' compared with the previous school year.']
                table_14a = createTable(metric_14a_label, metric_14a_data)

                metric_14b_data = combined_years[(combined_years['Category'].str.contains('|'.join(grades))) & (combined_years['Category'].str.contains('Math'))]
                metric_14b_label = ['1.4b Grade level proficiency on the state assessment in',html.Br(), html.U('Math'), ' compared with the previous school year.']
                table_14b = createTable(metric_14b_label, metric_14b_data)

                table_container_14ab = setLayout(table_14a,table_14b,combined_years.columns)

                metric_14c_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(grades))) & (combined_delta['Category'].str.contains('ELA'))]
                metric_14c_label = ['1.4c Grade level proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' compared with traditional school corporation.']
                table_14c = createTable(metric_14c_label, metric_14c_data)

                metric_14d_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(grades))) & (combined_delta['Category'].str.contains('Math'))]            
                metric_14d_label = ['1.4.d Grade level proficiency on the state assessment in',html.Br(), html.U('Math'), ' compared with traditional school corporation.']
                table_14d = createTable(metric_14d_label, metric_14d_data)

                table_container_14cd = setLayout(table_14c,table_14d,combined_delta.columns)

                # NOTE: Placeholder (Accountability Metrics 1.4.e & 1.4.f)
                all_cols = combined_years.columns.tolist()
                simple_cols = [x for x in all_cols if not x.endswith('+/-')]

                year_proficiency_empty = pd.DataFrame(columns = simple_cols)

                year_proficiency_dict = {
                    'Category': ['1.4.e. Percentage of students enrolled for at least two (2) school years achieving proficiency on the state assessment in English Language Arts.', 
                            '1.4.f. Percentage of students enrolled for at least two (2) school years achieving proficiency on the state assessment in Math.'
                        ]
                    }
                year_proficiency = pd.DataFrame(year_proficiency_dict)

                metric_14ef_data = pd.concat([year_proficiency_empty, year_proficiency], ignore_index = True)
                metric_14ef_data.reset_index()

                for h in metric_14ef_data.columns:
                    if 'Rating' in h:
                        metric_14ef_data[h].fillna(value='NA', inplace=True)
                    else:
                        metric_14ef_data[h].fillna(value='No Data', inplace=True)

                metric_14ef_label = 'Accountability Metrics 1.4.e & 1.4.f'
                table_14ef = createTable(metric_14ef_label, metric_14ef_data)
                table_container_14ef = setLayout(table_14ef, table_14ef, metric_14ef_data.columns)
                
                # iread_data_json
                if data['21']:
                    json_data = json.loads(data['21'])
                    iread_data = pd.DataFrame.from_dict(json_data)
                    metric_14g_label = '1.4.g. Percentage of students achieving proficiency on the IREAD-3 state assessment.'
                    table_14g = createTable(metric_14g_label, iread_data)
                    table_container_14g = setLayout(table_14g, table_14g, iread_data.columns)

                else:
                    table_container_14g = emptyTable('1.4.g Percentage of students achieving proficiency on the IREAD-3 state assessment.')

                # NOTE: Placeholder (Accountability Metrics 1.5.a, 1.5.b, 1.5.c, & 1.5.d)
                growth_metrics_empty = pd.DataFrame(columns = simple_cols)
                growth_metrics_dict = {
                    'Category': ['1.5.a Percentage of students achieving “typical” or “high” growth on the state assessment in \
                        English Language Arts according to Indiana\'s Growth Model',
                    '1.5.b Percentage of students achieving “typical” or “high” growth on the state assessment in \
                        Math according to Indiana\'s Growth Model',
                    '1.5.c. Median Student Growth Percentile ("SGP") of students achieving "adequate and sufficient growth" \
                        on the state assessment in English Language Arts according to Indiana\'s Growth Model',
                    '1.5.d. Median SGP of students achieving "adequate and sufficient growth" on the state assessment \
                        in Math according to Indiana\'s Growth Model',
                        ]
                    }
                growth_metrics = pd.DataFrame(growth_metrics_dict)

                metric_15abcd_data = pd.concat([growth_metrics_empty, growth_metrics], ignore_index = True)
                metric_15abcd_data.reset_index()

                for h in metric_15abcd_data.columns:
                    if 'Rating' in h:
                        metric_15abcd_data[h].fillna(value='NA', inplace=True)
                    else:
                        metric_15abcd_data[h].fillna(value='No Data', inplace=True)

                metric_15abcd_label = 'Accountability Metrics 1.5.a, 1.5.b, 1.5.c, & 1.5.d'
                table_15abcd = createTable(metric_15abcd_label, metric_15abcd_data)
                table_container_15abcd = setLayout(table_15abcd, table_15abcd, metric_15abcd_data.columns)

                metric_16a_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(subgroup))) & (combined_delta['Category'].str.contains('ELA'))]
                metric_16a_label = ['1.6a Proficiency on the state assessment in ', html.U('English Language Arts'), html.Br(),'for each subgroup compared with traditional school corporation.']
                table_16a = createTable(metric_16a_label,metric_16a_data)

                metric_16b_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(subgroup))) & (combined_delta['Category'].str.contains('Math'))]            
                metric_16b_label = ['1.6b Proficiency on the state assessment in ', html.U('Math'), ' for each', html.Br(), 'subgroup compared with traditional school corporation.']
                table_16b = createTable(metric_16b_label, metric_16b_data)

                table_container_16ab = setLayout(table_16a,table_16b,combined_delta.columns)

                metric_16c_data = combined_years[(combined_years['Category'].str.contains('|'.join(subgroup))) & (combined_years['Category'].str.contains('ELA'))]
                metric_16c_label = ['1.6c The change in proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' for each subgroup compared with the previous school year.']
                table_16c = createTable(metric_16c_label,metric_16c_data)

                metric_16d_data = combined_years[(combined_years['Category'].str.contains('|'.join(subgroup))) & (combined_years['Category'].str.contains('Math'))]
                metric_16d_label = ['1.6d The change in proficiency on the state assessment in',html.Br(), html.U('Math'), ' for each subgroup compared with the previous school year.']
                table_16d = createTable(metric_16d_label,metric_16d_data)

                table_container_16cd = setLayout(table_16c,table_16d,combined_years.columns)

            else:

                # K8 - 'No Data to Display' (except attendance (container_11ab))
                table_container_11cd = table_container_14ab = table_container_14cd = \
                    table_container_14ef = table_container_14g = table_container_15abcd = table_container_16ab = \
                    table_container_16cd = {}
                display_k8_metrics = {'display': 'none'}

                table_container_empty = emptyTable('Academic Accountability Metrics')
                display_empty_table = {}

    # If no matching school_type - display empty table (catch-all)
    if school_index['School Type'].values[0] != 'K8' and school_index['School Type'].values[0] != 'K12' and school_index['School Type'].values[0] != 'HS' and school_index['School Type'].values[0] != 'AHS':
        
        table_container_11ab = table_container_11cd = table_container_14ab = table_container_14cd = table_container_14ef = table_container_14g = table_container_15abcd = table_container_16ab = table_container_16cd = {}
        display_attendance = {'display': 'none'}
        display_k8_metrics = {'display': 'none'}

        table_container_17ab = table_container_17cd = {}
        display_hs_metrics = {'display': 'none'}
        
        table_container_ahs_113 = table_container_ahs_1214 = {}
        display_ahs_metrics = {'display': 'none'}

        table_container_empty = emptyTable('Academic Accountability Metrics')
        display_empty_table = {}

    # attendance_rate_data_json
    metric_11ab_label = 'Accountability Metrics 1.1.a & 1.1.b'

    if data['19']:

        json_data = json.loads(data['19'])
        attendance_data = pd.DataFrame.from_dict(json_data)

        # NOTE: Placeholder data (Acountability Metric 1.1.b.)
        teacher_retention_rate = pd.DataFrame({'Category': ['1.1.b. Teacher Retention Rate (compared to school corporation average)']})

        metric_11ab_data = pd.merge(attendance_data, teacher_retention_rate, how='outer', on='Category')

        for h in metric_11ab_data.columns:
            if 'Rating' in h:
                metric_11ab_data[h].fillna(value='NA', inplace=True)
            else:
                metric_11ab_data[h].fillna(value='No Data', inplace=True)

        table_11ab = createTable(metric_11ab_label, metric_11ab_data)
        table_container_11ab = setLayout(table_11ab, table_11ab, metric_11ab_data.columns)

    else:

        table_container_11ab = {}
        display_attendance = {'display': 'none'}
#        table_container_11ab = emptyTable(metric_11ab_label)

    # NOTE: Placeholder data (Acountability Metrics 1.1.c & 1.1.d)
    # NOTE: Does not display for school with no academic data

    metric_11cd_label = 'Accountability Metrics 1.1.c & 1.1.d'
    
    if data['18']:

        student_retention_rate_dict = {'Category': ['1.1.c. Student Re-Enrollment Rate (End of Year to Beginning of Year)',
            '1.1.d. Student Re-Enrollment Rate (Year over Year)']
        }
        student_retention_empty = pd.DataFrame(columns = combined_years.columns.tolist())
        student_retention_rate = pd.DataFrame(student_retention_rate_dict)

        metric_11cd_data = pd.concat([student_retention_empty, student_retention_rate], ignore_index = True)
        metric_11cd_data.reset_index()

        for h in metric_11cd_data.columns:
            if 'Rating' in h:
                metric_11cd_data[h].fillna(value='NA', inplace=True)
            else:
                metric_11cd_data[h].fillna(value='No Data', inplace=True)

        table_11cd = createTable(metric_11cd_label, metric_11cd_data)
        table_container_11cd = setLayout(table_11cd, table_11cd, metric_11cd_data.columns)

    else:

        table_container_11cd = emptyTable(metric_11cd_label)

## Organizational Indicators
    # organizational_indicators_json
    if not data['15']:
        table_org_compliance = empty_table
    else:
        json_data = json.loads(data['15'])        
        org_compliance_data = pd.DataFrame.from_dict(json_data)
        
        table_org_compliance = [
                    dash_table.DataTable(
                        org_compliance_data.to_dict('records'),
                        columns = [{'name': i, 'id': i} for i in org_compliance_data.columns],
                        style_data={
                            'fontSize': '12px',
                            'border': 'none',
                            'fontFamily': 'Roboto, sans-serif',
                        },
                        style_data_conditional=
                        [                                            
                            {
                                'if': {
                                    'row_index': 'odd'
                                },
                                'backgroundColor': '#eeeeee',
                            },
                        ] +
                        [
                            {
                                'if': {
                                    'filter_query': "{{{col}}} = 'DNMS'".format(col=col),
                                    'column_id': col
                                },
                                'backgroundColor': '#b44655',
                                'fontWeight': 'bold',
                                'color': 'white',
                                'borderBottom': 'solid 1px white',
                                'borderRight': 'solid 1px white',
                            } for col in org_compliance_data.columns
                        ] +
                        [
                            {
                                'if': {
                                    'filter_query': "{{{col}}} = 'MS'".format(col=col),
                                    'column_id': col
                                },
                                'backgroundColor': '#81b446',
                                'fontWeight': 'bold',
                                'color': 'white',
                                'borderBottom': 'solid 1px white',
                                'borderRight': 'solid 1px white',
                            } for col in org_compliance_data.columns
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
                        style_cell={
                            'whiteSpace': 'normal',
                            'height': 'auto',
                            'textAlign': 'center',
                            'color': '#6783a9',
                            'minWidth': '25px', 'width': '25px', 'maxWidth': '25px',
                        },
                        style_cell_conditional=[
                            {
                                'if': {'column_id': 'Standard'},
                                    'textAlign': 'Center',
                                    'fontWeight': '500',
                                    'width': '7%'
                            },
                            {   
                                'if': {'column_id': 'Description'},
                                    'width': '50%',
                                    'textAlign': 'Left',
                                    'fontWeight': '500',
                            },
                        ],
                    )
        ]

#### ALL teh tables
 
    return table_financial_information, table_financial_metrics, table_financial_indicators, \
        table_container_11ab, display_attendance, table_container_11cd, table_container_14ab, \
        table_container_14cd, table_container_14ef, table_container_14g, \
        table_container_15abcd, table_container_16ab, table_container_16cd, display_k8_metrics, \
        table_container_17ab, table_container_17cd, display_hs_metrics, \
        table_container_ahs_113, table_container_ahs_1214, display_ahs_metrics, \
        table_container_empty, display_empty_table, \
        table_org_compliance

#### ALL teh layouts

label_style = {
    'height': 'auto',
    'lineHeight': '1.5em',
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
                                html.Label('Audited Financial Information', style=label_style),
                                html.Div(id='ptable-financial-information')
                            ],
                            className = 'pretty_container twelve columns',
                        ),
                    ],
                    className = 'bare_container twelve columns',
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label('Financial Accountability Metrics', style=label_style),
                                        html.Div(id='ptable-financial-metrics')
                                    ],
                                    className = 'pretty_container twelve columns',
                                ),
                            ],
                            className = 'bare_container twelve columns',
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
                                        html.Label('Other Financial Accountability Indicators', style=label_style),
                                        html.Div(id='ptable-financial-indicators')
                                    ],
                                    className = 'pretty_container twelve columns',
                                ),
                            ],
                            className = 'bare_container twelve columns',
                        ),
                    ],
                    className = 'row', # pagebreak',
                ),
# Academic
                html.Div(
                    [
                        html.Div(id='ptable-container-11ab', children=[]),
                    ],
                    id = 'pdisplay-attendance',
                ),
                html.Div(
                    [
                        html.Div(id='ptable-container-11cd', children=[]),
                        html.Div(id='ptable-container-14ab', children=[]),
                        html.Div(id='ptable-container-14cd', children=[]),
                        html.Div(id='ptable-container-14ef', children=[]),
                        html.Div(id='ptable-container-14g', children=[]),
                        html.Div(id='ptable-container-15abcd', children=[]),
                        html.Div(id='ptable-container-16ab', children=[]),
                        html.Div(id='ptable-container-16cd', children=[]),
                    ],
                    id = 'pdisplay-k8-metrics',
                ),
                html.Div(
                    [
                        html.Div(id='ptable-container-17ab', children=[]),
                        html.Div(id='ptable-container-17cd', children=[]),
                    ],
                    id = 'pdisplay-hs-metrics',
                ),
                html.Div(
                    [
                        html.Div(id='ptable-container-ahs-113', children=[]),
                        html.Div(id='ptable-container-ahs-1214', children=[]),
                    ],
                    id = 'pdisplay-ahs-metrics',
                ),
                html.Div(
                    [
                        html.Div(id='ptable-container-empty', children=[]),
                    ],
                    id = 'pdisplay-empty-table',
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label('Organizational and Operational Accountability', style=label_style),
                                        html.Div(id='ptable-org-compliance')
                                    ],
                                    className = 'pretty_container twelve columns',
                                ),
                            ],
                            className = 'bare_container twelve columns'
                        ),
                    ],
                    className = 'row',
                ),
        ],
        id='mainContainer',
        style={
            'display': 'flex',
            'flexDirection': 'column'
        }
    )