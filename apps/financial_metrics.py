#####################
# Financial Metrics #
#####################
# author:   jbetley
# rev:     08.22.22

from dash import html, dash_table, Input, Output
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
import itertools

from app import app
# np.warnings.filterwarnings('ignore')

## Caclulates Metrics Based on ICSB Accountability System Financial Framework ##
def calculateMetrics(metrics):

    columns = list(metrics)

    # get year headers as array of strings in descending order -> 2021, 2020, 2019, etc.
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
    occupancyRatio=[]
    humanRatio=[]
    instructionRatio=[]
    summary=[]

    # convert all values to integers
    for col in columns:
        metrics[col] = pd.to_numeric(metrics[col], errors='coerce')

    # Loop through each column
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
        daysCash.append(metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i]].values[0] / ((metrics.loc[metrics['Category'].isin(['Operating Expenses'])][year[i]].values[0] - metrics.loc[metrics['Category'].isin(['Depreciation Expense'])][year[i]].values[0])/365))

        if ((y - i) == 1):
            if (daysCash[i] >= 45):
                r_daysCash.append("MS")
            else:
                r_daysCash.append("DNMS")
        else:
            if (daysCash[i] >= 45 or (daysCash[i] >= 30 and daysCash[i] >= (metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+1]].values[0] / ((metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+1]].values[0] - metrics.loc[metrics['Category'].isin(['Depreciation Expense'])][year[i+1]].values[0])/365)))):
                r_daysCash.append("MS")
            else:
                r_daysCash.append("DNMS")
                    
        # Annual Enrollment Change
        if ((y - i) == 1):
            enrollChange.append(0)
        else:
            enrollChange.append((metrics.loc[metrics['Category'].isin(['ADM Average'])][year[i]].values[0] - metrics.loc[metrics['Category'].isin(['ADM Average'])][year[i+1]].values[0]) / metrics.loc[metrics['Category'].isin(['ADM Average'])][year[i+1]].values[0]) 

        if ((y - i) == 1):
            r_enrollChange.append("N/A")
        else:
            if (enrollChange[i] > -0.1):
                    r_enrollChange.append("MS")
            else:
                    r_enrollChange.append("DNMS")

        # Primary Reserve Ratio (to replace)
        primaryReserve.append(metrics.loc[metrics['Category'].isin(['Unrestricted Net Assets'])][year[i]].values[0] / metrics.loc[metrics['Category'].isin(['Operating Expenses'])][year[i]].values[0])

        if (primaryReserve[i] > 0.25):
            r_primaryReserve.append("MS")
        else:
            r_primaryReserve.append("DNMS")

        ## Long Term Indicators ##

        # Change in Net Assets Margin & Aggregated Three-Year Margin
        chNetAssMar.append(metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] / metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i]].values[0])

        if ((y - i) <= 2):
            aggMar.append(0)
        else:
            aggMar.append((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+2]].values[0]))

        if ((y - i) == 1):
            if (chNetAssMar[i] > 0):
                r_assetMar.append("MS")
                r_aggMar.append("N/A")
            else:
                r_assetMar.append("DNMS")
                r_aggMar.append("N/A")
        elif ((y - i) == 2):
            if (chNetAssMar[i] + (metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] / metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+1]].values[0]) > 0):
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
            if ((chNetAssMar[i] > 0 and aggMar[i] > 0) or ((chNetAssMar[i] > 0 and aggMar[i] > -.015) and (aggMar[i] > ((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+3]].values[0]))) and (((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+3]].values[0])) > ((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+4]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+3]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[i+4]].values[0]))))):
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
                cashFlow.append(0)
        else:
            cashFlow.append(metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i]].values[0] - metrics.loc[metrics['Category'].isin(['Unrestricted Cash'])][year[i+1]].values[0])

        # Multi-Year Cash Flow
        if ((y - i) <= 2):
            myCashFlow.append(0)
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
        debtCoverageRatio.append((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Lease Payments (Facility)'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Depreciation Expense'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Interest Expense'])][year[i]].values[0]) / (metrics.loc[metrics['Category'].isin(['Lease Payments (Facility)'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Principal Payments'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Interest Expense'])][year[i]].values[0]))

        if (debtCoverageRatio[i] > 1):
            r_debtCoverageRatio.append("MS")
        else:
            r_debtCoverageRatio.append("DNMS")

    # End Loop #

    # Internal Metrics - Harcoded for first run, as there is only CY data. Move to loop in 2021-22
    occupancyRatio.append((metrics.loc[metrics['Category'].isin(['Lease Payments (Facility)'])][year[0]].values[0] + metrics.loc[metrics['Category'].isin(['Depreciation Expense'])][year[0]].values[0] + metrics.loc[metrics['Category'].isin(['Insurance (Facility)'])][year[0]].values[0] + metrics.loc[metrics['Category'].isin(['Electric & Gas'])][year[0]].values[0] + metrics.loc[metrics['Category'].isin(['Water & Sewage'])][year[0]].values[0] + metrics.loc[metrics['Category'].isin(['Waste Disposal'])][year[0]].values[0] + metrics.loc[metrics['Category'].isin(['Security Services'])][year[0]].values[0] + metrics.loc[metrics['Category'].isin(['Maintenance/Repair'])][year[0]].values[0])/metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[0]].values[0])
    humanRatio.append(metrics.loc[metrics['Category'].isin(['Total Personnel Expenses'])][year[0]].values[0]/metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[0]].values[0])
    instructionRatio.append((metrics.loc[metrics['Category'].isin(['Instructional & Support Staff'])][year[0]].values[0] + metrics.loc[metrics['Category'].isin(['Instructional Supplies'])][year[0]].values[0]) / metrics.loc[metrics['Category'].isin(['Operating Revenue'])][year[0]].values[0])

    # Create single list for each metric and rating value
    # use itertools to alternate metric value and rating

    def alt_chain(*iters, fillvalue=None):
        return itertools.chain.from_iterable(itertools.zip_longest(*iters, fillvalue=fillvalue))

    currentRatio = list(np.around(np.array(currentRatio),2))
    # To convert numpy.list to python.list: currentRatio = np.array(currentRatio).tolist()
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

    occupancyRatio.insert(0,'Occupancy Ratio')
    humanRatio.insert(0,'Human Capital Ratio')
    instructionRatio.insert(0,'Instruction Ratio')

    # Add word "Rating + #" to headers in appropriate places/replace on display
    rating = []

    end = y
    k=1

    for y in range(end):
        j=str(k)
        rating.append('Rating ' + j)
        k=k+1

    mcolumns = [x for x in itertools.chain.from_iterable(itertools.zip_longest(columns,rating)) if x]
    mcolumns.insert(0,'Metric')
    subhead1 = ["Near Term"]
    subhead2 = ["Long Term"]
    subhead3 = ["Other Metrics"]

    summary = pd.DataFrame([subhead1,m1,m2,m3,m4,subhead2,m5,m6,m7,m8,m9,m10,subhead3,occupancyRatio,humanRatio,instructionRatio],columns=mcolumns)
    
    return summary
## End Function

## Global var - to determine table columns dynamically
#class_name = "pretty_container ten columns"

## Callback ##
@app.callback(
    Output('metric-table', 'children'),
    Output('defn-table', 'children'),
    Output('other-table', 'children'),
    Input('charter-dropdown', 'value'),
    Input('dash-session', 'data')
)
def update_finmet_page(school, data):
    if not school:
        raise PreventUpdate

    finance_metrics = pd.DataFrame.from_dict(data['1'])
    finance_metrics = finance_metrics.iloc[:, ::-1]   # flip dataframe back to normal
    finance_metrics.index = finance_metrics.index.astype(int) # convert index to int

    if len(finance_metrics.index) == 0:

        metric_table = [
            dash_table.DataTable(
                columns = [
                    {'id': "emptytable", 'name': "No Data to Display"},
                ],
                style_header={
                    'fontSize': '14px',
                    'border': 'none',
                    'textAlign': 'center',
                    'color': '#6783a9',
                    'fontFamily': 'Robotoa, sans-serif',
                },
            )
        ]

    else:
        
        all_metrics = calculateMetrics(finance_metrics)

        # Clean Data #
        all_metrics = all_metrics.replace(np.nan, '',regex=True)

        for col in all_metrics.columns:
            all_metrics[col]=all_metrics[col].replace(0.0, '')

        # Force correct format in datatable for display
        for x in range(1,len(all_metrics.columns),2):
            if all_metrics.iat[3,x]:
                all_metrics.iat[3,x] = '{:.0%}'.format(all_metrics.iat[3,x])
            if all_metrics.iat[9,x]:
                all_metrics.iat[9,x] = '{:,.2f}'.format(all_metrics.iat[9,x])
            if all_metrics.iat[10,x]:
                all_metrics.iat[10,x] = '{:,.2f}'.format(all_metrics.iat[10,x])
            if all_metrics.iat[13,x]:
                all_metrics.iat[13,x] = '{:.0%}'.format(all_metrics.iat[13,x])
            if all_metrics.iat[14,x]:
                all_metrics.iat[14,x] = '{:.0%}'.format(all_metrics.iat[14,x])
            if all_metrics.iat[15,x]:
                all_metrics.iat[15,x] = '{:.0%}'.format(all_metrics.iat[15,x])

        headers = all_metrics.columns.tolist()

#### TODO: Adjust table width depending on number of columns?
### Do this in table style or adjusting number of 'pretty' columns (use variable in div? e.g., if 1 metric, use 'four', if 3 or more metrics use 'six')
### TEST: Adjust 'column' size based on # of columns        
        #
#        global class_name
         # use to determine table size
#        table_size = len(headers)
        
#        if table_size == 11:
#            col_width = 'ten'
#        elif table_size == 9:
#            col_width = 'nine'
#        elif table_size == 7:
#            col_width = 'eight'
#        else:
#            col_width = 'four'       
#        class_name = "pretty_container " + col_width + " columns"

        # Somewhat hacky - in df they must be unique (e.g., Rating 1, Rating 2, . . .)
        # for display purposes, we want them all to read: 'Rating'
        clean_headers = [] 
        for i, x in enumerate (headers):
            if 'Rating' in x:
                clean_headers.append('Rating')
            else:
                clean_headers.append(x)

        metric_table = [
                        dash_table.DataTable(
                        all_metrics.to_dict('records'),
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
                                    'filter_query': '{Metric} eq "Near Term" || {Metric} eq "Long Term" || {Metric} eq "Other Metrics"'
                                },
                                'paddingLeft': '10px',
                                'text-decoration': 'underline',
                                "fontWeight": "bold"
                            },
                        ] +
                        [
                            {
                                'if': {
                                    'filter_query': '{{{col}}} = "DNMS"'.format(col=col),
                                    'column_id': col
                                },
                                'backgroundColor': '#b44655',
                                'fontWeight': 'bold',
                                'color': 'white',
                            } for col in all_metrics.columns
                        ] +
                        [
                            {
                                'if': {
                                    'filter_query': '{{{col}}} = "MS"'.format(col=col),
                                    'column_id': col
                                },
                                'backgroundColor': '#81b446',
                                'fontWeight': 'bold',
                                'color': 'white',
                            } for col in all_metrics.columns
                        ],
                        style_header={
                            'backgroundColor': '#ffffff',
                            'fontSize': '12px',
                            'fontFamily': 'Open Sans, sans-serif',
                            'color': '#6783a9',
                            'textAlign': 'center',
                            'fontWeight': 'bold'
                        },
                        style_cell={
                            'whiteSpace': 'normal',
    #                            'height': 'auto',
                            'textAlign': 'center',
                            'color': '#6783a9',
                            'boxShadow': '0 0',
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

    defn_table_data = [
        ['Current Ratio = Current Assets / Current Liabilities','Current Ratio is greater than 1.1; or is between 1.0 and 1.1 and the one-year trend is not negative.'],
        ['Days Cash on Hand = Unrestricted Cash / ((Operating Expenses - Depreciation Expense)/365)','School has greater than 45 unrestricted days cash; or between 30 - 45 unrestricted days cash and the one-year trend is not negative.'],
        ['Annual Enrollment Change = (Current Year ADM - Previous Year ADM) / Previous Year ADM','Annual Enrollment Change increases or shows a current year decrease of less than 10%.'],
        ['Primary Reserve Ratio = Unrestricted Net Assets / Operating Expenses','Primary Reserve Ratio is greater than .025.'],
        ['Change in Net Assets Margin = Net Asset Position / Operating Revenue;Aggregated 3-Year Margin = 3 Year Net Asset Position / 3 Year Operating Revenue','Aggregated Three-Year Margin is positive and the most recent year Change in Net Assets Margin is positive; or Aggregated Three-Year Margin is greater than -1.5%, the trend is positive for the last two years, and Change in Net Assets Margin for the most recent year is positive. For schools in their first and second year of operation, the cumulative Change in Net Assets Margin must be positive.'],
        ['Debt to Asset Ratio = Total Liabilities / Total Assets','Debt to Asset Ratio is less than 0.9.'],
        ['One Year Cash Flow = Recent Year Total Cash - Previous Year Total Cash; Multi-Year Cash Flow = Recent Year Total Cash - Two Years Previous Total Cash','Multi-Year Cash Flow is positive and One Year Cash Flow is positive in two out of three years, including the most recent year. For schools in the first two years of operation, both years must have a positive Cash Flow (for purposes of calculating Cash Flow, the school\'s Year 0 balance is assumed to be zero).'],
        ['Debt Service Coverage Ratio = (Change in Net Assets + Depreciation Expense + Interest Expense + Lease Payments) / (Principal Payments + Lease Payments +  Interest Expense)','Debt Service Coverage Ratio is greater than or equal to 1.0.']                                  
    ]

    defn_table_keys = ['DEFINITIONS','REQUIREMENTS TO MEET STANDARD']
    defn_table_dict= [dict(zip(defn_table_keys, l)) for l in defn_table_data ]

    defn_table = [
            dash_table.DataTable(
                data = defn_table_dict,
                columns = [{'name': i, 'id': i} for i in defn_table_keys],
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
                    }
                ],
                style_header={
                    'backgroundColor': '#ffffff',
                    'fontSize': '12px',
                    'fontFamily': 'Roboto, sans-serif',
                    'color': '#6783a9',
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'text-decoration': 'none',
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
                            'column_id': 'DEFINITIONS'
                        },
                        'width': '50%',
                        'text-decoration': 'underline',
                    },
                ],
                style_as_list_view=True
            )
    ]

    other_table_data = [
        ['Occupancy Ratio = (Facility Lease Payments + Depreciation Expense + Facility Insurance + Electric & Gas + Water & Sewage + Waste Disposal + Security Services + Maintenance/Repair)  / Operating Revenue','Measures the percentage of total revenue used to occupy and maintain school facilities. A school\'s occupancy ratio generally should be less than 25%.'],
        ['Human Capital Ratio = Total Personnel Expenses / Operating Revenue','Measures the percentage of total revenue used for payroll. A school\'s human capital ratio should be less than 50%. A human capital ratio that is significantly Higher than a school\'s instruction ratio may be a sign that the school is \'top-heavy.\''],
        ['Instruction Ratio = (Instructional & Support Staff + Instructional Supplies) / Operating Revenue','Measures how much of a school\'s revenue is used to pay for instruction.']
    ]

    other_table_keys = ['METRIC','DEFINITION']
    other_table_dict= [dict(zip(other_table_keys, l)) for l in other_table_data ]

    other_table = [               
                dash_table.DataTable(
                    data = other_table_dict,
                    columns = [{'name': i, 'id': i} for i in other_table_keys],
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
                        }
                    ],
                    style_header={
                        'backgroundColor': '#ffffff',
                        'fontSize': '12px',
                        'fontFamily': 'Roboto, sans-serif',
                        'color': '#6783a9',
                        'textAlign': 'center',
                        'fontWeight': 'bold',
                        'text-decoration': 'none'
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
                                'column_id': 'METRIC'
                            },
                            'width': '50%',
                            'text-decoration': 'underline',
                        },
                    ],
                    style_as_list_view=True
                )
    ]
    return metric_table, defn_table, other_table
## End Callback

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
                                            html.Label("Financial Accountability Metrics", style=label_style),
                                            html.Div(id='metric-table')
                                        ],
                                        className = "pretty_container ten columns",
                                    ),
                                ],
                                className = "bare_container twelve columns",
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
                                            html.Label("Accountability Metrics Definitions & Requirements", style=label_style),
                                            html.Div(id='defn-table')
                                        ],
                                        className = "pretty_container ten columns"
                                    ),
                                ],
                                className = "bare_container twelve columns",
                            ),
                        ],
                        className = 'row pagebreak'
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label("Ratio Definitions", style=label_style),
                                            html.Div(id='other-table')
                                        ],
                                        className = "pretty_container ten columns",
                                    ),
                                ],
                                className = "bare_container twelve columns",
                            ),
                        ],
                        className = 'row'
                    ),
                ]
            )

if __name__ == '__main__':
    app.run_server(debug=True)