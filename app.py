#########################
# ICSB School Dashboard #
#########################
# author:    jbetley
# version:  1.03
# date:     5/22/23

## NOTE: Because of the way data is store and presented by IDOE, there are
# cases in which data points need to be manually calculated that the school
# level for data that is stored at the corporation level. Specifically, this
# is an issue for calculating demographic enrollment when there is a school
# that crosses natural grade span splits, e.g., Split Grade K8 and 912 enrollment using
# proportionate split for:
#   Christel House South (CHS/CHWMHS)
#   Circle City Prep (Ele/Mid)

# flask and flask-login #
# https://levelup.gitconnected.com/how-to-setup-user-authentication-for-dash-apps-using-python-and-flask-6c2e430cdb51
# https://community.plotly.com/t/dash-app-pages-with-flask-login-flow-using-flask/69507/38
# https://stackoverflow.com/questions/52286507/how-to-merge-flask-login-with-a-dash-application
# https://python-adv-web-apps.readthedocs.io/en/latest/flask_db2.html

import os
from flask import Flask, url_for, redirect, request, render_template, session, jsonify
from flask_login import login_user, LoginManager, UserMixin, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

import dash
from dash import ctx, dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc

from dotenv import load_dotenv

# load data and global variables
from pages.load_data import school_index, current_academic_year

from pages.load_db import get_financial_data

# from pages.load_db import engine
# This is used solely to generate metric rating svg circles
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"

external_stylesheets = ["https://fonts.googleapis.com/css2?family=Jost:400", FONT_AWESOME]

# NOTE: Cannot get static folder to work (images do not load and give 302 Found error)

server = Flask(__name__, static_folder="static")

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))
server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "users.db"
)
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
server.config.update(SECRET_KEY=os.getenv("SECRET_KEY"))

bcrypt = Bcrypt()

db = SQLAlchemy(server)

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"

# each table in the database needs a class to be created for it
# using the db.Model, all db columns must be identified by name
# and data type. UserMixin provides a get_id method that returns
# the id attribute or raises an exception. Need to either name the
# database attribute 'id' or override the get_id function to return user_id
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text, unique=True)

# load_user is used by login_user, passes the user_id
# and gets the User object that matches that id
@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

# The default is to block all requests unless user is on login page or is authenticated
@server.before_request
def check_login():
    if request.method == "GET":
        if request.path in ["/login"]:
            return
        if current_user:
            if current_user.is_authenticated:
                return
            else:
                for pg in dash.page_registry:
                    if request.path == dash.page_registry[pg]["path"]:
                        session["url"] = request.url

        return redirect(url_for("login"))
    else:
        if current_user:
            if request.path == "/login" or current_user.is_authenticated:
                return
        return jsonify({"status": "401", "statusText": "unauthorized access"})

# Login logic
message = "Invalid username and/or password."

@server.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        # if user is authenticated - redirect to dash app
        if current_user.is_authenticated:
            return redirect("/")

        # otherwise show the login page
        return render_template("login.html", message=message)

    if request.method == "POST":
        if request.form:
            user = request.form["username"]
            password = request.form["password"]

            # Get user_data from the User object matching the provided username
            user_data = User.query.filter_by(username=user).first()

            if user_data:
                # check a hash of the provided password against the hashed password stored in the
                # User object
                if bcrypt.check_password_hash(user_data.password, password):

                    # if True, login the user using the User object
                    login_user(user_data)

                    if "url" in session:
                        if session["url"]:
                            url = session["url"]
                            session["url"] = None
                            return redirect(url)  ## redirect to target url
                    return redirect("/")  ## redirect to home

    # Redirect to login page on error
    return redirect(url_for("login", error=1))

@server.route("/logout", methods=["GET"])
def logout():
    if current_user:
        if current_user.is_authenticated:
            logout_user()
    return render_template("login.html", message="You have been logged out.")

app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    meta_tags=[
    {
        "name": "viewport",
        "content": "width=device-width, initial-scale=1, maximum-scale=1",
    }
],
)

# Dropdown shows single school if school login is used
# It shows all schools if admin login is used.
# NOTE: 'application-state' is a dummy input
@callback(
    Output("charter-dropdown", "options"),
    [Input("application-state", "children")]
)
def set_dropdown_options(app_state):
    # Get the current user id using the current_user proxy,
    # use the ._get_current_object() method to return the
    # underlying object (User)
    authorized_user = current_user._get_current_object()

    # admin user
    if authorized_user.id == 0:
        # use entire list
        charters = school_index[["School Name", "School ID", "School Type"]]

    else:
        # select only the authorized school using the id field of the authorized_user
        # object. need to subtract 1 from id to get correct school from index, because
        # the admin login is at index 0
        charters = school_index.iloc[[(authorized_user.id - 1)]]

    dropdown_dict = dict(zip(charters["School Name"], charters["School ID"]))
    dropdown_list = dict(sorted(dropdown_dict.items()))
    dropdown_options = [{"label": name, "value": id} for name, id in dropdown_list.items()]

    return dropdown_options

# Set default charter dropdown option to the first school in the list (alphanumeric)
@callback(
    Output("charter-dropdown", "value"),
    Input("charter-dropdown", "options")
)
def set_dropdown_value(charter_options):
    return charter_options[0]["value"]

# @callback(
#     Output('where-am-i', 'children'),
#     Input('_pages_location', 'path')
# )
# def where_am_i(page):
#     print(page)
#     return page
from furl import furl
# TODO: NOT WORKING

# https://stackoverflow.com/questions/69913867/get-parameters-from-url-in-dash-python-this-id-is-assigned-to-a-dash-core-compo
@app.callback(Output('content', 'children'),
              [Input('url', 'href')])
def where_am_i(href: str):
    print(href)
    f = furl(href)
    print(f)
    # param1= f.args['param1']
    # param2= f.args['param2']

    return f
                       
# year options are the range of:
#   max = current_academic_year
#   min = the earliest year for which the school has adm (is open)
#   limit = typically a limit of 5 years (currently and
#   temporarily 4 years so that 2018 academic data is not shown)

@callback(
    Output("year-dropdown", "options"),
    Output("year-dropdown", "value"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    # https://community.plotly.com/t/duplicate-callback-outputs-solution-api-discussion/55909/20
)
def set_year_dropdown_options(school, year):

    input_trigger = ctx.args_grouping #.triggered_id
    print(input_trigger)
#TODO: Get Academic Years of Data for Academic Data
#TODO: Get FInancial YEars of Data for Financial/ORg Data
    # Year Dropdown Options
    # TODO: Change to 5 years in 2023
    max_dropdown_years = 4

    financial_data = get_financial_data(school)

    # Empty file could potentially still have 'School Id','School Name', and 'Category'
    # NOTE: should never be a school ID associated with a missing financial db entry,
    # however, we test anyway.
    if len(financial_data) > 3:

        financial_data = financial_data.dropna(axis=1, how='all')
        financial_data.columns = financial_data.columns.astype(str)
        financial_data = financial_data.drop(['School ID','School Name'], axis=1)

        if 'Q' in financial_data.columns[1]:
            financial_data = financial_data.drop(financial_data.columns[[1]],axis = 1)

        adm_years = financial_data[financial_data['Category'].str.contains('ADM Average')]

        school_academic_years = len(adm_years.columns) - 1

    num_dropdown_years = school_academic_years if school_academic_years <= max_dropdown_years else max_dropdown_years

    # subtract 1 total to account for current year in display
    first_available_year = int(current_academic_year) - (num_dropdown_years-1)

    # 'year' represents the State of the year-dropdown when a school is selected.
    # This sets the current year_value equal to: current_academic_year (when app
    # is first opened); current_year state (if the school has available data for
    # that year), or to the next earliest year of academic data that is available
    # for the school

    if year is None:
        year_value = str(current_academic_year)
    elif int(year) < first_available_year:
        year_value = str(first_available_year)
    else:
        year_value = str(year)

    year_options=[
        {"label": str(y), "value": str(y)}
        for y in range(
            first_available_year,
            int(current_academic_year) + 1,
        )
    ]

    return year_options, year_value

app.layout = html.Div(
    [
        dcc.Store(id="dash-session", storage_type="session"),
        # dcc.Location(id='where-am-i', refresh=False),
        dcc.Location(id='url', refresh=False),        
        # dcc.Store(id='where-am-i', storage_type="session"), #data=[{'path':'Path'}]),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.A("logout", href="../logout", className="logout-button"),
                            ],
                            className="bare_container one columns",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Select School:"),
                                    ],
                                    className="dash_label",
                                    id="school_dash_label",
                                ),
                                dcc.Dropdown(
                                    id="charter-dropdown",
                                    style={
                                        "fontFamily": "Roboto, sans-serif",
                                        'color': 'steelblue',

                                    },
                                    multi=False,
                                    clearable=False,
                                    className="school_dash_control",
                                ),
                                # NOTE: Dummy input for dropdown
                                html.Div(id="application-state", style={"display": "none"}),
                            ],
                            className="pretty_container five columns",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Select Year:"),
                                    ],
                                    className="dash_label",
                                    id="year_dash_label",
                                ),
                                dcc.Dropdown(
                                    id="year-dropdown",
                                    style={
                                        "fontFamily": "Roboto, sans-serif",
                                        'color': 'steelblue',
                                    },
                                    multi=False,
                                    clearable=False,
                                    className="year_dash_control",
                                ),
                            ],
                            className="pretty_container three columns",
                        ),
                    ],
                    className="fixed-row",
                ),
            ],
            className="fixed-row",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                dbc.Nav(
                                    [
                                        dbc.NavLink(
                                            page["name"],
                                            href=page["path"],
                                            className="tab",
                                            active="exact",
                                        )
                                        for page in dash.page_registry.values()
                                        if page.get("top_nav")
                                        if page["module"] != "pages.not_found_404"
                                    ],
                                    className="tabs",
                                ),
                            ],
                            className="bare_container twelve columns",
                                style={
                                    "padding": "50px",
                                    "paddingBottom": "60px",
                                    "marginTop": "50px",
                                }
                        ),
                    ],
                    className="row",
                ),
                dash.page_container,
            ],
        )
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)
#    application.run(host='0.0.0.0', port='8080')