##################################
# ICSB Dashboard - Subnavigation #
##################################
# author:   jbetley
# version:  1.10
# date:     09/10/23

import dash
from dash import html
import dash_bootstrap_components as dbc

# subnav tabs for financial information and academic information
def subnav_academic_analysis():
    return html.Div (
        dbc.Nav(
            [
                dbc.NavLink(
                    page['name'],
                    href=page['path'],
                    className = 'tab',
                    active='partial'
                )
                for page in dash.page_registry.values()
                if page["path"].startswith('/analysis')
            ],
            className='sub-tabs',
            style={"marginTop": "-40px"}
        )
    )

def subnav_academic_type():
    return html.Div(
        dbc.Nav(
            [
                dbc.NavLink(
                    
                    page['name'],
                    href=page['path'],
                    className = 'tab',
                    active='partial'
                )
                for page in dash.page_registry.values()
                if page["path"].startswith("/info")
            ],
            className='sub-tabs',
            # style={"marginTop": "-40px"}
        ),
    )