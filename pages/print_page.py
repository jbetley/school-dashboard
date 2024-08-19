###################
# Print Dashboard #
###################
# author:   jbetley
# rev:     08.18.24

# TODO: https://community.plotly.com/t/exporting-multi-page-dash-app-to-pdf-with-entire-layout/37953/21

import dash
from dash import html, dash_table, Input, Output, State, callback, ctx, dcc
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np

from .charts import loading_fig
from .print_layout import create_print_layout

dash.register_page(__name__, path="/print_page", top_nav=True, order=12)


# TODO: SUBNAV still loading briefly
@callback(
    Output("checklist-list", "value"),
    Output("print-layout", "children"),
    # Output("empty-layout", "children"),
    Input("year-dropdown", "value"),
    Input("charter-dropdown", "value"),
    Input("print-button", "n_clicks"),
    [Input("checklist-all", "value")],
    [State("checklist-list", "value")],
    [State("checklist-list", "options")],
)
def print_page(
    year,
    school_id,
    print_button,
    select_all_value,
    select_list_value,
    select_list_options,
):
    print_layout = []

    # TODO: why is triggered triggering print?
    if ctx.triggered_id == "checklist-all":
        print_button == 0  # need to reset button or it will trigger when All is selected

        if select_all_value:
            selected = [option["value"] for option in select_list_options]
        else:
            selected = []
    else:
        selected = select_list_value

    if print_button > 0:
        if selected:
            print(selected)
            print_layout = create_print_layout(year, school_id, selected)

    return selected, print_layout #, empty_layout


layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Select Pages to Print (NOT YET FUNCTIONAL):",
                            className="label__header",
                        ),
                        dcc.Checklist(
                            id="checklist-all",
                            options=[{"label": "All", "value": "all"}],
                            value=[],
                        ),
                        dcc.Checklist(
                            options=[
                                {"label": "About", "value": "about"},
                                {
                                    "label": "Financial Information",
                                    "value": "fininfo",
                                },
                                {"label": "Financial Metrics", "value": "finmetrics"},
                                {"label": "Financial Analysis", "value": "finanalysis"},
                                {
                                    "label": "Organizational Compliance",
                                    "value": "orgcompliance",
                                },
                                {
                                    "label": "Academic Information",
                                    "value": "academicinfo",
                                },
                                {
                                    "label": "Academic Metrics",
                                    "value": "academicmetrics",
                                },
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
        html.Div(
            [
                html.Div(id="print-layout", children=[]),
            ],
            className="bare-container--relative twelve columns",
        ),
        # html.Div(
        #     [
        #         html.Div(id="empty-layout", children=[]),
        #     ],
        #     className="bare-container--relative twelve columns",
        # ),
    ],
    id="main-container",
)
