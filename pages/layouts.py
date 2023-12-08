#####################################
# ICSB Dashboard - Layout Functions #
#####################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.13
# date:     10/13/23

import pandas as pd
import numpy as np
from dash import html
import dash_bootstrap_components as dbc
from .string_helpers import (
    create_chart_label,
    combine_school_name_and_grade_levels,
    identify_missing_categories,
    create_school_label,
)
from .charts import make_group_bar_chart, make_multi_line_chart
from .tables import create_comparison_table, no_data_page
# from typing import Tuple

def create_hs_analysis_layout(
    data_type: str, data: pd.DataFrame, categories: list, school_id: str
) -> list:
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
        final_analysis_group = []  # type:list

        return final_analysis_group

    analysis_cols = [
        col
        for col in data.columns
        if search_string in col
        and any(substring for substring in categories if substring in col)
    ]

    added_cols = ["School Name", "Low Grade", "High Grade", "School ID"]

    analysis_cols = added_cols + analysis_cols

    analysis_data = data[analysis_cols]

    analysis_data = analysis_data.filter(
        regex="|".join(
            [data_type, "School Name", "School ID", "Low Grade", "High Grade"]
        )
    )

    # data will always have at least three cols (School Name, School ID, Low Grade, High Grade)
    if len(analysis_data.columns) > 4:
        # NOTE: For transparency purposes, we want to identify all categories that are missing from
        # the possible dataset, including those that aren't going to be displayed (because the school
        # is missing them). Because there are many cases where there wont be any data at all (eg, data
        # hasn't yet been released, or there is no data for a particular category). So we need to check whether
        # there is any data to display before and after we collect the missing category information. After
        # we collect any missing information, we need to drop any columns where the school has no data and
        # then check again to see if the dataframe has any info.

        analysis_data, category_string, school_string = identify_missing_categories(
            analysis_data, tested_categories
        )

        # Once the missing category and missing school strings are built, we drop any columns
        # where the school has no data by finding the index of the row containing the school
        # name and dropping all columns where the row at school_name_idx has a NaN value

        if len(analysis_data.columns) > 1:
            analysis_label = create_chart_label(analysis_data)
            analysis_trace_colors, analysis_chart = make_group_bar_chart(
                analysis_data, school_id, analysis_label
            )
            analysis_table_data = combine_school_name_and_grade_levels(analysis_data)

            analysis_table = create_comparison_table(
                analysis_table_data, analysis_trace_colors, school_id
            )  # , "")
            final_analysis_group = create_group_barchart_layout(
                analysis_chart, analysis_table, category_string, school_string
            )

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
                className="bare-container--flex--center twelve columns",
            )
        ]

    else:
        if len(cols) >= 4:
            table_layout = [
                html.Div(
                    table1,
                    className="bare-container--flex--center twelve columns",
                ),
                html.Div(
                    table2,
                    className="bare-container--flex--center twelve columns",
                ),
            ]

        else:
            table_layout = [
                html.Div(
                    [
                        table1[0],
                        table2[0],
                    ],
                    className="bare-container--flex--center twelve columns",
                ),
            ]

    return table_layout


def create_group_barchart_layout(
    fig: list, table: list, category_string: str, school_string: str
) -> list:
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

    # the difference between this layout and the barchart layout below
    # is the addition of the information strings
    # TODO: Combine the two and just add a check for the strings

    # year_over_year charts do not have category or school strings
    if category_string == "" and school_string == "":
        layout = [
            html.Div(
                [
                    html.Div(
                        [html.Div(fig, style={"marginBottom": "-20px"})],
                        className="pretty-container--close eleven columns",
                    ),
                ],
                className="row",
            ),
            html.Div(
                [
                    html.Div(
                        [html.Div(table)],
                        className="container__close eleven columns",
                    ),
                ],
                className="row",
            ),
        ]
    else:
        layout = [
            html.Div(
                [
                    html.Div(
                        [html.Div(fig, style={"marginBottom": "-20px"})],
                        className="pretty-container--close twelve columns",
                    ),
                ],
                className="row",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(table),
                            html.P(
                                children=[
                                    html.Span(
                                        "Selected school has insufficient n-size or no data for:",
                                        className="category-string__label",
                                    ),
                                    html.Span(
                                        category_string, className="category-string"
                                    ),
                                ],
                                style={"marginTop": -10, "marginBottom": -10},
                            ),
                            html.P(
                                children=[
                                    html.Span(
                                        "Schools with insufficient n-size or no data:",
                                        className="school-string__label",
                                    ),
                                    html.Span(school_string, className="school-string"),
                                ],
                            ),
                        ],
                        className="container__close twelve columns",
                    )
                ],
                className="row",
            ),
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

    # a two row layout (like group_barchart layout), uncomment
    # this to use the side-by-side-layout
    # layout = [
    #     html.Div(
    #         [
    #             html.Div(
    #                 [html.Div(fig)],
    #                 className="pretty-container nine columns",
    #             ),
    #             html.Div(
    #                 [html.Div(table)],
    #                 className="pretty-container three columns",
    #             ),
    #         ],
    #         className="row bar-chart-print",
    #     )
    # ]

    layout = [
        html.Div(
            [
                html.Div(
                    [html.Div(fig, style={"marginBottom": "-20px"})],
                    className="pretty-container--close eleven columns",
                ),
            ],
            className="row bar-chart-print",
        ),
        html.Div(
            [
                html.Div(
                    [html.Div(table)],
                    className="container__close eleven columns",
                ),
            ],
            className="row bar-chart-print",
        ),
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
    layout = [
        html.Div(
            [
                html.Label(label, className="label__header"),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(table, style={"marginTop": "20px"}),
                                html.P(""),
                                html.P(
                                    "Hover over each data point to see N-Size.",
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


def create_radio_layout(page: str, group_catagory: str = "", width: str = "twelve"):
    group = page + "-" + group_catagory + "-radio"
    container = group + "-container"

    # NOTE: THis is dumb, need to find a better way to distinguish
    if width == "twelve":
        layout = "bare-container--flex--center " + width + " columns"
    else:
        layout = "bare-container--flex--center_subnav_float"

    radio_button_group = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    dbc.RadioItems(
                                        id=group,
                                        className="btn-group",
                                        inputClassName="btn-check",
                                        labelClassName="btn btn-outline-primary",
                                        labelCheckedClassName="active",
                                        value=[],
                                        persistence=False,
                                    ),
                                ],
                                className="radio-group-academic",
                            )
                        ],
                        className=layout,
                    ),
                ],
                className="row",
            ),
        ],
        id=container,
    )

    return radio_button_group


def create_year_over_year_layout(school_id, data, school_id_list, label, msg):
    # drop columns where all values are nan
    data = data.dropna(axis=1, how="all")

    if not msg:
        msg = "No Data for Selected School."

    # if school was dropped because it has no data return empty table

    if data["School ID"][0] != np.int64(school_id):
        layout = no_data_page(label, msg)
    else:
        data = data.drop("School ID", axis=1)

        # drop rows (years) where the school has no data (2nd column will always be selected school)
        # NOTE: tried to use name, but there are too many differences in DOE data
        data = data[data.iloc[:, 1].notna()]

        table_data = data.copy()

        # transpose and merge table data and school_id_list
        # the data is pivoted so we need to unpivot it before we add School ID back
        # school id is used to identify the school in the comparison_table function
        table_data = (
            table_data.set_index("Year")
            .T.rename_axis("School Name")
            .rename_axis(None, axis=1)
            .reset_index()
        )
        table_data = pd.merge(
            table_data, school_id_list, on=["School Name"], how="left"
        )

        fig_trace_colors, fig = make_multi_line_chart(data, label)

        # Use Low/High grade columns to modify School Name and then drop.
        table_data["School Name"] = create_school_label(table_data)
        table_data = table_data.drop(["Low Grade", "High Grade"], axis=1)

        table = create_comparison_table(table_data, fig_trace_colors, school_id)  # , "")
        category_string = ""
        school_string = ""
        layout = create_group_barchart_layout(
            fig, table, category_string, school_string
        )

    return layout
