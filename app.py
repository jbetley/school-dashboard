#########################
# ICSB School Dashboard #
#########################
# author:    jbetley
# date:         08/15/22

import dash
from dash import dcc, html, Input, Output
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
import os.path
import sys  # calculates size of nested dict

external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=Roboto:400",
]

app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)

# AWS: Was getting circular import issue until I moved the apps import BELOW the app instantiation
from apps import (
    aboot,
    financial_analysis,
    financial_information,
    financial_metrics,
    academic_information_k12,
    academic_metrics,
    academic_analysis,
    organizational_compliance,
)


# Functions
def get_size(obj, seen=None):
    # Recursively finds size of objects
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, "__dict__"):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size


## Styles
tabs_styles = {
    "zIndex": 99,
    "display": "inline-block",
    "height": "6vh",
    "width": "85vw",
    "position": "relative",
    #    'top': '12.5vh',
    "left": "2vw",
}

tab_style = {
    "textTransform": "uppercase",
    "fontFamily": "Roboto, sans-serif",
    "color": "steelblue",
    "fontSize": "12px",
    "fontWeight": "400",
    "alignItems": "center",
    "justifyContent": "center",
    "border": "1px solid rgba(192,193,199, .5)",
    "borderRadius": ".5rem",
    "padding": "6px",
}

tab_selected_style = {
    "textTransform": "uppercase",
    "fontFamily": "Roboto, sans-serif",
    "color": "white",
    "fontSize": "12px",
    "fontWeight": "700",
    "alignItems": "center",
    "justifyContent": "center",
    "background": "#c0c1c7",
    "border": "1px solid rgba(70,130,180, .5)",
    "borderadius": ".5rem",
    "padding": "6px",
}

# category variables
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
grades = ["Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"]
eca = ["Grade 10|ELA", "Grade 10|Math"]
info = ["Year", "School Type"]
subject = ["Math", "ELA"]

## Load Data Files ##
print("#### Loading Data. . . . . ####")

index = pd.read_csv(r"data/school_index.csv", dtype=str)
k8_academic_data = pd.read_csv(r"data/academic_data1922.csv", dtype=str)
hs_academic_data = pd.read_csv(r"data/academic_data_hs1921.csv", dtype=str)

demographics = pd.read_csv(
    r"data/demographic_data1922.csv", dtype=str
)  ## TODO: Missing 2022 Status (ELL/Special Education) Demographic Data
adm = pd.read_csv(r"data/adm.csv", dtype=str)

# Fixes issue where converting string to int adds trailing '.0'
k8_academic_data["Low Grade"] = (
    k8_academic_data["Low Grade"].astype(str).str.replace(".0", "", regex=False)
)
k8_academic_data["High Grade"] = (
    k8_academic_data["High Grade"].astype(str).str.replace(".0", "", regex=False)
)

# Get current year - demographic data will almost always be more current than academic data (due to IDOE release cadence)
# NOTE: had to add str() to year dropdown post update from dash 2.31 -> 2.51
current_year = k8_academic_data["Year"].unique().max()

# Build dropdown list #
charters = index[["School Name", "School ID", "School Type"]]
charter_dict = dict(zip(charters["School Name"], charters["School ID"]))
charter_list = dict(sorted(charter_dict.items()))

app.layout = html.Div(
    [
        dcc.Store(id="dash-session", storage_type="session"),
        html.Div(
            [
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
                            options=[
                                {"label": name, "value": id}
                                for name, id in charter_list.items()
                            ],
                            style={
                                "fontSize": "85%",
                                "fontFamily": "Roboto, sans-serif",
                            },
                            multi=False,
                            clearable=False,
                            className="school_dash_control",
                        ),
                    ],
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Select Accountability Year:"),
                            ],
                            className="dash_label",
                            id="year_dash_label",
                        ),
                        dcc.Dropdown(
                            id="year-dropdown",
                            options=[
                                {"label": str(y), "value": str(y)}
                                for y in range(
                                    int(current_year) - 3, int(current_year) + 1
                                )
                            ],
                            style={
                                "fontSize": "85%",
                                "fontFamily": "Roboto, sans-serif",
                            },
                            value=current_year,
                            multi=False,
                            clearable=False,
                            className="year_dash_control",
                        ),
                    ],
                    className="pretty_container five columns",
                ),
            ],
            className="row",
        ),
        html.Div(
            [
                dcc.Tabs(
                    id="tabs",
                    value="tab-1",
                    children=[
                        dcc.Tab(
                            label="About",
                            value="tab-1",
                            style=tab_style,
                            selected_style=tab_selected_style,
                        ),
                        dcc.Tab(
                            label="Financial Performance",
                            value="tab-2",
                            style=tab_style,
                            selected_style=tab_selected_style,
                            children=[
                                dcc.Tabs(
                                    id="subtab2",
                                    value="subtab2-1",
                                    children=[
                                        dcc.Tab(
                                            label="Financial Information",
                                            value="subtab2-1",
                                            style=tab_style,
                                            selected_style=tab_selected_style,
                                        ),
                                        dcc.Tab(
                                            label="Financial Metrics",
                                            value="subtab2-2",
                                            style=tab_style,
                                            selected_style=tab_selected_style,
                                        ),
                                        dcc.Tab(
                                            label="Financial Analysis",
                                            value="subtab2-3",
                                            style=tab_style,
                                            selected_style=tab_selected_style,
                                        ),
                                    ],
                                )
                            ],
                        ),
                        dcc.Tab(
                            label="Academic Performance",
                            value="tab-3",
                            style=tab_style,
                            selected_style=tab_selected_style,
                            children=[
                                dcc.Tabs(
                                    id="subtab3",
                                    value="subtab3-1",
                                    children=[
                                        dcc.Tab(
                                            label="Academic Information",
                                            value="subtab3-1",
                                            style=tab_style,
                                            selected_style=tab_selected_style,
                                        ),
                                        dcc.Tab(
                                            label="Academic Metrics",
                                            value="subtab3-2",
                                            style=tab_style,
                                            selected_style=tab_selected_style,
                                        ),
                                        dcc.Tab(
                                            label="Academic Analysis",
                                            value="subtab3-3",
                                            style=tab_style,
                                            selected_style=tab_selected_style,
                                        ),
                                    ],
                                )
                            ],
                        ),
                        dcc.Tab(
                            label="Organizational Compliance",
                            value="tab-4",
                            style=tab_style,
                            selected_style=tab_selected_style,
                        ),
                    ],
                    style=tabs_styles,
                ),
            ],
            className="no-print",
        ),
        html.Div(
            id="tabs-content",
        ),
    ]
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

    school_name = index.loc[index["School ID"] == school, ["School Name"]].values[0][
        0
    ]  # returns the first (only) element from list
    corp_id = index.loc[index["School ID"] == school, ["Corporation ID"]].values[0][
        0
    ]  # returns the first (only) element from list

    finance_file = "data/F-" + school_name + ".csv"

    school_index = index.loc[index["School ID"] == school]
    index_dict = school_index.to_dict()  # dict[0]

    # current_year is the most current year of available 'Academic' data / year is selected year
    num_years_to_remove = int(current_year) - int(year)

    # School Financial Information
    if os.path.isfile(finance_file):
        school_finance = pd.read_csv(finance_file)

        # filter dataframe to show data beginning with selected year
        # col[0] = category, col[1] - col[n] are years in descending order with col[1] as most recent year
        # 'current_year' - selected 'year' equals the number of columns from col[1] we need to remove
        # e.g., if 2019 is selected, we need to remove 2 columns -> col[1] & col[2] (2021 & 2020)
        if num_years_to_remove != 0:  # if num_years_to_remove == 0, year = current_year
            school_finance.drop(
                school_finance.columns[1:num_years_to_remove], axis=1, inplace=True
            )

        # if a school doesn't have data for the selected year, df will only have 1 column (Category)
        if len(school_finance.columns) <= 1:
            school_finance_dict = {}

        else:
            # default is to only show 5 years of accountability data (remove this to show all data)
            # select only up to the first 6 columns of the financial df (category + maximum of 5 years)
            school_finance = school_finance.iloc[:, :6]
            school_finance_dict = school_finance.to_dict()  # dict[1]
    else:
        school_finance_dict = {}

    #### K8 Academic Data

    # Filter k8 academic data to exclude any years (format YYYY) more recent than selected year (can still be multi-year data)
    excluded_years = []
    for i in range(num_years_to_remove):
        excluded_year = int(current_year) - i
        excluded_years.append(
            str(excluded_year)
        )  # creates a list of year strings to be excluded

    # Get selected year as string for filtering purposes
    academic_year = str(year)

    # store current year separatly for demographic data because data exists for 2020 (pandemic year)
    demographic_year = str(year)

    # account for the fact that there is no academic data for 2020
    if academic_year == "2020":
        academic_year = "2019"

    # list of comparison schools
    comparison_schools = (
        school_index.loc[:, (school_index.columns.str.contains("Comp"))]
        .values[0]
        .tolist()
    )
    comparison_schools = [
        x for x in comparison_schools if x == x
    ]  # remove nan (nan != nan)

    k8_all_data_included_years = k8_academic_data[
        ~k8_academic_data["Year"].isin(excluded_years)
    ]
    k8_school_data = k8_all_data_included_years.loc[
        k8_all_data_included_years["School ID"] == school
    ]

    if (
        len(k8_school_data.index) == 0
    ):  # if school is not in k8 academic dataframe skip loading the other dataframes
        k8_school_dict = {}
        k8_corp_dict = {}
        k8_comparison_dict = {}
    else:
        #### Process School and Corporation K8 Academic Data Dataframe

        k8_corp_data = k8_all_data_included_years.loc[
            (
                k8_all_data_included_years["Corp ID"]
                == school_index["GEO Corp"].values[0]
            )
        ]
        k8_comparison_data = k8_all_data_included_years.loc[
            (k8_all_data_included_years["School ID"].isin(comparison_schools))
        ]

        # NOTE: this does two things: replaces all NaN's with 0 and replaces all '***' (insufficient n-size) with -99
        # This step makes it much easier to perform mathmatetical calculations on the dataframe without worrying about losing
        # the string data, which we need to keep track of when we are ready to display the dataframe. This works without an
        # additional step because 'Total Tested' will never be '***'. The process for final conversion is as follows:
        # NOTE: both IREAD Test N and IREAD Pass N may be '***' (only exception)
        #       'Total Proficient' can be #, '***', 0, or blank
        # for each category + 'Proficient %' (value per year):
        #   if 'Proficient %' > 0:                                                  'Proficient %' = value
        #   if 'Proficient %' == 1 (in case of IREAD Test N and Pass N both ***):   'Proficient %' = '***'
        #   if 'Proficient %' < 0 (-1 or -#):                                       'Proficient %' = '***'
        #   if 'Proficient %' == 0:                                                 'Proficient %' = '0'
        #   if 'Proficient %' = NaN:                                                'Proficient %' = ''
        #   if 'Proficient %' for all years are NaN:                                drop row

        k8_school = k8_school_data.fillna(0)
        k8_school = k8_school.replace("***", -99)

        k8_school_info = k8_school[
            ["State Grade", "Federal Rating", "School Name"]
        ].copy()  # remove text columns from dataframe

        # keep only those columns used in calculations
        k8_school = k8_school.filter(
            regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|^Year$",
            axis=1,
        ).copy()
        k8_corp = k8_corp_data.filter(
            regex=r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|^Year$",
            axis=1,
        ).copy()

        # remove 'ELA & Math' columns (NOTE: Comment this out to retain 'ELA & Math' columns)

        k8_school.drop(list(k8_school.filter(regex="ELA & Math")), axis=1, inplace=True)
        k8_corp.drop(list(k8_corp.filter(regex="ELA & Math")), axis=1, inplace=True)

        # change values to numeric
        for col in k8_school.columns:
            k8_school[col] = pd.to_numeric(k8_school[col], errors="coerce")

        for col in k8_corp.columns:
            k8_corp[col] = pd.to_numeric(k8_corp[col], errors="coerce")

        # we want corporation average, so sum each category of the corp datafile, grouping by year
        k8_corp_sum = k8_corp.groupby(["Year"]).sum(numeric_only=True).copy()

        # iterate over all columns, calculate the average, and store in a new column
        categories = ethnicity + status + grades + ["School Total"]
        for s in subject:
            for c in categories:
                new_col = c + "|" + s + " Proficient %"
                proficient = c + "|" + s + " Total Proficient"
                tested = c + "|" + s + " Total Tested"

                k8_school[new_col] = k8_school[proficient] / k8_school[tested]
                k8_corp_sum[new_col] = k8_corp_sum[proficient] / k8_corp_sum[tested]

        # calculate IREAD Pass %
        k8_school["IREAD Pass %"] = (
            k8_school["IREAD Pass N"] / k8_school["IREAD Test N"]
        )
        k8_corp_sum["IREAD Pass %"] = (
            k8_corp_sum["IREAD Pass N"] / k8_corp_sum["IREAD Test N"]
        )

        # filter all columns keeping only the relevant ones (NOTE: comment this out to retain all columns)
        k8_school = k8_school.filter(
            regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$",
            axis=1,
        )
        k8_corp = k8_corp_sum.filter(
            regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$",
            axis=1,
        )

        # add text info columns back and reset index
        k8_school = pd.concat([k8_school, k8_school_info], axis=1, join="inner")

        # find categories with no data for any year and drop from dataframe
        none_categories = k8_school.columns[k8_school.isna().all()].tolist()

        k8_school = k8_school.drop(columns=none_categories)
        k8_corp = k8_corp.drop(columns=none_categories)

        # reset index
        k8_school = k8_school.reset_index(drop=True)
        k8_corp = k8_corp.reset_index()

        # ensure columns headers are strings
        k8_school.columns = k8_school.columns.astype(str)
        k8_corp.columns = k8_corp.columns.astype(str)

        #### Process Comparable Schools K8 Academic Data Dataframe

        ## k8 Comparable School Data (filtered to pass only those categories that are used)
        # smaller set of schools identified (in index file as 'Comp') due to strong comparability MAY include charter schools
        k8_comparison = k8_comparison_data.filter(
            regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$|^School Name$",
            axis=1,
        )

        # limit number of displayed years in all dataframes to the available years of academic data in 'school' dataframe
        # get all unique values in the 'Year' column of the school and corp dataframes
        # 'limit' will be empty if the lists are the same- because both dataframes cover the same years, if not, it will
        # consist of a list of each year in the corp dataframe that is not in the school dataframe
        # use this list to remove the rows in the comparable/similar dataframes from the identified year(s)
        k8_year_limit = list(
            set(k8_corp["Year"].unique().tolist())
            - set(k8_school["Year"].unique().tolist())
        )

        if k8_year_limit:
            k8_corp = k8_corp[~k8_corp["Year"].isin(k8_year_limit)]
            k8_comparison = k8_comparison[~k8_comparison["Year"].isin(k8_year_limit)]

        k8_comparison.columns = k8_comparison.columns.astype(str)  # NOTE: NEED?

        # convert dataframes to dictionaries for dcc.store
        k8_school_dict = k8_school.to_dict()  # dict[2]
        k8_corp_dict = k8_corp.to_dict()  # dict[3]
        k8_comparison_dict = k8_comparison.to_dict()  # dict[4]

    #### HS Academic Data

    hs_all_data_included_years = hs_academic_data[
        ~hs_academic_data["Year"].isin(excluded_years)
    ]
    hs_school_data = hs_all_data_included_years.loc[
        hs_all_data_included_years["School ID"] == school
    ]

    if (
        len(hs_school_data.index) == 0
    ):  # if school is not in hs academic dataframe (e.g., new school)
        hs_school_dict = {}
        hs_corp_dict = {}
        hs_comparison_dict = {}

    else:
        hs_corp_data = hs_all_data_included_years.loc[
            (
                hs_all_data_included_years["Corp ID"]
                == school_index["GEO Corp"].values[0]
            )
        ]
        hs_comparison_data = hs_all_data_included_years.loc[
            (hs_all_data_included_years["School ID"].isin(comparison_schools))
        ]

        # slightly different process than k8 because both Cohort Count and Graduates can be equal to '***'
        # which means that '***' / '***) == 1 (-99/-99)
        # need an additional step to convert all '1' values to -99 AFTER everything is processed
        hs_school = hs_school_data.fillna(0)
        hs_school = hs_school.replace("***", -99)

        hs_school_info = hs_school[
            ["School Name", "State Grade", "Federal Rating"]
        ].copy()  # remove text columns from dataframe

        # drop any adult high schools (AHS) from corp avg df
        hs_corp = hs_corp_data[hs_corp_data["School Type"].str.contains("AHS") == False]

        # keep only those columns used in calculations
        hs_school = hs_school.filter(
            regex=r"Cohort Count$|Graduates$|Pass N|Test N|^Year$", axis=1
        )
        hs_corp = hs_corp.filter(
            regex=r"Cohort Count$|Graduates$|Pass N|Test N|^Year$", axis=1
        )

        # remove 'ELA & Math' columns (NOTE: Comment this out to retain 'ELA & Math' columns)
        hs_school.drop(list(hs_school.filter(regex="ELA & Math")), axis=1, inplace=True)
        hs_corp.drop(list(hs_corp.filter(regex="ELA & Math")), axis=1, inplace=True)

        # TODO: TEST ON OTHER SCHOOLS TO MAKE SURE WORKING
        none_categories = hs_school.columns[hs_school.isna().all()].tolist()

        # change values to numeric
        for col in hs_school.columns:
            hs_school[col] = pd.to_numeric(hs_school[col], errors="coerce")

        for col in hs_corp.columns:
            hs_corp[col] = pd.to_numeric(hs_corp[col], errors="coerce")

        # group corp dataframe by year and sum all rows for each category
        hs_corp = hs_corp.groupby(["Year"]).sum(numeric_only=True)

        # reverse order of rows (Year) and reset index to bring Year back as column
        hs_corp = hs_corp.loc[::-1].reset_index()

        # list of categories for calculations
        eca_categories = ["Grade 10|ELA", "Grade 10|Math"]
        grad_categories = ethnicity + status + ["Total"]
        grad_cohort_categories = [g + "|Cohort Count" for g in grad_categories]

        # no specific 'Non-Waiver|Graduates' column, so add manually
        grad_cohort_categories.append("Non-Waiver|Cohort Count")

        # calculate the averages for remaining categories ([category] + '|Cohort Count' / [category] + '|Graduates')
        # and add to empty dataframes
        for g in grad_categories:
            new_col = g + " Graduation Rate"
            hs_school[new_col] = (
                hs_school[g + "|Graduates"] / hs_school[g + "|Cohort Count"]
            )
            hs_corp[new_col] = hs_corp[g + "|Graduates"] / hs_corp[g + "|Cohort Count"]

        # calculate ECA averages ('Grade 10' + '|ELA/Math' + 'Test N' / 'Grade 10' + '|ELA/Math' + 'Pass N')
        # if none_categories includes 'Grade 10' - there is no ECA data available for the school for the selected Years
        if "Grade 10" not in none_categories:
            for e in eca_categories:
                new_col = e + " Pass Rate"
                hs_corp[new_col] = hs_corp[e + " Pass N"] / hs_corp[e + " Test N"]
                hs_school[new_col] = hs_school[e + " Pass N"] / hs_school[e + " Test N"]

        # add 'non-waiver grad rate' ('Non-Waiver|Cohort Count' / 'Total|Cohort Count')
        # and 'strength of diploma' (Non-Waiver|Cohort Count` * 1.08) / `Total|Cohort Count`) calculation and average to both dataframes
        # if none_categories includes 'Non-Waiver' - there is no data available for the school for the selected Years
        if "Non-Waiver" not in none_categories:
            hs_corp["Non-Waiver Graduation Rate"] = (
                hs_corp["Non-Waiver|Cohort Count"] / hs_corp["Total|Cohort Count"]
            )
            hs_corp["Strength of Diploma"] = (
                hs_corp["Non-Waiver|Cohort Count"] * 1.08
            ) / hs_corp["Total|Cohort Count"]
            hs_school["Non-Waiver Graduation Rate"] = (
                hs_school["Non-Waiver|Cohort Count"] / hs_school["Total|Cohort Count"]
            )
            hs_school["Strength of Diploma"] = (
                hs_school["Non-Waiver|Cohort Count"] * 1.08
            ) / hs_school["Total|Cohort Count"]

        # filter all columns keeping only the relevant ones (NOTE: comment this out to retain all columns)
        hs_school = hs_school.filter(
            regex=r"^Category|Graduation Rate$|Pass Rate$|^Strength of Diploma|^Year$",
            axis=1,
        )
        hs_corp = hs_corp.filter(
            regex=r"^Category|Graduation Rate$|Pass Rate$|^Strength of Diploma|^Year$",
            axis=1,
        )

        ## State Avg Graduation Rate
        # includes two possible calculations:
        #   1) all HS (state_grad_average_all); and
        #   2) all HS excluding AHS (state_grad_average_noAHS)

        hs_all_data_included_years["Total|Graduates"] = pd.to_numeric(
            hs_all_data_included_years["Total|Graduates"], errors="coerce"
        )
        hs_all_data_included_years["Total|Cohort Count"] = pd.to_numeric(
            hs_all_data_included_years["Total|Cohort Count"], errors="coerce"
        )
        state_grad_average_all = (
            hs_all_data_included_years.groupby("Year", as_index=False)
            .sum()
            .eval("Grad_Average_All = `Total|Graduates` / `Total|Cohort Count`")
        )

        hs_all_data_included_years["Total|Graduates"] = hs_all_data_included_years.loc[
            hs_all_data_included_years["School Type"] != "AHS", "Total|Graduates"
        ]
        hs_all_data_included_years[
            "Total|Cohort Count"
        ] = hs_all_data_included_years.loc[
            hs_all_data_included_years["School Type"] != "AHS", "Total|Cohort Count"
        ]
        state_grad_average_noAHS = (
            hs_all_data_included_years.groupby("Year", as_index=False)
            .sum()
            .eval("Grad_Average_NoAHS = `Total|Graduates` / `Total|Cohort Count`")
        )

        # change which dataframe is copied to determine which grad rate calculation is used.
        state_grad_avg = state_grad_average_noAHS.copy()

        # drop all other columns, invert rows (so most recent year at index [0]) & reset the index
        state_grad_avg = state_grad_avg[["Year", "Grad_Average_NoAHS"]]
        state_grad_avg = state_grad_avg.loc[::-1].reset_index(drop=True)

        # merge applicable years of grad_avg dataframe into hs_school df using an inner merge and rename the column
        # this merges data only where both dataframes share a common key, in this case 'Year')
        state_grad_avg["Year"] = state_grad_avg["Year"].astype(int)
        hs_school = hs_school.merge(state_grad_avg, on="Year", how="inner")
        hs_school.rename(
            columns={"Grad_Average_NoAHS": "State Average Graduation Rate"},
            inplace=True,
        )

        # this is a bit fiddly - as we are going to eventually combine the two dataframes and calcuate differences, we
        # need identical categories in both dataframes. We are going to compare the Category 'State Average Graduation Rate'
        # against the corp 'Total Graduation rate', so we need to duplicate the 'Total' row and name it 'State Average Graduation Rate'
        hs_corp["State Average Graduation Rate"] = hs_corp["Total Graduation Rate"]

        # reset school_info index (to make sure the dataframe indexes are identical) and concat hs_info df back into school df
        hs_school_info = hs_school_info.reset_index(drop=True)
        hs_school = pd.concat([hs_school, hs_school_info], axis=1, join="inner")

        # find categories with no data for any year and drop from dataframe
        none_categories = hs_school.columns[hs_school.isna().all()].tolist()

        hs_school = hs_school.drop(columns=none_categories)

        # check first to see if column exists in corp df (may not), otherwise throws error
        hs_corp = hs_corp.drop(
            [x for x in none_categories if x in hs_corp.columns], axis=1
        )

        # ensure columns headers are strings
        hs_school.columns = hs_school.columns.astype(str)
        hs_corp.columns = hs_corp.columns.astype(str)

        # filter comparable school data
        hs_comparison = hs_comparison_data.filter(
            regex=r"Cohort Count$|Graduates$|Pass N|Test N|^Year$", axis=1
        )

        ## See above (k8_diff)
        hs_diff = list(
            set(hs_corp["Year"].unique().tolist())
            - set(hs_school["Year"].unique().tolist())
        )

        if hs_diff:
            hs_corp = hs_corp[~hs_corp["Year"].isin(hs_diff)]
            hs_comparison = hs_comparison[~hs_comparison["Year"].isin(hs_diff)]

        # ensure columns headers are strings
        hs_comparison.columns = hs_comparison.columns.astype(str)

        # convert dataframes to dictionaries for dcc.store
        hs_school_dict = hs_school.to_dict()  # dict[5]
        hs_corp_dict = hs_corp.to_dict()  # dict[6]
        hs_comparison_dict = hs_comparison.to_dict()  # dict[7]

    #### Demographic Data
    # Get demographic data for school & corp (matching school corporation of residence by corp id) and filter by selected year

    school_demographics = demographics.loc[
        (demographics["School ID"] == school)
        & (demographics["Year"] == demographic_year)
    ]

    if (
        len(school_demographics.index) == 0
    ):  # if school is not in degmographic dataframe
        school_demographics_dict = {}
        #        school_gradespan_dict = {}
        corp_demographics_dict = {}

    else:
        ## School Demographics
        school_demographics_dict = school_demographics.to_dict()  # dict[8]

        ## Corporation Demographics
        corp_demographics = demographics.loc[
            (demographics["School ID"] == school_index["GEO Corp"].values[0])
            & (demographics["Year"] == demographic_year)
        ]
        corp_demographics_dict = corp_demographics.to_dict()  # dict[9]

    #### ADM Data
    # Get school ADM data (matching school by corp id) and filter by selected year

    # school_adm = adm.loc[(adm['School ID'] == school) & (demographics['Year'] == demographic_year)]
    school_adm = adm.loc[adm["Corp"] == corp_id]
    school_adm = school_adm.filter(regex=r"September|February", axis=1)
    for col in school_adm.columns:
        school_adm[col] = pd.to_numeric(school_adm[col], errors="coerce")

    # transpose adm dataframe and group by year (by splitting 'Name' Column e.g., '2022 February ADM', '2022 September ADM', etc.
    # after 1st space) and sum() result
    # https://stackoverflow.com/questions/35746847/sum-values-of-columns-starting-with-the-same-string-in-pandas-dataframe
    school_adm = (
        school_adm.T.groupby([s.split(" ", 1)[0] for s in school_adm.T.index.values])
        .sum()
        .T
    )

    # average resulting sum (September and February Count)
    school_adm = school_adm / 2

    # drop zero columns (e.g., no ADM for that year)
    school_adm = school_adm.loc[:, (school_adm != 0).any(axis=0)].reset_index(drop=True)

    # This dataset can be longer than five years, so we have to filter it by both the selected year and the total # of years
    year_limit = 5
    adm_years = len(school_adm.columns)

    # if number of available years exceeds year_limit, drop excess columns (years)
    if adm_years > year_limit:
        school_adm.drop(
            columns=school_adm.columns[: (adm_years - year_limit)], axis=1, inplace=True
        )

    # if the display year is less than current year
    # drop columns where year matches any years in 'excluded years' list
    if excluded_years:
        school_adm = school_adm.loc[
            :, ~school_adm.columns.str.contains("|".join(excluded_years))
        ]

    if len(school_adm.index) == 0:  # if no adm data
        school_adm_dict = {}
    else:
        school_adm_dict = school_adm.to_dict()  # dict[10]

    #### combine all dictionaries into a dictionary of dictionaries (dcc.store needs a dict)
    dict_of_df = {}

    dict_of_df[0] = index_dict
    dict_of_df[1] = school_finance_dict
    dict_of_df[2] = k8_school_dict
    dict_of_df[3] = k8_corp_dict
    dict_of_df[4] = k8_comparison_dict
    dict_of_df[5] = hs_school_dict
    dict_of_df[6] = hs_corp_dict
    dict_of_df[7] = hs_comparison_dict
    dict_of_df[8] = school_demographics_dict
    dict_of_df[9] = corp_demographics_dict
    dict_of_df[10] = school_adm_dict

    # ### dict size testing
    #     print(get_size(dict_of_df))

    #     for i in range(11):
    #         print(i)
    #         print(get_size(dict_of_df[i]))

    return dict_of_df


# Set dropdown
@app.callback(Output("charter-dropdown", "value"), Input("charter-dropdown", "options"))
def set_dropdown_value(charter_options):
    return charter_options[0]["value"]


# Set tab
@app.callback(
    Output("tabs-content", "children"),
    [Input("tabs", "value"), Input("subtab2", "value"), Input("subtab3", "value")],
)
def render_content(tab, subtab2, subtab3):
    if tab == "tab-1":
        return aboot.layout
    if tab == "tab-2":
        if subtab2 == "subtab2-1":
            return financial_information.layout
        elif subtab2 == "subtab2-2":
            return financial_metrics.layout
        elif subtab2 == "subtab2-3":
            return financial_analysis.layout
    elif tab == "tab-3":
        if subtab3 == "subtab3-1":
            return academic_information_k12.layout
        elif subtab3 == "subtab3-2":
            return academic_metrics.layout
        elif subtab3 == "subtab3-3":
            return academic_analysis.layout
    elif tab == "tab-4":
        return organizational_compliance.layout


if __name__ == "__main__":
    app.run_server(debug=True)
