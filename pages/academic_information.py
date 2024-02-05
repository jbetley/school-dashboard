#######################################################
# ICSB Dashboard - Academic Information - Proficiency #
#######################################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.14
# date:     02/04/24

import dash
from dash import dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import numpy as np
import pandas as pd
from functools import reduce
import re
import itertools

# import local functions
from pages.load_data import (
    ethnicity,
    subgroup,
    subject,
    grades_all,
    grades,
    grades_ordinal,
    get_ilearn_stns,
    get_iread_student_data,
    get_wida_student_data,
    get_ilearn_student_data,
    get_k8_school_academic_data,
    get_high_school_academic_data,
    get_school_index,
    get_excluded_years,
    get_attendance_data
)
from pages.process_data import (
    process_k8_academic_data,
    process_high_school_academic_data,
    filter_high_school_academic_data,
)
from pages.tables import (
    no_data_page,
    no_data_table,
    create_multi_header_table_with_container,
    create_key_table,
    create_single_header_table,
    create_multi_header_table,
)
from pages.charts import no_data_fig_label, make_stacked_bar, make_line_chart
from pages.layouts import set_table_layout, create_line_fig_layout
from pages.calculations import round_percentages
from pages.string_helpers import natural_keys

dash.register_page(
    __name__,
    top_nav=True,
    name="Academic Information",
    path="/academic_information",
    order=7,
)


# Main
@callback(
    Output("iread-breakdown", "children"),
    Output("iread-breakdown-container", "style"),
    Output("wida-breakdown", "children"),
    Output("wida-breakdown-container", "style"),    
    Output("proficiency-grades-ela", "children"),
    Output("ela-grade-bar-fig", "children"),
    Output("proficiency-ela-grades-container", "style"),
    Output("proficiency-ethnicity-ela", "children"),
    Output("ela-ethnicity-bar-fig", "children"),
    Output("proficiency-ela-ethnicity-container", "style"),
    Output("proficiency-subgroup-ela", "children"),
    Output("ela-subgroup-bar-fig", "children"),
    Output("proficiency-ela-subgroup-container", "style"),
    Output("proficiency-grades-math", "children"),
    Output("math-grade-bar-fig", "children"),
    Output("proficiency-math-grades-container", "style"),
    Output("proficiency-ethnicity-math", "children"),
    Output("math-ethnicity-bar-fig", "children"),
    Output("proficiency-math-ethnicity-container", "style"),
    Output("proficiency-subgroup-math", "children"),
    Output("math-subgroup-bar-fig", "children"),
    Output("proficiency-math-subgroup-container", "style"),
    Output("attendance-table-k8", "children"),
    Output("attendance-table-hs", "children"),
    Output("k8-table-container", "style"),
    Output("k12-grad-overview-table", "children"),
    Output("k12-grad-ethnicity-table", "children"),
    Output("k12-grad-subgroup-table", "children"),
    Output("k12-grad-table-container", "style"),
    Output("k12-sat-cut-scores-table", "children"),
    Output("k12-sat-overview-table", "children"),
    Output("k12-sat-ethnicity-table", "children"),
    Output("k12-sat-subgroup-table", "children"),
    Output("k12-sat-table-container", "style"),
    Output("academic-information-main-container", "style"),
    Output("academic-information-empty-container", "style"),
    Output("academic-information-no-data", "children"),
    Output("academic-information-notes-string", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("academic-information-type-radio", "value"),
    Input("academic-information-category-radio", "value"),
)
def update_academic_information_page(
    school: str, year: str, radio_type: str, radio_category: str
):
    if not school:
        raise PreventUpdate
        
    selected_year_string = year
    selected_year_numeric = int(selected_year_string)

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]
    selected_school_id = int(selected_school["School ID"].values[0])
    selected_school_name = selected_school["School Name"].values[0]
    selected_school_name = selected_school_name.strip()

    if not radio_type:
        radio_type = "k8"

    if not radio_category:
        radio_category = "all"

    # default styles - start with all values empty
    # and only empty_container displayed)
    k12_grad_overview_table = []
    k12_grad_ethnicity_table = []
    k12_grad_subgroup_table = []
    k12_sat_overview_table = []
    k12_sat_ethnicity_table = []
    k12_sat_subgroup_table = []
    k12_sat_cut_scores_table = []
    k12_sat_table_container = {"display": "none"}
    k12_grad_table_container = {"display": "none"}

    iread_breakdown = []  # type: list
    wida_breakdown = []  # type: list
    proficiency_grades_ela = []
    ela_grade_bar_fig = []
    proficiency_ethnicity_ela = []
    ela_ethnicity_bar_fig = []
    proficiency_subgroup_ela = []
    ela_subgroup_bar_fig = []
    proficiency_grades_math = []
    math_grade_bar_fig = []
    proficiency_ethnicity_math = []
    math_ethnicity_bar_fig = []
    proficiency_subgroup_math = []
    math_subgroup_bar_fig = []
    wida_breakdown_container = {"display": "none"}
    iread_breakdown_container = {"display": "none"}
    proficiency_ela_grades_container = {"display": "none"}
    proficiency_ela_ethnicity_container = {"display": "none"}
    proficiency_ela_subgroup_container = {"display": "none"}
    proficiency_math_grades_container = {"display": "none"}
    proficiency_math_ethnicity_container = {"display": "none"}
    proficiency_math_subgroup_container = {"display": "none"}

    attendance_table_k8 = []      # type: list
    attendance_table_hs = []
    k8_table_container = {"display": "none"}

    academic_information_notes_string = ""
    main_container = {"display": "none"}
    empty_container = {"display": "block"}

    no_display_data = no_data_page("No Data to Display.", "Academic Proficiency")

    # HS and AHS do not have proficiency data

    if (
        selected_school_type == "HS"
        or selected_school_type == "AHS"
        or (selected_school_id == 5874 and selected_year_numeric < 2021)
        or selected_school_type == "K12"
        and radio_type == "hs"
    ):
        # load HS academic data
        selected_raw_hs_school_data = get_high_school_academic_data(school)

        excluded_years = get_excluded_years(selected_year_string)

        # exclude years later than the selected year
        if excluded_years:
            selected_raw_hs_school_data = selected_raw_hs_school_data[
                ~selected_raw_hs_school_data["Year"].isin(excluded_years)
            ]

        if len(selected_raw_hs_school_data.index) > 0:
            selected_raw_hs_school_data = filter_high_school_academic_data(
                selected_raw_hs_school_data
            )

            all_hs_school_data = process_high_school_academic_data(
                selected_raw_hs_school_data, school
            )

            if not all_hs_school_data.empty:
                main_container = {"display": "block"}
                empty_container = {"display": "none"}

                # Graduation Rate Tables ("Strength of Diploma" is in data,
                # but not currently displayed)
                grad_overview_categories = ["Total", "Non Waiver", "State Average"]

                if selected_school_type == "AHS":
                    grad_overview_categories.append("CCR Percentage")

                all_hs_school_data.columns = all_hs_school_data.columns.astype(str)

                # Graduation Rate Tables
                graduation_data = all_hs_school_data[
                    all_hs_school_data["Category"].str.contains("Graduation")
                ].copy()

                if len(graduation_data.columns) > 1 and len(graduation_data.index) > 0:
                    k12_grad_table_container = {"display": "block"}

                    graduation_data["Category"] = (
                        graduation_data["Category"]
                        .str.replace("Graduation Rate", "")
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
                k12_sat_table_data = all_hs_school_data[
                    all_hs_school_data["Category"].str.contains("Benchmark %")
                ].copy()

                if (
                    len(k12_sat_table_data.columns) > 1
                    and len(k12_sat_table_data.index) > 0
                ):
                    k12_sat_table_container = {"display": "block"}

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

                    # SAT Cut-Score Table
                    # https://www.in.gov/sboe/files/2021-2022-k12-sat-Standard-Setting-SBOE-Review.pdf
                    k12_sat_cut_scores_label = "SAT Proficiency Cut Scores (2021 - 22)"
                    k12_sat_cut_scores_dict = {
                        "Content Area": [
                            "Mathematics",
                            "Evidenced-Based Reading and Writing",
                        ],
                        "Below College-Ready Benchmark": ["200 - 450", "200 - 440"],
                        "Approaching College-Ready Benchmark": [
                            "460 - 520",
                            "450 - 470",
                        ],
                        "At College-Ready Benchmark": ["530 - 800", "480 - 800"],
                    }

                    k12_sat_cut_scores = pd.DataFrame(k12_sat_cut_scores_dict)
                    k12_sat_cut_scores_table = create_key_table(
                        k12_sat_cut_scores, k12_sat_cut_scores_label
                    )

                ## Attendance Rate & Chronic Absenteeism
                attendance_rate = get_attendance_data(
                    selected_school_id, selected_school_type, selected_year_string
                )

                if len(attendance_rate.index) > 0 and len(attendance_rate.columns) > 1:

                    attendance_table = create_single_header_table(
                        attendance_rate, "Attendance Data"
                    )
                else:
                    attendance_table = no_data_table(
                        "No Data to Display.", "Attendance Data", "six"
                    )

                attendance_table_hs = set_table_layout(
                    attendance_table, attendance_table, attendance_rate.columns
                )

                academic_information_notes_string = "Beginning with the 2021-22 SY, SAT replaced ISTEP+ as the state mandated HS assessment. \
                    Beginning with the 2023 cohort, all students in grade 11 are required to take the SAT per federal requirements."
    # End HS block
    
    elif (
        selected_school_type == "K8"
        or selected_school_type == "K12"
        or (selected_school_id == 5874 and selected_year_numeric >= 2021)
    ) and radio_type == "k8":
        
        selected_raw_k8_school_data = get_k8_school_academic_data(school)

        # remove years of data greater than the selected year
        excluded_years = get_excluded_years(selected_year_string)

        if excluded_years:
            selected_raw_k8_school_data = selected_raw_k8_school_data[
                ~selected_raw_k8_school_data["Year"].isin(excluded_years)
            ]

        # NOTE: There was no academic data available in 2020
        if (
            len(selected_raw_k8_school_data.index) > 0
            and selected_year_string != "2020"
        ):
            
            # this gives us proficiency and N-Size data for ILEARN and IREAD
            # with column names = ["2019School", "2019N-Size", . . . ] -
            # use N-Size data for table tooltips
            ilearn_table_data = process_k8_academic_data(selected_raw_k8_school_data)

            if not ilearn_table_data.empty:                
                k8_table_container = {"display": "block"}
                main_container = {"display": "block"}
                empty_container = {"display": "none"}

                ilearn_table_data["Category"] = (
                    ilearn_table_data["Category"]
                    .str.replace(" Proficient %", "")
                    .str.strip()
                )

                # Reformat data for multi-year line charts
                # Remove N-Size cols, strip suffix from years, and
                # transpose dataframe so categories become column names
                ilearn_fig_data = ilearn_table_data.loc[
                    :, ~ilearn_table_data.columns.str.contains("N-Size")
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
                ilearn_fig_data["School Name"] = selected_school_name

            ## ILEARN Charts and Tables
                # NOTE: We use all_k8_school data for tables because we
                # need N-Size values. Use 
                # get column lists for each subject/category combination
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
                        ilearn_table_data["Category"].str.contains(
                            "|".join(grades_all)
                        )
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
                        ilearn_table_data["Category"].str.contains(
                            "|".join(grades_all)
                        )
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

                math_ethnicity_table = create_multi_header_table(
                    years_by_ethnicity_math
                )

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
                ilearn_proficency_data = selected_raw_k8_school_data.loc[
                    selected_raw_k8_school_data["Year"] == selected_year_numeric
                ].copy()

                ilearn_proficency_data = ilearn_proficency_data.dropna(axis=1)
                ilearn_proficency_data = ilearn_proficency_data.reset_index()

                for col in ilearn_proficency_data.columns:
                    ilearn_proficency_data[col] = pd.to_numeric(
                        ilearn_proficency_data[col], errors="coerce"
                    )

                # this keeps ELA and Math as well, which we drop later
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

                # create dataframe to hold fig annotations
                annotations = pd.DataFrame(
                    columns=["Category", "Total Tested"]
                )

                categories = grades_all + ethnicity + subgroup

                for c in categories:
                    for s in subject:
                        category_subject = c + "|" + s
                        proficiency_columns = [
                            category_subject + " " + x for x in proficiency_rating
                        ]
                        total_tested = category_subject + " " + "Total Tested"

                        # We do not want categories that do not appear in the dataframe to appear
                        # in a chart. However, we also do not want to lose sight of critical data
                        # because of the way that IDOE determines insufficient N-Size. There are
                        # three possible data configurations for each column:
                        # 1) Total Tested > 0 and the sum of proficiency_rating(s) is > 0: the school
                        #    has tested category and there is publicly available data [display]
                        # 2) Total Tested AND sum of proficiency_rating(s) == 0: the school does not
                        #    have data for the tested category [do not display, but 'may' want
                        #    annotation as "Missing"]
                        # 3) Total Tested > 0 and the sum of proficiency_rating(s) are == "NaN": the
                        #    school has tested category but there is no publicly available data
                        #    [do not display, but 'may' want annotation as "Insufficient N-size"

                        # Neither (2) or (3) permit the creation of a valid or meaningful chart.
                        # However, we do want to track which Category/Subject combinations meet
                        # either condition (for figure annotation purposes).

                        if total_tested in ilearn_proficency_data.columns:
                            # The following is true if: 1) there are any NaN values in the set
                            # (one or more '***) or 2) the sum of all values is equal to 0 (no
                            # data) or 0.0 (NaN's converted from '***' meaning insufficient data)
                            # Can tell whether the annotation reflects insufficient n-size or
                            # missing data by the value in Total Tested (will be 0 for missing)
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
                                # add the category and value of Total Tested to a df
                                annotation_category = proficiency_columns[0].split("|")[0]
                                annotations.loc[len(annotations.index)] = [
                                    annotation_category + "|" + s,
                                    ilearn_proficency_data[total_tested].values[0]
                                ]

                                # drop any columns in the (non-chartable) category from the df
                                all_proficiency_columns = proficiency_columns + [
                                    total_tested
                                ]

                                ilearn_proficency_data = ilearn_proficency_data.drop(
                                    all_proficiency_columns, axis=1
                                )

                            else:
                                # calculate percentage
                                ilearn_proficency_data[
                                    proficiency_columns
                                ] = ilearn_proficency_data[proficiency_columns].divide(
                                    ilearn_proficency_data[total_tested], axis="index"
                                )

                                # get a list of all values
                                row_list = ilearn_proficency_data[
                                    proficiency_columns
                                ].values.tolist()

                                # round percentages using Largest Remainder Method
                                # to build the 100% stacked bar chart
                                rounded = round_percentages(row_list[0])

                                # add back to dataframe
                                rounded_percentages = pd.DataFrame([rounded])
                                rounded_percentages_cols = list(
                                    rounded_percentages.columns
                                )
                                ilearn_proficency_data[
                                    proficiency_columns
                                ] = rounded_percentages[rounded_percentages_cols]

                ilearn_proficency_data.drop(
                    list(
                        ilearn_proficency_data.filter(
                            regex="Total Proficient|ELA and Math"
                        )
                    ),
                    axis=1,
                    inplace=True,
                )

                # Replace Grade X with ordinal number (e.g., Grade 4 = 4th)
                ilearn_proficency_data = ilearn_proficency_data.rename(
                    columns=lambda x: re.sub("(Grade )(\d)", "\\2th", x)
                )

                # all use "th" suffix except for 3rd - so we need to specially treat "3""
                ilearn_proficency_data.columns = [
                    x.replace("3th", "3rd")
                    for x in ilearn_proficency_data.columns.to_list()
                ]

                ilearn_proficency_data = (
                    ilearn_proficency_data.T.rename_axis("Category")
                    .rename_axis(None, axis=1)
                    .reset_index()
                )

                # split Grade column into two columns and rename what used to be the index
                ilearn_proficency_data[
                    ["Category", "Proficiency"]
                ] = ilearn_proficency_data["Category"].str.split("|", expand=True)

                ilearn_proficency_data.rename(columns={0: "Percentage"}, inplace=True)

                ilearn_proficency_data = ilearn_proficency_data[
                    ilearn_proficency_data["Category"] != "index"
                ]

                bar_fig_title = "Proficiency Breakdown (" + selected_year_string + ")"

                # Proficiency Breakdown - ELA by Grade - Current Year
                grade_pattern = '|'.join(grades)

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
                eth_pattern = '|'.join(ethnicity)

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
                sub_pattern = '|'.join(subgroup)

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

        # End ILEARN block                  
        
        ## IREAD School and Student Level Data

        # get IREAD total students tested (school level data)
        # from public ILEARN data table
        iread_school_total = ilearn_table_data[
            ilearn_table_data["Category"] == "Total|IREAD"
        ]

        if not iread_school_total.empty:                
            k8_table_container = {"display": "block"}
            main_container = {"display": "block"}
            empty_container = {"display": "none"}

            iread_school_total_data = iread_school_total.filter(
                regex=r"School", axis=1
            ).reset_index(drop=True)

            total_iread_data = iread_school_total_data.T.rename_axis(
                "Year"
            ).reset_index()

            total_iread_data = total_iread_data.rename(columns={0: "Total|IREAD"})
            total_iread_data["Year"] = total_iread_data["Year"].str[:4]

            iread_school_total_tested = iread_school_total.filter(
                regex=r"N-Size", axis=1
            ).reset_index(drop=True)

            total_iread_tested = iread_school_total_tested.T.rename_axis(
                "Year"
            ).reset_index()

            total_iread_tested = total_iread_tested.rename(columns={0: "N-Size"})
            total_iread_tested["Year"] = total_iread_tested["Year"].str[:4]

            # get raw student IREAD data
            iread_student_data = get_iread_student_data(school)

            # If school has no student level data (or is a Guest school), we replace
            # student level chart and table with a basic school level chart and table
            if len(iread_student_data.index) < 1:
                # if school has no iread data (e.g., a MS), then all values in the IREAD
                # column will be "No Data." In this case, no IREAD chart at all.
                if (
                    pd.to_numeric(
                        total_iread_data["Total|IREAD"],
                        errors="coerce",
                    ).sum()
                    == 0
                ):
                    iread_breakdown = []

                else:
                    # Generate simple table and chart with school level IREAD
                    # data only
                    total_iread_data = total_iread_data.rename(
                        columns={
                            "Total|IREAD": "Total",
                        }
                    )

                    iread_fig = make_line_chart(total_iread_data)

                    total_iread_table_data = (
                        total_iread_data.set_index("Year")
                        .T.rename_axis("Category")
                        .rename_axis(None, axis=1)
                        .reset_index()
                    )

                    total_iread_table_data = total_iread_table_data.set_index("Category")
                    
                    total_iread_table_data = total_iread_table_data.applymap("{:.2%}".format)
                    total_iread_table_data = total_iread_table_data.reset_index()

                    iread_table = create_single_header_table(
                        total_iread_table_data, "IREAD"
                    )

                    iread_breakdown = create_line_fig_layout(
                        iread_table, iread_fig, "IREAD"
                    )

            else:
                # Begin processing student level iread data
                iread_student_data = iread_student_data.rename(
                    columns={"Test Year": "Year"}
                )

                iread_student_data["STN"] = iread_student_data[
                    "STN"
                ].astype(str)

                iread_student_data["Year"] = iread_student_data[
                    "Year"
                ].astype(str)

                # Group by Year and Period - get percentage passing and not passing
                iread_student_pass = (
                    iread_student_data.groupby(["Year", "Test Period"])[
                        "Status"
                    ]
                    .value_counts(normalize=True)
                    .reset_index(name="Percent")
                )

                # Filter to remove everything but Passing Students
                iread_student_pass = iread_student_pass[iread_student_pass["Status"].str.startswith("Pass")]

                # Get count (nsize) for total # of Students Tested per year and period
                iread_student_tested = (
                    iread_student_data.groupby(["Year", "Test Period"])[
                        "Status"
                    ]
                    .count()
                    .reset_index(name="N-Size")
                )

                # pivot to get Test Period as Column Name and Year as col value
                iread_student_tested = (
                    iread_student_tested.pivot_table(
                        index=["Year"], columns="Test Period", values="N-Size"
                    )
                    .reset_index()
                    .rename_axis(None, axis=1)
                )

                iread_student_tested = iread_student_tested.rename(
                    columns={"Spring": "Spring N-Size", "Summer": "Summer N-Size"}
                )

                iread_student_pass = iread_student_pass.drop(["Status"], axis=1)

                final_iread_student_pass = (
                    iread_student_pass.pivot_table(
                        index=["Year"], columns="Test Period", values="Percent"
                    )
                    .reset_index()
                    .rename_axis(None, axis=1)
                )

                # merge student level data with the school level
                # data calculated above for fig display
                iread_fig_data = pd.merge(
                    final_iread_student_pass, total_iread_data, on=["Year"]
                )

                iread_fig_data = iread_fig_data.rename(
                    columns={
                        "Total|IREAD": "Total",
                    }
                )

                iread_fig = make_line_chart(iread_fig_data)

                # IREAD Table data
                iread_table_data = iread_fig_data.copy()
                
                # Combine passing and tested students
                iread_table_data = iread_table_data.merge(
                    iread_student_tested, on="Year", how="inner"
                )
                iread_table_cols = iread_table_data.columns.tolist()

                # reorder columns (move "Total" to the end and then swap places of
                # "Summer" and "Spring N-Size")
                iread_table_cols.append(
                    iread_table_cols.pop(iread_table_cols.index("Total"))
                )
                iread_table_cols[2], iread_table_cols[-3] = (
                    iread_table_cols[-3],
                    iread_table_cols[2],
                )
                iread_table_data = iread_table_data[iread_table_cols]

                # Create dataframes for other desired IREAD data points

                # Number of 2nd Graders Tested and 2nd Grader Proficiency
                iread_grade2_count = iread_student_data[
                    iread_student_data["Tested Grade"] == "Grade 2"
                ]

                iread_grade2_tested = (
                    iread_grade2_count.groupby(["Year", "Test Period", "Status"])[
                        "Tested Grade"
                    ]
                    .value_counts()
                    .reset_index(name="2nd Graders Tested")
                )

                iread_grade2_proficiency = (
                    iread_grade2_count.groupby(["Year", "Test Period"])["Status"]
                    .value_counts(normalize=True)
                    .reset_index(name="2nd Graders Proficiency")
                )

                # Number of Exemptions Granted for Non-Pass Students
                iread_exemption_count = iread_student_data[
                    iread_student_data["Exemption Status"] == "Exemption"
                ]

                iread_exemptions = (
                    iread_exemption_count.groupby(["Year"])["Exemption Status"]
                    .value_counts()
                    .reset_index(name="No Pass (Exemption)")
                )

                # Number of Non-passing Students Advanced
                iread_advance_no_pass_count = iread_student_data[
                    (iread_student_data["Status"] == "Did Not Pass")
                    & (iread_student_data["Current Grade"] == "Grade 4")
                ]
                iread_advance_no_pass = (
                    iread_advance_no_pass_count.groupby(["Year"])["Status"]
                    .value_counts()
                    .reset_index(name="No Pass (Advanced)")
                )

                # Number of Students Retained
                iread_retained_count = iread_student_data[
                    (
                        (iread_student_data["Status"] == "Did Not Pass")
                        & (iread_student_data["Tested Grade"] == "Grade 3")
                        & (iread_student_data["Current Grade"] == "Grade 3")
                    )
                ]
                iread_retained = (
                    iread_retained_count.groupby(["Year"])["Status"]
                    .value_counts()
                    .reset_index(name="No Pass (Retained)")
                )
            
                ## Add WIDA data to IREAD table
                # Only add this to table if IREAD data otherwise exists

                # Available WIDA data fields: 'Comprehension Proficiency Level',
                # 'Listening Proficiency Level', 'Literacy Proficiency Level',
                # 'Oral Proficiency Level', 'Reading Proficiency Level',
                # 'Speaking Proficiency Level', 'Writing Proficiency Level'

                # get a list of all STNs past and present from the ILEARN
                # dataset for the given school ID to use to match WIDA data
                # to each school. the WIDA data, for some reason, does not
                # have School ID information. This will be empty for guest (non-ICSB) schools
                school_stns = get_ilearn_stns(school)

                if len(school_stns.index) < 1:
                    wida_breakdown = []

                else:
                    school_stns["STN"] = school_stns["STN"].astype(str)

                    all_wida = get_wida_student_data()
                    all_wida["STN"] = all_wida["STN"].astype(str)

                    # get School WIDA data and build dfs to compare IREAD and
                    # WIDA data - NOTE: For many schools this will be empty or
                    # a very small dataset.
                    wida_comp_data = all_wida[["STN", "Year", "Composite Overall Proficiency Level"]].copy()
                    iread_comp_data = iread_student_data[["STN", "Year", "Test Period", "Status", "Exemption Status"]].copy() 

                    wida_comp_data["Year"] = wida_comp_data["Year"].astype(str)
                    iread_comp_data["Year"] = iread_comp_data["Year"].astype(str)              
                    iread_comp_data["STN"] = iread_comp_data["STN"].astype(str)

                    # matches all STNs with WIDA and IREAD scores from same year.
                    # NOTE: This captures all students who took WIDA in the same year
                    # that they took IREAD. It does not match students with a recorded
                    # WIDA score either before or after a recorded IREAD score. While
                    # we do not want to capture the latter, we do want to add those
                    # students who has a prior year WIDA score. So we need to run two
                    # merge operations, one on STN and YEAR (which captures same year
                    # testers) and one just on STN where we search for any STN
                    # matches where IREAD Tested Year is > than Max WIDA Tested Year
                    current_testers = pd.merge(iread_comp_data, wida_comp_data, on=["STN","Year"])
                    
                    # need to differentiate between years when not merging on Year
                    iread_comp_data = iread_comp_data.rename(columns={"Year": "IREAD Year"})
                    wida_comp_data = wida_comp_data.rename(columns={"Year": "WIDA Year"})
                    
                    # find STNs where WIDA tested year < IREAD Year
                    prior_testers = pd.merge(iread_comp_data, wida_comp_data, on=["STN"])
                    
                    # Find Max WIDA Year value for each STN
                    max_wida = prior_testers.groupby(['STN'])['WIDA Year'].max().reset_index(name="WIDA Max")
                    
                    # drop duplicates from the full data set (where the same STN can appear
                    # up to 5 times) and merge with WIDA Max to add IREAD Year
                    prior_testers = prior_testers.drop_duplicates(subset=['STN'], keep='last')
                    max_wida = pd.merge(max_wida,prior_testers,on=["STN"], how="left")

                    # filter by STNs where IREAD Year is > then WIDA Max Year
                    wida_stn_to_add = max_wida[max_wida["IREAD Year"].astype(int) > \
                        max_wida["WIDA Max"].astype(int)]

                    # Merge the prior and current testers into one df
                    if not wida_stn_to_add.empty:

                        # change column names to match
                        wida_stn_to_add = wida_stn_to_add.drop(["WIDA Max", "WIDA Year"], axis=1)
                        wida_stn_to_add = wida_stn_to_add.rename(columns={"IREAD Year": "Year"})

                        wida_iread_data = pd.concat([current_testers, wida_stn_to_add])
                    else:
                        wida_iread_data = current_testers
                
                    # Get WIDA Average by Year and Status (Pass/No Pass)
                    wida_iread_avg = (
                        wida_iread_data.groupby(["Year","Status"])["Composite Overall Proficiency Level"]
                        .mean()
                        .reset_index(name="Average")
                    )

                    # Get N-Size for each Year and category (Pass/No Pass)
                    wida_iread_nsize = (
                        wida_iread_data.groupby("Year")["Status"]
                        .value_counts()
                        .reset_index(name="N-Size")
                    )

                    # Merge to add N-Size to WIDA Average df
                    wida_iread_final = pd.merge(wida_iread_avg, wida_iread_nsize, on=["Year","Status"])

                    wida_nopass = wida_iread_final[wida_iread_final["Status"] == "Did Not Pass"]
                    wida_pass = wida_iread_final[wida_iread_final["Status"] == "Pass"]

                    wida_pass = wida_pass.rename(columns={
                        "Average": "Avg. Comp. WIDA for Passing Students",
                        "N-Size": "# of WIDA Tested Students Passing IREAD"})
                    wida_nopass = wida_nopass.rename(columns={
                        "Average": "Avg. Comp. WIDA for Non-Passing Students",
                        "N-Size": "# of WIDA Tested Students Not Passing IREAD"})
                  
                    # Merge iread/wida table data
                    iread_dfs_to_merge = [
                        iread_table_data,
                        iread_grade2_tested,
                        iread_grade2_proficiency,
                        iread_exemptions,
                        iread_advance_no_pass,
                        iread_retained,
                        wida_pass,
                        wida_nopass
                    ]

                    iread_merged = reduce(
                        lambda left, right: pd.merge(
                            left,
                            right,
                            on=["Year"],
                            how="outer",
                            suffixes=("", "_remove"),
                        ),
                        iread_dfs_to_merge,
                    )

                    # select and order columns
                    iread_merged = iread_merged[
                        [
                            "Year",
                            "Spring",
                            "Spring N-Size",
                            "Summer",
                            "Summer N-Size",
                            "Total",
                            "2nd Graders Tested",
                            "2nd Graders Proficiency",
                            "No Pass (Exemption)",
                            "No Pass (Advanced)",
                            "No Pass (Retained)",
                            "# of WIDA Tested Students Passing IREAD",
                            "Avg. Comp. WIDA for Passing Students",
                            "# of WIDA Tested Students Not Passing IREAD",
                            "Avg. Comp. WIDA for Non-Passing Students"
                        ]
                    ]

                    iread_final_table_data = (
                        iread_merged.set_index("Year")
                        .T.rename_axis("Category")
                        .rename_axis(None, axis=1)
                        .reset_index()
                    )

                    # format table data
                    for col in iread_final_table_data.columns[1:]:
                        iread_final_table_data[col] = pd.to_numeric(iread_final_table_data[col], errors="coerce")

                    # NOTE: dataframes aren't built for row-wise operations, so if we need different
                    # formatting for different rows, we have to do something grotesque like the following
                    # start at 1 to again skip "Category" column
                    for x in range(1, len(iread_final_table_data.columns)):
                        for i in range(0, len(iread_final_table_data.index)):
                            if (i == 0) | (i == 2) | (i == 4) | (i == 6):
                                if ~np.isnan(iread_final_table_data.iat[i, x]):
                                    iread_final_table_data.iat[i, x] = "{:.2%}".format(iread_final_table_data.iat[i, x])
                            elif (i == 11) | (i == 13):
                                iread_final_table_data.iat[i, x] = "{:,.2f}".format(iread_final_table_data.iat[i, x])
                            else:
                                iread_final_table_data.iat[i, x] = "{:,.0f}".format(iread_final_table_data.iat[i, x])

                    # replace Nan with "-"
                    iread_final_table_data = iread_final_table_data.replace({"nan": "\u2014", np.NaN: "\u2014"}, regex=True)

                    iread_table = create_single_header_table(
                        iread_final_table_data, "IREAD"
                    )

                    iread_breakdown = create_line_fig_layout(
                        iread_table, iread_fig, "IREAD"
                    )
        # End IREAD Table and Fig block
                    
        ## WIDA data
                    
        # get IREAD STNs and merge with ILEARN STNs
        iread_stns = pd.DataFrame()
        iread_stns["STN"] = iread_student_data["STN"]
        iread_stns["STN"] = iread_stns["STN"].astype(str)

        all_stns = pd.concat(
            [school_stns, iread_stns], axis=0, ignore_index=True
        )

        # drop duplicate STNs ("set" is quite a bit faster than
        # drop_duplicates())
        stn_list = list(set(all_stns["STN"].to_list()))

        all_wida = get_wida_student_data()
        
        school_wida = all_wida[all_wida["STN"].isin(stn_list)]

        if len(school_wida.index) < 1:
            wida_breakdown = []

        else:

            # Get WIDA average per grade by year
            wida_school_total = (
                school_wida.groupby(["Year", "Tested Grade"])[
                    "Composite Overall Proficiency Level"
                ]
                .mean()
                .reset_index(name="Average")
            )

            # get WIDA total school average by year
            wida_school_total_data = (
                school_wida.groupby(["Year"])[
                    "Composite Overall Proficiency Level"
                ]
                .mean()
                .reset_index(name="Average")
            )

            # Drop data for AHS students
            wida_school_total = wida_school_total.loc[
                wida_school_total["Tested Grade"] != "Grade 12+/Adult"
            ]

            # pivot to show average WIDA schore by grade (col) by year (row)
            wida_fig_data = (
                wida_school_total.pivot_table(
                    index=["Year"], columns="Tested Grade", values="Average"
                )
                .reset_index()
                .rename_axis(None, axis=1)
            )

            # Sort the Grade columns in ascending order
            tmp_col = wida_fig_data["Year"]
            wida_fig_data = wida_fig_data.drop(["Year"], axis=1)

            # reindex and sort columns using only the numerical part
            wida_fig_data = wida_fig_data.reindex(
                sorted(wida_fig_data.columns, key=lambda x: float(x[6:])),
                axis=1,
            )
            wida_fig_data.insert(loc=0, column="Year", value=tmp_col)

            # Add school Average to by year calcs
            wida_fig_data = pd.merge(wida_fig_data, wida_school_total_data, on="Year")

            # Get N-Size for each grade for each year and add to table data
            wida_nsize = school_wida.value_counts(["Tested Grade","Year"]).reset_index().rename(columns={0: "N-Size"})
            wida_nsize_data = pd.merge(wida_school_total, wida_nsize, on=["Year","Tested Grade"])

            # Get nsize data in same format as scores
            wida_nsize_data = wida_nsize_data.drop("Average", axis = 1)

            wida_nsize_data = (
                wida_nsize_data.pivot_table(
                    index=["Year"], columns="Tested Grade", values="N-Size"
                )
                .reset_index()
                .rename_axis(None, axis=1)
            )

            # identify year columns to get totals (named Average to match
            # scores df col name)
            nsize_years = [c for c in wida_nsize_data.columns if "Grade" in c]                      
            wida_nsize_data["Average"] = wida_nsize_data[nsize_years].sum(axis=1)
            
            # sort nsize columns to match data dataframe (using natural sort)
            nsize_years.sort(key=natural_keys)
            nsize_cols_sorted = ["Year"] + nsize_years + ["Average"]
            wida_nsize_data = wida_nsize_data[nsize_cols_sorted]

            # should not have negative values, but bad data causes them to
            # appear from time to time   
            wida_fig_data[wida_fig_data < 0] = np.NaN

            # Create line chart for WIDA Scores by Grade and Total
            wida_fig = make_line_chart(wida_fig_data)

            wida_table_data = (
                wida_fig_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )

            wida_nsize_data = (
                wida_nsize_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )

            wida_nsize_data.columns = wida_nsize_data.columns.astype(str)
            wida_nsize_data.columns = ["Category"] + [str(col) + 'N-Size' for col in wida_nsize_data.columns if "Category" not in col]
            wida_table_data.columns = wida_table_data.columns.astype(str)
            wida_nsize_data.columns = ["Category"] + [str(col) + 'School' for col in wida_nsize_data.columns if "Category" not in col]

            for col in wida_table_data.columns[1:]:
                wida_table_data[col] = pd.to_numeric(wida_table_data[col], errors="coerce")
            
            wida_table_data = wida_table_data.set_index("Category")
            
            wida_table_data = wida_table_data.applymap("{:.2f}".format)
            wida_table_data = wida_table_data.reset_index()

            wida_table_data = wida_table_data.replace({"nan": "\u2014", np.NaN: "\u2014"}, regex=True) # add dash

            # merge nsize data into data to get into format
            # expected by multi_table function

            # interweave columns and add category back
            data_cols = [e for e in wida_table_data.columns if "Category" not in e]
            nsize_cols = [e for e in wida_nsize_data.columns if "Category" not in e]
            final_cols = list(itertools.chain(*zip(data_cols, nsize_cols)))
            final_cols.insert(0, "Category")

            # merge and re-order using final_cols
            wida_final_data = pd.merge(wida_table_data, wida_nsize_data, on="Category")
            
            wida_final_data = wida_final_data[final_cols]

            wida_table = create_multi_header_table(wida_final_data)

            wida_breakdown = create_line_fig_layout(
                wida_table, wida_fig, "WIDA"
            )

        # End WIDA block
            
        ## Student level ILEARN data (all data for all years)
        # NOTE: Not currently used
        # TODO: ADD CROSS REFERENCE TO STUDENT LEVEL ILEARN DATA -
        # TODO: LONGITUDINAL TRACKING 3-8 ELA
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)  
        ilearn_student_all = get_ilearn_student_data(school)
        iread_student_data = get_iread_student_data(school)
        ilearn_filtered = ilearn_student_all.filter(
            regex=r"STN|Current Grade|Tested Grade|Math|ELA"
        )
        ilearn_filtered = ilearn_filtered.rename(
            columns={
                "Current Grade": "ILEARN Current Grade",
                "Tested Grade": "ILEARN Tested Grade",
            }
        )
        ilearn_filtered["STN"] = ilearn_filtered["STN"].astype(str)

        school_all_student_data = pd.merge(
            iread_student_data, ilearn_filtered, on="STN"
        )


        school_all_student_data = school_all_student_data[["Test Year",
            "STN","Tested Grade","Status","Exemption Status","ILEARN Tested Grade",
            "Math Proficiency","ELA Proficiency"]]

        # proficiency_values = {
        #     "Below Proficiency": 1,
        #     "Approaching Proficiency": 2,
        #     "At Proficiency": 3,
        #     "Above Proficiency": 4,
        # }
        # school_all_student_data = school_all_student_data.replace({"Math Proficiency": proficiency_values})
        # school_all_student_data = school_all_student_data.replace({"ELA Proficiency": proficiency_values})        
        
        all_student_data_nopass = school_all_student_data[school_all_student_data["Status"] == "Did Not Pass"]
        all_student_data_pass = school_all_student_data[school_all_student_data["Status"] == "Pass"]
        
                        # Group by Year and Period - get percentage passing and not passing
        iread_ilearn_pass = (
            all_student_data_pass.groupby(["Test Year", "ILEARN Tested Grade"])[
                "Math Proficiency"
            ]
            .value_counts()
            .reset_index(name="Proficiency")
        )

        iread_ilearn_nopass = (
            all_student_data_nopass.groupby(["Test Year", "ILEARN Tested Grade"])[
                "Math Proficiency"
            ]
            .value_counts()
            .reset_index(name="Proficiency")
        )

        print(iread_ilearn_pass)
        print(iread_ilearn_nopass)
        # TODO: Performance on ILEARN for students not passing IREAD
        # Get total # of students for each grade for each year
        # Calculate Proficiency for each year for each grade ->
        #   # students / # At or Above
        #   # students / # Approaching
        #   for IREAD Passing Students and IREAD not passing students
        # % Proficiency for students not passing IREAD
        # % Proficiency for students passing IREAD
        #

        filename = "tst.csv"
        school_all_student_data.to_csv(filename, index=False)

        # IREAD data goes back to 2018, ILEARN goes back to 2019,
        # because we typically only show 5 years of data, a current
        # eighth grader would have taken IREAD in 2018.
        # NOTE: If we want longitudinal data for earlier years, we
        # need to add earlier IREAD. An eight grader in 2019 would
        # have taken IREAD in 2014.

        # because IREAD goes back farther, use it as base and merge
        # ILEARN data

        # ilearn_stn_list = ilearn_filtered["STN"].tolist()
        # tst_all_data = iread_student_data[iread_student_data["STN"].isin(ilearn_stn_list)]


        # # TODO: Test different merge types here to see what we want
        # school_all_student_data = pd.merge(
        #     iread_filtered, ilearn_filtered, on="STN"
        # )

        # # Calculate ILEARN Year
        # # Current Grade in file is the grade the student is rising into at the
        # # end of the data year. So if Current Grade is 7th, then the student was
        # # in 6th grade for the data year. To get year of a given ILEARN Test:
        # #       (Max Data Year + 1) - (ILEARN Current Grade - ILEARN Tested Grade)

        # # E.g., = (2023 + 1) - (8 - 3) = 2024 - 5 = 2019 -> a 2024 Grade 8 Student took
        # # IREAD in 2019. If the row of data shows ILEARN CG of 8 and TG of 3, the ILEARN
        # # Tested year is 2019.
        # school_all_student_data["ILEARN Year"] = (
        #     current_academic_year + 1
        # ) - (
        #     school_all_student_data["ILEARN Current Grade"]
        #     .str[-1]
        #     .astype(int)
        #     - school_all_student_data["ILEARN Tested Grade"]
        #     .str[-1]
        #     .astype(int)
        # )

        #
        # # Avg ELA/Math over time for IREAD Pass - 2018-19, 21, 22, 23
        # # group by IREAD Pass and ILEARN Year:
        # # a) count Exceeds, At, Approach, Below
        # # b) measure point diff between Cut and Scale and Average
        # # c) measure raw scale score avg
        # # Avg ELA over time for IREAD No Pass

    ## Attendance Data (Attendance Rate/Chronic Absenteeism)
    attendance_rate = get_attendance_data(
        selected_school_id, selected_school_type, selected_year_string
    )

    if len(attendance_rate.index) > 0 and len(attendance_rate.columns) > 1:

        attendance_table = create_single_header_table(
            attendance_rate, "Attendance Data"
        )
    else:
        attendance_table = no_data_table(
            "No Data to Display.", "Attendance Data", "six"
        )

    attendance_table_hs = set_table_layout(
        attendance_table, attendance_table, attendance_rate.columns
    )
            
    # variables for display purposes
    if radio_category == "grade":
        wida_breakdown_container = {"display": "block"}
        iread_breakdown_container = {"display": "block"}
        proficiency_ela_grades_container = {"display": "block"}
        proficiency_math_grades_container = {"display": "block"}
        proficiency_ethnicity_math = []
        math_ethnicity_bar_fig = []
        proficiency_subgroup_math = []
        math_subgroup_bar_fig = []
        proficiency_ethnicity_ela = []
        ela_ethnicity_bar_fig = []
        proficiency_subgroup_ela = []
        ela_subgroup_bar_fig = []
    elif radio_category == "ethnicity":
        proficiency_ela_ethnicity_container = {"display": "block"}
        proficiency_math_ethnicity_container = {"display": "block"}
        proficiency_grades_ela = []
        ela_grade_bar_fig = []
        proficiency_subgroup_ela = []
        ela_subgroup_bar_fig = []
        proficiency_grades_math = []
        math_grade_bar_fig = []
        proficiency_subgroup_math = []
        math_subgroup_bar_fig = []
    elif radio_category == "subgroup":
        proficiency_ela_subgroup_container = {"display": "block"}
        proficiency_math_subgroup_container = {"display": "block"}
        proficiency_grades_ela = []
        ela_grade_bar_fig = []
        proficiency_ethnicity_ela = []
        ela_ethnicity_bar_fig = []
        proficiency_grades_math = []
        math_grade_bar_fig = []
        proficiency_ethnicity_math = []
        math_ethnicity_bar_fig = []
    elif radio_category == "all":
        wida_breakdown_container = {"display": "block"}
        iread_breakdown_container = {"display": "block"}
        proficiency_ela_grades_container = {"display": "block"}
        proficiency_math_grades_container = {"display": "block"}
        proficiency_ela_ethnicity_container = {"display": "block"}
        proficiency_math_ethnicity_container = {"display": "block"}
        proficiency_ela_subgroup_container = {"display": "block"}
        proficiency_math_subgroup_container = {"display": "block"}
    else:
        iread_breakdown = []
        proficiency_grades_ela = []
        ela_grade_bar_fig = []
        proficiency_ethnicity_ela = []
        ela_ethnicity_bar_fig = []
        proficiency_subgroup_ela = []
        ela_subgroup_bar_fig = []
        proficiency_grades_math = []
        math_grade_bar_fig = []
        proficiency_ethnicity_math = []
        math_ethnicity_bar_fig = []
        proficiency_subgroup_math = []
        math_subgroup_bar_fig = []

    academic_information_notes_string = "There are a number of factors that make it difficult to make \
        valid and reliable comparisons between test scores from 2019 to 2022. For example, ILEARN was \
        administered for the first time during the 2018-19 SY and represented an entirely new type and \
        mode of assessment (adaptive and online-only). No State assessment was administered in 2020 because \
        of the Covid-19 pandemic. Finally, the 2019 data set includes only students  who attended the \
        testing school for 162 days, while the 2021 and 2022 data sets included all tested students."

    return (
        wida_breakdown,
        wida_breakdown_container,
        iread_breakdown,
        iread_breakdown_container,
        proficiency_grades_ela,
        ela_grade_bar_fig,
        proficiency_ela_grades_container,
        proficiency_ethnicity_ela,
        ela_ethnicity_bar_fig,
        proficiency_ela_ethnicity_container,
        proficiency_subgroup_ela,
        ela_subgroup_bar_fig,
        proficiency_ela_subgroup_container,
        proficiency_grades_math,
        math_grade_bar_fig,
        proficiency_math_grades_container,
        proficiency_ethnicity_math,
        math_ethnicity_bar_fig,
        proficiency_math_ethnicity_container,
        proficiency_subgroup_math,
        math_subgroup_bar_fig,
        proficiency_math_subgroup_container,
        attendance_table_k8,
        attendance_table_hs,
        k8_table_container,
        k12_grad_overview_table,
        k12_grad_ethnicity_table,
        k12_grad_subgroup_table,
        k12_grad_table_container,
        k12_sat_cut_scores_table,
        k12_sat_overview_table,
        k12_sat_ethnicity_table,
        k12_sat_subgroup_table,
        k12_sat_table_container,
        main_container,
        empty_container,
        no_display_data,
        academic_information_notes_string,
    )


# layout = html.Div(
# this needs to be a function in order for it to be called correctly by subnav_academic_information()
def layout():
    return html.Div(
        [
            html.Div(
                [
                    dcc.Loading(
                        id="loading",
                        type="circle",
                        fullscreen=True,
                        style={
                            "position": "absolute",
                            "alignSelf": "center",
                            "backgroundColor": "#F2F2F2",
                        },
                        children=[
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="iread-breakdown",
                                                        children=[],
                                                    ),
                                                ],
                                                id="iread-breakdown-container",
                                                className="pagebreak-after",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="wida-breakdown",
                                                        children=[],
                                                    ),
                                                ],
                                                id="wida-breakdown-container",
                                                className="pagebreak-after",
                                            ),                                            
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="proficiency-grades-ela",
                                                        children=[],
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        id="ela-grade-bar-fig"
                                                                    ),
                                                                ],
                                                                className="pretty-container--close--top six columns",
                                                            ),
                                                        ],
                                                        className="bare-container--flex--center twelve columns",
                                                    ),
                                                ],
                                                id="proficiency-ela-grades-container",
                                                className="pagebreak-after",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="proficiency-ethnicity-ela",
                                                        children=[],
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        id="ela-ethnicity-bar-fig"
                                                                    ),
                                                                ],
                                                                className="pretty-container--close--top six columns",
                                                            ),
                                                        ],
                                                        className="bare-container--flex--center twelve columns",
                                                    ),
                                                ],
                                                id="proficiency-ela-ethnicity-container",
                                                className="pagebreak-after",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="proficiency-subgroup-ela",
                                                        children=[],
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        id="ela-subgroup-bar-fig"
                                                                    ),
                                                                ],
                                                                className="pretty-container--close--top six columns",
                                                            ),
                                                        ],
                                                        className="bare-container--flex--center twelve columns",
                                                    ),
                                                ],
                                                id="proficiency-ela-subgroup-container",
                                                className="pagebreak-after",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="proficiency-grades-math",
                                                        children=[],
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        id="math-grade-bar-fig"
                                                                    ),
                                                                ],
                                                                className="pretty-container--close--top six columns",
                                                            ),
                                                        ],
                                                        className="bare-container--flex--center twelve columns",
                                                    ),
                                                ],
                                                id="proficiency-math-grades-container",
                                                className="pagebreak-after",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="proficiency-ethnicity-math",
                                                        children=[],
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        id="math-ethnicity-bar-fig"
                                                                    ),
                                                                ],
                                                                className="pretty-container--close--top six columns",
                                                            ),
                                                        ],
                                                        className="bare-container--flex--center twelve columns",
                                                    ),
                                                ],
                                                id="proficiency-math-ethnicity-container",
                                                className="pagebreak-after",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="proficiency-subgroup-math",
                                                        children=[],
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        id="math-subgroup-bar-fig"
                                                                    ),
                                                                ],
                                                                className="pretty-container--close--top six columns",
                                                            ),
                                                        ],
                                                        className="bare-container--flex--center twelve columns",
                                                    ),
                                                ],
                                                id="proficiency-math-subgroup-container",
                                            ),
                                            html.Div(
                                                id="attendance-table-k8", children=[]
                                            ),
                                        ],
                                        id="k8-table-container",
                                    ),
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
                                            html.Div(id="k12-grad-overview-table"),
                                            html.Div(id="k12-grad-ethnicity-table"),
                                            html.Div(id="k12-grad-subgroup-table"),
                                        ],
                                        id="k12-grad-table-container",
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
                                            html.Div(
                                                id="k12-sat-cut-scores-table",
                                                children=[],
                                            ),
                                            html.Div(id="k12-sat-overview-table"),
                                            html.Div(id="k12-sat-ethnicity-table"),
                                            html.Div(id="k12-sat-subgroup-table"),
                                        ],
                                        id="k12-sat-table-container",
                                    ),
                                    html.Div(
                                        id="attendance-table-hs", children=[]
                                    ),
                                ],
                                id="academic-information-main-container",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label(
                                                "Notes:", className="key-label__header"
                                            ),
                                            html.P(""),
                                            html.P(
                                                id="academic-information-notes-string",
                                                style={
                                                    "textAlign": "Left",
                                                    "color": "#6783a9",
                                                    "fontSize": 12,
                                                    "marginLeft": "10px",
                                                    "marginRight": "10px",
                                                    "marginTop": "10px",
                                                },
                                            ),
                                        ],
                                        className="pretty-container__key ten columns",
                                    ),
                                ],
                                className="bare-container--flex--center twelve columns",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                [
                    html.Div(id="academic-information-no-data"),
                ],
                id="academic-information-empty-container",
            ),
        ],
        id="main-container",
    )
