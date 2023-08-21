######################################
# ICSB Dashboard - Academic Analysis #
######################################
# author:   jbetley
# version:  1.09
# date:     08/14/23
#
# TODO#1: Fix loading spinner issue - Loading spinner should trigger every time a new school is
# TODO: loaded, but not when the comparison dropdown is used.
# The Hacky fix right now has the Spinner loading the first 6 figs, so it looks like the
# whole page is loading on initial load, but doesn't reload the remainder of the figs
# when the comparison dropdown is triggered. Issues: Does not show loading spinner in
# bottom half of page when school dropdown is used. The loading spinner also stops
# spinning too early  as other parts of the page load first before they are pushed down by the layout.
# https://community.plotly.com/t/dcc-loading-only-on-first-load-of-dl-map-not-when-clicked-hover-on-feature-in-the-map/77587/3
# https://stackoverflow.com/questions/68116540/dcc-loading-on-first-load-only-python
# https://community.plotly.com/t/displaying-loading-screen-when-pages-container-is-loading/72109

# TODO#2: Add AHS/HS Data

import dash
from dash import ctx, dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd

# import local functions
from .load_data import ethnicity, subgroup, ethnicity, info_categories, get_k8_school_academic_data, get_school_index, \
    get_school_coordinates, get_comparable_schools, get_k8_corporation_academic_data
from .process_data import process_k8_academic_data, process_k8_corp_academic_data
from .calculations import find_nearest, calculate_proficiency, recalculate_total_proficiency, get_excluded_years
from .chart_helpers import no_data_fig_label, make_line_chart, make_bar_chart, make_group_bar_chart
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
    # HS and AHS should never generate a list of comparable schools.
    if (selected_school_type == "HS" or selected_school_type == "AHS"):
        return [],[],[]
    
    # Get School ID, School Name, Lat & Lon for all schools in the set for selected year
    schools_by_distance = get_school_coordinates(numeric_year)
    
    # Drop any school not testing at least 20 students. "SchoolTotal|ELATotalTested" is a proxy
    # for school size here (probably only impacts ~20 schools)
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

        # NOTE: This should never ever happen because we"ve already determined that the school exists in
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

        # if list is None or empty ([]), use the default options
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
    Output("fig14a", "children"),
    Output("fig14b", "children"),
    Output("fig14c", "children"),
    Output("fig14d", "children"),
    Output("fig-iread", "children"),
    Output("fig16c1", "children"),
    Output("fig16d1", "children"),
    Output("fig16c2", "children"),
    Output("fig16d2", "children"),
    Output("fig14g", "children"),
    Output("dropdown-container", "style"),
    Output("fig16a1", "children"),   
    Output("fig16a1-container", "style"),    
    Output("fig16b1", "children"),
    Output("fig16b1-container", "style"),
    Output("fig16a2", "children"),
    Output("fig16a2-container", "style"),
    Output("fig16b2", "children"),
    Output("fig16b2-container", "style"),
    Output("academic-analysis-main-container", "style"),
    Output("academic-analysis-empty-container", "style"),
    Output("academic-analysis-no-data", "children"),
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
    fig14a = []
    fig14b = []    
    fig14c = []
    fig14d = []
    fig_iread = []
    fig16c1 = []
    fig16d1 = []
    fig16c2 = []
    fig16d2 = []
    fig14g = []
        
    fig16a1 = []
    fig16a1_container = {"display": "none"}

    fig16b1 = []
    fig16b1_container = {"display": "none"}

    fig16a2 = []
    fig16a2_container = {"display": "none"}

    fig16b2 = []
    fig16b2_container = {"display": "none"}

    dropdown_container = {"display": "none"}
    academic_analysis_main_container = {"display": "none"}
    academic_analysis_empty_container = {"display": "block"}

    no_data_to_display = no_data_page("Academic Analysis")
    
    # Currently we only display data for Grades K-8. So nothing is displayed for
    # High Schools (HS) or Adult High Schools (AHS)
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

                # In addition, page is empty if the school is a K8/K12, and the df has data, but the tested_year
                # (YEARSchool) does not exist in the dataframe- this catches any year with no data (e.g., 2020) OR
                # if the tested header does exist, but all data in the column is NaN- this catches any year where
                # the school has no data or insufficient n-size ("***")

                raw_comparison_data['Test Year'] = pd.to_numeric(raw_comparison_data[tested_year], errors="coerce")

                if raw_comparison_data['Test Year'].isnull().all():
                    no_data_to_display = no_data_page("Academic Analysis","No Available Data with a sufficient n-size.")
                
                elif tested_year in raw_comparison_data.columns:

                    academic_analysis_main_container = {"display": "block"}            
                    academic_analysis_empty_container = {"display": "none"}

                    raw_comparison_data = raw_comparison_data.drop('Test Year', axis=1)

                    ## Year over Year figs
                    school_academic_data = raw_comparison_data[[col for col in raw_comparison_data.columns if "School" in col or "Category" in col]].copy()
                    school_academic_data.columns = school_academic_data.columns.str.replace(r"School$", "", regex=True)

                    display_academic_data = school_academic_data.set_index("Category").T.rename_axis("Year").rename_axis(None, axis=1).reset_index()

                    # add suffix to certain Categories
                    display_academic_data = display_academic_data.rename(columns={c: c + " Proficient %" for c in display_academic_data.columns if c not in ["Year", "School Name"]})

                    yearly_school_data = display_academic_data.copy()
                    yearly_school_data["School Name"] = school_name

                    # Chart 1: Year over Year ELA Proficiency by Grade (1.4.a)
                    fig14a_data = yearly_school_data.filter(regex = r"^Grade \d\|ELA|^School Name$|^Year$",axis=1)

                    # NOTE: make_line_chart() returns a list (plotly dash html layout), that either
                    # contains a chart (if data) or a no data fig
                    fig14a = make_line_chart(fig14a_data,"Year over Year ELA Proficiency by Grade")

                    # Chart 2: Year over Year Math Proficiency by Grade (1.4.b)
                    fig14b_data = yearly_school_data.filter(regex = r"^Grade \d\|Math|^School Name$|^Year$",axis=1)
                    fig14b = make_line_chart(fig14b_data,"Year over Year Math Proficiency by Grade")

                    # Charts 3 & 4: See below

                    # Chart 5: Year over Year ELA Proficiency by Ethnicity (1.6.c)
                    categories_16c1 = []
                    for e in ethnicity:
                        categories_16c1.append(e + "|" + "ELA Proficient %")

                    fig16c1_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16c1)) | (yearly_school_data.columns.isin(["School Name","Year"]))]
                    fig16c1_data = fig16c1_data.rename(columns = {"Native Hawaiian or Other Pacific Islander|ELA Proficient %": "Pacific Islander|ELA Proficient %"})
                    fig16c1 = make_line_chart(fig16c1_data,"Year over Year ELA Proficiency by Ethnicity")

                    # Chart 6: Year over Year Math Proficiency by Ethnicity (1.6.d)
                    categories_16d1 = []
                    for e in ethnicity:
                        categories_16d1.append(e + "|" + "Math Proficient %")

                    fig16d1_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16d1)) | (yearly_school_data.columns.isin(["School Name","Year"]))]
                    fig16d1_data = fig16d1_data.rename(columns = {"Native Hawaiian or Other Pacific Islander|Math Proficient %": "Pacific Islander|Math Proficient %"})
                    fig16d1 = make_line_chart(fig16d1_data,"Year over Year Math Proficiency by Ethnicity")

                    # Chart 7: Year over Year ELA Proficiency by Subgroup (1.6.c)
                    categories_16c2 = []
                    for s in subgroup:
                        categories_16c2.append(s + "|" + "ELA Proficient %")

                    fig16c2_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16c2)) | (yearly_school_data.columns.isin(["School Name","Year"]))]
                    fig16c2 = make_line_chart(fig16c2_data,"Year over Year ELA Proficiency by Subgroup")

                    # Chart 8: Year over Year Math Proficiency by Subgroup (1.6.d)
                    categories_16d2 = []
                    for s in subgroup:
                        categories_16d2.append(s + "|" + "Math Proficient %")

                    fig16d2_data = yearly_school_data.loc[:, (yearly_school_data.columns.isin(categories_16d2)) | (yearly_school_data.columns.isin(["School Name","Year"]))]
                    fig16d2 = make_line_chart(fig16d2_data,"Year over Year Math Proficiency by Subgroup")

                    # Chart 9 - IREAD Year over Year
                    category_iread = "IREAD Proficient %"

                    fig14g_data = yearly_school_data.loc[:, (yearly_school_data.columns == category_iread) | (yearly_school_data.columns.isin(["School Name","Year"]))]         
                    fig14g = make_line_chart(fig14g_data, category_iread)

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
        fig14a, fig14b, fig14c, fig14d, fig_iread, fig16c1, fig16d1, fig16c2, fig16d2, fig14g,
        dropdown_container, fig16a1, fig16a1_container, fig16b1, fig16b1_container, fig16a2,
        fig16a2_container, fig16b2, fig16b2_container, academic_analysis_main_container,
        academic_analysis_empty_container, no_data_to_display
    )

def layout():
    layout = html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(subnav_academic(),className="tabs"),
                                ],
                                className="bare_container_center twelve columns"
                            ),
                        ],
                        className="row"
                    ),
                    html.Div(
                        [
                            # NOTE: This is an awkward workaround. Want a loading spinner on load, but for it not
                            # to trigger when comparison dropdown callback is triggered (which would happen if
                            # Loading wraps the entire page). So we just wrap the first 6 figs, so loading shows
                            # on initial load, but not on comparison dropdown use.         
                            dcc.Loading(
                                id="loading",
                                type="circle",
                                fullscreen = True,
                                style={
                                    "position": "absolute",
                                    "align-self": "center",
                                    "background-color": "#F2F2F2",
                                },
                                children=[                         
                                    html.Div(
                                        [                                            
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Div(id="fig14a", children=[])
                                                        ],
                                                        className = "pretty_container six columns"
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(id="fig14b", children=[])
                                                        ],
                                                        className = "pretty_container six columns"
                                                    )
                                                ],
                                                className="bare_container twelve columns",
                                            ),
                                        ],
                                        className="row",
                                    ),                                            
                                    html.Div(
                                        [                                            
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Div(id="fig16c1", children=[])
                                                        ],
                                                        className = "pretty_container six columns"
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(id="fig16d1", children=[])
                                                        ],
                                                        className = "pretty_container six columns"
                                                    )
                                                ],
                                                className="bare_container twelve columns",
                                            ),
                                        ],
                                        className="row",
                                    ),                                              
                                    html.Div(
                                        [                                        
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Div(id="fig16c2", children=[])        
                                                        ],
                                                        className = "pretty_container six columns"
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Div(id="fig16d2", children=[])
                                                        ],
                                                        className = "pretty_container six columns"
                                                    )
                                                ],
                                                className="bare_container twelve columns",
                                            ),
                                        ],
                                        className="row",
                                    ),
                                        
                                ]
                            ),                
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(id="fig14g", children=[])
                                                ],
                                                className = "pretty_container six columns"
                                            ),
                                        ],
                                        className="bare_container twelve columns",
                                    )
                                ],
                                className="row",
                            ),
                            # Comparison Charts
                            html.Div(
                                [                                        
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.P("Add or Remove Schools: ", className="control_label"),
                                                    dcc.Dropdown(
                                                        id="comparison-dropdown",
                                                        style={"fontSize": "1em"},
                                                        multi = True,
                                                        clearable = False,
                                                        # className="multi_dropdown"
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
                        id = "academic-analysis-main-container",
                        style= {"display": "none"}, 
                    ),
                    html.Div(
                        [
                            html.Div(id="academic-analysis-no-data"),
                        ],
                        id = "academic-analysis-empty-container",
                    ),          
                ],
                id="mainContainer"
            )
    return layout