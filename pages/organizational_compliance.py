##############################################
# ICSB Dashboard - Organizational Compliance #
##############################################
# author:   jbetley
# version:  .99.021323

import dash
from dash import html, dash_table, Input, Output, callback
from dash.exceptions import PreventUpdate
import os.path
import pandas as pd

dash.register_page(__name__, top_nav=True, order=7)

@callback(
    Output('org-compliance-table', 'children'),
    Output('org-compliance-definitions-table', 'children'),
    Input('dash-session', 'data'),
    Input('year-dropdown', 'value')
)
def update_about_page(data, year):
    if not data:
        raise PreventUpdate

    school_index = pd.DataFrame.from_dict(data['0'])

    empty_table = [
        dash_table.DataTable(
            columns = [
                {'id': 'emptytable', 'name': 'No Data Available'},
            ],
            style_header={
                'fontSize': '16px',
                'border': 'none',
                'backgroundColor': '#ffffff',
                'paddingTop': '15px',                    
                'verticalAlign': 'center',
                'textAlign': 'center',
                'color': '#6783a9',
                'fontFamily': 'Roboto, sans-serif',
            },
        )
    ]

    finance_file = 'data\F-' + school_index['School Name'].values[0] + '.csv'

    if os.path.isfile(finance_file):

        school_finance = pd.read_csv(finance_file)

        most_recent_finance_year = school_finance.columns[1]
        excluded_finance_years = int(most_recent_finance_year) - int(year)

        if excluded_finance_years > 0:
            school_finance.drop(school_finance.columns[1:excluded_finance_years+1], axis=1, inplace=True)

        # if a school doesn't have data for the selected year, df will only have 1 column (Category)
        if len(school_finance.columns) <= 1:
            org_compliance_table = empty_table

        else:
            organizational_indicators = school_finance[school_finance['Category'].str.startswith('3.')].copy()
            organizational_indicators[['Standard','Description']] = organizational_indicators['Category'].str.split('|', expand=True)

            # reorder and clean up dataframe
            organizational_indicators = organizational_indicators.drop('Category', axis=1)
            standard = organizational_indicators['Standard']
            description = organizational_indicators['Description']
            organizational_indicators = organizational_indicators.drop(columns=['Standard','Description'])
            organizational_indicators.insert(loc=0, column='Description', value = description)
            organizational_indicators.insert(loc=0, column='Standard', value = standard)

            org_compliance_table = [
                        dash_table.DataTable(
                            organizational_indicators.to_dict('records'),
                            columns = [{'name': i, 'id': i} for i in organizational_indicators.columns],
                            style_data={
                                'fontSize': '12px',
                                'border': 'none',
                                'fontFamily': 'Roboto, sans-serif',
                            },
                            style_data_conditional=
                            [                                            
                                {
                                    'if': {
                                        'row_index': 'odd'
                                    },
                                    'backgroundColor': '#eeeeee',
                                },
                            ] +
                            [
                                {
                                    'if': {
                                        'filter_query': "{{{col}}} = 'DNMS'".format(col=col),
                                        'column_id': col
                                    },
                                    'backgroundColor': '#b44655',
                                    'fontWeight': 'bold',
                                    'color': 'white',
                                    'borderBottom': 'solid 1px white',
                                    'borderRight': 'solid 1px white',
                                } for col in organizational_indicators.columns
                            ] +
                            [
                                {
                                    'if': {
                                        'filter_query': "{{{col}}} = 'MS'".format(col=col),
                                        'column_id': col
                                    },
                                    'backgroundColor': '#81b446',
                                    'fontWeight': 'bold',
                                    'color': 'white',
                                    'borderBottom': 'solid 1px white',
                                    'borderRight': 'solid 1px white',
                                } for col in organizational_indicators.columns
                            ],
                            style_header={
                                'height': '20px',
                                'backgroundColor': '#ffffff',
                                'border': 'none',
                                'borderBottom': '.5px solid #6783a9',
                                'fontSize': '12px',
                                'fontFamily': 'Roboto, sans-serif',
                                'color': '#6783a9',
                                'textAlign': 'center',
                                'fontWeight': 'bold'
                            },
                            style_cell={
                                'whiteSpace': 'normal',
                                'height': 'auto',
                                'textAlign': 'center',
                                'color': '#6783a9',
                                'minWidth': '25px', 'width': '25px', 'maxWidth': '25px',
                            },
                            style_cell_conditional=[
                                {
                                    'if': {'column_id': 'Standard'},
                                        'textAlign': 'Center',
                                        'fontWeight': '500',
                                        'width': '7%'
                                },
                                {   
                                    'if': {'column_id': 'Description'},
                                        'width': '50%',
                                        'textAlign': 'Left',
                                        'fontWeight': '500',
                                },
                            ],
                        )
            ]

    else:
        org_compliance_table = empty_table
    
    org_compliance_definitions_data = [
        ['3.1.','The school materially complied with admissions and enrollment requirements based on applicable laws, rules and regulations, and all \
            relevant provisions of the charter agreement. This includes, but is not limited to: 1) Following fair and open recruitment practices; 2) \
            Not seeking or using information in ways that would have been discriminatory or otherwise contrary to law; 3) Implementing all required \
            admissions preferences and only allowable discretionary preferences; 4) Carrying out a lottery consistent with applicable rules and policies; \
            5) Compiling and utilizing waiting list consistent with applicable rules and policies; 6) Enrolling students in accordance with a lawful \
            admissions policy, lottery results, and waiting list results; and 6) Not “counseling out” students either in advance of enrollment or thereafter.'],
        ['3.2.','The school conducted suspensions and expulsions in material compliance with the school’s discipline policy, applicable laws, rules \
            and regulations, and all relevant provisions of the charter agreement. The school has promptly and effectively remedied shortcomings when identified.'],
        ['3.3.','The school consistently treated students with identified disabilities and those suspected of having a disability in accordance with \
            applicable laws, rules and regulations, and all relevant provisions of the charter agreement. This includes, but is not limited to: \
            1) Identification: It consistently complied with rules relating to identification & referral. 2) Operational Compliance: It consistently \
            complied with rules relating to the academic program, assessments, discipline, and all other aspects of the school’s program and responsibilities. \
            2) IEPs: Student Individualized Education Plans and Section 504 plans were appropriately carried out, and confidentiality was maintained. 3) \
            Accessibility: Access to the school’s facility and program was provided to students and parents in a lawful manner and consistent with their \
            abilities. 4) Funding: All applicable funding was secured and utilized in ways consistent with applicable laws, rules, regulations and provisions \
            of the school’s charter agreement.'],
        ['3.4.','The school complied with English Language Learner requirements and consistently treated ELL students in a manner consistent with all \
            applicable laws, rules and regulations, and all relevant provisions of the charter agreement. 1) Identification: The school consistently \
            and effectively implemented steps to identify students in need of ELL services. 2) Delivery of Services: Appropriate ELL services were \
            equitably provided to identified students pursuant to the school’s policy and educational program. 3) Accommodations: Students were provided \
            with appropriate accommodations on assessments. 4) Exiting: Students were exited from ELL services in accordance with their capacities. 5) \
            Monitor: The school monitors the academic progress of former ELL students for at least two years'],
        ['3.5.','The school materially complied with the laws protecting student rights, including due process protections, civil rights, Title IX, and \
            other student liberties, including First Amendment protections relating to free speech and religion.'],
        ['3.6.','The organizer materially complied with applicable laws, rules and regulations, and all relevant provisions of the charter agreement relating \
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
            its duties and responsibilities to the ESP.'],
        ['3.7.','The school substantially met all ICSB and IDOE Reporting Requirements. For these purposes, “substantially meets” means no more than \
            three (3) reports are submitted late for a given year.'],
        ['3.8.','The school complied with applicable laws, rules and regulations, and relevant provisions of the charter agreement relating to safety \
            and security and the provision of health-related services to students and the school community, including but not limited to: 1) Fire \
            inspections and related records; 2) Maintaining a viable certificate of occupancy; 3) Maintaining student records and testing materials\
            securely; 4) Maintaining documentation of requisite insurance coverage; 5) Offering appropriate nursing services; and 6) Provision of food services.'],
        ['3.9.','The school materially complied with all other applicable laws, rules and regulations, and the provisions of the charter, including, but \
            not limited to, teacher licensure, background checks, maintaining appropriate governance and managerial procedures and financial controls, \
            and providing proper notice to ICSB as required by Section 8.4 of the Charter.']
    ]

    org_compliance_definitions_table_keys = ['Standard','Requirement to Meet Standard']
    org_compliance_definitions_table_dict= [dict(zip(org_compliance_definitions_table_keys, l)) for l in org_compliance_definitions_data]

    org_compliance_definitions_table = [
                    dash_table.DataTable(
                        data = org_compliance_definitions_table_dict,
                        columns = [{'name': i, 'id': i} for i in org_compliance_definitions_table_keys],
                        style_data={
                            'fontSize': '12px',
                            'border': 'none',
                            'fontFamily': 'Roboto, sans-serif',
                        },
                        style_data_conditional=[
                            {
                                'if': {
                                    'row_index': 'odd'
                                },
                                'backgroundColor': '#eeeeee',
                            },
                            {   # NOTE: Kludget to ensure first col header has border
                                'if': {
                                    'row_index': 0,
                                    'column_id': 'Standard'
                                },
                                'borderTop': '.5px solid #6783a9'
                            },
                        ],
                        style_header={
                            'height': '20px',
                            'backgroundColor': '#ffffff',
                            'border': 'none',
                            'borderBottom': '.5px solid #6783a9',
                            'fontSize': '12px',
                            'fontFamily': 'Roboto, sans-serif',
                            'color': '#6783a9',
                            'textAlign': 'center',
                            'fontWeight': 'bold'
                        },
                        style_cell={
                            'whiteSpace': 'normal',
                            'height': 'auto',
                            'textAlign': 'left',
                            'color': '#6783a9',
                            'minWidth': '25px', 'width': '25px', 'maxWidth': '25px',
                        },
                        style_cell_conditional=[
                            {
                                'if': {
                                    'column_id': 'Standard'
                                },
                                    'textAlign': 'Center',
                                    'fontWeight': '500',
                                    'width': '7%',
                            },
                        ],
                    )
                ]

    return org_compliance_table, org_compliance_definitions_table

#### Layout

label_style = {
    'height': '20px',
    'backgroundColor': '#6783a9',
    'fontSize': '12px',
    'fontFamily': 'Roboto, sans-serif',
    'color': '#ffffff',
    'textAlign': 'center',
    'fontWeight': 'bold',
    'paddingBottom': '5px',
    'paddingTop': '5px'
}

layout = html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label('Organizational and Operational Accountability', style=label_style),
                                            html.Div(id='org-compliance-table')

                                        ],
                                        className = 'pretty_container ten columns',
                                    ),
                                ],
                                className = 'bare_container twelve columns'
                            ),
                        ],
                        className = 'row',
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                        html.Label('Organizational and Operational Accountability Definitions', style=label_style),
                                        html.Div(id='org-compliance-definitions-table')
                                        ],
                                        className = 'pretty_container ten columns'
                                    ),
                                ],
                                className = 'bare_container twelve columns',
                            )
                        ],
                        className = 'row'
                    ),
            ],
            id='mainContainer',
            style={
                'display': 'flex',
                'flexDirection': 'column'
            }
        )