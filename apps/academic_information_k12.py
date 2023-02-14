######################################
# Academic Information - K12 Schools #
######################################
# author:   jbetley
# rev:     08.15.22
## NOTE: We are using pandas to build lots of dash datatables, so there is some funky ass fiddly dataframe manipulation
## shit required get everything aligned and in the order that we want it.

from dash import html, dash_table, Input, Output
from dash.exceptions import PreventUpdate
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign
import pandas as pd
import numpy as np

from app import app
# np.warnings.filterwarnings('ignore')

## Build Page based on Dropdown Value ##
@app.callback(
    Output('k8-grade-table', 'children'),
    Output('k8-ethnicity-table', 'children'),
    Output('k8-status-table', 'children'),
    Output('k8-other-table', 'children'),
    Output('k8-table-container', 'style'),
    Output('hs-grad-overview-table', 'children'),    
    Output('hs-grad-ethnicity-table', 'children'),
    Output('hs-grad-status-table', 'children'),
    Output('hs-eca-table', 'children'),
    Output('hs-other-data-table', 'children'),
    Output('hs-table-container', 'style'),
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    Input('dash-session', 'data')
)
def update_acadinfo_page(school, year, data):
    if not school:
        raise PreventUpdate

    # Category Variables
    # removed 'American Indiana' because it doesn't appear in the data set
    #ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
    ethnicity = ['Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
    status = ['Special Education','General Education','Paid Meals','Free/Reduced Price Meals','English Language Learners','Non-English Language Learners']
    grades = ['Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8','School Total','IREAD Pass %']

    school_index = pd.DataFrame.from_dict(data['0'])

    # Data is passed through dcc.store as dict of dicts
    # data['1'] = k8 data for selected school
    # data['2'] = k8 data for similar schools for current year
    # data['4'] = HS data for selected school
    # data['5'] = HS data for similar schools

    if school_index['School Type'].values[0] == 'K8' or school_index['School Type'].values[0] == 'K12':

        school_dataK8 = pd.DataFrame.from_dict(data['2'])  # 3-8 academic data for school (from dcc.store)
        corp_dataK8 = pd.DataFrame.from_dict(data['3'])    # 3-8 academic data for traditional public schools in same school corporation
       
    if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'AHS' or school_index['School Type'].values[0] == 'K12':
        school_dataHS = pd.DataFrame.from_dict(data['5'])     # hs academic data for school
        corp_dataHS = pd.DataFrame.from_dict(data['6'])      # hs academic data for schools in same school corporation

    # the school_type determines which table to display - default is display both
    k8_table_container = hs_table_container = {}

    # if school type is K8 and there is no data in dataframe, hide all tables and return a single table with 'No Data' message
    if school_index['School Type'].values[0] == 'K8' and len(school_dataK8.index) == 0:

        #k8_grade_table = k8_ethnicity_table = k8_status_table = k8_other_table = []
        #k8_table_container = {'display': 'none'}
        
        hs_grad_overview_table = hs_grad_ethnicity_table = hs_grad_status_table = hs_eca_table = hs_other_data_table = []
        hs_table_container = {'display': 'none'}

        k8_grade_table = k8_ethnicity_table = k8_status_table = k8_other_table = [
            dash_table.DataTable(
                columns = [
                    {'id': 'emptytable', 'name': 'No Data to Display'},
                ],
                style_header={
                    'fontSize': '14px',
                    'border': 'none',
                    'textAlign': 'center',
                    'color': '#6783a9',
                    'fontFamily': 'Open Sans, sans-serif',
                },
            )
        ]

    else:
        
        ## K8 Data Table ##
        if school_index['School Type'].values[0] == 'K8' or school_index['School Type'].values[0] == 'K12':

        # Build tables with k8 data (this could be for either a k8 school or the k8 part of a k12 school)
        # NOTE: there is no 2020 data for k8 schools, in the event 2020 is selected, 2019 data is displayed

            # if K8, hide HS table
            if school_index['School Type'].values[0] == 'K8':
                hs_grad_overview_table = hs_grad_ethnicity_table = hs_grad_status_table = hs_eca_table = hs_other_data_table = []
                hs_table_container = {'display': 'none'}

            num_years = len(school_dataK8.index)

            k8_corp_data = corp_dataK8.copy()
            k8_school_data = school_dataK8.copy()
        
            # transpose dataframes and clean headers
            k8_school_data = k8_school_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
            k8_school_data = k8_school_data.iloc[:,:(num_years+1)]     # Keep category and all available years of data

            k8_corp_data = k8_corp_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
            k8_corp_data = k8_corp_data.iloc[:,:(num_years+1)]     # Keep category and all available years of data

            # Drop State/Federal grade rows from school_data (used in 'about' tab, but not here)
            k8_school_data = k8_school_data[k8_school_data['Category'].str.contains('State Grade|Federal Rating|School Name') == False]
            k8_school_data = k8_school_data.reset_index(drop=True)

            # reverse order of corp_data columns (ignoring 'Category') so current year is first 
            k8_corp_data = k8_corp_data[list(k8_corp_data.columns[:1]) + list(k8_corp_data.columns[:0:-1])]

            # get clean list of years
            year_cols = list(k8_school_data.columns[:0:-1])
            year_cols.reverse()

            # add_suffix is applied to entire df. To hide columns we dont want renamed, set them as index and reset back after renaming.
            k8_corp_data = k8_corp_data.set_index(['Category']).add_suffix('Corp Avg').reset_index()
            k8_school_data = k8_school_data.set_index(['Category']).add_suffix('School').reset_index()

            # Create list of alternating columns by year (School Value/Similar School Value)
            school_cols = list(k8_school_data.columns[:0:-1])
            school_cols.reverse()
            
            corp_cols = list(k8_corp_data.columns[:0:-1])
            corp_cols.reverse()

            result_cols = [str(s) + '+/-' for s in year_cols]
            
            import itertools
            final_cols = list(itertools.chain(*zip(school_cols, corp_cols, result_cols)))
            final_cols.insert(0,'Category')

            merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
            merged_cols.insert(0,'Category')
            merged_data = k8_school_data.merge(k8_corp_data, on ='Category', how='left')
            merged_data = merged_data[merged_cols]

            tmp_category = k8_school_data['Category']

            # temporarily drop 'Category' column to simplify calculating difference
            k8_school_data.drop('Category', inplace=True, axis=1)
            k8_corp_data.drop('Category', inplace=True, axis=1)

            # calculate difference between two dataframes
            result = pd.DataFrame(k8_school_data.values - k8_corp_data.values)

            # add headers
            result.set_axis(result_cols, axis=1,inplace=True)
            result.insert(loc=0,column='Category',value = tmp_category)
        
            final_data = merged_data.merge(result, on ='Category', how='left')
            final_data = final_data[final_cols]

            # drop 'Proficient %' from all 'Category' rows and remove whitespace
            final_data['Category'] = final_data['Category'].str.replace('Proficient %', '').str.strip()
            
            # rename IREAD Category
            final_data.loc[final_data['Category'] == 'IREAD Pass %', 'Category'] = 'IREAD Proficiency (Grade 3 only)'
            
            # Clean up for display
            # for each category:
            # if '[year]School' < 0:  '[year]School' = '***' & '[year]+/-' = '***'
            # if '[year]School' = NaN: '[year]School' = '', '[year]Corp Avg' = '', '' & '[year]+/-' = '***'

            # simple loop to: 1) replace negative values in school column with '***', 2) replace any value with '***' values
            # in '+/-' column if school column is '***'; and 3) NaN in both 'Corp Avg' & '+/-' columns if School column is NaN
            for y in year_cols:
                final_data[str(y) + 'School'] = np.where(final_data[str(y) + 'School'] < 0,'***', final_data[str(y) + 'School'])
                final_data[str(y) + '+/-'] = np.where(final_data[str(y) + 'School'] == '***','***', final_data[str(y) + '+/-'])
                final_data[str(y) + 'Corp Avg'] = np.where(final_data[str(y) + 'School'].isnull(), final_data[str(y) + 'School'], final_data[str(y) + 'Corp Avg'])

            # group rows by 'category' - must match by string because df may not have same status or ethnicity sub-categories
            years_by_grade = final_data[final_data['Category'].str.contains('|'.join(grades))]
            years_by_status = final_data[final_data['Category'].str.contains('|'.join(status))]
            years_by_ethnicity = final_data[final_data['Category'].str.contains('|'.join(ethnicity))]

        ## Other Academic Data Table (missing metrics)
            other_academic_data = [
                {'Category': 'Attendance Rate', 'CY': 'N/A', 'PY': 'N/A', 'Change': 'N/A', 'Similar Schools': 'N/A', 'Difference': 'N/A'},
                {'Category': 'Teacher Retention Rate', 'CY': 'N/A', 'PY': 'N/A', 'Change': 'N/A', 'Similar Schools': 'N/A', 'Difference': 'N/A'},
                {'Category': 'Student Re-Enrollment Rate (EoY to BoY)', 'CY': 'N/A', 'PY': 'N/A', 'Change': 'N/A', 'Similar Schools': 'N/A', 'Difference': 'N/A'},
                {'Category': 'Student Re-Enrollment Rate (YoY)', 'CY': 'N/A', 'PY': 'N/A', 'Change': 'N/A', 'Similar Schools': 'N/A', 'Difference': 'N/A'},
                {'Category': 'Two Year Students Grade Level Proficiency (ELA)', 'CY': 'N/A', 'PY': 'N/A', 'Change': 'N/A', 'Similar Schools': 'N/A', 'Difference': 'N/A'},
                {'Category': 'Two Year Students Grade Level Proficiency (Math)', 'CY': 'N/A', 'PY': 'N/A', 'Change': 'N/A', 'Similar Schools': 'N/A', 'Difference': 'N/A'},
                {'Category': 'Typical or High Growth ELA', 'CY': 'N/A', 'PY': 'N/A', 'Change': 'N/A', 'Similar Schools': 'N/A', 'Difference': 'N/A'},
                {'Category': 'Typical or High Growth Math', 'CY': 'N/A', 'PY': 'N/A', 'Change': 'N/A', 'Similar Schools': 'N/A', 'Difference': 'N/A'},
                {'Category': 'Adequate and Sufficient Growth ELA', 'CY': 'N/A', 'PY': 'N/A', 'Change': 'N/A', 'Similar Schools': 'N/A', 'Difference': 'N/A'},
                {'Category': 'Adequate and Sufficient Growth Math', 'CY': 'N/A', 'PY': 'N/A', 'Change': 'N/A', 'Similar Schools': 'N/A', 'Difference': 'N/A'},
            ]

    #### Tables
        ## Prepare table columns

            # get list of dataframe columns (used as index to identify columns in table)
            idx_cols = final_data.columns.tolist()

            # get list of +/- columns (used by datatable filter_query' to ID columns for color formatting)
            format_cols = [k for k in idx_cols if '+/-' in k]

            # create list of display columns
            # in order to use datatables multi-level headers, need to split the 'name' prop into a list of two strings:
            # top-level: Year, 2nd level: Descriptor(School, Corp Avg, +/-)
            # we do this by iterating through column idx list and splitting the column idx name after the 4th character
            # we 'check' each item to make sure it starts with '20' (the first two digits of the year) and then
            # use slicing to get first 4 characters and all remaining characters
            # https://stackoverflow.com/questions/70020608/plotly-dash-datatable-how-create-multi-headers-table-from-pandas-multi-headers
            # https://stackoverflow.com/questions/69642786/multilevel-dataframe-to-dash-table

            name_cols = [['Category','']]
            
            for item in idx_cols:
                if item.startswith('20'):
                    name_cols.append([item[:4],item[4:]])

            # use columns to build school column dict
            # example result (dict):
            #   {"name": ["Category"], "id": "Category"},
            #   {"name": ["2021","School"], "id": "2021School"},
            #   {"name": ["2021","Corp Avg"], "id": "2021CorpAvg"},
            #   {"name": ["2021","+/-"], "id": "2021+/-"},
            #   .....
            
            k12_table_columns = [
                {
                    'name': col,
                    'id': idx_cols[idx],
                    'type':'numeric',
                    'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
                    } for (idx, col) in enumerate(name_cols)
            ]

            # default table styles
            table_style = {
                'fontSize': '11px',
                'fontFamily': 'Roboto, sans-serif',
                'border': 'none'
            }

            table_header = {
                'backgroundColor': '#ffffff',
                'fontSize': '11px',
                'fontFamily': 'Roboto, sans-serif',
                'color': '#6783a9',
                'textAlign': 'center',
                'fontWeight': 'bold'            
            }

            table_cell = {
                'whiteSpace': 'normal',
        #           'height': 'auto',
                'textAlign': 'center',
                'color': '#6783a9',
                'boxShadow': '0 0',
                'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
            }

            k12_table_data_conditional = [
                {
                    'if': {
                        'row_index': 'odd'
                    },
                    'backgroundColor': '#eeeeee'
                }
            ] + [
                {
                    'if': {
                        'filter_query': '{{{col}}} < 0'.format(col=col),
                        'column_id': col
                    },
                    'fontWeight': 'bold',
                    'color': '#b44655',
                    'fontSize': '10px',
                } for col in format_cols
            ] + [
                {
                    'if': {
                        'filter_query': '{{{col}}} > 0'.format(col=col),
                        'column_id': col
                    },
                    'fontWeight': 'bold',
                    'color': '#81b446',
                    'fontSize': '10px',
                } for col in format_cols
            ]

        ## Create Tables

            k8_grade_table = [
                        dash_table.DataTable(
                            years_by_grade.to_dict('records'),
                            columns = k12_table_columns,
                            style_data = table_style,
                            style_data_conditional = k12_table_data_conditional,
                            style_header = table_header,
                            style_cell = table_cell,
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '10px',
                                    'width': '35%'
                                }
                            ],
                            merge_duplicate_headers=True,
                            style_as_list_view=True
                        )
            ]

            k8_ethnicity_table = [
                        dash_table.DataTable(
                            years_by_ethnicity.to_dict('records'),
                            columns = k12_table_columns,
                            style_data = table_style,
                            style_data_conditional = k12_table_data_conditional,
                            style_header = table_header,
                            style_cell = table_cell,
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '10px',
                                    'width': '35%'
                                }
                            ],
                            merge_duplicate_headers=True,
                            style_as_list_view=True
                        )
            ]

            k8_status_table = [
                        dash_table.DataTable(
                            years_by_status.to_dict('records'),
                            columns = k12_table_columns,
                            style_data = table_style,
                            style_data_conditional = k12_table_data_conditional,
                            style_header = table_header,
                            style_cell = table_cell,
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '10px',
                                    'width': '35%'
                                }
                            ],
                            merge_duplicate_headers=True,
                            style_as_list_view=True
                        )
            ]

            other_academic_data_columns = ['Category','CY','PY','Change','Similar Schools','Difference']

            k8_other_table = [
                        dash_table.DataTable(
                            other_academic_data,
                            columns = [{'name': i, 'id': i} for i in other_academic_data_columns],
                            style_data = table_style,
                            style_data_conditional = k12_table_data_conditional,
                            style_header = table_header,
                            style_cell = table_cell,
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '10px',
                                    'width': '40%'
                                },
                            ],
                            style_as_list_view=True
                        )
            ]

        ## High School (Grad Rate and ECA) Data ##
        if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'AHS' or school_index['School Type'].values[0] == 'K12':

            # if HS or AHS, hide K8 table
            if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'AHS':
                k8_grade_table = k8_ethnicity_table = k8_status_table = k8_other_table = []
                k8_table_container = {'display': 'none'}

            if len(school_dataHS.index) == 0:
                hs_grad_overview_table = hs_grad_ethnicity_table = hs_grad_status_table = hs_eca_table = hs_other_data_table = [
                    dash_table.DataTable(
                        columns = [
                            {'id': 'emptytable', 'name': 'No Data to Display'},
                        ],
                        style_header={
                            'fontSize': '14px',
                            'border': 'none',
                            'textAlign': 'center',
                            'color': '#6783a9',
                            'fontFamily': 'Open Sans, sans-serif',
                        },
                    )
                ]

            else:

                num_years = len(school_dataHS.index)        
            
            ### Graduation Rates

                hs_corp_data = corp_dataHS.copy()
                hs_school_data = school_dataHS.copy()
            
                # transpose dataframes and clean headers
                hs_school_data = hs_school_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
                hs_school_data = hs_school_data.iloc[:,:(num_years+1)]     # Keep category and all available years of data

                hs_corp_data = hs_corp_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
                hs_corp_data = hs_corp_data.iloc[:,:(num_years+1)]     # Keep category and all available years of data

                # Drop State/Federal grade rows from school_data (used in 'about' tab, but not here)
                hs_school_data = hs_school_data[hs_school_data['Category'].str.contains('State Grade|Federal Rating|School Name') == False]
                hs_school_data = hs_school_data.reset_index(drop=True)

                # get clean list of years
                year_cols = list(hs_school_data.columns[:0:-1])
                year_cols.reverse()

                # add_suffix is applied to entire df. To hide columns we dont want renamed, set them as index and reset back after renaming.
                hs_corp_data = hs_corp_data.set_index(['Category']).add_suffix('Corp Avg').reset_index()
                hs_school_data = hs_school_data.set_index(['Category']).add_suffix('School').reset_index()

                # Create list of alternating columns by year (School Value/Similar School Value)
                school_cols = list(hs_school_data.columns[:0:-1])
                school_cols.reverse()
                
                corp_cols = list(hs_corp_data.columns[:0:-1])
                corp_cols.reverse()

                result_cols = [str(s) + '+/-' for s in year_cols]
                
                import itertools
                final_cols = list(itertools.chain(*zip(school_cols, corp_cols, result_cols)))
                final_cols.insert(0,'Category')

                merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
                merged_cols.insert(0,'Category')
                hs_merged_data = hs_school_data.merge(hs_corp_data, on ='Category', how='left')
                hs_merged_data = hs_merged_data[merged_cols]

                tmp_category = hs_school_data['Category']

## TODO: DO AHS EVEN HAVE GEOCORPS? IS IT RIGHT TO COMPARE THEM? I WOULD SAY NO
                
                # temporarily drop 'Category' column to simplify calculating difference
                hs_school_data.drop('Category', inplace=True, axis=1)
                hs_corp_data.drop('Category', inplace=True, axis=1)
                
                # make sure there are no lingering NoneTypes to screw up the creation of hs_results
                hs_corp_data = hs_corp_data.fillna(value=np.nan)

                # calculate difference between two dataframes
                hs_results = pd.DataFrame(hs_school_data.values - hs_corp_data.values)

                # add headers
                hs_results.set_axis(result_cols, axis=1,inplace=True)
                hs_results.insert(loc=0,column='Category',value = tmp_category)
            
                final_data_hs = hs_merged_data.merge(hs_results, on ='Category', how='left')
                final_data_hs = final_data_hs[final_cols]

                # Clean up for display
                # for each category:
                # if '[year]School' < 0 or '[year]School' == 1:  '[year]School' = '***' & '[year]+/-' = '***'
                # if '[year]School' = NaN: '[year]School' = '', '[year]Corp Avg' = '', '' & '[year]+/-' = '***'
## TODO: ADD CHECK FOR 1.08 (if diploma strength is -1 -1 = -1*1.08/-1)
                # simple loop to: 1) replace negative values in school column with '***', 2) replace any value with '***' values
                # in '+/-' column if school column is '***'; and 3) NaN in both 'Corp Avg' & '+/-' columns if School column is NaN
                for y in year_cols:
                    final_data_hs[str(y) + 'School'] = np.where(final_data_hs[str(y) + 'School'] < 0,'***', final_data_hs[str(y) + 'School'])
                    final_data_hs[str(y) + 'School'] = np.where(final_data_hs[str(y) + 'School'] == 1,'***', final_data_hs[str(y) + 'School'])
                    final_data_hs[str(y) + '+/-'] = np.where(final_data_hs[str(y) + 'School'] == '***','***', final_data_hs[str(y) + '+/-'])
                    final_data_hs[str(y) + 'Corp Avg'] = np.where(final_data_hs[str(y) + 'School'].isnull(), final_data_hs[str(y) + 'School'], final_data_hs[str(y) + 'Corp Avg'])

                # split data into subsets for display in various tables
                overview = ['Total Graduation Rate','Non-Waiver Graduation Rate','State Average Graduation Rate','Strength of Diploma']

                grad_overview = final_data_hs[final_data_hs['Category'].str.contains('|'.join(overview))]
                grad_ethnicity = final_data_hs[final_data_hs['Category'].str.contains('|'.join(ethnicity))]
                grad_status = final_data_hs[final_data_hs['Category'].str.contains('|'.join(status))]
                eca_data = final_data_hs[final_data_hs['Category'].str.contains('|'.join(['Grade 10']))]

                ## create dictionary for placeholder data - not currently measured as data isn't available
                comp_other_hs_data = {
                    'Category': [           
                                'Percentage of Students entering Grade 12 who Graduated',
                                'Percentage of Graduating Students planning to pursue CCR',
                                ],
                    'Value': ['NA','NA'],
                    'Comparison': ['NA','NA']
                }

                k12_other_hs_data = pd.DataFrame(comp_other_hs_data)

            #### Tables
            ## Prepare table columns

                # get list of dataframe columns (used as index to identify columns in table)
                idx_cols = final_data_hs.columns.tolist()

                # get list of +/- columns (used by datatable filter_query' to ID columns for color formatting)
                format_cols = [k for k in idx_cols if '+/-' in k]

                # create list of display columns
                # in order to use datatables multi-level headers, need to split the 'name' prop into a list of two strings:
                # top-level: Year, 2nd level: Descriptor(School, Corp Avg, +/-)
                # we do this by iterating through column idx list and splitting the column idx name after the 4th character
                # we 'check' each item to make sure it starts with '20' (the first two digits of the year) and then
                # use slicing to get first 4 characters and all remaining characters
                # https://stackoverflow.com/questions/70020608/plotly-dash-datatable-how-create-multi-headers-table-from-pandas-multi-headers
                # https://stackoverflow.com/questions/69642786/multilevel-dataframe-to-dash-table

                name_cols = [['Category','']]
                
                for item in idx_cols:
                    if item.startswith('20'):
                        name_cols.append([item[:4],item[4:]])

                # use above columns to build school column dict
                # example result (dict):
                #   {"name": ["Category"], "id": "Category"},
                #   {"name": ["2021","School"], "id": "2021School"},
                #   {"name": ["2021","Corp Avg"], "id": "2021CorpAvg"},
                #   {"name": ["2021","+/-"], "id": "2021+/-"},
                #   .....
                
                k12_hs_table_columns = [
                    {
                        'name': col,
                        'id': idx_cols[idx],
                        'type':'numeric',
                        'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
                        } for (idx, col) in enumerate(name_cols)
                ]

                # default table styles
                table_style = {
                    'fontSize': '11px',
                    'fontFamily': 'Roboto, sans-serif',
                    'border': 'none'
                }

                table_header = {
                    'backgroundColor': '#ffffff',
                    'fontSize': '11px',
                    'fontFamily': 'Roboto, sans-serif',
                    'color': '#6783a9',
                    'textAlign': 'center',
                    'fontWeight': 'bold'            
                }

                table_cell = {
                    'whiteSpace': 'normal',
            #           'height': 'auto',
                    'textAlign': 'center',
                    'color': '#6783a9',
                    'boxShadow': '0 0',
                    'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                }

                # color average difference either red (lower than average) or green (higher than average) in '+/-' cols
                k12_hs_table_data_conditional = [

                    {
                        'if': {
                            'row_index': 'odd'
                        },
                        'backgroundColor': '#eeeeee'
                    }
                ] + [
                    {
                        'if': {
                            'filter_query': '{{{col}}} < 0'.format(col=col),
                            'column_id': col
                        },
                        'fontWeight': 'bold',
                        'color': '#b44655',
                        'fontSize': '10px',
                    } for col in format_cols
                ] + [
                    {
                        'if': {
                            'filter_query': '{{{col}}} > 0'.format(col=col),
                            'column_id': col
                        },
                        'fontWeight': 'bold',
                        'color': '#81b446',
                        'fontSize': '10px',
                    } for col in format_cols
                ]


            ## Create Tables

                hs_grad_overview_table = [
                            dash_table.DataTable(
                                grad_overview.to_dict('records'),
                                columns = k12_hs_table_columns,
                                style_data = table_style,
                                style_data_conditional = k12_hs_table_data_conditional,
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
                                columns = k12_hs_table_columns,
                                style_data = table_style,
                                style_data_conditional = k12_hs_table_data_conditional,
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
                                columns = k12_hs_table_columns,
                                style_data = table_style,
                                style_data_conditional = k12_hs_table_data_conditional,
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
                                columns = k12_hs_table_columns,
                                style_data = table_style,
                                style_data_conditional = k12_hs_table_data_conditional,
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

                hs_other_data_table = [
                            dash_table.DataTable(
                                k12_other_hs_data.to_dict('records'),
                                columns = [{'name': i, 'id': i, 'type':'numeric','format': FormatTemplate.percentage(2)} for i in k12_other_hs_data.columns],
                                style_data = table_style,
                                style_data_conditional = k12_hs_table_data_conditional,
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

        return k8_grade_table, k8_ethnicity_table, k8_status_table, k8_other_table, k8_table_container, hs_grad_overview_table, \
            hs_grad_ethnicity_table, hs_grad_status_table, hs_eca_table, hs_other_data_table, hs_table_container

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
                                    className = "pretty_container ten columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Proficiency by Ethnicity: Year over Year", style=label_style),
                                        html.Div(id='k8-ethnicity-table')

                                    ],
                                    className = "pretty_container ten columns"
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
                                    className = "pretty_container ten columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Other Academic Metrics (Not Calculated)", style=label_style),
                                        html.Div(id='k8-other-table')
                                    ],
                                    className = "pretty_container ten columns"
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
                                    className = "pretty_container ten columns"
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
                                    className = "pretty_container ten columns"
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
                                    className = "pretty_container ten columns"
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
                                    className = "pretty_container ten columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Other HS Metrics (Not Currently Measured)", style=label_style),
                                        html.Div(id='hs-other-data-table')
                                    ],
                                    className = "pretty_container ten columns"
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