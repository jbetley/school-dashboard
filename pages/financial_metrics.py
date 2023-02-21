######################################
# ICSB Dashboard - Financial Metrics #
######################################
# author:   jbetley
# version:  .99.021323

import dash
from dash import html, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
import os.path
import itertools

# import subnav function
from .subnav import subnav_finance
dash.register_page(__name__, path='/financial_metrics', order=2)

# Caclulate metrics based on ICSB Accountability System financial framework
def calculateMetrics(metrics):

    # Need to handle pre-opening year data where there is financial activity
    # but school is not receiving state/federal grants. This 'easy' fix ignore
    # all columns (years) where the value in the State Grant column is equal to '0'

    # TODO: A more precise fix would be to keep all columns (including those with
    # no value in grant columns), but ignore/except any calculation that requires
    # either grant revenue and adm

    metrics = metrics.loc[:,~(metrics.iloc[1]==0)]
    
    columns = list(metrics)

    # get year headers as array of strings in descending order
    year = columns
    del year[0]

    y = len(year)

    ## Metrics ##
    currentRatio=[]
    r_currentRatio=[]
    daysCash=[]
    r_daysCash=[]
    enrollChange=[]
    r_enrollChange=[]
    primaryReserve=[]
    r_primaryReserve=[]
    chNetAssMar=[]
    r_assetMar=[]
    aggMar=[]
    r_aggMar=[]
    debtAssetRatio=[]
    r_debtAssetRatio=[]
    cashFlow=[]
    r_cashFlow=[]
    myCashFlow=[]
    r_mycashFlow=[]
    debtCoverageRatio=[]
    r_debtCoverageRatio=[]
    summary=[]

    # convert all values to integers
    for col in columns:
        metrics[col] = pd.to_numeric(metrics[col], errors='coerce')


    ## NOTE: See financial_metrics.py for formula definitions
    for col in columns:
        i = metrics.columns.get_loc(col) - 1

    ## Near Term Indicators ##

        # Current Ratio
        currentRatio.append(metrics.loc[metrics['Category'].isin(['Current Assets'])][year[i]].values[0]/metrics.loc[metrics['Category'].isin(['Current Liabilities'])][year[i]].values[0])

        if ((y - i) == 1):
            if (currentRatio[i] > 1.1):
                r_currentRatio.append("MS")
            else:
                r_currentRatio.append("DNMS")
        else:
            if (currentRatio[i] > 1.1 or (currentRatio[i] > 1 and currentRatio[i] >= (metrics.loc[metrics['Category'].isin(['Current Assets'])][year[i+1]].values[0]/metrics.loc[metrics['Category'].isin(['Current Liabilities'])][year[i+1]].values[0]))):
                r_currentRatio.append("MS")
            else:
                r_currentRatio.append("DNMS")

        # Days Cash On Hand
        daysCash.append(metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i]].values[0] / ((metrics.loc[metrics['Category'].isin(['Operating Expenses'])][year[i]].values[0] - metrics.loc[metrics['Category'].isin(['Depreciation/Amortization'])][year[i]].values[0])/365))

        if ((y - i) == 1):
            if (daysCash[i] >= 45):
                r_daysCash.append("MS")
            else:
                r_daysCash.append("DNMS")
        else:
            if (daysCash[i] >= 45 or (daysCash[i] >= 30 and daysCash[i] >= (metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+1]].values[0] / ((metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] - metrics.loc[metrics['Category'].isin(['Depreciation/Amortization'])][year[i+1]].values[0])/365)))):
                r_daysCash.append("MS")
            else:
                r_daysCash.append("DNMS")

        # Annual Enrollment Change
        if ((y - i) == 1):
            enrollChange.append(-999)
        else:
            enrollChange.append((metrics.loc[metrics['Category'].isin(['ADM Average'])][year[i]].values[0] - metrics.loc[metrics['Category'].isin(['ADM Average'])][year[i+1]].values[0]) / metrics.loc[metrics['Category'].isin(['ADM Average'])][year[i+1]].values[0])

        if ((y - i) == 1):
            r_enrollChange.append("N/A")
        else:
            if (enrollChange[i] > -0.1):
                    r_enrollChange.append("MS")
            else:
                    r_enrollChange.append("DNMS")

        # TODO: Replace Primary Reserve Ratio with a more appropriate financial metric
        # Primary Reserve Ratio
        primaryReserve.append(metrics.loc[metrics['Category'].isin(['Unrestricted Net Assets'])][year[i]].values[0] / metrics.loc[metrics['Category'].isin(['Operating Expenses'])][year[i]].values[0])

        if (primaryReserve[i] > 0.25):
            r_primaryReserve.append("MS")
        else:
            r_primaryReserve.append("DNMS")

        ## Long Term Indicators ##

        # Change in Net Assets Margin & Aggregated Three-Year Margin
        change_in_net_assets_margin = \
            metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] / \
            metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i]].values[0]

        chNetAssMar.append(change_in_net_assets_margin)
        # chNetAssMar.append(metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] / metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i]].values[0])

        if ((y - i) <= 2):
            aggMar.append(-999)
        else:
            print('first year is first:', year[i])

            aggregated_3_year_margin = \
                (metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0]) / \
                (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0])
            
            print(aggregated_3_year_margin)

            aggMar.append(aggregated_3_year_margin)
            # aggMar.append((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0]))


        if ((y - i) == 1):
            if (chNetAssMar[i] > 0):
                r_assetMar.append("MS")
                r_aggMar.append("N/A")
            else:
                r_assetMar.append("DNMS")
                r_aggMar.append("N/A")
        elif ((y - i) == 2):
            if (chNetAssMar[i] + (metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] / metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0]) > 0):
                r_assetMar.append("MS")
                r_aggMar.append("N/A")
            else:
                r_assetMar.append("DNMS")
                r_aggMar.append("N/A")
        elif ((y - i) >= 3 and ((y - i) < 4)):
            if (chNetAssMar[i] > 0 and aggMar[i] > 0):
                r_assetMar.append("MS")
                r_aggMar.append("MS")
            else:
                r_assetMar.append("DNMS")
                r_aggMar.append("DNMS")
        else:
# TODO: The calculation for Aggregated Three-Year Margin is: ATYM is positive and the most recent year Change
# in Net Assets Margin is positive; or Aggregated Three-Year Margin is greater than -1.5%, the trend is positive
# for the last two years, and Change in Net Assets Margin for the most recent year is positive.
# Question: Does 'last two years' mean the last year and the current year? or the last TWO years and the current year?
# The following commented out code assumes it means CY < PY < PY-1 - This needs FIVE total years of data
# If this is actually what we want, then uncomment this code. Comment out the following line AND
# change the previous elif from to elif ((y - i) >= 3 and ((y - i) <= 4)): (changing < 4 to <=4)
#            if ((chNetAssMar[i] > 0 and aggMar[i] > 0) or ((chNetAssMar[i] > 0 and aggMar[i] > -.015) and (aggMar[i] > ((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+3]].values[0]))) and (((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+3]].values[0])) > ((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+4]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+3]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+4]].values[0]))))):
# This code says meet standard if CHNAM > 0 and (AGMAR > -.015 AND AGMAR > AGMAR for PY) - This needs FOUR total years of data
            if ((chNetAssMar[i] > 0 and aggMar[i] > 0) or ((chNetAssMar[i] > 0 and aggMar[i] > -.015) and (aggMar[i] > ((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+3]].values[0]))))):
                r_assetMar.append("MS")
                r_aggMar.append("MS")
            else:
                r_assetMar.append("DNMS")
                r_aggMar.append("DNMS")

        # Debt to Asset Ratio
        debtAssetRatio.append(metrics.loc[metrics['Category'].isin(['Total Liabilities'])][year[i]].values[0] / metrics.loc[metrics['Category'].isin(['Total Assets'])][year[i]].values[0])

        if (debtAssetRatio[i] < 0.9):
            r_debtAssetRatio.append("MS")
        else:
            r_debtAssetRatio.append("DNMS")

        # Cash Flow
        if ((y - i) == 1):
            if (metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i]].values[0] != 0):
                cashFlow.append(metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i]].values[0])
            else:
                cashFlow.append(-999)
        else:
            cashFlow.append(metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i]].values[0] - metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+1]].values[0])

        # Multi-Year Cash Flow
        if ((y - i) <= 2):
            myCashFlow.append(-999)
        else:
            myCashFlow.append(metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i]].values[0] - metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+2]].values[0])

        if ((y - i) == 1):
            if (cashFlow[i] > 0):
                r_cashFlow.append("MS")
                r_mycashFlow.append("N/A")
            else:
                r_cashFlow.append("DNMS")
                r_mycashFlow.append("N/A")
        elif ((y - i) == 2):
            if (cashFlow[i] > 0 and (metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+1]].values[0] > 0)):
                r_cashFlow.append("MS")
                r_mycashFlow.append("N/A")
            else:
                r_cashFlow.append("DNMS")
                r_mycashFlow.append("N/A")
        elif ((y - i) == 3):
            if ((cashFlow[i] > 0 and myCashFlow[i] > 0) and (((metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+1]].values[0] - metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+2]].values[0]) > 0) + (metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+2]].values[0] > 0) >=1)):
                r_cashFlow.append("MS")
                r_mycashFlow.append("MS")
            else:
                r_cashFlow.append("DNMS")
                r_mycashFlow.append("DNMS")
        else:
            if ((cashFlow[i] > 0 and myCashFlow[i] > 0) and (((metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+1]].values[0] - metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+2]].values[0]) > 0) or ((metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+2]].values[0] - metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+3]].values[0]) > 0) > 0)):
                r_cashFlow.append("MS")
                r_mycashFlow.append("MS")
            else:
                r_cashFlow.append("DNMS")
                r_mycashFlow.append("DNMS")

        # Debt Service Coverage Ratio
        debtCoverageRatio.append((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Lease/Mortgage Payments'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Depreciation/Amortization'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Interest Expense'])][year[i]].values[0]) / (metrics.loc[metrics['Category'].isin(['Lease/Mortgage Payments'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Principal Payments'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Interest Expense'])][year[i]].values[0]))

        if (debtCoverageRatio[i] > 1):
            r_debtCoverageRatio.append("MS")
        else:
            r_debtCoverageRatio.append("DNMS")
    # End Loop #

    # Create single list for each metric and rating value
    # use itertools to alternate metric value and rating

    def alt_chain(*iters, fillvalue=None):
        return itertools.chain.from_iterable(itertools.zip_longest(*iters, fillvalue=fillvalue))

    currentRatio = list(np.around(np.array(currentRatio),2))

    m1 = list(alt_chain(currentRatio,r_currentRatio))
    m1.insert(0,'Current Ratio')

    daysCash = list(np.around(np.array(daysCash),2))
    m2 = list(alt_chain(daysCash,r_daysCash))
    m2.insert(0,'Days Cash on Hand')

    enrollChange = list(np.around(np.array(enrollChange),2))
    m3 = list(alt_chain(enrollChange,r_enrollChange))
    m3.insert(0,'Annual Enrollment Change')

    primaryReserve = list(np.around(np.array(primaryReserve),2))
    m4 = list(alt_chain(primaryReserve,r_primaryReserve))
    m4.insert(0,'Primary Reserve Ratio')

    chNetAssMar = list(np.around(np.array(chNetAssMar),2))
    m5 = list(alt_chain(chNetAssMar,r_assetMar))
    m5.insert(0,'Change in Net Assets Margin')

    aggMar = list(np.around(np.array(aggMar),2))
    m6 = list(alt_chain(aggMar,r_aggMar))
    m6.insert(0,'Aggregated Three-Year Margin')

    debtAssetRatio = list(np.around(np.array(debtAssetRatio),2))
    m7 = list(alt_chain(debtAssetRatio,r_debtAssetRatio))
    m7.insert(0,'Debt to Asset Ratio')

    cashFlow = list(np.around(np.array(cashFlow),2))
    m8 = list(alt_chain(cashFlow,r_cashFlow))
    m8.insert(0,'Cash Flow')

    myCashFlow = list(np.around(np.array(myCashFlow),2))
    m9 = list(alt_chain(myCashFlow,r_mycashFlow))
    m9.insert(0,'Multi-Year Cash Flow')

    debtCoverageRatio = list(np.around(np.array(debtCoverageRatio),2))
    m10 = list(alt_chain(debtCoverageRatio,r_debtCoverageRatio))
    m10.insert(0,'Debt Service Coverage Ratio')

    # Add "Rating" to headers (along with number to distinguish)
    rating = []
    end = y
    k=1
    for y in range(end):
        j=str(k)
        rating.append('Rating ' + j)
        k=k+1

    mcolumns = [x for x in itertools.chain.from_iterable(itertools.zip_longest(columns,rating)) if x]
    mcolumns.insert(0,'Metric')
    subhead1 = ['Near Term']
    subhead2 = ['Long Term']

    summary = pd.DataFrame([subhead1,m1,m2,m3,m4,subhead2,m5,m6,m7,m8,m9,m10],columns=mcolumns)

    return summary
## End Functions

@callback(
    Output('financial-metrics-table', 'children'),
    Output('radio-finance-metrics-content', 'children'),
    Output('radio-finance-metrics-display', 'style'),
    Output('finance-metrics-table-title', 'children'),
    Output('financial-indicators-table', 'children'),
    Output('financial-metrics-definitions-table', 'children'),
    Input('dash-session', 'data'),
    Input('year-dropdown', 'value'),
    Input(component_id='radio-button-finance-metrics', component_property='value')
)
def update_financial_metrics(data,year,radio_value):
    if not data:
         raise PreventUpdate

    empty_table = [
        dash_table.DataTable(
            columns = [
                {'id': 'emptytable', 'name': 'No Data to Display'},
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

    max_display_years = 5
    school_index = pd.DataFrame.from_dict(data['0'])

    # Displays either School or Network level financials for some pages,
    # if a school is not part of a network, no radio buttons are displayed.
    # If a school is part of a network, define and display radio button.
    # Storing the radio buttons in a variable ensures there is no flickering
    # of the component as it is drawn and then hidden - as the button variable
    # has no content until it also meets the display condition.
    if school_index['Network'].values[0] != 'None':
        if radio_value == 'network-metrics':
            radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-metrics',
                        className='btn-group',
                        inputClassName='btn-check',
                        labelClassName='btn btn-outline-primary',
                        labelCheckedClassName='active',
                        options=[
                            {'label': 'School', 'value': 'school-metrics'},
                            {'label': 'Network', 'value': 'network-metrics'},
                        ],
                        value='network-metrics',
                    ),
                ],
                className='radio-group',
            )

        else:
            radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-metrics',
                        className='btn-group',
                        inputClassName='btn-check',
                        labelClassName='btn btn-outline-primary',
                        labelCheckedClassName='active',
                        options=[
                            {'label': 'School', 'value': 'school-metrics'},
                            {'label': 'Network', 'value': 'network-metrics'},
                        ],
                        value='school-metrics',
                    ),
                ],
                className='radio-group',
            )

        display_radio = {}

    else:
        radio_content = html.Div(
                [
                    dbc.RadioItems(
                        id='radio-button-finance-metrics',
                        className='btn-group',
                        inputClassName='btn-check',
                        labelClassName='btn btn-outline-primary',
                        labelCheckedClassName='active',
                        options=[],
                        value='',
                    ),
                ],
                className='radio-group',
            )

        display_radio = {'display': 'none'}

    if radio_value == 'network-metrics':
        finance_file = "data/F-" + school_index['Network'].values[0] + ".csv"
        table_title = 'Financial Accountability Metrics (' + school_index['Network'].values[0] + ')'
    else:
        finance_file = "data/F-" + school_index['School Name'].values[0] + ".csv"
        
        # don't display school name in title if the school isn't part of a network
        if school_index['Network'].values[0] == 'None':
            table_title = 'Financial Accountability Metrics'        
        else:
            table_title = 'Financial Accountability Metrics (' + school_index['School Name'].values[0] + ')'

    if os.path.isfile(finance_file):

        financial_data = pd.read_csv(finance_file)

        most_recent_finance_year = financial_data.columns[1]
        excluded_finance_years = int(most_recent_finance_year) - int(year)

        if excluded_finance_years > 0:
            financial_data.drop(financial_data.columns[1:excluded_finance_years+1], axis=1, inplace=True)

        # financial file exists, but is empty
        if len(financial_data.columns) <= 1:
            financial_metrics_table = empty_table

        else:

            # We calculate all rows requiring a 'calculation': Total Grants'
            # (State Grants + Federal Grants), 'Net Asset Position' (Total Assets
            # - Total Liabilities), and 'Change in Net Assets' (Operating Revenues
            # - Operating Expenses)

            for col in financial_data.columns:
                financial_data[col]=pd.to_numeric(financial_data[col], errors='coerce').fillna(financial_data[col]).tolist()

            # set Category as index (so we can use .loc). This assumes that the final
            # rows already exist in the dataframe. If they do not, then need to use the
            # following pattern:
            # new_row = financial_data.loc['State Grants'] + financial_data.loc['Federal Grants']
            # new_row.name = 'Total Grants'
            # financial_data.append([new_row])

            financial_data = financial_data.set_index(['Category'])
            financial_data.loc['Total Grants'] = financial_data.loc['State Grants'] + financial_data.loc['Federal Grants']
            financial_data.loc['Net Asset Position'] = financial_data.loc['Total Assets'] - financial_data.loc['Total Liabilities']
            financial_data.loc['Change in Net Assets'] = financial_data.loc['Operating Revenues'] - financial_data.loc['Operating Expenses']        

            # reset index, which shifts Category back to column one
            financial_data = financial_data.reset_index()

            # Ensure that only the 'max_display_years' number of years (currently 5)
            # worth of financial data is displayed (add +1 to max_display_years to
            # account for the category column). To show all years of data, comment out this line.
            financial_data = financial_data.iloc[: , :(max_display_years+1)]

            years = financial_data.columns.tolist()
            years.pop(0)
            years.reverse()

            # remove audit and other indicator data (it is displayed on the financial metrics page)
            financial_values = financial_data.drop(financial_data.index[41:])

            # School ADM is calculated from actual count day numbers, Network ADM is
            # manually calculated in the Network's finance file - so skip this process for Networks
            if radio_value == 'school-metrics':
                school_adm = school_index.filter(regex = r'September ADM|February ADM',axis=1).copy()

                for col in school_adm.columns:
                    school_adm[col]=pd.to_numeric(school_adm[col], errors='coerce')

                # filter each month by header, reverse order, and match years to financial information df
                sept = school_adm.loc[:, school_adm.columns.str.contains('September')]
                sept = sept[sept.columns[::-1]] 
                sept = sept.iloc[: , :(len(financial_values.columns) - 1)] 

                feb = school_adm.loc[:, school_adm.columns.str.contains('February')]
                feb = feb[feb.columns[::-1]]
                feb = feb.iloc[: , :(len(financial_values.columns) - 1)]
                
                # create a list of the averages of the two months for each year
                sept_val = sept.values.flatten().tolist()
                feb_val = feb.values.flatten().tolist()
                adm_avg = [(g + h) / 2 for g, h in zip(sept_val, feb_val)]
                adm_avg.insert(0, 'ADM Average')

                # insert values into financial information datafarame
                sept.insert(loc=0, column='Category', value = 'September Count')
                financial_values.loc[financial_values['Category'] == 'September Count'] = [sept.values.flatten().tolist()]
                feb.insert(loc=0, column='Category', value = 'February Count')
                financial_values.loc[financial_values['Category'] == 'February Count'] = [feb.values.flatten().tolist()]
                financial_values.loc[financial_values['Category'] == 'ADM Average'] = [adm_avg]

            # Release The Hounds!
            financial_metrics = calculateMetrics(financial_values)

            # In calculations we distinguish 'numerical zero' from 'no data' using -999
            # need to replace -999 with blank
            financial_metrics = financial_metrics.replace(-999, '',regex=True)

            # Force correct format for display of df in datatable
            for x in range(1,len(financial_metrics.columns),2):
                if financial_metrics.iat[3,x]:
                    financial_metrics.iat[3,x] = '{:.0%}'.format(financial_metrics.iat[3,x])
                if financial_metrics.iat[9,x]:
                    financial_metrics.iat[9,x] = '{:,.2f}'.format(financial_metrics.iat[9,x])
                if financial_metrics.iat[10,x]:
                    financial_metrics.iat[10,x] = '{:,.2f}'.format(financial_metrics.iat[10,x])
        
            headers = financial_metrics.columns.tolist()

            clean_headers = []
            for i, x in enumerate (headers):
                if 'Rating' in x:
                    clean_headers.append('Rating')
                else:
                    clean_headers.append(x)

            # The ratios are shown on the Financial Analysis page
            remove_categories = ['Other Metrics', 'Instruction Ratio','Human Capitol Ratio','Occupancy Ratio']

            financial_metrics = financial_metrics[~financial_metrics['Metric'].isin(remove_categories)]

            financial_metrics_table = [
                            dash_table.DataTable(
                            financial_metrics.to_dict('records'),
                            columns=[{
                                'name': col,
                                'id': headers[idx]
                                } for (idx, col) in enumerate(clean_headers)],
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
                                {
                                    'if': {
                                        'filter_query': "{Metric} eq 'Near Term' || {Metric} eq 'Long Term' || {Metric} eq 'Other Metrics'"
                                    },
                                    'paddingLeft': '10px',
                                    'text-decoration': 'underline',
                                    'fontWeight': 'bold'
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
                                } for col in financial_metrics.columns
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
                                } for col in financial_metrics.columns
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
                                'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                            },
                            style_cell_conditional=[
                                {
                                    'if': {
                                        'column_id': 'Metric'
                                    },
                                    'textAlign': 'left',
                                    'fontWeight': '500',
                                    'paddingLeft': '20px',
                                    'width': '20%'
                                },
                                {
                                    'if': {
                                        'column_id': ['Rating 1','Rating 2','Rating 3','Rating 4','Rating 5']
                                    },
                                    'width': '6%'
                                },
                            ],
                            style_as_list_view=True
                        )
            ]

        # Financial Indicators
        financial_indicators = financial_data[financial_data['Category'].str.startswith('2.1.')].copy()
        
        # Display an empty table if financial indicators has fewer than 2 columns
        # (Category + Year)
        if len(financial_indicators.columns) <= 1 or financial_indicators.empty:    
            financial_indicators_table = empty_table

        else:
            financial_indicators[['Standard','Description']] = financial_indicators['Category'].str.split('|', expand=True).copy()

            # reorder and clean up dataframe
            financial_indicators = financial_indicators.drop('Category', axis=1)
            standard = financial_indicators['Standard']
            description = financial_indicators['Description']
            financial_indicators = financial_indicators.drop(columns=['Standard','Description'])
            financial_indicators.insert(loc=0, column='Description', value = description)
            financial_indicators.insert(loc=0, column='Standard', value = standard)

            financial_indicators_table = [
                        dash_table.DataTable(
                        financial_indicators.to_dict('records'),
                        columns = [{'name': i, 'id': i} for i in financial_indicators.columns],
                        style_data={
                            'fontSize': '12px',
                            'fontFamily': 'Roboto, sans-serif',
                            'border': 'none'
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
                            } for col in financial_indicators.columns
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
                                'position': 'relative',
                                'borderBottom': 'solid 1px white',
                                'borderRight': 'solid 1px white',
                            } for col in financial_indicators.columns
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
                            'minWidth': '25px', 'width': '25px', 'maxWidth': '25px'
                        },
                        style_cell_conditional=[
                            {
                                'if': {
                                    'column_id': 'Standard'
                                },
                                'textAlign': 'center',
                                'fontWeight': '500',
                                'width': '7%'
                            },
                            {
                                'if': {
                                    'column_id': 'Description'
                                },
                                'width': '45%',
                                'textAlign': 'Left',
                                'fontWeight': '500',
                                'paddingLeft': '20px',
                            },
                        ],
                    )
            ]

    else:
        financial_metrics_table = empty_table
        financial_indicators_table = empty_table

# TODO: Possibly make this table easier to read either through Markdown or embedded images
# (neither works currently with dash 2.6 datatables)
# http://www.latex2png.com/
# https://stackoverflow.com/questions/70205486/clickable-hyperlinks-in-plotly-dash-datatable
# https://stackoverflow.com/questions/66583063/how-to-add-hyperlink-in-column-field-of-dash-datatable

    financial_metrics_definitions_data = [
        ['Current Ratio = Current Assets ÷ Current Liabilities','Current Ratio is greater than 1.1; or is between 1.0 and 1.1 and the one-year trend is not negative.'],
        ['Days Cash on Hand = Unrestricted Cash ÷ ((Operating Expenses - Depreciation Expense) ÷ 365)','School has greater than 45 unrestricted days cash; or between 30 - 45 unrestricted days cash and the one-year trend is not negative.'],
        ['Annual Enrollment Change = (Current Year ADM - Previous Year ADM) ÷ Previous Year ADM','Annual Enrollment Change increases or shows a current year decrease of less than 10%.'],
        ['Primary Reserve Ratio = Unrestricted Net Assets ÷ Operating Expenses','Primary Reserve Ratio is greater than .25.'],
        ['Change in Net Assets Margin = (Operating Revenues - Operating Expenses) ÷ Operating Revenues ; Aggregated 3-Year Margin = (3 Year Operating Revenues - 3 Year Operating Expense) ÷ 3 Year Operating Revenues','Aggregated Three-Year Margin is positive and the most recent year Change in Net Assets Margin is positive; or Aggregated Three-Year Margin is greater than -1.5%, the trend is positive for the last two years, and Change in Net Assets Margin for the most recent year is positive. For schools in their first and second year of operation, the cumulative Change in Net Assets Margin must be positive.'],
        ['Debt to Asset Ratio = Total Liabilities ÷ Total Assets','Debt to Asset Ratio is less than 0.9.'],
        ['One Year Cash Flow = Recent Year Total Cash - Previous Year Total Cash; Multi-Year Cash Flow = Recent Year Total Cash - Two Years Previous Total Cash','Multi-Year Cash Flow is positive and One Year Cash Flow is positive in two out of three years, including the most recent year. For schools in the first two years of operation, both years must have a positive Cash Flow (for purposes of calculating Cash Flow, the school\'s Year 0 balance is assumed to be zero).'],
        ['Debt Service Coverage Ratio = (Change in Net Assets + Depreciation/Amortization Expense + Interest Expense + Rent/Lease Expense) ÷ (Principal Payments + Interest Expense + Rent/Lease Expense)','Debt Service Coverage Ratio is greater than or equal to 1.0.']
    ]

    financial_metrics_definitions_keys = ['Calculation','Requirement to Meet Standard']
    financial_metrics_definitions_dict = [dict(zip(financial_metrics_definitions_keys, l)) for l in financial_metrics_definitions_data ]

    financial_metrics_definitions_table = [
            dash_table.DataTable(
                data = financial_metrics_definitions_dict,
                columns = [{'name': i, 'id': i, 'presentation': 'markdown'} for i in financial_metrics_definitions_keys],
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
                    {   # Kludge to ensure first col header has border
                        'if': {
                            'row_index': 0,
                            'column_id': 'Calculation'
                        },
                        'borderTop': '.75px solid rgb(103,131,169)'
                    },
                ],
                style_header={
                    'backgroundColor': '#ffffff',
                    'fontSize': '12px',
                    'fontFamily': 'Roboto, sans-serif',
                    'color': '#6783a9',
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'text-decoration': 'none',
                    'borderBottom': '.75px solid rgb(103,131,169)'                    
                },
                style_cell={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'textAlign': 'left',
                    'color': '#6783a9',
                },
                style_cell_conditional=[
                    {
                        'if': {
                            'column_id': 'Calculation'
                        },
                        'width': '50%',
                        'fontWeight': 'bold'
                    },
                ],
                style_as_list_view=True
            )
    ]

    return financial_metrics_table, radio_content, display_radio, table_title, financial_indicators_table, financial_metrics_definitions_table

## Layout
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

def layout():
    return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(subnav_finance(),className='tabs'),
                            ],
                            className='bare_container twelve columns'
                        ),
                    ],
                    className='row'
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label(id='finance-metrics-table-title', style=label_style),
                                        html.Div(
                                            [
                                            html.Div(
                                                [
                                                    html.Div(id='radio-finance-metrics-content', children=[]),
                                                ],
                                                id = 'radio-button-finance-metrics',
                                                ),
                                            ],
                                            id = 'radio-finance-metrics-display',
                                        ),
                                        html.Div(id='financial-metrics-table')
                                    ],
                                    className = 'pretty_container ten columns',
                                ),
                            ],
                            className = 'bare_container twelve columns',
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
                                        html.Label('Other Financial Accountability Indicators', style=label_style),
                                        html.Div(id='financial-indicators-table')
                                    ],
                                    className = 'pretty_container ten columns',
                                ),
                            ],
                            className = 'bare_container twelve columns',
                        ),
                    ],
                    className = 'row pagebreak',
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label('Accountability Metrics Definitions & Requirements', style=label_style),
                                        html.Div(id='financial-metrics-definitions-table')
                                    ],
                                    className = 'pretty_container ten columns'
                                ),
                            ],
                            className = 'bare_container twelve columns',
                        ),
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