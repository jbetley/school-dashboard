##################################
# ICSB Dashboard - Subnavigation #
##################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.11
# date:     10/03/23

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
        )
    )

def subnav_academic_information():
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
                if page["path"].startswith("/academic_data")
            ],
        ),
    )

# def subnav_academic_information():
#     return html.Div(
#         dbc.Nav(
#             [
#                 dbc.NavLink(
#                     page['name'],
#                     href=page['path'],
#                     className = 'tab',
#                     active='partial'
#                 )
#                 for page in dash.page_registry.values()
#                 if page["path"].startswith("/info")
#             ],
#         ),
#     )