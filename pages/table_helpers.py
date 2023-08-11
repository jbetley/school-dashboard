########################################
# ICSB Dashboard - DataTable Functions #
########################################
# author:   jbetley
# version:  1.08
# date:     08/01/23

import numpy as np
import pandas as pd
from dash import dash_table, html
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign
import re
from typing import Tuple
from .load_data import ethnicity, subgroup, info_categories

# Global styles
table_style = {
    'fontSize': '12px',
    'border': 'none',
    'fontFamily': 'Jost, sans-serif',
}

table_cell = {
    'whiteSpace': 'normal',
    'height': 'auto',
    'textAlign': 'center',
    'color': '#6783a9',
    'minWidth': '25px',
    'width': '25px',
    'maxWidth': '25px',
}

table_header = {
    'backgroundColor': '#ffffff',
    'fontSize': '12px',
    'fontFamily': 'Jost, sans-serif',
    'color': '#6783a9',
    'textAlign': 'center',
    'fontWeight': 'bold',
    'border': 'none'
}

def get_svg_circle(val: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a Dataframe and replaces text with svg circles coded certain colors
    based on the text. See:
    https://stackoverflow.com/questions/19554834/how-to-center-a-circle-in-an-svg
    https://stackoverflow.com/questions/65778593/insert-shape-in-dash-datatable
    https://community.plotly.com/t/adding-markdown-image-in-dashtable/53894/2

    Args:
        val (pd.Dataframe): Pandas dataframe with metric Rating columns

    Returns:
        pd.Dataframe: returns the same dataframe with svg circles in place of text
    """
    result = val.copy()

    # Use regex and beginning(^) and end-of-line ($) regex anchors to ensure exact matches only
    # NOTE: Using font-awesome circle icon.
    result = result.replace(["^DNMS$",'Does Not Meet Expectations'],'<span style="font-size: 1em; color: #ea5545;"><i class="fa fa-circle center-icon"></i></span>', regex=True)
    result = result.replace(["^AS$",'Approaches Expectations'],'<span style="font-size: 1em; color: #ede15b;"><i class="fa fa-circle center-icon"></i></span>', regex=True)
    result = result.replace(["^MS$",'Meets Expectations'],'<span style="font-size: 1em; color: #87bc45;"><i class="fa fa-circle center-icon"></i></span>', regex=True)
    result = result.replace(["^ES$",'Exceeds Expectations'],'<span style="font-size: 1em; color: #b33dc6;"><i class="fa fa-circle center-icon"></i></span>', regex=True)
    result = result.replace(['N/A','NA','No Rating',np.nan],'', regex=True)

    return result

def create_proficiency_key() -> dash_table.DataTable:
    """
    Creates a dash datatable 'key' using proficiency ratings and
    the Font Awesome circle icon

    Args: 
        None

    Returns:
        key_table (dict): dash DataTable
    """
    rating_icon = '<span style="font-size: 1em;"><i class="fa fa-circle"></i></span>'

    proficiency_key = pd.DataFrame(
        dict(
            [
                (
                    'Rate',
                    [
                        'Exceeds Standard',
                    ],
                ),
                ('icon', [rating_icon]),
                (
                    'Rate2',
                    [
                        'Meets Standard',
                    ],
                ),
                ('icon2', [rating_icon]),
                (
                    'Rate3',
                    [
                        'Approaches Standard',
                    ],
                ),
                ('icon3', [rating_icon]),
                (
                    'Rate4',
                    [
                        'Does Not Meet Standard',
                    ],
                ),
                ('icon4', [rating_icon]),
                (
                    'Rate5',
                    [
                        'No Rating',
                    ],
                ),
                ('icon5', [rating_icon]),
            ]
        )
    )

    rating_headers = proficiency_key.columns.tolist()
    rating_cols = list(col for col in proficiency_key.columns if 'Rate' in col)
    icon_cols = list(col for col in proficiency_key.columns if 'icon' in col)

    key_table = [ 
        dash_table.DataTable(
            css=[dict(selector='tr:first-child', rule='display: none')],
            data=proficiency_key.to_dict('records'),
            cell_selectable=False,
            columns=[
                {'id': 'icon', 'name': '', 'presentation': 'markdown'},
                {'id': 'Rate', 'name': '', 'presentation': 'markdown'},
                {'id': 'icon2', 'name': '', 'presentation': 'markdown'},
                {'id': 'Rate2', 'name': '', 'presentation': 'markdown'},
                {'id': 'icon3', 'name': '', 'presentation': 'markdown'},
                {'id': 'Rate3', 'name': '', 'presentation': 'markdown'},
                {'id': 'icon4', 'name': '', 'presentation': 'markdown'},
                {'id': 'Rate4', 'name': '', 'presentation': 'markdown'},
                {'id': 'icon5', 'name': '', 'presentation': 'markdown'},
                {'id': 'Rate5', 'name': '', 'presentation': 'markdown'},
            ],
            markdown_options={'html': True},
            style_table={
                'paddingTop': '15px',
                'fontSize': '.75em',
                'border': 'none',
                'fontFamily': 'Jost, sans-serif',
            },
            style_cell = {
                'whiteSpace': 'normal',
                'height': 'auto',
                'border': 'none',
                'textAlign': 'right',
                'color': '#6783a9',
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
                    'if': {
                        'filter_query': '{Rate} = "Exceeds Standard"',
                        'column_id': 'icon',
                    },
                    'color': '#b33dc6',
                },
                {
                    'if': {'filter_query': '{Rate2} = "Meets Standard"',
                        'column_id': 'icon2'
                    },
                    'color': '#87bc45',
                },
                {
                    'if': {'filter_query': '{Rate3} = "Approaches Standard"',
                        'column_id': 'icon3'
                    },
                    'color': '#ede15b',
                },
                {
                    'if': {'filter_query': '{Rate4} = "Does Not Meet Standard"',
                        'column_id': 'icon4'
                    },
                    'color': '#ea5545',
                },
                {
                    'if': {'filter_query': '{Rate5} = "No Rating"',
                        'column_id': 'icon5'
                    },
                    'color': '#a4a2a8',
                },
                {
                'if': {
                    'column_id': rating_headers[1],
                },
                'marginLeft':'10px',
                },
            ],
        )
    ]
    return key_table

# TODO: Standardize empty tables

# TODO: This table does not currently display
def no_data_table(label: str = 'No Data to Display') -> list:
    """
    Creates single empty table with provided label

    Args:
        label (String): table label string

    Returns:
        table_layout (list): a dash html.Label object and html.Div object enclosing a dash DataTable
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
                            'fontFamily': 'Jost, sans-serif',
                            'height': '30vh',
                        },
                    ),
                ),
            ]

    return table_layout

# TODO: THis table will display
def no_data_page(label: str) -> list:
    """
    Creates a layout with a single empty table to be used as a replacement for an entire
    page without data for any tables/figs, with provided label

    Args:
        label (String): string label

    Returns:
        table_layout (list): dash html.Div objects enclosing a dash html.Label
        object and a dash DataTable, with css classes
    """

    empty_dict = [{"": ""}]
    table_layout = [
        html.Div(
            [        
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(label, className='header_label'),
                                html.Div(
                                    dash_table.DataTable(
                                        data=empty_dict,
                                        columns = [
                                            {'id': 'emptytable', 'name': 'No Data to Display'},
                                        ],
                                        style_header={
                                            'fontSize': '14px',
                                            'border': 'none',
                                            'textAlign': 'center',
                                            'color': '#6783a9',
                                            'fontFamily': 'Jost, sans-serif',
                                            'height': '30vh',
                                        },
                                        style_data={
                                            'display': 'none',
                                        },
                                    ),
                                ),
                            ],
                            className = 'pretty_container eight columns'
                        ),
                    ],
                    className = 'bare_container_center twelve columns',
                ),
            ],
            className = 'empty_table',
        )
    ]

    return table_layout

# NOTE: Not currently used
def hidden_table() -> list:
    """
    Creates an empty table with no cells. Will be automatically hidden
    ('display': 'none') by css selector chaining for pretty_container.
    See stylesheet.css

    Args:
        None

    Returns:
        table_layout (list): a dash html.Div object enclosing a dash DataTable
    """
    table_layout = [
                html.Div(
                    dash_table.DataTable(
                        columns = [
                            {'id': 'hidden-table', 'name': 'hidden-table'},
                        ],
                    ),
                ),
            ]
    
    return table_layout

def create_chart_label(final_data: pd.DataFrame) -> str:
    """
    Takes a dataframe of academic data and creates a chart label based on
    the df columns

    Args:
        final_data (pd.DataFrame): dataframe of academic data

    Returns:
        label (str): chart label
    """

    final_data_columns = final_data.columns.tolist()

    # the list returns any strings in final_data_columns that are in the
    # ethnicity list or subgroup list. Label is based on whichever list
    # of substrings matches the column list
    if len([i for e in ethnicity for i in final_data_columns if e in i]) > 0:
        label_category = ' Proficiency by Ethnicity'

    elif len([i for e in subgroup for i in final_data_columns if e in i]) > 0:
        label_category = ' Proficiency by Subgroup'                      

    # get the subject using regex
    label_subject = re.search(r'(?<=\|)(.*?)(?=\s)',final_data_columns[0]).group()
    
    label = 'Comparison: ' + label_subject + label_category

    return label
    
def create_school_label(data: pd.DataFrame) -> str:
    """
    Takes a dataframe of academic data and creates a label for each school including
    the school's gradespan.

    Args:
        final_data (pd.DataFrame): dataframe of academic data

    Returns:
        label (str): school label with name and gradespan
    """

    label = data['School Name'] + ' (' + data['Low Grade'].fillna('').astype(str) + \
        '-' + data['High Grade'].fillna('').astype(str) + ')'
    
    # removes empty parentheses from School Corp
    label = label.str.replace("\(-\)", '',regex=True)

    return label

# NOTE: Displays both 162Day and Majority Enrolled, along with Difference
def create_growth_table_both(label: str, content: pd.DataFrame, kind: str) -> list:
    """
    Takes a label, a dataframe, and a descriptive (type) string and creates a multi-header
    table with academic growth and sgp data.

    Args:
        label (str): Table title
        content (pd.DataTable): dash dataTable
        kind (str): 'sgp|growth'
    Returns:
        table_layout (list): dash html.Div enclosing html.Label and DataTable
    """
   
    data = content.copy()

    num_cols = len(data.columns)

    if len(data.index) == 0 or num_cols == 1:
        table_layout = [
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

        # determines the col_width class and width of the category column based
        # on the size (# of cols) of the dataframe
        if num_cols <= 3:
            col_width = 'four'
            category_width = 70
        if num_cols > 3 and num_cols <=4:
            col_width = 'six'
            category_width = 35
        elif num_cols >= 5 and num_cols <= 8:
            col_width = 'six'
            category_width = 30
        elif num_cols == 9:
            col_width = 'seven'
            category_width = 30
        elif num_cols >= 10 and num_cols <= 13:
            col_width = 'seven'
            category_width = 15
        elif num_cols > 13 and num_cols <=17:
            col_width = 'nine'
            category_width = 15
        elif num_cols > 17:
            col_width = 'ten'
            category_width = 15

        # splits column width evenly for all columns other than 'Category'
        data_col_width = (100 - category_width) / (num_cols - 1)

        class_name = 'pretty_container ' + col_width + ' columns'

        all_cols = data.columns.tolist()

        data_cols = [col for col in all_cols if 'Category' not in col]
        first_cols = [col for col in all_cols if 'Days' in col]
        diff_cols = [col for col in all_cols if 'Diff' in col]

        # remove subject from category
        data['Category'] = data['Category'].map(lambda x: x.split('|')[0]).copy()

        # build multi-level headers
        name_cols = [['Category','']]

        # Split columns into Year (top level) and "162 Days", "Majority Enrolled",
        # "diff" (second level)
        for item in all_cols:

            if item.startswith('20'):
                name_cols.append([item[:4],item[4:]])

        table_header_conditional = [
            {   # need border left on the first column (162 Days) of each group
                'if': {
                    'column_id': col,
                    'header_index': 1,
                },
                'borderLeft': '.5px solid #b2bdd4',
            } for col in first_cols
        ] + [
            {   
                'if': {
                    'column_id': col,
                    'header_index': 1,
                },
                'borderTop': '.5px solid #b2bdd4',
                'borderBottom': '.5px solid #b2bdd4',
        } for col in data_cols
        ] + [
            {
                'if': {
                    'column_id': data_cols[-1],
                    'header_index': 1,
                },
                'borderRight': '.5px solid #b2bdd4',
            }
        ]

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
                    'column_id': col
                },
                'textAlign': 'center',
                'fontWeight': '500',
                'width': str(data_col_width) + '%',
            } for col in data_cols
        ]

        table_data_conditional = [
            {
                'if': {
                    'state': 'selected'
                },
                'backgroundColor': 'rgba(112,128,144, .3)',
                'border': 'thin solid silver'
            },
            {
                'if': {
                    'row_index': 'odd'
                },
                'backgroundColor': '#eeeeee'
            }
        ] + [
            {
                'if': {
                    'column_id': data_cols[-1],
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
                    'column_id': col,
                },
                'borderRight': '.5px solid #b2bdd4',
                'textAlign': 'center',
            } for col in diff_cols
        ] + [
            {
                'if': {
                    'filter_query': '{{{col}}} < 0'.format(col=col),
                    'column_id': col
                },
                'fontWeight': 'bold',
                'color': '#b44655',
                'fontSize': '10px',
            } for col in diff_cols
        ] + [
            {
                'if': {
                    'filter_query': '{{{col}}} > 0'.format(col=col),
                    'column_id': col
                },
                'fontWeight': 'bold',
                'color': '#81b446',
                'fontSize': '10px',
            } for col in diff_cols
        ]

        if kind == 'sgp':
            col_format=[
                {
                'name': col, 'id': all_cols[idx], 'type':'numeric',
                'format': Format()
                }
                for (idx, col) in enumerate(name_cols)
            ]

        else:
            col_format=[
                {
                'name': col, 'id': all_cols[idx], 'type':'numeric',
                'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
                }
                for (idx, col) in enumerate(name_cols)
            ]

        table_layout = [
            html.Div(
                [
                    html.Label(label, className='header_label'),
                    html.Div(
                        dash_table.DataTable(
                            data.to_dict('records'),
                            columns=col_format,
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

    return table_layout

# NOTE: Displays just Majority Enrolled (with 162 Day values in tooltip)
def create_growth_table(label: str, data: pd.DataFrame, kind: str) -> list:
    """
    Takes a label, a dataframe, and a descriptive (type) string and creates a multi-header
    table with academic growth and sgp data.

    Args:
        label (str): Table title
        content (pd.DataTable): dash dataTable
        kind (str): 'sgp|growth'
    Returns:
        table_layout (list): dash html.Div enclosing html.Label and DataTable
    """
    data_me = data.loc[:, data.columns.str.contains('Category|Majority Enrolled')].copy()
    data_me = data_me.rename(columns={c: c[:4] for c in data_me.columns if c not in ['Category']})

    # 162 day data is used for tooltip
    data_162 = data.loc[:, data.columns.str.contains('Category|162 Days')].copy()
    data_162 = data_162.rename(columns={c: c[:4] for c in data_162.columns if c not in ['Category']})
    data_162 = data_162.drop('Category', axis=1)
    
    num_cols = len(data_me.columns)

    if len(data_me.index) == 0 or num_cols == 1:
        table_layout = [
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

        if num_cols <= 3:
            col_width = 'four'
            category_width = 70
        if num_cols > 3 and num_cols <=4:
            col_width = 'six'
            category_width = 35
        elif num_cols >= 5 and num_cols <= 8:
            col_width = 'six'
            category_width = 30
        elif num_cols > 9:
            col_width = 'seven'
            category_width = 30

        data_cols = (100 - category_width) / (num_cols - 1)
        class_name = 'pretty_container ' + col_width + ' columns'

        all_cols = data_me.columns.tolist()
        data_cols = [col for col in all_cols if 'Category' not in col]

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
                    'column_id': col
                },
                'textAlign': 'center',
                'fontWeight': '500',
                'width': str(data_cols) + '%',
            } for col in data_cols
        ]

        table_header_conditional = [
            {
                'if': {
                    'column_id': col,
                },
                'borderBottom': '.5px solid #b2bdd4',
            } for col in data_cols
        ]

        table_data_conditional = [
            {
                'if': {
                    'state': 'selected'
                },
                'backgroundColor': 'rgba(112,128,144, .3)',
                'border': 'thin solid silver'
            },
            {
                'if': {
                    'row_index': 'odd'
                },
                'backgroundColor': '#eeeeee'
            },
        ] + [
            {
                'if': {
                    'row_index': 0
                },
                'paddingTop': '5px'
            },
        ]

        if kind == 'sgp':
            column_format=[
                {
                'name': col, 'id': col, 'type':'numeric',
                'format': Format()
                }
                for col in all_cols
            ]

            # NOTE: if value != value then value is NaN
            tooltip_format = [
                {
                    column: {
                        'value': '162 Days: {:.1f}'.format(float(value)) if value == value else '',
                        'type': 'markdown'
                    }
                    for column, value in row.items()
                }
                for row in data_162.to_dict('records')
            ]

        else:
            column_format = [
                {
                'name': col, 'id': col, 'type':'numeric',
                'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
                }
                for col in all_cols
            ]

            tooltip_format = [
                {
                    column: {
                        'value': '162 Days: {:.2%}'.format(float(value)) if value == value else '',
                        'type': 'markdown'
                    }
                    for column, value in row.items()
                }
                for row in data_162.to_dict('records')
            ]                

        table_layout = [
            html.Div(
                [
                    html.Label(label, className='header_label'),
                    html.Div(
                        dash_table.DataTable(
                            data_me.to_dict('records'),
                            columns = column_format,
                            style_table = {'height': '300px'},
                            style_data = table_style,
                            style_data_conditional = table_data_conditional,
                            style_header = table_header,
                            style_header_conditional = table_header_conditional,
                            style_cell = table_cell,
                            style_cell_conditional = table_cell_conditional,
                            tooltip_data = tooltip_format,
                            css=[{
                                'selector': '.dash-table-tooltip',
                                'rule': 'font-size: 12px'
                            }],
                        )
                    )
                ],
                # className = class_name
            )
        ]

    return table_layout

def process_table_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a series that merges school name and grade spans and drops the
    grade span columns from the dataframe (they are not charted)

    Args:
        data (pd.DataFrame): dataframe of academic data

    Returns:
        data (pd.DataFrame): dataframe
    """    
    school_names = create_school_label(data)

    data = data.drop(['Low Grade', 'High Grade'], axis = 1)

    # shift the 'School Name' column to the first position and replace
    # the values in 'School Name' column with the school_names series
    data = data.drop('School Name', axis = 1)
    data['School Name'] = school_names

    first_column = data.pop('School Name')
    data.insert(0, 'School Name', first_column)
    
    return data

def process_chart_data(school_data: pd.DataFrame, corporation_data: pd.DataFrame, comparison_data: pd.DataFrame, categories: list, corp_name: str) -> Tuple[pd.DataFrame, str, str]:
    """
    Processes several dataframes for display in comparison tables while tracking both schools that are missing data for 
    a particulary category (category_string) and schools that are missing data for all categories (school_string).

    Args:
        school_data (pd.DataFrame): academic data from the selected school
        corporation_data (pd.DataFrame): academic data from the school corporation where the school is located
        comparison_data (pd.DataFrame): academic data from comparable schools (may or may not be in school corp)
        categories (list): a list of academic categories
        corp_name (str): the name of the school corporation

    Returns:
        Tuple[
            final_data (pd.DataFrame): all dataframes cleaned up and combined
            category_string (str): a string of categories for which the selected school has no data. 
            school_string (str): a string of schools which have no data
        ]
    """
    all_categories = categories + info_categories

    school_columns = [i for i in categories if i in school_data.columns]

    # sort corp data by the school columns (this excludes any categories
    # not in the school data)
    corporation_data = corporation_data.loc[:, (corporation_data.columns.isin(school_columns))].copy()

    # add the school corporation name
    corporation_data['School Name'] = corp_name

    # concatenate the school and corporation dataframes, filling empty values (e.g., Low and High Grade) with ''
    first_merge_data = pd.concat([school_data, corporation_data], sort=False).fillna('')

    # filter comparable schools
    comparison_data = comparison_data.loc[:, comparison_data.columns.isin(all_categories)].copy()

    # concatenate school/corp and comparison dataframes
    combined_data = pd.concat([first_merge_data,comparison_data])
    combined_data = combined_data.reset_index(drop=True)

    # make a copy (used for comparison purposes)
    final_data = combined_data.copy()

    # get a list of all of the Categories (each one a column)
    school_categories = [ele for ele in school_columns if ele not in info_categories]

    # test all school columns and drop any where all columns (proficiency data) is nan/null
    final_data = final_data.dropna(subset=school_categories, how='all')  

    # replace any blanks with NaN
    final_data = final_data.replace(r'^\s*$', np.nan, regex=True)

    # get the names of the schools that have no data by comparing the
    # column sets before and after the drop
    missing_schools = list(set(combined_data['School Name']) - set(final_data['School Name']))

    # Now comes the hard part. Get the names and categories of schools that
    # have data for some categories and not others. In the end we want
    # to build a list of schools that is made up of schools that are missing
    # all data + schools that are missing some data + what data they are
    # missing
    check_data = final_data.copy()
    check_data = check_data.drop(['Low Grade','High Grade'], axis = 1)
    check_data = check_data.reset_index(drop=True)

    # get a list of the categories that are missing from selected school data and
    # strip everything following '|' delimeter for annotation
    # NOTE: this is doing a slightly different thing than the check_for_insufficient_n_size()
    # & check_for_no_data() functions (calculations.py), but may want to check at some point
    # to see which process is faster
    missing_categories = [i for i in categories if i not in check_data.columns]                
    missing_categories = [s.split('|')[0] for s in missing_categories]

    # get index and columns where there are null values (numpy array)
    idx, idy = np.where(pd.isnull(check_data))

    # np.where returns an index for each column, resulting in duplicate
    # indexes for schools missing multiple categories. But we only need one
    # unique value for each school that is missing data
    schools_with_missing = np.unique(idx, axis=0)

    schools_with_missing_list = []
    if schools_with_missing.size != 0:
        for i in schools_with_missing:

            schools_with_missing_name = check_data.iloc[i]['School Name']

            # get missing categories as a list, remove everything
            # after the '|', and filter down to unique categories
            with_missing_categories = list(check_data.columns[idy])
            with_missing_categories = [s.split('|')[0] for s in with_missing_categories]
            unique__missing_categories = list(set(with_missing_categories))

            # create a list of ['School Name (Cat 1, Cat2)']
            schools_with_missing_list.append(schools_with_missing_name + ' (' + ', '.join(unique__missing_categories) + ')')

    else:
        schools_with_missing_list = []

    # create the string. Yes this is ugly, and i will probably fix it later, but
    # we need to make sure that all conditions match proper punctuation.
    if len(schools_with_missing_list) != 0:
        if len(schools_with_missing_list) > 1:
            schools_with_missing_list = ', '.join(schools_with_missing_list)
        else:
            schools_with_missing_list = schools_with_missing_list[0]

        if missing_schools:
            missing_schools = [i + ' (All)' for i in missing_schools]
            school_string = ', '.join(list(map(str, missing_schools))) + '.'
            school_string = schools_with_missing_list + ', ' + school_string
        else:
            school_string = schools_with_missing_list + '.'
    else:
        if missing_schools:
            missing_schools = [i + ' (All)' for i in missing_schools]
            school_string = ', '.join(list(map(str, missing_schools))) + '.'
        else:
            school_string = 'None.'

    # Create string for categories for which the selected school has
    # no data. These categories are not shown at all.
    if missing_categories:
        category_string = ', '.join(list(map(str, missing_categories))) + '.'
    else:
        category_string = 'None.'

    return final_data, category_string, school_string

def create_basic_info_table(data: pd.DataFrame, label: str) -> list:
    """
    Takes a dataframe of two or more columns and a label and creates a single
    header table with borders around each cell. If more rows are added, need
    to adjust logic to remove horizontal borders between rows.
    
    Args:
        label (String): Table title
        data (pd.DataTable): dash dataTable
        table_type (String): type of table.

    Returns:
        table_layout (list): dash DataTable wrapped in dash html components
    """

    table_size = len(data.columns)

    # determines the col_width class and width of the category column based
    # on the size (# of cols) of the dataframe
    if table_size <= 3:
        col_width = 'six'
        category_width = 35
    if table_size > 3 and table_size <=5:
        col_width = 'seven'
        category_width = 25
    elif table_size > 5 and table_size <= 7:
        col_width = 'eight'
        category_width = 20
    elif table_size > 7 and table_size <= 9:
        col_width = 'nine'
        category_width = 20
    elif table_size >= 10 and table_size <= 13:
        col_width = 'ten'
        category_width = 15
    elif table_size > 13:
        col_width = 'ten'
        category_width = 15

    class_name = 'pretty_container ' + col_width + ' columns'

    year_headers = [y for y in data.columns.tolist() if 'Category' not in y]

    # set column widths
    # category_width = 20
    category_width = category_width + 10
    data_width = 100 - category_width
    year_width = data_width / (table_size - 1)

    table_cell_conditional = [
        {
            'if': {
                'column_id': 'Category'
            },
            'textAlign': 'left',
            'paddingLeft': '20px',
            'fontWeight': '500',
            'width': str(category_width) + '%'
        }
    ] + [
        {
            'if': {
                'column_id': year
            },
            'textAlign': 'center',
            'fontWeight': '500',
            'width': str(year_width) + '%',
            'borderRight': '.5px solid #b2bdd4',
            'borderLeft': '.5px solid #b2bdd4',  
        } for year in year_headers
    ]

    table_header_conditional = [
        {
            'if': {
                'column_id': year,
            },
            'borderBottom': '.5px solid #b2bdd4'
        } for year in year_headers
    ]

    table_data_conditional = [
        {
            'if': {
                'state': 'selected'
            },
            'backgroundColor': 'rgba(112,128,144, .3)',
            'border': 'thin solid silver'
        },
        {
            'if': {
                'row_index': 'odd'
            },
            'backgroundColor': '#eeeeee'
        }
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
                'column_id': data.columns[-1],
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
            'borderLeft': 'none',
            'borderTop': 'none',                        
        },
    ] + [
        { 
            'if': {
                'column_id': year,
            },
            'fontSize': '10px',
            'textAlign': 'center',
            'borderLeft': '.5px solid #b2bdd4',
        } for year in year_headers
    ]


    table_layout = [
        html.Div(
            [
                html.Label(label, className='header_label'),
                html.Div(
                    dash_table.DataTable(
                        data.to_dict('records'),
                        columns = [{"name": i, "id": i, "type":"numeric","format": FormatTemplate.percentage(2)} for i in data.columns],
                        style_data = {
                            'fontSize': '12px',
                            'fontFamily': 'Jost, sans-serif',
                            'border': 'none'                    
                        },    
                        style_header = table_header,
                        style_cell = {
                            'whiteSpace': 'normal',
                            'height': 'auto',
                            'textAlign': 'center',
                            'color': '#6783a9',
                            'minWidth': '25px',
                            'width': '25px',
                            'maxWidth': '25px',
                        },
                        style_data_conditional = table_data_conditional,
                        style_header_conditional = table_header_conditional,
                        style_cell_conditional = table_cell_conditional,
                        merge_duplicate_headers=True
                    ),
                ),
            ],
            className = class_name
        )        
    ]

    return table_layout

def create_academic_info_table(data: pd.DataFrame, label: str) -> list:
    """
    Takes a dataframe of two or more columns and a label, and creates a table with multi-headers.
    
    Args:
        label (String): Table title
        data (pd.DataTable): dash dataTable

    Returns:
        table_layout (list): dash DataTable wrapped in dash html components
    """

    table_size = len(data.columns)

    if table_size > 1:
        # determines the col_width class and width of the category column based
        # on the size (# of cols) of the dataframe
        if table_size <= 3:
            col_width = 'four'
            category_width = 40
        if table_size > 3 and table_size <=5:
            col_width = 'six'
            category_width = 20
        elif table_size > 5 and table_size < 7:
            col_width = 'six'
            category_width = 20
        elif table_size >= 7 and table_size < 9:
            col_width = 'seven'
            category_width = 20
        elif table_size >= 9 and table_size <= 13:
            col_width = 'eight'
            category_width = 15
        elif table_size > 13 and table_size <=17:
            col_width = 'nine'
            category_width = 15
        elif table_size > 17:
            col_width = 'ten'
            category_width = 15

        class_name = 'pretty_container ' + col_width + ' columns'

        # rename columns n_size before getting n col list
        data.columns = data.columns.str.replace('N-Size|SN-Size', 'Tested', regex=True)
        data.columns = data.columns.str.replace('School', 'Proficiency', regex=True)
        nsize_headers = [y for y in data.columns if 'Tested' in y]
        year_headers = [y for y in data.columns if 'Proficiency' in y]

        # get new list of cols after replacing N-Size
        all_cols = data.columns.tolist()

        # set column widths
        if table_size <= 3:
            data_width = 100 - category_width
            nsize_width = year_width = data_width / (table_size - 1)          
        
        else:
            nsize_width = 5
            data_width = 100 - category_width - nsize_width
            year_width = data_width / (table_size - 1)

  
        # formatting logic is slightly different for a multi-header table
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
                'column_id': nsize
            },
                'textAlign': 'center',
                'fontWeight': '300',
                'fontSize': '8px',
                'width': str(nsize_width) + '%'
            } for nsize in nsize_headers
        ]

        table_header_conditional = [
            {
                'if': {
                    'column_id': year,
                    'header_index': 1,
                },
                'borderLeft': '.5px solid #b2bdd4',
                'borderTop': '.5px solid #b2bdd4',
                'borderBottom': '.5px solid #b2bdd4'
            } for year in year_headers
        ] + [
            {   'if': {
                'column_id': nsize,
                'header_index': 1,
            },
                'textAlign': 'center',
                'fontWeight': '400',
                'fontSize': '12px',
                'borderRight': '.5px solid #b2bdd4',
                'borderTop': '.5px solid #b2bdd4',
                'borderBottom': '.5px solid #b2bdd4'
        } for nsize in nsize_headers
        ] + [
            {   'if': {
                'column_id': all_cols[-1],
                'header_index': 1,
            },
            'borderRight': '.5px solid #b2bdd4',
            }
        ]

        table_data_conditional = [
            {
                'if': {
                    'state': 'selected'
                },
                'backgroundColor': 'rgba(112,128,144, .3)',
                'border': 'thin solid silver'
            },
            {
                'if': {
                    'row_index': 'odd'
                },
                'backgroundColor': '#eeeeee'
            }
        ] + [
            {
                'if': {
                    'column_id': all_cols[-1],
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
                    'column_id': nsize,
                },
                'fontSize': '10px',
                'textAlign': 'center',
                'borderRight': '.5px solid #b2bdd4',
            } for nsize in nsize_headers
        ]

        # build multi-level headers
        name_cols = [['Category','']]

        # Split columns into two levels
        for item in all_cols:
            if item.startswith('20'):
                name_cols.append([item[:4],item[4:]])

        table_columns = [
                {
                    'name': col,
                    'id': all_cols[idx],
                    'type': 'numeric',
                    'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses),
                }
                if 'Proficiency' in col      
                
                else
                    {
                        'name': col,
                        'id': all_cols[idx],
                        'type':'numeric',
                        'format': Format()
                    }
                    for (idx, col) in enumerate(name_cols)
        ]

        table_layout = [
            html.Div(
                [
                    html.Label(label, className='header_label'),
                    html.Div(
                        dash_table.DataTable(
                            data.to_dict('records'),
                            columns = table_columns,
                            style_data = table_style,
                            style_data_conditional = table_data_conditional,
                            style_header = table_header,
                            style_cell = table_cell,
                            style_header_conditional = table_header_conditional,
                            style_cell_conditional = table_cell_conditional,
                            merge_duplicate_headers=True
                        ),
                    )
                ],
                className = class_name
            )
        ]

    else:

        empty_dict = [{"": ""}]
        table_layout = [
            html.Div(
                [
                    html.Label(label, className='header_label'),
                    html.Div(
                        dash_table.DataTable(
                            data=empty_dict,
                            columns = [
                                {'id': 'emptytable', 'name': 'No Data to Display'},
                            ],
                            style_header={
                                'fontSize': '14px',
                                'border': 'none',
                                'textAlign': 'center',
                                'color': '#6783a9',
                                'fontFamily': 'Jost, sans-serif',
                                'height': '30vh',
                            },
                            style_data={
                                'display': 'none',
                            },
                        ),
                    ),
                ],
                className = 'pretty_container four columns'
            )
        ]

    return table_layout

def create_metric_table(label: str, content: pd.DataFrame) -> list:
    """
    Takes a label and a dataframe consisting of Rating and Metric Columns and returns
    a dash datatable. NOTE: could possibly be less complicated than it is, or maybe not-
    gonna leave it up to future me

    Args:
        label (String): Table title
        content (pd.DataTable): dash dataTable

    Returns:
        table (list): dash html.Div enclosing html.Label and DataTable
    """

    data = content.copy()

    table_size = len(data.columns)

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
        # calculation from calculateMetrics(), but leaving it in for now in case
        # we ultimately choose to display it

        # NOTE: The order of these operations matters
        # remove all Corp Rate / Corp Avg columns
        data = data.loc[:, ~data.columns.str.contains('Corp')]

        # determines the col_width class and width of the category column based
        # on the size (# of cols) of the dataframe
        if table_size <= 3:
            col_width = 'four'
            category_width = 40
        if table_size > 3 and table_size <=5:
            col_width = 'six'
            category_width = 35
        elif table_size > 5 and table_size <= 7:
            col_width = 'seven'
            category_width = 30
        elif table_size > 7 and table_size <= 9:
            col_width = 'seven'
            category_width = 20
        elif table_size >= 10 and table_size <= 13:
            col_width = 'eight'
            category_width = 15
        elif table_size > 13 and table_size <=17:
            col_width = 'ten'
            category_width = 15
        elif table_size > 17:
            col_width = 'eleven'
            category_width = 15

        list_cols = data.columns.tolist()
        # used for formatting purposes
        year_headers = [y for y in list_cols if 'School' in y]
        rating_headers = [y for y in list_cols if 'Rate' in y]
        diff_headers = [y for y in list_cols if 'Diff' in y]

        # rename n_size before getting col list
        data.columns = data.columns.str.replace('N-Size', 'Tested', regex=True)
        nsize_headers = [y for y in data.columns.tolist() if 'Tested' in y]

        # get new col list after renaming N-Size
        all_cols = data.columns.tolist()

        format_cols = rating_headers + diff_headers

        # splits column width evenly for all columns other than 'Category'
        # can adjust individual categories by adjusting formula

        # set column widths
        if table_size <= 3:
            data_width = 100 - category_width
            nsize_width = year_width = rating_width = diff_width = data_width / (table_size - 1)          
        
        else:

            nsize_width = 5
            data_width = 100 - category_width - nsize_width

            data_col_width = data_width / (table_size - 1)
            rating_width = data_col_width/2
            year_width = data_col_width + data_col_width/4
            diff_width = data_col_width + data_col_width/4

        class_name = 'pretty_container ' + col_width + ' columns'

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
                'column_id': nsize
            },
                'textAlign': 'center',
                'fontWeight': '500',
                'width': str(nsize_width) + '%'
            } for nsize in nsize_headers
        ]  + [            
            {   'if': {
                'column_id': rating
            },
                'textAlign': 'center',
                'fontWeight': '700',
                'width': str(rating_width) + '%'
            } for rating in rating_headers
        ]  + [
            {   'if': {
                'column_id': diff
            },
                'textAlign': 'center',
                'fontWeight': '500',
                'width': str(diff_width) + '%'
            } for diff in diff_headers
        ]
 
        data['Category'] = data['Category'].map(lambda x: x.split('|')[0]).copy()

        name_cols = [['Category','']]

        # Build list of lists, top level and secondary level column names
        # for multi-level headers
        for item in all_cols:
            if item.startswith('20'):
                if 'Rate' in item:
                    item = item[:8]

                name_cols.append([item[:4],item[4:]])

        # NOTE: This add a border to header_index:1 for each category
        # For a single bottom line: comment out blocks, comment out
        # style_header_conditional in table declaration,
        # and uncomment style_as_list in table declaration
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
                'column_id': diff,
                'header_index': 1,
            },
                'textAlign': 'center',
                'fontWeight': '400',
                'fontSize': '12px',
                'borderTop': '.5px solid #b2bdd4',
                'borderBottom': '.5px solid #b2bdd4',
        } for diff in diff_headers
        ]  + [
            {   'if': {
                'column_id': nsize,
                'header_index': 1,
            },
                'textAlign': 'center',
                'fontWeight': '400',
                'fontSize': '12px',
                'borderTop': '.5px solid #b2bdd4',
                'borderBottom': '.5px solid #b2bdd4',
        } for nsize in nsize_headers
        ] + [
            # Use 'headers[-1]' and 'borderRight' for each subheader to have full border
            # Use 'headers[1]' and 'borderLeft' to leave first and last columns open on
            # right and left
            {   'if': {
                'column_id': all_cols[-1],
            #    'column_id': headers[1],
                'header_index': 1,
            },
            'borderRight': '.5px solid #b2bdd4',
            }
        ]

        # formatting logic is slightly different for a multi-header table
        table_data_conditional = [
            {
                'if': {
                    'state': 'selected'
                },
                'backgroundColor': 'rgba(112,128,144, .3)',
                'border': 'thin solid silver'
            },
            {
                'if': {
                    'row_index': 'odd'
                },
                'backgroundColor': '#eeeeee'
            }
        ] + [
            {
                'if': {
                    'column_id': all_cols[-1],
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
            {   # NOTE: This doesn't work as cell_conditional - is it because its markdown?
                'if': {
                    'column_id': nsize,
                },
                'fontSize': '10px',
                'textAlign': 'center',
            } for nsize in nsize_headers
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

        table_columns = [
            {
                'name': col,
                'id': all_cols[idx],
                'presentation': 'markdown'
            }
            if 'Rate' in col or 'Tested' in col

            # NOTE: Cannot figure out how to have three different col formatting conditions   
            # { 
            #     'name': col,
            #     'id': headers[idx],
            #     'type':'numeric',
            #     'format': Format()
            # }
            # if 'n' in col

            else {
                'name': col,
                'id': all_cols[idx],
                'type':'numeric',
                'format': Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
            }
            for (idx, col) in enumerate(name_cols)
        ]

        table = [
            html.Div(
                [
                    html.Label(label, className='header_label'),
                    html.Div(
                        dash_table.DataTable(
                            data.to_dict('records'),
                            columns = table_columns,
                            style_data = table_style,
                            style_data_conditional = table_data_conditional,
                            style_header = table_header,
                            style_header_conditional = table_header_conditional,
                            style_cell = table_cell,
                            style_cell_conditional = table_cell_conditional,
                            merge_duplicate_headers=True,
                            markdown_options={'html': True},
                            tooltip_conditional=[
                                {
                                    'if': {
                                        'column_id': col,
                                        'filter_query': f'{{{col}}} = "-***"',
                                    },
                                    'type': 'markdown',
                                    'value': 'This indicates a reduction from "***" (a measurable, but not reportable, value) in one year to "0" in the following year.'
                                } for col in data.columns
                            ],
                            tooltip_delay=0,
                            tooltip_duration=None
                        )
                    )
                ],
                className = class_name
            )
        ]

    return table


def set_table_layout(table1: list, table2: list, cols: pd.Series) -> list:
    """
    Determines table layout depending on the size (# of cols) of the tables,
    either side by side or on an individual row

    Args:
        table1 (list): dash DataTable
        table2 (list): dash DataTable
        cols (pandas.core.indexes.Base.index): Pandas series of column headers

    Returns:
        table_layout (list): an html Div enclosing dash DataTables and css formatting
    """

    # if same table is passed twice, we force single table layout
    if table1 == table2:
        table_layout = [
                html.Div(
                    table1,
                    className = 'bare_container_center twelve columns',
                )
        ]

    else:

        if len(cols) >= 4:
            table_layout = [
                    html.Div(
                        table1,
                        className = 'bare_container_center twelve columns',
                    ),
                    html.Div(
                        table2,
                        className = 'bare_container_center twelve columns',
                    ),
            ]

        else:

            table_layout = [
                    html.Div(
                        [
                            table1[0],
                            table2[0],
                        ],
                        className = 'bare_container_center twelve columns',
                    ),
            ]

    return table_layout

def create_comparison_table(data: pd.DataFrame, school_name: str, label: str) -> list:
    """
    Takes a dataframe that is a column of schools and one or more columns
    of data, school name, and table label. Uses the school name to find
    the index of the selected school to highlight it in table

    Args:
        data (pd.DataFrame): dataframe of academic data
        school_name (str): 
        label (str): title of table

    Returns:
        table_layout (list): dash DataTable wrapped in dash html components
    """

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

    # simplify and clarify column names (remove everything between | & %)
    data.columns = data.columns.str.replace(r'\|(.*?)\%', '', regex=True)

# NOTE: Try AG Grid for more responsive table
#       pip install dash-ag-grid==2.0.0
#       import dash_ag_grid as dag

    table = dash_table.DataTable(
        data.to_dict('records'),
        columns = [{'name': i, 'id': i, 'type':'numeric','format': FormatTemplate.percentage(2)} for i in data.columns],
        # sort_action='native',
        merge_duplicate_headers=True,
        style_as_list_view=True,
        id='tst-table',
        style_data = table_style,
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
            {
                'if': {
                    'state': 'selected'
                },
                'backgroundColor': 'rgba(112,128,144, .3)',
                'border': 'thin solid silver'
            }
        ],
        style_header = table_header,
        style_header_conditional = [
            {
                'if': {
                    'header_index': 0,
                    },
                    'text-decoration': 'underline'
            },
        ],
        style_cell = table_cell,
        style_cell_conditional = [
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
                html.Div(table)
                ]
            )
        ]
    else:
        table_layout = [
            html.Div(
                [
                html.Div(table)
                ]
            )
        ]

    return table_layout

def combine_group_barchart_and_table(fig,table,category_string,school_string):

    layout = [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(fig, style={"marginBottom": "-20px"})
                    ],
                    className = "pretty_close_container twelve columns",
                ),
            ],
            className="row"
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(table),
                        html.P(
                            children=[
                            html.Span("Categories with no data to display:", className = "category_string_label"),
                            html.Span(category_string, className = "category_string"),
                            ],
                            style={"marginTop": -10, "marginBottom": -10}
                        ),
                        html.P(
                            children=[
                            html.Span("School Categories with insufficient n-size or no data:",className = "school_string_label"),
                            html.Span(school_string, className = "school_string"),
                            ],
                            
                        ),
                    ],
                    className = "close_container twelve columns"
                )
                ],
                className="row"
            )
    ]
    return layout
