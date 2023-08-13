##################################
# ICSB Dashboard - Subnavigation #
##################################
# author:   jbetley
# version:  1.03
# date:     5/22/23

import dash
from dash import html
import dash_bootstrap_components as dbc

def subnav_finance():
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
                if page["path"].startswith('/financial')
            ],
            className='sub-tabs',
            style={"marginTop": "-40px"}
        )
    )

def subnav_academic():
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
                if page["path"].startswith("/academic")
            ],
            className='sub-tabs',
            style={"marginTop": "-40px"}
        )
    )