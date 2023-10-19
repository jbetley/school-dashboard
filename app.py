#########################
# ICSB School Dashboard #
#########################
# author:    jbetley (https://github.com/jbetley)
# version:  1.13
# date:     10/13/23

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
from dash import dcc, html, Input, Output, State, callback

# from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from pages.load_data import (
    get_school_index,
    get_academic_dropdown_years,
    get_financial_info_dropdown_years,
    get_school_dropdown_list,
    get_financial_analysis_dropdown_years,
    get_gradespan,
    get_ethnicity,
    get_subgroup,
)
from pages.layouts import create_radio_layout
from pages.subnav import subnav_academic_information, subnav_academic_analysis

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
class User(UserMixin, db.Model):  # type: ignore
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
def login(message=""):
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
                            return redirect(url)  # redirect to target url
                    return redirect("/")  # redirect to home
                return render_template("login.html", message=message)
            else:
                return render_template("login.html", message=message)
    else:
        if current_user:
            if current_user.is_authenticated:
                return redirect("/")

    return render_template("login.html", message=message)
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
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, maximum-scale=1",
        }
    ],
)

# Top Level Navigation #


# Selected School Dropdown - shows a single school if a ';'school' login is used, an associated
# group of schools if a 'network' login is used, and all schools if 'admin' login is used.
@callback(
    Output("charter-dropdown", "options"),
    [Input("application-state", "children")],  # dummy input
)
def set_dropdown_options(app_state):
    # Get the current user id using the current_user proxy,
    # use the ._get_current_object() method to return the
    # underlying object (User). get the group_id property
    # to determine which schools to include for a network
    # login. NOTE: user 0 is admin; users 1-6 are network logins; users 7- are individual schools
    # Groups: CHA (-1); Excel (-2); GEI (-3); PLA (-4); Paramount (-5); Purdue (-6)
    authorized_user = current_user._get_current_object()
    group_id = current_user.group_id

    available_charters = get_school_dropdown_list()

    # admin user
    if authorized_user.id == 0:
        charters = available_charters

    else:
        # check for network login
        if group_id < 0:
            charters = available_charters[
                available_charters["GroupID"] == str(abs(group_id))
            ]

        else:
            # select only the authorized school using the id field of the authorized_user
            # object. need to subtract 7 to account for Admin and Network Logins (loc 0-6)
            charters = available_charters.iloc[[(authorized_user.id - 7)]]

    dropdown_dict = dict(zip(charters["SchoolName"], charters["SchoolID"]))
    dropdown_list = dict(sorted(dropdown_dict.items()))
    dropdown_options = [
        {"label": name, "value": id} for name, id in dropdown_list.items()
    ]

    return dropdown_options


# Selected School Dropdown - sets the default value to the first school in
# respective list of schools
@callback(Output("charter-dropdown", "value"), Input("charter-dropdown", "options"))
def set_dropdown_value(charter_options):
    return charter_options[0]["value"]


# Selected Year Dropdown -
# options max: 5 years
# values: depend on which page is being accessed and, in some circumstances, the type of
# school (or selected type of school). for academic_information, academic_metrics, and
# academic_analysis pages, 'academic_dropdown_years' are the 5 most recently available
# years of academic data in either academic_data_k8 or academic_data_hs database table.
# for the financial_analysis page, we use a list of the 'year' column names for each
# year for which ADM Average is greater than '0' in the financial_data database table.
# All other pages use 'financial_info_dropdown_years' which is the same as
# 'financial_analysis_dropdown_years' except the quarterly data string (Q#) is removed.


# "url" and "hidden" are used to track the currently selected url
@callback(
    Output("year-dropdown", "options"),
    Output("year-dropdown", "value"),
    Output("hidden", "children"),
    Input("charter-dropdown", "value"),
    Input("url", "href"),
    Input("analysis-type-radio", "value"),
    State("year-dropdown", "value"),
)
def set_year_dropdown_options(
    school_id: str, current_page: str, analysis_type_value: str, year_state: str
):
    max_dropdown_years = 5

    current_page = current_page.rsplit("/", 1)[-1]

    selected_school = get_school_index(school_id)
    school_type = selected_school["School Type"].values[0]

    # for K12 schools, we need to use "HS" data when analysis_type is "hs."" We also
    # want to make sure that we reset the type if the user switches to a k8 school
    # from a AHS/HS/K12 where the analysis_type was "hs"
    if school_type == "K8" and analysis_type_value == "hs":
        analysis_type_value = "k8"

    # Guest schools do not have financial data
    if (
        "academic" in current_page
        or "academic_analysis_single" in current_page
        or "academic_analysis_multiple" in current_page
        or selected_school["Guest"].values[0] == "Y"
    ):
        if (
            "academic_information" in current_page
            or "academic_analysis_single" in current_page
            or "academic_analysis_multiple" in current_page
        ) and analysis_type_value == "hs":
            years = get_academic_dropdown_years(school_id, "HS")
        else:
            years = get_academic_dropdown_years(school_id, school_type)

    elif "financial_analysis" in current_page:
        years = get_financial_analysis_dropdown_years(school_id)

    else:
        years = get_financial_info_dropdown_years(school_id)

    # set year_value and year_options
    number_of_years_to_display = (
        len(years) if len(years) <= max_dropdown_years else max_dropdown_years
    )
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

    if year_state is None:
        year_value = str(first_available_year)

    elif int(year_state) < int(earliest_available_year):
        year_value = str(earliest_available_year)

    elif int(year_state) > int(first_available_year):
        year_value = str(first_available_year)

    else:
        year_value = str(year_state)

    # K8 schools do not have data for 2020 - so that year should never appear in the dropdown.
    # HS, AHS, and K12 schools with the "HS" academic_type_radio button selected could have 2020 data-
    # school_type generally takes care of this for K8, HS, and AHS schools, but not K12
    if (
        (
            "academic" in current_page
            or "academic_analysis_single" in current_page
            or "academic_analysis_multiple" in current_page
            or selected_school["Guest"].values[0] == "Y"
        )
        and (
            (school_type == "K8")
            or (school_type == "K12" and analysis_type_value == "k8")
        )
        and year_state == "2020"
    ):
        year_value = "2019"

    if not dropdown_years:
        raise Exception(
            "There is simply no way that you can be seeing this error message."
        )  # except i saw it once

    year_options = [{"label": str(y), "value": str(y)} for y in dropdown_years]

    return year_options, year_value, current_page


# Need to put this into its own callback in order to avoid circular callbacks.
@callback(
    Output("analysis-type-radio", "options"),
    Output("analysis-type-radio", "value"),
    Output("analysis-type-radio-container", "style"),
    Input("charter-dropdown", "value"),
    Input("analysis-type-radio", "value"),
)
def get_school_type(school_id: str, analysis_type_value: str):
    selected_school = get_school_index(school_id)
    school_type = selected_school["School Type"].values[0]

    type_options_default = [
        {"label": "K8", "value": "k8"},
        {"label": "High School", "value": "hs"},
    ]

    if not analysis_type_value:
        if school_type == "HS" or school_type == "AHS":
            analysis_type_value = "hs"
        else:
            analysis_type_value = "k8"

    # analysis-type: used for both pages - is the only subnavigation
    # for analysis_single_year.py
    if school_type == "K12":
        analysis_type_options = type_options_default

        if analysis_type_value in ["k8", "hs"]:
            analysis_type_value = analysis_type_value
        else:
            analysis_type_value = "k8"

        analysis_type_container = {"display": "block"}

    else:
        analysis_type_value = "k8"
        analysis_type_options = []
        analysis_type_container = {"display": "none"}

    return analysis_type_options, analysis_type_value, analysis_type_container


# Subnavigation - Year Dropdown #
# NOTE: There are no doubt better ways to structure this; however, given how complicated
# it is and how the values are interlinked, in order to avoid circular callbacks, we are
# using a single callback
@callback(
    Output("academic-information-type-radio", "options"),
    Output("academic-information-type-radio", "value"),
    Output("academic-information-type-radio-container", "style"),
    Output("academic-information-category-radio", "options"),
    Output("academic-information-category-radio", "value"),
    Output("academic-information-category-radio-container", "style"),
    Output("academic-information-subnav-container", "style"),
    Output("academic-information-navigation-container", "style"),
    # Output("analysis-type-radio", "options"),
    # Output("analysis-type-radio", "value"),
    # Output("analysis-type-radio-container", "style"),
    Output("analysis-multi-hs-group-radio", "options"),
    Output("analysis-multi-hs-group-radio", "value"),
    Output("analysis-multi-hs-group-radio-container", "style"),
    Output("analysis-multi-subject-radio", "options"),
    Output("analysis-multi-subject-radio", "value"),
    Output("analysis-multi-subject-radio-container", "style"),
    Output("analysis-multi-category-radio", "options"),
    Output("analysis-multi-category-radio", "value"),
    Output("analysis-multi-category-radio-container", "style"),
    Output("analysis-multi-subcategory-radio", "options"),
    Output("analysis-multi-subcategory-radio", "value"),
    Output("analysis-multi-subcategory-radio-container", "style"),
    Output("analysis-subnav-container", "style"),
    Output("analysis-navigation-container", "style"),
    Input("url", "href"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("academic-information-type-radio", "value"),
    Input("analysis-multi-hs-group-radio", "value"),
    Input("analysis-multi-category-radio", "value"),
    Input("analysis-multi-subcategory-radio", "value"),
    Input("analysis-type-radio", "value"),
    State("academic-information-category-radio", "options"),
    State("academic-information-category-radio", "value"),
    State("analysis-multi-subject-radio", "value"),
)
def navigation(
    current_page: str,
    school_id: str,
    year_value: str,
    info_type_value: str,
    analysis_hs_group_value: str,
    analysis_multi_category_value: str,
    analysis_multi_subcategory_value: str,
    analysis_type_state: str,
    info_category_options_state: list,
    info_category_value_state: str,
    analysis_multi_subject_state: str,
):
    selected_school = get_school_index(school_id)
    school_type = selected_school["School Type"].values[0]

    current_page = current_page.rsplit("/", 1)[-1]

    type_options_default = [
        {"label": "K8", "value": "k8"},
        {"label": "High School", "value": "hs"},
    ]

    # academic_information.py and academic_information_growth.py
    if "academic_info" in current_page:
        # hide academic analysis navigation
        analysis_type_state = "k8"
        # analysis_type_options = []
        # analysis_type_container = {"display": "none"}

        analysis_multi_hs_group_options = []
        analysis_multi_hs_group_value = ""
        analysis_multi_hs_group_container = {"display": "none"}

        analysis_multi_subject_options = []  # type: list
        analysis_multi_subject_value = ""
        analysis_multi_subject_container = {"display": "none"}

        analysis_multi_category_options = []
        analysis_multi_category_value = ""
        analysis_multi_category_container = {"display": "none"}

        analysis_multi_subcategory_options = []  # type: list
        analysis_multi_subcategory_value = ""
        analysis_multi_subcategory_container = {"display": "none"}

        analysis_nav_container = {"display": "none"}
        analysis_subnav_container = {"display": "none"}

        # begin academic_info navigation
        info_nav_container = {"display": "block"}

        category_options_default = [
            {"label": "All Data", "value": "all"},
            {"label": "By Grade", "value": "grade"},
            {"label": "By Ethnicity", "value": "ethnicity"},
            {"label": "By Subgroup", "value": "subgroup"},
        ]

        # no subnavigation is displayed for HS/AHS
        if school_type == "HS" or school_type == "AHS":
            info_subnav_container = {"display": "none"}

            info_type_options = []  # type: list
            info_type_value = "hs"
            info_type_container = {"display": "none"}

            info_category_options = []
            info_category_value = ""
            info_category_container = {"display": "none"}

        # categories of K8 schools
        elif school_type == "K8":
            info_subnav_container = {"display": "block"}

            info_type_options = []
            info_type_value = "k8"
            info_type_container = {"display": "none"}

            if info_category_value_state:
                info_category_value = info_category_value_state
            else:
                info_category_value = "all"

            if info_category_options_state:
                info_category_options = info_category_options_state
            else:
                info_category_options = category_options_default

            info_category_container = {"display": "block"}

        # categories for K12 schools who have selected a type of 'k8'
        # note that academic_information_growth.py does not have a type radio button
        elif school_type == "K12" and (info_type_value == "k8" or not info_type_value):
            info_subnav_container = {"display": "block"}

            if current_page == "academic_information_growth":
                info_type_options = []
                info_type_value = "k8"
                info_type_container = {"display": "none"}

            else:
                info_type_options = type_options_default

                if info_type_value in ["k8", "hs"]:
                    info_type_value = info_type_value
                else:
                    info_type_value = "k8"
                info_type_container = {"display": "block"}

            if info_category_value_state:
                info_category_value = info_category_value_state
            else:
                info_category_value = "all"

            if info_category_options_state:
                info_category_options = info_category_options_state
            else:
                info_category_options = category_options_default

            info_category_container = {"display": "block"}

        # no subnavigation for K12 school that has selected a type of "hs"
        elif school_type == "K12" and info_type_value == "hs":
            info_subnav_container = {"display": "none"}

            info_type_options = type_options_default

            if info_type_value in ["k8", "hs"]:
                info_type_value = info_type_value
            else:
                info_type_value = "k8"

            info_type_container = {"display": "block"}

            info_category_options = []
            info_category_value = ""
            info_category_container = {"display": "none"}

    # analysis_single_year.py and analysis_multiple_years.py
    elif "academic_analysis" in current_page:
        # hide academic information subnavigation
        info_nav_container = {"display": "none"}
        info_subnav_container = {"display": "none"}
        info_type_container = {"display": "none"}
        info_category_container = {"display": "none"}

        info_type_options = []
        info_type_value = ""

        info_category_options = []
        info_category_value = ""

        # begin analysis sub_navigation
        analysis_nav_container = {"display": "block"}
        analysis_subnav_container = {"display": "block"}

        # # set default if empty
        # if not analysis_type_state:
        #     if school_type == "HS" or school_type == "AHS":
        #         analysis_type_state = "hs"
        #     else:
        #         analysis_type_state = "k8"

        # # analysis-type: used for both pages - is the only subnavigation
        # # for analysis_single_year.py
        # if school_type == "K12":
        #     # analysis_type_options = type_options_default

        #     if analysis_type_state in ["k8", "hs"]:
        #         analysis_type_state = analysis_type_state
        #     else:
        #         analysis_type_state = "k8"

        #     # analysis_type_container = {"display": "block"}

        # else:
        #     analysis_type_state = "k8"
        # analysis_type_options = []
        # analysis_type_container = {"display": "none"}

        # analysis_multiple_years.py
        if "analysis_multiple" in current_page:
            # group button for HS/AHS/K12 (hs type)
            if (
                school_type == "HS"
                or school_type == "AHS"
                or (school_type == "K12" and analysis_type_state == "hs")
            ):
                analysis_multi_hs_group_options = [
                    {"label": "Graduation Rate", "value": "Graduation Rate"},
                    {"label": "SAT", "value": "SAT"},
                ]

                analysis_multi_hs_group_container = {"display": "block"}

                if analysis_hs_group_value:
                    analysis_multi_hs_group_value = analysis_hs_group_value
                else:
                    analysis_multi_hs_group_value = "Graduation Rate"

            else:
                analysis_multi_hs_group_options = []
                analysis_multi_hs_group_value = ""
                analysis_multi_hs_group_container = {"display": "none"}

            # category button for HS/AHS/K12 (hs type)
            if (
                school_type == "HS"
                or school_type == "AHS"
                or (school_type == "K12" and analysis_type_state == "hs")
            ):
                # graduation rate categories
                if (
                    analysis_multi_hs_group_value == "Graduation Rate"
                    or analysis_multi_hs_group_value == ""
                ):
                    # hide subject and subcategory
                    analysis_multi_subject_value = ""
                    analysis_multi_subject_options = []
                    analysis_multi_subject_container = {"display": "none"}

                    analysis_multi_category_options = [
                        {"label": "Total", "value": "Total"},
                        {"label": "Subgroup", "value": "Subgroup"},
                        {"label": "Race/Ethnicity", "value": "Race/Ethnicity"},
                    ]
                    analysis_multi_category_container = {"display": "block"}

                    if analysis_multi_category_value in [
                        "Total",
                        "Subgroup",
                        "Race/Ethnicity",
                    ]:
                        analysis_multi_category_value = analysis_multi_category_value
                    else:
                        analysis_multi_category_value = "Total"

                # SAT subject and categories (SAT is only group that has subject values
                # other than ELA & Math)

                elif analysis_multi_hs_group_value == "SAT":
                    analysis_multi_subject_options = [
                        {"label": "EBRW", "value": "EBRW"},
                        {"label": "Math", "value": "Math"},
                    ]
                    analysis_multi_subject_container = {"display": "block"}

                    if analysis_multi_subject_state in ["EBRW", "Math"]:
                        analysis_multi_subject_value = analysis_multi_subject_state
                    else:
                        analysis_multi_subject_value = "EBRW"

                    analysis_multi_category_options = [
                        {"label": "School Total", "value": "School Total"},
                        {"label": "Subgroup", "value": "Subgroup"},
                        {"label": "Race/Ethnicity", "value": "Race/Ethnicity"},
                    ]
                    analysis_multi_category_container = {"display": "block"}

                    if analysis_multi_category_value in [
                        "School Total",
                        "Subgroup",
                        "Race/Ethnicity",
                    ]:
                        analysis_multi_category_value = analysis_multi_category_value
                    else:
                        analysis_multi_category_value = "School Total"

            else:
                # subject and categories for K8 and K12 (k8 type)
                if school_type == "K8" or (
                    school_type == "K12" and analysis_type_state == "k8"
                ):
                    analysis_multi_subject_options = [
                        {"label": "ELA", "value": "ELA"},
                        {"label": "Math", "value": "Math"},
                    ]
                    analysis_multi_subject_container = {"display": "block"}

                    if analysis_multi_subject_state in ["ELA", "Math"]:
                        analysis_multi_subject_value = analysis_multi_subject_state
                    else:
                        analysis_multi_subject_value = "ELA"

                    analysis_multi_category_options = [
                        {"label": "Grade", "value": "Grade"},
                        {"label": "Subgroup", "value": "Subgroup"},
                        {"label": "Race/Ethnicity", "value": "Race/Ethnicity"},
                    ]
                    analysis_multi_category_container = {"display": "block"}

                    if analysis_multi_category_value in [
                        "Grade",
                        "Subgroup",
                        "Race/Ethnicity",
                    ]:
                        analysis_multi_category_value = analysis_multi_category_value
                    else:
                        analysis_multi_category_value = "Grade"

            # get years for subcategoires
            # TODO: The following is a duplication of code from year-dropdown. Need
            # TODO: to switch this with an Input value for dropdown-year, "options".
            if school_type == "K8" and analysis_type_state == "hs":
                analysis_type_state = "k8"

            # Guest schools do not have financial data
            if (
                "academic" in current_page
                or "analysis_single" in current_page
                or "analysis_multiple" in current_page
                or selected_school["Guest"].values[0] == "Y"
            ):
                if (
                    "academic_information" in current_page
                    or "analysis_single" in current_page
                    or "analysis_multiple" in current_page
                ) and analysis_type_state == "hs":
                    years = get_academic_dropdown_years(school_id, "HS")

                else:
                    years = get_academic_dropdown_years(school_id, school_type)

            # subcategories for all schools
            if analysis_multi_category_value == "Grade":
                grades = get_gradespan(school_id, year_value, years)

                if grades:
                    analysis_multi_subcategory_options = [
                        {"label": g, "value": "Grade " + g} for g in grades
                    ]
                    analysis_multi_subcategory_options.append(
                        {"label": "Total", "value": "School Total"}
                    )

                    grade_strings = ["Grade " + g for g in grades]

                    if analysis_multi_subcategory_value in grade_strings:
                        analysis_multi_subcategory_value = (
                            analysis_multi_subcategory_value
                        )
                    else:
                        analysis_multi_subcategory_value = "School Total"

                    analysis_multi_subcategory_container = {"display": "block"}

                else:
                    analysis_multi_subcategory_options = []
                    analysis_multi_subcategory_value = "No Data"
                    analysis_multi_subcategory_container = {"display": "block"}

            elif analysis_multi_category_value == "Race/Ethnicity":
                ethnicity = get_ethnicity(
                    school_id,
                    analysis_type_state,
                    analysis_multi_hs_group_value,
                    year_value,
                    years,
                )
                analysis_multi_subcategory_options = [
                    {"label": e, "value": e} for e in ethnicity
                ]
                ethnicity.sort()

                if ethnicity:
                    if analysis_multi_subcategory_value in ethnicity:
                        analysis_multi_subcategory_value = (
                            analysis_multi_subcategory_value
                        )
                    else:
                        analysis_multi_subcategory_value = ethnicity[0]

                    analysis_multi_subcategory_container = {"display": "block"}

                else:
                    analysis_multi_subcategory_options = []
                    analysis_multi_subcategory_value = "No Race/Ethnicity Data"
                    analysis_multi_subcategory_container = {"display": "block"}

            elif analysis_multi_category_value == "Subgroup":
                subgroup = get_subgroup(
                    school_id,
                    analysis_type_state,
                    analysis_multi_hs_group_value,
                    year_value,
                    years,
                )
                subgroup.sort()

                if subgroup:
                    analysis_multi_subcategory_options = [
                        {"label": s, "value": s} for s in subgroup
                    ]
                    print(subgroup)
                    print(analysis_multi_subcategory_value)
                    if analysis_multi_subcategory_value in subgroup:
                        analysis_multi_subcategory_value = (
                            analysis_multi_subcategory_value
                        )

                    else:
                        analysis_multi_subcategory_value = subgroup[0]

                    analysis_multi_subcategory_container = {"display": "block"}

                else:
                    analysis_multi_subcategory_options = []
                    analysis_multi_subcategory_value = "No Subgroup Data"
                    analysis_multi_subcategory_container = {"display": "block"}

            # for SAT ('School Total') and Grad Rate ('Total) set single value,
            # with no options
            else:
                if analysis_multi_hs_group_value == "SAT":
                    analysis_multi_subcategory_value = "School Total"

                else:  # graduation Rate
                    analysis_multi_subcategory_value = "Total"

                analysis_multi_subcategory_options = []
                analysis_multi_subcategory_container = {"display": "none"}

        else:  # analysis_single_year page has no radio buttons other than 'type'
            analysis_multi_subcategory_options = []
            analysis_multi_subcategory_value = ""
            analysis_multi_subcategory_container = {"display": "none"}

            analysis_multi_hs_group_options = []
            analysis_multi_hs_group_value = ""
            analysis_multi_hs_group_container = {"display": "none"}

            analysis_multi_subject_options = []
            analysis_multi_subject_value = ""
            analysis_multi_subject_container = {"display": "none"}

            analysis_multi_category_options = []
            analysis_multi_category_value = ""
            analysis_multi_category_container = {"display": "none"}

    # all other pages have no sub_navigation (other than Financal Tabs
    # [School][Network] subnavigation - those are currently part of the individual
    # pages)
    # TODO: Move Financial Tab [School][Network] subnavigation here
    else:
        # analysis both
        analysis_type_state = "k8"
        # analysis_type_options = []
        # analysis_type_container = {"display": "none"}

        # analysis multi
        analysis_nav_container = {"display": "none"}
        analysis_subnav_container = {"display": "none"}

        analysis_multi_hs_group_options = []
        analysis_multi_hs_group_value = ""
        analysis_multi_hs_group_container = {"display": "none"}

        analysis_multi_subject_options = []
        analysis_multi_subject_value = ""
        analysis_multi_subject_container = {"display": "none"}

        analysis_multi_category_options = []
        analysis_multi_category_value = ""
        analysis_multi_category_container = {"display": "none"}

        analysis_multi_subcategory_options = []
        analysis_multi_subcategory_value = ""
        analysis_multi_subcategory_container = {"display": "none"}

        # academic info
        info_nav_container = {"display": "none"}
        info_subnav_container = {"display": "none"}
        info_type_container = {"display": "none"}
        info_category_container = {"display": "none"}

        info_type_options = []
        info_type_value = ""

        info_category_options = []
        info_category_value = ""

    return (
        info_type_options,
        info_type_value,
        info_type_container,
        info_category_options,
        info_category_value,
        info_category_container,
        info_subnav_container,
        info_nav_container,
        # analysis_type_options,
        # analysis_type_state,
        # analysis_type_container,
        analysis_multi_hs_group_options,
        analysis_multi_hs_group_value,
        analysis_multi_hs_group_container,
        analysis_multi_subject_options,
        analysis_multi_subject_value,
        analysis_multi_subject_container,
        analysis_multi_category_options,
        analysis_multi_category_value,
        analysis_multi_category_container,
        analysis_multi_subcategory_options,
        analysis_multi_subcategory_value,
        analysis_multi_subcategory_container,
        analysis_subnav_container,
        analysis_nav_container,
    )


# redirects the url from academic_information_growth.py to
# academic_information.py if the user is at academic_information_growth
# url and selects a HS, AHS, & K12(hs type)
@callback(
    Output("url", "href"), Input("charter-dropdown", "value"), Input("url", "href")
)
def redirect_hs(school: str, current_page: str):
    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]

    current_page = current_page.rsplit("/", 1)[-1]

    if current_page == "academic_information_growth" and (
        school_type == "HS" or school_type == "AHS"
    ):
        return f"/academic_information"
    else:
        return dash.no_update


# app.layout = html.Div(
# NOTE: Test to see effect of layout as function vs. variable
def layout():
    return html.Div(
        [
            dcc.Location(id="url", refresh="callback-nav"),
            html.Div(id="hidden", style={"display": "none"}),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.A(
                                        "logout",
                                        href="../logout",
                                        className="logout-button",
                                    ),
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
                                    html.Div(
                                        id="application-state",
                                        style={"display": "none"},
                                    ),
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
                                                        active="exact",
                                                    ),
                                                    dbc.NavLink(
                                                        "Financial Information",
                                                        href="/financial_information",
                                                        className="tab",
                                                        active="exact",
                                                    ),
                                                    dbc.NavLink(
                                                        "Financial Metrics",
                                                        href="/financial_metrics",
                                                        className="tab",
                                                        active="exact",
                                                    ),
                                                    dbc.NavLink(
                                                        "Financial Analysis",
                                                        href="/financial_analysis",
                                                        className="tab",
                                                        active="exact",
                                                    ),
                                                    dbc.NavLink(
                                                        "Organizational Compliance",
                                                        href="/organizational_compliance",
                                                        className="tab",
                                                        active="exact",
                                                    ),
                                                    # hardcoding this instead of using a loop so that we
                                                    # can manually add this break
                                                    html.Br(),
                                                    html.Div(
                                                        style={"marginTop": "17px"}
                                                    ),
                                                    dbc.NavLink(
                                                        "Academic Information",
                                                        href="/academic_information",
                                                        className="tab",
                                                        active="exact",
                                                    ),
                                                    dbc.NavLink(
                                                        "Academic Metrics",
                                                        href="/academic_metrics",
                                                        className="tab",
                                                        active="exact",
                                                    ),
                                                    dbc.NavLink(
                                                        "Academic Analysis",
                                                        href="/academic_analysis_single_year",
                                                        className="tab",
                                                        active="exact",
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
                    # Subnavigation #
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        subnav_academic_information(),
                                                        id="subnav-academic-info",
                                                        className="tabs",
                                                    ),
                                                ],
                                                className="bare-container--flex--center twelve columns",
                                            ),
                                        ],
                                        className="row",
                                    ),
                                ],
                                id="academic-information-subnav-container",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                create_radio_layout(
                                                    "academic-information", "type"
                                                ),
                                                className="tabs",
                                            ),
                                        ],
                                        className="bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className="row",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                create_radio_layout(
                                                    "academic-information", "category"
                                                ),
                                                className="tabs",
                                            ),
                                        ],
                                        className="bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className="row",
                            ),
                        ],
                        id="academic-information-navigation-container",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        subnav_academic_analysis(),
                                                        id="subnav-academic-analysis",
                                                        className="tabs",
                                                    ),
                                                ],
                                                className="bare-container--flex--center twelve columns",
                                            ),
                                        ],
                                        className="row",
                                    ),
                                ],
                                id="analysis-subnav-container",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                create_radio_layout("analysis", "type"),
                                                className="tabs",
                                            ),
                                        ],
                                        className="bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className="row",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                create_radio_layout(
                                                    "analysis-multi", "hs-group"
                                                ),
                                                className="tabs",
                                            ),
                                        ],
                                        className="bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className="row",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                create_radio_layout(
                                                    "analysis-multi", "subject", "six"
                                                ),
                                                className="tabs",
                                            ),
                                            html.Div(
                                                create_radio_layout(
                                                    "analysis-multi", "category", "six"
                                                ),
                                                className="tabs",
                                            ),
                                        ],
                                        className="bare-container--flex--center_subnav twelve columns",
                                    ),
                                ],
                                className="row",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                create_radio_layout(
                                                    "analysis-multi", "subcategory"
                                                ),
                                                className="tabs",
                                            ),
                                        ],
                                        className="bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className="row",
                            ),
                        ],
                        id="analysis-navigation-container",
                    ),
                    # dash page content
                    dash.page_container,
                ],
            ),
        ],
    )


# testing layout as a function - not sure its faster
app.layout = layout

if __name__ == "__main__":
    app.run_server(debug=True)
#    application.run(host="0.0.0.0", port="8080")
