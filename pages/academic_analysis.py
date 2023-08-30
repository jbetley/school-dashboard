######################################
# ICSB Dashboard - Academic Analysis #
######################################
# author:   jbetley
# version:  1.10
# date:     08/31/23

# TODO: Add Grad Rate/SAT/? 

import dash
from dash import ctx, dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd

# import local functions
from .load_data import ethnicity, subgroup, ethnicity, info_categories, get_k8_school_academic_data, get_school_index, \
    get_school_coordinates, get_comparable_schools, get_k8_corporation_academic_data, get_high_school_academic_data, \
    get_hs_corporation_academic_data
from .process_data import process_k8_academic_data, process_k8_corp_academic_data, filter_high_school_academic_data, \
    process_high_school_academic_data
from .calculations import find_nearest, calculate_proficiency, recalculate_total_proficiency, get_excluded_years
from .chart_helpers import no_data_fig_label, make_bar_chart, make_group_bar_chart
from .table_helpers import create_comparison_table, no_data_page, no_data_table, combine_group_barchart_and_table, \
    combine_barchart_and_table
from .string_helpers import create_school_label, identify_missing_categories, combine_school_name_and_grade_levels, \
    create_school_label, create_chart_label
from .calculate_metrics import calculate_k8_comparison_metrics
from .subnav import subnav_academic

dash.register_page(__name__, path = "/academic_analysis", order=6)

# Set dropdown options for comparison schools
@callback(
    Output("comparison-dropdown", "options"),
    Output("input-warning","children"),
    Output("comparison-dropdown", "value"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("comparison-dropdown", "value"),
)
def set_dropdown_options(school, year, comparison_schools):

    string_year = "2019" if year == "2020" else year
    numeric_year = int(string_year)

    # clear the list of comparison_schools when a new school is
    # selected (e.g., "charter-dropdown" Input). otherwise
    # comparison_schools will carry over from school to school
    input_trigger = ctx.triggered_id
    if input_trigger == "charter-dropdown":
        comparison_schools = []

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]

    # There is some time cost for running the dropdown selection function (typically
    # ~0.8 - 1.2s), so we want to exit out as early as possible if we know it isn't necessary
    # HS and AHS currently do not have any data so don't need comparable schools.

# TODO: Add HS and K12 calculations
    if (selected_school_type == "AHS"): # selected_school_type == "HS" or 
        return [],[],[]
    
    # Get School ID, School Name, Lat & Lon for all schools in the set for selected year
    schools_by_distance = get_school_coordinates(numeric_year)
    
    # Drop any school not testing at least 20 students. "SchoolTotal|ELATotalTested" is a proxy
    # for school size here (probably only impacts ~20 schools)
    if selected_school_type != "HS":
        schools_by_distance = schools_by_distance[schools_by_distance["School Total|ELA Total Tested"] >= 20] 

    # It is a year when the school didnt exist
    if int(school) not in schools_by_distance["School ID"].values:
        return [],[],[]
    
    else:

        # NOTE: Before we do the distance check, we reduce the size of the df by removing
        # schools where there is no, or only a one grade overlap between the comparison schools.
        # the variable "overlap" is one less than the the number of grades that we want as a
        # minimum (a value of "1" means a 2 grade overlap, "2" means 3 grade overlap, etc.).
        overlap = 1

        schools_by_distance = schools_by_distance.replace({"Low Grade" : { "PK" : 0, "KG" : 1}})
        schools_by_distance["Low Grade"] = schools_by_distance["Low Grade"].astype(int)
        schools_by_distance["High Grade"] = schools_by_distance["High Grade"].astype(int)
        school_grade_span = schools_by_distance.loc[schools_by_distance["School ID"] == int(school)][["Low Grade","High Grade"]].values[0].tolist()
        school_low = school_grade_span[0]
        school_high = school_grade_span[1]

        # In order to fit within the distance parameters, the tested school must:
        #   a)  have a low grade that is less than or equal to the selected school and
        #       a high grade minus the selected school's low grade that is greater than or
        #       eqaul to the overlap; or
        #   b) have a low grade that is greater than or equal to the selected school and
        #       a high grade minus the tested school's low grade that is greater than or 
        #       equal to the overlap.
        # Examples -> assume a selected school with a gradespan of 5-8:
        #   i) a school with grades 3-7 -   [match]: low grade is less than selected school's
        #       low grade and high grade (7) minus selected school low grade (5) is greater (2)
        #       than the overlap (1).
        #   i) a school with grades 2-5 -   [No match]: low grade is less than selected school's
        #       low grade but high grade (5) minus selected school low grade (5) is not greater (0)
        #       than the overlap (1). In this case while there is an overlap, it is below our
        #       threshold (1 grade).
        #   c) a school with grades 6-12-   [match]: low grade is higher than selected school's
        #       low grade and high grade (12) minus the tested school low grade (5) is greater
        #       (7) than the overlap (1).
        #   d) a school with grades 3-4     [No match]: low grade is lower than selected school's
        #       low grade, but high grade (4) minus the selected school's low grade (5) is not greater
        #       (-1) than the overlap (1).

        schools_by_distance = schools_by_distance.loc[(
                (schools_by_distance["Low Grade"] <= school_low) & \
                (schools_by_distance["High Grade"] - school_low >= overlap)
            ) | \
            (
                (schools_by_distance["Low Grade"] >= school_low) & \
                (school_high - schools_by_distance["Low Grade"]  >= overlap)
            ), :]
        
        schools_by_distance = schools_by_distance.reset_index(drop = True)
        all_schools = schools_by_distance.copy()

        school_idx = schools_by_distance[schools_by_distance["School ID"] == int(school)].index

        # NOTE: This should never ever happen because we've already determined that the school exists in
        # the check above. However, it did happen once, somehow, so we leave this in here just in case.
        if school_idx.size == 0:
            return [],[],[]
        
        # kdtree spatial tree function returns two np arrays: an array of indexes and an array of distances
        index_array, dist_array = find_nearest(school_idx,schools_by_distance)

        index_list = index_array[0].tolist()
        distance_list = dist_array[0].tolist()

        # Match School ID with indexes
        closest_schools = pd.DataFrame()
        closest_schools["School ID"] = schools_by_distance[schools_by_distance.index.isin(index_list)]["School ID"]

        # Merge the index and distances lists into a dataframe
        distances = pd.DataFrame({"index":index_list, "y":distance_list})
        distances = distances.set_index(list(distances)[0])

        # Merge School ID with Distances by index
        combined = closest_schools.join(distances)

        # Merge the original df with the combined distance/SchoolID df (essentially just adding School Name)
        comparison_set = pd.merge(combined, all_schools, on="School ID", how="inner")
        comparison_set = comparison_set.rename(columns = {"y": "Distance"})
    
        # drop selected school (so it cannot be selected in the dropdown)
        comparison_set = comparison_set.drop(comparison_set[comparison_set["School ID"] == int(school)].index)

        # limit maximum dropdown to the [n] closest schools
        num_schools_expanded = 20

        comparison_set = comparison_set.sort_values(by=["Distance"], ascending=True)

        comparison_dropdown = comparison_set.head(num_schools_expanded)

        comparison_dict = dict(zip(comparison_dropdown["School Name"], comparison_dropdown["School ID"]))

        # final list will be displayed in order of increasing distance from selected school
        comparison_list = dict(comparison_dict.items())

        # Set default display selections to all schools in the list
        default_options = [{"label":name,"value":id} for name, id in comparison_list.items()]
        options = default_options

        # value for number of default display selections and maximum
        # display selections (because of zero indexing, max should be
        # 1 less than actual desired number)
        default_num_to_display = 4
        max_num_to_display = 7

        # used to display message if the number of selections exceeds the max
        input_warning = None

        # if list is None or empty ([]), use the default options (NOTE: The callback takes
        # comparison schools as an input, so this will only be empty on first run)
        if not comparison_schools:
            comparison_schools = [d["value"] for d in options[:default_num_to_display]]

        else:
            if len(comparison_schools) > max_num_to_display:
                input_warning = html.P(
                    id="input-warning",
                    children="Limit reached (Maximum of " + str(max_num_to_display+1) + " schools).",
                )
                options = [
                    {"label": option["label"], "value": option["value"], "disabled": True}
                    for option in default_options
                ]
        
        return options, input_warning, comparison_schools

@callback(
    Output("academic-analysis-notes-string", "children"),
    Output("fig14c", "children"),
    Output("fig14d", "children"),
    Output("fig-iread", "children"),
    Output("dropdown-container", "style"),
    Output("fig16a1", "children"),   
    Output("fig16a1-container", "style"),    
    Output("fig16b1", "children"),
    Output("fig16b1-container", "style"),
    Output("fig16a2", "children"),
    Output("fig16a2-container", "style"),
    Output("fig16b2", "children"),
    Output("fig16b2-container", "style"),
    Output("k8-analysis-main-container", "style"),
    Output("k8-analysis-empty-container", "style"),
    Output("k8-analysis-no-data", "children"),

    Output("hs-grad-overview", "children"),
    Output("hs-grad-overview-container", "style"),    
    Output("hs-grad-ethnicity", "children"),
    Output("hs-grad-ethnicity-container", "style"),    
    Output("hs-grad-subgroup", "children"),
    Output("hs-grad-subgroup-container", "style"),    
    Output("sat-overview", "children"),
    Output("sat-overview-container", "style"),    
    Output("sat-ethnicity", "children"),
    Output("sat-ethnicity-container", "style"),    
    Output("sat-subgroup", "children"),
    Output("sat-subgroup-container", "style"),    
    Output("hs-analysis-main-container", "style"),
    Output("hs-analysis-empty-container", "style"),
    Output("hs-analysis-no-data", "children"),

    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    [Input("comparison-dropdown", "value")],
)
def update_academic_analysis(school: str, year: str, comparison_school_list: list):
    if not school:
        raise PreventUpdate

    # show 2019 instead of 2020 as 2020 has no academic data
    string_year = "2019" if year == "2020" else year
    numeric_year = int(string_year)

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]
    school_name = selected_school["School Name"].values[0]

    # default values (only empty container displayed)
    fig14c = []
    fig14d = []
    fig_iread = []
        
    fig16a1 = []
    fig16a1_container = {"display": "none"}

    fig16b1 = []
    fig16b1_container = {"display": "none"}

    fig16a2 = []
    fig16a2_container = {"display": "none"}

    fig16b2 = []
    fig16b2_container = {"display": "none"}

    dropdown_container = {"display": "none"}
    k8_analysis_main_container = {"display": "none"}
    k8_analysis_empty_container = {"display": "block"}

    grad_overview = []  # type: ignore
    grad_overview_container = {"display": "none"}

    grad_ethnicity = [] # type: ignore
    grad_ethnicity_container = {"display": "none"}

    grad_subgroup = []  # type: ignore
    grad_subgroup_container = {"display": "none"}

    sat_overview = []   
    sat_overview_container = {"display": "none"}

    sat_ethnicity = []
    sat_ethnicity_container = {"display": "none"}

    sat_subgroup = []
    sat_subgroup_container = {"display": "none"}

    hs_analysis_main_container = {"display": "none"}
    hs_analysis_empty_container = {"display": "block"}

    k8_analysis_no_data = hs_analysis_no_data = no_data_page("Academic Analysis")
    
    academic_analysis_notes_string = "Use this page to view ILEARN proficiency comparison data for all grades, ethnicities, \
        and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
        the selected school. Up to eight (8) schools may be displayed at once. Data Source: Indiana Department of Education \
        Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)."

    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)  

    # Currently we only display data for Grades K-8. So nothing is displayed for
    # High Schools (HS) or Adult High Schools (AHS)
    if selected_school_type == "HS" or selected_school_type == "AHS" or selected_school_type == "K12":
         
        if selected_school_type == "HS" or selected_school_type == "AHS":
            k8_analysis_main_container = {"display": "none"}
            k8_analysis_empty_container = {"display": "none"}

        raw_hs_school_data = get_high_school_academic_data(school)
        
        raw_hs_school_data = raw_hs_school_data.loc[raw_hs_school_data["Year"] == numeric_year]
        hs_school_name = raw_hs_school_data['School Name'].values[0]
        
        filtered_hs_school_data = filter_high_school_academic_data(raw_hs_school_data)

        if not filtered_hs_school_data.empty:

            raw_hs_corp_data = get_hs_corporation_academic_data(school)

            raw_hs_corp_data = raw_hs_corp_data.loc[raw_hs_corp_data["Year"] == numeric_year]   
            
            hs_corporation_name = raw_hs_corp_data['Corporation Name'].values[0]

            for col in raw_hs_corp_data.columns:
                raw_hs_corp_data[col] = pd.to_numeric(raw_hs_corp_data[col], errors="coerce")

            # find the intersection of the two sets and use it to ensure only cols present in
            # the school df are used
            common_cols = [col for col in set(filtered_hs_school_data.columns).intersection(raw_hs_corp_data.columns)]
            
            raw_hs_corp_data = raw_hs_corp_data[common_cols]

            processed_hs_school_data = process_high_school_academic_data(filtered_hs_school_data, school)

            # processing adds 'N-Size' col which we don't need here - so drop
            processed_hs_school_data = processed_hs_school_data[processed_hs_school_data.columns[~processed_hs_school_data.columns.str.contains(r"N-Size")]]

            processed_hs_corp_data = process_high_school_academic_data(raw_hs_corp_data, school)

            processed_hs_corp_data = processed_hs_corp_data[processed_hs_corp_data.columns[~processed_hs_corp_data.columns.str.contains(r"N-Size")]]

            hs_corp_data = processed_hs_corp_data.set_index("Category").T.rename_axis("Year").rename_axis(None, axis=1).reset_index()
            
            hs_corp_data = hs_corp_data[hs_corp_data.columns[hs_corp_data.columns.str.contains(r"Benchmark \%|Graduation Rate|Low Grade|High Grade")]]
            
            hs_school_data = processed_hs_school_data.set_index("Category").T.rename_axis("Year").rename_axis(None, axis=1).reset_index()

            hs_school_data = hs_school_data[hs_school_data.columns[hs_school_data.columns.str.contains(r"Benchmark \%|Graduation Rate|Low Grade|High Grade")]]
            
            hs_school_data['School Name'] = hs_school_name
            hs_corp_data['School Name'] = hs_corporation_name

# TODO: Explore adding Low and High Grade later in the chain so we don't have to keep dropping/ignoring
            low_grade =  raw_hs_school_data.loc[(raw_hs_school_data["Year"] == numeric_year), "Low Grade"].values[0]
            high_grade =  raw_hs_school_data.loc[(raw_hs_school_data["Year"] == numeric_year), "High Grade"].values[0]

            # Grade range data is used for the chart "hovertemplate"         
            hs_school_data["Low Grade"] =  raw_hs_school_data.loc[(raw_hs_school_data["Year"] == numeric_year), "Low Grade"].values[0]
            hs_school_data["High Grade"] =  raw_hs_school_data.loc[(raw_hs_school_data["Year"] == numeric_year), "High Grade"].values[0]

            print('COMPARE')
            print(comparison_school_list)

            comparison_hs_schools_filtered = get_comparable_schools(comparison_school_list, numeric_year)
            # print(comparison_hs_schools_filtered)
            
            combined_hs_data = pd.concat([hs_school_data, hs_corp_data], ignore_index = True)

            hs_cols = [c for c in combined_hs_data if "School Name" not in c]
            
            # force all to numeric (this removes '***' strings) - we later use NaN as a proxy
            for col in hs_cols:
                combined_hs_data[col]=pd.to_numeric(combined_hs_data[col], errors="coerce")

            # there are currently only two available data points for AHS and HS: Grad Rate and SAT

            # Graduation Rate Overview
            grad_overview_cols = ["School Name","Total Graduation Rate", "Non Waiver Graduation Rate","Low Grade","High Grade"]

            grad_overview_data = combined_hs_data.loc[:, (combined_hs_data.columns.isin(grad_overview_cols))]

            # df will always have at least three cols (School Name, Low Grade, High Grade)
            if len(grad_overview_data.columns) > 3:

                grad_overview_data, grad_overview_category_string, grad_overview_school_string = \
                    identify_missing_categories(grad_overview_data, hs_corp_data, hs_corp_data, grad_overview_cols, hs_corporation_name)

                # Once missing category and strings are built, we need to drop any columns for which the
                # school has no data (we only want to display columns including the school)

                # find the index of the row containing the school name
                school_name_idx = grad_overview_data.index[grad_overview_data["School Name"].str.contains(hs_school_name)].tolist()[0]

                # drop all columns where the row at school_name_idx has a NaN value
                grad_overview_data = grad_overview_data.loc[:, ~grad_overview_data.iloc[school_name_idx].isna()]

                if len(grad_overview_data.columns) > 1:
                    grad_overview_label = create_chart_label(grad_overview_data)
                    grad_overview_chart = make_group_bar_chart(grad_overview_data, school_name, grad_overview_label)
                    grad_overview_table_data = combine_school_name_and_grade_levels(grad_overview_data)

                    # TODO: Last arg is for a label - determine if it is needed
                    grad_overview_table = create_comparison_table(grad_overview_table_data, school_name,"")

                    grad_overview = combine_group_barchart_and_table(grad_overview_chart,grad_overview_table, grad_overview_category_string, grad_overview_school_string)
                    
                    grad_overview_container = {"display": "block"}
                    hs_analysis_main_container = {"display": "block"}
                    hs_analysis_empty_container = {"display": "none"}
                    dropdown_container = {"display": "block"}

                else:
                    grad_overview = no_data_fig_label("Comparison: Graduation Rate by Ethnicity", 200)
                    grad_overview_container = {"display": "none"}

            else:
                grad_overview = no_data_fig_label("Comparison: Total/Non Waiver Graduation Rate", 200)
                grad_overview_container = {"display": "none"}

            # Graduation Rate Ethnicity
            grad_ethnicity_cols = [col for col in combined_hs_data.columns if 'Graduation Rate' in col and any(substring for substring in ethnicity if substring in col)]
            grad_ethnicity_cols = info_categories + grad_ethnicity_cols
            grad_ethnicity_data = combined_hs_data[grad_ethnicity_cols]

# TODO: Grad Data has Low/High at this point and SAT does not. WHY?
            print('RAW Grad DATA')
            print(grad_ethnicity_data)

            if len(grad_ethnicity_data.columns) > 3:

                grad_ethnicity_data, grad_ethnicity_category_string, grad_ethnicity_school_string = \
                    identify_missing_categories(grad_ethnicity_data, hs_corp_data, hs_corp_data, grad_ethnicity_cols, hs_corporation_name)

                school_name_idx = grad_ethnicity_data.index[grad_ethnicity_data["School Name"].str.contains(hs_school_name)].tolist()[0]
                grad_ethnicity_data = grad_ethnicity_data.loc[:, ~grad_ethnicity_data.iloc[school_name_idx].isna()]

                print('Grad DATA - Post Stringify')
                print(grad_ethnicity_data)

                if len(grad_ethnicity_data.columns) > 1:
                    grad_ethnicity_label = create_chart_label(grad_ethnicity_data)
                    grad_ethnicity_chart = make_group_bar_chart(grad_ethnicity_data, school_name, grad_ethnicity_label)
                    grad_ethnicity_table_data = combine_school_name_and_grade_levels(grad_ethnicity_data)
                    grad_ethnicity_table = create_comparison_table(grad_ethnicity_table_data, school_name,"")

                    grad_ethnicity = combine_group_barchart_and_table(grad_ethnicity_chart,grad_ethnicity_table, grad_ethnicity_category_string, grad_ethnicity_school_string)
                    
                    grad_ethnicity_container = {"display": "block"}
                    hs_analysis_main_container = {"display": "block"}
                    hs_analysis_empty_container = {"display": "none"}
                    dropdown_container = {"display": "block"}

                else:
                    grad_ethnicity = no_data_fig_label("Comparison: Graduation Rate by Ethnicity", 200)
                    grad_ethnicity_container = {"display": "none"}

            else:
                grad_ethnicity = no_data_fig_label("Comparison: Graduation Rate by Ethnicity", 200)
                grad_ethnicity_container = {"display": "none"}

            # Graduation Rate Subgroup
            grad_subgroup_cols = [col for col in combined_hs_data.columns if 'Graduation Rate' in col and any(substring for substring in subgroup if substring in col)]
            grad_subgroup_cols = info_categories + grad_subgroup_cols
            grad_subgroup_data = combined_hs_data[grad_subgroup_cols]

            if len(grad_subgroup_data.columns) > 3:

                grad_subgroup_data, grad_subgroup_category_string, grad_subgroup_school_string = \
                    identify_missing_categories(grad_subgroup_data, hs_corp_data, hs_corp_data, grad_subgroup_cols, hs_corporation_name)

                school_name_idx = grad_subgroup_data.index[grad_subgroup_data["School Name"].str.contains(hs_school_name)].tolist()[0]
                grad_subgroup_data = grad_subgroup_data.loc[:, ~grad_subgroup_data.iloc[school_name_idx].isna()]

                if len(grad_subgroup_data.columns) > 1:
                    grad_subgroup_label = create_chart_label(grad_subgroup_data)
                    grad_subgroup_chart = make_group_bar_chart(grad_subgroup_data, school_name, grad_subgroup_label)
                    grad_subgroup_table_data = combine_school_name_and_grade_levels(grad_subgroup_data)
                    grad_subgroup_table = create_comparison_table(grad_subgroup_table_data, school_name,"")

                    grad_subgroup = combine_group_barchart_and_table(grad_subgroup_chart,grad_subgroup_table, grad_subgroup_category_string, grad_subgroup_school_string)
                    
                    grad_subgroup_container = {"display": "block"}
                    hs_analysis_main_container = {"display": "block"}
                    hs_analysis_empty_container = {"display": "none"}                
                    dropdown_container = {"display": "block"}

                else:
                    grad_subgroup = no_data_fig_label("Comparison: Graduation Rate by Subgroup", 200)
                    grad_subgroup_container = {"display": "none"}

            else:
                grad_subgroup = no_data_fig_label("Comparison: Graduation Rate by Subgroup", 200)
                grad_subgroup_container = {"display": "none"}

            # SAT Total
            sat_overview_cols = [col for col in combined_hs_data.columns if 'School Total' in col]
            sat_overview_cols = info_categories + sat_overview_cols
            sat_overview_data = combined_hs_data[sat_overview_cols]

            # NOTE: For transparency purposes, we want to identify all categories that are missing from
            # the possible dataset, including those that aren't going to be displayed (because the school
            # is missing them). Because there are many cases where there wont be any data at all (eg, it
            # hasn't yet been released, or there is no data for a particular yet. So we need to check whether
            # there is any data to display before and after we collect the missing category information. After
            # we collect any missing information, we need to drop any columns where the school has no data and
            # then check again to see if the dataframe has any info.

            if len(sat_overview_data.columns) > 1:

                sat_overview_data, sat_overview_category_string, sat_overview_school_string = \
                    identify_missing_categories(sat_overview_data, hs_corp_data, hs_corp_data, sat_overview_cols, hs_corporation_name)

                # Once missing category and strings are built, we need to drop any columns for which the
                # school has no data (we only want to display columns including the school)

                # find the index of the row containing the school name
                school_name_idx = sat_overview_data.index[sat_overview_data["School Name"].str.contains(hs_school_name)].tolist()[0]

                # drop all columns where the row at school_name_idx has a NaN value
                sat_overview_data = sat_overview_data.loc[:, ~sat_overview_data.iloc[school_name_idx].isna()]

                if len(sat_overview_data.columns) > 1:
                    sat_overview_label = create_chart_label(sat_overview_data)
                    sat_overview_chart = make_group_bar_chart(sat_overview_data, school_name, sat_overview_label)
                    sat_overview_table_data = combine_school_name_and_grade_levels(sat_overview_data)
                    sat_overview_table = create_comparison_table(sat_overview_table_data, school_name,"")

                    sat_overview = combine_group_barchart_and_table(sat_overview_chart,sat_overview_table,sat_overview_category_string, sat_overview_school_string)
                    
                    sat_overview_container = {"display": "block"}
                    hs_analysis_main_container = {"display": "block"}
                    hs_analysis_empty_container = {"display": "none"}                
                    dropdown_container = {"display": "block"}

                else:
                    sat_overview = no_data_fig_label("Comparison: SAT School Total", 200)
                    sat_overview_container = {"display": "none"}

            else:
                sat_overview = no_data_fig_label("Comparison: SAT School Total", 200)
                sat_overview_container = {"display": "none"}
            
            # SAT Ethnicity - EBRW
            sat_ethnicity_cols = [col for col in combined_hs_data.columns if 'Benchmark' in col and any(substring for substring in ethnicity if substring in col)]
            sat_ethnicity_cols = info_categories + sat_ethnicity_cols
            sat_ethnicity_data = combined_hs_data[sat_ethnicity_cols]
            
            sat_ethnicity_data =  sat_ethnicity_data[[col for col in sat_ethnicity_data.columns if "EBRW" in col or "School Name" in col]]
            print('RAW SAT DATA')
            print(sat_ethnicity_data)
            if len(sat_ethnicity_data.columns) > 1:

                sat_ethnicity_data, sat_ethnicity_category_string, sat_ethnicity_school_string = \
                    identify_missing_categories(sat_ethnicity_data, hs_corp_data, hs_corp_data, sat_ethnicity_cols, hs_corporation_name)

                school_name_idx = sat_ethnicity_data.index[sat_ethnicity_data["School Name"].str.contains(hs_school_name)].tolist()[0]
                sat_ethnicity_data = sat_ethnicity_data.loc[:, ~sat_ethnicity_data.iloc[school_name_idx].isna()]
                
                print('SAT DATA - Post Stringify')
                print(sat_ethnicity_data)

                if len(sat_ethnicity_data.columns) > 1:
                    sat_ethnicity_label = create_chart_label(sat_ethnicity_data)
                    sat_ethnicity_chart = make_group_bar_chart(sat_ethnicity_data, school_name, sat_ethnicity_label)
                    sat_ethnicity_table_data = combine_school_name_and_grade_levels(sat_ethnicity_data)
                    sat_ethnicity_table = create_comparison_table(sat_ethnicity_table_data, school_name,"")

                    sat_ethnicity = combine_group_barchart_and_table(sat_ethnicity_chart,sat_ethnicity_table, sat_ethnicity_category_string, sat_ethnicity_school_string)
                    
                    sat_ethnicity_container = {"display": "block"}
                    hs_analysis_main_container = {"display": "block"}
                    hs_analysis_empty_container = {"display": "none"}                
                    dropdown_container = {"display": "block"}

                else:
                    sat_ethnicity = no_data_fig_label("Comparison: SAT By Ethnicity", 200)
                    sat_ethnicity_container = {"display": "none"}

            else:
                sat_ethnicity = no_data_fig_label("Comparison: SAT By Ethnicity", 200)
                sat_ethnicity_container = {"display": "none"}

            # SAT Subgroup - EBRW
            sat_subgroup_cols = [col for col in combined_hs_data.columns if 'Benchmark' in col and any(substring for substring in subgroup if substring in col)]
            sat_subgroup_cols = info_categories + sat_subgroup_cols
            sat_subgroup_data = combined_hs_data[sat_subgroup_cols]

            sat_subgroup_data =  sat_subgroup_data[[col for col in sat_subgroup_data.columns if "EBRW" in col or "School Name" in col]]

            if len(sat_subgroup_data.columns) > 1:

                sat_subgroup_data, sat_subgroup_category_string, sat_subgroup_school_string = \
                    identify_missing_categories(sat_subgroup_data, hs_corp_data, hs_corp_data, sat_subgroup_cols, hs_corporation_name)
                
                school_name_idx = sat_subgroup_data.index[sat_subgroup_data["School Name"].str.contains(hs_school_name)].tolist()[0]
                sat_subgroup_data = sat_subgroup_data.loc[:, ~sat_subgroup_data.iloc[school_name_idx].isna()]

                if len(sat_subgroup_data.columns) > 1:
                    sat_subgroup_label = create_chart_label(sat_subgroup_data)
                    sat_subgroup_chart = make_group_bar_chart(sat_subgroup_data, school_name, sat_subgroup_label)
                    sat_subgroup_table_data = combine_school_name_and_grade_levels(sat_subgroup_data)
                    sat_subgroup_table = create_comparison_table(sat_subgroup_table_data, school_name,"")

                    sat_subgroup = combine_group_barchart_and_table(sat_subgroup_chart,sat_subgroup_table, sat_subgroup_category_string, sat_subgroup_school_string)
                    
                    sat_subgroup_container = {"display": "block"}
                    hs_analysis_main_container = {"display": "block"}
                    hs_analysis_empty_container = {"display": "none"}                
                    dropdown_container = {"display": "block"}

                else:
                    sat_subgroup = no_data_fig_label("Comparison: SAT By Subgroup", 200)
                    sat_subgroup_container = {"display": "none"}   

            else:
                sat_subgroup = no_data_fig_label("Comparison: SAT By Subgroup", 200)
                sat_subgroup_container = {"display": "none"}   

    if selected_school_type != "HS" or selected_school_type != "AHS":
        
        # get academic data
        selected_raw_k8_school_data = get_k8_school_academic_data(school)

        excluded_years = get_excluded_years(year)

        if excluded_years:
            selected_raw_k8_school_data = selected_raw_k8_school_data[~selected_raw_k8_school_data["Year"].isin(excluded_years)]

        if ((selected_school_type == "K8" or selected_school_type == "K12") and len(selected_raw_k8_school_data.index) > 0):

            selected_raw_k8_school_data = selected_raw_k8_school_data.replace({"^": "***"})

            clean_school_data = process_k8_academic_data(selected_raw_k8_school_data)

            if not clean_school_data.empty:

                raw_corp_data = get_k8_corporation_academic_data(school)

                corp_name = raw_corp_data["Corporation Name"].values[0]

                clean_corp_data = process_k8_corp_academic_data(raw_corp_data, clean_school_data)

                raw_comparison_data = calculate_k8_comparison_metrics(clean_school_data, clean_corp_data, string_year)
                
                tested_year = string_year + "School"

                # Page is also empty if the school is a K8/K12, and the df has data, but the tested_year
                # (YEARSchool) does not exist in the dataframe- this catches any year with no data (e.g., 2020) OR
                # if the tested header does exist, but all data in the column is NaN- this catches any year where
                # the school has no data or insufficient n-size ("***")

                raw_comparison_data['Test Year'] = pd.to_numeric(raw_comparison_data[tested_year], errors="coerce")

                if raw_comparison_data['Test Year'].isnull().all():
                    no_data_to_display = no_data_page("Academic Analysis","No Available Data with a sufficient n-size.")
                
                elif tested_year in raw_comparison_data.columns:

                    k8_analysis_main_container = {"display": "block"}
                    k8_analysis_empty_container = {"display": "none"}

                    raw_comparison_data = raw_comparison_data.drop('Test Year', axis=1)

                    school_academic_data = raw_comparison_data[[col for col in raw_comparison_data.columns if "School" in col or "Category" in col]].copy()
                    school_academic_data.columns = school_academic_data.columns.str.replace(r"School$", "", regex=True)

                    display_academic_data = school_academic_data.set_index("Category").T.rename_axis("Year").rename_axis(None, axis=1).reset_index()

                    # add suffix to certain Categories
                    display_academic_data = display_academic_data.rename(columns={c: c + " Proficient %" for c in display_academic_data.columns if c not in ["Year", "School Name"]})

# TODO: Add by Grade multi-line fig

                    ## Comparison data ##
                    current_school_data = display_academic_data.loc[display_academic_data["Year"] == string_year].copy()

                    # this time we want to force '***' to NaN
                    for col in current_school_data.columns:
                        current_school_data[col]=pd.to_numeric(current_school_data[col], errors="coerce")

                    current_school_data = current_school_data.dropna(axis=1, how="all")
                    current_school_data["School Name"] = school_name

                    # Grade range data is used for the chart "hovertemplate"            
                    current_school_data["Low Grade"] =  selected_raw_k8_school_data.loc[(selected_raw_k8_school_data["Year"] == numeric_year), "Low Grade"].values[0]
                    current_school_data["High Grade"] =  selected_raw_k8_school_data.loc[(selected_raw_k8_school_data["Year"] == numeric_year), "High Grade"].values[0]

                    # process academic data for the school corporation in which the selected school is located
                    corp_academic_data = clean_corp_data.set_index("Category").T.rename_axis("Year").rename_axis(None, axis=1).reset_index()
                    current_corp_data = corp_academic_data.loc[corp_academic_data["Year"] == string_year].copy()

                    for col in current_corp_data.columns:
                        current_corp_data[col]=pd.to_numeric(current_corp_data[col], errors="coerce")

                    comparison_schools_filtered = get_comparable_schools(comparison_school_list, numeric_year)

                    comparison_schools_filtered = comparison_schools_filtered.filter(regex = r"Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year|School Name|School ID|Distance|Low Grade|High Grade",axis=1)

                    # create list of columns with no data (used in loop below)
                    comparison_schools_info = comparison_schools_filtered[["School Name","Low Grade","High Grade"]].copy()            
                    comparison_schools_filtered = comparison_schools_filtered.drop(["School ID","School Name","Low Grade","High Grade"], axis=1)

                    # change values to numeric
                    for col in comparison_schools_filtered.columns:
                        comparison_schools_filtered[col] = pd.to_numeric(comparison_schools_filtered[col], errors="coerce")

                    comparison_schools = calculate_proficiency(comparison_schools_filtered)
                    comparison_schools = recalculate_total_proficiency(comparison_schools, clean_school_data)

                    # calculate IREAD Pass %
                    if "IREAD Proficient %" in current_school_data:
                        comparison_schools["IREAD Proficient %"] = comparison_schools["IREAD Pass N"] / comparison_schools["IREAD Test N"]
                    
                    # remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
                    comparison_schools = comparison_schools.filter(regex = r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Proficient %|^Year$",axis=1)

                    # drop all columns from the comparison dataframe that aren't in the school dataframe

                    # because the school file has already been processed, column names will not directly
                    # match, so we create a list of unique substrings from the column names and use it
                    # to filter the comparison set
                    valid_columns = current_school_data.columns.str.split("|").str[0].tolist()

                    comparison_schools = comparison_schools.filter(regex="|".join(valid_columns))

                    # drop any rows where all values in tested cols (proficiency data) are null (remove "Year" from column
                    # list because "Year" will never be null)
                    tested_columns = comparison_schools.columns.tolist()
                    tested_columns.remove("Year")
                    comparison_schools = comparison_schools.dropna(subset=tested_columns,how="all")

                    # add text info columns back
                    comparison_schools = pd.concat([comparison_schools, comparison_schools_info], axis=1, join="inner")

                    # reset indicies
                    comparison_schools = comparison_schools.reset_index(drop=True)

                    ## TODO: Placeholder for HS/AHS data

                    #### Current Year ELA Proficiency Compared to Similar Schools (1.4.c) #
                    category = "School Total|ELA Proficient %"

                    # Get school value for specific category
                    if category in current_school_data.columns:

                        fig14c_k8_school_data = current_school_data[info_categories + [category]].copy()

                        # add corp average for category to dataframe - note we are using 'clean_corp_data'
                        # because the 'Corp' values have been dropped from raw_comparison_data
                        fig14c_k8_school_data.loc[len(fig14c_k8_school_data.index)] = \
                            [corp_name,"3","8",clean_corp_data[clean_corp_data['Category'] == category][string_year].values[0]]

                        fig14c_comp_data = comparison_schools[info_categories + [category]]

                        # Combine data, fix dtypes, and send to chart function
                        fig14c_all_data = pd.concat([fig14c_k8_school_data,fig14c_comp_data])

                        fig14c_table_data = fig14c_all_data.copy()

                        fig14c_all_data[category] = pd.to_numeric(fig14c_all_data[category])

                        fig14c_chart = make_bar_chart(fig14c_all_data, category, school_name, "Comparison: Current Year ELA Proficiency")

                        fig14c_table_data["School Name"] = create_school_label(fig14c_table_data)

                        fig14c_table_data = fig14c_table_data[["School Name", category]]
                        fig14c_table_data = fig14c_table_data.reset_index(drop=True)

                        fig14c_table = create_comparison_table(fig14c_table_data, school_name,"Proficiency")

                    else:
                        # NOTE: This should never ever happen. So yeah.
                        fig14c_chart = no_data_fig_label("Comparison: Current Year ELA Proficiency",200)
                        fig14c_table = no_data_table(["Proficiency"])

                    fig14c = combine_barchart_and_table(fig14c_chart,fig14c_table)

                    #### Current Year Math Proficiency Compared to Similar Schools (1.4.d) #
                    category = "School Total|Math Proficient %"

                    if category in current_school_data.columns:

                        fig14d_k8_school_data = current_school_data[info_categories + [category]].copy()

                        fig14d_k8_school_data.loc[len(fig14d_k8_school_data.index)] = \
                            [corp_name, "3","8",clean_corp_data[clean_corp_data['Category'] == category][string_year].values[0]]

                        # Get comparable school values for the specific category
                        fig14d_comp_data = comparison_schools[info_categories + [category]]

                        fig14d_all_data = pd.concat([fig14d_k8_school_data,fig14d_comp_data])

                        fig14d_table_data = fig14d_all_data.copy()

                        fig14d_all_data[category] = pd.to_numeric(fig14d_all_data[category])

                        fig14d_chart = make_bar_chart(fig14d_all_data,category, school_name, "Comparison: Current Year Math Proficiency")

                        fig14d_table_data["School Name"] = create_school_label(fig14d_table_data)
                        
                        fig14d_table_data = fig14d_table_data[["School Name", category]]
                        fig14d_table_data = fig14d_table_data.reset_index(drop=True)

                        fig14d_table = create_comparison_table(fig14d_table_data, school_name, "Proficiency")
                    
                    else:
                        fig14d_chart = no_data_fig_label("Comparison: Current Year Math Proficiency",200)
                        fig14d_table = no_data_table(["Proficiency"])

                    fig14d = combine_barchart_and_table(fig14d_chart,fig14d_table)

                    #### Current Year IREAD Proficiency Compared to Similar Schools #
                    category = "IREAD Proficient %"

                    if category in current_school_data.columns:

                        fig_iread_k8_school_data = current_school_data[info_categories + [category]].copy()

                        fig_iread_k8_school_data.loc[len(fig_iread_k8_school_data.index)] = \
                            [corp_name, "3","8",clean_corp_data[clean_corp_data['Category'] == category][string_year].values[0]]

                        fig_iread_comp_data = comparison_schools[info_categories + [category]]

                        # drop schools that do not have grade 3
                        fig_iread_comp_data = fig_iread_comp_data.loc[~((pd.to_numeric(fig_iread_comp_data["Low Grade"], errors="coerce") > 3))]

                        fig_iread_all_data = pd.concat([fig_iread_k8_school_data,fig_iread_comp_data])

                        fig_iread_table_data = fig_iread_all_data.copy()

                        fig_iread_all_data[category] = pd.to_numeric(fig_iread_all_data[category])

                        fig_iread_chart = make_bar_chart(fig_iread_all_data,category, school_name, "Comparison: Current Year IREAD Proficiency")

                        fig_iread_table_data["School Name"] = create_school_label(fig_iread_table_data)

                        fig_iread_table_data = fig_iread_table_data[["School Name", category]]
                        fig_iread_table_data = fig_iread_table_data.reset_index(drop=True)

                        fig_iread_table = create_comparison_table(fig_iread_table_data, school_name, "Proficiency")

                    else:
                        fig_iread_chart = no_data_fig_label("Comparison: Current Year IREAD Proficiency",200)
                        fig_iread_table = no_data_table(["Proficiency"])

                    fig_iread = combine_barchart_and_table(fig_iread_chart,fig_iread_table)

                    # ELA Proficiency by Ethnicity Compared to Similar Schools (1.6.a.1)
                    headers_16a1 = []
                    for e in ethnicity:
                        headers_16a1.append(e + "|" + "ELA Proficient %")

                    categories_16a1 =  info_categories + headers_16a1

                    # filter dataframe by categories
                    fig16a1_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16a1))]

                    if len(fig16a1_k8_school_data.columns) > 3:
                        fig16a1_final_data, fig16a1_category_string, fig16a1_school_string = \
                            identify_missing_categories(fig16a1_k8_school_data, current_corp_data, comparison_schools, headers_16a1, corp_name)
                        fig16a1_label = create_chart_label(fig16a1_final_data)
                        fig16a1_chart = make_group_bar_chart(fig16a1_final_data, school_name, fig16a1_label)
                        fig16a1_table_data = combine_school_name_and_grade_levels(fig16a1_final_data)
                        fig16a1_table = create_comparison_table(fig16a1_table_data, school_name,"")

                        fig16a1 = combine_group_barchart_and_table(fig16a1_chart,fig16a1_table,fig16a1_category_string,fig16a1_school_string)
                        
                        fig16a1_container = {"display": "block"}
                        dropdown_container = {"display": "block"}
                    
                    else:
                        fig16a1 = no_data_fig_label("Comparison: ELA Proficiency by Ethnicity", 200)             
                        fig16a1_container = {"display": "none"}

                    # Math Proficiency by Ethnicity Compared to Similar Schools (1.6.b.1)
                    headers_16b1 = []
                    for e in ethnicity:
                        headers_16b1.append(e + "|" + "Math Proficient %")

                    categories_16b1 =  info_categories + headers_16b1

                    fig16b1_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16b1))]

                    if len(fig16b1_k8_school_data.columns) > 3:
                        
                        fig16b1_final_data, fig16b1_category_string, fig16b1_school_string = \
                            identify_missing_categories(fig16b1_k8_school_data, current_corp_data, comparison_schools, headers_16b1, corp_name)
                        fig16b1_label = create_chart_label(fig16b1_final_data)
                        fig16b1_chart = make_group_bar_chart(fig16b1_final_data, school_name, fig16b1_label)
                        fig16b1_table_data = combine_school_name_and_grade_levels(fig16b1_final_data)
                        fig16b1_table = create_comparison_table(fig16b1_table_data, school_name,"")

                        fig16b1 = combine_group_barchart_and_table(fig16b1_chart,fig16b1_table,fig16b1_category_string,fig16b1_school_string)

                        fig16b1_container = {"display": "block"}
                        dropdown_container = {"display": "block"}                   
                    
                    else:
                        fig16b1 = no_data_fig_label("Comparison: Math Proficiency by Ethnicity", 200)
                    
                        fig16b1_container = {"display": "none"}

                    # ELA Proficiency by Subgroup Compared to Similar Schools (1.6.a.2)
                    headers_16a2 = []
                    for s in subgroup:
                        headers_16a2.append(s + "|" + "ELA Proficient %")
                    
                    categories_16a2 =  info_categories + headers_16a2

                    fig16a2_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16a2))]

                    if len(fig16a2_k8_school_data.columns) > 3:
            
                        fig16a2_final_data, fig16a2_category_string, fig16a2_school_string = \
                            identify_missing_categories(fig16a2_k8_school_data, current_corp_data, comparison_schools, headers_16a2, corp_name)
                        fig16a2_label = create_chart_label(fig16a2_final_data)
                        fig16a2_chart = make_group_bar_chart(fig16a2_final_data, school_name, fig16a2_label)
                        fig16a2_table_data = combine_school_name_and_grade_levels(fig16a2_final_data)
                        fig16a2_table = create_comparison_table(fig16a2_table_data, school_name,"")
                        
                        fig16a2 = combine_group_barchart_and_table(fig16a2_chart, fig16a2_table,fig16a2_category_string,fig16a2_school_string)
                        fig16a2_container = {"display": "block"}
                        dropdown_container = {"display": "block"}                
                    
                    else:
                        fig16a2 = no_data_fig_label("Comparison: ELA Proficiency by Subgroup", 200)                
                        fig16a2_container = {"display": "none"}

                    # Math Proficiency by Subgroup Compared to Similar Schools (1.6.b.2)
                    headers_16b2 = []
                    for s in subgroup:
                        headers_16b2.append(s + "|" + "Math Proficient %")

                    categories_16b2 =  info_categories + headers_16b2

                    fig16b2_k8_school_data = current_school_data.loc[:, (current_school_data.columns.isin(categories_16b2))]

                    if len(fig16b2_k8_school_data.columns) > 3:

                        fig16b2_final_data, fig16b2_category_string, fig16b2_school_string = \
                            identify_missing_categories(fig16b2_k8_school_data, current_corp_data, comparison_schools, headers_16b2, corp_name)
                        fig16b2_label = create_chart_label(fig16b2_final_data)
                        fig16b2_chart = make_group_bar_chart(fig16b2_final_data, school_name, fig16b2_label)
                        fig16b2_table_data = combine_school_name_and_grade_levels(fig16b2_final_data)
                        fig16b2_table = create_comparison_table(fig16b2_table_data, school_name,"")

                        fig16b2 = combine_group_barchart_and_table(fig16b2_chart, fig16b2_table,fig16b2_category_string,fig16b2_school_string)
                        fig16b2_container = {"display": "block"}
                        dropdown_container = {"display": "block"}
                    
                    else:
                        fig16b2 = no_data_fig_label("Comparison: Math Proficiency by Subgroup", 200)            
                        fig16b2_container = {"display": "none"}

    return (
        academic_analysis_notes_string, fig14c, fig14d, fig_iread, dropdown_container, fig16a1, 
        fig16a1_container, fig16b1, fig16b1_container, fig16a2, fig16a2_container, fig16b2,
        fig16b2_container, k8_analysis_main_container, k8_analysis_empty_container, k8_analysis_no_data,
        grad_overview, grad_overview_container, grad_ethnicity, grad_ethnicity_container,
        grad_subgroup, grad_subgroup_container, sat_overview, sat_overview_container,
        sat_ethnicity, sat_ethnicity_container, sat_subgroup, sat_subgroup_container,
        hs_analysis_main_container, hs_analysis_empty_container, hs_analysis_no_data
    )

def layout():
    return html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(subnav_academic(),className="tabs"),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                        ],
                        className="row"
                    ),
                    html.Hr(),
                    html.Div(
                        [
                            html.Div(
                                [     
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Label("Academic Comparison - ILEARN Proficiency", className="key_header_label"),
                                                    html.P(""),
                                                        html.P(id="academic-analysis-notes-string",
                                                            style={
                                                                    "textAlign": "Left",
                                                                    "color": "#6783a9",
                                                                    "fontSize": 12,
                                                                    "marginLeft": "10px",
                                                                    "marginRight": "10px",
                                                                    "marginTop": "10px",
                                                            }
                                                        ),
                                                ],
                                                className = "pretty_key_container seven columns"
                                            ),
                                        ],
                                        className = "bare_container_center twelve columns"
                                    ),
                                ],
                                className="row"
                            ),
                            html.Div(
                                [                                        
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.P("Add or Remove Schools: ", className="control_label"),
                                                    dcc.Dropdown(
                                                        id="comparison-dropdown",
                                                        style={"fontSize": "1.1rem"},
                                                        multi = True,
                                                        clearable = False,
                                                        className="multi_dropdown"
                                                    ),
                                                    html.Div(id="input-warning"),
                                                ],
                                            ),
                                        ],
                                        className="row"
                                    ),
                                ],
                                id="dropdown-container",
                                style= {"display": "none"},
                            ),                                         
                            html.Div(id="fig14c", children=[]),
                            html.Div(id="fig14d", children=[]),
                            html.Div(id="fig-iread", children=[]),
                            html.Div(
                                [
                                    html.Div(id="fig16a1"),
                                ],
                                id = "fig16a1-container",
                                style= {"display": "none"},
                            ),
                            html.Div([
                                    html.Div(id="fig16b1"),
                                ],
                                id = "fig16b1-container",
                                style= {"display": "none"},
                            ),
                            html.Div(
                                [      
                            html.Div(id="fig16a2"),
                                ],
                                id = "fig16a2-container",
                                style= {"display": "none"},
                            ),                                 
                            html.Div(
                                [                        
                                    html.Div(id="fig16b2"),
                                ],
                                id = "fig16b2-container",
                                style= {"display": "none"},
                            ),
                        ],
                        id = "k8-analysis-main-container",
                        style= {"display": "none"}, 
                    ),
                    html.Div(
                        [
                            html.Div(id="k8-analysis-no-data"),
                        ],
                        id = "k8-analysis-empty-container",
                    ),
                    
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="hs-grad-overview"),
                                ],
                                id = "hs-grad-overview-container",
                                style= {"display": "none"},
                            ),
                            html.Div([
                                    html.Div(id="hs-grad-ethnicity"),
                                ],
                                id = "hs-grad-ethnicity-container",
                                style= {"display": "none"},
                            ),
                            html.Div(
                                [      
                            html.Div(id="hs-grad-subgroup"),
                                ],
                                id = "hs-grad-subgroup-container",
                                style= {"display": "none"},
                            ),                                 
                            html.Div(
                                [                        
                                    html.Div(id="sat-overview"),
                                ],
                                id = "sat-overview-container",
                                style= {"display": "none"},
                            ),
                            html.Div(
                                [                        
                                    html.Div(id="sat-ethnicity"),
                                ],
                                id = "sat-ethnicity-container",
                                style= {"display": "none"},
                            ),
                            html.Div(
                                [                        
                                    html.Div(id="sat-subgroup"),
                                ],
                                id = "sat-subgroup-container",
                                style= {"display": "none"},
                            ),                                                        
                        ],
                        id = "hs-analysis-main-container",
                        style= {"display": "none"}, 
                    ),
                    html.Div(
                        [
                            html.Div(id="hs-analysis-no-data"),
                        ],
                        id = "hs-analysis-empty-container",
                    ),
                ],
                id="mainContainer"
            )