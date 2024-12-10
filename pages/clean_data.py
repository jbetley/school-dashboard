##################################
# ICSB Dashboard - Data Cleaning #
##################################
# author:   jbetley (https://github.com/jbetley)
# version:  1.16
# date:     12/10/24

import pandas as pd
import numpy as np

from .load_data import (
    get_excluded_years,
    get_ahs_averages,
    get_corporation_academic_data,
    get_adm_data,
    get_school_index,
    get_graduation_data,
)
from .calculations import (
    calculate_graduation_rate,
    calculate_sat_rate,
    calculate_proficiency,
    recalculate_total_proficiency,
)
from .process_data import transpose_data


def clean_discipline_data(data, demographic, category, year):
    results = data.copy()

    results = results.rename(columns={"Test Year": "Year"})

    # Drop years of data that have been excluded by the
    # selected year (are later than)
    excluded_years = get_excluded_years(year)

    if excluded_years:
        results = results[~results["Year"].isin(excluded_years)]

    for col in results.columns:
        results[col] = pd.to_numeric(results[col], errors="coerce")

    results = results.sort_values(by="Year", ascending=False)
    results = results.reset_index(drop=True)

    # NOTE: drop Arrest and Law Enforcement data #s are
    # generally too low to be worth measuring, so we don't
    # include them in the set, see globals.py definition of discipline_categories

    # drop_cols = [
    #     col
    #     for col in results.columns.to_list()
    #     if ("Arrest" in col or "Law Enforcement" in col) and "Overall" not in col
    # ]
    # results = results.drop(drop_cols, axis=1)

    # NOTE: Uncomment to store "law data" in separate df
    # law_data = raw_data[
    #     ["Year", "Arrests|Overall", "Law Enforcement Incidents|Overall"]
    # ]
    # results = results.drop(
    #     [
    #         "Arrests|Overall",
    #         "Arrests Unique Students|Overall",
    #         "Law Enforcement Incidents|Overall",
    #         "Law Enforcement Incidents Unique Students|Overall",
    #     ],
    #     axis=1,
    # )

    # converts float to str while dropping the decimal
    results["School ID"] = results["School ID"].astype("Int64").astype("str")
    results["Corporation ID"] = results["Corporation ID"].astype("Int64").astype("str")

    # annoyingly, there are two cases in which str.contains grabs two "categories"
    # instead of 1: "Homeless" also returns "Not Homeless" and "English Language Learner"
    # also returns "Non English Language Learner"- so we need to test and drop

    # We want the following columns for each selection:
    # 1) "Year"
    # 2) "Category" + "|" "Demographic" (e.g., In School Suspension|Male)
    # 3) "Category" + "Unique Students|" + "Demographic" (e.g., In School Suspension Unique Students|Male)
    # 4) "Total Unique Students|Overall"
    # 5) "Total Unique Students|" + "Category" (e.g., Total Unique Students|Male)

    year_col = "Year"
    total_students = "Total Unique Students|Overall"
    selected_category = category + "|" + demographic
    selected_category_unique = category + " Unique Students|" + demographic

    # "Overall" does not have column (5) (it is the same as (4)).
    if demographic != "Overall":
        category_students_unique = "Total Unique Students|" + demographic
        selected_cols = [
            year_col,
            selected_category,
            total_students,
            category_students_unique,
            selected_category_unique,
        ]
    else:
        selected_cols = [
            year_col,
            total_students,
            selected_category,
            selected_category_unique,
        ]

    discipline_data = results[selected_cols].copy()

    if category == "Homeless" or category == "English Language Learner":
        discipline_data = discipline_data[
            discipline_data.columns[~discipline_data.columns.str.contains(r"Not|Non")]
        ]

    # drop years where total students for the category is = 0
    student_total = "Total Unique Students|" + demographic

    discipline_data = discipline_data[~discipline_data[student_total].isna()]

    # table gets real wide, so we limit to three years of data
    # limit to 3 years of data, also drop any years with no data.
    discipline_data = discipline_data[discipline_data[selected_category].notna()].copy()
    discipline_data = discipline_data.iloc[0:3]

    return discipline_data


def clean_adm_data(data):
    results = data.copy()

    # drop "Virtual ADM"
    results = results.drop(
        list(
            results.filter(
                regex="Fall Virtual ADM|Spring Virtual ADM|School ID|Corporation ID|Corporation Name|School Name"
            )
        ),
        axis=1,
    )

    # Each adm average requires 2 columns (Fall and Spring). If there are an
    # odd number of columns after the above drop, that means that the last
    # column is a Fall without a Spring, so we store that column, drop it,
    # and add it back later
    last_col = pd.DataFrame()

    if (len(results.columns) % 2) != 0:
        last_col_name = str(int(results.columns[-1][:4]) + 1)
        last_col[last_col_name] = results[results.columns[-1]]
        results = results.drop(results.columns[-1], axis=1)

    # get years with data
    adm_columns = [c[:4] for c in results.columns if "Spring" in c]

    # make numbers
    for col in results:
        results[col] = pd.to_numeric(results[col], errors="coerce")

    # Average each group of 2 columns and use name of 2nd column (Spring) for result
    final = results.groupby(np.arange(len(results.columns)) // 2, axis=1).mean()
    final.columns = adm_columns

    if not last_col.empty:
        final[last_col_name] = last_col[last_col_name]

    return final


def clean_ahs_averages(data):
    results = data.copy()

    drop_cols = ["School Name", "School Type", "Lat", "Lon"]
    results = results.drop(drop_cols, axis=1)

    non_sum_cols = [
        "Year",
        "School ID",
        "Corporation ID",
        "Corporation Name",
        "Low Grade",
        "High Grade",
    ]
    sum_cols = [c for c in results.columns if c not in non_sum_cols]

    for col in sum_cols:
        results[col] = pd.to_numeric(results[col], errors="coerce")

    # create a dict for agg()
    column_map = {col: "first" for col in non_sum_cols}
    column_map2 = {col: "sum" for col in sum_cols}
    column_map3 = {"Attendance Rate": "mean"}
    group_cols = {**column_map, **column_map2, **column_map3}

    final_results = results.groupby(["Year"], as_index=False).agg(group_cols)

    final_results["Corporation Name"] = "AHS State Average"
    final_results["Corporation ID"] = 9999
    final_results["School ID"] = 9999

    final_results = final_results.sort_values(by="Year")

    return final_results


def clean_academic_data(data, schools, school_type, year, page):
    school_data = data.copy()

    school_data = school_data.fillna(value=np.nan)

    school_id = schools[0]
    # get corp data (for academic_metrics and academic_analysis_single_year)
    # and add to dataframe
    if school_type == "ahs":
        corp_data = get_ahs_averages()
    else:
        corp_data = get_corporation_academic_data(school_id, school_type)

    # add columns not in corp database
    corp_data["School ID"] = corp_data["Corporation ID"]
    corp_data["School Name"] = corp_data["Corporation Name"]

    corp_data = corp_data.fillna(value=np.nan)

    # merge - result includes school, school corp, and comparable schools if
    # multiple school ids in the schools variable
    raw_merged_data = pd.concat([school_data, corp_data], axis=0)

    # Drop years of data that have been excluded by the
    # selected year (are later than)
    excluded_years = get_excluded_years(year)

    if excluded_years:
        raw_merged_data = raw_merged_data[~raw_merged_data["Year"].isin(excluded_years)]

    if len(raw_merged_data.index) < 1 or raw_merged_data.empty:
        return pd.DataFrame()

    raw_merged_data = raw_merged_data.sort_values(by="Year", ascending=False)

    raw_merged_data = raw_merged_data.reset_index(drop=True)

    # TODO: Is this redundant? Same check is performed in Calculate Proficiency?
    ## Drop all columns for a Category if the value of "Total Tested" for
    # the Category for the school is null or 0 for the "school"
    drop_columns = []

    data = raw_merged_data.copy()

    data["School ID"] = data["School ID"].astype("Int64").astype("str")
    data["Corporation ID"] = data["Corporation ID"].astype("Int64").astype("str")

    if school_type == "k8":
        tested_cols = [
            col
            for col in data.columns.to_list()
            if "Total Tested" in col or "Test N" in col
        ]
    else:
        tested_cols = [
            col
            for col in data.columns.to_list()
            if "Total Tested" in col or "Cohort Count" in col
        ]

    for col in tested_cols:
        if (
            pd.to_numeric(
                data[data["School ID"] == school_id][col], errors="coerce"
            ).sum()
            == 0
            or data[data["School ID"] == school_id][col].isnull().all()
        ):
            if "Total Tested" in col:
                match_string = " Total Tested"
            else:
                if school_type == "k8":
                    match_string = " Test N"
                else:
                    match_string = "|Cohort Count"

            matching_cols = data.columns[
                pd.Series(data.columns).str.startswith(col.split(match_string)[0])
            ]

            drop_columns.append(matching_cols.tolist())

    drop_all = [i for sub_list in drop_columns for i in sub_list]

    data = data.drop(drop_all, axis=1).copy()

    # k8 or hs data with excluded years and non-tested categories dropped
    data = data.reset_index(drop=True)

    # HS/AHS data
    if school_type == "hs" or school_type == "ahs":
        processed_data = data.copy()

        # remove "EBRW and Math" columns
        processed_data = processed_data.drop(
            list(processed_data.filter(regex="EBRW and Math")), axis=1
        )

        # In Cohort Grad Rate
        if "Total|Cohort Count" in processed_data.columns:
            processed_data = calculate_graduation_rate(processed_data)

        # SAT Benchmark proficiency
        if "Total|EBRW Total Tested" in processed_data.columns:
            processed_data = calculate_sat_rate(processed_data)

        # AHS only data
        if school_type == "ahs":
            # Total Grad rate satisfies Accountability Metric 1.2.a -
            #  4-year cohort graduation rate

            ahs_data = processed_data.copy()
            if "AHS|CCR" in ahs_data.columns:
                ahs_data["AHS|CCR"] = pd.to_numeric(
                    ahs_data["AHS|CCR"], errors="coerce"
                )

            if "AHS|Actual Graduates" in ahs_data.columns:
                ahs_data["AHS|Actual Graduates"] = pd.to_numeric(
                    ahs_data["AHS|Actual Graduates"], errors="coerce"
                )

            # Student performance, dual-credit accumulation and/or industry
            # certification reflects college and career readiness, based on
            # the percentage of non-duplicated graduating students in the
            # current school year
            if {"AHS|CCR", "AHS|Actual Graduates"}.issubset(ahs_data.columns):
                ahs_data["CCR Percentage"] = (
                    ahs_data["AHS|CCR"] / ahs_data["AHS|Actual Graduates"]
                )

            # AHS|Actual Graduates is used in three calculations where we want to track N-Size,
            # "Graduation Graduation to Enrollment", "Grade 12 Graduation", and "CCR Percentage"
            ahs_data["Graduation to Enrollment|Cohort Count"] = ahs_data[
                "AHS|Actual Graduates"
            ]
            ahs_data["CCR Percentage|Count"] = ahs_data["AHS|Actual Graduates"]

            ahs_data = ahs_data.rename(
                columns={"AHS|Actual Graduates": "Grade 12|Cohort Count"}
            )

            if "AHS|Actual Enrollment" in ahs_data.columns:
                ahs_data["AHS|Actual Enrollment"] = pd.to_numeric(
                    ahs_data["AHS|Actual Enrollment"], errors="coerce"
                )

            # Students enrolled in grade 12 graduate within the school year being assessed.
            if {
                "AHS|Actual Enrollment",
                "Grade 12|Cohort Count",
            }.issubset(ahs_data.columns):
                ahs_data["Grade 12|Graduation Rate"] = (
                    ahs_data["Grade 12|Cohort Count"]
                    / ahs_data["AHS|Actual Enrollment"]
                )

            ## AHS Graduation Calculation (AHS Accountability)
            # NOTE: a school must have at least ten (10) students graduate in the school
            # year being assessed. If school has fewer than ten (10) graduates for a year
            # based calculation on the current graduates aggregated with each immediately
            # preceding year's graduates until a cohort of at least ten (10) graduates is reached

            selected_school = get_school_index(school_id)
            corp_id = int(selected_school["Corporation ID"].values[0])

            # get adm average and add to dataframe matching on school_id and Year
            adm_average = get_adm_data(corp_id)
            school_adm = adm_average.T.rename_axis("Year").reset_index()
            school_adm = school_adm.rename(columns={0: "ADM Average"})
            school_adm["School ID"] = school_id

            for col in school_adm.columns:
                school_adm[col] = pd.to_numeric(school_adm[col], errors="coerce")

            ahs_data["School ID"] = ahs_data["School ID"].astype(int)

            processed_data = pd.merge(
                ahs_data,
                school_adm,
                how="left",
                on=["Year", "School ID"],
                suffixes=("", "_y"),
            )

            # need to convert back to str or else we get a numpy error around line 1360 (data check)
            # see: https://stackoverflow.com/questions/40659212/futurewarning-elementwise-comparison
            # -failed-returning-scalar-but-in-the-futur
            processed_data["School ID"] = ahs_data["School ID"].astype(str)

            # NOTE: graduation calculation proposed by AHS. This is not unlike
            # the Indiana Adult Accountability Graduation to Enrollment Percentage
            # calculation (weighted 90%). the denominator is the school's
            # within-year-average number of students (ADM average), the numerator
            # is the total number of graduates for the assessed year, and then
            # multiply the quotient by 4
            processed_data["Graduation to Enrollment|Graduation Rate"] = (
                processed_data["Graduation to Enrollment|Cohort Count"]
                / processed_data["ADM Average"]
            ) * 4

            # NOTE: the Indiana Adult Graduation Rate (weighted 10%) is not
            # currently calculated because we don't have a reliable way to
            # get the 5-year grad rate:
            #   (1) Calculate 5-Year grad rate (IC 20-26-13-10.2) for the cohort
            #   immediately prior to the assessed year cohort.
            #   Formula: (Total|Graduates + PY Total|Graduates) / Total|Cohort
            #   (2) Calculate 4-Year grad rate for the cohort immediately preceding
            #   the prior year cohort
            #   Formula: Total|Graduates/Total|Cohort
            #   (3) Subtract the four 4-Year graduation rate from the 4-Year
            #   graduation rate for the previous year.
            #   (4) Add the sum of (3) to the 4-Year graduation rate of the
            #   assessed year cohort

            # Final Graduation Calculation
            #   (1) Calculate graduation qualifying examination passing rate
            #   equals 1 if rate is at least 90% else use actual % passing
            #   (2) Multiply GQE passing rate by the sum of Graduation to
            #   Enrollment + Graduation Weights

            # CCR Score
            #   (1) calculate the college and career achievement rate;
            #   (2) the college and career readiness factor (100/.8); and
            #   (3) one hundred (100).

            # Final Calculation
            # First Year weighting: graduation calculation (20%) and ccr score (80%)
            # All Other Years: graduation calculation (40%) / ccr score (60%)

    # K8 data
    elif school_type == "k8":
        processed_data = data.copy()

        # remove "ELA and Math" columns
        processed_data = processed_data.drop(
            list(processed_data.filter(regex="ELA and Math")), axis=1
        )

        processed_data = calculate_proficiency(processed_data)

        # In order for an apples to apples comparison between School Total Proficiency,
        # we need to recalculate it for the comparison schools using the same grade span
        # as the selected school. E.g., school is k-5, comparison school is k-8, we
        # recalculate comparison school totals using only grade k-5 data.
        comparison_data = processed_data.loc[
            processed_data["School ID"] != school_id
        ].copy()

        school_data = processed_data.loc[
            processed_data["School ID"] == school_id
        ].copy()

        revised_totals = recalculate_total_proficiency(comparison_data, school_data)

        processed_data = processed_data.set_index(["School ID", "Year"])
        processed_data.update(revised_totals.set_index(["School ID", "Year"]))

        # this is school, school corporation, and comparable school data
        processed_data = processed_data.reset_index()

    # Page specific processing

    # the dataframe can be empty if all columns other than the 1st
    # Year are null or if the dataframe has no school_id
    if (
        processed_data.iloc[:, 1:].isna().all().all()
        or school_id not in processed_data["School ID"].values
    ):
        return pd.DataFrame()

    else:
        ## Keep five years of data at most
        years = processed_data["Year"].unique().tolist()
        if len(years) > 5:
            keep_years = years[:5]
            processed_data = processed_data[processed_data["Year"].isin(keep_years)]

        # TODO add multipage analysis data (currently being calculated separately in
        # TODO: get_multiyear_data)
        if page == "analysis":
            ## HS/AHS academic_analysis_single.py
            if school_type == "hs" or school_type == "ahs":
                hs_data = processed_data.copy()

                # NOTE: Cohort data (not currently kept): Actual Graduates,
                # Actual Enrollment, CCR
                if school_type == "ahs":
                    analysis_data = hs_data.filter(
                        regex=r"School ID|School Name|Low Grade|High Grade|Corporation ID|Corporation Name \
                        |CCR Percentage|Grade 12|Total\|Graduation Rate|Graduation to Enrollment|Benchmark \%|^Year$",
                        axis=1,
                    ).copy()
                else:
                    analysis_data = hs_data.filter(
                        regex=r"School ID|School Name|Low Grade|High Grade|Corporation ID|Corporation Name|Graduation Rate$|Benchmark \%|^Year$",
                        axis=1,
                    ).copy()

                analysis_data = analysis_data.drop(
                    list(analysis_data.filter(regex="EBRW and Math")), axis=1
                )

                hs_cols = [
                    c
                    for c in analysis_data.columns
                    if c not in ["School Name", "Corporation Name"]
                ]

                # get index of rows where school_id matches selected school
                school_idx = analysis_data.index[
                    analysis_data["School ID"] == school_id
                ].tolist()[0]

                for col in hs_cols:
                    analysis_data[col] = pd.to_numeric(
                        analysis_data[col], errors="coerce"
                    )

                # drop all columns where the row at school_name_idx has a NaN value
                analysis_data = analysis_data.loc[:, ~hs_data.iloc[school_idx].isna()]

                return analysis_data

            ## K8 academic_analysis_single.py
            else:
                k8_data = processed_data.copy()

                analysis_data = k8_data.filter(
                    regex=r"\|ELA Proficient %$|\|Math Proficient %$|IREAD Proficient %|^Year$|Low|High|School Name|School ID|Corporation ID",
                    axis=1,
                )
                analysis_data = analysis_data.sort_values("Year").reset_index(drop=True)

                analysis_data = analysis_data[
                    analysis_data.columns[
                        ~analysis_data.columns.str.contains(r"Female|Male")
                    ]
                ]

                # We don't want to get rid of "***" yet, but we also don't
                # want to pass through a dataframe that that is all "***" - so
                # we convert create a copy, coerce all of the academic columns
                # to numeric and check to see if the entire dataframe for NaN
                check_for_unchartable_data = analysis_data.copy()

                check_for_unchartable_data.drop(
                    ["School Name", "School ID", "Low Grade", "High Grade", "Year"],
                    axis=1,
                    inplace=True,
                )

                for col in check_for_unchartable_data.columns:
                    check_for_unchartable_data[col] = pd.to_numeric(
                        check_for_unchartable_data[col], errors="coerce"
                    )

                # one last check
                if (
                    (school_type == "k8" or school_type == "k12")
                    and len(analysis_data.index) > 0
                ) and check_for_unchartable_data.isnull().all().all() == True:
                    analysis_data = pd.DataFrame()

                    return analysis_data

                else:
                    return analysis_data

        elif page == "info" or page == "metrics":
            corp_data = processed_data[
                processed_data["School ID"] == processed_data["Corporation ID"]
            ].copy()
            school_data = processed_data[
                processed_data["School ID"] == school_id
            ].copy()

            ## AHS academic_metrics.py
            if school_type == "ahs" and page == "metrics":
                school_metric_data = school_data[
                    [
                        "Year",
                        "CCR Percentage",
                        "Total|Graduation Rate",
                        "Grade 12|Graduation Rate",
                        "Graduation to Enrollment|Graduation Rate",
                    ]
                ]

                return school_metric_data

            ## HS academic_information.py & academic_metrics.py
            elif school_type == "hs":
                corp_data = processed_data[
                    processed_data["School ID"] == processed_data["Corporation ID"]
                ].copy()
                school_data = processed_data[
                    processed_data["School ID"] == school_id
                ].copy()

                # ["schools", "type", "year", "page"]

                school_metrics_data = transpose_data(school_data, school_type)

                # break early if data is empty
                if school_metrics_data.empty:
                    return school_metrics_data

                corp_metrics_data = transpose_data(corp_data, school_type)

                # Remove N-Size columns from corp dataframe
                corp_metrics_data = corp_metrics_data.filter(
                    regex=r"Category|Corp", axis=1
                )

                ## HS academic_information.py
                if page == "info":
                    return school_metrics_data

                ## HS academic_metrics.py
                else:
                    # add state graduation average to corp df
                    state_grad_average = get_graduation_data()

                    corp_metrics_data = pd.concat(
                        [
                            corp_metrics_data.reset_index(drop=True),
                            state_grad_average.reset_index(drop=True),
                        ],
                        axis=0,
                    ).reset_index(drop=True)

                    # for the school calculation we duplicate the school's Total
                    # Graduation rate values and rename the first column ("Category")
                    # to "State Grad Average" - for the corporation df, Total Graduation
                    # is equal to the Corp Average and State Grade Average is the
                    # Stat Average. So when the difference is calculated
                    # between the two data frames, Total Graduation Rate is the diff
                    # between school total and corp total and "State Average" is the
                    # diff between school total and state average.

                    # for this to work, we need to make sure the school has a "Total
                    # Graduation Rate" Category- if is missing, we add a new row filled
                    # with nan (by enlargement)
                    if (
                        "Total|Graduation Rate"
                        not in school_metrics_data["Category"].values
                    ):
                        school_metrics_data.loc[len(school_metrics_data)] = np.nan

                        school_metrics_data.loc[
                            school_metrics_data.index[-1], "Category"
                        ] = "Total|Graduation Rate"

                    duplicate_row = school_metrics_data[
                        school_metrics_data["Category"] == "Total|Graduation Rate"
                    ].copy()

                    duplicate_row["Category"] = "State Graduation Average"

                    # NOTE: Need to declare an explicit type here because there is a
                    # bug in "pandas-stubs" that causes mypy to mark code as
                    # "unreachable" following a pd.concat with Iterable[None]. See:
                    # https://stackoverflow.com/questions/78156640/why-is-visual-studio-code-saying-my-code-in-unreachable-after-using-the-pandas-c
                    # NOTE: trying and failing to suppress this warning by adding
                    # 'disable_error_code = "annotation-unchecked"' to mypy.ini. but kept
                    # getting errors. So here it stays
                    # https://stackoverflow.com/questions/74578185/suppress-mypy-notes
                    merged_dataframes: list[pd.DataFrame] = [
                        school_metrics_data,
                        duplicate_row,
                    ]

                    school_metrics_data = pd.concat(
                        merged_dataframes, axis=0, ignore_index=True
                    )

                    # Corp -State Grad Rate should equal State Grad Rate
                    # Corp - Total Grad Rate and Nonwaiver Grad Rate should equal corp totals
                    # School - Both State and Total Grad Rate should equal school total grad rate
                    # School - Nonwaiver = school

                    # calcs = School (Grad) - Corp (State) = State Grad Avg diff
                    #       = School (Grad) - Corp (Total) = Corp Grad Avg diff
                    #       = School (NonW) - Corp

                    # add corp data to df

                    corp_proficiency_cols = [
                        col
                        for col in corp_metrics_data.columns.to_list()
                        if "Corp" in col
                    ]
                    merged_data = pd.concat(
                        [school_metrics_data, corp_metrics_data[corp_proficiency_cols]],
                        axis=1,
                    )

                    # NOTE: at the moment HS metrics only include Total Graduation Rate,
                    # Non Waiver Graduation Rate, and State Graduation Average

                    # clean up and filter
                    merged_data = merged_data.replace(
                        {
                            "Total|Graduation Rate": "Total Graduation Rate",
                            "Non Waiver|Graduation Rate": "Non Waiver Graduation Rate",
                        },
                        regex=False,
                    )

                    hs_categories = [
                        "Total Graduation Rate",
                        "Non Waiver Graduation Rate",
                        "State Graduation Average",
                    ]
                    metric_data = merged_data[
                        merged_data["Category"].str.contains("|".join(hs_categories))
                    ]

                    metric_data = metric_data.reset_index(drop=True)

                    return metric_data

            ## K8 academic_information.py & academic_metrics.py
            else:
                school_info_data = processed_data[
                    processed_data["School ID"] == school_id
                ]

                final_school_data = transpose_data(school_info_data, school_type)

                ## K8 academic_information.py
                if page == "info":
                    return final_school_data

                ## K8 academic_metrics.py
                else:
                    corp_info_data = processed_data[
                        processed_data["School ID"] == processed_data["Corporation ID"]
                    ]

                    final_corp_data = transpose_data(corp_info_data, school_type)

                    corp_proficiency_cols = [
                        col
                        for col in final_corp_data.columns.to_list()
                        if "Corp" in col
                    ]

                    # School Proficiency and N-Size and Corp Profiency
                    metric_data = pd.concat(
                        [final_school_data, final_corp_data[corp_proficiency_cols]],
                        axis=1,
                    )

                    return metric_data
