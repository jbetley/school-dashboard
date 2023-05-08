#########################################
# ICSB Dashboard - Academic Information #
#########################################
# author:   jbetley
# version:  1.01.040323

import dash
from dash import html, Input, Output, callback, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import numpy as np
import json
import pandas as pd
import re
import os

# import local functions
from .table_helpers import no_data_page, no_data_table, create_academic_info_table, get_svg_circle
from .chart_helpers import no_data_fig_label, make_stacked_bar
from .calculations import round_percentages
from .subnav import subnav_academic

### Testing ###
# pd.set_option('display.max_rows', 400)

dash.register_page(__name__, top_nav=True, path='/academic_information', order=4)

@callback(
    Output('k8-grade-table', 'children'),
    Output('k8-grade-ela-fig', 'children'),
    Output('k8-grade-math-fig', 'children'),
    Output('k8-ethnicity-table', 'children'),
    Output('k8-ethnicity-ela-fig', 'children'),
    Output('k8-ethnicity-math-fig', 'children'),
    Output('k8-subgroup-table', 'children'),
    Output('k8-subgroup-ela-fig', 'children'),
    Output('k8-subgroup-math-fig', 'children'),
    Output('k8-other-table', 'children'),
    Output('k8-not-calculated-table', 'children'),
    Output('k8-table-container', 'style'),
    Output('hs-grad-overview-table', 'children'),
    Output('hs-grad-ethnicity-table', 'children'),
    Output('hs-grad-subgroup-table', 'children'),
    Output('sat-overview-table', 'children'),
    Output('sat-ethnicity-table', 'children'),
    Output('sat-subgroup-table', 'children'),
    Output('hs-eca-table', 'children'),
    Output('hs-not-calculated-table', 'children'),
    Output('hs-table-container', 'style'),
    Output('academic-information-main-container', 'style'),
    Output('academic-information-empty-container', 'style'),
    Output('academic-information-no-data', 'children'),
##
    Output('k8-overall-indicators', 'children'),
    Output('k8-growth-container', 'style'),        
    Output('hs-overall-indicators', 'children'),
    Output('combined-indicators', 'children'),
    Output('hs-growth-container', 'style'),    
    Output('enrollment-indicators', 'children'),
    Output('enrollment-container', 'style'),      
    Output('subgroup-grades', 'children'),
    Output('subgroup-grades-container', 'style'),      
    Output('k8-academic-achievement', 'children'),
    Output('k8-achievement-container', 'style'),        
    Output('hs-academic-achievement', 'children'),
    Output('hs-achievement-container', 'style'),        
    Output('k8-academic-progress', 'children'),
    Output('k8-progress-container', 'style'),       
    Output('hs-academic-progress', 'children'),
    Output('hs-progress-container', 'style'),       
    Output('closing-achievement-gap', 'children'),
    Output('closing-achievement-gap-container', 'style'),      
    Output('graduation-rate-indicator', 'children'),
    Output('strength-of-diploma-indicator', 'children'),
    Output('grad-indicator-container', 'style'),    
    Output('ela-progress-indicator', 'children'),
    Output('ela-progress-container', 'style'),       
    Output('absenteeism-indicator', 'children'),
    Output('absenteeism-container', 'style'),      
    Output('academic-growth-main-container', 'style'),
    Output('academic-growth-empty-container', 'style'),
    Output('academic-growth-no-data', 'children'),    
##
    Output('notes-string', 'children'),
    Input('dash-session', 'data'),
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    Input(component_id='radio-button-academic-info', component_property='value')
)
def update_academic_information_page(data, school, year, radio_value):
    if not data:
        raise PreventUpdate

    # NOTE: removed 'American Indian' because the category doesn't appear in all data sets
    # ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial', 'Native Hawaiian or Other Pacific Islander','White']
    ethnicity = [
        'Asian',
        'Black',
        'Hispanic',
        'Multiracial',
        'Native Hawaiian or Other Pacific Islander',
        'White'
    ]
    subgroup = [
        'Special Education',
        'General Education',
        'Paid Meals',
        'Free/Reduced Price Meals',
        'English Language Learners',
        'Non-English Language Learners'
    ]
    grades = [
        'Grade 3',
        'Grade 4',
        'Grade 5',
        'Grade 6',
        'Grade 7',
        'Grade 8',
        'Total',
        'IREAD Pass %'
    ]

    grades_ordinal = [
        '3rd',
        '4th',
        '5th',
        '6th',
        '7th',
        '8th'
    ]
    subject = ['ELA', 'Math']

    # default styles
    main_container = {'display': 'block'}
    k8_table_container = {'display': 'block'}
    hs_table_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_to_display = no_data_page('Academic Proficiency')
    
    main_growth_container = {'display': 'block'}
    k8_growth_container = hs_growth_container = enrollment_container = subgroup_grades_container = \
        k8_achievement_container = hs_achievement_container = k8_progress_container = \
        hs_progress_container = grad_indicator_container = closing_achievement_gap_container = \
        ela_progress_container = absenteeism_container = {'display': 'none'}
    
    empty_growth_container = {'display': 'none'}
    no_growth_data_to_display = no_data_page('Academic Growth')

    school_index = pd.DataFrame.from_dict(data['0'])
    
    if radio_value == 'proficiency':

        k8_overall_indicators = {}
        hs_overall_indicators = {}
        combined_indicators = {}
        enrollment_indicators = {}
        subgroup_grades = {}
        k8_academic_achievement = {}
        hs_academic_achievement = {}
        k8_academic_progress = {}
        hs_academic_progress = {}
        closing_achievement_gap = {}
        graduation_rate_indicator = {}
        strength_of_diploma_indicator = {}
        ela_progress_indicator = {}
        absenteeism_indicator = {}
        main_growth_container = {'display': 'none'}
        empty_growth_container = {'display': 'none'}

        if (
            school_index['School Type'].values[0] == 'K8'
            or school_index['School Type'].values[0] == 'K12'
        ):
            # load K8 academic_data
            if data['10']:
                json_data = json.loads(data['10'])
                academic_data_k8 = pd.DataFrame.from_dict(json_data)
            else:
                academic_data_k8 = pd.DataFrame()

        # NOTE: There is a special exception here for Christel House
        # South - prior to 2021, CHS was a K12. From 2021 onwards,
        # CHS is a K8, with the high school moving to Christel House
        # Watanabe Manual HS
        if (
            school_index['School Type'].values[0] == 'HS'
            or school_index['School Type'].values[0] == 'AHS'
            or school_index['School Type'].values[0] == 'K12'
            or (school_index['School ID'].values[0] == '5874' and int(year) < 2021)
        ):
            # load HS academic data
            if data['12']:
                json_data = json.loads(data['12'])
                academic_data_hs = pd.DataFrame.from_dict(json_data)
            else:
                academic_data_hs = pd.DataFrame()

        if (
            school_index['School Type'].values[0] == 'K8'
            and len(academic_data_k8.index) == 0
        ):
            hs_grad_overview_table = {}
            hs_grad_ethnicity_table = {}
            hs_grad_subgroup_table = {}
            sat_overview_table = {}
            sat_ethnicity_table = {}
            sat_subgroup_table = {}        
            hs_eca_table = {}
            hs_not_calculated_table = {}
            hs_table_container = {'display': 'none'}

            k8_grade_table = {}
            k8_ethnicity_table = {}
            k8_subgroup_table = {}
            k8_other_table = {}
            k8_not_calculated_table = {}
            k8_table_container = {'display': 'none'}

            k8_grade_ela_fig = {}
            k8_grade_math_fig = {}
            k8_ethnicity_ela_fig = {}
            k8_ethnicity_math_fig = {}
            k8_subgroup_ela_fig = {}
            k8_subgroup_math_fig = {}

            main_container = {'display': 'none'}
            empty_container = {'display': 'block'}

        else:

            ## K8 Academic Information
            if (
                school_index['School Type'].values[0] == 'K8'
                or school_index['School Type'].values[0] == 'K12'
            ):
                # if K8, hide HS table (except for CHS prior to 2021 when it was a K12)
                if school_index['School Type'].values[0] == 'K8' and not (
                    school_index['School ID'].values[0] == '5874' and int(year) < 2021
                ):
                    hs_grad_overview_table = {}
                    hs_grad_ethnicity_table = {}
                    hs_grad_subgroup_table = {}
                    sat_overview_table = {}
                    sat_ethnicity_table = {}
                    sat_subgroup_table = {}                  
                    hs_eca_table = {}
                    hs_not_calculated_table = {}
                    hs_table_container = {'display': 'none'}

                # for academic information, strip out all comparative data and clean headers
                k8_academic_info = academic_data_k8[
                    [
                        col
                        for col in academic_data_k8.columns
                        if 'School' in col or 'Category' in col
                    ]
                ]
                k8_academic_info.columns = k8_academic_info.columns.str.replace(
                    r'School$', '', regex=True
                )

                years_by_grade = k8_academic_info[
                    k8_academic_info['Category'].str.contains('|'.join(grades))
                ]
                if not years_by_grade.empty:
                    k8_grade_table = create_academic_info_table(years_by_grade,'Proficiency by Grade','proficiency')
                else:
                    k8_grade_table = no_data_table('Proficiency by Grade')

                years_by_subgroup = k8_academic_info[
                    k8_academic_info['Category'].str.contains('|'.join(subgroup))
                ]
                if not years_by_subgroup.empty:            
                    k8_subgroup_table = create_academic_info_table(years_by_subgroup,'Proficiency by Subgroup','proficiency')
                else:
                    k8_subgroup_table = no_data_table('Proficiency by Subgroup')

                years_by_ethnicity = k8_academic_info[
                    k8_academic_info['Category'].str.contains('|'.join(ethnicity))
                ]
                if not years_by_ethnicity.empty:            
                    k8_ethnicity_table = create_academic_info_table(years_by_ethnicity,'Proficiency by Ethnicity','proficiency')
                else:
                    k8_ethnicity_table = no_data_table('Proficiency by Ethnicity')

                # attendance_rate_data_json
                if data['4']:
                    json_data = json.loads(data['4'])
                    final_attendance_data = pd.DataFrame.from_dict(json_data)
                    final_attendance_data = final_attendance_data[
                        [
                            col
                            for col in final_attendance_data.columns
                            if 'School' in col or 'Category' in col
                        ]
                    ]
                    final_attendance_data.columns = (
                        final_attendance_data.columns.str.replace(
                            r'School$', '', regex=True
                        )
                    )

                    # replace 'metric' title with more generic name
                    final_attendance_data['Category'] = 'Attendance Rate'
                else:
                    final_attendance_data = pd.DataFrame()

                final_attendance_data = final_attendance_data.fillna('No Data')

                for col in final_attendance_data.columns:
                    final_attendance_data[col] = pd.to_numeric(final_attendance_data[col], errors='coerce').fillna(final_attendance_data[col]).tolist()

                if not final_attendance_data.empty:
                    k8_other_table = create_academic_info_table(final_attendance_data,'Attendance Data','proficiency')
                else:
                    k8_other_table = no_data_table('Attendance Data')

                k8_not_calculated = [
                    {
                        'Category': "The school’s teacher retention rate."
                    },
                    {
                        'Category': "The school’s student re-enrollment rate."
                    },
                    {
                        'Category': 'Proficiency in ELA and Math of students who have been enrolled in school for at least two (2) full years.'
                    },
                    {
                        'Category': "Student growth on the state assessment in ELA and Math according to Indiana's Growth Model."
                    },
                ]

                k8_not_calculated_data = pd.DataFrame(k8_not_calculated)
                k8_not_calculated_data = k8_not_calculated_data.reindex(
                    columns=k8_academic_info.columns
                )
                k8_not_calculated_data = k8_not_calculated_data.fillna('N/A')

                # as this is generated by the script, it will always have data
                k8_not_calculated_table = create_academic_info_table(k8_not_calculated_data,'Not Currently Calculated','proficiency')

                # Proficiency Breakdown stacked bar charts #
                
                # The raw proficency data from IDOE is annoyingly inconsistent. In some cases missing
                # data is blank and in other cases it is represented by '0.'
                k8_all_data_all_years = pd.read_csv(r'data/ilearnAll.csv', dtype=str)
                
                # Get selected school data for all categories
                school_k8_all_data = k8_all_data_all_years.loc[k8_all_data_all_years['School ID'] == school]

                school_k8_all_data =  school_k8_all_data.reset_index(drop=True)

                # show 2019 instead of 2020 as 2020 has no academic data
                year = '2019' if year == '2020' else year

                school_k8_proficiency_data = school_k8_all_data.loc[
                school_k8_all_data['Year'] == str(year)
                ]

                # drop columns with no values and reset index
                school_k8_proficiency_data = school_k8_proficiency_data.dropna(axis=1)
                school_k8_proficiency_data = school_k8_proficiency_data.reset_index()

                # NOTE: Leaving this line commented out means that pd.to_numeric
                # converts all '***' (e.g., where there were tested students, but
                # the proficiency value does not meet n-size requirements) values to NaN.
                # If we want to track those values, uncomment this line:

                # school_k8_proficiency_data =  school_k8_proficiency_data.replace({'***': float(-99)})

                for col in school_k8_proficiency_data.columns:
                    school_k8_proficiency_data[col] = pd.to_numeric(
                        school_k8_proficiency_data[col], errors='coerce'
                    )

                # Drop columns: 'Year','School ID', 'School Name', 'Corp ID','Corp Name'
                # which will automatically exclude these categories
                # Also drop 'ELA & Math' Category (not currently displayed on dashboard)
                school_k8_proficiency_data = school_k8_proficiency_data.drop(
                    list(
                        school_k8_proficiency_data.filter(
                            regex='ELA & Math|Year|Corp ID|Corp Name|School ID|School Name'
                        )
                    ),
                    axis=1,
                )

                all_proficiency_data = school_k8_proficiency_data.copy()

                proficiency_rating = [
                    'Below Proficiency',
                    'Approaching Proficiency',
                    'At Proficiency',
                    'Above Proficiency'
                ]

                # for each category, create a list of columns using the strings in
                # 'proficiency_rating' and then divide each column by 'Total Tested'
                categories = grades + ethnicity + subgroup

                # create dataframe to hold annotations (Categories missing data)
                # NOTE: Currently, annotations are stored but not used
                annotations = pd.DataFrame(columns= ['Category','Total Tested','Status'])

                for c in categories:
                    for s in subject:
                        category_subject = c + '|' + s
                        colz = [category_subject + ' ' + x for x in proficiency_rating]
                        total_tested = category_subject + ' ' + 'Total Tested'

                        # We do not want categories that do not appear in the dataframe
                        # At this point in the code there are three possible data 
                        # configurations for each column:
                        # 1) Total Tested > 0 and all proficiency_rating(s) are > 0
                        #   (School has tested category and there is publicly available data)
                        # 2) Total Tested > 0 and all proficiency_rating(s) are == 'NaN'
                        #   (School has tested category but there is no publicly available
                        #   data (insufficient N-size))) [do not display]
                        # 3) Total Tested AND all proficiency_rating == 0 (School does
                        #   not have tested category) [do not display]

                        # Neither (2) nor (3) should be displayed. However, we do want to
                        # track which Category/Subject combinations meet either condition
                        # (for figure annotation purposes). So we use a little trick. The
                        # sum of a series of '0' values is 0 (a numpy.int64). The sum of a
                        # series of 'NaN' values is also 0.0 (but the value is a float because
                        # numpy treats NaN as a numpy.float64). While either value returns True
                        # when tested if the value is 0, we can test the 'type' of the result (using
                        # np.integer and np.floating) to distinguish between them.

                        if total_tested in all_proficiency_data.columns:

                            if all_proficiency_data[colz].iloc[0].sum() == 0:

                                # if the value is a float, the measured values were NaN, which
                                # means they were converted '***', and thus insufficient data
                                if isinstance(all_proficiency_data[colz].iloc[0].sum(), np.floating):
                                    annotations.loc[len(annotations.index)] = [colz[0],all_proficiency_data[total_tested].values[0],'Insufficient']

                                # if the value is an integer, the measured values were 0, which
                                # means missing data
                                elif isinstance(all_proficiency_data[colz].iloc[0].sum(), np.integer):

                                    # Only add to annotations if it is a non 'Grade' category.
                                    # this is to account for IDOE's shitty data practices- sometimes
                                    # missing grades are blank (the correct way) and sometimes the
                                    # columns are filled with 0. So if everything is 0 AND it is a Grade
                                    # category, we assume it is just IDOE's fucked up data entry
                                    if ~all_proficiency_data[colz].columns.str.contains('Grade').any():
                                        annotations.loc[len(annotations.index)] = [colz[0],all_proficiency_data[total_tested].values[0],'Missing']

                                # either way, drop all columns related to the category from the df
                                all_colz = colz + [total_tested]

                                all_proficiency_data = all_proficiency_data.drop(all_colz, axis=1)

                            else:
                                # calculate percentage
                                all_proficiency_data[colz] = all_proficiency_data[colz].divide(
                                    all_proficiency_data[total_tested], axis='index'
                                )

                                # get a list of all values
                                row_list = all_proficiency_data[colz].values.tolist()

                                # round percentages using Largest Remainder Method
                                rounded = round_percentages(row_list[0])

                                # add back to dataframe
                                tmp_df = pd.DataFrame([rounded])
                                cols = list(tmp_df.columns)
                                all_proficiency_data[colz] = tmp_df[cols]

                            # each existing category has a calculated proficiency column
                            # named 'grade_subject'. Since we arent using it, we need to
                            # drop it from each category
                            all_proficiency_data.drop(category_subject, axis=1, inplace=True)

                # drop all remaining columns used for calculation that we
                # dont want to chart
                all_proficiency_data.drop(
                    list(
                        all_proficiency_data.filter(
                            regex='School Total|Total Proficient'
                        )
                    ),
                    axis=1,
                    inplace=True,
                )

                # Replace Grade X with ordinal number (e.g., Grade 4 = 4th)
                all_proficiency_data = all_proficiency_data.rename(
                    columns=lambda x: re.sub('(Grade )(\d)', '\\2th', x)
                )
                # all use 'th' suffix except for 3rd - so we need to specially treat '3''
                all_proficiency_data.columns = [
                    x.replace('3th', '3rd') for x in all_proficiency_data.columns.to_list()
                ]

                # transpose df
                all_proficiency_data = (
                    all_proficiency_data.T.rename_axis('Category')
                    .rename_axis(None, axis=1)
                    .reset_index()
                )

                # split Grade column into two columns and rename what used to be the index
                all_proficiency_data[['Category', 'Proficiency']] = all_proficiency_data[
                    'Category'
                ].str.split('|', expand=True)

                all_proficiency_data.rename(columns={0: 'Percentage'}, inplace=True)

                # Drop 'index' row (created during transpose)
                all_proficiency_data = all_proficiency_data[
                    all_proficiency_data['Category'] != 'index'
                ]

                ela_title = year + ' ELA Proficiency Breakdown'
                math_title = year + ' Math Proficiency Breakdown'
                
                # ELA by Grade
                grade_annotations = annotations.loc[annotations['Category'].str.contains('Grade')]

                grade_ela_fig_data = all_proficiency_data[
                    all_proficiency_data['Category'].isin(grades_ordinal)
                    & all_proficiency_data['Proficiency'].str.contains('ELA')
                ]

                if not grade_ela_fig_data.empty:
                    k8_grade_ela_fig = make_stacked_bar(grade_ela_fig_data,ela_title)
                else:
                    k8_grade_ela_fig = no_data_fig_label(ela_title, 100)

                # Math by Grade
                grade_math_fig_data = all_proficiency_data[
                    all_proficiency_data['Category'].isin(grades_ordinal)
                    & all_proficiency_data['Proficiency'].str.contains('Math')
                ]

                if not grade_math_fig_data.empty:
                    k8_grade_math_fig = make_stacked_bar(grade_math_fig_data,math_title)
                else:
                    k8_grade_math_fig = no_data_fig_label(math_title, 100)

                # ELA by Ethnicity
                ethnicity_annotations = annotations.loc[annotations['Category'].str.contains('Ethnicity')]

                ethnicity_ela_fig_data = all_proficiency_data[
                    all_proficiency_data['Category'].isin(ethnicity)
                    & all_proficiency_data['Proficiency'].str.contains('ELA')
                ]

                if not ethnicity_ela_fig_data.empty:
                    k8_ethnicity_ela_fig = make_stacked_bar(ethnicity_ela_fig_data,ela_title)
                else:
                    k8_ethnicity_ela_fig = no_data_fig_label(ela_title, 100)

                # Math by Ethnicity
                ethnicity_math_fig_data = all_proficiency_data[
                    all_proficiency_data['Category'].isin(ethnicity)
                    & all_proficiency_data['Proficiency'].str.contains('Math')
                ]

                if not ethnicity_math_fig_data.empty:
                    k8_ethnicity_math_fig = make_stacked_bar(ethnicity_math_fig_data,math_title)
                else:
                    k8_ethnicity_math_fig = no_data_fig_label(math_title, 100)

                # ELA by Subgroup
                subgroup_annotations = annotations.loc[annotations['Category'].str.contains('Subgroup')]

                subgroup_ela_fig_data = all_proficiency_data[
                    all_proficiency_data['Category'].isin(subgroup)
                    & all_proficiency_data['Proficiency'].str.contains('ELA')
                ]

                if not subgroup_ela_fig_data.empty:
                    k8_subgroup_ela_fig = make_stacked_bar(subgroup_ela_fig_data,ela_title)
                else:
                    k8_subgroup_ela_fig = no_data_fig_label(ela_title, 100)

                # Math by Subgroup
                subgroup_math_fig_data = all_proficiency_data[
                    all_proficiency_data['Category'].isin(subgroup)
                    & all_proficiency_data['Proficiency'].str.contains('Math')
                ]

                if not subgroup_math_fig_data.empty:
                    k8_subgroup_math_fig = make_stacked_bar(subgroup_math_fig_data,math_title)
                else:

                    k8_subgroup_math_fig = no_data_fig_label(math_title, 100)

        ## HS academic information
        if (
            school_index['School Type'].values[0] == 'HS'
            or school_index['School Type'].values[0] == 'AHS'
            or school_index['School Type'].values[0] == 'K12'
            or (school_index['School ID'].values[0] == '5874' and int(year) < 2021)
        ):
            # if HS or AHS, hide K8 table
            if (
                school_index['School Type'].values[0] == 'HS'
                or school_index['School Type'].values[0] == 'AHS'
            ):
                k8_grade_table = {}
                k8_ethnicity_table = {}
                k8_subgroup_table = {}
                k8_other_table = {}
                k8_not_calculated_table = {}

                k8_grade_ela_fig = {}
                k8_grade_math_fig = {}
                k8_ethnicity_ela_fig = {}
                k8_ethnicity_math_fig = {}
                k8_subgroup_ela_fig = {}
                k8_subgroup_math_fig = {}
                k8_table_container = {'display': 'none'}

            if len(academic_data_hs.index) == 0:
                hs_grad_overview_table = {}
                hs_grad_ethnicity_table = {}
                hs_grad_subgroup_table = {}
                sat_overview_table = {}
                sat_ethnicity_table = {}
                sat_subgroup_table = {}              
                hs_eca_table = {}
                hs_not_calculated_table = {}
                hs_table_container = {'display': 'none'}

                main_container = {'display': 'none'}
                empty_container = {'display': 'block'}

            else:

                # NOTE: Strength of Diploma not displayed

                # Gradution Rate
                grad_overview_categories = [
                    'Total',
                    'Non-Waiver',
                    'State Average'
                    # 'Strength of Diploma',
                ]

                if school_index['School Type'].values[0] == 'AHS':
                    grad_overview_categories.append('CCR Percentage')

                # strip out all comparative data and clean headers
                hs_academic_info = academic_data_hs[
                    [
                        col
                        for col in academic_data_hs.columns
                        if 'School' in col or 'Category' in col
                    ]
                ]

                hs_academic_info.columns = hs_academic_info.columns.str.replace(
                    r'School$', '', regex=True
                )

                eca_data = hs_academic_info[
                    hs_academic_info['Category'].str.contains('Grade 10')
                ].copy()
                if not eca_data.empty:            
                    hs_eca_table = create_academic_info_table(eca_data,'End of Course Assessments','proficiency')            
                else:
                    hs_eca_table = no_data_table('End of Course Assessments')

                # Graduation Rate Tables
                graduation_data = hs_academic_info[
                    hs_academic_info['Category'].str.contains('Graduation')
                ].copy()

                # drop 'Graduation Rate' from all 'Category' rows and remove whitespace
                graduation_data['Category'] = (
                    graduation_data['Category']
                    .str.replace('Graduation Rate', '')
                    .str.strip()
                )

                grad_overview = graduation_data[
                    graduation_data['Category'].str.contains('|'.join(grad_overview_categories))
                ]
                if not grad_overview.empty:
                    hs_grad_overview_table = create_academic_info_table(grad_overview,'Graduation Rate Overview','proficiency')
                else:
                    hs_grad_overview_table = no_data_table('Graduation Rate Overview')

                grad_ethnicity = graduation_data[
                    graduation_data['Category'].str.contains('|'.join(ethnicity))
                ]
                if not grad_ethnicity.empty:                 
                    hs_grad_ethnicity_table = create_academic_info_table(grad_ethnicity,'Graduation Rate by Ethnicity','proficiency')
                else:
                    hs_grad_ethnicity_table = no_data_table('Graduation Rate by Ethnicity')

                grad_subgroup = graduation_data[
                    graduation_data['Category'].str.contains('|'.join(subgroup))
                ]
                if not grad_subgroup.empty:                
                    hs_grad_subgroup_table = create_academic_info_table(grad_subgroup,'Graduation Rate by Subgroup','proficiency')
                else:
                    hs_grad_subgroup_table = no_data_table('Graduation Rate by Subgroup')

                # SAT Benchmark Tables
                sat_table_data = hs_academic_info[
                    hs_academic_info['Category'].str.contains('Benchmark %')
                ].copy()

                # drop 'Graduation Rate' from all 'Category' rows and remove whitespace
                sat_table_data['Category'] = (
                    sat_table_data['Category']
                    .str.replace('Benchmark %', '')
                    .str.strip()
                )

                sat_overview = sat_table_data[
                    sat_table_data['Category'].str.contains('School Total')
                ]
                if not sat_overview.empty:          
                    sat_overview_table = create_academic_info_table(sat_overview,'SAT Overview','proficiency')
                else:
                    sat_overview_table = no_data_table('SAT Overview')

                sat_ethnicity = sat_table_data[
                    sat_table_data['Category'].str.contains('|'.join(ethnicity))
                ]
                if not sat_ethnicity.empty:                 
                    sat_ethnicity_table = create_academic_info_table(sat_ethnicity,'SAT Benchmarks by Ethnicity','proficiency')
                else:
                    sat_ethnicity_table = no_data_table('SAT Benchmarks by Ethnicity')

                sat_subgroup = sat_table_data[
                    sat_table_data['Category'].str.contains('|'.join(subgroup))
                ]
                if not sat_subgroup.empty:                
                    sat_subgroup_table = create_academic_info_table(sat_subgroup,'SAT Benchmarks by Subgroup','proficiency')
                else:
                    sat_subgroup_table = no_data_table('SAT Benchmarks by Subgroup')

                hs_not_calculated = [
                    {
                        'Category': 'The percentage of students entering grade 12 at the beginning of the school year who graduated from high school'
                    },
                    {
                        'Category': 'The percentage of graduating students planning to pursue college or career (as defined by IDOE).'
                    },
                ]

                hs_not_calculated_data = pd.DataFrame(hs_not_calculated)
                hs_not_calculated_data = hs_not_calculated_data.reindex(
                    columns=hs_academic_info.columns
                )
                hs_not_calculated_data = hs_not_calculated_data.fillna('NA')

                hs_not_calculated_table = create_academic_info_table(hs_not_calculated_data,'Not Currently Calculated','proficiency')

    else:
        ## GROWTH TABLES ##

        # TODO: THIS IS HORRENDOUS - NOT SURE HOW TO DO CLEANLY WITHOUT EITHER DB
        # TODO: OR Multiplying csv's x 14
        
        # NOTE: This data sucks ass. It originates from an excel file that has a mishmash of small
        # tables with different headers and varying columns and rows. Data is different for different
        # grade configurations, and, to add insult to injury, sometimes tables are present with null
        # values and other times the tables are just missing. So we pull the data out by specific rows
        # in order to avoid column index errors when pandas tries to read it in all at once.

        growth_file = 'data/growth_data' + school + '.csv'

        # Adult high schools and new charter schools do not have growth data.
        if os.path.isfile(growth_file):

            # NOTE: This whole thing is terrible, because it means you cannot use
            # any global data-cleaning techniques. So there is much repitition. Must
            # figure out how to fix.

            k8_overall_indicators_data = pd.read_csv(growth_file, nrows=9)
            hs_overall_indicators_data = pd.read_csv(growth_file, skiprows=10, nrows=9)
            combined_indicators_data = pd.read_csv(growth_file, skiprows=20, nrows=3)
            enrollment_indicators_data = pd.read_csv(growth_file, skiprows=24, nrows=2)
            subgroup_grades_data = pd.read_csv(growth_file, skiprows=27, nrows=5)
            k8_academic_achievement_data = pd.read_csv(growth_file, skiprows=34, nrows=2)
            hs_academic_achievement_data = pd.read_csv(growth_file, skiprows=38, nrows=2)
            k8_academic_progress_data = pd.read_csv(growth_file, skiprows=42, nrows=2)
            hs_academic_progress_data = pd.read_csv(growth_file, skiprows=46, nrows=2)
            closing_achievement_gap_data = pd.read_csv(growth_file, skiprows=50, nrows=2)
            graduation_rate_indicator_data = pd.read_csv(growth_file, skiprows=53, nrows=1)
            strength_of_diploma_indicator_data = pd.read_csv(growth_file, skiprows=55, nrows=1)
            ela_progress_indicator_data = pd.read_csv(growth_file, skiprows=57, nrows=2)
            absenteeism_indicator_data = pd.read_csv(growth_file, skiprows=60, nrows=2)

            ## TODO: Do not display is information does not exist (one for each table)
           # TODO: align and arrange tables in a pleasing fashion

            pd.set_option('display.max_columns', None)
            pd.set_option('display.max_rows', None)

            if not k8_overall_indicators_data.isnull().all().all():

                # replace metrics with svg circles
                k8_overall_indicators_data = get_svg_circle(k8_overall_indicators_data)
               
                k8_overall_indicators = create_academic_info_table(k8_overall_indicators_data,'Elementary/Middle Growth Summary','growth')
                k8_growth_container = {'display': 'block'}
            else:
                k8_overall_indicators = {}
                k8_growth_container = {'display': 'none'}

            if not hs_overall_indicators_data.isnull().all().all():

                # drop null columns
                hs_overall_indicators_data = hs_overall_indicators_data.dropna(axis=1, how='all')

                # replace metrics with svg circles
                hs_overall_indicators_data = get_svg_circle(hs_overall_indicators_data)

                hs_overall_indicators = create_academic_info_table(hs_overall_indicators_data,'High School Growth Summary','growth')
                hs_growth_container = {'display': 'block'}
            else:
                hs_overall_indicators = {}
                hs_growth_container = {'display': 'none'} 

            if not combined_indicators_data.isnull().all().all():

                # combined indicators data has several null columns and no headers

                # drop empty columns
                combined_indicators_data = combined_indicators_data.dropna(axis=1, how='all')
                # in order to add a header without replacing the current header (which we want to
                # be the first row), we have to use some transpose shenanigans to add a dummy header
                # index to replace
                combined_indicators_data = combined_indicators_data.T.reset_index().T.reset_index(drop=True)
                combined_indicators_data.columns = ['Category','Weighted Points']

                # replace rating metrics with svg circles
                combined_indicators_data = get_svg_circle(combined_indicators_data)

                combined_indicators = create_academic_info_table(combined_indicators_data,'Combined Growth Summary','growth')
                hs_growth_container = {'display': 'block'}            
            else:
                combined_indicators = {}
                hs_growth_container = {'display': 'none'} 

            if not enrollment_indicators_data.isnull().all().all():
                
                # enrollment_indicators_data has two rows, Grades 3-8 and Grades 9-12, 
                # regardless of whether the school has data for both. In thus case
                # no data is represented by a '0'. This checks the second row (index 1)
                # and removes it if it is equal to '0'.
                if enrollment_indicators_data.iloc[1,1] == 0:
                    enrollment_indicators_data = enrollment_indicators_data.iloc[:1]        

                # rename first column
                enrollment_indicators_data = enrollment_indicators_data.rename(columns={enrollment_indicators_data.columns[0]: 'Grade Span'})
                
                enrollment_indicators = create_academic_info_table(enrollment_indicators_data,'Enrollment Indicators','growth')
                enrollment_container = {'display': 'block'}  
            else:
                enrollment_indicators = {}
                enrollment_container = {'display': 'none'}                 

            if not subgroup_grades_data.isnull().all().all():

                # subgroup grades data header is a mess, so easier to just replace the entire thing
                # need to account for duplicate headers for svg circle function
                subgroup_grades_data.columns = ['Subgroup1', 'Points1', 'Rating1', 'Subgroup2', 'Points2', 'Rating2']
                
                # replace rating metrics with svg circles
                subgroup_grades_data = get_svg_circle(subgroup_grades_data)
                
                # remove the numbers we added above for display purposes
                subgroup_grades_data.columns = subgroup_grades_data.columns.str.replace(r'1|2', '')

                subgroup_grades = create_academic_info_table(subgroup_grades_data,'Subgroup Grades','growth')
                subgroup_grades_container = {'display': 'block'}                
            else:
                subgroup_grades = {}
                subgroup_grades_container = {'display': 'none'}

            if not k8_academic_achievement_data.isnull().all().all():

                # remove excess spaces
                k8_academic_achievement_data = k8_academic_achievement_data.replace(r'\s+(?=[^(\)]*\))','', regex=True)
                k8_academic_achievement_data = k8_academic_achievement_data.replace(r'(?<=\d) +(?=%)','', regex=True)                

                k8_academic_achievement = create_academic_info_table(k8_academic_achievement_data,'Elementary/Middle Academic Achievement','growth')
                k8_achievement_container = {'display': 'block'}             
            else:
                k8_academic_achievement = {}
                k8_achievement_container = {'display': 'none'}  

            # skip category row in determining whether all cols are null
            if not hs_academic_achievement_data.iloc[:,1:].isna().all().all():
                
                # remove excess spaces
                hs_academic_achievement_data = hs_academic_achievement_data.replace(r'\s+(?=[^(\)]*\))','', regex=True) 
                hs_academic_achievement_data = hs_academic_achievement_data.replace(r'(?<=\d) +(?=%)','', regex=True) 
                
                hs_academic_achievement = create_academic_info_table(hs_academic_achievement_data,'High School Academic Achievement','growth')
                hs_achievement_container = {'display': 'block'}              
            else:
                hs_academic_achievement = {}
                hs_achievement_container = {'display': 'none'}              

            if not k8_academic_progress_data.iloc[:,1:].isna().all().all():

                # remove excess spaces
                k8_academic_progress_data = k8_academic_progress_data.replace(r'\s+(?=[^(\)]*\))','', regex=True)
                k8_academic_progress_data = k8_academic_progress_data.replace(r'(?<=\d) +(?=%)','', regex=True) 
                
                k8_academic_progress = create_academic_info_table(k8_academic_progress_data,'Elementary/Middle Progress Indicators','growth')
                k8_progress_container = {'display': 'block'}            
            else:
                k8_academic_progress = {}
                k8_progress_container = {'display': 'none'}

            if not hs_academic_progress_data.iloc[:,1:].isna().all().all():

                # remove excess spaces
                hs_academic_progress_data = hs_academic_progress_data.replace(r'\s+(?=[^(\)]*\))','', regex=True) 
                hs_academic_progress_data = hs_academic_progress_data.replace(r'(?<=\d) +(?=%)','', regex=True) 

                hs_academic_progress = create_academic_info_table(hs_academic_progress_data,'High School Progress Indicators','growth')
                hs_progress_container = {'display': 'block'}            
            else:
                hs_academic_progress = {}
                hs_progress_container = {'display': 'none'}

            if not closing_achievement_gap_data.iloc[:,1:].isna().all().all():

                # remove excess spaces
                closing_achievement_gap_data = closing_achievement_gap_data.replace(r'\s+(?=[^(\)]*\))','', regex=True) 
                closing_achievement_gap_data = closing_achievement_gap_data.replace(r'(?<=\d) +(?=%)','', regex=True) 

                closing_achievement_gap = create_academic_info_table(closing_achievement_gap_data,'Closing the Achievement Gap','growth')
                closing_achievement_gap_container = {'display': 'block'}            
            else:
                closing_achievement_gap = {}
                closing_achievement_gap_container = {'display': 'none'}

            if not graduation_rate_indicator_data.isnull().all().all():

                # remove excess spaces
                graduation_rate_indicator_data = graduation_rate_indicator_data.replace(r'\s+(?=[^(\)]*\))','', regex=True) 
                graduation_rate_indicator_data = graduation_rate_indicator_data.replace(r'(?<=\d) +(?=%)','', regex=True) 

                graduation_rate_indicator = create_academic_info_table(graduation_rate_indicator_data,'Graduation Rate Indicator','growth')
                grad_indicator_container = {'display': 'block'}            
            else:
                graduation_rate_indicator = {}
                grad_indicator_container = {'display': 'none'}

            if not strength_of_diploma_indicator_data.isnull().all().all():

                # remove excess spaces
                strength_of_diploma_indicator_data = strength_of_diploma_indicator_data.replace(r'\s+(?=[^(\)]*\))','', regex=True) 
                strength_of_diploma_indicator_data = strength_of_diploma_indicator_data.replace(r'(?<=\d) +(?=%)','', regex=True) 

                strength_of_diploma_indicator = create_academic_info_table(strength_of_diploma_indicator_data,'Strength of Diploma Indicator','growth')
                grad_indicator_container = {'display': 'block'}
            else:
                strength_of_diploma_indicator = {}
                grad_indicator_container = {'display': 'none'}

            if not ela_progress_indicator_data.iloc[:,1:].isna().all().all():

                # See comment for enrollment_indicators_data except it removes the row
                # if all the data columns are null.
                if ela_progress_indicator_data.loc[[1]].isna().sum().sum() >=3:
                    ela_progress_indicator_data = ela_progress_indicator_data.iloc[:1]

                # remove excess spaces
                ela_progress_indicator_data = ela_progress_indicator_data.replace(r'\s+(?=[^(\)]*\))','', regex=True) 
                ela_progress_indicator_data = ela_progress_indicator_data.replace(r'(?<=\d) +(?=%)','', regex=True) 

                ela_progress_indicator = create_academic_info_table(ela_progress_indicator_data,'Progress in Achieving English Language Proficiency Indicator','growth')
                ela_progress_container = {'display': 'block'}
            else:
                ela_progress_indicator = {}
                ela_progress_container = {'display': 'none'}

            if not absenteeism_indicator_data.iloc[:,1:].isna().all().all():

                # see comment for ela_progress_indicator_data
                if absenteeism_indicator_data.loc[[1]].isna().sum().sum() >=3:
                    absenteeism_indicator_data = absenteeism_indicator_data.iloc[:1]

                # remove excess spaces
                absenteeism_indicator_data = absenteeism_indicator_data.replace(r'\s+(?=[^(\)]*\))','', regex=True) 
                absenteeism_indicator_data = absenteeism_indicator_data.replace(r'(?<=\d) +(?=%)','', regex=True) 

                absenteeism_indicator = create_academic_info_table(absenteeism_indicator_data,'Addressing Chronic Absenteeism Indicator','growth')
                absenteeism_container = {'display': 'block'}
            else:
                absenteeism_indicator = {}
                absenteeism_container = {'display': 'none'}

            hs_grad_overview_table = {}
            hs_grad_ethnicity_table = {}
            hs_grad_subgroup_table = {}
            sat_overview_table = {}
            sat_ethnicity_table = {}
            sat_subgroup_table = {}        
            hs_eca_table = {}
            hs_not_calculated_table = {}
            hs_table_container = {'display': 'none'}

            k8_grade_table = {}
            k8_ethnicity_table = {}
            k8_subgroup_table = {}
            k8_other_table = {}
            k8_not_calculated_table = {}
            k8_table_container = {'display': 'none'}

            k8_grade_ela_fig = {}
            k8_grade_math_fig = {}
            k8_ethnicity_ela_fig = {}
            k8_ethnicity_math_fig = {}
            k8_subgroup_ela_fig = {}
            k8_subgroup_math_fig = {}

            main_container = {'display': 'none'}
            empty_container = {'display': 'none'}

        else:

            hs_grad_overview_table = {}
            hs_grad_ethnicity_table = {}
            hs_grad_subgroup_table = {}
            sat_overview_table = {}
            sat_ethnicity_table = {}
            sat_subgroup_table = {}        
            hs_eca_table = {}
            hs_not_calculated_table = {}
            hs_table_container = {'display': 'none'}

            k8_grade_table = {}
            k8_ethnicity_table = {}
            k8_subgroup_table = {}
            k8_other_table = {}
            k8_not_calculated_table = {}
            k8_table_container = {'display': 'none'}

            k8_grade_ela_fig = {}
            k8_grade_math_fig = {}
            k8_ethnicity_ela_fig = {}
            k8_ethnicity_math_fig = {}
            k8_subgroup_ela_fig = {}
            k8_subgroup_math_fig = {}

            main_container = {'display': 'none'}
            empty_container = {'display': 'none'}
            k8_overall_indicators = {}
            hs_overall_indicators = {}
            combined_indicators = {}
            enrollment_indicators = {}
            subgroup_grades = {}
            k8_academic_achievement = {}
            hs_academic_achievement = {}
            k8_academic_progress = {}
            hs_academic_progress = {}
            closing_achievement_gap = {}
            graduation_rate_indicator = {}
            strength_of_diploma_indicator = {}
            ela_progress_indicator = {}
            absenteeism_indicator = {}
            main_growth_container = {'display': 'none'}
            empty_growth_container = {'display': 'block'}
            k8_growth_container = hs_growth_container = enrollment_container = subgroup_grades_container = \
                k8_achievement_container = hs_achievement_container = k8_progress_container = \
                hs_progress_container = grad_indicator_container = closing_achievement_gap_container = \
                ela_progress_container = absenteeism_container = {'display': 'none'}            

    # back to main #

    # Add relevant notes string
    if school_index['School Type'].values[0] == 'AHS':
        notes_string = 'Adult High Schools enroll students who are over the age of 18, under credited, \
            dropped out of high school for a variety of reasons, and are typically out of cohort from \
            their original graduation year. Because graduation rate is calculated at the end of the school \
            year regardless of the length of time a student is enrolled at a school, it is not comparable to \
            the graduation rate of a traditional high school.'
        
    elif (
            school_index['School Type'].values[0] == 'K8'
            or school_index['School Type'].values[0] == 'K12'
            or school_index['School Type'].values[0] == 'HS'
            ):
        notes_string = 'There are a number of factors that make it difficult to make valid and reliable \
            comparisons between test scores from 2019 to 2022. For example, ILEARN was administered for \
            the first time during the 2018-19 SY and represented an entirely new type and mode of \
            assessment (adaptive and online-only). No State assessment was administered  in 2020 because \
            of the Covid-19 pandemic. Finally, the 2019 data set includes only students  who attended the \
            testing school for 162 days, while the 2021 and 2022 data sets included all tested students. \
            Data Source: Indiana Department of Education Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/).'
    else:
        notes_string = ''

    if radio_value == 'growth':
        notes_string = 'Growth Data comes from IDOE\'s School Report Card Summaries. While the data represented \
            here is an accurate representation of the data present in the Summaries, it has not been otherwise \
            reconciled with the raw data used to produce the Summaries. It is presented here in beta format and \
            should be used for informational purposes only.'
            
    return (
        k8_grade_table,
        k8_grade_ela_fig,
        k8_grade_math_fig,
        k8_ethnicity_table,
        k8_ethnicity_ela_fig,
        k8_ethnicity_math_fig,
        k8_subgroup_table,
        k8_subgroup_ela_fig,
        k8_subgroup_math_fig,
        k8_other_table,
        k8_not_calculated_table,
        k8_table_container,
        hs_grad_overview_table,
        hs_grad_ethnicity_table,
        hs_grad_subgroup_table,
        sat_overview_table,
        sat_ethnicity_table,
        sat_subgroup_table,
        hs_eca_table,
        hs_not_calculated_table,
        hs_table_container,
        main_container,
        empty_container,
        no_data_to_display,
##
        k8_overall_indicators,
        k8_growth_container,        
        hs_overall_indicators,
        combined_indicators,
        hs_growth_container,          
        enrollment_indicators,
        enrollment_container,
        subgroup_grades,
        subgroup_grades_container,
        k8_academic_achievement,
        k8_achievement_container,          
        hs_academic_achievement,
        hs_achievement_container,          
        k8_academic_progress,
        k8_progress_container,           
        hs_academic_progress,
        hs_progress_container,         
        closing_achievement_gap,
        closing_achievement_gap_container,
        graduation_rate_indicator,
        strength_of_diploma_indicator,
        grad_indicator_container,
        ela_progress_indicator,
        ela_progress_container,
        absenteeism_indicator,
        absenteeism_container,
        main_growth_container,
        empty_growth_container,
        no_growth_data_to_display,
        notes_string
)

def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(subnav_academic(), className='tabs'),
                        ],
                        className='bare_container twelve columns',
                    ),
                ],
                className='row',
            ),
            html.Div(
                [        
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label('Notes:', className='header_label'),
                                    html.P(''),
                                        html.P(id='notes-string',
                                            style={
                                                    'textAlign': 'Left',
                                                    'color': '#6783a9',
                                                    'fontSize': 12,
                                                    'marginLeft': '10px',
                                                    'marginRight': '10px',
                                                    'marginTop': '10px',
                                            }
                                        ),
                                ],
                                className = 'pretty_container seven columns'
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
                                    dbc.RadioItems(
                                        id='radio-button-academic-info',
                                        className='btn-group',
                                        inputClassName='btn-check',
                                        labelClassName='btn btn-outline-primary',
                                        labelCheckedClassName='active',
                                        options=[
                                            {'label': 'Proficiency', 'value': 'proficiency'},
                                            {'label': 'Growth', 'value': 'growth'},
                                        ],
                                        value='proficiency',
                                        persistence=True,
                                        persistence_type='local',
                                    ),
                                ],
                                className='radio-group',
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
                                    html.Div(
                                        [
                                            html.Div(id='k8-grade-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='k8-grade-ela-fig'),
                                        ],
                                        className='pretty_container four columns',
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id='k8-grade-math-fig'),
                                        ],
                                        className='pretty_container four columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='k8-ethnicity-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='k8-ethnicity-ela-fig'),
                                        ],
                                        className='pretty_container four columns',
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id='k8-ethnicity-math-fig'),
                                        ],
                                        className='pretty_container four columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='k8-subgroup-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='k8-subgroup-ela-fig'),
                                        ],
                                        className='pretty_container four columns',
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id='k8-subgroup-math-fig'),
                                        ],
                                        className='pretty_container four columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='k8-other-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='k8-not-calculated-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                        ],
                        id='k8-table-container',
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='hs-grad-overview-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='hs-grad-ethnicity-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='hs-grad-subgroup-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='sat-overview-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='sat-ethnicity-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='sat-subgroup-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),                            
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='hs-eca-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id='hs-not-calculated-table'),
                                        ],
                                        className='pretty_container six columns',
                                    ),
                                ],
                                className='bare_container twelve columns',
                            ),
                        ],
                        id='hs-table-container',
                    ),
                ],
                id = 'academic-information-main-container',
            ),
            html.Div(
                [
                    html.Div(id='academic-information-no-data'),
                ],
                id = 'academic-information-empty-container',
            ),            
########################################
            html.Div(
                [
                    # html.Div(
                    #     [
                            html.Div(
                                [                        
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(id='k8-overall-indicators'),
                                                ],
                                                className='pretty_container six columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),
                                ],
                                id='k8-growth-container',
                            ),                               
                            html.Div(
                                [                            
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(id='hs-overall-indicators'),
                                                ],
                                                className='pretty_container six columns',
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(id='combined-indicators'),
                                                ],
                                                className='pretty_container six columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),
                                ],
                                id='hs-growth-container',
                            ),
                            html.Div(
                                [                            
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(id='enrollment-indicators'),
                                                ],
                                                className='pretty_container six columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),
                                ],
                                id='enrollment-container',
                            ),       
                            html.Div(
                                [                                                    
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(id='subgroup-grades'),
                                                ],
                                                className='pretty_container six columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),
                                ],
                                id='subgroup-grades-container',
                            ),                               
                            html.Div(
                                [  
                                    html.Div(
                                        [                                  
                                            html.Div(
                                                [
                                                    html.Div(id='k8-academic-achievement'),
                                                ],
                                                className='pretty_container six columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),                                      
                                ],
                                id='k8-achievement-container',
                            ),
                                html.Div(
                                    [                                                             
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Div(id='hs-academic-achievement'),
                                                    ],
                                                    className='pretty_container six columns',
                                                ),
                                            ],
                                            className='bare_container twelve columns',
                                        ),
                                ],
                                id='hs-achievement-container',
                            ), 
                            html.Div(
                                [                             
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(id='k8-academic-progress'),
                                                ],
                                                className='pretty_container four columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),
                                ],
                                id='k8-progress-container',
                            ),                             
                            html.Div(
                                [                                 
                                    html.Div(
                                        [                                                                
                                            html.Div(
                                                [
                                                    html.Div(id='hs-academic-progress'),
                                                ],
                                                className='pretty_container four columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),
                                ],
                                id='hs-progress-container',
                            ),                                
                            html.Div(
                                [
                                    html.Div(
                                        [        
                                            html.Div(
                                                [
                                                    html.Div(id='closing-achievement-gap'),
                                                ],
                                                className='pretty_container six columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),
                                ],
                                id='closing-achievement-gap-container',
                            ),                              
                            html.Div(
                                [                            
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(id='graduation-rate-indicator'),
                                                ],
                                                className='pretty_container six columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(id='strength-of-diploma-indicator'),
                                                ],
                                                className='pretty_container six columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),
                                ],
                                id='grad-indicator-container',
                            ),
                            html.Div(
                                [                            
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(id='ela-progress-indicator'),
                                                ],
                                                className='pretty_container six columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),
                                ],
                                id='ela-progress-container',
                            ),
                            html.Div(
                                [                            
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(id='absenteeism-indicator'),
                                                ],
                                                className='pretty_container six columns',
                                            ),
                                        ],
                                        className='bare_container twelve columns',
                                    ),
                                ],
                                id='absenteeism-container',
                            ),
                            # TODO: Alternative to using style props to hide tables. Using this
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            dash_table.DataTable(id="hidden-table",
                                                columns=[
                                                    {'id': "foo", 'name': "bar"},
                                                ],
                                            ),
                                        ],
                                        className='pretty_container',# six columns',
                                    ),
                                ],
                                className='bare_container',# twelve columns',
                            ),
                    #     ],
                    #     id='k8-table-container',
                    # ),
                ],
                id = 'academic-growth-main-container',
            ),
            html.Div(
                [
                    html.Div(id='academic-growth-no-data'),
                ],
                id = 'academic-growth-empty-container',
            ),
############################################                 
        ],
        id='mainContainer',
    )