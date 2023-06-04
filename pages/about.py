#######################################
# ICSB Dashboard - About/Demographics #
#######################################
# author:   jbetley
# version:  1.03
# date:     5/22/23

import dash
from dash import dcc, html, dash_table, Input, Output, callback
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import numpy as np

from .chart_helpers import loading_fig, no_data_fig_label
from .table_helpers import no_data_table, no_data_page
from .load_data import school_index, ethnicity, subgroup, max_display_years, current_academic_year
from .load_db import get_finance, get_demographics, get_letter_grades

dash.register_page(__name__, path='/', order=0, top_nav=True)

@callback(
    Output('school-name', 'children'),
    Output('info-table', 'children'),
    Output('letter-grade-table', 'children'),
    Output('enroll-title', 'children'),
    Output('enroll-table', 'children'),
    Output('adm_fig', 'figure'),
    Output('ethnicity-title', 'children'),
    Output('ethnicity-fig', 'figure'),
    Output('subgroup-title', 'children'),
    Output('subgroup-fig', 'figure'),
    Output('about-main-container', 'style'),
    Output('about-empty-container', 'style'),
    Output('school-name-no-data', 'children'),
    Output('info-table-no-data', 'children'),    
    Output('about-no-data', 'children'),
    Input('year-dropdown', 'value'),
    Input('charter-dropdown', 'value'),
    # Input('dash-session', 'data')
)
def update_about_page(year: str, school: str):
    if not school:
        raise PreventUpdate

    # see color list in chart_helpers.py
    linecolor = ['#df8f2d']
    bar_colors = ['#74a2d7', '#df8f2d']

    main_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_to_display = no_data_page('School Enrollment & Demographics')

    selected_school = school_index.loc[school_index["School ID"] == school]
    school_name = selected_school['School Name'].values[0]
    headers = ['Category','Description']

    # school index df has additional values that can be added to this list
    # see selected_school.columns
    info = selected_school[['City','Principal','Opening Year']]

    school_info = info.T
    school_info = school_info.reset_index()
    school_info.columns = headers

    info_table = [
        dash_table.DataTable(
            school_info.to_dict('records'),
            columns = [{'name': i, 'id': i} for i in school_info.columns],
            style_table={
                'height': '20vh'
            },            
            style_data={
                'fontSize': '12px',
                'fontFamily': 'Jost, sans-serif',
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

    school_demographics = get_demographics(school)
    school_letter_grades = get_letter_grades(school)

    finance_file = get_finance(school)
    
    # clean up
    finance_file = finance_file.drop(['School ID','School Name'], axis=1)
    finance_file = finance_file.dropna(axis=1, how='all')

    school_financial_data = finance_file.copy()

    if len(school_letter_grades.index) == 0 and (len(school_demographics.index) == 0 & \
          len(school_financial_data.index) == 0):
        
        letter_grade_table = {}
        enroll_title = {}
        enroll_table = {}
        adm_fig = {}
        ethnicity_title = {}
        ethnicity_fig = {}
        subgroup_title = {}
        subgroup_fig = {}

        main_container = {'display': 'none'}
        empty_container = {'display': 'block'}

    else:

        # Enrollment table
        corp_id = selected_school['GEO Corp'].values[0]
        
        corp_demographics = get_demographics(corp_id)

        selected_year = str(year)
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

            school_demographics = school_demographics.loc[school_demographics["Year"] == int(year)]
            corp_demographics = corp_demographics.loc[corp_demographics["Year"] == int(year)]

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
                        'fontFamily': 'Jost, sans-serif',
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


        # create State and Federal ratings table
        if len(school_letter_grades.index) == 0:

            letter_grade_table = no_data_table('State and Federal Ratings')

        else:

            school_letter_grades = (
                school_letter_grades.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
        )

            year_columns = [str(i) for i in school_letter_grades.columns if i not in ['Category','2018']]

            # schools have been held harmless by the State of Indiana since
            # 2019, and continue to be held harmless (2019-2023). This builds
            # a list of all hold harmless years for the table tooltip.
            # NOTE: This will need to be re-configured once (if) the State
            # ever begins holding schools accountable again.
            if year_columns:
                year_columns.reverse()
                last_year = year_columns[-1]
                hold_harmless_years = year_columns.copy()
                hold_harmless_years.remove(last_year)

                if hold_harmless_years:
                    hold_harmless_year_string = ', '.join(hold_harmless_years) + ', and ' + last_year
                else:
                    hold_harmless_year_string = last_year

                hold_harmless_string = 'Schools were \'Held Harmless\' by the State in ' \
                    + hold_harmless_year_string + '. Under Hold Harmless, a school cannot receive a \
                    lower A-F grade than what it received for the previous school year.'
            else:
                hold_harmless_string =''

            letter_grade_table = [
                dash_table.DataTable(
                    school_letter_grades.to_dict('records'),
                    columns = [{'name': str(i), 'id': str(i)} for i in school_letter_grades.columns],
                    style_table={
                        'height': '20vh'
                    },
                    style_data={
                        'fontSize': '12px',
                        'fontFamily': 'Jost, sans-serif',
                        'border': 'none',
                    },
                    style_data_conditional=[
                        {
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
                        'fontFamily': 'Jost, sans-serif',
                        'color': '#6783a9',
                        'textAlign': 'center',
                        'fontWeight': 'bold'
                    },
                    style_cell={
                        'whiteSpace': 'normal',
                        'textAlign': 'center',
                        'color': '#6783a9',
                        'fontFamily': 'Jost, sans-serif',
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
                    tooltip_header={
                        col: [
                            {
                                'type': 'markdown',
                                'value': hold_harmless_string
                            }
                        ]
                        for col in year_columns
                    },
                    css=[{
                    'selector': '.dash-table-tooltip',
                    'rule': 'background-color: grey; font-family: Jost, sans-serif; color: white'
                    }],
                    style_as_list_view=True
                )
            ]

        # ADM chart

        if len(school_financial_data.index) == 0:

            adm_fig = no_data_fig_label('Average Daily Membership History',400)
        
        else:

            adm_values = school_financial_data[school_financial_data['Category'].str.contains('ADM Average')]
            adm_values = adm_values.drop('Category', axis=1)
            adm_values = adm_values.reset_index(drop=True)

            for col in adm_values.columns:
                adm_values[col] = pd.to_numeric(adm_values[col], errors="coerce")
            
            adm_values = adm_values.loc[:, (adm_values != 0).any(axis=0)]

            adm_values = adm_values[adm_values.columns[::-1]]

            # file exists, but there is no adm data
            if (int(adm_values.sum(axis=1).values[0]) == 0):

                adm_fig = no_data_fig_label('Average Daily Membership History',400)
            
            else:

                # ADM dataset can be longer than five years (maximum display), so
                # need to filter both the selected year (the year to display) and the
                # total # of years
                operating_years_by_adm = len(adm_values.columns)

                # if number of available years exceeds year_limit, drop excess columns (years)
                if operating_years_by_adm > max_display_years:
                    adm_values = adm_values.drop(columns = adm_values.columns[: (operating_years_by_adm - max_display_years)],axis=1)

                # 'excluded years' is a list of YYYY strings (all years more
                # recent than selected year) that can be used to filter data
                # that should not be displayed
                excluded_academic_years = current_academic_year - int(year)
                
                excluded_years = []
                
                for i in range(excluded_academic_years):
                    excluded_year = current_academic_year - i
                    excluded_years.append(str(excluded_year))
                
                # if the display year is less than current year
                # drop columns where year matches any years in 'excluded years' list
                if excluded_years:
                    adm_values = adm_values.loc[
                        :, ~adm_values.columns.str.contains("|".join(excluded_years))
                    ]

            # drop any columns with partial year data (e.g., 2023 (Q2)) because
            # they generally do not have reliable adm data.
            adm_values = adm_values[adm_values.columns.drop(list(adm_values.filter(regex='Q')))]
            
            # turn single row dataframe into two lists (column headers and data)
            adm_data=adm_values.iloc[0].tolist()
            years=adm_values.columns.tolist()

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
                    family='Jost, sans-serif',
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

            # Calculate Percentage
            for i in range(0, 2): 
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
                    family='Jost, sans-serif',
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
            subgroup_school = school_demographics.loc[:, (school_demographics.columns.isin(subgroup)) | (school_demographics.columns.isin(['Corporation Name','Total Enrollment']))]
            subgroup_corp = corp_demographics.loc[:, (corp_demographics.columns.isin(subgroup)) | (corp_demographics.columns.isin(['Corporation Name','Total Enrollment']))]
            subgroup_data = pd.concat([subgroup_school,subgroup_corp])

            total_enrollment=subgroup_data['Total Enrollment'].tolist()
            total_enrollment = [int(i) for i in total_enrollment]
            subgroup_data.drop('Total Enrollment',axis=1,inplace=True)

            cols=[i for i in subgroup_data.columns if i not in ['Corporation Name']]
            for col in cols:
                subgroup_data[col]=pd.to_numeric(subgroup_data[col], errors='coerce')

            # store categories with no data (NaN)
            subgroup_no_data = subgroup_data[subgroup_data.columns[subgroup_data.isna().any()]].columns.tolist()

            subgroup_data_t = subgroup_data.set_index('Corporation Name').T

            # Calculate Percentage
            for i in range(0, 2):
                subgroup_data_t.iloc[:,i] = subgroup_data_t.iloc[:,i] / total_enrollment[i]

            # force categories to wrap
            categories_wrap=['English<br>Language<br>Learners', 'Special<br>Education', 'Free/Reduced<br>Price Meals', 'Paid Meals']

            elements = subgroup_data_t.columns.tolist()

            trace_color = {elements[i]: bar_colors[i] for i in range(len(elements))}

            subgroup_fig = px.bar(
                data_frame = subgroup_data_t,
                x = [c for c in subgroup_data_t.columns],
                y = categories_wrap,
                text_auto=True,
                color_discrete_map=trace_color,
                opacity = 0.9,
                orientation = 'h',
                barmode = 'group',
            )
            subgroup_fig.update_xaxes(ticks='outside', tickcolor='#a9a9a9', range=[0, 1], dtick=0.2, tickformat=',.0%', title='')
            subgroup_fig.update_yaxes(ticks='outside', tickcolor='#a9a9a9', title='')

            # add text traces
            subgroup_fig.update_traces(textposition='outside')

            # Want to distinguish between null (no data) and '0'
            # so loop through data and only color text traces when the value of x (t.x) is not NaN
            # display all: subgroup_fig.for_each_trace(lambda t: t.update(textfont_color=t.marker.color,textfont_size=11))
            subgroup_fig.for_each_trace(lambda t: t.update(textfont_color=np.where(~np.isnan(t.x),t.marker.color, 'white'),textfont_size=11))

            subgroup_fig.update_traces(hovertemplate = None, hoverinfo='skip')

            # Uncomment to add hover
            #subgroup_fig['data'][0]['hovertemplate'] = subgroup_fig['data'][0]['name'] + ': %{x}<extra></extra>'
            #subgroup_fig['data'][1]['hovertemplate'] = subgroup_fig['data'][1]['name'] + ': %{x}<extra></extra>'

            subgroup_fig.update_layout(
                margin=dict(l=10, r=40, t=60, b=70,pad=0),
                font = dict(
                    family='Jost, sans-serif',
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

            if subgroup_no_data:
                subgroup_anno_txt = ', '.join(subgroup_no_data)

                subgroup_fig.add_annotation(
                    text = (f'Data not available: ' + subgroup_anno_txt + '.'),
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
            subgroup_fig = no_data_fig_label('Enrollment by Subgroup', 400)
            ethnicity_fig = no_data_fig_label('Enrollment by Ethnicity', 400)

    return school_name, info_table, letter_grade_table, \
        enroll_title, enroll_table, adm_fig, ethnicity_title, ethnicity_fig, \
        subgroup_title, subgroup_fig, main_container, empty_container, school_name,\
        info_table, no_data_to_display

layout = \
    html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [     
                                    html.Div(
                                        [
                                            html.Label(id='school-name', className = 'header_label'),
                                            html.Div(id='info-table'),
                                        ],
                                        className='pretty_container six columns'
                                    ),
                                    html.Div(
                                        [
                                            html.Label('State and Federal Ratings', className = 'header_label'),
                                            html.Div(id='letter-grade-table'),
                                        ],
                                        className='pretty_container six columns'
                                    ),
                                ],
                                className='bare_container twelve columns'
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
                                            html.Label(id='enroll-title', className = 'header_label'),
                                            html.Div(id='enroll-table')
                                        ],
                                        className='pretty_container six columns'
                                    ),
                                    html.Div(
                                        [
                                            html.Label('Average Daily Membership History', className = 'header_label'),
                                            dcc.Graph(id='adm_fig', figure = loading_fig(),config={'displayModeBar': False})
                                        ],
                                        className = 'pretty_container six columns'
                                    ),
                                ],
                                className='bare_container_no_center twelve columns',
                            ),
                        ],
                        className = 'row',
                    ),                    
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(id='subgroup-title', className = 'header_label'),
                                    dcc.Graph(id='subgroup-fig', figure = loading_fig(),config={'displayModeBar': False})
                                ],
                                className = 'pretty_container six columns'
                            ),
                            html.Div(
                                [
                                    html.Label(id='ethnicity-title', className = 'header_label'),
                                    dcc.Graph(id='ethnicity-fig', figure = loading_fig(),config={'displayModeBar': False})
                                ],
                                className = 'pretty_container six columns'
                            ),
                        ],
                        className='bare_container twelve columns',
                    ),
                ],
                id = 'about-main-container',
            ),
            html.Div(
                [
                    html.Div(
                        [    
                            html.Div(
                                [
                                    html.Label(id='school-name-no-data', className = 'header_label'),
                                    html.Div(id='info-table-no-data'),
                                ],
                                className='pretty_container eight columns'
                            ),
                        ],
                        className = 'bare_container twelve columns',
                    ),
                    html.Div(id='about-no-data'),
                ],
                id = 'about-empty-container',
            ),
        ],
        id='mainContainer'
    )