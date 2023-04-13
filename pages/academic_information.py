#########################################
# ICSB Dashboard - Academic Information #
#########################################
# author:   jbetley
# version:  1.01.040323

import dash
from dash import html, dcc, Input, Output, callback
from dash.exceptions import PreventUpdate
import numpy as np
import json
import pandas as pd
import re

# import local functions
from .table_helpers import no_data_page, no_data_table, create_academic_info_table
from .chart_helpers import loading_fig, no_data_fig_label, make_stacked_bar
from .calculations import round_percentages
from .subnav import subnav_academic

### Testing ###
pd.set_option("display.max_rows", 400)

dash.register_page(__name__, top_nav=True, path="/academic_information", order=4)

@callback(
    Output("k8-grade-table", "children"),
    Output("k8-grade-ela-fig", "children"),
    Output("k8-grade-math-fig", "children"),
    Output("k8-ethnicity-table", "children"),
    Output("k8-ethnicity-ela-fig", "children"),
    Output("k8-ethnicity-math-fig", "children"),
    Output("k8-subgroup-table", "children"),
    Output("k8-subgroup-ela-fig", "children"),
    Output("k8-subgroup-math-fig", "children"),
    Output("k8-other-table", "children"),
    Output("k8-not-calculated-table", "children"),
    Output("k8-table-container", "style"),
    Output("hs-grad-overview-table", "children"),
    Output("hs-grad-ethnicity-table", "children"),
    Output("hs-grad-subgroup-table", "children"),
    Output("sat-overview-table", "children"),
    Output("sat-ethnicity-table", "children"),
    Output("sat-subgroup-table", "children"),
    Output("hs-eca-table", "children"),
    Output("hs-not-calculated-table", "children"),
    Output("hs-table-container", "style"),
    Output('academic-information-main-container', 'style'),
    Output('academic-information-empty-container', 'style'),
    Output('academic-information-no-data', 'children'),  
    Input("dash-session", "data"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
)
def update_abcademic_information_page(data, school, year):
    if not data:
        raise PreventUpdate

    # NOTE: removed 'American Indian' because the category doesn't 
    # appear in all data sets
    # ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial',
    # 'Native Hawaiian or Other Pacific Islander','White']
    ethnicity = [
        "Asian",
        "Black",
        "Hispanic",
        "Multiracial",
        "Native Hawaiian or Other Pacific Islander",
        "White"
    ]
    subgroup = [
        "Special Education",
        "General Education",
        "Paid Meals",
        "Free/Reduced Price Meals",
        "English Language Learners",
        "Non-English Language Learners"
    ]
    grades = [
        "Grade 3",
        "Grade 4",
        "Grade 5",
        "Grade 6",
        "Grade 7",
        "Grade 8",
        "Total",
        "IREAD Pass %"
    ]

    grades_ordinal = [
        "3rd",
        "4th",
        "5th",
        "6th",
        "7th",
        "8th"
    ]
    subject = ["ELA", "Math"]

    # default styles
    main_container = {'display': 'block'}
    k8_table_container = {'display': 'block'}
    hs_table_container = {'display': 'block'}
    empty_container = {'display': 'none'}
    no_data_to_display = no_data_page('Academic Information')

    school_index = pd.DataFrame.from_dict(data["0"])

    if (
        school_index["School Type"].values[0] == "K8"
        or school_index["School Type"].values[0] == "K12"
    ):
        # load K8 academic_data
        if data["10"]:
            json_data = json.loads(data["10"])
            academic_data_k8 = pd.DataFrame.from_dict(json_data)
        else:
            academic_data_k8 = pd.DataFrame()

    # NOTE: There is a special exception here for Christel House
    # South - prior to 2021, CHS was a K12. From 2021 onwards,
    # CHS is a K8, with the high school moving to Christel House
    # Watanabe Manual HS
    if (
        school_index["School Type"].values[0] == "HS"
        or school_index["School Type"].values[0] == "AHS"
        or school_index["School Type"].values[0] == "K12"
        or (school_index["School ID"].values[0] == "5874" and int(year) < 2021)
    ):
        # load HS academic data
        if data["12"]:
            json_data = json.loads(data["12"])
            academic_data_hs = pd.DataFrame.from_dict(json_data)
        else:
            academic_data_hs = pd.DataFrame()

    if (
        school_index["School Type"].values[0] == "K8"
        and len(academic_data_k8.index) == 0
    ):
        hs_grad_overview_table = {}
        hs_grad_ethnicity_table = {}
        hs_grad_subgroup_table = {}
        sat_overview_table = {}
        sat_ethnicity_table = {}
        sat_subgroup_table = {}        
        hs_eca_table = {}
        hs_not_calculated_table = {}
        hs_table_container = {"display": "none"}

        k8_grade_table = {}
        k8_ethnicity_table = {}
        k8_subgroup_table = {}
        k8_other_table = {}
        k8_not_calculated_table = {}
        k8_table_container = {"display": "none"}

        k8_grade_ela_fig = {}
        k8_grade_math_fig = {}
        k8_ethnicity_ela_fig = {}
        k8_ethnicity_math_fig = {}
        k8_subgroup_ela_fig = {}
        k8_subgroup_math_fig = {}

        main_container = {'display': 'none'}
        empty_container = {'display': 'block'}

    else:

        ## K8 Academic Information
        if (
            school_index["School Type"].values[0] == "K8"
            or school_index["School Type"].values[0] == "K12"
        ):
            # if K8, hide HS table (except for CHS prior to 2021 when it
            # was a K12)
            if school_index["School Type"].values[0] == "K8" and not (
                school_index["School ID"].values[0] == "5874" and int(year) < 2021
            ):
                hs_grad_overview_table = {}
                hs_grad_ethnicity_table = {}
                hs_grad_subgroup_table = {}
                sat_overview_table = {}
                sat_ethnicity_table = {}
                sat_subgroup_table = {}                  
                hs_eca_table = {}
                hs_not_calculated_table = {}
                hs_table_container = {"display": "none"}

            # for academic information, strip out all comparative data and clean headers
            k8_academic_info = academic_data_k8[
                [
                    col
                    for col in academic_data_k8.columns
                    if "School" in col or "Category" in col
                ]
            ]
            k8_academic_info.columns = k8_academic_info.columns.str.replace(
                r"School$", "", regex=True
            )

            years_by_grade = k8_academic_info[
                k8_academic_info["Category"].str.contains("|".join(grades))
            ]
            if not years_by_grade.empty:
                k8_grade_table = create_academic_info_table(years_by_grade,'Proficiency by Grade')
            else:
                k8_grade_table = no_data_table('Proficiency by Grade')

            years_by_subgroup = k8_academic_info[
                k8_academic_info["Category"].str.contains("|".join(subgroup))
            ]
            if not years_by_subgroup.empty:            
                k8_subgroup_table = create_academic_info_table(years_by_subgroup,'Proficiency by Subgroup')
            else:
                k8_subgroup_table = no_data_table('Proficiency by Subgroup')

            years_by_ethnicity = k8_academic_info[
                k8_academic_info["Category"].str.contains("|".join(ethnicity))
            ]
            if not years_by_ethnicity.empty:            
                k8_ethnicity_table = create_academic_info_table(years_by_ethnicity,'Proficiency by Ethnicity')
            else:
                k8_ethnicity_table = no_data_table('Proficiency by Ethnicity')

            # attendance_rate_data_json
            if data["4"]:
                json_data = json.loads(data["4"])
                final_attendance_data = pd.DataFrame.from_dict(json_data)
                final_attendance_data = final_attendance_data[
                    [
                        col
                        for col in final_attendance_data.columns
                        if "School" in col or "Category" in col
                    ]
                ]
                final_attendance_data.columns = (
                    final_attendance_data.columns.str.replace(
                        r"School$", "", regex=True
                    )
                )

                # replace 'metric' title with more generic name
                final_attendance_data["Category"] = "Attendance Rate"
            else:
                final_attendance_data = pd.DataFrame()

            final_attendance_data = final_attendance_data.fillna("No Data")

            for col in final_attendance_data.columns:
                final_attendance_data[col] = pd.to_numeric(final_attendance_data[col], errors="coerce").fillna(final_attendance_data[col]).tolist()

            if not final_attendance_data.empty:
                k8_other_table = create_academic_info_table(final_attendance_data,'Attendance Data')
            else:
                k8_other_table = no_data_table('Attendance Data')

            k8_not_calculated = [
                {
                    "Category": "The school’s teacher retention rate."
                },
                {
                    "Category": "The school’s student re-enrollment rate."
                },
                {
                    "Category": "Proficiency in ELA and Math of students who have been enrolled in school for at least two (2) full years."
                },
                {
                    "Category": "Student growth on the state assessment in ELA and Math according to Indiana's Growth Model."
                },
            ]

            k8_not_calculated_data = pd.DataFrame(k8_not_calculated)
            k8_not_calculated_data = k8_not_calculated_data.reindex(
                columns=k8_academic_info.columns
            )
            k8_not_calculated_data = k8_not_calculated_data.fillna("N/A")

            # as this is generated by the script, it will always have data
            k8_not_calculated_table = create_academic_info_table(k8_not_calculated_data,'Not Currently Calculated')

            # Proficiency Breakdown stacked bar charts #
            
            # NOTE: The proficency data is annoyingly inconsistent. In some cases missing
            # data is blank, but in other cases, it is represented by a '0.'
            k8_all_data_all_years = pd.read_csv(r"data/ilearnAll.csv", dtype=str)
            
            # Get selected school data for all categories
            school_k8_all_data = k8_all_data_all_years.loc[k8_all_data_all_years["School ID"] == school]

            # Skip 2020 as there is no academic data
            year = '2019' if year == '2020' else year

            school_k8_proficiency_data = school_k8_all_data.loc[
            school_k8_all_data["Year"] == year
            ]

            # drop columns with no values and reset index
            school_k8_proficiency_data = school_k8_proficiency_data.dropna(axis=1)
            school_k8_proficiency_data = school_k8_proficiency_data.reset_index()

            # TODO: May need this if we want to differentiate those categories
            # NOTE: Leaving this line commented out means that pd.to_numeric
            # converts all '***' (e.g., where there were tested students, but
            # the proficiency value does not meet n-size requirements) values to NaN.
            # If we want to track those values, uncomment this line:
            # school_k8_proficiency_data =  school_k8_proficiency_data.replace({'***': float(-99)})

            for col in school_k8_proficiency_data.columns:
                school_k8_proficiency_data[col] = pd.to_numeric(
                    school_k8_proficiency_data[col], errors="coerce"
                )

            # Drop columns: 'Year','School ID', 'School Name', 'Corp ID','Corp Name'
            # which will automatically exclude these categories
            # Also drop 'ELA & Math' Category (not currently displayed on dashboard)
            school_k8_proficiency_data = school_k8_proficiency_data.drop(
                list(
                    school_k8_proficiency_data.filter(
                        regex="ELA & Math|Year|Corp ID|Corp Name|School ID|School Name"
                    )
                ),
                axis=1,
            )

            all_proficiency_data = school_k8_proficiency_data.copy()

            proficiency_rating = [
                "Below Proficiency",
                "Approaching Proficiency",
                "At Proficiency",
                "Above Proficiency"
            ]

            # for each category, create a list of columns using the strings in
            #  'proficiency_rating' and then divide each column by 'Total Tested'
            categories = grades + ethnicity + subgroup

            annotations = pd.DataFrame(columns= ['Category','Total Tested','Status'])

            for c in categories:
                for s in subject:
                    category_subject = c + "|" + s
                    colz = [category_subject + " " + x for x in proficiency_rating]
                    total_tested = category_subject + " " + "Total Tested"

                    # We do not want categories that do not appear in the dataframe
                    # NOTE: at this point in the code there are three possible data 
                    # configurations for each column:
                    # 1) Total Tested > 0 and all proficiency_rating(s) are > 0
                    #   (School has tested category and there is publicly available data)
                    # 2) Total Tested > 0 and all proficiency_rating(s) are == 'NaN'
                    #   (School has tested category but there is no publicly available
                    #   data (insufficient N-size))) [do not display]
                    # 3) Total Tested AND all proficiency_rating == 0 (School does
                    #   not have tested category) [do not display]

                    # Neither (2) nor (3) should be displayed. However, we do want to
                    # track which Category/Subject combinations meet either condition
                    # (for figure annotation purposes). So we use a little trick. The
                    # sum of a series of '0' values is 0 (a numpy.int64). The sum of a
                    # series of 'NaN' values is also 0.0 (but the value is a float because
                    # numpy treats NaN as a numpy.float64). While either value returns True
                    # when tested if it == 0, we can test the 'type' of the result (using
                    # np.integer and np.floating) to distinuish between them.

                    if total_tested in all_proficiency_data.columns:

                        if all_proficiency_data[colz].iloc[0].sum() == 0:

                            # if the value is a float, the measured values were NaN, which
                            # means they were converted '***', and thus insufficient data
                            if isinstance(all_proficiency_data[colz].iloc[0].sum(), np.floating):
                                annotations.loc[len(annotations.index)] = [colz[0],all_proficiency_data[total_tested].values[0],'Insufficient']

                            # if the value is an integer, the measured values were '0'. which
                            # means missing data
                            elif isinstance(all_proficiency_data[colz].iloc[0].sum(), np.integer):
                                # Only add to annotations if it is a non 'Grade' category.
                                # this is to account for IDOE's shitty data practices- sometimes
                                # they treat missing grades, e.g., a school does not offer that
                                # grade level, as blank (the correct way) and sometimes with '0's
                                # (the dumbass way). So if everything is 0 AND it is a Grade
                                # category, we assume it is just IDOE's fucked up data entry
                                if ~all_proficiency_data[colz].columns.str.contains('Grade').any():
                                    annotations.loc[len(annotations.index)] = [colz[0],all_proficiency_data[total_tested].values[0],'Missing']

                            # either way, drop the entire category from the chart data
                            all_colz = colz + [total_tested]

                            all_proficiency_data = all_proficiency_data.drop(all_colz, axis=1)

                        else:
                            # calculate percentage
                            all_proficiency_data[colz] = all_proficiency_data[colz].divide(
                                all_proficiency_data[total_tested], axis="index"
                            )

                            # get a list of all values
                            row_list = all_proficiency_data[colz].values.tolist()

                            # round percentages using Largest Remainder Method
                            rounded = round_percentages(row_list[0])

                            # add back to dataframe
                            tmp_df = pd.DataFrame([rounded])
                            cols = list(tmp_df.columns)
                            all_proficiency_data[colz] = tmp_df[cols]

                        # each existing category has a calculated proficiency column
                        # named 'grade_subject'. Since we arent using it, we need to
                        # drop it from each category
                        all_proficiency_data.drop(category_subject, axis=1, inplace=True)

            # drop all remaining columns used for calculation that we
            # dont want to chart
            all_proficiency_data.drop(
                list(
                    all_proficiency_data.filter(
                        regex="School Total|Total Proficient"
                    )
                ),
                axis=1,
                inplace=True,
            )

            # Replace Grade X with ordinal number (e.g., Grade 3 = 3rd)
            all_proficiency_data = all_proficiency_data.rename(
                columns=lambda x: re.sub("(Grade )(\d)", "\\2th", x)
            )
            # all use 'th' suffix except for 3rd - so we need to specially treat '3''
            all_proficiency_data.columns = [
                x.replace("3th", "3rd") for x in all_proficiency_data.columns.to_list()
            ]

            # transpose df
            all_proficiency_data = (
                all_proficiency_data.T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )

            # split Grade column into two columns and rename what used to be the index
            all_proficiency_data[["Category", "Proficiency"]] = all_proficiency_data[
                "Category"
            ].str.split("|", expand=True)

            all_proficiency_data.rename(columns={0: "Percentage"}, inplace=True)

            # Drop 'index' row (created during transpose)
            all_proficiency_data = all_proficiency_data[
                all_proficiency_data["Category"] != "index"
            ]

            # NOTE: Currently, annotations are collected but not used
            ela_title = year + ' ELA Proficiency Breakdown'
            math_title = year + ' Math Proficiency Breakdown'
            
            # ELA by Grade
            grade_annotations = annotations.loc[annotations['Category'].str.contains("Grade")]
            grade_ela_fig_data = all_proficiency_data[
                all_proficiency_data["Category"].isin(grades_ordinal)
                & all_proficiency_data["Proficiency"].str.contains("ELA")
            ]

            if not grade_ela_fig_data.empty:
                k8_grade_ela_fig = make_stacked_bar(grade_ela_fig_data,ela_title)
            else:
                k8_grade_ela_fig = no_data_fig_label(ela_title, 100)

            # Math by Grade
            grade_math_fig_data = all_proficiency_data[
                all_proficiency_data["Category"].isin(grades_ordinal)
                & all_proficiency_data["Proficiency"].str.contains("Math")
            ]

            if not grade_math_fig_data.empty:
                k8_grade_math_fig = make_stacked_bar(grade_math_fig_data,math_title)
            else:
                k8_grade_math_fig = no_data_fig_label(math_title, 100)

            # ELA by Ethnicity
            ethnicity_annotations = annotations.loc[annotations['Category'].str.contains("Ethnicity")]
            ethnicity_ela_fig_data = all_proficiency_data[
                all_proficiency_data["Category"].isin(ethnicity)
                & all_proficiency_data["Proficiency"].str.contains("ELA")
            ]

            if not ethnicity_ela_fig_data.empty:
                k8_ethnicity_ela_fig = make_stacked_bar(ethnicity_ela_fig_data,ela_title)
            else:
                k8_ethnicity_ela_fig = no_data_fig_label(ela_title, 100)

            # Math by Ethnicity
            ethnicity_math_fig_data = all_proficiency_data[
                all_proficiency_data["Category"].isin(ethnicity)
                & all_proficiency_data["Proficiency"].str.contains("Math")
            ]

            if not ethnicity_math_fig_data.empty:
                k8_ethnicity_math_fig = make_stacked_bar(ethnicity_math_fig_data,math_title)
            else:
                k8_ethnicity_math_fig = no_data_fig_label(math_title, 100)

            # ELA by Subgroup
            subgroup_annotations = annotations.loc[annotations['Category'].str.contains("Subgroup")]
            subgroup_ela_fig_data = all_proficiency_data[
                all_proficiency_data["Category"].isin(subgroup)
                & all_proficiency_data["Proficiency"].str.contains("ELA")
            ]

            if not subgroup_ela_fig_data.empty:
                k8_subgroup_ela_fig = make_stacked_bar(subgroup_ela_fig_data,ela_title)
            else:
                k8_subgroup_ela_fig = no_data_fig_label(ela_title, 100)

            # Math by Subgroup
            subgroup_math_fig_data = all_proficiency_data[
                all_proficiency_data["Category"].isin(subgroup)
                & all_proficiency_data["Proficiency"].str.contains("Math")
            ]

            if not subgroup_math_fig_data.empty:
                k8_subgroup_math_fig = make_stacked_bar(subgroup_math_fig_data,math_title)
            else:

                k8_subgroup_math_fig = no_data_fig_label(math_title, 100)

    ## HS academic information
    if (
        school_index["School Type"].values[0] == "HS"
        or school_index["School Type"].values[0] == "AHS"
        or school_index["School Type"].values[0] == "K12"
        or (school_index["School ID"].values[0] == "5874" and int(year) < 2021)
    ):
        # if HS or AHS, hide K8 table
        if (
            school_index["School Type"].values[0] == "HS"
            or school_index["School Type"].values[0] == "AHS"
        ):
            k8_grade_table = {}
            k8_ethnicity_table = {}
            k8_subgroup_table = {}
            k8_other_table = {}
            k8_not_calculated_table = {}

            k8_grade_ela_fig = {}
            k8_grade_math_fig = {}
            k8_ethnicity_ela_fig = {}
            k8_ethnicity_math_fig = {}
            k8_subgroup_ela_fig = {}
            k8_subgroup_math_fig = {}
            k8_table_container = {"display": "none"}

        if len(academic_data_hs.index) == 0:
            hs_grad_overview_table = {}
            hs_grad_ethnicity_table = {}
            hs_grad_subgroup_table = {}
            sat_overview_table = {}
            sat_ethnicity_table = {}
            sat_subgroup_table = {}              
            hs_eca_table = {}
            hs_not_calculated_table = {}
            hs_table_container = {"display": "none"}

            main_container = {'display': 'none'}
            empty_container = {'display': 'block'}

        else:

            # NOTE: Strength of Diploma not displayed

            # Gradution Rate
            grad_overview_categories = [
                "Total",
                "Non-Waiver",
                "State Average"
                # "Strength of Diploma",
            ]

            if school_index["School Type"].values[0] == "AHS":
                grad_overview_categories.append("CCR Percentage")

            # strip out all comparative data and clean headers
            hs_academic_info = academic_data_hs[
                [
                    col
                    for col in academic_data_hs.columns
                    if "School" in col or "Category" in col
                ]
            ]

            hs_academic_info.columns = hs_academic_info.columns.str.replace(
                r"School$", "", regex=True
            )

            eca_data = hs_academic_info[
                hs_academic_info["Category"].str.contains('Grade 10')
            ].copy()
            if not eca_data.empty:            
                hs_eca_table = create_academic_info_table(eca_data,'End of Course Assessments')            
            else:
                hs_eca_table = no_data_table('End of Course Assessments')

            # Graduation Rate Tables
            graduation_data = hs_academic_info[
                hs_academic_info["Category"].str.contains('Graduation')
            ].copy()

            # drop 'Graduation Rate' from all 'Category' rows and remove whitespace
            graduation_data["Category"] = (
                graduation_data["Category"]
                .str.replace("Graduation Rate", "")
                .str.strip()
            )

            grad_overview = graduation_data[
                graduation_data["Category"].str.contains("|".join(grad_overview_categories))
            ]
            if not grad_overview.empty:
                hs_grad_overview_table = create_academic_info_table(grad_overview,'Graduation Rate Overview')
            else:
                hs_grad_overview_table = no_data_table('Graduation Rate Overview')

            grad_ethnicity = graduation_data[
                graduation_data["Category"].str.contains("|".join(ethnicity))
            ]
            if not grad_ethnicity.empty:                 
                hs_grad_ethnicity_table = create_academic_info_table(grad_ethnicity,'Graduation Rate by Ethnicity')
            else:
                hs_grad_ethnicity_table = no_data_table('Graduation Rate by Ethnicity')

            grad_subgroup = graduation_data[
                graduation_data["Category"].str.contains("|".join(subgroup))
            ]
            if not grad_subgroup.empty:                
                hs_grad_subgroup_table = create_academic_info_table(grad_subgroup,'Graduation Rate by Subgroup')
            else:
                hs_grad_subgroup_table = no_data_table('Graduation Rate by Subgroup')

            # SAT Benchmark Tables
            sat_table_data = hs_academic_info[
                hs_academic_info["Category"].str.contains('Benchmark %')
            ].copy()

            # drop 'Graduation Rate' from all 'Category' rows and remove whitespace
            sat_table_data["Category"] = (
                sat_table_data["Category"]
                .str.replace("Benchmark %", "")
                .str.strip()
            )

            sat_overview = sat_table_data[
                sat_table_data["Category"].str.contains('School Total')
            ]
            if not sat_overview.empty:          
                sat_overview_table = create_academic_info_table(sat_overview,'SAT Overview')
            else:
                sat_overview_table = no_data_table('SAT Overview')

            sat_ethnicity = sat_table_data[
                sat_table_data["Category"].str.contains("|".join(ethnicity))
            ]
            if not sat_ethnicity.empty:                 
                sat_ethnicity_table = create_academic_info_table(sat_ethnicity,'SAT Benchmarks by Ethnicity')
            else:
                sat_ethnicity_table = no_data_table('SAT Benchmarks by Ethnicity')

            sat_subgroup = sat_table_data[
                sat_table_data["Category"].str.contains("|".join(subgroup))
            ]
            if not sat_subgroup.empty:                
                sat_subgroup_table = create_academic_info_table(sat_subgroup,'SAT Benchmarks by Subgroup')
            else:
                sat_subgroup_table = no_data_table('SAT Benchmarks by Subgroup')

            hs_not_calculated = [
                {
                    "Category": "The percentage of students entering grade 12 at the beginning of the school year who graduated from high school"
                },
                {
                    "Category": "The percentage of graduating students planning to pursue college or career (as defined by IDOE)."
                },
            ]

            hs_not_calculated_data = pd.DataFrame(hs_not_calculated)
            hs_not_calculated_data = hs_not_calculated_data.reindex(
                columns=hs_academic_info.columns
            )
            hs_not_calculated_data = hs_not_calculated_data.fillna("NA")

            hs_not_calculated_table = create_academic_info_table(hs_not_calculated_data,'Not Currently Calculated')

    return (
        k8_grade_table,
        k8_grade_ela_fig,
        k8_grade_math_fig,
        k8_ethnicity_table,
        k8_ethnicity_ela_fig,
        k8_ethnicity_math_fig,
        k8_subgroup_table,
        k8_subgroup_ela_fig,
        k8_subgroup_math_fig,
        k8_other_table,
        k8_not_calculated_table,
        k8_table_container,
        hs_grad_overview_table,
        hs_grad_ethnicity_table,
        hs_grad_subgroup_table,
        sat_overview_table,
        sat_ethnicity_table,
        sat_subgroup_table,
        hs_eca_table,
        hs_not_calculated_table,
        hs_table_container,
        main_container,
        empty_container,
        no_data_to_display
    )

def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(subnav_academic(), className="tabs"),
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
                                    html.Label('Notes:',
                                        style = {
                                            'height': 'auto',
                                            'lineHeight': '1.5em',
                                            'backgroundColor': '#6783a9',
                                            'fontSize': '12px',
                                            'fontFamily': 'Roboto, sans-serif',
                                            'color': '#ffffff',
                                            'textAlign': 'center',
                                            'fontWeight': 'bold',
                                            'paddingBottom': '5px',
                                            'paddingTop': '5px'
                                        }
                                    ),
                                    html.P(""),
                                        html.P("There are a number of factors that make it difficult to make valid and reliable comparisons between \
                                               test scores from 2019 to 2022. For example, ILEARN was administered for the first \
                                               time during the 2018-19 SY and represented an entirely new type and mode of assessment (adaptive \
                                               and online-only). No State assessment was administered in 2020 because of the Covid-19 pandemic. Finally, \
                                               the 2019 data set includes only students who attended the testing school for 162 days, while \
                                               the 2021 and 2022 data sets included all tested students.",
                                            style={
                                                    'textAlign': 'Left',
                                                    'color': '#6783a9',
                                                    'fontSize': 12,
                                                    'marginLeft': '10px',
                                                    'marginRight': '10px',
                                                    'marginTop': '10px',
                                                }
                                            ),
                                            html.P("Data Source: Indiana Department of Education Data Center & Reports (https://www.in.gov/doe/it/data-center-and-reports/)",
                                            style={
                                                'color': '#6783a9',
                                                'fontSize': 10,
                                                'marginLeft': '10px',
                                                'marginRight': '10px',
                                                'marginTop': '10px',
                                            }),
                                ],
                                className = "pretty_container seven columns"
                            ),
                        ],
                        className = "bare_container twelve columns"
                    ),        
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-grade-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-grade-ela-fig"),
                                            # dcc.Graph(id="k8-grade-ela-fig",
                                            #     figure=loading_fig(),
                                            #     config={
                                            #         'displayModeBar': False,
                                            #         'showAxisDragHandles': False,
                                            #         'showAxisRangeEntryBoxes': False,
                                            #         'scrollZoom': False
                                            #     }
                                            # ),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="k8-grade-math-fig"),        
                                            # dcc.Graph(id="k8-grade-math-fig",
                                            #     figure=loading_fig(),
                                            #     config={
                                            #         'displayModeBar': False,
                                            #         'showAxisDragHandles': False,
                                            #         'showAxisRangeEntryBoxes': False,
                                            #         'scrollZoom': False
                                            #     }
                                            # ),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-ethnicity-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-ethnicity-ela-fig"),        
                                            # dcc.Graph(id="k8-ethnicity-ela-fig",
                                            #     figure=loading_fig(),
                                            #     config={
                                            #         'displayModeBar': False,
                                            #         'showAxisDragHandles': False,
                                            #         'showAxisRangeEntryBoxes': False,
                                            #         'scrollZoom': False
                                            #     }
                                            # ),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="k8-ethnicity-math-fig"),          
                                            # dcc.Graph(id="k8-ethnicity-math-fig",
                                            #     figure=loading_fig(),
                                            #     config={
                                            #         'displayModeBar': False,
                                            #         'showAxisDragHandles': False,
                                            #         'showAxisRangeEntryBoxes': False,
                                            #         'scrollZoom': False
                                            #     }
                                            # ),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-subgroup-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-subgroup-ela-fig"),          
                                            # dcc.Graph(id="k8-subgroup-ela-fig",
                                            #     figure=loading_fig(),
                                            #     config={
                                            #         'displayModeBar': False,
                                            #         'showAxisDragHandles': False,
                                            #         'showAxisRangeEntryBoxes': False,
                                            #         'scrollZoom': False
                                            #     }
                                            # ),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(id="k8-subgroup-math-fig"),        
                                            # dcc.Graph(id="k8-subgroup-math-fig",
                                            #     figure=loading_fig(),
                                            #     config={
                                            #         'displayModeBar': False,
                                            #         'showAxisDragHandles': False,
                                            #         'showAxisRangeEntryBoxes': False,
                                            #         'scrollZoom': False
                                            #     }
                                            # ),
                                        ],
                                        className="pretty_container four columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-other-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="k8-not-calculated-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                        ],
                        id="k8-table-container",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-grad-overview-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-grad-ethnicity-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-grad-subgroup-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="sat-overview-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="sat-ethnicity-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="sat-subgroup-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),                            
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-eca-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(id="hs-not-calculated-table"),
                                        ],
                                        className="pretty_container six columns",
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),
                        ],
                        id="hs-table-container",
                    ),
                ],
                id = 'academic-information-main-container',
            ),
            html.Div(
                [
                    html.Div(id='academic-information-no-data'),
                ],
                id = 'academic-information-empty-container',
            ),
        ],
        id="mainContainer",
    )