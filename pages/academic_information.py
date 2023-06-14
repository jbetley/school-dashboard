#########################################
# ICSB Dashboard - Academic Information #
#########################################
# author:   jbetley
# version:  1.03
# date:     5/22/23

import dash
from dash import html, Input, Output, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import re
import os
import time

# import local functions
from .table_helpers import no_data_page, no_data_table, hidden_table, create_academic_info_table, get_svg_circle
from .chart_helpers import no_data_fig_label, make_stacked_bar
from .calculations import round_percentages #, calculate_percentage
from .subnav import subnav_academic
from .load_data import school_index, ethnicity, subgroup, subject, grades, grades_all, grades_ordinal, \
    process_k8_academic_data, get_attendance_data, process_high_school_academic_data, get_excluded_years
from .load_db import get_k8_school_academic_data, get_high_school_academic_data, get_demographic_data, get_school_index

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
    Output('k8-overall-indicators', 'children'),
    Output('hs-overall-indicators', 'children'),
    Output('combined-indicators', 'children'),
    Output('enrollment-indicators', 'children'),
    Output('subgroup-grades', 'children'),
    Output('k8-academic-achievement', 'children'),
    Output('hs-academic-achievement', 'children'),
    Output('k8-academic-progress', 'children'),
    Output('hs-academic-progress', 'children'),
    Output('closing-achievement-gap', 'children'),
    Output('graduation-rate-indicator', 'children'),
    Output('strength-of-diploma-indicator', 'children'),
    Output('ela-progress-indicator', 'children'),
    Output('absenteeism-indicator', 'children'),
    Output('academic-growth-main-container', 'style'),
    Output('academic-growth-empty-container', 'style'),
    Output('academic-growth-no-data', 'children'),    
    Output('notes-string', 'children'),
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    Input(component_id='radio-button-academic-info', component_property='value')
)
def update_academic_information_page(school: str, year: str, radio_value:str):

    if not school:
        raise PreventUpdate

    # default styles
    main_container = {'display': 'block'}
    k8_table_container = {'display': 'block'}
    hs_table_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_to_display = no_data_page('Academic Proficiency')
    
    main_growth_container = {'display': 'block'}
    empty_growth_container = {'display': 'none'}
    no_growth_data_to_display = no_data_page('Academic Growth')

# TODO: ADD get_info()
    selected_school = school_index.loc[school_index['School ID'] == school]
    selected_school_type = selected_school['School Type'].values[0]

    ## Proficiency Tables ##
    if radio_value == 'proficiency':

        # set growth tables to null
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

        if (selected_school_type == 'K8' or selected_school_type == 'K12'):

            raw_k8_school_data = get_k8_school_academic_data(school)
            all_k8_school_data = process_k8_academic_data(raw_k8_school_data, year, school)

            all_k8_school_data = all_k8_school_data.fillna("No Data")

            # TODO: Errr
            if len(all_k8_school_data.index) == 0:
                all_k8_school_data = pd.DataFrame()
            
            else:

                all_k8_school_data = (all_k8_school_data.set_index(["Category"]).add_suffix("School").reset_index())

                all_k8_school_data.columns = all_k8_school_data.columns.str.replace(r'School$', '', regex=True)

                all_k8_school_data["Category"] = (all_k8_school_data["Category"].str.replace(" Proficient %", "").str.strip())

                all_k8_school_data.loc[all_k8_school_data["Category"] == "IREAD Pass %", "Category"] = "IREAD Proficiency (Grade 3 only)"

        else:
            all_k8_school_data = pd.DataFrame()

        # NOTE: There is a special exception here for Christel House South - prior to 2021,
        # CHS was a K12. From 2021 onwards, CHS is a K8, with the high school moving to
        # Christel House Watanabe Manual HS
        if (selected_school_type == 'HS' or selected_school_type == 'AHS' or selected_school_type == 'K12'
            or (selected_school['School ID'].values[0] == '5874' and int(year) < 2021)):

            # load HS academic data
            raw_hs_school_data = get_high_school_academic_data(school)
            all_hs_school_data = process_high_school_academic_data(raw_hs_school_data, year, school)

            # TODO: Errr.
            if len(all_hs_school_data.index) == 0:
                all_hs_school_data = pd.DataFrame()

        # If school is K8 and dataframe is empty set all tables to null and style properties to 'display': 'none' 
        # except for the empty table style
        if (selected_school_type == 'K8' and len(all_k8_school_data.index) == 0):
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
            # Both K8 school types and K12 school types can have K8 data
            if (selected_school_type == 'K8' or selected_school_type == 'K12'):

                # if K8, hide HS table (except for CHS prior to 2021 when it was a K12)
                if selected_school_type == 'K8' and not (selected_school_type == '5874' and int(year) < 2021):
                    hs_grad_overview_table = {}
                    hs_grad_ethnicity_table = {}
                    hs_grad_subgroup_table = {}
                    sat_overview_table = {}
                    sat_ethnicity_table = {}
                    sat_subgroup_table = {}                  
                    hs_eca_table = {}
                    hs_not_calculated_table = {}
                    hs_table_container = {'display': 'none'}

                years_by_grade = all_k8_school_data[all_k8_school_data['Category'].str.contains('|'.join(grades_all))]

                if not years_by_grade.empty:
                    k8_grade_table = create_academic_info_table(years_by_grade,'Proficiency by Grade','proficiency')
                else:
                    k8_grade_table = no_data_table('Proficiency by Grade')

                years_by_subgroup = all_k8_school_data[all_k8_school_data['Category'].str.contains('|'.join(subgroup))]

                if not years_by_subgroup.empty:            
                    k8_subgroup_table = create_academic_info_table(years_by_subgroup,'Proficiency by Subgroup','proficiency')
                else:
                    k8_subgroup_table = no_data_table('Proficiency by Subgroup')

                years_by_ethnicity = all_k8_school_data[all_k8_school_data['Category'].str.contains('|'.join(ethnicity))]

                if not years_by_ethnicity.empty:            
                    k8_ethnicity_table = create_academic_info_table(years_by_ethnicity,'Proficiency by Ethnicity','proficiency')
                else:
                    k8_ethnicity_table = no_data_table('Proficiency by Ethnicity')

                # Attendance rate
                school_demographic_data = get_demographic_data(school)
                attendance_rate = get_attendance_data(school_demographic_data, year)

                if len(attendance_rate.index) == 0:
                    k8_other_table = no_data_table('Attendance Data')
                else:
                    k8_other_table = create_academic_info_table(attendance_rate,'Attendance Data','proficiency')

                # TODO: K8 Information that is not calculated (is this info or Metrics?)
                k8_not_calculated = [
                    {'Category': "The school’s teacher retention rate."},
                    {'Category': "The school’s student re-enrollment rate."},
                    {'Category': 'Proficiency in ELA and Math of students who \
                     have been enrolled in school for at least two (2) full years.'},
                    {'Category': "Student growth on the state assessment in ELA and \
                     Math according to Indiana's Growth Model."},
                ]

                k8_not_calculated_data = pd.DataFrame(k8_not_calculated)
                k8_not_calculated_data = k8_not_calculated_data.reindex(columns = all_k8_school_data.columns)
                k8_not_calculated_data = k8_not_calculated_data.fillna('N/A')

                # as this is generated by the script, it will always have data
                k8_not_calculated_table = create_academic_info_table(k8_not_calculated_data,'Not Currently Calculated','proficiency')

                excluded_years = get_excluded_years(year)

# TODO: Move to function?
                ## Proficiency Breakdown ##
                proficiency_data = get_k8_school_academic_data(school)
                proficiency_data = proficiency_data[~proficiency_data["Year"].isin(excluded_years)]

                # IDOE's raw proficency data is annoyingly inconsistent. In some cases missing
                # data is blank and in other cases it is represented by '0.'

                # get all data
                t3 = time.process_time()

                # show 2019 instead of 2020 as 2020 has no academic data
                year = '2019' if year == '2020' else year

                school_k8_proficiency_data = proficiency_data.loc[proficiency_data['Year'] == int(year)]
                # school_k8_proficiency_data = school_all_k8_data.loc[school_all_k8_data['Year'] == int(year)]

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

                # Filter needed categories (this captures ELA&Math as well, which we drop later)

                school_k8_proficiency_data = school_k8_proficiency_data.filter(
                    regex=r"ELA Below|ELA At|ELA Approaching|ELA Above|ELA Total|Math Below|Math At|Math Approaching|Math Above|Math Total",
                    axis=1,
                )

                all_proficiency_data = school_k8_proficiency_data.copy()
                
                proficiency_rating = [
                    'Below Proficiency',
                    'Approaching Proficiency',
                    'At Proficiency',
                    'Above Proficiency'
                ]

                # for each category, create a proficiency_columns list of columns using the strings in
                # 'proficiency_rating' and then divide each column by 'Total Tested'
                categories = grades_all + ethnicity + subgroup

                # create dataframe to hold annotations (Categories missing data)
                # NOTE: Currently, annotations are stored but not used
                annotations = pd.DataFrame(columns= ['Category','Total Tested','Status'])

                for c in categories:
                    for s in subject:
                        category_subject = c + '|' + s
                        proficiency_columns = [category_subject + ' ' + x for x in proficiency_rating]
                        total_tested = category_subject + ' ' + 'Total Tested'

                        # We do not want categories that do not appear in the dataframe
                        # At this point in the code there are three possible data 
                        # configurations for each column:
                        # 1) Total Tested > 0 and all proficiency_rating(s) are > 0:
                        #       School has tested category and there is publicly available data
                        # 2) Total Tested > 0 and all proficiency_rating(s) are == 'NaN':
                        #       School has tested category but there is no publicly available
                        #       data (insufficient N-size) [do not display]
                        # 3) Total Tested AND all proficiency_rating == 0:
                        #       School does not have tested category [do not display]

                        # Neither (2) nor (3) should be displayed. However, we do want to
                        # track which Category/Subject combinations meet either condition
                        # (for figure annotation purposes). So we use a little trick. The
                        # sum of a series of '0' values is 0 (a numpy.int64). The sum of a
                        # series of 'NaN' values is also 0.0 (but the value is a float because
                        # numpy treats NaN as a numpy.float64). While either value returns True
                        # when tested if the value is 0, we can test the 'type' of the result (using
                        # np.integer and np.floating) to distinguish between them.

                        if total_tested in all_proficiency_data.columns:

                            if all_proficiency_data[proficiency_columns].iloc[0].sum() == 0:

                                # if the value is a float, the measured values were NaN, which
                                # means they were converted '***', and thus 'insufficient data'
                                if isinstance(all_proficiency_data[proficiency_columns].iloc[0].sum(), np.floating):
                                    annotations.loc[len(annotations.index)] = [proficiency_columns[0],all_proficiency_data[total_tested].values[0],'Insufficient']

                                # if the value is an integer, the measured values were 0, which
                                # means 'missing data'
                                elif isinstance(all_proficiency_data[proficiency_columns].iloc[0].sum(), np.integer):

                                    # Only add to annotations if it is a non 'Grade' category.
                                    # this is to account for IDOE's shitty data practices- sometimes
                                    # missing grades are blank (the correct way) and sometimes the
                                    # columns are filled with 0. So if everything is 0 AND it is a Grade
                                    # category, we assume it is just IDOE's fucked up data entry
                                    if ~all_proficiency_data[proficiency_columns].columns.str.contains('Grade').any():
                                        annotations.loc[len(annotations.index)] = [proficiency_columns[0],all_proficiency_data[total_tested].values[0],'Missing']

                                # either way, drop all columns related to the category from the df
                                all_proficiency_columns = proficiency_columns + [total_tested]

                                all_proficiency_data = all_proficiency_data.drop(all_proficiency_columns, axis=1)

                            else:
                                # calculate percentage
                                all_proficiency_data[proficiency_columns] = all_proficiency_data[proficiency_columns].divide(
                                    all_proficiency_data[total_tested], axis='index'
                                )

                                # get a list of all values
                                row_list = all_proficiency_data[proficiency_columns].values.tolist()

                                # round percentages using Largest Remainder Method
                                rounded = round_percentages(row_list[0])

                                # add back to dataframe
                                tmp_df = pd.DataFrame([rounded])
                                tmp_cols = list(tmp_df.columns)
                                all_proficiency_data[proficiency_columns] = tmp_df[tmp_cols]

                # drop all remaining columns used for calculation that we dont want to chart
                all_proficiency_data.drop(list(all_proficiency_data.filter(regex='Total\||Total Proficient|ELA and Math')),
                    axis=1,
                    inplace=True,
                )

                # Replace Grade X with ordinal number (e.g., Grade 4 = 4th)
                all_proficiency_data = all_proficiency_data.rename(columns=lambda x: re.sub('(Grade )(\d)', '\\2th', x))

                # all use 'th' suffix except for 3rd - so we need to specially treat '3''
                all_proficiency_data.columns = [x.replace('3th', '3rd') for x in all_proficiency_data.columns.to_list()]

                # transpose df
                all_proficiency_data = (
                    all_proficiency_data.T.rename_axis('Category')
                    .rename_axis(None, axis=1)
                    .reset_index()
                )

                # split Grade column into two columns and rename what used to be the index
                all_proficiency_data[['Category', 'Proficiency']] = all_proficiency_data['Category'].str.split('|', expand=True)

                all_proficiency_data.rename(columns={0: 'Percentage'}, inplace=True)

                all_proficiency_data = all_proficiency_data[all_proficiency_data['Category'] != 'index']

                load_proficiency_data = time.process_time() - t3

                print(f'Time to load proficiency data: ' + str(load_proficiency_data))

                ela_title = str(year) + ' ELA Proficiency Breakdown'
                math_title = str(year) + ' Math Proficiency Breakdown'

                t4 = time.process_time()

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

                load_proficiency_charts = time.process_time() - t4
                print(f'Time to load proficiency charts: ' + str(load_proficiency_charts))

        # Academic Information - High School #
        # Includes K12 and HS school_type
        if (selected_school_type == 'HS' or selected_school_type == 'AHS' or selected_school_type == 'K12'
            or (selected_school_type == '5874' and int(year) < 2021)):

            # if HS or AHS, hide K8 tables
            if (selected_school_type == 'HS' or selected_school_type == 'AHS'):
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

            # If school type is HS, AHS, or K12 but dataframe is empty
            # set everything to null/display:none except empty_container
            if len(all_hs_school_data.index) == 0:
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

                # Graduation Rate
                grad_overview_categories = [
                    'Total',
                    'Non Waiver',
                    'State Average'
                    # 'Strength of Diploma',    # Not currently displayed
                ]

                if selected_school_type == 'AHS':
                    grad_overview_categories.append('CCR Percentage')

                all_hs_school_data.columns = all_hs_school_data.columns.astype(str)

                eca_data = all_hs_school_data[all_hs_school_data['Category'].str.contains('Grade 10')].copy()

                if not eca_data.empty:            
                    hs_eca_table = create_academic_info_table(eca_data,'End of Course Assessments','proficiency')            
                else:
                    hs_eca_table = no_data_table('End of Course Assessments')

                # Graduation Rate Tables
                graduation_data = all_hs_school_data[all_hs_school_data['Category'].str.contains('Graduation')].copy()

                # drop 'Graduation Rate' from all 'Category' rows and remove whitespace
                graduation_data['Category'] = (graduation_data['Category'].str.replace('Graduation Rate', '').str.strip())

                grad_overview = graduation_data[graduation_data['Category'].str.contains('|'.join(grad_overview_categories))]

                if not grad_overview.empty:
                    hs_grad_overview_table = create_academic_info_table(grad_overview,'Graduation Rate Overview','proficiency')
                else:
                    hs_grad_overview_table = no_data_table('Graduation Rate Overview')

                grad_ethnicity = graduation_data[graduation_data['Category'].str.contains('|'.join(ethnicity))]

                if not grad_ethnicity.empty:                 
                    hs_grad_ethnicity_table = create_academic_info_table(grad_ethnicity,'Graduation Rate by Ethnicity','proficiency')
                else:
                    hs_grad_ethnicity_table = no_data_table('Graduation Rate by Ethnicity')

                grad_subgroup = graduation_data[graduation_data['Category'].str.contains('|'.join(subgroup))]

                if not grad_subgroup.empty:                
                    hs_grad_subgroup_table = create_academic_info_table(grad_subgroup,'Graduation Rate by Subgroup','proficiency')
                else:
                    hs_grad_subgroup_table = no_data_table('Graduation Rate by Subgroup')

                # SAT Benchmark Tables
                sat_table_data = all_hs_school_data[all_hs_school_data['Category'].str.contains('Benchmark %')].copy()

                # drop 'Graduation Rate' from all 'Category' rows and remove whitespace
                sat_table_data['Category'] = (sat_table_data['Category'].str.replace('Benchmark %', '').str.strip())

                sat_overview = sat_table_data[sat_table_data['Category'].str.contains('School Total')]

                if not sat_overview.empty:          
                    sat_overview_table = create_academic_info_table(sat_overview,'SAT Overview','proficiency')
                else:
                    sat_overview_table = no_data_table('SAT Overview')

                sat_ethnicity = sat_table_data[sat_table_data['Category'].str.contains('|'.join(ethnicity))]

                if not sat_ethnicity.empty:                 
                    sat_ethnicity_table = create_academic_info_table(sat_ethnicity,'SAT Benchmarks by Ethnicity','proficiency')
                else:
                    sat_ethnicity_table = no_data_table('SAT Benchmarks by Ethnicity')

                sat_subgroup = sat_table_data[sat_table_data['Category'].str.contains('|'.join(subgroup))]

                if not sat_subgroup.empty:                
                    sat_subgroup_table = create_academic_info_table(sat_subgroup,'SAT Benchmarks by Subgroup','proficiency')
                else:
                    sat_subgroup_table = no_data_table('SAT Benchmarks by Subgroup')

                hs_not_calculated = [
                    {'Category': 'The percentage of students entering grade 12 at the beginning of the school year who graduated from high school'},
                    {'Category': 'The percentage of graduating students planning to pursue college or career (as defined by IDOE).'}
                ]

                hs_not_calculated_data = pd.DataFrame(hs_not_calculated)
                hs_not_calculated_data = hs_not_calculated_data.reindex(columns = all_hs_school_data.columns)
                hs_not_calculated_data = hs_not_calculated_data.fillna('NA')

                hs_not_calculated_table = create_academic_info_table(hs_not_calculated_data,'Not Currently Calculated','proficiency')
        
    else:

        # set all proficiency tables to null and containers to display:none
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

        ## Build Growth Page ##
        # TODO: Move to Academic Metrics

        # NOTE: Currently have a single year of growth data (2022). Therefore unless
        # the selected year is 2022, we show an empty table.
        if year == '2022':
            # NOTE: This data sucks ass. It originates from an excel file that has a mishmash of small
            # tables with different headers and varying columns and rows. Data is different for different
            # grade configurations, and, to add insult to injury, sometimes tables are present with null
            # values and other times the tables are just missing. So we pull the data out by specific rows
            # in order to avoid column index errors when pandas tries to read it in all at once.
            
            # NOTE: the original excel files (format: "2022ReportCardSummary86855593ALL") are in even
            # worse shape with tables arranged horizontally and a liberal use of Merge Columns. There 
            # is a utility file ('_growthFileScrape.py') that converts these original files to a flattened
            # csv with all tables arranged vertically and missing tables represented by empty rows.
            # Unfortunately,it still has variable and unrelated columns, so we need to pull each individual
            # table out by row using iloc (e.g., growth_data.iloc[0:10]). Eventually we need to put
            # all this crap into a database.

            #TODO: Need to figure out a way to get this into DB
            growth_file = 'data/growth_data' + school + '.csv'
            
            # Adult high schools and new charter schools do not have growth data.
            # First check if there is a growth data file. There will either be a
            # file with data or there will not be a file. There will never be an
            # empty growth data file.
            if os.path.isfile(growth_file):

                # get all tables. Because there are variable columns, we set a fixed
                # range equal to the maximum number of columns
                growth_data = pd.read_csv(growth_file,header = None,names=range(8))

                # Global cleaning of growth data
                growth_data = growth_data.replace({
                    'English/Lang. Arts': 'ELA',
                    'Mathematics': 'Math',
                    'Sugroup': 'Subgroup',
                    'Hispanic Ethnicity': 'Hispanic',
                    'Elementary/Middle School Overall Weight and Points:': 'Overall',
                    'High School Overall Weight and Points:': 'Overall'
                    })

                # remove excess spaces between '(' and ')'
                growth_data = growth_data.replace(r'\s+(?=[^(\)]*\))','', regex=True)

                # remove extra space between number and '%'
                growth_data = growth_data.replace(r'(?<=\d) +(?=%)','', regex=True)                

                # Get individual tables one by one because tables have variable
                # number of columns

                def replace_header(data: pd.DataFrame) -> pd.DataFrame:
                    """ Takes a Pandas Dataframe, replaces header with first row, and
                        drops all nan columns
                    Args:
                        data (pd.Dataframe): Pandas dataframe

                    Returns:
                        pd.Dataframe: returns the same dataframe first row headers and
                        no NaN columns
                    """
                    data.columns = data.iloc[0].tolist()
                    data = data[1:]
                    data = data.dropna(axis=1, how='all')

                    return data
        
                ## k8 growth indicators ##
                k8_overall_indicators_data = growth_data.iloc[0:10].copy()

                if not k8_overall_indicators_data.isnull().all().all():
                    
                    k8_overall_indicators_data = replace_header(k8_overall_indicators_data)

                    # Drop rows where there are zero points and No Rating
                    k8_overall_indicators_data = k8_overall_indicators_data.loc[~((k8_overall_indicators_data['Points'] == '0.00') & \
                        (k8_overall_indicators_data['Rating'] == 'No Rating'))]
                    
                    # replace metrics with svg circles
                    k8_overall_indicators_data = get_svg_circle(k8_overall_indicators_data)
                
                    k8_overall_indicators = create_academic_info_table(k8_overall_indicators_data,'Elementary/Middle Growth Summary','growth')
                else:
                    k8_overall_indicators = hidden_table()

                ## hs growth indicators ##
                hs_overall_indicators_data = growth_data.iloc[10:20].copy()

                if not hs_overall_indicators_data.isnull().all().all():

                    hs_overall_indicators_data = replace_header(hs_overall_indicators_data)

                    hs_overall_indicators_data = hs_overall_indicators_data.loc[~((hs_overall_indicators_data['Points'] == '0.00') & \
                        (hs_overall_indicators_data['Rating'] == 'No Rating'))]
                    
                    hs_overall_indicators_data = get_svg_circle(hs_overall_indicators_data)

                    hs_overall_indicators = create_academic_info_table(hs_overall_indicators_data,'High School Growth Summary','growth')
                else:
                    hs_overall_indicators = hidden_table()

                ## combined growth indicators ##
                combined_indicators_data = growth_data.iloc[20:24].copy()

                if not combined_indicators_data.isnull().all().all():

                    # drop empty columns and add headers
                    combined_indicators_data = combined_indicators_data.dropna(axis=1, how='all')
                    combined_indicators_data.columns = ['Category','Weighted Points']
                    
                    combined_indicators_data = get_svg_circle(combined_indicators_data)

                    combined_indicators = create_academic_info_table(combined_indicators_data,'Combined Growth Summary','growth')
                else:
                    combined_indicators = hidden_table()

                ## enrollment indicators ##
                enrollment_indicators_data = growth_data.iloc[24:27].copy()

                if not enrollment_indicators_data.isnull().all().all():
                    
                    enrollment_indicators_data = replace_header(enrollment_indicators_data)

                    # some tables, including enrollment_indicators_data, have a Grades 3-8 row
                    # and a Grades 9-12 row regardless of whether the school has data for both.
                    # So either check second row for '0' (as in this case) or NaN and remove if true.
                    if enrollment_indicators_data.iloc[1,1] == '0':
                        enrollment_indicators_data = enrollment_indicators_data.iloc[:1]        

                    # rename first column
                    enrollment_indicators_data = enrollment_indicators_data.rename(columns={enrollment_indicators_data.columns[0]: 'Grade Span'})
                    
                    enrollment_indicators = create_academic_info_table(enrollment_indicators_data,'Enrollment Indicators','growth')
                else:
                    enrollment_indicators = hidden_table()

                ## subgroup grades indicators ##
                subgroup_grades_data = growth_data.iloc[27:33].copy()

                if not subgroup_grades_data.isnull().all().all():
                    
                    subgroup_grades_data = replace_header(subgroup_grades_data)

                    # subgroup_grades_data is two tables side by side with the same column headers.
                    # We use groupby() to unpivot & combine the duplicate columns, and then reorder
                    # the columns
                    subgroup_grades_data = subgroup_grades_data.groupby(subgroup_grades_data.columns.values, axis=1).agg(lambda x: x.values.tolist()).sum().apply(pd.Series).T
                    subgroup_grades_data = subgroup_grades_data[['Subgroup', 'Points', 'Rating']]

                    subgroup_grades_data = subgroup_grades_data.loc[~((subgroup_grades_data['Points'] == '0') & \
                        (subgroup_grades_data['Rating'] == 'No Rating'))]

                    subgroup_grades_data = get_svg_circle(subgroup_grades_data)
                    
                    subgroup_grades = create_academic_info_table(subgroup_grades_data,'Subgroup Grades','growth')
                else:
                    subgroup_grades = hidden_table()

                ## k8 academic achievement indicators ##
                k8_academic_achievement_data = growth_data.iloc[34:37].copy()

                if not k8_academic_achievement_data.iloc[1:,1:].isnull().all().all():

                    k8_academic_achievement_data = replace_header(k8_academic_achievement_data)

                    k8_academic_achievement = create_academic_info_table(k8_academic_achievement_data,'Elementary/Middle Academic Achievement','growth')
                else:
                    k8_academic_achievement = hidden_table()

                ## hs academic achievement indicators ##
                hs_academic_achievement_data = growth_data.iloc[38:41].copy()

                # skip 1st column and 1st row in determining whether all cols are null
                if not hs_academic_achievement_data.iloc[1:,1:].isna().all().all():

                    hs_academic_achievement_data = replace_header(hs_academic_achievement_data)

                    hs_academic_achievement = create_academic_info_table(hs_academic_achievement_data,'High School Academic Achievement','growth')
            
                else:
                    hs_academic_achievement = hidden_table()

                ## k8 academic progress indicators ##
                k8_academic_progress_data = growth_data.iloc[42:45].copy()

                if not k8_academic_progress_data.iloc[1:,1:].isna().all().all():

                    k8_academic_progress_data = replace_header(k8_academic_progress_data)

                    k8_academic_progress = create_academic_info_table(k8_academic_progress_data,'Elementary/Middle Progress Indicators','growth')
                else:
                    k8_academic_progress = hidden_table()

                ## hs academic progress indicators ##
                hs_academic_progress_data = growth_data.iloc[46:49].copy()

                if not hs_academic_progress_data.iloc[1:,1:].isna().all().all():

                    hs_academic_progress_data = replace_header(hs_academic_progress_data)

                    hs_academic_progress = create_academic_info_table(hs_academic_progress_data,'High School Progress Indicators','growth')
                else:
                    hs_academic_progress = hidden_table()

                ## closing achievement gap indicators ##
                closing_achievement_gap_data = growth_data.iloc[50:53].copy()

                if not closing_achievement_gap_data.iloc[1:,1:].isna().all().all():

                    closing_achievement_gap_data = replace_header(closing_achievement_gap_data)

                    closing_achievement_gap = create_academic_info_table(closing_achievement_gap_data,'Closing the Achievement Gap','growth')
        
                else:
                    closing_achievement_gap = hidden_table()

                ## graduation rate indicator ##
                graduation_rate_indicator_data = growth_data.iloc[53:55].copy()

                if not graduation_rate_indicator_data.isnull().all().all():

                    graduation_rate_indicator_data = replace_header(graduation_rate_indicator_data)

                    graduation_rate_indicator = create_academic_info_table(graduation_rate_indicator_data,'Graduation Rate Indicator','growth')
                else:
                    graduation_rate_indicator = hidden_table()

                ## strength of diploma indicator ##
                strength_of_diploma_indicator_data = growth_data.iloc[55:57].copy()

                if not strength_of_diploma_indicator_data.isnull().all().all():

                    strength_of_diploma_indicator_data = replace_header(strength_of_diploma_indicator_data)
                    
                    strength_of_diploma_indicator = create_academic_info_table(strength_of_diploma_indicator_data,'Strength of Diploma Indicator','growth')
                else:
                    strength_of_diploma_indicator = hidden_table()

                ## ela progress indicators ##
                ela_progress_indicator_data = growth_data.iloc[57:60].copy()

                if not ela_progress_indicator_data.iloc[1:,1:].isna().all().all():

                    ela_progress_indicator_data = replace_header(ela_progress_indicator_data)

                    # drops second row by index (Grade 9-12) if all value columns are NaN
                    if ela_progress_indicator_data.loc[[59]].isna().sum().sum() >=3:
                        ela_progress_indicator_data = ela_progress_indicator_data.iloc[:1]

                    ela_progress_indicator = create_academic_info_table(ela_progress_indicator_data,'Progress in Achieving English Language Proficiency Indicator','growth')
                else:
                    ela_progress_indicator = hidden_table()

                ## chronic absenteeism indicators ##
                absenteeism_indicator_data = growth_data.iloc[60:64].copy()

                if not absenteeism_indicator_data.iloc[1:,1:].isna().all().all():

                    absenteeism_indicator_data = replace_header(absenteeism_indicator_data)

                    if absenteeism_indicator_data.loc[[62]].isna().sum().sum() >=3:
                        absenteeism_indicator_data = absenteeism_indicator_data.iloc[:1]

                    absenteeism_indicator = create_academic_info_table(absenteeism_indicator_data,'Addressing Chronic Absenteeism Indicator','growth')
                else:
                    absenteeism_indicator = hidden_table()

            else:
                
                # If no growth file exists, null out all tables and styles and set containers to display:none
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

        else:
        # If selected year is anything other than 2022, hide all tables
            
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

    # Add notes string based on school type
    if radio_value == 'proficiency':
        if selected_school_type == 'AHS':
            notes_string = 'Adult High Schools enroll students who are over the age of 18, under credited, \
                dropped out of high school for a variety of reasons, and are typically out of cohort from \
                their original graduation year. Because graduation rate is calculated at the end of the school \
                year regardless of the length of time a student is enrolled at a school, it is not comparable to \
                the graduation rate of a traditional high school.'
            
        elif (selected_school_type == 'K8' or selected_school_type == 'K12' or selected_school_type == 'HS'):
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
        k8_overall_indicators,
        hs_overall_indicators,
        combined_indicators,
        enrollment_indicators,
        subgroup_grades,
        k8_academic_achievement,
        hs_academic_achievement,
        k8_academic_progress,
        hs_academic_progress,
        closing_achievement_gap,
        graduation_rate_indicator,
        strength_of_diploma_indicator,
        ela_progress_indicator,
        absenteeism_indicator,
        main_growth_container,
        empty_growth_container,
        no_growth_data_to_display,
        notes_string
)

# TODO: Consider consolidation of Growth sub tables into tooltips

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
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id='k8-overall-indicators'),
                                ],
                                className='pretty_container five columns',
                            ),
                        ],
                        className='bare_container twelve columns',
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id='hs-overall-indicators'),
                                ],
                                className='pretty_container five columns',
                            ),
                        ],
                        className='bare_container twelve columns',
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id='combined-indicators'),
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
                                    html.Div(id='enrollment-indicators'),
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
                                    html.Div(id='subgroup-grades'),
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
                                    html.Div(id='k8-academic-achievement'),
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
                                    html.Div(id='hs-academic-achievement'),
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
                                    html.Div(id='k8-academic-progress'),
                                ],
                                className='pretty_container five columns',
                            ),
                        ],
                        className='bare_container twelve columns',
                    ),
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
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id='graduation-rate-indicator'),
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
                                    html.Div(id='strength-of-diploma-indicator'),
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
                                    html.Div(id='ela-progress-indicator'),
                                ],
                                className='pretty_container five columns',
                            ),
                        ],
                        className='bare_container twelve columns',
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id='absenteeism-indicator'),
                                ],
                                className='pretty_container five columns',
                            ),
                        ],
                        className='bare_container twelve columns',
                    ),
                ],
                id = 'academic-growth-main-container',
            ),
            html.Div(
                [
                    html.Div(id='academic-growth-no-data'),
                ],
                id = 'academic-growth-empty-container',
            ),
        ],
        id='mainContainer',
    )