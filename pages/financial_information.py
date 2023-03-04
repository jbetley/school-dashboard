##########################################
# ICSB Dashboard - Financial Information #
##########################################
# author:   jbetley
# version:  .99.021323

import dash
from dash import html, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
import os.path

from .table_helpers import create_empty_table
from .subnav import subnav_finance
dash.register_page(__name__, top_nav=True, path = '/financial_information', order=1)

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

@callback(
    Output('financial-information-table', 'children'),
    Output('radio-finance-info-display', 'style'),
    Output('radio-finance-info-content', 'children'),
    Output('financial-information-main-container', 'style'),
    Output('financial-information-empty-container', 'style'),
    Output('financial-information-no-data', 'children'),    
    Input('dash-session', 'data'),
    Input('year-dropdown', 'value'),
    Input(component_id='radio-button-finance-info', component_property='value')
)
def update_financial_information_page(data,year,radio_value):
    if not data:
        raise PreventUpdate

    main_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_to_display = create_empty_table('Audited Financial Information')

    max_display_years = 5
    school_index = pd.DataFrame.from_dict(data['0'])

    # Displays either School or Network level financials, if a school is not
    # part of a network, no radio buttons are displayed at all. If a school
    # is part of a network, define and display radio button. Storing the radio
    # buttons in a variable ensures there is no flickering of the component as
    # it is drawn and then hidden - as the button variable has no content until
    # it also meets the display condition.
    if school_index['Network'].values[0] != 'None':
        if radio_value == 'network-finance':

            radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-info',
                        className='btn-group',
                        inputClassName='btn-check',
                        labelClassName='btn btn-outline-primary',
                        labelCheckedClassName='active',
                        options=[
                            {'label': 'School', 'value': 'school-finance'},
                            {'label': 'Network', 'value': 'network-finance'},
                        ],
                        value='network-finance',
                        persistence=True,
                        persistence_type='local',
                    ),
                ],
                className='radio-group',
            )

        else:
            radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-info',
                        className='btn-group',
                        inputClassName='btn-check',
                        labelClassName='btn btn-outline-primary',
                        labelCheckedClassName='active',
                        options=[
                            {'label': 'School', 'value': 'school-finance'},
                            {'label': 'Network', 'value': 'network-finance'},
                        ],
                        value='school-finance',
                        persistence=True,
                        persistence_type='local',
                    ),
                ],
                className='radio-group',
            )

        display_radio = {}

    else:
        radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-info',
                        className='btn-group',
                        inputClassName='btn-check',
                        labelClassName='btn btn-outline-primary',
                        labelCheckedClassName='active',
                        options=[],
                        value='',
                        persistence=True,
                        persistence_type='local',
                    ),
                ],
                className='radio-group',
            )

        display_radio = {'display': 'none'}

    if radio_value == 'network-finance':
        finance_file = 'data/F-' + school_index['Network'].values[0] + '.csv'
        table_title = 'Audited Financial Information (' + school_index['Network'].values[0] + ')'
    else:
        finance_file = 'data/F-' + school_index['School Name'].values[0] + '.csv'
        
        # don't display the school name in table title if the school isn't part of a network
        if school_index['Network'].values[0] == 'None':
            table_title = 'Audited Financial Information'
        else:
            table_title = 'Audited Financial Information (' + school_index['School Name'].values[0] + ')'

    if os.path.isfile(finance_file):

        financial_data = pd.read_csv(finance_file)

        #TODO: FIGURE OUT WHERE WE ARE PUTTING ADM DATA
        # school_adm_dict        
        school_adm = pd.DataFrame.from_dict(data['6'])

        # 'operating_years_by_finance' is equal to the total number of years a school
        # has been financially active,by counting the total number of years in the
        # financial df (subtracting 1 for category column). We do not currently use this,
        # for dashboard purposes, we only care whether a school has five or fewer years of data
        operating_years_by_finance = max_display_years if len(financial_data.columns) - 1 >= max_display_years else len(financial_data.columns) - 1

        # drop any years that are later in time than the selected year
        most_recent_finance_year = financial_data.columns[1]
        excluded_finance_years = int(most_recent_finance_year) - int(year)

        if excluded_finance_years > 0:
            financial_data.drop(financial_data.columns[1:excluded_finance_years+1], axis=1, inplace=True)

        # financial file exists, but is empty
        if len(financial_data.columns) <= 1:
            financial_information_table = {}
            main_container = {'display': 'none'}
            empty_container = {'display': 'block'}

        else:

            # We calculate all rows requiring a 'calculation': Total Grants'
            # (State Grants + Federal Grants), 'Net Asset Position' (Total Assets
            # - Total Liabilities), and 'Change in Net Assets' (Operating Revenues
            # - Operating Expenses)

            # change all cols to numeric except for Category
            for col in financial_data.columns[1:]:
                financial_data[col]=pd.to_numeric(financial_data[col], errors='coerce') #.fillna(financial_data[col]).tolist()

            # set Category as index (so we can use .loc). This assumes that the final
            # rows already exist in the dataframe. If they do not, then need to use
            # the following pattern:
            # new_row = financial_data.loc['State Grants'] + financial_data.loc['Federal Grants']
            # new_row.name = 'Total Grants'
            # financial_data.append([new_row])

            financial_data = financial_data.set_index(['Category'])
            financial_data.loc['Total Grants'] = financial_data.loc['State Grants'] + financial_data.loc['Federal Grants']
            financial_data.loc['Net Asset Position'] = financial_data.loc['Total Assets'] - financial_data.loc['Total Liabilities']
            financial_data.loc['Change in Net Assets'] = financial_data.loc['Operating Revenues'] - financial_data.loc['Operating Expenses']        

            # reset index, which shifts Category back to column one
            financial_data = financial_data.reset_index()

            # Ensure that only the 'max_display_years' number of years (currently 5)
            # worth of financial data is displayed (add +1 to max_display_years to
            # account for the category column). To show all years of data, comment out this line.
            financial_data = financial_data.iloc[: , :(max_display_years+1)]

            years=financial_data.columns.tolist()
            years.pop(0)
            years.reverse()

            # remove audit and other indicator data (it is displayed on the financial metrics page)
            financial_data = financial_data.drop(financial_data.index[41:])
            
            # Each column in the financial_information df must have at least 12 values
            # to be valid. To avoid a situation where there is a column that only contains
            # financial ratio data (e.g., where a school existed prior to being required
            # to report financial data to ICSB), drop any column where more than 31 rows
            # contain empty strings (df has 43 total rows)
            for c in financial_data.columns:
                if len(financial_data[financial_data[c] == ''].index) > 31:
                    financial_data.drop([c], inplace=True, axis=1)

            # the following rows (categories) are not used and should be removed
            remove_categories = ['Administrative Staff', 'Instructional Staff','Instructional and Support Staff','Non-Instructional Staff','Total Personnel Expenses',
                'Instructional & Support Staff', 'Instructional Supplies','Management Fee','Insurance (Facility)','Electric and Gas',
                'Water and Sewer','Waste Disposal','Security Services','Repair and Maintenance','Occupancy Ratio','Human Capital Ratio',
                'Instruction Ratio']

            financial_data = financial_data[~financial_data['Category'].isin(remove_categories)]

            # drop any column (year) with all NaN (this can happen for schools that
            # existed prior to being with ICSB- e.g., they have Ratio data (from form 9),
            # but no financial information with ICSB
            financial_data = financial_data.dropna(axis=1, how='all')
            financial_data = financial_data.reset_index(drop=True)
               
            # Force correct format for display of df in datatable (accounting, no '$')
            for year in years:
                financial_data[year] = pd.Series(['{:,.2f}'.format(val) for val in financial_data[year]], index = financial_data.index)
            
            # clean file for display, replacing nan and 0.00 with ''
            financial_data.replace([0.0, '0.0',0.00,'0.00', np.nan], '', inplace=True)

            year_headers = [i for i in financial_data.columns if i not in ['Category']]
            table_size = len(financial_data.columns)

            if table_size == 2:
                col_width = 'four'
                category_width = 55
            if table_size == 3:
                col_width = 'six'
                category_width = 55
            if table_size > 3 and table_size <=8:
                col_width = 'eight'
                category_width = 35
            elif table_size >= 9:
                col_width = 'ten'
                category_width = 25
            elif table_size >= 10:
                col_width = 'twelve'
                category_width = 15

            data_width = 100 - category_width
            data_col_width = data_width / (table_size - 1)
            year_width = data_col_width

            class_name = 'pretty_container ' + col_width + ' columns'

            financial_information_table = [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(table_title, style=label_style),
                                html.Div(
                                    dash_table.DataTable(
                                        financial_data.to_dict('records'),
                                        columns = [{'name': i, 'id': i} for i in financial_data.columns],
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
                                            {
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
                                        ],
                                        style_as_list_view=True
                                    )
                                )
                            ],
                            className = class_name,
                        ),
                    ],
                    className = 'bare_container twelve columns',
                )
            ]
    else:
        financial_information_table = {}
        main_container = {'display': 'none'}
        empty_container = {'display': 'block'}

    return financial_information_table, display_radio,radio_content, \
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
                                        html.Div(
                                            [
                                                html.Div(id='radio-finance-info-content', children=[]),
                                            ],
                                            id = 'radio-button-finance-info',
                                        ),
                                    ],
                                    id = 'radio-finance-info-display',
                                ),
                            ],
                            className = 'bare_container twelve columns',
                        ),
                    ],
                    className = 'row',
                ),
                html.Div(
                    [                    
                        html.Div(id='financial-information-table', children=[]),
                    ],
                    id = 'financial-information-main-container',
                ),                
                html.Div(
                    [
                        html.Div(id='financial-information-no-data'),
                    ],
                    id = 'financial-information-empty-container',
                ),
            ],
            id='mainContainer',
            style={
                'display': 'flex',
                'flexDirection': 'column'
            }
        )