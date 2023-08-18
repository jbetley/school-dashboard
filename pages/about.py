#######################################
# ICSB Dashboard - About/Demographics #
#######################################
# author:   jbetley
# version:  1.09
# date:     08/14/23

import dash
from dash import dcc, html, dash_table, Input, Output, callback
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import numpy as np

from .load_data import ethnicity, subgroup, max_display_years, current_academic_year, get_school_index, \
    get_financial_data, get_demographic_data
from .chart_helpers import loading_fig, no_data_fig_label
from .table_helpers import no_data_table, no_data_page, create_key_table
from .calculations import get_excluded_years

dash.register_page(__name__, path="/", order=0, top_nav=True)

@callback(
    Output("update-table", "children"),        
    Output("enroll-title", "children"),
    Output("enroll-table", "children"),
    Output("adm-fig", "figure"),
    Output("ethnicity-title", "children"),
    Output("ethnicity-fig", "figure"),
    Output("subgroup-title", "children"),
    Output("subgroup-fig", "figure"),
    Output("about-main-container", "style"),
    Output("about-empty-container", "style"),   
    Output("about-no-data", "children"),
    Input("year-dropdown", "value"),
    Input("charter-dropdown", "value"),
)
def update_about_page(year: str, school: str):
    if not school:
        raise PreventUpdate

    selected_year_string = year
    selected_year_numeric = int(selected_year_string)
    previous_year_numeric = selected_year_numeric - 1
    previous_year_string = str(previous_year_numeric)

    year_title = previous_year_string + "-" + selected_year_string[-2:]
    enroll_title = ["Enrollment " + "(" + year_title + ")"]
    ethnicity_title = "Enrollment by Ethnicity " + "(" + year_title + ")"
    subgroup_title = "Enrollment by Subgroup " + "(" + year_title + ")"
    
    excluded_years = get_excluded_years(selected_year_string)

    # see full color list in chart_helpers.py
    linecolor = ["#df8f2d"]
    bar_colors = ["#74a2d7", "#df8f2d"]

    main_container = {"display": "block"}
    empty_container = {"display": "none"}
    no_data_to_display = no_data_page("School Enrollment & Demographics")

    selected_school = get_school_index(school)

    demographic_data = get_demographic_data(school)
    financial_data = get_financial_data(school)

    if (len(demographic_data.index) == 0 or demographic_data.empty) and \
        (len(financial_data.columns) <= 1 or financial_data.empty):
        update_table = []
        enroll_title = []
        enroll_table = []
        adm_fig = []
        ethnicity_title = ""
        ethnicity_fig = []
        subgroup_title = ""
        subgroup_fig = []

        main_container = {"display": "none"}
        empty_container = {"display": "block"}

    else:

        # Updates Table - Right Now hardcoded - may want to add to DB
        update_table_label = "Recent Updates"
        update_table_dict = {
            "Date": ["07.12.23", "08.16.23", "08.18.23", "08.18.23"],
            "Update": ["Added 2023 ILEARN data for all K-8 schools and school corporations.","Added 2023 IREAD Data for all K-8 schools and school corporations.", "Added 2023 SAT Scores  for all high schools and school corporations.", "Added 2023 Demographic Data  for all schools and school corporations."],
        }
        
        update_table_df = pd.DataFrame(update_table_dict)
        
        first_column_width = 15
        update_table = create_key_table(update_table_df, update_table_label, first_column_width)

        if excluded_years:
            demographic_data = demographic_data[~demographic_data["Year"].isin(excluded_years)]

        if len(demographic_data.index) == 0:
            enroll_table = no_data_table(enroll_title)
            subgroup_fig = no_data_fig_label("Enrollment by Subgroup", 400)
            ethnicity_fig = no_data_fig_label("Enrollment by Ethnicity", 400)

        else:

            # Enrollment table
            corp_id = str(selected_school["GEO Corp"].values[0])
            corp_demographics = get_demographic_data(corp_id)

            demographic_data = demographic_data.loc[demographic_data["Year"] == selected_year_numeric]
            corp_demographics = corp_demographics.loc[corp_demographics["Year"] == selected_year_numeric]

            enrollment_filter = demographic_data.filter(regex = r"^Grade \d{1}|[1-9]\d{1}$;|^Pre-K$|^Kindergarten$|^Total Enrollment$",axis=1)
            enrollment_filter = enrollment_filter[[c for c in enrollment_filter if c not in ["Total Enrollment"]] + ["Total Enrollment"]]
            enrollment_filter = enrollment_filter.dropna(axis=1, how="all")

            school_enrollment = enrollment_filter.T
            school_enrollment.rename(columns={school_enrollment.columns[0]:"Enrollment"}, inplace=True)
            school_enrollment.rename(index={"Total Enrollment":"Total"},inplace=True)

            school_enrollment = school_enrollment.reset_index()
      
            enroll_table = [
                dash_table.DataTable(
                    school_enrollment.to_dict("records"),
                    columns = [{"name": i, "id": i} for i in school_enrollment.columns],
                    style_data={
                        "fontSize": "12px",
                        "fontFamily": "Jost, sans-serif",
                        "border": "none"
                    },
                    style_data_conditional=[
                        {
                            "if": {
                                "row_index": "odd"
                            },
                            "backgroundColor": "#eeeeee"
                        },
                        {
                            "if": {
                                "column_id": "index",
                            },
                            "borderRight": ".5px solid #6783a9",
                        },
                        {
                            "if": {
                                "filter_query": "{index} eq 'Total'"
                            },
                            "borderTop": ".5px solid #6783a9",
                        },
                        {
                            "if": {
                                "state": "selected"
                            },
                            "backgroundColor": "rgba(112,128,144, .3)",
                            "border": "thin solid silver"
                        }                        
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
                    },
                )
            ]

        # Enrollment by ethnicity fig
        ethnicity_school = demographic_data.loc[:, (demographic_data.columns.isin(ethnicity)) | (demographic_data.columns.isin(["Corporation Name","Total Enrollment"]))].copy()
        ethnicity_corp = corp_demographics.loc[:, (corp_demographics.columns.isin(ethnicity)) | (corp_demographics.columns.isin(["Corporation Name","Total Enrollment"]))].copy()

        if not ethnicity_school.empty:

            ethnicity_school.rename(columns = {"Native Hawaiian or Other Pacific Islander": "Pacific Islander"}, inplace = True)
            ethnicity_corp.rename(columns = {"Native Hawaiian or Other Pacific Islander": "Pacific Islander"}, inplace = True)

            ethnicity_data = pd.concat([ethnicity_school,ethnicity_corp])

            # Only need to calculate total enrollment once
            total_enrollment = ethnicity_data["Total Enrollment"].tolist()
            total_enrollment = [int(i) for i in total_enrollment]
            ethnicity_data.drop("Total Enrollment",axis=1,inplace=True)

            cols = [i for i in ethnicity_data.columns if i not in ["Corporation Name"]]

            for col in cols:
                ethnicity_data[col]=pd.to_numeric(ethnicity_data[col], errors="coerce")

            ethnicity_data_t = ethnicity_data.set_index("Corporation Name").T

            # Calculate Percentage
            for i in range(0, 2): 
                ethnicity_data_t.iloc[:,i] = ethnicity_data_t.iloc[:,i] / total_enrollment[i]

            # Find rows where percentage is < .005 (1% after rounding) - and create string for annotation purposes
            no_show = ethnicity_data_t[((ethnicity_data_t.iloc[:, 0] < .005) | (pd.isnull(ethnicity_data_t.iloc[:, 0])) & (ethnicity_data_t.iloc[:, 1] < .005) | (pd.isnull(ethnicity_data_t.iloc[:, 1])))]
            ethnicity_anno_txt = ", ".join(no_show.index.values.astype(str))

            # Drop rows that meet the above condition
            ethnicity_data_t = ethnicity_data_t.drop(ethnicity_data_t[((ethnicity_data_t.iloc[:, 0] < .005) | (pd.isnull(ethnicity_data_t.iloc[:, 0])) & (ethnicity_data_t.iloc[:, 1] < .005) | (pd.isnull(ethnicity_data_t.iloc[:, 1])))].index)

            ethnicity_data_t = ethnicity_data_t.fillna(0)

            categories = ethnicity_data_t.index.tolist()
            elements = ethnicity_data_t.columns.tolist()

            trace_color = {elements[i]: bar_colors[i] for i in range(len(elements))}

            ethnicity_fig = px.bar(
                data_frame = ethnicity_data_t,
                x = [c for c in ethnicity_data_t.columns],
                y = categories,
                text_auto=True,
                color_discrete_map=trace_color,
                opacity = 0.9,
                orientation = "h",
                barmode = "group"
            )
            ethnicity_fig.update_xaxes(ticks="outside", tickcolor="#a9a9a9", range=[0, 1], dtick=0.2, tickformat=",.0%", title="")
            ethnicity_fig.update_yaxes(ticks="outside", tickcolor="#a9a9a9", title="")
            ethnicity_fig.update_traces(textposition="outside")
            ethnicity_fig.for_each_trace(lambda t: t.update(textfont_color=t.marker.color,textfont_size=11))
            ethnicity_fig.update_traces(hovertemplate = None, hoverinfo="skip")

            # Uncomment to add hover
            #ethnicity_fig["data"][0]["hovertemplate"] = ethnicity_fig["data"][0]["name"] + ": %{x}<extra></extra>"
            #ethnicity_fig["data"][1]["hovertemplate"] = ethnicity_fig["data"][1]["name"] + ": %{x}<extra></extra>"

            ethnicity_fig.update_layout(
                margin=dict(l=10, r=40, t=60, b=70,pad=0),
                font = dict(
                    family="Jost, sans-serif",
                    color="#6783a9",
                    size=11
                    ),
                legend=dict(
                    yanchor="top",
                    xanchor= "center",
                    orientation="h",
                    x=.4,
                    y=1.2
                ),
                bargap=.15,
                bargroupgap=0,
                height=400,
                legend_title="",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )

            ethnicity_fig.add_annotation(
                text = (f"Less than .05% of student population: " + ethnicity_anno_txt + "."),
                showarrow=False,
                x = -0.1,
                y = -0.25,
                xref="paper",
                yref="paper",
                xanchor="left",
                yanchor="bottom",
                xshift=-1,
                yshift=-5,
                font=dict(size=10, color="#6783a9"),
                align="left"
            )

            # Enrollment by subgroup fig
            subgroup_school = demographic_data.loc[:, (demographic_data.columns.isin(subgroup)) | (demographic_data.columns.isin(["Corporation Name","Total Enrollment"]))]
            subgroup_corp = corp_demographics.loc[:, (corp_demographics.columns.isin(subgroup)) | (corp_demographics.columns.isin(["Corporation Name","Total Enrollment"]))]
            subgroup_data = pd.concat([subgroup_school,subgroup_corp])

            total_enrollment = subgroup_data["Total Enrollment"].tolist()
            total_enrollment = [int(i) for i in total_enrollment]
            subgroup_data.drop("Total Enrollment",axis=1,inplace=True)

            cols=[i for i in subgroup_data.columns if i not in ["Corporation Name"]]
            for col in cols:
                subgroup_data[col]=pd.to_numeric(subgroup_data[col], errors="coerce")

            # store categories with no data (NaN)
            subgroup_no_data = subgroup_data[subgroup_data.columns[subgroup_data.isna().any()]].columns.tolist()

            subgroup_data_t = subgroup_data.set_index("Corporation Name").T

            # Calculate Percentage
            for i in range(0, 2):
                subgroup_data_t.iloc[:,i] = subgroup_data_t.iloc[:,i] / total_enrollment[i]

            # force categories to wrap
            categories_wrap=["English<br>Language<br>Learners", "Special<br>Education", "Free or Reduced<br>Price Meals", "Paid Meals"]

            elements = subgroup_data_t.columns.tolist()

            trace_color = {elements[i]: bar_colors[i] for i in range(len(elements))}

            subgroup_fig = px.bar(
                data_frame = subgroup_data_t,
                x = [c for c in subgroup_data_t.columns],
                y = categories_wrap,
                text_auto=True,
                color_discrete_map=trace_color,
                opacity = 0.9,
                orientation = "h",
                barmode = "group",
            )
            subgroup_fig.update_xaxes(ticks="outside", tickcolor="#a9a9a9", range=[0, 1], dtick=0.2, tickformat=",.0%", title="")
            subgroup_fig.update_yaxes(ticks="outside", tickcolor="#a9a9a9", title="")

            # add text traces
            subgroup_fig.update_traces(textposition="outside")

            # NOTE: In order to distinguish between null (no data) and "0" values,  loop through
            # the data and only color text traces when the value of x (t.x) is not NaN
            subgroup_fig.for_each_trace(lambda t: t.update(textfont_color=np.where(~np.isnan(t.x),t.marker.color, "white"),textfont_size=11))
            
            subgroup_fig.update_traces(hovertemplate = None, hoverinfo="skip")

            # Uncomment to add hover
            #subgroup_fig["data"][0]["hovertemplate"] = subgroup_fig["data"][0]["name"] + ": %{x}<extra></extra>"
            #subgroup_fig["data"][1]["hovertemplate"] = subgroup_fig["data"][1]["name"] + ": %{x}<extra></extra>"

            subgroup_fig.update_layout(
                margin=dict(l=10, r=40, t=60, b=70,pad=0),
                font = dict(
                    family="Jost, sans-serif",
                    color="#6783a9",
                    size=11
                    ),
                legend=dict(
                    yanchor="top",
                    xanchor= "center",
                    orientation="h",
                    x=.4,
                    y=1.2
                ),
                bargap=.15,
                bargroupgap=0,
                height=400,
                legend_title="",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )

            if subgroup_no_data:
                subgroup_anno_txt = ", ".join(subgroup_no_data)

                subgroup_fig.add_annotation(
                    text = (f"Data not available: " + subgroup_anno_txt + "."),
                    showarrow=False,
                    x = -0.1,
                    y = -0.25,
                    xref="paper",
                    yref="paper",
                    xanchor="left",
                    yanchor="bottom",
                    xshift=-1,
                    yshift=-5,
                    font=dict(size=10, color="#6783a9"),
                    align="left"
                )

        # Get ADM Data
        # NOTE: Usually we don't use Quarterly data, however, by Q3 ADM data is
        # known for the year. So we check the first data column and if ADM Avg
        # has data we use it.
        financial_data = financial_data.drop(["School ID","School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        available_years = financial_data.columns.difference(['Category'], sort=False).tolist()
        available_years = [int(c[:4]) for c in available_years]

        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year -  selected_year_numeric

        if selected_year_numeric < most_recent_finance_year:
            financial_data.drop(financial_data.columns[1:(years_to_exclude+1)], axis=1, inplace=True)

        if len(financial_data.columns) <= 1:
            adm_fig = no_data_fig_label("Average Daily Membership History",400)
        
        else:

            # ADM chart
            adm_values = financial_data[financial_data["Category"].str.contains("ADM Average")]
            adm_values = adm_values.drop("Category", axis=1)
            adm_values = adm_values.reset_index(drop=True)

            for col in adm_values.columns:
                adm_values[col] = pd.to_numeric(adm_values[col], errors="coerce")
            
            adm_values = adm_values.loc[:, (adm_values != 0).any(axis=0)]

            adm_values = adm_values[adm_values.columns[::-1]]

            # file exists, but there is no adm data
            if (int(adm_values.sum(axis=1).values[0]) == 0):

                adm_fig = no_data_fig_label("Average Daily Membership History",400)
            
            else:

                # ADM dataset can be longer than five years (maximum display), so
                # need to filter both the selected year (the year to display) and the
                # total # of years
                operating_years_by_adm = len(adm_values.columns)

                # if number of available years exceeds year_limit, drop excess columns (years)
                if operating_years_by_adm > max_display_years:
                    adm_values = adm_values.drop(columns = adm_values.columns[: (operating_years_by_adm - max_display_years)],axis=1)

                # "excluded years" is a list of YYYY strings (all years more
                # recent than selected year) that can be used to filter data
                # that should not be displayed
                excluded_academic_years = current_academic_year - selected_year_numeric
                
                excluded_years = []
                
                for i in range(excluded_academic_years):
                    excluded_year = current_academic_year - i
                    excluded_years.append(str(excluded_year))
                
                # if the display year is less than current year
                # drop columns where year matches any years in "excluded years" list
                if excluded_years:
                    adm_values = adm_values.loc[
                        :, ~adm_values.columns.str.contains("|".join(excluded_years))
                    ]

            # strip any (Q#) suffix
            adm_values.columns = adm_values.columns.str[:4]

            # turn single row dataframe into two lists (column headers and data)
            adm_data=adm_values.iloc[0].tolist()
            years=adm_values.columns.tolist()

            # create chart
            adm_fig = px.line(
                x=years,
                y=adm_data,
                markers=True,
                color_discrete_sequence=linecolor,
            )
            adm_fig.update_traces(mode="markers+lines", hovertemplate=None)
            adm_fig["data"][0]["showlegend"]=True
            adm_fig["data"][0]["name"]="ADM Average"
            adm_fig.update_yaxes(title="", showgrid=True, gridcolor="#b0c4de")
            adm_fig.update_xaxes(ticks="outside", tickcolor="#b0c4de", title="")

            adm_fig.update_layout(
                margin=dict(l=40, r=40, t=40, b=40),
                font = dict(
                    family="Jost, sans-serif",
                    color="#6783a9",
                    size=12
                    ),
                hovermode="x unified",
                height=400,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )

    return (
        update_table, enroll_title, enroll_table, adm_fig, ethnicity_title, ethnicity_fig, subgroup_title,
        subgroup_fig, main_container, empty_container, no_data_to_display
    )

layout = html.Div(
        [
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
                            html.Div(id="update-table", children=[]),
                            html.Div(
                                [                                
                                    html.Div(
                                        [
                                            html.Label(id="enroll-title", className = "header_label"),
                                            html.Div(id="enroll-table")
                                        ],
                                        className="pretty_container_left six columns",
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Average Daily Membership History", className = "header_label"),
                                            dcc.Graph(id="adm-fig", figure = loading_fig(),config={"displayModeBar": False})
                                        ],
                                        className = "pretty_container six columns"
                                    ),
                                ],
                                className="bare_container twelve columns",
                            ),                  
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label(id="subgroup-title", className = "header_label"),
                                            dcc.Graph(id="subgroup-fig", figure = loading_fig(),config={"displayModeBar": False})
                                        ],
                                        className = "pretty_container six columns"
                                    ),
                                    html.Div(
                                        [
                                            html.Label(id="ethnicity-title", className = "header_label"),
                                            dcc.Graph(id="ethnicity-fig", figure = loading_fig(),config={"displayModeBar": False})
                                        ],
                                        className = "pretty_container six columns"
                                    ),
                                ],
                                className="bare_container_center twelve columns",
                            ),
                        ],
                        id = "about-main-container",
                    )
                ],
            ),
            html.Div(
                [
                    html.Div(id="about-no-data"),
                ],
                id = "about-empty-container",
            ),
        ],
        id="mainContainer"
    )