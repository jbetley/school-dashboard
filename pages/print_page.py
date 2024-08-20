###################
# Print Dashboard #
###################
# author:   jbetley
# rev:     08.18.24

# TODO: https://community.plotly.com/t/exporting-multi-page-dash-app-to-pdf-with-entire-layout/37953/21

import dash
from dash import html, dash_table, Input, Output, State, callback, ctx, dcc

# from dash.dash_table import FormatTemplate
# from dash.dash_table.Format import Format, Scheme, Sign
# from dash.exceptions import PreventUpdate
# import pandas as pd
# import numpy as np

from .charts import loading_fig
from .print_layout import (
    create_about_layout,
    create_fininfo_layout,
    create_finmetrics_layout,
    create_finanalysis_layout,
    create_orgcompliance_layout,
    create_academicinfo_layout,
    create_academicmetrics_layout,
)

dash.register_page(__name__, path="/print_page", top_nav=True, order=12)


# TODO: SUBNAV still loading briefly
@callback(
    Output("checklist-list", "value"),
    Output("about-layout", "children"),
    Output("academicinfo-layout", "children"),
    Output("fininfo-layout", "children"),
    Output("finmetrics-layout", "children"),
    Output("finanalysis-layout", "children"),
    Output("orgcompliance-layout", "children"),
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
    about_layout = []
    academicinfo_layout = []
    fininfo_layout = []
    finmetrics_layout = []
    finanalysis_layout = []
    orgcompliance_layout = []
    # all_container = {"display": "none"}
    # about_container = {"display": "none"}
    # fininfo_container = {"display": "none"}
    # finmetrics_container = {"display": "none"}
    # finanalysis_container = {"display": "none"}
    # orgcompliance_container = {"display": "none"}
    # academicinfo_container = {"display": "none"}
    # academicmetrics_container = {"display": "none"}
    # # empty_container = {"display": "block"}

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

            if "all" in selected:
                about_layout = create_about_layout(year, school_id)
                fininfo_layout = create_fininfo_layout(year, school_id)
                finmetrics_layout = create_finmetrics_layout(year, school_id)
                finanalysis_layout = create_finanalysis_layout(year, school_id)
                orgcompliance_layout = create_orgcompliance_layout(year, school_id)
                academicinfo_layout = create_academicinfo_layout(year, school_id)
                academicmetrics_layout = create_academicmetrics_layout(year, school_id)

            else:
                if "about" in selected:
                    about_layout = create_about_layout(year, school_id)

                if "fininfo" in selected:
                    fininfo_layout = create_fininfo_layout(year, school_id)

                if "finmetrics" in selected:
                    finmetrics_layout = create_finmetrics_layout(year, school_id)

                if "finanalysis" in selected:
                    finanalysis_layout = create_finanalysis_layout(year, school_id)

                if "orgcompliance" in selected:
                    orgcompliance_layout = create_orgcompliance_layout(year, school_id)

                if "academicinfo" in selected:
                    academicinfo_layout = create_academicinfo_layout(year, school_id)

                if "academicmetrics" in selected:
                    academicmetrics_layout = create_academicmetrics_layout(
                        year, school_id
                    )

    return (
        selected,
        about_layout,
        academicinfo_layout,
        fininfo_layout,
        finmetrics_layout,
        finanalysis_layout,
        orgcompliance_layout,  # , empty_layout
    )

# TODO: Fix layout error
layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Select Page(s) to Print:",
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
                html.Div(id="about-layout", children=[]),
                html.Div(id="academicinfo-layout", children=[]),
                html.Div(id="fininfo-layout", children=[]),
                html.Div(id="finmetrics-layout", children=[]),
                html.Div(id="finanalysis-layout", children=[]),
                html.Div(id="orgcompliance-layout", children=[]),
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
