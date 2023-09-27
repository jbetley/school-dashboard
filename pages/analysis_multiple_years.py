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
from .load_data import get_school_index, get_gradespan, get_ethnicity, get_subgroup, get_school_coordinates, \
    get_year_over_year_data
from .calculations import find_nearest
from .tables import no_data_page
from .layouts import create_radio_layout, create_year_over_year_layout
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
        else:
            gradespan_value = "k8"
    
    elif school_type == "AHS" or school_type == "HS":
        gradespan_value = "hs"

    else:
        gradespan_value = "k8"

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
            {"label": "Graduation Rate", "value": "Graduation Rate"},
            {"label": "SAT", "value": "SAT"}
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
    # Both ILEARN and SAT have subject categories, although the name for english is different: ELA/EBRW;
    # Graduation Rate does not have subject categories
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

    category_value = ""
    category_options = [] 
    category_container = {'display': 'none'}
    
    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]

    if school_type == "K8" or (school_type == "K12" and gradespan_value == "k8"):

        category_options = [
            {"label": "Grade", "value": "Grade"},
            {"label": "Subgroup", "value": "Subgroup"},
            {"label": "Race/Ethnicity", "value": "Race/Ethnicity"},
        ]
        category_container = {'display': 'block'}

        if category_state and category_state in ["Grade", "Subgroup", "Race/Ethnicity"]:
            category_value = category_state
        else:
            category_value = "Grade"

    elif school_type == "HS" or school_type == "AHS" or (school_type == "K12" and gradespan_value == "hs"):

        if hs_category_value == "Graduation Rate" or hs_category_value == "":

            category_options = [
                {"label": "Total", "value": "Total"},
                {"label": "Subgroup", "value": "Subgroup"},
                {"label": "Race/Ethnicity", "value": "Race/Ethnicity"},
            ]
            category_container = {'display': 'block'}

            if category_state and category_state in ["Total", "Subgroup", "Race/Ethnicity"]:
                category_value = category_state
            else:
                category_value = "Total"

        else:
            category_options = [
                {"label": "School Total", "value": "School Total"},
                {"label": "Subgroup", "value": "Subgroup"},
                {"label": "Race/Ethnicity", "value": "Race/Ethnicity"},
            ]
            category_container = {'display': 'block'}

            if category_state and category_state in ["School Total", "Subgroup", "Race/Ethnicity"]:
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

    if category_value == "Grade":
        grades = get_gradespan(school)

        if grades:
            subcategory_options = [{"label": g, "value": "Grade " + g} for g in grades]
            subcategory_options.append({"label": "Total", "value": "School Total"})

            if subcategory_state and subcategory_state in grades:
                subcategory_value = subcategory_state
            else:
                subcategory_value = "School Total"

            subcategory_container = {'display': 'block'}

        else:
            subcategory_value = "No Data"
    
    elif category_value == "Race/Ethnicity":
        ethnicity = get_ethnicity(school, gradespan_state, hs_category_state)
        subcategory_options = [{"label": e, "value": e} for e in ethnicity]
        ethnicity.sort()

        if ethnicity:
            if subcategory_state and subcategory_state in ethnicity:
                subcategory_value = subcategory_state
            else:
                subcategory_value = ethnicity[0]
            
            subcategory_container = {'display': 'block'}
        else:
            subcategory_value = "No Race/Ethnicity Data"

    elif category_value == "Subgroup":

        subgroup = get_subgroup(school, gradespan_state, hs_category_state)
        subgroup.sort()

        if subgroup:
            subcategory_options = [{"label": s, "value": s} for s in subgroup]           

            if subcategory_state and subcategory_state in subgroup:
                subcategory_value = subcategory_state
            
            else:
                subcategory_value = subgroup[0]

            subcategory_container = {'display': 'block'}
        else:
            subcategory_value = "No Subgroup Data"

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
    # the second condition ensures that the school is retained if it exists
    if school_type == "K8":
        schools_by_distance = schools_by_distance[(schools_by_distance["School Total|ELA Total Tested"] >= 20) | 
            (schools_by_distance["School ID"] == int(school))]

    # If school doesn't exist
    if int(school) not in schools_by_distance["School ID"].values:
        return [],[],[]
    
    else:

        # NOTE: Before we do the distance check, we reduce the size of the df removing
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

        # Merge School ID with Distances index
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
        default_num_to_display = 3
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
    year = "2019" if year == "2020" else year

    selected_school = get_school_index(school)
    school_type = selected_school["School Type"].values[0]
    school_name = selected_school["School Name"].values[0]
    school_name = school_name.strip()

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
        
        # get data for school (these labels are used to generate the message on the empty tables)
        if (subcategory_radio != "No Subgroup Data" and subcategory_radio != "No Race/Ethnicity Data" and
                subcategory_radio != "No Data"):
                    
            if hs_category == "SAT":
                if subcategory_radio:
                    category = subcategory_radio + "|" + subject_radio
                else:
                    category = "School Total|EBRW"

                label = "Year over Year Comparison (SAT At Benchmark) - " + category
                msg = ""

                year_over_year_hs_data = get_year_over_year_data(school, comparison_school_list, category , year, "sat")
                
            elif hs_category == "Graduation Rate" or hs_category == "":
                if subcategory_radio:
                    category = subcategory_radio + "|"
                else:
                    category = "Total|"

                label = "Year over Year Comparison (Graduation Rate) - " + category[:-1]
                msg = ""

                year_over_year_hs_data= get_year_over_year_data(school, comparison_school_list, category, year, "grad")                    
        else:

            year_over_year_hs_data = pd.DataFrame()
            
            if subcategory_radio == "No Data" or subcategory_radio == "":
                label = "Year over Year Comparison (" + hs_category + ")"
                msg = "No Data for Selected School."
            else:
                label = "Year over Year Comparison (" + hs_category + ") - " + subcategory_radio[3:-5:]
                msg = subcategory_radio + " for Selected School."

        if year_over_year_hs_data.empty:

            dropdown_container = {"display": "none"}            
            hs_analysis_multi_empty_container = {"display": "block"}
            year_over_year_hs = []

        else:
            hs_analysis_multi_main_container = {"display": "block"}
            hs_analysis_multi_empty_container = {"display": "none"}
            dropdown_container = {"display": "block"}

            ## Create Year Over Year HS (SAT and Graduation Rate) Chart
            year_over_year_hs = create_year_over_year_layout(school, year_over_year_hs_data, label, msg)

    elif school_type == "K8" or (school_type == "K12" and gradespan_value == "k8"):
                
        hs_analysis_multi_main_container =  {"display": "none"}
        year_over_year_hs = []

        analysis__multi_notes_label = "Comparison Data - K-8"
        analysis__multi_notes_string = "Use this page to view ILEARN proficiency comparison data for all grades, ethnicities, \
            and subgroups. The dropdown list consists of the twenty (20) closest schools that overlap at least two grades with \
            the selected school. Up to eight (8) schools may be displayed at once. Data Source: Indiana Department of Education \
            Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)."

        ## K8 Year Over Year Chart
        if (subcategory_radio != "No Subgroup Data" and subcategory_radio != "No Race/Ethnicity Data" and
                subcategory_radio != "No Data"):

            if subcategory_radio:
                category = subcategory_radio + "|" + subject_radio
            else:
                category = "School Total|ELA"

            label = "Year over Year Comparison - " + category
            msg = ""

            year_over_year_k8_data = get_year_over_year_data(school, comparison_school_list, category, year, "k8")

        else:

            year_over_year_k8_data = pd.DataFrame()
            
            if subcategory_radio == "No Data" or subcategory_radio == "":
                label = "Year over Year Comparison (" + subcategory_radio + "|" + subject_radio + ")"
                msg = "No Data for Selected School."
            else:
                label = "Year over Year Comparison (" + subcategory_radio + "|" + subject_radio + ") - " + subcategory_radio[3:-5:]
                msg = subcategory_radio + " for Selected School."

        if year_over_year_k8_data.empty:

            dropdown_container = {"display": "none"}            
            k8_analysis_multi_empty_container = {"display": "block"}
            year_over_year_hs = []

        else:
            k8_analysis_multi_main_container = {"display": "block"}
            k8_analysis_multi_empty_container = {"display": "none"}
            dropdown_container = {"display": "block"}

            year_over_year_grade = create_year_over_year_layout(school, year_over_year_k8_data, label, subcategory_radio)

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
                                                    html.Div("Add or Remove Schools: ", className="comparison-dropdown-label"),
                                                ],
                                                className="bare-container two columns"
                                            ),
                                            html.Div(
                                                [                                            
                                                    dcc.Dropdown(
                                                        id="multi-year-comparison-dropdown",
                                                        style={"fontSize": "1.1rem"},
                                                        multi = True,
                                                        clearable = False,
                                                        className="comparison-dropdown-control"
                                                    ),
                                                    html.Div(id="multi-year-input-warning"),
                                                ],
                                                className="bare-container eight columns"
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