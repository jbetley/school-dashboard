######################
# About/Demographics #
######################
# author:   jbetley
# date:     08.15.22

## TODO: Add 2021-22 EL and Special Education Demographics
## TODO: Add Federal Rating for AHS/HS 2020-21 (from academichs)


from dash import dcc, html, dash_table, Input, Output
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import numpy as np

from app import app

# np.warnings.filterwarnings('ignore')


## Callback ##
@app.callback(
    Output("school-name", "children"),
    Output("info-table", "children"),
    Output("grade-table", "children"),
    Output("enroll-title", "children"),
    Output("enroll-table", "children"),
    Output("adm_fig", "figure"),
    Output("ethnicity-fig", "figure"),
    Output("status-fig", "figure"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("dash-session", "data"),
)
def update_about_page(school, year, data):
    if not school:
        raise PreventUpdate

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
    #    color=["#98abc5","#8a89a6","#7b6888","#6b486b","#a05d56","#d0743c","#ff8c00"]
    bar_colors = ["#98abc5", "#c5b298"]

    # Get basic school information
    school_index = pd.DataFrame.from_dict(data["0"])
    school_name = school_index["School Name"].values[0]
    info = school_index[["City", "Principal", "Opening Year"]]
    school_info = info.T  # transpose data for display
    school_info = school_info.reset_index()

    print("ABOUT")
    print("***************************************")
    print(school_index)
    # move first row (School Name) into header row
    school_info.columns = school_info.iloc[0]
    school_info = school_info[1:]

    info_table = [
        dash_table.DataTable(
            school_info.to_dict("records"),
            columns=[{"name": i, "id": i} for i in school_info.columns],
            style_data={
                "fontSize": "12px",
                "fontFamily": "Roboto, sans-serif",
                "border": "none",
            },
            style_header={
                "backgroundColor": "#ffffff",
                "fontSize": "12px",
                "fontFamily": "Roboto, sans-serif",
                "color": "#6783a9",
                "textAlign": "center",
                "bottomBorder": "0px",
            },
            style_cell={
                "whiteSpace": "normal",
                #                            'height': 'auto',
                "textAlign": "center",
                "color": "#6783a9",
                "boxShadow": "0 0",
                "minWidth": "25px",
                "width": "25px",
                "maxWidth": "25px",
            },
            style_as_list_view=True,
        )
    ]

    ### School Enrollment
    # Get demographic data for school & corp (matching school corporation of residence by corp id) and filter by selected year
    selected_year = str(year)

    school_demographics = pd.DataFrame.from_dict(data["8"])
    corp_demographics = pd.DataFrame.from_dict(data["9"])

    current_year = selected_year
    previous_year = int(current_year) - 1
    year_string = str(previous_year) + "-" + str(current_year)[-2:]

    enroll_title = "Enrollment " + "(" + year_string + ")"

    if len(school_demographics.index) == 0:
        enroll_table = [
            dash_table.DataTable(
                columns=[
                    {"id": "emptytable", "name": "No Data to Display"},
                ],
                style_header={
                    "fontSize": "14px",
                    "border": "none",
                    "verticalAlign": "center",
                    "textAlign": "center",
                    "color": "#6783a9",
                    "fontFamily": "Roboto, sans-serif",
                },
            )
        ]

    else:
        enrollment_filter = school_demographics.filter(
            regex=r"^Grade \d{1}|[1-9]\d{1}$;|^Pre-K$|^Kindergarten$|^Total Enrollment$",
            axis=1,
        )
        enrollment_filter = enrollment_filter[
            [c for c in enrollment_filter if c not in ["Total Enrollment"]]
            + ["Total Enrollment"]
        ]
        enrollment_filter = enrollment_filter.dropna(axis=1, how="all")

        school_enrollment = enrollment_filter.T
        school_enrollment.rename(
            columns={school_enrollment.columns[0]: "Enrollment"}, inplace=True
        )
        school_enrollment.transpose().values.tolist()
        school_enrollment.rename(index={"Total Enrollment": "Total"}, inplace=True)

        school_enrollment = school_enrollment.reset_index()

        enroll_table = [
            dash_table.DataTable(
                school_enrollment.to_dict("records"),
                columns=[{"name": i, "id": i} for i in school_enrollment.columns],
                # TODO: Row Height Adjustment not working
                css=[
                    {
                        "selector": ".dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner tr",
                        "rule": "max-height: 15px !important; height: 15px !important;",
                    }
                ],
                style_data={
                    "fontSize": "12px",
                    "fontFamily": "Roboto, sans-serif",
                    "border": "none",
                },
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "#eeeeee"},
                    {
                        "if": {
                            "column_id": "index",
                        },
                        "borderRight": ".5px solid #6783a9",
                    },
                    {
                        "if": {"filter_query": '{index} eq "Total"'},
                        "borderTop": ".5px solid #6783a9",
                    },
                ],
                style_header={
                    "display": "none",
                    "border": "none",
                },
                style_cell={
                    "whiteSpace": "normal",
                    "height": "auto",
                    "textAlign": "center",
                    "color": "#6783a9",
                    #                            'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                },
                style_cell_conditional=[
                    # {
                    #     'if': {
                    #         'column_id': 'Category'
                    #         },
                    #         'textAlign': 'left',
                    #         'fontWeight': '500',
                    #         'paddingLeft': '20px',
                    #         'width': '35%'
                    # },
                ],
            )
        ]

    #### State and Federal Ratings
    letter_gradesK8 = pd.DataFrame.from_dict(data["2"])
    letter_gradesK12 = pd.DataFrame.from_dict(data["5"])

    if (
        (
            school_index["School Type"].values[0] == "K8"
            and len(letter_gradesK8.index) == 0
        )
        or school_index["School Type"].values[0] == "K12"
        and (len(letter_gradesK8.index) == 0 and len(letter_gradesK8.index) == 0)
        or (
            school_index["School Type"].values[0] == "AHS"
            or school_index["School Type"].values[0] == "HS"
        )
        and len(letter_gradesK12.index) == 0
    ):
        grade_table = [
            dash_table.DataTable(
                columns=[
                    {"id": "emptytable", "name": "No Data to Display"},
                ],
                style_header={
                    "fontSize": "14px",
                    "border": "none",
                    "verticalAlign": "center",
                    "textAlign": "center",
                    "color": "#6783a9",
                    "fontFamily": "Roboto, sans-serif",
                },
            )
        ]
    else:
        grade_cols = ["State Grade", "Federal Rating", "Year"]

        if (
            school_index["School Type"].values[0] == "K8"
            or school_index["School Type"].values[0] == "K12"
        ):
            # filter dataframe
            grade_data = letter_gradesK8[grade_cols]

            # replace 0 with NaN
            grade_data[grade_cols] = grade_data[grade_cols].replace(
                {"0": np.nan, 0: np.nan}
            )

            # transpose
            grade_data = (
                grade_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )

        elif (
            school_index["School Type"].values[0] == "HS"
            or school_index["School Type"].values[0] == "AHS"
        ):
            grade_data = letter_gradesK12[["State Grade", "Federal Rating", "Year"]]

            # replace 0 with NaN
            grade_data[grade_cols] = grade_data[grade_cols].replace(
                {"0": np.nan, 0: np.nan}
            )

            grade_data = (
                grade_data.set_index("Year")
                .T.rename_axis("Category")
                .rename_axis(None, axis=1)
                .reset_index()
            )

        grade_table = [
            dash_table.DataTable(
                grade_data.to_dict("records"),
                columns=[
                    {"name": str(i), "id": str(i)} for i in grade_data.columns
                ],  # [{'name': i, 'id': i} for i in grade_data.columns],
                style_data={
                    "fontSize": "12px",
                    "fontFamily": "Roboto, sans-serif",
                    "border": "none",
                },
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "#eeeeee"}
                ],
                style_header={
                    "backgroundColor": "#ffffff",
                    "fontSize": "12px",
                    "fontFamily": "Roboto, sans-serif",
                    #                            'fontFamily': 'Open Sans, sans-serif',
                    "color": "#6783a9",
                    "textAlign": "center",
                    "fontWeight": "bold",
                },
                style_cell={
                    "whiteSpace": "normal",
                    #                            'height': 'auto',
                    "textAlign": "center",
                    "color": "#6783a9",
                    "fontFamily": "Roboto, sans-serif",
                    "boxShadow": "0 0",
                    "minWidth": "25px",
                    "width": "25px",
                    "maxWidth": "25px",
                },
                style_cell_conditional=[
                    {
                        "if": {"column_id": "Category"},
                        "textAlign": "left",
                        "fontWeight": "500",
                        "paddingLeft": "20px",
                        "width": "35%",
                    },
                ],
                style_as_list_view=True,
            )
        ]

    #### ADM Chart
    linecolor = ["#d0743c", "#a05d56"]

    school_adm = pd.DataFrame.from_dict(data["10"])

    if len(school_adm.index) == 0:
        adm_fig = {
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
                            "color": "#6783a9",
                            "fontFamily": "Open Sans, sans-serif",
                        },
                    }
                ],
            }
        }
    else:
        # turn single row dataframe into two lists (column headers and data)
        adm_data = school_adm.iloc[0].tolist()
        years = school_adm.columns.tolist()

        # create chart
        adm_fig = px.line(
            x=years,
            y=adm_data,
            markers=True,
            color_discrete_sequence=linecolor,
        )
        adm_fig.update_traces(mode="markers+lines", hovertemplate=None)
        adm_fig["data"][0]["showlegend"] = True
        adm_fig["data"][0]["name"] = "ADM Average"
        adm_fig.update_yaxes(
            title="", showgrid=True, gridcolor="#b0c4de"
        )  # ticks='outside', tickcolor='#a9a9a9',
        adm_fig.update_xaxes(ticks="outside", tickcolor="#b0c4de", title="")

        adm_fig.update_layout(
            margin=dict(l=40, r=40, t=40, b=40),
            font=dict(family="Roboto, sans-serif", color="#6783a9", size=12),
            hovermode="x unified",
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

    #### Enrollment by Ethnicity ##
    ethnicity_school = school_demographics.loc[
        :,
        (school_demographics.columns.isin(ethnicity))
        | (school_demographics.columns.isin(["Corporation Name", "Total Enrollment"])),
    ]
    ethnicity_corp = corp_demographics.loc[
        :,
        (corp_demographics.columns.isin(ethnicity))
        | (corp_demographics.columns.isin(["Corporation Name", "Total Enrollment"])),
    ]

    if not ethnicity_school.empty:
        ethnicity_school.rename(
            columns={"Native Hawaiian or Other Pacific Islander": "Pacific Islander"},
            inplace=True,
        )
        ethnicity_corp.rename(
            columns={"Native Hawaiian or Other Pacific Islander": "Pacific Islander"},
            inplace=True,
        )

        ethnicity_data = pd.concat([ethnicity_school, ethnicity_corp])

        # Only Need This (calculate total enrollment) once
        total_enrollment = ethnicity_data["Total Enrollment"].tolist()
        total_enrollment = [int(i) for i in total_enrollment]
        ethnicity_data.drop("Total Enrollment", axis=1, inplace=True)

        cols = [i for i in ethnicity_data.columns if i not in ["Corporation Name"]]

        for col in cols:
            ethnicity_data[col] = pd.to_numeric(ethnicity_data[col], errors="coerce")

        ethnicity_data_t = ethnicity_data.set_index("Corporation Name").T

        for i in range(0, 2):  # Calculate Percentage
            ethnicity_data_t.iloc[:, i] = (
                ethnicity_data_t.iloc[:, i] / total_enrollment[i]
            )

        # Find rows where percentage is < .005 (1% after rounding)
        # Capture rows that meet this condition (for annotation)
        no_show = ethnicity_data_t[
            (
                (ethnicity_data_t.iloc[:, 0] < 0.005)
                | (pd.isnull(ethnicity_data_t.iloc[:, 0]))
                & (ethnicity_data_t.iloc[:, 1] < 0.005)
                | (pd.isnull(ethnicity_data_t.iloc[:, 1]))
            )
        ]

        anno_txt = ", ".join(
            no_show.index.values.astype(str)
        )  # create string of ethnicities with fewer than 1/2% of representation

        # Drop rows that meet this condition (to display in chart)
        ethnicity_data_t = ethnicity_data_t.drop(
            ethnicity_data_t[
                (
                    (ethnicity_data_t.iloc[:, 0] < 0.005)
                    | (pd.isnull(ethnicity_data_t.iloc[:, 0]))
                    & (ethnicity_data_t.iloc[:, 1] < 0.005)
                    | (pd.isnull(ethnicity_data_t.iloc[:, 1]))
                )
            ].index
        )

        # replace any remaining NaN with 0
        ethnicity_data_t = ethnicity_data_t.fillna(0)

        categories = ethnicity_data_t.index.tolist()

        elements = ethnicity_data_t.columns.tolist()

        trace_color = {elements[i]: bar_colors[i] for i in range(len(elements))}

        ethnicity_fig = px.bar(
            data_frame=ethnicity_data_t,
            x=[c for c in ethnicity_data_t.columns],
            y=categories,  # categories_wrap,
            text_auto=True,
            color_discrete_map=trace_color,
            opacity=0.9,
            orientation="h",
            barmode="group",
        )
        ethnicity_fig.update_xaxes(
            ticks="outside",
            tickcolor="#a9a9a9",
            range=[0, 1],
            dtick=0.2,
            tickformat=",.0%",
            title="",
        )
        ethnicity_fig.update_yaxes(ticks="outside", tickcolor="#a9a9a9", title="")
        ethnicity_fig.update_traces(textposition="outside")
        ethnicity_fig.for_each_trace(
            lambda t: t.update(textfont_color=t.marker.color, textfont_size=11)
        )
        ethnicity_fig.update_traces(hovertemplate=None, hoverinfo="skip")

        # Uncomment to add hover
        # ethnicity_fig['data'][0]['hovertemplate'] = ethnicity_fig['data'][0]['name'] + ': %{x}<extra></extra>'
        # ethnicity_fig['data'][1]['hovertemplate'] = ethnicity_fig['data'][1]['name'] + ': %{x}<extra></extra>'

        ethnicity_fig.update_layout(
            margin=dict(l=10, r=40, t=60, b=70, pad=0),
            font=dict(family="Roboto, sans-serif", color="#6783a9", size=11),
            legend=dict(yanchor="top", xanchor="center", orientation="h", x=0.4, y=1.2),
            bargap=0.15,
            bargroupgap=0,
            height=400,
            legend_title="",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        ethnicity_fig.add_annotation(
            text=(f"Less than .05% of student population: " + anno_txt + "."),
            showarrow=False,
            x=-0.1,  # -0.25,
            y=-0.25,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="bottom",
            xshift=-1,
            yshift=-5,
            font=dict(size=10, color="#6783a9"),
            align="left",
        )

        ## Enrollment by Status ##
        status_school = school_demographics.loc[
            :,
            (school_demographics.columns.isin(status))
            | (
                school_demographics.columns.isin(
                    ["Corporation Name", "Total Enrollment"]
                )
            ),
        ]
        status_corp = corp_demographics.loc[
            :,
            (corp_demographics.columns.isin(status))
            | (
                corp_demographics.columns.isin(["Corporation Name", "Total Enrollment"])
            ),
        ]
        status_data = pd.concat([status_school, status_corp])

        total_enrollment = status_data["Total Enrollment"].tolist()
        total_enrollment = [int(i) for i in total_enrollment]
        status_data.drop("Total Enrollment", axis=1, inplace=True)

        cols = [i for i in status_data.columns if i not in ["Corporation Name"]]
        for col in cols:
            status_data[col] = pd.to_numeric(status_data[col], errors="coerce")

        status_data_t = status_data.set_index("Corporation Name").T

        for i in range(0, 2):  # Calculate Percentage
            status_data_t.iloc[:, i] = status_data_t.iloc[:, i] / total_enrollment[i]

        # wrap text
        # categories = status_data_t.index.tolist()
        categories_wrap = [
            "English<br>Language<br>Learners",
            "Special<br>Education",
            "Free/Reduced<br>Price Meals",
            "Paid Meals",
        ]

        elements = status_data_t.columns.tolist()

        trace_color = {elements[i]: bar_colors[i] for i in range(len(elements))}

        status_fig = px.bar(
            data_frame=status_data_t,
            x=[c for c in status_data_t.columns],
            y=categories_wrap,
            text_auto=True,
            color_discrete_map=trace_color,
            opacity=0.9,
            orientation="h",
            barmode="group",
        )
        status_fig.update_xaxes(
            ticks="outside",
            tickcolor="#a9a9a9",
            range=[0, 1],
            dtick=0.2,
            tickformat=",.0%",
            title="",
        )
        status_fig.update_yaxes(ticks="outside", tickcolor="#a9a9a9", title="")

        # add text traces
        status_fig.update_traces(textposition="outside")

        # want to distinguish between null (no data) and '0'
        # so loop through data and only color text traces when the value of x (t.x) is not NaN
        # display all: status_fig.for_each_trace(lambda trace: trace.update(textfont_color=trace.marker.color,textfont_size=11))

        for t in status_fig.data:
            status_fig.update_traces(
                textfont_color=np.where(~np.isnan(t.x), t.marker.color, "white"),
                textfont_size=11,
            )

        status_fig.update_traces(hovertemplate=None, hoverinfo="skip")

        # Uncomment below to add hover
        # status_fig['data'][0]['hovertemplate'] = status_fig['data'][0]['name'] + ': %{x}<extra></extra>'
        # status_fig['data'][1]['hovertemplate'] = status_fig['data'][1]['name'] + ': %{x}<extra></extra>'

        status_fig.update_layout(
            margin=dict(l=10, r=40, t=60, b=70, pad=0),
            font=dict(family="Roboto, sans-serif", color="#6783a9", size=11),
            legend=dict(yanchor="top", xanchor="center", orientation="h", x=0.4, y=1.2),
            bargap=0.15,
            bargroupgap=0,
            height=400,
            legend_title="",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

    else:
        status_fig = ethnicity_fig = {
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
                            "color": "#6783a9",
                            "fontFamily": "Roboto, sans-serif",
                        },
                    }
                ],
            }
        }

    return (
        school_name,
        info_table,
        grade_table,
        enroll_title,
        enroll_table,
        adm_fig,
        ethnicity_fig,
        status_fig,
    )


## End Callback

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
                        html.Label(id="school-name", style=label_style),
                        html.Div(id="info-table"),
                    ],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [
                        html.Label("State and Federal Ratings", style=label_style),
                        html.Div(id="grade-table"),
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
                        html.Label(id="enroll-title", style=label_style),
                        html.Div(id="enroll-table"),
                    ],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [
                        html.Label("Enrollment History", style=label_style),
                        dcc.Graph(
                            id="adm_fig", figure={}, config={"displayModeBar": False}
                        ),
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
                        html.Label("Enrollment by Status", style=label_style),
                        dcc.Graph(
                            id="status-fig", figure={}, config={"displayModeBar": False}
                        ),
                    ],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [
                        html.Label("Enrollment by Ethnicity", style=label_style),
                        dcc.Graph(
                            id="ethnicity-fig",
                            figure={},
                            config={"displayModeBar": False},
                        ),
                    ],
                    className="pretty_container six columns",
                ),
            ],
            className="bare_container twelve columns",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flexDirection": "column"},
)

if __name__ == "__main__":
    app.run_server(debug=True)
