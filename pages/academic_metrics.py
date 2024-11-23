#####################################
# ICSB Dashboard - Academic Metrics #
#####################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.16
# date:     10/03/24

import dash
from dash import html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd
import itertools

# import local functions
from .globals import ethnicity, subgroup, grades_all

from .load_data import (
    get_school_index,
    get_academic_data,
    get_ilearn_student_data,
    get_excluded_years,
)

from .tables import (
    create_metric_table,
    create_proficiency_key,
    create_empty_page_layout,
    create_empty_table_layout,
)

from .layouts import set_table_layout

from .string_helpers import convert_to_svg_circle

from .calculate_metrics import (
    calculate_high_school_metrics,
    calculate_adult_high_school_metrics,
    calculate_attendance_metrics,
    calculate_iread_metrics,
    calculate_values,
    calculate_metrics,
)

from .calculations import conditional_fillna, set_academic_rating

dash.register_page(__name__, path="/academic_metrics", top_nav=True, order=9)


@callback(
    Output("table-container-11ab", "children"),
    Output("attendance-container", "style"),
    Output("table-container-11cd", "children"),
    Output("table-container-14ab", "children"),
    Output("table-container-14cd", "children"),
    Output("table-container-14ef", "children"),
    Output("table-container-14g", "children"),
    # Output("table-container-15abcd", "children"),    # growth data (not yet implemented)
    Output("table-container-16ab", "children"),
    Output("table-container-16cd", "children"),
    Output("k8-metrics-container", "style"),
    Output("table-container-17ab", "children"),
    Output("table-container-17cd", "children"),
    Output("hs-metrics-container", "style"),
    Output("table-container-ahs", "children"),
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

    selected_year_string = year
    selected_year_numeric = int(selected_year_string)

    # default values (only empty container displayed)
    table_container_11ab = []
    table_container_11cd = []
    table_container_14ab = []
    table_container_14cd = []
    table_container_14ef = []
    table_container_14g = []
    # table_container_15abcd = []
    table_container_16ab = []
    table_container_16cd = []
    attendance_container = {"display": "none"}
    k8_metrics_container = {"display": "none"}

    table_container_17ab = []
    table_container_17cd = []
    hs_metrics_container = {"display": "none"}

    ahs_table_container = []
    ahs_metrics_container = {"display": "none"}

    main_container = {"display": "none"}
    empty_container = {"display": "block"}

    no_data_to_display = create_empty_page_layout(
        "No Data to Display.", "Academic Metrics"
    )

    selected_school = get_school_index(school)
    selected_school_type = selected_school["School Type"].values[0]
    selected_school_id = int(selected_school["School ID"].values[0])

    # split K12 school exception (CHS)
    if selected_school_id == 5874 and selected_year_numeric < 2021:
        selected_school_type = "k12"

    # K8 Academic Metrics (for K8 and K12 schools)
    if selected_school_type == "k8" or selected_school_type == "k12":
        list_of_schools = [school]
        if selected_school_type == "k12":
            school_type = "k8"
        else:
            school_type = selected_school_type

        metric_data = get_academic_data(
            list_of_schools, school_type, selected_year_numeric, "metrics"
        )

        if len(metric_data.index) > 0:
            metric_data = metric_data.replace({"^": "***"})

            k8_metrics_container = {"display": "block"}
            main_container = {"display": "block"}
            empty_container = {"display": "none"}

            k8_year_values, k8_comparison_values = calculate_values(
                metric_data, selected_year_string
            )

            # Get Year over Year and Combined Metrics
            combined_years, combined_delta = calculate_metrics(
                k8_year_values, k8_comparison_values
            )

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

            ## Accountability Metrics 1.4.e & 1.4.f

            # The percentage of students who have been enrolled for at least two (2)
            # full school years achieving proficiency on the state assessment in English
            # Language Arts & Math.
            ilearn_student_raw = get_ilearn_student_data(school)

            ilearn_student_raw = ilearn_student_raw[
                (ilearn_student_raw["ELA Proficiency"] != "Did Not Test")
                & (ilearn_student_raw["Math Proficiency"] != "Did Not Test")
            ]

            # sort by STN and Year and then shift STN up one - this shifts the
            # previous year STN up - so any row with matching STN's is a row where
            # the same student has been at the school for at least 2 years.
            ilearn_student_raw = ilearn_student_raw.sort_values(
                ["STN", "Year"], ascending=[True, False]
            )

            ilearn_student_raw["STN_shift"] = ilearn_student_raw["STN"].shift(-1)

            # Raw df also includes scale scores- which we aren't using here
            ilearn_2yr = ilearn_student_raw.filter(
                regex=rf"Year|School ID|STN|STN_shift|ELA Proficiency|Math Proficiency"
            ).copy()

            ilearn_2yr_final = ilearn_2yr[ilearn_2yr["STN"] == ilearn_2yr["STN_shift"]]

            # NOTE: Not currently breaking down by proficiency category, so we change
            # "Above Proficiency" to "At Proficiency" to get final percentage
            ilearn_2yr_final = ilearn_2yr_final.replace(
                {"Above Proficiency": "At Proficiency"}, regex=True
            )

            #  Calculate N-Size and Proficiency Percentage
            ilearn_2yr_ela = (
                ilearn_2yr_final.groupby("Year")["ELA Proficiency"]
                .value_counts()
                .reset_index(name="SN-Size")
            )
            ela_prof = (
                ilearn_2yr_final.groupby("Year")["ELA Proficiency"]
                .value_counts(normalize=True)
                .reset_index(name="School")
            )
            ilearn_2yr_ela["School"] = ela_prof["School"]

            ilearn_2yr_ela = ilearn_2yr_ela[
                (ilearn_2yr_ela["ELA Proficiency"] == "At Proficiency")
            ]

            ilearn_2yr_ela = ilearn_2yr_ela.replace(
                {"At Proficiency": "ELA Proficiency"}, regex=True
            )
            ilearn_2yr_ela = ilearn_2yr_ela.rename(
                columns={"ELA Proficiency": "Proficiency"}
            )

            ilearn_2yr_math = (
                ilearn_2yr_final.groupby("Year")["Math Proficiency"]
                .value_counts()
                .reset_index(name="SN-Size")
            )
            math_prof = (
                ilearn_2yr_final.groupby("Year")["Math Proficiency"]
                .value_counts(normalize=True)
                .reset_index(name="School")
            )
            ilearn_2yr_math["School"] = math_prof["School"]

            ilearn_2yr_math = ilearn_2yr_math[
                (ilearn_2yr_math["Math Proficiency"] == "At Proficiency")
            ]

            ilearn_2yr_math = ilearn_2yr_math.replace(
                {"At Proficiency": "Math Proficiency"}, regex=True
            )
            ilearn_2yr_math = ilearn_2yr_math.rename(
                columns={"Math Proficiency": "Proficiency"}
            )

            # merge
            ilearn_2yr_all = pd.concat([ilearn_2yr_ela, ilearn_2yr_math], axis=0)

            # drop excluded years
            excluded_years = get_excluded_years(selected_year_string)

            if excluded_years:
                ilearn_2yr_all = ilearn_2yr_all[
                    ~ilearn_2yr_all["Year"].isin(excluded_years)
                ]

            # reshape
            ilearn_2yr_shape = ilearn_2yr_all.pivot(
                index="Proficiency", columns="Year", values=["SN-Size", "School"]
            )
            ilearn_2yr_shape.columns = [
                f"{y}{x}" for x, y in ilearn_2yr_shape.columns.to_flat_index()
            ]
            ilearn_2yr_shape = ilearn_2yr_shape.reset_index()
            ilearn_2yr_shape = ilearn_2yr_shape.rename(
                columns={"Proficiency": "Category"}
            )

            ilearn_2yr_shape.loc[
                ilearn_2yr_shape["Category"] == "ELA Proficiency",
                "Category",
            ] = "1.4.e Two year student proficiency in ELA."

            ilearn_2yr_shape.loc[
                ilearn_2yr_shape["Category"] == "Math Proficiency",
                "Category",
            ] = "1.4.f Two year student proficiency in Math."

            # reorder columns
            # #TODO: convert to function
            school_cols = [e for e in ilearn_2yr_shape.columns if "School" in e]
            nsize_cols = [e for e in ilearn_2yr_shape.columns if "SN-Size" in e]

            school_cols.sort()
            nsize_cols.sort()

            final_cols = list(itertools.chain(*zip(school_cols, nsize_cols)))

            final_cols.insert(0, "Category")
            metric_14ef_data = ilearn_2yr_shape[final_cols]

            # calculate metrics
            ilearn_2yr_limits = [0.8, 0.69, 0.59]

            [
                metric_14ef_data.insert(
                    i + 1,
                    str(metric_14ef_data.columns[i - 1])[: 7 - 3] + "Rate" + str(i),
                    metric_14ef_data.apply(
                        lambda x: set_academic_rating(
                            x[metric_14ef_data.columns[i - 1]], ilearn_2yr_limits, 2
                        ),
                        axis=1,
                    ),
                )
                for i in range(metric_14ef_data.shape[1] - 1, 1, -2)
            ]

            metric_14ef_label = [
                "Percentage of students enrolled for at least two school years achieving proficiency on the state assessment in English Language Arts (1.4.e) and Math (1.4.f)"
            ]

            metric_14ef_data = convert_to_svg_circle(metric_14ef_data)
            table_14ef = create_metric_table(metric_14ef_label, metric_14ef_data)

            table_container_14ef = set_table_layout(
                table_14ef, table_14ef, metric_14ef_data.columns
            )

            # iread_data
            # we have to recalculate IREAD metrics because the initial
            # calculation (including IREAD with all other metrics) gives
            # an erroneous result
            # NOTE: combined_delta has other available data as well
            iread_data = combined_delta[
                combined_delta["Category"] == "Total|IREAD Proficient %"
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
                # create_metric_table requies label to be a list, while
                # create_empty_table_layout wants a string
                empty_table_14g = create_empty_table_layout(
                    "No Data to Display.",
                    "1.4.g Percentage of students achieving proficiency on the IREAD-3 state assessment.",
                    "six",
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
        selected_school_type == "hs"
        or selected_school_type == "ahs"
        or selected_school_type == "k12"
    ):
        if selected_school_type == "k12":
            selected_school_type = "hs"

        list_of_schools = [school]

        raw_metric_data = get_academic_data(
            list_of_schools, selected_school_type, selected_year_numeric, "metrics"
        )

        if len(raw_metric_data.index) > 0:
            # Adult High School Metrics (in single table atm)
            # NOTE: Create additional tables as needed
            if selected_school_type == "ahs":
                ahs_metrics_container = {"display": "block"}
                main_container = {"display": "block"}
                empty_container = {"display": "none"}

                ahs_metric_data = calculate_adult_high_school_metrics(raw_metric_data)

                ahs_metric_data["Category"] = (
                    ahs_metric_data["Metric"] + " " + ahs_metric_data["Category"]
                )

                ahs_metric_data = ahs_metric_data.drop("Metric", axis=1)

                # TODO: Split these out into separate tables. one for each label
                ahs_metric_label = ["In-cohort Graduation Rate (1.2.a)"]
                # ahs_metric_label = ["Grade 12 Graduation Rate (1.2.b)"]
                # ahs_metric_label = ["CCR Percentage (1.3)"]
                # ahs_metric_label = ["State Letter Grade (1.1)"]

                ahs_metric_data = convert_to_svg_circle(ahs_metric_data)

                ahs_table = create_metric_table(ahs_metric_label, ahs_metric_data)

                ahs_table_container = set_table_layout(
                    ahs_table, ahs_table, ahs_metric_data.columns
                )

            else:
                # NOTE: We do not currently use hs_year_over_year_values
                # for hs metrics
                hs_year_over_year_values, hs_comparison_values = calculate_values(
                    raw_metric_data, selected_year_string
                )

                if not hs_comparison_values.empty:
                    hs_metrics_container = {"display": "block"}
                    main_container = {"display": "block"}
                    empty_container = {"display": "none"}

                    hs_metric_data = calculate_high_school_metrics(hs_comparison_values)

                    metric_17ab_label = [
                        "High School Accountability Metrics 1.7.a & 1.7.b"
                    ]
                    hs_metric_data = convert_to_svg_circle(hs_metric_data)
                    table_17ab = create_metric_table(metric_17ab_label, hs_metric_data)
                    table_container_17ab = set_table_layout(
                        table_17ab, table_17ab, hs_metric_data.columns
                    )

                    # Create placeholders (High School Accountability Metrics 1.7.c & 1.7.d)
                    all_cols = hs_metric_data.columns.tolist()

                    simple_cols = [
                        x
                        for x in all_cols
                        if (
                            not x.endswith("+/-") and not x.endswith("Diff")
                        )  # Difference
                    ]

                    grad_metrics_empty = pd.DataFrame(columns=simple_cols)

                    grad_metrics_dict = {
                        "Category": [
                            "1.7.c The percentage of students entering Grade 12 at beginning of year who graduated",
                            "1.7.d. The percentage of graduating students planning to pursue college or career.",
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

                    # TODO: Testing -this is borken?? try uncommenting and
                    # TODO: commenting in calculate_high school metrifcs
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

    attendance_data = calculate_attendance_metrics(
        school, selected_school_type, selected_year_string
    )

    if len(attendance_data.index) > 0:
        attendance_container = {"display": "block"}

        # Create placeholders (Acountability Metric 1.1.b.)
        teacher_retention_rate = pd.DataFrame(
            {"Category": ["1.1.b Teacher Retention Rate"]}
        )

        metric_11ab_data = pd.merge(
            attendance_data, teacher_retention_rate, how="outer", on="Category"
        )

        # TODO: Testing, normally uncommented
        # metric_11ab_data = conditional_fillna(metric_11ab_data)

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

        # TODO: Testing
        # metric_11cd_data = conditional_fillna(metric_11cd_data)

        metric_11cd_data = convert_to_svg_circle(metric_11cd_data)
        table_11cd = create_metric_table(metric_11cd_label, metric_11cd_data)
        table_container_11cd = set_table_layout(
            table_11cd, table_11cd, metric_11cd_data.columns
        )

    else:
        empty_table_11ab = create_empty_table_layout(
            "No Data to Display.",
            "Student Attendance Rate (1.1.a) and Teacher Retention Rate (1.1.b) compared with traditional school corporation.",
            "six",
        )

        table_container_11ab = set_table_layout(
            empty_table_11ab, empty_table_11ab, [""]
        )

        empty_table_11cd = create_empty_table_layout(
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
        ahs_table_container,
        ahs_metrics_container,
        main_container,
        empty_container,
        no_data_to_display,
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
                            html.Div(
                                id="table-container-11cd",
                                children=[],
                                className="pagebreak-after",
                            ),
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
                            html.Div(id="table-container-ahs", children=[]),
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
