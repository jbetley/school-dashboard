######################################
# ICSB Dashboard - Academic Analysis #
######################################
# author:   jbetley
# version:  1.01.040323

# TODO: Add AHS/HS Analysis

import dash
from dash import ctx, dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
import json
import re

# import local functions
from .calculations import find_nearest, filter_grades
from .chart_helpers import no_data_fig_label, make_line_chart,make_bar_chart, make_group_bar_chart # ,loading_fig
from .table_helpers import create_comparison_table, no_data_page, no_data_table
from .subnav import subnav_academic

dash.register_page(__name__, path = '/academic_analysis', order=6)

# TODO: CHOOSE A FREAKING COLOR!
#color_short=['#98abc5','#8a89a6','#7b6888','#6b486b','#a05d56','#d0743c','#ff8c00']
#color=['#98abc5','#919ab6','#8a89a6','#837997','#7b6888','#73587a','#6b486b','#865361','#a05d56','#b86949','#d0743c','#e8801e','#ff8c00']
# color=["fbf8cc","fde4cf","ffcfd2","f1c0e8","cfbaf0","a3c4f3","90dbf4","8eecf5","98f5e1","b9fbc0"]
# NOTE: removed 'American Indian' because the category doesn't appear in all data sets
# ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial', 'Native Hawaiian or Other Pacific Islander','White']
ethnicity = ['Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
subgroup = ['Special Education','General Education','Paid Meals','Free/Reduced Price Meals','English Language Learners','Non-English Language Learners']
grades = ['Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8']
subject = ['Math','ELA'] # 'ELA & Math'

# load comparison data file
all_schools_k8_academic_data = pd.read_csv(r'data/academic_data_k8.csv', dtype=str)

# get school information
school_index= pd.read_csv(r'data/school_index.csv', dtype=str)

# Set options for comparison schools (multi-select dropdown)
# NOTE: See 01.10.22 backup for original code
@callback(
    Output('comparison-dropdown', 'options'),
    Output('input-warning','children'),
    Output('comparison-dropdown', 'value'),
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    Input('comparison-dropdown', 'value'),
)
def set_dropdown_options(school, year, comparison_schools):

    # clear the list of comparison_schools when a new school is
    # selected (e.g., 'charter-dropdown' Input). otherwise
    # comparison_schools will carry over from school to school
    input_trigger = ctx.triggered_id
    if input_trigger == 'charter-dropdown':
        comparison_schools = []

    # filter out schools that did not exist in the selected year
    eval_year = [str(year)]
    
    current_year_all_schools_k8_academic_data = all_schools_k8_academic_data[all_schools_k8_academic_data['Year'].isin(eval_year)]
    current_year_all_schools_k8_academic_data = current_year_all_schools_k8_academic_data.reset_index(drop=True)

    location_data = current_year_all_schools_k8_academic_data[['Lat','Lon']]
    school_idx = current_year_all_schools_k8_academic_data[current_year_all_schools_k8_academic_data['School ID'] == school].index

    # because school_idx is calculated by searching the academic data
    # for grades 3-8, any school that is not included in the grade 3-8
    # dataset will have an empty school_idx. This check prevents HS and
    # AHS from generating a list of comparable schools.
    if school_idx.size == 0:
        return [],[],[]
    
    # get array of indexes and distances using the kdtree spatial tree function
    index_array, dist_array = find_nearest(school_idx,location_data)

    # convert np arrays to lists
    index_list = index_array[0].tolist()
    distance_list = dist_array[0].tolist()

    # create dataframe with distances and indexes
    distances = pd.DataFrame({'index':index_list, 'y':distance_list})
    distances = distances.set_index(list(distances)[0])

    # filter comparison set by matching indexes
    closest_schools = current_year_all_schools_k8_academic_data[current_year_all_schools_k8_academic_data.index.isin(index_list)]

    # add 'Distance' column to comparison_set (NOTE: Not currently used)
    comparison_set = pd.merge(closest_schools,distances,left_index=True, right_index=True)
    comparison_set = comparison_set.rename(columns = {'y': 'Distance'})

    # Drop the selected school from the list of available selections,
    # so selected school cannot be removed from dropdown. Comment this
    # line out to permit selected school to be cleared from chart (NOTE:
    # this may cause unexpected behavior)
    comparison_set = comparison_set.drop(comparison_set[comparison_set['School ID'] == school].index)

    # drop schools with no grade overlap with selected school by getting school grade span and filtering
    school_grade_span = current_year_all_schools_k8_academic_data.loc[current_year_all_schools_k8_academic_data['School ID'] == school][['Low Grade','High Grade']].values[0].tolist()
    school_grade_span = [s.replace('KG', '0').replace('PK', '0') for s in school_grade_span]
    school_grade_span = [int(i) for i in school_grade_span]
    school_grade_range = list(range(school_grade_span[0],(school_grade_span[1]+1)))

    # PK and KG are not tested grades
    comparison_set = comparison_set.replace({'Low Grade' : { 'PK' : '0', 'KG' : '0'}})

    # drop schools with no grades (NOTE: Not sure why dropna doesn't work here,
    # but it doesn't - maybe because its 'nan' instead of 'NaN'?)
    comparison_set = comparison_set[comparison_set['Low Grade'].str.contains('nan')==False]

    grade_mask = comparison_set.apply(filter_grades, compare=school_grade_range, axis=1)
    comparison_set = comparison_set[grade_mask]

    # limit maximum dropdown to the [n] closest schools
    num_schools_expanded = 20

    comparison_set = comparison_set.sort_values(by=['Distance'], ascending=True)

    comparison_dropdown = comparison_set.head(num_schools_expanded)

    comparison_dict = dict(zip(comparison_dropdown['School Name'], comparison_dropdown['School ID']))

    # final list will be displayed in order of increasing distance from selected school
    comparison_list = dict(comparison_dict.items())

    # Set default display selections to all schools in the list and
    # the number of options to be pre-selected to 4
    default_options = [{'label':name,'value':id} for name, id in comparison_list.items()]
    options = default_options

    # value for number of default display selections and maximum
    # display selections (because of zero indexing, max should be
    # 1 less than actual desired number)
    default_num_to_display = 4
    max_num_to_display = 7

    # the following tracks the number of selections and disables all remaining
    # selections once 8 schools have been selected
    input_warning = None

    # if list is None or empty ([]), use the default options
    if not comparison_schools:
        comparison_schools = [d['value'] for d in options[:default_num_to_display]]

    else:

        if len(comparison_schools) > max_num_to_display:
            input_warning = html.P(
                id='input-warning',
                children='Limit reached (Maximum of ' + str(max_num_to_display+1) + ' schools).',
            )
            options = [
                {"label": option["label"], "value": option["value"], "disabled": True}
                for option in default_options
            ]
    
    return options, input_warning, comparison_schools

@callback(
    Output('fig14a', 'children'),
    Output('fig14b', 'children'),
    Output('fig14c', 'children'),
    Output('fig14c-table', 'children'),
    Output('fig14d', 'children'),
    Output('fig14d-table', 'children'),
    Output('fig-iread', 'children'),
    Output('fig-iread-table', 'children'),
    Output('fig16c1', 'children'),
    Output('fig16d1', 'children'),
    Output('fig16c2', 'children'),
    Output('fig16d2', 'children'),
    Output('fig14g', 'children'),
    Output('fig16a1', 'children'),
    Output('fig16a1-table', 'children'),
    Output('fig16a1-category-string', 'children'),
    Output('fig16a1-school-string', 'children'),
    Output('fig16a1-table-container', 'style'),    
    Output('fig16b1', 'children'),
    Output('fig16b1-table', 'children'),
    Output('fig16b1-category-string', 'children'),
    Output('fig16b1-school-string', 'children'),
    Output('fig16b1-table-container', 'style'),
    Output('fig16a2', 'children'),
    Output('fig16a2-table', 'children'),    
    Output('fig16a2-category-string', 'children'),
    Output('fig16a2-school-string', 'children'),
    Output('fig16a2-table-container', 'style'),
    Output('fig16b2', 'children'),
    Output('fig16b2-table', 'children'),
    Output('fig16b2-category-string', 'children'),
    Output('fig16b2-school-string', 'children'),
    Output('fig16b2-table-container', 'style'),
    Output('academic-analysis-main-container', 'style'),
    Output('academic-analysis-empty-container', 'style'),
    Output('academic-analysis-no-data', 'children'),
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    Input('dash-session', 'data'),
    [Input('comparison-dropdown', 'value')],
)
def update_academic_analysis(school, year, data, comparison_school_list):
    if not school:
        raise PreventUpdate

    selected_year = str(year)

    # default styles
    main_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_to_display = no_data_page('Academic Analysis')

    # school_index.json
    school_info = pd.DataFrame.from_dict(data['0'])
    school_name = school_info['School Name'].values[0]

    # Test if data exists - there are 4 cases where we end up with an empty page:
    #   1) the dataframe itself does not exist because there is no academic data for the school at all
    #   2) the school is of a type (AHS/HS) that doesn't yet have any charted data
    #   3) the dataframe exists, but the tested_header (YEARSchool) does not exist in the dataframe-
    #       this catches any year with no data (e.g., 2020School because there is no 2020 data in the
    #       dataframe
    #   4) the tested header does exist, but all data in the column is NaN- this catches any year where
    #       the school has no data or insufficient n-size ('***')
    
    #   Only get to tests (3) and (4) if dataframe passes tests (1) & (2)

    # Testing (1) and (2)
    if (school_info['School Type'].values[0] == 'K8' and not data['8']) or \
        school_info['School Type'].values[0] == 'HS' or school_info['School Type'].values[0] == 'AHS':

        fig14a = fig14b = fig14c = fig14d = fig_iread = fig16c1 = fig16d1 = fig16c2 = fig16d2 = fig14g = fig16a1 = fig16b1 = fig16a2 = fig16b2 = {}
        fig14c_table = fig14d_table = fig_iread_table = fig16a1_table = fig16b1_table = fig16a2_table = fig16b2_table = {}
        fig16a1_category_string = fig16b1_category_string = fig16a2_category_string = fig16b2_category_string = ''
        fig16a1_school_string = fig16b1_school_string = fig16a2_school_string = fig16b2_school_string = ''
        fig16a1_table_container = {'display': 'none'}
        fig16b1_table_container = {'display': 'none'}
        fig16a2_table_container = {'display': 'none'}
        fig16b2_table_container = {'display': 'none'}
        main_container = {'display': 'none'}
        empty_container = {'display': 'block'}

    else:
        
        # load k8_academic_data_json (School/Corp/+- for each category)
        json_data = json.loads(data['8'])
        school_academic_matrix = pd.DataFrame.from_dict(json_data)
        
        tested_academic_data = school_academic_matrix.copy()
        
        for col in tested_academic_data.columns:
            tested_academic_data[col] = pd.to_numeric(tested_academic_data[col], errors='coerce')
        
        tested_header = selected_year + 'School'

        # Testing (3) and (4)
        if tested_header not in tested_academic_data.columns or \
            tested_academic_data[tested_header].isnull().all():
            
            fig14a = fig14b = fig14c = fig14d = fig_iread = fig16c1 = fig16d1 = fig16c2 = fig16d2 = fig14g = fig16a1 = fig16b1 = fig16a2 = fig16b2 = {}
            fig14c_table = fig14d_table = fig_iread_table = fig16a1_table = fig16b1_table = fig16a2_table = fig16b2_table = {}
            fig16a1_category_string = fig16b1_category_string = fig16a2_category_string = fig16b2_category_string = ''
            fig16a1_school_string = fig16b1_school_string = fig16a2_school_string = fig16b2_school_string = ''
            fig16a1_table_container = {'display': 'none'}
            fig16b1_table_container = {'display': 'none'}
            fig16a2_table_container = {'display': 'none'}
            fig16b2_table_container = {'display': 'none'}
            main_container = {'display': 'none'}
            empty_container = {'display': 'block'}

        else:

            # Display selected school's year over year data

            # keep only columns with 'Category' or 'School' in name
            school_academic_data = school_academic_matrix[[col for col in school_academic_matrix.columns if 'School' in col or 'Category' in col]].copy()

            # remove 'School' from column headers (leaving the Year)
            school_academic_data.columns = school_academic_data.columns.str.replace(r'School$', '', regex=True)

            # TODO: Need to come up with a way to display when a school has insufficient n-size,
            # TODO: because it implies that there is no data- makes it hard to measure trends, e.g.,
            # TODO: when a school shows a percentage for a year and the no data for the subsequent year
            # TODO: for example Allegiant for subgroup in 2021 (data) vs 2022 (no data because ***)
            # TODO: perhaps determine which categories are *** and store them in separate list and show
            # TODO: them as annotations

            # drop any column (Year) where all values are either None or ***
            # '***' represents data, but is unchartable. Do this by converting all
            # columns other than 'Category' to numeric. This turns all None
            # and '***' values to NaN, and then dropping all columns where every
            # value is NaN
            school_academic_data_numeric_headers = [j for j in school_academic_data.columns if 'Category' not in j]

            for col in school_academic_data_numeric_headers:
                school_academic_data[col] = pd.to_numeric(school_academic_data[col], errors='coerce')
            
            school_academic_data = school_academic_data.dropna(axis=1, how='all')

            # transpose the resulting dataframe (making Categories the column headers)
            display_academic_data = school_academic_data.set_index('Category').T.rename_axis('Year').rename_axis(None, axis=1).reset_index()

            # drop any Category where all values are NaN
            display_academic_data = display_academic_data.dropna(axis=1, how='all')

            # add suffix to certain Categories
            display_academic_data = display_academic_data.rename(columns={c: c + ' Proficient %' for c in display_academic_data.columns if c not in ['Year', 'School Name','IREAD Proficiency (Grade 3 only)']})

            # must be at least one year (one row) of data
            if len(display_academic_data.index) >= 1:

                yearly_school_data = display_academic_data.copy()
                yearly_school_data['School Name'] = school_name

                # Chart 1: Year over Year ELA Proficiency by Grade (1.4.a)
                fig14a_data = yearly_school_data.filter(regex = r'^Grade \d\|ELA|^School Name$|^Year$',axis=1)
                fig14a = make_line_chart(fig14a_data,'Year over Year ELA Proficiency by Grade')

                # Chart 2: Year over Year Math Proficiency by Grade (1.4.b)
                fig14b_data = yearly_school_data.filter(regex = r'^Grade \d\|Math|^School Name$|^Year$',axis=1)
                fig14b = make_line_chart(fig14b_data,'Year over Year Math Proficiency by Grade')

                # Charts 3 & 4: See below

                # Chart 5: Year over Year ELA Proficiency by Ethnicity (1.6.c)
                categories_16c1 = []
                for e in ethnicity:
                    categories_16c1.append(e + '|' + 'ELA Proficient %')

                fig16c1_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16c1)) | (yearly_school_data.columns.isin(['School Name','Year']))]
                fig16c1_data = fig16c1_data.rename(columns = {'Native Hawaiian or Other Pacific Islander|ELA Proficient %': 'Pacific Islander|ELA Proficient %'})
                fig16c1 = make_line_chart(fig16c1_data,'Year over Year ELA Proficiency by Ethnicity')

                # Chart 6: Year over Year Math Proficiency by Ethnicity (1.6.d)
                categories_16d1 = []
                for e in ethnicity:
                    categories_16d1.append(e + '|' + 'Math Proficient %')

                fig16d1_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16d1)) | (yearly_school_data.columns.isin(['School Name','Year']))]
                fig16d1_data = fig16d1_data.rename(columns = {'Native Hawaiian or Other Pacific Islander|Math Proficient %': 'Pacific Islander|Math Proficient %'})
                fig16d1 = make_line_chart(fig16d1_data,'Year over Year Math Proficiency by Ethnicity')

                # Chart 7: Year over Year ELA Proficiency by Subgroup (1.6.c)
                categories_16c2 = []
                for s in subgroup:
                    categories_16c2.append(s + '|' + 'ELA Proficient %')

                fig16c2_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16c2)) | (yearly_school_data.columns.isin(['School Name','Year']))]
                fig16c2 = make_line_chart(fig16c2_data,'Year over Year ELA Proficiency by Subgroup')

                # Chart 8: Year over Year Math Proficiency by Subgroup (1.6.d)
                categories_16d2 = []
                for s in subgroup:
                    categories_16d2.append(s + '|' + 'Math Proficient %')

                fig16d2_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16d2)) | (yearly_school_data.columns.isin(['School Name','Year']))]
                fig16d2 = make_line_chart(fig16d2_data,'Year over Year Math Proficiency by Subgroup')

                # Chart 9 - IREAD Year over Year
                category_iread = 'IREAD Proficiency (Grade 3 only)'

                fig14g_data = yearly_school_data.loc[:, (yearly_school_data.columns == category_iread) | (yearly_school_data.columns.isin(['School Name','Year']))]
                fig14g = make_line_chart(fig14g_data, category_iread)

            else:   
                
                # As long as we are rendering 1 year of data, this should never happen. If
                # the dataframe has no data, the entire page would be blank.
                # TODO: TEST AND REMOVE IF UNNECESSARY

                fig14a = no_data_fig_label('Year over Year ELA Proficiency by Grade', 200)
                fig14b = no_data_fig_label('Year over Year Math Proficiency by Grade', 200)
                fig16c1 = no_data_fig_label('Year over Year ELA Proficiency by Ethnicity', 200)
                fig16d1 = no_data_fig_label('Year over Year Math Proficiency by Ethnicity', 200)
                fig16c2 = no_data_fig_label('Year over Year ELA Proficiency by Subgroup', 200)
                fig16d2 = no_data_fig_label('Year over Year Math Proficiency by Subgroup', 200)
                fig14g = no_data_fig_label('Year over Year IREAD Proficiency', 200)

            # Display the selected year's academic data compared to comparable schools
            # selected by the user.

            # Get current year school data
            current_school_data = display_academic_data.loc[display_academic_data['Year'] == selected_year].copy()

            # drop any Category where value is NaN
            current_school_data = current_school_data.dropna(axis=1, how='all')

            current_school_data['School Name'] = school_name

            # Grade range data is used for the chart 'hovertemplate'
            current_school_data['Low Grade'] = all_schools_k8_academic_data.loc[(all_schools_k8_academic_data['School ID'] == school) & (all_schools_k8_academic_data['Year'] == selected_year)]['Low Grade'].values[0]
            current_school_data['High Grade'] = all_schools_k8_academic_data.loc[(all_schools_k8_academic_data['School ID'] == school) & (all_schools_k8_academic_data['Year'] == selected_year)]['High Grade'].values[0]
            
            # get dataframe for traditional public schools located within the school
            # corporation that selected school resides

            # academic_analysis_corp_dict
            k8_corp_data = pd.DataFrame.from_dict(data['7'])

            corp_current_data = k8_corp_data.loc[k8_corp_data['Year'] == int(selected_year)]

            # filter unnecessary columns
            corp_current_data = corp_current_data.filter(regex = r'\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$|^School Name$',axis=1)

            # rename IREAD column
            corp_current_data = corp_current_data.rename(
                columns={"IREAD Pass %": "IREAD Proficiency (Grade 3 only)"}
            )            
      
            # coerce data types to numeric (except strings)
            for col in corp_current_data.columns:
                corp_current_data[col]=pd.to_numeric(corp_current_data[col], errors='coerce').fillna(corp_current_data[col]).tolist()

            # get academic data for comparison schools
            # filter full set by year and the schools selected in the dropdown

            eval_year = [str(current_school_data['Year'].values[0])]

            current_year_all_schools_k8_academic_data = all_schools_k8_academic_data[all_schools_k8_academic_data['Year'].isin(eval_year)]

            comparison_schools_filtered = current_year_all_schools_k8_academic_data[current_year_all_schools_k8_academic_data['School ID'].isin(comparison_school_list)]

            # drop unused columns
            comparison_schools_filtered = comparison_schools_filtered.filter(regex = r'Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year|School Name|School ID|Distance|Low Grade|High Grade',axis=1)

            # create list of columns with no date (used in loop below)
            # missing_mask returns boolean series of columns where all elements in the column
            # are equal to null 
            missing_mask = pd.isnull(current_school_data[current_school_data.columns]).all()
            missing_cols = current_school_data.columns[missing_mask].to_list()

            comparison_schools_info = comparison_schools_filtered[['School ID','School Name','Low Grade','High Grade']].copy()
            comparison_schools_filtered = comparison_schools_filtered.drop(['School ID','School Name','Low Grade','High Grade'], axis=1)

            # change values to numeric
            for col in comparison_schools_filtered.columns:
                comparison_schools_filtered[col] = pd.to_numeric(comparison_schools_filtered[col], errors='coerce')

            comparison_schools = comparison_schools_filtered.copy()

            # iterate over all categories, ignoring missing columns, calculate the average, and store in a new column
            categories = ethnicity + subgroup + grades + ['Total']

            for s in subject:
                for c in categories:
                    new_col = c + '|' + s + ' Proficient %'
                    proficient = c + '|' + s + ' Total Proficient'
                    tested = c + '|' + s + ' Total Tested'

                    if proficient not in missing_cols:
                        comparison_schools[new_col] = comparison_schools[proficient] / comparison_schools[tested]

            # NOTE: The masking step above removes grades from the comparison
            # dataframe that are not also in the school dataframe (e.g., if
            # school only has data for grades 3, 4, & 5, only those grades
            # will remain in comparison df). However, the 'School Total' for
            # proficiency in a subject that is in the raw data was calculated
            # using ALL grades. So we need to recalculate the 'School Total' rate
            # manually to ensure it includes only the included grades.
            all_grades_math_proficient_comp = comparison_schools.filter(regex=r"Grade.+?Math Total Proficient")
            all_grades_math_tested_comp = comparison_schools.filter(regex=r"Grade.+?Math Total Tested")
            comparison_schools['Total|Math Proficient %'] = all_grades_math_proficient_comp.sum(axis=1) / all_grades_math_tested_comp.sum(axis=1)

            all_grades_ela_proficient_comp = comparison_schools.filter(regex=r"Grade.+?ELA Total Proficient")
            all_grades_ela_tested_comp = comparison_schools.filter(regex=r"Grade.+?ELA Total Tested")
            comparison_schools['Total|ELA Proficient %'] = all_grades_ela_proficient_comp.sum(axis=1) / all_grades_ela_tested_comp.sum(axis=1)

            # calculate IREAD Pass %
            if 'IREAD Proficiency (Grade 3 only)' in current_school_data:
                comparison_schools['IREAD Proficiency (Grade 3 only)'] = comparison_schools['IREAD Pass N'] / comparison_schools['IREAD Test N']

            # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
            comparison_schools = comparison_schools.filter(regex = r'\|ELA Proficient %$|\|Math Proficient %$|^IREAD Proficiency|^Year$',axis=1)

            # drop all columns from the comparison dataframe that aren't in the school dataframe
            # because the school file has already been processed, column names will not directly
            # match, so we create a list of unique substrings from the column names and use it
            # to filter the comparison set
            valid_columns = current_school_data.columns.str.split('|').str[0].tolist()
            comparison_schools = comparison_schools.filter(regex='|'.join(valid_columns))

            # drop any rows where all values in tested cols (proficiency data) are null (remove 'Year' from column
            # list because 'Year' will never be null)
            tested_columns = comparison_schools.columns.tolist()
            tested_columns.remove('Year')
            comparison_schools = comparison_schools.dropna(subset=tested_columns,how='all')

            # add text info columns back
            comparison_schools = pd.concat([comparison_schools, comparison_schools_info], axis=1, join='inner')

            # reset indicies
            comparison_schools = comparison_schools.reset_index(drop=True)
            
### TODO: Add HS Data ###
            # hs_comparison_data = hs_all_data_included_years.loc[(hs_all_data_included_years['School ID'].isin(comparison_schools))]
            #     # filter comparable school data
            # hs_comparison_data = hs_comparison_data.filter(regex = r'Cohort Count$|Graduates$|Pass N|Test N|^Year$',axis=1)

            # ## See above (k8_diff)
            # hs_diff = list(set(hs_corp_data['Year'].unique().tolist()) - set(hs_school_data['Year'].unique().tolist()))

            # if hs_diff:
            #     hs_corp_data = hs_corp_data[~hs_corp_data['Year'].isin(hs_diff)]
            #     hs_comparison_data = hs_comparison_data[~hs_comparison_data['Year'].isin(hs_diff)]

            # # ensure columns headers are strings
            # hs_comparison_data.columns = hs_comparison_data.columns.astype(str)

### TODO: how id the position of the position of the selected school trace determined? Can
### TODO: we place it manually?

            ### TODO: Refactor?
            # get name of school corporation
            school_corporation_name = current_year_all_schools_k8_academic_data.loc[(all_schools_k8_academic_data['Corp ID'] == school_info['GEO Corp'].values[0])]['Corp Name'].values[0]

            #### Current Year ELA Proficiency Compared to Similar Schools (1.4.c) #
            category = 'Total|ELA Proficient %'

            # Get school value for specific category
            if category in current_school_data.columns:

                fig14c_k8_school_data = current_school_data[['School Name','Low Grade','High Grade',category]].copy()

                # add corp average for category to dataframe - the '','','N/A' are values for Low & High Grade and Distance columns
                fig14c_k8_school_data.loc[len(fig14c_k8_school_data.index)] = [school_corporation_name,'3','8',corp_current_data[category].values[0]]

                # Get comparable school values for the specific category
                fig14c_comp_data = comparison_schools[['School Name','Low Grade','High Grade',category]]

                # Combine data, fix dtypes, and send to chart function
                fig14c_all_data = pd.concat([fig14c_k8_school_data,fig14c_comp_data])

                # save table data
                fig14c_table_data = fig14c_all_data.copy()

                # convert datatypes
                fig14c_all_data[category] = pd.to_numeric(fig14c_all_data[category])

                # make the bar chart
                fig14c = make_bar_chart(fig14c_all_data, category, school_name, 'Comparison: Current Year ELA Proficiency')

                # merge column names and make ELA Proficiency table
                fig14c_table_data['School Name'] = fig14c_table_data['School Name'] + " (" + fig14c_table_data['Low Grade'] + "-" + fig14c_table_data['High Grade'] + ")"
                fig14c_table_data = fig14c_table_data[['School Name', category]]
                fig14c_table_data = fig14c_table_data.reset_index(drop=True)

                fig14c_table = create_comparison_table(fig14c_table_data, school_name,'Proficiency')

            else:

                # TODO: TEST - WILL THIS EVER BE BLANK? IF SO, DISCOVER BLANK CONDITION AND
                # TODO: MOVE TO THE make_bar_chart function (similar to make_line_chart)

                fig14c = no_data_fig_label('Comparison: Current Year ELA Proficiency',200)
                fig14c_table = no_data_table('Proficiency')

        #### Current Year Math Proficiency Compared to Similar Schools (1.4.d) #
            category = 'Total|Math Proficient %'

            if category in current_school_data.columns:

                fig14d_k8_school_data = current_school_data[['School Name','Low Grade','High Grade',category]].copy()

                # add corp average for category to dataframe - the '','','N/A' are values for Low & High Grade and Distance columns
                fig14d_k8_school_data.loc[len(fig14d_k8_school_data.index)] = [school_corporation_name, '3','8',corp_current_data[category].values[0]]

                # Get comparable school values for the specific category
                fig14d_comp_data = comparison_schools[['School Name','Low Grade','High Grade',category]]
                # fig14d_comp_data = comparison_schools[['School Name','Low Grade','High Grade','Distance',category]]

                fig14d_all_data = pd.concat([fig14d_k8_school_data,fig14d_comp_data])

                # save table data
                fig14d_table_data = fig14d_all_data.copy()

                fig14d_all_data[category] = pd.to_numeric(fig14d_all_data[category])

                fig14d = make_bar_chart(fig14d_all_data,category, school_name, 'Comparison: Current Year Math Proficiency')

                # Math Proficiency table
                fig14d_table_data['School Name'] = fig14d_table_data['School Name'] + " (" + fig14d_table_data['Low Grade'] + "-" + fig14d_table_data['High Grade'] + ")"
                fig14d_table_data = fig14d_table_data[['School Name', category]]
                fig14d_table_data = fig14d_table_data.reset_index(drop=True)

                fig14d_table = create_comparison_table(fig14d_table_data, school_name, 'Proficiency')
            else:
                fig14d = no_data_fig_label('Comparison: Current Year Math Proficiency',200)
                fig14d_table = no_data_table('Proficiency')

            #### Current Year IREAD Proficiency Compared to Similar Schools #
            category = 'IREAD Proficiency (Grade 3 only)'

            if category in current_school_data.columns:

                fig_iread_k8_school_data = current_school_data[['School Name','Low Grade','High Grade',category]].copy()

                # add corp average for category to dataframe - the '','','N/A' are values for Low & High Grade and Distance columns
                fig_iread_k8_school_data.loc[len(fig_iread_k8_school_data.index)] = [school_corporation_name, '3','8',corp_current_data[category].values[0]]

                # Get comparable school values for the specific category
                fig_iread_comp_data = comparison_schools[['School Name','Low Grade','High Grade',category]]
                # fig_iread_comp_data = comparison_schools[['School Name','Low Grade','High Grade','Distance',category]]

                fig_iread_all_data = pd.concat([fig_iread_k8_school_data,fig_iread_comp_data])
                # save table data
                fig_iread_table_data = fig_iread_all_data.copy()

                fig_iread_all_data[category] = pd.to_numeric(fig_iread_all_data[category])

                fig_iread = make_bar_chart(fig_iread_all_data,category, school_name, 'Comparison: Current Year IREAD Proficiency')

                # Math Proficiency table
                fig_iread_table_data['School Name'] = fig_iread_table_data['School Name'] + " (" + fig_iread_table_data['Low Grade'] + "-" + fig_iread_table_data['High Grade'] + ")"
                fig_iread_table_data = fig_iread_table_data[['School Name', category]]
                fig_iread_table_data = fig_iread_table_data.reset_index(drop=True)

                fig_iread_table = create_comparison_table(fig_iread_table_data, school_name, 'Proficiency')
            else:
                fig_iread = no_data_fig_label('Comparison: Current Year IREAD Proficiency',200)
                fig_iread_table = no_data_table('Proficiency')

            # create comparison charts/tables
            # NOTE: See backup data 01.23.23 for pre- create_full_chart() function code

            # info col headers is the same for all dataframes
            info_categories = ['School Name','Low Grade','High Grade']
            
            def create_full_chart(school_data, categories, corp_name):
                # A fig, a table, and two strings walk into a bar . . .

                # TODO: This is messy. Uses functions from both helper files.
                # TODO: Could move to chart-helpers and call table_helpers there
                # TODO: but does that cause any circular references?

                info_categories = ['School Name','Low Grade','High Grade']
                all_categories = categories + info_categories

                # get a list of the categories that exist in school data
                academic_columns = [i for i in categories if i in school_data.columns]

                # get a list of the categories that are missing from school data and
                # strip everything following '|' delimeter
                missing_categories = [i for i in categories if i not in school_data.columns]
                missing_categories = [s.split('|')[0] for s in missing_categories]

                # sort corp data by the academic columns
                corp_data = corp_current_data.loc[:, (corp_current_data.columns.isin(academic_columns))].copy()

                # add the school corporation name
                corp_data['School Name'] = corp_name

                # concatenate the school and corporation dataframes, filling empty values (e.g., Low and High Grade) with ''
                first_merge_data = pd.concat([school_data, corp_data], sort=False).fillna('')

                # filter comparable schools
                comp_data = comparison_schools.loc[:, comparison_schools.columns.isin(all_categories)]

                # concatenate school/corp and comparison dataframes
                combined_data = pd.concat([first_merge_data,comp_data])
                combined_data = combined_data.reset_index(drop=True)

                # make a copy (used for comparison purposes)
                final_data = combined_data.copy()

                # get a list of all of the schools (each one a column)
                category_columns = final_data.columns.tolist()
                category_columns = [ele for ele in category_columns if ele not in info_categories]

                # test all school columns and drop any where all columns (proficiency data) is nan/null
                final_data = final_data.dropna(subset=category_columns, how='all')

                # Create a series that merges school name and grade spans and drop the grade span columns 
                # from the dataframe (they are not charted)
                school_names = final_data['School Name'] + " (" + final_data['Low Grade'] + "-" \
                + final_data['High Grade'] + ")"      
                
                final_data = final_data.drop(['Low Grade', 'High Grade'], axis = 1)

                # In some cases, cell data is '' or ' ', so we need to replace any
                # blanks with NaN
                final_data = final_data.replace(r'^\s*$', np.nan, regex=True)

                # get the names of the schools that have no data by comparing the column sets before and
                # after the drop
                missing_schools = list(set(combined_data['School Name']) - set(final_data['School Name']))

                # Create missing category string
                if missing_categories:
                    category_string = ', '.join(list(map(str, missing_categories))) + '.'
                else:
                    category_string = 'None.'                  

                # Create missing schools string
                if missing_schools:
                    school_string = ', '.join(list(map(str, missing_schools))) + '.'
                else:
                    school_string = 'None.'

                final_data_columns = final_data.columns.tolist()

                # Create the chart label

                # the list returns any strings in final_data_columns that are in the
                # ethnicity list or subgroup list. Label is based on whichever list
                # of substrings matches the column list

                if len([i for e in ethnicity for i in final_data_columns if e in i]) > 0:
                    label_category= ' Proficiency by Ethnicity'
                elif len([i for e in subgroup for i in final_data_columns if e in i]) > 0:
                    label_category= ' Proficiency by Subgroup'                      

                # get the subject using regex
                label_subject = re.search(r'(?<=\|)(.*?)(?=\s)',final_data_columns[0]).group()
                
                label = 'Comparison: ' + label_subject + label_category
                
                #  create chart
                chart = make_group_bar_chart(final_data, school_name, label)

                # shift the 'School Name' column to the first position and replace
                # the values in 'School Name' column with the series we created earlier
                final_data = final_data.drop('School Name', axis = 1)
                final_data['School Name'] = school_names

                first_column = final_data.pop('School Name')
                final_data.insert(0, 'School Name', first_column)

                # create table
                table = create_comparison_table(final_data, school_name,'')

                return chart, table, category_string, school_string

            # TODO: Turn this into function?
            # TODO: See above, need to account for '***'
            # ELA Proficiency by Ethnicity Compared to Similar Schools (1.6.a.1)
            headers_16a1 = []
            for e in ethnicity:
                headers_16a1.append(e + '|' + 'ELA Proficient %')

            categories_16a1 =  info_categories + headers_16a1

            # filter dataframe by categories
            fig16a1_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16a1))]
            
            if len(fig16a1_k8_school_data.columns) > 3:
                fig16a1, fig16a1_table, fig16a1_category_string, fig16a1_school_string = \
                    create_full_chart(fig16a1_k8_school_data, headers_16a1, school_corporation_name)

                fig16a1_table_container = {'display': 'block'}
            
            else:
                fig16a1 = no_data_fig_label('Comparison: ELA Proficiency by Ethnicity', 200)
                fig16a1_table = {}
                fig16a1_category_string = ''
                fig16a1_school_string = ''                
                fig16a1_table_container = {'display': 'none'}

            # Math Proficiency by Ethnicity Compared to Similar Schools (1.6.b.1)
            headers_16b1 = []
            for e in ethnicity:
                headers_16b1.append(e + '|' + 'Math Proficient %')

            categories_16b1 =  info_categories + headers_16b1

            # filter dataframe by categories
            fig16b1_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16b1))]

            if len(fig16b1_k8_school_data.columns) > 3:
                fig16b1, fig16b1_table, fig16b1_category_string, fig16b1_school_string = \
                    create_full_chart(fig16b1_k8_school_data, headers_16b1, school_corporation_name)

                fig16b1_table_container = {'display': 'block'}
            
            else:
                fig16b1 = no_data_fig_label('Comparison: Math Proficiency by Ethnicity', 200)
                fig16b1_table = {}
                fig16b1_category_string = ''
                fig16b1_school_string = ''                
                fig16b1_table_container = {'display': 'none'}

            # ELA Proficiency by Subgroup Compared to Similar Schools (1.6.a.2)
            headers_16a2 = []
            for s in subgroup:
                headers_16a2.append(s + '|' + 'ELA Proficient %')
            
            categories_16a2 =  info_categories + headers_16a2

            # filter dataframe by categories
            fig16a2_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16a2))]

            if len(fig16a2_k8_school_data.columns) > 3:
                fig16a2, fig16a2_table, fig16a2_category_string, fig16a2_school_string = \
                    create_full_chart(fig16a2_k8_school_data, headers_16a2, school_corporation_name)

                fig16a2_table_container = {'display': 'block'}
            
            else:
                fig16a2 = no_data_fig_label('Comparison: ELA Proficiency by Subgroup', 200)
                fig16a2_table = {}
                fig16a2_category_string = ''
                fig16a2_school_string = ''                
                fig16a2_table_container = {'display': 'none'}

            # Math Proficiency by Subgroup Compared to Similar Schools (1.6.b.2)
            headers_16b2 = []
            for s in subgroup:
                headers_16b2.append(s + '|' + 'Math Proficient %')

            categories_16b2 =  info_categories + headers_16b2

            # filter dataframe by categories
            fig16b2_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16b2))]

            if len(fig16b2_k8_school_data.columns) > 3:
                fig16b2, fig16b2_table, fig16b2_category_string,fig16b2_school_string = \
                    create_full_chart(fig16b2_k8_school_data, headers_16b2, school_corporation_name)

                fig16b2_table_container = {'display': 'block'}
            
            else:
                fig16b2 = no_data_fig_label('Comparison: Math Proficiency by Subgroup', 200)
                fig16b2_table = {}
                fig16b2_category_string = ''
                fig16b2_school_string = ''                
                fig16b2_table_container = {'display': 'none'}

    # main_container = {'display': 'block'}
    return fig14a, fig14b, fig14c, fig14c_table, fig14d, fig14d_table, fig_iread, \
        fig_iread_table, fig16c1, fig16d1, fig16c2, fig16d2, fig14g, fig16a1, \
        fig16a1_table, fig16a1_category_string, \
        fig16a1_school_string, fig16a1_table_container, fig16b1, fig16b1_table, \
        fig16b1_category_string, fig16b1_school_string, fig16b1_table_container, \
        fig16a2, fig16a2_table, fig16a2_category_string, fig16a2_school_string, \
        fig16a2_table_container, fig16b2, fig16b2_table, fig16b2_category_string, \
        fig16b2_school_string, fig16b2_table_container, \
        main_container, empty_container, no_data_to_display

def layout():
    return html.Div(
# layout = html.Div(
            [
 # NOTE: Could not figure out how to add loading block due
 # to number of charts - instead we are using a blank_fig with 
 # "Loading ..." text as a placeholder until graph loads
 # https://stackoverflow.com/questions/63811550/plotly-how-to-display-graph-after-clicking-a-button

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
                                        html.Div(id='fig14a', children=[])
                                    ],
                                    className = 'pretty_container six columns'
                                ),
                                html.Div(
                                    [
                                        html.Div(id='fig14b', children=[])
                                    ],
                                    className = 'pretty_container six columns'
                                )
                            ],
                            className='row'
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='fig16c1', children=[])
                                    ],
                                    className = 'pretty_container six columns'
                                ),
                                html.Div(
                                    [
                                        html.Div(id='fig16d1', children=[])
                                    ],
                                    className = 'pretty_container six columns'
                                )
                            ],
                            className='row'
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='fig16c2', children=[])        
                                    ],
                                    className = 'pretty_container six columns'
                                ),
                                html.Div(
                                    [
                                        html.Div(id='fig16d2', children=[])
                                    ],
                                    className = 'pretty_container six columns'
                                )
                            ],
                            className='row',
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='fig14g', children=[])
                                    ],
                                    className = 'pretty_container six columns'
                                ),
                            ],
                            className='row',
                        ),

                        # Comparison Charts
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P(
                                            'Add or Remove Schools: ',
                                            className='control_label'
                                        ),
                                        dcc.Dropdown(
                                            id='comparison-dropdown',
                                            style={'fontSize': '85%'},
                                            multi = True,
                                            clearable = False,
                                            className='dcc_control'
                                        ),
                                        html.Div(id='input-warning'),
                                    ],
                                ),
                            ],
                            className='row'
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='fig14c', children=[])           
                                    ],
                                    className = 'pretty_container nine columns',
                                ),
                                html.Div(
                                    [
                                        html.Div(id='fig14c-table', children=[])           
                                    ],
                                    className = 'pretty_container three columns'
                                ),
                            ],
                            className='row'
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='fig14d', children=[])         
                                    ],
                                    className = 'pretty_container nine columns',
                                ),
                                html.Div(
          
                                    [
                                        html.Div(id='fig14d-table', children=[])          
                                    ],
                                    className = 'pretty_container three columns'
                                )
                            ],
                            className='row'
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='fig-iread', children=[])         
                                    ],
                                    className = 'pretty_container nine columns',
                                ),
                                html.Div(
                                    [
                                        html.Div(id='fig-iread-table', children=[])          
                                    ],
                                    className = 'pretty_container three columns'
                                ),
                            ],
                            className='row'
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='fig16a1', children=[])           
                                    ],
                                    className = 'pretty_close_container twelve columns',
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
                                                html.Div(id='fig16a1-table'),
                                                html.P(
                                                    id='fig16a1-category-string',
                                                    children=[
                                                    'Categories with insufficient n-size or no data:',
                                                    html.Span(id='fig16a1-category-string', children='', className = 'category_string'),
                                                    ],
                                                    className = 'category_string_label',
                                                ),
                                                html.P(
                                                    id='fig16a1-school-string',
                                                    children=[
                                                    'Schools with insufficient n-size or no data:',
                                                    html.Span(id='fig16a1-school-string', children='', className = 'school_string'),
                                                    ],
                                                    className = 'school_string_label',
                                                ),
                                            ],
                                            className = 'close_container twelve columns'
                                        )
                                    ],
                                    className='row'
                                ),
                            ],
                            id = 'fig16a1-table-container',
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='fig16b1', children=[])
                                    ],
                                    className = 'pretty_close_container twelve columns',
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
                                                html.Div(id='fig16b1-table'),
                                                html.P(
                                                    id='fig16b1-category-string',
                                                    children=[
                                                    'Categories with insufficient n-size or no data:',
                                                    html.Span(id='fig16b1-category-string', children='', className = 'category_string'),
                                                    ],
                                                    className = 'category_string_label',
                                                ),
                                                html.P(
                                                    id='fig16b1-school-string',
                                                    children=[
                                                    'Schools with insufficient n-size or no data:',
                                                    html.Span(id='fig16b1-school-string', children='', className = 'school_string'),
                                                    ],
                                                    className = 'school_string_label',
                                                ),               
                                            ],
                                            className = 'close_container twelve columns'
                                        )
                                    ],
                                    className='row'
                                ),
                            ],
                            id = 'fig16b1-table-container',
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='fig16a2', children=[])        
                                    ],
                                    className = 'pretty_close_container twelve columns',
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
                                                html.Div(id='fig16a2-table'),
                                                html.P(
                                                    id='fig16a2-category-string',
                                                    children=[
                                                    'Categories with insufficient n-size or no data:',
                                                    html.Span(id='fig16a2-category-string', children='', className = 'category_string'),
                                                    ],
                                                    className = 'category_string_label',
                                                ),
                                                html.P(
                                                    id='fig16a2-school-string',
                                                    children=[
                                                    'Schools with insufficient n-size or no data:',
                                                    html.Span(id='fig16a2-school-string', children='', className = 'school_string'),
                                                    ],
                                                    className = 'school_string_label',
                                                ),                                                                                 
                                            ],
                                            className = 'close_container twelve columns'
                                        )
                                    ],
                                    className='row'
                                ),
                            ],
                            id = 'fig16a2-table-container',
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(id='fig16b2', children=[])
                                    ],
                                    className = 'pretty_close_container twelve columns',
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
                                                html.Div(id='fig16b2-table'),
                                                html.P(
                                                    id='fig16b2-category-string',
                                                    children=[
                                                    'Categories with insufficient n-size or no data:',
                                                    html.Span(id='fig16b2-category-string', children='', className = 'category_string'),
                                                    ],
                                                    className = 'category_string_label',
                                                ),
                                                html.P(
                                                    id='fig16b2-school-string',
                                                    children=[
                                                    'Schools with insufficient n-size or no data:',
                                                    html.Span(id='fig16b2-school-string', children='', className = 'school_string'),
                                                    ],
                                                    className = 'school_string_label',
                                                ),                        
                                            ],
                                            className = 'close_container twelve columns'
                                        ),
                                    ],
                                    className='row'
                                ),
                            ],
                            id = 'fig16b2-table-container',
                        ),
                    ],
                    id = 'academic-analysis-main-container',
                ),
                html.Div(
                    [
                    html.Div(id='academic-analysis-no-data'),
                    ],
                    id = 'academic-analysis-empty-container',
                ),
            ],
            id='mainContainer'
        )