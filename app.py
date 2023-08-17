#########################
# ICSB School Dashboard #
#########################
# author:    jbetley
# version:  1.09
# date:     08/13/23

# NOTE: Because of the way data is store and presented by IDOE, there are
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
from dotenv import load_dotenv

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

from pages.load_data import get_school_index, get_academic_dropdown_years, get_financial_info_dropdown_years, \
    get_school_dropdown_list, get_financial_analysis_dropdown_years

# Used to generate metric rating svg circles
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"

external_stylesheets = ["https://fonts.googleapis.com/css2?family=Jost:400", FONT_AWESOME]
# external_stylesheets = ["https://fonts.googleapis.com/css2?family=Noto+Sans&display=swap", FONT_AWESOME]

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
# the id attribute or raises an exception.
class User(UserMixin, db.Model):    # type: ignore
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
    # compress=False, # testing
    meta_tags=[
    {
        "name": "viewport",
        "content": "width=device-width, initial-scale=1, maximum-scale=1",
    }
],
)

# Dropdown shows single school if school login is used
# shows all schools if admin login is used.
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

    available_charters = get_school_dropdown_list()
    
    # admin user
    if authorized_user.id == 0:
        # use entire list
        charters = available_charters

    else:
        # select only the authorized school using the id field of the authorized_user
        # object. need to subtract 1 from id to get correct school from index, because
        # the admin login is at index 0
        charters = available_charters.iloc[[(authorized_user.id - 1)]]

    dropdown_dict = dict(zip(charters["SchoolName"], charters["SchoolID"]))
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
            
# year options are the range of:
#   max = current_academic_year
#   min = the earliest year for which the school has adm (is open)
#   limit = typically a limit of 5 years (currently and
#   temporarily 4 years so that 2018 academic data is not shown)
# NOTE: Input current-page and Output hidden are used to track the currently
# selected url (Tab)
@callback(
    Output("year-dropdown", "options"),
    Output("year-dropdown", "value"),
    Output('hidden', 'children'),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input('current-page', 'href'),
)
def set_year_dropdown_options(school_id: str, year: str, current_page: str):

    max_dropdown_years = 5

    current_page = current_page.rsplit('/', 1)[-1]

    selected_school = get_school_index(school_id)    
    school_type = selected_school['School Type'].values[0]

    # source of available years depends on selected tab
    if 'academic' in current_page:
        years = get_academic_dropdown_years(school_id,school_type)

    elif 'financial_analysis' in current_page:
        years = get_financial_analysis_dropdown_years(school_id)

    else:
        years = get_financial_info_dropdown_years(school_id)

#TODO: Account for situation where fin_anal year is 2022 but school actually has 2023 data - not sure way to do this
# TODO: TBH I have no idea what the issue is here - need to revisit.
# Currently both financial_analysis_dropdown and financial_info_dropdown are the same - they both
# reads financial_data and returns a list of Year column names for each year for which ADM Average
# is greater than '0'     

    # set year_value and year_options
    number_of_years_to_display = len(years) if len(years) <= max_dropdown_years else max_dropdown_years
    dropdown_years = years[0:number_of_years_to_display]
    first_available_year = dropdown_years[0]
    earliest_available_year = dropdown_years[-1]

    # 'year' represents the State of the year-dropdown when a school is selected.
    # Current year_value is set to:
    #   1) current_academic year (when app is first opened);
    #   2) the earliest_available_year (if the selected year is earlier
    #       than the first year of available data);
    #   3) the first_available_year (if the selected year is later
    #       than the first year of available data);); or
    #   4) the selected year.
    if year is None:
        year_value = str(first_available_year)
    
    elif int(year) < int(earliest_available_year):
        year_value = str(earliest_available_year)

    elif int(year) > int(first_available_year):
        year_value = str(first_available_year)

    else:
        year_value = str(year)

    if not dropdown_years:
        raise Exception("There is simply no way that you can be seeing this error message.")
    
    year_options=[
        {"label": str(y), "value": str(y)}
        for y in dropdown_years
    ]

    return year_options, year_value, current_page

# app.layout = html.Div(    # NOTE: Test to see if it impacts speed
def layout():
    return html.Div(
    [
        dcc.Store(id="dash-session", storage_type="session"),

        # the next two components are used by the year dropdown callback to determine the current url
        dcc.Location(id='current-page', refresh=False),
        html.Div(id='hidden', style={"display": "none"}),
        
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.A("logout", href="../logout", className="logout-button"),
                            ],
                            className="bare_container_center one columns",
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
                                # Dummy input for dropdown
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
                            className="bare_container_center twelve columns",
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

app.layout = layout # testing layout as a function - not sure its faster

if __name__ == "__main__":
    app.run_server(debug=True)
# #    application.run(host='0.0.0.0', port='8080')