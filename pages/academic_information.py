#########################################
# ICSB Dashboard - Academic Information #
#########################################
# author:   jbetley
# version:  .99.021323

import dash
import plotly.colors
import plotly.express as px
from dash import html, dcc, dash_table, Input, Output, callback
from dash.exceptions import PreventUpdate
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Sign
# import numpy as np
import json
import pandas as pd
import re

from .chart_helpers import blank_fig, make_stacked_bar
from .calculations import round_percentages

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

# ## Blank (Loading) Fig ##
# # https://stackoverflow.com/questions/66637861/how-to-not-show-default-dcc-graph-template-in-dash
# def blank_fig():
#     fig = {
#         "layout": {
#             "xaxis": {"visible": False},
#             "yaxis": {"visible": False},
#             "annotations": [
#                 {
#                     "text": "Loading . . .",
#                     "xref": "paper",
#                     "yref": "paper",
#                     "showarrow": False,
#                     "font": {
#                         "size": 16,
#                         "color": "#6783a9",
#                         "family": "Roboto, sans-serif",
#                     },
#                 }
#             ],
#         }
#     }
#     return fig

@callback(
    Output("k8-grade-table", "children"),
    Output("k8-grade-ela-fig", "figure"),
    Output("k8-grade-math-fig", "figure"),
    Output("k8-ethnicity-table", "children"),
    Output("k8-ethnicity-ela-fig", "figure"),
    Output("k8-ethnicity-math-fig", "figure"),    
    Output("k8-subgroup-table", "children"),
    Output("k8-subgroup-ela-fig", "figure"),
    Output("k8-subgroup-math-fig", "figure"),
    Output("k8-other-table", "children"),
    Output("k8-not-calculated-table", "children"),
    Output("k8-table-container", "style"),
    Output("hs-grad-overview-table", "children"),
    Output("hs-grad-ethnicity-table", "children"),
    Output("hs-grad-subgroup-table", "children"),
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
    subgroup = [
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

    grades_ordinal = [
        "3rd",
        "4th",
        "5th",
        "6th",
        "7th",
        "8th",
        # "Total",
        # "IREAD Pass %",
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
        hs_grad_subgroup_table = []
        hs_eca_table = []
        hs_not_calculated_table = []
        hs_table_container = {"display": "none"}

        k8_grade_table = empty_table
        k8_ethnicity_table = empty_table
        k8_subgroup_table = empty_table
        k8_other_table = empty_table
        k8_not_calculated_table = empty_table

    else:
        ## TESTING 100% Stackd Bar Chart ##
        pd.set_option("display.max_rows", 400)
        # Clean up dataframe (none of these work)
        # k8_all_data.columns = k8_all_data.columns.str.replace(r'\s+', '', regex=True)
        # newlines = {"\nProficient \n%":"", "\n":" ","\n":" "}
        # k8_all_data.columns = [x.replace(newlines) for x in k8_all_data.columns.to_list()]
        # k8_all_data.columns = [x.replace({"\nProficient \n%":"", "\n":" ","\n":" "}) for x in k8_all_data.columns.to_list()]
        
        # load all proficiency information
        k8_all_data = pd.read_csv(r"data/ilearn2022all.csv", dtype=str)    

        # Clean up dataframe
        k8_all_data.columns = [
            x.replace("\nProficient \n%", "") for x in k8_all_data.columns.to_list()
        ]
        k8_all_data.columns = [x.replace(" \n", " ") for x in k8_all_data.columns.to_list()]
        k8_all_data.columns = [x.replace("\n", " ") for x in k8_all_data.columns.to_list()]

        # Get selected school data for all categories
        school_k8_all_data = k8_all_data.loc[k8_all_data["School ID"] == school]

        # drop columns with no values and reset index
        school_k8_all_data = school_k8_all_data.dropna(axis=1)
        school_k8_all_data = school_k8_all_data.reset_index()
        
        # TODO: May need this if we want to differentiate those categories
        # where there is no data from those categories where there were tested
        # students, but the proficiency value does not meet 'n-size' requirements
        # e.g., the value is '***'
        # school_k8_all_data =  school_k8_all_data.replace({'***': float(-99)})

        # NOTE: Leaving the above line commented out means that the below
        # conversion turns all '***' to NaN.
        for col in school_k8_all_data.columns:
            school_k8_all_data[col] = pd.to_numeric(
                school_k8_all_data[col], errors="coerce"
            )

        # Drop columns: 'Year','School ID', 'School Name', 'Corp ID','Corp Name'
        # TODO: May not need to do the above as we are filtering data for each chart
        # which will automatically exclude these categories
        # Also drop 'ELA & Math' Category (not currently displayed on dashboard)
        school_k8_all_data = school_k8_all_data.drop(
            list(
                school_k8_all_data.filter(
                    regex="ELA & Math|Year|Corp ID|Corp Name|School ID|School Name"
                )
            ),
            axis=1,
        )

        all_proficiency_data = school_k8_all_data.copy()

        proficiency_rating = [
            "Below Proficiency",
            "Approaching Proficiency",
            "At Proficiency",
            "Above Proficiency",
        ]

        # for each category, create a list of columns using the strings in
        #  'proficiency_rating' and then divide each column by 'Total Tested'
        categories = grades + ethnicity + subgroup

        for c in categories:
            for s in subject:
                category_subject = c + "|" + s

                colz = [category_subject + " " + x for x in proficiency_rating]
                total_tested = category_subject + " " + "Total Tested"

                if total_tested in all_proficiency_data.columns:

                    # if all_proficiency_data[colz].iloc[0].sum() == 0:
                    #     print(all_proficiency_data[colz])
                    # else
                    # replace NaN with 0
                    
                    # NOTE:
                    # At this point in the code there are three possible data configurations for 
                    # each grouping of Category + Subject:
                    # 1) Total Tested > 0 and all proficiency_rating(s) are > 0 (School has tested category AND
                    #       there is publicly available data)
                    # 2) Total Tested > 0 and all proficiency_rating(s) are == 'NaN' (School has tested category BUT
                    #       there is no publicly available data (insufficient N-size)))
                    # 3) Total Tested and all proficiency_rating == 0 (School does not have tested category)

                    # Neither (2) nor (3) should be displayed. However, we do want to track which
                    # Category/Subject combinations meet either condition (for figure annotation
                    # purposes).

                    #all_proficiency_data[colz] = all_proficiency_data[colz].fillna(0)

                    # Only want to calculate a percentage for those categories where both
                    # 'Total Tested' > 0 and the sum of all 'Category' values are > 0. If
                    # the sum of all 'Category' values is 0, there is no data. If the sum
                    # of all 'Category' values is NaN, there is insufficient data.
                    import numpy as np

                    # This is a bit of a hack.
                    # The sum of a series of '0' values is a numpy.int64 (0).
                    # The sume of a series of 'NaN' values is a numpy.float65 (0.0).
                    # So checking type of a sum of the row tells us whether a Category +
                    # Subject falls under (2) or (3) above.
                    
                    # print(all_proficiency_data[colz].iloc[0].sum())
                    # print(type(all_proficiency_data[colz].iloc[0].sum()))
                    # print(all_proficiency_data[colz].iloc[0].sum() == 0)
                    
                    if all_proficiency_data[colz].iloc[0].sum() == 0:

                        if isinstance(all_proficiency_data[colz].iloc[0].sum(), np.floating):
                            print('INSUFFICIENT N-SIZE')
                            print(colz)
                        elif isinstance(all_proficiency_data[colz].iloc[0].sum(), np.integer):
                            print('NO DATA')
                            print(colz)
                        # print((all_proficiency_data[colz].iloc[0].sum() == 0))
                    else:
                        print('YAY DATA')
                        print(colz)

                    if (all_proficiency_data[total_tested].values[0] > 0) and \
                        (all_proficiency_data[colz].iloc[0].sum() != 0):

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
                        # print('No Data: ', colz)
                        # print('Insufficient Data: ', colz)
                        all_proficiency_data.drop(colz, axis=1, inplace=True)

                    # each category has a calculated proficiency column named
                    # 'grade_subject'. Since we arent using it, we need to
                    # drop it from each category

                    all_proficiency_data.drop(category_subject, axis=1, inplace=True)

        # drop columns used for calculation that aren't in final chart
        all_proficiency_data.drop(
            list(
                all_proficiency_data.filter(
                    regex="School Total|Total Proficient"
                )
            ),
            axis=1,
            inplace=True,
        )

        # print(all_proficiency_data.T)
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

        # def make_stacked_bar(data):
        #     colors = plotly.colors.qualitative.Prism
            
        #     if data["Proficiency"].str.contains('Math').any():
        #         fig_title = year + " Math Proficiency Breakdown"
        #     else:
        #         fig_title = year + " ELA Proficiency Breakdown"
            
        #     data["Proficiency"] = data["Proficiency"].replace(
        #         {"Math ": "", "ELA ": ""}, regex=True
        #     )

        #     # Use this function to create wrapped text using
        #     # html tags based on the specified width
        #     # NOTE: adding two spaces before <br> to ensure the words at
        #     # the end of each break have the same spacing as 'ticksuffix'
        #     # below
        #     import textwrap
        #     def customwrap(s,width=16):
        #         return "  <br>".join(textwrap.wrap(s,width=width))
            
        #     # In order to get the total_tested value into hovertemplate
        #     # without displaying it on the chart, we need to pull the
        #     # Total Tested values out of the dataframe and into a new
        #     # column
        #     # Copy all of the Total Tested Values
        #     total_tested = data.loc[data['Proficiency'] == 'Total Tested']

        #     # Merge the total tested values with the existing dataframe
        #     # This adds 'percentage_x' and 'percentage_y' columns.
        #     # 'percentage_y' is equal to the Total Tested Values
        #     data = pd.merge(data, total_tested[['Category','Percentage']], on=['Category'], how='left')

        #     # rename the columns (percentage_x to Percentage & percentage_y to Total Tested)
        #     data.columns = ['Category','Percentage','Proficiency','Total Tested']

        #     # drop the Total Tested Rows
        #     data = data[(data['Proficiency'] != 'Total Tested')]

        #     fig = px.bar(
        #         data,
        #         x= data['Percentage'],
        #         y = data['Category'].map(customwrap),
        #         color=data['Proficiency'],
        #         barmode='stack',
        #         text=[f'{i}%' for i in data['Percentage']],
        #         # custom_data = np.stack((data['Proficiency'], data['Total Tested']), axis=-1),
        #         custom_data = [data['Proficiency'], data['Total Tested']],
        #         orientation="h",
        #         color_discrete_sequence=colors,
        #         height=200,
        #         title = fig_title
        #     )

        #     #TODO: Remove trace name. Show Total Tested only once. Remove legend colors.
            
        #     #customize the hovertemplate for each segment of each bar
        #     fig['data'][0]['hovertemplate']='Total Tested: %{customdata[1]}<br><br>' + '%{text}: %{customdata[0]}<extra></extra>'
        #     fig['data'][1]['hovertemplate']='Total Tested: %{customdata[1]}<br><br>' + '%{text}: %{customdata[0]}<extra></extra>'
        #     fig['data'][2]['hovertemplate']='Total Tested: %{customdata[1]}<br><br>' + '%{text}: %{customdata[0]}<extra></extra>'
        #     fig['data'][3]['hovertemplate']='Total Tested: %{customdata[1]}<br><br>' + '%{text}: %{customdata[0]}<extra></extra>'

        #     print(fig['data'][3])
        #     # Add hoverdata
        #     # TODO: Issue: In a 100% stacked bar chart traces are generated by grouping
        #     # a column with values adding up to 100%. In this case, there will always
        #     # be 4 values (the number of items in "proficiency_rating"). So each trace
        #     # is made up of 4 rows. With a unified hovermode, customdata[0] and customdata[1]
        #     #  read only the number of rows in the dataframe equal to the number of traces, in
        #     # this case 4. So we need to restructure customdata to include: each rating
        #     # print(data['Total Tested'])
        #     # data.loc[1, 'Total Tested'] = '99'
        #     # print(data['Total Tested'])

        #     # customdata = np.stack((data['Proficiency'], data['Total Tested']), axis=-1)
        #     # print(customdata)
        #     # hovertemplate = (
        #     #     'Total Tested: %{customdata[1]}<br>' +
        #     #     '%{text}: %{customdata[0]}<extra></extra>')
            
        #     # fig.update_traces(customdata=customdata, hovertemplate=hovertemplate)


        #     # the uniformtext_minsize and uniformtext_mode settings hide bar chart
        #     # text (Percentage) if the size of the chart causes the text of the font
        #     # to decrease below 8px. The text is required to be positioned 'inside'
        #     # the bar due to the 'textposition' variable
        #     fig.update_layout(
        #         margin=dict(l=10, r=10, t=20, b=0),
        #         font_family="Open Sans, sans-serif",
        #         font_color="steelblue",
        #         font_size=8,
        #         # legend=dict(
        #         #     orientation="h",
        #         #     title="",
        #         #     x=0,
        #         #     font=dict(
        #         #         family="Open Sans, sans-serif", color="steelblue", size=8
        #         #     ),
        #         # ),
        #         plot_bgcolor="white",
        #         hovermode='y unified',
        #         hoverlabel=dict(
        #             bgcolor = 'grey',
        #             font=dict(
        #                 family="Open Sans, sans-serif", color="white", size=8
        #             ),
        #         ),
        #         yaxis=dict(autorange="reversed"),
        #         uniformtext_minsize=8,
        #         uniformtext_mode='hide',
        #         title={
        #             'y':0.975,
        #             'x':0.5,
        #             'xanchor': 'center',
        #             'yanchor': 'top'},
        #         bargroupgap = 0,
        #         showlegend = False,
        #     )

        #     fig.update_traces(
        #         textfont_size=8,
        #         insidetextanchor = 'middle',
        #         textposition='inside',
        #         marker_line=dict(width=0),
        #         # bar_width=0,
        #         showlegend = False, # Trying to get rid of legend in hoverlabel
        #     )

        #     fig.update_xaxes(title="")

        #     # ticksuffix increases the space between the end of the tick label and the chart
        #     fig.update_yaxes(title="",ticksuffix = "  ")

        #     return fig

        # ELA by Grade
        
        grade_ela_fig_data = all_proficiency_data[
            all_proficiency_data["Category"].isin(grades_ordinal)
            & all_proficiency_data["Proficiency"].str.contains("ELA")
        ]
        k8_grade_ela_fig = make_stacked_bar(grade_ela_fig_data,year)

        # Math by Grade
        grade_math_fig_data = all_proficiency_data[
            all_proficiency_data["Category"].isin(grades_ordinal)
            & all_proficiency_data["Proficiency"].str.contains("Math")
        ]
        k8_grade_math_fig = make_stacked_bar(grade_math_fig_data,year)

        # ELA by Ethnicity
        ethnicity_ela_fig_data = all_proficiency_data[
            all_proficiency_data["Category"].isin(ethnicity)
            & all_proficiency_data["Proficiency"].str.contains("ELA")
        ]
        k8_ethnicity_ela_fig = make_stacked_bar(ethnicity_ela_fig_data,year)

        # Math by Ethnicity
        ethnicity_math_fig_data = all_proficiency_data[
            all_proficiency_data["Category"].isin(ethnicity)
            & all_proficiency_data["Proficiency"].str.contains("Math")
        ]
        k8_ethnicity_math_fig = make_stacked_bar(ethnicity_math_fig_data,year)

        # ELA by Subgroup
        subgroup_ela_fig_data = all_proficiency_data[
            all_proficiency_data["Category"].isin(subgroup)
            & all_proficiency_data["Proficiency"].str.contains("ELA")
        ]
        k8_subgroup_ela_fig = make_stacked_bar(subgroup_ela_fig_data,year)

        # Math by Subgroup
        subgroup_math_fig_data = all_proficiency_data[
            all_proficiency_data["Category"].isin(subgroup)
            & all_proficiency_data["Proficiency"].str.contains("Math")
        ]
        k8_subgroup_math_fig = make_stacked_bar(subgroup_math_fig_data,year)

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
                hs_grad_subgroup_table = []
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
            years_by_subgroup = k8_academic_info[
                k8_academic_info["Category"].str.contains("|".join(subgroup))
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

            k8_subgroup_table = [
                dash_table.DataTable(
                    years_by_subgroup.to_dict("records"),
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
            k8_subgroup_table = []
            k8_other_table = []
            k8_not_calculated_table = []
            k8_table_container = {"display": "none"}

        if len(academic_data_hs.index) == 0:
            hs_grad_overview_table = (
                hs_grad_ethnicity_table
            ) = (
                hs_grad_subgroup_table
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
            grad_subgroup = hs_academic_info[
                hs_academic_info["Category"].str.contains("|".join(subgroup))
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

            hs_grad_subgroup_table = [
                dash_table.DataTable(
                    grad_subgroup.to_dict("records"),
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
        hs_eca_table,
        hs_not_calculated_table,
        hs_table_container
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

fig_label_style = {
    "height": "14px",
    "backgroundColor": "#6783a9",
    "fontSize": "8px",
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
                                    dcc.Graph(id="k8-grade-ela-fig", figure=blank_fig(),config={'displayModeBar': False}),
                                ],
                                className="pretty_container four columns",
                            ),
                            html.Div(
                                [
                                    dcc.Graph(id="k8-grade-math-fig", figure=blank_fig(),config={'displayModeBar': False}),
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
                                    dcc.Graph(id="k8-ethnicity-ela-fig", figure=blank_fig(),config={'displayModeBar': False}),
                                ],
                                className="pretty_container four columns",
                            ),
                            html.Div(
                                [
                                    dcc.Graph(id="k8-ethnicity-math-fig", figure=blank_fig(),config={'displayModeBar': False}),
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
                                    html.Label(
                                        "Proficiency by Subgroup", style=label_style
                                    ),
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
                                    dcc.Graph(id="k8-subgroup-ela-fig", figure=blank_fig(),config={'displayModeBar': False}),
                                ],
                                className="pretty_container four columns",
                            ),
                            html.Div(
                                [
                                    dcc.Graph(id="k8-subgroup-math-fig", figure=blank_fig(),config={'displayModeBar': False}),
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
                                        "Graduation Rate by Subgroup", style=label_style
                                    ),
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