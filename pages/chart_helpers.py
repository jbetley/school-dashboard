import plotly.express as px
import plotly.colors
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import dash_table, html
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign

# Steelblue
#color=['#98abc5','#919ab6','#8a89a6','#837997','#7b6888','#73587a','#6b486b','#865361','#a05d56','#b86949','#d0743c','#e8801e','#ff8c00']

# Easter at Grandmas
#color=["#fbf8cc","#fde4cf","#ffcfd2","#f1c0e8","#cfbaf0","#a3c4f3","#90dbf4","#8eecf5","#98f5e1","#b9fbc0"]

# Squid Game
#color = ['#e27d60','#85cdca','#e8a87c','#c38d9e','#41b3a3','#e27d60','#85cdca','#e8a87c','#c38d9e','#41b3a3']

# Earthy Kitt
color = ['#8d8741','#659dbd','#daad86','#bc986a','#fbeec1','#8d8741','#659dbd','#daad86','#bc986a','#fbeec1']

# Russian Green
#color = ['#8ee4af','#edf5e1','#5cdb95','#907163','#379683','#8ee4af','#edf5e1','#5cdb95','#907163','#379683',]

# Bridgett's Favorite
#color = ['#5d5c61','#379683','#7395ae','#557a95','#b1a296','#5d5c61','#379683','#7395ae','#557a95','#b1a296',]

# Clown Car
#color = ['#d79922','#efe2ba','#f13c20','#4056a1','#c5cbe3','#d79922','#efe2ba','#f13c20','#4056a1','#c5cbe3']
## Blank (Loading) Fig ##
# https://stackoverflow.com/questions/66637861/how-to-not-show-default-dcc-graph-template-in-dash

def loading_fig():
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

# Create an empty figure with the provided label and height.
def no_data_fig(label,height):

    fig = go.Figure()
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=0),
        height = height,
        title={
            'text': label,
            'y':0.975,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font_family': 'Roboto, sans-serif',
            'font_color': 'steelblue',
            'font_size': 10
        },
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

# Use this function to create wrapped text using
# html tags based on the specified width
# NOTE: adding two spaces before <br> to ensure the words at
# the end of each break have the same spacing as 'ticksuffix'
# below
import textwrap
def customwrap(s,width=16):
    return "  <br>".join(textwrap.wrap(s,width=width))

def make_stacked_bar(values,fig_title):
    data = values.copy()
    # https://plotly.com/python/discrete-color/

    # colors = plotly.colors.qualitative.T10

    # In order to get the total_tested value into hovertemplate
    # without displaying it on the chart, we need to pull the
    # Total Tested values out of the dataframe and into a new
    # column

    # Copy all of the Total Tested Values
    # total_tested = data.loc[data['Proficiency'] == 'Total Tested']
    total_tested = data[data['Proficiency'].str.contains('Total Tested')]

    # Merge the total tested values with the existing dataframe
    # This adds 'percentage_x' and 'percentage_y' columns.
    # 'percentage_y' is equal to the Total Tested Values
    data = pd.merge(data, total_tested[['Category','Percentage']], on=['Category'], how='left')

    # rename the columns (percentage_x to Percentage & percentage_y to Total Tested)
    data.columns = ['Category','Percentage','Proficiency','Total Tested']

    # drop the Total Tested Rows
    # data = data[(data['Proficiency'] != 'Total Tested')]
    data = data[data['Proficiency'].str.contains('Total Tested') == False]
    
    fig = px.bar(
        data,
        x= data['Percentage'],
        y = data['Category'].map(customwrap),
        color=data['Proficiency'],
        barmode='stack',
        text=[f'{i}%' for i in data['Percentage']],
        # custom_data = np.stack((data['Proficiency'], data['Total Tested']), axis=-1),
        custom_data = [data['Proficiency'], data['Total Tested']],
        orientation="h",
        color_discrete_sequence=color,
        height=200,
        title = fig_title
    )

    #TODO: Remove trace name. Show Total Tested only once. Remove legend colors.
    
    #customize the hovertemplate for each segment of each bar
    fig['data'][0]['hovertemplate']='Total Tested: %{customdata[1]}<br><br>' + '%{text}: %{customdata[0]}<extra></extra>'
    fig['data'][1]['hovertemplate']='Total Tested: %{customdata[1]}<br><br>' + '%{text}: %{customdata[0]}<extra></extra>'
    fig['data'][2]['hovertemplate']='Total Tested: %{customdata[1]}<br><br>' + '%{text}: %{customdata[0]}<extra></extra>'
    fig['data'][3]['hovertemplate']='Total Tested: %{customdata[1]}<br><br>' + '%{text}: %{customdata[0]}<extra></extra>'

    # print(fig['data'][3])
    # Add hoverdata
    # TODO: Issue: In a 100% stacked bar chart traces are generated by grouping
    # a column with values adding up to 100%. In this case, there will always
    # be 4 values (the number of items in "proficiency_rating"). So each trace
    # is made up of 4 rows. With a unified hovermode, customdata[0] and customdata[1]
    #  read only the number of rows in the dataframe equal to the number of traces, in
    # this case 4. So we need to restructure customdata to include: each rating
    # print(data['Total Tested'])
    # data.loc[1, 'Total Tested'] = '99'
    # print(data['Total Tested'])

    # customdata = np.stack((data['Proficiency'], data['Total Tested']), axis=-1)
    # print(customdata)
    # hovertemplate = (
    #     'Total Tested: %{customdata[1]}<br>' +
    #     '%{text}: %{customdata[0]}<extra></extra>')
    
    # fig.update_traces(customdata=customdata, hovertemplate=hovertemplate)


    # the uniformtext_minsize and uniformtext_mode settings hide bar chart
    # text (Percentage) if the size of the chart causes the text of the font
    # to decrease below 8px. The text is required to be positioned 'inside'
    # the bar due to the 'textposition' variable
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=0),
        font_family="Roboto, sans-serif",
        font_color="steelblue",
        font_size=8,
        # legend=dict(
        #     orientation="h",
        #     title="",
        #     x=0,
        #     font=dict(
        #         family="Open Sans, sans-serif", color="steelblue", size=8
        #     ),
        # ),
        plot_bgcolor="white",
        hovermode='y unified',
        hoverlabel=dict(
            bgcolor = 'grey',
            font=dict(
                family="Open Sans, sans-serif", color="white", size=8
            ),
        ),
        yaxis=dict(autorange="reversed"),
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        title={
            'y':0.975,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        bargroupgap = 0,
        showlegend = False,
    )

    fig.update_traces(
        textfont_size=8,
        insidetextanchor = 'middle',
        textposition='inside',
        marker_line=dict(width=0),
        # bar_width=0,
        showlegend = False, # Trying to get rid of legend in hoverlabel
    )

    fig.update_xaxes(title="")

    # ticksuffix increases the space between the end of the tick label and the chart
    fig.update_yaxes(title="",ticksuffix = "  ")

    return fig

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