# import plotly.express as px
# import pandas as pd
# import numpy as np
from dash import dash_table, html
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign

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
color=['#98abc5','#919ab6','#8a89a6','#837997','#7b6888','#73587a','#6b486b','#865361','#a05d56','#b86949','#d0743c','#e8801e','#ff8c00']

# create empty table with custom label
def no_data_table(label):
    table = [
                # html.Div(
                #     [
                #         html.Div(
                #             [
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
                                            'height': '30vh',
                                        },
                                    ),
                                ),
                #             ],
                #             className = 'pretty_container eight columns'
                #         ),
                #     ],
                #     className = 'bare_container twelve columns',
                # )
    ]

    return table

# create empty table with custom label
def no_data_page(label):
    table = [
                html.Div(
                    [
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
                                            'height': '30vh',
                                        },
                                    ),
                                ),
                            ],
                            className = 'pretty_container eight columns'
                        ),
                    ],
                    className = 'bare_container twelve columns',
                )
    ]

    return table

# Display tables either side by side or on individual rows depending on # of columns
def set_table_layout(table1, table2, cols):

    # Can force single table layout by passing same table twice
    if table1 == table2:

        table_layout = [
                html.Div(
                    table1,
                    className = 'bare_container twelve columns',
                )
        ]
    else:
        if len(cols) >= 4:

            table_layout = [
                    html.Div(
                        table1,
                        className = 'bare_container twelve columns',
                    ),
                    html.Div(
                        table2,
                        className = 'bare_container twelve columns',
                    ),
            ]

        else:

            table_layout = [
                    html.Div(
                        [
                            table1[0],
                            table2[0],
                        ],
                        className = 'bare_container twelve columns',
                    ),
            ]

    return table_layout

def create_metric_table(label, content):
# Generate tables given data and label - could
# possibly be less complicated than it is, or
# maybe not - gonna leave it up to future me
## Global table styles

# TODO: dont want global font size, but need to change numbers font sized
# to 10 to align with the difference columns
# JUST WANT NUMBERS (?) <- what does this mean?

    table_style = {
        'fontSize': '11px',
        'border': 'none',
        'fontFamily': 'Open Sans, sans-serif',
    }

    table_cell = {
        'whiteSpace': 'normal',
        'height': 'auto',
        'textAlign': 'center',
        'color': '#6783a9',
        'boxShadow': '0 0',
        'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
    }

    data = content.copy()
    
    cols = data.columns
    table_size = len(cols)

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
                className = 'pretty_container ten columns'
            )
        ]

    else:

        # Formatting on the fly - determines the col_width class and width
        # of the category column based on the size on the dataframe
        if table_size == 2:
            col_width = 'eight'
            category_width = 70
        if table_size > 2 and table_size <=4:
            col_width = 'eight'
            category_width = 35
        elif table_size >= 5 and table_size <= 9:
            col_width = 'eight'
            category_width = 30
        elif table_size >= 10 and table_size <= 15:
            col_width = 'twelve'
            category_width = 15
        elif table_size >= 16:
            col_width = 'twelve'
            category_width = 15
        
        year_headers = [y for y in data.columns.tolist() if 'School' in y]
        rating_headers = [y for y in data.columns.tolist() if 'Rating' in y]
        difference_headers = [y for y in data.columns.tolist() if '+/-' in y]
        corporation_headers = [y for y in data.columns.tolist() if 'Rate' in y or 'Avg' in y] # Gets cols with 'Rate' and 'Avg' in header

        # splits column width evenly for all columns other than 'Category'
        # right now is even, but can finesse this by splitting data_width
        # into unequal values for each 'data' category, e.g.:
        #   rating_width = data_col_width + (data_col_width * .1)
        #   remaining_width = data_width - rating_width
        #   remaining_col_width = remaining_width / (table_size - 1)

        data_width = 100 - category_width
        data_col_width = data_width / (table_size - 1)
        rating_width = year_width = difference_width = corporation_width = data_col_width

        class_name = 'pretty_container ' + col_width + ' columns'

        headers = data.columns.tolist()

        table_cell_conditional = [
            {
                'if': {
                    'column_id': 'Category'
                },
                'textAlign': 'left',
                'paddingLeft': '20px',
                'fontWeight': '500',
                'width': str(category_width) + '%'
            },
        ] + [
            {
                'if': {
                    'column_id': year
                },
                'textAlign': 'center',
                'fontWeight': '500',
                'width': str(year_width) + '%',
            } for year in year_headers
        ]  + [
            {   'if': {
                'column_id': rating
            },
                'textAlign': 'center',
                'fontWeight': '600',
                'width': str(rating_width) + '%'
            } for rating in rating_headers
        ]  + [
            {   'if': {
                'column_id': difference
            },
                'textAlign': 'center',
                'fontWeight': '500',
                'width': str(difference_width) + '%'
            } for difference in difference_headers
        ]  + [
            {   'if': {
                'column_id': corporation
            },
                'textAlign': 'center',
                'fontWeight': '500',
                'width': str(corporation_width) + '%'
            } for corporation in corporation_headers
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
                    'filter_query': '{{{col}}} = "DNMS"'.format(col=col),
                    'column_id': col
                },
                'backgroundColor': '#e56565',
                'color': 'white',
            } for col in cols
        ] + [
            {
                'if': {
                    'filter_query': '{{{col}}} = "AS"'.format(col=col),
                    'column_id': col
                },
                'backgroundColor': '#ddd75a',
                'color': 'white',
            } for col in cols
        ] + [
            {
                'if': {
                    'filter_query': '{{{col}}} = "ES"'.format(col=col),
                    'column_id': col
                },
                'backgroundColor': '#b29600',
                'color': 'white',
            } for col in cols
        ] + [
            {
                'if': {
                    'filter_query': '{{{col}}} = "MS"'.format(col=col),
                    'column_id': col
                },
                'backgroundColor': '#75b200',
                'color': 'white',
            } for col in cols
        ]

        data['Category'] = data['Category'].map(lambda x: x.split('|')[0]).copy()

        # build multi-level headers
        # get list of +/- columns (used by datatable filter_query' to ID columns for color formatting)

        format_cols = [k for k in headers if '+/-' in k or 'Rating' in k]

        name_cols = [['Category','']]
    
        for item in headers:
            if item.startswith('20'):
                if 'Rating' in item:
                    item = item[:10]
                
                name_cols.append([item[:4],item[4:]])

        # NOTE: The next two two styling blocks add a border to header_index:1
        # For a single bottom line: comment out blocks, comment out
        # style_header_conditional in table declaration,
        # and uncomment style_as_list in table declaration

        table_header = {
            'backgroundColor': '#ffffff',
            'fontSize': '11px',
            'fontFamily': 'Roboto, sans-serif',
            'color': '#6783a9',
            'textAlign': 'center',
            'fontWeight': 'bold',
            'border': 'none'     
        }

        table_header_conditional = [
            {
                'if': {
                    'column_id': year,
                    'header_index': 1,
                },
                'borderLeft': '.5px solid #b2bdd4',
                'borderTop': '.5px solid #b2bdd4',
                'borderBottom': '.5px solid #b2bdd4',
            } for year in year_headers
        ] + [
            {   'if': {
                'column_id': corporation,
                'header_index': 1,
            },
                'borderTop': '.5px solid #b2bdd4',
                'borderBottom': '.5px solid #b2bdd4',
        } for corporation in corporation_headers
        ]  + [
            {   'if': {
                'column_id': rating,
                'header_index': 1,
            },
                'borderTop': '.5px solid #b2bdd4',
                'borderBottom': '.5px solid #b2bdd4',
        } for rating in rating_headers
        ]  + [
            {   'if': {
                'column_id': difference,
                'header_index': 1,
            },
                'borderTop': '.5px solid #b2bdd4',
                'borderBottom': '.5px solid #b2bdd4',
        } for difference in difference_headers
        ] + [
            # Two options:
            #   1) use 'headers[-1]' and 'borderRight' for each subheader to have full border
            #   2) use 'headers[1]' and 'borderLeft' to leave first and last columns open on right and left
            {   'if': {
                'column_id': headers[-1],
            #    'column_id': headers[1],
                'header_index': 1,
            },
            'borderRight': '.5px solid #b2bdd4',
            }
        ]

        # formatting logic is different for multi-header table
        table_data_conditional = [
            {
                'if': {
                    'row_index': 'odd'
                },
                'backgroundColor': '#eeeeee'
            }
        ] + [
            {
                'if': {
                'filter_query': '{{{col}}} = "DNMS"'.format(col=col),
                'column_id': col
                },
                'backgroundColor': '#e56565',
                'color': 'white',
                'boxShadow': 'inset 0px 0px 0px 1px white'
            } for col in cols
        ] + [
            {
                'if': {
                'filter_query': '{{{col}}} = "AS"'.format(col=col),
                'column_id': col
                },
                'backgroundColor': '#ddd75a',
                'color': 'white',
                'boxShadow': 'inset 0px 0px 0px 1px white'
            } for col in cols
        ] + [
            {
                'if': {
                'filter_query': '{{{col}}} = "ES"'.format(col=col),
                'column_id': col
                },
                'backgroundColor': '#b29600',
                'color': 'white',
                'boxShadow': 'inset 0px 0px 0px 1px white'
            } for col in cols
        ] + [
            {
                'if': {
                'filter_query': '{{{col}}} = "MS"'.format(col=col),
                'column_id': col
                },
                'backgroundColor': '#75b200',
                'color': 'white',
                'boxShadow': 'inset 0px 0px 0px 1px white'
            } for col in cols
        ] + [
            {
                'if': {
                    'filter_query': '{{{col}}} = "NA"'.format(col=col),
                    'column_id': col
                },
                'backgroundColor': '#9a9a9a',
                'color': 'white',
                'boxShadow': 'inset 0px 0px 0px 1px white',
            } for col in cols
        ] + [
            {
                'if': {
                    'column_id': headers[-1],
                },
                'borderRight': '.5px solid #b2bdd4',
            },
        ] + [
            {
                'if': {
                    'row_index': 0
                },
                'paddingTop': '5px'
            }
        ] + [
            {
                'if': {
                    'row_index': len(data)-1
                },
                'borderBottom': '.5px solid #b2bdd4',
            }
        ] + [
            {
                'if': {
                    'column_id': 'Category',
                },
                'borderRight': '.5px solid #b2bdd4',
                'borderBottom': 'none',                
            },
        ] + [ 
            {
                'if': {
                    'column_id': rating,
                },
                'borderRight': '.5px solid #b2bdd4',
            } for rating in rating_headers                
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
                    'filter_query': '{{{col}}} = "-***"'.format(col=col),
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

        table = [
            html.Div(
                [
                    html.Label(label, style=label_style),
                    html.Div(
                        dash_table.DataTable(
                            data.to_dict('records'),
                            columns=[
                                    {
                                        'name': col,
                                        'id': headers[idx],
                                        'type':'numeric',
                                        'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
                                    } for (idx, col) in enumerate(name_cols)
                                ],
                            style_data = table_style,
                            style_data_conditional = table_data_conditional,
                            style_header = table_header,
                            style_header_conditional = table_header_conditional,
                            style_cell = table_cell,
                            style_cell_conditional = table_cell_conditional,
                            merge_duplicate_headers=True,
                        )
                    )
                ],
                className = class_name
            )
        ]

    # else:
    #     # headers
    #     clean_headers = []
    #     for i, x in enumerate (headers):
    #         if 'Rating' in x:
    #             clean_headers.append('Rating')
    #         else:
    #             clean_headers.append(x)

    #     table_header = {
    #         'backgroundColor': '#ffffff',
    #         'fontSize': '11px',
    #         'fontFamily': 'Roboto, sans-serif',
    #         'color': '#6783a9',
    #         'textAlign': 'center',
    #         'fontWeight': 'bold'            
    #     }

    #     table = [
    #         html.Div(
    #             [
    #                 html.Label(label, style=label_style),
    #                 html.Div(
    #                     dash_table.DataTable(
    #                         data.to_dict('records'),
    #                         columns=[{
    #                             'name': col, 
    #                             'id': headers[idx],
    #                             'type':'numeric',
    #                             'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)                                    
    #                             } for (idx, col) in enumerate(clean_headers)],
    #                         style_data = table_style,
    #                         style_data_conditional = table_data_conditional,
    #                         style_header = table_header,
    #                         style_cell = table_cell,
    #                         style_cell_conditional = table_cell_conditional,
    #                         style_as_list_view=True
    #                     )
    #                 )
    #             ],
    #             className = class_name
    #         )
    #     ]

    return table

def create_comparison_table(data,school_name):

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