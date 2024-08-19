##################################
# ICSB Dashboard - Print Layouts #
##################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     08/18/24

import dash
from dash import dcc, html, dash_table, Input, Output, callback
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import numpy as np


from .globals import ethnicity, subgroup, max_display_years
from .load_data import (
    get_excluded_years,
    get_school_index,
    get_financial_data,
    get_corp_demographic_data,
    get_school_demographic_data,
    get_adm,
    get_attendance_data,
    get_discipline_data,
)

from .process_data import process_discipline_data

from .charts import (
    loading_fig,
    no_data_fig_label,
    make_line_chart,
    make_demographics_bar_chart,
)
from .tables import (
    no_data_table,
    no_data_page,
    create_key_table,
    create_single_header_table,
)
from .layouts import create_line_fig_layout, create_two_fig_layout



def create_print_layout(year: str, school_id: str, options: list) -> list:

    print("Selected")
    print(options)
    print_layout = []

    all_container = {"display": "none"}
    about_container = {"display": "none"}
    fininfo_container = {"display": "none"}
    finmetrics_container = {"display": "none"}
    finanalysis_container = {"display": "none"}
    orgcompliance_container = {"display": "none"}
    academicinfo_container = {"display": "none"}
    academicmetrics_container = {"display": "none"}
    empty_container = {"display": "block"}

    if "all" in options:
        about_layout = create_about_layout(year, school_id)
        print_layout.append(about_layout)

        fininfo_layout = create_fininfo_layout(year, school_id)
        print_layout.append(fininfo_layout)

        finmetrics_layout = create_finmetrics_layout(year, school_id)
        print_layout.append(finmetrics_layout)            

        finanalysis_layout = create_finanalysis_layout(year, school_id)
        print_layout.append(finanalysis_layout)               

        orgcompliance_layout = create_orgcompliance_layout(year, school_id)
        print_layout.append(orgcompliance_layout)                

        academicinfo_layout = create_academicinfo_layout(year, school_id)
        print_layout.append(academicinfo_layout)    

        academicmetrics_layout = create_academicmetrics_layout(year, school_id)
        print_layout.append(academicmetrics_layout)      
    else:
        if "about" in options:
            about_layout = create_about_layout(year, school_id)
            print_layout.append(about_layout)
            # about_container = {"display": "none"}
        if "fininfo" in options:
            fininfo_layout = create_fininfo_layout(year, school_id)
            print_layout.append(fininfo_layout)
            # fininfo_container = {"display": "none"}
        if "finmetrics" in options:
            finmetrics_layout = create_finmetrics_layout(year, school_id)
            print_layout.append(finmetrics_layout)            
            # finmetrics_container = {"display": "none"}
        if "finanalysis" in options:
            finanalysis_layout = create_finanalysis_layout(year, school_id)
            print_layout.append(finanalysis_layout)               
            # finanalysis_container = {"display": "none"}            
        if "orgcompliance" in options:
            orgcompliance_layout = create_orgcompliance_layout(year, school_id)
            print_layout.append(orgcompliance_layout)                
            # orgcompliance_container = {"display": "none"}            
        if "academicinfo" in options:
            academicinfo_layout = create_academicinfo_layout(year, school_id)
            print_layout.append(academicinfo_layout)    
            # academicinfo_container = {"display": "none"}            
        if "academicmetrics" in options:
            academicmetrics_layout = create_academicmetrics_layout(year, school_id)
            print_layout.append(academicmetrics_layout)    
            # academicmetrics_container = {"display": "none"}

    # TODO: Not printing both items - figure out nesting
    print(print_layout)
    level_one = print_layout[0]
    return level_one[0]

# Attendance Rate, Chronic Absenteeism, and Demographic Breakdown
def create_about_layout(year: str, school_id: str) -> list:

    about_layout = []

    year_string = year
    year_numeric = int(year)

    selected_school = get_school_index(school_id)
    selected_school_type = selected_school["School Type"].values[0]

    attendance_rate_data = get_attendance_data(
        school_id, selected_school_type, year_string
    )

    if len(attendance_rate_data.index) > 0 and len(attendance_rate_data.columns) > 1:
        attendance_table = create_single_header_table(
            attendance_rate_data, "Attendance"
        )

        attendance_fig_data = (
            attendance_rate_data.set_index("Category")
            .T.rename_axis("Year")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        attendance_fig = make_line_chart(attendance_fig_data)

    else:
        attendance_table = no_data_fig_label()
        attendance_fig = no_data_fig_label()

    if selected_school_type == "AHS":
        attendance_title = "Attendance Rate"
    else:
        attendance_title = "Attendance Rate and Chronic Absenteeism"

    attendance_layout = create_line_fig_layout(
        attendance_table, attendance_fig, attendance_title
    )

    demographic_data = get_school_demographic_data(school_id)
    demographic_data = demographic_data.loc[demographic_data["Year"] == year_numeric]

    if len(demographic_data.index) == 0:
        subgroup_fig = no_data_fig_label("Enrollment by Subgroup", 400)
        ethnicity_fig = no_data_fig_label("Enrollment by Ethnicity", 400)

    else:

        demographics_title = "Demographic Breakdown"

        corp_id = str(selected_school["GEO Corp"].values[0])
        corp_demographics = get_corp_demographic_data(corp_id)
        corp_demographics = corp_demographics.loc[
            corp_demographics["Year"] == year_numeric
        ]

        ethnicity_school = demographic_data.loc[
            :,
            (demographic_data.columns.isin(ethnicity))
            | (demographic_data.columns.isin(["Corporation Name", "Total Enrollment"])),
        ]

        if not ethnicity_school.empty:
            ethnicity_corp = corp_demographics.loc[
                :,
                (corp_demographics.columns.isin(ethnicity))
                | (
                    corp_demographics.columns.isin(["Corporation Name", "Total Enrollment"])
                ),
            ]

            ethnicity_school = ethnicity_school.rename(
                columns={"Native Hawaiian or Other Pacific Islander": "Pacific Islander"}
            )

            ethnicity_corp = ethnicity_corp.rename(
                columns={"Native Hawaiian or Other Pacific Islander": "Pacific Islander"}
            )

            ethnicity_data = pd.concat([ethnicity_school, ethnicity_corp])

            ethnicity_fig = make_demographics_bar_chart(ethnicity_data)

        subgroup_school = demographic_data.loc[
            :,
            (demographic_data.columns.isin(subgroup))
            | (demographic_data.columns.isin(["Corporation Name", "Total Enrollment"])),
        ]

        if not subgroup_school.empty:
            subgroup_corp = corp_demographics.loc[
                :,
                (corp_demographics.columns.isin(subgroup))
                | (
                    corp_demographics.columns.isin(["Corporation Name", "Total Enrollment"])
                ),
            ]

            subgroup_merged_data = pd.concat([subgroup_school, subgroup_corp])

            subgroup_fig = make_demographics_bar_chart(subgroup_merged_data)

        demographics_layout = create_two_fig_layout(
            subgroup_fig, ethnicity_fig, demographics_title
        )

    about_layout.append(attendance_layout)
    about_layout.append(demographics_layout)

    return about_layout

# c. Academic Information
def create_academicinfo_layout(year: str, school_id: str) -> list:
    pass
    # return academicinfo_layout

def create_academicmetrics_layout(year: str, school_id: str) -> list:
    pass
    # return academicmetrics_layout

def create_fininfo_layout(year: str, school_id: str) -> list:
    pass
    # return fininfo_layout

def create_finmetrics_layout(year: str, school_id: str) -> list:
    pass
    # return finmetrics_layout

def create_finanalysis_layout(year: str, school_id: str) -> list:
    pass
    # return finanalysis_layout

def create_orgcompliance_layout(year: str, school_id: str) -> list:
    pass
    # return orgcompliance_layout