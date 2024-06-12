###################
# Print Dashboard #
###################
# author:   jbetley
# rev:     10.31.22

# TODO: https://community.plotly.com/t/exporting-multi-page-dash-app-to-pdf-with-entire-layout/37953/21

import dash
from dash import html, dash_table, Input, Output, State, callback, ctx, dcc
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np

dash.register_page(__name__, path="/print_page", top_nav=True, order=12)

# TODO: SUBNAV still loading briefly


@callback(
    Output("checklist-list", "value"),
    Input("print-button", "n_clicks"),
    [Input("checklist-all", "value")],
    [State("checklist-list", "value")],
    [State("checklist-list", "options")],
)
def select_all(print_button, select_all_value, select_list_value, select_list_options):
    # TODO: why is triggered triggering print?
    if ctx.triggered_id == "checklist-all":
        print_button == 0  # need to reset button or it will trigger when All is selected

        if select_all_value:
            checked = [option["value"] for option in select_list_options]
        else:
            checked = []
    else:
        print(print_button)
        checked = select_list_value

    if print_button > 0:
        if checked:
            print("Printing:")
            print(checked)

    return checked


layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Select Pages to Print:", className="label__header"),
                        dcc.Checklist(
                            id="checklist-all",
                            options=[{"label": "All", "value": "ALL"}],
                            value=[],
                        ),
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
                            ],
                            inline=True,
                            value=[],
                            id="checklist-list",
                        ),
                        html.Div(
                            html.Button(
                                "Print", id="print-button", n_clicks=0, className="btn"
                            ),
                        ),
                    ],
                    className="pretty-container four columns",
                ),
            ],
            className="bare-container--flex--center twelve columns",
        ),
    ],
    id="main-container",
)
