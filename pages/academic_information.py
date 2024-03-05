#######################################################
# ICSB Dashboard - Academic Information - Proficiency #
#######################################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     02/21/24

# TODO: Break down into three pages: ILEARN; IREAD; WIDA

import dash
from dash import dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import numpy as np
import pandas as pd
from functools import reduce
import re
import itertools

# import local functions
from .load_data import (
    ethnicity,
    subgroup,
    subject,
    grades_all,
    grades,
    grades_ordinal,
    get_school_stns,
    get_iread_student_data,
    get_wida_student_data,
    get_k8_school_academic_data,
    get_high_school_academic_data,
    get_school_index,
    get_excluded_years,
    get_all_the_data
)
from .process_data import (
    process_k8_info_data,
    process_high_school_academic_data,
    filter_high_school_academic_data
)
from .tables import (
    no_data_page,
    create_multi_header_table_with_container,
    create_key_table,
    create_single_header_table,
    create_multi_header_table,
    create_iread_ilearn_table
)
from .charts import no_data_fig_label, make_stacked_bar, make_line_chart
from .layouts import set_table_layout, create_line_fig_layout
from .calculations import round_percentages
from .string_helpers import natural_keys

dash.register_page(
    __name__,
    top_nav=True,
    name="Academic Information",
    path="/academic_information",
    order=7
)


@callback(
    Output("iread-school-level-layout", "children"),
    Output("iread-school-level-layout-container", "style"),
    Output("iread-school-details", "children"),
    Output("iread-school-details-container", "style"),
    Output("wida-breakdown", "children"),
    Output("wida-breakdown-container", "style"),
    Output("wida-iread-table", "children"),
    Output("wida-iread-table-container", "style"),
    Output("iread-ilearn-ela-table", "children"),
    Output("iread-ilearn-math-table", "children"),    
    Output("ilearn-iread-table-container", "style"),        
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
    Output("academic-information-notes-string-container", "style"),   
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

    is_guest = True if selected_school["Guest"].values[0] == "Y" else False

    excluded_years = get_excluded_years(selected_year_string)
    
    if not radio_type:
        radio_type = "k8"

    if not radio_category:
        radio_category = "all"

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

    academic_information_notes_string = ""
    academic_information_notes_string_container = {"display": "none"}
    
    # the default is to display nothing
    main_container = {"display": "none"}
    empty_container = {"display": "block"}
    no_display_data = no_data_page("No Data to Display.", "Academic Information")

    # High School Data
    if (
        selected_school_type == "HS"
        or selected_school_type == "AHS"
        or (selected_school_id == 5874 and selected_year_numeric < 2021)
        or (selected_school_type == "K12" and radio_type == "hs")
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

        # load HS academic data
        selected_raw_hs_school_data = get_high_school_academic_data(school)
        
        # remove excluded years (more recent than selected)
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

            if all_hs_school_data.empty:
                k12_grad_table_container = {"display": "none"}
                k12_sat_table_container = {"display": "none"}
                no_display_data = no_data_page("No Data to Display.", "High School Academic Data")
            
            else:
                main_container = {"display": "block"}
                empty_container = {"display": "none"}

                # Graduation Rate Tables
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

                    # SAT cut score key table
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

                academic_information_notes_string = "Beginning with the 2021-22 SY, SAT replaced ISTEP+ as the state mandated HS assessment. \
                    Beginning with the 2023 cohort, all students in grade 11 are required to take the SAT per federal requirements."
                academic_information_notes_string_container = {"display": "block"}
    # End HS block

    # Begin K8 block
    elif (
        selected_school_type == "K8"
        or (selected_school_type == "K12" and radio_type == "k8")
        or (selected_school_id == 5874 and selected_year_numeric >= 2021)
    ):

        selected_raw_k8_school_data = get_k8_school_academic_data(school)

        if excluded_years:
            selected_raw_k8_school_data = selected_raw_k8_school_data[
                ~selected_raw_k8_school_data["Year"].isin(excluded_years)
            ]

        # NOTE: no ilearn/iread data available for 2020
        if (
            len(selected_raw_k8_school_data.index) > 0
            and selected_year_string != "2020"
        ):

            # this gives us proficiency and N-Size data for ILEARN and IREAD
            # with column names = ["2019School", "2019N-Size", . . . ] -
            # use N-Size data for table tooltips
            ilearn_table_data = process_k8_info_data(selected_raw_k8_school_data)

            if ilearn_table_data.empty:

                #TODO: this necessary here? Container logic?
                # proficiency_ela_grades_container = {"display": "none"}
                # proficiency_ela_ethnicity_container = {"display": "none"}
                # proficiency_ela_subgroup_container = {"display": "none"}
                # proficiency_math_grades_container = {"display": "none"}
                # proficiency_math_ethnicity_container = {"display": "none"}
                # proficiency_math_subgroup_container = {"display": "none"}
                k8_table_container = {"display": "none"}

                no_display_data = no_data_page("No Data to Display.", "Academic Proficiency")
            
            else:

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

                academic_information_notes_string = "ILEARN was administered for the first time during the 2018-19 SY, \
                    representing an entirely new type and mode of assessment (adaptive and online-only). No State assessment \
                    was administered in 2020 due to the Covid-19 pandemic. The students included in the tested cohort for purposes \
                    of calculating the proficiency percentage has not been consistent- in 2019, the cohort included only students \
                    who attended the testing school for 162 days, the 2021 and 2022 calculations included all tested students, regardless \
                    of the length of time that the student attended the testing school, and the 2023 calculation included students in the \
                    cohort of the school in which the student spent the majority of time enrolled."
                
                academic_information_notes_string_container = {"display": "block"}

        # End K-8 ILEARN block
                
# NOTE: Do we want to add classification for "MS" and "ES" ?

        # IREAD - School Level Totals, Ethnicity, & Status
        both = ethnicity + subgroup + ["Total"]
        categories_iread_all = []

        for b in both:
            categories_iread_all.append(b + "|IREAD")

        # get public IREAD data (Total + Ethincity + Subgroup)
        public_iread_school_data = ilearn_table_data[
                ilearn_table_data["Category"].str.contains("|".join(both))
                & ilearn_table_data["Category"].str.contains("IREAD")
        ]

        # no IREAD data (e.g., MS or ES without grade 3)
        # because public data suppresses, it is actually possible (although
        # unlikely) to have no public data, but still have student level data
        
        if public_iread_school_data.empty:

            if radio_category == "iread":
                main_container = {"display": "none"}
                empty_container = {"display": "block"}
                no_display_data = no_data_page("No Data to Display.", "IREAD")
            
            else:
                iread_school_level_layout = []
                iread_school_details = []

        else:
            main_container = {"display": "block"}
            empty_container = {"display": "none"}         

            public_iread_school_table = create_multi_header_table(public_iread_school_data)

            iread_school_fig_data = ilearn_fig_data.loc[
                :,
                (ilearn_fig_data.columns.isin(categories_iread_all))
                | (ilearn_fig_data.columns.isin(["School Name", "Year"]))
            ]

            public_iread_school_fig = make_line_chart(iread_school_fig_data)

            iread_school_level_layout = create_line_fig_layout(
                public_iread_school_table, public_iread_school_fig, "IREAD Breakdown"
            )

            ## get student level IREAD data (ICSB Schools Only)
            iread_student_data = get_iread_student_data(school)

            if excluded_years:
                iread_student_data = iread_student_data[
                    ~iread_student_data["Year"].astype(int).isin(excluded_years)
                ]

            # If school has no student level data (or is a Guest school), hide
            # school details
            if is_guest == True or len(iread_student_data.index) < 1:
                iread_school_details = []
                # iread_student_data = pd.DataFrame()

            else:

                # student level IREAD chart and table
                main_container = {"display": "block"}
                empty_container = {"display": "none"} 
                
                # Group by Year and Period - get percentage passing and not passing
                iread_student_pass = (
                    iread_student_data.groupby(["Year", "Test Period"])[
                        "Status"
                    ]
                    .value_counts(normalize=True)
                    .reset_index(name="Percent")
                )

                # There are potentially six rows for each year: 1) Spring Pass;
                # 2) Spring Did Not Pass; 3) Spring No Result; 4) Summer Pass;
                # 5) Summer Did Not Pass; 6) Summer No Result. However, if, for example,
                # all students were either Pass or Did Not Pass, the opposite row will
                # be missing- e.g., if all students Did Not Pass, there will not be a Pass
                # row for that year and period

                # The solution is to use pd.MultiIndex.from_product. This makes a MultiIndex
                # from the cartesian product of multiple iterables. That is, we get a multindex
                # of all possible combinations from columns by index.levels (in this case, "Year"
                # "Test Period", and "Status" passed to .reindex. Will get a ValueError: "cannot
                # handle a non-unique multi-index" when there are duplicated pairs in the passed
                # columns, so we remove any duplicates first.
                iread_student_mask = iread_student_pass.duplicated(['Year','Test Period','Status'])
                iread_student_pass = iread_student_pass[~iread_student_mask].set_index(['Year','Test Period','Status'])
                iread_student_pass = (iread_student_pass.reindex(pd.MultiIndex.from_product(iread_student_pass.index.levels)).fillna({'Test Period':'Summer', 'Percent':0}).reset_index())

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

                final_iread_student_pass = final_iread_student_pass.rename(
                    columns={"Spring": "Spring Pass %", "Summer": "Summer Pass %"}
                )

                # merge student level data with school total
                iread_total_only = public_iread_school_data[
                    public_iread_school_data["Category"] == "Total|IREAD"
                ]
                
                iread_total_only = iread_total_only.filter(
                    regex=r"School", axis=1
                ).reset_index(drop=True)

                iread_total_only = iread_total_only.T.rename_axis(
                    "Year"
                ).reset_index()

                iread_total_only = iread_total_only.rename(columns={0: "Total|IREAD"})
                iread_total_only["Year"] = iread_total_only["Year"].str[:4]

                # IREAD Details fig
                iread_details_fig_data = pd.merge(
                    final_iread_student_pass, iread_total_only, on=["Year"]
                )

                iread_details_fig_data = iread_details_fig_data.rename(
                    columns={
                        "Total|IREAD": "School Total",
                    }
                )

                iread_details_fig = make_line_chart(iread_details_fig_data)

                # IREAD Details table
                iread_details_table_data = iread_details_fig_data.copy()

                # Combine passing and tested students
                iread_details_table_data = iread_details_table_data.merge(
                    iread_student_tested, on="Year", how="inner"
                )
                iread_details_table_cols = iread_details_table_data.columns.tolist()

                # reorder columns (move "Total" to the end and then swap places of
                # "Summer" and "Spring N-Size")
                iread_details_table_cols.append(
                    iread_details_table_cols.pop(iread_details_table_cols.index("School Total"))
                )
                iread_details_table_cols[2], iread_details_table_cols[-3] = (
                    iread_details_table_cols[-3],
                    iread_details_table_cols[2],
                )

                iread_details_table_data = iread_details_table_data[iread_details_table_cols]

                # Create dataframes for other IREAD data points
                if iread_details_table_data.empty:
                    
                    iread_school_details = []

                #     if not total_iread_data.empty:

                #         iread_school_details = create_simple_iread_layout(total_iread_data)

                #     # else:
                #     #     iread_school_details = []
                #     #     iread_ilearn_ela_table = []
                #     #     iread_ilearn_math_table = []
                # else:
                    
                else:
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

                    # Merge iread table data
                    iread_dfs_to_merge = [
                        iread_details_table_data,
                        iread_grade2_tested,
                        iread_grade2_proficiency,
                        iread_exemptions,
                        iread_advance_no_pass,
                        iread_retained
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
                            "Spring Pass %",
                            "Spring N-Size",
                            "Summer Pass %",
                            "Summer N-Size",
                            "School Total",
                            "2nd Graders Tested",
                            "2nd Graders Proficiency",
                            "No Pass (Exemption)",
                            "No Pass (Advanced)",
                            "No Pass (Retained)",
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
                            if (i == 0) | (i == 2) | (i == 4) | (i == 6) | (i == 14) | (i == 16):
                                if ~np.isnan(iread_final_table_data.iat[i, x]):
                                    iread_final_table_data.iat[i, x] = "{:.2%}".format(iread_final_table_data.iat[i, x])
                            elif (i == 11) | (i == 13):
                                iread_final_table_data.iat[i, x] = "{:,.2f}".format(iread_final_table_data.iat[i, x])
                            else:
                                iread_final_table_data.iat[i, x] = "{:,.0f}".format(iread_final_table_data.iat[i, x])

                    # replace Nan with "-"
                    iread_final_table_data = iread_final_table_data.replace({"nan": "\u2014", np.NaN: "\u2014"}, regex=True)

                    iread_details_table = create_single_header_table(
                        iread_final_table_data, "IREAD"
                    )

                    iread_school_details = create_line_fig_layout(
                        iread_details_table, iread_details_fig, "IREAD Details"
                    )

            # End IREAD Details (student level) block

            # IREAD to ILEARN Table
            if iread_student_data.empty or ilearn_table_data.empty:
                iread_ilearn_ela_table = []
                iread_ilearn_math_table = []

            else:
                iread_ilearn_ela_table = create_iread_ilearn_table(school,"ELA",excluded_years)
                iread_ilearn_math_table = create_iread_ilearn_table(school,"Math",excluded_years)

        # End IREAD Breakdown (school level) block
                    
        ## WIDA - Student Level Data
        # Available WIDA data fields: 'Comprehension Proficiency Level',
        # 'Listening Proficiency Level', 'Literacy Proficiency Level',
        # 'Oral Proficiency Level', 'Reading Proficiency Level',
        # 'Speaking Proficiency Level', 'Writing Proficiency Level'
                            
        # NOTE: Currently only displaying for K-8 Schools - may want to build
        # WIDA table for HS/K12 as well

        # Guests will never have WIDA data 
        if is_guest == True:
            
            if radio_category == "wida":
                main_container = {"display": "none"}
                empty_container = {"display": "block"}
                no_display_data = no_data_page("No Data to Display.", "WIDA")
            
            else:
                wida_iread_details_table = []
                wida_breakdown = []
        else:

            # NOTE: Currently, the WIDA LINK file does not have a School ID column,
            # so we have to get a list of all STNs associated with the school (from
            # both IREAD and ILEARN data files) and then match
            all_stns = get_school_stns(school)

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
                    no_display_data = no_data_page("No Data to Display.", "WIDA")
                
                else:
                    wida_iread_details_table = []
                    wida_breakdown = []

            else:
                main_container = {"display": "block"}
                empty_container = {"display": "none"}

                # Get WIDA average per grade by year
                wida_avg_per_grade = (
                    wida_student_data.groupby(["Year", "Tested Grade"])[
                        "Composite Overall Proficiency Level"
                    ]
                    .mean()
                    .reset_index(name="Average")
                )

                # get WIDA total school average by year
                wida_avg_total = (
                    wida_student_data.groupby(["Year"])[
                        "Composite Overall Proficiency Level"
                    ]
                    .mean()
                    .reset_index(name="Average")
                )

                # Drop data for AHS students
                wida_avg_per_grade = wida_avg_per_grade.loc[
                    wida_avg_per_grade["Tested Grade"] != "Grade 12+/Adult"
                ]

                # pivot to show average WIDA schore by grade (col) by year (row)
                wida_breakdown_fig_data = (
                    wida_avg_per_grade.pivot_table(
                        index=["Year"], columns="Tested Grade", values="Average"
                    )
                    .reset_index()
                    .rename_axis(None, axis=1)
                )

                # temporarily store and drop Year col
                wida_breakdown_year_col = wida_breakdown_fig_data["Year"]
                wida_breakdown_fig_data = wida_breakdown_fig_data.drop(["Year"], axis=1)

                # reindex and sort columns using only the numerical part
                wida_breakdown_fig_data = wida_breakdown_fig_data.reindex(
                    sorted(wida_breakdown_fig_data.columns, key=lambda x: float(x[6:])),
                    axis=1,
                )

                # add Year col back
                wida_breakdown_fig_data.insert(loc=0, column="Year", value = wida_breakdown_year_col)

                # Add school Average to by year calcs
                wida_breakdown_fig_data = pd.merge(wida_breakdown_fig_data, wida_avg_total, on="Year")

                # Get N-Size for each grade for each year and add to table data
                wida_school_nsize_data = wida_student_data.value_counts(["Tested Grade","Year"]).reset_index().rename(columns={0: "N-Size"})
                wida_breakdown_nsize = pd.merge(wida_avg_per_grade, wida_school_nsize_data, on=["Year","Tested Grade"])

                # put nsize data in same format as scores
                wida_breakdown_nsize = wida_breakdown_nsize.drop("Average", axis = 1)

                wida_breakdown_nsize = (
                    wida_breakdown_nsize.pivot_table(
                        index=["Year"], columns="Tested Grade", values="N-Size"
                    )
                    .reset_index()
                    .rename_axis(None, axis=1)
                )

                # identify year columns to get totals (named Average to match
                # scores df col name)
                wida_nsize_years = [c for c in wida_breakdown_nsize.columns if "Grade" in c]
                wida_breakdown_nsize["Average"] = wida_breakdown_nsize[wida_nsize_years].sum(axis=1)

                # sort nsize columns to match data dataframe (using natural sort)
                wida_nsize_years.sort(key=natural_keys)
                wida_nsize_columns_sorted = ["Year"] + wida_nsize_years + ["Average"]
                wida_breakdown_nsize = wida_breakdown_nsize[wida_nsize_columns_sorted]

                # should not have negative values, but bad data causes them to
                # appear from time to time
                wida_breakdown_fig_data[wida_breakdown_fig_data < 0] = np.NaN

                # Create line chart for WIDA Scores by Grade and Total
                wida_breakdown_fig = make_line_chart(wida_breakdown_fig_data)

                wida_breakdown_table_data = (
                    wida_breakdown_fig_data.set_index("Year")
                    .T.rename_axis("Category")
                    .rename_axis(None, axis=1)
                    .reset_index()
                )

                wida_breakdown_nsize = (
                    wida_breakdown_nsize.set_index("Year")
                    .T.rename_axis("Category")
                    .rename_axis(None, axis=1)
                    .reset_index()
                )

                # clean and format table data
                wida_breakdown_nsize.columns = wida_breakdown_nsize.columns.astype(str)
                wida_breakdown_nsize.columns = ["Category"] + [str(col) + 'N-Size' for col in wida_breakdown_nsize.columns if "Category" not in col]
                wida_breakdown_table_data.columns = wida_breakdown_table_data.columns.astype(str)
                wida_breakdown_nsize.columns = ["Category"] + [str(col) + 'School' for col in wida_breakdown_nsize.columns if "Category" not in col]

                for col in wida_breakdown_table_data.columns[1:]:
                    wida_breakdown_table_data[col] = pd.to_numeric(wida_breakdown_table_data[col], errors="coerce")

                wida_breakdown_table_data = wida_breakdown_table_data.set_index("Category")

                wida_breakdown_table_data = wida_breakdown_table_data.applymap("{:.2f}".format)
                wida_breakdown_table_data = wida_breakdown_table_data.reset_index()

                wida_breakdown_table_data = wida_breakdown_table_data.replace({"nan": "\u2014", np.NaN: "\u2014"}, regex=True) # add dash

                # merge nsize data into data to get into the format
                # expected by multi_table function

                # interweave columns and add category back
                wida_data_columns = [e for e in wida_breakdown_table_data.columns if "Category" not in e]
                wida_nsize_columns = [e for e in wida_breakdown_nsize.columns if "Category" not in e]
                wida_final_columns = list(itertools.chain(*zip(wida_data_columns, wida_nsize_columns)))
                wida_final_columns.insert(0, "Category")

                # merge and re-order using wida_final_columns
                wida_breakdown_data = pd.merge(wida_breakdown_table_data, wida_breakdown_nsize, on="Category")

                wida_breakdown_data = wida_breakdown_data[wida_final_columns]

                wida_breakdown_table = create_multi_header_table(wida_breakdown_data)

                wida_breakdown = create_line_fig_layout(
                    wida_breakdown_table, wida_breakdown_fig, "WIDA Breakdown"
                )

                ## WIDA to IREAD table
                        
                # we are still in the wida_student_data block, but we need
                # both wida and iread student level dataframes to have data
                # in order to produce table
                if iread_student_data.empty:
                    wida_iread_details_table = []

                else:

                    main_container = {"display": "block"}
                    empty_container = {"display": "none"}

                    all_stns = get_school_stns(school)
                    # all_stns["STN"] = all_stns["STN"].astype(str)
                    wida_student_data["STN"] = wida_student_data["STN"].astype(str)

                    # NOTE: For many schools the number of students (STNs) with
                    # both IREAD and WIDA data will be small.
                    wida_comp_data = wida_student_data[["STN", "Year", "Composite Overall Proficiency Level"]].copy()
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
                    wida_iread_current_match = pd.merge(iread_comp_data, wida_comp_data, on=["STN","Year"])

                    # need to differentiate between years when not merging on Year
                    iread_comp_data = iread_comp_data.rename(columns={"Year": "IREAD Year"})
                    wida_comp_data = wida_comp_data.rename(columns={"Year": "WIDA Year"})

                    # find STNs where WIDA tested year < IREAD Year
                    wida_iread_prior_match = pd.merge(iread_comp_data, wida_comp_data, on=["STN"])

                    # Find Max WIDA Year value for each STN
                    wida_year_max = wida_iread_prior_match.groupby(['STN'])['WIDA Year'].max().reset_index(name="WIDA Max")

                    # drop duplicates from the full data set (where the same STN can appear
                    # up to 5 times) and merge with WIDA Max to add IREAD Year
                    wida_iread_prior_match = wida_iread_prior_match.drop_duplicates(subset=['STN'], keep='last')
                    wida_year_max = pd.merge(wida_year_max,wida_iread_prior_match,on=["STN"], how="left")

                    # filter by STNs where IREAD Year is > then WIDA Max Year
                    wida_stn_to_add = wida_year_max[wida_year_max["IREAD Year"].astype(int) > \
                        wida_year_max["WIDA Max"].astype(int)]

                    # Merge the prior and current testers into one df
                    if not wida_stn_to_add.empty:

                        # change column names to match
                        wida_stn_to_add = wida_stn_to_add.drop(["WIDA Max", "WIDA Year"], axis=1)
                        wida_stn_to_add = wida_stn_to_add.rename(columns={"IREAD Year": "Year"})

                        wida_iread_details_data = pd.concat([wida_iread_current_match, wida_stn_to_add])
                    
                    else:
                        wida_iread_details_data = wida_iread_current_match

                    if wida_iread_details_data.empty:
                        wida_iread_details_table = []

                    else:

                        # Get WIDA Average by Year and Status (Pass/No Pass)
                        wida_iread_details_avg = (
                            wida_iread_details_data.groupby(["Year","Status"])["Composite Overall Proficiency Level"]
                            .mean()
                            .reset_index(name="Average")
                        )

                        # Get N-Size for each Year and category (Pass/No Pass)
                        wida_iread_details_nsize = (
                            wida_iread_details_data.groupby("Year")["Status"]
                            .value_counts()
                            .reset_index(name="N-Size")
                        )

                        # Merge to add N-Size to WIDA Average df
                        wida_iread_details_final = pd.merge(wida_iread_details_avg, wida_iread_details_nsize, on=["Year","Status"])

                        wida_details_nopass = wida_iread_details_final[wida_iread_details_final["Status"] == "Did Not Pass"]
                        wida_details_pass = wida_iread_details_final[wida_iread_details_final["Status"] == "Pass"]

                        wida_details_pass = wida_details_pass.rename(columns={
                            "Average": "Avg. WIDA for Students Passing IREAD",
                            "N-Size": "# of WIDA Tested Students Passing IREAD"})
                        wida_details_nopass = wida_details_nopass.rename(columns={
                            "Average": "Avg. WIDA for Students Not Passing IREAD",
                            "N-Size": "# of WIDA Tested Students Not Passing IREAD"})

                        # prepare to combine
                        wida_details_nopass = wida_details_nopass.drop(["Year","Status"], axis=1)
                        wida_details_pass = wida_details_pass.drop("Status", axis=1)
                        wida_details_pass = wida_details_pass.reset_index(drop=True)
                        wida_details_nopass = wida_details_nopass.reset_index(drop=True)

                        wida_iread_details_table_data = pd.concat([wida_details_pass, wida_details_nopass], axis=1)

                        for col in wida_iread_details_table_data.columns[1:]:
                            wida_iread_details_table_data[col] = pd.to_numeric(wida_iread_details_table_data[col], errors="coerce")

                        wida_iread_details_nsize = wida_iread_details_table_data["# of WIDA Tested Students Passing IREAD"].fillna(0) + \
                            wida_iread_details_table_data["# of WIDA Tested Students Not Passing IREAD"].fillna(0)

                        wida_iread_details_table_data["N-Size"] = wida_iread_details_nsize
                        wida_iread_details_table_data["% of WIDA Tested Students Passing IREAD"] = \
                            wida_iread_details_table_data["# of WIDA Tested Students Passing IREAD"] / wida_iread_details_nsize

                        wida_iread_details_table_data = wida_iread_details_table_data.drop(["# of WIDA Tested Students Passing IREAD", 
                            "# of WIDA Tested Students Not Passing IREAD"], axis=1)
                        
                        wida_iread_details_table_data=wida_iread_details_table_data[["Year","% of WIDA Tested Students Passing IREAD",
                            "Avg. WIDA for Students Passing IREAD", "Avg. WIDA for Students Not Passing IREAD","N-Size"]]
                        
                        wida_iread_details_table_data = (
                            wida_iread_details_table_data.set_index("Year")
                            .T.rename_axis("Category")
                            .rename_axis(None, axis=1)
                            .reset_index()
                        )

                        # table format
                        for x in range(1, len(wida_iread_details_table_data.columns)):
                            for i in range(0, len(wida_iread_details_table_data.index)):
                                if (i == 0):
                                    if ~np.isnan(wida_iread_details_table_data.iat[i, x]):
                                        wida_iread_details_table_data.iat[i, x] = "{:.2%}".format(wida_iread_details_table_data.iat[i, x])                                
                                elif (i == 1) | (i == 2):
                                    wida_iread_details_table_data.iat[i, x] = "{:,.2f}".format(wida_iread_details_table_data.iat[i, x])
                                else:
                                    wida_iread_details_table_data.iat[i, x] = "{:,.0f}".format(wida_iread_details_table_data.iat[i, x])

                        # replace Nan with "-"
                        wida_iread_details_table_data = wida_iread_details_table_data.replace({"nan": "\u2014", np.NaN: "\u2014"}, regex=True)

                        wida_iread_details_table = create_single_header_table(
                            wida_iread_details_table_data, "WIDA Details"
                        )

                # End WIDA to IREAD Table
        # End WIDA Breakdown (School Level) block
                                            
# TODO: Add 2 year ILEARN comparisons (YoY comparing STN)
# TODO: but still need Test Year column in ILEARN data
# Get total # of students for each grade for each year
# Calculate Proficiency for each year for each grade ->
#   # students / # At or Above
#   # students / # Approaching
#   for IREAD Passing Students and IREAD not passing students
# % Proficiency for students not passing IREAD
# % Proficiency for students passing IREAD

# # Avg ELA/Math over time for IREAD Pass - 2018-19, 21, 22, 23
# # group by IREAD Pass and ILEARN Year:
# # a) count Exceeds, At, Approach, Below
# # b) measure point diff between Cut and Scale and Average
# # c) measure raw scale score avg
# # Avg ELA over time for IREAD No Pass

        # category selection determines which divs are displayed
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
            k12_sat_table_container = {"display": "none"}
            k12_grad_table_container = {"display": "none"}
                
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
            k12_sat_table_container = {"display": "none"}
            k12_grad_table_container = {"display": "none"}

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
            k12_sat_table_container = {"display": "none"}
            k12_grad_table_container = {"display": "none"}

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
            k12_sat_table_container = {"display": "none"}
            k12_grad_table_container = {"display": "none"}
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
            k12_sat_table_container = {"display": "none"}
            k12_grad_table_container = {"display": "none"}
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
            k8_table_container = {"display": "block"}
            
            k12_sat_table_container = {"display": "none"}
            k12_grad_table_container = {"display": "none"}

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
        academic_information_notes_string_container
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
                                                        id="iread-school-level-layout",
                                                        children=[],
                                                    ),
                                                ],
                                                id="iread-school-level-layout-container",
                                                className="pagebreak-after",
                                            ),                                            
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="iread-school-details",
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
                                                        id="wida-iread-table",
                                                        children=[],
                                                    ),
                                                ],
                                                id="wida-iread-table-container",
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
                                        id="academic-information-notes-string-container",
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