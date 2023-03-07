#####################################
# ICSB Dashboard - Academic Metrics #
#####################################
# author:   jbetley
# version:  .99.021323

import dash
from dash import html, dash_table, Input, Output, callback
from dash.dash_table.Format import Format, Scheme, Sign
from dash.exceptions import PreventUpdate
import json
import pandas as pd

from .table_helpers import no_data_page, no_data_table, create_metric_table, set_table_layout
from .subnav import subnav_academic

dash.register_page(__name__,  path = '/academic_metrics', order=5)

@callback(
    Output('table-container-11ab', 'children'),
    Output('display-attendance', 'style'),
    Output('table-container-11cd', 'children'),
    Output('table-container-14ab', 'children'),
    Output('table-container-14cd', 'children'),
    Output('table-container-14ef', 'children'),
    Output('table-container-14g', 'children'),
    Output('table-container-15abcd', 'children'),
    Output('table-container-16ab', 'children'),
    Output('table-container-16cd', 'children'),
    Output('display-k8-metrics', 'style'),
    Output('table-container-17ab', 'children'),
    Output('table-container-17cd', 'children'),
    Output('display-hs-metrics', 'style'),
    Output('table-container-ahs-113', 'children'),
    Output('table-container-ahs-1214', 'children'),
    Output('display-ahs-metrics', 'style'),
    # Output('table-container-empty', 'children'),
    # Output('display-empty-table', 'style'),
    Output('academic-metrics-main-container', 'style'),
    Output('academic-metrics-empty-container', 'style'),
    Output('academic-metrics-no-data', 'children'),  
    Input('dash-session', 'data'),
    Input('year-dropdown', 'value')
)
def update_academic_metrics(data,year):
    if not data:
        raise PreventUpdate

    school_index = pd.DataFrame.from_dict(data['0'])

    # default styles
    display_attendance = {}
    display_k8_metrics = {}
    display_hs_metrics = {}
    display_ahs_metrics = {}
    main_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_to_display = no_data_page('Academic Metrics')    

     # Adult High School Academic Metrics
    if school_index['School Type'].values[0] == 'AHS':

        # if AHS, hide all non-AHS related metrics
        table_container_11cd = {}
        table_container_14ab = {}
        table_container_14cd = {}
        table_container_14ef = {}
        table_container_14g = {}
        table_container_15abcd = {}
        table_container_16ab = {}
        table_container_16cd = {}
        display_k8_metrics = {'display': 'none'}

        table_container_17ab = {}
        table_container_17cd = {}
        display_hs_metrics = {'display': 'none'}

        # load ahs_academic_metrics_json
        if data['13']:
             
            json_data = json.loads(data['13'])
            metric_ahs_113_data = pd.DataFrame.from_dict(json_data)

            metric_ahs_113_data['Category'] = metric_ahs_113_data['Metric'] + ' ' + metric_ahs_113_data['Category']
            
            metric_ahs_113_data.drop('Metric', inplace=True, axis=1)

            metric_ahs_113_label = 'Adult High School Accountability Metrics 1.1 & 1.3'
            table_ahs_113 = create_metric_table(metric_ahs_113_label, metric_ahs_113_data)
            table_container_ahs_113 = set_table_layout(table_ahs_113, table_ahs_113, metric_ahs_113_data.columns)

            # Create placeholders (Adult Accountability Metrics 1.2.a, 1.2.b, 1.4.a, & 1.4.b)
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
                    metric_ahs_1214_data[h].fillna(value='N/A', inplace=True)
                else:
                    metric_ahs_1214_data[h].fillna(value='No Data', inplace=True)
            
            metric_ahs_1214_label = 'Adult Accountability Metrics 1.2.a, 1.2.b, 1.4.a, & 1.4.b (Not Calculated)'
            table_ahs_1214 = create_metric_table(metric_ahs_1214_label, metric_ahs_1214_data)
            table_container_ahs_1214 = set_table_layout(table_ahs_1214, table_ahs_1214, metric_ahs_1214_data.columns)

        else:
            # school is AHS, but has no data
            table_container_ahs_113 = {}
            table_container_ahs_1214 = {}
            display_ahs_metrics = {'display': 'none'}            
            # no_data_to_display = no_data_page('Adult High School Accountability Metrics')
            main_container = {'display': 'none'}
            empty_container = {'display': 'block'}

    # K8, K12, & High School Accountability Metrics
    else:   
        
        # hide AHS metrics
        table_container_ahs_113 = {}
        table_container_ahs_1214 = {}
        display_ahs_metrics = {'display': 'none'}

        # High School Academic Metrics (including CHS if prior to 2021)
        if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'K12' or \
            (school_index['School ID'].values[0] == '5874' and int(year) < 2021):
        
            # if HS only, no K8 data
            if school_index['School Type'].values[0] == 'HS':
                table_container_11cd = {}
                table_container_14ab = {}
                table_container_14cd = {}
                table_container_14ef = {}
                table_container_14g = {}
                table_container_15abcd = {}
                table_container_16ab = {}
                table_container_16cd = {}
                display_k8_metrics = {'display': 'none'}

            # combined_grad_metrics_json
            if data['14']:

                json_data = json.loads(data['14'])
                combined_grad_metrics_data = pd.DataFrame.from_dict(json_data)

                metric_17ab_label = 'High School Accountability Metrics 1.7.a & 1.7.b'
                table_17ab = create_metric_table(metric_17ab_label, combined_grad_metrics_data)
                table_container_17ab = set_table_layout(table_17ab, table_17ab, combined_grad_metrics_data.columns)

                # Create placeholders (High School Accountability Metrics 1.7.c & 1.7.d)
                all_cols = combined_grad_metrics_data.columns.tolist()
                simple_cols = [x for x in all_cols if (not x.endswith('+/-') and not x.endswith('Avg'))]

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
                table_17cd = create_metric_table(metric_17cd_label, metric_17cd_data)
                table_container_17cd = set_table_layout(table_17cd, table_17cd, metric_17cd_data.columns)

            else:
                # school is HS, but has no data
                table_container_17ab = {}
                table_container_17cd = {}
                display_hs_metrics = {'display': 'none'}
                # no_data_to_display = no_data_page('Academic Accountability Metrics')
                main_container = {'display': 'none'}
                empty_container = {'display': 'block'}

        # K8 Academic Metrics (for K8 and K12 schools)
        if school_index['School Type'].values[0] == 'K8' or school_index['School Type'].values[0] == 'K12':

            # if schooltype is K8, hide 9-12(HS) tables (except for CHS prior to 2021)
            if school_index['School Type'].values[0] == 'K8' and not (school_index['School ID'].values[0] == '5874' and int(year) < 2021):
                table_container_17ab = {}
                table_container_17cd = {}
                display_hs_metrics = {'display': 'none'}

            # load k-8 data files                        
            if (data['10'] and data['11']):

                # diff_to_corp_json
                json_data = json.loads(data['10'])
                combined_delta = pd.DataFrame.from_dict(json_data)

                # year_over_year_values_json
                json_data = json.loads(data['11'])
                combined_years = pd.DataFrame.from_dict(json_data)
                
                ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
                status = ['Special Education','General Education','Paid Meals','Free/Reduced Price Meals','English Language Learners','Non-English Language Learners']
                grades = ['Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8','Total','IREAD Pass %']
                subgroup = ethnicity + status

                metric_14a_data = combined_years[(combined_years['Category'].str.contains('|'.join(grades))) & (combined_years['Category'].str.contains('ELA'))]
                metric_14a_label = ['1.4a Grade level proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' compared with the previous school year.']
                table_14a = create_metric_table(metric_14a_label, metric_14a_data)

                metric_14b_data = combined_years[(combined_years['Category'].str.contains('|'.join(grades))) & (combined_years['Category'].str.contains('Math'))]
                metric_14b_label = ['1.4b Grade level proficiency on the state assessment in',html.Br(), html.U('Math'), ' compared with the previous school year.']
                table_14b = create_metric_table(metric_14b_label, metric_14b_data)

                table_container_14ab = set_table_layout(table_14a,table_14b,combined_years.columns)

                metric_14c_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(grades))) & (combined_delta['Category'].str.contains('ELA'))]
                metric_14c_label = ['1.4c Grade level proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' compared with traditional school corporation.']
                table_14c = create_metric_table(metric_14c_label, metric_14c_data)

                metric_14d_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(grades))) & (combined_delta['Category'].str.contains('Math'))]            
                metric_14d_label = ['1.4.d Grade level proficiency on the state assessment in',html.Br(), html.U('Math'), ' compared with traditional school corporation.']
                table_14d = create_metric_table(metric_14d_label, metric_14d_data)

                table_container_14cd = set_table_layout(table_14c,table_14d,combined_delta.columns)

                # Create placeholders (Accountability Metrics 1.4.e & 1.4.f)
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
                table_14ef = create_metric_table(metric_14ef_label, metric_14ef_data)
                table_container_14ef = set_table_layout(table_14ef, table_14ef, metric_14ef_data.columns)
                
                # iread_data_json
                if data['9']:
                    json_data = json.loads(data['9'])
                    iread_data = pd.DataFrame.from_dict(json_data)

                    metric_14g_label = '1.4.g. Percentage of students achieving proficiency on the IREAD-3 state assessment.'
                    table_14g = create_metric_table(metric_14g_label, iread_data)
                    table_container_14g = set_table_layout(table_14g, table_14g, iread_data.columns)

                else:
                    table_container_14g = no_data_table('1.4.g Percentage of students achieving proficiency on the IREAD-3 state assessment.')

                # Create placeholders (Accountability Metrics 1.5.a, 1.5.b, 1.5.c, & 1.5.d)
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
                table_15abcd = create_metric_table(metric_15abcd_label, metric_15abcd_data)
                table_container_15abcd = set_table_layout(table_15abcd, table_15abcd, metric_15abcd_data.columns)

                metric_16a_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(subgroup))) & (combined_delta['Category'].str.contains('ELA'))]
                metric_16a_label = ['1.6a Proficiency on the state assessment in ', html.U('English Language Arts'), html.Br(),'for each subgroup compared with traditional school corporation.']
                table_16a = create_metric_table(metric_16a_label,metric_16a_data)

                metric_16b_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(subgroup))) & (combined_delta['Category'].str.contains('Math'))]            
                metric_16b_label = ['1.6b Proficiency on the state assessment in ', html.U('Math'), ' for each', html.Br(), 'subgroup compared with traditional school corporation.']
                table_16b = create_metric_table(metric_16b_label, metric_16b_data)

                table_container_16ab = set_table_layout(table_16a,table_16b,combined_delta.columns)

                metric_16c_data = combined_years[(combined_years['Category'].str.contains('|'.join(subgroup))) & (combined_years['Category'].str.contains('ELA'))]
                metric_16c_label = ['1.6c The change in proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' for each subgroup compared with the previous school year.']
                table_16c = create_metric_table(metric_16c_label,metric_16c_data)

                metric_16d_data = combined_years[(combined_years['Category'].str.contains('|'.join(subgroup))) & (combined_years['Category'].str.contains('Math'))]
                metric_16d_label = ['1.6d The change in proficiency on the state assessment in',html.Br(), html.U('Math'), ' for each subgroup compared with the previous school year.']
                table_16d = create_metric_table(metric_16d_label,metric_16d_data)

                table_container_16cd = set_table_layout(table_16c,table_16d,combined_years.columns)

            else:

                # school is K8 only and has no data
                table_container_11cd = {}
                table_container_14ab = {}
                table_container_14cd = {}
                table_container_14ef = {}
                table_container_14g = {}
                table_container_15abcd = {}
                table_container_16ab = {}
                table_container_16cd = {}
                display_k8_metrics = {'display': 'none'}

                # no_data_to_display = no_data_page('Academic Accountability Metrics')
                main_container = {'display': 'none'}
                empty_container = {'display': 'block'}

    # If no matching school_type - display empty table (catch-all)
    if school_index['School Type'].values[0] != 'K8' and school_index['School Type'].values[0] != 'K12' and school_index['School Type'].values[0] != 'HS' and school_index['School Type'].values[0] != 'AHS':
        
        table_container_11ab = {}
        table_container_11cd = {}
        table_container_14ab = {}
        table_container_14cd = {}
        table_container_14ef = {}
        table_container_14g = {}
        table_container_15abcd = {}
        table_container_16ab = {}
        table_container_16cd = {}
        display_attendance = {'display': 'none'}
        display_k8_metrics = {'display': 'none'}

        table_container_17ab = {}
        table_container_17cd = {}
        display_hs_metrics = {'display': 'none'}
        
        table_container_ahs_113 = {}
        table_container_ahs_1214 = {}
        display_ahs_metrics = {'display': 'none'}

        # no_data_to_display = no_data_page('Academic Accountability Metrics')
        main_container = {'display': 'none'}
        empty_container = {'display': 'block'}

    metric_11ab_label = 'Accountability Metrics 1.1.a & 1.1.b'
    
    # attendance_data_metrics_json
    if data['5']:

        json_data = json.loads(data['5'])
        attendance_data = pd.DataFrame.from_dict(json_data)

        # Create placeholders (Acountability Metric 1.1.b.)
        teacher_retention_rate = pd.DataFrame({'Category': ['1.1.b. Teacher Retention Rate (compared to school corporation rate)']})

        metric_11ab_data = pd.merge(attendance_data, teacher_retention_rate, how='outer', on='Category')

        for h in metric_11ab_data.columns:
            if 'Rating' in h:
                metric_11ab_data[h].fillna(value='NA', inplace=True)
            else:
                metric_11ab_data[h].fillna(value='No Data', inplace=True)

        table_11ab = create_metric_table(metric_11ab_label, metric_11ab_data)
        table_container_11ab = set_table_layout(table_11ab, table_11ab, metric_11ab_data.columns)

    else:

        table_container_11ab = {}
        table_container_11ab = no_data_table(metric_11ab_label) # TODO
        display_attendance = {'display': 'none'}

    # Create placeholders (Acountability Metrics 1.1.c & 1.1.d)
    # if school has academic data
    metric_11cd_label = 'Accountability Metrics 1.1.c & 1.1.d'
    
    # Test to see if year_over_year_values_json exists
    if data['11']:

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

        table_11cd = create_metric_table(metric_11cd_label, metric_11cd_data)
        table_container_11cd = set_table_layout(table_11cd, table_11cd, metric_11cd_data.columns)

    else:

        table_container_11cd = no_data_table(metric_11cd_label)

#### ALL teh tables
 
    return table_container_11ab, display_attendance, table_container_11cd, table_container_14ab, \
        table_container_14cd, table_container_14ef, table_container_14g, \
        table_container_15abcd, table_container_16ab, table_container_16cd, display_k8_metrics, \
        table_container_17ab, table_container_17cd, display_hs_metrics, \
        table_container_ahs_113, table_container_ahs_1214, display_ahs_metrics, \
        main_container, empty_container, no_data_to_display

#### ALL teh layouts

key_label_style = {
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

# NOTE: Adds md_table as a 'key'. Doesn't look great. Other options? go.table?
def layout():
    return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(subnav_academic(),className='tabs'),
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
                                        html.Label('Key', style=key_label_style),
                                        html.Table(className='md_table',
                                            children = 
                                                [
                                                html.Tr( [html.Td('Corp Rate'), html.Td('The corporation rate for the school corporation in which the school\
                                                    is located (including only grades for which the school has a tested average).') ]),
                                                html.Tr( [html.Td('+/-'), html.Td('The difference between the school\'s proficiency and the corporation rate.') ]),
                                                html.Tr( [html.Td('Blank Cell'), html.Td('No data available.') ]),
                                                html.Tr( [html.Td('***'), html.Td(
                                                    [html.Span('Insufficient n-size (a '),
                                                    html.Span('-***', style={'color': '#b44655'}),
                                                    html.Span(' value indicates a reduction from a measurable, but not reportable, value to 0).')]
                                                ) ] ),
                                                ], 
                                                style={
                                                    'color': 'steelblue',
                                                    'fontSize': '.75em',
                                                },
                                        ),
                                        html.P(""),
                                        html.Center(
                                            html.P("Data Source: Indiana Department of Education Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)",
                                            style={
                                                'color': '#6783a9',
                                                'fontSize': 10,
                                                'marginLeft': '10px',
                                                'marginRight': '10px',
                                                'marginTop': '10px',
                                            })
                                        ),
                                    ],
                                    className = "pretty_container eight columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        # Display attendance separately: 1) because new schools will have attendance data even if they
                        # have no academic data, and 2) we measure it for HS (and AHS (?)) 
                        html.Div(
                            [
                                html.Div(id='table-container-11ab', children=[]),
                            ],
                            id = 'display-attendance',
                        ),
                        html.Div(
                            [
                                html.Div(id='table-container-11cd', children=[]),
                                html.Div(id='table-container-14ab', children=[]),
                                html.Div(id='table-container-14cd', children=[]),
                                html.Div(id='table-container-14ef', children=[]),
                                html.Div(id='table-container-14g', children=[]),
                                html.Div(id='table-container-15abcd', children=[]),
                                html.Div(id='table-container-16ab', children=[]),
                                html.Div(id='table-container-16cd', children=[]),
                            ],
                            id = 'display-k8-metrics',
                        ),
                        html.Div(
                            [
                                html.Div(id='table-container-17ab', children=[]),
                                html.Div(id='table-container-17cd', children=[]),
                            ],
                            id = 'display-hs-metrics',
                        ),
                        html.Div(
                            [
                                html.Div(id='table-container-ahs-113', children=[]),
                                html.Div(id='table-container-ahs-1214', children=[]),
                            ],
                            id = 'display-ahs-metrics',
                        ),
                    ],
                    id = 'academic-metrics-main-container',
                ),                
                html.Div(
                    [
                        html.Div(id='academic-metrics-no-data'),
                    ],
                    id = 'academic-metrics-empty-container',
                ),   
        ],
        id='mainContainer',
        style={
            'display': 'flex',
            'flexDirection': 'column'
        }
    )