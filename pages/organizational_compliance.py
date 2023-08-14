##############################################
# ICSB Dashboard - Organizational Compliance #
##############################################
# version:  1.09
# date:     08/14/23

import dash
from dash import html, dash_table, Input, Output, callback
from dash.exceptions import PreventUpdate

from .load_data import get_financial_data
from .table_helpers import no_data_table, create_proficiency_key
from .string_helpers import convert_to_svg_circle

dash.register_page(__name__, top_nav=True, order=7)

@callback(
    Output("org-compliance-table", "children"),
    Output("org-compliance-definitions-table", "children"),
    Input("charter-dropdown", "value"),
    Input("year-dropdown", "value"),
)
def update_organizational_compliance(school, year):
    if not school:
        raise PreventUpdate

    selected_year_numeric = int(year)

    # get organizational comliance data from financial data and clean-up
    financial_data = get_financial_data(school)

    if (len(financial_data.columns) <= 1 or financial_data.empty):

        org_compliance_table = no_data_table("Organizational and Operational Accountability")    

    else:

        financial_data = financial_data.drop(["School ID","School Name"], axis=1)
        financial_data = financial_data.dropna(axis=1, how="all")

        # Drop partial years
        if "Q" in financial_data.columns[1]:
            financial_data = financial_data.drop(financial_data.columns[[1]],axis = 1)

        available_years = financial_data.columns.difference(['Category'], sort=False).tolist()
        available_years = [int(c[:4]) for c in available_years]
        most_recent_finance_year = max(available_years)

        years_to_exclude = most_recent_finance_year - selected_year_numeric

        if selected_year_numeric < most_recent_finance_year:
            financial_data.drop(financial_data.columns[1:(years_to_exclude+1)], axis=1, inplace=True)

        if len(financial_data.columns) > 1:

            organizational_indicators = financial_data[financial_data["Category"].str.startswith("3.")].copy()
            organizational_indicators[["Standard","Description"]] = organizational_indicators["Category"].str.split("|", expand=True)

            # reorder and clean up dataframe
            organizational_indicators = organizational_indicators.drop("Category", axis=1)
            standard = organizational_indicators["Standard"]
            description = organizational_indicators["Description"]
            organizational_indicators = organizational_indicators.drop(columns=["Standard","Description"])
            organizational_indicators.insert(loc=0, column="Description", value = description)
            organizational_indicators.insert(loc=0, column="Standard", value = standard)

            # convert ratings to colored circles
            organizational_indicators = convert_to_svg_circle(organizational_indicators)

            headers = organizational_indicators.columns.tolist()
            year_headers = [x for x in headers if "Description" not in x and "Standard" not in x]

            # Only want Year headers to be treated as markdown (ensures that svg circles are
            # formatted correctly in each cell). See ".cell-markdown > p" in stylesheet.css)
            org_compliance_table = [
                        dash_table.DataTable(
                            organizational_indicators.to_dict("records"),
                                columns=[
                                    {"name": i, "id": i, "presentation": "markdown"}
                                    if i in year_headers
                                    else {"name": i, "id": i,
                                }
                                for i in headers
                            ],
                            style_data={
                                "fontSize": "12px",
                                "border": "none",
                                "fontFamily": "Jost, sans-serif",
                            },
                            style_data_conditional=
                            [
                                {
                                    "if": {
                                        "row_index": "odd"
                                    },
                                    "backgroundColor": "#eeeeee",
                                }
                            ] + [
                                {
                                    "if": {
                                        "state": "selected"
                                    },
                                    "backgroundColor": "rgba(112,128,144, .3)",
                                    "border": "thin solid silver"
                                }      
                            ] + [
                                {
                                    "if": {
                                        "column_id": year
                                    },
                                    "textAlign": "center",
                                    "fontWeight": "500",
                                    "width": "5%",
                                } for year in year_headers
                            ],
                            style_header={
                                "height": "20px",
                                "backgroundColor": "#ffffff",
                                "border": "none",
                                "borderBottom": ".5px solid #6783a9",
                                "fontSize": "12px",
                                "fontFamily": "Jost, sans-serif",
                                "color": "#6783a9",
                                "textAlign": "center",
                                "fontWeight": "bold"
                            },
                            style_cell={
                                "whiteSpace": "normal",
                                "height": "auto",
                                "textAlign": "center",
                                "color": "#6783a9",
                                "minWidth": "25px", "width": "25px", "maxWidth": "25px",
                            },
                            style_cell_conditional=[
                                {
                                    "if": {"column_id": "Standard"},
                                        "textAlign": "Center",
                                        "fontWeight": "500",
                                        "width": "7%"
                                },
                                {   
                                    "if": {"column_id": "Description"},
                                        "width": "50%",
                                        "textAlign": "Left",
                                        "fontWeight": "500",
                                },
                            ],
                            markdown_options={"html": True},
                        )
            ]
    
    org_compliance_definitions_data = [
        ["3.1.","The school materially complied with admissions and enrollment requirements based on applicable laws, rules and regulations, and all \
            relevant provisions of the charter agreement. This includes, but is not limited to: 1) Following fair and open recruitment practices; 2) \
            Not seeking or using information in ways that would have been discriminatory or otherwise contrary to law; 3) Implementing all required \
            admissions preferences and only allowable discretionary preferences; 4) Carrying out a lottery consistent with applicable rules and policies; \
            5) Compiling and utilizing waiting list consistent with applicable rules and policies; 6) Enrolling students in accordance with a lawful \
            admissions policy, lottery results, and waiting list results; and 6) Not “counseling out” students either in advance of enrollment or thereafter."],
        ["3.2.","The school conducted suspensions and expulsions in material compliance with the school's discipline policy, applicable laws, rules \
            and regulations, and all relevant provisions of the charter agreement. The school has promptly and effectively remedied shortcomings when identified."],
        ["3.3.","The school consistently treated students with identified disabilities and those suspected of having a disability in accordance with \
            applicable laws, rules and regulations, and all relevant provisions of the charter agreement. This includes, but is not limited to: \
            1) Identification: It consistently complied with rules relating to identification & referral. 2) Operational Compliance: It consistently \
            complied with rules relating to the academic program, assessments, discipline, and all other aspects of the school's program and responsibilities. \
            2) IEPs: Student Individualized Education Plans and Section 504 plans were appropriately carried out, and confidentiality was maintained. 3) \
            Accessibility: Access to the school's facility and program was provided to students and parents in a lawful manner and consistent with their \
            abilities. 4) Funding: All applicable funding was secured and utilized in ways consistent with applicable laws, rules, regulations and provisions \
            of the school's charter agreement."],
        ["3.4.","The school complied with English Language Learner requirements and consistently treated ELL students in a manner consistent with all \
            applicable laws, rules and regulations, and all relevant provisions of the charter agreement. 1) Identification: The school consistently \
            and effectively implemented steps to identify students in need of ELL services. 2) Delivery of Services: Appropriate ELL services were \
            equitably provided to identified students pursuant to the school's policy and educational program. 3) Accommodations: Students were provided \
            with appropriate accommodations on assessments. 4) Exiting: Students were exited from ELL services in accordance with their capacities. 5) \
            Monitor: The school monitors the academic progress of former ELL students for at least two years"],
        ["3.5.","The school materially complied with the laws protecting student rights, including due process protections, civil rights, Title IX, and \
            other student liberties, including First Amendment protections relating to free speech and religion."],
        ["3.6.","The organizer materially complied with applicable laws, rules and regulations, and all relevant provisions of the charter agreement relating \
            to governance of the school by the governing board, including, but not limited to: 1) The governing board operates in compliance with its articles \
            of incorporation, by-laws, code of ethics, and conflict of interest policy; 2) The governing board meets a minimum of four (4) times a year; 3) The \
            governing board keeps minutes of all board meetings which must include, at a minimum: i) the date, time, and place of the meeting, ii) the members \
            of the governing body recorded as either present or absent, including whether the member is participating electronically, iii) the general substance \
            of all matters proposed, discussed, or decided, and iv) a record of all votes taken, by individual members if there is a roll call; 4) Board meeting \
            schedules, meeting notices, and copies of board minutes are easily accessible and available to the public on the charter school's website; 5) The \
            governing board complies with Indiana's Open Door and Access to Public Records laws, including providing electronic notice to ICSB of all board \
            meetings; 6) The organizer is in good legal standing with the Internal Revenue Service and the State of Indiana; 7) The organizer is in legal \
            compliance with all contractual obligations with third parties; 8) If contracting with an Educational Service Provider (ESP), the organizer is \
            functionally and structurally independent from, properly oversees, and holds accountable the ESP. Indicators of functional and structural \
            independence include but are not limited to: i) governing documents that do not tie the organizer to the ESP; ii) the governing board has \
            independent legal counsel; iii) the governing board is not appointed or controlled by the ESP; iv) the board has not improperly delegated \
            its duties and responsibilities to the ESP."],
        ["3.7.","The school substantially met all ICSB and IDOE Reporting Requirements. For these purposes, “substantially meets” means no more than \
            three (3) reports are submitted late for a given year."],
        ["3.8.","The school complied with applicable laws, rules and regulations, and relevant provisions of the charter agreement relating to safety \
            and security and the provision of health-related services to students and the school community, including but not limited to: 1) Fire \
            inspections and related records; 2) Maintaining a viable certificate of occupancy; 3) Maintaining student records and testing materials\
            securely; 4) Maintaining documentation of requisite insurance coverage; 5) Offering appropriate nursing services; and 6) Provision of food services."],
        ["3.9.","The school materially complied with all other applicable laws, rules and regulations, and the provisions of the charter, including, but \
            not limited to, teacher licensure, background checks, maintaining appropriate governance and managerial procedures and financial controls, \
            and providing proper notice to ICSB as required by Section 8.4 of the Charter."]
    ]

    org_compliance_definitions_table_keys = ["Standard","Requirement to Meet Standard"]
    org_compliance_definitions_table_dict= [dict(zip(org_compliance_definitions_table_keys, l)) for l in org_compliance_definitions_data]

    org_compliance_definitions_table = [
        dash_table.DataTable(
            data = org_compliance_definitions_table_dict,
            columns = [{"name": i, "id": i} for i in org_compliance_definitions_table_keys],
            style_data={
                "fontSize": "12px",
                "border": "none",
                "fontFamily": "Jost, sans-serif",
            },
            style_data_conditional=[
                {
                    "if": {
                        "row_index": "odd"
                    },
                    "backgroundColor": "#eeeeee",
                },
                {
                    "if": {
                        "row_index": 0,
                        "column_id": "Standard"
                    },
                    "borderTop": ".5px solid #6783a9"
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
                "height": "20px",
                "backgroundColor": "#ffffff",
                "border": "none",
                "borderBottom": ".5px solid #6783a9",
                "fontSize": "12px",
                "fontFamily": "Jost, sans-serif",
                "color": "#6783a9",
                "textAlign": "center",
                "fontWeight": "bold"
            },
            style_cell={
                "whiteSpace": "normal",
                "height": "auto",
                "textAlign": "left",
                "color": "#6783a9",
                "minWidth": "25px", "width": "25px", "maxWidth": "25px",
            },
            style_cell_conditional=[
                {
                    "if": {
                        "column_id": "Standard"
                    },
                        "textAlign": "Center",
                        "fontWeight": "500",
                        "width": "7%",
                },
            ],
        )
    ]

    return org_compliance_table, org_compliance_definitions_table

layout = html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label("Key", className = "header_label"),
                                            html.Div(create_proficiency_key()),
                                        ],
                                        className = "pretty_container six columns"
                                    ),
                                ],
                                className = "bare_container_center twelve columns"
                            ),
                        ],
                        className = "row",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label("Organizational and Operational Accountability", className = "header_label"),
                                            html.Div(id="org-compliance-table")

                                        ],
                                        className = "pretty_container ten columns",
                                    ),
                                ],
                                className = "bare_container_center twelve columns"
                            ),
                        ],
                        className = "row",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                        html.Label("Organizational and Operational Accountability Definitions", className = "header_label"),
                                        html.Div(id="org-compliance-definitions-table")
                                        ],
                                        className = "pretty_container ten columns"
                                    ),
                                ],
                                className = "bare_container_center twelve columns",
                            )
                        ],
                        className = "row"
                    ),
            ],
            id="mainContainer"
        )