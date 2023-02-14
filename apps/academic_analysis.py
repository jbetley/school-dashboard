#####################
# Academic Analysis #
#####################
# author:   jbetley
# rev:     08.15.22

# TODO: Test all() vs any() effect on data (currently using any())
# TODO: May be way to refactor to reduce duplication (but not at expense of readibility)
# TODO: Add IREAD-3 chart? (14g)
# TODO: Add AHS/HS Analysis
# TODO: Do we need to mask out null or *** values when calculating mean()?

from dash import dcc, html, Input, Output
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import numpy as np

from app import app

# np.warnings.filterwarnings('ignore')

color = ["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#ff8c00"]
color_long = [
    "#98abc5",
    "#919ab6",
    "#8a89a6",
    "#837997",
    "#7b6888",
    "#73587a",
    "#6b486b",
    "#865361",
    "#a05d56",
    "#b86949",
    "#d0743c",
    "#e8801e",
    "#ff8c00",
]

### Functions ###


# single line chart (input: dataframe and title string)
def make_line_chart(data):
    data.columns = data.columns.str.split("|").str[0]

    cols = [i for i in data.columns if i not in ["School Name", "Year"]]
    for col in cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data.sort_values("Year", inplace=True)

    marks = [v for v in list(data.columns) if v not in ["School Name", "Year"]]

    fig = px.line(
        data,
        x="Year",
        y=marks,
        markers=True,
        color_discrete_sequence=color,
    )
    fig.update_yaxes(range=[0, 1], dtick=0.2, tickformat=",.0%", title="Proficiency")
    fig.update_traces(mode="markers+lines", hovertemplate=None)
    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=60),
        title_x=0.5,
        font=dict(family="Open Sans, sans-serif", color="steelblue", size=10),
        hovermode="x unified",
        height=400,
        legend_title="",
    )
    return fig


# single bar chart (input: dataframe and title string)
def make_bar_chart(data, category):
    elements = data["School Name"].tolist()
    trace_color = {elements[i]: color[i] for i in range(len(elements))}

    fig = px.bar(
        data,
        x="School Name",
        y=category,
        color_discrete_map=trace_color,
        color="School Name",
    )
    fig.update_yaxes(range=[0, 1], dtick=0.2, tickformat=",.0%", title="")
    fig.update_xaxes(type="category", showticklabels=False, title="")
    fig.update_layout(
        title_x=0.5,
        margin=dict(l=40, r=40, t=40, b=60),
        font=dict(family="Open Sans, sans-serif", color="steelblue", size=10),
        legend=dict(orientation="h", title="", xanchor="center", x=0.45),
        height=400,
    )
    fig.update_traces(hovertemplate="<b>%{x}</b><br>Proficiency: %{y}<extra></extra>")

    return fig


# grouped bar chart (input: dataframe and title string)
def make_group_bar_chart(data):
    # remove trailing string
    data.columns = data.columns.str.split("|").str[0]

    # force non-string columns to numeric
    cols = [i for i in data.columns if i not in ["School Name", "Year"]]
    for col in cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    # drop 'Year' column
    data.drop(data.columns[[0]], axis=1, inplace=True)

    # transpose dataframe
    data_t = data.set_index("School Name").T

    # replace all '***' values (insufficient n-size) with NaN
    data_t = data_t.replace("***", np.nan)

    # identify and remove all rows (categories) where entire row is NaN (either 0 or '***)
    remove = data_t.index[data_t.isnull().all(1)]
    data_t = data_t.drop(remove)

    # create string of all removed categories for later annotation
    anno_txt = ", ".join(remove.values.astype(str))

    # replace any remaining NaN with 0
    data_t = data_t.fillna(0)

    categories = data_t.index.tolist()
    elements = data_t.columns.tolist()
    trace_color = {elements[i]: color[i] for i in range(len(elements))}

    fig = px.bar(
        data_frame=data_t,
        x=categories,
        y=elements,
        color_discrete_map=trace_color,
        opacity=0.9,
        orientation="v",
        barmode="group",
    )
    fig.update_yaxes(range=[0, 1], dtick=0.2, tickformat=",.0%", title="")
    fig.update_xaxes(title="")
    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=60),
        title_x=0.5,
        font=dict(family="Open Sans, sans-serif", color="steelblue", size=10),
        bargap=0.15,
        bargroupgap=0,
        height=400,
        legend_title="",
    )

    # add annotation if categories were removed
    if not remove.empty:
        fig.add_annotation(
            text=(f"<b>Insufficient n-size or no data:</b> " + anno_txt + "."),
            showarrow=False,
            x=-0.5,
            y=0,
            xref="x",  #'paper',
            yref="y",  #'paper',
            xanchor="left",
            yanchor="bottom",
            xshift=0,
            yshift=-50,
            font=dict(size=10, color="#6783a9"),
            align="left",
        )

    ### TODO: insert name in hovertext
    # customdata = np.stack((data['School Name']), axis=-1)
    # print(customdata)
    #    fig.update_traces(customdata=customdata, hovertemplate = '%{customdata} <b>%{x}</b><br>Proficiency: %{y}<extra></extra>')
    # status_fig['data'][1]['hovertemplate'] = status_fig['data'][1]['name'] + ': %{x}<extra></extra>'
    ####

    return fig


### End Functions ###


##  Build page based on dash-session data (see index.py)
@app.callback(
    Output("fig14a", "figure"),
    Output("fig14b", "figure"),
    Output("fig14c", "figure"),
    Output("fig14d", "figure"),
    Output("fig16c1", "figure"),
    Output("fig16d1", "figure"),
    Output("fig16c2", "figure"),
    Output("fig16d2", "figure"),
    Output("fig16a1", "figure"),
    Output("fig16b1", "figure"),
    Output("fig16a2", "figure"),
    Output("fig16b2", "figure"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("dash-session", "data"),
)
def update_acadanal_page(school, year, data):
    if not school:
        raise PreventUpdate

    selected_year = str(year)

    # define blank chart
    blank_chart = {
        "layout": {
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "annotations": [
                {
                    "text": "No Data to Display",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 16,
                        "color": "#4682b4",
                        "family": "Open Sans, sans-serif",
                    },
                }
            ],
        }
    }

    # Don't need the below. School data is empty df for HS/AHS
    # TODO: Currently no charts for AHS or HS - is there anything worth charting?

    #    if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'AHS':
    #        fig14a = fig14b = fig14c = fig14d = fig16c1 = fig16d1 = fig16c2 = fig16d2 = fig16a1 = fig16b1 = fig16a2 = fig16b2={
    #            "layout": {
    #                "xaxis": {
    #                    "visible": False
    #                },
    #                "yaxis": {
    #                    "visible": False
    #                },
    #                "annotations": [
    #                    {
    #                        "text": "No Data to Display",
    #                        "xref": "paper",
    #                        "yref": "paper",
    #                        "showarrow": False,
    #                        "font": {
    #                            'size': 16,
    #                            'color': '#4682b4',
    #                            'family': 'Open Sans, sans-serif'
    #                        }
    #                    }
    #                ]
    #            }
    #        }
    #    else:

    # Get school data (all years)
    k8_school_data = pd.DataFrame.from_dict(data["2"])

    if (
        len(k8_school_data.index) == 0
    ):  # if dataframe is empty (no data) all charts are blank
        fig14a = (
            fig14b
        ) = (
            fig14c
        ) = (
            fig14d
        ) = (
            fig16c1
        ) = (
            fig16d1
        ) = fig16c2 = fig16d2 = fig16a1 = fig16b1 = fig16a2 = fig16b2 = blank_chart

    else:
        # Set category and status types

        ethnicity = [
            "American Indian",
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

        current_year = selected_year

        # TODO: APPWIDE - figure out how to address 2019 and 2020
        # Special condition to account for the lack of 2020 data - force display of 2019 data
        if current_year == "2020":
            display_year = "2019"
        else:
            display_year = current_year

        #### Year over Year  Data ####

        # are there at least two years of data (length of index gives number of rows)
        if len(k8_school_data.index) >= 2:
            # Use only most recent two years
            k8_school_data_YoY = k8_school_data.iloc[:2]

            info_categories = k8_school_data_YoY[
                ["School Name", "State Grade", "Federal Rating"]
            ]

            # temporarily drop 'Category' column to simplify calculating difference
            k8_school_data_YoY.drop(
                columns=["School Name", "State Grade", "Federal Rating"],
                inplace=True,
                axis=1,
            )

            # Skip charts if school has no chartable data (includes neg values which are the result of subbing -99 for '***')
            # drop all columns with negative values
            k8_school_data_YoY = k8_school_data_YoY.loc[
                :, ~k8_school_data_YoY.lt(0).any()
            ]

            # add info_columns (strings) back to dataframe
            k8_school_data_YoY = k8_school_data_YoY.join(info_categories)

            #### Year over Year ELA Proficiency by Grade (1.4.a) #
            # regex matches: 'Grade X|ELA Proficient %'
            fig14a_data = k8_school_data_YoY.filter(
                regex=r"^Grade \d\|ELA Proficient %$|^School Name$|^Year$", axis=1
            )
            fig14a = make_line_chart(
                fig14a_data
            )  # ,'Year over Year ELA Proficiency by Grade')

            #### Year over Year Math Proficiency by Grade (1.4.b) #
            # regex matches: 'Grade X|Math Proficient %'
            fig14b_data = k8_school_data_YoY.filter(
                regex=r"^Grade \d\|Math Proficient %$|^School Name$|^Year$", axis=1
            )
            fig14b = make_line_chart(
                fig14b_data
            )  # ,'Year over Year Math Proficiency by Grade')

            #### Year over Year ELA Proficiency by Ethnicity (1.6.c) #
            headers = []
            for e in ethnicity:
                headers.append(e + "|" + "ELA Proficient %")

            fig16c1_data = k8_school_data_YoY.loc[
                :,
                (k8_school_data_YoY.columns.isin(headers))
                | (k8_school_data_YoY.columns.isin(["School Name", "Year"])),
            ]
            fig16c1_data.rename(
                columns={
                    "Native Hawaiian or Other Pacific Islander|ELA Proficient %": "Pacific Islander|ELA Proficient %"
                },
                inplace=True,
            )
            fig16c1 = make_line_chart(
                fig16c1_data
            )  # ,'Year over Year ELA Proficiency by Ethnicity')

            #### Year over Year Math Proficiency by Ethnicity (1.6.d) #
            headers = []
            for e in ethnicity:
                headers.append(e + "|" + "Math Proficient %")

            fig16d1_data = k8_school_data_YoY.loc[
                :,
                (k8_school_data_YoY.columns.isin(headers))
                | (k8_school_data_YoY.columns.isin(["School Name", "Year"])),
            ]
            fig16d1_data.rename(
                columns={
                    "Native Hawaiian or Other Pacific Islander|Math Proficient %": "Pacific Islander|Math Proficient %"
                },
                inplace=True,
            )
            fig16d1 = make_line_chart(
                fig16d1_data
            )  # ,'Year over Year Math Proficiency by Ethnicity')

            #### Year over Year ELA Proficiency by Status (1.6.c) #
            headers = []
            for s in status:
                headers.append(s + "|" + "ELA Proficient %")

            fig16c2_data = k8_school_data_YoY.loc[
                :,
                (k8_school_data_YoY.columns.isin(headers))
                | (k8_school_data_YoY.columns.isin(["School Name", "Year"])),
            ]
            fig16c2 = make_line_chart(
                fig16c2_data
            )  # ,'Year over Year ELA Proficiency by Status')

            #### Year over Year Math Proficiency by Status (1.6.d) #
            headers = []
            for s in status:
                headers.append(s + "|" + "Math Proficient %")

            fig16d2_data = k8_school_data_YoY.loc[
                :,
                (k8_school_data_YoY.columns.isin(headers))
                | (k8_school_data_YoY.columns.isin(["School Name", "Year"])),
            ]
            fig16d2 = make_line_chart(
                fig16d2_data
            )  # ,'Year over Year Math Proficiency by Status')

        else:  # only one year of data (zero years would be empty dataframe)
            fig14a = (
                fig14b
            ) = fig14d = fig16c1 = fig16d1 = fig16c2 = fig16d2 = blank_chart

        #### Similar and Comparable Schools [CURRENT YEAR]
        # display: 1) school value; 2) similar school avg; and 3) all comparable schools with data

        # Get current year school data
        school_current_data = k8_school_data.loc[
            k8_school_data["Year"] == int(display_year)
        ]

        # coerce data types to numeric
        for col in school_current_data.columns:
            school_current_data[col] = (
                pd.to_numeric(school_current_data[col], errors="coerce")
                .fillna(school_current_data[col])
                .tolist()
            )

        info_categories = school_current_data[
            ["School Name", "State Grade", "Federal Rating"]
        ]

        # temporarily drop 'Category' column to simplify calculating difference
        school_current_data.drop(
            columns=["School Name", "State Grade", "Federal Rating"],
            inplace=True,
            axis=1,
        )

        # Skip charts if school has no chartable data (includes neg values which are the result of subbing -99 for '***')
        # drop all columns with negative values
        school_current_data = school_current_data.loc[
            :, ~school_current_data.lt(0).any()
        ]

        # add info_columns (strings) back to dataframe
        school_current_data = school_current_data.join(info_categories)

        # get dataframe for traditional public schools located within school corporation that selected school resides
        k8_corp_data = pd.DataFrame.from_dict(data["3"])

        corp_current_data = k8_corp_data.loc[k8_corp_data["Year"] == int(display_year)]

        # coerce data types to numeric (except strings)
        for col in corp_current_data.columns:
            corp_current_data[col] = (
                pd.to_numeric(corp_current_data[col], errors="coerce")
                .fillna(corp_current_data[col])
                .tolist()
            )

        # filter unnecessary columns
        corp_current_data = corp_current_data.filter(
            regex=r"\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$|^School Name$",
            axis=1,
        )

        # comparable schools are (generally) smaller subset of 'most' similar schools
        comparison_schools = pd.DataFrame.from_dict(data["4"])

        # TODO: Why is Year a string in this df and an int in the school and corp dfs? How does datatype coercion work pre
        # and post conversion to dict in index.py?
        comp_current_data = comparison_schools.loc[
            comparison_schools["Year"] == display_year
        ]

        #### Current Year ELA Proficiency Compared to Similar Schools (1.4.c) #
        category = "School Total|ELA Proficient %"

        # Get school value for specific category
        if category in school_current_data.columns:
            fig14c_k8_school_data = school_current_data[["School Name", category]]

            # add corp average for category to dataframe
            fig14c_k8_school_data.loc[len(fig14c_k8_school_data.index)] = [
                "Corporation Average",
                corp_current_data[category].values[0],
            ]

            # Get comparable school values for the specific category
            fig14c_comp_data = comp_current_data[["School Name", category]]

            # Combine data, fix dtypes, and send to chart function
            fig14c_all_data = pd.concat([fig14c_k8_school_data, fig14c_comp_data])
            fig14c_all_data[category] = pd.to_numeric(fig14c_all_data[category])

            fig14c = make_bar_chart(
                fig14c_all_data, category
            )  # ,'Comparison: Current Year ELA Proficiency')
        else:
            fig14c = blank_chart

        #### Current Year Math Proficiency Compared to Similar Schools (1.4.d) #
        category = "School Total|Math Proficient %"

        if category in school_current_data.columns:
            fig14d_k8_school_data = school_current_data[["School Name", category]]

            # add corp average for category to dataframe
            fig14d_k8_school_data.loc[len(fig14d_k8_school_data.index)] = [
                "Corporation Average",
                corp_current_data[category].values[0],
            ]

            # Get comparable school values for the specific category
            fig14d_comp_data = comp_current_data[["School Name", category]]

            fig14d_all_data = pd.concat([fig14d_k8_school_data, fig14d_comp_data])
            fig14d_all_data[category] = pd.to_numeric(fig14d_all_data[category])

            fig14d = make_bar_chart(
                fig14d_all_data, category
            )  # ,'Comparison: Current Year Math Proficiency')
        else:
            fig14d = blank_chart

        ### TODO: HEEERREE

        #### ELA Proficiency by Ethnicity Compared to Similar Schools (1.6.a) [CURRENT YEAR]
        # Note: school proficiency comparison to corporation average proficiency by grade - can isolate grade level proficiency, but
        # cannot limit ethnicity/status comparison to exact grades (because it isn't broken out in raw data)

        headers = []
        for e in ethnicity:
            headers.append(e + "|" + "ELA Proficient %")

        # filter df to return only ethnicity categories
        fig16a1_k8_school_data = school_current_data.loc[
            :,
            (school_current_data.columns.isin(headers))
            | (school_current_data.columns.isin(["School Name", "Year"])),
        ]

        if (
            len(fig16a1_k8_school_data.columns) >= 3
        ):  # if less than 3 columns, there is no data to display
            # filter similar schools, get mean of each category (ignoring '***'), save in separate df, and rename
            fig16a1_corp_data = corp_current_data.loc[
                :,
                (corp_current_data.columns.isin(headers))
                | (corp_current_data.columns.isin(["School Name", "Year"])),
            ]

            # fig16a1_corp_data.loc['Avg'] = fig16a1_corp_data.mask(fig16a1_corp_data.isin(['***'])).mean()
            # fig16a1_corp_avg = fig16a1_corp_data.loc[['Avg']]

            fig16a1_corp_data["School Name"] = "School Corporation Average"

            # filter comparable schools
            # TODO: '***' ??
            fig16a1_comp_data = comp_current_data.loc[
                :,
                (comp_current_data.columns.isin(headers))
                | (comp_current_data.columns.isin(["School Name", "Year"])),
            ]

            # merge dataframes and send to chart function
            fig16a1_all_data = pd.concat(
                [fig16a1_corp_data, fig16a1_comp_data, fig16a1_k8_school_data]
            )
            fig16a1 = make_group_bar_chart(
                fig16a1_all_data
            )  # ,'Comparison: ELA Proficiency by Ethnicity')

        else:
            fig16a1 = blank_chart

        #### Math Proficiency by Ethnicity Compared to Similar Schools (1.6.b) #
        headers = []
        for e in ethnicity:
            headers.append(e + "|" + "Math Proficient %")

        fig16b1_k8_school_data = school_current_data.loc[
            :,
            (school_current_data.columns.isin(headers))
            | (school_current_data.columns.isin(["School Name", "Year"])),
        ]

        if (
            len(fig16b1_k8_school_data.columns) >= 3
        ):  # if less than 3 columns, there is no data to display
            fig16b1_corp_data = corp_current_data.loc[
                :,
                (corp_current_data.columns.isin(headers))
                | (corp_current_data.columns.isin(["School Name", "Year"])),
            ]

            # fig16b1_corp_data.loc['Avg'] = fig16b1_corp_data.mask(fig16b1_corp_data.isin(['***'])).mean()
            # fig16b1_corp_avg = fig16b1_corp_data.loc[['Avg']]
            fig16b1_corp_data["School Name"] = "School Corporation Average"

            fig16b1_comp_data = comp_current_data.loc[
                :,
                (comp_current_data.columns.isin(headers))
                | (comp_current_data.columns.isin(["School Name", "Year"])),
            ]

            fig16b1_all_data = pd.concat(
                [fig16b1_corp_data, fig16b1_comp_data, fig16b1_k8_school_data]
            )
            fig16b1 = make_group_bar_chart(
                fig16b1_all_data
            )  # ,'Comparison: Math Proficiency by Ethnicity')

        else:
            fig16b1 = blank_chart
        #### ELA Proficiency by Status Compared to Similar Schools (1.6.a) #
        headers = []
        for s in status:
            headers.append(s + "|" + "ELA Proficient %")

        fig16a2_k8_school_data = school_current_data.loc[
            :,
            (school_current_data.columns.isin(headers))
            | (school_current_data.columns.isin(["School Name", "Year"])),
        ]

        if (
            len(fig16a2_k8_school_data.columns) >= 3
        ):  # if less than 3 columns, there is no data to display
            fig16a2_corp_data = corp_current_data.loc[
                :,
                (corp_current_data.columns.isin(headers))
                | (corp_current_data.columns.isin(["School Name", "Year"])),
            ]

            # fig16a2_corp_data.loc['Avg'] = fig16a2_corp_data.mask(fig16a2_corp_data.isin(['***'])).mean()
            # fig16a2_corp_avg = fig16a2_corp_data.loc[['Avg']]
            fig16a2_corp_data["School Name"] = "School Corporation Average"

            fig16a2_comp_data = comp_current_data.loc[
                :,
                (comp_current_data.columns.isin(headers))
                | (comp_current_data.columns.isin(["School Name", "Year"])),
            ]

            fig16a2_all_data = pd.concat(
                [fig16a2_corp_data, fig16a2_comp_data, fig16a2_k8_school_data]
            )
            fig16a2 = make_group_bar_chart(
                fig16a2_all_data
            )  # ,'Comparison: ELA Proficiency by Status')

        else:
            fig16a2 = blank_chart

        #### Math Proficiency by Status Compared to Similar Schools (1.6.b) #
        headers = []
        for s in status:
            headers.append(s + "|" + "Math Proficient %")

        fig16b2_k8_school_data = school_current_data.loc[
            :,
            (school_current_data.columns.isin(headers))
            | (school_current_data.columns.isin(["School Name", "Year"])),
        ]

        if (
            len(fig16b2_k8_school_data.columns) >= 3
        ):  # if less than 3 columns, there is no data to display
            fig16b2_corp_data = corp_current_data.loc[
                :,
                (corp_current_data.columns.isin(headers))
                | (corp_current_data.columns.isin(["School Name", "Year"])),
            ]
            # fig16b2_corp_data.loc['Avg'] = fig16b2_corp_data.mask(fig16b2_corp_data.isin(['***'])).mean()
            # fig16b2_corp_avg = fig16b2_corp_data.loc[['Avg']]
            fig16b2_corp_data["School Name"] = "School Corporation Average"

            fig16b2_comp_data = comp_current_data.loc[
                :,
                (comp_current_data.columns.isin(headers))
                | (comp_current_data.columns.isin(["School Name", "Year"])),
            ]

            fig16b2_all_data = pd.concat(
                [fig16b2_corp_data, fig16b2_comp_data, fig16b2_k8_school_data]
            )
            fig16b2 = make_group_bar_chart(
                fig16b2_all_data
            )  # ,'Comparison: Math Proficiency by Status')

        else:
            fig16b2 = blank_chart

    return (
        fig14a,
        fig14b,
        fig14c,
        fig14d,
        fig16c1,
        fig16d1,
        fig16c2,
        fig16d2,
        fig16a1,
        fig16b1,
        fig16a2,
        fig16b2,
    )


## Layout ##
label_style = {
    "height": "20px",
    "backgroundColor": "#6783a9",
    "fontSize": "12px",
    "fontFamily": "Roboto, sans-serif",
    "color": "#ffffff",
    "textAlign": "center",
    "fontWeight": "bold",
    "paddingBottom": "5px",
    "paddingTop": "5px",
}

layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Year over Year ELA Proficiency by Grade", style=label_style
                        ),
                        dcc.Graph(id="fig14a", figure={}),
                    ],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [
                        html.Label(
                            "Year over Year Math Proficiency by Grade",
                            style=label_style,
                        ),
                        dcc.Graph(id="fig14b", figure={}),
                    ],
                    className="pretty_container six columns",
                ),
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Comparison: Current Year ELA Proficiency",
                            style=label_style,
                        ),
                        dcc.Graph(id="fig14c", figure={}),
                    ],
                    className="pretty_container twelve columns",
                ),
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Comparison: Current Year Math Proficiency",
                            style=label_style,
                        ),
                        dcc.Graph(id="fig14d", figure={}),
                    ],
                    className="pretty_container twelve columns",
                )
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Year over Year ELA Proficiency by Ethnicity",
                            style=label_style,
                        ),
                        dcc.Graph(id="fig16c1", figure={}),
                    ],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [
                        html.Label(
                            "Year over Year Math Proficiency by Ethnicity",
                            style=label_style,
                        ),
                        dcc.Graph(id="fig16d1", figure={}),
                    ],
                    className="pretty_container six columns",
                ),
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Year over Year ELA Proficiency by Status",
                            style=label_style,
                        ),
                        dcc.Graph(id="fig16c2", figure={}),
                    ],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [
                        html.Label(
                            "Year over Year Math Proficiency by Status",
                            style=label_style,
                        ),
                        dcc.Graph(id="fig16d2", figure={}),
                    ],
                    className="pretty_container six columns",
                ),
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Comparison: ELA Proficiency by Ethnicity",
                            style=label_style,
                        ),
                        dcc.Graph(id="fig16a1", figure={}),
                    ],
                    className="pretty_container twelve columns",
                ),
                html.Div(
                    [
                        html.Label(
                            "Comparison: Math Proficiency by Ethnicity",
                            style=label_style,
                        ),
                        dcc.Graph(id="fig16b1", figure={}),
                    ],
                    className="pretty_container twelve columns",
                ),
            ],
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Comparison: ELA Proficiency by Status", style=label_style
                        ),
                        dcc.Graph(id="fig16a2", figure={}),
                    ],
                    className="pretty_container twelve columns",
                ),
                html.Div(
                    [
                        html.Label(
                            "Comparison: Math Proficiency by Status", style=label_style
                        ),
                        dcc.Graph(id="fig16b2", figure={}),
                    ],
                    className="pretty_container twelve columns",
                ),
            ],
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flexDirection": "column"},
)

if __name__ == "__main__":
    app.run_server(debug=True)
