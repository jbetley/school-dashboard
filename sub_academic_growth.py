#########################################
# ICSB Dashboard - Academic Information #
#########################################
# author:   jbetley
# version:  1.07
# date:     07/10/23

import dash
from dash import dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import re
import os

# import local functions
from .table_helpers import no_data_page, no_data_table, hidden_table, set_table_layout, create_growth_table
from .chart_helpers import make_growth_chart
from .calculations import round_percentages
from .subnav import subnav_academic
from .load_data import ethnicity, subgroup, subject, grades_all, grades_ordinal, get_excluded_years, \
    process_growth_data
from .load_db import get_k8_school_academic_data, get_high_school_academic_data, get_growth_data, get_school_index

dash.register_page(__name__, top_nav=True, path="/academic_information", order=4)

@callback(
    Output("tst-fig", "children"),
    Output("tst-fig2", "children"),   
    Output("display-k8-metrics", "style"),
    Output("academic-metrics-main-container", "style"),
    Output("academic-metrics-empty-container", "style"),
    Output("academic-metrics-no-data", "children"),
    Output("table-grades-growth-ela-container", "children"),
    Output("table-grades-growth-math-container", "children"),
    Output("table-ethnicity-growth-ela-container", "children"),
    Output("table-ethnicity-growth-math-container", "children"),
    Output("table-subgroup-growth-ela-container", "children"),
    Output("table-subgroup-growth-math-container", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input(component_id="radio-button-academic-info", component_property="value")
)
def update_academic_information_page(school: str, year: str, radio_value:str):
    if not school:
        raise PreventUpdate

    # show 2019 instead of 2020 as 2020 has no academic data
    string_year = year
    selected_year_string = "2019" if string_year == "2020" else string_year
    selected_year_numeric = int(selected_year_string)

    excluded_years = get_excluded_years(selected_year_string)

    # default styles
    main_container = {"display": "block"}
    k8_table_container = {"display": "block"}
    # hs_table_container = {"display": "block"}
    empty_container = {"display": "none"}
    no_data_to_display = no_data_page("Academic Proficiency")
    
    main_growth_container = {"display": "block"}
    empty_growth_container = {"display": "none"}
    no_growth_data_to_display = no_data_page("Federal Growth Calculations")

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]
    selected_school_id = int(selected_school["School ID"].values[0])

    ## Proficiency Tables ##
    if radio_value == "proficiency":
        pass
        # Shift to Academic Info Page

    else:

        if (selected_school_type == "K8" or selected_school_type == "K12" or (selected_school_id == 5874 and selected_year_numeric > 2021)):

## TODO: Move Growth Metric tab from Academic Info page here (or to its own page)
### TODO - Add Growth Data both to Academic Information and Metrics ###

            # Growth Data

            # NOTE: "162-Days" means a student was enrolled at the school where they were assigned for at least
            # 162 days. "Majority Enrolled" is misleading. It actually means "Greatest Number of Days." So the actual
            # number of days could easily be less than 82 if, for example, a student transferred a few times, or
            # was out of the system for most of the year. "Tested School" is where the student actually took the
            # test. IDOE uses "Majority Enrolled" for their calculations

            # Percentage of students achieving “typical” or “high” growth on the state assessment in ELA/Math
            # Median SGP of students achieving 'adequate and sufficient growth' on the state assessment in ELA/Math


                # ILEARNGrowthLevel / TestYear / GradeLevel / Subject
                # group by Year, Subject and Grade Level?
                # Also: Ethnicity, Socio Economic Status Category, English Learner Status Category, Special Ed Status Category
                # Homeless Status Category, High Ability Status Category    

            # dataset is all students who are coded as 'Majority Enrolled' at the school
            growth_data = get_growth_data(school)

            if len(growth_data.index) > 0:
                
                # NOTE: This calculates the student difference
                # find the difference between the count of Majority Enrolled and 162-Day students by Year
                # counts_growth = growth_data.groupby('Test Year')['Test Year'].count().reset_index(name = "Count (Majority Enrolled)")
                # counts_growth_162 = growth_data_162.groupby('Test Year')['Test Year'].count().reset_index(name = "Count (162 Days)")

                # counts_growth['School Name'] = selected_school["School Name"].values[0]
                # counts_growth['Count (162 Days)'] = counts_growth_162['Count (162 Days)']
                # counts_growth['Difference'] = counts_growth['Count (Majority Enrolled)'] - counts_growth['Count (162 Days)']

                # print('Count Difference')
                # print(counts_growth)

                # diff_threshold = abs(len(growth_data.index) - len(growth_data_162.index))

                # print(f'Percentage difference: ' + str(diff_threshold / len(growth_data.index)))

                # Percentage of students achieving 'Adequate Growth'
                fig_data_grades_growth, table_data_grades_growth = process_growth_data(growth_data,'Grade Level','growth')
                fig_data_ethnicity_growth, table_data_ethnicity_growth = process_growth_data(growth_data,'Ethnicity','growth')
                fig_data_ses_growth, table_data_ses_growth = process_growth_data(growth_data,'Socioeconomic Status','growth')
                fig_data_el_growth, table_data_el_growth = process_growth_data(growth_data,'English Learner Status','growth')
                fig_data_sped_growth, table_data_sped_growth = process_growth_data(growth_data,'Special Education Status','growth')

                # Median SGP for 'all' students
                fig_data_grades_sgp, table_data_grades_sgp = process_growth_data(growth_data,'Grade Level','sgp')
                fig_data_ethnicity_sgp, table_data_ethnicity_sgp = process_growth_data(growth_data,'Ethnicity','sgp')
                fig_data_ses_sgp, table_data_ses_sgp = process_growth_data(growth_data,'Socioeconomic Status','sgp')
                fig_data_el_sgp, table_data_el_sgp = process_growth_data(growth_data,'English Learner Status','sgp')
                fig_data_sped_sgp, table_data_sped_sgp = process_growth_data(growth_data,'Special Education Status','sgp')

                # combine subgroups
                table_data_subgroup_growth = pd.concat([table_data_ses_growth, table_data_el_growth, table_data_sped_growth])
                fig_data_subgroup_growth = pd.concat([fig_data_ses_growth, fig_data_el_growth, fig_data_sped_growth], axis=1)

                table_data_subgroup_sgp = pd.concat([table_data_ses_sgp, table_data_el_sgp, table_data_sped_sgp])
                fig_data_subgroup_sgp = pd.concat([fig_data_ses_sgp, fig_data_el_sgp, fig_data_sped_sgp], axis=1)
                
                # Tables

                # by grade
                table_data_grades_growth_ela = table_data_grades_growth[(table_data_grades_growth["Category"].str.contains("ELA"))]
                table_data_grades_growth_math= table_data_grades_growth[(table_data_grades_growth["Category"].str.contains("Math"))]                    
                table_data_grades_sgp_ela = table_data_grades_sgp[(table_data_grades_sgp["Category"].str.contains("ELA"))]                    
                table_data_grades_sgp_math = table_data_grades_sgp[(table_data_grades_sgp["Category"].str.contains("Math"))]

                table_grades_growth_ela = create_growth_table('Percentage of Students with Adequate Growth - by Grade (ELA)', table_data_grades_growth_ela,'growth')
                table_grades_sgp_ela = create_growth_table('Median SGP - All Students By Grade (ELA)', table_data_grades_sgp_ela,'sgp')

                table_grades_growth_ela_container = set_table_layout(table_grades_growth_ela, table_grades_sgp_ela, table_data_grades_growth.columns)

                table_grades_growth_math = create_growth_table('Percentage of Students with Adequate Growth - by Grade (Math)', table_data_grades_growth_math,'growth')
                table_grades_sgp_math = create_growth_table('Median SGP - All Students By Grade (Math)', table_data_grades_sgp_math,'sgp')

                table_grades_growth_math_container = set_table_layout(table_grades_growth_math, table_grades_sgp_math, table_data_grades_growth.columns)

                # by ethnicity
                table_data_ethnicity_growth_ela = table_data_ethnicity_growth[(table_data_ethnicity_growth["Category"].str.contains("ELA"))]
                table_data_ethnicity_growth_math= table_data_ethnicity_growth[(table_data_ethnicity_growth["Category"].str.contains("Math"))]                    
                table_data_ethnicity_sgp_ela = table_data_ethnicity_sgp[(table_data_ethnicity_sgp["Category"].str.contains("ELA"))]                    
                table_data_ethnicity_sgp_math = table_data_ethnicity_sgp[(table_data_ethnicity_sgp["Category"].str.contains("Math"))]

                table_ethnicity_growth_ela = create_growth_table('Percentage of Students with Adequate Growth - by Ethnicity (ELA)', table_data_ethnicity_growth_ela,'growth')
                table_ethnicity_sgp_ela = create_growth_table('Median SGP - All Students By Ethnicity (ELA)', table_data_ethnicity_sgp_ela,'sgp')

                table_ethnicity_growth_ela_container = set_table_layout(table_ethnicity_growth_ela, table_ethnicity_sgp_ela, table_data_ethnicity_growth.columns)

                table_ethnicity_growth_math = create_growth_table('Percentage of Students with Adequate Growth - by Ethnicity (Math)', table_data_ethnicity_growth_math,'growth')
                table_ethnicity_sgp_math = create_growth_table('Median SGP - All Students By Ethnicity (Math)', table_data_ethnicity_sgp_math,'sgp')

                table_ethnicity_growth_math_container = set_table_layout(table_ethnicity_growth_math, table_ethnicity_sgp_math, table_data_ethnicity_growth.columns)

                # by subgroup
                table_data_subgroup_growth_ela = table_data_subgroup_growth[(table_data_subgroup_growth["Category"].str.contains("ELA"))]
                table_data_subgroup_growth_math= table_data_subgroup_growth[(table_data_subgroup_growth["Category"].str.contains("Math"))]                    
                table_data_subgroup_sgp_ela = table_data_subgroup_sgp[(table_data_subgroup_sgp["Category"].str.contains("ELA"))]                    
                table_data_subgroup_sgp_math = table_data_subgroup_sgp[(table_data_subgroup_sgp["Category"].str.contains("Math"))]

                table_subgroup_growth_ela = create_growth_table('Percentage of Students with Adequate Growth - by Ethnicity (ELA)', table_data_subgroup_growth_ela,'growth')
                table_subgroup_sgp_ela = create_growth_table('Median SGP - All Students By Ethnicity (ELA)', table_data_subgroup_sgp_ela,'sgp')

                table_subgroup_growth_ela_container = set_table_layout(table_subgroup_growth_ela, table_subgroup_sgp_ela, table_data_subgroup_growth.columns)

                table_subgroup_growth_math = create_growth_table('Percentage of Students with Adequate Growth - by Ethnicity (Math)', table_data_subgroup_growth_math,'growth')
                table_subgroup_sgp_math = create_growth_table('Median SGP - All Students By Ethnicity (Math)', table_data_subgroup_sgp_math,'sgp')

                table_subgroup_growth_math_container = set_table_layout(table_subgroup_growth_math, table_subgroup_sgp_math, table_data_subgroup_growth.columns)

                # table_grades_growth_ela_container = {},
                # table_grades_growth_math_container = {},
                # table_ethnicity_growth_ela_container = {},
                # table_ethnicity_growth_math_container = {},
                # table_subgroup_growth_ela_container = {},
                # table_subgroup_growth_math_container = {}

            ## Figures

                # Growth by Grade (Both ME and 162)
                growth_data_162_grades_ela = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains('162')) & (fig_data_grades_growth.columns.str.contains('ELA'))]
                growth_data_162_grades_math = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains('162')) & (fig_data_grades_growth.columns.str.contains('Math'))]
                growth_data_me_grades_ela = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains('Majority Enrolled')) & (fig_data_grades_growth.columns.str.contains('ELA'))]
                growth_data_me_grades_math = fig_data_grades_growth.loc[:,(fig_data_grades_growth.columns.str.contains('Majority Enrolled')) & (fig_data_grades_growth.columns.str.contains('Math'))]
                
                growth_data_162_grades_ela.columns = growth_data_162_grades_ela.columns.str.split('_').str[1]
                growth_data_162_grades_math.columns = growth_data_162_grades_math.columns.str.split('_').str[1]
                growth_data_me_grades_ela.columns = growth_data_me_grades_ela.columns.str.split('_').str[1]
                growth_data_me_grades_math.columns = growth_data_me_grades_math.columns.str.split('_').str[1]

                # Growth by Ethnicity (Both ME and 162)
                growth_data_162_ethnicity_ela = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains('162')) & (fig_data_ethnicity_growth.columns.str.contains('ELA'))]
                growth_data_162_ethnicity_math = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains('162')) & (fig_data_ethnicity_growth.columns.str.contains('Math'))]
                growth_data_me_ethnicity_ela = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains('Majority Enrolled')) & (fig_data_ethnicity_growth.columns.str.contains('ELA'))]
                growth_data_me_ethnicity_math = fig_data_ethnicity_growth.loc[:,(fig_data_ethnicity_growth.columns.str.contains('Majority Enrolled')) & (fig_data_ethnicity_growth.columns.str.contains('Math'))]
                
                growth_data_162_ethnicity_ela.columns = growth_data_162_ethnicity_ela.columns.str.split('_').str[1]
                growth_data_162_ethnicity_math.columns = growth_data_162_ethnicity_math.columns.str.split('_').str[1]
                growth_data_me_ethnicity_ela.columns = growth_data_me_ethnicity_ela.columns.str.split('_').str[1]
                growth_data_me_ethnicity_math.columns = growth_data_me_ethnicity_math.columns.str.split('_').str[1]
        
                # Growth by Subgroup (Both ME and 162)                     
                growth_data_162_subgroup_ela = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains('162')) & (fig_data_subgroup_growth.columns.str.contains('ELA'))]
                growth_data_162_subgroup_math = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains('162')) & (fig_data_subgroup_growth.columns.str.contains('Math'))]
                growth_data_me_subgroup_ela = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains('Majority Enrolled')) & (fig_data_subgroup_growth.columns.str.contains('ELA'))]
                growth_data_me_subgroup_math = fig_data_subgroup_growth.loc[:,(fig_data_subgroup_growth.columns.str.contains('Majority Enrolled')) & (fig_data_subgroup_growth.columns.str.contains('Math'))]
                
                growth_data_162_subgroup_ela.columns = growth_data_162_subgroup_ela.columns.str.split('_').str[1]
                growth_data_162_subgroup_math.columns = growth_data_162_subgroup_math.columns.str.split('_').str[1]
                growth_data_me_subgroup_ela.columns = growth_data_me_subgroup_ela.columns.str.split('_').str[1]
                growth_data_me_subgroup_math.columns = growth_data_me_subgroup_math.columns.str.split('_').str[1]

                # SGP by Grade (Both ME and 162)
                sgp_data_162_grades_ela = fig_data_grades_sgp.loc[:,(fig_data_grades_sgp.columns.str.contains('162')) & (fig_data_grades_sgp.columns.str.contains('ELA'))]
                sgp_data_162_grades_math = fig_data_grades_sgp.loc[:,(fig_data_grades_sgp.columns.str.contains('162')) & (fig_data_grades_sgp.columns.str.contains('Math'))]
                sgp_data_me_grades_ela = fig_data_grades_sgp.loc[:,(fig_data_grades_sgp.columns.str.contains('Majority Enrolled')) & (fig_data_grades_sgp.columns.str.contains('ELA'))]
                sgp_data_me_grades_math = fig_data_grades_sgp.loc[:,(fig_data_grades_sgp.columns.str.contains('Majority Enrolled')) & (fig_data_grades_sgp.columns.str.contains('Math'))]
                
                sgp_data_162_grades_ela.columns = sgp_data_162_grades_ela.columns.str.split('_').str[1]
                sgp_data_162_grades_math.columns = sgp_data_162_grades_math.columns.str.split('_').str[1]
                sgp_data_me_grades_ela.columns = sgp_data_me_grades_ela.columns.str.split('_').str[1]
                sgp_data_me_grades_math.columns = sgp_data_me_grades_math.columns.str.split('_').str[1]

                # SGP by Ethnicity (Both ME and 162)
                sgp_data_162_ethnicity_ela = fig_data_ethnicity_sgp.loc[:,(fig_data_ethnicity_sgp.columns.str.contains('162')) & (fig_data_ethnicity_sgp.columns.str.contains('ELA'))]
                sgp_data_162_ethnicity_math = fig_data_ethnicity_sgp.loc[:,(fig_data_ethnicity_sgp.columns.str.contains('162')) & (fig_data_ethnicity_sgp.columns.str.contains('Math'))]
                sgp_data_me_ethnicity_ela = fig_data_ethnicity_sgp.loc[:,(fig_data_ethnicity_sgp.columns.str.contains('Majority Enrolled')) & (fig_data_ethnicity_sgp.columns.str.contains('ELA'))]
                sgp_data_me_ethnicity_math = fig_data_ethnicity_sgp.loc[:,(fig_data_ethnicity_sgp.columns.str.contains('Majority Enrolled')) & (fig_data_ethnicity_sgp.columns.str.contains('Math'))]
                
                sgp_data_162_ethnicity_ela.columns = sgp_data_162_ethnicity_ela.columns.str.split('_').str[1]
                sgp_data_162_ethnicity_math.columns = sgp_data_162_ethnicity_math.columns.str.split('_').str[1]
                sgp_data_me_ethnicity_ela.columns = sgp_data_me_ethnicity_ela.columns.str.split('_').str[1]
                sgp_data_me_ethnicity_math.columns = sgp_data_me_ethnicity_math.columns.str.split('_').str[1]

                # SGP by Subgroup (Both ME and 162)                     
                sgp_data_162_subgroup_ela = fig_data_subgroup_sgp.loc[:,(fig_data_subgroup_sgp.columns.str.contains('162')) & (fig_data_subgroup_sgp.columns.str.contains('ELA'))]
                sgp_data_162_subgroup_math = fig_data_subgroup_sgp.loc[:,(fig_data_subgroup_sgp.columns.str.contains('162')) & (fig_data_subgroup_sgp.columns.str.contains('Math'))]
                sgp_data_me_subgroup_ela = fig_data_subgroup_sgp.loc[:,(fig_data_subgroup_sgp.columns.str.contains('Majority Enrolled')) & (fig_data_subgroup_sgp.columns.str.contains('ELA'))]
                sgp_data_me_subgroup_math = fig_data_subgroup_sgp.loc[:,(fig_data_subgroup_sgp.columns.str.contains('Majority Enrolled')) & (fig_data_subgroup_sgp.columns.str.contains('Math'))]
                
                sgp_data_162_subgroup_ela.columns = sgp_data_162_subgroup_ela.columns.str.split('_').str[1]
                sgp_data_162_subgroup_math.columns = sgp_data_162_subgroup_math.columns.str.split('_').str[1]
                sgp_data_me_subgroup_ela.columns = sgp_data_me_subgroup_ela.columns.str.split('_').str[1]
                sgp_data_me_subgroup_math.columns = sgp_data_me_subgroup_math.columns.str.split('_').str[1]
                
                # TODO: Samples of each - 4 for each 'category' so 12 charts (grade, ethnicity, subgroup)
                lbl ="Percentage of Students Achieving Adequate Growth in ELA by Grade"
                tst_fig = make_growth_chart(growth_data_me_grades_ela, growth_data_162_grades_ela, lbl)

                lbl2 ="Median SGP in ELA by Grade"
                tst_fig2 = make_growth_chart(sgp_data_me_grades_ela, sgp_data_162_grades_ela, lbl2)

            # # if K8, hide HS tables (except for CHS prior to 2021 when it was a K12)
            # if selected_school_type == "K8" and not (selected_school_id == 5874 and selected_year_numeric < 2021):

            # Growth Data

            # NOTE: "162-Days" means a student was enrolled at the school where they were assigned for at least
            # 162 days. "Majority Enrolled" is misleading. It actually means "Greatest Number of Days." So the actual
            # number of days could easily be less than 82 if, for example, a student transferred a few times, or
            # was out of the system for most of the year. "Tested School" is where the student actually took the
            # test. IDOE uses "Majority Enrolled" for their calculations

            # Percentage of students achieving “typical” or “high” growth on the state assessment in ELA/Math
            # Median SGP of students achieving 'adequate and sufficient growth' on the state assessment in ELA/Math


                # ILEARNGrowthLevel / TestYear / GradeLevel / Subject
                # group by Year, Subject and Grade Level?
                # Also: Ethnicity, Socio Economic Status Category, English Learner Status Category, Special Ed Status Category
                # Homeless Status Category, High Ability Status Category    

            # dataset is all students who are coded as 'Majority Enrolled' at the school
            growth_data = get_growth_data(school)

            if len(growth_data.index) > 0:
                
                # TODO: Do we want to add the # of students difference?
                # find the difference between the count of Majority Enrolled and 162-Day students by Year
                # counts_growth = growth_data.groupby('Test Year')['Test Year'].count().reset_index(name = "Count (Majority Enrolled)")
                # counts_growth_162 = growth_data_162.groupby('Test Year')['Test Year'].count().reset_index(name = "Count (162 Days)")

                # counts_growth['School Name'] = selected_school["School Name"].values[0]
                # counts_growth['Count (162 Days)'] = counts_growth_162['Count (162 Days)']
                # counts_growth['Difference'] = counts_growth['Count (Majority Enrolled)'] - counts_growth['Count (162 Days)']

                # print('Count Difference')
                # print(counts_growth)

                # diff_threshold = abs(len(growth_data.index) - len(growth_data_162.index))

                # print(f'Percentage difference: ' + str(diff_threshold / len(growth_data.index)))

                def process_growth_data(df: pd.DataFrame, category: str, calculation: str) -> pd.DataFrame:

                    # step 1: find the percentage of students with Adequate growth using
                    # 'Majority Enrolled' students (all available data) and the percentage
                    # of students with Adequate growth using the set of students enrolled for
                    # '162 Days' (a subset of available data)

                    data_162 = df[df['Day 162'] == 'TRUE']
                    data = df.copy()

                    if calculation == 'growth':
                        data = df.groupby(['Test Year', category, 'Subject'])['ILEARNGrowth Level'].value_counts(normalize=True).reset_index(name='Majority Enrolled')
                        data_162 = data_162.groupby(['Test Year',category, 'Subject'])['ILEARNGrowth Level'].value_counts(normalize=True).reset_index(name='162 Days')
                    
                    elif calculation == 'sgp':
                        data = df.groupby(['Test Year', category, 'Subject'])['ILEARNGrowth Percentile'].median().reset_index(name='Majority Enrolled')
                        data_162 = data_162.groupby(['Test Year', category, 'Subject'])['ILEARNGrowth Percentile'].median().reset_index(name='162 Days')
                    
                    # step 3: add ME column to df and calculate difference
                    data['162 Days'] = data_162['162 Days']
                    data['Difference'] = data['162 Days'] - data['Majority Enrolled']

                    # step 4: get into proper format for display as multi-header DataTable
                    
                    # create final category
                    data['Category'] = data[category] + "|" + data['Subject']
                    
                    # drop unused rows and columns
                    if calculation == 'growth':
                        data = data[data["ILEARNGrowth Level"].str.contains("Not Adequate") == False]
                        data = data.drop([category, 'Subject','ILEARNGrowth Level'], axis=1)                        
                    elif calculation == 'sgp':
                        data = data.drop([category, 'Subject'], axis=1)
                    
                    # create specific column order. sort_index does not work
                    cols = []
                    yrs = list(set(data['Test Year'].to_list()))
                    yrs.sort(reverse=True)
                    for y in yrs:
                        cols.append(str(y) + '162 Days')
                        cols.append(str(y) + 'Majority Enrolled')
                        cols.append(str(y) + 'Difference')

                    # pivot df from wide to long' add years to each column name; move year to
                    # front of column name; sort and reset_index
                    data = data.pivot(index=['Category'], columns='Test Year')
                    data.columns = data.columns.map(lambda x: ''.join(map(str, x)))
                    data.columns = data.columns.map(lambda x: x[-4:] + x[:-4])
                    data = data[cols]
                    data = data.reset_index()

                    return data

                # Percentage of students achieving 'Adequate Growth'
                grades_growth = process_growth_data(growth_data,'Grade Level','growth')
                ethnicity_growth = process_growth_data(growth_data,'Ethnicity','growth')
                ses_growth = process_growth_data(growth_data,'Socioeconomic Status','growth')
                el_growth = process_growth_data(growth_data,'English Learner Status','growth')
                sped_growth = process_growth_data(growth_data,'Special Education Status','growth')

                # Median SGP Data
                grades_sgp = process_growth_data(growth_data,'Grade Level','sgp')
                ethnicity_sgp = process_growth_data(growth_data,'Ethnicity','sgp')
                ses_sgp = process_growth_data(growth_data,'Socioeconomic Status','sgp')
                el_sgp = process_growth_data(growth_data,'English Learner Status','sgp')
                sped_sgp = process_growth_data(growth_data,'Special Education Status','sgp')

                # Tables

                # by grade
                grades_growth_ela = grades_growth[(grades_growth["Category"].str.contains("ELA"))]
                grades_growth_math= grades_growth[(grades_growth["Category"].str.contains("Math"))]                    
                
                table_grades_growth_ela = create_growth_table('Percentage of Students with Adequate Growth - by Grade (ELA)', grades_growth_ela,'growth')
                
                # by ethnicity

                # by socioeconomic status

                # by english learner status

                # by special education status
                # Median SGP for 'all' students
                
                grades_sgp_ela = grades_sgp[(grades_sgp["Category"].str.contains("ELA"))]
                table_grades_sgp_ela = create_growth_table('Median SGP - All Students By Grade (ELA)', grades_sgp_ela,'sgp')

            # table_grades_growth_math = create_growth_table('Percentage of Students with Adequate Growth - by Grade (Math)', grades_growth_math)

                table_growth_container = set_table_layout(table_grades_growth_ela, table_grades_sgp_ela, grades_growth.columns)
                



            # TODO: ## Federal Growth Data ##

            # # NOTE: Currently have a single year of growth data (2022). Therefore unless
            # # the selected year is 2022, we show an empty table.
            # if selected_year_string == "2022":
            #     # NOTE: This data sucks ass. It originates from an excel file that has a mishmash of small
            #     # tables with different headers and varying columns and rows. Data is different for different
            #     # grade configurations, and, to add insult to injury, sometimes tables are present with null
            #     # values and other times the tables are just missing. So we pull the data out by specific rows
            #     # in order to avoid column index errors when pandas tries to read it in all at once.
                
            #     # NOTE: the original excel files (format: "2022ReportCardSummary86855593ALL") are in even
            #     # worse shape with tables arranged horizontally and a liberal use of Merge Columns. There 
            #     # is a utility file ("_growthFileScrape.py") that converts these original files to a flattened
            #     # csv with all tables arranged vertically and missing tables represented by empty rows.
            #     # Unfortunately,it still has variable and unrelated columns, so we need to pull each individual
            #     # table out by row using iloc (e.g., growth_data.iloc[0:10]). Eventually we need to put
            #     # all this crap into a database.

            #     growth_file = "data/growth_data" + school + ".csv"
                
            #     # Adult high schools and new charter schools do not have growth data.
            #     # First check if there is a growth data file. There will either be a
            #     # file with data or there will not be a file. There will never be an
            #     # empty growth data file.
            #     if os.path.isfile(growth_file):

            #         # get all tables. Because there are variable columns, we set a fixed
            #         # range equal to the maximum number of columns
            #         growth_data = pd.read_csv(growth_file,header = None,names=range(8))

            #         # Global cleaning of growth data
            #         growth_data = growth_data.replace({
            #             "English/Lang. Arts": "ELA",
            #             "Mathematics": "Math",
            #             "Sugroup": "Subgroup",
            #             "Hispanic Ethnicity": "Hispanic",
            #             "Elementary/Middle School Overall Weight and Points:": "Overall",
            #             "High School Overall Weight and Points:": "Overall"
            #             })

            #         # remove excess spaces between "(" and ")"
            #         growth_data = growth_data.replace(r"\s+(?=[^(\)]*\))","", regex=True)

            #         # remove extra space between number and "%"
            #         growth_data = growth_data.replace(r"(?<=\d) +(?=%)","", regex=True)                

            #         # Get individual tables one by one because tables have variable
            #         # number of columns

            #         def replace_header(data: pd.DataFrame) -> pd.DataFrame:
            #             """ Takes a Pandas Dataframe, replaces header with first row, and
            #                 drops all nan columns
            #             Args:
            #                 data (pd.Dataframe): Pandas dataframe

            #             Returns:
            #                 pd.Dataframe: returns the same dataframe first row headers and
            #                 no NaN columns
            #             """
            #             data.columns = data.iloc[0].tolist()
            #             data = data[1:]
            #             data = data.dropna(axis=1, how="all")

            #             return data
            
            #         ## k8 growth indicators ##
            #         k8_overall_indicators_data = growth_data.iloc[0:10].copy()

            #         if not k8_overall_indicators_data.isnull().all().all():
                        
            #             k8_overall_indicators_data = replace_header(k8_overall_indicators_data)

            #             # Drop rows where there are zero points and No Rating
            #             k8_overall_indicators_data = k8_overall_indicators_data.loc[~((k8_overall_indicators_data["Points"] == "0.00") & \
            #                 (k8_overall_indicators_data["Rating"] == "No Rating"))]
                        
            #             # replace metrics with svg circles
            #             k8_overall_indicators_data = get_svg_circle(k8_overall_indicators_data)
                    
            #             k8_overall_indicators = create_academic_info_table(k8_overall_indicators_data,"Elementary/Middle Growth Summary","growth")
            #         else:
            #             k8_overall_indicators = hidden_table()

            #         ## hs growth indicators ##
            #         hs_overall_indicators_data = growth_data.iloc[10:20].copy()

            #         if not hs_overall_indicators_data.isnull().all().all():

            #             hs_overall_indicators_data = replace_header(hs_overall_indicators_data)

            #             hs_overall_indicators_data = hs_overall_indicators_data.loc[~((hs_overall_indicators_data["Points"] == "0.00") & \
            #                 (hs_overall_indicators_data["Rating"] == "No Rating"))]
                        
            #             hs_overall_indicators_data = get_svg_circle(hs_overall_indicators_data)

            #             hs_overall_indicators = create_academic_info_table(hs_overall_indicators_data,"High School Growth Summary","growth")
            #         else:
            #             hs_overall_indicators = hidden_table()

            #         ## combined growth indicators ##
            #         combined_indicators_data = growth_data.iloc[20:24].copy()

            #         if not combined_indicators_data.isnull().all().all():

            #             # drop empty columns and add headers
            #             combined_indicators_data = combined_indicators_data.dropna(axis=1, how="all")
            #             combined_indicators_data.columns = ["Category","Weighted Points"]
                        
            #             combined_indicators_data = get_svg_circle(combined_indicators_data)

            #             combined_indicators = create_academic_info_table(combined_indicators_data,"Combined Growth Summary","growth")
            #         else:
            #             combined_indicators = hidden_table()

            #         ## enrollment indicators ##
            #         enrollment_indicators_data = growth_data.iloc[24:27].copy()

            #         if not enrollment_indicators_data.isnull().all().all():
                        
            #             enrollment_indicators_data = replace_header(enrollment_indicators_data)

            #             # some tables, including enrollment_indicators_data, have a Grades 3-8 row
            #             # and a Grades 9-12 row regardless of whether the school has data for both.
            #             # So either check second row for "0" (as in this case) or NaN and remove if true.
            #             if enrollment_indicators_data.iloc[1,1] == "0":
            #                 enrollment_indicators_data = enrollment_indicators_data.iloc[:1]        

            #             # rename first column
            #             enrollment_indicators_data = enrollment_indicators_data.rename(columns={enrollment_indicators_data.columns[0]: "Grade Span"})
                        
            #             enrollment_indicators = create_academic_info_table(enrollment_indicators_data,"Enrollment Indicators","growth")
            #         else:
            #             enrollment_indicators = hidden_table()

            #         ## subgroup grades indicators ##
            #         subgroup_grades_data = growth_data.iloc[27:33].copy()

            #         if not subgroup_grades_data.isnull().all().all():
                        
            #             subgroup_grades_data = replace_header(subgroup_grades_data)

            #             # subgroup_grades_data is two tables side by side with the same column headers.
            #             # We use groupby() to unpivot & combine the duplicate columns, and then reorder
            #             # the columns
            #             subgroup_grades_data = subgroup_grades_data.groupby(subgroup_grades_data.columns.values, axis=1).agg(lambda x: x.values.tolist()).sum().apply(pd.Series).T
            #             subgroup_grades_data = subgroup_grades_data[["Subgroup", "Points", "Rating"]]

            #             subgroup_grades_data = subgroup_grades_data.loc[~((subgroup_grades_data["Points"] == "0") & \
            #                 (subgroup_grades_data["Rating"] == "No Rating"))]

            #             subgroup_grades_data = get_svg_circle(subgroup_grades_data)
                        
            #             subgroup_grades = create_academic_info_table(subgroup_grades_data,"Subgroup Grades","growth")
            #         else:
            #             subgroup_grades = hidden_table()

            #         ## k8 academic achievement indicators ##
            #         k8_academic_achievement_data = growth_data.iloc[34:37].copy()

            #         if not k8_academic_achievement_data.iloc[1:,1:].isnull().all().all():

            #             k8_academic_achievement_data = replace_header(k8_academic_achievement_data)

            #             k8_academic_achievement = create_academic_info_table(k8_academic_achievement_data,"Elementary/Middle Academic Achievement","growth")
            #         else:
            #             k8_academic_achievement = hidden_table()

            #         ## hs academic achievement indicators ##
            #         hs_academic_achievement_data = growth_data.iloc[38:41].copy()

            #         # skip 1st column and 1st row in determining whether all cols are null
            #         if not hs_academic_achievement_data.iloc[1:,1:].isna().all().all():

            #             hs_academic_achievement_data = replace_header(hs_academic_achievement_data)

            #             hs_academic_achievement = create_academic_info_table(hs_academic_achievement_data,"High School Academic Achievement","growth")
                
            #         else:
            #             hs_academic_achievement = hidden_table()

            #         ## k8 academic progress indicators ##
            #         k8_academic_progress_data = growth_data.iloc[42:45].copy()

            #         if not k8_academic_progress_data.iloc[1:,1:].isna().all().all():

            #             k8_academic_progress_data = replace_header(k8_academic_progress_data)

            #             k8_academic_progress = create_academic_info_table(k8_academic_progress_data,"Elementary/Middle Progress Indicators","growth")
            #         else:
            #             k8_academic_progress = hidden_table()

            #         ## hs academic progress indicators ##
            #         hs_academic_progress_data = growth_data.iloc[46:49].copy()

            #         if not hs_academic_progress_data.iloc[1:,1:].isna().all().all():

            #             hs_academic_progress_data = replace_header(hs_academic_progress_data)

            #             hs_academic_progress = create_academic_info_table(hs_academic_progress_data,"High School Progress Indicators","growth")
            #         else:
            #             hs_academic_progress = hidden_table()

            #         ## closing achievement gap indicators ##
            #         closing_achievement_gap_data = growth_data.iloc[50:53].copy()

            #         if not closing_achievement_gap_data.iloc[1:,1:].isna().all().all():

            #             closing_achievement_gap_data = replace_header(closing_achievement_gap_data)

            #             closing_achievement_gap = create_academic_info_table(closing_achievement_gap_data,"Closing the Achievement Gap","growth")
            
            #         else:
            #             closing_achievement_gap = hidden_table()

            #         ## graduation rate indicator ##
            #         graduation_rate_indicator_data = growth_data.iloc[53:55].copy()

            #         if not graduation_rate_indicator_data.isnull().all().all():

            #             graduation_rate_indicator_data = replace_header(graduation_rate_indicator_data)

            #             graduation_rate_indicator = create_academic_info_table(graduation_rate_indicator_data,"Graduation Rate Indicator","growth")
            #         else:
            #             graduation_rate_indicator = hidden_table()

            #         ## strength of diploma indicator ##
            #         strength_of_diploma_indicator_data = growth_data.iloc[55:57].copy()

            #         if not strength_of_diploma_indicator_data.isnull().all().all():

            #             strength_of_diploma_indicator_data = replace_header(strength_of_diploma_indicator_data)
                        
            #             strength_of_diploma_indicator = create_academic_info_table(strength_of_diploma_indicator_data,"Strength of Diploma Indicator","growth")
            #         else:
            #             strength_of_diploma_indicator = hidden_table()

            #         ## ela progress indicators ##
            #         ela_progress_indicator_data = growth_data.iloc[57:60].copy()

            #         if not ela_progress_indicator_data.iloc[1:,1:].isna().all().all():

            #             ela_progress_indicator_data = replace_header(ela_progress_indicator_data)

            #             # drops second row by index (Grade 9-12) if all value columns are NaN
            #             if ela_progress_indicator_data.loc[[59]].isna().sum().sum() >=3:
            #                 ela_progress_indicator_data = ela_progress_indicator_data.iloc[:1]

            #             ela_progress_indicator = create_academic_info_table(ela_progress_indicator_data,"Progress in Achieving English Language Proficiency Indicator","growth")
            #         else:
            #             ela_progress_indicator = hidden_table()

            #         ## chronic absenteeism indicators ##
            #         absenteeism_indicator_data = growth_data.iloc[60:64].copy()

            #         if not absenteeism_indicator_data.iloc[1:,1:].isna().all().all():

            #             absenteeism_indicator_data = replace_header(absenteeism_indicator_data)

            #             if absenteeism_indicator_data.loc[[62]].isna().sum().sum() >=3:
            #                 absenteeism_indicator_data = absenteeism_indicator_data.iloc[:1]

            #             absenteeism_indicator = create_academic_info_table(absenteeism_indicator_data,"Addressing Chronic Absenteeism Indicator","growth")
            #         else:
            #             absenteeism_indicator = hidden_table()

            else:
                
                table_growth_container = {}
                # TODO: Do we want to limit to median SGP for those students achieving 'Adequate Growth'?
                # # median SGP for students achieving 'Adequate Growth' grouped by Year, Grade, and Subject
                # adequate_growth_data = growth_data[growth_data['ILEARNGrowth Level'] == 'Adequate Growth']
                # median_sgp_adequate = adequate_growth_data.groupby(['Test Year','Grade Level', 'Subject'])['ILEARNGrowth Percentile'].median()
                # adequate_growth_data_162 = growth_data_162[growth_data_162['ILEARNGrowth Level'] == 'Adequate Growth']
                # median_sgp_adequate_162 = adequate_growth_data_162.groupby(['Test Year','Grade Level', 'Subject'])['ILEARNGrowth Percentile'].median()

        else:
            # No Data to Display
            table_growth_container = {}
 

    # Add notes string based on school type
    # if radio_value == "proficiency":
    #     if selected_school_type == "AHS":
    #         notes_string = "Adult High Schools enroll students who are over the age of 18, under credited, \
    #             dropped out of high school for a variety of reasons, and are typically out of cohort from \
    #             their original graduation year. Because graduation rate is calculated at the end of the school \
    #             year regardless of the length of time a student is enrolled at a school, it is not comparable to \
    #             the graduation rate of a traditional high school."
            
    #     elif (selected_school_type == "K8" or selected_school_type == "K12" or selected_school_type == "HS"):
    #         notes_string = "There are a number of factors that make it difficult to make valid and reliable \
    #             comparisons between test scores from 2019 to 2022. For example, ILEARN was administered for \
    #             the first time during the 2018-19 SY and represented an entirely new type and mode of \
    #             assessment (adaptive and online-only). No State assessment was administered  in 2020 because \
    #             of the Covid-19 pandemic. Finally, the 2019 data set includes only students  who attended the \
    #             testing school for 162 days, while the 2021 and 2022 data sets included all tested students. \
    #             Data Source: Indiana Department of Education Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)."
    #     else:
    #         notes_string = ""

    # if radio_value == "growth":
    #     notes_string = "Growth Data comes from IDOE\"s School Report Card Summaries of Federal Growth indicators. \
    #         While the data represented here is an accurate representation of the data present in the Summaries, \
    #         it has not been otherwise reconciled with the raw data used to produce the Summaries. It is presented \
    #         here for informational purposes only."

    return (
        table_grades_growth_ela_container, table_grades_growth_math_container, table_ethnicity_growth_ela_container, \
        table_ethnicity_growth_math_container, table_subgroup_growth_ela_container, table_subgroup_growth_math_container,\
        tst_fig, tst_fig2, 
        k8_table_container,
        main_container,
        empty_container,
        no_data_to_display,
        main_growth_container,
        empty_growth_container,
        no_growth_data_to_display,
        # notes_string
)

# TODO: Consider consolidation of Growth sub tables into tooltips

def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(subnav_academic(), className="tabs"),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                ],
                className="row",
            ),
            html.Div(
                [    
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label("Notes:", className="header_label"),
                                    html.P(""),
                                        html.P(id="notes-string",
                                            style={
                                                    "textAlign": "Left",
                                                    "color": "#6783a9",
                                                    "fontSize": 12,
                                                    "marginLeft": "10px",
                                                    "marginRight": "10px",
                                                    "marginTop": "10px",
                                            }
                                        ),
                                ],
                                className = "pretty_container seven columns"
                            ),
                        ],
                        className = "bare_container_center twelve columns"
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
                                    dbc.RadioItems(
                                        id="radio-button-academic-info",
                                        className="btn-group",
                                        inputClassName="btn-check",
                                        labelClassName="btn btn-outline-primary",
                                        labelCheckedClassName="active",
                                        options=[
                                            {"label": "Proficiency", "value": "proficiency"},
                                            {"label": "Growth", "value": "growth"},
                                        ],
                                        value="proficiency",
                                        persistence=True,
                                        persistence_type="local",
                                    ),
                                ],
                                className="radio-group",
                            ),
                        ],
                        className = "bare_container_center twelve columns",
                    ),
                ],
                className = "row",
            ),
            html.Div(
                [
                dcc.Loading(
                    id="loading",
                    type="circle",
                    fullscreen = True,
                    style={
                        "position": "absolute",
                        "align-self": "center",
                        "background-color": "#F2F2F2",
                        },
                    children=[
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-grade-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-grade-ela-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="k8-grade-math-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-ethnicity-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-ethnicity-ela-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="k8-ethnicity-math-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-subgroup-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-subgroup-ela-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="k8-subgroup-math-fig"),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-other-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                        ],
                        id="k8-table-container",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-grad-overview-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-grad-ethnicity-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-grad-subgroup-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="sat-overview-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="sat-ethnicity-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="sat-subgroup-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),                            
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-eca-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                        ],
                        id="hs-table-container",
                    ),
                    ]),
                ],
                id = "academic-information-main-container",
            ),
            html.Div(
                [
                    html.Div(id="academic-information-no-data"),
                ],
                id = "academic-information-empty-container",
            ),            
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="k8-overall-indicators"),
                                ],
                                className="pretty_container five columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="hs-overall-indicators"),
                                ],
                                className="pretty_container five columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="combined-indicators"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="enrollment-indicators"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="subgroup-grades"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [                                  
                            html.Div(
                                [
                                    html.Div(id="k8-academic-achievement"),
                                ],
                                className="pretty_container six columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),                                      
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="hs-academic-achievement"),
                                ],
                                className="pretty_container six columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="k8-academic-progress"),
                                ],
                                className="pretty_container five columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [                                                                
                            html.Div(
                                [
                                    html.Div(id="hs-academic-progress"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [        
                            html.Div(
                                [
                                    html.Div(id="closing-achievement-gap"),
                                ],
                                className="pretty_container six columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="graduation-rate-indicator"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="strength-of-diploma-indicator"),
                                ],
                                className="pretty_container four columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="ela-progress-indicator"),
                                ],
                                className="pretty_container five columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="absenteeism-indicator"),
                                ],
                                className="pretty_container five columns",
                            ),
                        ],
                        className="bare_container_center twelve columns",
                    ),
                ],
                id = "academic-growth-main-container",
            ),
            html.Div(
                [
                    html.Div(id="academic-growth-no-data"),
                ],
                id = "academic-growth-empty-container",
            ),
        ],
        id="mainContainer",
    )