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
import json
import pandas as pd
import numpy as np

# from app import app
# np.warnings.filterwarnings('ignore')
# dash.register_page(__name__, top_nav=True, order=8)

## Callback ##
@callback(
    Output('ptable-financial-information', 'children'),
    Output('ptable-financial-metrics', 'children'),
    Output('ptable-financial-indicators', 'children'),
    Output('ptable-container-11ab', 'children'),
    Output('pdisplay-attendance', 'style'),
    Output('ptable-container-11cd', 'children'),
    Output('ptable-container-14ab', 'children'),
    Output('ptable-container-14cd', 'children'),
    Output('ptable-container-14ef', 'children'),
    Output('ptable-container-14g', 'children'),
    Output('ptable-container-15abcd', 'children'),
    Output('ptable-container-16ab', 'children'),
    Output('ptable-container-16cd', 'children'),
    Output('pdisplay-k8-metrics', 'style'),
    Output('ptable-container-17ab', 'children'),
    Output('ptable-container-17cd', 'children'),
    Output('pdisplay-hs-metrics', 'style'),
    Output('ptable-container-ahs-113', 'children'),
    Output('ptable-container-ahs-1214', 'children'),    
    Output('pdisplay-ahs-metrics', 'style'),
    Output('ptable-container-empty', 'children'),
    Output('pdisplay-empty-table', 'style'),
    Output('ptable-org-compliance', 'children'),
    Input('charter-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    Input('dash-session', 'data')
)
def print_page(school, year, data):
    if not school:
        raise PreventUpdate

label_style = {
    'height': 'auto',
    'lineHeight': '1.5em',
    'backgroundColor': '#6783a9',
    'fontSize': '12px',
    'fontFamily': 'Roboto, sans-serif',
    'color': '#ffffff',
    'textAlign': 'center',
    'fontWeight': 'bold',
    'paddingBottom': '5px',
    'paddingTop': '5px'
}

layout = html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Select Pages to Print:", style=label_style),
                                html.Div(
                                    dcc.Checklist(
                                        options=[
                                            {'label': 'About', 'value': 'AB'},
                                            {'label': 'Financial Information', 'value': 'FI'},
                                            {'label': 'Financial Metrics', 'value': 'FM'},
                                            {'label': 'Financial Analysis', 'value': 'FA'},
                                            {'label': 'Organizational Compliance', 'value': 'OC'},
                                            {'label': 'Academic Information', 'value': 'AI'},
                                            {'label': 'Academic Metrics', 'value': 'AM'},
                                            {'label': 'All', 'value': 'ALL'},                                            
                                        ],
                                        value=['ALL']
                                        ),
                                ),
                            ],
                            className = 'pretty_container twelve columns',
                        ),
                    ],
                    className = 'bare_container twelve columns',
                ),
        ],
        id='mainContainer',
        style={
            'display': 'flex',
            'flexDirection': 'column'
        }
)