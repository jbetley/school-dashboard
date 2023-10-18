##################################
# ICSB Dashboard - Subnavigation #
##################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.13
# date:     10/13/23

import dash
from dash import html
import dash_bootstrap_components as dbc


# subnav tabs for analysis_single_year.py and analysis_multi_year.py
def subnav_academic_analysis():
    return html.Div(
        dbc.Nav(
            [
                dbc.NavLink(
                    page["name"], href=page["path"], className="tab", active="partial"
                )
                for page in dash.page_registry.values()
                if page["path"].startswith("/academic_analysis")
            ],
            className="sub-tabs",
        )
    )


# subnav tabs for academic_information.py and academic_information_growth.py
def subnav_academic_information():
    return html.Div(
        dbc.Nav(
            [
                dbc.NavLink(
                    page["name"], href=page["path"], className="tab", active="exact"
                )
                for page in dash.page_registry.values()
                if page["path"].startswith("/academic_info")
            ],
        ),
    )
