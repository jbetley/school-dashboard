####################################################
# ICSB Dashboard - Academic Analysis - Single Year #
####################################################
# author:   jbetley (https://github.com/jbetley) 
# version:  1.13
# date:     10/13/23

import dash
from dash import ctx, dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np

# import local functions
from .load_data import ethnicity, subgroup, ethnicity, info_categories, get_school_index, get_school_coordinates, \
    get_comparable_schools, get_k8_corporation_academic_data, get_high_school_academic_data, \
    get_hs_corporation_academic_data, get_selected_k8_school_academic_data
from .process_data import process_high_school_academic_analysis_data, process_selected_k8_academic_data
from .calculations import find_nearest, recalculate_total_proficiency
from .charts import no_data_fig_label, make_bar_chart, make_group_bar_chart
from .tables import create_comparison_table, no_data_page, no_data_table
from .layouts import create_group_barchart_layout, create_barchart_layout, create_hs_analysis_layout
from .string_helpers import create_school_label, combine_school_name_and_grade_levels, create_chart_label, \
     identify_missing_categories

dash.register_page(__name__, name = "Selected Year", path = "/analysis_single_year", top_nav=True, order=10)
    
# Set dropdown options for comparison schools
@callback(
    Output("single-year-comparison-dropdown", "options"),
    Output("single-year-input-warning","children"),
    Output("single-year-comparison-dropdown", "value"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("single-year-comparison-dropdown", "value"),
    Input("analysis-type-radio", "value"),
)
def set_dropdown_options(school_id: str, year: str, comparison_schools: list, analysis_type_value = str):

    # TODO: TEST REMOVING THIS LINE HERE
    # string_year = "2019" if year == "2020" else year
    
    string_year = year
    numeric_year = int(string_year)

    # clear the list of comparison_schools when a new school is
    # selected, otherwise comparison_schools will carry over
    input_trigger = ctx.triggered_id
    if input_trigger == "charter-dropdown":
        comparison_schools = []

    selected_school = get_school_index(school_id)
    school_type = selected_school["School Type"].values[0]

    # There is some time cost for running the dropdown selection function (typically
    # ~0.8 - 1.2s), so we want to exit out as early as possible if we know it isn't necessary
    
    # For AHS we use other AHS as a placeholder
        
    # Get School ID, School Name, Lat & Lon for all schools in the set for selected year
    # SQL query depends on school type
    if school_type == "K12":
        if analysis_type_value == "hs":
            school_type = "HS"
        else:
            school_type = "K8"

    schools_by_distance = get_school_coordinates(numeric_year, school_type)

    # Drop any school not testing at least 20 students. "SchoolTotal|ELATotalTested" is a proxy
    # for school size here (probably only impacts ~20 schools)
    if school_type == "K8":
        schools_by_distance = schools_by_distance[schools_by_distance["School Total|ELA Total Tested"] >= 20] 

    # It is a year when the school didnt exist
    if int(school_id) not in schools_by_distance["School ID"].values:
        return [],[],[]
    
    else:

        # NOTE: Before we do the distance check, we reduce the size of the df by removing
        # schools where there is no, or only a one grade overlap between the comparison schools.
        # the variable "overlap" is one less than the the number of grades that we want as a
        # minimum (a value of "1" means a 2 grade overlap, "2" means 3 grade overlap, etc.).

        # Skip this step for AHS (don't have a 'gradespan' in the technical sense)
        if school_type != "AHS":

            overlap = 1
            schools_by_distance = schools_by_distance.replace({"Low Grade" : { "PK" : 0, "KG" : 1}})
            schools_by_distance["Low Grade"] = schools_by_distance["Low Grade"].astype(int)
            schools_by_distance["High Grade"] = schools_by_distance["High Grade"].astype(int)
            school_grade_span = schools_by_distance.loc[schools_by_distance["School ID"] == int(school_id)][["Low Grade","High Grade"]].values[0].tolist()
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

        school_idx = schools_by_distance[schools_by_distance["School ID"] == int(school_id)].index

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
        comparison_set = comparison_set.drop(comparison_set[comparison_set["School ID"] == int(school_id)].index)

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
                    id="single-year-input-warning",
                    children="Limit reached (Maximum of " + str(max_num_to_display+1) + " schools).",
                )
                options = [
                    {"label": option["label"], "value": option["value"], "disabled": True}
                    for option in default_options
                ]

        return options, input_warning, comparison_schools

@callback(
    Output("single-year-analysis-notes", "children"),
    Output("fig14c", "children"),
    Output("fig14d", "children"),
    Output("fig-iread", "children"),
    Output("single-year-dropdown-container", "style"),
    Output("fig16a1", "children"),   
    Output("fig16a1-container", "style"),    
    Output("fig16b1", "children"),
    Output("fig16b1-container", "style"),
    Output("fig16a2", "children"),
    Output("fig16a2-container", "style"),
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
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("analysis-type-radio", "value"), 
    [Input("single-year-comparison-dropdown", "value")],
)
def update_academic_analysis(school_id: str, year: str, analysis_type_value: str, comparison_school_list: list):
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
    fig16a2 = []
    fig16a2_container = {"display": "none"}
    fig16b2 = []
    fig16b2_container = {"display": "none"}
    dropdown_container = {"display": "none"}

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

    k8_analysis_no_data = no_data_page("No Data to Display.", "Comparison Data - K-8 Academic Data")
    hs_analysis_no_data = no_data_page("No Data to Display.", "Comparison Data - High School Academic Data")

    academic_analysis_notes_label = ""    
    academic_analysis_notes_string = ""
    
    if school_type == "HS" or school_type == "AHS" or (school_type == "K12" and analysis_type_value == "hs"):

        k8_analysis_empty_container = {"display": "none"}

        academic_analysis_notes_label = "Comparison Data - High School"
        academic_analysis_notes_string = "Use this page to view SAT and Graduation Rate comparison data for all ethnicities, \
            and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
            the selected school. Up to eight (8) schools may be displayed at once. Data Source: Indiana Department of Education \
            Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)."
        
        # get data for school
        raw_hs_school_data = get_high_school_academic_data(school_id)

        # filter by selected year
        raw_hs_school_data = raw_hs_school_data.loc[raw_hs_school_data["Year"] == numeric_year]
        raw_hs_school_data = raw_hs_school_data.reset_index(drop=True)
        
        if raw_hs_school_data.empty:
            dropdown_container = {"display": "none"}            
            hs_analysis_empty_container = {"display": "block"}
        
        else:
            hs_school_name = raw_hs_school_data['School Name'].values[0]
            hs_school_name = hs_school_name.strip()

            # get data for corporation
            raw_hs_corp_data = get_hs_corporation_academic_data(school_id)
            hs_corporation_name = raw_hs_corp_data['Corporation Name'].values[0]
            hs_corporation_id = raw_hs_corp_data['Corporation ID'].values[0]

            raw_hs_corp_data = raw_hs_corp_data.loc[raw_hs_corp_data["Year"] == numeric_year]   
            raw_hs_corp_data = raw_hs_corp_data.reset_index(drop=True)

            # need to add some missing categories that aren't in corp df and drop
            # some columns that are in corp df but shouldnt be
            hs_info_columns = ["School Name", "School ID", "Lat", "Lon"]

            add_columns = hs_info_columns + raw_hs_corp_data.columns.tolist()
            raw_hs_corp_data = raw_hs_corp_data.reindex(columns = add_columns)
            
            raw_hs_corp_data['School Name'] = hs_corporation_name
            raw_hs_corp_data['School ID'] = hs_corporation_id
            raw_hs_corp_data['School Type'] = "School Corporation"
            raw_hs_corp_data = raw_hs_corp_data.drop(raw_hs_corp_data.filter(regex="Benchmark %").columns, axis=1)

            # get data for comparable schools (already filtered by selected year in SQL query)
            raw_hs_comparison_data = get_comparable_schools(comparison_school_list, numeric_year, "HS")

            # concatenate all three dataframes together
            combined_hs_data = pd.concat([raw_hs_school_data, raw_hs_corp_data, raw_hs_comparison_data], ignore_index = True)
            
            # calculate values
            processed_hs_data = process_high_school_academic_analysis_data(combined_hs_data)

            hs_analysis_data = processed_hs_data.set_index("Category").T.rename_axis("Year").rename_axis(None, axis=1).reset_index()

            hs_cols = [c for c in hs_analysis_data if c != "School Name"]
            
            # force all to numeric (this removes '***' strings) - we later use NaN as a proxy
            for col in hs_cols:
                hs_analysis_data[col]=pd.to_numeric(hs_analysis_data[col], errors="coerce")

            # drop all columns where the row at school_name_idx has a NaN value
            school_name_idx = hs_analysis_data.index[hs_analysis_data["School Name"].str.contains(hs_school_name)].tolist()[0]
            hs_analysis_data = hs_analysis_data.loc[:, ~hs_analysis_data.iloc[school_name_idx].isna()]

            # check to see if there is data after processing
            if len(hs_analysis_data.columns) <= 5:
                dropdown_container = {"display": "none"}            
                hs_analysis_empty_container = {"display": "block"}
            
            else:

                hs_analysis_main_container = {"display": "block"}
                hs_analysis_empty_container = {"display": "none"}

                # Graduation Comparison Sets
                grad_overview_categories = ["Total", "Non Waiver"]
                grad_overview = create_hs_analysis_layout("Graduation Rate", hs_analysis_data, grad_overview_categories, school_id) #hs_school_name)
                grad_ethnicity = create_hs_analysis_layout("Graduation Rate", hs_analysis_data, ethnicity, school_id)
                grad_subgroup = create_hs_analysis_layout("Graduation Rate", hs_analysis_data, subgroup, school_id)

                # SAT Comparison Sets
                overview = ["School Total|Math", "School Total|EBRW", "School Total|Both"]
                sat_overview = create_hs_analysis_layout("School Total", hs_analysis_data, overview, school_id)        
                sat_ethnicity_ebrw = create_hs_analysis_layout("EBRW", hs_analysis_data, ethnicity, school_id)
                sat_ethnicity_math = create_hs_analysis_layout("Math", hs_analysis_data, ethnicity, school_id)
                sat_subgroup_ebrw = create_hs_analysis_layout("EBRW", hs_analysis_data, subgroup, school_id)
                sat_subgroup_math = create_hs_analysis_layout("Math", hs_analysis_data, subgroup, school_id)

                # Display Logic
             
                if not grad_overview and not grad_ethnicity and not grad_subgroup:
                    grad_overview = no_data_fig_label("Comparison: Graduation Rates", 200, "pretty")
                    grad_overview_container = {"display": "block"}
                else:                    
                    if grad_overview:
                        grad_overview_container = {"display": "block"}
                    else:
                        grad_overview = no_data_fig_label("Comparison: Total/Non Waiver Graduation Rate", 200, "pretty")
                        grad_overview_container = {"display": "block"}

                    if grad_ethnicity:
                        grad_ethnicity_container = {"display": "block"}
                    else:
                        grad_ethnicity = no_data_fig_label("Comparison: Graduation Rate by Ethnicity", 200, "pretty")
                        grad_ethnicity_container = {"display": "block"}

                    if grad_subgroup:
                        grad_subgroup_container = {"display": "block"}
                    else:
                        grad_subgroup = no_data_fig_label("Comparison: Graduation Rate by Subgroup", 200, "pretty")
                        grad_subgroup_container = {"display": "block"}

                if not sat_overview and not sat_ethnicity_ebrw and not sat_ethnicity_math and not \
                    sat_subgroup_ebrw and not sat_subgroup_math:
                    sat_overview = no_data_fig_label("Comparison: % of Students At Benchmark (SAT)", 200, "pretty")
                    sat_overview_container = {"display": "block"}
                else:
                    if sat_overview:
                        sat_overview_container = {"display": "block"}
                    else:
                        sat_overview = no_data_fig_label("Comparison: SAT At Benchmark School Total ", 200, "pretty")
                        sat_overview_container = {"display": "block"}
                
                    if sat_ethnicity_math or sat_ethnicity_ebrw:
                        if not sat_ethnicity_ebrw:
                            sat_ethnicity_ebrw = no_data_fig_label("Comparison: SAT At Benchmark by Ethnicity (EBRW)", 200, "pretty")
                        
                        if not sat_ethnicity_math:
                            sat_ethnicity_math = no_data_fig_label("Comparison: SAT At Benchmark by Ethnicity (Math)", 200, "pretty")

                        sat_ethnicity_container = {"display": "block"}

                    else:
                        sat_ethnicity_container = {"display": "none"}    

                    if sat_subgroup_math or sat_subgroup_ebrw:
                        
                        if not sat_subgroup_ebrw:
                            sat_subgroup_ebrw = no_data_fig_label("Comparison: SAT At Benchmark by Subgroup (EBRW)", 200, "pretty")
                        
                        if not sat_subgroup_math:
                            sat_subgroup_math = no_data_fig_label("Comparison: SAT At Benchmark by Subgroup (Math)", 200, "pretty")                
                        
                        sat_subgroup_container = {"display": "block"}
                    else:
                        sat_subgroup_container = {"display": "none"}
                    
                    # show dropdown container
                    dropdown_container = {"display": "block"}
    
    if school_type == "K8" or school_type == "K12":
                    
        # If school is K12 and highschool tab is selected, skip k8 data
        if school_type == "K12" and analysis_type_value == "hs":
            k8_analysis_main_container = {"display": "none"}
        
        else:

            academic_analysis_notes_label = "Comparison Data - K-8"
            academic_analysis_notes_string = "Use this page to view ILEARN proficiency comparison data for all grades, ethnicities, \
                and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
                the selected school. Up to eight (8) schools may be displayed at once. Data Source: Indiana Department of Education \
                Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)."
        
            # get single year academic data
            list_of_schools = comparison_school_list + [school_id]
            selected_k8_school_data = get_selected_k8_school_academic_data(list_of_schools, year)

            selected_clean_data = process_selected_k8_academic_data(selected_k8_school_data, school_id)

            # NOTE: We don't want to get rid of "***" yet, but we also don't want to pass through a
            # dataframe that that is all "***" - so we convert create a copy, coerce all of the academic
            # columns to numeric and check to see if the entire dataframe for NaN
            check_for_unchartable_data = selected_clean_data.copy()
            check_for_unchartable_data.drop(["School Name", "School ID", "Low Grade", "High Grade", "Year"], axis=1, inplace=True)
            for col in check_for_unchartable_data.columns:
                check_for_unchartable_data[col] = pd.to_numeric(check_for_unchartable_data[col], errors="coerce")

            if ((school_type == "K8" or school_type == "K12") and len(selected_clean_data.index) > 0) and \
                check_for_unchartable_data.isnull().all().all() == False:

                k8_analysis_main_container = {"display": "block"}
                k8_analysis_empty_container = {"display": "none"}

                raw_corp_data = get_k8_corporation_academic_data(school_id)

                selected_corp_data = raw_corp_data.loc[raw_corp_data["Year"] == numeric_year]
                
                # align Name and ID
                selected_corp_data = selected_corp_data.rename(columns = {"Corporation Name": "School Name", "Corporation ID": "School ID"})
                
                # recalculate school totals to align with gradespan of selected school
                revised_school_totals = recalculate_total_proficiency(selected_corp_data, selected_clean_data)

                # replace current school total with revised data                
                selected_corp_data["School Total|Math"] = selected_corp_data["School ID"].map(revised_school_totals.set_index("School ID")["School Total|Math Proficient %"]).fillna(selected_corp_data["School Total|Math"])
                selected_corp_data["School Total|ELA"] = selected_corp_data["School ID"].map(revised_school_totals.set_index("School ID")["School Total|ELA Proficient %"]).fillna(selected_corp_data["School Total|ELA"])
                
                if "IREAD Pass N" in selected_corp_data.columns:
                    selected_corp_data["IREAD"] = pd.to_numeric(selected_corp_data["IREAD Pass N"], errors="coerce") \
                        / pd.to_numeric(selected_corp_data["IREAD Test N"], errors="coerce")

                    # If either Test or Pass category had a "***" value, the resulting value will be 
                    # NaN - we want it to display "***", so we just fillna
                    selected_corp_data["IREAD"] = selected_corp_data["IREAD"].fillna("***")

                # clean up
                selected_corp_data = selected_corp_data[selected_corp_data.columns[~selected_corp_data.columns.str.contains(r"Above|Approaching|At|Tested|Proficient|Pass|Test|ELA and Math|Male|Female")]]
                selected_corp_data = selected_corp_data.rename(columns={c: c + " Proficient %" for c in selected_corp_data.columns if c not in ["Year", "School Name", "School ID"]})

                # only keep columns in school df
                selected_corp_data = selected_corp_data.loc[:, selected_corp_data.columns.isin(selected_clean_data.columns)].copy()
                
                # add last two missing cols
                selected_corp_data["Low Grade"] = "KG"
                selected_corp_data["High Grade"] = "12"

                combined_selected_data = pd.concat([selected_clean_data, selected_corp_data])
                
                # Force '***' to NaN for numeric columns
                numeric_columns = [col for col in combined_selected_data.columns.to_list() if col not in info_categories]
                
                for col in numeric_columns:
                    combined_selected_data[col]=pd.to_numeric(combined_selected_data[col], errors="coerce")                    

                # Now that *** is Nan, we drop all columns where selected school has null data
                school_idx = combined_selected_data.index[combined_selected_data["School ID"] ==  np.int64(school_id)].tolist()[0]
                combined_selected_data = combined_selected_data.loc[:, ~combined_selected_data.iloc[school_idx].isna()]                    
                combined_selected_data = combined_selected_data.reset_index(drop=True)

                # We want to add the information categories back to each dataframe
                added_categories = ["School Name","School ID", "Low Grade","High Grade"]

                #### Current Year ELA Proficiency Compared to Similar Schools (1.4.c) #
                category = "School Total|ELA Proficient %"

                # Get school value for specific category
                if category in combined_selected_data.columns:

                    fig14c_all_data = combined_selected_data[added_categories + [category]].copy()

                    fig14c_table_data = fig14c_all_data.copy()

                    fig14c_all_data[category] = pd.to_numeric(fig14c_all_data[category])

                    fig14c_chart = make_bar_chart(fig14c_all_data, category, school_id, "Comparison: Current Year ELA Proficiency")

                    fig14c_table_data["School Name"] = create_school_label(fig14c_table_data)
                    fig14c_table_data = fig14c_table_data[["School Name", "School ID", category]]
                    fig14c_table_data = fig14c_table_data.reset_index(drop=True)

                    fig14c_table = create_comparison_table(fig14c_table_data, school_id,"ELA Proficiency")
                else:
                    # NOTE: This should never ever happen. So yeah.
                    fig14c_chart = no_data_fig_label("Comparison: Current Year ELA Proficiency",200)
                    fig14c_table = no_data_table("No Data to Display.", "ELA Proficiency", "none")

                fig14c = create_barchart_layout(fig14c_chart,fig14c_table)

                #### Current Year Math Proficiency Compared to Similar Schools (1.4.d) #
                category = "School Total|Math Proficient %"

                if category in combined_selected_data.columns:

                    fig14d_all_data = combined_selected_data[added_categories + [category]].copy()
          
                    fig14d_table_data = fig14d_all_data.copy()

                    fig14d_all_data[category] = pd.to_numeric(fig14d_all_data[category])

                    fig14d_chart = make_bar_chart(fig14d_all_data,category, school_id, "Comparison: Current Year Math Proficiency")

                    fig14d_table_data["School Name"] = create_school_label(fig14d_table_data)
                    
                    fig14d_table_data = fig14d_table_data[["School Name", "School ID", category]]
                    fig14d_table_data = fig14d_table_data.reset_index(drop=True)

                    fig14d_table = create_comparison_table(fig14d_table_data, school_id, "Math Proficiency")
                
                else:
                    fig14d_chart = no_data_fig_label("Comparison: Current Year Math Proficiency",200)
                    fig14d_table = no_data_table("No Data to Display.", "Math Proficiency", "none")

                fig14d = create_barchart_layout(fig14d_chart,fig14d_table)

                #### Current Year IREAD Proficiency Compared to Similar Schools #
                category = "IREAD Proficient %"

                if category in combined_selected_data.columns:

                    fig_iread_all_data = combined_selected_data[added_categories + [category]].copy()

                    fig_iread_table_data = fig_iread_all_data.copy()

                    fig_iread_all_data[category] = pd.to_numeric(fig_iread_all_data[category])

                    fig_iread_chart = make_bar_chart(fig_iread_all_data,category, school_id, "Comparison: Current Year IREAD Proficiency")

                    fig_iread_table_data["School Name"] = create_school_label(fig_iread_table_data)

                    fig_iread_table_data = fig_iread_table_data[["School Name", "School ID", category]]
                    fig_iread_table_data = fig_iread_table_data.reset_index(drop=True)

                    fig_iread_table = create_comparison_table(fig_iread_table_data, school_id, "IREAD Proficiency")

                else:
                    fig_iread_chart = no_data_fig_label("Comparison: Current Year IREAD Proficiency",200)
                    fig_iread_table = no_data_table("No Data to Display.", "IREAD Proficiency", "none")

                fig_iread = create_barchart_layout(fig_iread_chart,fig_iread_table)

                # ELA Proficiency by Ethnicity Compared to Similar Schools (1.6.a.1)

                headers_16a1 = []
                for e in ethnicity:
                    headers_16a1.append(e + "|" + "ELA Proficient %")

                categories_16a1 =  added_categories + headers_16a1

                fig16a1_final_data = combined_selected_data.loc[:, (combined_selected_data.columns.isin(categories_16a1))]

                if len(fig16a1_final_data.columns) > 4:

                    fig16a1_final_data, fig16a1_category_string, fig16a1_school_string = identify_missing_categories(fig16a1_final_data, categories_16a1)

                    fig16a1_label = create_chart_label(fig16a1_final_data)
                    fig16a1_chart = make_group_bar_chart(fig16a1_final_data, school_id, fig16a1_label)
                    fig16a1_table_data = combine_school_name_and_grade_levels(fig16a1_final_data)
                    fig16a1_table = create_comparison_table(fig16a1_table_data, school_id,"")

                    fig16a1 = create_group_barchart_layout(fig16a1_chart,fig16a1_table,fig16a1_category_string,fig16a1_school_string)
                    
                    fig16a1_container = {"display": "block"}
                    dropdown_container = {"display": "block"}
                
                else:
                    fig16a1 = no_data_fig_label("Comparison: ELA Proficiency by Ethnicity", 200)             
                    fig16a1_container = {"display": "none"}

                # Math Proficiency by Ethnicity Compared to Similar Schools (1.6.b.1)
                headers_16b1 = []
                for e in ethnicity:
                    headers_16b1.append(e + "|" + "Math Proficient %")

                categories_16b1 =  added_categories + headers_16b1
                
                fig16b1_final_data = combined_selected_data.loc[:, (combined_selected_data.columns.isin(categories_16b1))]
                
                if len(fig16b1_final_data.columns) > 4:

                    fig16b1_final_data, fig16b1_category_string, fig16b1_school_string = identify_missing_categories(fig16b1_final_data, categories_16b1)                            
                    
                    fig16b1_label = create_chart_label(fig16b1_final_data)
                    fig16b1_chart = make_group_bar_chart(fig16b1_final_data, school_id, fig16b1_label)
                    fig16b1_table_data = combine_school_name_and_grade_levels(fig16b1_final_data)
                    fig16b1_table = create_comparison_table(fig16b1_table_data, school_id,"")

                    fig16b1 = create_group_barchart_layout(fig16b1_chart,fig16b1_table,fig16b1_category_string,fig16b1_school_string)

                    fig16b1_container = {"display": "block"}
                    dropdown_container = {"display": "block"}                   
                
                else:
                    fig16b1 = no_data_fig_label("Comparison: Math Proficiency by Ethnicity", 200)
                
                    fig16b1_container = {"display": "none"}

                # ELA Proficiency by Subgroup Compared to Similar Schools (1.6.a.2)
                headers_16a2 = []
                for s in subgroup:
                    headers_16a2.append(s + "|" + "ELA Proficient %")
                
                categories_16a2 =  added_categories + headers_16a2

                fig16a2_final_data = combined_selected_data.loc[:, (combined_selected_data.columns.isin(categories_16a2))]
             
                if len(fig16a2_final_data.columns) > 4:
        
                    # fig16a2_final_data = merge_schools(fig16a2_k8_school_data, current_corp_data, comparison_schools, headers_16a2, corp_name)
                    fig16a2_final_data, fig16a2_category_string, fig16a2_school_string = identify_missing_categories(fig16a2_final_data, categories_16a2)                            

                    fig16a2_label = create_chart_label(fig16a2_final_data)
                    fig16a2_chart = make_group_bar_chart(fig16a2_final_data, school_id, fig16a2_label)
                    fig16a2_table_data = combine_school_name_and_grade_levels(fig16a2_final_data)
               
                    fig16a2_table = create_comparison_table(fig16a2_table_data, school_id,"")
                    
                    fig16a2 = create_group_barchart_layout(fig16a2_chart, fig16a2_table,fig16a2_category_string,fig16a2_school_string)
                    fig16a2_container = {"display": "block"}
                    dropdown_container = {"display": "block"}                
                
                else:
                    fig16a2 = no_data_fig_label("Comparison: ELA Proficiency by Subgroup", 200)                
                    fig16a2_container = {"display": "none"}

                # Math Proficiency by Subgroup Compared to Similar Schools (1.6.b.2)
                headers_16b2 = []
                for s in subgroup:
                    headers_16b2.append(s + "|" + "Math Proficient %")

                categories_16b2 =  added_categories + headers_16b2

                fig16b2_final_data = combined_selected_data.loc[:, (combined_selected_data.columns.isin(categories_16b2))]

                if len(fig16b2_final_data.columns) > 4:

                    fig16b2_final_data, fig16b2_category_string, fig16b2_school_string = identify_missing_categories(fig16b2_final_data, categories_16b2)

                    fig16b2_label = create_chart_label(fig16b2_final_data)
                    fig16b2_chart = make_group_bar_chart(fig16b2_final_data, school_id, fig16b2_label)
                    fig16b2_table_data = combine_school_name_and_grade_levels(fig16b2_final_data)
                    fig16b2_table = create_comparison_table(fig16b2_table_data, school_id, "")

                    fig16b2 = create_group_barchart_layout(fig16b2_chart, fig16b2_table,fig16b2_category_string,fig16b2_school_string)
                    fig16b2_container = {"display": "block"}
                    dropdown_container = {"display": "block"}
                
                else:
                    fig16b2 = no_data_fig_label("Comparison: Math Proficiency by Subgroup", 200)            
                    fig16b2_container = {"display": "none"}

    academic_analysis_notes = [
            html.Div(
                [        
                    html.Div(
                        [
                            html.Label(academic_analysis_notes_label, className="key-label__header"),
                            html.P(""),
                                html.P(academic_analysis_notes_string,
                                    style={
                                            "textAlign": "Left",
                                            "color": "#6783a9",
                                            "fontSize": "1.2rem",
                                            "margin": "10px"
                                    }
                                ),
                        ],
                        className = "pretty-container__key seven columns"
                    )
                ],
                className = "bare-container--flex--center twelve columns"
            )        
        ]

    return (
        academic_analysis_notes, fig14c, fig14d, fig_iread, dropdown_container, fig16a1, 
        fig16a1_container, fig16b1, fig16b1_container, fig16a2, fig16a2_container, fig16b2,
        fig16b2_container, k8_analysis_main_container, k8_analysis_empty_container, k8_analysis_no_data,
        grad_overview, grad_overview_container, grad_ethnicity, grad_ethnicity_container,
        grad_subgroup, grad_subgroup_container, sat_overview, sat_overview_container,
        sat_ethnicity_ebrw, sat_ethnicity_math, sat_ethnicity_container,
        sat_subgroup_ebrw, sat_subgroup_math, sat_subgroup_container,
        hs_analysis_main_container, hs_analysis_empty_container, hs_analysis_no_data
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
                                                    html.Div("Add or Remove Schools: ", className="comparison-dropdown-label"),
                                                ],
                                                className="bare-container two columns"
                                            ),
                                            html.Div(
                                                [                                            
                                                    dcc.Dropdown(
                                                        id="single-year-comparison-dropdown",
                                                        style={"fontSize": "1.1rem"},
                                                        multi = True,
                                                        clearable = False,
                                                        className="comparison-dropdown-control"
                                                    ),
                                                    html.Div(id="single-year-input-warning"),
                                                ],
                                                className="bare-container eight columns"
                                            ),
                                        ],
                                        className="comparison-dropdown-row"
                                    ),
                                ],
                                id="single-year-dropdown-container",
                                style= {"display": "none"},
                            ),
                            html.Div(
                                [      
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
                                    html.Div(
                                        [     
                                            html.Div(id="single-year-analysis-notes", children=[]),
                                        ],
                                        className="row"
                                    ),                                    
                                ],
                                id = "k8-analysis-single-main-container",
                                style= {"display": "none"}, 
                            ),
                            html.Div(
                                [
                                    html.Div(id="k8-analysis-single-no-data"),
                                ],
                                id = "k8-analysis-single-empty-container",
                            ),
                            html.Div(
                                [                                      
                                    html.Div(
                                        [
                                            html.Div(id="grad-overview"),
                                        ],
                                        id = "grad-overview-container",
                                        style= {"display": "none"},
                                    ),
                                    html.Div([
                                            html.Div(id="grad-ethnicity"),
                                        ],
                                        id = "grad-ethnicity-container",
                                        style= {"display": "none"},
                                    ),
                                    html.Div(
                                        [      
                                    html.Div(id="grad-subgroup"),
                                        ],
                                        id = "grad-subgroup-container",
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
                                            html.Div(id="sat-ethnicity-ebrw"),
                                            html.Div(id="sat-ethnicity-math"),                                            
                                        ],
                                        id = "sat-ethnicity-container",
                                        style= {"display": "none"},
                                    ),
                                    html.Div(
                                        [                        
                                            html.Div(id="sat-subgroup-ebrw"),
                                            html.Div(id="sat-subgroup-math"),                                            
                                        ],
                                        id = "sat-subgroup-container",
                                        style= {"display": "none"},
                                    ),                                                        
                                ],
                                id = "hs-analysis-single-main-container",
                                style= {"display": "none"}, 
                            ),
                            html.Div(
                                [
                                    html.Div(id="hs-analysis-single-no-data"),
                                ],
                                id = "hs-analysis-single-empty-container",
                            ),
                        ],
                        id="single-academic-analysis-page"
                    )                            
                ],
                id="main-container"
            )