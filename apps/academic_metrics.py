####################
# Academic Metrics #
####################
# author:   jbetley
# rev:     06.29.22

# TODO: Test any() vs all() effect on data

from dash import html, dash_table, Input, Output
from dash.exceptions import PreventUpdate
from dash.dash_table import FormatTemplate
import pandas as pd
import numpy as np
#from pandas.testing import assert_frame_equal
#from toolz import interleave

from app import app
# np.warnings.filterwarnings('ignore')

# Calculate difference between two values
def difference(CY, PY):
    if CY == None and PY == None:
        val = 'XX'  # Mark for removal
    elif (CY != '***' and CY != None) and (PY != '***' and PY != None):
        val = float(CY) - float(PY)
    else:
        val = '***'
    return val

# Calculate percentage change between two values [not currently used]
# def percentChange(CY, PY):
#     if (CY != '***' and PY != '***' and PY != 0):
#         val = (float(CY) - float(PY)) / float(PY)
#     else:
#         val = 'NA'
#     return val

# Get Academic Rating (inputs: value (float) and metric threshold as a list)
def getRating(data,threshold):
    if data == '***':       
        indicator = 'Not Available'
    elif data == 'XX':      # mark for removal
        indicator = 'XX'
    elif data is None:
        indicator = ''
    elif np.isnan(data):
        indicator = ''
    elif data >= threshold[0]:
        indicator = 'Exceeds the Standard'
    elif data > threshold[1]:
        indicator = 'Meets the Standard'
    elif data >= threshold[2]:
        indicator = 'Approaches the Standard'
    elif data <= threshold[3]:
        indicator = 'Does Not Meet the Standard'

    return indicator

# Get Grad Rate Rating (inputs: value (float) and metric threshold as a list)
def getGradRating(data,limit):
    if data == '***':
        return 'Not Available'
    if data >= limit[0]:
        diploma_indicator = 'Exceeds the Standard'
    elif data <= limit[0] and data >= limit[1]:
        diploma_indicator = 'Meets the Standard'
    elif data <= limit[1] and data >= limit[2]:
        diploma_indicator = 'Approaches the Standard'
    else:
        diploma_indicator = 'Does Not Meet the Standard'

    return diploma_indicator
## End Functions ##

@app.callback(
    Output('table-container-14ab', 'children'),
    Output('table-container-14cd', 'children'),
    Output('table-container-14ef', 'children'),
    Output('table-container-14g', 'children'),        
    Output('table-container-15abcd', 'children'),
    Output('table-container-16ab', 'children'),
    Output('table-container-16cd', 'children'),
    Output('display-k8-table', 'style'),    
    Output('table-title-hs', 'children'),
    Output('table-container-hs', 'children'),
    Output('display-hs-table', 'style'),
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),    
    Input('dash-session', 'data')
)
def update_acadmet_page(school, year, data):
    if not school:
        raise PreventUpdate

    # Data is passed through dcc.store as dict of dicts
    # data['1'] = k8 data for selected school
    # data['2'] = k8 data for 'similar' schools for current year
    # data['3'] = k8 data for 'comparable' schools for current year
    # data['4'] = HS data for selected school
    # data['5'] = HS data for 'similar' schools for current year
    # data['6'] = HS data for 'comparable' schools for current year
    # data['7'] = state grad rate average

    ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
    status = ['Special Education','General Education','Paid Meals','Free/Reduced Price Meals','English Language Learners','Non-English Language Learners']
    grades = ['Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8','School Total']

    selected_year = str(year)
    
    # the title of hs_metrics table depends on the school_type - default to high school
    hs_metrics_title = 'High School Accountability Metrics' 

    # the school_type also determines which table to display - default is display both
    display_k8_table = display_hs_table = {}

#### Global Table Styles

    table_style = {
        'fontSize': '12px',
        'border': 'none',
        'fontFamily': 'Open Sans, sans-serif',
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
        'height': 'auto',
        'textAlign': 'center',
        'color': '#6783a9',
        'boxShadow': '0 0',
        'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
    }


#### Build the Tables

    #index = pd.read_csv(r'data\school_index.csv', dtype=str)
    #school_index = index.loc[index['School ID'] == school]

    school_index = pd.DataFrame.from_dict(data['0'])

    # get 3-8 academic data from dcc.store and convert to df
    school_dataK8 = pd.DataFrame.from_dict(data['2'])  # 3-8 academic data for school (from dcc.store)
    corp_dataK8 = pd.DataFrame.from_dict(data['3'])    # 3-8 academic data for traditional public schools in same school corporation

    # if school type is K8 and there is no data in dataframe, hide all k8 tables and return a single table with 'No Data' message
    # (use 'hs_metrics_table' as variable for convenience as it is a single table)

    if len(school_dataK8.index) == 0 and school_index['School Type'].values[0] == 'K8':

        table_container_14ab = table_container_14cd = table_container_14ef = table_container_14g = table_container_15abcd = table_container_16ab = table_container_16cd = []
        display_k8_table = {'display': 'none'}
        
        hs_metrics_title = 'Academic Accountability'

        hs_metrics_table = [
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

        return table_container_14ab, table_container_14cd, table_container_14ef, table_container_14g, table_container_15abcd, table_container_16ab, table_container_16cd, display_k8_table, hs_metrics_title, hs_metrics_table, display_hs_table
    
    else:

    # Build tables with k8 data (this could be for either a k8 school or the k8 part of a k12 school)
    # NOTE: there is no 2020 data for k8 schools, in the event 2020 is selected, 2019 data is displayed

        if school_index['School Type'].values[0] == 'K8' or school_index['School Type'].values[0] == 'K12':

            # however, if the school type is K8, don't display the hs table at all
            if school_index['School Type'].values[0] == 'K8':
                hs_metrics_table = []
                display_hs_table = {'display': 'none'}

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

            # Store category column and drop from both dataframes to simplify calculation
            category_header = k8_school_data['Category']
            k8_school_data.drop('Category', inplace=True, axis=1)
            k8_corp_data.drop('Category', inplace=True, axis=1)

            # calculate difference between two dataframes
            delta_data = pd.DataFrame(k8_school_data.values - k8_corp_data.values)

            # add headers
            delta_data.set_axis(year_cols, axis=1,inplace=True)
            delta_data.insert(loc=0,column='Category',value = category_header)

            years_data = pd.DataFrame()
            
            # calculate difference between columns (note: need two years for each calculation, so
            # final year will always be NaN)
            # https://stackoverflow.com/questions/61332276/python-pandas-subtracting-each-column-and-creating-new-column
            years_data = k8_school_data.iloc[:, :num_years].diff(axis=1,periods=-1) #.add_suffix('_diff')

            # add headers
            years_data.set_axis(year_cols, axis=1,inplace=True)
            years_data.insert(loc=0,column='Category',value = category_header)

            # Clean up delta (corp comparison) data
            # for each delta_data category: if 'Year' <= -1:  'Year' = '***'
            # for each year_data category: if 'Year' >= 1:  'Year' = '***'

            for y in year_cols:
                delta_data[y] = np.where(delta_data[y] <= -1 ,'***', delta_data[y])
                years_data[y] = np.where(years_data[y] >= 1 ,'***', years_data[y])

            # add category back to school_data because it is used later in script
            k8_school_data.insert(loc=0,column='Category',value = category_header)

            # ensure all column headers are strings
            delta_data.columns = delta_data.columns.astype(str)
            years_data.columns = years_data.columns.astype(str)
            k8_school_data.columns = k8_school_data.columns.astype(str)

            delta_limits = [.1,.02,0,0]     # metric thresholds for comparison analysis   
            years_limits = [.05,.02,0,0]    # metric thresholds for year over year analysis

            # iterate over each dataframe, inserting 'Rating' every other row and adding the results of getRating()
            [years_data.insert(i,'Rating' + str(i), years_data.apply(lambda x : getRating(x[years_data.columns[i-1]], years_limits), axis = 1)) for i in range(years_data.shape[1], 1, -1)]
            [delta_data.insert(i,'Rating' + str(i), delta_data.apply(lambda x : getRating(x[delta_data.columns[i-1]], delta_limits), axis = 1)) for i in range(delta_data.shape[1], 1, -1)]

        # subgroup and grade variables
            ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
            status = ['Special Education','General Education','Paid Meals','Free/Reduced Price Meals','English Language Learners','Non-English Language Learners']
            grades = ['Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8','School Total','IREAD Pass %']

            subgroup = ethnicity + status

### TODO: Placeholders until data is available
    ## Two (2) year student proficiency metrics (1.4e and 1.4f) not yet available
            d14e_dict = {
                'Metric': '1.4e',
                'Category': 'Percentage of students enrolled for at least two (2) school years achieving proficiency on the state assessment in English Language Arts',
            }

            d14f_dict = {
                'Metric': '1.4f',
                'Category': 'Percentage of students enrolled for at least two (2) school years achieving proficiency on the state assessment in Math',
            }

        ## Growth Metrics (1.5a, 1.5b, 1.5c, 1.5d) not currently available
            d15a_dict = {
                'Metric': '1.5a',
                'Category': 'Percentage of students achieving “typical” or “high” growth on the state assessment in \
                    English Language Arts according to Indiana\'s Growth Model',
            }
            d15b_dict = {
                'Metric': '1.5b',
                'Category': 'Percentage of students achieving “typical” or “high” growth on the state assessment in \
                    Math according to Indiana\'s Growth Model',
            }
            d15c_dict = {
                'Metric': '1.5c',
                'Category': 'Median Student Growth Percentile ("SGP") of students achieving "adequate and sufficient growth" \
                    on the state assessment in English Language Arts according to Indiana\'s Growth Model',
            }
            d15d_dict = {
                'Metric': '1.5d',
                'Category': 'Median SGP of students achieving "adequate and sufficient growth" on the state assessment \
                    in Math according to Indiana\'s Growth Model',
            }

            for i in range(num_years):
                year = int(selected_year) - i
                d14e_dict[str(year)] = 'Not Available'
                d14e_dict['Rating' + str(i)] = 'Not Available'
                d14f_dict[str(year)] = 'Not Available'
                d14f_dict['Rating' + str(i)] = 'Not Available'
                d15a_dict[str(year)] = 'Not Available'
                d15a_dict['Rating' + str(i)] = 'Not Available'
                d15b_dict[str(year)] = 'Not Available'
                d15b_dict['Rating' + str(i)] = 'Not Available'
                d15c_dict[str(year)] = 'Not Available'
                d15c_dict['Rating' + str(i)] = 'Not Available'
                d15d_dict[str(year)] = 'Not Available'
                d15d_dict['Rating' + str(i)] = 'Not Available'                                

            d14ef_list = [d14e_dict,d14f_dict]
            d14ef = pd.DataFrame(d14ef_list)

            d15abcd_list = [d15a_dict,d15b_dict,d15c_dict,d15d_dict]
            d15abcd = pd.DataFrame(d15abcd_list)

            def createTable(label, data):#, cols):

                cols = data.columns
                table_size = len(cols)

                if table_size < 4:
                    col_width = 'six'
                elif table_size >= 4 and table_size < 7:
                    col_width = 'eight'
                elif table_size == 7:
                    col_width = 'ten'
                else:
                    col_width = 'twelve'
                
                class_name = "pretty_container " + col_width + " columns"
                
                headers = data.columns.tolist()

                # TODO: this seems kludgy:
                # 1) do df's need unique col headers?
                # 2) do dict's need unique keys?
                # have to have for display purposes, we want them all to read: 'Rating'
                clean_headers = []
                for i, x in enumerate (headers):
                    if 'Rating' in x:
                        clean_headers.append('Rating')
                    else:
                        clean_headers.append(x)

                if len(data.index) == 0 or table_size == 1:
                    table = [
                        html.Div(
                            [
                                html.Label(label, style=label_style),
                                html.Div(
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
                                )
                            ],
                            className = class_name
                        )
                    ]

                else:

## TODO: Adjust Category column depending on total # of columns

                    table_cell_conditional = [
                        {
                            'if': {
                                'column_id': 'Metric'
                            },
                            'textAlign': 'center',
                            'fontWeight': '500',
                            'width': '10%'
                        },
                    ] + [
                        {
                            'if': {
                                'column_id': 'Category'
                            },
                            'textAlign': 'left',
                            'paddingLeft': '20px',
                            'fontWeight': '500',
                            'width': '15%'
                        },
                    ] + [
                        {
                            'if': {
                                'column_id': 'Value'
                            },
                            'textAlign': 'center',
                            'fontWeight': '500',
                            'width': '10%'
                        },
                    ]  + [
                        {   'if': {
                            'column_id': 'Rating'
                        },
                            'textAlign': 'center',
                            'fontWeight': '600',
                        #    'width': '25%'
                        },
                    ]

                    table_data_conditional =  [
                        {
                            'if': {
                                'row_index': 'odd'
                            },
                            'backgroundColor': '#eeeeee',
                        }
                    ] + [
                        {
                            'if': {
                                'filter_query': '{{{col}}} = "Does Not Meet the Standard"'.format(col=col),
                                'column_id': col
                            },
                            'backgroundColor': '#e56565',
                            'color': 'white',
                        } for col in cols
                    ] + [
                        {
                            'if': {
                                'filter_query': '{{{col}}} = "Approaches the Standard"'.format(col=col),
                                'column_id': col
                            },
                            'backgroundColor': '#ddd75a',
                            'color': 'white',
                        } for col in cols
                    ] + [
                        {
                            'if': {
                                'filter_query': '{{{col}}} = "Exceeds the Standard"'.format(col=col),
                                'column_id': col
                            },
                            'backgroundColor': '#b29600',
                            'color': 'white',
                        } for col in cols
                    ] + [
                        {
                            'if': {
                                'filter_query': '{{{col}}} = "Meets the Standard"'.format(col=col),
                                'column_id': col
                            },
                            'backgroundColor': '#75b200',
                            'color': 'white',
                        } for col in cols
                    ]

                    # Clean Category column by removing everything following '|'
                    data['Category'] = data['Category'].map(lambda x: x.split('|')[0])

                    table = [
                        html.Div(
                            [
                                html.Label(label, style=label_style),
                                html.Div(
                                    dash_table.DataTable(
                                        data.to_dict('records'),
                                        columns=[{
                                            'name': col, 
                                            'id': headers[idx],
                                            'type':'numeric',
                                            'format': FormatTemplate.percentage(2)
                                            } for (idx, col) in enumerate(clean_headers)],
                                        #columns = [{'name': i, 'id': i, 'type':'numeric','format': FormatTemplate.percentage(2)} for i in cols],
                                        style_data = table_style,
                                        style_data_conditional = table_data_conditional,
                                        style_header = table_header,
                                        style_cell = table_cell,
                                        style_cell_conditional = table_cell_conditional,
                                        style_as_list_view=True
                                    )
                                )
                            ],
                            className = class_name
                        )
                    ]

                return table

            def setLayout(table1, table2, cols):

                ## TODO: Kludge for forcing single table layout
                if table1 == table2:

                    table_layout = [
                            html.Div(
                                table1,
                                className = "bare_container twelve columns",
                            )
                    ]
                else:
                    if len(cols) >= 4:

                        table_layout = [
                                html.Div(
                                    table1,
                                    className = "bare_container twelve columns",
                                ),
                                html.Div(
                                    table2,
                                    className = "bare_container twelve columns",
                                ),
                        ]

                    else:

                        table_layout = [
                                html.Div(
                                    [
                                        table1[0],
                                        table2[0],
                                    ],
                                    className = "bare_container twelve columns",
                                ),
                        ]

                return table_layout

        ## Create metric tables
        # each metric is a separate table except for placeholders

            metric_14a_data = years_data[(years_data['Category'].str.contains('|'.join(grades))) & (years_data['Category'].str.contains('ELA'))]
            metric_14a_label = ['1.4a Grade level proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' compared with the previous school year.']
            table_14a = createTable(metric_14a_label, metric_14a_data)

            metric_14b_data = years_data[(years_data['Category'].str.contains('|'.join(grades))) & (years_data['Category'].str.contains('Math'))]
            metric_14b_label = ['1.4b Grade level proficiency on the state assessment in',html.Br(), html.U('Math'), ' compared with the previous school year.']
            table_14b = createTable(metric_14b_label, metric_14b_data)

            table_container_14ab = setLayout(table_14a,table_14b,years_data.columns)

            metric_14c_data = delta_data[(delta_data['Category'].str.contains('|'.join(grades))) & (delta_data['Category'].str.contains('ELA'))]
            metric_14c_label = ['1.4c Grade level proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' compared with similar* traditional public schools.']
            table_14c = createTable(metric_14c_label, metric_14c_data)

            metric_14d_data = delta_data[(delta_data['Category'].str.contains('|'.join(grades))) & (delta_data['Category'].str.contains('Math'))]            
            metric_14d_label = ['1.4.d Grade level proficiency on the state assessment in',html.Br(), html.U('Math'), ' compared with similar* traditional public schools.']
            table_14d = createTable(metric_14d_label, metric_14d_data)

            table_container_14cd = setLayout(table_14c,table_14d,delta_data.columns)

            metric_14ef_data = d14ef
            metric_14ef_label = 'Accountability Metrics 1.4e & 1.4f'
            table_14ef = createTable(metric_14ef_label, metric_14ef_data)

        ## TODO: sending same table twice is a kludge to force single table display (until I get layout figured out)
            table_container_14ef = setLayout(table_14ef, table_14ef, d14ef.columns)

            print(k8_school_data.loc[k8_school_data['Category'] == 'IREAD Pass %'])
            if not (k8_school_data.loc[k8_school_data['Category'] == 'IREAD Pass %']).empty:
                iread_limits=[.9,.8,.7,.7]
                metric_14g_data = k8_school_data.loc[k8_school_data['Category'] == 'IREAD Pass %']
                [metric_14g_data.insert(i,'Rating' + str(i), metric_14g_data.apply(lambda x : getRating(x[metric_14g_data.columns[i-1]], iread_limits), axis = 1)) for i in range(metric_14g_data.shape[1], 1, -1)]
                metric_14g_label = '1.4.g Percentage of students achieving proficiency on the IREAD-3 state assessment.'
                table_14g = createTable(metric_14g_label, metric_14g_data)
                table_container_14g = setLayout(table_14g, table_14g, metric_14g_data.columns)

            else:
# TODO: ???? DOES THIS EVEN WORK
                table14g = [
                            html.Div(
                                [
                                    html.Label('14.g. baby', style=label_style),
                                    html.Div(
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
                                    )
                                ]
                            )
                ]
                table_container_14g = setLayout(table14g, table14g, table14g.columns)

            metric_15abcd_data = d15abcd
            metric_15abcd_label = '1.5 Growth Metrics (1.5a, 1.5b, 1.5c, & 1.5d)'
            table_15abcd = createTable(metric_15abcd_label, metric_15abcd_data)

            table_container_15abcd = setLayout(table_15abcd, table_15abcd, d15abcd.columns)

            metric_16a_data = delta_data[(delta_data['Category'].str.contains('|'.join(subgroup))) & (delta_data['Category'].str.contains('ELA'))]
            metric_16a_label = ['1.6a Proficiency on the state assessment in ', html.U('English Language Arts'), html.Br(),'for each subgroup compared with similar* traditional public schools.']
            table_16a = createTable(metric_16a_label,metric_16a_data)

            metric_16b_data = delta_data[(delta_data['Category'].str.contains('|'.join(subgroup))) & (delta_data['Category'].str.contains('Math'))]            
            metric_16b_label = ['1.6b Proficiency on the state assessment in ', html.U('Math'), ' for each', html.Br(), 'subgroup compared with similar* traditional public schools.']
            table_16b = createTable(metric_16b_label, metric_16b_data)

            table_container_16ab = setLayout(table_16a,table_16b,delta_data.columns)

            metric_16c_data = years_data[(years_data['Category'].str.contains('|'.join(subgroup))) & (years_data['Category'].str.contains('ELA'))]
            metric_16c_label = ['1.6c The change in proficiency on the state assessment in',html.Br(), html.U('English Language Arts'), ' for each subgroup compared with the previous school year.']
            table_16c = createTable(metric_16c_label,metric_16c_data)

            metric_16d_data = years_data[(years_data['Category'].str.contains('|'.join(subgroup))) & (years_data['Category'].str.contains('Math'))]
            metric_16d_label = ['1.6d The change in proficiency on the state assessment in',html.Br(), html.U('Math'), ' for each subgroup compared with the previous school year.']
            table_16d = createTable(metric_16d_label,metric_16d_data)

            table_container_16cd = setLayout(table_16c,table_16d,years_data.columns)

#### AHS and HS Metrics (for HS and K12)

        if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'AHS' or school_index['School Type'].values[0] == 'K12': 
        
            # if HS or AHS, k8 table always empty
            if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'AHS':
                table_container_14ab = table_container_14cd = table_container_14ef = table_container_14g = table_container_15abcd = table_container_16ab = table_container_16cd = []
                display_k8_table = {'display': 'none'}

            # get HS academic data from dcc.store and convert to df
            school_dataHS = pd.DataFrame.from_dict(data['5'])  # 3-8 academic data for school (from dcc.store)
            corp_dataHS = pd.DataFrame.from_dict(data['6'])    # 3-8 academic data for traditional public schools in same school corporation
            
            if len(school_dataHS.index) == 0:
                hs_metrics_table = [
                    dash_table.DataTable(
                        columns = [
                            {'id': "emptytable", 'name': "No Data to Display"},
                        ],
                        style_header={
                            'fontSize': '14px',
                            'border': 'none',
                            'textAlign': 'center',
                            'color': '#4682b4',
                            'fontFamily': 'Open Sans, sans-serif',
                        },
                    )
                ]

            else:

            ## Adult High School Accountability (may need to separate once table can be generated dynamically)
                if school_index['School Type'].values[0] == 'AHS': 
                
                    # create default (blank) AHS Accountability Table
                    hs_metric_data = {
                        'Metric': ['1.1a','1.2a','1.2b','1.3','1.4a','1.4b'],
                        'Category': [
                                    'School meets standard under State Alternative Accountability System',
                                    'Students Graduate from school in 4 years',
                                    'Students enrolled in grade 12 graduate within school year assessed',
                                    'Percentage of graduating students achieving one or more CCR indicators',
                                    'ELA proficiency of graduating students',
                                    'Math proficiency of graduating students'
                                    ],
                        'Value': ['NA','NA','NA','NA','NA','NA'],
                        'Rating': ['NA','NA','NA','NA','NA','NA']
                    }
                    hs_final_data = pd.DataFrame(hs_metric_data)
                    
                    hs_metrics_title='Adult High School Accountability Metrics'

                else:

                ## HS or K12 (9-12) accountability
                    #num_years = len(school_dataHS.index)        
                
                ### Graduation Rates

                    hs_corp_data = corp_dataHS.copy()
                    hs_school_data = school_dataHS.copy()

                    hs_final_data = hs_school_data[['Year']].copy()

                    # see index.py. In order to facilitate tracking '***,' we need the additional step of
                    # converting all '1' values (indicating '***' / '***') into -99
                    #hs_school_data = hs_school_data.replace(1, -99)

                    hs_final_data['Grad Rate Compared to State Average'] = hs_school_data['Total Graduation Rate'] - hs_school_data['State Average Graduation Rate']
                    hs_final_data['Grad Rate Compared to Corporation Average'] = hs_school_data['Total Graduation Rate'] - hs_corp_data['Total Graduation Rate']
                    hs_final_data['Strength of Diploma Indicator'] = hs_school_data['Strength of Diploma']

                    # transpose dataframes and clean headers
                    hs_final_data = hs_final_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
                    hs_final_data = hs_final_data.iloc[:,:(num_years+1)]     # Keep category and all available years of data

                    # ensure column headers are strings
                    hs_final_data.columns = hs_final_data.columns.astype(str)

                    # iterate over each dataframe, inserting 'Rating' every other row and adding the results of getRating()
                    # TODO: KLUDGE - NEED TO FIGURE OUT BETTER WAY TO ITERATE OVER ROWS WITH DIFFERENT LIMITS

                    # 1.7.a The school’s four-year graduation rate compared with the state average for traditional
                    # public high schools(Excluding Adult High Schools from average).
                    hs_final_data17a = hs_final_data.loc[hs_final_data['Category'] == 'Grad Rate Compared to State Average']
                    d17a_limits = [0,.05,.15,.15]
                    [hs_final_data17a.insert(i,'Rating' + str(i), hs_final_data17a.apply(lambda x : getGradRating(x[hs_final_data17a.columns[i-1]], d17a_limits), axis = 1)) for i in range(hs_final_data17a.shape[1], 1, -1)]

                    # 1.7.b The school’s four-year graduation rate compared with traditional public high schools
                    # within the same school corporation
                    hs_final_data17b = hs_final_data.loc[hs_final_data['Category'] == 'Grad Rate Compared to Corporation Average']
                    d17b_limits = [0,.05,.10,.10]
                    [hs_final_data17b.insert(i,'Rating' + str(i), hs_final_data17b.apply(lambda x : getGradRating(x[hs_final_data17b.columns[i-1]], d17b_limits), axis = 1)) for i in range(hs_final_data17b.shape[1], 1, -1)]

                    # 1.7.e Strength of diploma indicator
                    hs_final_data17e = hs_final_data.loc[hs_final_data['Category'] == 'Strength of Diploma Indicator']                    
                    d17e_limits = [1,.9170,.7794,.7793]
                    [hs_final_data17e.insert(i,'Rating' + str(i), hs_final_data17e.apply(lambda x : getGradRating(x[hs_final_data17e.columns[i-1]], d17e_limits), axis = 1)) for i in range(hs_final_data17e.shape[1], 1, -1)]
                    
                    hs_final_data = pd.concat([hs_final_data17a, hs_final_data17b, hs_final_data17e])

                hs_metrics_table = [
                    dash_table.DataTable(
                        hs_final_data.to_dict('records'),
                        columns = [{'name': i, 'id': i, 'type':'numeric','format': FormatTemplate.percentage(2)} for i in hs_final_data.columns],
                        style_data = table_style,
                        style_data_conditional=[
                            {
                                'if': {
                                    'row_index': 'odd'
                                },
                                'backgroundColor': '#eeeeee',
                            },
                        ]  +
                        [
                            {
                                'if': {
                                'filter_query': '{{{col}}} = "Does Not Meet the Standard"'.format(col=col),
                                'column_id': col
                                },
                                'backgroundColor': '#e56565',
                                'color': 'white',
                            } for col in hs_final_data.columns
                        ] +
                        [
                            {
                                'if': {
                                'filter_query': '{{{col}}} = "Approaches the Standard"'.format(col=col),
                                'column_id': col
                                },
                                'backgroundColor': '#ddd75a',
                                'color': 'white',
                            } for col in hs_final_data.columns
                        ] +                       
                        [
                            {
                                'if': {
                                'filter_query': '{{{col}}} = "Exceeds the Standard"'.format(col=col),
                                'column_id': col
                                },
                                'backgroundColor': '#b29600',
                                'color': 'white',
                            } for col in hs_final_data.columns
                        ] +                    
                        [
                            {
                                'if': {
                                'filter_query': '{{{col}}} = "Meets the Standard"'.format(col=col),
                                'column_id': col
                                },
                                'backgroundColor': '#75b200',
                                'color': 'white',
                            } for col in hs_final_data.columns
                        ],
                        style_header = table_header,
                        style_cell = table_cell,
                        style_cell_conditional=[
                            {'if': {'column_id': 'Metric'},
                            'textAlign': 'left',
                            'fontWeight': '500',
                            'paddingLeft': '20px',
                            'width': '8%'},
                        ] + [
                            {'if': {'column_id': 'Category'},
                            'textAlign': 'left',
                            'fontWeight': '500',
                            'paddingLeft': '20px',
                            'width': '52%'},
                        ] + [
                            {'if': {'column_id': 'Value'},
                            'textAlign': 'center',
                            'fontWeight': '500',
                            'paddingLeft': '20px',
                            'width': '15%'},
                        ]  + [
                            {'if': {'column_id': 'Rating'},
                            'textAlign': 'center',
                            'fontWeight': '600',
                            'paddingLeft': '20px',
                            'width': '35%'},
                        ],
                        style_as_list_view=True                    
                    )
                ]

        return table_container_14ab, table_container_14cd, table_container_14ef,table_container_14g, table_container_15abcd, table_container_16ab, table_container_16cd, display_k8_table, hs_metrics_title, hs_metrics_table, display_hs_table

#### Layout

label_style = {
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

layout = html.Div(
            [
                html.Div(
                    [
                        html.Div(id='table-container-14ab', children=[]), #id = "table-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='table-container-14cd', children=[]), #id = "table-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='table-container-14ef', children=[]), #id = "table-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='table-container-14g', children=[]), #id = "table-container-16ab" #className='bare_container twelve columns',                        
                        html.Div(id='table-container-15abcd', children=[]), #id = "table-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='table-container-16ab', children=[]), #id = "table-container-16ab" #className='bare_container twelve columns',
                        html.Div(id='table-container-16cd', children=[]), #id = "table-container-16ab" #className='bare_container twelve columns',
                    ],
                    id = 'display-k8-table',
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label(id='table-title-hs', style=label_style),
                                        html.Div(id='table-container-hs')
                                    ],
                                    className = "pretty_container ten columns"
                                ),
                            ],
                            className = "bare_container twelve columns"
                        ),
                    ],
                    id = 'display-hs-table',
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