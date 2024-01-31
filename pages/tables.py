########################################
# ICSB Dashboard - DataTable Functions #
########################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.13
# date:     01/01/24

import pandas as pd
from typing import Tuple
import re
import numpy as np
from dash import dash_table, html
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign
import dash_mantine_components as dmc

from .load_data import metric_strings

# default table styles
table_style = {"fontSize": "12px", "border": "none", "fontFamily": "Inter, sans-serif"}

table_cell = {
    "whiteSpace": "normal",
    "height": "auto",
    "textAlign": "center",
    "color": "#6783a9",
    "minWidth": "25px",
    "width": "25px",
    "maxWidth": "25px",
}

table_header = {
    "backgroundColor": "#ffffff",
    "fontSize": "12px",
    "fontFamily": "Montserrat, sans-serif",
    "color": "#6783a9",
    "textAlign": "center",
    "fontWeight": "bold",
    "border": "none",
}


def create_proficiency_key() -> list:
    """
    Creates a dash datatable "key" using proficiency ratings and
    the Font Awesome circle icon

    Args:
        None

    Returns:
        key_table (list): a list that will be displayed as a dash_table.DataTable
    """
    rating_icon = "<span style='font-size: 1em;'><i class='fa fa-circle'></i></span>"

    proficiency_key = pd.DataFrame(
        dict(
            [
                (
                    "Rate",
                    [
                        "Exceeds Standard",
                    ],
                ),
                ("icon", [rating_icon]),
                (
                    "Rate2",
                    [
                        "Meets Standard",
                    ],
                ),
                ("icon2", [rating_icon]),
                (
                    "Rate3",
                    [
                        "Approaches Standard",
                    ],
                ),
                ("icon3", [rating_icon]),
                (
                    "Rate4",
                    [
                        "Does Not Meet Standard",
                    ],
                ),
                ("icon4", [rating_icon]),
                (
                    "Rate5",
                    [
                        "No Rating",
                    ],
                ),
                ("icon5", [rating_icon]),
            ]
        )
    )

    rating_headers = proficiency_key.columns.tolist()
    rating_cols = list(col for col in proficiency_key.columns if "Rate" in col)
    icon_cols = list(col for col in proficiency_key.columns if "icon" in col)

    key_table = [
        dash_table.DataTable(
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
                "paddingTop": "15px",
                "fontSize": "1.2em",
                "border": "none",
                "fontFamily": "Inter, sans-serif",
            },
            style_cell={
                "whiteSpace": "normal",
                "height": "auto",
                "border": "none",
                "textAlign": "right",
                "color": "#6783a9",
            },
            style_cell_conditional=[
                {
                    "if": {"column_id": rating},
                    "textAlign": "right",
                }
                for rating in rating_cols
            ]
            + [
                {
                    "if": {"column_id": icon},
                    "textAlign": "left",
                    "width": "2%",
                }
                for icon in icon_cols
            ],
            style_data_conditional=[
                {
                    "if": {
                        "filter_query": "{Rate} = 'Exceeds Standard'",
                        "column_id": "icon",
                    },
                    "color": "#0D9FE1",
                },
                {
                    "if": {
                        "filter_query": "{Rate2} = 'Meets Standard'",
                        "column_id": "icon2",
                    },
                    "color": "#87bc45",
                },
                {
                    "if": {
                        "filter_query": "{Rate3} = 'Approaches Standard'",
                        "column_id": "icon3",
                    },
                    "color": "#F5A30F",
                },
                {
                    "if": {
                        "filter_query": "{Rate4} = 'Does Not Meet Standard'",
                        "column_id": "icon4",
                    },
                    "color": "#ea5545",
                },
                {
                    "if": {
                        "filter_query": "{Rate5} = 'No Rating'",
                        "column_id": "icon5",
                    },
                    "color": "#a4a2a8",
                },
                {
                    "if": {
                        "column_id": rating_headers[1],
                    },
                    "marginLeft": "10px",
                },
            ],
        )
    ]

    return key_table


def empty_table(text: str) -> dash_table.DataTable:
    """
    empty dash_table.Datatable with given text as only data.

    Args:
        text (list): table content

    Returns:
        dash datatable (dash_table.DataTable): a dash DataTable
    """

    # default table text
    if text == "":
        text = "No Data to Display."

    empty_table = dash_table.DataTable(
        columns=[
            {"id": "emptytable", "name": text},
        ],
        style_header={
            "fontSize": "14px",
            "border": "none",
            "textAlign": "center",
            "color": "#6783a9",
            "backgroundColor": "#ffffff",
            "fontFamily": "Inter, sans-serif",
            "height": "30vh",
        },
    )

    return empty_table


def no_data_table(
    text: str, label: str = "No Data to Display", width: str = "four"
) -> list:
    """
    Uses empty_table function and returns empty table with given label and content.

    Args:
        label (list): table label
        text (list): table content
        width (str): text number of columns (one - twelve) or "none" - if none,
                    no container is used

    Returns:
        table_layout (list): a dash html.Label object and html.Div object enclosing a dash DataTable
    """

    if width == "none":
        table_layout = [
            html.Label(label, className="label__header"),
            html.Div(empty_table(text), className="empty-table"),
        ]
    else:
        table_layout = [
            html.Div(
                [
                    html.Label(label, className="label__header"),
                    html.Div(empty_table(text), className="empty-table"),
                ],
                className="pretty-container " + width + " columns",
            ),
        ]
    return table_layout


def no_data_page(text: str, label: str = "No Data to Display") -> list:
    """
    Uses empty_table function and returns empty table with given label and content. This
    table has a fixed column size (eight cols) and is meant to use when there is no data
    at all to be displayed on a page.

    Args:
        label (str): string label
        text (list)

    Returns:
        table_layout (list): dash html.Div objects enclosing a dash html.Label
        object and a dash DataTable, with css classes
    """

    table_layout = [
        html.Div(
            [
                html.Div(
                    [
                        html.Label(label, className="label__header"),
                        html.Div(empty_table(text), className="empty-table"),
                    ],
                    className="pretty-container eight columns",
                ),
            ],
            className="bare-container--flex--center twelve columns",
        ),
    ]

    return table_layout


# def hidden_table() -> list:
#     """
#     Creates an empty table with no cells. Will be automatically hidden
#     ("display": "none") by css selector chaining for pretty-container.
#     Don't remember why I needed this.
#     See stylesheet.css

#     Args:
#         None

#     Returns:
#         table_layout (list): a dash html.Div object enclosing a dash DataTable
#     """
#     table_layout = [
#                 html.Div(
#                     dash_table.DataTable(
#                         columns = [
#                             {"id": "hidden-table", "name": "hidden-table"},
#                         ],
#                     ),
#                 ),
#             ]

#     return table_layout


def create_growth_table(all_data: pd.DataFrame, label: str = "") -> list:
    """
    Takes a label, a dataframe, and a descriptive (type) string and creates a multi-header
    table with academic growth and sgp data using Majority Enrolled Students (162-Day Student
    data in in tooltips).

    Args:
        label (str): Table title
        content (pd.DataTable): dash dataTable
        kind (str): "sgp|growth"
    Returns:
        table_layout (list): dash html.Div enclosing html.Label and DataTable
    """
    data = all_data.copy()

    data["Category"] = data["Category"].str.split("|").str[0]

    data_me = data.loc[
        :, data.columns.str.contains("Category|Majority Enrolled")
    ].copy()

    data_me = data_me.rename(
        columns={c: c[:4] for c in data_me.columns if c not in ["Category"]}
    )

    # 162 day data is used for tooltip
    data_162 = data.loc[:, data.columns.str.contains("Category|162 Days")].copy()
    data_162 = data_162.rename(
        columns={c: c[:4] for c in data_162.columns if c not in ["Category"]}
    )
    data_162 = data_162.drop("Category", axis=1)

    # Reverse year order (ignoring Category) to align with charts (ascending order)
    data_me = data_me.iloc[:, ::-1]

    # replace NaN with em dash (—)
    data_me = data_me.fillna(value="\u2014")

    data_me.insert(0, "Category", data_me.pop("Category"))

    table_size = len(data_me.columns)

    if len(data_me.index) == 0 or table_size == 1:
        table_layout = [
            html.Div(
                [
                    html.Div(no_data_table("", label)),
                ],
                className="pretty-container ten columns",
            )
        ]

    else:
        if table_size <= 3:
            category_width = 70
        if table_size > 3 and table_size <= 4:
            category_width = 35
        elif table_size >= 5 and table_size <= 8:
            category_width = 30
        elif table_size > 9:
            category_width = 30

        remaining_width = 100 - category_width
        data_col_width = remaining_width / (table_size - 1)

        all_cols = data_me.columns.tolist()
        data_cols = [col for col in all_cols if "Category" not in col]

        table_cell_conditional = [
            {
                "if": {"column_id": "Category"},
                "textAlign": "left",
                "paddingLeft": "20px",
                "fontWeight": "500",
                "width": str(category_width) + "%",
            },
        ] + [
            {
                "if": {"column_id": col},
                "textAlign": "center",
                "fontWeight": "500",
                "width": str(data_col_width) + "%",
            }
            for col in data_cols
        ]

        table_header_conditional = [
            {
                "if": {
                    "column_id": col,
                },
                "borderBottom": ".5px solid #b2bdd4",
            }
            for col in data_cols
        ]

        table_data_conditional = [
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(112,128,144, .3)",
                "border": "thin solid silver",
            },
            {"if": {"row_index": "odd"}, "backgroundColor": "#eeeeee"},
        ] + [
            {"if": {"row_index": 0}, "paddingTop": "5px"},
        ]

        column_format = [
            {
                "name": col,
                "id": col,
                "type": "numeric",
                "format": Format(
                    scheme=Scheme.percentage, precision=2, sign=Sign.parantheses
                ),
            }
            for col in all_cols
        ]

        tooltip_format = [
            {
                column: {
                    "value": "162 Days: {:.2%}".format(float(value))
                    if value == value
                    else "\u2014",
                    "type": "markdown",
                }
                for column, value in row.items()
            }
            for row in data_162.to_dict("records")
        ]

        table = dash_table.DataTable(
            data_me.to_dict("records"),
            columns=column_format,
            style_table={"height": "300px"},
            style_data=table_style,
            style_data_conditional=table_data_conditional,
            style_header=table_header,
            style_header_conditional=table_header_conditional,
            style_cell=table_cell,
            style_cell_conditional=table_cell_conditional,
            tooltip_data=tooltip_format,
            css=[{"selector": ".dash-table-tooltip", "rule": "font-size: 12px"}],
        )

        table_layout = [html.Div([html.Div(table)])]

    return table_layout


def create_key_table(data: pd.DataFrame, label: str = "", width: int = 0) -> list:
    """
    Takes a dataframe, a string, and a width (optional) and creates a simple
    header table with a border around the edge.

    Args:
        label (String): Table title
        data (pd.DataTable): dash dataTable
        table_type (String): type of table.

    Returns:
        table_layout (list): dash DataTable wrapped in dash html components
    """

    table_size = len(data.columns)

    # determines the col_width class and width of the category column based
    # on the size (# of cols) of the dataframe - in the case of the basic
    # table, "Category" is simply whatever is in the first column (it may
    # or may not have the name "Category")
    if table_size <= 3:
        col_width = "six"
        category_width = 35
    if table_size > 3 and table_size <= 5:
        col_width = "seven"
        category_width = 25
    elif table_size > 5 and table_size <= 7:
        col_width = "eight"
        category_width = 20
    elif table_size > 7 and table_size <= 9:
        col_width = "nine"
        category_width = 20
    elif table_size >= 10 and table_size <= 13:
        col_width = "ten"
        category_width = 15
    elif table_size > 13:
        col_width = "ten"
        category_width = 15

    if width:
        category_width = width

    class_name = "pretty-container__key " + col_width + " columns"

    first_column = data.columns[0]
    other_columns = data.columns[1:]

    first_column_width = category_width + 10
    remaining_width = 100 - category_width
    other_column_width = remaining_width / table_size

    table_cell_conditional = [
        {
            "if": {"column_id": other},
            "width": str(other_column_width) + "%",
        }
        for other in other_columns
    ] + [
        {
            "if": {"column_id": first_column},
            "textAlign": "left",
            "paddingLeft": "20px",
            "fontWeight": "600",
            "width": str(first_column_width) + "%",
        }
    ]

    table_data_conditional = (
        [
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(112,128,144, .3)",
                "border": "thin solid silver",
            },
        ]
        + [{"if": {"row_index": 0}, "paddingTop": "5px"}]
        + [
            {
                "if": {
                    "column_id": first_column,
                },
                "borderRight": "none",
                "borderBottom": "none",
                "borderLeft": "none",
                "borderTop": "none",
            },
        ]
        + [
            {
                "if": {
                    "column_id": other,
                },
                "fontSize": "10px",
                "textAlign": "center",
                "fontWeight": "500",
                "borderLeft": ".5px solid #b2bdd4",
            }
            for other in other_columns
        ]
    )

    table_layout = [
        html.Div(
            [
                html.Div(
                    [
                        html.Label(label, className="key-label__header"),
                        html.Div(
                            dash_table.DataTable(
                                data.to_dict("records"),
                                columns=[
                                    {
                                        "name": i,
                                        "id": i,
                                        "type": "numeric",
                                        "format": FormatTemplate.percentage(2),
                                    }
                                    for i in data.columns
                                ],
                                style_data={
                                    "fontSize": "12px",
                                    "fontFamily": "Inter, sans-serif",
                                    "border": "none",
                                    "color": "#6783a9",
                                },
                                style_header={
                                    "fontSize": "12px",
                                    "fontFamily": "Montserrat, sans-serif",
                                    "color": "#6783a9",
                                    "textAlign": "center",
                                    "fontWeight": "bold",
                                    "border": "none",
                                    "backgroundColor": "#ffffff",
                                },
                                style_cell={
                                    "whiteSpace": "normal",
                                    "height": "auto",
                                    "textAlign": "center",
                                    "minWidth": "25px",
                                    "width": "25px",
                                    "maxWidth": "25px",
                                },
                                style_data_conditional=table_data_conditional,
                                style_cell_conditional=table_cell_conditional,
                                merge_duplicate_headers=True,
                            ),
                        ),
                    ],
                    className=class_name,
                )
            ],
            className="bare-container--flex--center twelve columns",
        )
    ]

    return table_layout


def create_single_header_table(data: pd.DataFrame, label: str) -> list:
    """
    Takes a dataframe of two or more columns and a label and creates a single
    header table with borders around each cell. If more rows are added, need
    to adjust logic to remove horizontal borders between rows.

    Note: If "IREAD" or "WIDA" is passed as a label, a special layout is produced.

    Args:
        label (String): Table title
        data (pd.DataTable): dash dataTable
        table_type (String): type of table.

    Returns:
        table_layout (list): dash DataTable wrapped in dash html components
    """

    table_size = len(data.columns)

    # determines the col_width class and width of the category column based
    # on the size (# of cols) of the dataframe - in the case of the basic
    # table, "Category" is simply whatever is in the first column (it may
    # or may not have the name "Category")
    if table_size <= 3:
        col_width = "six"
        category_width = 35
    if table_size > 3 and table_size <= 5:
        col_width = "seven"
        category_width = 25
    elif table_size > 5 and table_size <= 7:
        col_width = "eight"
        category_width = 20
    elif table_size > 7 and table_size <= 9:
        col_width = "nine"
        category_width = 20
    elif table_size >= 10 and table_size <= 13:
        col_width = "ten"
        category_width = 15
    elif table_size > 13:
        col_width = "ten"
        category_width = 15

    class_name = "pretty-container " + col_width + " columns"

    data.columns = data.columns.astype(str)

    first_column = data.columns[0]
    other_columns = data.columns[1:]

    first_column_width = category_width + 10
    remaining_width = 100 - category_width
    other_column_width = remaining_width / table_size

    table_cell_conditional = [
        {
            "if": {"column_id": first_column},
            "textAlign": "left",
            "paddingLeft": "20px",
            "fontWeight": "500",
            "width": str(first_column_width) + "%",
        }
    ] + [
        {
            "if": {"column_id": other},
            "textAlign": "center",
            "fontWeight": "500",
            "width": str(other_column_width) + "%",
            "borderRight": ".5px solid #b2bdd4",
            "borderLeft": ".5px solid #b2bdd4",
        }
        for other in other_columns
    ]

    table_header_conditional = [
        {
            "if": {
                "column_id": other,
            },
            "borderBottom": ".5px solid #b2bdd4",
        }
        for other in other_columns
    ]

    table_data_conditional = (
        [
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(112,128,144, .3)",
                "border": "thin solid silver",
            },
            {"if": {"row_index": "odd"}, "backgroundColor": "#eeeeee"},
        ]
        + [{"if": {"row_index": 0}, "paddingTop": "5px"}]
        + [
            {
                "if": {
                    "column_id": data.columns[-1],
                },
                "borderRight": ".5px solid #b2bdd4",
            },
        ]
        + [{"if": {"row_index": 0}, "paddingTop": "5px"}]
        + [
            {
                "if": {"row_index": len(data) - 1},
                "borderBottom": ".5px solid #b2bdd4",
            }
        ]
        + [
            {
                "if": {
                    "column_id": first_column,
                },
                "borderRight": ".5px solid #b2bdd4",
                "borderBottom": "none",
                "borderLeft": "none",
                "borderTop": "none",
            },
        ]
        + [
            {
                "if": {
                    "column_id": other,
                },
                "fontSize": "10px",
                "textAlign": "center",
                "borderLeft": ".5px solid #b2bdd4",
            }
            for other in other_columns
        ]
    )

    # Special layout for IREAD table on Academic Information page
    if label == "IREAD" or label == "WIDA":

        table_layout = [
            dash_table.DataTable(
                data.to_dict("records"),
                columns=[
                    {
                        "name": i,
                        "id": i,
                    }
                    for i in data.columns
                ],
                style_data={
                    "fontSize": "12px",
                    "fontFamily": "Inter, sans-serif",
                    "border": "none",
                },
                style_data_conditional=table_data_conditional,
                style_header=table_header,
                style_cell={
                    "whiteSpace": "normal",
                    "height": "auto",
                    "textAlign": "center",
                    "color": "#6783a9",
                    "minWidth": "25px",
                    "width": "25px",
                    "maxWidth": "25px",
                },
                style_header_conditional=table_header_conditional,
                style_cell_conditional=table_cell_conditional,
            ),
        ]

    else:
        table_layout = [
            html.Div(
                [
                    html.Div(
                        [
                            html.Label(label, className="label__header"),
                            html.Div(
                                dash_table.DataTable(
                                    data.to_dict("records"),
                                    columns=[
                                        {
                                            "name": i,
                                            "id": i,
                                            "type": "numeric",
                                            "format": FormatTemplate.percentage(2),
                                        }
                                        for i in data.columns
                                    ],
                                    style_data={
                                        "fontSize": "12px",
                                        "fontFamily": "Inter, sans-serif",
                                        "border": "none",
                                    },
                                    style_header=table_header,
                                    style_cell={
                                        "whiteSpace": "normal",
                                        "height": "auto",
                                        "textAlign": "center",
                                        "color": "#6783a9",
                                        "minWidth": "25px",
                                        "width": "25px",
                                        "maxWidth": "25px",
                                    },
                                    style_data_conditional=table_data_conditional,
                                    style_header_conditional=table_header_conditional,
                                    style_cell_conditional=table_cell_conditional,
                                    merge_duplicate_headers=True,
                                ),
                            ),
                        ],
                        className=class_name,
                    )
                ],
                className="bare-container--flex--center twelve columns",
            )
        ]

    return table_layout


def create_multi_header_table_with_container(data: pd.DataFrame, label: str) -> list:
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
        if table_size <= 3:
            col_width = "four"
            category_width = 60
        if table_size > 3 and table_size < 5:
            col_width = "five"
            category_width = 30
        elif table_size >= 5 and table_size <= 7:
            col_width = "six"
            category_width = 30
        elif table_size > 7 and table_size <= 9:
            col_width = "seven"
            category_width = 20
        elif table_size >= 10 and table_size <= 13:
            col_width = "eight"
            category_width = 15
        elif table_size > 13 and table_size <= 17:
            col_width = "nine"
            category_width = 15
        elif table_size > 17:
            col_width = "ten"
            category_width = 15

        class_name = "pretty-container " + col_width + " columns"

        # rename all n_size columns before getting n col list
        data.columns = data.columns.str.replace("N-Size|SN-Size", "(N)", regex=True)

        if "SAT" in label:
            data.columns = data.columns.str.replace(
                "School", "At Benchmark", regex=True
            )
            school_headers = [y for y in data.columns if "At Benchmark" in y]
        elif "Graduation Rate":
            data.columns = data.columns.str.replace("School", "Rate", regex=True)
            school_headers = [y for y in data.columns if "Rate" in y]
        else:
            data.columns = data.columns.str.replace("School", "Proficiency", regex=True)
            school_headers = [y for y in data.columns if "Proficiency" in y]

        nsize_headers = [y for y in data.columns if "(N)" in y]

        all_cols = data.columns.tolist()

        if table_size <= 3:
            data_width = 100 - category_width
            nsize_width = school_width = data_width / (table_size - 1)

        else:
            nsize_width = 3
            data_width = 100 - category_width - nsize_width
            school_width = data_width / (table_size - 1)

        table_cell_conditional = (
            [
                {
                    "if": {"column_id": "Category"},
                    "textAlign": "left",
                    "paddingLeft": "20px",
                    "fontWeight": "500",
                    "fontSize": "11px",
                    "width": str(category_width) + "%",
                },
            ]
            + [
                {
                    "if": {"column_id": school},
                    "textAlign": "center",
                    "fontWeight": "500",
                    "fontSize": "11px",
                    "width": str(school_width) + "%",
                }
                for school in school_headers
            ]
            + [
                {
                    "if": {"column_id": nsize},
                    "textAlign": "center",
                    "fontWeight": "500",
                    "fontSize": "11px",
                    "width": str(nsize_width) + "%",
                }
                for nsize in nsize_headers
            ]
        )

        table_header_conditional = (
            [
                {
                    "if": {
                        "column_id": school,
                        "header_index": 1,
                    },
                    "fontWeight": "500",
                    "fontSize": "10px",
                    "borderLeft": ".5px solid #b2bdd4",
                    "borderTop": ".5px solid #b2bdd4",
                    "borderBottom": ".5px solid #b2bdd4",
                }
                for school in school_headers
            ]
            + [
                {
                    "if": {
                        "column_id": nsize,
                        "header_index": 1,
                    },
                    "textAlign": "center",
                    "fontWeight": "500",
                    "fontSize": "10px",
                    "borderRight": ".5px solid #b2bdd4",
                    "borderTop": ".5px solid #b2bdd4",
                    "borderBottom": ".5px solid #b2bdd4",
                }
                for nsize in nsize_headers
            ]
            + [
                {
                    "if": {
                        "column_id": all_cols[-1],
                        "header_index": 1,
                    },
                    "borderRight": ".5px solid #b2bdd4",
                }
            ]
        )

        table_data_conditional = (
            [
                {
                    "if": {"state": "selected"},
                    "backgroundColor": "rgba(112,128,144, .3)",
                    "border": "thin solid silver",
                },
                {"if": {"row_index": "odd"}, "backgroundColor": "#eeeeee"},
            ]
            + [
                {
                    "if": {
                        "column_id": all_cols[-1],
                    },
                    "borderRight": ".5px solid #b2bdd4",
                },
            ]
            + [{"if": {"row_index": 0}, "paddingTop": "5px"}]
            + [
                {
                    "if": {"row_index": len(data) - 1},
                    "borderBottom": ".5px solid #b2bdd4",
                }
            ]
            + [
                {
                    "if": {
                        "column_id": "Category",
                    },
                    "borderRight": ".5px solid #b2bdd4",
                    "borderBottom": "none",
                },
            ]
            + [
                {
                    "if": {
                        "column_id": nsize,
                    },
                    "fontSize": "11px",
                    "textAlign": "center",
                    "borderRight": ".5px solid #b2bdd4",
                }
                for nsize in nsize_headers
            ]
        )

        # build multi-level headers
        name_cols = [["Category", ""]]

        # Split columns into two levels
        for item in all_cols:
            if item.startswith("20"):
                name_cols.append([item[:4], item[4:]])

        table_columns = [
            {
                "name": col,
                "id": all_cols[idx],
                "type": "numeric",
                "format": Format(
                    scheme=Scheme.percentage, precision=2, sign=Sign.parantheses
                ),
            }
            if "Proficiency" in col or "At Benchmark" in col or "Rate" in col
            else {
                "name": col,
                "id": all_cols[idx],
                "type": "numeric",
                "format": Format(),
            }
            for (idx, col) in enumerate(name_cols)
        ]

        table_layout = [
            html.Div(
                [
                    html.Label(label, className="hollow-label__header"),
                    html.Div(
                        dash_table.DataTable(
                            data.to_dict("records"),
                            columns=table_columns,
                            style_data=table_style,
                            style_data_conditional=table_data_conditional,
                            style_header=table_header,
                            style_cell=table_cell,
                            style_header_conditional=table_header_conditional,
                            style_cell_conditional=table_cell_conditional,
                            merge_duplicate_headers=True,
                        ),
                    ),
                ],
                className=class_name,
            )
        ]

    else:
        table_layout = no_data_table("", label)

    return table_layout


def create_multi_header_table(data: pd.DataFrame) -> list:
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
        # pull out nsize data for tooltips and drop from main df
        nsize_data = data.loc[:, data.columns.str.contains("N-Size")].copy()
        nsize_data = nsize_data.rename(columns={c: c[:4] for c in nsize_data.columns})

        for col in nsize_data.columns:
            nsize_data[col] = pd.to_numeric(nsize_data[col], errors="coerce")

        data = data[data.columns[~data.columns.str.contains(r"N-Size")]]

        data.columns = data.columns.str.replace("School", "", regex=True)
        data = data.replace("No Data", "\u2014", regex=True)
        school_headers = [y for y in data.columns if "Category" not in y]

        all_cols = data.columns.tolist()

        # nsize_width = 2
        category_width = 20
        data_width = 100 - category_width
        school_width = data_width / (table_size - 1)

        # formatting logic is slightly different for a multi-header table
        table_cell_conditional = [
            {
                "if": {"column_id": "Category"},
                "textAlign": "left",
                "paddingLeft": "20px",
                "fontWeight": "500",
                "width": str(category_width) + "%",
            },
        ] + [
            {
                "if": {"column_id": school},
                "textAlign": "center",
                "fontWeight": "500",
                "width": str(school_width) + "%",
            }
            for school in school_headers
        ]

        table_header_conditional = [
            {
                "if": {
                    "column_id": col,
                },
                "borderBottom": ".5px solid #b2bdd4",
            }
            for col in school_headers
        ]

        table_data_conditional = [
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(112,128,144, .3)",
                "border": "thin solid silver",
            },
            {"if": {"row_index": "odd"}, "backgroundColor": "#eeeeee"},
        ] + [{"if": {"row_index": 0}, "paddingTop": "5px"}]

        table_columns = [
            {
                "name": col,
                "id": col,
                "type": "numeric",
                "format": Format(
                    scheme=Scheme.percentage, precision=2, sign=Sign.parantheses
                ),
            }
            for col in all_cols
        ]

        tooltip_format = [
            {
                column: {
                    "value": "N-Size: {:.1f}".format(float(value))
                    if value == value
                    else "\u2014",
                    "type": "markdown",
                }
                for column, value in row.items()
            }
            for row in nsize_data.to_dict("records")
        ]

        table_layout = [
            dash_table.DataTable(
                data.to_dict("records"),
                style_table={"height": "300px"},
                columns=table_columns,
                style_data=table_style,
                style_data_conditional=table_data_conditional,
                style_header=table_header,
                style_cell=table_cell,
                style_header_conditional=table_header_conditional,
                style_cell_conditional=table_cell_conditional,
                merge_duplicate_headers=True,
                tooltip_data=tooltip_format,
                css=[{"selector": ".dash-table-tooltip", "rule": "font-size: 12px"}],
            ),
        ]

    else:
        table_layout = [
            html.Div(
                [
                    html.Div(empty_table("No Data to Display.")),
                ],
                className="pretty-container four columns",
            )
        ]

    return table_layout


def create_metric_table(label: list, data: pd.DataFrame) -> list:
    """
    Takes a label and a dataframe consisting of Rating and Metric Columns and returns
    a dash datatable. NOTE: could possibly be less complicated than it is, or maybe not-
    gonna leave it up to future me. Also, beware of some tricksy bits.

    Args:
        label (String): Table title
        content (pd.DataTable): dash dataTable

    Returns:
        table (list): dash html.Div enclosing html.Label and DataTable
    """

    table_size = len(data.columns)

    # this is annoying, but some labels are passed as lists so they can include html
    # elements (html.U() & html.Br()) - so we need to remove these elements and convert
    # to a string for empty tables.
    if len(label) == 1:
        string_label = label[0]
    else:
        clean_label = " ".join(str(l) for l in label)
        string_label = (
            clean_label.replace("Br(None) ", "").replace("U('", "").replace("') ", "")
        )

    if len(data.index) == 0 or table_size == 1:
        table = no_data_table("No Data to Display.", string_label, "ten")

    else:
        if table_size <= 3:
            col_width = "four"
            category_width = 40
        if table_size > 3 and table_size < 5:
            col_width = "six"
            category_width = 35
        elif table_size >= 5 and table_size <= 7:
            col_width = "seven"
            category_width = 30
        elif table_size > 7 and table_size <= 9:
            col_width = "seven"
            category_width = 20
        elif table_size >= 10 and table_size <= 13:
            col_width = "eight"
            category_width = 15
        elif table_size > 13 and table_size <= 17:
            col_width = "eleven"
            category_width = 15
        elif table_size > 17:
            col_width = "twelve"
            category_width = 15

        data.columns = data.columns.str.replace("N-Size", "(N)", regex=True)
        data.columns = data.columns.str.replace("Rate", "Rating", regex=True)
        data.columns = data.columns.str.replace("Diff", "Difference", regex=True)

        # different column headers for AHS

        if data["Category"].str.contains("1.1|1.2.a").any() == True:
            data.columns = data.columns.str.replace("School", "Value", regex=True)
            school_headers = [y for y in data.columns.tolist() if "Value" in y]
        else:
            data.columns = data.columns.str.replace("School", "%", regex=True)
            school_headers = [y for y in data.columns.tolist() if "%" in y]

        nsize_headers = [y for y in data.columns.tolist() if "N" in y]
        rating_headers = [y for y in data.columns.tolist() if "Rating" in y]
        diff_headers = [y for y in data.columns.tolist() if "Difference" in y]

        # get new col list after renaming N-Size
        all_cols = data.columns.tolist()

        format_cols = rating_headers + diff_headers

        # splits column width evenly for all columns other than "Category"
        # can adjust individual categories by adjusting formula
        if table_size <= 3:
            data_width = 100 - category_width
            nsize_width = school_width = rating_width = diff_width = data_width / (
                table_size - 1
            )

        else:
            nsize_width = 3
            rating_width = 4
            remaining_width = 100 - category_width - (nsize_width + rating_width)

            data_col_width = remaining_width / (table_size - 1)

            school_width = data_col_width - (data_col_width * 0.15)
            diff_width = data_col_width + (data_col_width * 0.15)

        class_name = "pretty-container " + col_width + " columns"

        table_cell_conditional = (
            [
                {
                    "if": {"column_id": "Category"},
                    "textAlign": "left",
                    "paddingLeft": "20px",
                    "fontWeight": "500",
                    "fontSize": "11px",
                    "width": str(category_width) + "%",
                },
            ]
            + [
                {
                    "if": {"column_id": school},
                    "textAlign": "center",
                    "fontWeight": "500",
                    "fontSize": "11px",
                    "width": str(school_width) + "%",
                }
                for school in school_headers
            ]
            + [
                {
                    "if": {"column_id": nsize},
                    "textAlign": "center",
                    "fontWeight": "500",
                    "fontSize": "11px",
                    "width": str(nsize_width) + "%",
                }
                for nsize in nsize_headers
            ]
            + [
                {
                    "if": {"column_id": rating},
                    "textAlign": "center",
                    "fontWeight": "500",
                    "fontSize": "11px",
                    "width": str(rating_width) + "%",
                }
                for rating in rating_headers
            ]
            + [
                {
                    "if": {"column_id": diff},
                    "textAlign": "center",
                    "fontWeight": "500",
                    "fontSize": "11px",
                    "width": str(diff_width) + "%",
                }
                for diff in diff_headers
            ]
        )

        # drop subject from category strings
        data["Category"] = data["Category"].map(lambda x: x.split("|")[0])

        # Build list of lists, top level and secondary level column names
        # for multi-level headers
        name_cols = [["Category", ""]]

        for item in all_cols:
            if item.startswith("20"):
                if "Rating" in item:
                    item = item[:10]

                name_cols.append([item[:4], item[4:]])

        # NOTE: Can't think of any non-stupid way to do this. We need some way to determine which
        # column is the "first" year of data, such that no rating is calculated and then mark it
        # with "Initial Year." The problem is in the variety of dataframes. We can't just check one
        # index to make a determination. I'm sure there is a more elegant way, but right now, we
        # check the 2nd, 3rd, and 4th cols looking for the pattern "%, (N), %", which (trust me),
        # is 'a' way to tell when we need to add str "Initial Year" to idx 1 & 2.
        # we also want to save the name of the second column header (in format YYYY(N)), so
        # we can apply a right hand border to that column when styling the table
        first_year = None

        if any("Rating" in s for s in all_cols):
            if (
                name_cols[1][1] == "%"
                and name_cols[2][1] == "(N)"
                and name_cols[3][1] == "%"
            ):
                name_cols[1][0] = name_cols[1][0] + " (Initial Year)"
                first_year = name_cols[2][0] + name_cols[2][1]
                name_cols[2][0] = name_cols[2][0] + " (Initial Year)"

        # NOTE: This adds a border to header_index:1 for each category
        # For a single bottom line: comment out blocks, comment out
        # style_header_conditional in table declaration,
        # and uncomment style_as_list in table declaration

        table_header_conditional = (
            [
                {
                    "if": {
                        "column_id": school,
                        "header_index": 1,
                    },
                    "fontWeight": "600",
                    "fontSize": "10px",
                    "borderLeft": ".5px solid #b2bdd4",
                    "borderTop": ".5px solid #b2bdd4",
                    "borderBottom": ".5px solid #b2bdd4",
                }
                for school in school_headers
            ]
            + [
                {
                    "if": {
                        "column_id": rating,
                        "header_index": 1,
                    },
                    "fontWeight": "500",
                    "fontSize": "10px",
                    "borderTop": ".5px solid #b2bdd4",
                    "borderBottom": ".5px solid #b2bdd4",
                }
                for rating in rating_headers
            ]
            + [
                {
                    "if": {
                        "column_id": diff,
                        "header_index": 1,
                    },
                    "textAlign": "center",
                    "fontWeight": "500",
                    "fontSize": "10px",
                    "borderTop": ".5px solid #b2bdd4",
                    "borderBottom": ".5px solid #b2bdd4",
                }
                for diff in diff_headers
            ]
            + [
                {
                    "if": {
                        "column_id": nsize,
                        "header_index": 1,
                    },
                    "textAlign": "center",
                    "fontWeight": "500",
                    "fontSize": "10px",
                    "borderTop": ".5px solid #b2bdd4",
                    "borderBottom": ".5px solid #b2bdd4",
                }
                for nsize in nsize_headers
            ]
            + [
                # Use "all_cols[-1]" and "borderRight" for each subheader to have full border
                # Use "all_cols[1]" and "borderLeft" to leave first and last columns open on
                # right and left
                {
                    "if": {
                        "column_id": all_cols[-1],
                        #    "column_id": all_cols[1],
                        "header_index": 1,
                    },
                    "borderRight": ".5px solid #b2bdd4",
                }
            ]
        )

        # NOTE: A wee kludge here. Typically, we want a border on the right side of every Rating
        # column to signify the right edge of a year. However, for IREAD, we actually want the
        # border on the right side of the Difference column and not on the Rating column. So we
        # simply swap rating headers for diff headers if we are dealing with the IREAD data.
        if "IREAD-3" in label[0]:
            rating_headers = diff_headers

        # formatting logic is slightly different for a multi-header table
        table_data_conditional = (
            [
                {
                    "if": {"state": "selected"},
                    "backgroundColor": "rgba(112,128,144, .3)",
                    "border": "thin solid silver",
                },
                {"if": {"row_index": "odd"}, "backgroundColor": "#eeeeee"},
            ]
            + [
                {
                    "if": {
                        "column_id": all_cols[-1],
                    },
                    "borderRight": ".5px solid #b2bdd4",
                },
            ]
            + [{"if": {"row_index": 0}, "paddingTop": "5px"}]
            + [
                {
                    "if": {"row_index": len(data) - 1},
                    "borderBottom": ".5px solid #b2bdd4",
                }
            ]
            + [
                {
                    "if": {
                        "column_id": "Category",
                    },
                    "borderRight": ".5px solid #b2bdd4",
                    "borderBottom": "none",
                },
            ]
            + [
                {
                    "if": {
                        "column_id": nsize,
                    },
                    "fontSize": "11px",  # NOTE: This doesn't work as cell_conditional - is it because its markdown?
                    "textAlign": "center",
                }
                for nsize in nsize_headers
            ]
            + [
                {
                    "if": {
                        "column_id": rating,
                    },
                    "borderRight": ".5px solid #b2bdd4",
                    "textAlign": "center",
                }
                for rating in rating_headers
            ]
            + [
                {
                    "if": {
                        "filter_query": "{{{col}}} < 0".format(col=col),
                        "column_id": col,
                    },
                    "color": "#b44655",
                }
                for col in format_cols
            ]
            + [
                {
                    "if": {
                        "filter_query": "{{{col}}} = '-***'".format(col=col),
                        "column_id": col,
                    },
                    "color": "#b44655",
                }
                for col in format_cols
            ]
            + [
                {
                    "if": {
                        "filter_query": "{{{col}}} > 0".format(col=col),
                        "column_id": col,
                    },
                    "color": "#81b446",
                }
                for col in format_cols
            ]
            + [
                {
                    "if": {
                        "column_id": first_year,
                    },
                    "borderRight": ".5px solid #b2bdd4",
                }
            ]
        )

        table_columns = [
            {"name": col, "id": all_cols[idx], "presentation": "markdown"}
            if "Rating" in col or "(N)" in col
            # NOTE: Cannot figure out how to have three different col formatting conditions
            # {
            #     "name": col,
            #     "id": headers[idx],
            #     "type":"numeric",
            #     "format": Format()
            # }
            # if "n" in col
            else {
                "name": col,
                "id": all_cols[idx],
                "type": "numeric",
                "format": Format(
                    scheme=Scheme.percentage, precision=2, sign=Sign.parantheses
                ),
            }
            for (idx, col) in enumerate(name_cols)
        ]

        # Create custom tooltip with metric/rating definitions- because the default tooltip is limited,
        # we use dash-mantine-components: a dmc.Table inside of a dmc.HoverCard

        # Metric definitions are stored in a dictionary keyed to the metric number in load_data.py.
        metric_id = re.findall(r"[\d\.]+[a-z]{1}|[\d\.]+", label[0])

        def create_tooltip(id: list) -> Tuple[list, list]:
            # TODO: AHS - split out 1.1, 1.3 (AHS), 1.2.a (AHS) and 1.2.b (AHS)
            # NOTE: There is a known bug in HoverCard that can cause the browser to hang if the pop
            # up opens in a space where there is no room for it (e.g., if it is set to position "top"
            # and it is triggered by something at the top of the browser window. One workaround is to
            # set the position of the Card to bottom, where it is less likely to have no space. This
            # was fixed in the current alpha (0.13) but is not released yet
            # https://community.plotly.com/t/dash-mantine-datepicker/75251/2

            if not id:
                header = []
                body = []
            else:
                # These metrics share ratings with their counterparts (1.1.b,1.4.f,& 1.7.d)
                # 1.1.c and 1.7.a have been merged
                if (
                    id[0] == "1.1.a"
                    or id[0] == "1.1.c"
                    or id[0] == "1.4.e"
                    or id[0] == "1.7.a"
                    or id[0] == "1.7.c"
                ):
                    header_string = id[0] + " & " + id[1]
                else:
                    header_string = id[0]

                header = [
                    html.Tr(
                        [
                            html.Th("Rating"),
                            html.Th("Metric (" + header_string + ")"),
                        ]
                    )
                ]

                rows = []
                ratings = ["Exceeds", "Meets", "Approaches", "Does Not Meet"]

                if id[0] in metric_strings:
                    for s in range(0, len(metric_strings[id[0]])):
                        if metric_strings[id[0]][s]:
                            # use id and 'im-very-special' class to ensure metrics with only three
                            # ratings have the third rating colored red rather than orange
                            if id[0] == "1.1.a" and s == 3:
                                rows.append(
                                    html.Tr(
                                        [
                                            html.Td(ratings[s], id="im-very-special"),
                                            html.Td(metric_strings[id[0]][s]),
                                        ]
                                    )
                                )
                            else:
                                rows.append(
                                    html.Tr(
                                        [
                                            html.Td(ratings[s]),
                                            html.Td(metric_strings[id[0]][s]),
                                        ]
                                    )
                                )

                body = [html.Tbody(rows)]

            return header, body

        header, body = create_tooltip(metric_id)

        table = [
            html.Div(
                [
                    dmc.HoverCard(
                        className="hover_card",
                        withArrow=False,
                        width=300,
                        shadow="md",
                        position="bottom",
                        children=[
                            dmc.HoverCardTarget(
                                html.Label(label, className="label__header"),
                            ),
                            dmc.HoverCardDropdown(dmc.Table(header + body)),
                        ],
                    ),
                    html.Div(
                        dash_table.DataTable(
                            data.to_dict("records"),
                            columns=table_columns,
                            style_data=table_style,
                            style_data_conditional=table_data_conditional,
                            style_header=table_header,
                            style_header_conditional=table_header_conditional,
                            style_cell=table_cell,
                            style_cell_conditional=table_cell_conditional,
                            merge_duplicate_headers=True,
                            markdown_options={"html": True},
                            tooltip_conditional=[
                                {
                                    "if": {
                                        "column_id": col,
                                        "filter_query": f"{{{col}}} = '-***'",
                                    },
                                    "type": "markdown",
                                    "value": "This indicates a reduction from '***' (a measurable, but not reportable, value) in one year to '0' in the following year.",
                                }
                                for col in data.columns
                            ],
                            tooltip_delay=0,
                            tooltip_duration=None,
                        )
                    ),
                ],
                className=class_name,
            )
        ]

    return table


def create_comparison_table(
    data: pd.DataFrame, trace_colors: dict, school_id: str
) -> list:
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

    # replace color with Font Awesome string and create df to merge
    icon_colors = {
        k: v.replace(
            v,
            '<span style="font-size: 1em;"><i class="fa fa-square" style="color: '
            + v
            + ';"></i></style>',
        )
        for k, v in trace_colors.items()
    }
    color_df = pd.DataFrame(list(icon_colors.items()), columns=["Name", "Icon"])

    # sort dataframe by the column with the most recent year of datafirst
    # column with data and reset index
    data = data.sort_values(data.columns[1], ascending=False, na_position="last")

    data = data.reset_index(drop=True)
    data.columns = data.columns.astype(str)

    # locate school index by School ID and then drop School ID column
    school_name_idx = data.index[data["School ID"] == np.int64(school_id)].tolist()[0]
    data = data.drop("School ID", axis=1)

    # strip gradespan data and whitespace for merge key
    data["Name"] = data["School Name"].str.replace(r"\([^)]+\)", "", regex=True)
    data["Name"] = data["Name"].str.strip()

    # merge colored icons into df and combine into School Name
    data = pd.merge(data, color_df, on="Name")

    data = data.drop(["Name"], axis=1)

    # shift "Icon" column to front of df for display
    icon_col = data.pop("Icon")
    data.insert(0, "Icon", icon_col)

    if data.columns.str.contains("Total").any() == True:
        # keep everything between | and "Benchmark %"
        data.columns = data.columns.str.replace("Benchmark %", "")
        data.columns = data.columns.str.replace("Total\|", "", regex=True)

    # this should work for another 976 years (skip the year over year dfs)
    elif data.columns.str.startswith("2").any() == True:
        pass

    else:
        # remove everything between | & % in column name
        data.columns = data.columns.str.replace(r"\|(.*?)\%", "", regex=True)

    # NOTE: sort on native DataTable is ugly - explore migration to AG Grid
    table = dash_table.DataTable(
        data.to_dict("records"),
        columns=[
            {"name": i, "id": i, "presentation": "markdown"}
            if "Icon" in i
            else {
                "name": i,
                "id": i,
                "type": "numeric",
                "format": FormatTemplate.percentage(2),
            }
            for i in data.columns
        ],
        # sort_action="native",
        markdown_options={"html": True},
        merge_duplicate_headers=True,
        style_as_list_view=True,
        id="comparison-table",
        style_data=table_style,
        style_data_conditional=[
            {
                "if": {"row_index": "even"},
                "backgroundColor": "#eeeeee",
                "border": "none",
            },
            {
                "if": {"row_index": school_name_idx},
                "fontWeight": "bold",
                "color": "#b86949",
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(112,128,144, .3)",
                "border": "thin solid silver",
            },
        ],
        style_header=table_header,
        style_header_conditional=[
            {
                "if": {"header_index": 0},
                "text-decoration": "underline",
            },
        ],
        style_cell=table_cell,
        style_cell_conditional=[
            {
                "if": {"column_id": "School Name"},
                "textAlign": "left",
                "width": "30%",
            },
            {
                "if": {"column_id": "Icon"},
                "textAlign": "right",
                "width": "5%",
                "paddingLeft": "20px",
            },
        ],
        # This has the effect of hiding the header row
        css=[
            {
                "selector": "tr:first-child",
                "rule": "display: none",
            },
        ],
    )

    table_layout = [html.Div([html.Div(table)])]

    # NOTE: below code adds a label if one is passed (used for same row chart/
    # table layout). If using this, need to re-add 'label' variable to fn.

    # bar-chart tables (Math, ELA, & IREAD) should have a label multi-bar chart tables
    # (by Subgroup, by Ethnicity) should not have a label this is for formatting reasons.
    # this assumes label is set to "" for multi-bar charts
    # if label:
    #     table_layout = [
    #         html.Div([html.Label(label, className="label__header"), html.Div(table)])
    #     ]
    # else:
    #     table_layout = [html.Div([html.Div(table)])]

    return table_layout


def create_financial_analysis_table(data: pd.DataFrame, categories: list) -> list:
    category_data = data.loc[data["Category"].isin(categories)]

    years = [c for c in category_data if "Category" not in c]

    tmp_category = category_data["Category"]
    category_data = category_data.drop("Category", axis=1)

    # special case for revenue per student table

    if "ADM Average" in categories:
        # divide category by ADM and then drop ADM row
        category_data = category_data.div(category_data.iloc[len(category_data) - 1])
        category_data = category_data.iloc[:-1]

    # only calculate "% Change" if the number of columns with all zeros is
    # equal to 0 (e.g., all columns have nonzero values) force % formatting
    # Find % change for all tables
    if category_data.sum().eq(0).sum() == 0:
        category_data["% Change"] = (
            category_data[years[1]] - category_data[years[0]]
        ).div(abs(category_data[years[0]]))
        category_data["% Change"] = pd.Series(
            ["{0:.2f}%".format(val * 100) for val in category_data["% Change"]],
            index=category_data.index,
        )

    else:
        category_data["% Change"] = "N/A"

    # format numbers (since we are converting values to strings, we cannot vectorize,
    # need to iterate through each series)
    for year in years:
        category_data[year] = pd.Series(
            ["{:,.2f}".format(val) for val in category_data[year]],
            index=category_data.index,
        )

    # other clean-up for display purposes
    category_data.replace("nan", "0", inplace=True)
    category_data.replace(
        ["inf%", "0.00", "0.0", "0", np.inf, -np.inf], "N/A", inplace=True
    )

    category_data.insert(loc=0, column="Category", value=tmp_category)

    category_data = category_data.reset_index(drop=True)

    table = [
        dash_table.DataTable(
            category_data.to_dict("records"),
            columns=[{"name": i, "id": i} for i in category_data.columns],
            style_data={
                "fontSize": "12px",
                "fontFamily": "Inter, sans-serif",
            },
            style_data_conditional=[
                {
                    "if": {
                        "column_id": "Category",
                    },
                    "borderRight": ".5px solid #4682b4",
                },
                {
                    "if": {"state": "selected"},
                    "backgroundColor": "rgba(112,128,144, .3)",
                    "border": "thin solid silver",
                },
            ],
            style_header={
                "height": "20px",
                "backgroundColor": "#ffffff",
                "borderBottom": ".5px solid #6783a9",
                "borderTop": "none",
                "borderRight": "none",
                "borderLeft": "none",
                "fontSize": "12px",
                "fontFamily": "Inter, sans-serif",
                "color": "#6783a9",
                "textAlign": "center",
                "fontWeight": "bold",
            },
            style_header_conditional=[
                {
                    "if": {
                        "column_id": "Category",
                    },
                    "borderRight": ".5px solid #6783a9",
                    "borderBottom": ".5px solid #6783a9",
                    "textAlign": "left",
                },
            ],
            style_cell={
                "border": "none",
                "whiteSpace": "normal",
                "height": "auto",
                "textAlign": "center",
                "color": "#6783a9",
                "minWidth": "25px",
                "width": "25px",
                "maxWidth": "25px",
            },
            style_cell_conditional=[
                {
                    "if": {"column_id": "Category"},
                    "textAlign": "left",
                    "paddingLeft": "20px",
                    "width": "40%",
                },
            ],
        )
    ]
    return table
