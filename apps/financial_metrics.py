######################################
# ICSB Dashboard - Financial Metrics #
######################################
# author:   jbetley
# rev:     10.31.22

from dash import html, dash_table, Input, Output
from dash.exceptions import PreventUpdate
import pandas as pd
import json

from app import app

@app.callback(
    Output('financial-metrics-table', 'children'),
    Output('financial-indicators-table', 'children'),
    Output('financial-metrics-definitions-table', 'children'),
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

    # financial_metrics_json
    if not data['7']:

        financial_metrics_table = empty_table

    else:

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

        # NOTE: Ratios are shown on Financial Analysis page
        remove_categories = ['Other Metrics', 'Instruction Ratio','Human Capitol Ratio','Occupancy Ratio']

        financial_metrics_data = financial_metrics_data[~financial_metrics_data['Metric'].isin(remove_categories)]

        financial_metrics_table = [
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
    if not data['8']:

        financial_indicators_table = empty_table

    else:

        # financial_indicators_json
        json_data = json.loads(data['8'])
        financial_indicators_data = pd.DataFrame.from_dict(json_data)

        financial_indicators_table = [
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

# TODO: Make easier to read, either through Markdown or embedded images (neither works currently with dash 2.6 datatables)
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
                    },
                    {   # Not sure why this is necessary, but it is to ensure first col header has border
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
                    'fontFamily': 'Roboto, sans-serif',
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
            )
    ]

    return financial_metrics_table, financial_indicators_table, financial_metrics_definitions_table

## Layout
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
                                html.Div(
                                    [
                                        html.Label('Financial Accountability Metrics', style=label_style),
                                        html.Div(id='financial-metrics-table')
                                    ],
                                    className = 'pretty_container ten columns',
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
                                        html.Div(id='financial-indicators-table')
                                    ],
                                    className = 'pretty_container ten columns',
                                ),
                            ],
                            className = 'bare_container twelve columns',
                        ),
                    ],
                    className = 'row pagebreak',
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label('Accountability Metrics Definitions & Requirements', style=label_style),
                                        html.Div(id='financial-metrics-definitions-table')
                                    ],
                                    className = 'pretty_container ten columns'
                                ),
                            ],
                            className = 'bare_container twelve columns',
                        ),
                    ],
                    className = 'row'
                ),
            ],
            id='mainContainer',
            style={
                'display': 'flex',
                'flexDirection': 'column'
            }
        )

if __name__ == '__main__':
    app.run_server(debug=True)