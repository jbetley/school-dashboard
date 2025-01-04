#######################################################
# ICSB Dashboard - Academic Information - Proficiency #
#######################################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.16
# date:     12/29/24
# TODO: Break down into three pages: ILEARN; IREAD; WIDA
# TODO: Add hover for AHS graduation data

import dash
from dash import dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd
import re


from .globals import (
    ethnicity,
    subgroup,
    subject,
    grades_all,
    grades,
    grades_ordinal
)
from .load_data import (
    get_school_stns,
    get_iread_student_data,
    get_wida_student_data,
    get_proficiency_data,
    get_school_index,
    get_excluded_years,
    get_academic_data,
)
from .clean_data import clean_academic_data
from .tables import (
    create_multi_header_table,
    create_key_table,
    create_simple_table,
    create_single_header_table,
    create_iread_ilearn_table,
    create_empty_page_layout,
)
from .process_data import (
    remove_empty_cols,
    process_wida_data,
    process_wida_to_iread_details,
    process_iread_student_data,
    process_stacked_bar,
)
from .charts import no_data_fig_label, make_stacked_bar, make_line_chart
from .layouts import set_table_layout, create_line_fig_layout

dash.register_page(
    __name__,
    top_nav=True,
    name="Academic Information",
    path="/academic_information",
    order=7,
)


@callback(
    Output("linechart-iread-school-level-layout", "children"),
    Output("iread-school-level-layout-container", "style"),
    Output("linechart-iread-school-details", "children"),
    Output("iread-school-details-container", "style"),
    Output("linechart-wida-breakdown", "children"),
    Output("wida-breakdown-container", "style"),
    Output("wida-iread-table", "children"),
    Output("wida-iread-table-container", "style"),
    Output("iread-ilearn-ela-table", "children"),
    Output("iread-ilearn-math-table", "children"),
    Output("ilearn-iread-table-container", "style"),
    Output("linechart-proficiency-grades-ela", "children"),
    Output("stacked-ela-grade-bar-fig", "children"),
    Output("proficiency-ela-grades-container", "style"),
    Output("linechart-proficiency-ethnicity-ela", "children"),
    Output("ela-ethnicity-bar-fig", "children"),
    Output("proficiency-ela-ethnicity-container", "style"),
    Output("linechart-proficiency-subgroup-ela", "children"),
    Output("ela-subgroup-bar-fig", "children"),
    Output("proficiency-ela-subgroup-container", "style"),
    Output("proficiency-grades-math", "children"),
    Output("math-grade-bar-fig", "children"),
    Output("proficiency-math-grades-container", "style"),
    Output("linechart-proficiency-ethnicity-math", "children"),
    Output("math-ethnicity-bar-fig", "children"),
    Output("proficiency-math-ethnicity-container", "style"),
    Output("linechart-proficiency-subgroup-math", "children"),
    Output("math-subgroup-bar-fig", "children"),
    Output("proficiency-math-subgroup-container", "style"),
    Output("k8-table-container", "style"),
    Output("hs-grad-overview-table", "children"),
    Output("hs-grad-ethnicity-table", "children"),
    Output("hs-grad-subgroup-table", "children"),
    Output("hs-grad-table-container", "style"),
    Output("hs-sat-cut-scores-table", "children"),
    Output("hs-sat-overview-table", "children"),
    Output("hs-sat-ethnicity-table", "children"),
    Output("hs-sat-subgroup-table", "children"),
    Output("hs-sat-table-container", "style"),
    Output("academic-information-main-container", "style"),
    Output("academic-information-empty-container", "style"),
    Output("academic-information-no-data", "children"),
    Output("academic-information-notes-string", "children"),
    Output("academic-information-notes-string-container", "style"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("academic-type-radio", "value"),
    Input("academic-information-category-radio", "value"),
)
def update_academic_information_page(
    school_id: str, year: str, radio_type: str, radio_category: str
):
    if not school_id:
        raise PreventUpdate

    selected_year_string = year
    selected_year_numeric = int(selected_year_string)

    selected_school = get_school_index(school_id)
    selected_school_type = selected_school["School Type"].values[0]

    # CHS exception (see app.py)
    if int(school_id) == 5874 and selected_year_numeric < 2021:
        selected_school_type = "k12"

    selected_school_name = selected_school["School Name"].values[0]

    is_guest = True if selected_school["Guest"].values[0] == "Y" else False

    excluded_years = get_excluded_years(selected_year_string)

    if not radio_type:
        radio_type = "k8"

    if not radio_category:
        radio_category = "all"

    hs_grad_overview_table = []  # type: list
    hs_grad_ethnicity_table = []  # type: list
    hs_grad_subgroup_table = []  # type: list

    hs_sat_overview_table = []  # type: list
    hs_sat_ethnicity_table = []  # type: list
    hs_sat_subgroup_table = []  # type: list
    hs_sat_cut_scores_table = []  # type: list

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

    academic_information_notes_string = ""
    academic_information_notes_string_container = {"display": "none"}

    main_container = {"display": "none"}
    empty_container = {"display": "none"}

    no_display_data = create_empty_page_layout(
        "Academic Information", "No Data to Display."
    )

    academic_information_notes_string = "ILEARN was administered for the first time during the 2018-19 SY, \
        representing an entirely new type and mode of assessment (adaptive and online-only). No State assessment \
        was administered in 2020 due to the Covid-19 pandemic. The students included in the tested cohort for purposes \
        of calculating the proficiency percentage has not been consistent- in 2019, the cohort included only students \
        who attended the testing school for 162 days, the 2021 and 2022 calculations included all tested students, regardless \
        of the length of time that the student attended the testing school, and the 2023 calculation included students in the \
        cohort of the school in which the student spent the majority of time enrolled."

    # category selection determines which divs are displayed by default
    if radio_category == "grade":
        proficiency_ela_grades_container = {"display": "block"}
        proficiency_math_grades_container = {"display": "block"}
        k8_table_container = {"display": "block"}
        academic_information_notes_string_container = {"display": "block"}

        iread_school_level_layout_container = {"display": "none"}
        iread_school_details_container = {"display": "none"}
        ilearn_iread_table_container = {"display": "none"}
        wida_breakdown_container = {"display": "none"}
        wida_iread_details_table_container = {"display": "none"}
        proficiency_ela_subgroup_container = {"display": "none"}
        proficiency_math_subgroup_container = {"display": "none"}
        proficiency_ela_ethnicity_container = {"display": "none"}
        proficiency_math_ethnicity_container = {"display": "none"}
        hs_sat_table_container = {"display": "none"}
        hs_grad_table_container = {"display": "none"}

    elif radio_category == "ethnicity":
        proficiency_ela_ethnicity_container = {"display": "block"}
        proficiency_math_ethnicity_container = {"display": "block"}
        k8_table_container = {"display": "block"}
        academic_information_notes_string_container = {"display": "block"}

        iread_school_level_layout_container = {"display": "none"}
        iread_school_details_container = {"display": "none"}
        ilearn_iread_table_container = {"display": "none"}
        wida_breakdown_container = {"display": "none"}
        wida_iread_details_table_container = {"display": "none"}
        proficiency_ela_subgroup_container = {"display": "none"}
        proficiency_math_subgroup_container = {"display": "none"}
        proficiency_ela_grades_container = {"display": "none"}
        proficiency_math_grades_container = {"display": "none"}
        hs_sat_table_container = {"display": "none"}
        hs_grad_table_container = {"display": "none"}

    elif radio_category == "subgroup":
        proficiency_ela_subgroup_container = {"display": "block"}
        proficiency_math_subgroup_container = {"display": "block"}
        k8_table_container = {"display": "block"}
        academic_information_notes_string_container = {"display": "block"}

        iread_school_level_layout_container = {"display": "none"}
        iread_school_details_container = {"display": "none"}
        ilearn_iread_table_container = {"display": "none"}
        wida_breakdown_container = {"display": "none"}
        wida_iread_details_table_container = {"display": "none"}
        proficiency_ela_ethnicity_container = {"display": "none"}
        proficiency_math_ethnicity_container = {"display": "none"}
        proficiency_ela_grades_container = {"display": "none"}
        proficiency_math_grades_container = {"display": "none"}
        hs_sat_table_container = {"display": "none"}
        hs_grad_table_container = {"display": "none"}

    elif radio_category == "iread":
        iread_school_level_layout_container = {"display": "block"}
        iread_school_details_container = {"display": "block"}
        ilearn_iread_table_container = {"display": "block"}
        k8_table_container = {"display": "block"}

        wida_breakdown_container = {"display": "none"}
        wida_iread_details_table_container = {"display": "none"}
        proficiency_ela_grades_container = {"display": "none"}
        proficiency_ela_ethnicity_container = {"display": "none"}
        proficiency_ela_subgroup_container = {"display": "none"}
        proficiency_math_grades_container = {"display": "none"}
        proficiency_math_ethnicity_container = {"display": "none"}
        proficiency_math_subgroup_container = {"display": "none"}
        hs_sat_table_container = {"display": "none"}
        hs_grad_table_container = {"display": "none"}
        academic_information_notes_string_container = {"display": "none"}

    elif radio_category == "wida":
        wida_breakdown_container = {"display": "block"}
        wida_iread_details_table_container = {"display": "block"}
        k8_table_container = {"display": "block"}

        iread_school_level_layout_container = {"display": "none"}
        iread_school_details_container = {"display": "none"}
        ilearn_iread_table_container = {"display": "none"}
        proficiency_ela_grades_container = {"display": "none"}
        proficiency_ela_ethnicity_container = {"display": "none"}
        proficiency_ela_subgroup_container = {"display": "none"}
        proficiency_math_grades_container = {"display": "none"}
        proficiency_math_ethnicity_container = {"display": "none"}
        proficiency_math_subgroup_container = {"display": "none"}
        hs_sat_table_container = {"display": "none"}
        hs_grad_table_container = {"display": "none"}
        academic_information_notes_string_container = {"display": "none"}

    elif radio_category == "all":
        iread_school_level_layout_container = {"display": "block"}
        iread_school_details_container = {"display": "block"}
        ilearn_iread_table_container = {"display": "block"}
        wida_breakdown_container = {"display": "block"}
        wida_iread_details_table_container = {"display": "block"}
        proficiency_ela_grades_container = {"display": "block"}
        proficiency_math_grades_container = {"display": "block"}
        proficiency_ela_ethnicity_container = {"display": "block"}
        proficiency_math_ethnicity_container = {"display": "block"}
        proficiency_ela_subgroup_container = {"display": "block"}
        proficiency_math_subgroup_container = {"display": "block"}
        academic_information_notes_string_container = {"display": "block"}
        k8_table_container = {"display": "block"}

        hs_sat_table_container = {"display": "none"}
        hs_grad_table_container = {"display": "none"}

    # High School Data
    if (
        selected_school_type == "hs"
        or selected_school_type == "ahs"
        or (selected_school_type == "k12" and radio_type == "hs")
    ):
        iread_school_level_layout_container = {"display": "none"}
        iread_school_details_container = {"display": "none"}
        ilearn_iread_table_container = {"display": "none"}
        wida_breakdown_container = {"display": "none"}
        wida_iread_details_table_container = {"display": "none"}
        proficiency_ela_grades_container = {"display": "none"}
        proficiency_math_grades_container = {"display": "none"}
        proficiency_ela_ethnicity_container = {"display": "none"}
        proficiency_math_ethnicity_container = {"display": "none"}
        proficiency_ela_subgroup_container = {"display": "none"}
        proficiency_math_subgroup_container = {"display": "none"}
        k8_table_container = {"display": "none"}

        if selected_school_type == "k12":
            school_type = "hs"
        else:
            school_type = selected_school_type

        list_of_schools = [school_id]

        raw_hs_info_data = get_academic_data(list_of_schools, school_type)

        hs_info_data = clean_academic_data(
            raw_hs_info_data,
            list_of_schools,
            school_type,
            selected_year_numeric,
            "info",
        )

        # TODO: Add figs for SAT and Grad Rate
        if len(hs_info_data.index) < 1 or hs_info_data.empty:
            empty_container = {"display": "block"}
            academic_information_notes_string_container = {"display": "none"}
            hs_grad_table_container = {"display": "none"}
            hs_sat_table_container = {"display": "none"}

            no_display_data = create_empty_page_layout(
                "High School Academic Data", "No Data to Display."
            )

        else:
            main_container = {"display": "block"}

            hs_info_data.columns = hs_info_data.columns.astype(str)

            # Graduation Rate Tables
            grad_overview_categories = ["Total", "Non Waiver", "State Average"]

            if selected_school_type == "ahs":
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

            # SAT releases prior to grad rate, so it is possible to have SAT
            # data but no grad data - so we drop Cols that are all NaN or blank
            graduation_data = remove_empty_cols(graduation_data)

            if len(graduation_data.columns) > 1 and len(graduation_data.index) > 0:
                hs_grad_table_container = {"display": "block"}

                # clean up grad rate category
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

                hs_grad_overview_table = create_multi_header_table(
                    grad_overview, "Graduation Data"
                )

                hs_grad_overview_table = set_table_layout(
                    hs_grad_overview_table,
                    hs_grad_overview_table,
                    grad_overview.columns,
                )

                if selected_school_type != "ahs":
                    grad_ethnicity = graduation_data[
                        graduation_data["Category"].str.contains("|".join(ethnicity))
                    ]

                    grad_ethnicity = grad_ethnicity.dropna(axis=1, how="all")

                    hs_grad_ethnicity_table = create_multi_header_table(
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

                    hs_grad_subgroup_table = create_multi_header_table(
                        grad_subgroup, "Graduation Rate by Subgroup"
                    )
                    hs_grad_subgroup_table = set_table_layout(
                        hs_grad_subgroup_table,
                        hs_grad_subgroup_table,
                        grad_subgroup.columns,
                    )

            # SAT Benchmark Table
            hs_sat_table_data = hs_info_data[
                hs_info_data["Category"].str.contains("Benchmark %")
            ].copy()

            # remove columns that are all NaN/null/None
            hs_sat_table_data = remove_empty_cols(hs_sat_table_data)

            if len(hs_sat_table_data.columns) > 1 and len(hs_sat_table_data.index) > 0:
                hs_sat_table_container = {"display": "block"}

                hs_sat_table_data["Category"] = (
                    hs_sat_table_data["Category"]
                    .str.replace("Benchmark %", "")
                    .str.strip()
                )

                hs_sat_overview = hs_sat_table_data[
                    hs_sat_table_data["Category"].str.contains("Total")
                ]

                hs_sat_overview = hs_sat_overview.dropna(axis=1, how="all")

                hs_sat_overview_table = create_multi_header_table(
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

                hs_sat_ethnicity_table = create_multi_header_table(
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

                hs_sat_subgroup_table = create_multi_header_table(
                    hs_sat_subgroup, "SAT Benchmarks by Subgroup"
                )

                hs_sat_subgroup_table = set_table_layout(
                    hs_sat_subgroup_table,
                    hs_sat_subgroup_table,
                    hs_sat_subgroup.columns,
                )

                # SAT cut score key table
                # Source: Varies but start with IDOE website
                hs_sat_cut_scores_label = "SAT Proficiency Cut Scores (2023)"
                hs_sat_cut_scores_dict = {
                    "Content Area": [
                        "Mathematics",
                        "Evidenced-Based Reading and Writing",
                    ],
                    "Below College-Ready Benchmark": ["200 - 460", "200 - 450"],
                    "Approaching College-Ready Benchmark": [
                        "460 - 530",
                        "450 - 480",
                    ],
                    "At College-Ready Benchmark": ["530 - 800", "480 - 800"],
                }

                hs_sat_cut_scores = pd.DataFrame(hs_sat_cut_scores_dict)
                hs_sat_cut_scores_table = create_key_table(
                    hs_sat_cut_scores, hs_sat_cut_scores_label
                )

            academic_information_notes_string = "Beginning with the 2021-22 SY, SAT replaced ISTEP+ as the state mandated HS assessment. \
                Beginning with the 2023 cohort, all students in grade 11 are required to take the SAT per federal requirements."
            academic_information_notes_string_container = {"display": "block"}
    # End HS block

    # Begin K8 block
    elif selected_school_type == "k8" or (
        selected_school_type == "k12" and radio_type == "k8"
    ):
        if selected_school_type == "k12":
            school_type = "k8"
        else:
            school_type = selected_school_type

        list_of_schools = [school_id]

        # NOTE: no ilearn/iread data available for 2020
        raw_k8_info_data = get_academic_data(list_of_schools, school_type)

        k8_info_data = clean_academic_data(
            raw_k8_info_data,
            list_of_schools,
            school_type,
            selected_year_numeric,
            "info",
        )

        k8_info_data["Category"] = (
            k8_info_data["Category"].str.replace(" Proficient %", "").str.strip()
        )

        if len(k8_info_data.index) < 1 or k8_info_data.empty:
            k8_table_container = {"display": "none"}

            no_display_data = create_empty_page_layout(
                "Academic Proficiency", "No Data to Display."
            )

        else:
            k8_table_container = {"display": "block"}
            main_container = {"display": "block"}

            ilearn_table_data = k8_info_data.copy()

            # Reformat data for multiyear line charts
            # Remove N-Size cols, strip suffix from years, and
            # transpose dataframe so categories become column names
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
            ilearn_fig_data["School Name"] = selected_school_name

            ## ILEARN Proficiency Charts and Tables ##

            # NOTE: We use ilearn_table_data variable for tables because we
            # need N-Size values. ilearn_fig_data is similar, just transposed

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
                    ilearn_table_data["Category"].str.contains("|".join(grades_all))
                    & ilearn_table_data["Category"].str.contains("ELA")
                )
            ]

            ela_grade_table = create_single_header_table(years_by_grade_ela)

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

            ela_subgroup_table = create_single_header_table(years_by_subgroup_ela)

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

            ela_ethnicity_table = create_single_header_table(years_by_ethnicity_ela)

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

            math_grade_table = create_single_header_table(years_by_grade_math)

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

            math_subgroup_table = create_single_header_table(years_by_subgroup_math)

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

            math_ethnicity_table = create_single_header_table(years_by_ethnicity_math)

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

            ## ILEARN proficiency breakdown stacked bar charts ##
            raw_k8_info_data = get_proficiency_data(school_id)

            proficiency_rating = [
                "Below Proficiency",
                "Approaching Proficiency",
                "At Proficiency",
                "Above Proficiency",
            ]

            categories = grades_all + ethnicity + subgroup

            ilearn_proficency_data, annotations = process_stacked_bar(
                raw_k8_info_data,
                categories,
                subject,
                proficiency_rating,
                selected_year_numeric,
            )

            ilearn_proficency_data.drop(
                list(
                    ilearn_proficency_data.filter(regex="Total Proficient|ELA and Math")
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

        ## IREAD - School Level Totals, Ethnicity, & Status ##
        both = ethnicity + subgroup + ["Total"]
        categories_iread_all = []

        for b in both:
            categories_iread_all.append(b + "|IREAD")

        # public IREAD data (Total + Ethincity + Subgroup)
        public_iread_school_data = ilearn_table_data[
            ilearn_table_data["Category"].str.contains("|".join(both))
            & ilearn_table_data["Category"].str.contains("IREAD")
        ]

        # ILEARN data releases prior to IREAD3 data, so is possible
        # to have a year show up but be empty- so we drop Cols that
        # are all IREAD values are NaN or blank
        public_iread_school_data = remove_empty_cols(public_iread_school_data)

        # no IREAD data (e.g., MS or ES without grade 3)
        # because public data suppresses, it is actually possible
        # (although unlikely) to have no public data, but still
        # have student level data
        if public_iread_school_data.empty:
            iread_student_data = pd.DataFrame()

            if radio_category == "iread":
                main_container = {"display": "none"}
                empty_container = {"display": "block"}
                academic_information_notes_string_container = {"display": "none"}
                no_display_data = create_empty_page_layout(
                    "IREAD", "No Data to Display."
                )

            else:
                iread_school_level_layout = []
                iread_school_details = []

        else:
            main_container = {"display": "block"}

            public_iread_school_table = create_single_header_table(
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

            ## Student level IREAD data (ICSB Schools Only) ##
            iread_student_data = get_iread_student_data(school_id)

            if excluded_years:
                iread_student_data = iread_student_data[
                    ~iread_student_data["Year"].astype(int).isin(excluded_years)
                ]

            # If school has no student level data (or is a Guest school),
            # hide school details
            if is_guest == True or len(iread_student_data.index) < 1:
                iread_school_details = []

            else:
                # student level IREAD chart and table
                main_container = {"display": "block"}

                iread_total = public_iread_school_data[
                    public_iread_school_data["Category"] == "Total|IREAD"
                ]

                (
                    iread_details_fig_data,
                    iread_details_table_data,
                ) = process_iread_student_data(iread_student_data, iread_total)

                if len(iread_details_fig_data.index) == 0:
                    iread_details_fig = []
                else:
                    iread_details_fig = make_line_chart(iread_details_fig_data)

                if len(iread_details_table_data.index) == 0:
                    iread_details_table = []
                else:
                    iread_details_table = create_simple_table(
                        iread_details_table_data, "IREAD"
                    )

                if iread_details_fig and iread_details_table:
                    iread_school_details = create_line_fig_layout(
                        iread_details_table, iread_details_fig, "IREAD Details"
                    )
                else:
                    iread_school_details

            # IREAD to ILEARN Table
            if iread_student_data.empty or ilearn_table_data.empty:
                iread_ilearn_ela_table = []
                iread_ilearn_math_table = []

            else:
                iread_ilearn_ela_table = create_iread_ilearn_table(
                    school_id, "ELA", excluded_years
                )
                iread_ilearn_math_table = create_iread_ilearn_table(
                    school_id, "Math", excluded_years
                )

        ## WIDA - Student Level Data
        # Available WIDA data fields: 'Comprehension Proficiency Level',
        # 'Listening Proficiency Level', 'Literacy Proficiency Level',
        # 'Oral Proficiency Level', 'Reading Proficiency Level',
        # 'Speaking Proficiency Level', 'Writing Proficiency Level'

        # NOTE: Currently only displaying for K-8 Schools
        # TODO: add wida table for HS

        # Guests will never have WIDA data
        if is_guest == True:
            if radio_category == "wida":
                main_container = {"display": "none"}
                empty_container = {"display": "block"}
                academic_information_notes_string_container = {"display": "none"}
                no_display_data = create_empty_page_layout(
                    "WIDA", "No Data to Display."
                )

            else:
                wida_iread_details_table = []
                wida_breakdown = []
        else:
            # NOTE: Currently, the WIDA LINK file does not have a School ID column,
            # so we have to get a list of all STNs associated with the school (from
            # both IREAD and ILEARN data files) and then match - this would be much
            # easier if we can get the school ID added to the raw data
            all_stns = get_school_stns(school_id)

            stn_list = list(set(all_stns["STN"].to_list()))

            # Get student level wida data for the school by matching
            # against stn_list.
            wida_student_data = get_wida_student_data(stn_list)

            if excluded_years:
                wida_student_data = wida_student_data[
                    ~wida_student_data["Year"].astype(int).isin(excluded_years)
                ]

            if len(wida_student_data.index) < 1:
                if radio_category == "wida":
                    main_container = {"display": "none"}
                    empty_container = {"display": "block"}
                    academic_information_notes_string_container = {"display": "none"}
                    no_display_data = create_empty_page_layout(
                        "WIDA", "No Data to Display."
                    )

                else:
                    wida_iread_details_table = []
                    wida_breakdown = []

            else:
                main_container = {"display": "block"}

                final_fig_data, final_table_data = process_wida_data(wida_student_data)

                if len(final_fig_data.index) == 0:
                    wida_breakdown_fig = []
                else:
                    wida_breakdown_fig = make_line_chart(final_fig_data)

                if len(final_table_data.index) == 0:
                    wida_breakdown_table = []
                else:
                    wida_breakdown_table = create_single_header_table(final_table_data)

                if wida_breakdown_fig and wida_breakdown_table:
                    wida_breakdown = create_line_fig_layout(
                        wida_breakdown_table, wida_breakdown_fig, "WIDA Breakdown"
                    )
                else:
                    wida_breakdown = []

                ## WIDA to IREAD table
                if iread_student_data.empty:
                    wida_iread_details_table = []

                else:
                    main_container = {"display": "block"}

                    wida_iread_details_table_data = process_wida_to_iread_details(
                        wida_student_data, iread_student_data
                    )

                    if len(wida_iread_details_table_data.index) == 0:
                        wida_iread_details_table = []
                    else:
                        wida_iread_details_table = create_simple_table(
                            wida_iread_details_table_data, "WIDA Details"
                        )

    return (
        iread_school_level_layout,
        iread_school_level_layout_container,
        iread_school_details,
        iread_school_details_container,
        wida_breakdown,
        wida_breakdown_container,
        wida_iread_details_table,
        wida_iread_details_table_container,
        iread_ilearn_ela_table,
        iread_ilearn_math_table,
        ilearn_iread_table_container,
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
        k8_table_container,
        hs_grad_overview_table,
        hs_grad_ethnicity_table,
        hs_grad_subgroup_table,
        hs_grad_table_container,
        hs_sat_cut_scores_table,
        hs_sat_overview_table,
        hs_sat_ethnicity_table,
        hs_sat_subgroup_table,
        hs_sat_table_container,
        main_container,
        empty_container,
        no_display_data,
        academic_information_notes_string,
        academic_information_notes_string_container,
    )


# this needs to be a function in order for it to be called
# correctly by subnav_academic_information()
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
                                                        id="linechart-iread-school-level-layout",
                                                        children=[],
                                                    ),
                                                ],
                                                id="iread-school-level-layout-container",
                                                className="pagebreak-after",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="linechart-iread-school-details",
                                                        children=[],
                                                    ),
                                                ],
                                                id="iread-school-details-container",
                                                className="pagebreak-after",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="iread-ilearn-ela-table",
                                                        children=[],
                                                    ),
                                                    html.Div(
                                                        id="iread-ilearn-math-table",
                                                        children=[],
                                                    ),
                                                ],
                                                id="ilearn-iread-table-container",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="linechart-wida-breakdown",
                                                        children=[],
                                                    ),
                                                ],
                                                id="wida-breakdown-container",
                                                className="pagebreak-after",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="wida-iread-table",
                                                        children=[],
                                                    ),
                                                ],
                                                id="wida-iread-table-container",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="linechart-proficiency-grades-ela",
                                                        children=[],
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        id="stacked-ela-grade-bar-fig"
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
                                                        id="linechart-proficiency-ethnicity-ela",
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
                                                        id="linechart-proficiency-subgroup-ela",
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
                                                        id="linechart-proficiency-ethnicity-math",
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
                                                        id="linechart-proficiency-subgroup-math",
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
                                            html.Div(id="hs-grad-overview-table"),
                                            html.Div(id="hs-grad-ethnicity-table"),
                                            html.Div(id="hs-grad-subgroup-table"),
                                        ],
                                        id="hs-grad-table-container",
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
                                                id="hs-sat-cut-scores-table",
                                                children=[],
                                            ),
                                            html.Div(id="hs-sat-overview-table"),
                                            html.Div(id="hs-sat-ethnicity-table"),
                                            html.Div(id="hs-sat-subgroup-table"),
                                        ],
                                        id="hs-sat-table-container",
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
                                        id="academic-information-notes-string-container",
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
