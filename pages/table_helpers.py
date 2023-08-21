########################################
# ICSB Dashboard - DataTable Functions #
########################################
# author:   jbetley
# version:  1.09
# date:     08/14/23

import pandas as pd
from dash import dash_table, html
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign

# Global table styles
table_style = {
    "fontSize": "12px",
    "border": "none",
    "fontFamily": "Jost, sans-serif"
}

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
    "fontFamily": "Jost, sans-serif",
    "color": "#6783a9",
    "textAlign": "center",
    "fontWeight": "bold",
    "border": "none"
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
                "fontSize": "1em",
                "border": "none",
                "fontFamily": "Jost, sans-serif",
            },
            style_cell = {
                "whiteSpace": "normal",
                "height": "auto",
                "border": "none",
                "textAlign": "right",
                "color": "#6783a9",
            },
            style_cell_conditional = [
                {
                    "if": {
                        "column_id": rating
                    },
                    "textAlign": "right",
                } for rating in rating_cols
            ] + [
                {
                    "if": {
                        "column_id": icon
                    },
                    "textAlign": "left",
                    "width": "2%",
                } for icon in icon_cols
            ],
            style_data_conditional=[
                {
                    "if": {
                        "filter_query": "{Rate} = 'Exceeds Standard'",
                        "column_id": "icon",
                    },
                    "color": "#b33dc6",
                },
                {
                    "if": {"filter_query": "{Rate2} = 'Meets Standard'",
                        "column_id": "icon2"
                    },
                    "color": "#87bc45",
                },
                {
                    "if": {"filter_query": "{Rate3} = 'Approaches Standard'",
                        "column_id": "icon3"
                    },
                    "color": "#ede15b",
                },
                {
                    "if": {"filter_query": "{Rate4} = 'Does Not Meet Standard'",
                        "column_id": "icon4"
                    },
                    "color": "#ea5545",
                },
                {
                    "if": {"filter_query": "{Rate5} = 'No Rating'",
                        "column_id": "icon5"
                    },
                    "color": "#a4a2a8",
                },
                {
                "if": {
                    "column_id": rating_headers[1],
                },
                "marginLeft":"10px",
                },
            ],
        )
    ]

    return key_table

def no_data_table(label: list = ["Academic Data"], text: list = ["No Data to Display"]) -> list:
    """
    Creates empty table with provided label and content string

    Args:
        label (str): table label
        text (str): table content

    Returns:
        table_layout (list): a dash html.Label object and html.Div object enclosing a dash DataTable
    """

    table_layout = [
                html.Label(label, className="header_label"),
                html.Div(
                    dash_table.DataTable(
                        columns = [
                            {"id": "emptytable", "name": text},
                        ],
                        style_header={
                            "fontSize": "14px",
                            "border": "none",
                            "textAlign": "center",
                            "color": "#6783a9",
                            "fontFamily": "Jost, sans-serif",
                            "height": "30vh",
                        },
                    ),
                ),
            ]

    return table_layout

def no_data_page(label: str = "Academic Data", text: str = "No Data to Display") -> list:
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
                                html.Label(label, className="header_label"),
                                html.Div(
                                    dash_table.DataTable(
                                        data=empty_dict,
                                        columns = [
                                            {"id": "emptytable", "name": text},
                                        ],
                                        style_header={
                                            "fontSize": "14px",
                                            "border": "none",
                                            "textAlign": "center",
                                            "color": "#6783a9",
                                            "fontFamily": "Jost, sans-serif",
                                            "height": "30vh",
                                        },
                                        style_data={
                                            "display": "none",
                                        },
                                    ),
                                ),
                            ],
                            className = "pretty_container eight columns"
                        ),
                    ],
                    className = "bare_container_center twelve columns",
                ),
            ],
            className = "empty_table",
        )
    ]

    return table_layout

# def hidden_table() -> list:
#     """
#     Creates an empty table with no cells. Will be automatically hidden
#     ("display": "none") by css selector chaining for pretty_container.
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

def create_growth_table_and_fig(table: list, fig, label: str):    # : plotly.graph_objs._figure.Figure
    
    table_layout = [
        html.Div(
            [
                html.Div(
                    [                    
                        html.Label(label, className="header_label"),                    
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(table, style={"marginTop": "20px"}),
                                    ],
                                    className="pretty_container six columns",
                                ),
                                html.Div(
                                    [
                                        html.Div(fig, style={"marginTop": "-20px"}),
                                    ],
                                    className="pretty_container six columns",
                                ),
                            ],
                            className="bare_container twelve columns",
                        ),
                    ],
                    className="pretty_container twelve columns",
                ),       
            ],
            className="bare_container_center twelve columns",
        ),             
    ]

    return table_layout

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

    data_me = data.loc[:, data.columns.str.contains("Category|Majority Enrolled")].copy()
    data_me = data_me.rename(columns={c: c[:4] for c in data_me.columns if c not in ["Category"]})

    # 162 day data is used for tooltip
    data_162 = data.loc[:, data.columns.str.contains("Category|162 Days")].copy()
    data_162 = data_162.rename(columns={c: c[:4] for c in data_162.columns if c not in ["Category"]})
    data_162 = data_162.drop("Category", axis=1)

    # Reverse year order (ignoring Category) to align with charts (ascending order)
    data_me = data_me.iloc[:, ::-1]
    data_me.insert(0, "Category", data_me.pop("Category"))

    table_size = len(data_me.columns)

    if len(data_me.index) == 0 or table_size == 1:
        table_layout = [
            html.Div(
                [
                    html.Label(label, className="header_label"),
                    html.Div(
                        dash_table.DataTable(
                            columns = [
                                {"id": "emptytable", "name": "No Data to Display"},
                            ],
                            style_header={
                                "fontSize": "14px",
                                "border": "none",
                                "textAlign": "center",
                                "color": "#6783a9",
                                "fontFamily": "Open Sans, sans-serif",
                            },
                        )
                    )
                ],
                className = "pretty_container ten columns"
            )
        ]

    else:

        if table_size <= 3:
            category_width = 70
        if table_size > 3 and table_size <=4:
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
                "if": {
                    "column_id": "Category"
                },
                "textAlign": "left",
                "paddingLeft": "20px",
                "fontWeight": "500",
                "width": str(category_width) + "%"
            },
        ] + [
            {
                "if": {
                    "column_id": col
                },
                "textAlign": "center",
                "fontWeight": "500",
                "width": str(data_col_width) + "%",
            } for col in data_cols
        ]

        table_header_conditional = [
            {
                "if": {
                    "column_id": col,
                },
                "borderBottom": ".5px solid #b2bdd4",
            } for col in data_cols
        ]

        table_data_conditional = [
            {
                "if": {
                    "state": "selected"
                },
                "backgroundColor": "rgba(112,128,144, .3)",
                "border": "thin solid silver"
            },
            {
                "if": {
                    "row_index": "odd"
                },
                "backgroundColor": "#eeeeee"
            },
        ] + [
            {
                "if": {
                    "row_index": 0
                },
                "paddingTop": "5px"
            },
        ]

        column_format = [
            {
            "name": col, "id": col, "type":"numeric",
            "format": Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
            }
            for col in all_cols
        ]

        tooltip_format = [
            {
                column: {
                    "value": "162 Days: {:.2%}".format(float(value)) if value == value else "",
                    "type": "markdown"
                }
                for column, value in row.items()
            }
            for row in data_162.to_dict("records")
        ]                

        table = dash_table.DataTable(
                            data_me.to_dict("records"),
                            columns = column_format,
                            style_table = {"height": "300px"},
                            style_data = table_style,
                            style_data_conditional = table_data_conditional,
                            style_header = table_header,
                            style_header_conditional = table_header_conditional,
                            style_cell = table_cell,
                            style_cell_conditional = table_cell_conditional,
                            tooltip_data = tooltip_format,
                            css=[{
                                "selector": ".dash-table-tooltip",
                                "rule": "font-size: 12px"
                            }],
                        )

        table_layout = [
            html.Div(
                [
                html.Div(table)
                ]
            )
        ]        

    return table_layout

def create_key_table(data: pd.DataFrame, label: str, width: int = 0) -> list:
    """
    Takes a dataframe, a string, and an int (optional) and creates a simple
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
    if table_size > 3 and table_size <=5:
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

    class_name = "pretty_key_container " + col_width + " columns"

    first_column = data.columns[0]
    other_columns = data.columns[1:]

    # set column widths
    first_column_width = category_width + 10
    remaining_width = 100 - category_width
    other_column_width = remaining_width / table_size

    table_cell_conditional = [
        {
            "if": {
                "column_id": other
            },
            "textAlign": "center",
            "fontWeight": "600",
            "width": str(other_column_width) + "%",
        } for other in other_columns        
    ] + [
        {
            "if": {
                "column_id": first_column
            },
            "textAlign": "left",
            "paddingLeft": "20px",
            "fontWeight": "500",
            "width": str(first_column_width) + "%"
        }
    ]

    table_data_conditional = [
        {
            "if": {
                "state": "selected"
            },
            "backgroundColor": "rgba(112,128,144, .3)",
            "border": "thin solid silver"
        },
    ] + [
        {
            "if": {
                "row_index": 0
            },
            "paddingTop": "5px"
        }
    ] + [
        {
            "if": {
                "column_id": first_column,
            },
            "borderRight": "none",
            "borderBottom": "none",
            "borderLeft": "none",
            "borderTop": "none",                        
        },
    ] + [
        { 
            "if": {
                "column_id": other,
            },
            "fontSize": "10px",
            "textAlign": "center",
            "borderLeft": ".5px solid #b2bdd4",
        } for other in other_columns
    ]

    table_layout = [
        html.Div(
            [
                html.Div(
                    [
                        html.Label(label, className="key_header_label"),
                        html.Div(
                            dash_table.DataTable(
                                data.to_dict("records"),
                                columns = [{"name": i, "id": i, "type":"numeric","format": FormatTemplate.percentage(2)} for i in data.columns],
                                style_data = {
                                    "fontSize": "12px",
                                    "fontFamily": "Jost, sans-serif",
                                    "border": "none",
                                    "color": "#6783a9",
                                },
                                style_header = {
                                    "fontSize": "12px",
                                    "fontFamily": "Jost, sans-serif",
                                    "color": "#6783a9",
                                    "textAlign": "center",
                                    "fontWeight": "bold",
                                    "border": "none",
                                    "backgroundColor": "#ffffff"
                                },
                                style_cell = {
                                    "whiteSpace": "normal",
                                    "height": "auto",
                                    "textAlign": "center",
                                    "minWidth": "25px",
                                    "width": "25px",
                                    "maxWidth": "25px",
                                },
                                style_data_conditional = table_data_conditional,
                                style_cell_conditional = table_cell_conditional,
                                merge_duplicate_headers=True
                            ),
                        ),
                    ],
                    className = class_name
                )
            ],
            className = "bare_container_center twelve columns"
        )                
    ]

    return table_layout

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
    # on the size (# of cols) of the dataframe - in the case of the basic
    # table, "Category" is simply whatever is in the first column (it may
    # or may not have the name "Category")
    if table_size <= 3:
        col_width = "six"
        category_width = 35
    if table_size > 3 and table_size <=5:
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

    class_name = "pretty_container " + col_width + " columns"

    first_column = data.columns[0]
    other_columns = data.columns[1:]

    # set column widths
    first_column_width = category_width + 10
    remaining_width = 100 - category_width
    other_column_width = remaining_width / table_size

    table_cell_conditional = [
        {
            "if": {
                "column_id": first_column
            },
            "textAlign": "left",
            "paddingLeft": "20px",
            "fontWeight": "500",
            "width": str(first_column_width) + "%"
        }
    ] + [
        {
            "if": {
                "column_id": other
            },
            "textAlign": "center",
            "fontWeight": "500",
            "width": str(other_column_width) + "%",
            "borderRight": ".5px solid #b2bdd4",
            "borderLeft": ".5px solid #b2bdd4",  
        } for other in other_columns
    ]

    table_header_conditional = [
        {
            "if": {
                "column_id": other,
            },
            "borderBottom": ".5px solid #b2bdd4"
        } for other in other_columns
    ]

    table_data_conditional = [
        {
            "if": {
                "state": "selected"
            },
            "backgroundColor": "rgba(112,128,144, .3)",
            "border": "thin solid silver"
        },
        {
            "if": {
                "row_index": "odd"
            },
            "backgroundColor": "#eeeeee"
        }
    ] + [
        {
            "if": {
                "row_index": 0
            },
            "paddingTop": "5px"
        }
    ] + [
        {
            "if": {
                "column_id": data.columns[-1],
            },
            "borderRight": ".5px solid #b2bdd4",
        },
    ] + [
        {
            "if": {
                "row_index": 0
            },
            "paddingTop": "5px"
        }
    ] + [
        {
            "if": {
                "row_index": len(data)-1
            },
            "borderBottom": ".5px solid #b2bdd4",
        }
    ] + [        
        {
            "if": {
                "column_id": first_column,
            },
            "borderRight": ".5px solid #b2bdd4",
            "borderBottom": "none",
            "borderLeft": "none",
            "borderTop": "none",                        
        },
    ] + [
        { 
            "if": {
                "column_id": other,
            },
            "fontSize": "10px",
            "textAlign": "center",
            "borderLeft": ".5px solid #b2bdd4",
        } for other in other_columns
    ]

    table_layout = [
        html.Div(
            [
                html.Div(
                    [
                        html.Label(label, className="header_label"),
                        html.Div(
                            dash_table.DataTable(
                                data.to_dict("records"),
                                columns = [{"name": i, "id": i, "type":"numeric","format": FormatTemplate.percentage(2)} for i in data.columns],
                                style_data = {
                                    "fontSize": "12px",
                                    "fontFamily": "Jost, sans-serif",
                                    "border": "none",
                                },    
                                style_header = table_header,
                                style_cell = {
                                    "whiteSpace": "normal",
                                    "height": "auto",
                                    "textAlign": "center",
                                    "color": "#6783a9",
                                    "minWidth": "25px",
                                    "width": "25px",
                                    "maxWidth": "25px",
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
            ],
            className = "bare_container_center twelve columns"
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
            col_width = "four"
            category_width = 40
        if table_size > 3 and table_size <=5:
            col_width = "six"
            category_width = 20
        elif table_size > 5 and table_size < 7:
            col_width = "six"
            category_width = 20
        elif table_size >= 7 and table_size < 9:
            col_width = "seven"
            category_width = 20
        elif table_size >= 9 and table_size <= 13:
            col_width = "eight"
            category_width = 15
        elif table_size > 13 and table_size <=17:
            col_width = "nine"
            category_width = 15
        elif table_size > 17:
            col_width = "ten"
            category_width = 15

        class_name = "pretty_container " + col_width + " columns"

        # rename columns n_size before getting n col list
        data.columns = data.columns.str.replace("N-Size|SN-Size", "Tested", regex=True)

        if "SAT" in label:
            data.columns = data.columns.str.replace("School", "At Benchmark", regex=True)
            year_headers = [y for y in data.columns if "At Benchmark" in y]            
        else:
            data.columns = data.columns.str.replace("School", "Proficiency", regex=True)
            year_headers = [y for y in data.columns if "Proficiency" in y]
        
        nsize_headers = [y for y in data.columns if "Tested" in y]

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
                "if": {
                    "column_id": "Category"
                },
                "textAlign": "left",
                "paddingLeft": "20px",
                "fontWeight": "500",
                "width": str(category_width) + "%"
            },
        ] + [
            {
                "if": {
                    "column_id": year
                },
                "textAlign": "center",
                "fontWeight": "500",
                "width": str(year_width) + "%",
            } for year in year_headers
        ]  + [
            {   "if": {
                "column_id": nsize
            },
                "textAlign": "center",
                "fontWeight": "300",
                "fontSize": "8px",
                "width": str(nsize_width) + "%"
            } for nsize in nsize_headers
        ]

        table_header_conditional = [
            {
                "if": {
                    "column_id": year,
                    "header_index": 1,
                },
                "borderLeft": ".5px solid #b2bdd4",
                "borderTop": ".5px solid #b2bdd4",
                "borderBottom": ".5px solid #b2bdd4"
            } for year in year_headers
        ] + [
            {   "if": {
                "column_id": nsize,
                "header_index": 1,
            },
                "textAlign": "center",
                "fontWeight": "400",
                "fontSize": "12px",
                "borderRight": ".5px solid #b2bdd4",
                "borderTop": ".5px solid #b2bdd4",
                "borderBottom": ".5px solid #b2bdd4"
        } for nsize in nsize_headers
        ] + [
            {   "if": {
                "column_id": all_cols[-1],
                "header_index": 1,
            },
            "borderRight": ".5px solid #b2bdd4",
            }
        ]

        table_data_conditional = [
            {
                "if": {
                    "state": "selected"
                },
                "backgroundColor": "rgba(112,128,144, .3)",
                "border": "thin solid silver"
            },
            {
                "if": {
                    "row_index": "odd"
                },
                "backgroundColor": "#eeeeee"
            }
        ] + [
            {
                "if": {
                    "column_id": all_cols[-1],
                },
                "borderRight": ".5px solid #b2bdd4",
            },
        ] + [
            {
                "if": {
                    "row_index": 0
                },
                "paddingTop": "5px"
            }
        ] + [
            {
                "if": {
                    "row_index": len(data)-1
                },
                "borderBottom": ".5px solid #b2bdd4",
            }
        ] + [
            {
                "if": {
                    "column_id": "Category",
                },
                "borderRight": ".5px solid #b2bdd4",
                "borderBottom": "none",
            },
        ] + [
            { 
                "if": {
                    "column_id": nsize,
                },
                "fontSize": "10px",
                "textAlign": "center",
                "borderRight": ".5px solid #b2bdd4",
            } for nsize in nsize_headers
        ]

        # build multi-level headers
        name_cols = [["Category",""]]

        # Split columns into two levels
        for item in all_cols:
            if item.startswith("20"):
                name_cols.append([item[:4],item[4:]])

        table_columns = [
                {
                    "name": col,
                    "id": all_cols[idx],
                    "type": "numeric",
                    "format": Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses),
                }
                if "Proficiency" in col or "At Benchmark" in col
                
                else
                    {
                        "name": col,
                        "id": all_cols[idx],
                        "type":"numeric",
                        "format": Format()
                    }
                    for (idx, col) in enumerate(name_cols)
        ]

        table_layout = [
            html.Div(
                [
                    html.Label(label, className="header_label"),
                    html.Div(
                        dash_table.DataTable(
                            data.to_dict("records"),
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
                    html.Label(label, className="header_label"),
                    html.Div(
                        dash_table.DataTable(
                            data=empty_dict,
                            columns = [
                                {"id": "emptytable", "name": "No Data to Display"},
                            ],
                            style_header={
                                "fontSize": "14px",
                                "border": "none",
                                "textAlign": "center",
                                "color": "#6783a9",
                                "fontFamily": "Jost, sans-serif",
                                "height": "30vh",
                            },
                            style_data={
                                "display": "none",
                            },
                        ),
                    ),
                ],
                className = "pretty_container four columns"
            )
        ]

    return table_layout

def create_metric_table(label: list, data: pd.DataFrame) -> list:
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

    table_size = len(data.columns)

    if len(data.index) == 0 or table_size == 1:
        table = [
            html.Div(
                [
                    html.Label(label, className="header_label"),
                    html.Div(
                        dash_table.DataTable(
                            columns = [
                                {"id": "emptytable", "name": "No Data to Display"},
                            ],
                            style_header={
                                "fontSize": "14px",
                                "border": "none",
                                "textAlign": "center",
                                "color": "#6783a9",
                                "fontFamily": "Open Sans, sans-serif",
                            },
                        )
                    )
                ],
                className = "pretty_container ten columns"
            )
        ]

    else:

        # determines the col_width class and width of the category column based
        # on the size (# of cols) of the dataframe
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
        elif table_size > 13 and table_size <=17:
            col_width = "ten"
            category_width = 15
        elif table_size > 17:
            col_width = "eleven"
            category_width = 15

        list_cols = data.columns.tolist()

        # used for formatting purposes
        year_headers = [y for y in list_cols if "School" in y]
        rating_headers = [y for y in list_cols if "Rate" in y]
        diff_headers = [y for y in list_cols if "Diff" in y]

        # rename n_size before getting col list
        data.columns = data.columns.str.replace("N-Size", "Tested", regex=True)
        nsize_headers = [y for y in data.columns.tolist() if "Tested" in y]

        # get new col list after renaming N-Size
        all_cols = data.columns.tolist()

        format_cols = rating_headers + diff_headers

        # splits column width evenly for all columns other than "Category"
        # can adjust individual categories by adjusting formula

        # set column widths
        if table_size <= 3:
            data_width = 100 - category_width
            nsize_width = year_width = rating_width = diff_width = data_width / (table_size - 1)          
        
        else:

            nsize_width = 5
            remaining_width = 100 - category_width - nsize_width

            data_col_width = remaining_width / (table_size - 1)
            rating_width = data_col_width/2
            year_width = data_col_width + data_col_width/4
            diff_width = data_col_width + data_col_width/4

        class_name = "pretty_container " + col_width + " columns"

        table_cell_conditional = [
            {
                "if": {
                    "column_id": "Category"
                },
                "textAlign": "left",
                "paddingLeft": "20px",
                "fontWeight": "500",
                "width": str(category_width) + "%"
            },
        ] + [
            {
                "if": {
                    "column_id": year
                },
                "textAlign": "center",
                "fontWeight": "500",
                "width": str(year_width) + "%",
            } for year in year_headers
        ]  + [
            {   "if": {
                "column_id": nsize
            },
                "textAlign": "center",
                "fontWeight": "500",
                "width": str(nsize_width) + "%"
            } for nsize in nsize_headers
        ]  + [            
            {   "if": {
                "column_id": rating
            },
                "textAlign": "center",
                "fontWeight": "700",
                "width": str(rating_width) + "%"
            } for rating in rating_headers
        ]  + [
            {   "if": {
                "column_id": diff
            },
                "textAlign": "center",
                "fontWeight": "500",
                "width": str(diff_width) + "%"
            } for diff in diff_headers
        ]
 
        # drop subject
        data["Category"] = data["Category"].map(lambda x: x.split("|")[0])

        # Build list of lists, top level and secondary level column names
        # for multi-level headers
        name_cols = [["Category",""]]

        for item in all_cols:
            if item.startswith("20"):
                if "Rate" in item:
                    item = item[:8]

                name_cols.append([item[:4],item[4:]])

        # Each year of an academic metrics data file has a possible 4 columns:
        # School, Tested, Diff, and Rate. So if the last column for an academic metrics
        # dataframe is "Rate," then we have a full years worth of data for all calculations
        # (both comparison, which requires 1 year of data AND year over year, which requires
        # two years of data). However, the first year of data for a school means Diff and Rate
        # will not be calculated. So if the last column is a "Tested" column, we need to add
        # '(Initial Year)' to the header for all columns of that year. Thus also applies in the
        # case where the last column is 'School' (impacts one table)
        if name_cols[-1][1] == 'Tested':
            name_cols[-1][0] = name_cols[-1][0] + ' (Initial Year)'   # the first item in the last list
            name_cols[-2][0] = name_cols[-2][0] + ' (Initial Year)'   # the first item in the second to last list

        if name_cols[-1][1] == 'School':
            name_cols[-1][0] = name_cols[-1][0] + ' (Initial Year)'

        # NOTE: This add a border to header_index:1 for each category
        # For a single bottom line: comment out blocks, comment out
        # style_header_conditional in table declaration,
        # and uncomment style_as_list in table declaration
        table_header_conditional = [
            {
                "if": {
                    "column_id": year,
                    "header_index": 1,
                },
                "borderLeft": ".5px solid #b2bdd4",
                "borderTop": ".5px solid #b2bdd4",
                "borderBottom": ".5px solid #b2bdd4",
            } for year in year_headers
        ] + [
            {   "if": {
                "column_id": rating,
                "header_index": 1,
            },
                "borderTop": ".5px solid #b2bdd4",
                "borderBottom": ".5px solid #b2bdd4",
        } for rating in rating_headers
        ]  + [
            {   "if": {
                "column_id": diff,
                "header_index": 1,
            },
                "textAlign": "center",
                "fontWeight": "400",
                "fontSize": "12px",
                "borderTop": ".5px solid #b2bdd4",
                "borderBottom": ".5px solid #b2bdd4",
        } for diff in diff_headers
        ]  + [
            {   "if": {
                "column_id": nsize,
                "header_index": 1,
            },
                "textAlign": "center",
                "fontWeight": "400",
                "fontSize": "12px",
                "borderTop": ".5px solid #b2bdd4",
                "borderBottom": ".5px solid #b2bdd4",
        } for nsize in nsize_headers
        ] + [
            # Use "headers[-1]" and "borderRight" for each subheader to have full border
            # Use "headers[1]" and "borderLeft" to leave first and last columns open on
            # right and left
            {   "if": {
                "column_id": all_cols[-1],
            #    "column_id": headers[1],
                "header_index": 1,
            },
            "borderRight": ".5px solid #b2bdd4",
            }
        ]

        # formatting logic is slightly different for a multi-header table
        table_data_conditional = [
            {
                "if": {
                    "state": "selected"
                },
                "backgroundColor": "rgba(112,128,144, .3)",
                "border": "thin solid silver"
            },
            {
                "if": {
                    "row_index": "odd"
                },
                "backgroundColor": "#eeeeee"
            }
        ] + [
            {
                "if": {
                    "column_id": all_cols[-1],
                },
                "borderRight": ".5px solid #b2bdd4",
            },
        ] + [
            {
                "if": {
                    "row_index": 0
                },
                "paddingTop": "5px"
            }
        ] + [
            {
                "if": {
                    "row_index": len(data)-1
                },
                "borderBottom": ".5px solid #b2bdd4",
            }
        ] + [
            {
                "if": {
                    "column_id": "Category",
                },
                "borderRight": ".5px solid #b2bdd4",
                "borderBottom": "none",
            },
        ] + [
            {   # NOTE: This doesn't work as cell_conditional - is it because its markdown?
                "if": {
                    "column_id": nsize,
                },
                "fontSize": "10px",
                "textAlign": "center",
            } for nsize in nsize_headers
        ] + [
            {
                "if": {
                    "column_id": rating,
                },
                "borderRight": ".5px solid #b2bdd4",
                "textAlign": "center",
            } for rating in rating_headers
        ] + [
            {
                "if": {
                    "filter_query": '{{{col}}} < 0'.format(col=col),
                    "column_id": col
                },
                "fontWeight": "bold",
                "color": "#b44655",
                "fontSize": "10px",
            } for col in format_cols
        ] + [
            {
                "if": {
                    "filter_query": "{{{col}}} = '-***'".format(col=col),
                    "column_id": col
                },
                "fontWeight": "bold",
                "color": "#b44655",
                "fontSize": "10px",
            } for col in format_cols
        ] + [
            {
                "if": {
                    "filter_query": "{{{col}}} > 0".format(col=col),
                    "column_id": col
                },
                "fontWeight": "bold",
                "color": "#81b446",
                "fontSize": "10px",
            } for col in format_cols
        ]

        table_columns = [
            {
                "name": col,
                "id": all_cols[idx],
                "presentation": "markdown"
            }
            if "Rate" in col or "Tested" in col

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
                "type":"numeric",
                "format": Format(scheme=Scheme.percentage, precision=2, sign=Sign.parantheses)
            }
            for (idx, col) in enumerate(name_cols)
        ]

        table = [
            html.Div(
                [
                    html.Label(label, className="header_label"),
                    html.Div(
                        dash_table.DataTable(
                            data.to_dict("records"),
                            columns = table_columns,
                            style_data = table_style,
                            style_data_conditional = table_data_conditional,
                            style_header = table_header,
                            style_header_conditional = table_header_conditional,
                            style_cell = table_cell,
                            style_cell_conditional = table_cell_conditional,
                            merge_duplicate_headers=True,
                            markdown_options={"html": True},
                            tooltip_conditional=[
                                {
                                    "if": {
                                        "column_id": col,
                                        "filter_query": f"{{{col}}} = '-***'",
                                    },
                                    "type": "markdown",
                                    "value": "This indicates a reduction from '***' (a measurable, but not reportable, value) in one year to '0' in the following year."
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
                    className = "bare_container_center twelve columns",
                )
        ]

    else:

        if len(cols) >= 4:
            table_layout = [
                    html.Div(
                        table1,
                        className = "bare_container_center twelve columns",
                    ),
                    html.Div(
                        table2,
                        className = "bare_container_center twelve columns",
                    ),
            ]

        else:

            table_layout = [
                    html.Div(
                        [
                            table1[0],
                            table2[0],
                        ],
                        className = "bare_container_center twelve columns",
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
    school_name_idx = data.index[data["School Name"].str.contains(school_name)].tolist()[0]

    # drop all columns where the row at school_name_idx has a NaN value
    data = data.loc[:, ~data.iloc[school_name_idx].isna()]

    # sort dataframe by the "first" proficiency column and reset index
    data = data.sort_values(data.columns[1], ascending=False)

    data = data.reset_index(drop=True)

    # need to find the index again because the sort has jumbled things up
    school_name_idx = data.index[data["School Name"].str.contains(school_name)].tolist()[0]

    # hide the header "School Name"
    data = data.rename(columns = {"School Name" : ""})

    # simplify and clarify column names (remove everything between | & %)
    data.columns = data.columns.str.replace(r"\|(.*?)\%", "", regex=True)

# NOTE: Try AG Grid for more responsive table
#       pip install dash-ag-grid==2.0.0
#       import dash_ag_grid as dag

    table = dash_table.DataTable(
        data.to_dict("records"),
        columns = [{"name": i, "id": i, "type":"numeric","format": FormatTemplate.percentage(2)} for i in data.columns],
        # sort_action="native",
        merge_duplicate_headers=True,
        style_as_list_view=True,
        id="tst-table",
        style_data = table_style,
        style_data_conditional=[
            {
                "if": {
                    "row_index": "even"
                },
                "backgroundColor": "#eeeeee",
                "border": "none",
            },
            {
                "if": {
                    "row_index": school_name_idx
                },
                "fontWeight": "bold",
                "color": "#b86949",
            },
            {
                "if": {
                    "state": "selected"
                },
                "backgroundColor": "rgba(112,128,144, .3)",
                "border": "thin solid silver"
            }
        ],
        style_header = table_header,
        style_header_conditional = [
            {
                "if": {
                    "header_index": 0,
                    },
                    "text-decoration": "underline"
            },
        ],
        style_cell = table_cell,
        style_cell_conditional = [
            {
                "if": {
                    "column_id": ""
                },
                "textAlign": "left",
                "paddingLeft": "30px"
            }
        ]
    )

    # bar-chart tables (Math, ELA, & IREAD) should have a label
    # multi-bar chart tables (by Subgroup, by Ethnicity) should not have a label
    # this is for formatting reasons
    if data.columns.str.contains("Total").any() == True or data.columns.str.contains("IREAD").any() == True:
        table_layout = [
            html.Div(
                [
                html.Label(label, className = "header_label"),
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

def combine_barchart_and_table(fig: list, table: list) -> list:
    """
    A little helper function to combine a px.bar fig and a dash datatable

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
                        className = 'pretty_container nine columns',
                    ),
                    html.Div(
                        [
                            html.Div(table)           
                        ],
                        className = 'pretty_container three columns'
                    ),
                ],
                className='row'
            )
    ]

    return layout