#######################################################
# ICSB Dashboard - Academic Analysis - Year over Year #
#######################################################
# author:   jbetley
# version:  1.11
# date:     10/03/23

import dash
from dash import ctx, dcc, html, Input, State, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd

# import local functions
from .load_data import get_k8_school_academic_data, get_school_index, get_gradespan, get_ethnicity, get_subgroup, \
    get_school_coordinates, get_comparable_schools, get_k8_corporation_academic_data, get_high_school_academic_data, \
    get_hs_corporation_academic_data, get_year_over_year_data, get_excluded_years
from .process_data import process_k8_academic_data, process_k8_corp_academic_data, process_high_school_academic_analysis_data
from .calculations import find_nearest, calculate_proficiency, recalculate_total_proficiency
from .tables import no_data_page
from .layouts import create_radio_layout, create_year_over_year_layout
from .calculate_metrics import calculate_k8_comparison_metrics

from .subnav import subnav_academic_analysis

dash.register_page(__name__, name = "Year over Year", path = "/analysis_multiple_year", top_nav=False, order=11)

# Gradespan selection (K12 Only)
@callback(      
    Output("multi-year-gradespan-radio", "options"),
    Output("multi-year-gradespan-radio", "value"),
    Output('multi-year-gradespan-radio-container', 'style'),
    Input("charter-dropdown", "value"),
    State("multi-year-gradespan-radio", "value"),
)
def radio_gradespan_selector(school: str, gradespan_state: str):

    gradespan_value = "k8"
    gradespan_options = []
    gradespan_container = {'display': 'none'}

    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]

    if school_type == "K12":
        gradespan_options = [
            {"label": "K-8", "value": "k8"},
            {"label": "High School", "value": "hs"},
        ]
        gradespan_container = {'display': 'block'}

        if gradespan_state:
            gradespan_value = gradespan_state
    
    elif school_type == "AHS" or school_type == "HS":
        gradespan_value = "hs"

    return gradespan_options, gradespan_value, gradespan_container

# HS Grad Rate or SAT Selector
@callback(      
    Output("multi-year-hs-category-radio", "options"),
    Output("multi-year-hs-category-radio","value"),
    Output("multi-year-hs-category-radio-container", "style"),
    Input("charter-dropdown", "value"),
    Input("multi-year-gradespan-radio","value"),    
    State("multi-year-hs-category-radio", "value"),
)
def radio_hs_category_selector(school: str, gradespan_value: str, hs_category_state: str):

    hs_category_value = ""
    hs_category_options = []
    hs_category_container = {'display': 'none'}

    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]

    if school_type == "HS" or school_type == "AHS" or (gradespan_value == "hs" and school_type == "K12"):
        hs_category_options = [
            {"label": "SAT", "value": "SAT"},
            {"label": "Graduation Rate", "value": "Graduation Rate"},
        ]
        hs_category_container = {'display': 'block'}

        if hs_category_state:
            hs_category_value = hs_category_state
        else:
            hs_category_value = "Graduation Rate"

    return hs_category_options, hs_category_value, hs_category_container

# Subject selector
@callback(
    Output("multi-year-subject-radio", "options"),
    Output("multi-year-subject-radio","value"),
    Output("multi-year-subject-radio-container","style"),  
    Input("charter-dropdown", "value"),
    Input("multi-year-gradespan-radio","value"),
    Input("multi-year-hs-category-radio","value"),
    State("multi-year-subject-radio","value"),
)
def radio_subject_selector(school: str, gradespan_value: str, hs_category_value: str, subject_state: str):

    subject_value = ""
    subject_options = []    # type:list
    subject_container = {'display': 'none'}

    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]

    if hs_category_value == "Graduation Rate" and (school_type == "HS" or school_type == "AHS" or school_type == "K12"):
        return subject_options, subject_value, subject_container
    
    else:

        if school_type == "K8" or (school_type == "K12" and gradespan_value == "k8"):

            subject_options = [
                {"label": "ELA", "value": "ELA"},
                {"label": "Math", "value": "Math"},
            ]
            subject_container = {'display': 'block'}
        
            if subject_state and subject_state in ["ELA", "Math"]:
                subject_value = subject_state
            else:
                subject_value = "ELA"

        elif school_type == "HS" or school_type == "AHS" or (school_type == "K12" and gradespan_value == "hs"):

            subject_options = [
                {"label": "EBRW", "value": "EBRW"},
                {"label": "Math", "value": "Math"},
            ]   
            subject_container = {'display': 'block'}

            if subject_state and subject_state in ["EBRW", "Math"]:
                subject_value = subject_state
            else:
                subject_value = "EBRW"

    return subject_options, subject_value, subject_container

# Main Category selector
@callback(
    Output("multi-year-category-radio", "options"),
    Output("multi-year-category-radio","value"),
    Output("multi-year-category-radio-container","style"),    
    Input("charter-dropdown", "value"),
    Input("multi-year-gradespan-radio","value"),
    Input("multi-year-hs-category-radio","value"),    
    State("multi-year-category-radio","value"),
)
def top_level_selector(school: str, gradespan_value: str, hs_category_value: str, category_state: str):

    category_value = "School Total"
    category_options = [] 
    category_container = {'display': 'none'}
    
    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]

    if school_type == "K8" or (school_type == "K12" and gradespan_value == "k8"):

        category_options = [
            {"label": "By Grade", "value": "By Grade"},
            {"label": "By Subgroup", "value": "By Subgroup"},
            {"label": "By Ethnicity", "value": "By Ethnicity"},
        ]
        category_container = {'display': 'block'}

        if category_state and category_state in ["By Grade", "By Subgroup", "By Ethnicity"]:
            category_value = category_state
        else:
            category_value = "By Grade"

    elif school_type == "HS" or school_type == "AHS" or (school_type == "K12" and gradespan_value == "hs"):

        if hs_category_value == "Graduation Rate" or hs_category_value == "": # is None:

            category_options = [
                {"label": "Total", "value": "Total"},
                {"label": "By Subgroup", "value": "By Subgroup"},
                {"label": "By Ethnicity", "value": "By Ethnicity"},
            ]
            category_container = {'display': 'block'}

            if category_state and category_state in ["Total", "By Subgroup", "By Ethnicity"]:
                category_value = category_state
            else:
                category_value = "Total"

        else:
            category_options = [
                {"label": "School Total", "value": "School Total"},
                {"label": "By Subgroup", "value": "By Subgroup"},
                {"label": "By Ethnicity", "value": "By Ethnicity"},
            ]
            category_container = {'display': 'block'}

            if category_state and category_state in ["School Total", "By Subgroup", "By Ethnicity"]:
                category_value = category_state
            else:
                category_value = "School Total"

    return category_options, category_value, category_container

# Subcategory selector
@callback(
    Output("multi-year-subcategory-radio", "options"),
    Output("multi-year-subcategory-radio","value"),
    Output("multi-year-subcategory-radio-container","style"),    
    Input("charter-dropdown", "value"),
    Input("multi-year-category-radio","value"),
    State("multi-year-subcategory-radio","value"),
    State("multi-year-gradespan-radio", "value"),
    State("multi-year-hs-category-radio","value")
)
def radio_subcategory_selector(school: str, category_value: str, subcategory_state: str, 
                               gradespan_state: str, hs_category_state: str):

    # default values
    subcategory_value = ""
    subcategory_options = []  # type: list
    subcategory_container = {'display': 'none'}
    
    if category_value == "By Grade":
        grades = get_gradespan(school)
        subcategory_options = [{"label": g, "value": "Grade " + g} for g in grades]
        subcategory_options.append({"label": "Total", "value": "School Total"})

        if subcategory_state and subcategory_state in grades:
            subcategory_value = subcategory_state
        else:
            subcategory_value = "School Total"

        subcategory_container = {'display': 'block'}

    elif category_value == "By Ethnicity":
        ethnicity = get_ethnicity(school, gradespan_state, hs_category_state)
        subcategory_options = [{"label": e, "value": e} for e in ethnicity]

        if subcategory_state and subcategory_state in ethnicity:
            subcategory_value = subcategory_state
        else:
            subcategory_value = "Black"
        
        subcategory_container = {'display': 'block'}

    elif category_value == "By Subgroup":
        print(gradespan_state)
        print(hs_category_state)
        subgroup = get_subgroup(school, gradespan_state, hs_category_state)
        subcategory_options = [{"label": s, "value": s} for s in subgroup]           

        print(subgroup)
        if subcategory_state and subcategory_state in subgroup:
            subcategory_value = subcategory_state
        else:         
            subcategory_value = "General Education"

        subcategory_container = {'display': 'block'}

    return subcategory_options, subcategory_value, subcategory_container
    
# Set dropdown options for comparison schools
@callback(
    Output("multi-year-comparison-dropdown", "options"),
    Output("multi-year-input-warning","children"),
    Output("multi-year-comparison-dropdown", "value"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("multi-year-comparison-dropdown", "value"),
    Input("multi-year-gradespan-radio", "value"),    
)
def set_dropdown_options(school: str, year: str, comparison_schools: list, gradespan_value = str):

    string_year = "2019" if year == "2020" else year
    numeric_year = int(string_year)

    # clear the list of comparison_schools when a new school is
    # selected, otherwise comparison_schools will carry over
    input_trigger = ctx.triggered_id
    if input_trigger == "charter-dropdown":
        comparison_schools = []

    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]

    # There is some time cost for running the dropdown selection function (typically
    # ~0.8 - 1.2s), so we want to exit out as early as possible if we know it isn't necessary
    
    # For AHS we use other AHS as a placeholder
    # if (school_type == "AHS"):
    #     return [],[],[]
        
    # Get School ID, School Name, Lat & Lon for all schools in the set for selected year
    # SQL query depends on school type
    if school_type == "K12":
        if gradespan_value == "hs":
            school_type = "HS"
        else:
            school_type = "K8"

    schools_by_distance = get_school_coordinates(numeric_year, school_type)

    # Drop any school not testing at least 20 students. "SchoolTotal|ELATotalTested" is a proxy
    # for school size here (probably only impacts ~20 schools)
    if school_type == "K8":
        schools_by_distance = schools_by_distance[schools_by_distance["School Total|ELA Total Tested"] >= 20] 

    # It is a year when the school didnt exist
    if int(school) not in schools_by_distance["School ID"].values:
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
                    id="multi-year-input-warning",
                    children="Limit reached (Maximum of " + str(max_num_to_display+1) + " schools).",
                )
                options = [
                    {"label": option["label"], "value": option["value"], "disabled": True}
                    for option in default_options
                ]

        return options, input_warning, comparison_schools

@callback(
    Output("multi-year-analysis-notes", "children"),
    Output("year-over-year-grade", "children"),
    Output("year-over-year-hs", "children"),       
    Output("multi-year-dropdown-container", "style"),
    Output("k8-analysis-multi-main-container", "style"),
    Output("k8-analysis-multi-empty-container", "style"),
    Output("k8-analysis-multi-no-data", "children"),
    Output("hs-analysis-multi-main-container", "style"),
    Output("hs-analysis-multi-empty-container", "style"),
    Output("hs-analysis-multi-no-data", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("multi-year-gradespan-radio", "value"),
    Input("multi-year-subject-radio", "value"),
    Input("multi-year-subcategory-radio", "value"),
    Input("multi-year-hs-category-radio", "value"),    
    [Input("multi-year-comparison-dropdown", "value")],
)
def update_academic_analysis(school: str, year: str, gradespan_value: str, subject_radio: str, subcategory_radio: str, 
                                hs_category: str, comparison_school_list: list):
    if not school:
        raise PreventUpdate

    # show 2019 instead of 2020 as 2020 has no academic data
    string_year = "2019" if year == "2020" else year
    numeric_year = int(string_year)

    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]
    school_name = selected_school["School Name"].values[0]

    # Radio buttons don't play nice
    if not gradespan_value:
        gradespan_value = "k8"

    # default values (only empty container displayed)
    hs_analysis_multi_main_container = {"display": "none"}
    hs_analysis_multi_empty_container = {"display": "none"}
    k8_analysis_multi_main_container = {"display": "none"}
    k8_analysis_multi_empty_container = {"display": "block"}

    dropdown_container = {"display": "none"}

    k8_analysis_multi_no_data = no_data_page("Comparison Data - K-8 Academic Data")
    hs_analysis_multi_no_data = no_data_page("Comparison Data - High School Academic Data")

    analysis__multi_notes_label = ""    
    analysis__multi_notes_string = ""

    if school_type == "HS" or school_type == "AHS" or (school_type == "K12" and gradespan_value == "hs"):

        k8_analysis_multi_empty_container = {"display": "none"}
        year_over_year_grade = []

        analysis__multi_notes_label = "Comparison Data - High School"
        analysis__multi_notes_string = "Use this page to view SAT and Graduation Rate comparison data for all ethnicities, \
            and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
            the selected school. Up to eight (8) schools may be displayed at once. Data Source: Indiana Department of Education \
            Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)."
        
        # get data for school
        raw_hs_school_data = get_high_school_academic_data(school)

        if raw_hs_school_data.empty:
            dropdown_container = {"display": "none"}            
            hs_analysis_multi_empty_container = {"display": "block"}
        
        else:
            hs_school_name = raw_hs_school_data['School Name'].values[0]

            # filter by selected year
            raw_hs_school_data = raw_hs_school_data.loc[raw_hs_school_data["Year"] == numeric_year]
            raw_hs_school_data = raw_hs_school_data.reset_index(drop=True)

            # get data for corporation
            raw_hs_corp_data = get_hs_corporation_academic_data(school)
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

            hs_analysis_multi_data = processed_hs_data.set_index("Category").T.rename_axis("Year").rename_axis(None, axis=1).reset_index()

            hs_cols = [c for c in hs_analysis_multi_data if c != "School Name"]
            
            # force all to numeric (this removes '***' strings) - we later use NaN as a proxy
            for col in hs_cols:
                hs_analysis_multi_data[col]=pd.to_numeric(hs_analysis_multi_data[col], errors="coerce")

            # drop all columns where the row at school_name_idx has a NaN value
            school_name_idx = hs_analysis_multi_data.index[hs_analysis_multi_data["School Name"].str.contains(hs_school_name)].tolist()[0]
            hs_analysis_multi_data = hs_analysis_multi_data.loc[:, ~hs_analysis_multi_data.iloc[school_name_idx].isna()]

            # check to see if there is data after processing
            if len(hs_analysis_multi_data.columns) <= 4:
                dropdown_container = {"display": "none"}            
                hs_analysis_multi_empty_container = {"display": "block"}
                year_over_year_hs = []
            else:

                hs_analysis_multi_main_container = {"display": "block"}
                hs_analysis_multi_empty_container = {"display": "none"}

                ## Year Over Year HS (SAT and Graduation Rate) Chart
                if hs_category == "SAT":
                    if subcategory_radio:
                        category = subcategory_radio + "|" + subject_radio
                    else:
                        category = "School Total|EBRW"

                    label = "Year over Year Comparison (SAT At Benchmark) - " + category

                    year_over_year_hs_data = get_year_over_year_data(school, comparison_school_list, category , year, "sat")

                elif hs_category == "Graduation Rate" or hs_category == "":
                    if subcategory_radio:
                        category = subcategory_radio + "|"
                    else:
                        category = "Total|"

                    label = "Year over Year Comparison (Graduation Rate) - " + category[:-1]

                    year_over_year_hs_data= get_year_over_year_data(school, comparison_school_list, category , year, "grad")                    

                year_over_year_hs = create_year_over_year_layout(school_name, year_over_year_hs_data, label)

                # show dropdown container
                dropdown_container = {"display": "block"}

    if school_type == "K8" or school_type == "K12":
                    
        # If school is K12 and highschool tab is selected, skip k8 data
        if school_type == "K12" and gradespan_value == "hs":
            k8_analysis_multi_main_container = {"display": "none"}
        
        else:

            analysis__multi_notes_label = "Comparison Data - K-8"
            analysis__multi_notes_string = "Use this page to view ILEARN proficiency comparison data for all grades, ethnicities, \
                and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
                the selected school. Up to eight (8) schools may be displayed at once. Data Source: Indiana Department of Education \
                Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)."
        
            # get academic data
            selected_raw_k8_school_data = get_k8_school_academic_data(school)

            excluded_years = get_excluded_years(year)

            if excluded_years:
                selected_raw_k8_school_data = selected_raw_k8_school_data[~selected_raw_k8_school_data["Year"].isin(excluded_years)]

            if ((school_type == "K8" or school_type == "K12") and len(selected_raw_k8_school_data.index) > 0):

                selected_raw_k8_school_data = selected_raw_k8_school_data.replace({"^": "***"})

                clean_school_data = process_k8_academic_data(selected_raw_k8_school_data)

                if not clean_school_data.empty:

                    year_over_year_hs = []

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

                        k8_analysis_multi_main_container = {"display": "block"}
                        k8_analysis_multi_empty_container = {"display": "none"}

                        raw_comparison_data = raw_comparison_data.drop('Test Year', axis=1)

                        school_academic_data = raw_comparison_data[[col for col in raw_comparison_data.columns if "School" in col or "Category" in col]].copy()
                        school_academic_data.columns = school_academic_data.columns.str.replace(r"School$", "", regex=True)

                        display_academic_data = school_academic_data.set_index("Category").T.rename_axis("Year").rename_axis(None, axis=1).reset_index()

                        # add suffix to certain Categories
                        display_academic_data = display_academic_data.rename(columns={c: c + " Proficient %" for c in display_academic_data.columns if c not in ["Year", "School Name"]})

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

                        comparison_schools_filtered = get_comparable_schools(comparison_school_list, numeric_year, "K8")

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

                        ## K8 Year Over Year Chart
                        if subcategory_radio:
                            category = subcategory_radio + "|" + subject_radio
                        else:
                            category = "School Total|ELA"

                        label = "Year over Year Comparison - " + category

                        year_over_year_k8_data = get_year_over_year_data(school,comparison_school_list, category, year, "k8")                        
                        year_over_year_grade = create_year_over_year_layout(school_name, year_over_year_k8_data, label)

                        dropdown_container = {"display": "block"}

    analysis__multi_notes = [
            html.Div(
                [        
                    html.Div(
                        [
                            html.Label(analysis__multi_notes_label, className="key-label__header"),
                            html.P(""),
                                html.P(analysis__multi_notes_string,
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
        analysis__multi_notes, year_over_year_grade, year_over_year_hs, dropdown_container,
        k8_analysis_multi_main_container, k8_analysis_multi_empty_container, k8_analysis_multi_no_data,
        hs_analysis_multi_main_container, hs_analysis_multi_empty_container, hs_analysis_multi_no_data
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
                                            html.Div(subnav_academic_analysis(), id="subnav-academic", className="tabs"),
                                        ],
                                        className="bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className="row",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(create_radio_layout("multi-year", "gradespan"),className="tabs"),

                                        ],
                                        className = "bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className = "row",
                            ),                             
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(create_radio_layout("multi-year", "hs-category"),className="tabs"),

                                        ],
                                        className = "bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className = "row",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(create_radio_layout("multi-year", "subject", "six"),className="tabs"),
                                            html.Div(create_radio_layout("multi-year", "category", "six"),className="tabs"),
                                        ],
                                        className = "bare-container--flex--center_subnav twelve columns",
                                    ),
                                ],
                                className = "row",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(create_radio_layout("multi-year", "subcategory"),className="tabs"),

                                        ],
                                        className = "bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className = "row",
                            ),
                            html.Hr(className = "line_bottom"),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.P("Add or Remove Schools: ", className="multi-year-comparison-dropdown-label"),
                                                    dcc.Dropdown(
                                                        id="multi-year-comparison-dropdown",
                                                        style={"fontSize": "1.1rem"},
                                                        multi = True,
                                                        clearable = False,
                                                        className="multi-year-comparison-dropdown-control"
                                                    ),
                                                    html.Div(id="multi-year-input-warning"),
                                                ],
                                            ),
                                        ],
                                        className="row"
                                    ),
                                ],
                                id="multi-year-dropdown-container",
                                style= {"display": "none"},
                            ),
                            html.Div(
                                [      
                                    html.Div(id="year-over-year-grade", children=[]),                               
                                    html.Div(
                                        [     
                                            html.Div(id="multi-year-analysis-notes", children=[]),
                                        ],
                                        className="row"
                                    ),                                    
                                ],
                                id = "k8-analysis-multi-main-container",
                                style= {"display": "none"}, 
                            ),
                            html.Div(
                                [
                                    html.Div(id="k8-analysis-multi-no-data"),
                                ],
                                id = "k8-analysis-multi-empty-container",
                            ),
                            html.Div(
                                [
                                    html.Div(id="year-over-year-hs", children=[]),                                         
                                ],
                                id = "hs-analysis-multi-main-container",
                                style= {"display": "none"}, 
                            ),
                            html.Div(
                                [
                                    html.Div(id="hs-analysis-multi-no-data"),
                                ],
                                id = "hs-analysis-multi-empty-container",
                            ),
                        ],
                        id="multi-academic-analysis-page"
                    )                            
                ],
                id="main-container"
            )