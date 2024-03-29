#####################################
# ICSB Dashboard - Academic Metrics #
#####################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     03/25/24

import dash
from dash import html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd

# import local functions
from .globals import (
    ethnicity,
    subgroup,
    grades_all
)

from .load_data import (
    get_school_index,
    get_academic_data
)

from .tables import (
    no_data_page,
    no_data_table,
    create_metric_table,
    create_proficiency_key
)

from .layouts import set_table_layout

from .string_helpers import convert_to_svg_circle

from .calculate_metrics import (
    calculate_high_school_metrics,
    calculate_adult_high_school_metrics,
    calculate_attendance_metrics,
    calculate_iread_metrics,
    calculate_values,
    calculate_metrics
)

from .calculations import conditional_fillna

dash.register_page(__name__, path="/academic_metrics", top_nav=True, order=9)


@callback(
    Output("table-container-11ab", "children"),
    Output("attendance-container", "style"),
    Output("table-container-11cd", "children"),
    Output("table-container-14ab", "children"),
    Output("table-container-14cd", "children"),
    Output("table-container-14ef", "children"),
    Output("table-container-14g", "children"),
    # Output("table-container-15abcd", "children"),
    Output("table-container-16ab", "children"),
    Output("table-container-16cd", "children"),
    Output("k8-metrics-container", "style"),
    Output("table-container-17ab", "children"),
    Output("table-container-17cd", "children"),
    Output("hs-metrics-container", "style"),
    Output("table-container-ahs-113", "children"),
    Output("table-container-ahs-1214", "children"),
    Output("ahs-metrics-container", "style"),
    Output("academic-metrics-main-container", "style"),
    Output("academic-metrics-empty-container", "style"),
    Output("academic-metrics-no-data", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
)
def update_academic_metrics(school: str, year: str):
    if not school:
        raise PreventUpdate

    # 2020 has no academic data
    string_year = year
    selected_year_string = "2019" if string_year == "2020" else string_year
    selected_year_numeric = int(selected_year_string)

    # default values (only empty container displayed)
    table_container_11ab = []
    table_container_11cd = []
    table_container_14ab = []
    table_container_14cd = []
    table_container_14ef = []
    table_container_14g = []
    # table_container_15abcd = []   # growth data (not yet implemented)
    table_container_16ab = []
    table_container_16cd = []
    attendance_container = {"display": "none"}
    k8_metrics_container = {"display": "none"}

    table_container_17ab = []
    table_container_17cd = []
    hs_metrics_container = {"display": "none"}

    ahs_table_container_113 = []
    ahs_table_container_1214 = []
    ahs_metrics_container = {"display": "none"}

    main_container = {"display": "none"}
    empty_container = {"display": "block"}

    no_data_to_display = no_data_page("No Data to Display.", "Academic Metrics")

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]
    selected_school_id = int(selected_school["School ID"].values[0])

    # K8 Academic Metrics (for K8 and K12 schools)
    if selected_school_type == "K8" or selected_school_type == "K12":
        list_of_schools = [school]
        if selected_school_type == "K12":
            school_type = "K8"
        else:
            school_type = selected_school_type
        
        metric_data = get_academic_data(list_of_schools, school_type, selected_year_numeric, "metrics")

        if len(metric_data.index) > 0:

            metric_data = metric_data.replace(
                {"^": "***"}
            )

            k8_metrics_container = {"display": "block"}
            main_container = {"display": "block"}
            empty_container = {"display": "none"}


            k8_year_values, k8_comparison_values = calculate_values(metric_data,selected_year_string)

# TODO: Do we need to Test for empty here?
            
            # Get Year over Year and Combined Metrics
            combined_years, combined_delta = calculate_metrics(k8_year_values, k8_comparison_values)

            category = ethnicity + subgroup

            metric_14a_data = combined_years[
                (combined_years["Category"].str.contains("|".join(grades_all)))
                & (combined_years["Category"].str.contains("ELA"))
            ]
            metric_14a_label = [
                "1.4.a Grade level proficiency on the state assessment in",
                html.Br(),
                html.U("English Language Arts"),
                " compared with the previous school year.",
            ]

            metric_14a_data = convert_to_svg_circle(metric_14a_data)
            table_14a = create_metric_table(metric_14a_label, metric_14a_data)

            metric_14b_data = combined_years[
                (combined_years["Category"].str.contains("|".join(grades_all)))
                & (combined_years["Category"].str.contains("Math"))
            ]
            metric_14b_label = [
                "1.4.b Grade level proficiency on the state assessment in",
                html.Br(),
                html.U("Math"),
                " compared with the previous school year.",
            ]

            metric_14b_data = convert_to_svg_circle(metric_14b_data)
            table_14b = create_metric_table(metric_14b_label, metric_14b_data)

            table_container_14ab = set_table_layout(
                table_14a, table_14b, combined_years.columns
            )

            metric_14c_data = combined_delta[
                (combined_delta["Category"].str.contains("|".join(grades_all)))
                & (combined_delta["Category"].str.contains("ELA"))
            ]
            metric_14c_label = [
                "1.4.c Grade level proficiency on the state assessment in",
                html.Br(),
                html.U("English Language Arts"),
                " compared with traditional school corporation.",
            ]

            metric_14c_data = convert_to_svg_circle(metric_14c_data)
            table_14c = create_metric_table(metric_14c_label, metric_14c_data)

            metric_14d_data = combined_delta[
                (combined_delta["Category"].str.contains("|".join(grades_all)))
                & (combined_delta["Category"].str.contains("Math"))
            ]
            metric_14d_label = [
                "1.4.d Grade level proficiency on the state assessment in",
                html.Br(),
                html.U("Math"),
                " compared with traditional school corporation.",
            ]

            metric_14d_data = convert_to_svg_circle(metric_14d_data)
            table_14d = create_metric_table(metric_14d_label, metric_14d_data)

            table_container_14cd = set_table_layout(
                table_14c, table_14d, combined_delta.columns
            )

            # Accountability Metrics 1.4.e & 1.4.f (Placeholder)
            all_cols = combined_years.columns.tolist()

            simple_cols = [x for x in all_cols if "School" in x or "N-Size" in x]
            simple_cols = ["Category"] + simple_cols

            year_proficiency_empty = pd.DataFrame(columns=simple_cols)

            year_proficiency_dict = {
                "Category": [
                    "1.4.e Two year student proficiency in ELA.",
                    "1.4.f Two year student proficiency in Math.",
                ]
            }
            year_proficiency = pd.DataFrame(year_proficiency_dict)

            metric_14ef_data = pd.concat(
                [year_proficiency_empty, year_proficiency], ignore_index=True
            )
            metric_14ef_data.reset_index()
            metric_14ef_data = conditional_fillna(metric_14ef_data)
            metric_14ef_label = [
                "Percentage of students enrolled for at least two school years achieving proficiency on the state assessment in English Language Arts (1.4.e) and Math (1.4.f)"
            ]
            table_14ef = create_metric_table(metric_14ef_label, metric_14ef_data)
            table_container_14ef = set_table_layout(
                table_14ef, table_14ef, metric_14ef_data.columns
            )

# TODO: IREAD NOT SHOWING 2019-2021 for 21sty C
            # iread_data - combined_delta has all IREAD data, but we
            # currently only use Total
            iread_data = combined_delta[
                combined_delta["Category"] == "Total|IREAD"
            ].copy()

            if len(iread_data.index) > 0:
                iread_data.loc[
                    iread_data["Category"] == "IREAD", "Category"
                ] = "IREAD Proficient %"

                iread_data = iread_data.reset_index(drop=True)

                iread_data = calculate_iread_metrics(iread_data)

                metric_14g_label = [
                    "1.4.g Percentage of students achieving proficiency on the IREAD-3 state assessment."
                ]
                iread_data = convert_to_svg_circle(iread_data)
                table_14g = create_metric_table(metric_14g_label, iread_data)
                table_container_14g = set_table_layout(
                    table_14g, table_14g, iread_data.columns
                )

            else:
                # create_metric_table requies label to be a list, while no_data_table wants a string
                empty_table_14g = no_data_table(
                    "No Data to Display.",
                    "1.4.g Percentage of students achieving proficiency on the IREAD-3 state assessment.",
                    "six"
                )
                table_container_14g = set_table_layout(
                    empty_table_14g, empty_table_14g, [""]
                )
            # Placeholders for Growth data metrics (Accountability Metrics 1.5.a, 1.5.b, 1.5.c, & 1.5.d)

            # growth_metrics_empty = pd.DataFrame(columns = simple_cols)
            # growth_metrics_dict = {
            #     "Category": ["1.5.a Percentage of students achieving “typical” or “high” growth on the state assessment in \
            #         English Language Arts according to Indiana\'s Growth Model",
            #     "1.5.b Percentage of students achieving “typical” or “high” growth on the state assessment in \
            #         Math according to Indiana\'s Growth Model",
            #     "1.5.c. Median Student Growth Percentile ('SGP') of students achieving 'adequate and sufficient growth' \
            #         on the state assessment in English Language Arts according to Indiana\'s Growth Model",
            #     "1.5.d. Median SGP of students achieving 'adequate and sufficient growth' on the state assessment \
            #         in Math according to Indiana\'s Growth Model",
            #         ]
            #     }
            # growth_metrics = pd.DataFrame(growth_metrics_dict)
            # metric_15abcd_data = pd.concat([growth_metrics_empty, growth_metrics], ignore_index = True)
            # metric_15abcd_data.reset_index()
            # metric_15abcd_data = conditional_fill(metric_15abcd_data)
            # metric_15abcd_label = "Accountability Metrics 1.5.a, 1.5.b, 1.5.c, & 1.5.d"
            # metric_15abcd_data = convert_to_svg_circle(metric_15abcd_data)
            # table_15abcd = create_metric_table(metric_15abcd_label, metric_15abcd_data)
            # table_container_15abcd = set_table_layout(table_15abcd, table_15abcd, metric_15abcd_data.columns)
            
            print(combined_delta)
            filename99 = ("combined_delta.csv")
            combined_delta.to_csv(filename99, index=False)

            metric_16a_data = combined_delta[
                (combined_delta["Category"].str.contains("|".join(category)))
                & (combined_delta["Category"].str.contains("ELA"))
            ]
            metric_16a_label = [
                "1.6.a Proficiency on the state assessment in ",
                html.U("English Language Arts"),
                html.Br(),
                "for each subgroup compared with traditional school corporation.",
            ]
            metric_16a_data = convert_to_svg_circle(metric_16a_data)
            table_16a = create_metric_table(metric_16a_label, metric_16a_data)

            metric_16b_data = combined_delta[
                (combined_delta["Category"].str.contains("|".join(category)))
                & (combined_delta["Category"].str.contains("Math"))
            ]
            metric_16b_label = [
                "1.6.b Proficiency on the state assessment in ",
                html.U("Math"),
                " for each",
                html.Br(),
                "subgroup compared with traditional school corporation.",
            ]
            metric_16b_data = convert_to_svg_circle(metric_16b_data)
            print(metric_16b_data)
            table_16b = create_metric_table(metric_16b_label, metric_16b_data)

            table_container_16ab = set_table_layout(
                table_16a, table_16b, combined_delta.columns
            )

            metric_16c_data = combined_years[
                (combined_years["Category"].str.contains("|".join(category)))
                & (combined_years["Category"].str.contains("ELA"))
            ]
            metric_16c_label = [
                "1.6.c The change in proficiency on the state assessment in",
                html.Br(),
                html.U("English Language Arts"),
                " for each subgroup compared with the previous school year.",
            ]
            metric_16c_data = convert_to_svg_circle(metric_16c_data)
            table_16c = create_metric_table(metric_16c_label, metric_16c_data)

            metric_16d_data = combined_years[
                (combined_years["Category"].str.contains("|".join(category)))
                & (combined_years["Category"].str.contains("Math"))
            ]
            metric_16d_label = [
                "1.6.d The change in proficiency on the state assessment in",
                html.Br(),
                html.U("Math"),
                " for each subgroup compared with the previous school year.",
            ]
            metric_16d_data = convert_to_svg_circle(metric_16d_data)
            table_16d = create_metric_table(metric_16d_label, metric_16d_data)

            table_container_16cd = set_table_layout(
                table_16c, table_16d, combined_years.columns
            )

    if (
        selected_school_type == "HS"
        or selected_school_type == "AHS"
        or selected_school_type == "K12"
        or (selected_school_id == 5874 and selected_year_numeric < 2021)
    ):

        if selected_school_type == "K12":
            selected_school_type = "HS"

        list_of_schools = [school]
        raw_metric_data = get_academic_data(list_of_schools, selected_school_type, selected_year_numeric, "metrics")

        if len(raw_metric_data.index) > 0:

        # TODO: At some point need to add the State AHS Calculation
        # weighted graduation calculation score (20%) and weighted ccr score (80%) - yr1
        # other years grad (40%) / ccr (60%)
        # GRAD Calc:
        # (1) the graduation to enrollment percentage of the school year(90% - max 100);
        #   denominator- the school's within-year-average number of students
        #   numerator of which is - the number of students who graduated during the school year
        #       multiplied by four (4)
        # (2) the graduation rate (10%):
        #   STEP ONE: Calculate the five (5) year graduation rate for the cohort
        #   immediately preceding the prior year cohort.
        #   STEP TWO: Subtract the four (4) year graduation rate for the cohort
        #   immediately preceding the prior year cohort from the number determined
        #   under STEP ONE.
        #   STEP THREE: Add the number determined under STEP TWO to the four (4) year
        #   graduation rate from the prior year cohort.

        # final grad calc score:

        # (1) the sum of the weighted percentages for graduation to enrollment and graduation rate;
        # multiplied by
        # (2) the graduation qualifying examination passing rate:
        #   equal either to 1 if the graduation qualifying examination passing rate is at
        #   least 90% or the actual percent passing if below 90%.

        # CCR
        # (1) the college and career achievement rate;
        #   the percentage of all graduates in the school year being
        #   assessed who accomplished any of the following:
        #       (1) Passed an AP exam with a score of 3, 4, or 5.
        #       (2) Passed an IB exam with a score of 4, 5, 6, or 7.
        #       (3) Earned three (3) college credits, defined as credits awarded by a
        #       regionally accredited postsecondary institution in a department approved
        #       liberal arts or career or technical education dual credit course verifiable
        #       by a transcript.
        #       (4) Obtained an industry certification.
        #       (5) Any other benchmarks approved by the board.
        # (2) the college and career readiness factor (100/.8); and
        # (3) one hundred (100).

            # Adult High School Metrics
            if selected_school_type == "AHS":
                ahs_metrics_container = {"display": "block"}
                main_container = {"display": "block"}
                empty_container = {"display": "none"}

                ahs_metric_data_113 = calculate_adult_high_school_metrics(raw_metric_data)

                ahs_metric_data_113["Category"] = (
                    ahs_metric_data_113["Metric"]
                    + " "
                    + ahs_metric_data_113["Category"]
                )

                ahs_metric_data_113 = ahs_metric_data_113.drop("Metric", axis=1)

                ahs_metric_label_113 = [
                    "Adult High School Accountability Metrics 1.1 & 1.3"
                ]
                ahs_metric_data_113 = convert_to_svg_circle(ahs_metric_data_113)
                ahs_table_113 = create_metric_table(
                    ahs_metric_label_113, ahs_metric_data_113
                )
                ahs_table_container_113 = set_table_layout(
                    ahs_table_113, ahs_table_113, ahs_metric_data_113.columns
                )

                # Create placeholders (Adult Accountability Metrics 1.2.a, 1.2.b, 1.4.a, & 1.4.b)
                all_cols = ahs_metric_data_113.columns.tolist()
                simple_cols = [x for x in all_cols if not x.endswith("+/-")]

                ahs_nocalc_empty = pd.DataFrame(columns=simple_cols)

                ahs_nocalc_dict = {
                    "Category": [
                        "1.2.a Students graduate from high school in 4 years.",
                        "1.2.b Students enrolled in grade 12 graduate within the school year being assessed.",
                    ]
                }
                ahs_no_calc = pd.DataFrame(ahs_nocalc_dict)

                ahs_metric_data_1214 = pd.concat(
                    [ahs_nocalc_empty, ahs_no_calc], ignore_index=True
                )
                ahs_metric_data_1214.reset_index()

                # fill only value columns with "No Data" (until we actually HAVE the data)
                empty_year_cols = [
                    col for col in ahs_metric_data_1214.columns if "Value" in col
                ]
                for col in empty_year_cols:
                    ahs_metric_data_1214[col] = "No Data"

                ahs_metric_label_1214 = [
                    "Adult Accountability Metrics 1.2.a & 1.2.b"
                ]
                ahs_metric_data_1214 = convert_to_svg_circle(ahs_metric_data_1214)
                ahs_table_1214 = create_metric_table(
                    ahs_metric_label_1214, ahs_metric_data_1214
                )
                ahs_table_container_1214 = set_table_layout(
                    ahs_table_1214, ahs_table_1214, ahs_metric_data_1214.columns
                )

            else:
                # NOTE: We do not currently use hs_year_over_year_values
                # for hs metrics
                hs_year_over_year_values, hs_comparison_values = calculate_values(raw_metric_data,selected_year_string)

                if not hs_comparison_values.empty:
                    hs_metrics_container = {"display": "block"}
                    main_container = {"display": "block"}
                    empty_container = {"display": "none"}

                    hs_metric_data = calculate_high_school_metrics(hs_comparison_values)

                    metric_17ab_label = [
                        "High School Accountability Metrics 1.7.a & 1.7.b"
                    ]
                    hs_metric_data = convert_to_svg_circle(
                        hs_metric_data
                    )
                    table_17ab = create_metric_table(
                        metric_17ab_label, hs_metric_data
                    )
                    table_container_17ab = set_table_layout(
                        table_17ab, table_17ab, hs_metric_data.columns
                    )

                    # Create placeholders (High School Accountability Metrics 1.7.c & 1.7.d)
                    all_cols = hs_metric_data.columns.tolist()

                    simple_cols = [
                        x
                        for x in all_cols
                        if (not x.endswith("+/-") and not x.endswith("Diff")) # Difference
                    ]

                    grad_metrics_empty = pd.DataFrame(columns=simple_cols)

                    grad_metrics_dict = {
                        "Category": [
                            "1.7.c The percentage of students entering Grade 12 at beginning of year who graduated",
                            # "1.7.d. The percentage of graduating students planning to pursue college or career."
                        ]
                    }
                    grad_metrics = pd.DataFrame(grad_metrics_dict)

                    metric_17cd_data = pd.concat(
                        [grad_metrics_empty, grad_metrics], ignore_index=True
                    )
                    metric_17cd_data.reset_index()

                    # fill only value columns with "No Data" (until we actually HAVE the data)
                    empty_year_cols = [
                        col for col in metric_17cd_data.columns if "%" in col
                    ]
                    for col in empty_year_cols:
                        metric_17cd_data[col] = "No Data"

                    metric_17cd_data = conditional_fillna(metric_17cd_data)

                    metric_17cd_label = [
                        "High School Accountability Metrics 1.7.c & 1.7.d"
                    ]
                    metric_17cd_data = convert_to_svg_circle(metric_17cd_data)
                    table_17cd = create_metric_table(
                        metric_17cd_label, metric_17cd_data
                    )
                    table_container_17cd = set_table_layout(
                        table_17cd, table_17cd, metric_17cd_data.columns
                    )

    # Attendance Data & Teacher Retention Rate (all schools have this data)
    metric_11ab_label = [
        "Student Attendance Rate (1.1.a) and Teacher Retention Rate (1.1.b) compared with traditional school corporation."
    ]

    # Re-enrollment Rates (Acountability Metrics 1.1.c & 1.1.d): Currently Placeholders
    metric_11cd_label = [
        "End of Year to Beginning of Year (1.1.c) and Year over Year (1.1.d) Student Re-Enrollment Rate."
    ]

    attendance_data = calculate_attendance_metrics(school, selected_school_type, selected_year_string)

    if len(attendance_data.index) > 0:
        attendance_container = {"display": "block"}

        # Create placeholders (Acountability Metric 1.1.b.)
        teacher_retention_rate = pd.DataFrame(
            {"Category": ["1.1.b Teacher Retention Rate"]}
        )

        metric_11ab_data = pd.merge(
            attendance_data, teacher_retention_rate, how="outer", on="Category"
        )

        metric_11ab_data = conditional_fillna(metric_11ab_data)

        metric_11ab_data = convert_to_svg_circle(metric_11ab_data)
        table_11ab = create_metric_table(metric_11ab_label, metric_11ab_data)
        table_container_11ab = set_table_layout(
            table_11ab, table_11ab, metric_11ab_data.columns
        )

        # Create placeholders (Acountability Metric 1.1.c.)
        student_retention_rate_dict = {
            "Category": [
                "1.1.c End of Year to Beginning of Year Re-Enrollment Rate",
                "1.1.d Year over Year Re-Enrollment Rate",
            ]
        }

        mock_columns = [i for i in attendance_data.columns if "Corp Avg" not in i]

        # Only add placeholder if there is attendance data
        student_retention_empty = pd.DataFrame(columns=mock_columns)
        student_retention_rate = pd.DataFrame(student_retention_rate_dict)

        metric_11cd_data = pd.concat(
            [student_retention_empty, student_retention_rate], ignore_index=True
        )
        metric_11cd_data.reset_index()

        metric_11cd_data = conditional_fillna(metric_11cd_data)

        metric_11cd_data = convert_to_svg_circle(metric_11cd_data)
        table_11cd = create_metric_table(metric_11cd_label, metric_11cd_data)
        table_container_11cd = set_table_layout(
            table_11cd, table_11cd, metric_11cd_data.columns
        )

    else:
        empty_table_11ab = no_data_table(
            "No Data to Display.",
            "Student Attendance Rate (1.1.a) and Teacher Retention Rate (1.1.b) compared with traditional school corporation.",
            "six"
        )

        table_container_11ab = set_table_layout(
            empty_table_11ab, empty_table_11ab, [""]
        )

        empty_table_11cd = no_data_table(
            "No Data to Display.",
            "End of Year to Beginning of Year (1.1.c) and Year over Year (1.1.d) Student Re-Enrollment Rate.",
        )

        table_container_11cd = set_table_layout(
            empty_table_11cd, empty_table_11cd, [""]
        )

        attendance_container = {"display": "none"}

    return (
        table_container_11ab,
        attendance_container,
        table_container_11cd,
        table_container_14ab,
        table_container_14cd,
        table_container_14ef,
        table_container_14g,
        table_container_16ab,
        table_container_16cd,
        k8_metrics_container,
        table_container_17ab,
        table_container_17cd,
        hs_metrics_container,
        ahs_table_container_113,
        ahs_table_container_1214,
        ahs_metrics_container,
        main_container,
        empty_container,
        no_data_to_display
    )  # table_container_15abcd,


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label("Key", className="label__header"),
                                    html.Div(create_proficiency_key()),
                                    html.P(
                                        "Hover over table title for metric rating calculations.",
                                        className="banner",
                                    ),
                                ],
                                className="pretty-container six columns",
                            ),
                        ],
                        className="bare-container--flex--center twelve columns",
                    ),
                    # Display attendance data in div outside of the metrics containers, because
                    # individual schools may have attendance data even if they have no academic data
                    html.Div(
                        [
                            html.Div(id="table-container-11ab", children=[]),
                        ],
                        id="attendance-container",
                    ),
                    html.Div(
                        [
                            html.Div(id="table-container-11cd", children=[]),
                            html.Div(id="table-container-14ab", children=[]),
                            html.Div(id="table-container-14cd", children=[]),
                            html.Div(id="table-container-14ef", children=[]),
                            html.Div(id="table-container-14g", children=[]),
                            # html.Div(id="table-container-15abcd", children=[]),
                            html.Div(id="table-container-16cd", children=[]),
                            html.Div(id="table-container-16ab", children=[]),
                        ],
                        id="k8-metrics-container",
                    ),
                    html.Div(
                        [
                            html.Div(id="table-container-17ab", children=[]),
                            html.Div(id="table-container-17cd", children=[]),
                        ],
                        id="hs-metrics-container",
                    ),
                    html.Div(
                        [
                            html.Div(id="table-container-ahs-113", children=[]),
                            html.Div(id="table-container-ahs-1214", children=[]),
                        ],
                        id="ahs-metrics-container",
                    ),
                ],
                id="academic-metrics-main-container",
            ),
            html.Div(
                [
                    html.Div(id="academic-metrics-no-data"),
                ],
                id="academic-metrics-empty-container",
            ),
        ],
        id="main-container",
    )