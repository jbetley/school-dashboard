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
from dash import dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from collections import OrderedDict
import pandas as pd
import json
import numpy as np
import itertools
from dotenv import load_dotenv

# local functions
from pages.calculations import set_academic_rating, calculate_percentage, \
    calculate_difference

# load data and global variables
from pages.load_data import school_index, school_academic_data_k8, all_academic_data_hs, \
    corporation_rates, all_demographic_data, ethnicity, subgroup, grades, subject, current_academic_year

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
    # Charter Dropdown Options    
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

    # Year Dropdown Options
    # TODO: Change to 5 years in 2023
    max_dropdown_years = 4
  
    # count the number of years that a school has ADM data, ignoring
    # any most recent years with a 'Q#' prefix (indicating quarterly
    # data)
    finance_file = 'data/F-' + school_index.loc[school_index["School ID"] == school]['School Name'].values[0] + '.csv'

    if os.path.isfile(finance_file):
        financial_data = pd.read_csv(finance_file)

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
        year_value = current_academic_year
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

# Load data into dcc.Store ('dash-session')
@app.callback(
    Output("dash-session", "data"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
)
def load_data(school, year):
    if not school:
        raise PreventUpdate

    # 'year' is the selected year, it will be equal to None whenever 
    # the user selects a year and then switches to a school that has
    # no data for that year - at which point we reset it to the current_year
    if year is None:
        year = current_academic_year

    ### School Information
    school_info = school_index.loc[school_index["School ID"] == school]
    school_info_dict = school_info.to_dict()

    excluded_academic_years = int(current_academic_year) - int(year)

    # 'excluded years' is a list of YYYY strings (all years more
    # recent than selected year) that can be used to filter data
    # that should not be displayed
    excluded_years = []
    for i in range(excluded_academic_years):
        excluded_year = int(current_academic_year) - i
        excluded_years.append(str(excluded_year))

    # store current year separately for demographic data because
    # demographic data exists for 2020
    demographic_year = str(year)

    ## Demographic data
    # Get school demographic data for all years
    school_demographic_data = all_demographic_data.loc[
        all_demographic_data["School ID"] == school
    ]

    if len(school_demographic_data.index) == 0:
        school_demographic_selected_year_dict = {}
        corp_demographic_selected_year_dict = {}
        school_letter_grades_json = {}
        attendance_data_json = {}
        attendance_data_metrics_json = {}

    else:
        # get corp demographic data for all years
        corp_demographic_data = all_demographic_data.loc[
            all_demographic_data["School ID"] == school_info["GEO Corp"].values[0]
        ]

        # get school demographic data for selected year and save to dict
        school_demographic_selected_year = school_demographic_data.loc[
            school_demographic_data["Year"] == demographic_year
        ]
        school_demographic_selected_year_dict = (
            school_demographic_selected_year.to_dict()
        )

        # get corp demographic data for selected year and save to dict
        corp_demographic_selected_year = corp_demographic_data.loc[
            corp_demographic_data["Year"] == demographic_year
        ]
        corp_demographic_selected_year_dict = corp_demographic_selected_year.to_dict()

        # remove 'excluded years' from full demographic data sets
        if excluded_years:
            corp_demographic_data = corp_demographic_data[
                ~corp_demographic_data["Year"].isin(excluded_years)
            ]
            school_demographic_data = school_demographic_data[
                ~school_demographic_data["Year"].isin(excluded_years)
            ]

        ## State and Federal Letter Grades
        school_letter_grades = school_demographic_data[["State Grade", "Federal Rating", "Year"]]

        # transpose for display
        school_letter_grades = (
            school_letter_grades.set_index("Year")
            .T.rename_axis("Category")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        # ensure json is empty if letter grades df only has one column ('Category')
        if len(school_letter_grades.columns) == 1:
            school_letter_grades_json = {}
        else:
            school_letter_grades_dict = school_letter_grades.to_dict(into=OrderedDict)
            school_letter_grades_json = json.dumps(school_letter_grades_dict)

        # Attendance Rate Data
        school_attendance_rate = school_demographic_data[["Year", "Avg Attendance"]]
        corp_attendance_rate = corp_demographic_data[["Year", "Avg Attendance"]]

        attendance_merge = school_attendance_rate.merge(
            corp_attendance_rate, on="Year", how="left"
        )
        attendance_merge.columns = ['Year','School', 'Corp Average']

        # calculate difference
        attendance_merge['+/-'] = attendance_merge['School'].astype(float) - attendance_merge['Corp Average'].astype(float)

        # set year as index and unstack the dataframe,
        # unstack returns a series having a new level of column labels whose
        # inner-most level consists of the pivoted index ('Year') levels
        # use to_frame() to convert to df and then transpose
        attendance_merge = attendance_merge.set_index(['Year'])
        attendance_data = attendance_merge.unstack().to_frame().sort_index(level=1).T
        attendance_data.columns = attendance_data.columns.map(lambda x: f'{x[1]}{x[0]}')

        # reverse the order of the columns and add Category
        attendance_data = attendance_data[attendance_data.columns[::-1]]
        attendance_data.insert(0, "Category", "1.1.a. Attendance Rate")

        # save attendance_data to json
        attendance_data_dict = attendance_data.to_dict(into=OrderedDict)
        attendance_data_json = json.dumps(attendance_data_dict)

        # use the final data to calculate attendance data metrics
        attendance_data_metrics = attendance_data.copy()

        # threshold limits for rating calculations
        attendance_limits = [
            0,
            -0.01,
            -0.01,
        ]

        # NOTE: Calculates and adds an accountability rating ('MS', 'DNMS', 'N/A', etc)
        # as a new column to existing dataframe:
        #   1) the loop ('for i in range(attendance_data_metrics.shape[1], 1, -3)')
        #   counts backwards by -3, beginning with the index of the last column in
        #   the dataframe ('attendance_data_metrics.shape[1]') to '1' (actually '2'
        #   as range does not include the last number). These are indexes, so the
        #   loop stops at the third column (which has an index of 2);
        #   2) for each step, the code inserts a new column, at index 'i'. The column
        #   header is a string that is equal to 'the year (YYYY) part of the column
        #   string (attendance_data_metrics.columns[i-1])[:7 - 3]) + 'Rating' + 'i'
        #   (the value of 'i' doesn't matter other than to differentiate the columns) +
        #   the accountability value, a string returned by the set_academic_rating() function.
        #   3) the set_academic_rating() function calculates an 'accountability rating'
        #   ('MS', 'DNMS', 'N/A', etc) taking as args:
        #       i) the 'value' to be rated. this will be from the 'School' column, if
        #       the value itself is rated (e.g., iread performance), or the difference
        #       ('+/-') column, if there is an additional calculation required (e.g.,
        #       year over year or compared to corp);
        #       ii) a list of the threshold 'limits' to be used in the calculation; and
        #       iii) an integer 'flag' which tells the function which calculation to use.
        [
            attendance_data_metrics.insert(
                i,
                str(attendance_data_metrics.columns[i - 1])[: 7 - 3]
                + "Rate"
                + str(i),
                attendance_data_metrics.apply(
                    lambda x: set_academic_rating(
                        x[attendance_data_metrics.columns[i - 1]], attendance_limits, 3
                    ),
                    axis=1,
                ),
            )
            for i in range(attendance_data_metrics.shape[1], 1, -3)
        ]

        # save attendance metric data to json
        attendance_data_metrics_dict = attendance_data_metrics.to_dict(into=OrderedDict)
        attendance_data_metrics_json = json.dumps(attendance_data_metrics_dict)

    ## Financial Information
    # All schools will have a school finance file
    # Network schools (not 'None' in Network column) will also have network finance file

    # NOTE: school finances are currently accessed as separate csv files both because of
    # the way the financial data is processed and stored (still needs to be
    # human readable) and because there may be both school and network information.

    finance_file = 'data/F-' + school_info['School Name'].values[0] + '.csv'
    
    if os.path.isfile(finance_file):
        financial_data = pd.read_csv(finance_file)
        school_finance_dict = financial_data.to_dict(into=OrderedDict)
        school_finance_json = json.dumps(school_finance_dict)
    else:
        school_finance_json = {}

    if school_info['Network'].values[0] != 'None':
        # network_finance_file = 'data/F-' + school_info['Network'].values[0] + '.csv'
        # network_financial_data = pd.read_csv(network_finance_file)
        # network_finance_dict = network_financial_data.to_dict(into=OrderedDict)
        # network_finance_json = json.dumps(network_finance_dict)
        network_finance_json = {}        
    else:
        network_finance_json = {}

    # K8 Academic Data
    if (
        school_info["School Type"].values[0] == "K8"
        or school_info["School Type"].values[0] == "K12"
    ):
        if school_info["School Type"].values[0] == "K8":
            hs_academic_data_json = {}
            ahs_metrics_data_json = {}
            combined_grad_metrics_json = {}

        # get school academic data
        filtered_school_academic_data_k8 = school_academic_data_k8[
            ~school_academic_data_k8["Year"].isin(excluded_years)
        ]
        k8_school_data = filtered_school_academic_data_k8.loc[
            filtered_school_academic_data_k8["School ID"] == school
        ]

        if len(k8_school_data.index) == 0:
            k8_academic_data_json = {}
            year_over_year_values_json = {}
            diff_to_corp_json = {}
            iread_data_json = {}
            academic_analysis_corp_dict = {}

        else:
            # School Corp proficiency rates are keyed to the selected school's GEO Corp
            # value in index).
            # NOTE: corporation_rate values will not always be the same as aggregated
            # individual school values (e.g., School A, School B, and School C are in
            # School Corporation 1- but the value for Category Z for School Corporation
            # 1 will not necessarily be equal to the combined values (or average value) of
            # Schools A-C). This is because certain inclusion metrics are calculated 
            # differently at the Corporation Level. All things being equal, the corporation_rate
            # values will always be more accurate for Corporation level data.
            k8_corp_rates_filtered = corporation_rates[
                ~corporation_rates["Year"].isin(excluded_years)
            ]
            k8_corp_rate_filtered = k8_corp_rates_filtered.loc[
                (k8_corp_rates_filtered["Corp ID"] == school_info["GEO Corp"].values[0])
            ]

            k8_school_info = k8_school_data[["School Name"]].copy()

            # filter to remove columns not used in calculations (need
            # this in order to ensure columns match). Need to keep
            # School ID and School Name only for Academic Analysis
            # data tab purposes
            k8_school_data = k8_school_data.filter(
                regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",
                axis=1,
            )
            k8_corp_rate_filtered = k8_corp_rate_filtered.filter(
                regex=r"Total Tested$|Total Proficient$|IREAD Pass N|IREAD Test N|Year",
                axis=1,
            )

            # equalize the two dataframes by comparing corp columns to school columns

            # valid_mask returns a boolean series of columns where column is true
            # if any element in the column is not equal to null
            valid_mask = ~pd.isnull(k8_school_data[k8_school_data.columns]).all()

            # create list of columns with no date (used in loop below)
            # missing_mask returns boolean series of columns where column
            # is true if all elements in the column are equal to null
            missing_mask = pd.isnull(k8_school_data[k8_school_data.columns]).all()
            missing_cols = k8_school_data.columns[missing_mask].to_list()

            # use valid_mask keep only columns that have at least one value
            k8_school_data = k8_school_data[k8_school_data.columns[valid_mask]]
            k8_corp_rate_filtered = k8_corp_rate_filtered[
                k8_corp_rate_filtered.columns[valid_mask]
            ]

            # change corp_rate values to numeric as it does not have
            # mixed data types (the function used to calculate k8_school
            # difference values anticipates mixed dtypes)
            for col in k8_corp_rate_filtered.columns:
                k8_corp_rate_filtered[col] = pd.to_numeric(
                    k8_corp_rate_filtered[col], errors="coerce"
                )

            # reset index as 'Year' for corp_rate data
            k8_corp_rate_filtered = k8_corp_rate_filtered.set_index("Year")

            # iterate over (non missing) columns, calculate the average,
            # and store in a new column
            k8_corp_rate_data = k8_corp_rate_filtered.copy()

            categories = ethnicity + subgroup + grades + ["School Total"]

            for s in subject:
                for c in categories:
                    new_col = c + "|" + s + " Proficient %"
                    proficient = c + "|" + s + " Total Proficient"
                    tested = c + "|" + s + " Total Tested"

                    if proficient not in missing_cols:
                        k8_school_data[new_col] = calculate_percentage(
                            k8_school_data[proficient], k8_school_data[tested]
                        )
                        k8_corp_rate_data[new_col] = (
                            k8_corp_rate_data[proficient] / k8_corp_rate_data[tested]
                        )

            # replace 'Totals' with calculation taking the masking step into account
            # The masking step above removes grades from the corp_rate dataframe
            # that are not also in the school dataframe (e.g., if school only has data
            # for grades 3, 4, & 5, only those grades will remain in corp_rate df).
            # However, the 'Corporation Total' for proficiency in a subject is
            # calculated using ALL grades. So we need to recalculate the 'Corporation Total'
            # rate manually to ensure it includes only the included grades.
            adjusted_corp_total_math_proficient = k8_corp_rate_data.filter(
                regex=r"Grade.+?Math Total Proficient"
            )
            adjusted_corp_total_math_tested = k8_corp_rate_data.filter(
                regex=r"Grade.+?Math Total Tested"
            )

            k8_corp_rate_data[
                "School Total|Math Proficient %"
            ] = adjusted_corp_total_math_proficient.sum(
                axis=1
            ) / adjusted_corp_total_math_tested.sum(
                axis=1
            )

            adjusted_corp_total_ela_proficient = k8_corp_rate_data.filter(
                regex=r"Grade.+?ELA Total Proficient"
            )
            adjusted_corp_total_ela_tested = k8_corp_rate_data.filter(
                regex=r"Grade.+?ELA Total Tested"
            )

            k8_corp_rate_data[
                "School Total|ELA Proficient %"
            ] = adjusted_corp_total_ela_proficient.sum(
                axis=1
            ) / adjusted_corp_total_ela_tested.sum(
                axis=1
            )

            # calculate IREAD Pass %
            if "IREAD Pass N" in k8_school_data:
                
                k8_corp_rate_data["IREAD Pass %"] = (
                    k8_corp_rate_data["IREAD Pass N"]
                    / k8_corp_rate_data["IREAD Test N"]
                )

                k8_school_data["IREAD Pass %"] = pd.to_numeric(
                    k8_school_data["IREAD Pass N"], errors="coerce"
                ) / pd.to_numeric(k8_school_data["IREAD Test N"], errors="coerce")

                # If either Test or Pass category had a '***' value, the resulting value will be 
                # NaN - we want it to display '***', so we just fillna
                k8_school_data["IREAD Pass %"] = k8_school_data["IREAD Pass %"].fillna("***")

            # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
            k8_school_data = k8_school_data.filter(
                regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$",
                axis=1,
            )
            k8_corp_rate_data = k8_corp_rate_data.filter(
                regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$",                
                axis=1,
            )

            # add School Name column back
            k8_school_data = pd.concat([k8_school_data, k8_school_info], axis=1, join="inner")

            # reset indexes
            k8_school_data = k8_school_data.reset_index(drop=True)
            
            # no drop because index was previous set to year
            k8_corp_rate_data = k8_corp_rate_data.reset_index()
            
            # ensure columns headers are strings
            k8_school_data.columns = k8_school_data.columns.astype(str)
            k8_corp_rate_data.columns = k8_corp_rate_data.columns.astype(str)

            # freeze Corp Proficiency dataframe in current state for use in academic analysis page
            academic_analysis_corp_dict = k8_corp_rate_data.to_dict()
            k8_corp_data = k8_corp_rate_data.copy()

            # Ensure each df has same # of years - relies on each year having a single row
            k8_num_years = len(k8_school_data.index)

            # transpose dataframes and clean headers
            k8_school_data = (
                k8_school_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )

             # Keep category and all available years of data
            k8_school_data = k8_school_data.iloc[:, : (k8_num_years + 1)]

            k8_corp_data = (
                k8_corp_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )

            # Keep category and all available years of data
            k8_corp_data = k8_corp_data.iloc[:, : (k8_num_years + 1)]  

            k8_school_data = k8_school_data[
                k8_school_data["Category"].str.contains("School Name") == False
            ]

            k8_school_data = k8_school_data.reset_index(drop=True)

            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            # print('ORIG')
            # print(k8_school_data)
            # print(k8_corp_data)

# TODO: Metrics stuff starts here
            # reverse order of corp_data columns (ignoring 'Category') so current year is first and
            # get clean list of years
            k8_year_cols = list(k8_school_data.columns[:0:-1])
            k8_year_cols.reverse()

            k8_school_metric_data = k8_school_data.copy()

            # add_suffix is applied to entire df. To hide columns we dont want\
            # renamed, set it as index and reset back after renaming.
            k8_corp_data = (
                k8_corp_data.set_index(["Category"])
                .add_suffix("Corp Proficiency")
                .reset_index()
            )
            k8_school_data = (
                k8_school_data.set_index(["Category"])
                .add_suffix("School")
                .reset_index()
            )

            school_cols = list(k8_school_data.columns[:0:-1])
            school_cols.reverse()

            corp_cols = list(k8_corp_data.columns[:0:-1])
            corp_cols.reverse()

            result_cols = [str(s) + "+/-" for s in k8_year_cols]

            final_cols = list(itertools.chain(*zip(school_cols, corp_cols, result_cols)))

            final_cols.insert(0, "Category")

            merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
            merged_cols.insert(0, "Category")

            merged_data = k8_school_data.merge(k8_corp_data, on="Category", how="left")
            merged_data = merged_data[merged_cols]

            tmp_category = k8_school_data["Category"]
            k8_school_data = k8_school_data.drop("Category", axis=1)
            k8_corp_data = k8_corp_data.drop("Category", axis=1)

            k8_result = pd.DataFrame()

            for c in k8_school_data.columns:
                c = c[0:4]  # keeps only YYYY part of string
                k8_result[c + "+/-"] = calculate_difference(
                    k8_school_data[c + "School"], k8_corp_data[c + "Corp Proficiency"]
                )

            # add headers
            k8_result = k8_result.set_axis(result_cols, axis=1)
            k8_result.insert(loc=0, column="Category", value=tmp_category)

            # combined merged (school and corp) and result dataframes and reorder
            # (according to result columns)
            final_k8_academic_data = merged_data.merge(k8_result, on="Category", how="left")

            final_k8_academic_data = final_k8_academic_data[final_cols]

            # NOTE: Pretty sure this is redundant as we add 'Proficient %; suffix to totals
            # above, then remove it here, then pass to academic_analysis page, and add it
            # back. But I tried to fix it once and broke everything. So I'm just gonna
            # leave it alone for now.
            final_k8_academic_data["Category"] = (
                final_k8_academic_data["Category"]
                .str.replace(" Proficient %", "")
                .str.strip()
            )

            # rename IREAD Category
            final_k8_academic_data.loc[
                final_k8_academic_data["Category"] == "IREAD Pass %", "Category"
            ] = "IREAD Proficiency (Grade 3 only)"

            # convert to ordered_dict and then json
            k8_academic_data_dict = final_k8_academic_data.to_dict(into=OrderedDict)
            k8_academic_data_json = json.dumps(k8_academic_data_dict)

        ## Academic Metrics (k8)

            # Non-comparative indicators

            # NOTE: As comparative indicators (year-over-year or difference-from-school-corp)
            # are vectorized operations, we need to pull out any indicators requiring special
            # treatment and calculate them separately.

            # IREAD Data
            iread_data = k8_school_metric_data[
                k8_school_metric_data["Category"] == "IREAD Pass %"
            ]
            k8_school_metric_data = k8_school_metric_data.drop(
                k8_school_metric_data[
                    k8_school_metric_data["Category"] == "IREAD Pass %"
                ].index
            )

        ## IREAD 

            # NOTE: See code explanation in discussion of 'attendance_data_metrics'above.
            if not iread_data.empty:
                
                iread_limits = [0.9, 0.8, 0.7, 0.7] 
                
                iread_data = (
                    iread_data.set_index(["Category"])
                    .add_suffix("School")
                    .reset_index()
                )

                [
                    iread_data.insert(
                        i,
                        str(iread_data.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
                        iread_data.apply(
                            lambda x: set_academic_rating(
                                x[iread_data.columns[i - 1]], iread_limits, 1
                            ),
                            axis=1,
                        ),
                    )
                    for i in range(iread_data.shape[1], 1, -1)
                ]

            # replace NaN and ensure columns are strings
            iread_data = iread_data.fillna("No Data")
            iread_data.columns = iread_data.columns.astype(str)

            # save iread_data to_dict
            iread_data_dict = iread_data.to_dict(into=OrderedDict)
            iread_data_json = json.dumps(iread_data_dict)

        ## Comparative indicators (year-over-year and difference-from-corporation)

            category_header = k8_school_metric_data["Category"]
            k8_school_metric_data = k8_school_metric_data.drop("Category", axis=1)

            # temporarily store last column (first year of data chronologically) as
            # this is not used in first year-over-year calculation
            first_year = pd.DataFrame()
            first_year[k8_school_metric_data.columns[-1]] = k8_school_metric_data[
                k8_school_metric_data.columns[-1]
            ]

            # NOTE: Calculating year-over-year values is complicated by the fact that we need
            # to track, not ignore, insufficent n-size ('***'), a non-numeric value- . This is
            # used when there is available data, but not enough of it to show under privacy laws.

            # 1) If both the current_year and previous_year values are '***' -> the result is '***'
            # 2) If the previous year is either NaN or '***' and the current_year is 0 (that is 0% of students
            #    were proficient) -> the result is '-***", which is a special flag used for accountability
            #    purposes (a '-***' is generally treated as a Did Not Meet Standard rather than a No Rating).
            #   Thus:
            #   if None in Either Column -> None
            #   if *** in either column -> ***
            #   if # -> subtract
            #   if first value = 0 and second value is *** -> -***
            #   if first value = 0 and second value is NaN -> -***

## TODO: REMOVE TO CALC PAGE
            def calculate_year_over_year(current_year, previous_year):
                return np.where(
                    (current_year == 0) & ((previous_year.isna()) | (previous_year == "***")), "-***",
                    np.where(
                        (current_year == "***") | (previous_year == "***"), "***",
                        np.where(
                            (current_year.isna()) & (previous_year.isna()), None,
                            np.where(
                                (~current_year.isna()) & (previous_year.isna()), None,
                                
                                pd.to_numeric(current_year, errors="coerce") - pd.to_numeric(previous_year, errors="coerce"),
                            ),
                        ),
                    ),
                )

            # calculate year over year values
            # loops over dataframe calculating difference between col and col+1 and inserts it
            # into the dataframe
            z = 1
            x = 0
            for y in range(0, (len(k8_school_metric_data.columns)-1)):
                values = calculate_year_over_year(k8_school_metric_data.iloc[:, x], k8_school_metric_data.iloc[:, x + 1])
                k8_school_metric_data.insert(loc = z, column = k8_school_metric_data.columns[x] + '+/-', value = values)
                z+=2
                x+=2
           
            k8_school_metric_data.columns = [i + 'School' if '+/-' not in i else i for i in k8_school_metric_data.columns]

            k8_school_metric_data.insert(loc=0, column="Category", value=category_header)
            k8_school_metric_data["Category"] = (k8_school_metric_data["Category"].str.replace(" Proficient %", "").str.strip())
            
            # Add first_year data back
            k8_school_metric_data[first_year.columns] = first_year

            # Create clean col lists - (YYYY + 'School') and (YYYY + '+/-')
            school_years_cols = list(k8_school_metric_data.columns[1:])

# TODO: FIX THIS TOO
            # duplicate final academic data in preparation for calculating Ratings for diff_to_corp
            diff_to_corp = final_k8_academic_data.copy()

            delta_limits = [0.1, 0.02, 0, 0]
            years_limits = [0.05, 0.02, 0, 0]
            
            # NOTE: See comment in discussion of 'attendance_data_metrics' above.
            [
                diff_to_corp.insert(
                    i,
                    str(diff_to_corp.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
                    diff_to_corp.apply(
                        lambda x: set_academic_rating(
                            x[diff_to_corp.columns[i - 1]], delta_limits, 1
                        ),
                        axis=1,
                    ),
                )
                for i in range(diff_to_corp.shape[1], 1, -3)
            ]

            [
                k8_school_metric_data.insert(
                    i,
                    str(k8_school_metric_data.columns[i - 1])[: 7 - 3]
                    + "Rate"
                    + str(i),
                    k8_school_metric_data.apply(
                        lambda x: set_academic_rating(
                            x[k8_school_metric_data.columns[i - 1]], years_limits, 1
                        ),
                        axis=1,
                    ),
                )
                for i in range(k8_school_metric_data.shape[1], 1, -2)
            ]

            diff_to_corp = diff_to_corp.fillna("No Data")
            k8_school_metric_data = k8_school_metric_data.fillna("No Data")

            # ensure all column headers are strings
            diff_to_corp.columns = diff_to_corp.columns.astype(str)
            k8_school_metric_data.columns = k8_school_metric_data.columns.astype(str)

            # for the year_over_year df, drop the 'Rating' column for the last year_data column and rename it -
            # we don't use last Rating column becase we cannot calculate a 'year over year'calculation for the first year -
            # it is just the baseline

            k8_school_metric_data = k8_school_metric_data.iloc[:, :-2]
            k8_school_metric_data.columns.values[-1] = (k8_school_metric_data.columns.values[-1] + " (Initial Data Year)")

            diff_to_corp_dict = diff_to_corp.to_dict(into=OrderedDict)
            diff_to_corp_json = json.dumps(diff_to_corp_dict)

            # one last processing step is needed to ensure proper ratings. The set_academic_rating()
            # function assigns a rating based on the '+/-' difference value (either year over year
            # or as compared to corp). For the year over year comparison it is possible to get a
            # rating of 'Approaches Standard' for a '+/-' value of '0.00%' when the yearly ratings
            # are both '0'; and there is no case where we want a school to receive anything other
            # than a 'DNMS' for a 0% proficiency. However, the set_academic_rating() function does
            # not have access to the values used to calculate the difference value (so it cannot
            # tell if a 0 value is the result of a 0 proficiency). So we need to manually replace
            # any rating in the Rating column with 'DMNS' where the School proficiency value is '0.00%.'

            # because we are changing the value of one column based on the value of another (paired)
            # column, the way we do this is to create a list of tuples (a list of year and rating
            # column pairs), e.g., [('2022School', '2022Rating3')], and then iterate over the column pair

            # create the list of tuples
            # NOTE: the zip function stops at the end of the shortest list which automatically drops
            # the single 'Initial Year' column from the list. It returns an empty list if
            # school_years_cols only contains the Initial Year columns (because rating_cols will be empty)
            rating_cols = list(col for col in k8_school_metric_data.columns if "Rate" in col)
            col_pair = list(zip(school_years_cols, rating_cols))

            # iterate over list of tuples, if value in first item in pair is zero, change second
            # value in pair to DNMS
            if col_pair:
                for k, v in col_pair:
                    k8_school_metric_data[v] = np.where(
                        k8_school_metric_data[k] == 0, "DNMS", k8_school_metric_data[v]
                    )

            # save to_json
            year_over_year_values_dict = k8_school_metric_data.to_dict(into=OrderedDict)
            year_over_year_values_json = json.dumps(year_over_year_values_dict)

    ## HS Academic Information

    # NOTE: CHS (School ID: 5874) converted from a K12 to a K8 and
    # separate HS in 2021. We need to make a special exception here
    # to show HS data for CHS prior to 2021. In 2021 and thereafter,
    # the HS data is under CHMWHS (School ID: 9709)
    if (
        school_info["School Type"].values[0] == "HS"
        or school_info["School Type"].values[0] == "K12"
        or school_info["School Type"].values[0] == "AHS"
        or (school_info["School ID"].values[0] == "5874" and int(year) < 2021)
    ):
        # If the school is a HS or AHS -> all k8 dicts/json will be empty
        if (
            school_info["School Type"].values[0] == "HS"
            or school_info["School Type"].values[0] == "AHS"
        ):
            k8_academic_data_json = {}
            diff_to_corp_json = {}
            year_over_year_values_json = {}
            iread_data_json = {}
            academic_analysis_corp_dict = {}

        # if the school is a HS or K12 -> the ahs json will be empty
        if (
            school_info["School Type"].values[0] == "HS"
            or school_info["School Type"].values[0] == "K12"
            or (school_info["School ID"].values[0] == "5874" and int(year) < 2021)
        ):
            ahs_metrics_data_json = {}

        # remove 'excluded_years' from dataframe and get school data
        filtered_academic_data_hs = all_academic_data_hs[~all_academic_data_hs["Year"].isin(excluded_years)].copy()

        hs_school_data = filtered_academic_data_hs.loc[filtered_academic_data_hs["School ID"] == school]

        # If no data exists for the selected school, all dicts are empty
        if len(hs_school_data.index) == 0:
            hs_academic_data_json = {}
            combined_grad_metrics_json = {}
            ahs_metrics_data_json = {}

        else:

            # get school and school corporation hs academic data
            hs_corp_data = filtered_academic_data_hs.loc[
                (
                    filtered_academic_data_hs["Corp ID"]
                    == school_info["GEO Corp"].values[0]
                )
            ]

            # tmp remove text columns from dataframe
            hs_school_info = hs_school_data[["School Name"]].copy()


            # drop adult high schools (AHS) from Corp Average df
            hs_corp_data = hs_corp_data[
                hs_corp_data["School Type"].str.contains("AHS") == False
            ]

            # AHS- temporarily pull AHS specific values (CCR and GradAll)
            # where there is no corp equivalent.
            if school_info["School Type"].values[0] == "AHS":
                ahs_data = hs_school_data.filter(regex=r"GradAll$|CCR$", axis=1)

            # keep only those columns used in calculations

            # SAT Categories: 'Total Tested', 'Below Benchmark', 'Approaching Benchmark',
            #   'At Benchmark', & 'Benchmark %'
            # Grade 10 ECA Categories: 'Pass N' and 'Test N'
            # Graduation Categories: 'Cohort Count' and 'Graduates'
            hs_school_data = hs_school_data.filter(
                regex=r"Cohort Count$|Graduates$|Pass N|Test N|Benchmark|Total Tested|^Year$", axis=1
            )
            hs_corp_data = hs_corp_data.filter(
                regex=r"Cohort Count$|Graduates$|Pass N|Test N|Benchmark|Total Tested|^Year$", axis=1
            )

            # remove 'ELA & Math' columns (NOTE: Comment this out to retain 'ELA & Math' columns)
            hs_school_data = hs_school_data.drop(
                list(hs_school_data.filter(regex="ELA & Math")), axis=1
            )
            hs_corp_data = hs_corp_data.drop(
                list(hs_corp_data.filter(regex="ELA & Math")), axis=1
            )

            # valid_mask returns a boolean series of columns where column
            # is true if any element in the column is not equal to null
            valid_mask = ~pd.isnull(hs_school_data[hs_school_data.columns]).all()

            # create list of columns with no data (used in loop below)
            # missing_mask returns boolean series of columns where column
            # is true if all elements in the column are equal to null
            missing_mask = pd.isnull(hs_school_data[hs_school_data.columns]).all()
            missing_cols = hs_school_data.columns[missing_mask].to_list()

            # use valid_mask keep only columns that have at least one value
            hs_school_data = hs_school_data[hs_school_data.columns[valid_mask]]
            hs_corp_data = hs_corp_data[hs_corp_data.columns[valid_mask]]
            # Calculate Graduation Rates

            # NOTE: Coercing hs_corp_data values to numeric has the effect
            # of converting all '***' (insufficient n-size) values to NaN.
            # Because we are manually calculating a corp average, a NaN means
            # the school has been removed from the average calculation.
            # Typically, this won't have a large effect as there are few
            # traditional public high schools with supressed data, but it
            # could still potentially skew the results.

            # Do not convert school_corp_data values to numeric because the
            # function to calculate differences anticipates mixed dtypes.
            for col in hs_corp_data.columns:
                hs_corp_data[col] = pd.to_numeric(hs_corp_data[col], errors="coerce")

            # group corp dataframe by year and sum all rows for each category
            hs_corp_data = hs_corp_data.groupby(["Year"]).sum(numeric_only=True)

            # reverse order of rows (Year) and reset index to bring Year back as column
            hs_corp_data = hs_corp_data.loc[::-1].reset_index()

            grad_categories = ethnicity + subgroup + ["Total"]
            for g in grad_categories:
                new_col = g + " Graduation Rate"
                graduates = g + "|Graduates"
                cohort = g + "|Cohort Count"

                if cohort not in missing_cols:
                    hs_school_data[new_col] = calculate_percentage(hs_school_data[graduates], hs_school_data[cohort])
                    hs_corp_data[new_col] = (hs_corp_data[graduates] / hs_corp_data[cohort])

            # Calculate ECA (Grade 10) rate
            # Use ECA data as calculated at the corporation level (from corporation_rates datafile).
            # NOTE: 'Due to suspension of assessments in 2019-2020, Grade 11 students were assessed
            # on ISTEP10 in 2020-2021' 'Results reflect first-time test takers in Grade 11 Cohort
            # (Graduation Year 2022). 'Results may not be comparable to past years due to assessment
            # of Grade 11'
            hs_corp_rates_filtered = corporation_rates[~corporation_rates["Year"].isin(excluded_years)]
            hs_corp_rate_data = hs_corp_rates_filtered.loc[(hs_corp_rates_filtered["Corp ID"] == school_info["GEO Corp"].values[0])].copy()

            # change values to numeric (again not school because function accounts for '***')
            for col in hs_corp_rate_data.columns:
                hs_corp_rate_data[col] = pd.to_numeric(hs_corp_rate_data[col], errors="coerce")

            # NOTE: Special case for 2020 - corp_data exists for 2020 (e.g., grad rate),
            # but no data exists for 2020 in corp_rate_data - so there will always be a
            # mismatch - so need to take some additional steps

            # drop all non_matching years from hs_corp_rate_data
            hs_corp_rate_data = hs_corp_rate_data.loc[
                (hs_corp_rate_data["Year"].isin(hs_corp_data["Year"]))
            ]

            # get missing year(s) in hs_corp_rate_data by comparing the difference
            # between two list sets: usually just 2020, because the only available
            # academic data for 2020 is grad data (hs_corp_data).
            missing_year = list(
                sorted(
                    set(hs_corp_data["Year"].tolist())
                    - set(hs_corp_rate_data["Year"].tolist())
                )
            )

            # reset index
            hs_corp_rate_data = hs_corp_rate_data.reset_index(drop=True)

            # if there is a missing year add new row to hs_corp_rate_data with all
            # blanks except for the year value add the year value to the 'Year'
            # column at last index (most recently added row)
            if missing_year:
                for y in missing_year:
                    hs_corp_rate_data = pd.concat(
                        [
                            hs_corp_rate_data,
                            pd.DataFrame(
                                np.nan,
                                columns=hs_corp_rate_data.columns,
                                index=range(1),
                            ),
                        ],
                        ignore_index=True,
                    )
                    hs_corp_rate_data.at[hs_corp_rate_data.index[-1], "Year"] = y

            hs_corp_rate_data = hs_corp_rate_data.sort_values(by="Year", ascending=False)
            hs_corp_rate_data = hs_corp_rate_data.reset_index(drop=True)

            # if none_categories includes 'Grade 10' - there is no ECA data available
            # # for the school for the selected Years
            eca_categories = ["Grade 10|ELA", "Grade 10|Math"]

            # checks to see if substring ('Grade 10') is in the list of missing cols
            if "Grade 10" not in "\t".join(missing_cols):
                for e in eca_categories:
                    new_col = e + " Pass Rate"
                    passN = e + " Pass N"
                    testN = e + " Test N"

                    hs_school_data[new_col] = calculate_percentage(
                        hs_school_data[passN], hs_school_data[testN]
                    )

                    hs_corp_data[new_col] = (
                        hs_corp_rate_data[passN] / hs_corp_rate_data[testN]
                    )

            sat_categories = ethnicity + subgroup + ["School Total"]
            sat_subject = ['EBRW','Math','Both']

            for ss in sat_subject:
                for sc in sat_categories:
                    new_col = sc + "|" + ss + " Benchmark %"
                    at_benchmark = sc + "|" + ss + " At Benchmark"
                    total_tested = sc + "|" + ss + " Total Tested"

                    if total_tested not in missing_cols:
                        # Dats sometimes has 0's where there should be nulls
                        # so we drop all columns for a category where the
                        # total tested # of students is '0' (values are currently
                        # strings, get converted to numeric in the calculate-percentage
                        # function)
                        if hs_school_data[total_tested].values[0] == '0':
                            drop_columns = [new_col, at_benchmark, total_tested]
                            hs_school_data = hs_school_data.drop(drop_columns, axis=1)
                            hs_corp_data = hs_corp_data.drop(drop_columns, axis=1)
                        else:
                            hs_school_data[new_col] = calculate_percentage(
                                hs_school_data[at_benchmark], hs_school_data[total_tested]
                            )
                            hs_corp_data[new_col] = (
                                hs_corp_data[at_benchmark] / hs_corp_data[total_tested]
                            )
                            
            # if missing_cols includes 'Non-Waiver' - there is no data available for the school
            # for the selected Years
            if "Non-Waiver" not in "\t".join(missing_cols):

                # NOTE: In spring of 2020, SBOE waived the GQE requirement for students in the
                # 2020 cohort who where otherwise on schedule to graduate, so, for the 2020
                # cohort, there were no 'waiver' graduates (which means no non-waiver data).
                # so we replace 0 with NaN (to ensure a NaN result rather than 0)
                hs_corp_data["Non-Waiver|Cohort Count"] = hs_corp_data[
                    "Non-Waiver|Cohort Count"
                ].replace({"0": np.nan, 0: np.nan})

                hs_corp_data["Non-Waiver Graduation Rate"] = (
                    hs_corp_data["Non-Waiver|Cohort Count"]
                    / hs_corp_data["Total|Cohort Count"]
                )
                hs_corp_data["Strength of Diploma"] = (
                    hs_corp_data["Non-Waiver|Cohort Count"] * 1.08
                ) / hs_corp_data["Total|Cohort Count"]

                # NOTE: pd.to_numeric (coerce) should have converted all '***' values (to NaN)
                hs_school_data["Non-Waiver|Cohort Count"] = pd.to_numeric(
                    hs_school_data["Non-Waiver|Cohort Count"], errors="coerce"
                )
                hs_school_data["Total|Cohort Count"] = pd.to_numeric(
                    hs_school_data["Total|Cohort Count"], errors="coerce"
                )

                hs_school_data["Non-Waiver Graduation Rate"] = (
                    hs_school_data["Non-Waiver|Cohort Count"]
                    / hs_school_data["Total|Cohort Count"]
                )
                hs_school_data["Strength of Diploma"] = (
                    hs_school_data["Non-Waiver|Cohort Count"] * 1.08
                ) / hs_school_data["Total|Cohort Count"]

# TODO: AHS SPLIT STARTS HERE
            # Calculate CCR Rate (AHS Only), add Year column and store in temporary dataframe
            # NOTE: All other values pulled from HS dataframe required for AHS calculations
            # should go here
            if school_info["School Type"].values[0] == "AHS":
                ahs_school_data = pd.DataFrame()
                ahs_school_data["Year"] = hs_school_data["Year"]

                ahs_data["AHS|CCR"] = pd.to_numeric(
                    ahs_data["AHS|CCR"], errors="coerce"
                )
                ahs_data["AHS|GradAll"] = pd.to_numeric(
                    ahs_data["AHS|GradAll"], errors="coerce"
                )
                ahs_school_data["CCR Percentage"] = (
                    ahs_data["AHS|CCR"] / ahs_data["AHS|GradAll"]
                )

                ahs_metric_data = (ahs_school_data.copy())
                ahs_metric_data = ahs_metric_data.reset_index(drop=True)

            # filter out unused cols
            hs_school_data = hs_school_data.filter(
                regex=r"^Category|Graduation Rate$|Pass Rate$|Benchmark %|Below|Approaching|At|^CCR Percentage|Total Tested|^Year$", # ^Strength of Diploma
                axis=1,
            )
            hs_corp_data = hs_corp_data.filter(
                regex=r"^Category|Graduation Rate$|Pass Rate$|Benchmark %|Below|Approaching|At|Total Tested|^Year$", # ^Strength of Diploma
                axis=1,
            )

            # State Average Graduation Rate

            filtered_academic_data_hs["Total|Graduates"] = pd.to_numeric(
                filtered_academic_data_hs["Total|Graduates"], errors="coerce"
            )
            filtered_academic_data_hs["Total|Cohort Count"] = pd.to_numeric(
                filtered_academic_data_hs["Total|Cohort Count"], errors="coerce"
            )

            # NOTE: exclude AHS from graduation rate calculation due to the inapplicability
            # of grad rates to the AHS model
            filtered_academic_data_hs[
                "Total|Graduates"
            ] = filtered_academic_data_hs.loc[
                filtered_academic_data_hs["School Type"] != "AHS", "Total|Graduates"
            ]
            filtered_academic_data_hs[
                "Total|Cohort Count"
            ] = filtered_academic_data_hs.loc[
                filtered_academic_data_hs["School Type"] != "AHS", "Total|Cohort Count"
            ]

            state_grad_average = (
                filtered_academic_data_hs.groupby("Year", as_index=False)
                .sum(numeric_only=True)
                .eval("State_Grad_Average = `Total|Graduates` / `Total|Cohort Count`")
            )

            # drop all other columns, invert rows (so most recent year at index [0]) & reset the index
            state_grad_average = state_grad_average[["Year", "State_Grad_Average"]]
            state_grad_average = state_grad_average.loc[::-1].reset_index(drop=True)

            # merge applicable years of grad_avg dataframe into hs_school df using an inner merge
            # and rename the column this merges data only where both dataframes share a common key,
            # in this case 'Year')
            state_grad_average["Year"] = state_grad_average["Year"].astype(int)

            hs_corp_data = hs_corp_data.merge(state_grad_average, on="Year", how="inner")
            
            hs_corp_data = hs_corp_data.rename(
                columns={"State_Grad_Average": "Average State Graduation Rate"}
            )

            # duplicate 'Total Grad' row and name it 'State Average Graduation Rate'
            # for comparison purposes
            hs_school_data["Average State Graduation Rate"] = hs_school_data[
                "Total Graduation Rate"
            ]
  
            hs_school_info = hs_school_info.reset_index(drop=True)
            hs_school_data = hs_school_data.reset_index(drop=True)

            hs_school_data = pd.concat([hs_school_data, hs_school_info], axis=1, join="inner")

            hs_school_data.columns = hs_school_data.columns.astype(str)
            hs_corp_data.columns = hs_corp_data.columns.astype(str)

            # calculate difference (+/-) between school and corp grad rates
            hs_num_years = len(hs_school_data.index)

            # transpose dataframes and clean headers
            hs_school_data = (
                hs_school_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )

            # Keep category and all available years of data
            hs_school_data = hs_school_data.iloc[
                :, : (hs_num_years + 1)
            ]

            hs_corp_data = (
                hs_corp_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )
            hs_corp_data = hs_corp_data.iloc[:, : (hs_num_years + 1)]

            # State/Federal grade rows are used in 'about' page, but not here
            hs_school_data = hs_school_data[hs_school_data["Category"].str.contains("State Grade|Federal Rating|School Name") == False]
            
            hs_school_data = hs_school_data.reset_index(drop=True)

            # get clean list of years
            hs_year_cols = list(hs_school_data.columns[:0:-1])
            hs_year_cols.reverse()

            # add_suffix is applied to entire df. To hide columns we dont want renamed, set them as index and reset back after renaming.
            hs_corp_data = (
                hs_corp_data.set_index(["Category"])
                .add_suffix("Corp Average")
                .reset_index()
            )
            hs_school_data = (
                hs_school_data.set_index(["Category"])
                .add_suffix("School")
                .reset_index()
            )

            # have to do same things to ahs_data to be able to insert it back
            # into hs_data file even though there is no comparison data involved
            if school_info["School Type"].values[0] == "AHS":
                ahs_school_data = (
                    ahs_school_data.set_index("Year")
                    .T.rename_axis("Category")
                    .rename_axis(None, axis=1)
                    .reset_index()
                )
                ahs_school_data = ahs_school_data.iloc[:, : (hs_num_years + 1)]
                ahs_school_data = (
                    ahs_school_data.set_index(["Category"])
                    .add_suffix("School")
                    .reset_index()
                )

            # Create list of alternating columns by year (School Value/Similar School Value)
            school_cols = list(hs_school_data.columns[:0:-1])
            school_cols.reverse()

            corp_cols = list(hs_corp_data.columns[:0:-1])
            corp_cols.reverse()

            result_cols = [str(s) + "+/-" for s in hs_year_cols]

            final_cols = list(
                itertools.chain(*zip(school_cols, corp_cols, result_cols))
            )
            final_cols.insert(0, "Category")

            merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
            merged_cols.insert(0, "Category")
            hs_merged_data = hs_school_data.merge(
                hs_corp_data, on="Category", how="left"
            )
            hs_merged_data = hs_merged_data[merged_cols]

            tmp_category = hs_school_data["Category"]
            hs_school_data = hs_school_data.drop("Category", axis=1)
            hs_corp_data = hs_corp_data.drop("Category", axis=1)

            # make sure there are no lingering NoneTypes to screw up the creation of hs_results
            hs_school_data = hs_school_data.fillna(value=np.nan)
            hs_corp_data = hs_corp_data.fillna(value=np.nan)

            # calculate difference between two dataframes
            hs_results = pd.DataFrame()
            for y in hs_year_cols:
                hs_results[y] = calculate_difference(
                    hs_school_data[y + "School"], hs_corp_data[y + "Corp Average"]
                )

            # add headers
            hs_results = hs_results.set_axis(result_cols, axis=1)
            hs_results.insert(loc=0, column="Category", value=tmp_category)

            final_hs_academic_data = hs_merged_data.merge(
                hs_results, on="Category", how="left"
            )
            final_hs_academic_data = final_hs_academic_data[final_cols]

            # If AHS - add CCR data to hs_data file
            if school_info["School Type"].values[0] == "AHS":
                final_hs_academic_data = pd.concat(
                    [final_hs_academic_data, ahs_school_data], sort=False
                )
                final_hs_academic_data = final_hs_academic_data.reset_index(drop=True)


            hs_academic_data_dict = final_hs_academic_data.to_dict(into=OrderedDict)
            hs_academic_data_json = json.dumps(hs_academic_data_dict)

            # calculate AHS/HS Academic Metrics

            if school_info["School Type"].values[0] == "AHS":
                combined_grad_metrics_json = {}

                # transpose dataframe and clean headers
                ahs_metric_data = (
                    ahs_metric_data.set_index("Year")
                    .T.rename_axis("Category")
                    .rename_axis(None, axis=1)
                    .reset_index()
                )

                # Keep category and all available years of data
                ahs_metric_data = ahs_metric_data.iloc[:, : (hs_num_years + 1)]
                ahs_metric_data.columns = ahs_metric_data.columns.astype(str)

                # format for multi-header display
                ahs_metric_cols = list(ahs_metric_data.columns[:0:-1])
                ahs_metric_cols.reverse()

                ahs_metric_data = (
                    ahs_metric_data.set_index(["Category"])
                    .add_suffix("School")
                    .reset_index()
                )

                # ahs_metric_data = ahs_metric_data.loc[ahs_metric_data["Category"] == "CCR Percentage"]

                ccr_limits = [0.5, 0.499, 0.234]

                [
                    ahs_metric_data.insert(
                        i,
                        str(ahs_metric_cols[i - 2]) + "Rate" + str(i),
                        ahs_metric_data.apply(
                            lambda x: set_academic_rating(
                                x[ahs_metric_data.columns[i - 1]], ccr_limits, 2
                            ),
                            axis=1,
                        ),
                    )
                    for i in range(ahs_metric_data.shape[1], 1, -1)
                ]

                ahs_state_grades = school_letter_grades.iloc[0:1, :]

                ahs_state_grades.columns = ahs_state_grades.columns.astype(str)
                ahs_state_grades = (
                    ahs_state_grades.set_index(["Category"])
                    .add_suffix("School")
                    .reset_index()
                )

                # ensure state_grades df contains same years of data as ahs_metric_cols
                ahs_state_grades = ahs_state_grades.loc[:,ahs_state_grades.columns.str.contains("|".join(ahs_metric_cols + ["Category"]))]

                letter_grade_limits = ["A", "B", "C", "D", "F"]

                [
                    ahs_state_grades.insert(
                        i,
                        str(ahs_metric_cols[i - 2]) + "Rate" + str(i),
                        ahs_state_grades.apply(
                            lambda x: set_academic_rating(
                                x[ahs_state_grades.columns[i - 1]],
                                letter_grade_limits,
                                4,
                            ),
                            axis=1,
                        ),
                    )
                    for i in range(ahs_state_grades.shape[1], 1, -1)
                ]
# TODO: HERE
                print('ORIG GRADES')
                print(ahs_state_grades)

                # concatenate and add metric column
                ahs_metric_data = pd.concat([ahs_state_grades, ahs_metric_data])
                ahs_metric_data = ahs_metric_data.reset_index(drop=True)
                ahs_metric_nums = ["1.1.", "1.3."]
                ahs_metric_data.insert(loc=0, column="Metric", value=ahs_metric_nums)

                ahs_school_metric_dict = ahs_metric_data.to_dict(into=OrderedDict)
                ahs_metrics_data_json = json.dumps(ahs_school_metric_dict)

            else:
            # TODO: HS METRICS BEGIN HERE
                combined_hs_metrics = final_hs_academic_data.copy()

                # rename 'Corp Average' to 'Average'
                combined_hs_metrics.columns = combined_hs_metrics.columns.str.replace(r"Corp Average", "Average")

                grad_limits_state = [0, 0.05, 0.15, 0.15]

                state_grad_metric = combined_hs_metrics.loc[combined_hs_metrics["Category"] == "Average State Graduation Rate"]

                [
                    state_grad_metric.insert(
                        i,
                        str(state_grad_metric.columns[i - 1])[: 7 - 3]
                        + "Rate"
                        + str(i),
                        state_grad_metric.apply(
                            lambda x: set_academic_rating(
                                x[state_grad_metric.columns[i - 1]],
                                grad_limits_state,
                                2,
                            ),
                            axis=1,
                        ),
                    )
                    for i in range(state_grad_metric.shape[1], 1, -3)
                ]

                grad_limits_local = [0, 0.05, 0.10, 0.10]
                local_grad_metric = combined_hs_metrics[combined_hs_metrics["Category"].isin(["Total Graduation Rate", "Non-Waiver Graduation Rate"])]
                
                [
                    local_grad_metric.insert(
                        i,
                        str(local_grad_metric.columns[i - 1])[: 7 - 3]
                        + "Rate"
                        + str(i),
                        local_grad_metric.apply(
                            lambda x: set_academic_rating(
                                x[local_grad_metric.columns[i - 1]],
                                grad_limits_local,
                                2,
                            ),
                            axis=1,
                        ),
                    )
                    for i in range(local_grad_metric.shape[1], 1, -3)
                ]

                strength_diploma = combined_hs_metrics[combined_hs_metrics["Category"] == "Strength of Diploma"]
                
                strength_diploma = strength_diploma[
                    [
                        col
                        for col in strength_diploma.columns
                        if "School" in col or "Category" in col
                    ]
                ]

                # NOTE: Strength of Diploma is not currently displayed
                strength_diploma.loc[
                    strength_diploma["Category"] == "Strength of Diploma", "Category"
                ] = "1.7.e The school's strength of diploma indicator."

                # combine dataframes and rename categories
                combined_grad_metrics = pd.concat(
                    [state_grad_metric, local_grad_metric], ignore_index=True
                )
                combined_grad_metrics.loc[
                    combined_grad_metrics["Category"]
                    == "Average State Graduation Rate",
                    "Category",
                ] = "1.7.a 4 year graduation rate compared with the State average"
                combined_grad_metrics.loc[
                    combined_grad_metrics["Category"] == "Total Graduation Rate",
                    "Category",
                ] = "1.7.b 4 year graduation rate compared with school corporation average"
                combined_grad_metrics.loc[
                    combined_grad_metrics["Category"] == "Non-Waiver Graduation Rate",
                    "Category",
                ] = "1.7.b 4 year non-waiver graduation rate  with school corporation average"

                combined_grad_metrics_dict = combined_grad_metrics.to_dict(
                    into=OrderedDict
                )
                combined_grad_metrics_json = json.dumps(combined_grad_metrics_dict)

    # combine into dictionary of dictionarys for dcc.store
    # TODO: Reorder
    dict_of_df = {}

    dict_of_df[0] = school_info_dict
    dict_of_df[1] = school_demographic_selected_year_dict
    dict_of_df[2] = corp_demographic_selected_year_dict
    dict_of_df[3] = school_letter_grades_json
    dict_of_df[4] = attendance_data_json
    dict_of_df[5] = attendance_data_metrics_json
    
    dict_of_df[7] = academic_analysis_corp_dict
    dict_of_df[8] = k8_academic_data_json
    dict_of_df[9] = iread_data_json
    dict_of_df[10] = diff_to_corp_json
    dict_of_df[11] = year_over_year_values_json
    dict_of_df[12] = hs_academic_data_json
    dict_of_df[13] = ahs_metrics_data_json
    dict_of_df[14] = combined_grad_metrics_json

    dict_of_df[16] = network_finance_json
    dict_of_df[17] = school_finance_json

    return dict_of_df

if __name__ == "__main__":
    app.run_server(debug=True)
#    application.run(host='0.0.0.0', port='8080')