#########################
# ICSB School Dashboard #
#########################
# author:    jbetley
# version:  1.0.02.01.23

## NOTE: Need to manually determine certain data points at the school level if it is stored at the Corp Level
# E.g., Split Grade K8 and 912 enrollment / Proportionate split of demographic enrollment (subgroups, etc.)
# Christel House South (CHS/CHWMHS)
# Circle City Prep (Ele/Mid)

## NOTE: Using pandas dataframes (not typically used for display) to build lots of dash datatables
# to be used for display, so there is quite a bit of funky ass fiddly dataframe manipulation shit
# required to get everything aligned and in the order that we want it.

# flask and flask-login #
# https://levelup.gitconnected.com/how-to-setup-user-authentication-for-dash-apps-using-python-and-flask-6c2e430cdb51
import os
from flask import Flask, url_for, redirect, request, render_template, session, jsonify
from flask_login import login_user, LoginManager, UserMixin, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy

from pages.calculations import set_academic_rating

# from flask_migrate import Migrate
from sqlalchemy import create_engine, text, select

# from sqlalchemy.orm import sessionmaker, Session
from flask_bcrypt import Bcrypt

# from flask_wtf.csrf import CSRFProtect
# dash #
import dash
from dash import dcc, html, Input, Output, State, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from collections import OrderedDict
import pandas as pd
import json
import numpy as np
import itertools

# To access .env files in virtualenv
from dotenv import load_dotenv
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"

external_stylesheets = ["https://fonts.googleapis.com/css2?family=Roboto:400", FONT_AWESOME]

# Authentication with Flask-Login, Sqlite3, and Bcrypt
# https://community.plotly.com/t/dash-app-pages-with-flask-login-flow-using-flask/69507/38
# https://stackoverflow.com/questions/52286507/how-to-merge-flask-login-with-a-dash-application
server = Flask(__name__, static_folder="./static")

# dotenv_path = join(dirname(__file__), '.env')
# load_dotenv(dotenv_path)
load_dotenv()

# server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////users.db'
basedir = os.path.abspath(os.path.dirname(__file__))
server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "users.db"
)
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
server.config.update(SECRET_KEY=os.getenv("SECRET_KEY"))

bcrypt = Bcrypt()

# TODO: IMPLEMENT?
# Create CSRF protect
# csrf = CSRFProtect()
# csrf.init_app(server)

db = SQLAlchemy(server)

# Session = sessionmaker(bind=db)
# session = Session()

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"


# each table in the database needs a class to be created for it using the db.Model, all
# db columns must be identified by name and data type.
# UserMixin provides a get_id method that returns the id attribute or raises an exception.x
# Need to either name the database attribute 'id' or override the get_id function to return user_id
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text, unique=True)


# load_user is used by login_user, passes the user_id and gets the User object that matches that id
# The 'User.query.get(int(id))' method has been deprecated
# https://stackoverflow.com/questions/75365194/sqlalchemy-2-0-version-of-user-query-get1-in-flask-sqlalchemy
@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))


# The default is to block all requests unless user is on login page or is authenticated
@server.before_request
def check_login():
    if request.method == "GET":
        if request.path in ["/login"]:  # , '/logout']:
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
            # https://python-adv-web-apps.readthedocs.io/en/latest/flask_db2.html
            user_data = User.query.filter_by(username=user).first()

            if user_data:
                # check a hash of the provided password against the hashed password stored in the
                # User object
                if bcrypt.check_password_hash(user_data.password, password):
                    # if True, login the user using the User object
                    login_user(user_data)

                    # TODO: NOT ENTIRELY SURE WHAT IS GOING ON HERE
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


# Latest version was refactors to use new dash pages functionality (added dash 2.5)
# https://github.com/AnnMarieW/dash-multi-page-app-demos/tree/main/multi_page_layout_functions
# app = dash.Dash(__name__, use_pages=True, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)

# category variables
# NOTE: 'American Indian' has been removed from ethnicity variable
# - it seems to break some functionality due to inconsistent use as a category in data
ethnicity = [
    "Asian",
    "Black",
    "Hispanic",
    "Multiracial",
    "Native Hawaiian or Other Pacific Islander",
    "White",
]
status = [
    "Special Education",
    "General Education",
    "Paid Meals",
    "Free/Reduced Price Meals",
    "English Language Learners",
    "Non-English Language Learners",
]
subgroups = ethnicity + status

grades = ["Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"]
academic_info_grades = [
    "Grade 3",
    "Grade 4",
    "Grade 5",
    "Grade 6",
    "Grade 7",
    "Grade 8",
    "Total",
    "IREAD Pass %",
]
eca = ["Grade 10|ELA", "Grade 10|Math"]
info = ["Year", "School Type"]
subject = ["Math", "ELA"]

## Load Data Files ##
print("#### Loading Data. . . . . ####")

# NOTE: No K8 academic data exists for 2020
school_index = pd.read_csv(r"data/school_index.csv", dtype=str)
school_academic_data_k8 = pd.read_csv(r"data/school_data_k8.csv", dtype=str)
all_academic_data_hs = pd.read_csv(r"data/academic_data_hs.csv", dtype=str)
corporation_rates = pd.read_csv(r"data/corporate_rates.csv", dtype=str)
all_demographic_data = pd.read_csv(r"data/demographic_data.csv", dtype=str)

# Fixes issue where converting string to int adds trailing '.0'
school_academic_data_k8["Low Grade"] = (
    school_academic_data_k8["Low Grade"].astype(str).str.replace(".0", "", regex=False)
)
school_academic_data_k8["High Grade"] = (
    school_academic_data_k8["High Grade"].astype(str).str.replace(".0", "", regex=False)
)

# Get current year - demographic data will almost always be more current than academic data (due to IDOE release cadence)
current_academic_year = school_academic_data_k8["Year"].unique().max()

num_academic_years = len(school_academic_data_k8["Year"].unique())


# Build dropdown list based on current_user
# NOTE: application-state is a dummy input
@callback(
    Output("charter-dropdown", "options"), [Input("application-state", "children")]
)
def set_dropdown_options(year):
    # Get the current user id using the current_user proxy, use the ._get_current_object()
    # method to return the underlying object (User)
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
        # dropdown_data = school[['School Name','School ID','School Type']]

    dropdown_dict = dict(zip(charters["School Name"], charters["School ID"]))
    dropdown_list = dict(sorted(dropdown_dict.items()))
    options = [{"label": name, "value": id} for name, id in dropdown_list.items()]

    return options

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
                                        "fontSize": "85%",
                                        "fontFamily": "Roboto, sans-serif",
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
                                    options=[
                                        {"label": str(y), "value": str(y)}
                                        for y in range(
                                            int(current_academic_year) - num_academic_years,
                                            int(current_academic_year) + 1,
                                        )
                                    ],
                                    style={
                                        "fontSize": "85%",
                                        "fontFamily": "Roboto, sans-serif",
                                    },
                                    value=current_academic_year,
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
                                    "marginTop": "40px",
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

    ### School Information
    school_info = school_index.loc[school_index["School ID"] == school]
    school_info_dict = school_info.to_dict()

    # 'year' is selected year
    excluded_academic_years = int(current_academic_year) - int(year)

    # 'excluded years' is a list of YYYY strings (all years more recent than selected year)
    # that can be used to filter data that should not be displayed
    excluded_years = []
    for i in range(excluded_academic_years):
        excluded_year = int(current_academic_year) - i
        excluded_years.append(str(excluded_year))

    # store current year separately for demographic data because demographic data exists for 2020
    demographic_year = str(year)

    # NOTE: Maximum number of years of data to display
    max_display_years = 5

    ### Demographic Data (includes demographics, attendance rates, and state & federal grades)

    # get school demographic data for all years
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

        # get state & federal letter grades for all years and save to json
        school_letter_grades = school_demographic_data[
            ["State Grade", "Federal Rating", "Year"]
        ]

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

        # get attendance rate data
        school_attendance_rate = school_demographic_data[["Year", "Avg Attendance"]]

        # transpose for display
        school_attendance_rate = (
            school_attendance_rate.set_index("Year")
            .T.rename_axis(None, axis=1)
            .reset_index()
        )
        school_attendance_rate = school_attendance_rate.drop("index", axis=1)

        corp_attendance_rate = corp_demographic_data[["Year", "Avg Attendance"]]
        corp_attendance_rate = (
            corp_attendance_rate.set_index("Year")
            .T.rename_axis(None, axis=1)
            .reset_index()
        )
        corp_attendance_rate = corp_attendance_rate.drop("index", axis=1)

        # align corp df columns to school df (will drop years in corp df that aren't in school df)
        corp_attendance_rate = corp_attendance_rate[school_attendance_rate.columns]

        for col in corp_attendance_rate.columns:
            corp_attendance_rate[col] = pd.to_numeric(
                corp_attendance_rate[col], errors="coerce"
            )

        for col in school_attendance_rate.columns:
            school_attendance_rate[col] = pd.to_numeric(
                school_attendance_rate[col], errors="coerce"
            )

        # add accountability category
        school_attendance_rate = school_attendance_rate.replace(0, np.nan)
        school_attendance_rate[
            "Category"
        ] = "1.1.a. Attendance Rate (compared to school corporation average)"
        last_col = school_attendance_rate.pop("Category")
        school_attendance_rate.insert(0, "Category", last_col)
        corp_attendance_rate[
            "Category"
        ] = "1.1.a. Attendance Rate (compared to school corporation average)"
        last_col = corp_attendance_rate.pop("Category")
        corp_attendance_rate.insert(0, "Category", last_col)

        corp_attendance_rate = (
            corp_attendance_rate.set_index(["Category"])
            .add_suffix("Corp Avg")
            .reset_index()
        )
        school_attendance_rate = (
            school_attendance_rate.set_index(["Category"])
            .add_suffix("School")
            .reset_index()
        )

        # Create a column list ('merged_cols' that alternates school and corp cols)
        school_cols = list(school_attendance_rate.columns[:0:-1])
        school_cols.reverse()

        corp_cols = list(corp_attendance_rate.columns[:0:-1])
        corp_cols.reverse()

        merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
        merged_cols.insert(0, "Category")

        # merge the school and corp attendance rate dataframes and reorder using the interwoven cols
        merged_data = school_attendance_rate.merge(
            corp_attendance_rate, on="Category", how="left"
        )
        merged_data = merged_data[merged_cols]

        # temporarily store and drop 'Category' column from attendance rate dataframes
        tmp_category = school_attendance_rate["Category"]

        school_attendance_rate = school_attendance_rate.drop("Category", axis=1)
        corp_attendance_rate = corp_attendance_rate.drop("Category", axis=1)

        # calculate difference between two dataframes
        result_attendance_rate = pd.DataFrame(
            school_attendance_rate.values - corp_attendance_rate.values
        )

        # create a third column to store result (a clean list of years from school_letter_grades df + '+/-')
        clean_cols = list(school_letter_grades.columns[:0:-1])
        clean_cols.reverse()
        diff_cols = [str(s) + "+/-" for s in clean_cols]

        # create a final list of cols that interweaves the others and add 'Category' backg
        final_cols = list(itertools.chain(*zip(school_cols, corp_cols, diff_cols)))
        final_cols.insert(0, "Category")

        # add headers
        result_attendance_rate = result_attendance_rate.set_axis(diff_cols, axis=1)
        result_attendance_rate.insert(loc=0, column="Category", value=tmp_category)

        # merge result data with school/corp df and reorder according to the interwoven columns created earlier
        attendance_data = merged_data.merge(
            result_attendance_rate, on="Category", how="left"
        )
        attendance_data = attendance_data[final_cols]

        # save attendance_data to json
        attendance_data_dict = attendance_data.to_dict(into=OrderedDict)
        attendance_data_json = json.dumps(attendance_data_dict)

        # use the final data to calculate attendance data metrics
        attendance_data_metrics = attendance_data.copy()

        attendance_limits = [
            0,
            -0.01,
            -0.01,
        ]  # threshold limits for rating calculations

        # NOTE: General explanation of the accountability rating calcuations
        # calculate and add an accountability rating ('MS', 'DNMS', 'N/A', etc) as a new column to existing dataframe
        #   1) the loop ('for i in range(attendance_data_metrics.shape[1], 1, -3)') counts backwards by -3,
        #   beginning with the index of the last column in the dataframe ('attendance_data_metrics.shape[1]')
        #   to '1' (actually '2' as range does not include the last number). These are indexes, so the loop stops
        #   at the third column (which has an index of 2);
        #   2) for each step, the code inserts a new column, at index 'i'. The column header is a string that is
        #   equal to 'the year (YYYY) part of the column string (attendance_data_metrics.columns[i-1])[:7 - 3]) +
        #   'Rating' + 'i' (the value of 'i' doesn't matter other than to differentiate the columns) +
        #   the accountability value, a string returned by the set_academic_rating() function.
        #
        #   3) the set_academic_rating() function calculates an 'accountability rating' ('MS', 'DNMS', 'N/A', etc) taking as args:
        #       i) the 'value' to be rated. this will be from the 'School' column, if the value itself is rated
        #          (e.g., iread performance), or the difference ('+/-') column, if there is an additional calculation
        #           required (e.g., year over year or compared to corp);
        #       ii) a list of the threshold 'limits' to be used in the calculation; and
        #       iii) an integer 'flag' which tells the function which calculation to use.
        [
            attendance_data_metrics.insert(
                i,
                str(attendance_data_metrics.columns[i - 1])[: 7 - 3]
                + "Rating"
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

    ## Financial, Organizational, Average Daily Membership, and Federal Audit Findings

    ## Average Daily Membership
    # NOTE: Earlier versions used ADM from school_index. Current version uses
    # ADM Average as calculated from the school's financial file.
    finance_file = 'data/F-' + school_info['School Name'].values[0] + '.csv'

    if os.path.isfile(finance_file):
        financial_data = pd.read_csv(finance_file)

        adm_values = financial_data[financial_data['Category'].str.contains('ADM Average')]
        adm_values = adm_values.drop('Category', axis=1)
        adm_values = adm_values.reset_index(drop=True)
        
        for col in adm_values.columns:
            adm_values[col] = pd.to_numeric(adm_values[col], errors="coerce")
        
        adm_values = adm_values.loc[:, (adm_values != 0).any(axis=0)]

        # reverse order
        adm_values = adm_values[adm_values.columns[::-1]]

        if (
            adm_values.sum(axis=1).values[0] == 0
        ):  # this is true if all columns are equal to 0
            school_adm_dict = {}
        else:

            # NOTE: number of years with positive ADM is the most reliable way to track the number of years a school has been open to students
            # The ADM dataset can be longer than five years, so we have to filter it by both the selected year (the year to display) and the total # of years
            operating_years_by_adm = len(adm_values.columns)

            # if number of available years exceeds year_limit, drop excess columns (years)
            if operating_years_by_adm > max_display_years:
                adm_values = adm_values.drop(
                    columns = adm_values.columns[
                        : (operating_years_by_adm - max_display_years)
                    ],
                    axis=1
                )

            # if the display year is less than current year
            # drop columns where year matches any years in 'excluded years' list
            if excluded_years:
                adm_values = adm_values.loc[
                    :, ~adm_values.columns.str.contains("|".join(excluded_years))
                ]

            school_adm_dict = adm_values.to_dict()

    # # NOTE: Any time you see a copy() it is usually to avoid pandas SettingWithCopyWarning
    # school_adm = school_info.filter(regex=r"September ADM|February ADM", axis=1).copy()

    # for col in school_adm.columns:
    #     school_adm[col] = pd.to_numeric(school_adm[col], errors="coerce")

    # if (
    #     school_adm.sum(axis=1).values[0] == 0
    # ):  # this is true if all columns are equal to 0
    #     school_adm_dict = {}

    # else:
    #     # transpose adm dataframe and group by year (by splitting 'Name' Column e.g., '2022 February ADM', etc.
    #     # after 1st space) and sum() result
    #     # https://stackoverflow.com/questions/35746847/sum-values-of-columns-starting-with-the-same-string-in-pandas-dataframe
    #     school_adm = (
    #         school_adm.T.groupby(
    #             [s.split(" ", 1)[0] for s in school_adm.T.index.values]
    #         )
    #         .sum()
    #         .T
    #     )

    #     # average resulting sum (September and February Count)
    #     school_adm = school_adm / 2

    #     # years with no students (ADM = 0)
    #     school_adm = school_adm.loc[:, (school_adm != 0).any(axis=0)].reset_index(
    #         drop=True
    #     )

    #     # NOTE: number of years with positive ADM is the most reliable way to track the number of years a school has been open to students
    #     # The ADM dataset can be longer than five years, so we have to filter it by both the selected year (the year to display) and the total # of years
    #     operating_years_by_adm = len(school_adm.columns)

    #     # we want to limit display of certain data (e.g. ratios to years with students)
    #     years_with_adm = school_adm.columns.tolist()

    #     # if number of available years exceeds year_limit, drop excess columns (years)
    #     if operating_years_by_adm > max_display_years:
    #         school_adm = school_adm.drop(
    #             columns=school_adm.columns[
    #                 : (operating_years_by_adm - max_display_years)
    #             ],
    #             axis=1
    #         )

    #     # if the display year is less than current year
    #     # drop columns where year matches any years in 'excluded years' list
    #     if excluded_years:
    #         school_adm = school_adm.loc[
    #             :, ~school_adm.columns.str.contains("|".join(excluded_years))
    #         ]

    #     school_adm_dict = school_adm.to_dict()

    ## Financial & Organization Compliance Data is accessed in applicable application

    ### Academic Data

    # K8 Academic Data
    # import timeit

    # start_time = timeit.default_timer()

    if (
        school_info["School Type"].values[0] == "K8"
        or school_info["School Type"].values[0] == "K12"
    ):
        if school_info["School Type"].values[0] == "K8":
            hs_academic_data_json = {}
            ahs_metrics_data_json = {}
            combined_grad_metrics_json = {}

        # get school and school corporation academic data
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
            # get corporation proficiency rates (keyed to the GEO Corp value in index)
            # NOTE: corporation_rate values are calculated differently than school level values (when combined), so
            # we need to use corporation_rate values whenever we compare a charter (school corporation) to a traditional
            # school corporation.
            k8_corp_rates_filtered = corporation_rates[
                ~corporation_rates["Year"].isin(excluded_years)
            ]
            k8_corp_rate_filtered = k8_corp_rates_filtered.loc[
                (k8_corp_rates_filtered["Corp ID"] == school_info["GEO Corp"].values[0])
            ]

            # temporarily store School Name
            k8_school_info = k8_school_data[["School Name"]].copy()

            # filter to remove columns not used in calculations (need this in order to ensure columns match)
            # Need to keep School ID and School Name only for Academic Analysis data tab purposes
            k8_school_data = k8_school_data.filter(
                regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year",
                axis=1,
            )
            k8_corp_rate_filtered = k8_corp_rate_filtered.filter(
                regex=r"Total Tested$|Total Proficient$|IREAD Pass N|IREAD Test N|Year",
                axis=1,
            )
            # k8_comparison_data = k8_comparison_data.filter(regex = r'Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year|School Name|School ID',axis=1)

            # drop 'ELA & Math' columns [TODO: NOT NECESSARY]
            # NOTE: Comment out the following lines to retain 'ELA & Math' columns
            # k8_school_data.drop(list(k8_school_data.filter(regex = 'ELA & Math')), axis = 1, inplace = True)
            # k8_corp_rate_data.drop(list(k8_corp_rate_data.filter(regex = 'ELA & Math')), axis = 1, inplace = True)
            # k8_comparison_set.drop(list(k8_comparison_set.filter(regex = 'ELA & Math')), axis = 1, inplace = True)

            # valid_mask returns a boolean series of columns where column is true if any element in the column is not equal to null
            valid_mask = ~pd.isnull(k8_school_data[k8_school_data.columns]).all()

            # create list of columns with no date (used in loop below)
            # missing_mask returns boolean series of columns where column is true if all elements in the column are equal to null
            missing_mask = pd.isnull(k8_school_data[k8_school_data.columns]).all()
            missing_cols = k8_school_data.columns[missing_mask].to_list()

            # use valid_mask keep only columns that have at least one value
            k8_school_data = k8_school_data[k8_school_data.columns[valid_mask]]
            k8_corp_rate_filtered = k8_corp_rate_filtered[
                k8_corp_rate_filtered.columns[valid_mask]
            ]

            # change values to numeric (other than k8_school values because the function to calculate differences
            #  anticipates mixed dtypes)
            for col in k8_corp_rate_filtered.columns:
                k8_corp_rate_filtered[col] = pd.to_numeric(
                    k8_corp_rate_filtered[col], errors="coerce"
                )

            # reset index as 'Year'
            k8_corp_rate_filtered = k8_corp_rate_filtered.set_index("Year")

            def calculate_proficiency(proficient_col, tested_col):
                return np.where(
                    (proficient_col == "***") | (tested_col == "***"),
                    "***",
                    np.where(
                        (proficient_col.isna()) & (tested_col.isna()),
                        None,
                        np.where(
                            proficient_col.isna(),
                            0,
                            pd.to_numeric(proficient_col, errors="coerce")
                            / pd.to_numeric(tested_col, errors="coerce"),
                        ),
                    ),
                )

            # iterate over (non missing) columns, calculate the average, and store in a new column
            # TODO: THIS IS INEFFICIENT -> FIX
            # For school calculate all columns
            # for corp rate calculate school columns

            k8_corp_rate_data = k8_corp_rate_filtered.copy()

            categories = ethnicity + status + grades + ["Total"]

            for s in subject:
                for c in categories:
                    new_col = c + "|" + s + " Proficient %"
                    proficient = c + "|" + s + " Total Proficient"
                    tested = c + "|" + s + " Total Tested"

                    if proficient not in missing_cols:
                        k8_school_data[new_col] = calculate_proficiency(
                            k8_school_data[proficient], k8_school_data[tested]
                        )
                        k8_corp_rate_data[new_col] = (
                            k8_corp_rate_data[proficient] / k8_corp_rate_data[tested]
                        )

            # data = [{'A|Red Tested': 55, 'A|Red Passed': 23, 'B|Red Tested':77, 'B|Red Passed': 19, 'A|Blue Tested':77,'A|Blue Passed':25 },
            #         {'A|Red Tested': 100, 'A|Red Passed': 88, 'B|Red Tested':100, 'B|Red Passed': 99, 'A|Blue Tested':100,'A|Blue Passed':2 }]

            # df = pd.DataFrame(data)
            # print(df)
            # # print(proficienty)
            # # print (testedy)
            # # test = pd.DataFrame()
            # # # np.where((x[:, 2] == 861301) & (x[:, 3] == 861393))
            # # test['Proficient %'] = test[proficienty]/test[testedy]
            # # print(test)

            # NOTE: The masking step above removes grades from the corp_rate dataframe that are not also in the school dataframe (e.g., if
            # school only has data for grades 3, 4, & 5, only those grades will remain in corp_rate df). However, the
            # 'Corporation Total' for proficiency in a subject is calculated using ALL grades. So we need to recalculate the 'Corporation Total'
            # rate manually to ensure it includes only the included grades.
            adjusted_corp_total_math_proficient = k8_corp_rate_data.filter(
                regex=r"Grade.+?Math Total Proficient"
            )
            adjusted_corp_total_math_tested = k8_corp_rate_data.filter(
                regex=r"Grade.+?Math Total Tested"
            )
            k8_corp_rate_data[
                "Total|Math Proficient %"
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
                "Total|ELA Proficient %"
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

                # Need this in case where IREAD Test or Pass has '***' value (which results in Nan when divided)
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

            # add text info columns back
            k8_school_data = pd.concat(
                [k8_school_data, k8_school_info], axis=1, join="inner"
            )

            # reset indexes
            k8_school_data = k8_school_data.reset_index(drop=True)
            k8_corp_rate_data = (
                k8_corp_rate_data.reset_index()
            )  # no drop because index was previous set to year

            # ensure columns headers are strings
            k8_school_data.columns = k8_school_data.columns.astype(str)
            k8_corp_rate_data.columns = k8_corp_rate_data.columns.astype(str)

            # freeze corp rate dataframe in current state for use in academic analysis page
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
            k8_school_data = k8_school_data.iloc[
                :, : (k8_num_years + 1)
            ]  # Keep category and all available years of data

            k8_corp_data = (
                k8_corp_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )
            k8_corp_data = k8_corp_data.iloc[
                :, : (k8_num_years + 1)
            ]  # Keep category and all available years of data

            # Drop 'School Name'
            k8_school_data = k8_school_data[
                k8_school_data["Category"].str.contains("School Name") == False
            ]
            k8_school_data = k8_school_data.reset_index(drop=True)

            # reverse order of corp_data columns (ignoring 'Category') so current year is first and
            # get clean list of years
            k8_year_cols = list(k8_school_data.columns[:0:-1])
            k8_year_cols.reverse()

            # Create copy of school dataframe to use later for metric calculations
            k8_school_metric_data = k8_school_data.copy()

            # add_suffix is applied to entire df. To hide columns we dont want renamed, set them as index and reset back after renaming.
            k8_corp_data = (
                k8_corp_data.set_index(["Category"])
                .add_suffix("Corp Rate")
                .reset_index()
            )
            k8_school_data = (
                k8_school_data.set_index(["Category"])
                .add_suffix("School")
                .reset_index()
            )

            # Create list of alternating columns by year (School Value/Similar School Value)
            school_cols = list(k8_school_data.columns[:0:-1])
            school_cols.reverse()

            corp_cols = list(k8_corp_data.columns[:0:-1])
            corp_cols.reverse()

            result_cols = [str(s) + "+/-" for s in k8_year_cols]

            final_cols = list(
                itertools.chain(*zip(school_cols, corp_cols, result_cols))
            )
            final_cols.insert(0, "Category")

            merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
            merged_cols.insert(0, "Category")

            merged_data = k8_school_data.merge(k8_corp_data, on="Category", how="left")
            merged_data = merged_data[merged_cols]

            # temporarily drop 'Category' column to simplify calculating difference
            tmp_category = k8_school_data["Category"]

            k8_school_data = k8_school_data.drop("Category", axis=1)
            k8_corp_data = k8_corp_data.drop("Category", axis=1)

            # calculate difference between school and corp dataframes (with mixed data types)
            def calculate_difference(value1, value2):
                return np.where(
                    (value1 == "***") | (value2 == "***"),
                    "***",
                    np.where(
                        value1.isna(),
                        None,
                        pd.to_numeric(value1, errors="coerce")
                        - pd.to_numeric(value2, errors="coerce"),
                    ),
                )

            k8_result = pd.DataFrame()

            for c in k8_school_data.columns:
                c = c[0:4]  # keeps only YYYY part of string
                k8_result[c + "+/-"] = calculate_difference(
                    k8_school_data[c + "School"], k8_corp_data[c + "Corp Rate"]
                )

            # add headers
            k8_result = k8_result.set_axis(result_cols, axis=1)
            k8_result.insert(loc=0, column="Category", value=tmp_category)

            # combined merged (school and corp) and result dataframes and reorder (according to result columns)
            final_k8_academic_data = merged_data.merge(
                k8_result, on="Category", how="left"
            )

            final_k8_academic_data = final_k8_academic_data[final_cols]

            # TODO: We add Proficient % up above - remove the redundancy?
            # drop 'Proficient %' from all 'Category' rows and remove whitespace
            final_k8_academic_data["Category"] = (
                final_k8_academic_data["Category"]
                .str.replace("Proficient %", "")
                .str.strip()
            )

            # rename IREAD Category
            final_k8_academic_data.loc[
                final_k8_academic_data["Category"] == "IREAD Pass %", "Category"
            ] = "IREAD Proficiency (Grade 3 only)"

            # convert to ordered_dict and then json
            k8_academic_data_dict = final_k8_academic_data.to_dict(into=OrderedDict)
            k8_academic_data_json = json.dumps(k8_academic_data_dict)

            #### Academic Metrics (k8)

            ## Non-comparative indicators
            # NOTE: Need to pull out (and drop from main dataframe) and calculate ratings for any data point that is not comparative
            # (e.g., that is not year over year or diff from school corp)

            # IREAD Data
            iread_data = k8_school_metric_data[
                k8_school_metric_data["Category"] == "IREAD Pass %"
            ]
            k8_school_metric_data = k8_school_metric_data.drop(
                k8_school_metric_data[
                    k8_school_metric_data["Category"] == "IREAD Pass %"
                ].index
            )

            # calculate IREAD metrics

            # NOTE: See code explanation in discussion of 'attendance_data_metrics' above.
            if not iread_data.empty:
                iread_limits = [
                    0.9,
                    0.8,
                    0.7,
                    0.7,
                ]  # metric thresholds for IREAD performance
                iread_data = (
                    iread_data.set_index(["Category"])
                    .add_suffix("School")
                    .reset_index()
                )
                [
                    iread_data.insert(
                        i,
                        str(iread_data.columns[i - 1])[: 7 - 3] + "Rating" + str(i),
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

            ## Comparative (year over year and difference to corporation) indicators

            # Store category column and drop from dataframe to simplify calculation
            category_header = k8_school_metric_data["Category"]
            k8_school_metric_data = k8_school_metric_data.drop("Category", axis=1)

            # temporarily store last column (first year of data chronologically)
            first_year = pd.DataFrame()
            first_year[k8_school_metric_data.columns[-1]] = k8_school_metric_data[
                k8_school_metric_data.columns[-1]
            ]

            # the following function is necessary because a string representing insufficent n-size ('***') is included in
            # the data set and because there are special cases where a '0' result has a different meaning:
            # 1) When Total Tested is the same for two consecutive years and Total Proficient
            #   is *** -> this must be treated as a ***
            # 2) When Total Tested is the same for two consecutive years and Total Proficient is a
            #   number AND is the same (e.g.  2/10 (.20) ??? 2/20 (.20), the difference is also zero -> however, this
            #   must be treated as the number '0'
            # 3) When a school???s first tested year has NO calculation, none tested, none proficient (eg., NaN) and
            #   the school's second tested year is the number 0 (e.g., # tested, 0 proficient) -> this must
            #   somehow be flagged as different than '0' (we use '-***') because the rating should be [DNMS] not [AS]
            # 4) Similarly, if a school goes from *** to 0 -> this must also be '-***' and treated as [DNMS]
            # Flow:
            #   if None in Either Column -> None
            #   if *** in either column -> ***
            #   if # -> subtract
            #   if first value = 0 and second value is *** -> -***
            #   if first value = 0 and second value is NaN -> -***

            year_over_year_values_values = pd.DataFrame()

            def calculate_year_over_year(value1, value2):
                return np.where(
                    (value1 == 0) & ((value2.isna()) | (value2 == "***")),
                    "-***",
                    np.where(
                        (value1 == "***") | (value2 == "***"),
                        "***",
                        np.where(
                            (value1.isna()) & (value2.isna()),
                            None,
                            np.where(
                                (~value1.isna()) & (value2.isna()),
                                value1,
                                pd.to_numeric(value1, errors="coerce")
                                - pd.to_numeric(value2, errors="coerce"),
                            ),
                        ),
                    ),
                )

            # calculate year over year values
            # loops over dataframe calculating difference between col and col+1
            # the final df contains a column for each year showing the difference value between that year and the previous year
            for y in range(0, (len(k8_school_metric_data.columns) - 1)):
                year_over_year_values_values[
                    k8_school_metric_data.columns[y]
                ] = calculate_year_over_year(
                    k8_school_metric_data.iloc[:, y],
                    k8_school_metric_data.iloc[:, y + 1],
                )

            # Add first_year data back
            year_over_year_values_values[first_year.columns] = first_year

            # reorder using k8_year_cols list and add Category back
            year_over_year_values_values = year_over_year_values_values.set_axis(k8_year_cols, axis=1)
            year_over_year_values_values.insert(
                loc=0, column="Category", value=category_header
            )

            # duplicate final academic data in preparation for adding year_over_year data and calculating Ratings
            year_over_year_values = final_k8_academic_data.copy()

            # delete 'Corp Rate' and '+/-' columns as they aren't used in year over year calculation
            year_over_year_values = year_over_year_values.drop(
                [
                    col
                    for col in year_over_year_values.columns
                    if "Corp Rate" in col or "+/-" in col
                ],
                axis=1
            )

            # TODO: See above - is this redundant?
            # clean up df for display
            year_over_year_values_values = (
                year_over_year_values_values.set_index(["Category"])
                .add_suffix("+/-")
                .reset_index()
            )
            year_over_year_values_values["Category"] = (
                year_over_year_values_values["Category"]
                .str.replace("Proficient %", "")
                .str.strip()
            )

            # Create clean col lists - (YYYY + 'School') and (YYYY + '+/-')
            school_years_cols = list(year_over_year_values.columns[1:])
            year_over_year_values_values_cols = list(
                year_over_year_values_values.columns[1:]
            )

            # interweave the above two lists
            merged_years_cols = [
                val
                for pair in zip(school_years_cols, year_over_year_values_values_cols)
                for val in pair
            ]
            merged_years_cols.insert(0, "Category")

            # merge the values for each year (year_over_year_values) with the difference between the values for
            # each year and the previous year (diff_over_years_values)
            year_over_year_values = year_over_year_values.merge(
                year_over_year_values_values, on="Category", how="left"
            )
            year_over_year_values = year_over_year_values[merged_years_cols]

            # duplicate final academic data in preparation for calculating Ratings for diff_to_corp
            diff_to_corp = final_k8_academic_data.copy()

            delta_limits = [
                0.1,
                0.02,
                0,
                0,
            ]  # metric thresholds for difference analysis
            years_limits = [
                0.05,
                0.02,
                0,
                0,
            ]  # metric thresholds for year over year analysis

            # NOTE: See code explanation in discussion of 'attendance_data_metrics' above.
            [
                diff_to_corp.insert(
                    i,
                    str(diff_to_corp.columns[i - 1])[: 7 - 3] + "Rating" + str(i),
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
                year_over_year_values.insert(
                    i,
                    str(year_over_year_values.columns[i - 1])[: 7 - 3]
                    + "Rating"
                    + str(i),
                    year_over_year_values.apply(
                        lambda x: set_academic_rating(
                            x[year_over_year_values.columns[i - 1]], years_limits, 1
                        ),
                        axis=1,
                    ),
                )
                for i in range(year_over_year_values.shape[1], 1, -2)
            ]

            # Replace NaN
            diff_to_corp = diff_to_corp.fillna("No Data")
            year_over_year_values = year_over_year_values.fillna("No Data")

            # ensure all column headers are strings
            diff_to_corp.columns = diff_to_corp.columns.astype(str)
            year_over_year_values.columns = year_over_year_values.columns.astype(str)

            # for the year_over_year df, drop the 'Rating' column for the last year_data column and rename it -
            # we don't use last Rating column becase we cannot calculate a 'year over year'calculation for the first year -
            # it is just the baseline
            year_over_year_values = year_over_year_values.iloc[:, :-2]
            year_over_year_values.columns.values[-1] = (
                year_over_year_values.columns.values[-1] + " (Initial Data Year)"
            )

            diff_to_corp_dict = diff_to_corp.to_dict(into=OrderedDict)
            diff_to_corp_json = json.dumps(diff_to_corp_dict)

            # one last processing step is needed to ensure proper ratings. The set_academic_rating() function assigns a rating based on
            # the '+/-' difference value (either year over year or as compared to corp). For the year over year comparison
            # it is possible to get a rating of 'Approaches Standard' for a '+/-' value of '0.00%' when the yearly ratings
            # are both 0. E.g., both 2022 and 2021 proficiency are both 0% and there is no case where we want a school
            # to receive anything other than a 'DNMS' for a 0% proficiency. However, the set_academic_rating() function does not have
            # access to the values used to calculate the difference value (so it cannot tell if a 0 value is the result of
            # a 0 proficiency). So we manually replace any rating in the Rating column with 'DMNS' where the School proficiency
            # value is '0.00%.'

            # because we are changing the value of one column based on the value of another (paired) column,
            # the way we do this is to create a list of tuples (a list of year and rating column pairs), e.g.,
            # [('2022School', '2022Rating3')], and then iterate over the column pair

            # create the list of tuples
            # NOTE: the zip function stops at the end of the shortest list which automatically drops
            # the single 'Initial Year' column from the list. It returns an empty list if school_years_cols
            # only contains the Initial Year columns (because rating_cols will be empty)
            rating_cols = list(
                col for col in year_over_year_values.columns if "Rating" in col
            )
            col_pair = list(zip(school_years_cols, rating_cols))

            # iterate over list of tuples, if value in first item in pair is zero, change value in second item in pair
            if col_pair:
                for k, v in col_pair:
                    year_over_year_values[v] = np.where(
                        year_over_year_values[k] == 0, "DNMS", year_over_year_values[v]
                    )

            # save to_json
            year_over_year_values_dict = year_over_year_values.to_dict(into=OrderedDict)
            year_over_year_values_json = json.dumps(year_over_year_values_dict)

    #### HS Academic Information ####
    # elapsed = timeit.default_timer() - start_time
    # print("elapsed time:")
    # print(elapsed)

    # NOTE: CHS (School ID: 5874) converted from a K12 to a K8 and separate HS in 2021. We need to make a special exception here
    # to show HS data for CHS prior to 2021. In 2021 and thereafter, the HS data is under CHMWHS (School ID: 9709)

    ## TODO: THIS CONDITIONAL IS BROKEN

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
            # academic_analysis_comp_dict = {} # Use {} or ""?

        # if the school is a HS or K12 -> the ahs json will be empty
        if (
            school_info["School Type"].values[0] == "HS"
            or school_info["School Type"].values[0] == "K12"
            or (school_info["School ID"].values[0] == "5874" and int(year) < 2021)
        ):
            ahs_metrics_data_json = {}

        # remove 'excluded_years' from dataframe and get school data
        filtered_academic_data_hs = all_academic_data_hs[
            ~all_academic_data_hs["Year"].isin(excluded_years)
        ].copy()
        hs_school_data = filtered_academic_data_hs.loc[
            filtered_academic_data_hs["School ID"] == school
        ]

        if len(hs_school_data.index) == 0:
            hs_academic_data_json = {}
            combined_grad_metrics_json = {}
            ahs_metrics_data_json = {}
            # academic_analysis_corp_dict = {}
            # academic_analysis_comp_dict = {}

        else:
            ### TODO:   1) ADD SAT GRADE 11/ACT SCORES (DATASET IS MISSING 2019-2021?)

            # get school and school corporation hs academic data
            hs_corp_data = filtered_academic_data_hs.loc[
                (
                    filtered_academic_data_hs["Corp ID"]
                    == school_info["GEO Corp"].values[0]
                )
            ]

            # tmp remove text columns from dataframe
            hs_school_info = hs_school_data[["School Name"]].copy()

            # drop adult high schools (AHS) from corp avg df
            hs_corp_data = hs_corp_data[
                hs_corp_data["School Type"].str.contains("AHS") == False
            ]

            ## AHS- temporarily pull AHS specific values (CCR and GradAll) that don't have corp equivalent.
            if school_info["School Type"].values[0] == "AHS":
                ahs_data = hs_school_data.filter(regex=r"GradAll$|CCR$", axis=1)

            # keep only those columns used in calculations
            hs_school_data = hs_school_data.filter(
                regex=r"Cohort Count$|Graduates$|Pass N|Test N|^Year$", axis=1
            )
            hs_corp_data = hs_corp_data.filter(
                regex=r"Cohort Count$|Graduates$|Pass N|Test N|^Year$", axis=1
            )

            # remove 'ELA & Math' columns (NOTE: Comment this out to retain 'ELA & Math' columns)
            hs_school_data = hs_school_data.drop(
                list(hs_school_data.filter(regex="ELA & Math")), axis=1
            )
            hs_corp_data = hs_corp_data.drop(
                list(hs_corp_data.filter(regex="ELA & Math")), axis=1
            )

            # valid_mask returns a boolean series of columns where column is true if any element in the column is not equal to null
            valid_mask = ~pd.isnull(hs_school_data[hs_school_data.columns]).all()

            # create list of columns with no data (used in loop below)
            # missing_mask returns boolean series of columns where column is true if all elements in the column are equal to null
            missing_mask = pd.isnull(hs_school_data[hs_school_data.columns]).all()
            missing_cols = hs_school_data.columns[missing_mask].to_list()

            # use valid_mask keep only columns that have at least one value
            hs_school_data = hs_school_data[hs_school_data.columns[valid_mask]]
            hs_corp_data = hs_corp_data[hs_corp_data.columns[valid_mask]]

            # Calculate Graduation Rates
            # Coercing corp values to numeric converts all '***' (insufficient n-size) to NaN which effectively
            # removes the school from the average calculation. This won't have a large effect as there are few
            # traditional public high schools with supressed data.
            # Do not convert school values because the function to calculate differences anticipates mixed dtypes.
            # See:
            # https://towardsdatascience.com/imputing-missing-data-with-simple-and-advanced-techniques-f5c7b157fb87
            # https://cardoai.com/handling-missing-data-with-python/
            for col in hs_corp_data.columns:
                hs_corp_data[col] = pd.to_numeric(hs_corp_data[col], errors="coerce")

            # group corp dataframe by year and sum all rows for each category
            hs_corp_data = hs_corp_data.groupby(["Year"]).sum(numeric_only=True)

            # reverse order of rows (Year) and reset index to bring Year back as column
            hs_corp_data = hs_corp_data.loc[::-1].reset_index()

            # calculate graduation rate
            def calculate_grad_rate(graduate_col, cohort_col):
                return np.where(
                    (graduate_col == "***") | (cohort_col == "***"),
                    "***",
                    np.where(
                        (graduate_col.isna()) & (cohort_col.isna()),
                        None,
                        np.where(
                            graduate_col.isna(),
                            0,
                            pd.to_numeric(graduate_col, errors="coerce")
                            / pd.to_numeric(cohort_col, errors="coerce"),
                        ),
                    ),
                )

            # calculate grad rates
            grad_categories = ethnicity + status + ["Total"]
            for g in grad_categories:
                new_col = g + " Graduation Rate"
                graduates = g + "|Graduates"
                cohort = g + "|Cohort Count"

                if cohort not in missing_cols:
                    hs_school_data[new_col] = calculate_grad_rate(
                        hs_school_data[graduates], hs_school_data[cohort]
                    )
                    hs_corp_data[new_col] = (
                        hs_corp_data[graduates] / hs_corp_data[cohort]
                    )

            # Calculate ECA (Grade 10) rate
            def calculate_eca_rate(passN, testN):
                return np.where(
                    (passN == "***") | (testN == "***"),
                    "***",
                    np.where(
                        (passN.isna()) & (testN.isna()),
                        None,
                        np.where(
                            passN.isna(),
                            0,
                            pd.to_numeric(passN, errors="coerce")
                            / pd.to_numeric(testN, errors="coerce"),
                        ),
                    ),
                )

            # Use ECA data as calculated at the corporation level (from corporation_rates datafile).
            # NOTE:
            # 'Due to suspension of assessments in 2019-2020, Grade 11 students were assessed on ISTEP10 in 2020-2021'
            # 'Results reflect first-time test takers in Grade 11 Cohort (Graduation Year 2022)'
            # 'Results may not be comparable to past years due to assessment of Grade 11'
            hs_corp_rates_filtered = corporation_rates[
                ~corporation_rates["Year"].isin(excluded_years)
            ]
            hs_corp_rate_data = hs_corp_rates_filtered.loc[
                (hs_corp_rates_filtered["Corp ID"] == school_info["GEO Corp"].values[0])
            ].copy()

            # change values to numeric (again not school because function accounts for '***')
            for col in hs_corp_rate_data.columns:
                hs_corp_rate_data[col] = pd.to_numeric(
                    hs_corp_rate_data[col], errors="coerce"
                )

            # NOTE: Because we are going to take the results from one dataframe (hs_corp_rate_data) and add it to
            # another dataframe (hs_corp_data), we need to ensure that the dfs have the same number of years (rows)
            # Special case for 2020 - corp_data exists for 2020 (e.g., grad rate), but no data exists for 2020
            # in corp_rate_data - so there will always be a mismatch - so need to take some additional steps

            # drop all non_matching years from hs_corp_rate_data
            hs_corp_rate_data = hs_corp_rate_data.loc[
                (hs_corp_rate_data["Year"].isin(hs_corp_data["Year"]))
            ]

            # TODO: Test this to see if there are ever any missing years
            # get missing year(s) in hs_corp_rate_data by comparing the difference between two list sets
            # will almost always just be [2020]
            missing_year = list(
                sorted(
                    set(hs_corp_data["Year"].tolist())
                    - set(hs_corp_rate_data["Year"].tolist())
                )
            )

            # reset index
            hs_corp_rate_data = hs_corp_rate_data.reset_index(drop=True)

            # if there is a missing year add new row to hs_corp_rate_data with all blanks except for the year value
            # add the year value to the 'Year' column at last index (most recently added row)
            # append.frame deprecated in favor of concat
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
                    # hs_corp_rate_data = hs_corp_rate_data.append(pd.Series(np.nan, index=hs_corp_rate_data.columns), ignore_index=True)
                    hs_corp_rate_data.at[hs_corp_rate_data.index[-1], "Year"] = y

            # sort columns and reset index so the two df's match
            hs_corp_rate_data = hs_corp_rate_data.sort_values(by="Year", ascending=False)
            hs_corp_rate_data = hs_corp_rate_data.reset_index(drop=True)

            # calculate ECA averages ('Grade 10' + '|ELA/Math' + 'Test N' / 'Grade 10' + '|ELA/Math' + 'Pass N')
            # if none_categories includes 'Grade 10' - there is no ECA data available for the school for the selected Years
            eca_categories = ["Grade 10|ELA", "Grade 10|Math"]

            # checks to see if substring ('Grade 10') is in the list of missing cols
            # this performs substring search on a single combined string (separated by tabs):
            if "Grade 10" not in "\t".join(missing_cols):
                for e in eca_categories:
                    new_col = e + " Pass Rate"
                    passN = e + " Pass N"
                    testN = e + " Test N"

                    hs_school_data[new_col] = calculate_eca_rate(
                        hs_school_data[passN], hs_school_data[testN]
                    )
                    # TODO: Not currently using corp_rate (TODO: Add to Academic Analysis)
                    hs_corp_data[new_col] = (
                        hs_corp_rate_data[passN] / hs_corp_rate_data[testN]
                    )

            ### TODO: I Suspect that I got derailed here and stopped working on hs/ahs data
            ###       Need to revisit this entire section

            # add 'non-waiver grad rate' ('Non-Waiver|Cohort Count' / 'Total|Cohort Count')
            # and 'strength of diploma' (Non-Waiver|Cohort Count` * 1.08) / `Total|Cohort Count`) calculation and average to both dataframes

            # if missing_cols includes 'Non-Waiver' - there is no data available for the school for the selected Years
            if "Non-Waiver" not in "\t".join(missing_cols):
                # NOTE: In spring of 2020, SBOE waived the GQE requirement for students in the 2020 cohort who where otherwise
                # on schedule to graduate, so, for the 2020 cohort, there were no 'waiver' graduates (which means no non-waiver data).
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

                # TODO: forcing conversion causes '***' values to be NaN. We are unlikely to have a '***' value
                # here, but it is possible and we may want to eventually account for this
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

            # Calculate CCR Rate (AHS Only), add Year column and store in temporary dataframe
            # NOTE: ALl other values pulled from HS dataframe required for AHS calculations should happen here
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

                ahs_metric_data = (
                    ahs_school_data.copy()
                )  # Keep original data for metric calculations
                ahs_metric_data = ahs_metric_data.reset_index(drop=True)

            # filter all columns keeping only the relevant ones (NOTE: comment this out to retain all columns)
            hs_school_data = hs_school_data.filter(
                regex=r"^Category|Graduation Rate$|Pass Rate$|^Strength of Diploma|^CCR Percentage|^Year$",
                axis=1,
            )
            hs_corp_data = hs_corp_data.filter(
                regex=r"^Category|Graduation Rate$|Pass Rate$|^Strength of Diploma|^Year$",
                axis=1,
            )

            ## State Avg Graduation Rate

            filtered_academic_data_hs["Total|Graduates"] = pd.to_numeric(
                filtered_academic_data_hs["Total|Graduates"], errors="coerce"
            )
            filtered_academic_data_hs["Total|Cohort Count"] = pd.to_numeric(
                filtered_academic_data_hs["Total|Cohort Count"], errors="coerce"
            )

            # NOTE: exclude AHS from graduation rate calculation due to the inapplicability of grad rates to the model
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

            # merge applicable years of grad_avg dataframe into hs_school df using an inner merge and rename the column
            # this merges data only where both dataframes share a common key, in this case 'Year')
            state_grad_average["Year"] = state_grad_average["Year"].astype(int)
            hs_corp_data = hs_corp_data.merge(
                state_grad_average, on="Year", how="inner"
            )
            hs_corp_data = hs_corp_data.rename(
                columns={"State_Grad_Average": "Average State Graduation Rate"}
            )

            # duplicate 'Total Grad' row and name it 'State Average Graduation Rate' for comparison purposes
            hs_school_data["Average State Graduation Rate"] = hs_school_data[
                "Total Graduation Rate"
            ]

            # reset indicies and concat
            hs_school_info = hs_school_info.reset_index(drop=True)
            hs_school_data = hs_school_data.reset_index(drop=True)
            hs_school_data = pd.concat(
                [hs_school_data, hs_school_info], axis=1, join="inner"
            )

            # ensure columns headers are strings
            hs_school_data.columns = hs_school_data.columns.astype(str)
            hs_corp_data.columns = hs_corp_data.columns.astype(str)

            ### Calculate difference (+/-) between school and corp grad rates

            hs_num_years = len(hs_school_data.index)

            # transpose dataframes and clean headers
            hs_school_data = (
                hs_school_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )
            hs_school_data = hs_school_data.iloc[
                :, : (hs_num_years + 1)
            ]  # Keep category and all available years of data

            hs_corp_data = (
                hs_corp_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )
            hs_corp_data = hs_corp_data.iloc[:, : (hs_num_years + 1)]

            # Drop State/Federal grade rows from school_data (used in 'about' tab, but not here)
            hs_school_data = hs_school_data[
                hs_school_data["Category"].str.contains(
                    "State Grade|Federal Rating|School Name"
                )
                == False
            ]
            hs_school_data = hs_school_data.reset_index(drop=True)

            # get clean list of years
            hs_year_cols = list(hs_school_data.columns[:0:-1])
            hs_year_cols.reverse()

            # add_suffix is applied to entire df. To hide columns we dont want renamed, set them as index and reset back after renaming.
            hs_corp_data = (
                hs_corp_data.set_index(["Category"])
                .add_suffix("Corp Avg")
                .reset_index()
            )
            hs_school_data = (
                hs_school_data.set_index(["Category"])
                .add_suffix("School")
                .reset_index()
            )

            # have to do same things to ahs_data to be able to insert it back into hs_data file even though
            # there is no comparison data involved
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

            # temporarily drop 'Category' column to simplify calculating difference
            tmp_category = hs_school_data["Category"]
            hs_school_data = hs_school_data.drop("Category", axis=1)
            hs_corp_data = hs_corp_data.drop("Category", axis=1)

            # make sure there are no lingering NoneTypes to screw up the creation of hs_results
            hs_school_data = hs_school_data.fillna(value=np.nan)
            hs_corp_data = hs_corp_data.fillna(value=np.nan)

            # calculate graduation rate differences
            def calculate_graduation_rate_difference(school_col, corp_col):
                return np.where(
                    (school_col == "***") | (corp_col == "***"),
                    "***",
                    # np.where((school_col.isna()) & (corp_col.isna()),None,
                    #          np.where(school_col.isna(),0,
                    np.where(
                        school_col.isna(),
                        None,
                        pd.to_numeric(school_col, errors="coerce")
                        - pd.to_numeric(corp_col, errors="coerce"),
                    ),
                )  # )

            # calculate difference between two dataframes
            hs_results = pd.DataFrame()
            for y in hs_year_cols:
                hs_results[y] = calculate_graduation_rate_difference(
                    hs_school_data[y + "School"], hs_corp_data[y + "Corp Avg"]
                )

            # add headers
            hs_results = hs_results.set_axis(result_cols, axis=1)
            hs_results.insert(loc=0, column="Category", value=tmp_category)

            final_hs_academic_data = hs_merged_data.merge(
                hs_results, on="Category", how="left"
            )
            final_hs_academic_data = final_hs_academic_data[final_cols]

            # TODO: Refactor same as k8
            # # Clean up for display for each category:
            # # 1) replace negative values in School column with '***';
            # # 2) replace either '1' or '1.08' in School column with '***';
            # # 3) change '+/-' to '***' if school column is '***'; and
            # # 4) change 'Corp Avg' & '+/-' columns to NaN if School column is NaN
            # # NOTE: we test for 1.08 because of diploma strength calculation (-99 * 1.08 / -99)

            # # for y in hs_year_cols:
            # #     final_hs_academic_data[str(y) + 'School'] = np.where(final_hs_academic_data[str(y) + 'School'] < 0,'***', final_hs_academic_data[str(y) + 'School'])
            # #     final_hs_academic_data[str(y) + 'School'] = np.where(final_hs_academic_data[str(y) + 'School'] == 1,'***', final_hs_academic_data[str(y) + 'School'])
            # #     final_hs_academic_data[str(y) + 'School'] = np.where(final_hs_academic_data[str(y) + 'School'] == 1.08,'***', final_hs_academic_data[str(y) + 'School'])
            # #     final_hs_academic_data[str(y) + '+/-'] = np.where(final_hs_academic_data[str(y) + 'School'] == '***','***', final_hs_academic_data[str(y) + '+/-'])
            # #     final_hs_academic_data[str(y) + 'Corp Avg'] = np.where(final_hs_academic_data[str(y) + 'School'].isnull(), final_hs_academic_data[str(y) + '+/-'], final_hs_academic_data[str(y) + 'Corp Avg'])

            # If AHS - add CCR data to hs_data file
            if school_info["School Type"].values[0] == "AHS":
                final_hs_academic_data = pd.concat(
                    [final_hs_academic_data, ahs_school_data], sort=False
                )  # .fillna(0)
                final_hs_academic_data = final_hs_academic_data.reset_index(drop=True)

            hs_academic_data_dict = final_hs_academic_data.to_dict(into=OrderedDict)
            hs_academic_data_json = json.dumps(hs_academic_data_dict)

            ##### AHS/HS Academic Metrics

            if school_info["School Type"].values[0] == "AHS":
                combined_grad_metrics_json = {}

                # transpose dataframe and clean headers
                ahs_metric_data = (
                    ahs_metric_data.set_index("Year")
                    .T.rename_axis("Category")
                    .rename_axis(None, axis=1)
                    .reset_index()
                )
                ahs_metric_data = ahs_metric_data.iloc[
                    :, : (hs_num_years + 1)
                ]  # Keep category and all available years of data
                ahs_metric_data.columns = ahs_metric_data.columns.astype(str)

                # format for multi-header display
                ahs_metric_cols = list(ahs_metric_data.columns[:0:-1])
                ahs_metric_cols.reverse()

                ahs_metric_data = (
                    ahs_metric_data.set_index(["Category"])
                    .add_suffix("School")
                    .reset_index()
                )

                ahs_metric_data = ahs_metric_data.loc[
                    ahs_metric_data["Category"] == "CCR Percentage"
                ]

                ccr_limits = [0.5, 0.499, 0.234]
                [
                    ahs_metric_data.insert(
                        i,
                        str(ahs_metric_cols[i - 2]) + "Rating" + str(i),
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

                # ensure state_grades df contains same years of data as ahs_metric_cols (drop cols that don't match)
                ahs_state_grades = ahs_state_grades.loc[
                    :,
                    ahs_state_grades.columns.str.contains(
                        "|".join(ahs_metric_cols + ["Category"])
                    ),
                ]

                letter_grade_limits = ["A", "B", "C", "D", "F"]
                [
                    ahs_state_grades.insert(
                        i,
                        str(ahs_metric_cols[i - 2]) + "Rating" + str(i),
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

                # concatenate and add metric column
                ahs_metric_data = pd.concat([ahs_state_grades, ahs_metric_data])
                ahs_metric_data = ahs_metric_data.reset_index(drop=True)
                ahs_metric_nums = ["1.1.", "1.3."]
                ahs_metric_data.insert(loc=0, column="Metric", value=ahs_metric_nums)

                ahs_school_metric_dict = ahs_metric_data.to_dict(into=OrderedDict)
                ahs_metrics_data_json = json.dumps(ahs_school_metric_dict)

            else:
                combined_hs_metrics = final_hs_academic_data.copy()

                # rename 'Corp Avg' to 'Avg'
                combined_hs_metrics.columns = combined_hs_metrics.columns.str.replace(
                    r"Corp Avg", "Avg"
                )

                grad_limits_state = [0, 0.05, 0.15, 0.15]
                state_grad_metric = combined_hs_metrics.loc[
                    combined_hs_metrics["Category"] == "Average State Graduation Rate"
                ]

                [
                    state_grad_metric.insert(
                        i,
                        str(state_grad_metric.columns[i - 1])[: 7 - 3]
                        + "Rating"
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
                local_grad_metric = combined_hs_metrics[
                    combined_hs_metrics["Category"].isin(
                        ["Total Graduation Rate", "Non-Waiver Graduation Rate"]
                    )
                ]
                [
                    local_grad_metric.insert(
                        i,
                        str(local_grad_metric.columns[i - 1])[: 7 - 3]
                        + "Rating"
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

                strength_diploma = combined_hs_metrics[
                    combined_hs_metrics["Category"] == "Strength of Diploma"
                ]
                strength_diploma = strength_diploma[
                    [
                        col
                        for col in strength_diploma.columns
                        if "School" in col or "Category" in col
                    ]
                ]

                ## TODO: NOT CURRENTLY DISPLAYED
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
    dict_of_df = {}

    dict_of_df[0] = school_info_dict
    dict_of_df[1] = school_demographic_selected_year_dict
    dict_of_df[2] = corp_demographic_selected_year_dict
    dict_of_df[3] = school_letter_grades_json
    dict_of_df[4] = attendance_data_json
    dict_of_df[5] = attendance_data_metrics_json
    dict_of_df[6] = school_adm_dict
    dict_of_df[7] = academic_analysis_corp_dict
    dict_of_df[8] = k8_academic_data_json
    dict_of_df[9] = iread_data_json
    dict_of_df[10] = diff_to_corp_json
    dict_of_df[11] = year_over_year_values_json
    dict_of_df[12] = hs_academic_data_json
    dict_of_df[13] = ahs_metrics_data_json
    dict_of_df[14] = combined_grad_metrics_json

    return dict_of_df


@callback(Output("charter-dropdown", "value"), Input("charter-dropdown", "options"))
def set_dropdown_value(charter_options):
    return charter_options[0]["value"]


if __name__ == "__main__":
    app.run_server(debug=True)
#    application.run(host='0.0.0.0', port='8080')
