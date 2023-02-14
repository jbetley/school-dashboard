#############################
# Organizational Compliance #
#############################
# author:   jbetley
# rev:     06.01.22

from dash import html, dash_table, Input, Output
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
import os.path

from app import app

# np.warnings.filterwarnings('ignore')


## Callback ##
@app.callback(
    Output("org-table", "children"),
    Output("odefn-table", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("dash-session", "data"),
)
def update_orgcom_page(school, year, data):
    if not school:
        raise PreventUpdate

    school_index = pd.DataFrame.from_dict(data["0"])
    school = school_index.loc[
        school_index["School ID"] == school, ["School Name"]
    ].values[0][0]
    schoolFile = "data/O-" + school + ".csv"

    if os.path.isfile(schoolFile):
        org_data = pd.read_csv(schoolFile, dtype=str)

        # get first available year of data (index 2- after 'Standard' & 'Description')
        current_year = org_data.columns[2]

        # get number of cols (years) to delete from df by subtracting selected year from available year (e.g., 2022 - 2022 = 0, no cols to delete)
        num_years_to_remove = int(current_year) - int(year)

        # if years to delete, drop cols starting with most recent year (starting at index [2] and ending at index[2] + years to drop)
        if num_years_to_remove > 0:
            org_data.drop(
                org_data.columns[2 : 2 + num_years_to_remove], axis=1, inplace=True
            )

        # Clean Data #
        all_metrics = org_data.replace(np.nan, "", regex=True)
        headers = all_metrics.columns.tolist()
        clean_headers = []  # Change display headers to 'Rating'
        for i, x in enumerate(headers):
            if "Rating" in x:
                clean_headers.append("Rating")
            else:
                clean_headers.append(x)

        org_table = [
            dash_table.DataTable(
                org_data.to_dict("records"),
                columns=[{"name": i, "id": i} for i in org_data.columns],
                style_data={
                    "fontSize": "12px",
                    "border": "none",
                    "fontFamily": "Roboto, sans-serif",
                },
                style_data_conditional=[
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "#eeeeee",
                    },
                ]
                + [
                    {
                        "if": {
                            "filter_query": '{{{col}}} = "DNMS"'.format(col=col),
                            "column_id": col,
                        },
                        "backgroundColor": "#b44655",
                        "fontWeight": "bold",
                        "color": "white",
                        "borderBottom": "solid .5px white",
                        "borderRight": "solid .5px white",
                    }
                    for col in all_metrics.columns
                ]
                + [
                    {
                        "if": {
                            "filter_query": '{{{col}}} = "MS"'.format(col=col),
                            "column_id": col,
                        },
                        "backgroundColor": "#81b446",
                        "fontWeight": "bold",
                        "color": "white",
                        "borderBottom": "solid .5px white",
                        "borderRight": "solid .5px white",
                    }
                    for col in all_metrics.columns
                ],
                style_header={
                    "height": "20px",
                    "backgroundColor": "#ffffff",
                    "border": "none",
                    "borderBottom": ".5px solid #6783a9",
                    "fontSize": "12px",
                    "fontFamily": "Roboto, sans-serif",
                    "color": "#6783a9",
                    "textAlign": "center",
                    "fontWeight": "bold",
                },
                style_cell={
                    "whiteSpace": "normal",
                    "height": "auto",
                    "textAlign": "center",
                    "color": "#6783a9",
                    "minWidth": "25px",
                    "width": "25px",
                    "maxWidth": "25px",
                },
                style_cell_conditional=[
                    {
                        "if": {"column_id": "Standard"},
                        "textAlign": "Center",
                        "fontWeight": "500",
                        "width": "7%",
                    },
                    {
                        "if": {"column_id": "Description"},
                        "width": "50%",
                        "textAlign": "Left",
                        "fontWeight": "500",
                        "paddingLeft": "20px",
                    },
                ],
            )
        ]

    else:
        org_table = [
            dash_table.DataTable(
                columns=[
                    {"id": "emptytable", "name": "No Data to Display"},
                ],
                style_header={
                    "fontSize": "14px",
                    "border": "none",
                    "textAlign": "center",
                    "color": "#6783a9",
                    "fontFamily": "Roboto, sans-serif",
                },
            )
        ]

    defn_table_data = [
        [
            "3.1.",
            "The school materially complied with admissions and enrollment requirements based on applicable laws, rules and regulations, and all \
            relevant provisions of the charter agreement. This includes, but is not limited to: 1) Following fair and open recruitment practices; 2) \
            Not seeking or using information in ways that would have been discriminatory or otherwise contrary to law; 3) Implementing all required \
            admissions preferences and only allowable discretionary preferences; 4) Carrying out a lottery consistent with applicable rules and policies; \
            5) Compiling and utilizing waiting list consistent with applicable rules and policies; 6) Enrolling students in accordance with a lawful \
            admissions policy, lottery results, and waiting list results; and 6) Not “counseling out” students either in advance of enrollment or thereafter.",
        ],
        [
            "3.2.",
            "The school conducted suspensions and expulsions in material compliance with the school’s discipline policy, applicable laws, rules \
            and regulations, and all relevant provisions of the charter agreement. The school has promptly and effectively remedied shortcomings when identified.",
        ],
        [
            "3.3.",
            "The school consistently treated students with identified disabilities and those suspected of having a disability in accordance with \
            applicable laws, rules and regulations, and all relevant provisions of the charter agreement. This includes, but is not limited to: \
            1) Identification: It consistently complied with rules relating to identification & referral. 2) Operational Compliance: It consistently \
            complied with rules relating to the academic program, assessments, discipline, and all other aspects of the school’s program and responsibilities. \
            2) IEPs: Student Individualized Education Plans and Section 504 plans were appropriately carried out, and confidentiality was maintained. 3) \
            Accessibility: Access to the school’s facility and program was provided to students and parents in a lawful manner and consistent with their \
            abilities. 4) Funding: All applicable funding was secured and utilized in ways consistent with applicable laws, rules, regulations and provisions \
            of the school’s charter agreement.",
        ],
        [
            "3.4.",
            "The school complied with English Language Learner requirements and consistently treated ELL students in a manner consistent with all \
            applicable laws, rules and regulations, and all relevant provisions of the charter agreement. 1) Identification: The school consistently \
            and effectively implemented steps to identify students in need of ELL services. 2) Delivery of Services: Appropriate ELL services were \
            equitably provided to identified students pursuant to the school’s policy and educational program. 3) Accommodations: Students were provided \
            with appropriate accommodations on assessments. 4) Exiting: Students were exited from ELL services in accordance with their capacities. 5) \
            Monitor: The school monitors the academic progress of former ELL students for at least two years",
        ],
        [
            "3.5.",
            "The school materially complied with the laws protecting student rights, including due process protections, civil rights, Title IX, and \
            other student liberties, including First Amendment protections relating to free speech and religion.",
        ],
        [
            "3.6.",
            "The organizer materially complied with applicable laws, rules and regulations, and all relevant provisions of the charter agreement relating \
            to governance of the school by the governing board, including, but not limited to: 1) The governing board operates in compliance with its articles \
            of incorporation, by-laws, code of ethics, and conflict of interest policy; 2) The governing board meets a minimum of four (4) times a year; 3) The \
            governing board keeps minutes of all board meetings which must include, at a minimum: i) the date, time, and place of the meeting, ii) the members \
            of the governing body recorded as either present or absent, including whether the member is participating electronically, iii) the general substance \
            of all matters proposed, discussed, or decided, and iv) a record of all votes taken, by individual members if there is a roll call; 4) Board meeting \
            schedules, meeting notices, and copies of board minutes are easily accessible and available to the public on the charter school’s website; 5) The \
            governing board complies with Indiana’s Open Door and Access to Public Records laws, including providing electronic notice to ICSB of all board \
            meetings; 6) The organizer is in good legal standing with the Internal Revenue Service and the State of Indiana; 7) The organizer is in legal \
            compliance with all contractual obligations with third parties; 8) If contracting with an Educational Service Provider (ESP), the organizer is \
            functionally and structurally independent from, properly oversees, and holds accountable the ESP. Indicators of functional and structural \
            independence include but are not limited to: i) governing documents that do not tie the organizer to the ESP; ii) the governing board has \
            independent legal counsel; iii) the governing board is not appointed or controlled by the ESP; iv) the board has not improperly delegated \
            its duties and responsibilities to the ESP.",
        ],
        [
            "3.7.",
            "The school substantially met all ICSB and IDOE Reporting Requirements. For these purposes, “substantially meets” means no more than \
            three (3) reports are submitted late for a given year.",
        ],
        [
            "3.8.",
            "The school complied with applicable laws, rules and regulations, and relevant provisions of the charter agreement relating to safety \
            and security and the provision of health-related services to students and the school community, including but not limited to: 1) Fire \
            inspections and related records; 2) Maintaining a viable certificate of occupancy; 3) Maintaining student records and testing materials\
            securely; 4) Maintaining documentation of requisite insurance coverage; 5) Offering appropriate nursing services; and 6) Provision of food services.",
        ],
        [
            "3.9.",
            "The school materially complied with all other applicable laws, rules and regulations, and the provisions of the charter, including, but \
            not limited to, teacher licensure, background checks, maintaining appropriate governance and managerial procedures and financial controls, \
            and providing proper notice to ICSB as required by Section 8.4 of the Charter.",
        ],
    ]

    defn_table_keys = ["STANDARD", "REQUIREMENTS TO MEET STANDARD"]
    defn_table_dict = [dict(zip(defn_table_keys, l)) for l in defn_table_data]

    odefn_table = [
        dash_table.DataTable(
            data=defn_table_dict,
            columns=[{"name": i, "id": i} for i in defn_table_keys],
            style_data={
                "fontSize": "12px",
                "border": "none",
                "fontFamily": "Roboto, sans-serif",
            },
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "#eeeeee",
                },
            ],
            style_header={
                "height": "20px",
                "backgroundColor": "#ffffff",
                "borderBottom": ".5px solid #6783a9",
                "fontSize": "12px",
                "fontFamily": "Roboto, sans-serif",
                "color": "#6783a9",
                "textAlign": "center",
                "fontWeight": "700",
                "border": "none",
                "text-decoration": "none",
            },
            style_cell={
                "whiteSpace": "normal",
                "height": "auto",
                "textAlign": "left",
                "color": "#6783a9",
            },
            style_cell_conditional=[
                {
                    "if": {"column_id": "STANDARD"},
                    "textAlign": "Center",
                    "fontWeight": "500",
                    "width": "7%",
                },
            ],
        )
    ]

    return org_table, odefn_table


#### Layout

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
                        html.Div(
                            [
                                html.Label(
                                    "Organizational and Operational Accountability",
                                    style=label_style,
                                ),
                                html.Div(id="org-table"),
                            ],
                            className="pretty_container ten columns",
                        ),
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
                                    "Organizational and Operational Accountability Definitions",
                                    style=label_style,
                                ),
                                html.Div(id="odefn-table"),
                            ],
                            className="pretty_container ten columns",
                        ),
                    ],
                    className="bare_container twelve columns",
                )
            ],
            className="row",
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
