#####################################
# ICSB Dashboard - Layout Functions #
#####################################
# author:   jbetley
# version:  1.10
# date:     09/10/23

import pandas as pd
from dash import html
from .load_data import info_categories
from .string_helpers import create_chart_label,combine_school_name_and_grade_levels, identify_missing_categories
from .charts import make_group_bar_chart
from .tables import create_comparison_table

def create_hs_analysis_layout(data_type: str, data: pd.DataFrame, categories: list, school_name: str) -> list:

    tested_categories = []

    if data_type == "School Total":
        search_string = data_type

        for c in categories:
            tested_categories.append(c + " Benchmark %")

    elif data_type == "EBRW" or data_type == "Math":
        search_string = data_type + " Benchmark %"
        
        for c in categories:
            tested_categories.append(c + "|" + search_string)

    elif data_type == "Graduation Rate":
        search_string = data_type
    
        for c in categories:
            tested_categories.append(c + "|" + search_string)
    else:
        final_analysis_group = []   # type:list

        return final_analysis_group

    analysis_cols = [col for col in data.columns if search_string in col and any(substring for substring in categories if substring in col)]

    analysis_cols = info_categories + analysis_cols
    analysis_data = data[analysis_cols]

    analysis_data = analysis_data.filter(regex="|".join([data_type,"School Name","Low Grade","High Grade"]))

    # data will always have at least three cols (School Name, Low Grade, High Grade)
    if len(analysis_data.columns) > 3:

         # NOTE: For transparency purposes, we want to identify all categories that are missing from
        # the possible dataset, including those that aren't going to be displayed (because the school
        # is missing them). Because there are many cases where there wont be any data at all (eg, it
        # hasn't yet been released, or there is no data for a particular yet. So we need to check whether
        # there is any data to display before and after we collect the missing category information. After
        # we collect any missing information, we need to drop any columns where the school has no data and
        # then check again to see if the dataframe has any info.
        analysis_data, category_string, school_string = identify_missing_categories(analysis_data, tested_categories)

        # Once the missing category and missing school strings are built, we drop any columns
        # where the school has no data by finding the index of the row containing the school
        # name and dropping all columns where the row at school_name_idx has a NaN value
        school_name_idx = analysis_data.index[analysis_data["School Name"].str.contains(school_name)].tolist()[0]
        analysis_data = analysis_data.loc[:, ~analysis_data.iloc[school_name_idx].isna()]

        if len(analysis_data.columns) > 1:
            analysis_label = create_chart_label(analysis_data)
            analysis_chart = make_group_bar_chart(analysis_data, school_name, analysis_label)
            analysis_table_data = combine_school_name_and_grade_levels(analysis_data)
            analysis_table = create_comparison_table(analysis_table_data, school_name,"")

            final_analysis_group = create_group_barchart_layout(analysis_chart,analysis_table, category_string, school_string)

        else:
            final_analysis_group = []

    else:
        final_analysis_group = []

    return final_analysis_group

def create_growth_layout(table: list, fig: list, label: str) -> list:
    """
    Takes two lists, a simple html.Div layout containing a dash.DataTable and
    a simple html.Div layout with a plotly Go.Scatter object. Also a label.
    returns a combined layout for a plotly dash app.

    Args:
        table (list): dash datatable html.Div layout
        fig (list): plotly fig html.Div layout
        label (str): string

    Returns:
        list: table layout
    """    
    table_layout = [
        html.Div(
            [
                html.Div(
                    [                    
                        html.Label(label, className="label__header"),                    
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(table, style={"marginTop": "20px"}),
                                    ],
                                    className="pretty-container six columns",
                                ),
                                html.Div(
                                    [
                                        html.Div(fig),
                                    ],
                                    className="pretty-container six columns",
                                ),
                            ],
                            className="bare-container--flex twelve columns",
                        ),
                    ],
                    className="bare-container--flex--outline twelve columns",
                ),       
            ],
            className="bare-container--flex--center twelve columns",
        ),             
    ]

    return table_layout

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
                    className = "bare-container--flex--center twelve columns",
                )
        ]

    else:

        if len(cols) >= 4:
            table_layout = [
                    html.Div(
                        table1,
                        className = "bare-container--flex--center twelve columns",
                    ),
                    html.Div(
                        table2,
                        className = "bare-container--flex--center twelve columns",
                    ),
            ]

        else:

            table_layout = [
                    html.Div(
                        [
                            table1[0],
                            table2[0],
                        ],
                        className = "bare-container--flex--center twelve columns",
                    ),
            ]

    return table_layout

def create_group_barchart_layout(fig: list, table: list,category_string: str, school_string: str) -> list:
    """
    Takes two lists, a simple html.Div layout containing a dash.DataTable and
    a simple html.Div layout with a plotly px.bar object. Also two strings generated
    by the identify_missing_categories() function and return a combined layout for a plotly dash app.    

    Args:
        fig (list): plotly px.bar object in a layout (create_group_bar_chart())
        table (list): dash.DataTable in a layout (create_comparison_table())
        category_string (str): a string
        school_string (str): a string

    Returns:
        list: list layout html.Div object
    """

    layout = [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(fig, style={"marginBottom": "-20px"})
                    ],
                    className = "pretty-container--close twelve columns",
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
                            html.Span("Categories with no data to display:", className = "category-string__label"),
                            html.Span(category_string, className = "category-string"),
                            ],
                            style={"marginTop": -10, "marginBottom": -10}
                        ),
                        html.P(
                            children=[
                            html.Span("School Categories with insufficient n-size or no data:",className = "school-string__label"),
                            html.Span(school_string, className = "school-string"),
                            ],
                            
                        ),
                    ],
                    className = "container__close twelve columns"
                )
                ],
                className="row"
            )
    ]
    return layout

def create_barchart_layout(fig: list, table: list) -> list:
    """
    Combine a px.bar fig and a dash datatable

    Args:
        fig (list): a px.bar
        table (list): a dash DataTable

    Returns:
        layout (list): a dash html.Div layout with fig and DataTable
    """    
    layout = [
                html.Div(
                [
                    html.Div(
                        [
                            html.Div(fig)           
                        ],
                        className = 'pretty-container nine columns',
                    ),
                    html.Div(
                        [
                            html.Div(table)           
                        ],
                        className = 'pretty-container three columns'
                    ),
                ],
                className='row'
            )
    ]

    return layout

def create_line_fig_layout(table: list, fig: list, label: str) -> list:
    """
    Creates a layout combining a px.line fig and dash datatable

    Args:
        fig (list): a px.line
        table (list): a dash DataTable

    Returns:
        layout (list): a dash html.Div layout with fig
    """   
    layout =  [                          

        html.Div(
            [    
        html.Label(label, className="label__header"),
        html.Div(
            [                                       
                html.Div(
                    [
                        html.Div(table, style={"marginTop": "20px"}),
                        html.P(""),
                        html.P("Hover over each data point to see N-Size.",
                        style={
                            "color": "#6783a9",
                            "fontSize": 10,
                            "textAlign": "left",
                            "marginLeft": "10px",
                            "marginRight": "10px",
                            "marginTop": "20px",
                            "paddingTop": "5px",
                            "borderTop": ".5px solid #c9d3e0",
                            },
                        ), 
                    ],
                    className="pretty-container six columns",
                ),
                html.Div(
                    [
                        html.Div(fig),
                    ],
                    className="pretty-container six columns",
                ),
            ],
            className="bare-container--flex--center twelve columns",
        ),
            ],
            className="bare-container--relative twelve columns",
        ),                               
    ]

    return layout