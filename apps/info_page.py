###################
# Print Dashboard #
###################
# author:   jbetley
# rev:     10.31.22

from dash import html, dash_table, Input, Output
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign
from dash.exceptions import PreventUpdate
import json
import re
import pandas as pd
import numpy as np

from app import app
np.warnings.filterwarnings('ignore')

## Callback ##
@app.callback(
    Output('financial-metrics-definitions-table', 'children'),



    Output('ptable-financial-metrics', 'children'),
    Output('ptable-financial-indicators', 'children'),
    Output('ptable-container-11ab', 'children'),
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
    Output('ptable-org-compliance', 'children'),
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    Input('dash-session', 'data')
)
def update_about_page(school, year, data):
    if not school:
        raise PreventUpdate

    # default table styles
    table_style = {
        'fontSize': '11px',
        'fontFamily': 'Roboto, sans-serif',
        'border': 'none'
    }

    table_header = {
        'backgroundColor': '#ffffff',
        'fontSize': '11px',
        'fontFamily': 'Roboto, sans-serif',
        'color': '#6783a9',
        'textAlign': 'center',
        'fontWeight': 'bold'     
    }

    # table_header_conditional = [
    #     {
    #         'if': {
    #             'column_id': 'Category'
    #         },
    #         'textAlign': 'left',
    #         'paddingLeft': '10px',
    #         'width': '35%',
    #         'fontSize': '11px',
    #         'fontFamily': 'Roboto, sans-serif',
    #         'color': '#6783a9',
    #         'fontWeight': 'bold'
    #     }
    # ]

    table_cell = {
        'whiteSpace': 'normal',
        'height': 'auto',
        'textAlign': 'center',
        'color': '#6783a9',
        'boxShadow': '0 0',
        'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
    }

#     table_cell_conditional = [
#         {
#             'if': {
#                 'column_id': 'Category'
#             },
#             'textAlign': 'left',
#             'fontWeight': '500',
#             'paddingLeft': '10px',
#             'width': '35%'
#         }
# ]

    empty_table =[
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
    ]

    # Index
    school_index = pd.DataFrame.from_dict(data['0'])

####

### ADD ACOUNTABILITY INFO


#################
# TODO: Make easier to read, either through Markdown or embedded images (neither works currently with dash 2.6 datatables)
# http://www.latex2png.com/
# https://stackoverflow.com/questions/70205486/clickable-hyperlinks-in-plotly-dash-datatable
# https://stackoverflow.com/questions/66583063/how-to-add-hyperlink-in-column-field-of-dash-datatable

    financial_metrics_definitions_data = [
        ['Current Ratio = Current Assets ÷ Current Liabilities','Current Ratio is greater than 1.1; or is between 1.0 and 1.1 and the one-year trend is not negative.'],
        ['Days Cash on Hand = Unrestricted Cash ÷ ((Operating Expenses - Depreciation Expense) ÷ 365)','School has greater than 45 unrestricted days cash; or between 30 - 45 unrestricted days cash and the one-year trend is not negative.'],
        ['Annual Enrollment Change = (Current Year ADM - Previous Year ADM) ÷ Previous Year ADM','Annual Enrollment Change increases or shows a current year decrease of less than 10%.'],
        ['Primary Reserve Ratio = Unrestricted Net Assets ÷ Operating Expenses','Primary Reserve Ratio is greater than .25.'],
        ['Change in Net Assets Margin = (Operating Revenue - Operating Expenses) ÷ Operating Revenue ; Aggregated 3-Year Margin = (3 Year Operating Revenue - 3 Year Operating Expense) ÷ 3 Year Operating Revenue','Aggregated Three-Year Margin is positive and the most recent year Change in Net Assets Margin is positive; or Aggregated Three-Year Margin is greater than -1.5%, the trend is positive for the last two years, and Change in Net Assets Margin for the most recent year is positive. For schools in their first and second year of operation, the cumulative Change in Net Assets Margin must be positive.'],
        ['Debt to Asset Ratio = Total Liabilities ÷ Total Assets','Debt to Asset Ratio is less than 0.9.'],
        ['One Year Cash Flow = Recent Year Total Cash - Previous Year Total Cash; Multi-Year Cash Flow = Recent Year Total Cash - Two Years Previous Total Cash','Multi-Year Cash Flow is positive and One Year Cash Flow is positive in two out of three years, including the most recent year. For schools in the first two years of operation, both years must have a positive Cash Flow (for purposes of calculating Cash Flow, the school\'s Year 0 balance is assumed to be zero).'],
        ['Debt Service Coverage Ratio = (Change in Net Assets + Depreciation/Amortization Expense + Interest Expense + Rent/Lease Expense) ÷ (Principal Payments + Interest Expense + Rent/Lease Expense)','Debt Service Coverage Ratio is greater than or equal to 1.0.']
    ]

    financial_metrics_definitions_keys = ['Calculation','Requirement to Meet Standard']
    financial_metrics_definitions_dict = [dict(zip(financial_metrics_definitions_keys, l)) for l in financial_metrics_definitions_data]

    financial_metrics_definitions_table = [
            dash_table.DataTable(
                data = financial_metrics_definitions_dict,
                columns = [{'name': i, 'id': i, 'presentation': 'markdown'} for i in financial_metrics_definitions_keys],
                style_data={
                    'fontSize': '12px',
                    'border': 'none',
                    'fontFamily': 'Roboto, sans-serif',
                },
                style_data_conditional=[
                    {
                        'if': {
                            'row_index': 'odd'
                        },
                        'backgroundColor': '#eeeeee',
                    }
                ],
                style_header={
                    'backgroundColor': '#ffffff',
                    'fontSize': '12px',
                    'fontFamily': 'Roboto, sans-serif',
                    'color': '#6783a9',
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'text-decoration': 'none',
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
            )
    ]

# ## NOTE: Hide this table until ratios are added back in

#     ratio_definitions_keys = ['Calculation','Definition']
#     ratio_definitions_dict= [dict(zip(ratio_definitions_keys, l)) for l in ratio_definitions_data ]

#     ratio_definitions_table = [
#                 dash_table.DataTable(
#                     data = ratio_definitions_dict,
#                     columns = [{'name': i, 'id': i} for i in ratio_definitions_keys],
#                     style_data={
#                         'fontSize': '12px',
#                         'border': 'none',
#                         'fontFamily': 'Roboto, sans-serif',
#                     },
#                     style_data_conditional=[
#                         {
#                             'if': {
#                                 'row_index': 'odd'
#                             },
#                             'backgroundColor': '#eeeeee',
#                         }
#                     ],
#                     style_header={
#                         'backgroundColor': '#ffffff',
#                         'fontSize': '12px',
#                         'fontFamily': 'Roboto, sans-serif',
#                         'color': '#6783a9',
#                         'textAlign': 'center',
#                         'fontWeight': 'bold',
#                         'text-decoration': 'none'
#                     },
#                     style_cell={
#                         'whiteSpace': 'normal',
#                         'height': 'auto',
#                         'textAlign': 'left',
#                         'color': '#6783a9',
#                     },
#                     style_cell_conditional=[
#                         {
#                             'if': {
#                                 'column_id': 'Calculation'
#                             },
#                             'width': '50%',
#                             'text-decoration': 'underline',
#                         },
#                     ],
#                     style_as_list_view=True
#                 )
#     ]

    return financial_metrics_definitions_table #, ratio_definitions_table

###########3
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
                                html.Label("Audited Financial Information", style=label_style),
                                html.Div(id='ptable-financial-information')
                            ],
                            className = "pretty_container twelve columns",
                        ),
                    ],
                    className = "bare_container twelve columns",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Financial Accountability Metrics", style=label_style),
                                        html.Div(id='ptable-financial-metrics')
                                    ],
                                    className = "pretty_container twelve columns",
                                ),
                            ],
                            className = "bare_container twelve columns",
                        ),
                    ],
                    className = "row",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Other Financial Accountability Indicators", style=label_style),
                                        html.Div(id='ptable-financial-indicators')
                                    ],
                                    className = "pretty_container twelve columns",
                                ),
                            ],
                            className = "bare_container twelve columns",
                        ),
                    ],
                    className = 'row', # pagebreak',
                ),
                html.Div(
                    [
                        html.Div(id='ptable-container-11ab', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='ptable-container-11cd', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='ptable-container-14ab', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='ptable-container-14cd', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='ptable-container-14ef', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='ptable-container-14g', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='ptable-container-15abcd', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='ptable-container-16ab', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='ptable-container-16cd', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                    ],
                    id = 'pdisplay-k8-metrics',
                ),
                html.Div(
                    [
                        html.Div(id='ptable-container-17ab', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='ptable-container-17cd', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                    ],
                    id = 'pdisplay-hs-metrics',
                ),
                html.Div(
                    [
                        html.Div(id='ptable-container-ahs-113', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='ptable-container-ahs-1214', children=[]), #id = "ptable-container-16ab" #className='bare_container twelve columns',
                        # html.Div(
                        #     [
                                
                        #         html.Div(
                        #             [
                        #                 html.Label('Adult Accountability Metrics (Not Calculated)', style=label_style),
                        #                 html.Div(id='ptable-ahs-metrics')
                        #             ],
                        #             className = "pretty_container ten columns"
                        #         ),
                        #     ],
                        #     className = "bare_container twelve columns"
                        # ),
                    ],
                    id = 'pdisplay-ahs-metrics',
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
        id="mainContainer",
        style={
            "display": "flex",
            "flexDirection": "column"
        }
    )

if __name__ == '__main__':
    app.run_server(debug=True)