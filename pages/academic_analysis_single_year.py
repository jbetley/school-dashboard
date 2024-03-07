####################################################
# ICSB Dashboard - Academic Analysis - Single Year #
####################################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     02/21/24

import dash
from dash import ctx, dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np

# import local functions
from .load_data import (
    ethnicity,
    subgroup,
    ethnicity,
    info_categories,
    get_school_index,
    get_school_coordinates,
    get_comparable_schools,
    get_k8_corporation_academic_data,
    get_high_school_academic_data,
    get_hs_corporation_academic_data,
    get_selected_k8_school_academic_data,
    get_all_the_data
    # get_selected_hs_school_academic_data
)
from .process_data import (
    process_comparable_high_school_academic_data,
    process_k8_analysis_data
)
from .calculations import (
    calculate_proficiency,
    recalculate_total_proficiency,
    check_for_gradespan_overlap,
    calculate_comparison_school_list,
)
from .charts import no_data_fig_label, make_bar_chart, make_group_bar_chart
from .tables import create_comparison_table, no_data_page, no_data_table
from .layouts import (
    create_barchart_layout,
    create_hs_analysis_layout,
)
from .string_helpers import (
    create_school_label,
    combine_school_name_and_grade_levels,
    create_chart_label,
    identify_missing_categories,
)

dash.register_page(
    __name__,
    name="Selected Year",
    path="/academic_analysis_single_year",
    top_nav=True,
    order=10,
)

# Set dropdown options for comparison schools
@callback(
    Output("analysis-single-comparison-dropdown", "options"),
    Output("single-year-input-warning", "children"),
    Output("analysis-single-comparison-dropdown", "value"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("analysis-single-comparison-dropdown", "value"),
    Input("analysis-type-radio", "value"),
)
def set_dropdown_options(
    school_id: str, year: str, existing_comparison_schools_list: list, analysis_type_value=str
):
    string_year = year
    numeric_year = int(string_year)

    # clear the list of comparison_schools when a new school is
    # selected, otherwise comparison_schools will carry over, however
    # we want to keep the list for a year or type change
    input_trigger = ctx.triggered_id
    if input_trigger == "charter-dropdown":
        existing_comparison_schools_list = []

    selected_school = get_school_index(school_id)
    school_type = selected_school["School Type"].values[0]

    # Get School ID, School Name, Lat & Lon for all schools in the
    # set for selected year. SQL query depends on school type
    if school_type == "K12":
        if analysis_type_value == "hs":
            school_type = "HS"
        else:
            school_type = "K8"

    schools_by_distance = get_school_coordinates(numeric_year, school_type)

    # Drop any school not testing at least 20 students (k8 only- probably
    # impacts ~20 schools). Using "Total|ELATotalTested" as a proxy for school size
    if school_type == "K8":
        schools_by_distance["Total|ELA Total Tested"] = \
            pd.to_numeric(schools_by_distance["Total|ELA Total Tested"], errors="coerce")
        schools_by_distance = schools_by_distance[
            schools_by_distance["Total|ELA Total Tested"] >= 20
        ]

    # NOTE: There is some time cost for running the dropdown selection function (typically
    # ~0.8 - 1.2s), so we want to exit out as early as possible if we know it isn't necessary
    if int(school_id) not in schools_by_distance["School ID"].values:
        return [], [], []

    else:
        # NOTE: Before we do the distance check, we reduce the size of the df by removing
        # schools where there is no, or only a one grade overlap between the comparison schools.
        # the variable "overlap" is one less than the the number of grades that we want as a
        # minimum (a value of "1" means a 2 grade overlap, "2" means 3 grade overlap, etc.).

        # Skip this step for AHS (don't have a 'gradespan' in the technical sense)
        if school_type != "AHS":
            schools_by_distance = check_for_gradespan_overlap(
                school_id, schools_by_distance
            )

        num_schools_to_display = 40

        comparison_list = calculate_comparison_school_list(
            school_id, schools_by_distance, num_schools_to_display
        )

        # place new comparison schools into list of dicts
        new_comparison_schools = [
            {"label": name, "value": id} for name, id in comparison_list.items()
        ]

        # value for number of default display selections and maximum
        # display selections (because of zero indexing, max should be
        # 1 less than actual desired number)
        default_num_to_display = 4
        max_num_to_display = 7

        # used to display message if the number of selections exceeds the max
        input_warning = None

        # options and values (comparison_schools) logic
        # there are three occasions when we want to reset the list: 1) there are
        # no values (existing_comparison_schools_list = []); 2) there are values, but none
        # of the existing values overlap with the new values; 3) there are values, and there
        # is an overlap, but the number of overlapping schools is less than the total
        # number of existing schools.
        # (3) should only occur when we have a K12 school selected and are switching between
        # "K8" and "HS" types where there is another K12 school in the comparable school list.
        # Because the K12 school is in both lists- when the user switches, it is the only school
        # that will be displayed. We don't want this, so we reset.
        # NOTE: Probably easier to just reset K12 display every time the type changes, but I'm not
        # quite sure how to track that (value vs. state?)

        # at this point "existing_comparison_schools_list" is either [] (for no schools selected)
        # or a list of currently selected schools. "new_comparison_schools_list" is
        # a list of all of the schools matching the current selection (which is
        # triggered by a change in type from K8 to HS)

        new_comparison_schools_list = [d["value"] for d in new_comparison_schools]

        # count the number of schools shared by the two lists
        overlap = 0
        
        if not existing_comparison_schools_list:
            
            overlap = 0
        
        else:

            for sch in new_comparison_schools_list:
                overlap += existing_comparison_schools_list.count(sch)

        if not existing_comparison_schools_list or existing_comparison_schools_list and (
            # isdisjoint returns True if there are no common items between the sets
            # there is an existing list, but there is no overlap (e.g., K8 to HS)
            set(existing_comparison_schools_list).isdisjoint(new_comparison_schools_list) == True or

            # there is an existing list, and there is overlap, but the number of overlapping
            # schools is less than the length of all of the existing schools
           (
            set(existing_comparison_schools_list).isdisjoint(new_comparison_schools_list) == False and
                overlap < len(existing_comparison_schools_list)
                )
            ):

            # If any of these are true, we reset options and values
            comparison_schools = [d["value"] for d in new_comparison_schools[:default_num_to_display]]
            school_options = new_comparison_schools

        else:

            # if none of the above cases apply, we first test the length of the existing
            # list to make sure it hasn't exceeded max display

            if len(existing_comparison_schools_list) > max_num_to_display:
                
                # if it does, we throw a warning, keep the selected values the same
                # and disable all of the options
                input_warning = html.P(
                    id="single-year-input-warning",
                    children="Limit reached (Maximum of "
                    + str(max_num_to_display + 1)
                    + " schools).",
                )
                
                comparison_schools = existing_comparison_schools_list

                school_options = [
                    {
                        "label": option["label"],
                        "value": option["value"],
                        "disabled": True,
                    }
                    for option in new_comparison_schools
                ]
            
            else:
                # if it doesn't, we return the selected list and options.
                comparison_schools = existing_comparison_schools_list

                school_options = [
                    {
                        "label": option["label"],
                        "value": option["value"],
                        "disabled": False,
                    }
                    for option in new_comparison_schools
                ]

        return school_options, input_warning, comparison_schools


@callback(
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
    Input("analysis-type-radio", "value"),
    [Input("analysis-single-comparison-dropdown", "value")],
)
def update_academic_analysis_single_year(
    school_id: str, year: str, analysis_type_value: str, comparison_school_list: list
):
    if not school_id:
        raise PreventUpdate

    string_year = year
    numeric_year = int(string_year)

    selected_school = get_school_index(school_id)
    school_type = selected_school["School Type"].values[0]
    school_name = selected_school["School Name"].values[0]
    school_name = school_name.strip()

    # Radio buttons don't play nice
    if not analysis_type_value:
        analysis_type_value = "k8"

    # default values (only empty container displayed)
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

    k8_analysis_no_data = no_data_page(
        "No Data to Display.", "Comparison Data - K-8 Academic Data"
    )
    hs_analysis_no_data = no_data_page(
        "No Data to Display.", "Comparison Data - High School Academic Data"
    )

    academic_analysis_notes_label = ""
    academic_analysis_notes_string = ""

    if (
        school_type == "HS"
        or school_type == "AHS"
        or (school_type == "K12" and analysis_type_value == "hs")
    ):
        k8_analysis_empty_container = {"display": "none"}

        academic_analysis_notes_label = "Comparison Data - High School"
        academic_analysis_notes_string = "Use this page to view SAT and Graduation Rate comparison data for all ethnicities, \
            and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
            the selected school. Up to eight (8) schools may be displayed at once."

        # get data for school
        raw_hs_school_data = get_high_school_academic_data(school_id)

        # filter by selected year
        raw_hs_school_data = raw_hs_school_data.loc[
            raw_hs_school_data["Year"] == numeric_year
        ]
        raw_hs_school_data = raw_hs_school_data.reset_index(drop=True)

        if raw_hs_school_data.empty:
            analysis_single_dropdown_container = {"display": "none"}
            hs_analysis_empty_container = {"display": "block"}

        else:
            hs_school_name = raw_hs_school_data["School Name"].values[0]
            hs_school_name = hs_school_name.strip()

            # get data for corporation
            raw_hs_corp_data = get_hs_corporation_academic_data(school_id)
            hs_corporation_name = raw_hs_corp_data["Corporation Name"].values[0]
            hs_corporation_id = raw_hs_corp_data["Corporation ID"].values[0]

            raw_hs_corp_data = raw_hs_corp_data.loc[
                raw_hs_corp_data["Year"] == numeric_year
            ]
            raw_hs_corp_data = raw_hs_corp_data.reset_index(drop=True)

            # need to add some missing categories that aren't in corp df and drop
            # some columns that are in corp df but shouldnt be
            hs_info_columns = ["School Name", "School ID", "Lat", "Lon"]

            add_columns = hs_info_columns + raw_hs_corp_data.columns.tolist()
            raw_hs_corp_data = raw_hs_corp_data.reindex(columns=add_columns)

            raw_hs_corp_data["School Name"] = hs_corporation_name
            raw_hs_corp_data["School ID"] = hs_corporation_id
            raw_hs_corp_data["School Type"] = "School Corporation"

            # get data for comparable schools (already filtered by selected year in SQL query)
            raw_hs_comparison_data = get_comparable_schools(
                comparison_school_list, numeric_year, "HS"
            )

# TODO:     
            list_of_schools = [school_id] + comparison_school_list
            tst_data_hs = get_all_the_data(list_of_schools, "HS", numeric_year, "info")
# TODO:
            
# TODO: Want to replace the get comparable schools with get_selected
# TODO: In order to to do this, we need to revisit all of the HS processing
# TODO: Functions. So slightly more complicated. Goal is to make HS look
# TODO: Like K8, get rid of 'get_comparable_schools' and merge get_selected
# TODO: hs and k8 functions in to one                 
            # list_of_hs_schools = comparison_school_list + [school_id]
            # selected_hs_tst_data = get_selected_hs_school_academic_data(
            #     list_of_hs_schools, year
            # )

            # concatenate all three dataframes together. don't include
            # school corporation data if the selected school is an AHS,
            # it is not comparable and skews the output
            if school_type == "AHS":
                combined_hs_data = pd.concat(
                    [raw_hs_school_data, raw_hs_comparison_data],
                    ignore_index=True,
                )
            else:
                combined_hs_data = pd.concat(
                    [raw_hs_school_data, raw_hs_corp_data, raw_hs_comparison_data],
                    ignore_index=True,
                )

            # calculate values
            processed_hs_data = process_comparable_high_school_academic_data(
                combined_hs_data
            )

            hs_analysis_data = (
                processed_hs_data.set_index("Category")
                .T.rename_axis("Year")
                .rename_axis(None, axis=1)
                .reset_index()
            )

            hs_cols = [c for c in hs_analysis_data if c != "School Name"]

            # force all to numeric (this removes '***' strings) - we
            # later use NaN as a proxy
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
            ]
# TODO: HERE
            # check to see if there is data after processing
            if len(hs_analysis_data.columns) <= 5:
                analysis_single_dropdown_container = {"display": "none"}
                hs_analysis_empty_container = {"display": "block"}

            else:
                hs_analysis_main_container = {"display": "block"}
                hs_analysis_empty_container = {"display": "none"}

                # Graduation Comparison Sets
                grad_overview_categories = ["Total", "Non Waiver"]
                
                grad_overview = create_hs_analysis_layout(
                    "Graduation Rate",
                    hs_analysis_data,
                    grad_overview_categories,
                    school_id,
                )
                grad_ethnicity = create_hs_analysis_layout(
                    "Graduation Rate", hs_analysis_data, ethnicity, school_id
                )
                grad_subgroup = create_hs_analysis_layout(
                    "Graduation Rate", hs_analysis_data, subgroup, school_id
                )

                # SAT Comparison Sets
                overview = [
                    "Total|Math",
                    "Total|EBRW",
                ]
                sat_overview = create_hs_analysis_layout(
                    "Total", hs_analysis_data, overview, school_id
                )
                sat_ethnicity_ebrw = create_hs_analysis_layout(
                    "EBRW", hs_analysis_data, ethnicity, school_id
                )
                sat_ethnicity_math = create_hs_analysis_layout(
                    "Math", hs_analysis_data, ethnicity, school_id
                )
                sat_subgroup_ebrw = create_hs_analysis_layout(
                    "EBRW", hs_analysis_data, subgroup, school_id
                )
                sat_subgroup_math = create_hs_analysis_layout(
                    "Math", hs_analysis_data, subgroup, school_id
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
                        "Comparison: % of Students At Benchmark (SAT)", 200, "pretty"
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

    if school_type == "K8" or school_type == "K12":
        
        # If school is K12 and highschool tab is selected, skip k8 data
        if school_type == "K12" and analysis_type_value == "hs":
            k8_analysis_main_container = {"display": "none"}

        else:
            
            school_type = "K8"  # converts K12

            academic_analysis_notes_label = "Comparison Data - K-8"
            academic_analysis_notes_string = "Use this page to view ILEARN proficiency comparison data for all grades, ethnicities, \
                and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
                the selected school. Up to eight (8) schools may be displayed at once."

            # add school_id first
            list_of_schools = [school_id] + comparison_school_list
# # TODO:

            tst_data_k8 = get_all_the_data(list_of_schools, school_type, numeric_year, "info")
# # TODO:
            
            selected_k8_school_data = get_selected_k8_school_academic_data(
                list_of_schools, year
            )

            selected_clean_data = process_k8_analysis_data(
                selected_k8_school_data, school_id
            )

            # NOTE: We don't want to get rid of "***" yet, but we also don't
            # want to pass through a dataframe that that is all "***" - so
            # we convert create a copy, coerce all of the academic columns
            # to numeric and check to see if the entire dataframe for NaN
            check_for_unchartable_data = selected_clean_data.copy()

            check_for_unchartable_data.drop(
                ["School Name", "School ID", "Low Grade", "High Grade", "Year"],
                axis=1,
                inplace=True,
            )

            for col in check_for_unchartable_data.columns:
                check_for_unchartable_data[col] = pd.to_numeric(
                    check_for_unchartable_data[col], errors="coerce"
                )

            if (
                (school_type == "K8" or school_type == "K12")
                and len(selected_clean_data.index) > 0
            ) and check_for_unchartable_data.isnull().all().all() == False:
                k8_analysis_main_container = {"display": "block"}
                k8_analysis_empty_container = {"display": "none"}
                analysis_single_dropdown_container = {"display": "block"}

                raw_corp_data = get_k8_corporation_academic_data(school_id)

                selected_corp_data = raw_corp_data.loc[
                    raw_corp_data["Year"] == numeric_year
                ]

                # if no corp data, just use school data
                if selected_corp_data.empty:
                    combined_selected_data = selected_clean_data.copy()

                else:

                    # align Name and ID
                    selected_corp_data = selected_corp_data.rename(
                        columns={
                            "Corporation Name": "School Name",
                            "Corporation ID": "School ID",
                        }
                    )

                    # calculate proficiency for all corp categories
                    selected_corp_data = calculate_proficiency(selected_corp_data)

                    # recalculate total Math and ELA proficiency including only the
                    # gradespan of selected school (the default is calculated using
                    # all grades)
                    revised_school_totals = recalculate_total_proficiency(
                        selected_corp_data, selected_clean_data
                    )

                    selected_corp_data["Total|Math Proficient %"] = (
                        selected_corp_data["School ID"]
                        .map(
                            revised_school_totals.set_index("School ID")[
                                "Total|Math Proficient %"
                            ]
                        )
                        .fillna(selected_corp_data["Total|Math Proficient %"])
                    )

                    selected_corp_data["Total|ELA Proficient %"] = (
                        selected_corp_data["School ID"]
                        .map(
                            revised_school_totals.set_index("School ID")[
                                "Total|ELA Proficient %"
                            ]
                        )
                        .fillna(selected_corp_data["Total|ELA Proficient %"])
                    )

                    # clean up
                    selected_corp_data = selected_corp_data[
                        selected_corp_data.columns[
                            selected_corp_data.columns.str.contains(
                                r"Year|School ID|School Name|Proficient %"
                            )
                        ]
                    ]

                    # only keep columns in school df
                    selected_corp_data = selected_corp_data.loc[
                        :, selected_corp_data.columns.isin(selected_clean_data.columns)
                    ].copy()

                    # add two missing cols
                    selected_corp_data["Low Grade"] = np.nan
                    selected_corp_data["High Grade"] = np.nan

                    combined_selected_data = pd.concat(
                        [selected_clean_data, selected_corp_data]
                    )

                # Force '***' to NaN for numeric columns
                numeric_columns = [
                    col
                    for col in combined_selected_data.columns.to_list()
                    if col not in info_categories
                ]

                for col in numeric_columns:
                    combined_selected_data[col] = pd.to_numeric(
                        combined_selected_data[col], errors="coerce"
                    )

                # Now that *** is Nan, we drop all columns where selected school
                # has null data
                school_idx = combined_selected_data.index[
                    combined_selected_data["School ID"] == np.int64(school_id)
                ].tolist()[0]

                combined_selected_data = combined_selected_data.loc[
                    :, ~combined_selected_data.iloc[school_idx].isna()
                ]

                combined_selected_data = combined_selected_data.reset_index(drop=True)

                # add the information categories back to each dataframe
                added_categories = [
                    "School Name",
                    "School ID",
                    "Low Grade",
                    "High Grade",
                ]

                #### Current Year ELA Proficiency Compared to Similar Schools (1.4.c) #
                category = "Total|ELA Proficient %"

                # Get school value for specific category
                if category in combined_selected_data.columns:
                    fig14c_all_data = combined_selected_data[
                        added_categories + [category]
                    ].copy()

                    fig14c_table_data = fig14c_all_data.copy()

                    fig14c_all_data[category] = pd.to_numeric(fig14c_all_data[category])

                    fig14c_trace_color, fig14c_chart = make_bar_chart(
                        fig14c_all_data,
                        category,
                        school_id,
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
                        fig14c_table_data,
                        fig14c_trace_color,
                        school_id
                    )
                else:
                    # NOTE: This should never ever happen. So yeah.
                    fig14c_chart = no_data_fig_label(
                        "Comparison: Current Year ELA Proficiency", 200
                    )
                    fig14c_table = no_data_table(
                        "No Data to Display.", "ELA Proficiency", "none"
                    )

                fig14c = create_barchart_layout(fig14c_chart, fig14c_table,"","")

                #### Current Year Math Proficiency Compared to Similar Schools (1.4.d) #
                category = "Total|Math Proficient %"

                if category in combined_selected_data.columns:
                    fig14d_all_data = combined_selected_data[
                        added_categories + [category]
                    ].copy()

                    fig14d_table_data = fig14d_all_data.copy()

                    fig14d_all_data[category] = pd.to_numeric(fig14d_all_data[category])

                    fig14d_trace_color, fig14d_chart = make_bar_chart(
                        fig14d_all_data,
                        category,
                        school_id,
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
                        fig14d_table_data,
                        fig14d_trace_color,
                        school_id
                    )

                else:
                    fig14d_chart = no_data_fig_label(
                        "Comparison: Current Year Math Proficiency", 200
                    )
                    fig14d_table = no_data_table(
                        "No Data to Display.", "Math Proficiency", "none"
                    )

                fig14d = create_barchart_layout(fig14d_chart, fig14d_table,"","")

                #### Current Year IREAD Proficiency Compared to Similar Schools #
                category = "Total|IREAD Proficient %"

                if category in combined_selected_data.columns:
                    fig_iread_all_data = combined_selected_data[
                        added_categories + [category]
                    ].copy()

                    fig_iread_table_data = fig_iread_all_data.copy()

                    fig_iread_all_data[category] = pd.to_numeric(
                        fig_iread_all_data[category]
                    )

                    fig_iread_trace_color, fig_iread_chart = make_bar_chart(
                        fig_iread_all_data,
                        category,
                        school_id,
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
                        fig_iread_table_data,
                        fig_iread_trace_color,
                        school_id
                    )

                    fig_iread = create_barchart_layout(fig_iread_chart, fig_iread_table, "", "")

                else:
                    # NOTE: Better to display empty chart or no chart?
                    fig_iread_chart = []
                    fig_iread_table = []
                    
                # ELA Proficiency by Ethnicity Compared to Similar Schools (1.6.a.1)
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
                    fig16a1_trace_color, fig16a1_chart = make_group_bar_chart(
                        fig16a1_final_data, school_id, fig16a1_label
                    )
                    fig16a1_table_data = combine_school_name_and_grade_levels(
                        fig16a1_final_data
                    )
                    fig16a1_table = create_comparison_table(
                        fig16a1_table_data, fig16a1_trace_color, school_id)

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

                # IREAD Proficiency by Ethnicity Compared to Similar Schools
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
                    fig16b1_trace_color, fig16b1_chart = make_group_bar_chart(
                        fig16b1_final_data, school_id, fig16b1_label
                    )
                    fig16b1_table_data = combine_school_name_and_grade_levels(
                        fig16b1_final_data
                    )
                    
                    fig16b1_table = create_comparison_table(
                        fig16b1_table_data, fig16b1_trace_color, school_id)

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

                # Math Proficiency by Ethnicity Compared to Similar Schools (1.6.b.1)
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
                    fig16c1_trace_color, fig16c1_chart = make_group_bar_chart(
                        fig16c1_final_data, school_id, fig16c1_label
                    )
                    fig16c1_table_data = combine_school_name_and_grade_levels(
                        fig16c1_final_data
                    )
                    fig16c1_table = create_comparison_table(
                        fig16c1_table_data, fig16c1_trace_color, school_id)

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

                # ELA Proficiency by Subgroup Compared to Similar Schools (1.6.a.2)
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
                    fig16a2_trace_color, fig16a2_chart = make_group_bar_chart(
                        fig16a2_final_data, school_id, fig16a2_label
                    )
                    fig16a2_table_data = combine_school_name_and_grade_levels(
                        fig16a2_final_data
                    )

                    fig16a2_table = create_comparison_table(
                        fig16a2_table_data, fig16a2_trace_color, school_id)

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

                # IREAD Proficiency by Subgroup Compared to Similar Schools
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
                    fig16b2_trace_color, fig16b2_chart = make_group_bar_chart(
                        fig16b2_final_data, school_id, fig16b2_label
                    )
                    fig16b2_table_data = combine_school_name_and_grade_levels(
                        fig16b2_final_data
                    )

                    fig16b2_table = create_comparison_table(
                        fig16b2_table_data, fig16b2_trace_color, school_id)

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

                # Math Proficiency by Subgroup Compared to Similar Schools (1.6.b.2)
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
                    ) = identify_missing_categories(fig16c2_final_data, categories_16b2)

                    fig16c2_label = create_chart_label(fig16c2_final_data)
                    fig16c2_trace_color, fig16c2_chart = make_group_bar_chart(
                        fig16c2_final_data, school_id, fig16c2_label
                    )
                    fig16c2_table_data = combine_school_name_and_grade_levels(
                        fig16c2_final_data
                    )
                    fig16c2_table = create_comparison_table(
                        fig16c2_table_data, fig16c2_trace_color, school_id)

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

    return (
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
        academic_analysis_notes
    )


def layout():
    return html.Div(
        [
            html.Div(
                [
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
                                        className="bare-container two columns",
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
                        className="no-print",
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
            )
        ],
        id="main-container",
    )
