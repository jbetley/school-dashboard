"""color
Charting Functions
"""

import plotly.express as px
import pandas as pd
import numpy as np
import textwrap
import plotly.graph_objects as go
from dash import html, dcc

# Colors
# https://codepen.io/ctf0/pen/BwLezW

# Steelblue
#color=['#98abc5','#919ab6','#8a89a6','#837997','#7b6888','#73587a','#6b486b','#865361','#a05d56','#b86949','#d0743c','#e8801e','#ff8c00']

color= ['#74a2d7', '#df8f2d','#96b8db','#ebbb81','#bc986a','#a8b462','#f0c33b','#74a2d7','#f0c33b','#83941f','#999999']

## Blank (Loading) Fig ##
# https://stackoverflow.com/questions/66637861/how-to-not-show-default-dcc-graph-template-in-dash

# loading_fig is a blank chart with no title and no data other than
# the 'Loading . . .' string
def loading_fig() -> dict:
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

# blank fig with label and height.
def no_data_fig_label(label: str = 'No Data to Display', height: int = 400) -> go.Figure:

    fig = go.Figure()
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=0),
        height = height,
        # title={
        #     'text': label,
        #     'y':0.975,
        #     'x':0.5,
        #     'xanchor': 'center',
        #     'yanchor': 'top',
        #     'font_family': 'Roboto, sans-serif',
        #     'font_color': 'steelblue',
        #     'font_size': 10
        # },
        xaxis =  {
            "visible": False,
            'fixedrange': True
        },
        yaxis =  {
            "visible": False,
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
                    'family': 'Roboto, sans-serif'
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

# Blank fig with no label
def no_data_fig_blank() -> go.Figure:

    fig = go.Figure()
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=0),
        height = 400,
        # title={
        #     'y':0.975,
        #     'x':0.5,
        #     'xanchor': 'center',
        #     'yanchor': 'top',
        #     'font_family': 'Roboto, sans-serif',
        #     'font_color': 'steelblue',
        #     'font_size': 10
        # },
        xaxis =  {
            "visible": False,
            'fixedrange': True
        },
        yaxis =  {
            "visible": False,
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
                    'family': 'Roboto, sans-serif'
                }
            }
        ],
        dragmode = False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig

# Use this function to create wrapped text using html tags
# based on the specified width. add two spaces before <br>
# to ensure the words at the end of each break have the same
# spacing as 'ticksuffix' in make_stacked_bar()

def customwrap(s: str,width: int = 16):
    return "  <br>".join(textwrap.wrap(s,width=width))

def make_stacked_bar(values: pd.DataFrame, label: str) -> list: #px.bar:
    data = values.copy()

    # In order to get the total_tested value into hovertemplate
    # without displaying it on the chart, we need to pull the
    # Total Tested values out of the dataframe and into a new
    # column

    # Copy all of the Total Tested Values
    total_tested = data[data['Proficiency'].str.contains('Total Tested')]

    # Merge the total tested values with the existing dataframe
    # This adds 'percentage_x' and 'percentage_y' columns.
    # 'percentage_y' is equal to the Total Tested Values
    data = pd.merge(data, total_tested[['Category','Percentage']], on=['Category'], how='left')

    # rename the columns (percentage_x to Percentage & percentage_y to Total Tested)
    data.columns = ['Category','Percentage','Proficiency','Total Tested']

    # drop the Total Tested Rows
    data = data[data['Proficiency'].str.contains('Total Tested') == False]

    # Remove subject substring ('ELA/Math') from Proficiency column
    data['Proficiency'] = data['Proficiency'].str.split().str[1:].str.join(' ')

    fig = px.bar(
        data,
        x = data['Percentage'],
        y = data['Category'].map(customwrap),
        color=data['Proficiency'],
        barmode='stack',
        text=[f'{i}%' for i in data['Percentage']],
        orientation="h",
        color_discrete_sequence=color,
        height=200,
    )

    # Add hoverdata
    # TODO: Remove hover 'title' which is currently y-axis name
    # TODO: Add new label title that is equal to: "Total Tested: {z}"
    # https://stackoverflow.com/questions/59057881/how-to-customize-hover-template-on-with-what-information-to-show
    # fig.update_layout(hovermode="x unified")
    
    fig.update_traces(hovertemplate="%{text}")

    # the uniformtext_minsize and uniformtext_mode settings hide bar chart
    # text (Percentage) if the size of the chart causes the text of the font
    # to decrease below 8px. The text is required to be positioned 'inside'
    # the bar due to the 'textposition' variable

    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=0),
        font_family="Roboto, sans-serif",
        font_color="steelblue",
        font_size=8,
        bargroupgap = 0,
        showlegend = False,
        plot_bgcolor="white",
        hovermode='y unified',
        hoverlabel=dict(
            bgcolor="white",
            font_color='steelblue',
            font_size=10,
            font_family='Roboto Sans, sans-serif',
        ),        
        yaxis=dict(autorange="reversed"),
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    fig.update_traces(
        textfont_size=8,
        insidetextanchor = 'middle',
        textposition='inside',
        marker_line=dict(width=0),
        showlegend = False, # Trying to get rid of legend in hoverlabel
    )

    fig.update_xaxes(title="")

    # ticksuffix increases the space between the end of the tick label and the chart
    fig.update_yaxes(title="",ticksuffix = "  ")

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
    
    return fig_layout

# single line chart
### TODO: default tick behavior is ugly for small number of points. For example, if only
### TODO: two points, the 2 x-ticks are really far apart towards edges, same with 3 ticks
def make_line_chart(values: pd.DataFrame, label: str) -> list:

    data = values.copy()

    data.columns = data.columns.str.split('|').str[0]
    cols=[i for i in data.columns if i not in ['School Name','Year']]

    # create chart only if data exists
    if (len(cols)) > 0:

        for col in cols:
            data[col]=pd.to_numeric(data[col], errors='coerce')

        data.sort_values('Year', inplace=True)
        data = data.reset_index(drop=True)

        fig = px.line(
            data,
            x='Year',
            y=cols,
            markers=True,
            color_discrete_sequence=color,
        )

        fig.update_traces(mode='markers+lines', hovertemplate=None)
        fig.update_layout(
            margin=dict(l=40, r=40, t=40, b=60),
            title_x=0.5,
            font = dict(
                family = 'Roboto, sans-serif',
                color = 'steelblue',
                size = 10
                ),
            plot_bgcolor='white',
            xaxis = dict(
                title='',
                # type='date',
                tickmode = 'array',
                # tickmode = 'linear',
                tickvals = data['Year'],
                tickformat="%Y",
                # tick0 = data['Year'][0] - 1,
                # dtick ='M6',
                categoryorder = 'array',
                categoryarray = data['Year'],
                mirror=True,
                showline=True,
                linecolor='#b0c4de',
                linewidth=.5,
                gridwidth=.5,
                showgrid=True,
                gridcolor='#b0c4de',
                zeroline=False,
                ),   
            legend=dict(orientation="h"),         
            hovermode='x unified',
            height=400,
            legend_title='',
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
            range=[0, 1],
            dtick=.2,
            tickformat=',.0%',
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

# single bar chart
def make_bar_chart(values: pd.DataFrame, category: str, school_name: str, label: str) -> list:
    data = values.copy()

    # NOTE: Unless the entire page is blank, e.g., no data at all, the
    # dataframe for this chart should never be blank due to error
    # handling in the calling script. However, we know that 'should never'
    # is code for 'almost with certainty' so we test here too.

    # the dataframe should always have at least 4 columns
    if (len(data.columns)) > 3:
        schools = data['School Name'].tolist()

        # assign colors for each comparison school
        trace_color = {schools[i]: color[i] for i in range(len(schools))}

        # use specific color for selected school
        for key, value in trace_color.items():
            if key == school_name:
                trace_color[key] = '#0a66c2'

        # format distance data (not displayed)
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
                family='Roboto Sans, sans-serif',
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
            plot_bgcolor='rgba(0,0,0,0)',
            hoverlabel=dict(
                bgcolor="white",
                font_color='steelblue',
                font_size=10,
                font_family='Roboto Sans, sans-serif',
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

def make_group_bar_chart(values: pd.DataFrame, school_name: str, label: str) -> list: #px.bar:

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

    print(data)

# TODO: CUrrently treating NaN values like zero values. Need to fix that

    categories = data.columns.tolist()
    categories.remove('School Name')
    schools = data['School Name'].tolist()

    # melt dataframe from 'wide' format to 'long' format (plotly express
    # can handle either, but long format makes hovertemplate easier
    #  - trust me)
    data_set = pd.melt(data, id_vars='School Name',value_vars = categories, var_name='Categories', ignore_index=False)

    data_set.reset_index(drop=True, inplace=True)

# TODO: NaN is shown in bar text. Remove
    # replace any remaining NaN with 0
    # data_set = data_set.fillna(0)

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
        # text = [x if x is not None else '' for x in 'value'],
        text_auto=True
    )
    print(data_set['value'])

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

    # TODO: Better way to reduce the bottom margin of a chart to reduce empty space between chart and table
    # Currently adding negative margin - must be better way
    # Does this work? it takes maximum value and multiplies it by three for max range (eg., less than 100)
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
        bargroupgap=.1,
        height=400,
        legend_title='',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor="white",
            font_color='steelblue',
            font_size=10,
            font_family='Roboto Sans, sans-serif',
        ),
        hoverlabel_align = 'left'
    )        

## TODO: This adds lines for zero. Useful if text is not used.
## TODO: Outside text shows 0%. But also shows 0% for NaN and we don't want that
## TODO: Inside text doesn't show anything for 0% - Need to Figure out best solution

    # TODO: Add ability to click on 0?
    # Display '0' values visually on the chart.
    # NOTE: marker_line_color controls the color of the border around a trace. The border is
    # visible even when a value is 0, so it can be used as a visible representation of 0. Was
    # not able to get this to work using update traces (it applied the colors in the list to
    # each group rather than to each trace in a group): 
    # fig.update_traces(marker_line_width = 2, marker_line_color = list(trace_color.values()))
    
    # This seems extremely janky, but works by manually looping through the fig object using nested
    # loops. The top level loop iterates through each school. The internal loop loops through each
    # data point in the 'y' array. If the value is zero, the marker_array list appends the color 
    # black. If the value is not zero, the list appends the marker color. This has the effect of
    # creating a black marker_line border color for a zero value and otherwise creating a border
    # color that is the same as the marker.
    
    # TODO: Remove Black marker border from legend on zero value
    # if black exists in the array, plotly uses it as a border for the 'legend' marker. From
    # testing, it appears that the border uses the marker_line_color for the [0] item in
    # the 'data' array. So if there is a 0 value in the first chart, it causes the legend
    # outline to also be black.

    for i in range(0,len(data['School Name'])):

        marker_array = []
        for j in range(0,len(fig['data'][i]['y'])):

            if fig['data'][i]['y'][j] == 0:
                marker_array.append('#000000')
            else:
                marker_array.append(fig['data'][i]['marker']['color'])

        fig['data'][i]['marker']['line']['color'] = marker_array
        fig['data'][i]['marker']['line']['width'] = 3

    fig.update_traces(
        textposition='outside',
        hovertemplate="<br>".join(
            [
                s.replace(" ", "&nbsp;")
                for s in [
                    '<b>%{customdata[0]}</b>',
                    '<b>Proficiency: </b>%{y}<br><extra></extra>',
                ]
            ]
        )
    )

    fig_layout = [
        html.Div(
            [
            html.Label(label, className = 'header_label'),
            dcc.Graph(figure = fig, config={'displayModeBar': False})
            ]
        )
    ]

    return fig_layout