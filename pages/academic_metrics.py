#####################################
# ICSB Dashboard - Academic Metrics #
#####################################
# author:   jbetley
# version:  1.03
# date:     5/22/23

import dash
from dash import html, Input, Output, callback
from dash.exceptions import PreventUpdate

import pandas as pd
import time

# TESTING
# pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
# TESTING

# import local functions
from .table_helpers import no_data_page, no_data_table, create_metric_table, \
    set_table_layout, get_svg_circle, create_key
from .subnav import subnav_academic
from .load_data import school_index, ethnicity, subgroup, grades_all, process_k8_academic_data, \
    process_high_school_academic_data, calculate_k8_yearly_metrics, calculate_k8_comparison_metrics, \
        calculate_iread_metrics, get_attendance_metrics, merge_high_school_data, calculate_high_school_metrics, \
        calculate_adult_high_school_metrics, filter_high_school_academic_data

from .load_db import get_k8_school_academic_data, get_high_school_academic_data, get_high_school_corporation_academic_data

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
    Output('academic-metrics-main-container', 'style'),
    Output('academic-metrics-empty-container', 'style'),
    Output('academic-metrics-no-data', 'children'),  
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
)
def update_academic_metrics(school: str, year: str):
    if not school:
        raise PreventUpdate

    # default styles
    display_attendance = {}
    display_k8_metrics = {}
    display_hs_metrics = {}
    display_ahs_metrics = {}
    main_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_to_display = no_data_page('Academic Metrics')    

    selected_school = school_index.loc[school_index['School ID'] == school]
    selected_school_type = selected_school['School Type'].values[0]
        
     # Adult High School Academic Metrics
    if selected_school_type == 'AHS':

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

        ahs_metrics = calculate_adult_high_school_metrics(school)

        if len(ahs_metrics) > 0:
            
            ahs_metric_data_113 = ahs_metrics.copy()

            ahs_metric_data_113['Category'] = ahs_metric_data_113['Metric'] + ' ' + ahs_metric_data_113['Category']
            
            ahs_metric_data_113 = ahs_metric_data_113.drop('Metric', axis=1)

            ahs_metric_label_113 = 'Adult High School Accountability Metrics 1.1 & 1.3'
            ahs_metric_data_113 = get_svg_circle(ahs_metric_data_113)            
            ahs_table_113 = create_metric_table(ahs_metric_label_113, ahs_metric_data_113)
            ahs_table_container_113 = set_table_layout(ahs_table_113, ahs_table_113, ahs_metric_data_113.columns)

            # Create placeholders (Adult Accountability Metrics 1.2.a, 1.2.b, 1.4.a, & 1.4.b)
            all_cols = ahs_metric_data_113.columns.tolist()
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

            ahs_metric_data_1214 = pd.concat([ahs_nocalc_empty, ahs_no_calc], ignore_index = True)
            ahs_metric_data_1214.reset_index()
            
            for h in ahs_metric_data_1214.columns:
                if 'Rate' in h:
                    ahs_metric_data_1214[h].fillna(value='N/A', inplace=True)
                else:
                    ahs_metric_data_1214[h].fillna(value='No Data', inplace=True)
            
            ahs_metric_label_1214 = 'Adult Accountability Metrics 1.2.a, 1.2.b, 1.4.a, & 1.4.b (Not Calculated)'
            ahs_metric_data_1214 = get_svg_circle(ahs_metric_data_1214) 
            ahs_table_1214 = create_metric_table(ahs_metric_label_1214, ahs_metric_data_1214)
            ahs_table_container_1214 = set_table_layout(ahs_table_1214, ahs_table_1214, ahs_metric_data_1214.columns)

        else:
            # school is AHS, but has no data
            ahs_table_container_113 = {}
            ahs_table_container_1214 = {}
            display_ahs_metrics = {'display': 'none'}
            main_container = {'display': 'none'}
            empty_container = {'display': 'block'}

    # K8, K12, & HS Accountability Metrics
    else:   
        
        # hide AHS metrics
        ahs_table_container_113 = {}
        ahs_table_container_1214 = {}
        display_ahs_metrics = {'display': 'none'}

        # High School Academic Metrics (including CHS if prior to 2021)
        if selected_school_type == 'HS' or selected_school_type == 'K12' or \
            (selected_school_type == '5874' and int(year) < 2021):
        
            # if HS only, no K8 data
            if selected_school_type == 'HS':
                table_container_11cd = {}
                table_container_14ab = {}
                table_container_14cd = {}
                table_container_14ef = {}
                table_container_14g = {}
                table_container_15abcd = {}
                table_container_16ab = {}
                table_container_16cd = {}
                display_k8_metrics = {'display': 'none'}

            t0 = time.process_time()
            raw_hs_school_data = get_high_school_academic_data(school)
            raw_hs_school_data = filter_high_school_academic_data(raw_hs_school_data)
            
            if len(raw_hs_school_data) > 0:

# TODO: What if there is no Corp Data?
                raw_hs_corp_data = get_high_school_corporation_academic_data(school)

                print(f'Time to load HS data: ' + str(time.process_time() - t0))

                t1 = time.process_time()
                for col in raw_hs_corp_data.columns:
                    raw_hs_corp_data[col] = pd.to_numeric(raw_hs_corp_data[col], errors='coerce')

                # NOTE: hs_data columns are a subset of school_data columns, but we still need to ensure hs_data
                # only includes columns that are in school_data (after being cleaned/filtered above). So we find
                # the intersection of the two sets and use it to filted hs_data
                common_cols = [col for col in set(raw_hs_school_data.columns).intersection(raw_hs_corp_data.columns)]
                raw_hs_corp_data = raw_hs_corp_data[common_cols]

                clean_hs_school_data = process_high_school_academic_data(raw_hs_school_data, year, school)
                clean_hs_corp_data = process_high_school_academic_data(raw_hs_corp_data, year, school)

                hs_merged_data = merge_high_school_data(clean_hs_school_data, clean_hs_corp_data, year)
                combined_grad_metrics_data = calculate_high_school_metrics(hs_merged_data)

                print(f'Time to process HS data: ' + str(time.process_time() - t1))

                t2 = time.process_time()
                metric_17ab_label = 'High School Accountability Metrics 1.7.a & 1.7.b'
                combined_grad_metrics_data = get_svg_circle(combined_grad_metrics_data)  
                table_17ab = create_metric_table(metric_17ab_label, combined_grad_metrics_data)
                table_container_17ab = set_table_layout(table_17ab, table_17ab, combined_grad_metrics_data.columns)

                # Create placeholders (High School Accountability Metrics 1.7.c & 1.7.d)
                all_cols = combined_grad_metrics_data.columns.tolist()
                simple_cols = [x for x in all_cols if (not x.endswith('+/-') and not x.endswith('Average'))]

                grad_metrics_empty = pd.DataFrame(columns = simple_cols)

                grad_metrics_dict = {
                    'Category': [
                        '1.7.c. The percentage of students entering Grade 12 at beginning of year who graduated',
                        '1.7.d. The percentage of graduating students planning to pursue collge or career.'
                    ]
                }
                grad_metrics = pd.DataFrame(grad_metrics_dict)

                metric_17cd_data = pd.concat([grad_metrics_empty, grad_metrics], ignore_index = True)
                metric_17cd_data.reset_index()

                for h in metric_17cd_data.columns:
                    if 'Rate' in h:
                        metric_17cd_data[h].fillna(value='N/A', inplace=True)
                    else:
                        metric_17cd_data[h].fillna(value='No Data', inplace=True)
                
                metric_17cd_label = 'High School Accountability Metrics 1.7.c & 1.7.d'
                metric_17cd_data = get_svg_circle(metric_17cd_data)          
                table_17cd = create_metric_table(metric_17cd_label, metric_17cd_data)
                table_container_17cd = set_table_layout(table_17cd, table_17cd, metric_17cd_data.columns)

                print(f'Time to create HS tables: ' + str(time.process_time() - t2))

            else:
                # school is HS, but has no data
                table_container_17ab = {}
                table_container_17cd = {}
                display_hs_metrics = {'display': 'none'}

                # no_data_to_display = no_data_page('Academic Accountability Metrics')
                main_container = {'display': 'none'}
                empty_container = {'display': 'block'}

        # K8 Academic Metrics (for K8 and K12 schools)
        if selected_school['School Type'].values[0] == 'K8' or selected_school['School Type'].values[0] == 'K12':

            # if schooltype is K8, hide 9-12(HS) tables (except for CHS prior to 2021)
            if selected_school['School Type'].values[0] == 'K8' and not (selected_school['School ID'].values[0] == '5874' and int(year) < 2021):
                table_container_17ab = {}
                table_container_17cd = {}
                display_hs_metrics = {'display': 'none'}

            t2_5 = time.process_time()
            raw_school_data = get_k8_school_academic_data(school)
            print(f'Time to load k8 data: ' + str(time.process_time() - t2_5))
            if len(raw_school_data) > 0:

                t3 = time.process_time()
                raw_school_data = raw_school_data.replace({"^": "***"})

                # keep only school columns with non-null data.
                valid_column_mask = raw_school_data.any()

                # valid_mask = ~pd.isnull(data[data.columns]).all()        
                raw_school_data = raw_school_data[raw_school_data.columns[valid_column_mask]]

                # raw_corp_data = get_k8_corporation_academic_data(school)

                # TODO: Does this need to be moved to calculate_comparison function?
                # # Find the common columns between the two dataframes - need to do this because
                # # school data has many more columns than col data
                # common_cols = [col for col in set(raw_school_data.columns).intersection(raw_corp_data.columns)]
                # raw_corp_data = raw_corp_data[common_cols]

                clean_school_data = process_k8_academic_data(raw_school_data, year, school)
                
                # # TODO: CURRENTLY GETTING CORP DATA IN calculate fn - it isn't used anywhere else
                # # TODO: and should only be called if school data is not null.
                # clean_corp_data = process_k8_academic_data(raw_corp_data, year, school)
           
                combined_years = calculate_k8_yearly_metrics(clean_school_data)
                combined_delta = calculate_k8_comparison_metrics(clean_school_data, year, school)

                category = ethnicity + subgroup

                print(f'Time to process K8 data: ' + str(time.process_time() - t3))

                t4 = time.process_time()
                metric_14a_data = combined_years[(combined_years['Category'].str.contains('|'.join(grades_all))) & (combined_years['Category'].str.contains('ELA'))]
                metric_14a_label = ['1.4a Grade level proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' compared with the previous school year.']

                metric_14a_data = get_svg_circle(metric_14a_data)
                table_14a = create_metric_table(metric_14a_label, metric_14a_data)

                metric_14b_data = combined_years[(combined_years['Category'].str.contains('|'.join(grades_all))) & (combined_years['Category'].str.contains('Math'))]
                metric_14b_label = ['1.4b Grade level proficiency on the state assessment in',html.Br(), html.U('Math'), ' compared with the previous school year.']
                
                metric_14b_data = get_svg_circle(metric_14b_data)
                table_14b = create_metric_table(metric_14b_label, metric_14b_data)

                table_container_14ab = set_table_layout(table_14a,table_14b,combined_years.columns)

                metric_14c_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(grades_all))) & (combined_delta['Category'].str.contains('ELA'))]
                metric_14c_label = ['1.4c Grade level proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' compared with traditional school corporation.']
                
                metric_14c_data = get_svg_circle(metric_14c_data)
                table_14c = create_metric_table(metric_14c_label, metric_14c_data)

                metric_14d_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(grades_all))) & (combined_delta['Category'].str.contains('Math'))]            
                metric_14d_label = ['1.4.d Grade level proficiency on the state assessment in',html.Br(), html.U('Math'), ' compared with traditional school corporation.']
                
                metric_14d_data = get_svg_circle(metric_14d_data)
                table_14d = create_metric_table(metric_14d_label, metric_14d_data)

                table_container_14cd = set_table_layout(table_14c,table_14d,combined_delta.columns)

                # Create placeholders (Accountability Metrics 1.4.e & 1.4.f)
                all_cols = combined_years.columns.tolist()
                simple_cols = [x for x in all_cols if not x.endswith('+/-')]

                year_proficiency_empty = pd.DataFrame(columns = simple_cols)

                year_proficiency_dict = {
                    'Category': ['1.4.e. Two (2) year student proficiency in ELA.', 
                            '1.4.f. Two (2) year student proficiency in Math.'
                        ]
                    }
                year_proficiency = pd.DataFrame(year_proficiency_dict)

                metric_14ef_data = pd.concat([year_proficiency_empty, year_proficiency], ignore_index = True)
                metric_14ef_data.reset_index()

                for h in metric_14ef_data.columns:
                    if 'Rate' in h:
                        metric_14ef_data[h].fillna(value='N/A', inplace=True)
                    else:
                        metric_14ef_data[h].fillna(value='No Data', inplace=True)

                metric_14ef_label = 'Percentage of students enrolled for at least two (2) school years achieving proficiency on the state assessment in English Language Arts (1.4.e.) and Math (1.4.f.)'
                metric_14ef_data = get_svg_circle(metric_14ef_data)
                table_14ef = create_metric_table(metric_14ef_label, metric_14ef_data)
                table_container_14ef = set_table_layout(table_14ef, table_14ef, metric_14ef_data.columns)

                # iread_data
                iread_df = clean_school_data[clean_school_data["Category"] == "IREAD Pass %"]

                if len(iread_df) > 0:

                    iread_data = calculate_iread_metrics(iread_df)

                    metric_14g_label = '1.4.g. Percentage of students achieving proficiency on the IREAD-3 state assessment.'
                    iread_data = get_svg_circle(iread_data)   
                    table_14g = create_metric_table(metric_14g_label, iread_data)
                    table_container_14g = set_table_layout(table_14g, table_14g, iread_data.columns)

                else:
                    table_container_14g = no_data_table('1.4.g Percentage of students achieving proficiency on the IREAD-3 state assessment.')

## TODO: MOVE GROWTH METRIC STUFF HERE
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
                    if 'Rate' in h:
                        metric_15abcd_data[h].fillna(value='N/A', inplace=True)
                    else:
                        metric_15abcd_data[h].fillna(value='No Data', inplace=True)

                metric_15abcd_label = 'Accountability Metrics 1.5.a, 1.5.b, 1.5.c, & 1.5.d'
                metric_15abcd_data = get_svg_circle(metric_15abcd_data)
                table_15abcd = create_metric_table(metric_15abcd_label, metric_15abcd_data)
                table_container_15abcd = set_table_layout(table_15abcd, table_15abcd, metric_15abcd_data.columns)

                metric_16a_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(category))) & (combined_delta['Category'].str.contains('ELA'))]
                metric_16a_label = ['1.6a Proficiency on the state assessment in ', html.U('English Language Arts'), html.Br(),'for each subgroup compared with traditional school corporation.']
                metric_16a_data = get_svg_circle(metric_16a_data)
                table_16a = create_metric_table(metric_16a_label,metric_16a_data)

                metric_16b_data = combined_delta[(combined_delta['Category'].str.contains('|'.join(category))) & (combined_delta['Category'].str.contains('Math'))]            
                metric_16b_label = ['1.6b Proficiency on the state assessment in ', html.U('Math'), ' for each', html.Br(), 'subgroup compared with traditional school corporation.']
                metric_16b_data = get_svg_circle(metric_16b_data)
                table_16b = create_metric_table(metric_16b_label, metric_16b_data)

                table_container_16ab = set_table_layout(table_16a,table_16b,combined_delta.columns)

                metric_16c_data = combined_years[(combined_years['Category'].str.contains('|'.join(category))) & (combined_years['Category'].str.contains('ELA'))]
                metric_16c_label = ['1.6c The change in proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' for each subgroup compared with the previous school year.']
                metric_16c_data = get_svg_circle(metric_16c_data)
                table_16c = create_metric_table(metric_16c_label,metric_16c_data)

                metric_16d_data = combined_years[(combined_years['Category'].str.contains('|'.join(category))) & (combined_years['Category'].str.contains('Math'))]
                metric_16d_label = ['1.6d The change in proficiency on the state assessment in',html.Br(), html.U('Math'), ' for each subgroup compared with the previous school year.']
                metric_16d_data = get_svg_circle(metric_16d_data)
                table_16d = create_metric_table(metric_16d_label,metric_16d_data)

                table_container_16cd = set_table_layout(table_16c,table_16d,combined_years.columns)

                print(f'Time to create K8 tables: ' + str(time.process_time() - t4))
            else:

                #if school type is K8 only but dataframes are empty
                table_container_11cd = {}
                table_container_14ab = {}
                table_container_14cd = {}
                table_container_14ef = {}
                table_container_14g = {}
                table_container_15abcd = {}
                table_container_16ab = {}
                table_container_16cd = {}
                display_k8_metrics = {'display': 'none'}
                main_container = {'display': 'none'}
                empty_container = {'display': 'block'}

    # Theoretically, this should never happen . . . which is why we are accounting for it.
    if selected_school_type != 'K8' and selected_school_type != 'K12' \
        and selected_school_type != 'HS' and selected_school_type != 'AHS':
        
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
        
        ahs_table_container_113 = {}
        ahs_table_container_1214 = {}
        display_ahs_metrics = {'display': 'none'}

        main_container = {'display': 'none'}
        empty_container = {'display': 'block'}

    # Attendance Data & Teacher Retention Rate (All schools have this data)
    metric_11ab_label = 'Student Attendance Rate (1.1.a) and Teacher Retention Rate (1.1.b) compared with traditional school corporation.'
    
    attendance_data = get_attendance_metrics(school, year)
    
    # Get a list of unique years from columns (used this to build Placeholder tables)
    # r = re.compile(".*([1-3][0-9]{3})")
    # year_group = [m.group(1) for l in attendance_data.columns.to_list() for m in [r.search(l)] if m]
    # year_columns = [*set(year_group)].sort()

    if len(attendance_data) > 0:

        # Create placeholders (Acountability Metric 1.1.b.)
        teacher_retention_rate = pd.DataFrame({'Category': ['1.1.b. Teacher Retention Rate']})

        metric_11ab_data = pd.merge(attendance_data, teacher_retention_rate, how='outer', on='Category')

        for h in metric_11ab_data.columns:
            if 'Rate' in h:
                metric_11ab_data[h].fillna(value='N/A', inplace=True)
            else:
                metric_11ab_data[h].fillna(value='No Data', inplace=True)

        metric_11ab_data = get_svg_circle(metric_11ab_data)
        table_11ab = create_metric_table(metric_11ab_label, metric_11ab_data)
        table_container_11ab = set_table_layout(table_11ab, table_11ab, metric_11ab_data.columns)

    else:

        table_container_11ab = {}
        table_container_11ab = no_data_table(metric_11ab_label)
        display_attendance = {'display': 'none'}

    # Re-enrollment Rates (Acountability Metrics 1.1.c & 1.1.d): Currently Placeholders
    metric_11cd_label = 'End of Year to Beginning of Year (1.1.c.) and Year over Year (1.1.d.) Student Re-Enrollment Rate.'
    
    # Only add placeholder if there is attendance data
    if len(attendance_data) > 0:

        student_retention_rate_dict = {'Category': ['1.1.c. Re-Enrollment Rate',
            '1.1.d. Re-Enrollment Rate']
        }
        
        mock_columns = [i for i in attendance_data.columns if 'Corp Avg' not in i]

        student_retention_empty = pd.DataFrame(columns = mock_columns)
        student_retention_rate = pd.DataFrame(student_retention_rate_dict)

        metric_11cd_data = pd.concat([student_retention_empty, student_retention_rate], ignore_index = True)
        metric_11cd_data.reset_index()

        for h in metric_11cd_data.columns:
            if 'Rate' in h:
                metric_11cd_data[h].fillna(value='N/A', inplace=True)
            else:
                metric_11cd_data[h].fillna(value='No Data', inplace=True)

        metric_11cd_data = get_svg_circle(metric_11cd_data)
        table_11cd = create_metric_table(metric_11cd_label, metric_11cd_data)
        table_container_11cd = set_table_layout(table_11cd, table_11cd, metric_11cd_data.columns)

    else:

        table_container_11cd = no_data_table(metric_11cd_label)
 
    return table_container_11ab, display_attendance, table_container_11cd, table_container_14ab, \
        table_container_14cd, table_container_14ef, table_container_14g, \
        table_container_15abcd, table_container_16ab, table_container_16cd, display_k8_metrics, \
        table_container_17ab, table_container_17cd, display_hs_metrics, \
        ahs_table_container_113, ahs_table_container_1214, display_ahs_metrics, \
        main_container, empty_container, no_data_to_display

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
                                        html.Label('Key', className = 'header_label'),        
                                        html.Div(create_key()),
                                    ],
                                    className = 'pretty_container six columns'
                                ),
                            ],
                            className = 'bare_container twelve columns'
                        ),
                        # Display attendance data in div outside of the metrics containers, because
                        # individual schools may have attendance data even if they have no academic data
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
        id='mainContainer'
    )