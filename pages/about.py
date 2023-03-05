#######################################
# ICSB Dashboard - About/Demographics #
#######################################
# author:   jbetley
# version:  .99.021323

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import numpy as np
import json

from .chart_helpers import loading_fig, no_data_fig
from .table_helpers import no_data_table, no_data_page

dash.register_page(__name__, path="/", order=0, top_nav=True)

## Callback ##
@callback(
    Output('school-name', 'children'),
    Output('info-table', 'children'),
    Output('letter-grade-table', 'children'),
    Output('hold-harmless-string', 'children'),
    Output('enroll-title', 'children'),
    Output('enroll-table', 'children'),
    Output('adm_fig', 'figure'),
    Output('ethnicity-title', 'children'),
    Output('ethnicity-fig', 'figure'),
    Output('subgroup-title', 'children'),
    Output('status-fig', 'figure'),
    Output('about-main-container', 'style'),
    Output('about-empty-container', 'style'),
    Output('about-no-data', 'children'),      
    State('year-dropdown', 'value'),
    Input('dash-session', 'data')
)
def update_about_page(year, data):
    if not data:
        raise PreventUpdate

    ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
    status = ['Special Education','General Education','Paid Meals','Free/Reduced Price Meals','English Language Learners','Non-English Language Learners']
    bar_colors=['#98abc5','#c5b298']

    main_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_to_display = no_data_page('Audited Financial Information')

    # the school index will never be empty, so this is displayed
    # even if there is no other data
    school_index = pd.DataFrame.from_dict(data['0'])

    school_name = school_index['School Name'].values[0]
    headers = ['Category','Description']

    # school index df has additional values that can be added to this list
    info = school_index[['City','Principal','Opening Year']]

    school_info = info.T
    school_info = school_info.reset_index()
    school_info.columns = headers

    info_table = [
                    dash_table.DataTable(
                        school_info.to_dict('records'),
                        columns = [{'name': i, 'id': i} for i in school_info.columns],
                        style_data={
                            'fontSize': '12px',
                            'fontFamily': 'Roboto, sans-serif',
                            'border': 'none'
                        },
                        style_data_conditional=[
                            {
                                'if': {
                                    'column_id': 'Category',
                                },
                                'borderRight': '.5px solid #6783a9',
                            },
                        ],
                        style_header={
                            'display': 'none',
                            'border': 'none',
                        },
                        style_cell={
                            'whiteSpace': 'normal',
                            'height': 'auto',
                            'textAlign': 'center',
                            'color': '#6783a9',
                            'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                        },
                    )
        ]

    # get enrollment data (overall and by category)
    school_demographics = pd.DataFrame.from_dict(data['1'])

    # get adm dict
    school_adm = pd.DataFrame.from_dict(data['6'])

    # data['3'] is a json file (School Letter Grades). There is
    # no data if the file does not exist. For dicts, we check the
    # length of the index. It will be [] if there is no data 
    # if all empty/not exist then we show info table + no_data_page
    if not data['3'] and (len(school_demographics.index) == 0 & \
          len(school_adm.index) == 0):
        
        letter_grade_table = {}
        hold_harmless_string = {}
        enroll_title = {}
        enroll_table = {}
        adm_fig = {}
        ethnicity_title = {}
        ethnicity_fig = {}
        subgroup_title = {}
        status_fig = {}

        print('Missing ALL the DATA!')

    else:
    # if one or more of the data files exist, we show info table
    # and individual data or empty tables/figs
    # school_letter_grades_dict (check to make sure json
    # exists before loading or else it will error)

        # Enrollment table
        selected_year = str(year)

        # school_demographics_selected_year_dict & corp_demographics_selected_year_dict
        # school_demographics = pd.DataFrame.from_dict(data['1'])
        corp_demographics = pd.DataFrame.from_dict(data['2'])

        current_year = selected_year
        previous_year = int(current_year) - 1
        year_string = str(previous_year) + '-' + str(current_year)[-2:]

        # Build figure titles
        enroll_title = 'Enrollment ' + '(' + year_string + ')'
        ethnicity_title = 'Enrollment by Ethnicity ' + '(' + year_string + ')'
        subgroup_title = 'Enrollment by Subgroup ' + '(' + year_string + ')'

        if len(school_demographics.index) == 0:
            enroll_table = no_data_table(enroll_title)

        else:
            enrollment_filter = school_demographics.filter(regex = r'^Grade \d{1}|[1-9]\d{1}$;|^Pre-K$|^Kindergarten$|^Total Enrollment$',axis=1)
            enrollment_filter = enrollment_filter[[c for c in enrollment_filter if c not in ['Total Enrollment']] + ['Total Enrollment']]
            enrollment_filter = enrollment_filter.dropna(axis=1, how='all')

            school_enrollment = enrollment_filter.T
            school_enrollment.rename(columns={school_enrollment.columns[0]:'Enrollment'}, inplace=True)
            school_enrollment.rename(index={'Total Enrollment':'Total'},inplace=True)

            school_enrollment = school_enrollment.reset_index()

            enroll_table = [
                            dash_table.DataTable(
                                school_enrollment.to_dict('records'),
                                columns = [{'name': i, 'id': i} for i in school_enrollment.columns],
                                style_data={
                                    'fontSize': '12px',
                                    'fontFamily': 'Roboto, sans-serif',
                                    'border': 'none'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {
                                            'row_index': 'odd'
                                        },
                                        'backgroundColor': '#eeeeee'
                                    },
                                    {
                                        'if': {
                                            'column_id': 'index',
                                        },
                                        'borderRight': '.5px solid #6783a9',
                                    },
                                    {
                                        'if': {
                                            'filter_query': '{index} eq "Total"'
                                        },
                                        'borderTop': '.5px solid #6783a9',
                                    }
                                ],
                                style_header={
                                    'display': 'none',
                                    'border': 'none',
                                },
                                style_cell={
                                    'whiteSpace': 'normal',
                                    'height': 'auto',
                                    'textAlign': 'center',
                                    'color': '#6783a9',
                                    'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                                },
                            )
            ]

        # State and Federal ratings table
        if not data['3']:
            hold_harmless_string = ''
            letter_grade_table = no_data_table('State and Federal Ratings')

        else:
            # school_letter_grades_dict
            letter_grade_json = json.loads(data['3'])
            letter_grade_data = pd.DataFrame.from_dict(letter_grade_json)

            # 2019 and 2020 were 'Hold Harmless' years for all schools
            if '2019' in letter_grade_data:
                hold_harmless_years = '2020 and 2019'
            else:
                hold_harmless_years = '2020'

            hold_harmless_string = 'Schools were \'Held Harmless\' in ' + hold_harmless_years + '. Under Hold Harmless, a school cannot receive a lower A-F grade than what the school received for the previous school year.'

            letter_grade_table = [
                        dash_table.DataTable(
                            letter_grade_data.to_dict('records'),
                            columns = [{'name': str(i), 'id': str(i)} for i in letter_grade_data.columns],
                            style_data={
                                'fontSize': '12px',
                                'fontFamily': 'Roboto, sans-serif',
                                'border': 'none'
                            },
                            style_data_conditional=[
                                {   # Kludge to ensure first col header has border
                                    'if': {
                                        'row_index': 0,
                                        'column_id': 'Category'
                                    },
                                    'borderTop': '.5px solid #6783a9',
                                },
                                {
                                    'if': {
                                        'row_index': 'odd'
                                    },
                                    'backgroundColor': '#eeeeee'
                                },
                            ],
                            style_header={
                                'height': '20px',
                                'backgroundColor': '#ffffff',
                                'border': 'none',
                                'borderBottom': '.5px solid #6783a9',
                                'fontSize': '12px',
                                'fontFamily': 'Roboto, sans-serif',
                                'color': '#6783a9',
                                'textAlign': 'center',
                                'fontWeight': 'bold'
                            },
                            style_cell={
                                'whiteSpace': 'normal',
                                'textAlign': 'center',
                                'color': '#6783a9',
                                'fontFamily': 'Roboto, sans-serif',
                                'boxShadow': '0 0',
                                'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                            },
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Category'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '20px',
                                    'width': '35%',
                                },
                            ],
                            style_as_list_view=True
                        )
            ]

        # ADM chart
        linecolor=['#d0743c','#a05d56']

        # school_adm_dict
        # school_adm = pd.DataFrame.from_dict(data['6'])

        if len(school_adm.index) == 0:
            adm_fig = {
                'layout': {
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
                                'color': '#6783a9',
                                'family': 'Roboto, sans-serif',
                            }
                        }
                    ]
                }
            }
        else:

            # turn single row dataframe into two lists (column headers and data)
            adm_data=school_adm.iloc[0].tolist()
            years=school_adm.columns.tolist()

            # create chart
            adm_fig = px.line(
                x=years,
                y=adm_data,
                markers=True,
                color_discrete_sequence=linecolor,
            )
            adm_fig.update_traces(mode='markers+lines', hovertemplate=None)
            adm_fig['data'][0]['showlegend']=True
            adm_fig['data'][0]['name']='ADM Average'
            adm_fig.update_yaxes(title='', showgrid=True, gridcolor='#b0c4de')
            adm_fig.update_xaxes(ticks='outside', tickcolor='#b0c4de', title='')

            adm_fig.update_layout(
                margin=dict(l=40, r=40, t=40, b=40),
                font = dict(
                    family='Roboto, sans-serif',
                    color='#6783a9',
                    size=12
                    ),
                hovermode='x unified',
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )

        # Enrollment by ethnicity chart
        ethnicity_school = school_demographics.loc[:, (school_demographics.columns.isin(ethnicity)) | (school_demographics.columns.isin(['Corporation Name','Total Enrollment']))].copy()
        ethnicity_corp = corp_demographics.loc[:, (corp_demographics.columns.isin(ethnicity)) | (corp_demographics.columns.isin(['Corporation Name','Total Enrollment']))].copy()

        if not ethnicity_school.empty:

            ethnicity_school.rename(columns = {'Native Hawaiian or Other Pacific Islander': 'Pacific Islander'}, inplace = True)
            ethnicity_corp.rename(columns = {'Native Hawaiian or Other Pacific Islander': 'Pacific Islander'}, inplace = True)

            ethnicity_data = pd.concat([ethnicity_school,ethnicity_corp])

            # Only need to calculate total enrollment once
            total_enrollment=ethnicity_data['Total Enrollment'].tolist()
            total_enrollment = [int(i) for i in total_enrollment]
            ethnicity_data.drop('Total Enrollment',axis=1,inplace=True)

            cols = [i for i in ethnicity_data.columns if i not in ['Corporation Name']]

            for col in cols:
                ethnicity_data[col]=pd.to_numeric(ethnicity_data[col], errors='coerce')

            ethnicity_data_t = ethnicity_data.set_index('Corporation Name').T

            for i in range(0, 2): # Calculate Percentage
                ethnicity_data_t.iloc[:,i] = ethnicity_data_t.iloc[:,i] / total_enrollment[i]

            # Find rows where percentage is < .005 (1% after rounding) - and create string for annotation purposes
            no_show = ethnicity_data_t[((ethnicity_data_t.iloc[:, 0] < .005) | (pd.isnull(ethnicity_data_t.iloc[:, 0])) & (ethnicity_data_t.iloc[:, 1] < .005) | (pd.isnull(ethnicity_data_t.iloc[:, 1])))]
            ethnicity_anno_txt = ', '.join(no_show.index.values.astype(str))

            # Drop rows that meet the above condition
            ethnicity_data_t = ethnicity_data_t.drop(ethnicity_data_t[((ethnicity_data_t.iloc[:, 0] < .005) | (pd.isnull(ethnicity_data_t.iloc[:, 0])) & (ethnicity_data_t.iloc[:, 1] < .005) | (pd.isnull(ethnicity_data_t.iloc[:, 1])))].index)

            # replace any remaining NaN with 0
            ethnicity_data_t = ethnicity_data_t.fillna(0)

            categories = ethnicity_data_t.index.tolist()
            elements = ethnicity_data_t.columns.tolist()

            trace_color = {elements[i]: bar_colors[i] for i in range(len(elements))}

            ethnicity_fig = px.bar(
                data_frame = ethnicity_data_t,
                x = [c for c in ethnicity_data_t.columns],
                y = categories,
                text_auto=True,
                color_discrete_map=trace_color,
                opacity = 0.9,
                orientation = 'h',
                barmode = 'group'
            )
            ethnicity_fig.update_xaxes(ticks='outside', tickcolor='#a9a9a9', range=[0, 1], dtick=0.2, tickformat=',.0%', title='')
            ethnicity_fig.update_yaxes(ticks='outside', tickcolor='#a9a9a9', title='')
            ethnicity_fig.update_traces(textposition='outside')
            ethnicity_fig.for_each_trace(lambda t: t.update(textfont_color=t.marker.color,textfont_size=11))
            ethnicity_fig.update_traces(hovertemplate = None, hoverinfo='skip')

            # Uncomment to add hover
            #ethnicity_fig['data'][0]['hovertemplate'] = ethnicity_fig['data'][0]['name'] + ': %{x}<extra></extra>'
            #ethnicity_fig['data'][1]['hovertemplate'] = ethnicity_fig['data'][1]['name'] + ': %{x}<extra></extra>'

            ethnicity_fig.update_layout(
                margin=dict(l=10, r=40, t=60, b=70,pad=0),
                font = dict(
                    family='Roboto, sans-serif',
                    color='#6783a9',
                    size=11
                    ),
                legend=dict(
                    yanchor='top',
                    xanchor= 'center',
                    orientation='h',
                    x=.4,
                    y=1.2
                ),
                bargap=.15,
                bargroupgap=0,
                height=400,
                legend_title='',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )

            ethnicity_fig.add_annotation(
                text = (f'Less than .05% of student population: ' + ethnicity_anno_txt + '.'),
                showarrow=False,
                x = -0.1,
                y = -0.25,
                xref='paper',
                yref='paper',
                xanchor='left',
                yanchor='bottom',
                xshift=-1,
                yshift=-5,
                font=dict(size=10, color='#6783a9'),
                align='left'
            )

            # Enrollment by subgroup chart
            status_school = school_demographics.loc[:, (school_demographics.columns.isin(status)) | (school_demographics.columns.isin(['Corporation Name','Total Enrollment']))]
            status_corp = corp_demographics.loc[:, (corp_demographics.columns.isin(status)) | (corp_demographics.columns.isin(['Corporation Name','Total Enrollment']))]
            status_data = pd.concat([status_school,status_corp])

            total_enrollment=status_data['Total Enrollment'].tolist()
            total_enrollment = [int(i) for i in total_enrollment]
            status_data.drop('Total Enrollment',axis=1,inplace=True)

            cols=[i for i in status_data.columns if i not in ['Corporation Name']]
            for col in cols:
                status_data[col]=pd.to_numeric(status_data[col], errors='coerce')

            # store categories with no data (NaN)
            status_no_data = status_data[status_data.columns[status_data.isna().any()]].columns.tolist()

            status_data_t = status_data.set_index('Corporation Name').T

            for i in range(0, 2): # Calculate Percentage
                status_data_t.iloc[:,i] = status_data_t.iloc[:,i] / total_enrollment[i]

            # this forces the categories to wrap (use 'categories' for no wrap)
            # categories = status_data_t.index.tolist()

    # TODO:
            # Use this function to create wrapped text using
            # html tags based on the specified width
            import textwrap

            def customwrap(s,width=16):
                return "<br>".join(textwrap.wrap(s,width=width))

            categories_wrap=['English<br>Language<br>Learners', 'Special<br>Education', 'Free/Reduced<br>Price Meals', 'Paid Meals']

            elements = status_data_t.columns.tolist()

            trace_color = {elements[i]: bar_colors[i] for i in range(len(elements))}

            status_fig = px.bar(
                data_frame = status_data_t,
                x = [c for c in status_data_t.columns],
                y = categories_wrap,
                text_auto=True,
                color_discrete_map=trace_color,
                opacity = 0.9,
                orientation = 'h',
                barmode = 'group',
            )
            status_fig.update_xaxes(ticks='outside', tickcolor='#a9a9a9', range=[0, 1], dtick=0.2, tickformat=',.0%', title='')
            status_fig.update_yaxes(ticks='outside', tickcolor='#a9a9a9', title='')

            # add text traces
            status_fig.update_traces(textposition='outside')

            # Want to distinguish between null (no data) and '0'
            # so loop through data and only color text traces when the value of x (t.x) is not NaN
            # display all: status_fig.for_each_trace(lambda t: t.update(textfont_color=t.marker.color,textfont_size=11))
            status_fig.for_each_trace(lambda t: t.update(textfont_color=np.where(~np.isnan(t.x),t.marker.color, 'white'),textfont_size=11))

            status_fig.update_traces(hovertemplate = None, hoverinfo='skip')

            # Uncomment below to add hover
            #status_fig['data'][0]['hovertemplate'] = status_fig['data'][0]['name'] + ': %{x}<extra></extra>'
            #status_fig['data'][1]['hovertemplate'] = status_fig['data'][1]['name'] + ': %{x}<extra></extra>'

            status_fig.update_layout(
                margin=dict(l=10, r=40, t=60, b=70,pad=0),
                font = dict(
                    family='Roboto, sans-serif',
                    color='#6783a9',
                    size=11
                    ),
                legend=dict(
                    yanchor='top',
                    xanchor= 'center',
                    orientation='h',
                    x=.4,
                    y=1.2
                ),
                bargap=.15,
                bargroupgap=0,
                height=400,
                legend_title='',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )

            if status_no_data:
                status_anno_txt = ', '.join(status_no_data)

                status_fig.add_annotation(
                    text = (f'Data not available: ' + status_anno_txt + '.'),
                    showarrow=False,
                    x = -0.1,
                    y = -0.25,
                    xref='paper',
                    yref='paper',
                    xanchor='left',
                    yanchor='bottom',
                    xshift=-1,
                    yshift=-5,
                    font=dict(size=10, color='#6783a9'),
                    align='left'
                )

        else:
            status_fig = ethnicity_fig = {
                'layout': {
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
                                'color': '#6783a9',
                                'family': 'Roboto, sans-serif',
                            }
                        }
                    ]
                }
            }

    return school_name, info_table, letter_grade_table, hold_harmless_string, \
        enroll_title, enroll_table, adm_fig, ethnicity_title, ethnicity_fig, \
        subgroup_title, status_fig, main_container, empty_container, no_data_to_display

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

layout = html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(id='school-name', style=label_style),
                                html.Div(id='info-table'),
                            ],
                            className='pretty_container six columns'
                        ),
                        html.Div(
                            [
                                html.Label('State and Federal Ratings', style=label_style),
                                html.Div(id='letter-grade-table'),
                                html.P(id='hold-harmless-string',
                                style={
                                    'color': '#6783a9',
                                    'fontSize': 10,
                                    'marginLeft': '10px',
                                    'marginRight': '10px',
                                    'marginTop': '10px',
                                    # 'borderTop': '.5px solid #c9d3e0',
                                    }
                                )
                            ],
                            className='pretty_container six columns'
                        ),
                    ],
                    className='bare_container twelve columns'
                ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(id='enroll-title', style=label_style),
                                    html.Div(id='enroll-table')
                                ],
                                className='pretty_container six columns'
                            ),
                            html.Div(
                                [
                                    html.Label('Average Daily Membership History', style=label_style),
                                    dcc.Graph(id='adm_fig', figure = loading_fig(),config={'displayModeBar': False}) # figure={}
                                ],
                                className = 'pretty_container six columns'
                            ),
                        ],
                        className='bare_container twelve columns',
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(id='subgroup-title', style=label_style),
                                    dcc.Graph(id='status-fig', figure = loading_fig(),config={'displayModeBar': False}) # figure={}
                                ],
                                className = 'pretty_container six columns'
                            ),
                            html.Div(
                                [
                                    html.Label(id='ethnicity-title', style=label_style),
                                    dcc.Graph(id='ethnicity-fig', figure = loading_fig(),config={'displayModeBar': False}) # figure={}
                                ],
                                className = 'pretty_container six columns'
                            ),
                        ],
                        className='bare_container twelve columns',
                    ),
                ],
                id='mainContainer',
                style={
                    'display': 'flex',
                    'flexDirection': 'column'
                }
            )