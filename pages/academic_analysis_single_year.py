####################################################
# ICSB Dashboard - Academic Analysis - Single Year #
####################################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.16
# date:     12/29/24

import dash
from dash import ctx, dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd

from .globals import ethnicity, subgroup, ethnicity, color

from .load_data import (
    get_school_index,
    get_academic_data,
    current_academic_year,
)
from .clean_data import clean_academic_data
from .process_data import create_comparison_dropdown_list
from .charts import (
    no_data_fig_label,
    make_bar_chart,
    make_group_bar_chart
)
from .tables import (
    create_comparison_table,
    create_empty_page_layout,
    create_empty_table_layout,
)
from .layouts import create_barchart_layout, create_hs_analysis_layout
from .string_helpers import (
    create_school_label,
    combine_school_name_and_grade_levels,
    create_chart_label,
    identify_missing_categories,
    generate_colors,
)

dash.register_page(
    __name__,
    name="Single Year Analysis",
    path="/academic_analysis_single_year",
    top_nav=True,
    order=10,
)


# Comparison school dropdown
@callback(
    Output("analysis-single-comparison-dropdown", "options"),
    Output("single-year-input-warning", "children"),
    Output("analysis-single-comparison-dropdown", "value"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("analysis-single-comparison-dropdown", "value"),
    Input("academic-type-radio", "value"),
)
def set_dropdown_options(
    school_id: str,
    year: str,
    existing_comparison_schools_list: list,
    academic_type_value: str,
):
    if not year:
        year = current_academic_year

    # clear the list of comparison_schools when a new school is
    # selected, otherwise comparison_schools will carry over
    input_trigger = ctx.triggered_id
    if input_trigger == "charter-dropdown":
        existing_comparison_schools_list = []

    selected_school = get_school_index(school_id)
    selected_school_type = selected_school["School Type"].values[0]

    if selected_school_type == "k12":
        if academic_type_value == "hs":
            selected_school_type = "hs"
        else:
            selected_school_type = "k8"

    (
        school_options,
        input_warning,
        comparison_schools,
    ) = create_comparison_dropdown_list(
        school_id, year, existing_comparison_schools_list, academic_type_value
    )

    return school_options, input_warning, comparison_schools


@callback(
    Output("trace-color-state-single", "data"),
    Output("analysis-single-dropdown-container", "style"),
    Output("fig14c", "children"),
    Output("fig14d", "children"),
    Output("fig-iread", "children"),
    Output("fig16a1", "children"),
    Output("fig16a1-container", "style"),
    Output("fig16c1", "children"),
    Output("fig16c1-container", "style"),
    Output("fig16b1", "children"),
    Output("fig16b1-container", "style"),
    Output("fig16a2", "children"),
    Output("fig16a2-container", "style"),
    Output("fig16c2", "children"),
    Output("fig16c2-container", "style"),
    Output("fig16b2", "children"),
    Output("fig16b2-container", "style"),
    Output("k8-analysis-single-main-container", "style"),
    Output("k8-analysis-single-empty-container", "style"),
    Output("k8-analysis-single-no-data", "children"),
    Output("grad-overview", "children"),
    Output("grad-overview-container", "style"),
    Output("grad-ethnicity", "children"),
    Output("grad-ethnicity-container", "style"),
    Output("grad-subgroup", "children"),
    Output("grad-subgroup-container", "style"),
    Output("sat-overview", "children"),
    Output("sat-overview-container", "style"),
    Output("sat-ethnicity-ebrw", "children"),
    Output("sat-ethnicity-math", "children"),
    Output("sat-ethnicity-container", "style"),
    Output("sat-subgroup-ebrw", "children"),
    Output("sat-subgroup-math", "children"),
    Output("sat-subgroup-container", "style"),
    Output("hs-analysis-single-main-container", "style"),
    Output("hs-analysis-single-empty-container", "style"),
    Output("hs-analysis-single-no-data", "children"),
    Output("single-year-analysis-notes", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("academic-type-radio", "value"),
    [Input("analysis-single-comparison-dropdown", "value")],
    Input("trace-color-state-single", "data"),
)
def update_academic_analysis_single_year(
    school_id: str,
    year: str,
    academic_type_value: str,
    comparison_school_list: list,
    trace_color_state: dict,
):
    if not school_id:
        raise PreventUpdate

    string_year = year
    numeric_year = int(string_year)

    selected_school = get_school_index(school_id)
    selected_school_type = selected_school["School Type"].values[0]

    # Christel House South Exception
    # NOTE: need this on every page because school type is stored
    # in db and thus gets reset each time get_school_index is
    # accessed. may want to explore better way to handle type
    if int(school_id) == 5874 and numeric_year < 2021:
        selected_school_type = "k12"

    school_name = selected_school["School Name"].values[0]
    school_name = school_name.strip()

    if not academic_type_value:
        academic_type_value = "k8"

    if not trace_color_state:
        trace_color_state = {}

    combined_selected_data = pd.DataFrame()

    hs_analysis_main_container = {"display": "none"}
    hs_analysis_empty_container = {"display": "none"}
    k8_analysis_main_container = {"display": "none"}
    k8_analysis_empty_container = {"display": "block"}

    fig14c = []
    fig14d = []
    fig_iread = []
    fig16a1 = []
    fig16a1_container = {"display": "none"}
    fig16b1 = []
    fig16b1_container = {"display": "none"}
    fig16c1 = []
    fig16c1_container = {"display": "none"}
    fig16a2 = []
    fig16a2_container = {"display": "none"}
    fig16b2 = []
    fig16b2_container = {"display": "none"}
    fig16c2 = []
    fig16c2_container = {"display": "none"}
    analysis_single_dropdown_container = {"display": "none"}

    grad_overview = []
    grad_overview_container = {"display": "none"}
    grad_ethnicity = []
    grad_ethnicity_container = {"display": "none"}
    grad_subgroup = []
    grad_subgroup_container = {"display": "none"}
    sat_overview = []
    sat_overview_container = {"display": "none"}
    sat_ethnicity_ebrw = []
    sat_ethnicity_math = []
    sat_ethnicity_container = {"display": "none"}
    sat_subgroup_ebrw = []
    sat_subgroup_math = []
    sat_subgroup_container = {"display": "none"}

    k8_analysis_no_data = create_empty_page_layout(
        "Comparison Data - K-8 Academic Data", "No Data to Display."
    )
    hs_analysis_no_data = create_empty_page_layout(
        "Comparison Data - High School Academic Data", "No Data to Display."
    )

    academic_analysis_notes_label = ""
    academic_analysis_notes_string = ""

    if (
        selected_school_type == "hs"
        or selected_school_type == "ahs"
        or (selected_school_type == "k12" and academic_type_value == "hs")
    ):
        k8_analysis_empty_container = {"display": "none"}

        academic_analysis_notes_label = "Comparison Data - High School"
        academic_analysis_notes_string = "Use this page to view SAT and Graduation Rate comparison data for all ethnicities, \
            and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
            the selected school. Up to eight (8) schools may be displayed at once."

        if selected_school_type == "k12":
            school_type = "hs"
        else:
            school_type = selected_school_type

        list_of_schools = [school_id] + comparison_school_list
        raw_hs_analysis_data = get_academic_data(list_of_schools, school_type)

        clean_hs_analysis_data = clean_academic_data(
            raw_hs_analysis_data, list_of_schools, school_type, numeric_year, "analysis"
        )

        hs_analysis_data = clean_hs_analysis_data.loc[
            clean_hs_analysis_data["Year"] == numeric_year
        ].copy()

        if hs_analysis_data.empty:
            analysis_single_dropdown_container = {"display": "none"}
            hs_analysis_empty_container = {"display": "block"}

        else:
            hs_school_name = hs_analysis_data[
                hs_analysis_data["School ID"] == int(school_id)
            ]["School Name"].values[0]
            hs_school_name = hs_school_name.strip()

            hs_cols = [c for c in hs_analysis_data if c != "School Name"]

            for col in hs_cols:
                hs_analysis_data[col] = pd.to_numeric(
                    hs_analysis_data[col], errors="coerce"
                )

            # drop all columns where the row at school_name_idx has a NaN value
            school_name_idx = hs_analysis_data.index[
                hs_analysis_data["School Name"].str.contains(hs_school_name)
            ].tolist()[0]

            hs_analysis_data = hs_analysis_data.loc[
                :, ~hs_analysis_data.iloc[school_name_idx].isna()
            ].copy()

            # check to see if there is data after processing
            if len(hs_analysis_data.columns) <= 5:
                analysis_single_dropdown_container = {"display": "none"}
                hs_analysis_empty_container = {"display": "block"}

            else:
                hs_analysis_main_container = {"display": "block"}
                hs_analysis_empty_container = {"display": "none"}

                # this keeps trace colors consistent when schools are added or removed
                trace_colors = generate_colors(
                    hs_analysis_data, trace_color_state, color, school_name
                )

                ## Graduation Comparison Sets
                grad_overview_categories = ["Total", "NonWaiver"]

                grad_overview = create_hs_analysis_layout(
                    "Graduation Rate",
                    hs_analysis_data,
                    grad_overview_categories,
                    school_id,
                    trace_colors,
                )

                grad_ethnicity = create_hs_analysis_layout(
                    "Graduation Rate",
                    hs_analysis_data,
                    ethnicity,
                    school_id,
                    trace_colors,
                )

                grad_subgroup = create_hs_analysis_layout(
                    "Graduation Rate",
                    hs_analysis_data,
                    subgroup,
                    school_id,
                    trace_colors,
                )

                ## SAT Comparison Sets
                overview = [
                    "Total|Math",
                    "Total|EBRW",
                ]

                sat_overview = create_hs_analysis_layout(
                    "Total", hs_analysis_data, overview, school_id, trace_colors
                )

                sat_ethnicity_ebrw = create_hs_analysis_layout(
                    "EBRW", hs_analysis_data, ethnicity, school_id, trace_colors
                )

                sat_ethnicity_math = create_hs_analysis_layout(
                    "Math", hs_analysis_data, ethnicity, school_id, trace_colors
                )

                sat_subgroup_ebrw = create_hs_analysis_layout(
                    "EBRW", hs_analysis_data, subgroup, school_id, trace_colors
                )

                sat_subgroup_math = create_hs_analysis_layout(
                    "Math", hs_analysis_data, subgroup, school_id, trace_colors
                )

                # Display Logic - Grad data / SAT data
                if not grad_overview and not grad_ethnicity and not grad_subgroup:
                    grad_overview = no_data_fig_label(
                        "Comparison: Graduation Rates", 200, "pretty"
                    )
                    grad_overview_container = {"display": "block"}
                else:
                    analysis_single_dropdown_container = {"display": "block"}

                    if grad_overview:
                        grad_overview_container = {"display": "block"}
                    else:
                        grad_overview = no_data_fig_label(
                            "Comparison: Total/Non Waiver Graduation Rate",
                            200,
                            "pretty",
                        )
                        grad_overview_container = {"display": "block"}

                    if grad_ethnicity:
                        grad_ethnicity_container = {"display": "block"}
                    else:
                        grad_ethnicity = no_data_fig_label(
                            "Comparison: Graduation Rate by Ethnicity", 200, "pretty"
                        )
                        grad_ethnicity_container = {"display": "block"}

                    if grad_subgroup:
                        grad_subgroup_container = {"display": "block"}
                    else:
                        grad_subgroup = no_data_fig_label(
                            "Comparison: Graduation Rate by Subgroup", 200, "pretty"
                        )
                        grad_subgroup_container = {"display": "block"}

                if (
                    not sat_overview
                    and not sat_ethnicity_ebrw
                    and not sat_ethnicity_math
                    and not sat_subgroup_ebrw
                    and not sat_subgroup_math
                ):
                    sat_overview = no_data_fig_label(
                        f"Comparison: % of Students At Benchmark (SAT)", 200, "pretty"
                    )
                    sat_overview_container = {"display": "block"}
                else:
                    analysis_single_dropdown_container = {"display": "block"}

                    if sat_overview:
                        sat_overview_container = {"display": "block"}
                    else:
                        sat_overview = no_data_fig_label(
                            "Comparison: SAT At Benchmark School Total ", 200, "pretty"
                        )
                        sat_overview_container = {"display": "block"}

                    if sat_ethnicity_math or sat_ethnicity_ebrw:
                        if not sat_ethnicity_ebrw:
                            sat_ethnicity_ebrw = no_data_fig_label(
                                "Comparison: SAT At Benchmark by Ethnicity (EBRW)",
                                200,
                                "pretty",
                            )

                        if not sat_ethnicity_math:
                            sat_ethnicity_math = no_data_fig_label(
                                "Comparison: SAT At Benchmark by Ethnicity (Math)",
                                200,
                                "pretty",
                            )

                        sat_ethnicity_container = {"display": "block"}

                    else:
                        sat_ethnicity_container = {"display": "none"}

                    if sat_subgroup_math or sat_subgroup_ebrw:
                        if not sat_subgroup_ebrw:
                            sat_subgroup_ebrw = no_data_fig_label(
                                "Comparison: SAT At Benchmark by Subgroup (EBRW)",
                                200,
                                "pretty",
                            )

                        if not sat_subgroup_math:
                            sat_subgroup_math = no_data_fig_label(
                                "Comparison: SAT At Benchmark by Subgroup (Math)",
                                200,
                                "pretty",
                            )

                        sat_subgroup_container = {"display": "block"}
                    else:
                        sat_subgroup_container = {"display": "none"}

    if selected_school_type == "k8" or selected_school_type == "k12":
        if selected_school_type == "k12" and academic_type_value == "hs":
            k8_analysis_main_container = {"display": "none"}

        else:
            # set K12 school type to K8
            school_type = "k8"

            academic_analysis_notes_label = "Comparison Data - K-8"
            academic_analysis_notes_string = "Use this page to view ILEARN proficiency comparison data \
                for all grades, ethnicities, and subgroups. The dropdown list consists of the twenty (20) \
                closest schools that overlap at least two grades with the selected school. Up to eight (8) \
                schools may be displayed at once."

            # make sure selected school_id is first in list
            list_of_schools = [school_id] + comparison_school_list

            raw_k8_analysis_data = get_academic_data(list_of_schools, school_type)

            clean_k8_analysis_data = clean_academic_data(
                raw_k8_analysis_data,
                list_of_schools,
                school_type,
                numeric_year,
                "analysis",
            )

            k8_analysis_data = clean_k8_analysis_data.loc[
                clean_k8_analysis_data["Year"] == numeric_year
            ].copy()
            k8_analysis_data = k8_analysis_data.reset_index(drop=True)

            numeric_columns = [
                col
                for col in k8_analysis_data.columns.to_list()
                if col not in ["School Name", "School ID", "Low Grade", "High Grade"]
            ]

            for col in numeric_columns:
                k8_analysis_data[col] = pd.to_numeric(
                    k8_analysis_data[col], errors="coerce"
                )

            k8_analysis_data = k8_analysis_data.reset_index(drop=True)

            school_idx = k8_analysis_data.index[
                k8_analysis_data["School ID"] == school_id
            ].tolist()[0]

            combined_selected_data = k8_analysis_data.loc[
                :, ~k8_analysis_data.iloc[school_idx].isna()
            ].copy()

            combined_selected_data = combined_selected_data.reset_index(drop=True)

            # there are 6 "information" columns- having 6 or fewer means no
            # academic data
            if len(combined_selected_data.columns) <= 6:
                k8_analysis_main_container = {"display": "none"}
                k8_analysis_empty_container = {"display": "block"}

            else:
                k8_analysis_main_container = {"display": "block"}
                k8_analysis_empty_container = {"display": "none"}
                analysis_single_dropdown_container = {"display": "block"}

                # add the information categories back to each dataframe
                added_categories = [
                    "School Name",
                    "School ID",
                    "Low Grade",
                    "High Grade",
                ]

                # this keeps trace colors consistent when schools are added or removed
                trace_colors = generate_colors(
                    combined_selected_data, trace_color_state, color, school_name
                )

                ## Current Year ELA Proficiency Compared to Similar Schools (1.4.c) ##
                category = "Total|ELA Proficient %"

                # Get school value for specific category
                if category in combined_selected_data.columns:
                    fig14c_all_data = combined_selected_data[
                        added_categories + [category]
                    ].copy()

                    fig14c_table_data = fig14c_all_data.copy()

                    fig14c_all_data[category] = pd.to_numeric(fig14c_all_data[category])

                    fig14c_chart = make_bar_chart(
                        fig14c_all_data,
                        category,
                        school_id,
                        trace_colors,
                        "Comparison: Current Year ELA Proficiency",
                    )

                    fig14c_table_data["School Name"] = create_school_label(
                        fig14c_table_data
                    )
                    fig14c_table_data = fig14c_table_data[
                        ["School Name", "School ID", category]
                    ]
                    fig14c_table_data = fig14c_table_data.reset_index(drop=True)

                    fig14c_table = create_comparison_table(
                        fig14c_table_data, trace_colors, school_id
                    )
                else:
                    fig14c_chart = no_data_fig_label(
                        "Comparison: Current Year ELA Proficiency", 200
                    )
                    fig14c_table = create_empty_table_layout(
                        "ELA Proficiency", "No Data to Display.", "none"
                    )

                fig14c = create_barchart_layout(fig14c_chart, fig14c_table, "", "")

                ## Current Year Math Proficiency Compared to Similar Schools (1.4.d) ##
                category = "Total|Math Proficient %"

                if category in combined_selected_data.columns:
                    fig14d_all_data = combined_selected_data[
                        added_categories + [category]
                    ].copy()

                    fig14d_table_data = fig14d_all_data.copy()

                    fig14d_all_data[category] = pd.to_numeric(fig14d_all_data[category])

                    fig14d_chart = make_bar_chart(
                        fig14d_all_data,
                        category,
                        school_id,
                        trace_colors,
                        "Comparison: Current Year Math Proficiency",
                    )

                    fig14d_table_data["School Name"] = create_school_label(
                        fig14d_table_data
                    )

                    fig14d_table_data = fig14d_table_data[
                        ["School Name", "School ID", category]
                    ]
                    fig14d_table_data = fig14d_table_data.reset_index(drop=True)

                    fig14d_table = create_comparison_table(
                        fig14d_table_data, trace_colors, school_id
                    )

                else:
                    fig14d_chart = no_data_fig_label(
                        "Comparison: Current Year Math Proficiency", 200
                    )
                    fig14d_table = create_empty_table_layout(
                        "Math Proficiency", "No Data to Display.", "none"
                    )

                fig14d = create_barchart_layout(fig14d_chart, fig14d_table, "", "")

                ## Current Year IREAD Proficiency Compared to Similar Schools ##
                category = "Total|IREAD Proficient %"

                if category in combined_selected_data.columns:
                    fig_iread_all_data = combined_selected_data[
                        added_categories + [category]
                    ].copy()

                    fig_iread_table_data = fig_iread_all_data.copy()

                    fig_iread_all_data[category] = pd.to_numeric(
                        fig_iread_all_data[category]
                    )

                    fig_iread_chart = make_bar_chart(
                        fig_iread_all_data,
                        category,
                        school_id,
                        trace_colors,
                        "Comparison: Current Year IREAD Proficiency",
                    )

                    fig_iread_table_data["School Name"] = create_school_label(
                        fig_iread_table_data
                    )

                    fig_iread_table_data = fig_iread_table_data[
                        ["School Name", "School ID", category]
                    ]
                    fig_iread_table_data = fig_iread_table_data.reset_index(drop=True)

                    fig_iread_table = create_comparison_table(
                        fig_iread_table_data, trace_colors, school_id
                    )

                    fig_iread = create_barchart_layout(
                        fig_iread_chart, fig_iread_table, "", ""
                    )

                else:
                    fig_iread_chart = []
                    fig_iread_table = []

                ## ELA Proficiency by Ethnicity Compared to Similar Schools (1.6.a.1) ##
                headers_16a1 = []
                for e in ethnicity:
                    headers_16a1.append(e + "|" + "ELA Proficient %")

                categories_16a1 = added_categories + headers_16a1

                fig16a1_final_data = combined_selected_data.loc[
                    :, (combined_selected_data.columns.isin(categories_16a1))
                ]

                if len(fig16a1_final_data.columns) > 4:
                    (
                        fig16a1_final_data,
                        fig16a1_category_string,
                        fig16a1_school_string,
                    ) = identify_missing_categories(fig16a1_final_data, categories_16a1)

                    fig16a1_label = create_chart_label(fig16a1_final_data)
                    fig16a1_chart = make_group_bar_chart(
                        fig16a1_final_data, school_id, trace_colors, fig16a1_label
                    )
                    fig16a1_table_data = combine_school_name_and_grade_levels(
                        fig16a1_final_data
                    )
                    fig16a1_table = create_comparison_table(
                        fig16a1_table_data, trace_colors, school_id
                    )

                    fig16a1 = create_barchart_layout(
                        fig16a1_chart,
                        fig16a1_table,
                        fig16a1_category_string,
                        fig16a1_school_string,
                    )

                    fig16a1_container = {"display": "block"}
                    analysis_single_dropdown_container = {"display": "block"}

                else:
                    fig16a1 = no_data_fig_label(
                        "Comparison: ELA Proficiency by Ethnicity", 200
                    )
                    fig16a1_container = {"display": "none"}

                ## IREAD Proficiency by Ethnicity Compared to Similar Schools ##
                headers_16b1 = []
                for e in ethnicity:
                    headers_16b1.append(e + "|" + "IREAD Proficient %")

                categories_16b1 = added_categories + headers_16b1

                fig16b1_final_data = combined_selected_data.loc[
                    :, (combined_selected_data.columns.isin(categories_16b1))
                ]

                if len(fig16b1_final_data.columns) > 4:
                    (
                        fig16b1_final_data,
                        fig16b1_category_string,
                        fig16b1_school_string,
                    ) = identify_missing_categories(fig16b1_final_data, categories_16b1)

                    fig16b1_label = create_chart_label(fig16b1_final_data)
                    fig16b1_chart = make_group_bar_chart(
                        fig16b1_final_data, school_id, trace_colors, fig16b1_label
                    )
                    fig16b1_table_data = combine_school_name_and_grade_levels(
                        fig16b1_final_data
                    )

                    fig16b1_table = create_comparison_table(
                        fig16b1_table_data, trace_colors, school_id
                    )

                    fig16b1 = create_barchart_layout(
                        fig16b1_chart,
                        fig16b1_table,
                        fig16b1_category_string,
                        fig16b1_school_string,
                    )

                    fig16b1_container = {"display": "block"}
                    analysis_single_dropdown_container = {"display": "block"}

                else:
                    fig16b1 = no_data_fig_label(
                        "Comparison: IREAD Proficiency by Ethnicity", 200
                    )
                    fig16b1_container = {"display": "none"}

                ## Math Proficiency by Ethnicity Compared to Similar Schools (1.6.b.1) ##
                headers_16c1 = []
                for e in ethnicity:
                    headers_16c1.append(e + "|" + "Math Proficient %")

                categories_16c1 = added_categories + headers_16c1

                fig16c1_final_data = combined_selected_data.loc[
                    :, (combined_selected_data.columns.isin(categories_16c1))
                ]

                if len(fig16c1_final_data.columns) > 4:
                    (
                        fig16c1_final_data,
                        fig16c1_category_string,
                        fig16c1_school_string,
                    ) = identify_missing_categories(fig16c1_final_data, categories_16c1)

                    fig16c1_label = create_chart_label(fig16c1_final_data)
                    fig16c1_chart = make_group_bar_chart(
                        fig16c1_final_data, school_id, trace_colors, fig16c1_label
                    )
                    fig16c1_table_data = combine_school_name_and_grade_levels(
                        fig16c1_final_data
                    )
                    fig16c1_table = create_comparison_table(
                        fig16c1_table_data, trace_colors, school_id
                    )

                    fig16c1 = create_barchart_layout(
                        fig16c1_chart,
                        fig16c1_table,
                        fig16c1_category_string,
                        fig16c1_school_string,
                    )

                    fig16c1_container = {"display": "block"}
                    analysis_single_dropdown_container = {"display": "block"}

                else:
                    fig16c1 = no_data_fig_label(
                        "Comparison: Math Proficiency by Ethnicity", 200
                    )

                    fig16c1_container = {"display": "none"}

                ## ELA Proficiency by Subgroup Compared to Similar Schools (1.6.a.2) ##
                headers_16a2 = []
                for s in subgroup:
                    headers_16a2.append(s + "|" + "ELA Proficient %")

                categories_16a2 = added_categories + headers_16a2

                fig16a2_final_data = combined_selected_data.loc[
                    :, (combined_selected_data.columns.isin(categories_16a2))
                ]

                if len(fig16a2_final_data.columns) > 4:
                    (
                        fig16a2_final_data,
                        fig16a2_category_string,
                        fig16a2_school_string,
                    ) = identify_missing_categories(fig16a2_final_data, categories_16a2)

                    fig16a2_label = create_chart_label(fig16a2_final_data)
                    fig16a2_chart = make_group_bar_chart(
                        fig16a2_final_data, school_id, trace_colors, fig16a2_label
                    )
                    fig16a2_table_data = combine_school_name_and_grade_levels(
                        fig16a2_final_data
                    )

                    fig16a2_table = create_comparison_table(
                        fig16a2_table_data, trace_colors, school_id
                    )

                    fig16a2 = create_barchart_layout(
                        fig16a2_chart,
                        fig16a2_table,
                        fig16a2_category_string,
                        fig16a2_school_string,
                    )
                    fig16a2_container = {"display": "block"}
                    analysis_single_dropdown_container = {"display": "block"}

                else:
                    fig16a2 = no_data_fig_label(
                        "Comparison: ELA Proficiency by Subgroup", 200
                    )
                    fig16a2_container = {"display": "none"}

                ## IREAD Proficiency by Subgroup Compared to Similar Schools ##
                headers_16b2 = []
                for s in subgroup:
                    headers_16b2.append(s + "|" + "IREAD Proficient %")

                categories_16b2 = added_categories + headers_16b2

                fig16b2_final_data = combined_selected_data.loc[
                    :, (combined_selected_data.columns.isin(categories_16b2))
                ]

                if len(fig16b2_final_data.columns) > 4:
                    (
                        fig16b2_final_data,
                        fig16b2_category_string,
                        fig16b2_school_string,
                    ) = identify_missing_categories(fig16b2_final_data, categories_16b2)

                    fig16b2_label = create_chart_label(fig16b2_final_data)
                    fig16b2_chart = make_group_bar_chart(
                        fig16b2_final_data, school_id, trace_colors, fig16b2_label
                    )
                    fig16b2_table_data = combine_school_name_and_grade_levels(
                        fig16b2_final_data
                    )

                    fig16b2_table = create_comparison_table(
                        fig16b2_table_data, trace_colors, school_id
                    )

                    fig16b2 = create_barchart_layout(
                        fig16b2_chart,
                        fig16b2_table,
                        fig16b2_category_string,
                        fig16b2_school_string,
                    )
                    fig16b2_container = {"display": "block"}
                    analysis_single_dropdown_container = {"display": "block"}

                else:
                    fig16b2 = no_data_fig_label(
                        "Comparison: IREAD Proficiency by Subgroup", 200
                    )
                    fig16b2_container = {"display": "none"}

                ## Math Proficiency by Subgroup Compared to Similar Schools (1.6.c.2) ##
                headers_16c2 = []
                for s in subgroup:
                    headers_16c2.append(s + "|" + "Math Proficient %")

                categories_16c2 = added_categories + headers_16c2

                fig16c2_final_data = combined_selected_data.loc[
                    :, (combined_selected_data.columns.isin(categories_16c2))
                ]

                if len(fig16c2_final_data.columns) > 4:
                    (
                        fig16c2_final_data,
                        fig16c2_category_string,
                        fig16c2_school_string,
                    ) = identify_missing_categories(fig16c2_final_data, categories_16c2)

                    fig16c2_label = create_chart_label(fig16c2_final_data)
                    fig16c2_chart = make_group_bar_chart(
                        fig16c2_final_data, school_id, trace_colors, fig16c2_label
                    )
                    fig16c2_table_data = combine_school_name_and_grade_levels(
                        fig16c2_final_data
                    )
                    fig16c2_table = create_comparison_table(
                        fig16c2_table_data, trace_colors, school_id
                    )

                    fig16c2 = create_barchart_layout(
                        fig16c2_chart,
                        fig16c2_table,
                        fig16c2_category_string,
                        fig16c2_school_string,
                    )
                    fig16c2_container = {"display": "block"}
                    analysis_single_dropdown_container = {"display": "block"}

                else:
                    fig16c2 = no_data_fig_label(
                        "Comparison: Math Proficiency by Subgroup", 200
                    )
                    fig16c2_container = {"display": "none"}

    academic_analysis_notes = [
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            academic_analysis_notes_label, className="key-label__header"
                        ),
                        html.P(""),
                        html.P(
                            academic_analysis_notes_string,
                            style={
                                "textAlign": "Left",
                                "color": "#6783a9",
                                "fontSize": "1.2rem",
                                "margin": "10px",
                            },
                        ),
                    ],
                    className="pretty-container__key seven columns",
                )
            ],
            className="bare-container--flex--center twelve columns",
        )
    ]

    trace_color_state = trace_colors

    return (
        trace_color_state,
        analysis_single_dropdown_container,
        fig14c,
        fig14d,
        fig_iread,
        fig16a1,
        fig16a1_container,
        fig16c1,
        fig16c1_container,
        fig16b1,
        fig16b1_container,
        fig16a2,
        fig16a2_container,
        fig16c2,
        fig16c2_container,
        fig16b2,
        fig16b2_container,
        k8_analysis_main_container,
        k8_analysis_empty_container,
        k8_analysis_no_data,
        grad_overview,
        grad_overview_container,
        grad_ethnicity,
        grad_ethnicity_container,
        grad_subgroup,
        grad_subgroup_container,
        sat_overview,
        sat_overview_container,
        sat_ethnicity_ebrw,
        sat_ethnicity_math,
        sat_ethnicity_container,
        sat_subgroup_ebrw,
        sat_subgroup_math,
        sat_subgroup_container,
        hs_analysis_main_container,
        hs_analysis_empty_container,
        hs_analysis_no_data,
        academic_analysis_notes,
    )


# NOTE: Uncomment (and remove "layout =") to return layout as function
def layout():
    return html.Div(
        # layout = html.Div(
        [
            html.Div(
                [
                    # dict used to store {school:color} to ensure consistency
                    dcc.Store(
                        id="trace-color-state-single", storage_type="memory", data={}
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                "Add or Remove Schools: ",
                                                className="comparison-dropdown-label",
                                            ),
                                        ],
                                        className="bare-container one-half columns",
                                    ),
                                    html.Div(
                                        [
                                            dcc.Dropdown(
                                                id="analysis-single-comparison-dropdown",
                                                style={"fontSize": "1.1rem"},
                                                multi=True,
                                                clearable=False,
                                                className="comparison-dropdown-control",
                                            ),
                                            html.Div(id="single-year-input-warning"),
                                        ],
                                        className="bare-container eight columns",
                                    ),
                                ],
                                className="comparison-dropdown-row",
                            ),
                        ],
                        id="analysis-single-dropdown-container",
                        style={"display": "none"},
                        # className="no-print",
                    ),
                    html.Div(
                        [
                            html.Div(
                                id="fig14c",
                                children=[],
                                style={"table-layout": "fixed"},
                            ),
                            html.Div(id="fig14d", children=[], className="pagebreak"),
                            html.Div(
                                id="fig-iread", children=[], className="pagebreak"
                            ),
                            html.Div(
                                [
                                    html.Div(id="fig16a1"),
                                ],
                                id="fig16a1-container",
                                style={"display": "none"},
                                className="pagebreak",
                            ),
                            html.Div(
                                [
                                    html.Div(id="fig16b1"),
                                ],
                                id="fig16b1-container",
                                style={"display": "none"},
                                className="pagebreak",
                            ),
                            html.Div(
                                [
                                    html.Div(id="fig16c1"),
                                ],
                                id="fig16c1-container",
                                style={"display": "none"},
                                className="pagebreak",
                            ),
                            html.Div(
                                [
                                    html.Div(id="fig16a2"),
                                ],
                                id="fig16a2-container",
                                style={"display": "none"},
                                className="pagebreak",
                            ),
                            html.Div(
                                [
                                    html.Div(id="fig16b2"),
                                ],
                                id="fig16b2-container",
                                style={"display": "none"},
                                className="pagebreak",
                            ),
                            html.Div(
                                [
                                    html.Div(id="fig16c2"),
                                ],
                                id="fig16c2-container",
                                style={"display": "none"},
                                className="pagebreak",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        id="single-year-analysis-notes", children=[]
                                    ),
                                ],
                                className="row",
                            ),
                        ],
                        id="k8-analysis-single-main-container",
                        style={"display": "none"},
                    ),
                    html.Div(
                        [
                            html.Div(id="k8-analysis-single-no-data"),
                        ],
                        id="k8-analysis-single-empty-container",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="grad-overview"),
                                ],
                                id="grad-overview-container",
                                style={"display": "none"},
                            ),
                            html.Div(
                                [
                                    html.Div(id="grad-ethnicity"),
                                ],
                                id="grad-ethnicity-container",
                                style={"display": "none"},
                            ),
                            html.Div(
                                [
                                    html.Div(id="grad-subgroup"),
                                ],
                                id="grad-subgroup-container",
                                style={"display": "none"},
                            ),
                            html.Div(
                                [
                                    html.Div(id="sat-overview"),
                                ],
                                id="sat-overview-container",
                                style={"display": "none"},
                            ),
                            html.Div(
                                [
                                    html.Div(id="sat-ethnicity-ebrw"),
                                    html.Div(id="sat-ethnicity-math"),
                                ],
                                id="sat-ethnicity-container",
                                style={"display": "none"},
                            ),
                            html.Div(
                                [
                                    html.Div(id="sat-subgroup-ebrw"),
                                    html.Div(id="sat-subgroup-math"),
                                ],
                                id="sat-subgroup-container",
                                style={"display": "none"},
                            ),
                        ],
                        id="hs-analysis-single-main-container",
                        style={"display": "none"},
                    ),
                    html.Div(
                        [
                            html.Div(id="hs-analysis-single-no-data"),
                        ],
                        id="hs-analysis-single-empty-container",
                    ),
                ],
                id="single-academic-analysis-page",
            ),
        ],
        id="main-container",
    )
