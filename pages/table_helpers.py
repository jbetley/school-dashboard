"""
Table Helper Functions
"""
import numpy as np
import pandas as pd
from dash import dash_table, html
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign

color=['#98abc5','#919ab6','#8a89a6','#837997','#7b6888','#73587a','#6b486b','#865361','#a05d56','#b86949','#d0743c','#e8801e','#ff8c00']

def no_data_table(label: str = 'No Data to Display') -> list:
    """Creates single empty table with provided label

    Args:
        label (String): table label string

    Returns:
        list: dash DataTable
    """

    table_layout = [
                html.Label(label, className='header_label'),
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
                            'fontFamily': 'Roboto, sans-serif',
                            'height': '30vh',
                        },
                    ),
                ),
            ]

    return table_layout

def no_data_page(label: str) -> list:
    """Creates single empty table as page with provided label

    Args:
        label (String): string label

    Returns:
        list: dash DataTable
    """
    table_layout = [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(label, className='header_label'),
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
                                            'fontFamily': 'Roboto, sans-serif',
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

    return table_layout

# Display tables either side by side or on individual rows depending on # of columns
def set_table_layout(table1: list, table2: list, cols: pd.Series) -> list:
    """Determines table layout depending on the size (# of cols) of the tables 

    Args:
        table1 (list): dash DataTable
        table2 (list): dash DataTable
        cols (pandas.core.indexes.Base.index): Pandas series of column headers

    Returns:
        list: html Div enclosing dash DataTables and formatting
    """

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

def get_svg_circle(val: pd.DataFrame) -> pd.DataFrame:
    """Takes a Pandas Dataframe and replaces text with svg circles coded
        the correct colors based on rating text.
        https://stackoverflow.com/questions/19554834/how-to-center-a-circle-in-an-svg
        https://stackoverflow.com/questions/65778593/insert-shape-in-dash-datatable
        https://community.plotly.com/t/adding-markdown-image-in-dashtable/53894/2

    Args:
        val (pd.Dataframe): Pandas dataframe with metric Rating columns

    Returns:
        pd.Dataframe: returns the same dataframe with svg circles in place of text
    """
    result = val.copy()

    # Academic/Financial metric dataframes contain 'Rate' substring in columns if there
    # is sufficient data. Organizational metric dataframe contains 'Standard' column
    # the else ocurrs when a dataframe is passed that doesn't contain either
    if val.columns.str.contains('Rat').any() == True:
        rating_columns = val.loc[:, val.columns.str.contains('Rat')].columns
    elif val.columns.str.contains('Standard').any() == True:
        rating_columns = val.loc[:, ~val.columns.str.contains('Standard|Description',case=False, regex=True)].columns
    else:
        rating_columns = pd.Index([])

    # only process dataframes satisfying either condition above
    if ~rating_columns.empty:
        for col in rating_columns:

            conditions = [
            result[col].eq('DNMS'),
            result[col].eq('AS'),
            result[col].eq('MS'),
            result[col].eq('ES'),
            result[col].eq('N/A'),
            result[col].eq(np.nan),
            ]

            # NOTE: Using font-awesome circle icon. 
            did_not_meet ='<span style="font-size: 1em; color: #ea5545;"><i class="fa fa-circle center-icon"></i></span>'
            approaching ='<span style="font-size: 1em; color: #ede15b;"><i class="fa fa-circle center-icon"></i></span>'
            meets ='<span style="font-size: 1em; color: #87bc45;"><i class="fa fa-circle center-icon"></i></span>'
            exceeds ='<span style="font-size: 1em; color: #b33dc6;"><i class="fa fa-circle center-icon"></i></span>'
            no_rating ='<span style="font-size: 1em; color: #a4a2a8;"><i class="fa fa-circle center-icon"></i></span>'
            empty_cell =''

            # NOTE: this commented out code uses svg circle, which also works, but is
            # harder to keep consistent in different sized tables.
            # did_not_meet = f'<svg width="100%" height="100%" viewBox="-1 -1 2 2" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="0" cy="0" r=".3" fill="#ea5545" /></svg>'
            # approaching = f'<svg width="100%" height="100%" viewBox="-1 -1 2 2" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="0" cy="0" r=".3" fill="#ede15b" /></svg>'
            # meets = f'<svg width="100%" height="100%" viewBox="-1 -1 2 2" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="0" cy="0" r=".3" fill="#87bc45" /></svg>'
            # exceeds = f'<svg width="100%" height="100%" viewBox="-1 -1 2 2" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="0" cy="0" r=".3" fill="#b33dc6" /></svg>'
            # no_rating = f'<svg width="100%" height="100%" viewBox="-1 -1 2 2" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="0" cy="0" r=".3" fill="#a4a2a8" /></svg>'

            rating = [did_not_meet,approaching,meets,exceeds, no_rating, empty_cell]
            result[col] = np.select(conditions, rating, default=empty_cell)

    return result

def create_metric_table(label: str, content: pd.DataFrame) -> list:
    """Takes a dataframe consisting of Rating and Metric
    Columns and returns a list dash DataTable object
    NOTE: could possibly be less complicated than it is, or
    maybe not - gonna leave it up to future me

    Args:
        label (String): Table title
        content (pd.DataTable): dash dataTable

    Returns:
        list: Formatted dash DataTable
    """""""""

## Global table styles
# TODO: dont want global font size, but need to change numbers font sized
# TODO: to 10 to align with the difference columns
# NOTE: JUST WANT NUMBERS (?) <- what does this mean?

    table_style = {
        'fontSize': '11px',
        'border': 'none',
        'fontFamily': 'Roboto Sans, sans-serif',
    }

    table_cell = {
        'whiteSpace': 'normal',
        'height': 'auto',
        'textAlign': 'center',
        'color': '#6783a9',
        'boxShadow': '0 0',
    }

    data = content.copy()

    cols = data.columns
    table_size = len(cols)

    if len(data.index) == 0 or table_size == 1:
        table = [
            html.Div(
                [
                    html.Label(label, className='header_label'),
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

        # NOTE: Testing a version of the table comparing school and corporation rates
        # that does not include the corp rate, only the difference. This is in order
        # to decrease the number of columns. Eventually may want to remove the
        # calculation from calculateMetrics(), but am leaving it in for now in case
        # we ultimately choose to display it

        # NOTE: Order of these operations matters

        # remove all Corp Rate / Corp Avg columns
        data = data.loc[:, ~data.columns.str.contains('Corp')]

        # rename '+/-' columns
        data.columns = data.columns.str.replace('\+/-', 'Diff', regex=True)

        # Formatting on the fly - determines the col_width class and width
        # of the category column based on the size (# of cols) of the dataframe
        if table_size <= 3:
            col_width = 'four'
            category_width = 70
        if table_size > 3 and table_size <=4:
            col_width = 'six'
            category_width = 35
        elif table_size >= 5 and table_size <= 8:
            col_width = 'six'
            category_width = 30
        elif table_size == 9:
            col_width = 'seven'
            category_width = 30
        elif table_size >= 10 and table_size <= 13:
            col_width = 'seven'
            category_width = 15
        elif table_size > 13 and table_size <=17:
            col_width = 'nine'
            category_width = 15
        elif table_size > 17:
            col_width = 'ten'
            category_width = 15

        year_headers = [y for y in data.columns.tolist() if 'School' in y]
        rating_headers = [y for y in data.columns.tolist() if 'Rate' in y]
        difference_headers = [y for y in data.columns.tolist() if 'Diff' in y]
        average_headers = [y for y in data.columns.tolist() if 'Average' in y]

        # splits column width evenly for all columns other than 'Category'
        # right now is even, but can finesse this by splitting data_width
        # into unequal values for each 'data' category, e.g.:
        #   rating_width = data_col_width + (data_col_width * .1)
        #   remaining_width = data_width - rating_width
        #   remaining_col_width = remaining_width / (table_size - 1)

        data_width = 100 - category_width
        data_col_width = data_width / (table_size - 1)
        rating_width = year_width = difference_width = data_col_width # corporation_width =
        rating_width=rating_width/2

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
        ]
        table_data_conditional =  [
            {
                'if': {
                    'row_index': 'odd'
                },
                'backgroundColor': '#eeeeee',
            }
        ]

        data['Category'] = data['Category'].map(lambda x: x.split('|')[0]).copy()

        # build multi-level headers
        # get list of +/- columns (used by datatable filter_query' to
        # ID columns for color formatting)
        format_cols = [k for k in headers if 'Diff' in k or 'Rate' in k]

        name_cols = [['Category','']]

        # NOTE: This removes the identifying number from the header for display purposes.
        for item in headers:
            if item.startswith('20'):
                if 'Rate' in item:
                    item = item[:8]

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
        ]  + [
            {   'if': {
                'column_id': average_headers,
                'header_index': 1,
            },
                'borderTop': '.5px solid #b2bdd4',
                'borderBottom': '.5px solid #b2bdd4',
        }
        ] + [
            # Use 'headers[-1]' and 'borderRight' for each subheader to have full border
            # Use 'headers[1]' and 'borderLeft' to leave first and last columns open on
            # right and left
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
                'textAlign': 'center',
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

        # tooltip_note = [
        #     html.Span('A'),
        #     html.Span('-***', style={'color': '#b44655'}),
        #     html.Span(' value indicates a reduction from a measurable, but not reportable, value to 0).')
        # ]
        # css=[{
        #     'selector': '.dash-table-tooltip',
        #     'rule': 'font-size: .75em; color: steelblue'
        # }],


        table = [
            html.Div(
                [
                    html.Label(label, className='header_label'),
                    html.Div(
                        dash_table.DataTable(
                            data.to_dict('records'),
                            columns=[
                                {'name': col, 'id': headers[idx], 'presentation': 'markdown'}
                                if 'Rate' in col
                                else {'name': col, 'id': headers[idx], 'type':'numeric',
                                'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
                                }
                                for (idx, col) in enumerate(name_cols)
                            ],
                            style_data = table_style,
                            style_data_conditional = table_data_conditional,
                            style_header = table_header,
                            style_header_conditional = table_header_conditional,
                            style_cell = table_cell,
                            style_cell_conditional = table_cell_conditional,
                            merge_duplicate_headers=True,
                            markdown_options={"html": True},
## TODO: Tooltip styling not working
##TODO: Also want to limit to certain value in cell                            
                            tooltip_conditional=[
                                {
                                    'if': {
                                        'filter_query': '{{{year}}} contains "-***"',
                                        'column_id': year,
                                    },
                                    'type': 'markdown',
                                    'value': 'This row is significant.'
                                } for year in year_headers
                            ],

                            # tooltip_data=[
                            #     {
                            #         "Category": {
                            #             "value": "A <span style='color:blue'>-***</span> value indicates a reduction from a measurable, but not reportable, value to a 0 value.",
                            #             "type": "markdown",
                            #             "delay": None,
                            #             "duration": None,
                            #         }
                            #     }
                            # ],
                        )
                    )
                ],
                className = class_name
            )
        ]
    return table


def create_comparison_table(data: pd.DataFrame, school_name: str, label: str) -> list:

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

### TODO: Sort Native is limited - cannot easily limit which columns are sortable and cannot
### TODO: sort by clicking header (ugly arrows instead). In addition it breaks the conditional
### TODO: formatting that highlights the school row (because the row index does not reset when
### TODO: the school changes rows as a result of the sort). Perhaps try Dash AG Grid?

# AG Grid Install - Alpha
# pip install dash-ag-grid==v2.0.0a5
# import dash_ag_grid as dag

    table = dash_table.DataTable(
        data.to_dict('records'),
        columns = [{'name': i, 'id': i, 'type':'numeric','format': FormatTemplate.percentage(2)} for i in data.columns],
        # sort_action='native',
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
            {
                'if': {
                    'column_id': ''
                },
                'textAlign': 'left',
                'paddingLeft': '30px'
            }
        ]
    )

    # bar-chart tables (Math, ELA, & IREAD) should have a label
    # multi-bar chart tables (by Subgroup, by Ethnicity) should not have a label
    # this is for formatting reasons
    if data.columns.str.contains('Total').any() == True or data.columns.str.contains('IREAD').any() == True:
        table_layout = [
            html.Div(
                [
                html.Label(label, className = 'header_label'),
                table
                ]
            )
        ]
    else:
        table_layout = [
            html.Div(
                [
                table
                ]
            )
        ]

    return table_layout

def create_academic_info_table(data: pd.DataFrame, label: str) -> list:

    table_layout = [
        html.Label(label, className='header_label'),
        html.Div(
            dash_table.DataTable(
                data.to_dict("records"),
                columns = [
                    {
                        "name": col,
                        "id": col,
                        "type": "numeric",
                        "format": Format(
                            scheme=Scheme.percentage, precision=2, sign=Sign.parantheses
                        ),
                    }
                    for (col) in data.columns
                ],
                style_data = {
                    "fontSize": "11px",
                    "fontFamily": "Roboto,sans-serif",
                    "border": "none"
                },
                style_data_conditional = [
                    {"if": {"row_index": "odd"}, "backgroundColor": "#eeeeee"},
                    {
                        "if": {"row_index": 0, "column_id": "Category"},
                        "borderTop": ".5px solid #6783a9",
                    },
                ],
                style_header =  {
                    "height": "20px",
                    "backgroundColor": "#ffffff",
                    "border": "none",
                    "borderBottom": ".5px solid #6783a9",
                    "fontSize": "12px",
                    "fontFamily": "Roboto, sans-serif",
                    "color": "#6783a9",
                    "textAlign": "center",
                    "fontWeight": "bold",
                },
                style_cell = {
                    "whiteSpace": "normal",
                    "height": "auto",
                    "textAlign": "center",
                    "color": "#6783a9",
                    "minWidth": "25px",
                    "width": "25px",
                    "maxWidth": "25px",
                },
                style_header_conditional = [
                    {
                        "if": {"column_id": "Category"},
                        "textAlign": "left",
                        "paddingLeft": "10px",
                        "width": "35%",
                        "fontSize": "11px",
                        "fontFamily": "Roboto, sans-serif",
                        "color": "#6783a9",
                        "fontWeight": "bold",
                    }
                ],
                style_cell_conditional = [
                    {
                        "if": {"column_id": "Category"},
                        "textAlign": "left",
                        "fontWeight": "500",
                        "paddingLeft": "10px",
                        "width": "40%"
                    }
                ],
                merge_duplicate_headers=True,
                style_as_list_view=True,
                # add this to each table if we want to be able to export
                # export_format='xlsx',
                # export_headers='display'
            ),
        )
    ]
    
    return table_layout

def create_key() -> dash_table.DataTable:
    """Creates a dash datatable 'key' using proficiency ratings and
    the Font Awesome circle icon

    Returns:
        _type_: a dash DataTable
    """
    rating_icon = '<span style="font-size: 1em;"><i class="fa fa-circle"></i></span>'

    proficiency_key = pd.DataFrame(
        dict(
            [
                (
                    'Rate',
                    [
                        "Exceeds Standard",
                    ],
                ),
                ('icon', [rating_icon]),
                (
                    'Rate2',
                    [
                        "Meets Standard",
                    ],
                ),
                ('icon2', [rating_icon]),
                (
                    'Rate3',
                    [
                        "Approaches Standard",
                    ],
                ),
                ('icon3', [rating_icon]),
                (
                    'Rate4',
                    [
                        "Does Not Meet Standard",
                    ],
                ),
                ('icon4', [rating_icon]),
                (
                    'Rate5',
                    [
                        "No Rating",
                    ],
                ),
                ('icon5', [rating_icon]),
            ]
        )
    )

    rating_headers = proficiency_key.columns.tolist()
    rating_cols = list(col for col in proficiency_key.columns if "Rate" in col)
    icon_cols = list(col for col in proficiency_key.columns if "icon" in col)

    return  dash_table.DataTable(
                css=[dict(selector="tr:first-child", rule="display: none")],
                data=proficiency_key.to_dict("records"),
                cell_selectable=False,
                columns=[
                    {"id": "icon", "name": "", "presentation": "markdown"},
                    {"id": "Rate", "name": "", "presentation": "markdown"},
                    {"id": "icon2", "name": "", "presentation": "markdown"},
                    {"id": "Rate2", "name": "", "presentation": "markdown"},
                    {"id": "icon3", "name": "", "presentation": "markdown"},
                    {"id": "Rate3", "name": "", "presentation": "markdown"},
                    {"id": "icon4", "name": "", "presentation": "markdown"},
                    {"id": "Rate4", "name": "", "presentation": "markdown"},
                    {"id": "icon5", "name": "", "presentation": "markdown"},
                    {"id": "Rate5", "name": "", "presentation": "markdown"},
                ],
                markdown_options={"html": True},
                style_table={
                    'paddingTop': '15px',
                    'fontSize': '.75em',
                    'border': 'none',
                    'fontFamily': 'Roboto, sans-serif',
                },
                style_cell = {
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'border': 'none',                                        
                    'textAlign': 'right',
                    'color': '#6783a9',
                    'boxShadow': '0 0',
                },
                style_cell_conditional = [
                    {
                        'if': {
                            'column_id': rating
                        },
                        'textAlign': 'right',
                    } for rating in rating_cols        
                ] + [
                    {
                        'if': {
                            'column_id': icon
                        },
                        'textAlign': 'left',
                        'width': '2%',
                    } for icon in icon_cols             
                ],                                   
                style_data_conditional=[
                    {
                        "if": {
                            "filter_query": '{Rate} = "Exceeds Standard"',
                            "column_id": "icon",
                        },
                        "color": "#b33dc6",
                    },
                    {
                        "if": {"filter_query": '{Rate2} = "Meets Standard"',
                            "column_id": "icon2"
                        },
                        "color": "#87bc45",
                    },
                    {
                        "if": {"filter_query": '{Rate3} = "Approaches Standard"',
                            "column_id": "icon3"
                        },
                        "color": "#ede15b",
                    },
                    {
                        "if": {"filter_query": '{Rate4} = "Does Not Meet Standard"',
                            "column_id": "icon4"
                        },
                        "color": "#ea5545",
                    },
                    {
                        "if": {"filter_query": '{Rate5} = "No Rating"',
                            "column_id": "icon5"
                        },
                        "color": "#a4a2a8",
                    },
                    {
                    'if': {
                        'column_id': rating_headers[1],
                    },
                    'marginLeft':'10px',
                },
            ],
        )