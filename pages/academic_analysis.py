######################################
# ICSB Dashboard - Academic Analysis #
######################################
# author:   jbetley
# version:  .99.021323

# TODO: Add IREAD-3 chart? (14g)
# TODO: Add AHS/HS Analysis

import dash
from dash import dcc, dash_table, html, Input, Output, callback
from dash.dash_table import FormatTemplate
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import numpy as np
import json
import scipy.spatial as spatial

# Debuggging #
# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_colwidth', None)
import timeit
# #

### START TIME ###
initial_load_start = timeit.default_timer()
##################

# import subnav function
from .subnav import subnav_academic
dash.register_page(__name__, path = '/academic_analysis', order=6)

color_short=['#98abc5','#8a89a6','#7b6888','#6b486b','#a05d56','#d0743c','#ff8c00']
color=['#98abc5','#919ab6','#8a89a6','#837997','#7b6888','#73587a','#6b486b','#865361','#a05d56','#b86949','#d0743c','#e8801e','#ff8c00']

# NOTE: removed 'American Indian' because the category doesn't appear in all data sets (?)
#ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']

ethnicity = ['Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
subgroup = ['Special Education','General Education','Paid Meals','Free/Reduced Price Meals','English Language Learners','Non-English Language Learners']
grades = ['Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8']
subject = ['Math','ELA'] # 'ELA & Math'

# load comparison data file
all_academic_data_k8 = pd.read_csv(r'data/academic_data_k8.csv', dtype=str)

# get school information
school_index= pd.read_csv(r'data/school_index.csv', dtype=str)

### END TIME ###
initial_load_time = timeit.default_timer() - initial_load_start
print ('initial load time (Academic Analysis):', initial_load_time)
################

## Blank (Loading) Fig ##
# https://stackoverflow.com/questions/66637861/how-to-not-show-default-dcc-graph-template-in-dash

def blank_fig():
    fig = {
        'layout': {
            'xaxis': {
                'visible': False
            },
            'yaxis': {
                'visible': False
            },
            'annotations': [
                {
                    'text': 'Loading . . .',
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': {
                        'size': 16,
                        'color': '#6783a9',
                        'family': 'Roboto, sans-serif'
                    }
                }
            ]
        }
    }
    return fig

# Functions
# single line chart (input: dataframe)
def make_line_chart(values):
    data = values.copy()

    data.columns = data.columns.str.split('|').str[0]

    cols=[i for i in data.columns if i not in ['School Name','Year']]
    for col in cols:
        data[col]=pd.to_numeric(data[col], errors='coerce')

    data.sort_values('Year', inplace=True)

    marks = [v for v in list(data.columns) if v not in ['School Name','Year']]

    # determine tick range [Not currently using/skews graph too much]
    # # get max value in dataframe
    # max_val = data[cols].select_dtypes(include=[np.number]).max().max()
    
    # # round to nearest .1
    # tick_val = np.round(max_val,1)
    
    # # if it rounded down, add .1
    # if tick_val < max_val:
    #     tick_val = tick_val + .1

    fig = px.line(
        data,
        x='Year',
        y=marks,
        markers=True,
        color_discrete_sequence=color,
    )

    fig.update_traces(mode='markers+lines', hovertemplate=None)
    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=60),
        title_x=0.5,
        font = dict(
            family = 'Open Sans, sans-serif',
            color = 'steelblue',
            size = 10
            ),
        plot_bgcolor='white',
        # xaxis = dict(
        #     # title='',
        #     # type='category',
        #     # mirror=True,
        #     # showline=True,
        #     # # tickmode = 'linear',
        #     # # tick0 = data['Year'][0],
        #     # # dtick = 1,
        #     # # tickmode = 'array',
        #     # # tickvals = data['Year'],
        #     # # ticktext = data['Year'],
        #     # linecolor='#b0c4de',
        #     # linewidth=.5,
        #     # gridwidth=.5,
        #     # showgrid=True,
        #     # gridcolor='#b0c4de',
        #     # zeroline=False,
        #     ),   
        legend=dict(orientation="h"),         
        hovermode='x unified',
        height=400,
        legend_title='',
    )

# TODO: default tick behavior is quite ugly for small number of points. How to fix?
# May not be able to fix easily- at least find a way to space small number of ticks
# equally within chart space

    fig.update_xaxes(
        title='',
        # type='category',
        mirror=True,
        showline=True,
        # tickmode = 'linear',
        # tick0 = data['Year'].min() - 2,
        # dtick = 1,
        tickmode = 'array',
        tickvals = data['Year'],
        ticktext = data['Year'],
        linecolor='#b0c4de',
        linewidth=.5,
        gridwidth=.5,
        showgrid=True,
        gridcolor='#b0c4de',
        zeroline=False,     
    )

    fig.update_yaxes(
        title='',
        mirror=True,
        showline=True,
        linecolor='#b0c4de',
        linewidth=.5,
        gridwidth=.5,
        showgrid=True,
        gridcolor='#b0c4de',
        zeroline=False,
        range=[0, 1], #tick_val],  # adjusting tick value skews graph too much
        dtick=.2,
        tickformat=',.0%',
    )

    return fig

# single bar chart (input: dataframe and title string)
def make_bar_chart(values, category, school_name):
    data = values.copy()
    
    schools = data['School Name'].tolist()

    # assign colors for each comparison school
    trace_color = {schools[i]: color[i] for i in range(len(schools))}

    # use specific color for selected school
    for key, value in trace_color.items():
        if key == school_name:
            trace_color[key] = '#b86949'

    # format distance data (not displayed)
    # data['Distance'] = pd.Series(['{:,.2f}'.format(val) for val in data['Distance']], index = data.index)

    fig = px.bar(
        data,
        x='School Name',
        y=category,
        color_discrete_map=trace_color,
        color='School Name',
        custom_data  = ['Low Grade','High Grade'] #,'Distance']
    )

    fig.update_yaxes(range=[0, 1], dtick=0.2, tickformat=',.0%',title='',showgrid=True, gridcolor='#b0c4de')
    fig.update_xaxes(type='category', showticklabels=False, title='',showline=True,linewidth=1,linecolor='#b0c4de')

    fig.update_layout(
        title_x=0.5,
        margin=dict(l=40, r=40, t=40, b=60),
        font = dict(
            family='Open Sans, sans-serif',
            color='steelblue',
            size=10
            ),
        legend=dict(
            orientation='h',
            title='',
            xanchor= 'center',
            x=0.45
        ),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # TODO: Make prettier?
    fig.update_traces(
        # hovertemplate = '<b>%{x}</b> (Grades %{customdata[0]} - %{customdata[1]})<br>Distance in miles: %{customdata[2]}<br>Proficiency: %{y}<br><extra></extra>'
        hovertemplate = '<b>%{x}</b> (Grades %{customdata[0]} - %{customdata[1]})<br>Proficiency: %{y}<br><extra></extra>'
    )

    return fig

# grouped bar chart (input: dataframe)
def make_group_bar_chart(values, school_name):

    data = values.copy()

    # find the index of the row containing the school name,
    # use this to filter data (next line) and also with
    # data_table row_index to Bold the school's name.
    school_name_idx = data.index[data['School Name'].str.contains(school_name)].tolist()[0]

    # Only want to display categories where the selected school has data - this
    # drops all columns where the row at school_name_idx has a NaN value
    data = data.loc[:, ~data.iloc[school_name_idx].isna()]

    # reset index
    data.reset_index(drop=True,inplace=True)

    # remove trailing string
    data.columns = data.columns.str.split('|').str[0]

    # replace any '***' values (insufficient n-size) with NaN
    data = data.replace('***', np.nan)

    # force non-string columns to numeric
    cols=[i for i in data.columns if i not in ['School Name','Year']]
    for col in cols:
        data[col]=pd.to_numeric(data[col], errors='coerce')

    # num_schools = len(data['School Name'])

    categories = data.columns.tolist()
    categories.remove('School Name')
    schools = data['School Name'].tolist()

    # melt dataframe from 'wide' format to 'long' format (plotly express
    # can handle either, but long format makes hovertemplate easier
    #  - trust me)
    data_set = pd.melt(data, id_vars='School Name',value_vars = categories, var_name='Categories', ignore_index=False)

    data_set.reset_index(drop=True, inplace=True)

    # replace any remaining NaN with 0
    data_set = data_set.fillna(0)

    # assign colors for each comparison
    trace_color = {schools[i]: color[i] for i in range(len(schools))}

    # replace color for selected school
    for key, value in trace_color.items():
        if key == school_name:
            trace_color[key] = '#b86949'

    fig = px.bar(
        data_frame = data_set,
        x = 'Categories',
        y = 'value',
        color = 'School Name',
        color_discrete_map = trace_color,
        orientation = 'v',
        barmode = 'group',
        custom_data = ['School Name']
    )

    fig.update_yaxes(range=[0, 1], dtick=0.2, tickformat=',.0%', title='',showgrid=True, gridcolor='#b0c4de')
    fig.update_xaxes(title='',showline=True,linewidth=.5,linecolor='#b0c4de')

    # TODO: Issue with the relationship between the chart and the table.
    # Cannot figure out a way to reduce the bottom margin of a chart to
    # reduce the amount of empty space

    # Cannot seem to shrink bottom margin here - had to add negative margin
    # to each fig layout. Try this maybe:
    # it takes maximum value and multiplies it by three for max range (eg., less than 100)
    #fig.update_layout(yaxis=dict(range=[0, ymax*3]))

    fig.update_layout(
        title_x=0.5,
        margin=dict(l=40, r=40, t=40, b=40),
        font = dict(
            family='Open Sans, sans-serif',
            color='steelblue',
            size=10
            ),
        bargap=.15,
        bargroupgap=0,
        height=400,
        legend_title='',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

# TODO: In progress - The purpose of all this is to get '0' values in
# a bar chart to show up as a thin line (as opposed to no line for no data)

# TODO: Add thin marker_line_color (border) to each bar - This will cause '0' vals to show up as a thin line
# Currently cannot figure out how to make the marker_line_color match the bar color
# May be able to use Go to add each trace separately and just flag the zero value bar for a markerline, but
# that would require a complete rewrite which I'd like to avoid.
# Surely there is a way to get this to work with plotly express
# https://plotly.com/python/marker-style/
#
    # {'ACE Preparatory Academy': '#98abc5', 'Indianapolis Public Schools': '#919ab6', 'Center for Inquiry School 70': '#8a89a6', 'IPS/Butler Lab at Eliza Blaker 55': '#837997', 'Merle Sidener Gifted Academy': '#7b6888', 'Rousseau McClellan School 91': '#73587a'}
    # for i in range(num_schools):
    #     print(i)
    # colorlist = [[0, '#98abc5'], [.2, '#919ab6'], [.4, '#8a89a6'], [.6, '#837997'], [.8, '#7b6888'], [1, '#73587a']]
    # #colorlist = [[0, 'rgb(152, 171, 197)'], [1, 'rgb(145, 154, 182)'], [2, 'rgb(138, 137, 166)'], [3, 'rgb(131, 121, 151)'], [4, 'rgb(123, 104, 136)'], [5, 'rgb(115, 88, 122)']]

    # fig.update_traces(marker_line_width = 2, marker_line_color = colorlist) #marker_line_color = dict(trace_color),
    # fig.update_traces(
    #     marker_size=2,
    #     marker_line=dict(width=12, colorscale = colorlist), #color['hex']),
    #     selector=dict(mode='markers')
    # )

# https://stackoverflow.com/questions/69000770/plotly-bar-chart-with-dotted-or-dashed-border-how-to-implement
    # data2={"years":[2019,2020,2021,2022],
    #     "total_value":[100000000000,220000000000,350000000000,410000000000]}
    # print(data2)
    # print(data)
    # x_location = data["years"].index(2022)
    # print(x_location)
    # def get_plotly_xcoordinates(category, width=0.8):
    #     x_location = data_set['Categories'].index(category)
    #     print(x_location)
    #     return x_location - width/2, x_location + width/2
    
    # for cat in data_set['Categories']:
    #     print(cat)
    #     x0,x1 = get_plotly_xcoordinates(cat)

    #     fig.add_shape(type="rect", xref="x", yref="y",
    #         x0=x0, y0=0,
    #         x1=x1, y1=410000000000,
    #         line=dict(color="#FED241",dash="dash",width=3)
    # )

    #TODO: Make prettier?
    fig.update_traces(
        hovertemplate="<br>".join(
            [
                s.replace(" ", "&nbsp;")
                for s in [
                    '%{customdata[0]}',
                    'Proficiency: %{y}<br><extra></extra>',
                ]
            ]
        )
    )

    return fig

def make_table(data,school_name):

    # find the index of the row containing the school name
    school_name_idx = data.index[data['School Name'].str.contains(school_name)].tolist()[0]

    # drop all columns where the row at school_name_idx has a NaN value
    data = data.loc[:, ~data.iloc[school_name_idx].isna()]

    # sort dataframe by the 'first' proficiency column and reset index
    data = data.sort_values(data.columns[1], ascending=False)
    data = data.reset_index(drop=True)

    # need to find the index again because the sort has jumbled things up
    school_name_idx = data.index[data['School Name'].str.contains(school_name)].tolist()[0]

    # hide the header 'School Name'
    data = data.rename(columns = {'School Name' : ''})
    
    table = dash_table.DataTable(
        data.to_dict('records'),
        columns = [{'name': i, 'id': i, 'type':'numeric','format': FormatTemplate.percentage(2)} for i in data.columns],
        merge_duplicate_headers=True,
        style_as_list_view=True,
        id='tst-table',
        style_data={
            'fontSize': '10px',
            'fontFamily': 'Arial, Helvetica, sans-serif',
            'color': '#6783a9'
        },
        style_data_conditional=[
            {
                'if': {
                    'row_index': 'even'
                },
                'backgroundColor': '#eeeeee',
                'border': 'none',
            },
            {
                'if': {
                    'row_index': school_name_idx
                },
                'fontWeight': 'bold',
                'color': '#b86949',
            },
        ],
        style_header={
            'height': '10px',
            'backgroundColor': 'white',
            'fontSize': '10px',
            'fontFamily': 'Arial, Helvetica, sans-serif',
            'color': '#6783a9',
            'textAlign': 'center',
            'fontWeight': 'bold',
            'borderBottom': 'none',
            'borderTop': 'none',    
        },
        style_header_conditional=[
            {
                'if': {
                    'header_index': 0,
                    },
                    'text-decoration': 'underline'
            },
        ],
        style_cell={
            'whiteSpace': 'normal',
            'height': 'auto',
            'textAlign': 'center',
            'minWidth': '25px', 'width': '25px', 'maxWidth': '25px',
            'border': 'none',
        },
        style_cell_conditional=[
            {'if': {'column_id': ''},
            'textAlign': 'left',
            'paddingLeft': '30px'}
        ],
    )
    return table

# Find nearest schools in miles using a KDTree
def find_nearest(school_idx,data):
    "Based on https://stackoverflow.com/q/43020919/190597"
    "Uses scipy.spatial KDTree "
# https://stackoverflow.com/questions/45127141/find-the-nearest-point-in-distance-for-all-the-points-in-the-dataset-python
# https://stackoverflow.com/questions/43020919/scipy-how-to-convert-kd-tree-distance-from-query-to-kilometers-python-pandas
# https://kanoki.org/2020/08/05/find-nearest-neighbor-using-kd-tree/

    # the radius of earth in miles. For kilometers use 6372.8 km
    R = 3959.87433 

    # as the selected school already exists in 'data' df, just pass in index and use that to find it
    data = data.apply(pd.to_numeric)

    phi = np.deg2rad(data['Lat'])
    theta = np.deg2rad(data['Lon'])
    data['x'] = R * np.cos(phi) * np.cos(theta)
    data['y'] = R * np.cos(phi) * np.sin(theta)
    data['z'] = R * np.sin(phi)
    tree = spatial.KDTree(data[['x', 'y','z']])

    num_hits = 30

    # gets a list of the indexes and distances in the data tree that
    # match the [num_hits] number of 'nearest neighbor' schools
    distance, index = tree.query(data.iloc[school_idx][['x', 'y','z']], k = num_hits)
    
    return index, distance

## Callbacks

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
def set_dropdown_options(school, year, selected):

### START TIME ###
    build_kd_start = timeit.default_timer()
##################

    # filter out schools that did not exist in the selected year
    eval_year = [str(year)]
    
    filtered_academic_data_k8 = all_academic_data_k8[all_academic_data_k8['Year'].isin(eval_year)]
    filtered_academic_data_k8.reset_index(drop=True,inplace=True)

    location_data = filtered_academic_data_k8[['Lat','Lon']]
    school_idx = filtered_academic_data_k8[filtered_academic_data_k8['School ID'] == school].index

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
    distances.set_index(list(distances)[0], inplace=True)

    # filter comparison set by matching indexes
    closest_schools = filtered_academic_data_k8[filtered_academic_data_k8.index.isin(index_list)]

    # add 'Distance' column to comparison_set
    comparison_set = pd.merge(closest_schools,distances,left_index=True, right_index=True)
    comparison_set = comparison_set.rename(columns = {'y': 'Distance'})

### END TIME ###
    build_kd_time = timeit.default_timer() - build_kd_start
    print ('kdtree complete:')
    print (build_kd_time)
################

    # Drop the selected school from the list of available selections,
    # so selected school cannot be removed from dropdown. Comment this
    # line out to permit selected school to be cleared from chart
    comparison_set = comparison_set.drop(comparison_set[comparison_set['School ID'] == school].index)

    # drop schools with no grade overlap with selected school by getting school grade span and filtering
    school_grade_span = filtered_academic_data_k8.loc[filtered_academic_data_k8['School ID'] == school][['Low Grade','High Grade']].values[0].tolist()
    school_grade_span = [s.replace('KG', '0').replace('PK', '0') for s in school_grade_span]
    school_grade_span = [int(i) for i in school_grade_span]
    school_grade_range = list(range(school_grade_span[0],(school_grade_span[1]+1)))

    # PK and KG are not tested grades
    comparison_set = comparison_set.replace({'Low Grade' : { 'PK' : '0', 'KG' : '0'}})

    # drop schools with no grades (NOTE: Not sure why dropna doesn't work here, but it doesn't)
    comparison_set = comparison_set[comparison_set['Low Grade'].str.contains('nan')==False]

    # creates a boolean mask of those schools where there is a grade overlap based on a list created
    # from the Low Grade and High Grade values. We use it to filter out those schools within the school
    # corporation that do not overlap on grade span
    def filter_fn(row):
        row[['Low Grade', 'High Grade']] = row[['Low Grade', 'High Grade']].astype(int)
        row_grade_range = list(range(row['Low Grade'], row['High Grade']+1))

        if (set(school_grade_range) & set(row_grade_range)):
            return True
        else:
            return False

    grade_mask = comparison_set.apply(filter_fn, axis=1)
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
    default_num = 4 # value for number of default selections
    options = default_options

    # the following tracks the number of selections and disables all remaining
    # selections once 8 schools have been selected
    input_warning = None
    
    # if list is None or empty ([]), use the default options
    if not selected:
        selected = [d['value'] for d in options[:default_num]]

    else:
        if len(selected) > 7:
            input_warning = html.P(
                id='input-warning',
                children='Limit reached (Maximum of 8 schools).',
            )
            options = [
                {"label": option["label"], "value": option["value"], "disabled": True}
                for option in default_options
            ]
    
    return options, input_warning, selected

# Graphs and Tables
@callback(
    Output('fig14a', 'figure'),
    Output('fig14b', 'figure'),
    Output('fig14c', 'figure'),
    Output('fig14c-table', 'children'),
    Output('fig14d', 'figure'),
    Output('fig14d-table', 'children'),
    Output('fig16c1', 'figure'),
    Output('fig16d1', 'figure'),
    Output('fig16c2', 'figure'),
    Output('fig16d2', 'figure'),
    Output('fig16a1', 'figure'),
    Output('fig16a1-table', 'children'),
    Output('fig16a1-category-string', 'children'),
    Output('fig16a1-school-string', 'children'),
    Output('fig16a1-table-container', 'style'),    
    Output('fig16b1', 'figure'),
    Output('fig16b1-table', 'children'),
    Output('fig16b1-category-string', 'children'),
    Output('fig16b1-school-string', 'children'),
    Output('fig16b1-table-container', 'style'),
    Output('fig16a2', 'figure'),
    Output('fig16a2-table', 'children'),    
    Output('fig16a2-category-string', 'children'),
    Output('fig16a2-school-string', 'children'),
    Output('fig16a2-table-container', 'style'),
    Output('fig16b2', 'figure'),
    Output('fig16b2-table', 'children'),
    Output('fig16b2-category-string', 'children'),
    Output('fig16b2-school-string', 'children'),
    Output('fig16b2-table-container', 'style'),
    Output('main-container', 'style'),
    Output('empty-container', 'style'),
    Output('no-data-fig', 'figure'),            
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    Input('dash-session', 'data'),
    [Input('comparison-dropdown', 'value')],
)
def update_academic_analysis(school, year, data, comparison_school_list):
    if not school:
        raise PreventUpdate

    selected_year = str(year)

    # blank chart
    blank_chart = {
            'layout': {
                'height': 200,
                'xaxis': {
                    'visible': False
                },
                'yaxis': {
                    'visible': False
                },
                'annotations': [
                    {
                        'text': 'No Data to Display',
                        'xref': 'paper',
                        'yref': 'paper',
                        'showarrow': False,
                        'font': {
                            'size': 16,
                            'color': '#4682b4',
                            'family': 'Open Sans, sans-serif'
                        }
                    }
                ]
            }
        }

    # empty_table
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

    # default styles
    main_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_fig = blank_chart

    ### START TIME ###
    main_load_start = timeit.default_timer()
    ##################

    # school_index.json
    school_info = pd.DataFrame.from_dict(data['0'])
    school_name = school_info['School Name'].values[0]

    ##### TODO: Currently no charts for AHS or HS

    # Test if data exists - there are 4 possibilities:
    #   1) the dataframe itself does not exist because there is no academic data for the school at all
    #   2) the school is of a type (AHS/HS) that doesn't yet have any charted data
    #   3) the dataframe exists, but the tested_header (YEARSchool) does not exist in the dataframe-
    #       this catches any year with no data (e.g., 2020School because there is no 2020 data in the
    #       dataframe
    #   4) the tested header does exist, but all data in the column is NaN- this catches any year where
    #       the school has no data or insufficient n-size ('***')

    # Testing (1) and (2)
    if (school_info['School Type'].values[0] == 'K8' and not data['8']) or \
        school_info['School Type'].values[0] == 'HS' or school_info['School Type'].values[0] == 'AHS':

        fig14a = fig14b = fig14c = fig14d = fig16c1 = fig16d1 = fig16c2 = fig16d2 = fig16a1 = fig16b1 = fig16a2 = fig16b2 = blank_chart
        fig14c_table = fig14d_table = fig16a1_table = fig16b1_table = fig16a2_table = fig16b2_table = empty_table
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
        academic_data_k8 = pd.DataFrame.from_dict(json_data)
        
        tested_academic_data = academic_data_k8.copy()
        for col in tested_academic_data.columns:
            tested_academic_data[col] = pd.to_numeric(tested_academic_data[col], errors='coerce')
        
        tested_header = selected_year + 'School'

        # Testing (3) and (4)
        if tested_header not in tested_academic_data.columns or tested_academic_data[tested_header].isnull().all():
            fig14a = fig14b = fig14c = fig14d = fig16c1 = fig16d1 = fig16c2 = fig16d2 = fig16a1 = fig16b1 = fig16a2 = fig16b2 = blank_chart
            fig14c_table = fig14d_table = fig16a1_table = fig16b1_table = fig16a2_table = fig16b2_table = empty_table
            fig16a1_category_string = fig16b1_category_string = fig16a2_category_string = fig16b2_category_string = ''
            fig16a1_school_string = fig16b1_school_string = fig16a2_school_string = fig16b2_school_string = ''
            fig16a1_table_container = {'display': 'none'}
            fig16b1_table_container = {'display': 'none'}
            fig16a2_table_container = {'display': 'none'}
            fig16b2_table_container = {'display': 'none'}
            main_container = {'display': 'none'}
            empty_container = {'display': 'block'}

        else:

        ## Year over Year Data

            # keep only Category and School data columns
            k8_academic_info = academic_data_k8[[col for col in academic_data_k8.columns if 'School' in col or 'Category' in col]]

            # remove 'School' from column headers
            k8_academic_info.columns = k8_academic_info.columns.str.replace(r'School$', '', regex=True)

            # transpose df
            k8_academic_infoT = k8_academic_info.set_index('Category').T.rename_axis('Year').rename_axis(None, axis=1).reset_index()

            k8_academic_infoT = k8_academic_infoT.replace({'***': float(-99)})

            for col in k8_academic_infoT.columns:
                    k8_academic_infoT[col] = pd.to_numeric(k8_academic_infoT[col], errors='coerce')

            # add column for each year with the School's Name and add text to each category
            k8_academic_infoT['School Name'] = school_name
            k8_academic_infoT = k8_academic_infoT.rename(columns={c: c + ' Proficient %' for c in k8_academic_infoT.columns if c not in ['Year', 'School Name']})

            # are there at least two years of data (length of index gives number of rows)
            if len(k8_academic_infoT.index) >= 2:

                # NOTE: The commented code uses only the most recent two years,
                # the uncommented code uses all years
                #k8_school_data_YoY = k8_academic_infoT.iloc[:2]
                k8_school_data_YoY = k8_academic_infoT.copy()

                info_categories = k8_school_data_YoY[['School Name']]

                # temporarily drop 'Category' column to simplify calculating difference
                k8_school_data_YoY = k8_school_data_YoY.drop(columns=['School Name'], axis=1)

                # Skip charts if school has no chartable data (includes neg values
                # which are the result of subbing -99 for '***') drop columns with
                # all negative values and then replace remaining neg values with null
                k8_school_data_YoY = k8_school_data_YoY.loc[:, ~k8_school_data_YoY.lt(0).all()]
                k8_school_data_YoY = k8_school_data_YoY.replace(-99, '')

                # add info_columns (strings) back to dataframe
                k8_school_data_YoY  = k8_school_data_YoY.join(info_categories)

            ## Charts (1, 2, 5, 6, 7, & 8) - Year over Year

                ## Chart 1: Year over Year ELA Proficiency by Grade (1.4.a)
                fig14a_data = k8_school_data_YoY.filter(regex = r'^Grade \d\|ELA|^School Name$|^Year$',axis=1)
                fig14a = make_line_chart(fig14a_data)

                ## Chart 2: Year over Year Math Proficiency by Grade (1.4.b)
                fig14b_data = k8_school_data_YoY.filter(regex = r'^Grade \d\|Math|^School Name$|^Year$',axis=1)
                fig14b = make_line_chart(fig14b_data)

                # NOTE: Charts 3 & 4 (Comparisons) added below

                ## Chart 5: Year over Year ELA Proficiency by Ethnicity (1.6.c)
                categories = []
                for e in ethnicity:
                    categories.append(e + '|' + 'ELA Proficient %')

                fig16c1_data = k8_school_data_YoY.loc[:, (k8_school_data_YoY.columns.isin(categories)) | (k8_school_data_YoY.columns.isin(['School Name','Year']))]
                fig16c1_data = fig16c1_data.rename(columns = {'Native Hawaiian or Other Pacific Islander|ELA Proficient %': 'Pacific Islander|ELA Proficient %'})
                fig16c1 = make_line_chart(fig16c1_data)

                ## Chart 6: Year over Year Math Proficiency by Ethnicity (1.6.d)
                categories = []
                for e in ethnicity:
                    categories.append(e + '|' + 'Math Proficient %')

                fig16d1_data = k8_school_data_YoY.loc[:, (k8_school_data_YoY.columns.isin(categories)) | (k8_school_data_YoY.columns.isin(['School Name','Year']))]
                fig16d1_data = fig16d1_data.rename(columns = {'Native Hawaiian or Other Pacific Islander|Math Proficient %': 'Pacific Islander|Math Proficient %'})
                fig16d1 = make_line_chart(fig16d1_data)

                ## Chart 7: Year over Year ELA Proficiency by Subgroup (1.6.c)
                categories = []
                for s in subgroup:
                    categories.append(s + '|' + 'ELA Proficient %')

                fig16c2_data = k8_school_data_YoY.loc[:, (k8_school_data_YoY.columns.isin(categories)) | (k8_school_data_YoY.columns.isin(['School Name','Year']))]
                fig16c2 = make_line_chart(fig16c2_data)

                ## Chart 8: Year over Year Math Proficiency by Subgroup (1.6.d)
                categories = []
                for s in subgroup:
                    categories.append(s + '|' + 'Math Proficient %')

                fig16d2_data = k8_school_data_YoY.loc[:, (k8_school_data_YoY.columns.isin(categories)) | (k8_school_data_YoY.columns.isin(['School Name','Year']))]
                fig16d2 = make_line_chart(fig16d2_data)

            else:   # only one year of data (zero years would be empty dataframe)

                fig14a = fig14b = fig14d = fig16c1 = fig16d1 = fig16c2 = fig16d2 = blank_chart

        ## Charts (3 & 4)- Comparison Data
        # Uses: single [selected] year of data
        # Display: 1) school value; 2) similar school avg; and 3) all comparable schools with data

            # Get current year school data
            school_current_data = k8_academic_infoT.loc[k8_academic_infoT['Year'] == int(selected_year)]

            # temporarily store and drop 'School Name' string column to simplify calculations
            info_categories = school_current_data[['School Name']]
            school_current_data = school_current_data.drop(columns=['School Name'], axis=1)

            # coerce data types to numeric
            for col in school_current_data.columns:
                school_current_data[col]=pd.to_numeric(school_current_data[col], errors='coerce').fillna(school_current_data[col]).tolist()

            # Skip charts if school has no chartable data (includes neg values which are the result of subbing -99 for '***')
            # drop all columns with negative values (can use 'any' or 'all' as it is a single column)
            school_current_data = school_current_data.loc[:, ~school_current_data.lt(0).any()]

            # add info_columns (strings) back to dataframe
            school_current_data  = school_current_data.join(info_categories)

            # This data is used for the chart 'hovertemplate'
            # school_current_data['Distance'] = 0
            school_current_data['Low Grade'] = all_academic_data_k8.loc[(all_academic_data_k8['School ID'] == school) & (all_academic_data_k8['Year'] == selected_year)]['Low Grade'].values[0]
            school_current_data['High Grade'] = all_academic_data_k8.loc[(all_academic_data_k8['School ID'] == school) & (all_academic_data_k8['Year'] == selected_year)]['High Grade'].values[0]
            
            # get dataframe for traditional public schools located within school corporation that selected school resides
            # academic_analysis_corp_dict
            k8_corp_data = pd.DataFrame.from_dict(data['7'])

            corp_current_data = k8_corp_data.loc[k8_corp_data['Year'] == int(selected_year)]

            # filter unnecessary columns
            corp_current_data = corp_current_data.filter(regex = r'\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$|^School Name$',axis=1)

            # coerce data types to numeric (except strings)
            for col in corp_current_data.columns:
                corp_current_data[col]=pd.to_numeric(corp_current_data[col], errors='coerce').fillna(corp_current_data[col]).tolist()

            # get academic data for comparison schools
            # filter full set by year and by the comparison schools selected in the dropdown

            eval_year = [str(school_current_data['Year'].values[0])]

            filtered_academic_data_k8 = all_academic_data_k8[all_academic_data_k8['Year'].isin(eval_year)]

            comparison_schools_filtered = filtered_academic_data_k8[filtered_academic_data_k8['School ID'].isin(comparison_school_list)]


            # add 'Distance' value to dataframe using the gc_distance function [not currently implemented due to SLOWness]
            # def get_distance(row):
            #     return gc_distance(school_info['Lon'].values[0],school_info['Lat'].values[0],row['Lon'],row['Lat'])

            # comparison_schools['Distance'] = comparison_schools.apply(get_distance, axis=1)

            # drop unused columns
            comparison_schools_filtered = comparison_schools_filtered.filter(regex = r'Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year|School Name|School ID|Distance|Low Grade|High Grade',axis=1)

            # create list of columns with no date (used in loop below)
            # missing_mask returns boolean series of columns where column is true if all elements in the column are equal to null
            missing_mask = pd.isnull(school_current_data[school_current_data.columns]).all()
            missing_cols = school_current_data.columns[missing_mask].to_list()

            # temporarily store and drop 'information' columns [these lines include 'Distance' value]
            # comparison_schools_info = comparison_schools[['School ID','School Name','Distance','Low Grade','High Grade']].copy()
            # comparison_schools.drop(['School ID','School Name','Distance','Low Grade','High Grade'], inplace=True, axis=1)

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
            # proficiency in a subject is calculated using ALL grades. So we
            # need to recalculate the 'School Total' rate manually to ensure
            # it includes only the included grades.
            all_grades_math_proficient_comp = comparison_schools.filter(regex=r"Grade.+?Math Total Proficient")
            all_grades_math_tested_comp = comparison_schools.filter(regex=r"Grade.+?Math Total Tested")
            comparison_schools['Total|Math Proficient %'] = all_grades_math_proficient_comp.sum(axis=1) / all_grades_math_tested_comp.sum(axis=1)

            all_grades_ela_proficient_comp = comparison_schools.filter(regex=r"Grade.+?ELA Total Proficient")
            all_grades_ela_tested_comp = comparison_schools.filter(regex=r"Grade.+?ELA Total Tested")
            comparison_schools['Total|ELA Proficient %'] = all_grades_ela_proficient_comp.sum(axis=1) / all_grades_ela_tested_comp.sum(axis=1)

            # calculate IREAD Pass %
            if 'IREAD Proficiency (Grade 3 only) Proficient %' in school_current_data:
                comparison_schools['IREAD Proficiency (Grade 3 only) Proficient %'] = comparison_schools['IREAD Pass N'] / comparison_schools['IREAD Test N']

            # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
            comparison_schools = comparison_schools.filter(regex = r'\|ELA Proficient %$|\|Math Proficient %$|^IREAD Proficiency|^Year$',axis=1)

            # drop all columns from the comparison dataframe that aren't in the school dataframe
            # a bit of kludge - as the school file has already been processed, column names will not directly
            # match, so we create a list of unique substrings from the column names and use it to filter the comparison set
            valid_columns = school_current_data.columns.str.split('|').str[0].tolist()
            comparison_schools = comparison_schools.filter(regex='|'.join(valid_columns))

            # drop any rows where all values in tested cols (proficiency data) are null (remove 'Year' from column
            # list because 'Year' will never be null)
            tested_columns = comparison_schools.columns.tolist()
            tested_columns.remove('Year')
            comparison_schools = comparison_schools.dropna(subset=tested_columns,how='all')

            # add text info columns back
            comparison_schools = pd.concat([comparison_schools, comparison_schools_info], axis=1, join='inner')

            # reset indecies
            comparison_schools = comparison_schools.reset_index(drop=True)
            
### TODO: Do we add HS Data? ##
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
####

### TODO: position of selected school trace - random?
### TODO: Can probably refactor this to simplify as well

            # get name of school corporation
            school_corporation_name = filtered_academic_data_k8.loc[(all_academic_data_k8['Corp ID'] == school_info['GEO Corp'].values[0])]['Corp Name'].values[0]

        #### Current Year ELA Proficiency Compared to Similar Schools (1.4.c) #
            category = 'Total|ELA Proficient %'

            # Get school value for specific category
            if category in school_current_data.columns:

                # fig14c_k8_school_data = school_current_data[['School Name','Low Grade','High Grade','Distance',category]]
                fig14c_k8_school_data = school_current_data[['School Name','Low Grade','High Grade',category]].copy()

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

                fig14c = make_bar_chart(fig14c_all_data,category, school_name)

                # merge column names and make ELA Proficiency table
                fig14c_table_data['School Name'] = fig14c_table_data['School Name'] + " (" + fig14c_table_data['Low Grade'] + "-" + fig14c_table_data['High Grade'] + ")"
                fig14c_table_data = fig14c_table_data[['School Name', category]]
                fig14c_table_data.reset_index(drop=True,inplace=True)

                fig14c_table = make_table(fig14c_table_data, school_name)
            else:

                fig14c = blank_chart
                fig14c_table = empty_table

        #### Current Year Math Proficiency Compared to Similar Schools (1.4.d) #
            category = 'Total|Math Proficient %'

            if category in school_current_data.columns:

                fig14d_k8_school_data = school_current_data[['School Name','Low Grade','High Grade',category]].copy()

                # add corp average for category to dataframe - the '','','N/A' are values for Low & High Grade and Distance columns
                fig14d_k8_school_data.loc[len(fig14d_k8_school_data.index)] = [school_corporation_name, '3','8',corp_current_data[category].values[0]]

                # Get comparable school values for the specific category
                fig14d_comp_data = comparison_schools[['School Name','Low Grade','High Grade',category]]
                # fig14d_comp_data = comparison_schools[['School Name','Low Grade','High Grade','Distance',category]]

                fig14d_all_data = pd.concat([fig14d_k8_school_data,fig14d_comp_data])

                # save table data
                fig14d_table_data = fig14d_all_data.copy()

                fig14d_all_data[category] = pd.to_numeric(fig14d_all_data[category])

                fig14d = make_bar_chart(fig14d_all_data,category, school_name)

                # Math Proficiency table
                fig14d_table_data['School Name'] = fig14d_table_data['School Name'] + " (" + fig14d_table_data['Low Grade'] + "-" + fig14d_table_data['High Grade'] + ")"
                fig14d_table_data = fig14d_table_data[['School Name', category]]
                fig14d_table_data.reset_index(drop=True,inplace=True)

                fig14d_table = make_table(fig14d_table_data, school_name)
            else:
                fig14d = blank_chart
                fig14d_table = empty_table

    #### Comparison Charts & Tables
        # NOTE: See backup data 01.23.23 for pre- full_chart() function code

            # info col headers is the same for all dataframes
            info_categories = ['School Name','Low Grade','High Grade']

            # A function that returns a fig, a table, and two strings
            def create_full_chart(school_data, categories, corp_name):
                info_categories = ['School Name','Low Grade','High Grade']
                all_categories = categories + info_categories

                # get a list of the categories that exist in school data
                academic_columns = [i for i in categories if i in school_data.columns]

                # get a list of the categories that are missing from school data and strip everything following '|' delimeter
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
                school_names = final_data['School Name'] + " (" + final_data['Low Grade'] + "-" + final_data['High Grade'] + ")"      
                final_data = final_data.drop(['Low Grade', 'High Grade'], axis = 1)

                # In some cases, cell data is '' or ' ', so we need to replace any
                # blanks with NaN
                final_data = final_data.replace(r'^\s*$', np.nan, regex=True)

                #  send to chart function
                chart = make_group_bar_chart(final_data, school_name)

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

                # shift column 'School Name' to first position
                # replace values in 'School Name' column with the series we created earlier
                final_data = final_data.drop('School Name', axis = 1)
                final_data['School Name'] = school_names

                first_column = final_data.pop('School Name')
                final_data.insert(0, 'School Name', first_column)

                table = make_table(final_data, school_name)

                return chart, table, category_string, school_string

        #### ELA Proficiency by Ethnicity Compared to Similar Schools (1.6.a.1)
            headers_16a1 = []
            for e in ethnicity:
                headers_16a1.append(e + '|' + 'ELA Proficient %')

            categories_16a1 =  info_categories + headers_16a1

            # filter dataframe by categories
            fig16a1_k8_school_data = school_current_data.loc[:, (school_current_data.columns.isin(categories_16a1))]
            
            if len(fig16a1_k8_school_data.columns) > 3:
                fig16a1, fig16a1_table, fig16a1_category_string, fig16a1_school_string = \
                    create_full_chart(fig16a1_k8_school_data, headers_16a1, school_corporation_name)

                fig16a1_table_container = {'display': 'block'}
            
            else:
                fig16a1 = blank_chart
                fig16a1_table = empty_table
                fig16a1_category_string = ''
                fig16a1_school_string = ''                
                fig16a1_table_container = {'display': 'none'}

        #### Math Proficiency by Ethnicity Compared to Similar Schools (1.6.b.1)
            headers_16b1 = []
            for e in ethnicity:
                headers_16b1.append(e + '|' + 'Math Proficient %')

            categories_16b1 =  info_categories + headers_16b1

            # filter dataframe by categories
            fig16b1_k8_school_data = school_current_data.loc[:, (school_current_data.columns.isin(categories_16b1))]

            if len(fig16b1_k8_school_data.columns) > 3:
                fig16b1, fig16b1_table, fig16b1_category_string, fig16b1_school_string = \
                    create_full_chart(fig16b1_k8_school_data, headers_16b1, school_corporation_name)

                fig16b1_table_container = {'display': 'block'}
            
            else:
                fig16b1 = blank_chart
                fig16b1_table = empty_table
                fig16b1_category_string = ''
                fig16b1_school_string = ''                
                fig16b1_table_container = {'display': 'none'}

        #### ELA Proficiency by Subgroup Compared to Similar Schools (1.6.a.2)
            headers_16a2 = []
            for s in subgroup:
                headers_16a2.append(s + '|' + 'ELA Proficient %')
            
            categories_16a2 =  info_categories + headers_16a2

            # filter dataframe by categories
            fig16a2_k8_school_data = school_current_data.loc[:, (school_current_data.columns.isin(categories_16a2))]

            if len(fig16a2_k8_school_data.columns) > 3:
                fig16a2, fig16a2_table, fig16a2_category_string, fig16a2_school_string = \
                    create_full_chart(fig16a2_k8_school_data, headers_16a2, school_corporation_name)

                fig16a2_table_container = {'display': 'block'}
            
            else:
                fig16a2 = blank_chart
                fig16a2_table = empty_table
                fig16a2_category_string = ''
                fig16a2_school_string = ''                
                fig16a2_table_container = {'display': 'none'}

       #### Math Proficiency by Subgroup Compared to Similar Schools (1.6.b.2)
            headers_16b2 = []
            for s in subgroup:
                headers_16b2.append(s + '|' + 'Math Proficient %')

            categories_16b2 =  info_categories + headers_16b2

            # filter dataframe by categories
            fig16b2_k8_school_data = school_current_data.loc[:, (school_current_data.columns.isin(categories_16b2))]

            if len(fig16b2_k8_school_data.columns) > 3:
                fig16b2, fig16b2_table, fig16b2_category_string,fig16b2_school_string = \
                    create_full_chart(fig16b2_k8_school_data, headers_16b2, school_corporation_name)

                fig16b2_table_container = {'display': 'block'}
            
            else:
                fig16b2 = blank_chart
                fig16b2_table = empty_table
                fig16b2_category_string = ''
                fig16b2_school_string = ''                
                fig16b2_table_container = {'display': 'none'}

    ### END TIME ###
    main_load_time = timeit.default_timer() - main_load_start
    print ('main (re)load time:', main_load_time)
    ################

    # main_container = {'display': 'block'}
    return fig14a, fig14b, fig14c, fig14c_table, fig14d, fig14d_table, fig16c1, fig16d1, fig16c2, fig16d2, \
        fig16a1, fig16a1_table, fig16a1_category_string, fig16a1_school_string, fig16a1_table_container, fig16b1, \
        fig16b1_table, fig16b1_category_string, fig16b1_school_string, fig16b1_table_container, fig16a2, fig16a2_table, \
        fig16a2_category_string, fig16a2_school_string, fig16a2_table_container, fig16b2, fig16b2_table, \
        fig16b2_category_string, fig16b2_school_string, fig16b2_table_container, main_container, empty_container, no_data_fig

## Layout ##
label_style = {
    'height': '20px',
    'backgroundColor': '#6783a9',
    'fontSize': '12px',
    'fontFamily': 'Roboto, sans-serif',
    'color': '#ffffff',
    'textAlign': 'center',
    'fontWeight': 'bold',
    'paddingBottom': '5px',
    'paddingTop': '5px'
}

# The difference between regular and label style is label style is bolded.
# school_string styles also has no top margin or top border
category_string_label_style = {
    'color': '#6783a9',
    'fontSize': 11,
    'marginLeft': '10px',
    'marginRight': '10px',
    'marginTop': '10px',
    'borderTop': '.5px solid #c9d3e0',
    'fontWeight': 'bold'
}

category_string_style = {
    'color': '#6783a9',
    'fontSize': 11,
    'marginLeft': '10px',
    'marginRight': '10px',
    'marginTop': '10px',
    'borderTop': '.5px solid #c9d3e0',
    'fontWeight': 'normal'
}

school_string_label_style = {
    'color': '#6783a9',
    'fontSize': 11,
    'marginLeft': '10px',
    'marginRight': '10px',
    'fontWeight': 'bold'
}

school_string_style = {
    'color': '#6783a9',
    'fontSize': 11,
    'marginLeft': '10px',
    'marginRight': '10px',
    'fontWeight': 'normal'
}

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
                                        html.Label('Year over Year ELA Proficiency by Grade', style=label_style),
                                        dcc.Graph(id='fig14a', figure = blank_fig())
                                    ],
                                    className = 'pretty_container six columns'
                                ),
                                html.Div(
                                    [
                                        html.Label('Year over Year Math Proficiency by Grade', style=label_style),
                                        dcc.Graph(id='fig14b', figure = blank_fig())
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
                                        html.Label('Year over Year ELA Proficiency by Ethnicity', style=label_style),
                                        dcc.Graph(id='fig16c1', figure = blank_fig())
                                    ],
                                    className = 'pretty_container six columns'
                                ),
                                html.Div(
                                    [
                                        html.Label('Year over Year Math Proficiency by Ethnicity', style=label_style),
                                        dcc.Graph(id='fig16d1', figure = blank_fig())
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
                                        html.Label('Year over Year ELA Proficiency by Subgroup', style=label_style),
                                        dcc.Graph(id='fig16c2', figure = blank_fig())
                                    ],
                                    className = 'pretty_container six columns'
                                ),
                                html.Div(
                                    [
                                        html.Label('Year over Year Math Proficiency by Subgroup', style=label_style),
                                        dcc.Graph(id='fig16d2', figure = blank_fig())
                                    ],
                                    className = 'pretty_container six columns'
                                )
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
                                        html.Label('Comparison: Current Year ELA Proficiency', style=label_style),
                                        dcc.Graph(id='fig14c', figure = blank_fig())
                                    ],
                                    className = 'pretty_container nine columns',
                                ),
                                html.Div(
                                    [
                                        html.Label('Proficiency', style=label_style),
                                        html.Div(id='fig14c-table')
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
                                        html.Label('Comparison: Current Year Math Proficiency', style=label_style),
                                        dcc.Graph(id='fig14d', figure = blank_fig())
                                    ],
                                    className = 'pretty_container nine columns',
                                ),
                                html.Div(
                                    [
                                        html.Label('Proficiency', style=label_style),
                                        html.Div(id='fig14d-table')
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
                                        html.Label('Comparison: ELA Proficiency by Ethnicity', style=label_style),
                                        dcc.Graph(id='fig16a1', figure = blank_fig()) #, style={'margin-bottom': -20}),
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
                                                    html.Span(id='fig16a1-category-string', children='',style = category_string_style),
                                                    ],
                                                    style = category_string_label_style,
                                                ),
                                                html.P(
                                                    id='fig16a1-school-string',
                                                    children=[
                                                    'Schools with insufficient n-size or no data:',
                                                    html.Span(id='fig16a1-school-string', children='',style = school_string_style),
                                                    ],
                                                    style = school_string_label_style,
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

                                        # TODO: Margin-bottom makes for better graph display, but it breaks empty
                                        # chart display.. Need to figure out how to change margin in fig creation itself
                                        html.Label('Comparison: Math Proficiency by Ethnicity', style=label_style),
                                        dcc.Graph(id='fig16b1', figure = blank_fig()) #, style={'margin-bottom': -20}),
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
                                                    html.Span(id='fig16b1-category-string', children='',style = category_string_style),
                                                    ],
                                                    style = category_string_label_style,
                                                ),
                                                html.P(
                                                    id='fig16b1-school-string',
                                                    children=[
                                                    'Schools with insufficient n-size or no data:',
                                                    html.Span(id='fig16b1-school-string', children='',style = school_string_style),
                                                    ],
                                                    style = school_string_label_style,
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
                                        html.Label('Comparison: ELA Proficiency by Subgroup', style=label_style),
                                        dcc.Graph(id='fig16a2', figure = blank_fig()) #, style={'margin-bottom': -20}),
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
                                                    html.Span(id='fig16a2-category-string', children='',style = category_string_style),
                                                    ],
                                                    style = category_string_label_style,
                                                ),
                                                html.P(
                                                    id='fig16a2-school-string',
                                                    children=[
                                                    'Schools with insufficient n-size or no data:',
                                                    html.Span(id='fig16a2-school-string', children='',style = school_string_style),
                                                    ],
                                                    style = school_string_label_style,
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
                                        html.Label('Comparison: Math Proficiency by Subgroup', style=label_style),
                                        dcc.Graph(id='fig16b2', figure = blank_fig()) #, style={'margin-bottom': -20}),
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
                                                    html.Span(id='fig16b2-category-string', children='',style = category_string_style),
                                                    ],
                                                    style = category_string_label_style,
                                                ),
                                                html.P(
                                                    id='fig16b2-school-string',
                                                    children=[
                                                    'Schools with insufficient n-size or no data:',
                                                    html.Span(id='fig16b2-school-string', children='',style = school_string_style),
                                                    ],
                                                    style = school_string_label_style,
                                                ),                        
                                            ],
                                            className = 'close_container twelve columns'
                                        )
                                    ],
                                    className='row'
                                ),
                            ],
                            id = 'fig16b2-table-container',
                        ),

                    ],
                    id = 'main-container',
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label('Academic Analysis', style=label_style),
                                        dcc.Graph(id='no-data-fig', figure = blank_fig()) #, style={'margin-bottom': -20}),
                                    ],
                                    className = 'pretty_close_container twelve columns',
                                ),
                            ],
                            className='row'
                        ),
                    ],
                    id = 'empty-container',
                ),
            ],
            id='mainContainer',
            style={
                'display': 'flex',
                'flexDirection': 'column'
            }
        )