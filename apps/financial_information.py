##########################################
# ICSB Dashboard - Financial Information #
##########################################
# author:   jbetley
# rev:     10.31.22

from dash import html, dash_table, Input, Output
from dash.dash_table import FormatTemplate
from dash.exceptions import PreventUpdate
import pandas as pd
import json

from app import app

@app.callback(
    Output('financial-information-table', 'children'),
    Input('dash-session', 'data')
)
def update_about_page(data):
    if not data:
        raise PreventUpdate

    # financial_info_json
    if not data['6']:

        financial_information_table = [
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

    else:

        # financial_info_json
        json_data = json.loads(data['6'])
        finance_data = pd.DataFrame.from_dict(json_data)
        
        ## NOTE: the following rows (categories) are not used
        remove_categories = ['Administrative Staff', 'Instructional Staff','Instructional and Support Staff','Non-Instructional Staff','Total Personnel Expenses',
            'Instructional & Support Staff', 'Instructional Supplies','Management Fee','Insurance (Facility)','Electric and Gas',
            'Water and Sewer','Waste Disposal','Security Services','Repair and Maintenance','Occupancy Ratio','Human Capital Ratio',
            'Instruction Ratio']

        finance_data = finance_data[~finance_data['Category'].isin(remove_categories)]

        # drop any column (year) with all NaN (this can happen for schools that existed prior to being with ICSB- e.g., they have
        # Ratio data (from form 9), but no financial information with ICSB
        finance_data = finance_data.dropna(axis=1, how='all')
        finance_data = finance_data.reset_index(drop=True)
        
#TODO: TOOODDDDOOOO        
        # Force correct format for display of df in datatable
        # TODO: Better way to do this?
        # All years are money except for index 39, 40, 41 (ADM)
        # for year in two_year:
        #     per_student_data[year] = pd.Series(['{:,.2f}'.format(val) for val in per_student_data[year]], index = per_student_data.index)
        # per_student_data['% Change'] = pd.Series(["{0:.2f}%".format(val * 100) for val in per_student_data['% Change']], index = per_student_data.index)
        # NOTE: Bit of a kludge. Dash datatable 'FormatTemplate' affects all numeric rows. So we change the
        # last 3 rows (ADM) to str type so data isn't automatically formatted
        finance_data[-3:] = finance_data[-3:].astype(str)
        # for i, row in finance_data.iloc[-3:].iterrows():
        #     print(row)
        #     row = row.astype(str)
        #     print(row)
        # for p in range(39,42):
        #     finance_data.loc[p] = finance_data.loc[p].astype(str)

        financial_information_table = [
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

    return financial_information_table

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
                                html.Label('Audited Financial Information', style=label_style),
                                html.Div(id='financial-information-table')
                            ],
                            className = 'pretty_container ten columns',
                        ),
                    ],
                    className = 'bare_container twelve columns',
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