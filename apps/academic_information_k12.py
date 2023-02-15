########################
# Academic Information #
########################
# author:   jbetley
# rev:     10.31.22

from dash import html, dash_table, Input, Output
from dash.exceptions import PreventUpdate
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign
import json
import pandas as pd
import numpy as np

from app import app
np.warnings.filterwarnings('ignore')

# default table styles
table_style = {
    'fontSize': '11px',
    'fontFamily': 'Roboto, sans-serif',
    'border': 'none'
}

table_header = {
    'height': '20px',
    'backgroundColor': '#ffffff',
    'border': 'none',
    'borderBottom': '.5px solid #6783a9',
    'fontSize': '12px',
    'fontFamily': 'Roboto, sans-serif',
    'color': '#6783a9',
    'textAlign': 'center',
    'fontWeight': 'bold'
}
# {
#     'backgroundColor': '#ffffff',
#     'fontSize': '11px',
#     'fontFamily': 'Roboto, sans-serif',
#     'color': '#6783a9',
#     'textAlign': 'center',
#     'fontWeight': 'bold'     
# }


table_header_conditional = [
    {
        'if': {
            'column_id': 'Category'
        },
        'textAlign': 'left',
        'paddingLeft': '10px',
        'width': '35%',
        'fontSize': '11px',
        'fontFamily': 'Roboto, sans-serif',
        'color': '#6783a9',
        'fontWeight': 'bold'
    }
]

table_cell = {
    'whiteSpace': 'normal',
    'height': 'auto',
    'textAlign': 'center',
    'color': '#6783a9',
#    'boxShadow': '0 0',
    'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
}

table_cell_conditional = [
    {
        'if': {
            'column_id': 'Category'
        },
        'textAlign': 'left',
        'fontWeight': '500',
        'paddingLeft': '10px',
        'width': '35%'
    }
]

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

@app.callback(
    Output('k8-grade-table', 'children'),
    Output('k8-ethnicity-table', 'children'),
    Output('k8-status-table', 'children'),
    Output('k8-other-table', 'children'),
    Output('k8-not-calculated-table', 'children'),
    Output('k8-table-container', 'style'),
    Output('hs-grad-overview-table', 'children'),    
    Output('hs-grad-ethnicity-table', 'children'),
    Output('hs-grad-status-table', 'children'),
    Output('hs-eca-table', 'children'),
    Output('hs-not-calculated-table', 'children'),
    Output('hs-table-container', 'style'),
    Input('dash-session', 'data')
)
def update_about_page(data):
    if not data:
        raise PreventUpdate

    # NOTE: removed 'American Indian' because the category doesn't appear in all data sets (?)
    #ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
    ethnicity = ['Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
    status = ['Special Education','General Education','Paid Meals','Free/Reduced Price Meals','English Language Learners','Non-English Language Learners']
    grades = ['Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8','Total','IREAD Pass %']

    school_index = pd.DataFrame.from_dict(data['0'])
    
    if school_index['School Type'].values[0] == 'K8' or school_index['School Type'].values[0] == 'K12':

        # k8_academic_data_json
        if data['10']:
            json_data = json.loads(data['10'])
            academic_data_k8 = pd.DataFrame.from_dict(json_data)

        else:
            academic_data_k8 = pd.DataFrame()

    if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'AHS' or school_index['School Type'].values[0] == 'K12':
        
        # hs_academic_data_json
        if data['11']:
            json_data = json.loads(data['11'])
            academic_data_hs = pd.DataFrame.from_dict(json_data)

        else:
            academic_data_hs = pd.DataFrame()

    # School_type determines which tables to display - default is display both
    k8_table_container = hs_table_container = {}

    # if school type is K8 and there is no data in dataframe, hide all tables and return a single table with 'No Data' message
    if school_index['School Type'].values[0] == 'K8' and len(academic_data_k8.index) == 0:

        hs_grad_overview_table = hs_grad_ethnicity_table = hs_grad_status_table = hs_eca_table = hs_not_calculated_table = []
        hs_table_container = {'display': 'none'}
        
        k8_grade_table = k8_ethnicity_table = k8_status_table = k8_other_table = k8_not_calculated_table = empty_table
        
    else:
        
        # K8 Academic Information
        # NOTE: there is no 2020 data for k8 schools, in the event 2020 is selected, 2019 data is displayed

        if school_index['School Type'].values[0] == 'K8' or school_index['School Type'].values[0] == 'K12':

            # if K8, hide HS table
            if school_index['School Type'].values[0] == 'K8':
                hs_grad_overview_table = hs_grad_ethnicity_table = hs_grad_status_table = hs_eca_table = hs_not_calculated_table = []
                hs_table_container = {'display': 'none'}

            # for academic information, strip out all comparative data and clean headers
            k8_academic_info = academic_data_k8[[col for col in academic_data_k8.columns if 'School' in col or 'Category' in col]]
            k8_academic_info.columns = k8_academic_info.columns.str.replace(r'School$', '')

            years_by_grade = k8_academic_info[k8_academic_info['Category'].str.contains('|'.join(grades))]
            years_by_status = k8_academic_info[k8_academic_info['Category'].str.contains('|'.join(status))]
            years_by_ethnicity = k8_academic_info[k8_academic_info['Category'].str.contains('|'.join(ethnicity))]
            
            # attendance_rate_data_json
            if data['16']:

                json_data = json.loads(data['16'])
                final_attendance_data = pd.DataFrame.from_dict(json_data)
                final_attendance_data = final_attendance_data[[col for col in final_attendance_data.columns if 'School' in col or 'Category' in col]]
                final_attendance_data.columns = final_attendance_data.columns.str.replace(r'School$', '')

                # replace 'metric' title with more generic name
                final_attendance_data['Category'] = 'Attendance Rate'
                
            else:
            
                final_attendance_data = pd.DataFrame()

            k8_not_calculated = [
                {'Category': 'The school’s teacher retention rate.'},
                {'Category': 'The school’s student re-enrollment rate.'},
                {'Category': 'Proficiency in ELA and Math of students who have been enrolled in school for at least two (2) full years.'},
                {'Category': 'Student growth on the state assessment in ELA and Math according to Indiana\'s Growth Model.'}
            ]

            k8_not_calculated_data = pd.DataFrame(k8_not_calculated)
            k8_not_calculated_data = k8_not_calculated_data.reindex(columns=k8_academic_info.columns)
            k8_not_calculated_data = k8_not_calculated_data.fillna('NA')

            k8_table_columns = [
                {
                    'name': col,
                    'id': col,
                    'type':'numeric',
                    'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
                    } for (col) in k8_academic_info.columns
            ]

            k8_table_data_conditional = [
                {
                    'if': {
                        'row_index': 'odd'
                    },
                    'backgroundColor': '#eeeeee'
                },
                {   # Not sure why this is necessary, but it is to ensure first col header has border
                    'if': {
                        'row_index': 0,
                        'column_id': 'Category'
                    },
                    'borderTop': '.5px solid #6783a9'
                }
            ]

            k8_grade_table = [
                        dash_table.DataTable(
                            years_by_grade.to_dict('records'),
                            columns = k8_table_columns,
                            style_data = table_style,
                            style_data_conditional = k8_table_data_conditional,
                            style_header = table_header,
                            style_cell = table_cell,
                            style_header_conditional = table_header_conditional,
                            style_cell_conditional = table_cell_conditional,
                            merge_duplicate_headers=True,
                            style_as_list_view=True,
                            # export_format='xlsx',
                            # export_headers='display'
                        )
            ]

            k8_ethnicity_table = [
                        dash_table.DataTable(
                            years_by_ethnicity.to_dict('records'),
                            columns = k8_table_columns,
                            style_data = table_style,
                            style_data_conditional = k8_table_data_conditional,
                            style_header = table_header,
                            style_header_conditional = table_header_conditional,                            
                            style_cell = table_cell,
                            style_cell_conditional = table_cell_conditional,
                            merge_duplicate_headers=True,
                            style_as_list_view=True
                        )
            ]

            k8_status_table = [
                        dash_table.DataTable(
                            years_by_status.to_dict('records'),
                            columns = k8_table_columns,
                            style_data = table_style,
                            style_data_conditional = k8_table_data_conditional,
                            style_header = table_header,
                            style_header_conditional = table_header_conditional,
                            style_cell = table_cell,
                            style_cell_conditional = table_cell_conditional,
                            merge_duplicate_headers=True,
                            style_as_list_view=True
                        )
            ]

            if not final_attendance_data.empty:

                k8_other_table = [
                            dash_table.DataTable(
                                final_attendance_data.to_dict('records'),
                                columns = k8_table_columns,
                                style_data = table_style,
                                style_data_conditional = k8_table_data_conditional,
                                style_header = table_header,
                                style_header_conditional = table_header_conditional,
                                style_cell = table_cell,
                                style_cell_conditional = table_cell_conditional,
                                merge_duplicate_headers=True,
                                style_as_list_view=True
                            )
                ]

            else:
                
                k8_other_table = empty_table

            k8_not_calculated_table = [
                        dash_table.DataTable(
                            k8_not_calculated_data.to_dict('records'),
                            columns = [{'name': i, 'id': i} for i in k8_not_calculated_data.columns],
                            style_data = table_style,
                            style_data_conditional = k8_table_data_conditional,
                            style_header = table_header,
                            style_header_conditional = table_header_conditional,
                            style_cell = table_cell,
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '10px',
                                    'width': '40%'                      # Width is different than default
                                },
                            ],
                            style_as_list_view=True
                        )
            ]

## TODO: ADD AHS DATA!

        # HS academic information
    if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'AHS' or school_index['School Type'].values[0] == 'K12':

        # if HS or AHS, hide K8 table
        if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'AHS':
            k8_grade_table = k8_ethnicity_table = k8_status_table = k8_other_table = k8_not_calculated_table = []
            k8_table_container = {'display': 'none'}

        if len(academic_data_hs.index) == 0:

            hs_grad_overview_table = hs_grad_ethnicity_table = hs_grad_status_table = hs_eca_table = hs_not_calculated_table = empty_table

        else:
            
            # split data into subsets for display in various tables
            overview = ['Total Graduation Rate','Non-Waiver Graduation Rate','State Average Graduation Rate','Strength of Diploma']

            if school_index['School Type'].values[0] == 'AHS':
                overview.append('CCR Percentage')

            # for academic information, strip out all comparative data and clean headers
            hs_academic_info = academic_data_hs[[col for col in academic_data_hs.columns if 'School' in col or 'Category' in col]]
            hs_academic_info.columns = hs_academic_info.columns.str.replace(r'School$', '')

            grad_overview = hs_academic_info[hs_academic_info['Category'].str.contains('|'.join(overview))]
            grad_ethnicity = hs_academic_info[hs_academic_info['Category'].str.contains('|'.join(ethnicity))]
            grad_status = hs_academic_info[hs_academic_info['Category'].str.contains('|'.join(status))]
            eca_data = hs_academic_info[hs_academic_info['Category'].str.contains('|'.join(['Grade 10']))]

            hs_not_calculated = [
                {'Category': 'The percentage of students entering grade 12 at the beginning of the school year who graduated from high school'},
                {'Category': 'The percentage of graduating students planning to pursue college or career (as defined by IDOE).'}
            ]

            hs_not_calculated_data = pd.DataFrame(hs_not_calculated)
            hs_not_calculated_data = hs_not_calculated_data.reindex(columns=hs_academic_info.columns)
            hs_not_calculated_data = hs_not_calculated_data.fillna('NA')

            hs_table_columns = [
                {
                    'name': col,
                    'id': col,
                    'type':'numeric',
                    'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
                    } for (col) in hs_academic_info.columns
            ]                
            
            # color average difference either red (lower than average) or green (higher than average) in '+/-' cols
            hs_table_data_conditional = [
                {
                    'if': {
                        'row_index': 'odd'
                    },
                    'backgroundColor': '#eeeeee'
                },
                {   # Not sure why this is necessary, but it is to ensure first col header has border
                    'if': {
                        'row_index': 0,
                        'column_id': 'Category'
                    },
                    'borderTop': '.5px solid #6783a9'
                }
            ]

            hs_grad_overview_table = [
                        dash_table.DataTable(
                            grad_overview.to_dict('records'),
                            columns = hs_table_columns,
                            style_data = table_style,
                            style_data_conditional = hs_table_data_conditional,
                            style_header = table_header,
                            style_cell = table_cell,
                            style_cell_conditional = [
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '20px',
                                    'width': '25%'
                                },
                            ],
                            merge_duplicate_headers=True,
                            style_as_list_view=True
                        )
            ]

            hs_grad_ethnicity_table = [
                        dash_table.DataTable(
                            grad_ethnicity.to_dict('records'),
                            columns = hs_table_columns,
                            style_data = table_style,
                            style_data_conditional = hs_table_data_conditional,
                            style_header = table_header,
                            style_cell = table_cell,
                            style_cell_conditional = [
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '20px',
                                    'width': '25%'
                                },
                            ],
                            merge_duplicate_headers=True,                        
                            style_as_list_view=True
                        )
            ]

            hs_grad_status_table = [
                        dash_table.DataTable(
                            grad_status.to_dict('records'),
                            columns = hs_table_columns,
                            style_data = table_style,
                            style_data_conditional = hs_table_data_conditional,
                            style_header = table_header,
                            style_cell = table_cell,
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '20px',
                                    'width': '25%'
                                },
                            ],
                            merge_duplicate_headers=True,
                            style_as_list_view=True
                        )
            ]

            hs_eca_table = [
                        dash_table.DataTable(
                            eca_data.to_dict('records'),
                            columns = hs_table_columns,
                            style_data = table_style,
                            style_data_conditional = hs_table_data_conditional,
                            style_header = table_header,
                            style_cell = table_cell,
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '20px',
                                    'width': '25%'
                                },
                            ],
                            merge_duplicate_headers=True,
                            style_as_list_view=True
                        )
            ]

            hs_not_calculated_table = [
                        dash_table.DataTable(
                            hs_not_calculated_data.to_dict('records'),
                            columns = [{'name': i, 'id': i, 'type':'numeric','format': FormatTemplate.percentage(2)} for i in hs_not_calculated_data.columns],
                            style_data = table_style,
                            style_data_conditional = hs_table_data_conditional,
                            style_header = table_header,
                            style_cell = table_cell,
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '20px',
                                    'width': '45%'
                                },
                            ],
                            style_as_list_view=True
                        )
            ]

    return k8_grade_table, k8_ethnicity_table, k8_status_table, k8_other_table, k8_not_calculated_table, k8_table_container, hs_grad_overview_table, \
        hs_grad_ethnicity_table, hs_grad_status_table, hs_eca_table, hs_not_calculated_table, hs_table_container

#### Layout

label_style = {
    'height': '20px',
    'backgroundColor': '#6783a9',
    'fontSize': '12px',
    'fontFamily': 'Roboto, sans-serif',
    'color': '#ffffff',
    'border': 'none',
    'textAlign': 'center',
    'fontWeight': 'bold',
    'paddingBottom': '5px',
    'paddingTop': '5px'
}

# NOTE: Adds md_table as a 'key'. Doesn't look great. Other options? go.table?

layout = html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Proficiency by Grade", style=label_style),
                                        html.Div(id='k8-grade-table')
                                    ],
                                    className = "pretty_container six columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Proficiency by Ethnicity", style=label_style),
                                        html.Div(id='k8-ethnicity-table')

                                    ],
                                    className = "pretty_container six columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Proficiency by Status", style=label_style),
                                        html.Div(id='k8-status-table')
                                    ],
                                    className = "pretty_container six columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Other Academic Indicators", style=label_style),
                                        html.Div(id='k8-other-table')
                                    ],
                                    className = "pretty_container six columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Not Currently Calculated", style=label_style),
                                        html.Div(id='k8-not-calculated-table')
                                    ],
                                    className = "pretty_container six columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                    ],
                    id = 'k8-table-container',
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Graduation Rate Overview", style=label_style),
                                        html.Div(id='hs-grad-overview-table')
                                    ],
                                    className = "pretty_container six columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Graduation Rate by Ethnicity", style=label_style),
                                        html.Div(id='hs-grad-ethnicity-table')
                                    ],
                                    className = "pretty_container six columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Graduation Rate by Status", style=label_style),
                                        html.Div(id='hs-grad-status-table')
                                    ],
                                    className = "pretty_container six columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("End of Course Assessments", style=label_style),
                                        html.Div(id='hs-eca-table')
                                    ],
                                    className = "pretty_container six columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Not Currently Calculated", style=label_style),
                                        html.Div(id='hs-not-calculated-table')
                                    ],
                                    className = "pretty_container six columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                    ],
                    id = 'hs-table-container',
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