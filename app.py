#########################
# ICSB School Dashboard #
#########################
# author:    jbetley
# version:  1.11
# date:     10/03/23

# This is the main application file for the Indiana Charter School Board school
# dashboard. This dashboard consists of ~10 tabs of charts and tables created
# using the plotly dash data visualization libraries. It includes financial,
# operational, and academic data for schools serving all sorts of grade configurations
# in the K-12 and adult space. Currently, all data is stored in a single 30mb sqlite
# database with ~12 tables. One of the future goals of the app is to explore alternative
# ways to combine and store data, although the primary speed hit in the app is in the
# charting library and not in database access. All of the data is public and most of
# the academic data is available (as of 10/2023) on the website of the Indiana Department
# of Education: https://www.in.gov/doe/it/data-center-and-reports/. Financial data is reported
# by each school (on excel workbooks) and pulled into the db using python. Academic
# data comes from dozens of separate csv files produced over many years and presented
# primarily for human readibility, which means that they are messy, inconsistent, and
# often incomplete. All this is to say that a large part of this apps exists to filter,
# clean, validate, and process this data to satisfy a number of configurations. Even
# the exceptions to the exceptions have exceptions.

# I have chosen to structure the app this way rather than spending the considerable effort
# to clean and organize the data on the back-end, because it is inevitable that someone
# else will have to maintain this code at some point, and I have no idea how
# sophisticated their software engineering skills will be. The hope is that I will
# eventually have the code structured in such a way that whomever follows can simply drop an
# 'updated' IDOE academic file into a folder, click a script, have it added to the DB, and 
# have the program read it with no issue. That part is a work in progress. Another option
# would be to get access to IDOE's API for this data. This is also a work in progress. Changing
# to IDOE's API (using ED-FI standard), would be a gamechanger.

# NOTE: Because of the way data is store and presented by IDOE, there are
# cases in which data points need to be manually calculated that the school
# level for data that is stored at the corporation level. Specifically, this
# is an issue for calculating demographic enrollment when there is a school
# that crosses natural grade span splits, e.g., Split Grade K-5, 6-8 and 9-12
# enrollment using proportionate split for:
#   Christel House South (CHS/CHWMHS)
#   Circle City Prep (Ele/Mid)

# The Flask login code was adapted for Pages based on Nader Elshehabi's article:
# https://dev.to/naderelshehabi/securing-plotly-dash-using-flask-login-4ia2
# https://github.com/naderelshehabi/dash-flask-login
# and has been made available under the MIT license.
# (See https://github.com/naderelshehabi/dash-flask-login/blob/main/LICENSE.md)

# This version was updated by Dash community member @jinnyzor. For more info, see:
# https://community.plotly.com/t/dash-app-pages-with-flask-login-flow-using-flask/69507
# https://community.plotly.com/t/dash-app-pages-with-flask-login-flow-using-flask/69507/38
# https://community.plotly.com/t/dash-app-pages-with-flask-login-flow-using-flask/69507/55

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
FONT_FAMILY = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Sans&display=swap"
external_stylesheets = [FONT_FAMILY, FONT_AWESOME]

# NOTE: Cannot get static folder to work (images do not load and give 302 Found error)
server = Flask(__name__, static_folder="static")

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))
server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "icsb-users.db"
)
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
server.config.update(SECRET_KEY=os.getenv("SECRET_KEY"))

bcrypt = Bcrypt()

db = SQLAlchemy(server)

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"

# each table in the user database needs a class to be created for it
# using the db.Model, all db columns must be identified by name
# and data type. UserMixin provides a get_id method that returns
# the id attribute or raises an exception.
class User(UserMixin, db.Model):    # type: ignore
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text, unique=True)
    groupid = db.Column(db.Integer, unique=False)
    fullname = db.Column(db.Integer, unique=True)

    # these properties allow us to access additional fields in the user
    # database - in this case, they are used to populate the user dropdown
    # with associated groups of schools (by group id). fullname is not
    # currently used.
    @property
    def group_id(self):
        return self.groupid

    @property
    def full_name(self):
        return self.fullname
    
# load_user is used by login_user, passes the user_id
# and gets the User object that matches that id
@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

# The default is to block all requests unless user is on login page or is authenticated
@server.before_request
def check_login():
    if request.method == "GET":
        if request.path in ["/login", "/logout"]:
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

@server.route("/login", methods=["GET", "POST"])
def login(message = ""):
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

            message = "Invalid username and/or password."
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
                            return redirect(url)    # redirect to target url
                    return redirect("/")            # redirect to home
                return render_template('login.html', message=message)
            else:
                return render_template('login.html', message=message)
    else:
        if current_user:
            if current_user.is_authenticated:
                return redirect('/')
    
    return render_template('login.html', message=message)
    # return redirect(url_for("login", error=1))

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
    prevent_initial_callbacks="initial_duplicate",
    # compress=False, # testing
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, maximum-scale=1",
        }
    ],
)
        
# Dropdown shows single school if school login is used, shows the
# associated group of schools if a 'network' login is used, and
# shows all schools if admin login is used.
# NOTE: "application-state" is a dummy input
@callback(
    Output("charter-dropdown", "options"),
    [Input("application-state", "children")]
)
def set_dropdown_options(app_state):

    # Get the current user id using the current_user proxy,
    # use the ._get_current_object() method to return the
    # underlying object (User). get the group_id property
    # to determine which schools to include for a network
    # login
    # NOTE: user 0 is admin; users 1-6 are network logins; users 7- are individual schools
    # Groups: CHA (-1); Excel (-2); GEI (-3); PLA (-4); Paramount (-5); Purdue (-6)
    authorized_user = current_user._get_current_object()
    group_id = current_user.group_id

    available_charters = get_school_dropdown_list()

    # admin user
    if authorized_user.id == 0:
        charters = available_charters

    else:
        # check for network login (any group_id != 0)
        if group_id != 0:
            charters = available_charters[available_charters["GroupID"] == str(abs(group_id))]

        else:
            # select only the authorized school using the id field of the authorized_user
            # object. need to subtract 7 to account for Admin and Network Logins (loc 0-6)
            charters = available_charters.iloc[[(authorized_user.id-7)]]

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
            
# year options are the range of: max = current_academic_year; min = the earliest year
#   for which the school has adm (is open); limit = typically a limit of 5 years (currently and
#   temporarily 4 years so that 2018 academic data is not shown)
# NOTE: Input current-page and Output hidden are used to track the currently
# selected url (Tab)
@callback(
    Output("year-dropdown", "options"),
    Output("year-dropdown", "value"),
    Output("hidden", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("current-page", "href"),
)
def set_year_dropdown_options(school_id: str, year: str, current_page: str):

    max_dropdown_years = 5

    current_page = current_page.rsplit("/", 1)[-1]

    selected_school = get_school_index(school_id)    
    school_type = selected_school["School Type"].values[0]

    # source of available years depends on selected tab (guest schools do not have
    # financial data)
    if "academic" in current_page or selected_school["Guest"].values[0] == "Y":
        years = get_academic_dropdown_years(school_id,school_type)

    elif "financial_analysis" in current_page:
        years = get_financial_analysis_dropdown_years(school_id)

    else:
        years = get_financial_info_dropdown_years(school_id)

# Currently both financial_analysis_dropdown and financial_info_dropdown are the same - they both
# reads financial_data and returns a list of Year column names for each year for which ADM Average
# is greater than "0"     

    # set year_value and year_options
    number_of_years_to_display = len(years) if len(years) <= max_dropdown_years else max_dropdown_years
    dropdown_years = years[0:number_of_years_to_display]
    first_available_year = dropdown_years[0]
    earliest_available_year = dropdown_years[-1]

    # "year" represents the State of the year-dropdown when a school is selected.
    # Current year_value is set to:
    #   1) current_academic year (when app is first opened);
    #   2) the earliest year for which the school has data (if the selected year is earlier
    #       than the first year of available data);
    #   3) the latest year for which the school has data (if the selected year is later
    #       than the first year of available data); or
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
        raise Exception("There is simply no way that you can be seeing this error message.") # except i saw it once
    
    year_options=[
        {"label": str(y), "value": str(y)}
        for y in dropdown_years
    ]

    return year_options, year_value, current_page

# app.layout = html.Div(    # NOTE: Test to see effect of layout as function vs. variable
def layout():
    return html.Div(
        [
        # the next two components are used by the year dropdown callback to determine the current url
        dcc.Location(id="current-page", refresh=False),
        html.Div(id="hidden", style={"display": "none"}),
        html.Div(
            [
                html.Div(
                    [
                        
                        html.Div(
                            [
                                html.A("logout", href="../logout", className="logout-button no-print"),
                                   
                            ],
                            className="bare-container--flex--center one columns",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Select School:"),
                                    ],
                                    className="dash-label",
                                    id="charter-dropdown-label",
                                ),
                                dcc.Dropdown(
                                    id="charter-dropdown",
                                    multi=False,
                                    clearable=False,
                                    className="charter-dropdown-control",
                                ),
                                # Dummy input for dropdown
                                html.Div(id="application-state", style={"display": "none"}),
                            ],
                            className="bare-container--slim four columns no-print",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Select Year:"),
                                    ],
                                    className="dash-label",
                                    id="year-dropdown-label",
                                ),
                                dcc.Dropdown(
                                    id="year-dropdown",
                                    multi=False,
                                    clearable=False,
                                    className="year-dropdown-control",
                                ),
                            ],
                            className="bare-container--slim two columns no-print",
                        ),
                    ],
                    className="row--fixed--top",
                ),
            ],
            className="bare-container--flex twelve columns",
        ),
        html.Div(
            [
                html.Div(
                    [                
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dbc.Nav(
                                            [
                                                dbc.NavLink(
                                                    "About",
                                                     href="/",
                                                     className="tab",
                                                     active="exact"
                                                ),
                                                dbc.NavLink(
                                                    "Financial Information",
                                                     href="/financial_information",
                                                     className="tab",
                                                     active="exact"
                                                ),
                                                dbc.NavLink(
                                                    "Financial Metrics",
                                                     href="/financial_metrics",
                                                     className="tab",
                                                     active="exact"
                                                ),
                                                dbc.NavLink(
                                                    "Financial Analysis",
                                                     href="/financial_analysis",
                                                     className="tab",
                                                     active="exact"
                                                ),
                                                dbc.NavLink(
                                                    "Organizational Compliance",
                                                     href="/organizational_compliance",
                                                     className="tab",
                                                     active="exact"
                                                ),
                                                # hardcoding this instead of using a loop so that we
                                                # can manually add this break
                                                html.Br(),                                                
                                                html.Div(style={"marginTop": "17px"}),
                                                dbc.NavLink(
                                                    "Academic Information",
                                                     href="/academic_information",
                                                     className="tab",
                                                     active="exact"
                                                ),                                                
                                                dbc.NavLink(
                                                    "Academic Metrics",
                                                     href="/academic_metrics",
                                                     className="tab",
                                                     active="exact"
                                                ),
                                                dbc.NavLink(
                                                    "Academic Analysis",
                                                     href="/analysis_single_year",
                                                     className="tab",
                                                     active="exact"
                                                ),
                                            #     dbc.NavLink(
                                            #         page["name"],
                                            #         href=page["path"],
                                            #         className="tab",
                                            #         active="exact",
                                            #     )
                                            #     for page in dash.page_registry.values()
                                            #     if page.get("top_nav")
                                            #     if page["module"] != "pages.not_found_404"
                                            ],
                                            className="tabs",
                                        ),
                                    ],
                                    className="nav-container twelve columns", 
                                ),
                            ],
                            className="row",
                        ),
                        html.Hr(),
                    ],
                    className="no-print",
                ),                
                dash.page_container,
            ],
        )
    ],
)

# testing layout as a function - not sure its faster
app.layout = layout 

if __name__ == "__main__":
    app.run_server(debug=True)
#    application.run(host="0.0.0.0", port="8080")