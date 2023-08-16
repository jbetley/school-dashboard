#######################################
# ICSB Dashboard - Charting Functions #
#######################################
# author:   jbetley
# version:  1.09
# date:     08/14/23

import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html, dcc
from .calculations import check_for_insufficient_n_size, check_for_no_data
from .string_helpers import customwrap
import time

# Colors
# https://codepen.io/ctf0/pen/BwLezW

# Steelblue
#color=['#98abc5','#919ab6','#8a89a6','#837997','#7b6888','#73587a','#6b486b','#865361','#a05d56','#b86949','#d0743c','#e8801e','#ff8c00']

color= ['#74a2d7', '#df8f2d','#96b8db','#ebbb81','#bc986a','#a8b462','#f0c33b','#74a2d7','#f0c33b','#83941f','#7b6888']

def no_data_fig_blank() -> dict:
    """
    Creates a blank fig with no label

    Returns:
        fig (dict): plotly figure dict
    """
    fig = go.Figure()
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=0),
        height = 400,
        xaxis =  {
            'visible': False,
            'fixedrange': True
        },
        yaxis =  {
            'visible': False,
            'fixedrange': True
        },
        annotations = [
            {
                'text': 'No Data to Display . . .',
                'y': 0.5,
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {
                    'size': 16,
                    'color': '#6783a9',
                    'family': 'Jost, sans-serif'
                }
            }
        ],
        dragmode = False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def loading_fig() -> dict:
    """
    Creates a blank fig with no title and 'Loading . . .' string only

    Returns:
        fig (dict): plotly figure dict
    """

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
                        'family': 'Jost, sans-serif'
                    }
                }
            ]
        }
    }

    return fig

def no_data_fig_label(label: str = 'No Data to Display', height: int = 400) -> list:
    """
    Creates a blank fig with with a label and default height

    Args:
        label (str, optional): figure label. Defaults to 'No Data to Display'.
        height (int, optional): figure height. Defaults to 400.

    Returns:
        fig_layout (list): a dash html.Div with an html.Label object and dcc.Graph plotly figure dict
    """

    fig = go.Figure()
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=0),
        height = height,
        xaxis =  {
            'visible': False,
            'fixedrange': True
        },
        yaxis =  {
            'visible': False,
            'fixedrange': True
        },
        annotations = [
            {
                'text': 'No Data to Display . . .',
                'y': 0.5,
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {
                    'size': 16,
                    'color': '#6783a9',
                    'family': 'Jost, sans-serif'
                }
            }
        ],
        dragmode = False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig_layout = [
        html.Div(
            [
                html.Label(label, className = 'header_label'),
                dcc.Graph(figure = fig),
            ]
        )
    ]

    return fig_layout

def make_stacked_bar(values: pd.DataFrame, label: str) -> list:
    """
    Create a layout with a 100% stacked bar chart showing proficiency percentages for
    all academic categories

    Args:
        values (pd.DataFrame): a dataframe with categories, proficiency categories, and proficiency percentages
        label (str): title of the figure

    Returns:
        list: a plotly dash html layout in the form of a list containing a string and a stacked bar chart figure (px.bar)
    """

    t12 = time.process_time()

    data = values.copy()
    stacked_color = ['#df8f2d', '#ebbb81', '#96b8db', '#74a2d7']
    
    # In order to get the total_tested value into hovertemplate
    # without displaying it on the chart, we need to pull the
    # Total Tested values out of the dataframe and into a new
    # column.
    total_tested = data[data['Proficiency'].str.contains('Total Tested')]

    # Merge the total tested values with the existing dataframe
    # This adds 'percentage_x' and 'percentage_y' columns.
    # 'percentage_y' is equal to the Total Tested Values
    data = pd.merge(data, total_tested[['Category','Percentage']], on=['Category'], how='left')

    # rename the columns (percentage_x to Percentage & percentage_y to Total Tested)
    data.columns = ['Category','Percentage','Proficiency','Total Tested']

    # drop the Total Tested Rows
    data = data[data['Proficiency'].str.contains('Total Tested') == False]

    # Remove subject substring ('ELA' or 'Math') from Proficiency column
    data['Proficiency'] = data['Proficiency'].str.split().str[1:].str.join(' ')

    fig = px.bar(
        data,
        x = data['Percentage'],
        y = data['Category'].map(customwrap),
        color=data['Proficiency'],
        barmode='stack',
        text=[f'{i}%' for i in data['Percentage']],
        orientation='h',
        color_discrete_sequence = stacked_color,
        height=240,
    )

    # the uniformtext_minsize and uniformtext_mode settings hide bar chart
    # text (Percentage) if the size of the chart causes the text of the font
    # to decrease below 8px. The text is positioned 'inside' the bar due to
    # the 'textposition' variable

    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=0),
        font_family='Jost, sans-serif',
        font_color='steelblue',
        font_size = 9,
        bargroupgap = 0,
        showlegend = False,
        plot_bgcolor='white',
        hovermode='y unified',
        yaxis=dict(autorange='reversed'),
        uniformtext_minsize = 9,
        uniformtext_mode='hide'
    )

    # TODO: remove hover 'title' and, if possible, replace with: 'Total Tested: {z}'
    # https://stackoverflow.com/questions/59057881/how-to-customize-hover-template-on-with-what-information-to-show
    # fig.update_layout(hovermode='x unified')

    fig.update_traces(
        textfont_size = 9,
        insidetextanchor = 'middle',
        textposition='inside',
        marker_line=dict(width=0),
        hovertemplate='%{text}',
        hoverinfo='none',
    )

    fig.update_xaxes(title='', showticklabels=False)

    # ticksuffix increases the space between the end of the tick label and the chart
    fig.update_yaxes(title='',ticksuffix = '  ')

    fig_layout = [
        html.Div(
            [
                html.Label(label, className = 'header_label'),
                dcc.Graph(
                    figure = fig,
                    config={
                        'displayModeBar': False,
                        'showAxisDragHandles': False,
                        'showAxisRangeEntryBoxes': False,
                        'scrollZoom': False
                    }
                )
            ]
        )
    ]

    print(f'Time to process stacked bar chart: ' + str(time.process_time() - t12))    
    return fig_layout

def make_line_chart(values: pd.DataFrame, label: str) -> list:
    """
    Creates a dash html.Div layout with a label, a basic line (scatter) plot (px.line), and a
    series of strings (if applicable) detailing missing data.

    Args:
        values (pd.DataFrame): a dataframe with proficiency categories for each year
        label (str): title of the figure

    Returns:
        fig_layout (list): a plotly dash html layout in the form of a list containing a string, a px.line figure,
        and another string(s) if certain conditions are met.
    """

    t9 = time.process_time()
    
    data = values.copy()

    data.columns = data.columns.str.split('|').str[0]
    cols=[i for i in data.columns if i not in ['School Name','Year']]

    if (len(cols)) > 0:

        # NOTE: Currently insufficient n-size and no data information is displayed below
        # the fig in the layout. Would prefer to somehow add this to the actual
        # trace (x-unified) hover, but it doesn't currently seem to be possible.
        # https://community.plotly.com/t/customizing-text-on-x-unified-hovering/39440/19
        data, no_data_string = check_for_no_data(data)
        nsize_string = check_for_insufficient_n_size(data)

        for col in cols:
            data[col]=pd.to_numeric(data[col], errors='coerce')

        data.sort_values('Year', inplace=True)

        # One last check, if there is only one year of data being displayed, we need to drop
        # all columns with only NaN- otherwise the traces will be displayed on the chart
        # even though they are listed as having no data to display - afterwards we need
        # to reset the cols variable to make sure it matches the changed df
        if len(data.index) == 1:
            data = data.dropna(axis=1, how='all')
            cols=[i for i in data.columns if i not in ['School Name','Year']]

        data = data.reset_index(drop=True)
        
        # If the initial df has data, but after dropping all no data rows is then
        # empty, we return an empty layout
        if data.empty:

            fig = no_data_fig_blank()
            fig_layout = [
                html.Div(
                    [
                        html.Div(
                            [
                            html.Label(label, className = 'header_label'),
                            dcc.Graph(figure = fig, config={'displayModeBar': False})
                            ],
                        ),
                    ]
                )
            ]
        
        else:

            # TODO: Fix irregular axis lines (why is this so hard??)
            # NOTE: Plotly displays two years of data with the year axis near the edges, which is ugly
            # have tried numerous things to fix it, but none of them are satisfactory
            
            # attempt #1
            # when we only have 2 years of data, we add two additiona blank years on either side
            # of the range. Doesn't look that great
            # data_years = data['Year'].astype(int).tolist()
            # add_years = [data_years[len(data_years)-1]+1,data_years[0]-1]
            # if len(data_years) == 2:
            #     for y in add_years:
            #         data = pd.concat(
            #             [
            #                 data,
            #                 pd.DataFrame(
            #                     np.nan,
            #                     columns=data.columns,
            #                     index=range(1),
            #                 ),
            #             ],
            #             ignore_index=True,
            #         )
            #         data.at[data.index[-1], 'Year'] = y


            # attempts #2-7
            # fig.update_xaxes(constrain='domain')
            # fig.update_xaxes(autorange='reversed')
            # fig.update_xaxes(range=[2021, 2022])
            # fig.update_xaxes(constraintoward='center')
            # fig.update_xaxes(anchor='free')
            # fig.update_yaxes(position=.5)

            fig = px.line(
                data,
                x='Year',
                y=cols,
                markers=True,
                color_discrete_sequence=color,
                # custom_data = ['N_size']
            )

            # fig.update_traces(hovertemplate= 'Year=%{x}<br>value=%{y}<br>%{customdata}<extra></extra>''')
            fig.update_traces(hovertemplate=None)   # type: ignore
            fig.update_layout(                      # type: ignore
                margin=dict(l=40, r=40, t=40, b=0),
                title_x=0.5,
                font = dict(
                    family = 'Jost, sans-serif',
                    color = 'steelblue',
                    size = 12
                    ),
                plot_bgcolor='white',
                xaxis = dict(
                    title='',
                    type='date',
                    # tickmode = 'array',
                    # tickmode = 'linear',
                    tickvals = data['Year'],
                    tickformat='%Y',
                    # tick0 = data['Year'][0] - 1,
                    # dtick ='M6',
                    # categoryorder = 'array',
                    # categoryarray = data['Year'],
                    mirror=True,
                    showline=True,
                    linecolor='#b0c4de',
                    linewidth=.5,
                    gridwidth=.5,
                    showgrid=True,
                    gridcolor='#b0c4de',
                    zeroline=False,
                    # range = add_years
                    ),   
                legend=dict(
                    orientation='h'
                ),
                hovermode='x unified',
                height=400,
                legend_title='',
            )

            # NOTE: Set the range based on the highest single value in the dataframe. IREAD is set to 100%.
            # At higher ranges, the values compress together and are hard to read (unfortunately).
            data_max = data.max(numeric_only=True).max()

            if "IREAD Proficiency (Grade 3 only)" in data.columns:
                range_vals = [0,1]  # type: list[float]
            elif data_max < .5:
                range_vals = [0,.5] 
            else:
                range_vals = [0,data_max + .1]

            fig.update_yaxes(       # type: ignore
                title='',
                mirror=True,
                showline=True,
                linecolor='#b0c4de',
                linewidth=.5,
                gridwidth=.5,
                showgrid=True,
                gridcolor='#b0c4de',
                zeroline=False,
                range=range_vals, 
                dtick=.2,
                tickformat=',.0%',
            )

            if nsize_string and no_data_string:

                fig_layout = [
                    html.Div(
                        [
                            html.Div(
                                [
                                html.Label(label, className = 'header_label'),
                                dcc.Graph(figure = fig, config={'displayModeBar': False})
                                ],
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.P(
                                                children=[
                                                html.Span('Years with insufficient or no data:', className = 'nsize_string_label'),
                                                html.Span(no_data_string, className = 'no_data_string'),
                                                ],
                                            ),
                                            html.P(
                                                children=[
                                                html.Span('Insufficient n-size:', className = 'nsize_string_label'),
                                                html.Span(nsize_string, className = 'nsize_string'),
                                                ],
                                            ),
                                        ],
                                        className = 'close_clean_container twelve columns'
                                    )
                                ],
                                className='row'
                            ),
                        ]
                    )
                ]

            elif nsize_string and not no_data_string:

                fig_layout = [
                    html.Div(
                        [
                            html.Div(
                                [
                                html.Label(label, className = 'header_label'),
                                dcc.Graph(figure = fig, config={'displayModeBar': False})
                                ],
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [                              
                                            html.P(
                                                children=[
                                                html.Span('Insufficient n-size:', className = 'nsize_string_label'),
                                                html.Span(nsize_string, className = 'nsize_string'),
                                                ],
                                            ),
                                        ],
                                        className = 'close_clean_container twelve columns'
                                    )
                                ],
                                className='row'
                            ),
                        ]
                    )
                ]

            elif no_data_string and not nsize_string:
                
                fig_layout = [
                    html.Div(
                        [
                            html.Div(
                                [
                                html.Label(label, className = 'header_label'),
                                dcc.Graph(figure = fig, config={'displayModeBar': False})
                                ],
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.P(
                                                children=[
                                                html.Span('Years with insufficient or no data:', className = 'nsize_string_label'),
                                                html.Span(no_data_string, className = 'no_data_string'),
                                                ],
                                            ),
                                        ],
                                        className = 'close_clean_container twelve columns'
                                    )
                                    ],
                                    className='row'
                                ),
                        ]
                    )
                ]

            else:  

                fig_layout = [
                    html.Div(
                        [
                        html.Label(label, className = 'header_label'),
                        dcc.Graph(figure = fig, config={'displayModeBar': False})
                        ],
                    )
                ]

    else:

        fig = no_data_fig_blank()
        
        fig_layout = [
                html.Div(
                    [
                        html.Div(
                            [
                            html.Label(label, className = 'header_label'),
                            dcc.Graph(figure = fig, config={'displayModeBar': False})
                            ],
                        ),
                        ]
                    )
            ]

    print(f'Processing line chart: ' + str(time.process_time() - t9))
    
    return fig_layout

def make_growth_chart(data_me: pd.DataFrame, data_162: pd.DataFrame, label: str) -> list:
    """
    Creates a dash html.Div layout with a label, and a multi-line (scatter) plot (px.line) representing
    two discrete dataframes in solid and dotted lines

    Args:
        data_162 (pd.DataFrame): growth data representing students enrolled at a school for at least 162 days
        data_me (pd.DataFrame): growth data for students enrolled at a school for a majority of days
        label (str): title of the figure

    Returns:
        fig_layout (list): a plotly dash html layout in the form of a list containing a label and a px.line figure
    """

    data_me.columns = data_me.columns.map(lambda x: x.split("|")[0])
    data_162.columns = data_162.columns.map(lambda x: x.split("|")[0])

    color = ['#74a2d7', '#df8f2d','#96b8db','#ebbb81','#bc986a','#a8b462','#f0c33b','#74a2d7','#f0c33b','#83941f','#7b6888']
    
    fig = make_subplots() #specs=[[{"secondary_y": False}]]

    if 'Growth' in label:
        ytick ='.0%'
        ytitle='Adequate Growth %'
        hover = '.2%'
    elif 'SGP' in label:
        ytick ='.1f'
        ytitle='Median SGP'
        hover = '.1f'

    for i, col in enumerate(data_me.columns):
        fig.add_trace(
            go.Scatter(
                x=data_me.index,
                y=data_me[col],
                name=col,
                meta=[col], # wtf is this?? [https://community.plotly.com/t/hovertemplate-does-not-show-name-property/36139]
                mode='markers+lines',
                marker=dict(color=color[i], symbol = 'square'),
                line={'dash': 'solid'},
                customdata = [f'{i:.2%}' for i in data_162[col]] if 'Growth' in label else [f'{i:.1f}' for i in data_162[col]],
                text = [f'{i}' for i in data_me.columns],
                # NOTE: the legendgroup variable separates each dataframe into a separate
                # legend group, which is great because it allows you to turn on and off each
                # group. However, it looks bad because it does not currently allow you to display
                # the legends horizontally. Matter of preference
                # legendgroup = '1',    
                # legendgrouptitle_text="Majority Enrolled"
            ),
            secondary_y=False,
        )

        # NOTE: This adds scatter traces for the 162-Day data
        # fig.add_trace(
        #     go.Scatter(
        #         x=data_162.index,
        #         y=data_162[col],
        #         mode='markers+lines',                                
        #         line={'dash': 'dash'},
        #         marker=dict(color=color[i], symbol = 'diamond'),
        #         name=col,
        #         legendgroup = '2',
        #         legendgrouptitle_text="162 Days"
        #     ),
        #     secondary_y=False,
        # )

    # Add figure title
    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=0),
        title_x=0.5,
        font = dict(
            family = 'Jost, sans-serif',
            color = 'steelblue',
            size = 10
            ),
        plot_bgcolor='white',
        xaxis = dict(
            title='',
            type='date',
            tickvals = data_me.index,
            tickformat='%Y',
            showline=True,
            linecolor='#b0c4de',
            linewidth=.5,
            gridwidth=.5,
            showgrid=True,
            gridcolor='#b0c4de',
            zeroline=False,
            # range = add_years
            ),
        yaxis = dict(
            title='',
            tickformat=ytick,
            showline=True,
            linecolor='#b0c4de',
            linewidth=.5,
            gridwidth=.5,
            showgrid=True,
            gridcolor='#b0c4de',
            zeroline=False,
            hoverformat=hover, 
            # range = add_years
            ),
        legend=dict(
            orientation='h'
        ),
        hovermode='x unified',
        height=300,
        # width=400,
        # legend_title='',
    )                    
    fig.update_traces(
        hovertemplate='<br>'.join(
            [
                s.replace(' ', '&nbsp;')
                for s in [
                    '%{meta} (Majority Enrolled): <b>%{y}</b> (162 Days: %{customdata})<br><extra></extra>',
                ]
            ]
        )
    )
    # NOTE: annotation is used as a master legend to identify 162-day vs 162-ME scatter lines
    # diamond - &#9670;	&#x25C6;
    # square - &#9632;	&#x25A0;
    # fig.add_annotation(
    #     text="Students Enrolled For: <b>&#9670;: 162 Days &#9632;: Majority Enrolled</b>",
    #     align="left",
    #     showarrow=False,
    #     xref="paper",
    #     yref="paper",
    #     font=dict(color="steelblue", size = 11),
    #     bgcolor="rgba(0,0,0,0)",
    #     y=1.15,
    #     x=.5,
    #     xanchor="center",
    # )

    fig.update_yaxes(title_text=ytitle, secondary_y=False)

    fig_layout = [
                html.Div(
                    [
                    # html.Label(label, className = 'header_label'),
                    dcc.Graph(figure = fig, config={'displayModeBar': False})
                    ],      
                )
    ]

    return fig_layout

def make_bar_chart(values: pd.DataFrame, category: str, school_name: str, label: str) -> list:
    """
    Creates a dash html.Div layout with a label and a simple bar chart (px.bar)

    Args:
        values (pd.DataFrame): a dataframe with a list of schools and proficiency values
            for a given category
        category (str): the category being compared
        school_name (str): the name of the selected school
        label (str): the title of the figure

    Returns:
        fig_layout (list): a plotly dash html layout in the form of a list containing a string and px.bar figure
    """

    data = values.copy()

    # NOTE: Unless the entire page is blank, e.g., no data at all, the
    # dataframe for this chart should never be blank due to error
    # handling in the calling script. However, we know that 'should never'
    # is code for 'almost with certainty' so we test here too.

    # the dataframe should always have at least 4 columns ('School Name',
    # 'Low Grade', 'High Grade' & one data column)
    if (len(data.columns)) > 3:
        schools = data['School Name'].tolist()

        # assign colors for each comparison school
        trace_color = {schools[i]: color[i] for i in range(len(schools))}

        # use specific color for selected school
        for key, value in trace_color.items():
            if key == school_name:
                trace_color[key] = '#0a66c2'

        # Uncomment this and below to display distance from selected school
        # data['Distance'] = pd.Series(['{:,.2f}'.format(val) for val in data['Distance']], index = data.index)

        fig = px.bar(
            data,
            x='School Name',
            y=category,
            color_discrete_map=trace_color,
            color='School Name',
            custom_data  = ['Low Grade','High Grade'], #,'Distance']
            text_auto=True
        )

        fig.update_yaxes(range=[0, 1], dtick=0.2, tickformat=',.0%',title='',showgrid=True, gridcolor='#b0c4de')
        fig.update_xaxes(type='category', showticklabels=False, title='',showline=True,linewidth=1,linecolor='#b0c4de')

        fig.update_layout(
            title_x=0.5,
            margin=dict(l=40, r=40, t=40, b=60),
            font = dict(
                family='Jost, sans-serif',
                color='steelblue',
                size = 11
                ),
            legend=dict(
                orientation='h',
                title='',
                xanchor= 'center',
                x=0.45
            ),
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hoverlabel=dict(
                bgcolor='white',
                font_color='steelblue',
                font_size=11,
                font_family='Jost, sans-serif',
            ),
            hoverlabel_align = 'left'
        )

        fig.update_traces(
            textposition='outside',
            hovertemplate = '<b>%{x}</b> (Grades %{customdata[0]} - %{customdata[1]})<br><b>Proficiency: </b>%{y}<br><extra></extra>'
        )

    else:

        fig = no_data_fig_blank()

    fig_layout = [
        html.Div(
            [
            html.Label(label, className = 'header_label'),
            dcc.Graph(figure = fig, config={'displayModeBar': False})
            ]
        )
    ]

    return fig_layout

def make_group_bar_chart(values: pd.DataFrame, school_name: str, label: str) -> list:
    """
    Creates a layout containing a label and a grouped bar chart (px.bar)

    Args:
        values (pd.DataFrame): a dataframe with a list of schools and proficiency values
            for a given subject and category group (e.g., Math by Ethnicity)
        school_name (str): the name of the selected school
        label (str): the title of the figure

    Returns:
        fig_layout (list): a plotly dash html layout in the form of a list containing a string and px.bar figure
    """
    data = values.copy()

    if 'Low Grade' in data:
        data = data.drop(['Low Grade', 'High Grade'], axis = 1)

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
    cols = [i for i in data.columns if i not in ['School Name','Year']]

    for col in cols:
        data[col]=pd.to_numeric(data[col], errors='coerce')

    categories = data.columns.tolist()
    categories.remove('School Name')
    schools = data['School Name'].tolist()

    # melt dataframe from 'wide' format to 'long' format (plotly express
    # can handle either, but long format makes hovertemplate easier - trust me)
    data_set = pd.melt(data, id_vars='School Name',value_vars = categories, var_name='Categories', ignore_index=False)

    data_set.reset_index(drop=True, inplace=True)

    # Create text values for display.
    
    # NOTE: This can be 99.9% done by setting 'text_auto=True'
    # in 'fig' without setting specific 'text' values; EXCEPT, it does not hide the 'NaN%' text
    # that is displayed for ''. So this code converts the series to a string in the proper format
    # and replaces nan with ''    
    text_values = data_set['value'].map('{:.0%}'.format)
    text_values = text_values.str.replace('nan%','')
    
    # assign colors for each comparison
    trace_color = {schools[i]: color[i] for i in range(len(schools))}

    # replace color for selected school
    for key, value in trace_color.items():
        if key == school_name:
            trace_color[key] = '#0a66c2'

    fig = px.bar(
        data_frame = data_set,
        x = 'Categories',
        y = 'value',
        color = 'School Name',
        color_discrete_map = trace_color,
        orientation = 'v',
        barmode = 'group',
        custom_data = ['School Name'],
        text = text_values,
        # title=label,    # ADD BACKGROUND (style like header_label)
    )

    fig.update_yaxes(
        range=[0, 1],
        dtick=0.2,
        tickformat=',.0%',
        title='',
        showgrid=True,
        gridcolor='#b0c4de'
    )

    fig.update_xaxes(
        title='',
        showline=True,
        linewidth=.5,
        linecolor='#b0c4de'
    )

    fig.update_layout(
        title_x=0.5,
        margin=dict(l=40, r=40, t=40, b=10),
        font = dict(
            family='Jost, sans-serif',
            color='steelblue',
            size = 11
        ),
        bargap=.15,
        bargroupgap=.1,
        height=400,
        legend_title='',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor='white',
            font_color='steelblue',
            font_size = 11,
            font_family='Jost, sans-serif',
        ),
        hoverlabel_align = 'left'
    )        

    fig.update_traces(
        hovertemplate='<br>'.join(
            [
                s.replace(' ', '&nbsp;')
                for s in [
                    '<b>%{customdata[0]}</b>',
                    '<b>Proficiency: </b>%{y}<br><extra></extra>',
                ]
            ]
        )
    )

    # NOTE: Some dict manipulation to address two issues: 1) display values between 0 and 4% as text
    # outside of the trace, and all other values inside; and 2) display a 'marker' for '0' values.
    # Both have relatively simple solutions for single bar charts- neither of which work for
    # grouped bar charts, because both solutions end up applying 'per group' of bars rather than
    # to the individual bars in the group. See, e.g.:
    # https://stackoverflow.com/questions/70658955/how-do-i-display-bar-plot-for-values-that-are-zero-in-plotly
    # https://stackoverflow.com/questions/73905861/fully-display-the-amount-in-horizontal-bar-chart
    
    #  This uses a loop (ick) to directly manipulate each fig data object.
    
    for i in range(0,len(data_set['School Name'].unique())):

        marker_array = []
        position_array = []

        for j in range(0,len(fig['data'][i]['y'])):

            # # track location of school in index (to add border)
            # if fig['data'][i]['name'] == school_name:
            #     loc = i

            if fig['data'][i]['y'][j] < .05:
                position_array.append('outside')
            else:
                position_array.append('inside')

            if fig['data'][i]['y'][j] == 0:
                marker_array.append('#999999')
            else:
                marker_array.append(fig['data'][i]['marker']['color'])

        fig['data'][i]['marker']['line']['color'] = marker_array
        fig['data'][i]['marker']['line']['width'] = 2

        fig['data'][i]['textposition'] = position_array

    # NOTE: Uncomment to add border around selected school
    # having hard time making this look decent.
    # fig['data'][loc]['marker']['line']['color'] = 'grey'

    # NOTE: From testing, it appears that the legend marker uses the first item in the
    # marker_line_color array ([0]) as the border for the legend marker. So if the
    # marker_line_color is set to grey for a specific trace (e.g., the value of the trace
    # is '0'), that color is used for the legend marker. We do not want a grey border
    # around a legend marker. We fix this in stylesheet.css (See: .legendundefined))

    fig_layout = [
        html.Div(
            [
            html.Label(label, className = 'header_label'),
            dcc.Graph(figure = fig, config={'displayModeBar': False})
            ]
        )
    ]
    
    return fig_layout