##################################
# ICSB Dashboard - Print Layouts #
##################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     09/23/24

# NOTE: lots of duplicative code here. eventually want to replace the
# layouts in all of the other pages with calls to these functions, but
# would need to make sure all functionality is included

from dash import dcc, html, dash_table
from dash.dash_table import FormatTemplate
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from .globals import (
    ethnicity,
    subgroup,
    grades_all,
    max_display_years,
)

from .load_data import (
    get_school_index,
    get_financial_data,
    get_financial_ratios,
    get_corp_demographic_data,
    get_school_demographic_data,
    get_attendance_data,
    get_academic_data,
)

from .calculations import round_nearest, conditional_fillna

# from .process_data import process_discipline_data

from .calculate_metrics import (
    calculate_financial_metrics,
    calculate_high_school_metrics,
    calculate_adult_high_school_metrics,
    calculate_attendance_metrics,
    calculate_iread_metrics,
    calculate_values,
    calculate_metrics,
)

from .string_helpers import convert_to_svg_circle

from .tables import (
    no_data_table,
    create_metric_table,
    create_proficiency_key,
    create_multi_header_table_with_container,
    create_single_header_table,
    create_multi_header_table,
    create_financial_analysis_table,
)

from .charts import (
    no_data_fig_label,
    make_line_chart,
    make_demographics_bar_chart,
    make_line_chart,
)

from .layouts import create_line_fig_layout, set_table_layout


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

    if school_type == "ahs":
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
                                        html.Div(
                                            attendance_table,
                                            style={"marginTop": "10px"},
                                        ),
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
                    className="bare-container--relative twelve columns pagebreak",
                ),
            ]
        )
    ]

    return about_layout


def create_academicinfo_layout(year: str, school_id: str) -> list:
    year_string = year
    year_numeric = int(year_string)

    selected_school = get_school_index(school_id)
    school_type = selected_school["School Type"].values[0]
    school_name = selected_school["School Name"].values[0]

    hs_grad_overview_table = []  # type: list
    hs_grad_ethnicity_table = []  # type: list
    hs_grad_subgroup_table = []  # type: list
    grad_label = []

    hs_sat_overview_table = []  # type: list
    hs_sat_ethnicity_table = []  # type: list
    hs_sat_subgroup_table = []  # type: list
    sat_label = []

    iread_school_level_layout = []  # type: list

    proficiency_grades_ela = []  # type: list
    proficiency_ethnicity_ela = []  # type: list
    proficiency_subgroup_ela = []  # type: list
    proficiency_grades_math = []  # type: list
    proficiency_ethnicity_math = []  # type: list
    proficiency_subgroup_math = []  # type: list

    # HS
    if (
        school_type == "hs"
        or school_type == "k12"
        or school_type == "ahs"
        or (school_id == 5874 and year_numeric < 2021)
    ):
        if school_type == "k12":
            scoped_type = "hs"
        else:
            scoped_type = school_type

        list_of_schools = [school_id]

        hs_info_data = get_academic_data(
            list_of_schools, scoped_type, year_numeric, "info"
        )

        # TODO: Add figs for SAT and Grad Rates
        if len(hs_info_data.index) > 1 and not hs_info_data.empty:
            hs_info_data.columns = hs_info_data.columns.astype(str)

            grad_overview_categories = ["Total", "Non Waiver", "State Average"]

            if school_type == "ahs":
                grad_overview_categories = [
                    "Total|Graduation Rate",
                    "Grade 12|Graduation Rate",
                    "Graduation to Enrollment|Graduation Rate",
                    "CCR Percentage",
                ]

                graduation_data = hs_info_data[
                    hs_info_data["Category"].isin(grad_overview_categories)
                ].copy()

            else:
                # hs Graduation Rate data
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

                hs_grad_overview_table = create_multi_header_table_with_container(
                    grad_overview, "Graduation Data"
                )

                hs_grad_overview_table = set_table_layout(
                    hs_grad_overview_table,
                    hs_grad_overview_table,
                    grad_overview.columns,
                )

                grad_label = [
                    html.Div(
                        [
                            html.Label(
                                "Graduation Rate",
                                className="label__header",
                                style={"marginTop": "20px"},
                            ),
                        ],
                        className="bare-container--flex--center twelve columns",
                    )
                ]

                if school_type != "ahs":
                    grad_ethnicity = graduation_data[
                        graduation_data["Category"].str.contains("|".join(ethnicity))
                    ]

                    grad_ethnicity = grad_ethnicity.dropna(axis=1, how="all")

                    hs_grad_ethnicity_table = create_multi_header_table_with_container(
                        grad_ethnicity, "Graduation Rate by Ethnicity"
                    )

                    hs_grad_ethnicity_table = set_table_layout(
                        hs_grad_ethnicity_table,
                        hs_grad_ethnicity_table,
                        grad_ethnicity.columns,
                    )

                    grad_subgroup = graduation_data[
                        graduation_data["Category"].str.contains("|".join(subgroup))
                    ]

                    grad_subgroup = grad_subgroup.dropna(axis=1, how="all")

                    hs_grad_subgroup_table = create_multi_header_table_with_container(
                        grad_subgroup, "Graduation Rate by Subgroup"
                    )
                    hs_grad_subgroup_table = set_table_layout(
                        hs_grad_subgroup_table,
                        hs_grad_subgroup_table,
                        grad_subgroup.columns,
                    )

            hs_sat_table_data = hs_info_data[
                hs_info_data["Category"].str.contains("Benchmark %")
            ].copy()

            hs_sat_table_data = hs_sat_table_data.loc[
                :,
                ~hs_sat_table_data.where(hs_sat_table_data.astype(bool))
                .isna()
                .all(axis=0),
            ]

            if len(hs_sat_table_data.columns) > 1 and len(hs_sat_table_data.index) > 0:
                hs_sat_table_data["Category"] = (
                    hs_sat_table_data["Category"]
                    .str.replace("Benchmark %", "")
                    .str.strip()
                )

                hs_sat_overview = hs_sat_table_data[
                    hs_sat_table_data["Category"].str.contains("Total")
                ]

                hs_sat_overview = hs_sat_overview.dropna(axis=1, how="all")

                hs_sat_overview_table = create_multi_header_table_with_container(
                    hs_sat_overview, "SAT Overview"
                )

                hs_sat_overview_table = set_table_layout(
                    hs_sat_overview_table,
                    hs_sat_overview_table,
                    hs_sat_overview.columns,
                )

                hs_sat_ethnicity = hs_sat_table_data[
                    hs_sat_table_data["Category"].str.contains("|".join(ethnicity))
                ]

                hs_sat_ethnicity = hs_sat_ethnicity.dropna(axis=1, how="all")

                hs_sat_ethnicity_table = create_multi_header_table_with_container(
                    hs_sat_ethnicity, "SAT Benchmarks by Ethnicity"
                )

                hs_sat_ethnicity_table = set_table_layout(
                    hs_sat_ethnicity_table,
                    hs_sat_ethnicity_table,
                    hs_sat_ethnicity.columns,
                )

                hs_sat_subgroup = hs_sat_table_data[
                    hs_sat_table_data["Category"].str.contains("|".join(subgroup))
                ]

                hs_sat_subgroup = hs_sat_subgroup.dropna(axis=1, how="all")

                hs_sat_subgroup_table = create_multi_header_table_with_container(
                    hs_sat_subgroup, "SAT Benchmarks by Subgroup"
                )

                hs_sat_subgroup_table = set_table_layout(
                    hs_sat_subgroup_table,
                    hs_sat_subgroup_table,
                    hs_sat_subgroup.columns,
                )

                sat_label = [
                    html.Div(
                        [
                            html.Label(
                                "SAT",
                                className="label__header",
                                style={"marginTop": "20px"},
                            ),
                        ],
                        className="bare-container--flex--center twelve columns",
                    )
                ]

    # K8
    if (
        school_type == "k8"
        or school_type == "k12"
        or (school_id == 5874 and year_numeric >= 2021)
    ):
        scoped_type = "k8"

        list_of_schools = [school_id]

        k8_info_data = get_academic_data(
            list_of_schools, scoped_type, year_numeric, "info"
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

            ## ILEARN
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

            years_by_grade_ela = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(grades_all))
                    & ilearn_table_data["Category"].str.contains("ELA")
                )
            ]

            ela_grade_table = create_multi_header_table(years_by_grade_ela)

            ela_grade_fig_data = ilearn_fig_data.filter(
                regex=r"^Grade \d\|ELA|^School Name$|^Year$", axis=1
            )

            ela_grade_line_fig = make_line_chart(ela_grade_fig_data)

            proficiency_grades_ela = create_line_fig_layout(
                ela_grade_table, ela_grade_line_fig, "ELA By Grade"
            )

            years_by_subgroup_ela = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(subgroup))
                    & ilearn_table_data["Category"].str.contains("ELA")
                )
            ]

            ela_subgroup_table = create_multi_header_table(years_by_subgroup_ela)

            ela_subgroup_fig_data = ilearn_fig_data.loc[
                :,
                (ilearn_fig_data.columns.isin(categories_ela_subgroup))
                | (ilearn_fig_data.columns.isin(["School Name", "Year"])),
            ]
            ela_subgroup_line_fig = make_line_chart(ela_subgroup_fig_data)

            proficiency_subgroup_ela = create_line_fig_layout(
                ela_subgroup_table, ela_subgroup_line_fig, "ELA By Subgroup"
            )

            years_by_ethnicity_ela = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(ethnicity))
                    & ilearn_table_data["Category"].str.contains("ELA")
                )
            ]

            ela_ethnicity_table = create_multi_header_table(years_by_ethnicity_ela)

            ela_ethnicity_fig_data = ilearn_fig_data.loc[
                :,
                (ilearn_fig_data.columns.isin(categories_ela_ethnicity))
                | (ilearn_fig_data.columns.isin(["School Name", "Year"])),
            ]
            ela_ethnicity_line_fig = make_line_chart(ela_ethnicity_fig_data)

            proficiency_ethnicity_ela = create_line_fig_layout(
                ela_ethnicity_table, ela_ethnicity_line_fig, "ELA By Ethnicity"
            )

            years_by_grade_math = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(grades_all))
                    & ilearn_table_data["Category"].str.contains("Math")
                )
            ]

            math_grade_table = create_multi_header_table(years_by_grade_math)

            math_grade_fig_data = ilearn_fig_data.filter(
                regex=r"^Grade \d\|Math|^School Name$|^Year$", axis=1
            )
            math_grade_line_fig = make_line_chart(math_grade_fig_data)

            proficiency_grades_math = create_line_fig_layout(
                math_grade_table, math_grade_line_fig, "Math By Grade"
            )

            years_by_subgroup_math = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(subgroup))
                    & ilearn_table_data["Category"].str.contains("Math")
                )
            ]

            math_subgroup_table = create_multi_header_table(years_by_subgroup_math)

            math_subgroup_fig_data = ilearn_fig_data.loc[
                :,
                (ilearn_fig_data.columns.isin(categories_math_subgroup))
                | (ilearn_fig_data.columns.isin(["School Name", "Year"])),
            ]
            math_subgroup_line_fig = make_line_chart(math_subgroup_fig_data)

            proficiency_subgroup_math = create_line_fig_layout(
                math_subgroup_table, math_subgroup_line_fig, "Math By Subgroup"
            )

            years_by_ethnicity_math = ilearn_table_data[
                (
                    ilearn_table_data["Category"].str.contains("|".join(ethnicity))
                    & ilearn_table_data["Category"].str.contains("Math")
                )
            ]

            math_ethnicity_table = create_multi_header_table(years_by_ethnicity_math)

            math_ethnicity_fig_data = ilearn_fig_data.loc[
                :,
                (ilearn_fig_data.columns.isin(categories_math_ethnicity))
                | (ilearn_fig_data.columns.isin(["School Name", "Year"])),
            ]
            math_ethnicity_line_fig = make_line_chart(math_ethnicity_fig_data)

            proficiency_ethnicity_math = create_line_fig_layout(
                math_ethnicity_table, math_ethnicity_line_fig, "Math By Ethnicity"
            )

            # # ILEARN Breakdown
            # raw_k8_info_data = get_proficiency_data(school_id)

            # ilearn_proficency_data = raw_k8_info_data.loc[
            #     raw_k8_info_data["Year"] == year_numeric
            # ].copy()

            # ilearn_proficency_data = ilearn_proficency_data.dropna(axis=1)
            # ilearn_proficency_data = ilearn_proficency_data.reset_index()

            # for col in ilearn_proficency_data.columns:
            #     ilearn_proficency_data[col] = pd.to_numeric(
            #         ilearn_proficency_data[col], errors="coerce"
            #     )

            # ilearn_proficency_data = ilearn_proficency_data.filter(
            #     regex=r"ELA Below|ELA At|ELA Approaching|ELA Above|ELA Total|Math Below|Math At|Math Approaching|Math Above|Math Total",
            #     axis=1,
            # )

            # proficiency_rating = [
            #     "Below Proficiency",
            #     "Approaching Proficiency",
            #     "At Proficiency",
            #     "Above Proficiency",
            # ]

            # annotations = pd.DataFrame(columns=["Category", "Total Tested"])

            # categories = grades_all + ethnicity + subgroup

            # for c in categories:
            #     for s in subject:
            #         category_subject = c + "|" + s
            #         proficiency_columns = [
            #             category_subject + " " + x for x in proficiency_rating
            #         ]
            #         total_tested = category_subject + " " + "Total Tested"

            #         if total_tested in ilearn_proficency_data.columns:
            #             if (
            #                 ilearn_proficency_data[proficiency_columns]
            #                 .isna()
            #                 .sum()
            #                 .sum()
            #                 > 0
            #             ) or (
            #                 ilearn_proficency_data[proficiency_columns].iloc[0].sum()
            #                 == 0
            #             ):
            #                 annotation_category = proficiency_columns[0].split("|")[0]
            #                 annotations.loc[len(annotations.index)] = [
            #                     annotation_category + "|" + s,
            #                     ilearn_proficency_data[total_tested].values[0],
            #                 ]

            #                 annotations["Total Tested"] = annotations[
            #                     "Total Tested"
            #                 ].fillna(0)
            #                 annotations["Total Tested"] = annotations[
            #                     "Total Tested"
            #                 ].astype(int)

            #                 all_proficiency_columns = proficiency_columns + [
            #                     total_tested
            #                 ]

            #                 ilearn_proficency_data = ilearn_proficency_data.drop(
            #                     all_proficiency_columns, axis=1
            #                 )

            #             else:
            #                 ilearn_proficency_data[
            #                     proficiency_columns
            #                 ] = ilearn_proficency_data[proficiency_columns].divide(
            #                     ilearn_proficency_data[total_tested], axis="index"
            #                 )

            #                 row_list = ilearn_proficency_data[
            #                     proficiency_columns
            #                 ].values.tolist()

            #                 rounded = round_percentages(row_list[0])

            #                 rounded_percentages = pd.DataFrame([rounded])
            #                 rounded_percentages_cols = list(rounded_percentages.columns)
            #                 ilearn_proficency_data[
            #                     proficiency_columns
            #                 ] = rounded_percentages[rounded_percentages_cols]

            # ilearn_proficency_data.drop(
            #     list(
            #         ilearn_proficency_data.filter(regex="Total Proficient|ELA and Math")
            #     ),
            #     axis=1,
            #     inplace=True,
            # )

            # ilearn_proficency_data = ilearn_proficency_data.rename(
            #     columns=lambda x: re.sub("(Grade )(\d)", "\\2th", x)
            # )

            # ilearn_proficency_data.columns = [
            #     x.replace("3th", "3rd")
            #     for x in ilearn_proficency_data.columns.to_list()
            # ]

            # ilearn_proficency_data = (
            #     ilearn_proficency_data.T.rename_axis("Category")
            #     .rename_axis(None, axis=1)
            #     .reset_index()
            # )

            # ilearn_proficency_data[
            #     ["Category", "Proficiency"]
            # ] = ilearn_proficency_data["Category"].str.split("|", expand=True)

            # ilearn_proficency_data.rename(columns={0: "Percentage"}, inplace=True)

            # ilearn_proficency_data = ilearn_proficency_data[
            #     ilearn_proficency_data["Category"] != "index"
            # ]

            # bar_fig_title = "Proficiency Breakdown (" + year_string + ")"

            # grade_pattern = "|".join(grades)

            # grade_ela_annotations = annotations.loc[
            #     annotations["Category"].str.contains(grade_pattern)
            #     & annotations["Category"].str.contains("ELA")
            # ]

            # grade_ela_fig_data = ilearn_proficency_data[
            #     ilearn_proficency_data["Category"].isin(grades_ordinal)
            #     & ilearn_proficency_data["Proficiency"].str.contains("ELA")
            # ]

            # if not grade_ela_fig_data.empty:
            #     ela_grade_bar_fig = make_stacked_bar(
            #         grade_ela_fig_data, bar_fig_title, grade_ela_annotations
            #     )
            # else:
            #     ela_grade_bar_fig = no_data_fig_label(bar_fig_title, 100)

            # grade_math_annotations = annotations.loc[
            #     annotations["Category"].str.contains(grade_pattern)
            #     & annotations["Category"].str.contains("Math")
            # ]

            # grade_math_fig_data = ilearn_proficency_data[
            #     ilearn_proficency_data["Category"].isin(grades_ordinal)
            #     & ilearn_proficency_data["Proficiency"].str.contains("Math")
            # ]

            # if not grade_math_fig_data.empty:
            #     math_grade_bar_fig = make_stacked_bar(
            #         grade_math_fig_data, bar_fig_title, grade_math_annotations
            #     )
            # else:
            #     math_grade_bar_fig = no_data_fig_label(bar_fig_title, 100)

            # eth_pattern = "|".join(ethnicity)

            # ethnicity_ela_annotations = annotations.loc[
            #     annotations["Category"].str.contains(eth_pattern)
            #     & annotations["Category"].str.contains("ELA")
            # ]

            # ethnicity_ela_fig_data = ilearn_proficency_data[
            #     ilearn_proficency_data["Category"].isin(ethnicity)
            #     & ilearn_proficency_data["Proficiency"].str.contains("ELA")
            # ]

            # if not ethnicity_ela_fig_data.empty:
            #     ela_ethnicity_bar_fig = make_stacked_bar(
            #         ethnicity_ela_fig_data, bar_fig_title, ethnicity_ela_annotations
            #     )
            # else:
            #     ela_ethnicity_bar_fig = no_data_fig_label(bar_fig_title, 100)

            # ethnicity_math_annotations = annotations.loc[
            #     annotations["Category"].str.contains(eth_pattern)
            #     & annotations["Category"].str.contains("Math")
            # ]

            # ethnicity_math_fig_data = ilearn_proficency_data[
            #     ilearn_proficency_data["Category"].isin(ethnicity)
            #     & ilearn_proficency_data["Proficiency"].str.contains("Math")
            # ]

            # if not ethnicity_math_fig_data.empty:
            #     math_ethnicity_bar_fig = make_stacked_bar(
            #         ethnicity_math_fig_data, bar_fig_title, ethnicity_math_annotations
            #     )
            # else:
            #     math_ethnicity_bar_fig = no_data_fig_label(bar_fig_title, 100)

            # sub_pattern = "|".join(subgroup)

            # subgroup_ela_annotations = annotations.loc[
            #     annotations["Category"].str.contains(sub_pattern)
            #     & annotations["Category"].str.contains("ELA")
            # ]

            # subgroup_ela_fig_data = ilearn_proficency_data[
            #     ilearn_proficency_data["Category"].isin(subgroup)
            #     & ilearn_proficency_data["Proficiency"].str.contains("ELA")
            # ]

            # if not subgroup_ela_fig_data.empty:
            #     ela_subgroup_bar_fig = make_stacked_bar(
            #         subgroup_ela_fig_data, bar_fig_title, subgroup_ela_annotations
            #     )
            # else:
            #     ela_subgroup_bar_fig = no_data_fig_label(bar_fig_title, 100)

            # math_subgroup_annotations = annotations.loc[
            #     annotations["Category"].str.contains(sub_pattern)
            #     & annotations["Category"].str.contains("Math")
            # ]

            # subgroup_math_fig_data = ilearn_proficency_data[
            #     ilearn_proficency_data["Category"].isin(subgroup)
            #     & ilearn_proficency_data["Proficiency"].str.contains("Math")
            # ]

            # if not subgroup_math_fig_data.empty:
            #     math_subgroup_bar_fig = make_stacked_bar(
            #         subgroup_math_fig_data, bar_fig_title, math_subgroup_annotations
            #     )
            # else:
            #     math_subgroup_bar_fig = no_data_fig_label(bar_fig_title, 100)

        # IREAD
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

        if not public_iread_school_data.empty:
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

    # layouts
    academicinfo_layout = [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(iread_school_level_layout),
                    ],
                ),
                html.Div(
                    [
                        html.Div(proficiency_grades_ela),
                    ],
                    className="pagebreak",
                ),
                html.Div(
                    [
                        html.Div(proficiency_ethnicity_ela),
                    ],
                ),
                html.Div(
                    [
                        html.Div(proficiency_subgroup_ela),
                    ],
                ),
                html.Div(
                    [
                        html.Div(proficiency_grades_math),
                    ],
                ),
                html.Div(
                    [
                        html.Div(proficiency_ethnicity_math),
                    ],
                ),
                html.Div(
                    [
                        html.Div(proficiency_subgroup_math),
                    ]
                ),
            ]
        )
    ]

    academicinfo_hs_layout = [
        html.Div(
            [
                html.Div(
                    [
                        # html.Div(
                        #     [
                        #         html.Label(
                        #             "Graduation Rate",
                        #             className="label__header",
                        #             style={"marginTop": "20px"},
                        #         ),
                        #     ],
                        #     className="bare-container--flex--center twelve columns",
                        # ),
                        html.Div(grad_label),
                        html.Div(hs_grad_overview_table),
                        html.Div(hs_grad_ethnicity_table),
                        html.Div(hs_grad_subgroup_table),
                    ],
                ),
                html.Div(
                    [
                        # html.Div(
                        #     [
                        #         html.Label(
                        #             "SAT",
                        #             className="label__header",
                        #             style={"marginTop": "20px"},
                        #         ),
                        #     ],
                        #     className="bare-container--flex--center twelve columns",
                        # ),
                        html.Div(sat_label),
                        html.Div(hs_sat_overview_table),
                        html.Div(hs_sat_ethnicity_table),
                        html.Div(hs_sat_subgroup_table),
                    ]
                ),
            ]
        )
    ]

    if school_type == "hs" or school_type == "ahs":
        return academicinfo_hs_layout

    elif school_type == "k8":
        return academicinfo_layout

    else:  # K12
        merged_layout = academicinfo_layout + academicinfo_hs_layout

        return merged_layout


def create_academicmetrics_layout(year: str, school_id: str) -> list:
    selected_year_string = year
    selected_year_numeric = int(selected_year_string)

    # default values
    table_container_11ab = []
    table_container_11cd = []
    table_container_14ab = []
    table_container_14cd = []
    table_container_14ef = []
    table_container_14g = []
    table_container_16ab = []
    table_container_16cd = []

    table_container_17ab = []
    table_container_17cd = []

    ahs_table_container_113 = []
    ahs_table_container_1214 = []

    # no_data_to_display = no_data_page("No Data to Display.", "Academic Metrics")

    selected_school = get_school_index(school_id)
    selected_school_type = selected_school["School Type"].values[0]
    selected_school_id = int(selected_school["School ID"].values[0])

    # split K12 school exception (CHS)
    if selected_school_id == 5874 and selected_year_numeric < 2021:
        selected_school_type = "k12"

    # K8 Academic Metrics (for K8 and K12 schools)
    if selected_school_type == "k8" or selected_school_type == "k12":
        list_of_schools = [school_id]
        if selected_school_type == "k12":
            school_type = "k8"
        else:
            school_type = selected_school_type

        metric_data = get_academic_data(
            list_of_schools, school_type, selected_year_numeric, "metrics"
        )

        if len(metric_data.index) > 0:
            metric_data = metric_data.replace({"^": "***"})

            k8_year_values, k8_comparison_values = calculate_values(
                metric_data, selected_year_string
            )

            # Get Year over Year and Combined Metrics
            combined_years, combined_delta = calculate_metrics(
                k8_year_values, k8_comparison_values
            )

            category = ethnicity + subgroup

            metric_14a_data = combined_years[
                (combined_years["Category"].str.contains("|".join(grades_all)))
                & (combined_years["Category"].str.contains("ELA"))
            ]
            metric_14a_label = [
                "1.4.a Grade level proficiency on the state assessment in",
                html.Br(),
                html.U("English Language Arts"),
                " compared with the previous school year.",
            ]

            metric_14a_data = convert_to_svg_circle(metric_14a_data)
            table_14a = create_metric_table(metric_14a_label, metric_14a_data)

            metric_14b_data = combined_years[
                (combined_years["Category"].str.contains("|".join(grades_all)))
                & (combined_years["Category"].str.contains("Math"))
            ]
            metric_14b_label = [
                "1.4.b Grade level proficiency on the state assessment in",
                html.Br(),
                html.U("Math"),
                " compared with the previous school year.",
            ]

            metric_14b_data = convert_to_svg_circle(metric_14b_data)
            table_14b = create_metric_table(metric_14b_label, metric_14b_data)

            table_container_14ab = set_table_layout(
                table_14a, table_14b, combined_years.columns
            )

            metric_14c_data = combined_delta[
                (combined_delta["Category"].str.contains("|".join(grades_all)))
                & (combined_delta["Category"].str.contains("ELA"))
            ]
            metric_14c_label = [
                "1.4.c Grade level proficiency on the state assessment in",
                html.Br(),
                html.U("English Language Arts"),
                " compared with traditional school corporation.",
            ]

            metric_14c_data = convert_to_svg_circle(metric_14c_data)
            table_14c = create_metric_table(metric_14c_label, metric_14c_data)

            metric_14d_data = combined_delta[
                (combined_delta["Category"].str.contains("|".join(grades_all)))
                & (combined_delta["Category"].str.contains("Math"))
            ]
            metric_14d_label = [
                "1.4.d Grade level proficiency on the state assessment in",
                html.Br(),
                html.U("Math"),
                " compared with traditional school corporation.",
            ]

            metric_14d_data = convert_to_svg_circle(metric_14d_data)
            table_14d = create_metric_table(metric_14d_label, metric_14d_data)

            table_container_14cd = set_table_layout(
                table_14c, table_14d, combined_delta.columns
            )

            # Accountability Metrics 1.4.e & 1.4.f (Placeholder)
            all_cols = combined_years.columns.tolist()

            simple_cols = [x for x in all_cols if "School" in x or "N-Size" in x]
            simple_cols = ["Category"] + simple_cols

            year_proficiency_empty = pd.DataFrame(columns=simple_cols)

            year_proficiency_dict = {
                "Category": [
                    "1.4.e Two year student proficiency in ELA.",
                    "1.4.f Two year student proficiency in Math.",
                ]
            }
            year_proficiency = pd.DataFrame(year_proficiency_dict)

            metric_14ef_data = pd.concat(
                [year_proficiency_empty, year_proficiency], ignore_index=True
            )
            metric_14ef_data.reset_index()
            metric_14ef_data = conditional_fillna(metric_14ef_data)
            metric_14ef_label = [
                "Percentage of students enrolled for at least two school years achieving proficiency on the state assessment in English Language Arts (1.4.e) and Math (1.4.f)"
            ]
            table_14ef = create_metric_table(metric_14ef_label, metric_14ef_data)
            table_container_14ef = set_table_layout(
                table_14ef, table_14ef, metric_14ef_data.columns
            )

            # iread_data - combined_delta has all IREAD data, but we
            # currently only use Total
            iread_data = combined_delta[
                combined_delta["Category"] == "Total|IREAD Proficient %"
            ].copy()

            if len(iread_data.index) > 0:
                iread_data.loc[
                    iread_data["Category"] == "IREAD", "Category"
                ] = "IREAD Proficient %"

                iread_data = iread_data.reset_index(drop=True)
                iread_data = calculate_iread_metrics(iread_data)

                metric_14g_label = [
                    "1.4.g Percentage of students achieving proficiency on the IREAD-3 state assessment."
                ]
                iread_data = convert_to_svg_circle(iread_data)
                table_14g = create_metric_table(metric_14g_label, iread_data)
                table_container_14g = set_table_layout(
                    table_14g, table_14g, iread_data.columns
                )

            else:
                # create_metric_table requies label to be a list, while no_data_table wants a string
                empty_table_14g = no_data_table(
                    "No Data to Display.",
                    "1.4.g Percentage of students achieving proficiency on the IREAD-3 state assessment.",
                    "six",
                )
                table_container_14g = set_table_layout(
                    empty_table_14g, empty_table_14g, [""]
                )

            metric_16a_data = combined_delta[
                (combined_delta["Category"].str.contains("|".join(category)))
                & (combined_delta["Category"].str.contains("ELA"))
            ]
            metric_16a_label = [
                "1.6.a Proficiency on the state assessment in ",
                html.U("English Language Arts"),
                html.Br(),
                "for each subgroup compared with traditional school corporation.",
            ]
            metric_16a_data = convert_to_svg_circle(metric_16a_data)
            table_16a = create_metric_table(metric_16a_label, metric_16a_data)

            metric_16b_data = combined_delta[
                (combined_delta["Category"].str.contains("|".join(category)))
                & (combined_delta["Category"].str.contains("Math"))
            ]
            metric_16b_label = [
                "1.6.b Proficiency on the state assessment in ",
                html.U("Math"),
                " for each",
                html.Br(),
                "subgroup compared with traditional school corporation.",
            ]
            metric_16b_data = convert_to_svg_circle(metric_16b_data)

            table_16b = create_metric_table(metric_16b_label, metric_16b_data)

            table_container_16ab = set_table_layout(
                table_16a, table_16b, combined_delta.columns
            )

            metric_16c_data = combined_years[
                (combined_years["Category"].str.contains("|".join(category)))
                & (combined_years["Category"].str.contains("ELA"))
            ]
            metric_16c_label = [
                "1.6.c The change in proficiency on the state assessment in",
                html.Br(),
                html.U("English Language Arts"),
                " for each subgroup compared with the previous school year.",
            ]
            metric_16c_data = convert_to_svg_circle(metric_16c_data)
            table_16c = create_metric_table(metric_16c_label, metric_16c_data)

            metric_16d_data = combined_years[
                (combined_years["Category"].str.contains("|".join(category)))
                & (combined_years["Category"].str.contains("Math"))
            ]
            metric_16d_label = [
                "1.6.d The change in proficiency on the state assessment in",
                html.Br(),
                html.U("Math"),
                " for each subgroup compared with the previous school year.",
            ]
            metric_16d_data = convert_to_svg_circle(metric_16d_data)
            table_16d = create_metric_table(metric_16d_label, metric_16d_data)

            table_container_16cd = set_table_layout(
                table_16c, table_16d, combined_years.columns
            )

    if (
        selected_school_type == "hs"
        or selected_school_type == "ahs"
        or selected_school_type == "k12"
    ):
        if selected_school_type == "k12":
            selected_school_type = "hs"

        list_of_schools = [school_id]

        raw_metric_data = get_academic_data(
            list_of_schools, selected_school_type, selected_year_numeric, "metrics"
        )

        if len(raw_metric_data.index) > 0:
            # Adult High School Metrics
            if selected_school_type == "ahs":
                ahs_metric_data_113 = calculate_adult_high_school_metrics(
                    raw_metric_data
                )

                ahs_metric_data_113["Category"] = (
                    ahs_metric_data_113["Metric"]
                    + " "
                    + ahs_metric_data_113["Category"]
                )

                ahs_metric_data_113 = ahs_metric_data_113.drop("Metric", axis=1)

                ahs_metric_label_113 = ["Adult High School Accountability Metrics"]
                ahs_metric_data_113 = convert_to_svg_circle(ahs_metric_data_113)
                ahs_table_113 = create_metric_table(
                    ahs_metric_label_113, ahs_metric_data_113
                )
                ahs_table_container_113 = set_table_layout(
                    ahs_table_113, ahs_table_113, ahs_metric_data_113.columns
                )

                # # Create placeholders (Adult Accountability Metrics 1.2.a, 1.2.b, 1.4.a, & 1.4.b)
                # all_cols = ahs_metric_data_113.columns.tolist()
                # simple_cols = [x for x in all_cols if not x.endswith("+/-")]

                # ahs_nocalc_empty = pd.DataFrame(columns=simple_cols)

                # ahs_nocalc_dict = {
                #     "Category": [
                #         "1.2.a Students graduate from high school in 4 years.",
                #         "1.2.b Students enrolled in grade 12 graduate within the school year being assessed.",
                #     ]
                # }
                # ahs_no_calc = pd.DataFrame(ahs_nocalc_dict)

                # ahs_metric_data_1214 = pd.concat(
                #     [ahs_nocalc_empty, ahs_no_calc], ignore_index=True
                # )
                # ahs_metric_data_1214.reset_index()

                # # fill only value columns with "No Data" (until we actually HAVE the data)
                # empty_year_cols = [
                #     col for col in ahs_metric_data_1214.columns if "Value" in col
                # ]
                # for col in empty_year_cols:
                #     ahs_metric_data_1214[col] = "No Data"

                # ahs_metric_label_1214 = ["Adult Accountability Metrics 1.2.a & 1.2.b"]
                # ahs_metric_data_1214 = convert_to_svg_circle(ahs_metric_data_1214)
                # ahs_table_1214 = create_metric_table(
                #     ahs_metric_label_1214, ahs_metric_data_1214
                # )
                # ahs_table_container_1214 = set_table_layout(
                #     ahs_table_1214, ahs_table_1214, ahs_metric_data_1214.columns
                # )

            else:
                # NOTE: We do not currently use hs_year_over_year_values
                # for hs metrics
                hs_year_over_year_values, hs_comparison_values = calculate_values(
                    raw_metric_data, selected_year_string
                )

                if not hs_comparison_values.empty:
                    hs_metric_data = calculate_high_school_metrics(hs_comparison_values)

                    metric_17ab_label = [
                        "High School Accountability Metrics 1.7.a & 1.7.b"
                    ]
                    hs_metric_data = convert_to_svg_circle(hs_metric_data)
                    table_17ab = create_metric_table(metric_17ab_label, hs_metric_data)
                    table_container_17ab = set_table_layout(
                        table_17ab, table_17ab, hs_metric_data.columns
                    )

                    # Create placeholders (High School Accountability Metrics 1.7.c & 1.7.d)
                    all_cols = hs_metric_data.columns.tolist()

                    simple_cols = [
                        x
                        for x in all_cols
                        if (
                            not x.endswith("+/-") and not x.endswith("Diff")
                        )  # Difference
                    ]

                    grad_metrics_empty = pd.DataFrame(columns=simple_cols)

                    grad_metrics_dict = {
                        "Category": [
                            "1.7.c The percentage of students entering Grade 12 at beginning of year who graduated",
                            # "1.7.d. The percentage of graduating students planning to pursue college or career."
                        ]
                    }
                    grad_metrics = pd.DataFrame(grad_metrics_dict)

                    metric_17cd_data = pd.concat(
                        [grad_metrics_empty, grad_metrics], ignore_index=True
                    )
                    metric_17cd_data.reset_index()

                    # fill only value columns with "No Data" (until we actually HAVE the data)
                    empty_year_cols = [
                        col for col in metric_17cd_data.columns if "%" in col
                    ]
                    for col in empty_year_cols:
                        metric_17cd_data[col] = "No Data"

                    metric_17cd_data = conditional_fillna(metric_17cd_data)

                    metric_17cd_label = [
                        "High School Accountability Metrics 1.7.c & 1.7.d"
                    ]
                    metric_17cd_data = convert_to_svg_circle(metric_17cd_data)
                    table_17cd = create_metric_table(
                        metric_17cd_label, metric_17cd_data
                    )
                    table_container_17cd = set_table_layout(
                        table_17cd, table_17cd, metric_17cd_data.columns
                    )

    # Attendance Data & Teacher Retention Rate (all schools have this data)
    metric_11ab_label = [
        "Student Attendance Rate (1.1.a) and Teacher Retention Rate (1.1.b) compared with traditional school corporation."
    ]

    # Re-enrollment Rates (Acountability Metrics 1.1.c & 1.1.d): Currently Placeholders
    metric_11cd_label = [
        "End of Year to Beginning of Year (1.1.c) and Year over Year (1.1.d) Student Re-Enrollment Rate."
    ]

    attendance_data = calculate_attendance_metrics(
        school_id, selected_school_type, selected_year_string
    )

    if len(attendance_data.index) > 0:
        # attendance_container = {"display": "block"}

        # Create placeholders (Acountability Metric 1.1.b.)
        teacher_retention_rate = pd.DataFrame(
            {"Category": ["1.1.b Teacher Retention Rate"]}
        )

        metric_11ab_data = pd.merge(
            attendance_data, teacher_retention_rate, how="outer", on="Category"
        )

        metric_11ab_data = conditional_fillna(metric_11ab_data)

        metric_11ab_data = convert_to_svg_circle(metric_11ab_data)
        table_11ab = create_metric_table(metric_11ab_label, metric_11ab_data)
        table_container_11ab = set_table_layout(
            table_11ab, table_11ab, metric_11ab_data.columns
        )

        # Create placeholders (Acountability Metric 1.1.c.)
        student_retention_rate_dict = {
            "Category": [
                "1.1.c End of Year to Beginning of Year Re-Enrollment Rate",
                "1.1.d Year over Year Re-Enrollment Rate",
            ]
        }

        mock_columns = [i for i in attendance_data.columns if "Corp Avg" not in i]

        # Only add placeholder if there is attendance data
        student_retention_empty = pd.DataFrame(columns=mock_columns)
        student_retention_rate = pd.DataFrame(student_retention_rate_dict)

        metric_11cd_data = pd.concat(
            [student_retention_empty, student_retention_rate], ignore_index=True
        )
        metric_11cd_data.reset_index()

        metric_11cd_data = conditional_fillna(metric_11cd_data)

        metric_11cd_data = convert_to_svg_circle(metric_11cd_data)
        table_11cd = create_metric_table(metric_11cd_label, metric_11cd_data)
        table_container_11cd = set_table_layout(
            table_11cd, table_11cd, metric_11cd_data.columns
        )

    else:
        empty_table_11ab = no_data_table(
            "No Data to Display.",
            "Student Attendance Rate (1.1.a) and Teacher Retention Rate (1.1.b) compared with traditional school corporation.",
            "six",
        )

        table_container_11ab = set_table_layout(
            empty_table_11ab, empty_table_11ab, [""]
        )

        empty_table_11cd = no_data_table(
            "No Data to Display.",
            "End of Year to Beginning of Year (1.1.c) and Year over Year (1.1.d) Student Re-Enrollment Rate.",
        )

        table_container_11cd = set_table_layout(
            empty_table_11cd, empty_table_11cd, [""]
        )

    academicmetrics_layout = [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Key", className="label__header"),
                                html.Div(create_proficiency_key()),
                            ],
                            className="pretty-container six columns",
                        ),
                    ],
                    className="bare-container--flex--center twelve columns pagebreak",
                ),
                html.Div(
                    [
                        html.Div(table_container_11ab),
                    ],
                ),
                html.Div(
                    [
                        html.Div(table_container_11cd),
                        html.Div(table_container_14ab),
                        html.Div(table_container_14cd),
                        html.Div(table_container_14ef),
                        html.Div(table_container_14g),
                        html.Div(table_container_16cd),
                        html.Div(table_container_16ab),
                    ],
                ),
                html.Div(
                    [
                        html.Div(table_container_17ab),
                        html.Div(table_container_17cd),
                    ],
                ),
                html.Div(
                    [
                        html.Div(ahs_table_container_113),
                        html.Div(ahs_table_container_1214),
                    ],
                ),
            ],
        )
    ]

    return academicmetrics_layout


def create_fininfo_layout(year: str, school_id: str) -> list:
    year_string = year
    year_numeric = int(year_string)
    selected_school = get_school_index(school_id)

    # If the selected school is a guest school, load dummy data
    if selected_school["Guest"].values[0] == "Y":
        school_id = "9999"

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

    finmetrics_layout = []
    financial_indicators_table = []
    financial_metrics_table = []

    table_title = "Financial Accountability Metrics"

    financial_data = get_financial_data(school_id)

    # Financial Metrics
    if len(financial_data.columns) > 1 or not financial_data.empty:
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
            if len(financial_indicators.columns) > 1 or not financial_indicators.empty:
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

    if len(financial_data.columns) > 1 or not financial_data.empty:
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
                                html.Div(financial_ratios_table),
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
            ]
        )
    ]

    return finanalysis_layout


def create_orgcompliance_layout(year: str, school_id: str) -> list:
    selected_school = get_school_index(school_id)
    year_numeric = int(year)

    orgcompliance_layout = []

    if selected_school["Guest"].values[0] == "Y":
        school_id = "9999"

    financial_data = get_financial_data(school_id)

    if len(financial_data.columns) > 1 or not financial_data.empty:
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
                )
            ]

    return orgcompliance_layout
