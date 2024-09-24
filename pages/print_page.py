###################
# Print Dashboard #
###################
# author:   jbetley
# rev:     08.18.24

import dash

from dash import html, Input, Output, State, callback, clientside_callback, ctx, dcc

import dash_bootstrap_components as dbc
import json

from .load_data import get_school_index

from .print_layout import (
    create_about_layout,
    create_fininfo_layout,
    create_finmetrics_layout,
    # create_finanalysis_layout,
    create_orgcompliance_layout,
    create_academicinfo_layout,
    create_academicmetrics_layout,
)

dash.register_page(__name__, path="/print_page", top_nav=True, order=12)

# https://dash.plotly.com/advanced-callbacks (for: dash 2.16)

# https://community.plotly.com/t/show-spinner-in-dbc-button-via-client-side-callback/81048
clientside_callback(
    """
    function updateLoadingState(n_clicks) {
        return ["""
    + json.dumps(dbc.Spinner(size="sm").to_plotly_json())
    + """, " Generating Layout"] 
    }
    """,
    Output("print-button", "children", allow_duplicate=True),
    Input("print-button", "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output("checklist-list", "value"),
    Output("about-layout", "children"),
    Output("academicinfo-layout", "children"),
    Output("academicmetrics-layout", "children"),
    Output("fininfo-layout", "children"),
    Output("finmetrics-layout", "children"),
    Output("orgcompliance-layout", "children"),
    Output("print-button", "children"),
    Output("schoolname-layout", "children"),
    Input("print-button", "n_clicks"),
    Input("year-dropdown", "value"),
    Input("charter-dropdown", "value"),
    [Input("checklist-all", "value")],
    [State("checklist-list", "value")],
    [State("checklist-list", "options")],
    prevent_initial_call=True,
)
def generate_print_page(
    print_button,
    year,
    school_id,
    select_all_value,
    select_list_value,
    select_list_options,
):
    about_layout = []
    academicinfo_layout = []
    academicmetrics_layout = []
    fininfo_layout = []
    finmetrics_layout = []
    orgcompliance_layout = []
    schoolname_layout = []

    selected_school = get_school_index(school_id)
    school_name = selected_school["School Name"].values[0]

    if ctx.triggered_id == "checklist-all":
        print_button = 0  # need to reset button or it will trigger when All is selected

        if select_all_value:
            selected = [option["value"] for option in select_list_options]
        else:
            selected = []
    else:
        selected = select_list_value

    if print_button > 0:
        if selected:
            school_name = "ICSB Academic Dashboard for " + school_name
            schoolname_layout = [
                html.Label(
                    school_name,
                    className="school-name-label__header",
                    # style={"marginTop": "10px"},
                ),
            ]

            if "all" in selected:
                about_layout = create_about_layout(year, school_id)
                academicinfo_layout = create_academicinfo_layout(year, school_id)
                academicmetrics_layout = create_academicmetrics_layout(year, school_id)
                fininfo_layout = create_fininfo_layout(year, school_id)
                finmetrics_layout = create_finmetrics_layout(year, school_id)
                orgcompliance_layout = create_orgcompliance_layout(year, school_id)

            else:
                if "about" in selected:
                    about_layout = create_about_layout(year, school_id)

                if "academicinfo" in selected:
                    academicinfo_layout = create_academicinfo_layout(year, school_id)

                if "academicmetrics" in selected:
                    academicmetrics_layout = create_academicmetrics_layout(
                        year, school_id
                    )

                if "fininfo" in selected:
                    fininfo_layout = create_fininfo_layout(year, school_id)

                if "finmetrics" in selected:
                    finmetrics_layout = create_finmetrics_layout(year, school_id)

                if "orgcompliance" in selected:
                    orgcompliance_layout = create_orgcompliance_layout(year, school_id)

    return (
        selected,
        about_layout,
        academicinfo_layout,
        academicmetrics_layout,
        fininfo_layout,
        finmetrics_layout,
        orgcompliance_layout,
        "Generate Layout",
        schoolname_layout,
    )


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
                                    "label": "Academic Metrics",
                                    "value": "academicmetrics",
                                },
                                {
                                    "label": "Academic Information",
                                    "value": "academicinfo",
                                },
                                {"label": "Financial Metrics", "value": "finmetrics"},
                                {"label": "Financial Information", "value": "fininfo"},
                                {
                                    "label": "Organizational Compliance",
                                    "value": "orgcompliance",
                                },
                            ],
                            inline=True,
                            value=[],
                            id="checklist-list",
                        ),
                        html.Div(
                            dbc.Button(
                                children=["Generate Layout"],
                                id="print-button",
                                n_clicks=0,
                                className="btn",
                            ),
                        ),
                    ],
                    className="pretty-container four columns no-print",
                ),
            ],
            className="bare-container--flex--center twelve columns",
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Loading(
                            id="loading",
                            type="circle",
                            fullscreen=False,  # True,
                            style={
                                "position": "static",  # "absolute",
                                "top": "20px",
                                "alignSelf": "start",  # "center",
                                "backgroundColor": "#F2F2F2",
                            },
                            children=[
                                html.Div(id="schoolname-layout", children=[]),
                                html.Div(id="about-layout", children=[]),
                                html.Div(id="academicmetrics-layout", children=[]),
                                html.Div (
                                    [
                                        html.Div(id="academicinfo-layout", children=[]),
                                    ],
                                    className="pagebreak",
                                ),
                                html.Div (
                                    [                                
                                        html.Div(id="finmetrics-layout", children=[]),
                                    ],
                                    className="pagebreak",
                                ),                                
                                html.Div(id="fininfo-layout", children=[]),
                                html.Div(id="orgcompliance-layout", children=[]),
                            ],
                        )
                    ]
                )
            ],
            className="bare-container--relative twelve columns",
        ),
    ],
    id="main-container",
)
