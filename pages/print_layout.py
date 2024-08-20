##################################
# ICSB Dashboard - Print Layouts #
##################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     08/18/24

import dash
from dash import dcc, html, dash_table, Input, State, Output, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash.dash_table import FormatTemplate
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re

from .globals import (
    ethnicity,
    subgroup,
    subject,
    grades_all,
    grades,
    grades_ordinal,
    max_display_years,
)

from .load_data import (
    get_excluded_years,
    get_school_index,
    get_financial_data,
    get_financial_ratios,
    get_corp_demographic_data,
    get_school_demographic_data,
    get_attendance_data,
    get_discipline_data,
    get_academic_data,
    get_school_stns,
    get_iread_student_data,
    get_wida_student_data,
    get_proficiency_data,
)

from .calculations import round_nearest, round_percentages
from .process_data import process_discipline_data
from .calculate_metrics import calculate_financial_metrics
from .string_helpers import convert_to_svg_circle, natural_keys

from .tables import (
    no_data_page,
    create_multi_header_table_with_container,
    create_key_table,
    create_single_header_table,
    create_multi_header_table,
    create_iread_ilearn_table,
    no_data_table,
    create_financial_analysis_table,
)


from .charts import (
    loading_fig,
    no_data_fig_label,
    make_line_chart,
    make_demographics_bar_chart,
    make_stacked_bar,
    make_line_chart,
)
from .tables import (
    no_data_table,
    no_data_page,
    create_key_table,
    create_single_header_table,
)
from .layouts import create_line_fig_layout, set_table_layout


# def create_print_layout(year: str, school_id: str, options: list) -> list:
#     print("Selected")
#     print(options)
#     about_layout = []
#     fininfo_layout = []
#     # all_container = {"display": "none"}
#     # about_container = {"display": "none"}
#     # fininfo_container = {"display": "none"}
#     # finmetrics_container = {"display": "none"}
#     # finanalysis_container = {"display": "none"}
#     # orgcompliance_container = {"display": "none"}
#     # academicinfo_container = {"display": "none"}
#     # academicmetrics_container = {"display": "none"}
#     # empty_container = {"display": "block"}

#     if "all" in options:
#         about_layout = create_about_layout(year, school_id)
#         fininfo_layout = create_fininfo_layout(year, school_id)
#         finmetrics_layout = create_finmetrics_layout(year, school_id)
#         finanalysis_layout = create_finanalysis_layout(year, school_id)
#         orgcompliance_layout = create_orgcompliance_layout(year, school_id)
#         academicinfo_layout = create_academicinfo_layout(year, school_id)
#         academicmetrics_layout = create_academicmetrics_layout(year, school_id)

#     else:
#         if "about" in options:
#             about_layout = create_about_layout(year, school_id)

#         if "fininfo" in options:
#             fininfo_layout = create_fininfo_layout(year, school_id)

#         if "finmetrics" in options:
#             finmetrics_layout = create_finmetrics_layout(year, school_id)

#         if "finanalysis" in options:
#             finanalysis_layout = create_finanalysis_layout(year, school_id)

#         if "orgcompliance" in options:
#             orgcompliance_layout = create_orgcompliance_layout(year, school_id)

#         if "academicinfo" in options:
#             academicinfo_layout = create_academicinfo_layout(year, school_id)

#         if "academicmetrics" in options:
#             academicmetrics_layout = create_academicmetrics_layout(year, school_id)


#     return about_layout


def create_about_layout(year: str, school_id: str) -> list:
    about_layout = []

    year_string = year
    year_numeric = int(year)

    selected_school = get_school_index(school_id)
    school_type = selected_school["School Type"].values[0]

    attendance_rate_data = get_attendance_data(school_id, school_type, year_string)

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

    if school_type == "AHS":
        attendance_title = "Attendance Rate"
    else:
        attendance_title = "Attendance Rate and Chronic Absenteeism"

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
                    corp_demographics.columns.isin(
                        ["Corporation Name", "Total Enrollment"]
                    )
                ),
            ]

            ethnicity_school = ethnicity_school.rename(
                columns={
                    "Native Hawaiian or Other Pacific Islander": "Pacific Islander"
                }
            )

            ethnicity_corp = ethnicity_corp.rename(
                columns={
                    "Native Hawaiian or Other Pacific Islander": "Pacific Islander"
                }
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
                    corp_demographics.columns.isin(
                        ["Corporation Name", "Total Enrollment"]
                    )
                ),
            ]

            subgroup_merged_data = pd.concat([subgroup_school, subgroup_corp])

            subgroup_fig = make_demographics_bar_chart(subgroup_merged_data)

    about_layout = [
        html.Div(
            [
                html.Label(
                    attendance_title,
                    className="label__header",
                    style={"marginTop": "10px"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(attendance_table, style={"marginTop": "10px"}),
                            ],
                            className="pretty-container six columns",
                        ),
                        html.Div(
                            [
                                html.Div(attendance_fig),
                            ],
                            className="pretty-container six columns",
                        ),
                    ],
                    className="bare-container--flex--center twelve columns",
                ),
            ],
            className="bare-container--relative twelve columns",
        ),
        html.Div(
            [
                html.Label(
                    demographics_title,
                    className="label__header",
                    style={"marginTop": "10px"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Graph(
                                    figure=subgroup_fig,
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="pretty-container six columns",
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    figure=ethnicity_fig,
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="pretty-container six columns",
                        ),
                    ],
                    className="bare-container--flex--center twelve columns",
                ),
            ],
            className="bare-container--relative twelve columns",
        ),
    ]

    return about_layout


# c. Academic Information
def create_academicinfo_layout(year: str, school_id: str) -> list:
    year_string = year
    year_numeric = int(year_string)

    selected_school = get_school_index(school_id)
    school_type = selected_school["School Type"].values[0]
    school_name = selected_school["School Name"].values[0]

    excluded_years = get_excluded_years(year_string)

    k12_grad_overview_table = []  # type: list
    k12_grad_ethnicity_table = []  # type: list
    k12_grad_subgroup_table = []  # type: list

    k12_sat_overview_table = []  # type: list
    k12_sat_ethnicity_table = []  # type: list
    k12_sat_subgroup_table = []  # type: list
    k12_sat_cut_scores_table = []  # type: list

    iread_school_level_layout = []  # type: list
    iread_school_details = []  # type: list
    iread_ilearn_ela_table = []  # type: list
    iread_ilearn_math_table = []  # type: list

    wida_breakdown = []  # type: list
    wida_iread_details_table = []  # type: list

    proficiency_grades_ela = []  # type: list
    ela_grade_bar_fig = []  # type: list
    proficiency_ethnicity_ela = []  # type: list
    ela_ethnicity_bar_fig = []  # type: list
    proficiency_subgroup_ela = []  # type: list
    ela_subgroup_bar_fig = []  # type: list
    proficiency_grades_math = []  # type: list
    math_grade_bar_fig = []  # type: list
    proficiency_ethnicity_math = []  # type: list
    math_ethnicity_bar_fig = []  # type: list
    proficiency_subgroup_math = []  # type: list
    math_subgroup_bar_fig = []  # type: list

    # High School Data
    if (
        school_type == "HS"
        or school_type == "AHS"
        or (school_id == 5874 and year_numeric < 2021)
    ):
        if school_type == "K12":
            school_type = "HS"
        else:
            school_type = school_type

        list_of_schools = [school_id]

        hs_info_data = get_academic_data(
            list_of_schools, school_type, year_numeric, "info"
        )

        # TODO: Add figs for SAT and Grad Rates
        # TODO: Add AHS CCR Data to new table
        if len(hs_info_data.index) > 0:
            grad_overview_categories = ["Total", "Non Waiver", "State Average"]

            if school_type == "AHS":
                grad_overview_categories.append("CCR Percentage")

            hs_info_data.columns = hs_info_data.columns.astype(str)

            graduation_data = hs_info_data[
                hs_info_data["Category"].str.contains("Graduation")
            ].copy()

            graduation_data = graduation_data.loc[
                :,
                ~graduation_data.where(graduation_data.astype(bool)).isna().all(axis=0),
            ]

            graduation_data = graduation_data.loc[
                :, ~(graduation_data.astype(str) == "None").all()
            ]

            if len(graduation_data.columns) > 1 and len(graduation_data.index) > 0:
                graduation_data["Category"] = (
                    graduation_data["Category"]
                    .str.replace("|Graduation Rate", "", regex=False)
                    .str.strip()
                )

                grad_overview = graduation_data[
                    graduation_data["Category"].str.contains(
                        "|".join(grad_overview_categories)
                    )
                ]
                grad_overview = grad_overview.dropna(axis=1, how="all")

                k12_grad_overview_table = create_multi_header_table_with_container(
                    grad_overview, "Graduation Rate Overview"
                )

                k12_grad_overview_table = set_table_layout(
                    k12_grad_overview_table,
                    k12_grad_overview_table,
                    grad_overview.columns,
                )

                grad_ethnicity = graduation_data[
                    graduation_data["Category"].str.contains("|".join(ethnicity))
                ]

                grad_ethnicity = grad_ethnicity.dropna(axis=1, how="all")

                k12_grad_ethnicity_table = create_multi_header_table_with_container(
                    grad_ethnicity, "Graduation Rate by Ethnicity"
                )

                k12_grad_ethnicity_table = set_table_layout(
                    k12_grad_ethnicity_table,
                    k12_grad_ethnicity_table,
                    grad_ethnicity.columns,
                )

                grad_subgroup = graduation_data[
                    graduation_data["Category"].str.contains("|".join(subgroup))
                ]

                grad_subgroup = grad_subgroup.dropna(axis=1, how="all")

                k12_grad_subgroup_table = create_multi_header_table_with_container(
                    grad_subgroup, "Graduation Rate by Subgroup"
                )
                k12_grad_subgroup_table = set_table_layout(
                    k12_grad_subgroup_table,
                    k12_grad_subgroup_table,
                    grad_subgroup.columns,
                )

            # SAT Benchmark Table
            k12_sat_table_data = hs_info_data[
                hs_info_data["Category"].str.contains("Benchmark %")
            ].copy()

            # remove NaN/blank cols
            k12_sat_table_data = k12_sat_table_data.loc[
                :,
                ~k12_sat_table_data.where(k12_sat_table_data.astype(bool))
                .isna()
                .all(axis=0),
            ]

            if (
                len(k12_sat_table_data.columns) > 1
                and len(k12_sat_table_data.index) > 0
            ):
                k12_sat_table_data["Category"] = (
                    k12_sat_table_data["Category"]
                    .str.replace("Benchmark %", "")
                    .str.strip()
                )

                k12_sat_overview = k12_sat_table_data[
                    k12_sat_table_data["Category"].str.contains("Total")
                ]

                k12_sat_overview = k12_sat_overview.dropna(axis=1, how="all")

                k12_sat_overview_table = create_multi_header_table_with_container(
                    k12_sat_overview, "SAT Overview"
                )

                k12_sat_overview_table = set_table_layout(
                    k12_sat_overview_table,
                    k12_sat_overview_table,
                    k12_sat_overview.columns,
                )

                k12_sat_ethnicity = k12_sat_table_data[
                    k12_sat_table_data["Category"].str.contains("|".join(ethnicity))
                ]

                k12_sat_ethnicity = k12_sat_ethnicity.dropna(axis=1, how="all")

                k12_sat_ethnicity_table = create_multi_header_table_with_container(
                    k12_sat_ethnicity, "SAT Benchmarks by Ethnicity"
                )

                k12_sat_ethnicity_table = set_table_layout(
                    k12_sat_ethnicity_table,
                    k12_sat_ethnicity_table,
                    k12_sat_ethnicity.columns,
                )

                k12_sat_subgroup = k12_sat_table_data[
                    k12_sat_table_data["Category"].str.contains("|".join(subgroup))
                ]

                k12_sat_subgroup = k12_sat_subgroup.dropna(axis=1, how="all")

                k12_sat_subgroup_table = create_multi_header_table_with_container(
                    k12_sat_subgroup, "SAT Benchmarks by Subgroup"
                )

                k12_sat_subgroup_table = set_table_layout(
                    k12_sat_subgroup_table,
                    k12_sat_subgroup_table,
                    k12_sat_subgroup.columns,
                )

    # End HS block
    # Begin K8 block
    elif school_type == "K8" or (school_id == 5874 and year_numeric >= 2021):
        if school_type == "K12":
            school_type = "K8"
        else:
            school_type = school_type

        list_of_schools = [school_id]

        k8_info_data = get_academic_data(
            list_of_schools, school_type, year_numeric, "info"
        )

        k8_info_data["Category"] = (
            k8_info_data["Category"].str.replace(" Proficient %", "").str.strip()
        )

        if len(k8_info_data.index) > 0:
            ilearn_table_data = k8_info_data.copy()

            ilearn_fig_data = k8_info_data.loc[
                :, ~k8_info_data.columns.str.contains("N-Size")
            ].copy()

            ilearn_fig_data = ilearn_fig_data.set_index("Category")
            ilearn_fig_data.columns = ilearn_fig_data.columns.str[:4]
            ilearn_fig_data = ilearn_fig_data.reset_index()

            ilearn_fig_data = (
                ilearn_fig_data.set_index("Category")
                .T.rename_axis("Year")
                .rename_axis(None, axis=1)
                .reset_index()
            )
            ilearn_fig_data["School Name"] = school_name

            ## ILEARN Charts and Tables
            categories_ela_subgroup = []
            categories_math_subgroup = []
            for s in subgroup:
                categories_ela_subgroup.append(s + "|" + "ELA")
                categories_math_subgroup.append(s + "|" + "Math")

            categories_ela_ethnicity = []
            categories_math_ethnicity = []
            for e in ethnicity:
                categories_ela_ethnicity.append(e + "|" + "ELA")
                categories_math_ethnicity.append(e + "|" + "Math")

            # ELA by Grade table
            years_by_grade_ela = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(grades_all))
                    & ilearn_table_data["Category"].str.contains("ELA")
                )
            ]

            ela_grade_table = create_multi_header_table(years_by_grade_ela)

            # ELA by Grade fig
            ela_grade_fig_data = ilearn_fig_data.filter(
                regex=r"^Grade \d\|ELA|^School Name$|^Year$", axis=1
            )

            ela_grade_line_fig = make_line_chart(ela_grade_fig_data)

            proficiency_grades_ela = create_line_fig_layout(
                ela_grade_table, ela_grade_line_fig, "ELA By Grade"
            )

            # ELA by Subgroup table
            years_by_subgroup_ela = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(subgroup))
                    & ilearn_table_data["Category"].str.contains("ELA")
                )
            ]

            ela_subgroup_table = create_multi_header_table(years_by_subgroup_ela)

            # ELA by Subgroup fig
            ela_subgroup_fig_data = ilearn_fig_data.loc[
                :,
                (ilearn_fig_data.columns.isin(categories_ela_subgroup))
                | (ilearn_fig_data.columns.isin(["School Name", "Year"])),
            ]
            ela_subgroup_line_fig = make_line_chart(ela_subgroup_fig_data)

            proficiency_subgroup_ela = create_line_fig_layout(
                ela_subgroup_table, ela_subgroup_line_fig, "ELA By Subgroup"
            )

            # ELA by Ethnicity table
            years_by_ethnicity_ela = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(ethnicity))
                    & ilearn_table_data["Category"].str.contains("ELA")
                )
            ]

            ela_ethnicity_table = create_multi_header_table(years_by_ethnicity_ela)

            # ELA by Ethnicity fig
            ela_ethnicity_fig_data = ilearn_fig_data.loc[
                :,
                (ilearn_fig_data.columns.isin(categories_ela_ethnicity))
                | (ilearn_fig_data.columns.isin(["School Name", "Year"])),
            ]
            ela_ethnicity_line_fig = make_line_chart(ela_ethnicity_fig_data)

            proficiency_ethnicity_ela = create_line_fig_layout(
                ela_ethnicity_table, ela_ethnicity_line_fig, "ELA By Ethnicity"
            )

            # Math by Grade table
            years_by_grade_math = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(grades_all))
                    & ilearn_table_data["Category"].str.contains("Math")
                )
            ]

            math_grade_table = create_multi_header_table(years_by_grade_math)

            # Math by Grade fig
            math_grade_fig_data = ilearn_fig_data.filter(
                regex=r"^Grade \d\|Math|^School Name$|^Year$", axis=1
            )
            math_grade_line_fig = make_line_chart(math_grade_fig_data)

            proficiency_grades_math = create_line_fig_layout(
                math_grade_table, math_grade_line_fig, "Math By Grade"
            )

            # Math by Subgroup Table
            years_by_subgroup_math = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(subgroup))
                    & ilearn_table_data["Category"].str.contains("Math")
                )
            ]

            math_subgroup_table = create_multi_header_table(years_by_subgroup_math)

            # Math by Subgroup fig
            math_subgroup_fig_data = ilearn_fig_data.loc[
                :,
                (ilearn_fig_data.columns.isin(categories_math_subgroup))
                | (ilearn_fig_data.columns.isin(["School Name", "Year"])),
            ]
            math_subgroup_line_fig = make_line_chart(math_subgroup_fig_data)

            proficiency_subgroup_math = create_line_fig_layout(
                math_subgroup_table, math_subgroup_line_fig, "Math By Subgroup"
            )

            # Math by Ethnicity table
            years_by_ethnicity_math = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(ethnicity))
                    & ilearn_table_data["Category"].str.contains("Math")
                )
            ]

            math_ethnicity_table = create_multi_header_table(years_by_ethnicity_math)

            # Math by Ethnicity fig
            math_ethnicity_fig_data = ilearn_fig_data.loc[
                :,
                (ilearn_fig_data.columns.isin(categories_math_ethnicity))
                | (ilearn_fig_data.columns.isin(["School Name", "Year"])),
            ]
            math_ethnicity_line_fig = make_line_chart(math_ethnicity_fig_data)

            proficiency_ethnicity_math = create_line_fig_layout(
                math_ethnicity_table, math_ethnicity_line_fig, "Math By Ethnicity"
            )

            ## ILEARN proficiency breakdown stacked bar charts
            raw_k8_info_data = get_proficiency_data(school_id)

            ilearn_proficency_data = raw_k8_info_data.loc[
                raw_k8_info_data["Year"] == year_numeric
            ].copy()

            ilearn_proficency_data = ilearn_proficency_data.dropna(axis=1)
            ilearn_proficency_data = ilearn_proficency_data.reset_index()

            for col in ilearn_proficency_data.columns:
                ilearn_proficency_data[col] = pd.to_numeric(
                    ilearn_proficency_data[col], errors="coerce"
                )

            ilearn_proficency_data = ilearn_proficency_data.filter(
                regex=r"ELA Below|ELA At|ELA Approaching|ELA Above|ELA Total|Math Below|Math At|Math Approaching|Math Above|Math Total",
                axis=1,
            )

            proficiency_rating = [
                "Below Proficiency",
                "Approaching Proficiency",
                "At Proficiency",
                "Above Proficiency",
            ]

            annotations = pd.DataFrame(columns=["Category", "Total Tested"])

            categories = grades_all + ethnicity + subgroup

            for c in categories:
                for s in subject:
                    category_subject = c + "|" + s
                    proficiency_columns = [
                        category_subject + " " + x for x in proficiency_rating
                    ]
                    total_tested = category_subject + " " + "Total Tested"

                    if total_tested in ilearn_proficency_data.columns:
                        if (
                            ilearn_proficency_data[proficiency_columns]
                            .isna()
                            .sum()
                            .sum()
                            > 0
                        ) or (
                            ilearn_proficency_data[proficiency_columns].iloc[0].sum()
                            == 0
                        ):
                            annotation_category = proficiency_columns[0].split("|")[0]
                            annotations.loc[len(annotations.index)] = [
                                annotation_category + "|" + s,
                                ilearn_proficency_data[total_tested].values[0],
                            ]

                            annotations["Total Tested"] = annotations[
                                "Total Tested"
                            ].fillna(0)
                            annotations["Total Tested"] = annotations[
                                "Total Tested"
                            ].astype(int)

                            all_proficiency_columns = proficiency_columns + [
                                total_tested
                            ]

                            ilearn_proficency_data = ilearn_proficency_data.drop(
                                all_proficiency_columns, axis=1
                            )

                        else:
                            ilearn_proficency_data[
                                proficiency_columns
                            ] = ilearn_proficency_data[proficiency_columns].divide(
                                ilearn_proficency_data[total_tested], axis="index"
                            )

                            row_list = ilearn_proficency_data[
                                proficiency_columns
                            ].values.tolist()

                            rounded = round_percentages(row_list[0])

                            rounded_percentages = pd.DataFrame([rounded])
                            rounded_percentages_cols = list(rounded_percentages.columns)
                            ilearn_proficency_data[
                                proficiency_columns
                            ] = rounded_percentages[rounded_percentages_cols]

            ilearn_proficency_data.drop(
                list(
                    ilearn_proficency_data.filter(regex="Total Proficient|ELA and Math")
                ),
                axis=1,
                inplace=True,
            )

            ilearn_proficency_data = ilearn_proficency_data.rename(
                columns=lambda x: re.sub("(Grade )(\d)", "\\2th", x)
            )

            ilearn_proficency_data.columns = [
                x.replace("3th", "3rd")
                for x in ilearn_proficency_data.columns.to_list()
            ]

            ilearn_proficency_data = (
                ilearn_proficency_data.T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )

            ilearn_proficency_data[
                ["Category", "Proficiency"]
            ] = ilearn_proficency_data["Category"].str.split("|", expand=True)

            ilearn_proficency_data.rename(columns={0: "Percentage"}, inplace=True)

            ilearn_proficency_data = ilearn_proficency_data[
                ilearn_proficency_data["Category"] != "index"
            ]

            bar_fig_title = "Proficiency Breakdown (" + year_string + ")"

            # Proficiency Breakdown - ELA by Grade - Current Year
            grade_pattern = "|".join(grades)

            grade_ela_annotations = annotations.loc[
                annotations["Category"].str.contains(grade_pattern)
                & annotations["Category"].str.contains("ELA")
            ]

            grade_ela_fig_data = ilearn_proficency_data[
                ilearn_proficency_data["Category"].isin(grades_ordinal)
                & ilearn_proficency_data["Proficiency"].str.contains("ELA")
            ]

            if not grade_ela_fig_data.empty:
                ela_grade_bar_fig = make_stacked_bar(
                    grade_ela_fig_data, bar_fig_title, grade_ela_annotations
                )
            else:
                ela_grade_bar_fig = no_data_fig_label(bar_fig_title, 100)

            # Proficiency Breakdown - Math by Grade - Current Year
            grade_math_annotations = annotations.loc[
                annotations["Category"].str.contains(grade_pattern)
                & annotations["Category"].str.contains("Math")
            ]

            grade_math_fig_data = ilearn_proficency_data[
                ilearn_proficency_data["Category"].isin(grades_ordinal)
                & ilearn_proficency_data["Proficiency"].str.contains("Math")
            ]

            if not grade_math_fig_data.empty:
                math_grade_bar_fig = make_stacked_bar(
                    grade_math_fig_data, bar_fig_title, grade_math_annotations
                )
            else:
                math_grade_bar_fig = no_data_fig_label(bar_fig_title, 100)

            # Proficiency Breakdown - ELA by Ethnicity - Current Year
            eth_pattern = "|".join(ethnicity)

            ethnicity_ela_annotations = annotations.loc[
                annotations["Category"].str.contains(eth_pattern)
                & annotations["Category"].str.contains("ELA")
            ]

            ethnicity_ela_fig_data = ilearn_proficency_data[
                ilearn_proficency_data["Category"].isin(ethnicity)
                & ilearn_proficency_data["Proficiency"].str.contains("ELA")
            ]

            if not ethnicity_ela_fig_data.empty:
                ela_ethnicity_bar_fig = make_stacked_bar(
                    ethnicity_ela_fig_data, bar_fig_title, ethnicity_ela_annotations
                )
            else:
                ela_ethnicity_bar_fig = no_data_fig_label(bar_fig_title, 100)

            # Proficiency Breakdown - Math by Ethnicity - Current Year
            ethnicity_math_annotations = annotations.loc[
                annotations["Category"].str.contains(eth_pattern)
                & annotations["Category"].str.contains("Math")
            ]

            ethnicity_math_fig_data = ilearn_proficency_data[
                ilearn_proficency_data["Category"].isin(ethnicity)
                & ilearn_proficency_data["Proficiency"].str.contains("Math")
            ]

            if not ethnicity_math_fig_data.empty:
                math_ethnicity_bar_fig = make_stacked_bar(
                    ethnicity_math_fig_data, bar_fig_title, ethnicity_math_annotations
                )
            else:
                math_ethnicity_bar_fig = no_data_fig_label(bar_fig_title, 100)

            # Proficiency Breakdown - ELA by Subgroup - Current Year
            sub_pattern = "|".join(subgroup)

            subgroup_ela_annotations = annotations.loc[
                annotations["Category"].str.contains(sub_pattern)
                & annotations["Category"].str.contains("ELA")
            ]

            subgroup_ela_fig_data = ilearn_proficency_data[
                ilearn_proficency_data["Category"].isin(subgroup)
                & ilearn_proficency_data["Proficiency"].str.contains("ELA")
            ]

            if not subgroup_ela_fig_data.empty:
                ela_subgroup_bar_fig = make_stacked_bar(
                    subgroup_ela_fig_data, bar_fig_title, subgroup_ela_annotations
                )
            else:
                ela_subgroup_bar_fig = no_data_fig_label(bar_fig_title, 100)

            # Proficiency Breakdown - Math by Subgroup - Current Year
            math_subgroup_annotations = annotations.loc[
                annotations["Category"].str.contains(sub_pattern)
                & annotations["Category"].str.contains("Math")
            ]

            subgroup_math_fig_data = ilearn_proficency_data[
                ilearn_proficency_data["Category"].isin(subgroup)
                & ilearn_proficency_data["Proficiency"].str.contains("Math")
            ]

            if not subgroup_math_fig_data.empty:
                math_subgroup_bar_fig = make_stacked_bar(
                    subgroup_math_fig_data, bar_fig_title, math_subgroup_annotations
                )
            else:
                math_subgroup_bar_fig = no_data_fig_label(bar_fig_title, 100)

        # End K-8 ILEARN block

        # IREAD - School Level Totals, Ethnicity, & Status
        both = ethnicity + subgroup + ["Total"]
        categories_iread_all = []

        for b in both:
            categories_iread_all.append(b + "|IREAD")

        public_iread_school_data = ilearn_table_data[
            ilearn_table_data["Category"].str.contains("|".join(both))
            & ilearn_table_data["Category"].str.contains("IREAD")
        ]

        public_iread_school_data = public_iread_school_data.loc[
            :,
            ~public_iread_school_data.where(public_iread_school_data.astype(bool))
            .isna()
            .all(axis=0),
        ]

        if ~public_iread_school_data.empty:
            public_iread_school_table = create_multi_header_table(
                public_iread_school_data
            )

            iread_school_fig_data = ilearn_fig_data.loc[
                :,
                (ilearn_fig_data.columns.isin(categories_iread_all))
                | (ilearn_fig_data.columns.isin(["School Name", "Year"])),
            ]

            iread_school_fig_data = iread_school_fig_data[
                iread_school_fig_data["Total|IREAD"].notna()
            ]

            public_iread_school_fig = make_line_chart(iread_school_fig_data)

            iread_school_level_layout = create_line_fig_layout(
                public_iread_school_table, public_iread_school_fig, "IREAD Breakdown"
            )

    # Layout

    # TODO: K8 or HS or K12 (combined)
    academicinfo_layout = [
        # html.Div(
        #     [
        #         html.Div(
        #             [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(iread_school_level_layout),
                    ],
                    # id="iread-school-level-layout-container",
                    # className="pagebreak-after",
                ),
                # html.Div(
                #     [
                #         html.Div(
                #             id="iread-school-details",
                #             children=[],
                #         ),
                #     ],
                #     id="iread-school-details-container",
                #     className="pagebreak-after",
                # ),
                # html.Div(
                #     [
                #         html.Div(
                #             id="iread-ilearn-ela-table",
                #             children=[],
                #         ),
                #         html.Div(
                #             id="iread-ilearn-math-table",
                #             children=[],
                #         ),
                #     ],
                #     id="ilearn-iread-table-container",
                # ),
                # html.Div(
                #     [
                #         html.Div(
                #             id="wida-breakdown",
                #             children=[],
                #         ),
                #     ],
                #     id="wida-breakdown-container",
                #     className="pagebreak-after",
                # ),
                # html.Div(
                #     [
                #         html.Div(
                #             id="wida-iread-table",
                #             children=[],
                #         ),
                #     ],
                #     id="wida-iread-table-container",
                # ),
                html.Div(
                    [
                        html.Div(proficiency_grades_ela),
                        html.Div(
                            [
                                html.Div(
                                    [html.Div(ela_grade_bar_fig)],
                                    className="pretty-container--close--top six columns",
                                ),
                            ],
                            className="bare-container--flex--center twelve columns",
                        ),
                    ],
                    # id="proficiency-ela-grades-container",
                    # className="pagebreak-after",
                ),
                html.Div(
                    [
                        html.Div(proficiency_ethnicity_ela),
                        html.Div(
                            [
                                html.Div(
                                    [html.Div(ela_ethnicity_bar_fig)],
                                    className="pretty-container--close--top six columns",
                                ),
                            ],
                            className="bare-container--flex--center twelve columns",
                        ),
                    ],
                    # id="proficiency-ela-ethnicity-container",
                    # className="pagebreak-after",
                ),
                html.Div(
                    [
                        html.Div(proficiency_subgroup_ela),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(ela_subgroup_bar_fig),
                                    ],
                                    className="pretty-container--close--top six columns",
                                ),
                            ],
                            className="bare-container--flex--center twelve columns",
                        ),
                    ],
                    # id="proficiency-ela-subgroup-container",
                    # className="pagebreak-after",
                ),
                html.Div(
                    [
                        html.Div(proficiency_grades_math),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(math_grade_bar_fig),
                                    ],
                                    className="pretty-container--close--top six columns",
                                ),
                            ],
                            className="bare-container--flex--center twelve columns",
                        ),
                    ],
                    # id="proficiency-math-grades-container",
                    # className="pagebreak-after",
                ),
                html.Div(
                    [
                        html.Div(proficiency_ethnicity_math),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(math_ethnicity_bar_fig),
                                    ],
                                    className="pretty-container--close--top six columns",
                                ),
                            ],
                            className="bare-container--flex--center twelve columns",
                        ),
                    ],
                    # id="proficiency-math-ethnicity-container",
                    # className="pagebreak-after",
                ),
                html.Div(
                    [
                        html.Div(proficiency_subgroup_math),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(math_subgroup_bar_fig),
                                    ],
                                    className="pretty-container--close--top six columns",
                                ),
                            ],
                            className="bare-container--flex--center twelve columns",
                        ),
                    ],
                    # id="proficiency-math-subgroup-container",
                ),
            ],
            id="k8-table-container",
        )
    ]

    academicinfo_hs_layout = [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(
                                    "Graduation Rate",
                                    className="label__header",
                                    style={"marginTop": "20px"},
                                ),
                            ],
                            className="bare-container--flex--center twelve columns",
                        ),
                        html.Div(k12_grad_overview_table),
                        html.Div(k12_grad_ethnicity_table),
                        html.Div(k12_grad_subgroup_table),
                    ],
                    # id="k12-grad-table-container",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(
                                    "SAT",
                                    className="label__header",
                                    style={"marginTop": "20px"},
                                ),
                            ],
                            className="bare-container--flex--center twelve columns",
                        ),
                        html.Div(k12_sat_overview_table),
                        html.Div(k12_sat_ethnicity_table),
                        html.Div(k12_sat_subgroup_table),
                    ],
                    # id="k12-sat-table-container",
                ),
            ],
            className="bare-container--flex--center twelve columns",
        )
    ]

    # ## get student level IREAD data (ICSB Schools Only)
    # iread_student_data = get_iread_student_data(school_id)

    # if excluded_years:
    #     iread_student_data = iread_student_data[
    #         ~iread_student_data["Year"].astype(int).isin(excluded_years)
    #     ]

    # # If school has no student level data (or is a Guest school), hide
    # # school details
    # if is_guest == True or len(iread_student_data.index) < 1:
    #     iread_school_details = []

    # else:
    #     # student level IREAD chart and table
    #     main_container = {"display": "block"}

    #     # Group by Year and Period - get percentage passing and not passing
    #     iread_student_pass = (
    #         iread_student_data.groupby(["Year", "Test Period"])["Status"]
    #         .value_counts(normalize=True)
    #         .reset_index(name="Percent")
    #     )

    #     # There are potentially six rows for each year: 1) Spring Pass;
    #     # 2) Spring Did Not Pass; 3) Spring No Result; 4) Summer Pass;
    #     # 5) Summer Did Not Pass; 6) Summer No Result. However, if, for example,
    #     # all students were either Pass or Did Not Pass, the opposite row will
    #     # be missing- e.g., if all students Did Not Pass, there will not be a Pass
    #     # row for that year and period

    #     # The solution is to use pd.MultiIndex.from_product. This makes a MultiIndex
    #     # from the cartesian product of multiple iterables. That is, we get a multindex
    #     # of all possible combinations from columns by index.levels (in this case, "Year"
    #     # "Test Period", and "Status" passed to .reindex. Will get a ValueError: "cannot
    #     # handle a non-unique multi-index" when there are duplicated pairs in the passed
    #     # columns, so we remove any duplicates first.
    #     iread_student_mask = iread_student_pass.duplicated(
    #         ["Year", "Test Period", "Status"]
    #     )
    #     iread_student_pass = iread_student_pass[~iread_student_mask].set_index(
    #         ["Year", "Test Period", "Status"]
    #     )
    #     iread_student_pass = (
    #         iread_student_pass.reindex(
    #             pd.MultiIndex.from_product(iread_student_pass.index.levels)
    #         )
    #         .fillna({"Test Period": "Summer", "Percent": 0})
    #         .reset_index()
    #     )

    #     # Filter to remove everything but Passing Students
    #     iread_student_pass = iread_student_pass[
    #         iread_student_pass["Status"].str.startswith("Pass")
    #     ]

    #     # Get count (nsize) for total # of Students Tested per year and period
    #     iread_student_tested = (
    #         iread_student_data.groupby(["Year", "Test Period"])["Status"]
    #         .count()
    #         .reset_index(name="N-Size")
    #     )

    #     # pivot to get Test Period as Column Name and Year as col value
    #     iread_student_tested = (
    #         iread_student_tested.pivot_table(
    #             index=["Year"], columns="Test Period", values="N-Size"
    #         )
    #         .reset_index()
    #         .rename_axis(None, axis=1)
    #     )

    #     iread_student_tested = iread_student_tested.rename(
    #         columns={"Spring": "Spring N-Size", "Summer": "Summer N-Size"}
    #     )

    #     iread_student_pass = iread_student_pass.drop(["Status"], axis=1)

    #     final_iread_student_pass = (
    #         iread_student_pass.pivot_table(
    #             index=["Year"], columns="Test Period", values="Percent"
    #         )
    #         .reset_index()
    #         .rename_axis(None, axis=1)
    #     )

    #     final_iread_student_pass = final_iread_student_pass.rename(
    #         columns={"Spring": "Spring Pass %", "Summer": "Summer Pass %"}
    #     )

    #     # merge student level data with school total
    #     iread_total_only = public_iread_school_data[
    #         public_iread_school_data["Category"] == "Total|IREAD"
    #     ]

    #     iread_total_only = iread_total_only.filter(
    #         regex=r"School", axis=1
    #     ).reset_index(drop=True)

    #     iread_total_only = iread_total_only.T.rename_axis("Year").reset_index()

    #     iread_total_only = iread_total_only.rename(columns={0: "Total|IREAD"})
    #     iread_total_only["Year"] = iread_total_only["Year"].str[:4]

    #     # IREAD Details fig
    #     iread_details_fig_data = pd.merge(
    #         final_iread_student_pass, iread_total_only, on=["Year"]
    #     )

    #     iread_details_fig_data = iread_details_fig_data.rename(
    #         columns={
    #             "Total|IREAD": "School Total",
    #         }
    #     )

    #     iread_details_fig = make_line_chart(iread_details_fig_data)

    #     # IREAD Details table
    #     iread_details_table_data = iread_details_fig_data.copy()

    #     # Combine passing and tested students
    #     iread_details_table_data = iread_details_table_data.merge(
    #         iread_student_tested, on="Year", how="inner"
    #     )
    #     iread_details_table_cols = iread_details_table_data.columns.tolist()

    #     # reorder columns (move "Total" to the end and then swap places of
    #     # "Summer" and "Spring N-Size")
    #     iread_details_table_cols.append(
    #         iread_details_table_cols.pop(
    #             iread_details_table_cols.index("School Total")
    #         )
    #     )
    #     iread_details_table_cols[2], iread_details_table_cols[-3] = (
    #         iread_details_table_cols[-3],
    #         iread_details_table_cols[2],
    #     )

    #     iread_details_table_data = iread_details_table_data[
    #         iread_details_table_cols
    #     ]

    #     # Create dataframes for other IREAD data points
    #     if iread_details_table_data.empty:
    #         iread_school_details = []

    #     else:
    #         # Number of 2nd Graders Tested and 2nd Grader Proficiency
    #         iread_grade2_count = iread_student_data[
    #             iread_student_data["Tested Grade"] == "Grade 2"
    #         ]

    #         iread_grade2_tested = (
    #             iread_grade2_count.groupby(["Year", "Test Period", "Status"])[
    #                 "Tested Grade"
    #             ]
    #             .value_counts()
    #             .reset_index(name="2nd Graders Tested")
    #         )

    #         iread_grade2_proficiency = (
    #             iread_grade2_count.groupby(["Year", "Test Period"])["Status"]
    #             .value_counts(normalize=True)
    #             .reset_index(name="2nd Graders Proficiency")
    #         )

    #         # Number of Exemptions Granted for Non-Pass Students
    #         iread_exemption_count = iread_student_data[
    #             iread_student_data["Exemption Status"] == "Exemption"
    #         ]

    #         iread_exemptions = (
    #             iread_exemption_count.groupby(["Year"])["Exemption Status"]
    #             .value_counts()
    #             .reset_index(name="No Pass (Exemption)")
    #         )

    #         # Number of Non-passing Students Advanced
    #         iread_advance_no_pass_count = iread_student_data[
    #             (iread_student_data["Status"] == "Did Not Pass")
    #             & (iread_student_data["Current Grade"] == "Grade 4")
    #         ]
    #         iread_advance_no_pass = (
    #             iread_advance_no_pass_count.groupby(["Year"])["Status"]
    #             .value_counts()
    #             .reset_index(name="No Pass (Advanced)")
    #         )

    #         # Number of Students Retained
    #         iread_retained_count = iread_student_data[
    #             (
    #                 (iread_student_data["Status"] == "Did Not Pass")
    #                 & (iread_student_data["Tested Grade"] == "Grade 3")
    #                 & (iread_student_data["Current Grade"] == "Grade 3")
    #             )
    #         ]
    #         iread_retained = (
    #             iread_retained_count.groupby(["Year"])["Status"]
    #             .value_counts()
    #             .reset_index(name="No Pass (Retained)")
    #         )

    #         # Merge iread table data
    #         iread_dfs_to_merge = [
    #             iread_details_table_data,
    #             iread_grade2_tested,
    #             iread_grade2_proficiency,
    #             iread_exemptions,
    #             iread_advance_no_pass,
    #             iread_retained,
    #         ]

    #         iread_merged = reduce(
    #             lambda left, right: pd.merge(
    #                 left,
    #                 right,
    #                 on=["Year"],
    #                 how="outer",
    #                 suffixes=("", "_remove"),
    #             ),
    #             iread_dfs_to_merge,
    #         )

    #         # select and order columns
    #         iread_merged = iread_merged[
    #             [
    #                 "Year",
    #                 "Spring Pass %",
    #                 "Spring N-Size",
    #                 "Summer Pass %",
    #                 "Summer N-Size",
    #                 "School Total",
    #                 "2nd Graders Tested",
    #                 "2nd Graders Proficiency",
    #                 "No Pass (Exemption)",
    #                 "No Pass (Advanced)",
    #                 "No Pass (Retained)",
    #             ]
    #         ]

    #         iread_final_table_data = (
    #             iread_merged.set_index("Year")
    #             .T.rename_axis("Category")
    #             .rename_axis(None, axis=1)
    #             .reset_index()
    #         )

    #         # format table data
    #         for col in iread_final_table_data.columns[1:]:
    #             iread_final_table_data[col] = pd.to_numeric(
    #                 iread_final_table_data[col], errors="coerce"
    #             )

    #         # NOTE: dataframes aren't built for row-wise operations, so if we need different
    #         # formatting for different rows, we have to do something grotesque like the following
    #         # start at 1 to again skip "Category" column
    #         for x in range(1, len(iread_final_table_data.columns)):
    #             for i in range(0, len(iread_final_table_data.index)):
    #                 if (
    #                     (i == 0)
    #                     | (i == 2)
    #                     | (i == 4)
    #                     | (i == 6)
    #                     | (i == 14)
    #                     | (i == 16)
    #                 ):
    #                     if ~np.isnan(iread_final_table_data.iat[i, x]):
    #                         iread_final_table_data.iat[i, x] = "{:.2%}".format(
    #                             iread_final_table_data.iat[i, x]
    #                         )
    #                 elif (i == 11) | (i == 13):
    #                     iread_final_table_data.iat[i, x] = "{:,.2f}".format(
    #                         iread_final_table_data.iat[i, x]
    #                     )
    #                 else:
    #                     iread_final_table_data.iat[i, x] = "{:,.0f}".format(
    #                         iread_final_table_data.iat[i, x]
    #                     )

    #         # replace Nan with "-"
    #         iread_final_table_data = iread_final_table_data.replace(
    #             {"nan": "\u2014", np.NaN: "\u2014"}, regex=True
    #         )

    #         iread_details_table = create_single_header_table(
    #             iread_final_table_data, "IREAD"
    #         )

    #         iread_school_details = create_line_fig_layout(
    #             iread_details_table, iread_details_fig, "IREAD Details"
    #         )

    # # End IREAD Details (student level) block

    # # IREAD to ILEARN Table
    # if iread_student_data.empty or ilearn_table_data.empty:
    #     iread_ilearn_ela_table = []
    #     iread_ilearn_math_table = []

    # else:
    #     iread_ilearn_ela_table = create_iread_ilearn_table(
    #         school, "ELA", excluded_years
    #     )
    #     iread_ilearn_math_table = create_iread_ilearn_table(
    #         school, "Math", excluded_years
    #     )

    # End IREAD Breakdown (school level) block

    ## WIDA - Student Level Data
    # Available WIDA data fields: 'Comprehension Proficiency Level',
    # 'Listening Proficiency Level', 'Literacy Proficiency Level',
    # 'Oral Proficiency Level', 'Reading Proficiency Level',
    # 'Speaking Proficiency Level', 'Writing Proficiency Level'

    # NOTE: Currently only displaying for K-8 Schools - may want to build
    # WIDA table for HS/K12 as well

    # Guests will never have WIDA data
    # if is_guest == True:
    #     if radio_category == "wida":
    #         main_container = {"display": "none"}
    #         empty_container = {"display": "block"}
    #         academic_information_notes_string_container = {"display": "none"}
    #         no_display_data = no_data_page("No Data to Display.", "WIDA")

    #     else:
    #         wida_iread_details_table = []
    #         wida_breakdown = []
    # else:
    #     # NOTE: Currently, the WIDA LINK file does not have a School ID column,
    #     # so we have to get a list of all STNs associated with the school (from
    #     # both IREAD and ILEARN data files) and then match
    #     all_stns = get_school_stns(school)

    #     stn_list = list(set(all_stns["STN"].to_list()))

    #     # Get student level wida data for the school by matching
    #     # against stn_list.
    #     wida_student_data = get_wida_student_data(stn_list)

    #     if excluded_years:
    #         wida_student_data = wida_student_data[
    #             ~wida_student_data["Year"].astype(int).isin(excluded_years)
    #         ]

    #     if len(wida_student_data.index) < 1:
    #         if radio_category == "wida":
    #             main_container = {"display": "none"}
    #             empty_container = {"display": "block"}
    #             academic_information_notes_string_container = {"display": "none"}
    #             no_display_data = no_data_page("No Data to Display.", "WIDA")

    #         else:
    #             wida_iread_details_table = []
    #             wida_breakdown = []

    #     else:
    #         main_container = {"display": "block"}

    #         # Get WIDA average per grade by year
    #         wida_avg_per_grade = (
    #             wida_student_data.groupby(["Year", "Tested Grade"])[
    #                 "Composite Overall Proficiency Level"
    #             ]
    #             .mean()
    #             .reset_index(name="Average")
    #         )

    #         # get WIDA total school average by year
    #         wida_avg_total = (
    #             wida_student_data.groupby(["Year"])[
    #                 "Composite Overall Proficiency Level"
    #             ]
    #             .mean()
    #             .reset_index(name="Average")
    #         )

    #         # Drop data for AHS students
    #         wida_avg_per_grade = wida_avg_per_grade.loc[
    #             wida_avg_per_grade["Tested Grade"] != "Grade 12+/Adult"
    #         ]

    #         # pivot to show average WIDA schore by grade (col) by year (row)
    #         wida_breakdown_fig_data = (
    #             wida_avg_per_grade.pivot_table(
    #                 index=["Year"], columns="Tested Grade", values="Average"
    #             )
    #             .reset_index()
    #             .rename_axis(None, axis=1)
    #         )

    #         # temporarily store and drop Year col
    #         wida_breakdown_year_col = wida_breakdown_fig_data["Year"]
    #         wida_breakdown_fig_data = wida_breakdown_fig_data.drop(["Year"], axis=1)

    #         # reindex and sort columns using only the numerical part
    #         wida_breakdown_fig_data = wida_breakdown_fig_data.reindex(
    #             sorted(wida_breakdown_fig_data.columns, key=lambda x: float(x[6:])),
    #             axis=1,
    #         )

    #         # add Year col back
    #         wida_breakdown_fig_data.insert(
    #             loc=0, column="Year", value=wida_breakdown_year_col
    #         )

    #         # Add school Average to by year calcs
    #         wida_breakdown_fig_data = pd.merge(
    #             wida_breakdown_fig_data, wida_avg_total, on="Year"
    #         )

    #         # Get N-Size for each grade for each year and add to table data
    #         wida_school_nsize_data = (
    #             wida_student_data.value_counts(["Tested Grade", "Year"])
    #             .reset_index()
    #             .rename(columns={0: "N-Size"})
    #         )
    #         wida_breakdown_nsize = pd.merge(
    #             wida_avg_per_grade,
    #             wida_school_nsize_data,
    #             on=["Year", "Tested Grade"],
    #         )

    #         # put nsize data in same format as scores
    #         wida_breakdown_nsize = wida_breakdown_nsize.drop("Average", axis=1)

    #         wida_breakdown_nsize = (
    #             wida_breakdown_nsize.pivot_table(
    #                 index=["Year"], columns="Tested Grade", values="N-Size"
    #             )
    #             .reset_index()
    #             .rename_axis(None, axis=1)
    #         )

    #         # identify year columns to get totals (named Average to match
    #         # scores df col name)
    #         wida_nsize_years = [
    #             c for c in wida_breakdown_nsize.columns if "Grade" in c
    #         ]
    #         wida_breakdown_nsize["Average"] = wida_breakdown_nsize[
    #             wida_nsize_years
    #         ].sum(axis=1)

    #         # sort nsize columns to match data dataframe (using natural sort)
    #         wida_nsize_years.sort(key=natural_keys)
    #         wida_nsize_columns_sorted = ["Year"] + wida_nsize_years + ["Average"]
    #         wida_breakdown_nsize = wida_breakdown_nsize[wida_nsize_columns_sorted]

    #         # should not have negative values, but bad data causes them to
    #         # appear from time to time
    #         wida_breakdown_fig_data[wida_breakdown_fig_data < 0] = np.NaN

    #         # Create line chart for WIDA Scores by Grade and Total
    #         wida_breakdown_fig = make_line_chart(wida_breakdown_fig_data)

    #         wida_breakdown_table_data = (
    #             wida_breakdown_fig_data.set_index("Year")
    #             .T.rename_axis("Category")
    #             .rename_axis(None, axis=1)
    #             .reset_index()
    #         )

    #         wida_breakdown_nsize = (
    #             wida_breakdown_nsize.set_index("Year")
    #             .T.rename_axis("Category")
    #             .rename_axis(None, axis=1)
    #             .reset_index()
    #         )

    #         # clean and format table data
    #         wida_breakdown_nsize.columns = wida_breakdown_nsize.columns.astype(str)
    #         wida_breakdown_nsize.columns = ["Category"] + [
    #             str(col) + "N-Size"
    #             for col in wida_breakdown_nsize.columns
    #             if "Category" not in col
    #         ]
    #         wida_breakdown_table_data.columns = (
    #             wida_breakdown_table_data.columns.astype(str)
    #         )
    #         wida_breakdown_nsize.columns = ["Category"] + [
    #             str(col) + "School"
    #             for col in wida_breakdown_nsize.columns
    #             if "Category" not in col
    #         ]

    #         for col in wida_breakdown_table_data.columns[1:]:
    #             wida_breakdown_table_data[col] = pd.to_numeric(
    #                 wida_breakdown_table_data[col], errors="coerce"
    #             )

    #         wida_breakdown_table_data = wida_breakdown_table_data.set_index(
    #             "Category"
    #         )

    #         wida_breakdown_table_data = wida_breakdown_table_data.applymap(
    #             "{:.2f}".format
    #         )
    #         wida_breakdown_table_data = wida_breakdown_table_data.reset_index()

    #         wida_breakdown_table_data = wida_breakdown_table_data.replace(
    #             {"nan": "\u2014", np.NaN: "\u2014"}, regex=True
    #         )  # add dash

    #         # merge nsize data into data to get into the format
    #         # expected by multi_table function

    #         # interweave columns and add category back
    #         wida_data_columns = [
    #             e for e in wida_breakdown_table_data.columns if "Category" not in e
    #         ]
    #         wida_nsize_columns = [
    #             e for e in wida_breakdown_nsize.columns if "Category" not in e
    #         ]
    #         wida_final_columns = list(
    #             itertools.chain(*zip(wida_data_columns, wida_nsize_columns))
    #         )
    #         wida_final_columns.insert(0, "Category")

    #         # merge and re-order using wida_final_columns
    #         wida_breakdown_data = pd.merge(
    #             wida_breakdown_table_data, wida_breakdown_nsize, on="Category"
    #         )

    #         wida_breakdown_data = wida_breakdown_data[wida_final_columns]

    #         wida_breakdown_table = create_multi_header_table(wida_breakdown_data)

    #         wida_breakdown = create_line_fig_layout(
    #             wida_breakdown_table, wida_breakdown_fig, "WIDA Breakdown"
    #         )

    #         ## WIDA to IREAD table

    #         # we are still in the wida_student_data block, but we need
    #         # both wida and iread student level dataframes to have data
    #         # in order to produce table

    #         if iread_student_data.empty:
    #             wida_iread_details_table = []

    #         else:
    #             main_container = {"display": "block"}

    #             all_stns = get_school_stns(school)

    #             wida_student_data["STN"] = wida_student_data["STN"].astype(str)

    #             # NOTE: For many schools the number of students (STNs) with
    #             # both IREAD and WIDA data will be small.
    #             wida_comp_data = wida_student_data[
    #                 ["STN", "Year", "Composite Overall Proficiency Level"]
    #             ].copy()
    #             iread_comp_data = iread_student_data[
    #                 ["STN", "Year", "Test Period", "Status", "Exemption Status"]
    #             ].copy()

    #             wida_comp_data["Year"] = wida_comp_data["Year"].astype(str)
    #             iread_comp_data["Year"] = iread_comp_data["Year"].astype(str)
    #             iread_comp_data["STN"] = iread_comp_data["STN"].astype(str)

    #             # matches all STNs with WIDA and IREAD scores from same year.
    #             # NOTE: This captures all students who took WIDA in the same year
    #             # that they took IREAD. It does not match students with a recorded
    #             # WIDA score either before or after a recorded IREAD score. While
    #             # we do not want to capture the latter, we do want to add those
    #             # students who has a prior year WIDA score. So we need to run two
    #             # merge operations, one on STN and YEAR (which captures same year
    #             # testers) and one just on STN where we search for any STN
    #             # matches where IREAD Tested Year is > than Max WIDA Tested Year
    #             wida_iread_current_match = pd.merge(
    #                 iread_comp_data, wida_comp_data, on=["STN", "Year"]
    #             )

    #             # need to differentiate between years when not merging on Year
    #             iread_comp_data = iread_comp_data.rename(
    #                 columns={"Year": "IREAD Year"}
    #             )
    #             wida_comp_data = wida_comp_data.rename(
    #                 columns={"Year": "WIDA Year"}
    #             )

    #             # find STNs where WIDA tested year < IREAD Year
    #             wida_iread_prior_match = pd.merge(
    #                 iread_comp_data, wida_comp_data, on=["STN"]
    #             )

    #             # Find Max WIDA Year value for each STN
    #             wida_year_max = (
    #                 wida_iread_prior_match.groupby(["STN"])["WIDA Year"]
    #                 .max()
    #                 .reset_index(name="WIDA Max")
    #             )

    #             # drop duplicates from the full data set (where the same STN can appear
    #             # up to 5 times) and merge with WIDA Max to add IREAD Year
    #             wida_iread_prior_match = wida_iread_prior_match.drop_duplicates(
    #                 subset=["STN"], keep="last"
    #             )
    #             wida_year_max = pd.merge(
    #                 wida_year_max, wida_iread_prior_match, on=["STN"], how="left"
    #             )

    #             # filter by STNs where IREAD Year is > then WIDA Max Year
    #             wida_stn_to_add = wida_year_max[
    #                 wida_year_max["IREAD Year"].astype(int)
    #                 > wida_year_max["WIDA Max"].astype(int)
    #             ]

    #             # Merge the prior and current testers into one df
    #             if not wida_stn_to_add.empty:
    #                 # change column names to match
    #                 wida_stn_to_add = wida_stn_to_add.drop(
    #                     ["WIDA Max", "WIDA Year"], axis=1
    #                 )
    #                 wida_stn_to_add = wida_stn_to_add.rename(
    #                     columns={"IREAD Year": "Year"}
    #                 )

    #                 wida_iread_details_data = pd.concat(
    #                     [wida_iread_current_match, wida_stn_to_add]
    #                 )

    #             else:
    #                 wida_iread_details_data = wida_iread_current_match

    #             if wida_iread_details_data.empty:
    #                 wida_iread_details_table = []

    #             else:
    #                 # Get WIDA Average by Year and Status (Pass/No Pass)
    #                 wida_iread_details_avg = (
    #                     wida_iread_details_data.groupby(["Year", "Status"])[
    #                         "Composite Overall Proficiency Level"
    #                     ]
    #                     .mean()
    #                     .reset_index(name="Average")
    #                 )

    #                 # Get N-Size for each Year and category (Pass/No Pass)
    #                 wida_iread_details_nsize = (
    #                     wida_iread_details_data.groupby("Year")["Status"]
    #                     .value_counts()
    #                     .reset_index(name="N-Size")
    #                 )

    #                 # Merge to add N-Size to WIDA Average df
    #                 wida_iread_details_final = pd.merge(
    #                     wida_iread_details_avg,
    #                     wida_iread_details_nsize,
    #                     on=["Year", "Status"],
    #                 )

    #                 wida_details_nopass = wida_iread_details_final[
    #                     wida_iread_details_final["Status"] == "Did Not Pass"
    #                 ]
    #                 wida_details_pass = wida_iread_details_final[
    #                     wida_iread_details_final["Status"] == "Pass"
    #                 ]

    #                 wida_details_pass = wida_details_pass.rename(
    #                     columns={
    #                         "Average": "Avg. WIDA for Students Passing IREAD",
    #                         "N-Size": "# of WIDA Tested Students Passing IREAD",
    #                     }
    #                 )
    #                 wida_details_nopass = wida_details_nopass.rename(
    #                     columns={
    #                         "Average": "Avg. WIDA for Students Not Passing IREAD",
    #                         "N-Size": "# of WIDA Tested Students Not Passing IREAD",
    #                     }
    #                 )

    #                 # prepare to combine
    #                 wida_details_nopass = wida_details_nopass.drop(
    #                     ["Year", "Status"], axis=1
    #                 )
    #                 wida_details_pass = wida_details_pass.drop("Status", axis=1)
    #                 wida_details_pass = wida_details_pass.reset_index(drop=True)
    #                 wida_details_nopass = wida_details_nopass.reset_index(drop=True)

    #                 wida_iread_details_table_data = pd.concat(
    #                     [wida_details_pass, wida_details_nopass], axis=1
    #                 )

    #                 for col in wida_iread_details_table_data.columns[1:]:
    #                     wida_iread_details_table_data[col] = pd.to_numeric(
    #                         wida_iread_details_table_data[col], errors="coerce"
    #                     )

    #                 wida_iread_details_nsize = wida_iread_details_table_data[
    #                     "# of WIDA Tested Students Passing IREAD"
    #                 ].fillna(0) + wida_iread_details_table_data[
    #                     "# of WIDA Tested Students Not Passing IREAD"
    #                 ].fillna(
    #                     0
    #                 )

    #                 wida_iread_details_table_data[
    #                     "N-Size"
    #                 ] = wida_iread_details_nsize
    #                 wida_iread_details_table_data[
    #                     "% of WIDA Tested Students Passing IREAD"
    #                 ] = (
    #                     wida_iread_details_table_data[
    #                         "# of WIDA Tested Students Passing IREAD"
    #                     ]
    #                     / wida_iread_details_nsize
    #                 )

    #                 wida_iread_details_table_data = (
    #                     wida_iread_details_table_data.drop(
    #                         [
    #                             "# of WIDA Tested Students Passing IREAD",
    #                             "# of WIDA Tested Students Not Passing IREAD",
    #                         ],
    #                         axis=1,
    #                     )
    #                 )

    #                 wida_iread_details_table_data = wida_iread_details_table_data[
    #                     [
    #                         "Year",
    #                         "% of WIDA Tested Students Passing IREAD",
    #                         "Avg. WIDA for Students Passing IREAD",
    #                         "Avg. WIDA for Students Not Passing IREAD",
    #                         "N-Size",
    #                     ]
    #                 ]

    #                 wida_iread_details_table_data = (
    #                     wida_iread_details_table_data.set_index("Year")
    #                     .T.rename_axis("Category")
    #                     .rename_axis(None, axis=1)
    #                     .reset_index()
    #                 )

    #                 # table format
    #                 for x in range(1, len(wida_iread_details_table_data.columns)):
    #                     for i in range(0, len(wida_iread_details_table_data.index)):
    #                         if i == 0:
    #                             if ~np.isnan(
    #                                 wida_iread_details_table_data.iat[i, x]
    #                             ):
    #                                 wida_iread_details_table_data.iat[
    #                                     i, x
    #                                 ] = "{:.2%}".format(
    #                                     wida_iread_details_table_data.iat[i, x]
    #                                 )
    #                         elif (i == 1) | (i == 2):
    #                             wida_iread_details_table_data.iat[
    #                                 i, x
    #                             ] = "{:,.2f}".format(
    #                                 wida_iread_details_table_data.iat[i, x]
    #                             )
    #                         else:
    #                             wida_iread_details_table_data.iat[
    #                                 i, x
    #                             ] = "{:,.0f}".format(
    #                                 wida_iread_details_table_data.iat[i, x]
    #                             )

    #                 # replace Nan with "-"
    #                 wida_iread_details_table_data = (
    #                     wida_iread_details_table_data.replace(
    #                         {"nan": "\u2014", np.NaN: "\u2014"}, regex=True
    #                     )
    #                 )

    #                 wida_iread_details_table = create_single_header_table(
    #                     wida_iread_details_table_data, "WIDA Details"
    #                 )

    # End WIDA to IREAD Table
    # End WIDA Breakdown (School Level) block

    return academicinfo_layout


# TODO: Add Metrics
def create_academicmetrics_layout(year: str, school_id: str) -> list:
    pass
    # return academicmetrics_layout


# TODO: Add Metrics


def create_fininfo_layout(year: str, school_id: str) -> list:
    year_string = year
    year_numeric = int(year_string)
    selected_school = get_school_index(school_id)

    # If the selected school is a guest school, load dummy data (Schooly McSchoolface).
    if selected_school["Guest"].values[0] == "Y":
        school = "9999"

    financial_data = get_financial_data(school_id)

    table_title = "Financial Information"

    if len(financial_data.columns) <= 1 or financial_data.empty:
        fininfo_layout = []

    else:
        financial_data = financial_data.drop(["School ID", "School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        available_years = financial_data.columns.difference(
            ["Category"], sort=False
        ).tolist()

        available_years = [int(c[:4]) for c in available_years]
        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year - year_numeric

        if year_numeric < most_recent_finance_year:
            financial_data.drop(
                financial_data.columns[1 : (years_to_exclude + 1)], axis=1, inplace=True
            )

        if len(financial_data.columns) > 1:
            for col in financial_data.columns[1:]:
                financial_data[col] = pd.to_numeric(
                    financial_data[col], errors="coerce"
                )

            financial_data = financial_data.set_index(["Category"])
            financial_data.loc["Total Grants"] = (
                financial_data.loc["State Grants"]
                + financial_data.loc["Federal Grants"]
            )
            financial_data.loc["Net Asset Position"] = (
                financial_data.loc["Total Assets"]
                - financial_data.loc["Total Liabilities"]
            )
            financial_data.loc["Change in Net Assets"] = (
                financial_data.loc["Operating Revenues"]
                - financial_data.loc["Operating Expenses"]
            )

            financial_data = financial_data.reset_index()

            financial_data = financial_data.iloc[:, : (max_display_years + 1)]

            # sort Year cols in ascending order (ignore Category)
            financial_data = (
                financial_data.set_index("Category")
                .sort_index(ascending=True, axis=1)
                .reset_index()
            )

            string_years = financial_data.columns.tolist()
            string_years.pop(0)
            string_years.reverse()

            # remove audit and other indicator data (it is displayed on the financial metrics page)
            financial_data = financial_data.loc[
                : (financial_data["Category"] == "Audit Information").idxmax() - 1
            ]

            ordered_categories = [
                "Revenue",
                "State Grants",
                "Federal Grants",
                "Total Grants",
                "Contributions and Donations",
                "Student Fees",
                "Other Income",
                "Financial Position",
                "Total Assets",
                "Current Assets",
                "Total Liabilities",
                "Current Liabilities",
                "Net Asset Position",
                "Financial Activities",
                "Operating Revenues",
                "Operating Expenses",
                "Change in Net Assets",
                "Supplemental Information",
                "Unrestricted Net Assets",
                "Unrestricted Cash",
                "Principal Payments",
                "Interest Expense",
                "Lease/Mortgage Payments",
                "Depreciation/Amortization",
                "Enrollment Information",
                "September ADM",
                "February ADM",
                "ADM Average",
            ]

            financial_data = financial_data[
                financial_data["Category"].isin(ordered_categories)
            ]

            financial_data = financial_data.dropna(axis=1, how="all")
            financial_data = financial_data.set_index("Category")

            financial_data = financial_data.reindex(index=ordered_categories)
            financial_data = financial_data.reset_index()

            for year in string_years:
                financial_data[year] = pd.Series(
                    ["{:,.0f}".format(val) for val in financial_data[year]],
                    index=financial_data.index,
                )

            financial_data.replace(
                [0, "0", 0.0, "0.0", 0.00, "0.00", "nan", np.nan], "", inplace=True
            )

            year_headers = [i for i in financial_data.columns if i not in ["Category"]]

            table_size = len(financial_data.columns)

            if table_size == 2:
                col_width = "four"
                category_width = 55
            elif table_size == 3:
                col_width = "five"
                category_width = 50
            elif table_size == 4:
                col_width = "six"
                category_width = 40
            elif table_size == 5:
                col_width = "seven"
                category_width = 35
            elif table_size == 6:
                col_width = "eight"
                category_width = 30
            else:
                col_width = "ten"
                category_width = 25

            data_width = 100 - category_width
            year_width = data_width / (table_size - 1)

            pad_right = str(year_width / 3) + "%"

            class_name = "pretty-container " + col_width + " columns"

            fininfo_layout = [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(table_title, className="label__header"),
                                html.Div(
                                    dash_table.DataTable(
                                        financial_data.to_dict("records"),
                                        columns=[
                                            {"name": i, "id": i}
                                            for i in financial_data.columns
                                        ],
                                        style_data={
                                            "fontSize": "12px",
                                            "fontFamily": "Inter, sans-serif",
                                            "border": "none",
                                        },
                                        style_data_conditional=[
                                            {
                                                "if": {"row_index": "odd"},
                                                "backgroundColor": "#eeeeee",
                                            },
                                            {
                                                "if": {
                                                    "filter_query": "{Category} eq 'Revenue' || {Category} eq 'Financial Position' ||{Category} eq 'Financial Activities' || {Category} eq 'Supplemental Information' || {Category} eq 'Enrollment Information' || {Category} eq 'Audit Information'"
                                                },
                                                "paddingLeft": "10px",
                                                "text-decoration": "underline",
                                                "fontWeight": "bold",
                                            },
                                            {
                                                "if": {
                                                    "row_index": 0,
                                                    "column_id": "Category",
                                                },
                                                "borderTop": ".5px solid #6783a9",
                                            },
                                            {
                                                "if": {"state": "selected"},
                                                "backgroundColor": "rgba(112,128,144, .3)",
                                                "border": "thin solid silver",
                                            },
                                        ],
                                        style_header={
                                            "backgroundColor": "#ffffff",
                                            "border": "none",
                                            "borderBottom": ".5px solid #6783a9",
                                            "fontSize": "12px",
                                            "fontFamily": "Inter, sans-serif",
                                            "color": "#6783a9",
                                            "textAlign": "center",
                                            "fontWeight": "bold",
                                        },
                                        style_cell={
                                            "whiteSpace": "normal",
                                            "height": "auto",
                                            "textAlign": "center",
                                            "color": "#6783a9",
                                            "minWidth": "25px",
                                            "width": "25px",
                                            "maxWidth": "25px",
                                        },
                                        style_cell_conditional=[
                                            {
                                                "if": {"column_id": "Category"},
                                                "textAlign": "left",
                                                "fontWeight": "500",
                                                "paddingLeft": "20px",
                                                "width": str(category_width) + "%",
                                            },
                                        ]
                                        + [
                                            {
                                                "if": {"column_id": year},
                                                "textAlign": "right",
                                                "paddingRight": pad_right,
                                                "fontWeight": "500",
                                                "width": str(year_width) + "%",
                                            }
                                            for year in year_headers
                                        ],
                                        style_as_list_view=True,
                                    )
                                ),
                            ],
                            className=class_name,
                        ),
                    ],
                    className="bare-container--flex--center twelve columns",
                )
            ]

    return fininfo_layout


def create_finmetrics_layout(year: str, school_id: str) -> list:
    year_string = year
    year_numeric = int(year_string)
    selected_school = get_school_index(school_id)

    finmetrics_layout = []
    financial_indicators_table = []
    financial_metrics_table = []

    table_title = "Financial Accountability Metrics"

    financial_data = get_financial_data(school_id)

    # Financial Metrics
    if len(financial_data.columns) > 1 or ~financial_data.empty:
        financial_data = financial_data.drop(["School ID", "School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        available_years = financial_data.columns.difference(
            ["Category"], sort=False
        ).tolist()

        available_years = [int(c[:4]) for c in available_years]
        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year - year_numeric

        if year_numeric < most_recent_finance_year:
            financial_data.drop(
                financial_data.columns[1 : (years_to_exclude + 1)], axis=1, inplace=True
            )

        if (len(financial_data.columns) > 1) | (
            (len(financial_data.columns) == 2) and (financial_data.iloc[1][1] != "0")
        ):
            financial_data = (
                financial_data.set_index("Category")
                .sort_index(ascending=True, axis=1)
                .reset_index()
            )

            financial_indicators = financial_data[
                financial_data["Category"].str.startswith("2.1.")
            ].copy()

            financial_quarter = ""
            financial_quarter = (
                financial_data.columns[-1][5:]
                if len(financial_data.columns[-1]) > 4
                else ""
            )
            financial_data = financial_data.rename(
                columns=lambda x: str(x)[:4] if x != "Category" else x
            )

            for col in financial_data.columns:
                financial_data[col] = (
                    pd.to_numeric(financial_data[col], errors="coerce")
                    .fillna(financial_data[col])
                    .tolist()
                )

            financial_data = financial_data.set_index(["Category"])
            financial_data.loc["Total Grants"] = (
                financial_data.loc["State Grants"]
                + financial_data.loc["Federal Grants"]
            )
            financial_data.loc["Net Asset Position"] = (
                financial_data.loc["Total Assets"]
                - financial_data.loc["Total Liabilities"]
            )
            financial_data.loc["Change in Net Assets"] = (
                financial_data.loc["Operating Revenues"]
                - financial_data.loc["Operating Expenses"]
            )
            financial_data = financial_data.reset_index()

            for c in financial_data.columns:
                if len(financial_data[financial_data[c] == 0].index) > 31:
                    financial_data.drop([c], inplace=True, axis=1)

            financial_values = financial_data.loc[
                : (financial_data["Category"] == "Audit Information").idxmax() - 1
            ]

            financial_metrics = calculate_financial_metrics(financial_values)

            if len(financial_metrics.columns) != 0:
                metric_display_years = max_display_years * 2

                tmp_metric = financial_metrics["Metric"]
                financial_metrics = financial_metrics.drop("Metric", axis=1)

                if len(financial_metrics.columns) < metric_display_years:
                    metric_display_years = len(financial_metrics.columns)

                financial_metrics = financial_metrics.iloc[:, -metric_display_years:]

                financial_metrics.insert(loc=0, column="Metric", value=tmp_metric)

                financial_metrics = convert_to_svg_circle(financial_metrics)

                financial_metrics = financial_metrics.fillna("")

                for x in range(1, len(financial_metrics.columns), 2):
                    if financial_metrics.iat[3, x]:
                        financial_metrics.iat[3, x] = "{:.0%}".format(
                            financial_metrics.iat[3, x]
                        )
                    if financial_metrics.iat[9, x]:
                        financial_metrics.iat[9, x] = "{:,.2f}".format(
                            financial_metrics.iat[9, x]
                        )
                    if financial_metrics.iat[10, x]:
                        financial_metrics.iat[10, x] = "{:,.2f}".format(
                            financial_metrics.iat[10, x]
                        )

                if financial_quarter:
                    financial_metrics.columns.values[-2] = (
                        financial_metrics.columns.values[-2] + " " + financial_quarter
                    )

                headers = financial_metrics.columns.tolist()

                clean_headers = ["Rate" if "Rating" in c else c for c in headers]
                year_headers = [
                    i for i in headers if "Rating" not in i and "Metric" not in i
                ]
                rating_headers = [y for y in headers if "Rating" in y]

                table_size = len(financial_metrics.columns)

                if table_size <= 3:
                    col_width = "four"
                    category_width = 70
                elif table_size > 3 and table_size <= 4:
                    col_width = "six"
                    category_width = 35
                elif table_size >= 5 and table_size <= 8:
                    col_width = "seven"
                    category_width = 30
                elif table_size == 9:
                    col_width = "eight"
                    category_width = 25
                elif table_size >= 10:
                    col_width = "nine"
                    category_width = 20

                data_width = 100 - category_width
                data_col_width = data_width / (table_size - 1)
                rating_width = year_width = data_col_width
                rating_width = rating_width / 2

                class_name = "pretty-container " + col_width + " columns"

                financial_metrics_table = [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(table_title, className="label__header"),
                                    html.Div(
                                        dash_table.DataTable(
                                            financial_metrics.to_dict("records"),
                                            columns=[
                                                {
                                                    "name": col,
                                                    "id": headers[idx],
                                                    "presentation": "markdown",
                                                }
                                                if "Rate" in col
                                                else {"name": col, "id": headers[idx]}
                                                for (idx, col) in enumerate(
                                                    clean_headers
                                                )
                                            ],
                                            style_data={
                                                "fontSize": "12px",
                                                "border": "none",
                                                "fontFamily": "Inter, sans-serif",
                                            },
                                            style_data_conditional=[
                                                {
                                                    "if": {"row_index": "odd"},
                                                    "backgroundColor": "#eeeeee",
                                                },
                                                {
                                                    "if": {
                                                        "filter_query": "{Metric} eq 'Near Term' || {Metric} eq 'Long Term' || {Metric} eq 'Other Metrics'"
                                                    },
                                                    "paddingLeft": "10px",
                                                    "text-decoration": "underline",
                                                    "fontWeight": "bold",
                                                },
                                                {
                                                    "if": {"state": "selected"},
                                                    "backgroundColor": "rgba(112,128,144, .3)",
                                                    "border": "thin solid silver",
                                                },
                                            ],
                                            style_header={
                                                "height": "20px",
                                                "backgroundColor": "#ffffff",
                                                "border": "none",
                                                "borderBottom": ".5px solid #6783a9",
                                                "fontSize": "12px",
                                                "fontFamily": "Inter, sans-serif",
                                                "color": "#6783a9",
                                                "textAlign": "center",
                                                "fontWeight": "bold",
                                            },
                                            style_cell={
                                                "whiteSpace": "normal",
                                                "height": "auto",
                                                "textAlign": "center",
                                                "color": "#6783a9",
                                                "boxShadow": "0 0",
                                                "minWidth": "25px",
                                                "width": "25px",
                                                "maxWidth": "25px",
                                            },
                                            style_cell_conditional=[
                                                {
                                                    "if": {"column_id": "Metric"},
                                                    "textAlign": "left",
                                                    "paddingLeft": "20px",
                                                    "fontWeight": "500",
                                                    "width": str(category_width) + "%",
                                                },
                                            ]
                                            + [
                                                {
                                                    "if": {"column_id": year},
                                                    "textAlign": "center",
                                                    "fontWeight": "500",
                                                    "width": str(year_width) + "%",
                                                }
                                                for year in year_headers
                                            ]
                                            + [
                                                {
                                                    "if": {"column_id": rating},
                                                    "textAlign": "center",
                                                    "fontWeight": "500",
                                                    "width": str(rating_width) + "%",
                                                }
                                                for rating in rating_headers
                                            ],
                                            style_as_list_view=True,
                                            markdown_options={"html": True},
                                        )
                                    ),
                                ],
                                className=class_name,
                            ),
                        ],
                        className="bare-container--flex--center twelve columns",
                    )
                ]

            # Financial Indicators
            if len(financial_indicators.columns) > 1 or ~financial_indicators.empty:
                financial_indicators = financial_indicators.set_index(["Category"])

                indicator_display_years = max_display_years

                if len(financial_indicators.columns) < max_display_years:
                    indicator_display_years = len(financial_indicators.columns)

                financial_indicators = financial_indicators.iloc[
                    :, -indicator_display_years:
                ]
                financial_indicators = financial_indicators.reset_index()

                financial_indicators[["Standard", "Description"]] = (
                    financial_indicators["Category"].str.split("|", expand=True).copy()
                )
                financial_indicators = financial_indicators.drop(["Category"], axis=1)

                standard = financial_indicators["Standard"]
                description = financial_indicators["Description"]
                financial_indicators = financial_indicators.drop(
                    columns=["Standard", "Description"]
                )
                financial_indicators.insert(
                    loc=0, column="Description", value=description
                )
                financial_indicators.insert(loc=0, column="Standard", value=standard)

                financial_indicators = convert_to_svg_circle(financial_indicators)

                headers = financial_indicators.columns.tolist()
                year_headers = [
                    x for x in headers if "Description" not in x and "Standard" not in x
                ]

                financial_indicators_table = [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(
                                        "Other Financial Accountability Indicators",
                                        className="label__header",
                                    ),
                                    html.Div(
                                        dash_table.DataTable(
                                            financial_indicators.to_dict("records"),
                                            columns=[
                                                {
                                                    "name": col,
                                                    "id": headers[idx],
                                                    "presentation": "markdown",
                                                }
                                                if col in year_headers
                                                else {"name": col, "id": headers[idx]}
                                                for (idx, col) in enumerate(headers)
                                            ],
                                            style_data={
                                                "fontSize": "12px",
                                                "fontFamily": "Inter, sans-serif",
                                                "border": "none",
                                            },
                                            style_data_conditional=[
                                                {
                                                    "if": {"row_index": "odd"},
                                                    "backgroundColor": "#eeeeee",
                                                }
                                            ]
                                            + [
                                                {
                                                    "if": {"state": "selected"},
                                                    "backgroundColor": "rgba(112,128,144, .3)",
                                                    "border": "thin solid silver",
                                                }
                                            ]
                                            + [
                                                {
                                                    "if": {"column_id": year},
                                                    "textAlign": "center",
                                                    "fontWeight": "500",
                                                    "width": "8%",
                                                }
                                                for year in year_headers
                                            ],
                                            style_header={
                                                "height": "20px",
                                                "backgroundColor": "#ffffff",
                                                "border": "none",
                                                "borderBottom": ".5px solid #6783a9",
                                                "fontSize": "12px",
                                                "fontFamily": "Inter, sans-serif",
                                                "color": "#6783a9",
                                                "textAlign": "center",
                                                "fontWeight": "bold",
                                            },
                                            style_cell={
                                                "whiteSpace": "normal",
                                                "height": "auto",
                                                "textAlign": "center",
                                                "color": "#6783a9",
                                            },
                                            style_cell_conditional=[
                                                {
                                                    "if": {"column_id": "Standard"},
                                                    "textAlign": "center",
                                                    "fontWeight": "500",
                                                    "width": "7%",
                                                },
                                                {
                                                    "if": {"column_id": "Description"},
                                                    "width": "45%",
                                                    "textAlign": "Left",
                                                    "fontWeight": "500",
                                                    "paddingLeft": "20px",
                                                },
                                            ],
                                            markdown_options={"html": True},
                                        ),
                                    ),
                                ],
                                className="pretty-container eight columns",
                            ),
                        ],
                        className="bare-container--flex--center twelve columns",
                    )
                ]

    finmetrics_layout = [
        html.Div(
            [
                html.Div(financial_metrics_table),
                html.Div(financial_indicators_table),
            ]
        )
    ]

    return finmetrics_layout


def create_finanalysis_layout(year: str, school_id: str) -> list:
    year_string = year
    year_numeric = int(year_string)
    previous_year_numeric = year_numeric - 1

    selected_school = get_school_index(school_id)
    display_years = [str(previous_year_numeric)] + [year]

    financial_position_table = []  # type: list
    financial_activities_table = []  # type: list
    financial_ratios_table = []  # type: list
    per_student_table = []  # type: list
    revenue_expenses_fig = go.Figure()
    assets_liabilities_fig = go.Figure()

    RandE_title = "Revenue and Expenses"
    AandL_title = "Assets and Liabilities"
    FP_title = "2-Year Financial Position"
    FA_title = "2-Year Financial Activities"

    if selected_school["Guest"].values[0] == "Y":
        school_id = "9999"

    financial_data = get_financial_data(school_id)

    if len(financial_data.columns) > 1 or ~financial_data.empty:
        financial_data = financial_data.drop(["School ID", "School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        if "Q" in financial_data.columns[1]:
            financial_data = financial_data.drop(financial_data.columns[[1]], axis=1)

        available_years = financial_data.columns.difference(
            ["Category"], sort=False
        ).tolist()
        available_years = [int(c[:4]) for c in available_years]
        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year - year_numeric

        if year_numeric < most_recent_finance_year:
            financial_data.drop(
                financial_data.columns[1 : (years_to_exclude + 1)], axis=1, inplace=True
            )

        if len(financial_data.columns) > 1:
            color = ["#74a2d7", "#df8f2d"]

            for col in financial_data.columns:
                financial_data[col] = (
                    pd.to_numeric(financial_data[col], errors="coerce")
                    .fillna(financial_data[col])
                    .tolist()
                )

            financial_data = financial_data.set_index(["Category"])
            financial_data.loc["Total Grants"] = (
                financial_data.loc["State Grants"]
                + financial_data.loc["Federal Grants"]
            )
            financial_data.loc["Net Asset Position"] = (
                financial_data.loc["Total Assets"]
                - financial_data.loc["Total Liabilities"]
            )
            financial_data.loc["Change in Net Assets"] = (
                financial_data.loc["Operating Revenues"]
                - financial_data.loc["Operating Expenses"]
            )
            financial_data = financial_data.reset_index()

            financial_data = financial_data.iloc[:, : (max_display_years + 1)]

            financial_data_fig = financial_data.copy()

            for c in financial_data_fig.columns:
                if len(financial_data_fig[financial_data_fig[c] == 0].index) > 31:
                    financial_data_fig.drop([c], inplace=True, axis=1)

            string_fig_years = financial_data_fig.columns.tolist()
            string_fig_years.pop(0)
            string_fig_years.reverse()

            ## Fig 1: Operating Revenue, Operating Expenses, & Change in
            # Net Assets
            revenue_expenses_data = financial_data_fig[
                financial_data_fig["Category"].isin(
                    ["Operating Expenses", "Operating Revenues"]
                )
            ]
            revenue_expenses_data = revenue_expenses_data.reset_index(drop=True)

            for col in revenue_expenses_data.columns:
                revenue_expenses_data[col] = (
                    pd.to_numeric(revenue_expenses_data[col], errors="coerce")
                    .fillna(revenue_expenses_data[col])
                    .tolist()
                )

            revenue_expenses_data = revenue_expenses_data.iloc[:, ::-1]
            revenue_expenses_data.insert(
                0, "Category", revenue_expenses_data.pop("Category")
            )

            revenue_expenses_data = revenue_expenses_data.set_index("Category").T

            revenue_expenses_bar_fig = px.bar(
                data_frame=revenue_expenses_data,
                x=string_fig_years,
                y=[c for c in revenue_expenses_data.columns],
                color_discrete_sequence=color,
                barmode="group",
            )

            step = 6

            tick_val = round_nearest(revenue_expenses_data, step)

            revenue_expenses_bar_fig.update_xaxes(
                showline=False,
                linecolor="#a9a9a9",
                ticks="outside",
                tickcolor="#a9a9a9",
                title="",
            )
            revenue_expenses_bar_fig.update_yaxes(
                showgrid=True,
                gridcolor="#a9a9a9",
                title="",
                tickmode="linear",
                tick0=0,
                dtick=tick_val,
            )

            revenue_expenses_bar_fig.update_layout(
                margin=dict(l=40, r=40, t=40, b=60),
                font=dict(family="Inter, sans-serif", color="#6783a9", size=12),
                hovermode="x unified",
                showlegend=True,
                height=400,
                legend=dict(orientation="h", title="", traceorder="reversed"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            revenue_expenses_bar_fig["data"][0][
                "hovertemplate"
            ] = "Operating Revenues<br>$ %{y:,.2f}<extra></extra>"
            revenue_expenses_bar_fig["data"][1][
                "hovertemplate"
            ] = "Operating Expenses<br>$ %{y:,.2f}<extra></extra>"

            revenue_expenses_line_data = financial_data_fig[
                financial_data_fig["Category"].isin(["Change in Net Assets"])
            ]
            revenue_expenses_line_data = revenue_expenses_line_data.reset_index(
                drop=True
            )

            revenue_expenses_line_data = revenue_expenses_line_data.replace(
                "", 0, regex=True
            )

            cols = [
                i for i in revenue_expenses_line_data.columns if i not in ["Category"]
            ]

            for col in cols:
                revenue_expenses_line_data[col] = pd.to_numeric(
                    revenue_expenses_line_data[col], errors="coerce"
                )

            revenue_expenses_line_data = revenue_expenses_line_data.iloc[:, ::-1]
            revenue_expenses_line_data.pop("Category")
            revenue_expenses_line_data = (
                revenue_expenses_line_data.loc[:, :].values.flatten().tolist()
            )

            revenue_expenses_line_fig = px.line(
                x=string_fig_years,
                y=revenue_expenses_line_data,
                markers=True,
                color_discrete_sequence=["#75851b"],
            )

            revenue_expenses_fig = go.Figure(
                data=revenue_expenses_line_fig.data + revenue_expenses_bar_fig.data,
                layout=revenue_expenses_bar_fig.layout,
            )
            revenue_expenses_fig["data"][0]["showlegend"] = True
            revenue_expenses_fig["data"][0]["name"] = "Change in Net Assets"
            revenue_expenses_fig["data"][0][
                "hovertemplate"
            ] = "Change in Net Assets<br>$ %{y:,.2f}<extra></extra>"

            ## Fig 2: Assets + Liabilities per year bars and Net Asset Position as Line
            assets_liabilities_data = financial_data_fig[
                financial_data_fig["Category"].isin(
                    ["Total Assets", "Total Liabilities"]
                )
            ]
            assets_liabilities_data = assets_liabilities_data.reset_index(drop=True)

            assets_liabilities_data = assets_liabilities_data.replace("", 0, regex=True)

            cols = [i for i in assets_liabilities_data.columns if i not in ["Category"]]

            for col in cols:
                assets_liabilities_data[col] = pd.to_numeric(
                    assets_liabilities_data[col], errors="coerce"
                )

            assets_liabilities_data = assets_liabilities_data.iloc[:, ::-1]
            assets_liabilities_data.insert(
                0, "Category", assets_liabilities_data.pop("Category")
            )

            assets_liabilities_data = assets_liabilities_data.set_index("Category").T

            assets_liabilities_bar_fig = px.bar(
                data_frame=assets_liabilities_data,
                x=string_fig_years,
                y=[c for c in assets_liabilities_data.columns],
                color_discrete_sequence=color,
                barmode="group",
            )

            tick_val = round_nearest(assets_liabilities_data, step)

            assets_liabilities_bar_fig.update_xaxes(
                showline=False,
                linecolor="#a9a9a9",
                ticks="outside",
                tickcolor="#a9a9a9",
                title="",
            )
            assets_liabilities_bar_fig.update_yaxes(
                showgrid=True,
                gridcolor="#a9a9a9",
                title="",
                tickmode="linear",
                tick0=0,
                dtick=tick_val,
            )

            assets_liabilities_bar_fig.update_layout(
                margin=dict(l=40, r=40, t=40, b=60),
                font=dict(family="Inter, sans-serif", color="#6783a9", size=12),
                hovermode="x unified",
                legend=dict(orientation="h", title="", traceorder="reversed"),
                height=400,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            assets_liabilities_bar_fig["data"][1][
                "hovertemplate"
            ] = "Total Liabilities<br>$ %{y:,.2f}<extra></extra>"
            assets_liabilities_bar_fig["data"][0][
                "hovertemplate"
            ] = "Total Assets<br>$ %{y:,.2f}<extra></extra>"

            assets_liabilities_line_data = financial_data_fig.iloc[10].tolist()
            assets_liabilities_line_data.pop(0)
            assets_liabilities_line_data.reverse()

            assets_liabilities_line_fig = px.line(
                x=string_fig_years,
                y=assets_liabilities_line_data,
                markers=True,
                color_discrete_sequence=["#75851b"],
            )

            assets_liabilities_fig = go.Figure(
                data=assets_liabilities_line_fig.data + assets_liabilities_bar_fig.data,
                layout=assets_liabilities_bar_fig.layout,
            )

            assets_liabilities_fig["data"][0]["showlegend"] = True
            assets_liabilities_fig["data"][0]["name"] = "Net Asset Position"
            assets_liabilities_fig["data"][0][
                "hovertemplate"
            ] = "Net Asset Position<br>$ %{y:,.2f}<extra></extra>"

            ## Two Year Finance Tables (Financial Position and Financial Activities)
            default_headers = ["Category"] + display_years

            idx1 = financial_data.index[
                financial_data["Category"] == "ADM Average"
            ].values[0]
            idx2 = financial_data.index[
                financial_data["Category"] == "State Grants"
            ].values[0]

            financial_data = financial_data.loc[
                :, ~((financial_data.loc[idx1] == 0) | (financial_data.loc[idx2] == 0))
            ]

            if set(default_headers).issubset(set(financial_data.columns)):
                financial_data = financial_data[default_headers]

            else:
                missing_year = list(
                    set(default_headers).difference(financial_data.columns)
                )
                remaining_year = [
                    e for e in default_headers if e not in ("Category", missing_year[0])
                ]
                i = 1 if (int(missing_year[0]) < int(remaining_year[0])) else 0

                financial_data.insert(loc=i, column=missing_year[0], value=0)
                financial_data = financial_data[default_headers]

            financial_data = (
                financial_data.set_index("Category")
                .sort_index(ascending=True, axis=1)
                .reset_index()
            )

            # Table 1: 2-Year Financial Position
            financial_position_categories = [
                "Total Assets",
                "Current Assets",
                "Total Liabilities",
                "Current Liabilities",
                "Net Asset Position",
            ]
            financial_position_table = create_financial_analysis_table(
                financial_data, financial_position_categories
            )

            # Table 2: 2-Year Financial Activities
            financial_activity_categories = [
                "Operating Revenues",
                "Operating Expenses",
                "Change in Net Assets",
            ]
            financial_activities_table = create_financial_analysis_table(
                financial_data, financial_activity_categories
            )

            # Table #3: Per-Student Expenditures
            per_student_categories = [
                "State Grants",
                "Operating Revenues",
                "Operating Expenses",
                "Change in Net Assets",
                "ADM Average",
            ]
            per_student_table = create_financial_analysis_table(
                financial_data, per_student_categories
            )

            # Table 4: Financial Ratios
            school_corp = int(selected_school["Corporation ID"].values[0])
            financial_ratios_data = get_financial_ratios(school_corp)
            ratio_years = financial_ratios_data["Year"].astype(str).tolist()

            if len(financial_ratios_data.index) > 0 and set(ratio_years).isdisjoint(
                default_headers
            ):
                financial_ratios_data = financial_ratios_data.drop(
                    columns=["Corporation Name", "Corporation ID", "School ID"]
                )
                financial_ratios_data = (
                    financial_ratios_data.set_index("Year")
                    .T.rename_axis("Category")
                    .rename_axis(None, axis=1)
                    .reset_index()
                )

                financial_ratios_data.columns = financial_ratios_data.columns.astype(
                    str
                )

                for col in financial_ratios_data.columns[1:]:
                    financial_ratios_data[col] = pd.to_numeric(
                        financial_ratios_data[col], errors="coerce"
                    )

                default_df = pd.DataFrame(columns=default_headers)

                default_df["Category"] = financial_ratios_data["Category"]

                non_duplicate_cols = ["Category"] + [
                    i
                    for i in default_df.columns.to_list()
                    if i not in financial_ratios_data.columns.to_list()
                ]

                final_ratios_data = default_df.combine_first(
                    default_df[non_duplicate_cols].merge(financial_ratios_data, "left")
                )
                final_ratios_data = final_ratios_data[default_headers]

                final_ratios_data = final_ratios_data.fillna("N/A")

                for year in display_years:
                    if (final_ratios_data[year] != "N/A").any():
                        final_ratios_data[year] = pd.Series(
                            [
                                "{0:.2f}%".format(val * 100)
                                for val in final_ratios_data[year]
                            ],
                            index=final_ratios_data.index,
                        )

                financial_ratios_table = [
                    html.Label("Financial Ratios", className="label__header"),
                    html.P(""),
                    html.Div(
                        dash_table.DataTable(
                            data=final_ratios_data.to_dict("records"),
                            columns=[
                                {
                                    "name": i,
                                    "id": i,
                                    "type": "numeric",
                                    "format": FormatTemplate.percentage(2),
                                }
                                for i in final_ratios_data.columns
                            ],
                            style_data={
                                "fontSize": "11px",
                                "fontFamily": "Inter, sans-serif",
                            },
                            style_data_conditional=[
                                {
                                    "if": {
                                        "column_id": "Category",
                                    },
                                    "borderRight": ".5px solid #6783a9",
                                    "fontWeight": "600",
                                    "fontSize": "11px",
                                },
                                {
                                    "if": {
                                        "filter_query": "{Category} eq 'Occupancy Ratio'"
                                    },
                                    "borderTop": ".5px solid #6783a9",
                                },
                                {
                                    "if": {"state": "selected"},
                                    "backgroundColor": "rgba(112,128,144, .3)",
                                    "border": "thin solid silver",
                                },
                            ],
                            style_header={
                                "height": "20px",
                                "backgroundColor": "#ffffff",
                                "borderBottom": ".5px solid #6783a9",
                                "borderTop": "none",
                                "borderRight": "none",
                                "borderLeft": "none",
                                "fontSize": "12px",
                                "fontFamily": "Montserrat, sans-serif",
                                "color": "#6783a9",
                                "textAlign": "center",
                                "fontWeight": "bold",
                            },
                            style_header_conditional=[
                                {
                                    "if": {
                                        "column_id": "Category",
                                    },
                                    "borderRight": ".5px solid #6783a9",
                                    "borderBottom": ".5px solid #6783a9",
                                    "textAlign": "left",
                                },
                            ],
                            style_cell={
                                "border": "none",
                                "whiteSpace": "normal",
                                "height": "auto",
                                "textAlign": "center",
                                "color": "#6783a9",
                                "minWidth": "25px",
                                "width": "25px",
                                "maxWidth": "25px",
                            },
                            style_cell_conditional=[
                                {
                                    "if": {"column_id": "Category"},
                                    "textAlign": "left",
                                    "paddingLeft": "20px",
                                    "width": "40%",
                                }
                            ],
                        )
                    ),
                ]

    finanalysis_layout = [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(
                                    RandE_title,
                                    className="label__header",
                                ),
                                dcc.Graph(
                                    figure=revenue_expenses_fig,
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="pretty-container six columns",
                        ),
                        html.Div(
                            [
                                html.Label(
                                    AandL_title,
                                    className="label__header",
                                ),
                                dcc.Graph(
                                    figure=assets_liabilities_fig,
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="pretty-container six columns",
                        ),
                    ],
                    className="bare-container--flex--nocenter twelve columns",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(
                                    FP_title,
                                    className="label__header",
                                ),
                                html.P(""),
                                html.Div(financial_position_table),
                            ],
                            className="pretty-container--left six columns",
                        ),
                        html.Div(
                            [
                                html.Label(
                                    FA_title,
                                    className="label__header",
                                ),
                                html.P(""),
                                html.Div(financial_activities_table),
                            ],
                            className="pretty-container six columns",
                        ),
                    ],
                    className="bare-container--flex twelve columns",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    financial_ratios_table
                                    # children=[],
                                ),
                            ],
                            className="pretty-container--left six columns",
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "Revenues and Expenditures Per Student",
                                    className="label__header",
                                ),
                                html.P(""),
                                html.Div(per_student_table),
                            ],
                            className="pretty-container six columns",
                        ),
                    ],
                    className="bare-container--flex twelve columns",
                ),
            ],
        ),
    ]

    return finanalysis_layout


def create_orgcompliance_layout(year: str, school_id: str) -> list:
    selected_school = get_school_index(school_id)
    year_numeric = int(year)
    year_string = str(year_numeric)

    orgcompliance_layout = []

    if selected_school["Guest"].values[0] == "Y":
        school_id = "9999"

    financial_data = get_financial_data(school_id)

    if len(financial_data.columns) > 1 or ~financial_data.empty:
        if selected_school["Guest"].values[0] == "Y":
            table_title = "Organizational and Operational Accountability (SAMPLE DATA)"
        else:
            table_title = "Organizational and Operational Accountability"

        financial_data = financial_data.drop(["School ID", "School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        if "Q" in financial_data.columns[1]:
            if "Q4" in financial_data.columns[1]:
                financial_data = financial_data.rename(
                    columns={
                        c: c[:4]
                        for c in financial_data.columns
                        if c not in ["Category"]
                    }
                )

            else:
                financial_data = financial_data.drop(
                    financial_data.columns[[1]], axis=1
                )

        available_years = financial_data.columns.difference(
            ["Category"], sort=False
        ).tolist()
        available_years = [int(c[:4]) for c in available_years]
        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year - year_numeric

        if year_numeric < most_recent_finance_year:
            financial_data.drop(
                financial_data.columns[1 : (years_to_exclude + 1)], axis=1, inplace=True
            )

        if len(financial_data.columns) > 1:
            financial_data = financial_data.iloc[:, : (max_display_years + 1)]

            financial_data = (
                financial_data.set_index("Category")
                .sort_index(ascending=True, axis=1)
                .reset_index()
            )

            organizational_indicators = financial_data[
                financial_data["Category"].str.startswith("3.")
            ].copy()
            organizational_indicators[
                ["Standard", "Description"]
            ] = organizational_indicators["Category"].str.split("|", expand=True)

            organizational_indicators = organizational_indicators.drop(
                "Category", axis=1
            )
            standard = organizational_indicators["Standard"]
            description = organizational_indicators["Description"]
            organizational_indicators = organizational_indicators.drop(
                columns=["Standard", "Description"]
            )
            organizational_indicators.insert(
                loc=0, column="Description", value=description
            )
            organizational_indicators.insert(loc=0, column="Standard", value=standard)

            organizational_indicators = convert_to_svg_circle(organizational_indicators)

            headers = organizational_indicators.columns.tolist()
            year_headers = [
                x for x in headers if "Description" not in x and "Standard" not in x
            ]

            orgcompliance_layout = [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(table_title, className="label__header"),
                                dash_table.DataTable(
                                    organizational_indicators.to_dict("records"),
                                    columns=[
                                        {"name": i, "id": i, "presentation": "markdown"}
                                        if i in year_headers
                                        else {
                                            "name": i,
                                            "id": i,
                                        }
                                        for i in headers
                                    ],
                                    style_data={
                                        "fontSize": "12px",
                                        "border": "none",
                                        "fontFamily": "Inter, sans-serif",
                                    },
                                    style_data_conditional=[
                                        {
                                            "if": {"row_index": "odd"},
                                            "backgroundColor": "#eeeeee",
                                        }
                                    ]
                                    + [
                                        {
                                            "if": {"state": "selected"},
                                            "backgroundColor": "rgba(112,128,144, .3)",
                                            "border": "thin solid silver",
                                        }
                                    ]
                                    + [
                                        {
                                            "if": {"column_id": year},
                                            "textAlign": "center",
                                            "fontWeight": "500",
                                            "width": "5%",
                                        }
                                        for year in year_headers
                                    ],
                                    style_header={
                                        "height": "20px",
                                        "backgroundColor": "#ffffff",
                                        "border": "none",
                                        "borderBottom": ".5px solid #6783a9",
                                        "fontSize": "12px",
                                        "fontFamily": "Montserrat, sans-serif",
                                        "color": "#6783a9",
                                        "textAlign": "center",
                                        "fontWeight": "bold",
                                    },
                                    style_cell={
                                        "whiteSpace": "normal",
                                        "height": "auto",
                                        "textAlign": "center",
                                        "color": "#6783a9",
                                        "minWidth": "25px",
                                        "width": "25px",
                                        "maxWidth": "25px",
                                    },
                                    style_cell_conditional=[
                                        {
                                            "if": {"column_id": "Standard"},
                                            "textAlign": "Center",
                                            "fontWeight": "500",
                                            "width": "7%",
                                        },
                                        {
                                            "if": {"column_id": "Description"},
                                            "width": "50%",
                                            "textAlign": "Left",
                                            "fontWeight": "500",
                                        },
                                    ],
                                    markdown_options={"html": True},
                                ),
                            ],
                            className="pretty-container ten columns",
                        ),
                    ],
                    className="bare-container--flex--center twelve columns",
                ),
            ]

    return orgcompliance_layout
