###################
# Print Dashboard #
###################
# author:   jbetley
# rev:     10.31.22

import dash
from dash import html, dash_table, Input, Output, callback, dcc
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np

dash.register_page(__name__, path="/print_page", top_nav=True, order=12)

## Callback ##


@callback(
    Output("selected-value", "value"),
    Input("go-print", "n_clicks"),
    Input("school-checklist", "value"),
)
def print_page(click, checklist):
    if click is None:
        raise PreventUpdate
    selected = "ALL"
    print(click)
    if click:
        selected = checklist

    return selected


label_style = {
    "height": "auto",
    "lineHeight": "1.5em",
    "backgroundColor": "#6783a9",
    "fontSize": "12px",
    "fontFamily": "Roboto, sans-serif",
    "color": "#ffffff",
    "textAlign": "center",
    "fontWeight": "bold",
    "paddingBottom": "5px",
    "paddingTop": "5px",
    "paddingRight": "10px",
    "paddingLeft": "5px",
}
# TODO: Get rid of all subnav buttons when loading print page
layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(
                                    "Select Pages to Print:",
                                    style=label_style,
                                ),
                                html.Button("Print", id="go-print", n_clicks=0),
                            ],
                            # className="bare-container--center four columns row",
                        ),
                    ],
                    className="bare-container--center twelve columns",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Checklist(
                                    options=[
                                        {"label": "About", "value": "AB"},
                                        {
                                            "label": "Financial Information",
                                            "value": "FI",
                                        },
                                        {"label": "Financial Metrics", "value": "FM"},
                                        {"label": "Financial Analysis", "value": "FA"},
                                        {
                                            "label": "Organizational Compliance",
                                            "value": "OC",
                                        },
                                        {
                                            "label": "Academic Information",
                                            "value": "AI",
                                        },
                                        {"label": "Academic Metrics", "value": "AM"},
                                        {"label": "All", "value": "ALL"},
                                    ],
                                    inline=True,
                                    value=["ALL"],
                                    id="school-checklist",
                                ),
                            ],
                            className="bare-container--center four columns row",
                        ),
                        html.Div(id="selected-value"),
                    ],
                    className="bare-container--center twelve columns",
                ),
            ],

        ),
    ],
    id="main-container",
)
