#######################################
# ICSB Dashboard - Charting Functions #
#######################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.13
# date:     01/01/24

from dash import html, dcc
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .calculations import check_for_insufficient_n_size, check_for_no_data
from .string_helpers import customwrap
from .load_data import get_school_index

from typing import Tuple

# Colors
# https://codepen.io/ctf0/pen/BwLezW

color = [
    "#7b6888",
    "#df8f2d",
    "#a8b462",
    "#ebbb81",
    "#74a2d7",
    "#d4773f",
    "#83941f",
    "#f0c33b",
    "#bc986a",
    "#96b8db",
]


def loading_fig() -> dict:
    """
    Creates a blank fig with no title and 'Loading . . .' string only

    Returns:
        fig (dict): plotly figure dict
    """

    fig = {
        "layout": {
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "annotations": [
                {
                    "text": "Loading . . .",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 16,
                        "color": "#6783a9",
                        "family": "Inter, sans-serif",
                    },
                }
            ],
        }
    }

    return fig


def no_data_fig_blank() -> dict:
    """
    Creates a blank fig with no label

    Returns:
        fig (dict): plotly figure dict
    """
    fig = go.Figure()

    fig.update_layout(
        height=400,
        xaxis={"visible": False, "fixedrange": True},
        yaxis={"visible": False, "fixedrange": True},
        annotations=[
            {
                "text": "No Data to Display.",
                "align": "center",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16, "color": "#6783a9", "family": "Inter, sans-serif"},
            }
        ],
        dragmode=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def no_data_fig_label(
    label: str = "No Data to Display.", height: int = 400, table_type: str = "ugly"
) -> list:
    """
    Creates a blank fig with with a label and default height. ugly has no container, pretty wraps table
    in a pretty_container.

    Args:
        label (str, optional): figure label. Defaults to 'No Data to Display'.
        height (int, optional): figure height. Defaults to 400.
        type (str, optional): either "ugly" or "pretty"

    Returns:
        fig_layout (list): a dash html.Div with an html.Label object and dcc.Graph plotly figure dict
    """

    fig = go.Figure()

    fig.update_layout(
        height=height,
        xaxis={"visible": False, "fixedrange": True},
        yaxis={"visible": False, "fixedrange": True},
        annotations=[
            {
                "text": "No Data to Display.",
                "align": "center",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {
                    "size": 16,
                    "color": "#6783a9",
                    "family": "Inter, sans-serif",
                },
            }
        ],
        dragmode=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    if table_type == "pretty":
        fig_layout = [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(label, className="label__header"),
                                    dcc.Graph(figure=fig),
                                ],
                                className="pretty-container ten columns",
                            )
                        ],
                        className="bare-container--flex--center twelve columns",
                    )
                ],
                className="row",
            )
        ]

    else:
        fig_layout = [
            html.Div(
                [
                    html.Label(label, className="label__header"),
                    dcc.Graph(figure=fig),
                ]
            )
        ]

    return fig_layout


def make_stacked_bar(values: pd.DataFrame, label: str) -> list:
    """
    Create a layout with a 100% stacked bar chart showing proficiency percentages for
    all academic categories

    Args:
        values (pd.DataFrame): a dataframe with categories, proficiency categories, and proficiency percentages
        label (str): title of the figure

    Returns:
        list: a plotly dash html layout in the form of a list containing a string and a stacked bar chart figure (px.bar)
    """

    data = values.copy()
    stacked_color = ["#df8f2d", "#ebbb81", "#96b8db", "#74a2d7"]

    # In order to get the total_tested value into hovertemplate
    # without displaying it on the chart, we need to pull the
    # Total Tested values out of the dataframe and into a new
    # column.
    total_tested = data[data["Proficiency"].str.contains("Total Tested")]

    # Merge the total tested values with the existing dataframe
    # This adds 'percentage_x' and 'percentage_y' columns.
    # 'percentage_y' is equal to the Total Tested Values
    data = pd.merge(
        data, total_tested[["Category", "Percentage"]], on=["Category"], how="left"
    )

    # rename the columns (percentage_x to Percentage & percentage_y to Total Tested)
    data.columns = ["Category", "Percentage", "Proficiency", "Total Tested"]

    # drop the Total Tested Rows
    data = data[data["Proficiency"].str.contains("Total Tested") == False]

    # Remove subject substring ('ELA' or 'Math') from Proficiency column
    data["Proficiency"] = data["Proficiency"].str.split().str[1:].str.join(" ")

    fig = px.bar(
        data,
        x=data["Percentage"],
        y=data["Category"].map(customwrap),
        color=data["Proficiency"],
        barmode="stack",
        text=[f"{i}%" for i in data["Percentage"]],
        orientation="h",
        color_discrete_sequence=stacked_color,
        height=300,
        # custom_data = ["Total Tested"],   # Use this to add info to each trace
    )

    # the uniformtext_minsize and uniformtext_mode settings hide bar chart
    # text (Percentage) if the size of the chart causes the text of the font
    # to decrease below 8px. The text is positioned 'inside' the bar due to
    # the 'textposition' variable

    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=0),
        font_family="Inter, sans-serif",
        font_color="steelblue",
        font_size=9,
        bargroupgap=0,
        showlegend=False,
        plot_bgcolor="white",
        hovermode="y unified",
        yaxis=dict(autorange="reversed"),
        uniformtext_minsize=9,
        uniformtext_mode="hide",
    )

    # TODO: remove hover 'title' (currently the subcategory) and, if possible, replace with: 'Total Tested: {z}'
    # https://stackoverflow.com/questions/59057881/how-to-customize-hover-template-on-with-what-information-to-show
    # fig.update_layout(hovermode='x unified')

    fig.update_traces(
        textfont_size=9,
        insidetextanchor="middle",
        textposition="inside",
        marker_line=dict(width=0),
        hovertemplate="%{text}",
        # hovertemplate="%{text} (n-size: %{customdata[0]})",  # adds n-size (Total Tested) info to each trace.
        hoverinfo="none",
    )

    fig.update_xaxes(title="", showticklabels=False)

    # ticksuffix increases the space between the end of the tick label and the chart
    fig.update_yaxes(title="", ticksuffix="  ")

    fig_layout = [
        html.Div(
            [
                html.Label(label, className="hollow-label__header"),
                dcc.Graph(
                    figure=fig,
                    config={
                        "displayModeBar": False,
                        "showAxisDragHandles": False,
                        "showAxisRangeEntryBoxes": False,
                        "scrollZoom": False,
                    },
                ),
            ]
        )
    ]

    return fig_layout


# TODO: Merge this and make_single_line_chart ?


def make_multi_line_chart(values: pd.DataFrame, label: str) -> Tuple[dict, list]:
    """
    Creates a dash html.Div layout with a label, a basic line (scatter) plot (px.line), and a
    series of strings (if applicable) detailing missing data.

    Args:
        values (pd.DataFrame): a dataframe with proficiency categories for each year
        label (str): title of the figure

    Returns:
        fig_layout (list): a plotly dash html layout in the form of a list containing a string, a px.line figure,
        and another string(s) if certain conditions are met.
    """

    data = values.copy()

    school_cols = [i for i in data.columns if i not in ["Year"]]

    if (len(school_cols)) > 0 and len(data.index) > 0:
        data, no_data_string = check_for_no_data(data)

        nsize_string = check_for_insufficient_n_size(data)

        for school in school_cols:
            data[school] = pd.to_numeric(data[school], errors="coerce")

        data.sort_values("Year", inplace=True)

        # One last check, if there is only one year of data being displayed, we need to drop
        # all columns with only NaN- otherwise the traces will be displayed on the chart
        # even though they are listed as having no data to display - afterwards we need
        # to reset the cols variable to make sure it matches the changed df
        if len(data.index) == 1:
            data = data.dropna(axis=1, how="all")
            school_cols = [i for i in data.columns if i not in ["Year"]]

        data = data.reset_index(drop=True)

        # assign colors for each comparison school
        trace_color = {school_cols[i]: color[i] for i in range(len(school_cols))}

        # If the initial df has data, but after dropping all no data rows is then
        # empty, we return an empty layout
        if data.empty:
            fig = no_data_fig_blank()
            fig_layout = [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(label, className="label__header"),
                                dcc.Graph(figure=fig, config={"displayModeBar": False}),
                            ],
                        ),
                    ]
                )
            ]

        else:
            fig = px.line(
                data,
                x="Year",
                y=school_cols,
                markers=True,
                color_discrete_sequence=color,
            )

            fig.update_traces(hovertemplate=None)  # type: ignore
            fig.update_layout(  # type: ignore
                hoverlabel=dict(
                    namelength=-1,
                ),
                margin=dict(l=40, r=40, t=10, b=0),
                title_x=0.5,
                font=dict(family="Inter, sans-serif", color="steelblue", size=12),
                plot_bgcolor="white",
                xaxis=dict(
                    title="",
                    type="date",
                    tickvals=data["Year"],
                    tickformat="%Y",
                    mirror=True,
                    showline=True,
                    linecolor="#b0c4de",
                    linewidth=0.5,
                    gridwidth=0.5,
                    showgrid=True,
                    gridcolor="#b0c4de",
                    zeroline=False,
                ),
                showlegend=False,
                # legend=dict(
                #     orientation="v", yanchor="bottom", y=0.5, xanchor="right", x=-0.05
                # ),
                hovermode="x",
                height=400,
                legend_title="",
            )

            data["Year"] = data["Year"].astype(str)
            data_max = data.max(numeric_only=True).max()
            range_vals = [0, data_max + 0.05]

            fig.update_yaxes(  # type: ignore
                title="",
                mirror=True,
                showline=True,
                linecolor="#b0c4de",
                linewidth=0.5,
                gridwidth=0.5,
                showgrid=True,
                gridcolor="#b0c4de",
                zeroline=False,
                range=range_vals,
                dtick=0.2,
                tickformat=",.0%",
            )

            if nsize_string and no_data_string:
                fig_layout = [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(label, className="label__header"),
                                    dcc.Graph(
                                        figure=fig, config={"displayModeBar": False}
                                    ),
                                ],
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.P(
                                                children=[
                                                    html.Span(
                                                        "Years with insufficient or no data:",
                                                        className="msg-string__label",
                                                    ),
                                                    html.Span(
                                                        no_data_string,
                                                        className="nodata-string",
                                                    ),
                                                ],
                                            ),
                                            html.P(
                                                children=[
                                                    html.Span(
                                                        "Insufficient n-size:",
                                                        className="msg-string__label",
                                                    ),
                                                    html.Span(
                                                        nsize_string,
                                                        className="nsize-string",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="container--close--noborder twelve columns",
                                    )
                                ],
                                className="row",
                            ),
                        ]
                    )
                ]

            elif nsize_string and not no_data_string:
                fig_layout = [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(label, className="label__header"),
                                    dcc.Graph(
                                        figure=fig, config={"displayModeBar": False}
                                    ),
                                ],
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.P(
                                                children=[
                                                    html.Span(
                                                        "Insufficient n-size:",
                                                        className="msg-string__label",
                                                    ),
                                                    html.Span(
                                                        nsize_string,
                                                        className="nsize-string",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="container--close--noborder twelve columns",
                                    )
                                ],
                                className="row",
                            ),
                        ]
                    )
                ]

            elif no_data_string and not nsize_string:
                fig_layout = [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label(label, className="label__header"),
                                    dcc.Graph(
                                        figure=fig, config={"displayModeBar": False}
                                    ),
                                ],
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.P(
                                                children=[
                                                    html.Span(
                                                        "Years with insufficient or no data:",
                                                        className="msg-string__label",
                                                    ),
                                                    html.Span(
                                                        no_data_string,
                                                        className="nodata-string",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="container--close--noborder twelve columns",
                                    )
                                ],
                                className="row",
                            ),
                        ]
                    )
                ]

            else:
                fig_layout = [
                    html.Div(
                        [
                            html.Label(label, className="label__header"),
                            dcc.Graph(figure=fig, config={"displayModeBar": False}),
                        ],
                    )
                ]
    else:
        fig = no_data_fig_blank()

        fig_layout = [
            html.Div(
                [
                    html.Div(
                        [
                            html.Label(label, className="label__header"),
                            dcc.Graph(figure=fig, config={"displayModeBar": False}),
                        ],
                    ),
                ]
            )
        ]

    return trace_color, fig_layout


def make_line_chart(values: pd.DataFrame) -> list:
    """
    Creates a dash html.Div layout with a label, a basic line (scatter) plot (px.line), and a
    series of strings (if applicable) detailing missing data.

    Args:
        values (pd.DataFrame): a dataframe with proficiency categories for each year
        label (str): title of the figure

    Returns:
        fig_layout (list): a plotly dash html layout in the form of a list containing a string, a px.line figure,
        and another string(s) if certain conditions are met.
    """

    data = values.copy()

    data.columns = data.columns.str.split("|").str[0]

    if "IREAD Proficiency (Grade 3)" in data.columns:
        data = data.rename(columns={"IREAD Proficiency (Grade 3)": "IREAD"})

    cols = [i for i in data.columns if i not in ["School Name", "Year"]]

    if (len(cols)) > 0:
        # NOTE: the "insufficient n-size" and "no data" information is usually displayed
        # below the fig in the layout. However, given the size of the figs, it makes them
        # way too cluttered. So it is currently removed. Would prefer to somehow add this
        # to the trace (x-unified) hover, but it doesn't currently seem to be possible.
        # https://community.plotly.com/t/customizing-text-on-x-unified-hovering/39440/19

        data, no_data_string = check_for_no_data(data)
        # nsize_string = check_for_insufficient_n_size(data)

        # first check, if dataframe has more than one column, but not data
        # to display ("",NaN, or "***"), we catch it here
        if not data.empty:

            for col in cols:
                data[col] = pd.to_numeric(data[col], errors="coerce")

            data.sort_values("Year", inplace=True)

            # One last check, if there is only one year of data being displayed, we need to drop
            # all columns with only NaN- otherwise the traces will be displayed on the chart
            # even though they are listed as having no data to display - afterwards we need
            # to reset the cols variable to make sure it matches the changed df
            # if len(data.index) == 1:
            #     data = data.dropna(axis=1, how="all")
            #     cols = [i for i in data.columns if i not in ["School Name", "Year"]]

            data = data.dropna(axis=1, how="all")
            cols = [i for i in data.columns if i not in ["School Name", "Year"]]

            data = data.reset_index(drop=True)

            # Used below to set tick ranges

            data_max = data.drop("Year", axis=1).copy()
            data_max = data_max.max(numeric_only=True).max()

            # If data_max is > 1 then it is WIDA data (all other data are decimals)
            if data_max > 1:
                # make sure Year is a str and replace all negative numbers with 0
                data[data < 0] = 0
                data["Year"] = data["Year"].astype(str)

        # If the initial df has data, but after dropping all no data rows is then
        # empty, we return an empty layout
        if data.empty:
            fig = no_data_fig_blank()
            fig_layout = [
                html.Div(
                    [
                        html.Div(
                            [dcc.Graph(figure=fig, config={"displayModeBar": False})],
                        ),
                    ]
                )
            ]

        else:
            fig = px.line(
                data,
                x="Year",
                y=cols,
                markers=True,
                color_discrete_sequence=color,
            )

            # Set the range based on data_max (highest single value). IREAD is set to 100% regardless.
            # At higher ranges, the values compress together and are hard to read.
            if "IREAD Proficiency (Grade 3 only)" in data.columns:
                range_vals = [0, 1]  # type: list[float]
                tick_format = ",.0%"
                y_value = -0.4
                d_tick = 0.2

            # WIDA is only data where the max will be > 1
            elif data_max > 1:
                range_vals = [0, 5]
                tick_format = ".1f"
                y_value = -0.2
                d_tick = 1

            else:
                # legend shenanigans - adjust location based on columns
                if data.columns.str.contains("Grade").any():
                    y_value = -0.5
                elif data.columns.str.contains("Black").any():
                    y_value = -0.4
                elif data.columns.str.contains("Free").any():
                    y_value = -0.7
                else:
                    y_value = -0.4

                range_vals = [0, data_max + 0.05]
                tick_format = ",.0%"
                d_tick = 0.2

            # use this template if using x-unified
            # fig.update_traces(hovertemplate= 'Year=%{x}<br>value=%{y}<br>%{customdata}<extra></extra>''')

            fig.update_traces(hovertemplate=None)  # type: ignore
            fig.update_layout(  # type: ignore
                hoverlabel=dict(
                    namelength=-1,
                ),
                margin=dict(l=40, r=40, t=40, b=0),
                title_x=0.5,
                font=dict(family="Inter, sans-serif", color="steelblue", size=12),
                plot_bgcolor="white",
                xaxis=dict(
                    title="",
                    # next four values gives evenly spaced axis ticks from left edge to right edge.
                    autorange=False,
                    range=[0, len(data["Year"]) - 1],
                    tick0=0,
                    dtick=1,
                    tickvals=data["Year"],
                    tickformat=".4",  # "%Y",
                    mirror=True,
                    showline=True,
                    linecolor="#b0c4de",
                    linewidth=0.5,
                    gridwidth=0.5,
                    showgrid=True,
                    gridcolor="#b0c4de",
                    zeroline=False,
                ),
                legend=dict(
                    orientation="h", yanchor="bottom", y=y_value, xanchor="left", x=0.01
                ),
                hovermode="x",  # unified',
                height=400,
                legend_title="",
            )

            fig.update_yaxes(  # type: ignore
                title="",
                mirror=True,
                showline=True,
                linecolor="#b0c4de",
                linewidth=0.5,
                gridwidth=0.5,
                showgrid=True,
                gridcolor="#b0c4de",
                zeroline=False,
                range=range_vals,
                dtick=d_tick,
                tickformat=tick_format,
            )

            if no_data_string:
                fig_layout = [
                    html.Div(
                        [
                            html.Div(
                                [
                                    dcc.Graph(
                                        figure=fig, config={"displayModeBar": False}
                                    )
                                ],
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.P(
                                                children=[
                                                    html.Span(
                                                        "Years with insufficient or no data:",
                                                        className="msg-string__label",
                                                    ),
                                                    html.Span(
                                                        no_data_string,
                                                        className="nodata-string",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="container--close--noborder twelve columns",
                                    )
                                ],
                                className="row",
                            ),
                        ]
                    )
                ]

            else:
                fig_layout = [
                    html.Div(
                        [dcc.Graph(figure=fig, config={"displayModeBar": False})],
                    )
                ]
    else:
        fig = no_data_fig_blank()

        fig_layout = [
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(figure=fig, config={"displayModeBar": False})],
                    ),
                ]
            )
        ]

    return fig_layout


def make_growth_chart(
    data_me: pd.DataFrame, data_162: pd.DataFrame, label: str
) -> list:
    """
    Creates a dash html.Div layout with a label, and a multi-line (scatter) plot (px.line) representing
    two discrete dataframes in solid and dotted lines

    Args:
        data_162 (pd.DataFrame): growth data representing students enrolled at a school for at least 162 days
        data_me (pd.DataFrame): growth data for students enrolled at a school for a majority of days
        label (str): title of the figure

    Returns:
        fig_layout (list): a plotly dash html layout in the form of a list containing a label and a px.line figure
    """

    data_me.columns = data_me.columns.map(lambda x: x.split("|")[0])
    data_162.columns = data_162.columns.map(lambda x: x.split("|")[0])

    fig = make_subplots()

    if "Growth" in label:
        ytick = ".0%"
        ytitle = "Adequate Growth %"
        hover = ".2%"
    elif "SGP" in label:
        ytick = ".1f"
        ytitle = "Median SGP"
        hover = ".1f"

    for i, col in enumerate(data_me.columns):
        fig.add_trace(
            go.Scatter(
                x=data_me.index,
                y=data_me[col],
                name=col,
                meta=[
                    col
                ],  # wtf is this?? [https://community.plotly.com/t/hovertemplate-does-not-show-name-property/36139]
                mode="markers+lines",
                marker=dict(color=color[i], symbol="square"),
                line={"dash": "solid"},
                customdata=[
                    f"{i:.2%}" if not np.isnan(i) else "None" for i in data_162[col]
                ]
                if "Growth" in label
                else [f"{i:.1f}" for i in data_162[col]],
                text=[f"{i}" for i in data_me.columns],
                # NOTE: the legendgroup variable separates each dataframe into a separate
                # legend group, which is great because it allows you to turn on and off each
                # group. However, it looks bad because it does not currently allow you to display
                # the legends horizontally. It is a matter of preference
                # legendgroup = '1',
                # legendgrouptitle_text="Majority Enrolled"
            ),
            secondary_y=False,
        )

        # NOTE: Uncomment to add scatter traces for 162-Day data (it gets cluttered fast)
        # fig.add_trace(
        #     go.Scatter(
        #         x=data_162.index,
        #         y=data_162[col],
        #         mode='markers+lines',
        #         line={'dash': 'dash'},
        #         marker=dict(color=color[i], symbol = 'diamond'),
        #         name=col,
        #         legendgroup = '2',
        #         legendgrouptitle_text="162 Days"
        #     ),
        #     secondary_y=False,
        # )

    # TODO: Rework this to use a regular px.line so that we can adjust the ticks
    # TODO: the same way we do in make_line_chart (that is edge to edge)
    xaxis_data = pd.DataFrame()
    xaxis_data["Year"] = data_me.index.astype(str)

    # Add figure title
    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=0),
        title_x=0.5,
        font=dict(family="Inter, sans-serif", color="steelblue", size=10),
        plot_bgcolor="white",
        xaxis=dict(
            title="",
            type="date",
            # autorange=False,
            # range=[0, len(xaxis_data['Year'])-1],
            # tick0=0,
            # dtick=1,
            # tickvals=xaxis_data['Year'],
            tickvals=data_me.index,
            tickformat="%Y",
            mirror=True,  #
            showline=True,
            linecolor="#b0c4de",
            linewidth=0.5,
            gridwidth=0.5,
            showgrid=True,
            gridcolor="#b0c4de",
            zeroline=False,
        ),
        yaxis=dict(
            title="",
            tickformat=ytick,
            showline=True,
            linecolor="#b0c4de",
            linewidth=0.5,
            gridwidth=0.5,
            showgrid=True,
            gridcolor="#b0c4de",
            zeroline=False,
            hoverformat=hover,
        ),
        legend=dict(orientation="h"),
        hovermode="x unified",
        height=300,
    )
    fig.update_traces(
        hovertemplate="<br>".join(
            [
                s.replace(" ", "&nbsp;")
                for s in [
                    "%{meta} (Majority Enrolled): <b>%{y}</b> (162 Days: %{customdata})<br><extra></extra>",
                ]
            ]
        )
    )

    # NOTE: annotation is used as a master legend to identify 162-day vs 162-ME scatter lines
    # diamond - &#9670;	&#x25C6;
    # square - &#9632;	&#x25A0;
    # fig.add_annotation(
    #     text="Students Enrolled For: <b>&#9670;: 162 Days &#9632;: Majority Enrolled</b>",
    #     align="left",
    #     showarrow=False,
    #     xref="paper",
    #     yref="paper",
    #     font=dict(color="steelblue", size = 11),
    #     bgcolor="rgba(0,0,0,0)",
    #     y=1.15,
    #     x=.5,
    #     xanchor="center",
    # )

    fig.update_yaxes(title_text=ytitle, secondary_y=False)

    fig_layout = [
        html.Div(
            [dcc.Graph(figure=fig, config={"displayModeBar": False})],
        )
    ]

    return fig_layout


def make_bar_chart(
    values: pd.DataFrame, category: str, school_name: str, label: str
) -> Tuple[dict, list]:
    """
    Creates a dash html.Div layout with a label and a simple bar chart (px.bar)

    Args:
        values (pd.DataFrame): a dataframe with a list of schools and proficiency values
            for a given category
        category (str): the category being compared
        school_name (str): the name of the selected school
        label (str): the title of the figure

    Returns:
        fig_layout (list): a plotly dash html layout in the form of a list containing a string and px.bar figure
    """

    data = values.copy()

    # NOTE: Unless the entire page is blank, e.g., no data at all, the
    # dataframe for this chart should never be blank due to error
    # handling in the calling script. However, we know that 'should never'
    # is code for 'almost with certainty' so we test here too.

    # the dataframe should always have at least 4 columns ('School Name',
    # 'Low Grade', 'High Grade' & one data column)
    if (len(data.columns)) > 3:
        schools = data["School Name"].tolist()

        # assign colors for each comparison school - this data is returned
        # from the function
        trace_color = {schools[i]: color[i] for i in range(len(schools))}

        # use specific color for selected school
        for key, value in trace_color.items():
            if key == school_name:
                trace_color[key] = "#7b6888"  # "#0a66c2"

        # Uncomment this and below to display distance from selected school
        # data['Distance'] = pd.Series(['{:,.2f}'.format(val) for val in data['Distance']], index = data.index)

        fig = px.bar(
            data,
            x="School Name",
            y=category,
            color_discrete_map=trace_color,
            color="School Name",
            # custom_data=["Low Grade", "High Grade"],  # ,'Distance']
            text_auto=True,
        )

        fig.update_yaxes(
            range=[0, 1],
            dtick=0.2,
            tickformat=",.0%",
            title="",
            showgrid=True,
            gridcolor="#b0c4de",
        )
        fig.update_xaxes(
            type="category",
            showticklabels=False,
            title="",
            showline=True,
            linewidth=1,
            linecolor="#b0c4de",
        )

        fig.update_layout(
            title_x=0.5,
            margin=dict(l=40, r=40, t=40, b=60),
            font=dict(family="Inter, sans-serif", color="steelblue", size=11),
            # legend=dict(orientation="h", title="", xanchor="center", x=0.45),
            showlegend=False,
            height=350,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            hoverlabel=dict(
                bgcolor="white",
                font_color="steelblue",
                font_size=11,
                font_family="Inter, sans-serif",
                align="left",
            ),
        )

        fig.update_traces(
            textposition="outside",
            hovertemplate="<b>%{x}</b><br><b>Proficiency: </b>%{y}<br><extra></extra>",
            # hovertemplate="<b>%{x}</b> (Grades %{customdata[0]} - %{customdata[1]})<br><b>Proficiency: </b>%{y}<br><extra></extra>",
        )

    else:
        fig = no_data_fig_blank()

    fig_layout = [
        html.Div(
            [
                html.Label(label, className="label__header"),
                dcc.Graph(figure=fig, config={"displayModeBar": False}),
            ]
        )
    ]

    return trace_color, fig_layout


def make_group_bar_chart(
    values: pd.DataFrame, school_id: str, label: str
) -> Tuple[dict, list]:
    """
    Creates a layout containing a label and a grouped bar chart (px.bar)

    Args:
        values (pd.DataFrame): a dataframe with a list of schools and proficiency values
            for a given subject and category group (e.g., Math by Ethnicity)
        school_name (str): the name of the selected school
        label (str): the title of the figure

    Returns:
        fig_layout (list): a plotly dash html layout in the form of a list containing a string and px.bar figure
    """
    data = values.copy()

    selected_school = get_school_index(str(school_id))
    school_name = selected_school["School Name"].values[0]

    if "Low Grade" in data:
        data = data.drop(["Low Grade", "High Grade"], axis=1)

    data = data.drop("School ID", axis=1)

    # reset index
    data.reset_index(drop=True, inplace=True)

    # remove trailing string
    # "School Total" is for SAT and includes all three subjects - so we dont want to split
    if data.columns.str.contains("School Total").any() == True:
        # keep everything between | and "Benchmark %"
        data.columns = data.columns.str.replace("Benchmark %", "")
        data.columns = data.columns.str.replace("School Total\|", "", regex=True)

    else:
        data.columns = data.columns.str.split("|").str[0]

    # replace any '***' values (insufficient n-size) with NaN
    data = data.replace("***", np.nan)

    # force non-string columns to numeric
    cols = [i for i in data.columns if i not in ["School Name", "Year"]]

    for col in cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    categories = data.columns.tolist()
    categories.remove("School Name")
    schools = data["School Name"].tolist()

    # melt dataframe from 'wide' format to 'long' format (plotly express
    # can handle either, but long format makes hovertemplate easier - trust me)
    data_set = pd.melt(
        data,
        id_vars="School Name",
        value_vars=categories,
        var_name="Categories",
        ignore_index=False,
    )

    data_set.reset_index(drop=True, inplace=True)

    # Create text values for display.
    # NOTE: This can be 99.9% done by setting 'text_auto=True'
    # in 'fig' without setting specific 'text' values; EXCEPT, it does not hide the 'NaN%' text
    # that is displayed for ''. So this code converts the series to a string in the proper format
    # and replaces nan with ''
    text_values = data_set["value"].map("{:.0%}".format)
    text_values = text_values.str.replace("nan%", "")

    # assign colors for each comparison
    trace_color = {schools[i]: color[i] for i in range(len(schools))}

    # replace color for selected school
    for key, value in trace_color.items():
        if key == school_name:
            trace_color[key] = "#0a66c2"

    fig = px.bar(
        data_frame=data_set,
        x="Categories",
        y="value",
        color="School Name",
        color_discrete_map=trace_color,
        orientation="v",
        barmode="group",
        custom_data=["School Name"],
        text=text_values,
    )

    fig.update_yaxes(
        range=[0, 1],
        dtick=0.2,
        tickformat=",.0%",
        title="",
        showgrid=True,
        gridcolor="#b0c4de",
    )

    fig.update_xaxes(title="", showline=True, linewidth=0.5, linecolor="#b0c4de")

    fig.update_layout(
        title_x=0.5,
        margin=dict(l=40, r=40, t=40, b=10),
        font=dict(family="Inter, sans-serif", color="steelblue", size=11),
        bargap=0.15,
        bargroupgap=0.1,
        height=400,
        legend_title="",
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor="white",
            font_color="steelblue",
            font_size=11,
            font_family="Inter, sans-serif",
            align="left",
        ),
        # hoverlabel_align = 'left'
    )

    fig.update_traces(
        hovertemplate="<br>".join(
            [
                s.replace(" ", "&nbsp;")
                for s in [
                    "<b>%{customdata[0]}</b>",
                    "<b>Proficiency: </b>%{y}<br><extra></extra>",
                ]
            ]
        )
    )

    # NOTE: Some dict manipulation to address two issues: 1) display values between 0 and 4% as text
    # outside of the trace, and all other values inside; and 2) display a 'marker' for '0' values.
    # Both have relatively simple solutions for single bar charts- neither of which work for
    # grouped bar charts, because both solutions end up applying 'per group' of bars rather than
    # to the individual bars in the group. See, e.g.:
    # https://stackoverflow.com/questions/70658955/how-do-i-display-bar-plot-for-values-that-are-zero-in-plotly
    # https://stackoverflow.com/questions/73905861/fully-display-the-amount-in-horizontal-bar-chart

    #  This uses a loop (ick) to directly manipulate each fig data object.

    for i in range(0, len(data_set["School Name"].unique())):
        marker_array = []
        position_array = []

        for j in range(0, len(fig["data"][i]["y"])):
            # # track location of school in index (to add border)
            # if fig['data'][i]['name'] == school_name:
            #     loc = i

            if fig["data"][i]["y"][j] < 0.05:
                position_array.append("outside")
            else:
                position_array.append("inside")

            if fig["data"][i]["y"][j] == 0:
                marker_array.append("#999999")
            else:
                marker_array.append(fig["data"][i]["marker"]["color"])

        fig["data"][i]["marker"]["line"]["color"] = marker_array
        fig["data"][i]["marker"]["line"]["width"] = 2

        fig["data"][i]["textposition"] = position_array

    # NOTE: Uncomment to add border around selected school
    # having hard time making this look decent.
    # fig['data'][loc]['marker']['line']['color'] = 'grey'

    # NOTE: From testing, it appears that the legend marker uses the first item in the
    # marker_line_color array ([0]) as the border for the legend marker. So if the
    # marker_line_color is set to grey for a specific trace (e.g., the value of the trace
    # is '0'), that color is used for the legend marker. We do not want a grey border
    # around a legend marker. We fix this in stylesheet.css (See: .legendundefined))

    fig_layout = [
        html.Div(
            [
                html.Label(label, className="label__header"),
                dcc.Graph(figure=fig, config={"displayModeBar": False}),
            ]
        )
    ]

    return trace_color, fig_layout
