######################################
# ICSB Dashboard - Academic Analysis #
######################################
# author:   jbetley
# version:  1.03
# date:     5/22/23

import dash
from dash import ctx, dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd
import time

# import local functions
from .calculations import find_nearest, filter_grades
from .chart_helpers import no_data_fig_label, make_line_chart,make_bar_chart, make_group_bar_chart, \
    combine_barchart_and_table
from .table_helpers import create_comparison_table, no_data_page, no_data_table, create_school_label, \
    process_chart_data, process_table_data, create_school_label, create_chart_label
from .subnav import subnav_academic
from .load_data import all_academic_data_k8, ethnicity, subgroup, ethnicity, info_categories, \
   process_k8_academic_data, calculate_k8_comparison_metrics, calculate_proficiency #get_attendance_data, process_high_school_academic_data, get_excluded_years, \
    #filter_high_school_academic_data, 
from .load_db import get_k8_school_academic_data, get_school_index, \
    get_school_coordinates, get_comparable_schools, get_k8_corporation_academic_data # get_high_school_academic_data,

dash.register_page(__name__, path = '/academic_analysis', order=6)

# Set options for comparison schools (multi-select dropdown)
@callback(
    Output('comparison-dropdown', 'options'),
    Output('input-warning','children'),
    Output('comparison-dropdown', 'value'),
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    Input('comparison-dropdown', 'value'),
)
def set_dropdown_options(school, year, comparison_schools):
    t0 = time.process_time()
    # clear the list of comparison_schools when a new school is
    # selected (e.g., 'charter-dropdown' Input). otherwise
    # comparison_schools will carry over from school to school
    input_trigger = ctx.triggered_id
    if input_trigger == 'charter-dropdown':
        comparison_schools = []

    selected_school = get_school_index(school)
    selected_school_type = selected_school['School Type'].values[0]

    #prevents HS and AHS from generating a list of comparable schools.
    if (selected_school_type == 'HS' or selected_school_type == 'AHS'):
        return [],[],[]
    
    # Get School ID, School Name, Lat & Lon for all schools in the set for selected year
    schools_by_distance = get_school_coordinates(year)

    # drop schools with no grade overlap with selected school by getting school grade span and filtering
    school_grade_span = schools_by_distance.loc[schools_by_distance['School ID'] == int(school)][['Low Grade','High Grade']].values[0].astype(str).tolist()
    school_grade_span = [s.replace('KG', '1').replace('PK', '0') for s in school_grade_span]
    school_grade_span = [int(i) for i in school_grade_span]

    # ignore PreK(0) and K(1)
    low_bound = 3 if school_grade_span[0] < 3 else school_grade_span[0]
    school_grade_range = list(range(low_bound,(school_grade_span[1]+1)))

    # PK and KG are not tested grades
    schools_by_distance = schools_by_distance.replace({'Low Grade' : { 'PK' : 0, 'KG' : 1}})

    grade_mask = schools_by_distance.apply(filter_grades, compare=school_grade_range, axis=1)
    schools_by_distance = schools_by_distance[grade_mask]
    
    # reset index and make a copy to re-add School Names after distance sort
    schools_by_distance = schools_by_distance.reset_index(drop = True)
    all_schools = schools_by_distance.copy()

    # get school index
    school_idx = schools_by_distance[schools_by_distance['School ID'] == int(school)].index

    # if school doesn't exist in the datafile for some reason dropdown is empty
    if school_idx.size == 0:
        return [],[],[]
    
    # kdtree spatial tree function returns two np arrays: an array of indexes and an array of distances
    index_array, dist_array = find_nearest(school_idx,schools_by_distance)

    index_list = index_array[0].tolist()
    distance_list = dist_array[0].tolist()

    # Match School ID with indexes
    closest_schools = pd.DataFrame()
    closest_schools['School ID'] = schools_by_distance[schools_by_distance.index.isin(index_list)]['School ID']

    # Merge the index and distances lists into a dataframe
    distances = pd.DataFrame({'index':index_list, 'y':distance_list})
    distances = distances.set_index(list(distances)[0])

    # Merge School ID with Distances by index
    combined = closest_schools.join(distances)

    # Merge the original df with the combined distance/SchoolID df (essentially just adding School Name)
    comparison_set = pd.merge(combined, all_schools, on='School ID', how='inner')
    comparison_set = comparison_set.rename(columns = {'y': 'Distance'})
 
    # drop selected school (so it cannot be selected in the dropdown)
    comparison_set = comparison_set.drop(comparison_set[comparison_set['School ID'] == int(school)].index)

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
                {'label': option['label'], 'value': option['value'], 'disabled': True}
                for option in default_options
            ]
    print(f'Time to create dropdown: ' + str(time.process_time() - t0))

    return options, input_warning, comparison_schools

@callback(
    Output('fig14a', 'children'),
    Output('fig14b', 'children'),
    Output('fig14c', 'children'),
    Output('fig14d', 'children'),
    Output('fig-iread', 'children'),
    Output('fig16c1', 'children'),
    Output('fig16d1', 'children'),
    Output('fig16c2', 'children'),
    Output('fig16d2', 'children'),
    Output('fig14g', 'children'),
    Output('dropdown-container', 'style'),
    Output('fig16a1', 'children'),   
    Output('fig16a1-container', 'style'),    
    Output('fig16b1', 'children'),
    Output('fig16b1-container', 'style'),
    Output('fig16a2', 'children'),
    Output('fig16a2-container', 'style'),
    Output('fig16b2', 'children'),
    Output('fig16b2-container', 'style'),
    Output('academic-analysis-main-container', 'style'),
    Output('academic-analysis-empty-container', 'style'),
    Output('academic-analysis-no-data', 'children'),
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    [Input('comparison-dropdown', 'value')],
)
def update_academic_analysis(school, year, comparison_school_list):
    if not school:
        raise PreventUpdate

    selected_year = str(year)

    academic_analysis_main_container = {'display': 'none'}
    academic_analysis_empty_container = {'display': 'none'}
    dropdown_container = {'display': 'none'}
    no_data_to_display = no_data_page('Academic Analysis')

    selected_school = get_school_index(school)
    
    school_name = selected_school['School Name'].values[0]
    
    t1 = time.process_time()
    
    raw_school_data = get_k8_school_academic_data(school)

    # Test if data exists - there are 4 cases where we end up with an empty page:
    #   1)  the dataframe itself does not exist because there is no academic
    #       data for the school at all
    #   2)  the school is of a type (AHS/HS) that doesn't yet have any charted data
    #   3)  the dataframe exists, but the tested_header (YEARSchool) does not exist
    #       in the dataframe- this catches any year with no data (e.g., 2020School
    #       because there is no 2020 data in the dataframe
    #   4)  the tested header does exist, but all data in the column is NaN- this
    #       catches any year where the school has no data or insufficient n-size ('***')
    
    #   Only get to tests (3) and (4) if dataframe passes tests (1) & (2)

    # Testing (1) and (2)
    if (selected_school['School Type'].values[0] == 'K8' and len(raw_school_data.index) == 0) or \
        selected_school['School Type'].values[0] == 'HS' or selected_school['School Type'].values[0] == 'AHS':

        fig14a = fig14b = fig14c = fig14d = fig_iread = fig16c1 = fig16d1 = fig16c2 = fig16d2 = fig14g = {}
        
        fig16a1 = {}
        fig16a1_container = {'display': 'none'}

        fig16b1 = {}
        fig16b1_container = {'display': 'none'}

        fig16a2 = {}
        fig16a2_container = {'display': 'none'}

        fig16b2 = {}
        fig16b2_container = {'display': 'none'}

        academic_analysis_main_container = {'display': 'none'}
        academic_analysis_empty_container = {'display': 'block'}
        dropdown_container = {'display': 'none'}

    else:

        raw_school_data = raw_school_data.replace({"^": "***"})

        # keep only school columns with non-null data.
        valid_column_mask = raw_school_data.any()
      
        raw_school_data = raw_school_data[raw_school_data.columns[valid_column_mask]]

        clean_school_data = process_k8_academic_data(raw_school_data, year, school)

        print(f'Time to load and process K8 data: ' + str(time.process_time() - t1))
        
        t2 = time.process_time()        
        
        raw_comparison_data = calculate_k8_comparison_metrics(clean_school_data, year, school)

        print(f'Time to process comparison metrics: ' + str(time.process_time() - t2))        
        
        tested_header = selected_year + 'School'

        # Testing (3) and (4)
        if tested_header not in raw_comparison_data.columns or \
            raw_comparison_data[tested_header].isnull().all():
            
            fig14a = fig14b = fig14c = fig14d = fig_iread = fig16c1 = fig16d1 = fig16c2 = fig16d2 = fig14g = {}
            
            fig16a1 = {}
            fig16a1_container = {'display': 'none'}

            fig16b1 = {}
            fig16b1_container = {'display': 'none'}

            fig16a2 = {}
            fig16a2_container = {'display': 'none'}

            fig16b2 = {}
            fig16b2_container = {'display': 'none'}

            academic_analysis_main_container = {'display': 'none'}
            academic_analysis_empty_container = {'display': 'block'}
            dropdown_container = {'display': 'none'}

        else:
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None) 
            # Display selected school's year over year data

            # keep only columns with 'Category' or 'School' in name
            school_academic_data = raw_comparison_data[[col for col in raw_comparison_data.columns if 'School' in col or 'Category' in col]].copy()

            school_academic_data.columns = school_academic_data.columns.str.replace(r'School$', '', regex=True)

            # drop any column (Year) where all values are either None or ***
            # '***' represents data, but is unchartable. Do this by converting all
            # columns other than 'Category' to numeric. This turns all None
            # and '***' values to NaN, and then dropping all columns where every
            # value is NaN
            # TODO: This screws up charting tho - because it shows as a break in the line
            ## TODO: Capture '***' and display in tooltip

            school_year_headers = [j for j in school_academic_data.columns if 'Category' not in j]

#TODO: GET INFO AND USE FOR MISSING STRING LINE AT BOTTOM OF CHART

            # insufficient_n_size = np.where(data == '***')
            # pair = list(zip(list(insufficient_n_size[0]),list(insufficient_n_size[1])))
            # print(pair)
            # tst = pd.DataFrame()
            # for (i, j) in pair:
            #     tst['Category'] = data.columns[j]
            #     tst['Year'] = data['Year'][i]
            #     print(f'insufficent data for ' + data.columns[j] + ' in year: ' + data['Year'][i])
                # Leave strings ('***') intact for tracking purposes (see make_line_chart())

            for col in school_year_headers:
                school_academic_data[col] = pd.to_numeric(school_academic_data[col], errors='coerce').fillna(school_academic_data[col])

            school_academic_data = school_academic_data.dropna(axis=1, how='all')

            # transpose the resulting dataframe (making Categories the column headers)
            display_academic_data = school_academic_data.set_index('Category').T.rename_axis('Year').rename_axis(None, axis=1).reset_index()

            # drop any Category where all values are NaN
            display_academic_data = display_academic_data.dropna(axis=1, how='all')

            # add suffix to certain Categories
            display_academic_data = display_academic_data.rename(columns={c: c + ' Proficient %' for c in display_academic_data.columns if c not in ['Year', 'School Name','IREAD Proficiency (Grade 3 only)']})

        ## Make Line Charts

            t3 = time.process_time()   
            yearly_school_data = display_academic_data.copy()
            yearly_school_data['School Name'] = school_name

            # Chart 1: Year over Year ELA Proficiency by Grade (1.4.a)
            fig14a_data = yearly_school_data.filter(regex = r'^Grade \d\|ELA|^School Name$|^Year$',axis=1)
# TODO: Keep strings, track loc of '***' and convert inside line function before charting
            # print(fig14a_data.T)
            # All df contain 'Year' & 'School Name'. So 3rd and beyond categories would be data
            if len(fig14a_data.columns) >= 3:
                fig14a = make_line_chart(fig14a_data,'Year over Year ELA Proficiency by Grade')
            else:
                fig14a = no_data_fig_label('Year over Year ELA Proficiency by Grade', 200)

            # Chart 2: Year over Year Math Proficiency by Grade (1.4.b)
            fig14b_data = yearly_school_data.filter(regex = r'^Grade \d\|Math|^School Name$|^Year$',axis=1)

            if len(fig14b_data.columns) >= 3:
                fig14b = make_line_chart(fig14b_data,'Year over Year Math Proficiency by Grade')
            else:
                fig14b = no_data_fig_label('Year over Year Math Proficiency by Grade', 200)

            # Charts 3 & 4: See below

            # Chart 5: Year over Year ELA Proficiency by Ethnicity (1.6.c)
            categories_16c1 = []
            for e in ethnicity:
                categories_16c1.append(e + '|' + 'ELA Proficient %')

            fig16c1_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16c1)) | (yearly_school_data.columns.isin(['School Name','Year']))]
            fig16c1_data = fig16c1_data.rename(columns = {'Native Hawaiian or Other Pacific Islander|ELA Proficient %': 'Pacific Islander|ELA Proficient %'})
        
            if len(fig16c1_data.columns) >= 3:                
                fig16c1 = make_line_chart(fig16c1_data,'Year over Year ELA Proficiency by Ethnicity')
            else:
                fig16c1 = no_data_fig_label('Year over Year ELA Proficiency by Ethnicity', 200)

            # Chart 6: Year over Year Math Proficiency by Ethnicity (1.6.d)
            categories_16d1 = []
            for e in ethnicity:
                categories_16d1.append(e + '|' + 'Math Proficient %')

            fig16d1_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16d1)) | (yearly_school_data.columns.isin(['School Name','Year']))]
            fig16d1_data = fig16d1_data.rename(columns = {'Native Hawaiian or Other Pacific Islander|Math Proficient %': 'Pacific Islander|Math Proficient %'})
            
            if len(fig16d1_data.columns) >= 3:   
                fig16d1 = make_line_chart(fig16d1_data,'Year over Year Math Proficiency by Ethnicity')
            else:
                fig16d1 = no_data_fig_label('Year over Year Math Proficiency by Ethnicity', 200)

            # Chart 7: Year over Year ELA Proficiency by Subgroup (1.6.c)
            categories_16c2 = []
            for s in subgroup:
                categories_16c2.append(s + '|' + 'ELA Proficient %')

            fig16c2_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16c2)) | (yearly_school_data.columns.isin(['School Name','Year']))]
            
            if len(fig16c2_data.columns) >= 3:   
                fig16c2 = make_line_chart(fig16c2_data,'Year over Year ELA Proficiency by Subgroup')
            else:
                fig16c2 = no_data_fig_label('Year over Year ELA Proficiency by Subgroup', 200)

            # Chart 8: Year over Year Math Proficiency by Subgroup (1.6.d)
            categories_16d2 = []
            for s in subgroup:
                categories_16d2.append(s + '|' + 'Math Proficient %')

            fig16d2_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16d2)) | (yearly_school_data.columns.isin(['School Name','Year']))]
            
            if len(fig16d2_data.columns) >= 3:                   
                fig16d2 = make_line_chart(fig16d2_data,'Year over Year Math Proficiency by Subgroup')
            else:
                fig16d2 = no_data_fig_label('Year over Year Math Proficiency by Subgroup', 200)

            # Chart 9 - IREAD Year over Year
            category_iread = 'IREAD Proficiency (Grade 3 only)'

            fig14g_data = yearly_school_data.loc[:, (yearly_school_data.columns == category_iread) | (yearly_school_data.columns.isin(['School Name','Year']))]

            if len(fig14g_data.columns) >= 3:                
                fig14g = make_line_chart(fig14g_data, category_iread)
            else:
                fig14g = no_data_fig_label('Year over Year IREAD Proficiency', 200)

            print(f'Time to make line charts: ' + str(time.process_time() - t3))

            ## Current School Data ##
            # Get current year school data
            current_school_data = display_academic_data.loc[display_academic_data['Year'] == selected_year].copy()

            # COvnert '***' strings to NaN
            for col in current_school_data.columns:
                current_school_data[col]=pd.to_numeric(current_school_data[col], errors='coerce')

            # drop any Category where value is NaN
            current_school_data = current_school_data.dropna(axis=1, how='all')

            current_school_data['School Name'] = school_name

            # Grade range data is used for the chart 'hovertemplate'
            current_school_data['Low Grade'] = all_academic_data_k8.loc[(all_academic_data_k8['School ID'] == school) & (all_academic_data_k8['Year'] == selected_year)]['Low Grade'].values[0]
            current_school_data['High Grade'] = all_academic_data_k8.loc[(all_academic_data_k8['School ID'] == school) & (all_academic_data_k8['Year'] == selected_year)]['High Grade'].values[0]

            t4 = time.process_time()

            raw_corp_data = get_k8_corporation_academic_data(school)
            school_corporation_name = raw_corp_data['Corporation Name'].values[0]

            raw_corp_data = raw_corp_data.loc[raw_corp_data['Year'] == int(selected_year)]

            for col in raw_corp_data.columns:
                raw_corp_data[col]=pd.to_numeric(raw_corp_data[col], errors='coerce')

            corp_current_data = process_k8_academic_data(raw_corp_data, year, school)
            corp_current_data.loc[corp_current_data['Category'] == 'IREAD Pass %', 'Category'] = 'IREAD Proficiency (Grade 3 only)'

            # Re-transpose the corp df to get the Categories back to column headers
            corp_current_data = (
                corp_current_data.set_index("Category")
                .T.rename_axis("Year")
                .rename_axis(None, axis=1)
                .reset_index()
            )

            print(f'Time to get and process corp data: ' + str(time.process_time() - t4))

            # get academic data for comparison schools
            t5 = time.process_time()

            comparison_schools_filtered = get_comparable_schools(comparison_school_list, year)

            comparison_schools_filtered = comparison_schools_filtered.filter(regex = r'Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year|School Name|School ID|Distance|Low Grade|High Grade',axis=1)

            # create list of columns with no data (used in loop below)
            comparison_schools_info = comparison_schools_filtered[['School Name','Low Grade','High Grade']].copy()            
            comparison_schools_filtered = comparison_schools_filtered.drop(['School ID','School Name','Low Grade','High Grade'], axis=1)

            # change values to numeric
            for col in comparison_schools_filtered.columns:
                comparison_schools_filtered[col] = pd.to_numeric(comparison_schools_filtered[col], errors='coerce')

            comparison_schools = calculate_proficiency(comparison_schools_filtered)

            # NOTE: The masking step above removes grades from the comparison dataframe that are
            # not also in the school dataframe (e.g., if school only has data for grades 3, 4, & 5,
            # only those grades will remain in comparison df). However, the 'School Total' for
            # proficiency in a subject that is in the raw data was calculated using ALL grades.
            # So we need to recalculate the 'School Total' rate manually to ensure it includes only the included grades.
            all_grades_math_proficient_comp = comparison_schools.filter(regex=r'Grade.+?Math Total Proficient')
            all_grades_math_tested_comp = comparison_schools.filter(regex=r'Grade.+?Math Total Tested')
            comparison_schools['Total|Math Proficient %'] = all_grades_math_proficient_comp.sum(axis=1) / all_grades_math_tested_comp.sum(axis=1)

            all_grades_ela_proficient_comp = comparison_schools.filter(regex=r'Grade.+?ELA Total Proficient')
            all_grades_ela_tested_comp = comparison_schools.filter(regex=r'Grade.+?ELA Total Tested')

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
            print(f'Time to get and process comparison data: ' + str(time.process_time() - t5))
### TODO: Add AHS/HS Data ###
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
            
            t6 = time.process_time()
            #### Current Year ELA Proficiency Compared to Similar Schools (1.4.c) #
            category = 'School Total|ELA Proficient %'

            # Get school value for specific category
            if category in current_school_data.columns:

                fig14c_k8_school_data = current_school_data[info_categories + [category]].copy()

                # TODO: corp_current_data is missing the ' Proficient %' - may want to fix one of these days (?)

                # add corp average for category to dataframe - the '','','N/A' are values for
                # Low & High Grade and Distance columns
                fig14c_k8_school_data.loc[len(fig14c_k8_school_data.index)] = \
                    [school_corporation_name,'3','8',corp_current_data[category].values[0]]

                # Get comparable school values for the specific category

                fig14c_comp_data = comparison_schools[info_categories + [category]]

                # Combine data, fix dtypes, and send to chart function
                fig14c_all_data = pd.concat([fig14c_k8_school_data,fig14c_comp_data])

                # save table data
                fig14c_table_data = fig14c_all_data.copy()

                # convert datatypes
                fig14c_all_data[category] = pd.to_numeric(fig14c_all_data[category])

                # make the bar chart
                fig14c_chart = make_bar_chart(fig14c_all_data, category, school_name, 'Comparison: Current Year ELA Proficiency')

                fig14c_table_data['School Name'] = create_school_label(fig14c_table_data)

                fig14c_table_data = fig14c_table_data[['School Name', category]]
                fig14c_table_data = fig14c_table_data.reset_index(drop=True)

                fig14c_table = create_comparison_table(fig14c_table_data, school_name,'Proficiency')

            else:
                # NOTE: This should never ever happen. So it's critical that we expect it to.
                fig14c_chart = no_data_fig_label('Comparison: Current Year ELA Proficiency',200)
                fig14c_table = no_data_table('Proficiency')

            fig14c = combine_barchart_and_table(fig14c_chart,fig14c_table)

        #### Current Year Math Proficiency Compared to Similar Schools (1.4.d) #
            category = 'School Total|Math Proficient %'

            if category in current_school_data.columns:

                fig14d_k8_school_data = current_school_data[info_categories + [category]].copy()

                # TODO: corp_current_data is missing the ' Proficient %' - may want to fix one of these days (?)

                # add corp average for category to dataframe - the '','','N/A' are values for
                # Low & High Grade and Distance columns
                fig14d_k8_school_data.loc[len(fig14d_k8_school_data.index)] = \
                    [school_corporation_name, '3','8',corp_current_data[category].values[0]]

                # Get comparable school values for the specific category
                fig14d_comp_data = comparison_schools[info_categories + [category]]
                # fig14d_comp_data = comparison_schools[['School Name','Low Grade','High Grade','Distance',category]]

                fig14d_all_data = pd.concat([fig14d_k8_school_data,fig14d_comp_data])

                # save table data
                fig14d_table_data = fig14d_all_data.copy()

                fig14d_all_data[category] = pd.to_numeric(fig14d_all_data[category])

                fig14d_chart = make_bar_chart(fig14d_all_data,category, school_name, 'Comparison: Current Year Math Proficiency')

                # Math Proficiency table
                fig14d_table_data['School Name'] = create_school_label(fig14d_table_data)
                
                fig14d_table_data = fig14d_table_data[['School Name', category]]
                fig14d_table_data = fig14d_table_data.reset_index(drop=True)

                fig14d_table = create_comparison_table(fig14d_table_data, school_name, 'Proficiency')
            else:
                fig14d_chart = no_data_fig_label('Comparison: Current Year Math Proficiency',200)
                fig14d_table = no_data_table('Proficiency')

            fig14d = combine_barchart_and_table(fig14d_chart,fig14d_table)


            #### Current Year IREAD Proficiency Compared to Similar Schools #
            category = 'IREAD Proficiency (Grade 3 only)'

            if category in current_school_data.columns:

                fig_iread_k8_school_data = current_school_data[info_categories + [category]].copy()

                # add corp average for category to dataframe - the '','','N/A' are values for
                # Low & High Grade and Distance columns
                fig_iread_k8_school_data.loc[len(fig_iread_k8_school_data.index)] = \
                    [school_corporation_name, '3','8',corp_current_data[category].values[0]]
                
                # Get comparable school values for the specific category
                fig_iread_comp_data = comparison_schools[info_categories + [category]]
                # fig_iread_comp_data = comparison_schools[['School Name','Low Grade','High Grade','Distance',category]]

                fig_iread_all_data = pd.concat([fig_iread_k8_school_data,fig_iread_comp_data])
                # save table data
                fig_iread_table_data = fig_iread_all_data.copy()

                fig_iread_all_data[category] = pd.to_numeric(fig_iread_all_data[category])

                fig_iread_chart = make_bar_chart(fig_iread_all_data,category, school_name, 'Comparison: Current Year IREAD Proficiency')

                # Math Proficiency table
                fig_iread_table_data['School Name'] = create_school_label(fig_iread_table_data)

                fig_iread_table_data = fig_iread_table_data[['School Name', category]]
                fig_iread_table_data = fig_iread_table_data.reset_index(drop=True)

                fig_iread_table = create_comparison_table(fig_iread_table_data, school_name, 'Proficiency')
            else:
                fig_iread_chart = no_data_fig_label('Comparison: Current Year IREAD Proficiency',200)
                fig_iread_table = no_data_table('Proficiency')

            fig_iread = combine_barchart_and_table(fig_iread_chart,fig_iread_table)

            print(f'Time to make single subject bar charts: ' + str(time.process_time() - t6))

            def combine_group_barchart_and_table(fig,table,category_string,school_string):
                layout = [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(fig, style={'marginBottom': '-20px'})
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
                                    html.Div(table),
                                    html.P(
                                        children=[
                                        'Categories with no data to display:',
                                        html.Span(category_string, className = 'category_string'),
                                        ],
                                        className = 'category_string_label',
                                    ),
                                    html.P(
                                        children=[
                                        'School Categories with insufficient n-size or no data:',
                                        html.Span(school_string, className = 'school_string'),
                                        ],
                                        className = 'school_string_label',
                                    ),
                                ],
                                className = 'close_container twelve columns'
                            )
                            ],
                            className='row'
                        )
                ]
                return layout

            t7 = time.process_time()
# TODO: Why not process all categories for school, comparison schools, and corp at once and then just slice them
# TODO: up instead of running the process_chart_data function over and over again on the same dataframes?
            # ELA Proficiency by Ethnicity Compared to Similar Schools (1.6.a.1)
            headers_16a1 = []
            for e in ethnicity:
                headers_16a1.append(e + '|' + 'ELA Proficient %')

            categories_16a1 =  info_categories + headers_16a1

            # filter dataframe by categories
            fig16a1_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16a1))]

            # process_chart_data(fig16a1_k8_school_data, corp_current_data, comparison_schools, headers_16a1, school_corporation_name)
            if len(fig16a1_k8_school_data.columns) > 3:
                
                fig16a1_final_data, fig16a1_category_string, fig16a1_school_string = \
                    process_chart_data(fig16a1_k8_school_data, corp_current_data, comparison_schools, headers_16a1, school_corporation_name)
                fig16a1_label = create_chart_label(fig16a1_final_data)
                fig16a1_chart = make_group_bar_chart(fig16a1_final_data, school_name, fig16a1_label)
                fig16a1_table_data = process_table_data(fig16a1_final_data)
                fig16a1_table = create_comparison_table(fig16a1_table_data, school_name,'')

                fig16a1 = combine_group_barchart_and_table(fig16a1_chart,fig16a1_table,fig16a1_category_string,fig16a1_school_string)
                
                fig16a1_container = {'display': 'block'}
                dropdown_container={'display': 'block'}
            else:
                fig16a1 = no_data_fig_label('Comparison: ELA Proficiency by Ethnicity', 200)             
                fig16a1_container = {'display': 'none'}

            # Math Proficiency by Ethnicity Compared to Similar Schools (1.6.b.1)
            headers_16b1 = []
            for e in ethnicity:
                headers_16b1.append(e + '|' + 'Math Proficient %')

            categories_16b1 =  info_categories + headers_16b1

            # filter dataframe by categories
            fig16b1_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16b1))]

            if len(fig16b1_k8_school_data.columns) > 3:
                
                fig16b1_final_data, fig16b1_category_string, fig16b1_school_string = \
                    process_chart_data(fig16b1_k8_school_data, corp_current_data, comparison_schools, headers_16b1, school_corporation_name)
                fig16b1_label = create_chart_label(fig16b1_final_data)
                fig16b1_chart = make_group_bar_chart(fig16b1_final_data, school_name, fig16b1_label)
                fig16b1_table_data = process_table_data(fig16b1_final_data)
                fig16b1_table = create_comparison_table(fig16b1_table_data, school_name,'')

                fig16b1 = combine_group_barchart_and_table(fig16b1_chart,fig16b1_table,fig16b1_category_string,fig16b1_school_string)

                fig16b1_container = {'display': 'block'}
                dropdown_container={'display': 'block'}                   
            else:
                fig16b1 = no_data_fig_label('Comparison: Math Proficiency by Ethnicity', 200)
             
                fig16b1_container = {'display': 'none'}

            # ELA Proficiency by Subgroup Compared to Similar Schools (1.6.a.2)
            headers_16a2 = []
            for s in subgroup:
                headers_16a2.append(s + '|' + 'ELA Proficient %')
            
            categories_16a2 =  info_categories + headers_16a2

            # filter dataframe by categories
            fig16a2_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16a2))]

            if len(fig16a2_k8_school_data.columns) > 3:
    
                fig16a2_final_data, fig16a2_category_string, fig16a2_school_string = \
                    process_chart_data(fig16a2_k8_school_data, corp_current_data, comparison_schools, headers_16a2, school_corporation_name)
                fig16a2_label = create_chart_label(fig16a2_final_data)
                fig16a2_chart = make_group_bar_chart(fig16a2_final_data, school_name, fig16a2_label)
                fig16a2_table_data = process_table_data(fig16a2_final_data)
                fig16a2_table = create_comparison_table(fig16a2_table_data, school_name,'')
                
                fig16a2 = combine_group_barchart_and_table(fig16a2_chart, fig16a2_table,fig16a2_category_string,fig16a2_school_string)
                fig16a2_container = {'display': 'block'}
                dropdown_container={'display': 'block'}                
            else:
                fig16a2 = no_data_fig_label('Comparison: ELA Proficiency by Subgroup', 200)                
                fig16a2_container = {'display': 'none'}

            # Math Proficiency by Subgroup Compared to Similar Schools (1.6.b.2)
            headers_16b2 = []
            for s in subgroup:
                headers_16b2.append(s + '|' + 'Math Proficient %')

            categories_16b2 =  info_categories + headers_16b2

            # filter dataframe by categories
            fig16b2_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16b2))]

            if len(fig16b2_k8_school_data.columns) > 3:

                fig16b2_final_data, fig16b2_category_string, fig16b2_school_string = \
                    process_chart_data(fig16b2_k8_school_data, corp_current_data, comparison_schools, headers_16b2, school_corporation_name)
                fig16b2_label = create_chart_label(fig16b2_final_data)
                fig16b2_chart = make_group_bar_chart(fig16b2_final_data, school_name, fig16b2_label)
                fig16b2_table_data = process_table_data(fig16b2_final_data)
                fig16b2_table = create_comparison_table(fig16b2_table_data, school_name,'')

                fig16b2 = combine_group_barchart_and_table(fig16b2_chart, fig16b2_table,fig16b2_category_string,fig16b2_school_string)
                fig16b2_container = {'display': 'block'}
                dropdown_container={'display': 'block'}
            else:
                fig16b2 = no_data_fig_label('Comparison: Math Proficiency by Subgroup', 200)            
                fig16b2_container = {'display': 'none'}
    
            print(f'Time to make multibar comparison charts: ' + str(time.process_time() - t7))
    academic_analysis_main_container = {'display': 'block'}

    return fig14a, fig14b, fig14c, fig14d, fig_iread, \
        fig16c1, fig16d1, fig16c2, fig16d2, fig14g, dropdown_container, fig16a1, fig16a1_container, \
        fig16b1, fig16b1_container, fig16a2, fig16a2_container, fig16b2, fig16b2_container, \
        academic_analysis_main_container, academic_analysis_empty_container, no_data_to_display

def layout():
    layout = html.Div(
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
                                            ],
                                            id='dropdown-container',
                                            style= {'display': 'none'},
                                        ),                                         
                                        html.Div(id='fig14c', children=[]),
                                        html.Div(id='fig14d', children=[]),
                                        html.Div(id='fig-iread', children=[]),
                                        html.Div(
                                            [
                                                html.Div(id='fig16a1'),
                                            ],
                                            id = 'fig16a1-container',
                                            style= {'display': 'none'},
                                        ),
                                        html.Div(
                                            [
                                                html.Div(id='fig16b1'),
                                            ],
                                            id = 'fig16b1-container',
                                            style= {'display': 'none'},
                                        ),
                                        html.Div(
                                            [      
                                        html.Div(id='fig16a2'),
                                            ],
                                            id = 'fig16a2-container',
                                            style= {'display': 'none'},
                                        ),                                 
                                        html.Div(
                                            [                        
                                                html.Div(id='fig16b2'),
                                            ],
                                            id = 'fig16b2-container',
                                            style= {'display': 'none'},
                                        ),
                                    ],
                                    id = 'academic-analysis-main-container',
                                    style= {'display': 'none'}, 
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
    return layout             