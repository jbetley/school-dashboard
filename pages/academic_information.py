#########################################
# ICSB Dashboard - Academic Information #
#########################################
# author:   jbetley
# version:  .99.021323

import dash
import plotly.colors
import plotly.express as px
from dash import html, dash_table, Input, Output, callback
from dash.exceptions import PreventUpdate
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign
import json
import pandas as pd

# import subnav function
from .subnav import subnav_academic

dash.register_page(__name__, top_nav=True, path="/academic_information", order=4)

# default table styles
table_style = {"fontSize": "11px", "fontFamily": "Roboto, sans-serif", "border": "none"}

table_header = {
    "height": "20px",
    "backgroundColor": "#ffffff",
    "border": "none",
    "borderBottom": ".5px solid #6783a9",
    "fontSize": "12px",
    "fontFamily": "Roboto, sans-serif",
    "color": "#6783a9",
    "textAlign": "center",
    "fontWeight": "bold",
}

table_header_conditional = [
    {
        "if": {"column_id": "Category"},
        "textAlign": "left",
        "paddingLeft": "10px",
        "width": "35%",
        "fontSize": "11px",
        "fontFamily": "Roboto, sans-serif",
        "color": "#6783a9",
        "fontWeight": "bold",
    }
]

table_cell = {
    "whiteSpace": "normal",
    "height": "auto",
    "textAlign": "center",
    "color": "#6783a9",
    "minWidth": "25px",
    "width": "25px",
    "maxWidth": "25px",
}

table_cell_conditional = [
    {
        "if": {"column_id": "Category"},
        "textAlign": "left",
        "fontWeight": "500",
        "paddingLeft": "10px",
        "width": "35%",
    }
]

empty_table = [
    dash_table.DataTable(
        columns=[
            {"id": "emptytable", "name": "No Data to Display"},
        ],
        style_header={
            "fontSize": "16px",
            "border": "none",
            "backgroundColor": "#ffffff",
            "paddingTop": "15px",
            "verticalAlign": "center",
            "textAlign": "center",
            "color": "#6783a9",
            "fontFamily": "Roboto, sans-serif",
        },
    )
]

test_data = pd.read_csv(r"data/test2022-all.csv", dtype=str)


@callback(
    Output("k8-grade-table", "children"),
    Output("k8-ethnicity-table", "children"),
    Output("k8-status-table", "children"),
    Output("k8-other-table", "children"),
    Output("k8-not-calculated-table", "children"),
    Output("k8-table-container", "style"),
    Output("hs-grad-overview-table", "children"),
    Output("hs-grad-ethnicity-table", "children"),
    Output("hs-grad-status-table", "children"),
    Output("hs-eca-table", "children"),
    Output("hs-not-calculated-table", "children"),
    Output("hs-table-container", "style"),
    Input("dash-session", "data"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
)
def update_about_page(data, school, year):
    if not data:
        raise PreventUpdate

    # NOTE: removed 'American Indian' because the category doesn't appear in all data sets
    # ethnicity = ['American Indian','Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
    ethnicity = [
        "Asian",
        "Black",
        "Hispanic",
        "Multiracial",
        "Native Hawaiian or Other Pacific Islander",
        "White",
    ]
    status = [
        "Special Education",
        "General Education",
        "Paid Meals",
        "Free/Reduced Price Meals",
        "English Language Learners",
        "Non-English Language Learners",
    ]
    grades = [
        "Grade 3",
        "Grade 4",
        "Grade 5",
        "Grade 6",
        "Grade 7",
        "Grade 8",
        "Total",
        "IREAD Pass %",
    ]
    subject = ["ELA", "Math"]

    school_index = pd.DataFrame.from_dict(data["0"])

    if (
        school_index["School Type"].values[0] == "K8"
        or school_index["School Type"].values[0] == "K12"
    ):
        # k8_academic_data_json
        if data["10"]:
            json_data = json.loads(data["10"])
            academic_data_k8 = pd.DataFrame.from_dict(json_data)

        else:
            academic_data_k8 = pd.DataFrame()

    # NOTE: Need a special exception to display HS data for
    # Christel House South prior to 2021 (when it split into
    # CHS and CHWM HS)
    if (
        school_index["School Type"].values[0] == "HS"
        or school_index["School Type"].values[0] == "AHS"
        or school_index["School Type"].values[0] == "K12"
        or (school_index["School ID"].values[0] == "5874" and int(year) < 2021)
    ):
        # hs_academic_data_json
        if data["12"]:
            json_data = json.loads(data["12"])
            academic_data_hs = pd.DataFrame.from_dict(json_data)

        else:
            academic_data_hs = pd.DataFrame()

    # School_type determines which tables to display - default is display both
    k8_table_container = {}
    hs_table_container = {}

    # if school type is K8 and there is no data in dataframe, hide
    # all tables and return a single table with 'No Data' message
    if (
        school_index["School Type"].values[0] == "K8"
        and len(academic_data_k8.index) == 0
    ):
        hs_grad_overview_table = []
        hs_grad_ethnicity_table = []
        hs_grad_status_table = []
        hs_eca_table = []
        hs_not_calculated_table = []
        hs_table_container = {"display": "none"}

        k8_grade_table = empty_table
        k8_ethnicity_table = empty_table
        k8_status_table = empty_table
        k8_other_table = empty_table
        k8_not_calculated_table = empty_table

    else:
        ## TESTING 100% Stackd Bar Chart ##
        pd.set_option("display.max_rows", 200)
        # Clean up dataframe (none of these work)
        # test_data.columns = test_data.columns.str.replace(r'\s+', '', regex=True)
        # newlines = {"\nProficient \n%":"", "\n":" ","\n":" "}
        # test_data.columns = [x.replace(newlines) for x in test_data.columns.to_list()]
        # test_data.columns = [x.replace({"\nProficient \n%":"", "\n":" ","\n":" "}) for x in test_data.columns.to_list()]

        # Clean up dataframe
        test_data.columns = [
            x.replace("\nProficient \n%", "") for x in test_data.columns.to_list()
        ]
        test_data.columns = [x.replace(" \n", " ") for x in test_data.columns.to_list()]
        test_data.columns = [x.replace("\n", " ") for x in test_data.columns.to_list()]

        # Get selected school data for all categories
        school_test_data = test_data.loc[test_data["School ID"] == school]

        # drop columns with no values and reset index
        school_test_data = school_test_data.dropna(axis=1)
        school_test_data = school_test_data.reset_index()

        # convert to numeric
        for col in school_test_data.columns:
            school_test_data[col] = pd.to_numeric(
                school_test_data[col], errors="coerce"
            )
        # Drop columns: 'Year','School ID', 'School Name', 'Corp ID','Corp Name'
        # TODO: May not need to do the above as we are filtering data for each chart
        # which will automatically exclude these categories
        # Also drop 'ELA & Math' Category (not currently displayed on dashboard)
        school_test_data = school_test_data.drop(
            list(
                school_test_data.filter(
                    regex="ELA & Math|Year|Corp ID|Corp Name|School ID|School Name"
                )
            ),
            axis=1,
        )

        all_proficiency_data = school_test_data.copy()
        proficiency_rating = [
            "Below Proficiency",
            "Approaching Proficiency",
            "At Proficiency",
            "Above Proficiency",
        ]

        def round_percentages(percentages):
            """
            https://github.com/simondo92/round-percentages
            Given an iterable of percentages that add up to 100, round them to the nearest integer such
            that the rounded percentages also add up to 100. Uses the largest remainder method.
            E.g.
            round_percentages([13.626332, 47.989636, 9.596008, 28.788024]) -> [14, 48, 9, 29]

            Update: Added code to turn decimal percentages into ints
            """

            # if numbers are in decimal format (e.g. .57, .90) then the sum of the numbers should
            # bet at or near (1). To be safe we test to see if sum is less than 2. If it is, we
            # multiple all of the numbers in the list by 100 (e.g., 57, 90)
            if sum(percentages) < 2:
                percentages = [x * 100 for x in percentages]

            result = []
            sum_of_integer_parts = 0

            for index, percentage in enumerate(percentages):
                integer, decimal = str(float(percentage)).split(".")
                integer = int(integer)
                decimal = int(decimal)

                result.append([integer, decimal, index])
                sum_of_integer_parts += integer

            result.sort(key=lambda x: x[1], reverse=True)
            difference = 100 - sum_of_integer_parts

            for percentage in result:
                if difference == 0:
                    break
                percentage[0] += 1
                difference -= 1

            # order by the original order
            result.sort(key=lambda x: x[2])

            # return just the percentage
            return [percentage[0] for percentage in result]

        # for each category, create a list of columns using the strings in
        #  'proficiency_rating' and then divide each column by 'Total Tested'
        categories = grades + ethnicity + status

        for c in categories:
            for s in subject:
                grade_subject = c + "|" + s
                colz = [grade_subject + " " + x for x in proficiency_rating]
                total_tested = grade_subject + " " + "Total Tested"

                if total_tested in all_proficiency_data.columns:
                    # For some reason, dataset uses zero instead of blank for some
                    # categories. So we only calculate percentage for those categories
                    # where the number of tested students is > 0
                    if all_proficiency_data[total_tested].values[0] > 0:
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
                    else:
                        # if total tested is zero, drop all of the columns in the category
                        all_proficiency_data.drop(colz, axis=1, inplace=True)

                    # each category has a calculated proficiency column named
                    # 'grade_subject'. Since we arent using it, we need to
                    # drop it from each category

                    all_proficiency_data.drop(grade_subject, axis=1, inplace=True)

        # drop columns used for calculation that aren't in final chart
        all_proficiency_data.drop(
            list(
                all_proficiency_data.filter(
                    regex="School Total|Total Tested|Total Proficient"
                )
            ),
            axis=1,
            inplace=True,
        )

        # transpose df
        all_proficiency_data = (
            all_proficiency_data.T.rename_axis("Category")
            .rename_axis(None, axis=1)
            .reset_index()
        )

        # TODO: CHANGE THESE HEADERS - Category,
        # split Grade column into two columns and rename what used to be the index
        all_proficiency_data[["Category", "Proficiency"]] = all_proficiency_data[
            "Category"
        ].str.split("|", expand=True)
        all_proficiency_data.rename(columns={0: "Percentage"}, inplace=True)

        # Drop 'index' row (created during transpose)
        all_proficiency_data = all_proficiency_data[
            all_proficiency_data["Category"] != "index"
        ]
        # TEST
        def make_stacked_bar(data):
            colors = plotly.colors.qualitative.Prism

            fig = px.bar(
                data,
                x="Percentage",
                y="Category",
                color=data["Proficiency"],
                barmode="stack",
                text=[f"{i}%" for i in data["Percentage"]],
                orientation="h",
                color_discrete_sequence=colors,
            )

            # Don't forget to remove from update_traces
            fig.update_traces(textfont_size=12)

            return fig

        # ELA by Grade
        fig1_data = all_proficiency_data[
            all_proficiency_data["Category"].str.contains("Grade")
            & all_proficiency_data["Proficiency"].str.contains("ELA")
        ]
        fig1 = make_stacked_bar(fig1_data)
        fig1.show()

        # Math by Grade
        fig2_data = all_proficiency_data[
            all_proficiency_data["Category"].str.contains("Grade")
            & all_proficiency_data["Proficiency"].str.contains("Math")
        ]
        fig2 = make_stacked_bar(fig2_data)
        fig2.show()

        # # ELA by Subgroup [TEST]
        fig2_data = all_proficiency_data[
            all_proficiency_data["Category"].str.contains(status)
            & all_proficiency_data["Proficiency"].str.contains("ELA")
        ]
        # fig1 = make_stacked_bar(fig1_data)
        # fig1.show()

        # # Math by Subgroup
        # fig2_data = all_proficiency_data[
        #     all_proficiency_data["Category"].str.contains("Math")
        # ]
        # fig2 = make_stacked_bar(fig2_data)
        # fig2.show()

        # # ELA by Ethnicity
        # fig1_data = all_proficiency_data[
        #     all_proficiency_data["Category"].str.contains("ELA")
        # ]
        # fig1 = make_stacked_bar(fig1_data)
        # fig1.show()

        # # Math by Ethnicity
        # fig2_data = all_proficiency_data[
        #     all_proficiency_data["Category"].str.contains("Math")
        # ]
        # fig2 = make_stacked_bar(fig2_data)
        # fig2.show()

        ## K8 Academic Information
        if (
            school_index["School Type"].values[0] == "K8"
            or school_index["School Type"].values[0] == "K12"
        ):
            # if K8, hide HS table (except for CHS prior to 2021)
            if school_index["School Type"].values[0] == "K8" and not (
                school_index["School ID"].values[0] == "5874" and int(year) < 2021
            ):
                hs_grad_overview_table = []
                hs_grad_ethnicity_table = []
                hs_grad_status_table = []
                hs_eca_table = []
                hs_not_calculated_table = []
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
            years_by_status = k8_academic_info[
                k8_academic_info["Category"].str.contains("|".join(status))
            ]
            years_by_ethnicity = k8_academic_info[
                k8_academic_info["Category"].str.contains("|".join(ethnicity))
            ]

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

            k8_not_calculated = [
                {"Category": "The school’s teacher retention rate."},
                {"Category": "The school’s student re-enrollment rate."},
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

            k8_table_columns = [
                {
                    "name": col,
                    "id": col,
                    "type": "numeric",
                    "format": Format(
                        scheme=Scheme.percentage, precision=2, sign=Sign.parantheses
                    ),
                }
                for (col) in k8_academic_info.columns
            ]

            k8_table_data_conditional = [
                {"if": {"row_index": "odd"}, "backgroundColor": "#eeeeee"},
                {  # Kludge to ensure first col header has border
                    "if": {"row_index": 0, "column_id": "Category"},
                    "borderTop": ".5px solid #6783a9",
                },
            ]

            k8_grade_table = [
                dash_table.DataTable(
                    years_by_grade.to_dict("records"),
                    columns=k8_table_columns,
                    style_data=table_style,
                    style_data_conditional=k8_table_data_conditional,
                    style_header=table_header,
                    style_cell=table_cell,
                    style_header_conditional=table_header_conditional,
                    style_cell_conditional=table_cell_conditional,
                    merge_duplicate_headers=True,
                    style_as_list_view=True,
                    # add this to each table if we want to be able to export
                    # export_format='xlsx',
                    # export_headers='display'
                )
            ]

            k8_ethnicity_table = [
                dash_table.DataTable(
                    years_by_ethnicity.to_dict("records"),
                    columns=k8_table_columns,
                    style_data=table_style,
                    style_data_conditional=k8_table_data_conditional,
                    style_header=table_header,
                    style_header_conditional=table_header_conditional,
                    style_cell=table_cell,
                    style_cell_conditional=table_cell_conditional,
                    merge_duplicate_headers=True,
                    style_as_list_view=True,
                )
            ]

            k8_status_table = [
                dash_table.DataTable(
                    years_by_status.to_dict("records"),
                    columns=k8_table_columns,
                    style_data=table_style,
                    style_data_conditional=k8_table_data_conditional,
                    style_header=table_header,
                    style_header_conditional=table_header_conditional,
                    style_cell=table_cell,
                    style_cell_conditional=table_cell_conditional,
                    merge_duplicate_headers=True,
                    style_as_list_view=True,
                )
            ]

            if not final_attendance_data.empty:
                k8_other_table = [
                    dash_table.DataTable(
                        final_attendance_data.to_dict("records"),
                        columns=k8_table_columns,
                        style_data=table_style,
                        style_data_conditional=k8_table_data_conditional,
                        style_header=table_header,
                        style_header_conditional=table_header_conditional,
                        style_cell=table_cell,
                        style_cell_conditional=table_cell_conditional,
                        merge_duplicate_headers=True,
                        style_as_list_view=True,
                    )
                ]

            else:
                k8_other_table = empty_table

            k8_not_calculated_table = [
                dash_table.DataTable(
                    k8_not_calculated_data.to_dict("records"),
                    columns=[
                        {"name": i, "id": i} for i in k8_not_calculated_data.columns
                    ],
                    style_data=table_style,
                    style_data_conditional=k8_table_data_conditional,
                    style_header=table_header,
                    style_header_conditional=table_header_conditional,
                    style_cell=table_cell,
                    style_cell_conditional=[
                        {
                            "if": {"column_id": "Category"},
                            "textAlign": "left",
                            "fontWeight": "500",
                            "paddingLeft": "10px",
                            "width": "40%",  # Width is different than default
                        },
                    ],
                    style_as_list_view=True,
                )
            ]

    ## HS academic information
    ## TODO: ADD SAT GRADE 11/ACT SCORES
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
            k8_grade_table = []
            k8_ethnicity_table = []
            k8_status_table = []
            k8_other_table = []
            k8_not_calculated_table = []
            k8_table_container = {"display": "none"}

        if len(academic_data_hs.index) == 0:
            hs_grad_overview_table = (
                hs_grad_ethnicity_table
            ) = (
                hs_grad_status_table
            ) = hs_eca_table = hs_not_calculated_table = empty_table

        else:
            # split data into subsets for display in various tables
            overview = [
                "Total Graduation Rate",
                "Non-Waiver Graduation Rate",
                "State Average Graduation Rate",
                "Strength of Diploma",
            ]

            if school_index["School Type"].values[0] == "AHS":
                overview.append("CCR Percentage")

            # for academic information, strip out all comparative data and clean headers
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

            grad_overview = hs_academic_info[
                hs_academic_info["Category"].str.contains("|".join(overview))
            ]
            grad_ethnicity = hs_academic_info[
                hs_academic_info["Category"].str.contains("|".join(ethnicity))
            ]
            grad_status = hs_academic_info[
                hs_academic_info["Category"].str.contains("|".join(status))
            ]
            eca_data = hs_academic_info[
                hs_academic_info["Category"].str.contains("|".join(["Grade 10"]))
            ]

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

            hs_table_columns = [
                {
                    "name": col,
                    "id": col,
                    "type": "numeric",
                    "format": Format(
                        scheme=Scheme.percentage, precision=2, sign=Sign.parantheses
                    ),
                }
                for (col) in hs_academic_info.columns
            ]

            # color average difference either red (lower than average)
            # or green (higher than average) in '+/-' cols
            hs_table_data_conditional = [
                {"if": {"row_index": "odd"}, "backgroundColor": "#eeeeee"},
                {  # Kludge to ensure first col header has border
                    "if": {"row_index": 0, "column_id": "Category"},
                    "borderTop": ".5px solid #6783a9",
                },
            ]

            hs_grad_overview_table = [
                dash_table.DataTable(
                    grad_overview.to_dict("records"),
                    columns=hs_table_columns,
                    style_data=table_style,
                    style_data_conditional=hs_table_data_conditional,
                    style_header=table_header,
                    style_cell=table_cell,
                    style_cell_conditional=[
                        {
                            "if": {"column_id": "Category"},
                            "textAlign": "left",
                            "fontWeight": "500",
                            "paddingLeft": "20px",
                            "width": "25%",
                        },
                    ],
                    merge_duplicate_headers=True,
                    style_as_list_view=True,
                )
            ]

            hs_grad_ethnicity_table = [
                dash_table.DataTable(
                    grad_ethnicity.to_dict("records"),
                    columns=hs_table_columns,
                    style_data=table_style,
                    style_data_conditional=hs_table_data_conditional,
                    style_header=table_header,
                    style_cell=table_cell,
                    style_cell_conditional=[
                        {
                            "if": {"column_id": "Category"},
                            "textAlign": "left",
                            "fontWeight": "500",
                            "paddingLeft": "20px",
                            "width": "25%",
                        },
                    ],
                    merge_duplicate_headers=True,
                    style_as_list_view=True,
                )
            ]

            hs_grad_status_table = [
                dash_table.DataTable(
                    grad_status.to_dict("records"),
                    columns=hs_table_columns,
                    style_data=table_style,
                    style_data_conditional=hs_table_data_conditional,
                    style_header=table_header,
                    style_cell=table_cell,
                    style_cell_conditional=[
                        {
                            "if": {"column_id": "Category"},
                            "textAlign": "left",
                            "fontWeight": "500",
                            "paddingLeft": "20px",
                            "width": "25%",
                        },
                    ],
                    merge_duplicate_headers=True,
                    style_as_list_view=True,
                )
            ]

            hs_eca_table = [
                dash_table.DataTable(
                    eca_data.to_dict("records"),
                    columns=hs_table_columns,
                    style_data=table_style,
                    style_data_conditional=hs_table_data_conditional,
                    style_header=table_header,
                    style_cell=table_cell,
                    style_cell_conditional=[
                        {
                            "if": {"column_id": "Category"},
                            "textAlign": "left",
                            "fontWeight": "500",
                            "paddingLeft": "20px",
                            "width": "25%",
                        },
                    ],
                    merge_duplicate_headers=True,
                    style_as_list_view=True,
                )
            ]

            hs_not_calculated_table = [
                dash_table.DataTable(
                    hs_not_calculated_data.to_dict("records"),
                    columns=[
                        {
                            "name": i,
                            "id": i,
                            "type": "numeric",
                            "format": FormatTemplate.percentage(2),
                        }
                        for i in hs_not_calculated_data.columns
                    ],
                    style_data=table_style,
                    style_data_conditional=hs_table_data_conditional,
                    style_header=table_header,
                    style_cell=table_cell,
                    style_cell_conditional=[
                        {
                            "if": {"column_id": "Category"},
                            "textAlign": "left",
                            "fontWeight": "500",
                            "paddingLeft": "20px",
                            "width": "45%",
                        },
                    ],
                    style_as_list_view=True,
                )
            ]

    return (
        k8_grade_table,
        k8_ethnicity_table,
        k8_status_table,
        k8_other_table,
        k8_not_calculated_table,
        k8_table_container,
        hs_grad_overview_table,
        hs_grad_ethnicity_table,
        hs_grad_status_table,
        hs_eca_table,
        hs_not_calculated_table,
        hs_table_container,
    )


#### Layout

label_style = {
    "height": "20px",
    "backgroundColor": "#6783a9",
    "fontSize": "12px",
    "fontFamily": "Roboto, sans-serif",
    "color": "#ffffff",
    "border": "none",
    "textAlign": "center",
    "fontWeight": "bold",
    "paddingBottom": "5px",
    "paddingTop": "5px",
}


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
                                    html.Label(
                                        "Proficiency by Grade", style=label_style
                                    ),
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
                                    html.Label(
                                        "Proficiency by Ethnicity", style=label_style
                                    ),
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
                                    html.Label(
                                        "Proficiency by Status", style=label_style
                                    ),
                                    html.Div(id="k8-status-table"),
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
                                    html.Label(
                                        "Other Academic Indicators", style=label_style
                                    ),
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
                                    html.Label(
                                        "Not Currently Calculated", style=label_style
                                    ),
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
                                    html.Label(
                                        "Graduation Rate Overview", style=label_style
                                    ),
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
                                    html.Label(
                                        "Graduation Rate by Ethnicity",
                                        style=label_style,
                                    ),
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
                                    html.Label(
                                        "Graduation Rate by Status", style=label_style
                                    ),
                                    html.Div(id="hs-grad-status-table"),
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
                                    html.Label(
                                        "End of Course Assessments", style=label_style
                                    ),
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
                                    html.Label(
                                        "Not Currently Calculated", style=label_style
                                    ),
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
        id="mainContainer",
        style={"display": "flex", "flexDirection": "column"},
    )
