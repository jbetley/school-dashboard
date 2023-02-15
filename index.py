#########################
# ICSB School Dashboard #
#########################
# author:    jbetley
# date:      11.11.22
# rev: index refactor

## NOTE: Using pandas dataframes (not typically used for
# display) to build lots of dash datatables (to be used for display),
# so there is quite a bit of funky ass fiddly dataframe manipulation
# shit required to get everything aligned and in the order that we want it.

from dash import dcc, html,Input,Output
from dash.exceptions import PreventUpdate
from collections import OrderedDict
import pandas as pd
import json
import numpy as np
import os.path
import itertools

# Debuggging - uncomment to display all df rows in console using print statement#
pd.set_option('display.max_rows', None)

from app import app
from apps import about, financial_information, financial_metrics, financial_analysis, academic_information_k12, academic_metrics, academic_analysis, organizational_compliance, print_page

app.config['suppress_callback_exceptions'] = True

# Calculate difference between two values (while preserving insufficient n-size string value)
def difference(v1, v2):
#    if v1 == None and v2 == None:
#        val = 'XX'  # Mark for removal
    if (v1 != '***' and v1 != None) and (v2 != '***' and v2 != None):
        val = float(v1) - float(v2)
    else:
        val = '***'
    return val

# Get rating for academic indicators
# inputs: value, list, and integer
def getRating(data,threshold,flag):

    # if data is a string
    if data == '***' or data == 'No Grade':
        indicator = 'NA'
        return indicator

    if data == '-***':
        indicator = 'DNMS'
        return indicator

    # if data is NoneType
    if data is None:
        indicator = 'NA'
        return indicator

    # letter_grade ratings (type string)
    if flag == 4:   # lettergrade ratings
        if data == threshold[0]:
            indicator = 'ES'
        elif data == threshold[1]:
            indicator = 'MS'
        elif data == threshold[2]:
            indicator = 'AS'
        else:
            indicator = 'DNMS'
        return indicator

    # numeric checks - ensure type is float
    data = float(data)

    # if data is NaN
    if np.isnan(data):
        indicator = 'NA'
        return indicator

    # academic ratings (numeric)
    if flag == 1:
        if data >= threshold[0]:
            indicator = 'ES'
        elif data > threshold[1]:
            indicator = 'MS'
        elif data >= threshold[2]:
            indicator = 'AS'
        elif data <= threshold[3]:
            indicator = 'DNMS'

    # graduation rate ratings (numeric)
    if flag == 2:
        if data >= threshold[0]:
            indicator = 'ES'
        elif data < threshold[0] and data >= threshold[1]:
            indicator = 'MS'
        elif data < threshold[1] and data >= threshold[2]:
            indicator = 'AS'
        else:
            indicator = 'DNMS'

    # attendance rate ratings (numeric)
    if flag == 3:
        if data > threshold[0]:
            indicator = 'ES'
        elif data < threshold[0] and data >= threshold[1]:
            indicator = 'MS'
        # elif data < threshold[1]:
        #     indicator = 'AS'
        else:
            indicator = 'DNMS'

    return indicator

# Caclulates metrics based on ICSB Accountability System financial framework
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

        # TODO: Replace PRR with a more appropriate financial metric
        # Primary Reserve Ratio
        primaryReserve.append(metrics.loc[metrics['Category'].isin(['Unrestricted Net Assets'])][year[i]].values[0] / metrics.loc[metrics['Category'].isin(['Operating Expenses'])][year[i]].values[0])

        if (primaryReserve[i] > 0.25):
            r_primaryReserve.append("MS")
        else:
            r_primaryReserve.append("DNMS")

        ## Long Term Indicators ##

        # Change in Net Assets Margin & Aggregated Three-Year Margin        
        chNetAssMar.append(metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] / metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i]].values[0])

        if ((y - i) <= 2):
            aggMar.append(0)
        else:
            aggMar.append((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0]))

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
            if ((chNetAssMar[i] > 0 and aggMar[i] > 0) or ((chNetAssMar[i] > 0 and aggMar[i] > -.015) and (aggMar[i] > ((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+3]].values[0]))) and (((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+3]].values[0])) > ((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+4]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+3]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+4]].values[0]))))):
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
    subhead1 = ['Near Term']
    subhead2 = ['Long Term']

    summary = pd.DataFrame([subhead1,m1,m2,m3,m4,subhead2,m5,m6,m7,m8,m9,m10],columns=mcolumns)

    return summary
## End Function

## Styles
tabs_styles = {
    'zIndex': 99,
    'display': 'inline-block',
    'height': '6vh',
    'width': '85vw',
    'position': 'relative',
    'left': '2vw'
}

tab_style = {
    'textTransform': 'uppercase',
    'fontFamily': 'Roboto, sans-serif',
    'color': 'steelblue',
    'fontSize': '12px',
    'fontWeight': '400',
    'alignItems': 'center',
    'justifyContent': 'center',
    'border': '1px solid rgba(192,193,199, .5)',
    'borderRadius': '.5rem',
    'padding':'6px'
}

tab_selected_style = {
    'textTransform': 'uppercase',
    'fontFamily': 'Roboto, sans-serif',
    'color': 'white',
    'fontSize': '12px',
    'fontWeight': '700',
    'alignItems': 'center',
    'justifyContent': 'center',
    'background': '#c0c1c7',
    'border': '1px solid rgba(70,130,180, .5)',
    'borderadius': '.5rem',
    'padding':'6px'
}

# category variables

# NOTE: 'American Indian' has been removed from ethnicity variable - it seems to break some functionality
# due to inconsistent use as a category in data
ethnicity = ['Asian','Black','Hispanic','Multiracial','Native Hawaiian or Other Pacific Islander','White']
status = ['Special Education','General Education','Paid Meals','Free/Reduced Price Meals','English Language Learners','Non-English Language Learners']
subgroups = ethnicity + status

grades = ['Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8']
academic_info_grades = ['Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8','Total','IREAD Pass %']
eca = ['Grade 10|ELA','Grade 10|Math']
info = ['Year','School Type']
subject = ['Math','ELA']

## Load Data Files ##
print('#### Loading Data. . . . . ####')

# NOTE: No K8 academic data exists for 2020
index = pd.read_csv(r'data\school_index.csv', dtype=str)
all_academic_data_k8 = pd.read_csv(r'data\academic_data_k8.csv', dtype=str)
all_academic_data_hs = pd.read_csv(r'data\academic_data_hs.csv', dtype=str)
corporation_rates = pd.read_csv(r'data\corporate_rates.csv', dtype=str)
all_demographics = pd.read_csv(r'data\demographic_data.csv', dtype=str)

# Fixes issue where converting string to int adds trailing '.0'
all_academic_data_k8['Low Grade'] = all_academic_data_k8['Low Grade'].astype(str).str.replace('.0', '', regex=False)
all_academic_data_k8['High Grade'] = all_academic_data_k8['High Grade'].astype(str).str.replace('.0', '', regex=False)

# Get current year - demographic data will almost always be more current than academic data (due to IDOE release cadence)
dropdown_year = all_academic_data_k8['Year'].unique().max()

num_academic_years = len(all_academic_data_k8['Year'].unique())

# Build dropdown list #
charters = index[['School Name','School ID','School Type']]
charter_dict = dict(zip(charters['School Name'], charters['School ID']))
charter_list = dict(sorted(charter_dict.items()))

app.layout = html.Div(
                [
                    dcc.Store(id='dash-session', storage_type='session'),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label('Select School:'),
                                        ],
                                        className='dash_label',
                                        id='school_dash_label'
                                    ),
                                    dcc.Dropdown(
                                        id='charter-dropdown',
                                        options=[{'label':name,'value':id} for name, id in charter_list.items()],
                                        style={
                                            'fontSize': '85%',
                                            'fontFamily': 'Roboto, sans-serif',
                                        },
                                        multi = False,
                                        clearable = False,
                                        className='school_dash_control'
                                    ),
                                ],
                                className='pretty_container seven columns'
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label('Select Accountability Year:'),
                                        ],
                                        className='dash_label',
                                        id='year_dash_label'
                                    ),
                                    dcc.Dropdown(
                                        id='year-dropdown',
                                        options=[{'label':str(y), 'value': str(y)} for y in range(int(dropdown_year) - num_academic_years, int(dropdown_year) + 1)],
                                        style={
                                            'fontSize': '85%',
                                            'fontFamily': 'Roboto, sans-serif',
                                        },
                                        value = dropdown_year,
                                        multi = False,
                                        clearable = False,
                                        className='year_dash_control'
                                    ),
                                ],
                                className='pretty_container five columns'
                            ),
                        ],
                        className='row'
                    ),
                    html.Div(
                        [
                            dcc.Tabs(
                                id='tabs',
                                value='tab-1',
                                children=[
                                    dcc.Tab(label='About', value='tab-1', style=tab_style, selected_style=tab_selected_style),
                                    dcc.Tab(label='Financial Performance', value='tab-2', style=tab_style, selected_style=tab_selected_style, children=[
                                        dcc.Tabs(id="subtab2", value="subtab2-1", children=[
                                            dcc.Tab(label='Financial Information', value='subtab2-1', style=tab_style, selected_style=tab_selected_style),
                                            dcc.Tab(label='Financial Metrics', value='subtab2-2', style=tab_style, selected_style=tab_selected_style),
                                            dcc.Tab(label='Financial Analysis', value='subtab2-3', style=tab_style, selected_style=tab_selected_style)])]),
                                    dcc.Tab(label='Academic Performance', value='tab-3', style=tab_style, selected_style=tab_selected_style, children=[
                                        dcc.Tabs(id="subtab3", value="subtab3-1", children=[
                                            dcc.Tab(label='Academic Information', value='subtab3-1', style=tab_style, selected_style=tab_selected_style),
                                            dcc.Tab(label='Academic Metrics', value='subtab3-2', style=tab_style, selected_style=tab_selected_style),
                                            dcc.Tab(label='Academic Analysis', value='subtab3-3', style=tab_style, selected_style=tab_selected_style)])]),
                                    dcc.Tab(label='Organizational Compliance', value='tab-4', style=tab_style, selected_style=tab_selected_style),
                                    dcc.Tab(label='View Entire Dashboard', value='tab-5', style=tab_style, selected_style=tab_selected_style),
                                ],
                                style=tabs_styles
                            ),
                        ],
                        className='no-print'
                    ),
                    html.Div(
                        id='tabs-content',
                        )
                ]
            )

# Load data into dcc.Store ('dash-session')
@app.callback(
            Output('dash-session', 'data'),
            Input('charter-dropdown', 'value'),
            Input('year-dropdown', 'value')
)
def load_data(school, year):
    if not school:
        raise PreventUpdate

    school_name = index.loc[index['School ID'] == school,['School Name']].values[0][0]
    school_corp = index.loc[index['School ID'] == school,['Corporation ID']].values[0][0]

    # School Index
    school_index = index.loc[index['School ID'] == school]
    school_index_dict = school_index.to_dict()

    # current_year is the most current year of available academic data / year is selected year
    # filter k8 academic data to exclude any years (format YYYY) more recent than selected year (can still be multi-year data)
    # and create a list of year strings to be excluded
    current_academic_year = all_academic_data_k8['Year'].unique().max()
    excluded_academic_years = int(current_academic_year) - int(year)
    excluded_years = []

    for i in range(excluded_academic_years):
        excluded_year = int(current_academic_year) - i
        excluded_years.append(str(excluded_year)) 

    # store current year separately for demographic data because demographic data exists for 2020
    demographic_year = str(year)

    # maximum number of years to data to display
    # NOTE: Change this value to display more years (must review rest of code as other changes will also be required)
    max_display_years = 5

## Financial, Organizational, and Federal Audit Findings information

    # Average Daily Membership

    school_adm = school_index.filter(regex = r'September ADM|February ADM',axis=1)

    for col in school_adm.columns:
        school_adm[col]=pd.to_numeric(school_adm[col], errors='coerce')

    if school_adm.sum(axis = 1).values[0] == 0:   # True if all columns are equal to 0
        school_adm_dict = {}

    else:

        # transpose adm dataframe and group by year (by splitting 'Name' Column e.g., '2022 February ADM', etc.
        # after 1st space) and sum() result
        # https://stackoverflow.com/questions/35746847/sum-values-of-columns-starting-with-the-same-string-in-pandas-dataframe
        school_adm = school_adm.T.groupby([s.split(' ',1)[0] for s in school_adm.T.index.values]).sum().T

        # average resulting sum (September and February Count)
        school_adm = school_adm / 2

        # NOTE: ADM is probably the most reliable way to track a school's years of operation
        # Counts the number of columns (years) with a non-zero ADM value
        operating_years_adm = len(school_adm.loc[:, (school_adm != 0).any(axis=0)].columns)

        # drop zero columns (e.g., no ADM for that year)
        school_adm = school_adm.loc[:, (school_adm != 0).any(axis=0)].reset_index(drop=True)

        # The ADM dataset can be longer than five years, so we have to filter it by both the selected year (the year to display) and the total # of years
        adm_years = len(school_adm.columns)

        # if number of available years exceeds year_limit, drop excess columns (years)
        if adm_years > max_display_years:
            school_adm.drop(columns=school_adm.columns[:(adm_years - max_display_years)], axis=1, inplace=True)

        # if the display year is less than current year
        # drop columns where year matches any years in 'excluded years' list
        if excluded_years:
            school_adm = school_adm.loc[:, ~school_adm.columns.str.contains('|'.join(excluded_years))]

        school_adm_dict = school_adm.to_dict()

    # Financial Information

    finance_file = "data\F-" + school_name + ".csv"

    if os.path.isfile(finance_file):

        school_finance = pd.read_csv(finance_file)

        # NOTE: Use this to count the number of years a school has 'existed' (as compared to operated- as a school may exist as an entity prior
        # to serving students). Count number of years in financial column (subtracting 1 for category column).
        # For dashboard purposes, we only care whether a school has five or fewer years of data
        operating_years_finance = 5 if len(school_finance.columns) - 1 >= 5 else len(school_finance.columns) - 1

        # filter dataframe to show data beginning with selected year
        # col[0] = category; col[1] - col[n] are years in descending order with col[1] as most recent year
        # 'most_recent_year' - 'year' (dropdown year selected) equals the number of columns from col[1] we need to remove
        # e.g., if 2019 is selected, we need to remove 2 columns -> col[1] & col[2] (2021 & 2020)
        # if excluded_finance_years == 0, then most_recent_year and selected year are the same

        most_recent_finance_year = school_finance.columns[1]
        excluded_finance_years = int(most_recent_finance_year) - int(year)

        if excluded_finance_years > 0:
            school_finance.drop(school_finance.columns[1:excluded_finance_years+1], axis=1, inplace=True)

        # if a school doesn't have data for the selected year, df will only have 1 column (Category)
        if len(school_finance.columns) <= 1:
            financial_info_json = {}
            financial_metrics_json = {}
            financial_indicators_json = {}
            organizational_indicators_json = {}
            #federal_audit_findings_json = ""   [NOTE: Not currently used]

        else:

            # NOTE: default is to only show 5 years of accountability data (remove this to show all data)
            # select only up to the first 6 columns of the financial df (category + maximum of 5 years)
            school_finance = school_finance.iloc[: , :6]

            school_metrics = school_finance.copy()

            for col in school_finance.columns:
                school_finance[col]=pd.to_numeric(school_finance[col], errors='coerce').fillna(school_finance[col]).tolist()

            years=school_finance.columns.tolist()
            years.pop(0)
            years.reverse()

            financial_information = school_finance.drop(school_finance.index[42:])
            financial_information = financial_information.replace(np.nan, '',regex=True)

            for col in financial_information.columns:
                financial_information[col]=financial_information[col].replace(0.0, '')

            # NOTE: Bit of a kludge. Dash datatable 'FormatTemplate' affects all numeric rows. So we change the
            # last 7 rows (Enrollment, Audit info) to str type so data isn't automatically formatted
            for p in range(36,42):
                financial_information.loc[p] = financial_information.loc[p].astype(str)

            # Strip trailing zero from audit year (YYYY) - gets added during string conversion
            def stripper(val):
                if '20' in val:
                    return val[:-2]
                else:
                    return val

            financial_information.loc[41] = financial_information.loc[41].apply(stripper)

            # Financial Ratios (processed from Form 9 file(s))

            financial_ratios_data = pd.read_csv(r'data\financial_ratios.csv', dtype=str)
            financial_ratios_data = financial_ratios_data.loc[financial_ratios_data['School Corporation'] == school_corp]
            
            if (len(financial_ratios_data.index) == 0):

                financial_indicators_dict = {}

            else:

                # drop unused columns, transpose and rename
                financial_ratios_data = financial_ratios_data.drop(columns=['Corporation Name','School Corporation'])
                financial_ratios_data = financial_ratios_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()

                # adjust to display selected year
                if excluded_finance_years > 0:
                    financial_ratios_data.drop(financial_ratios_data.columns[1:excluded_finance_years], axis=1, inplace=True)

                # add ratio data to financial_information
                financial_information = pd.concat([financial_information, financial_ratios_data], ignore_index=True)

                # in some cases, a school will have ratio calculations, but no other financial data (e.g., when a
                # school existed prior to being required to report financial information to ICSB). In this case, all
                # rows other than the rows with ratio values will be NaN. In other cases, a school will have valid financial
                # data, but no ratio data. In this case, three rows (the ratio calculations) will be NaN. We want to drop the former column and keep
                # the later column. So we count the number of NaN values and drop any column that has more than 3
                for c in financial_information.columns:
                    if financial_information[c].isna().sum() > 3:
                        financial_information.drop([c], inplace=True, axis=1)

                financial_info_dict = financial_information.to_dict(into=OrderedDict)
                financial_info_json = json.dumps(financial_info_dict)

            # Financial Indicators

            financial_indicators = school_finance[school_finance['Category'].str.startswith('2.1.')]
            financial_indicators[['Standard','Description']] = financial_indicators['Category'].str.split('|', expand=True)

            # reorder and clean up dataframe
            financial_indicators = financial_indicators.drop('Category', axis=1)
            standard = financial_indicators['Standard']
            description = financial_indicators['Description']
            financial_indicators = financial_indicators.drop(columns=['Standard','Description'])
            financial_indicators.insert(loc=0, column='Description', value = description)
            financial_indicators.insert(loc=0, column='Standard', value = standard)

            financial_indicators_dict = financial_indicators.to_dict()
            financial_indicators_json = json.dumps(financial_indicators_dict)

            # Organizational Compliance Indicators

            organizational_indicators = school_finance[school_finance['Category'].str.startswith('3.')]
            organizational_indicators[['Standard','Description']] = organizational_indicators['Category'].str.split('|', expand=True)

            # reorder and clean up dataframe
            organizational_indicators = organizational_indicators.drop('Category', axis=1)
            standard = organizational_indicators['Standard']
            description = organizational_indicators['Description']
            organizational_indicators = organizational_indicators.drop(columns=['Standard','Description'])
            organizational_indicators.insert(loc=0, column='Description', value = description)
            organizational_indicators.insert(loc=0, column='Standard', value = standard)

            organizational_indicators_dict = organizational_indicators.to_dict()
            organizational_indicators_json = json.dumps(organizational_indicators_dict)

            # Federal Audit Findings [NOTE: Not currently used]
    
            # federal_audit_findings = school_finance[school_finance['Category'].str.startswith(("Audit is","Audit includes"))]
            # federal_audit_findings = federal_audit_findings.iloc[:,:3]  # display only up to first 2 years
            # federal_audit_findings = federal_audit_findings.fillna('N/A') # pandas automatically interprets 'N/A' as NaN - so need to force back to N/A
            # federal_audit_findings.rename(columns={'Category':'Federal Audit Findings'}, inplace=True)

            # federal_audit_findings_dict = federal_audit_findings.to_dict()
            # federal_audit_findings_json = json.dumps(federal_audit_findings_dict)

            # Financial Metrics
            # release the hounds!

            financial_metrics = calculateMetrics(school_metrics)

            financial_metrics = financial_metrics.replace(np.nan, '',regex=True)

            for col in financial_metrics.columns:
                financial_metrics[col]=financial_metrics[col].replace(0.0, '')

            # Force correct format for display of df in datatable
            for x in range(1,len(financial_metrics.columns),2):
                if financial_metrics.iat[3,x]:
                    financial_metrics.iat[3,x] = '{:.0%}'.format(financial_metrics.iat[3,x])
                if financial_metrics.iat[9,x]:
                    financial_metrics.iat[9,x] = '{:,.2f}'.format(financial_metrics.iat[9,x])
                if financial_metrics.iat[10,x]:
                    financial_metrics.iat[10,x] = '{:,.2f}'.format(financial_metrics.iat[10,x])

            # NOTE: Need both of the next two lines each time we convert a df to json for dcc.store. Creating
            # an ordered dict alone is not enough. Must also be explicitly converted to JSON.
            financial_metrics_dict = financial_metrics.to_dict(into=OrderedDict)
            financial_metrics_json = json.dumps(financial_metrics_dict)

    else:

            financial_info_json = ""
            financial_metrics_json = ""
            financial_indicators_json = ""
            #federal_audit_findings_json = ""
            organizational_indicators_json = ""

    ## Academic Data

    # K8 Academic Data

    if school_index['School Type'].values[0] == 'K8' or school_index['School Type'].values[0] == 'K12':

        if school_index['School Type'].values[0] == 'K8':
            hs_academic_data_json = hs_letter_grades_json = ahs_metrics_data_json = combined_grad_metrics_json = {}

        filtered_academic_data_k8 = all_academic_data_k8[~all_academic_data_k8['Year'].isin(excluded_years)]
        k8_school_data =  filtered_academic_data_k8.loc[filtered_academic_data_k8['School ID'] == school]
        filtered_corporation_rates = corporation_rates[~corporation_rates['Year'].isin(excluded_years)]

        if (len(k8_school_data.index) == 0):
            k8_academic_data_json = {}
            k8_letter_grades_json = {}
            diff_over_years_json = {}
            diff_to_corp_json = {}
            iread_data_json = {}
            academic_analysis_corp_dict = {}
            academic_analysis_comp_dict = {}

        else:

            # get corp data (keyed to the GEO Corp value in index)
            k8_corp_data = filtered_academic_data_k8.loc[(filtered_academic_data_k8['Corp ID'] == school_index['GEO Corp'].values[0])]
            corp_rate_data = filtered_corporation_rates.loc[(filtered_corporation_rates['Corp ID'] == school_index['GEO Corp'].values[0])]

            # get comparison school data (keyed to the Comp value in index) and filter nan (little trick, nan != nan)
            # NOTE: This is a different data set than corp data because some comparison schools (e.g., charters) will not be
            # in the GEO Corp subset
            comparison_schools = school_index.loc[:, (school_index.columns.str.contains('Comp'))].values[0].tolist()
            comparison_schools = [x for x in comparison_schools if x == x]
            k8_comparison_data = filtered_academic_data_k8.loc[(filtered_academic_data_k8['School ID'].isin(comparison_schools))]

            # temporarily store text columns
            k8_school_info = k8_school_data[['State Grade','Federal Rating','School Name']].copy()
            k8_comparison_info = k8_comparison_data[['School ID','School Name']].copy()

            # filter to remove columns not used in calculations
            # Need to keep School ID and School Name only for Academic Analysis data tab purposes
            k8_school_data = k8_school_data.filter(regex = r'Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year',axis=1)
            k8_corp_data = k8_corp_data.filter(regex = r'Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year',axis=1)
            k8_comparison_data = k8_comparison_data.filter(regex = r'Total Tested$|Total Proficient$|^IREAD Pass N|^IREAD Test N|Year|School Name|School ID',axis=1)
            corp_rate_data = corp_rate_data.filter(regex = r'Total Tested$|Total Proficient$|IREAD Pass N|IREAD Test N|Year',axis=1)

            # drop 'ELA & Math' columns
            # NOTE: Comment out the following two lines to retain 'ELA & Math' columns
            k8_school_data.drop(list(k8_school_data.filter(regex = 'ELA & Math')), axis = 1, inplace = True)
            k8_corp_data.drop(list(k8_corp_data.filter(regex = 'ELA & Math')), axis = 1, inplace = True)
            corp_rate_data.drop(list(corp_rate_data.filter(regex = 'ELA & Math')), axis = 1, inplace = True)
            k8_comparison_data.drop(list(k8_comparison_data.filter(regex = 'ELA & Math')), axis = 1, inplace = True)

            # valid_mask returns a boolean series of columns where column is true if any element in the column is not equal to null
            valid_mask = ~pd.isnull(k8_school_data[k8_school_data.columns]).all()

            # create list of columns with no date (used in loop below)
            # missing_mask returns boolean series of columns where column is true if all elements in the column are equal to null
            missing_mask = pd.isnull(k8_school_data[k8_school_data.columns]).all()
            missing_cols = k8_school_data.columns[missing_mask].to_list()

            # k8_corp_data.T.to_csv('k8.csv', index=True)
            # corp_rate_data.T.to_csv('corp.csv', index=True)

            # use valid_mask keep only columns that have at least one value
            k8_school_data = k8_school_data[k8_school_data.columns[valid_mask]]
            k8_corp_data = k8_corp_data[k8_corp_data.columns[valid_mask]]
            corp_rate_data = corp_rate_data[corp_rate_data.columns[valid_mask]]

            k8_comparison_data.drop(['School ID','School Name'], inplace=True, axis=1) # temporarily drop these columns (stored above)
            k8_comparison_data = k8_comparison_data[k8_comparison_data.columns[valid_mask]]

            # change values to numeric
            # NOTE: do not change k8_school values because the function to calculate differences anticipates mixed dtypes
            for col in k8_corp_data.columns:
                k8_corp_data[col] = pd.to_numeric(k8_corp_data[col], errors='coerce')
            for col in corp_rate_data.columns:
                corp_rate_data[col] = pd.to_numeric(corp_rate_data[col], errors='coerce')

            for col in k8_comparison_data.columns:
                k8_comparison_data[col] = pd.to_numeric(k8_comparison_data[col], errors='coerce')

            # want corporation average, so sum each category of the corp datafile, grouping by Year, School ID, and School Name
            k8_corp_sum = k8_corp_data.groupby(['Year']).sum(numeric_only=True)

            # reset index as 'Year'
            corp_rate_data.set_index('Year', inplace=True)

            def calculate_proficiency(proficient_col,tested_col):
                return np.where(
                    (proficient_col == "***") | (tested_col == "***"),"***",
                        np.where((proficient_col.isna()) & (tested_col.isna()),None,
                                 np.where(proficient_col.isna(),0,
                                          pd.to_numeric(proficient_col,errors='coerce')/pd.to_numeric(tested_col,errors='coerce'))
                    ))

            # iterate over (non missing) columns, calculate the average, and store in a new column
            categories = ethnicity + status + grades + ['Total']
            for s in subject:
                for c in categories:
                    new_col = c + '|' + s + ' Proficient %'
                    proficient = c + '|' + s + ' Total Proficient'
                    tested = c + '|' + s + ' Total Tested'

                    if proficient not in missing_cols:
                        k8_school_data[new_col] = calculate_proficiency(k8_school_data[proficient],k8_school_data[tested])
                        k8_comparison_data[new_col] = k8_comparison_data[proficient] / k8_comparison_data[tested]
                        k8_corp_sum[new_col] = k8_corp_sum[proficient] / k8_corp_sum[tested]

                        # if c == 'School Total': # replace 'School Total' with 'Corporation Total' for corp_rate_data
                        #     new_col = new_col.replace('School Total', 'Corporation Total')
                        #     proficient = proficient.replace('School Total', 'Corporation Total')
                        #     tested = tested.replace('School Total', 'Corporation Total')

                        corp_rate_data[new_col] = corp_rate_data[proficient] / corp_rate_data[tested]

            # NOTE: The masking step above removes grades from the corp_rate dataframe that are not also in the school dataframe (e.g., if
            # school only has data for grades 3, 4, & 5, only those grades will remain in corp_rate df). However, the
            # 'Corporation Total' for proficiency in a subject is calculated using ALL grades. So we need to recalculate the 'Corporation Total'
            # rate manually to ensure it includes only the included grades.
            all_grades_math_proficient_corp = k8_corp_sum.filter(regex=r"Grade.+?Math Total Proficient")
            all_grades_math_tested_corp = k8_corp_sum.filter(regex=r"Grade.+?Math Total Tested")
            k8_corp_sum['Total|Math Proficient %'] = all_grades_math_proficient_corp.sum(axis=1) / all_grades_math_tested_corp.sum(axis=1)
#####
            adjusted_corp_total_math_proficient = corp_rate_data.filter(regex=r"Grade.+?Math Total Proficient")
            adjusted_corp_total_math_tested = corp_rate_data.filter(regex=r"Grade.+?Math Total Tested")            
            corp_rate_data['Total|Math Proficient %'] = adjusted_corp_total_math_proficient.sum(axis=1) / adjusted_corp_total_math_tested.sum(axis=1)

            all_grades_math_proficient_comp = k8_comparison_data.filter(regex=r"Grade.+?Math Total Proficient")
            all_grades_math_tested_comp = k8_comparison_data.filter(regex=r"Grade.+?Math Total Tested")
            k8_comparison_data['Total|Math Proficient %'] = all_grades_math_proficient_comp.sum(axis=1) / all_grades_math_tested_comp.sum(axis=1)

            all_grades_ela_proficient_corp = k8_corp_sum.filter(regex=r"Grade.+?ELA Total Proficient")
            all_grades_ela_tested_corp = k8_corp_sum.filter(regex=r"Grade.+?ELA Total Tested")
            k8_corp_sum['Total|ELA Proficient %'] = all_grades_ela_proficient_corp.sum(axis=1) / all_grades_ela_tested_corp.sum(axis=1)
####
            adjusted_corp_total_ela_proficient = corp_rate_data.filter(regex=r"Grade.+?ELA Total Proficient")
            adjusted_corp_total_ela_tested = corp_rate_data.filter(regex=r"Grade.+?ELA Total Tested")            
            corp_rate_data['Total|ELA Proficient %'] = adjusted_corp_total_ela_proficient.sum(axis=1) / adjusted_corp_total_ela_tested.sum(axis=1)

            all_grades_ela_proficient_comp = k8_comparison_data.filter(regex=r"Grade.+?ELA Total Proficient")
            all_grades_ela_tested_comp = k8_comparison_data.filter(regex=r"Grade.+?ELA Total Tested")
            k8_comparison_data['Total|ELA Proficient %'] = all_grades_ela_proficient_comp.sum(axis=1) / all_grades_ela_tested_comp.sum(axis=1)

            # calculate IREAD Pass %
            if 'IREAD Pass N' in k8_school_data:

                k8_corp_sum['IREAD Pass %'] = k8_corp_sum['IREAD Pass N'] / k8_corp_sum['IREAD Test N']
                corp_rate_data['IREAD Pass %'] = corp_rate_data['IREAD Pass N'] / corp_rate_data['IREAD Test N']
                k8_school_data['IREAD Pass %'] = pd.to_numeric(k8_school_data['IREAD Pass N'],errors='coerce') / pd.to_numeric(k8_school_data['IREAD Test N'],errors='coerce')
                k8_comparison_data['IREAD Pass %'] = k8_comparison_data['IREAD Pass N'] / k8_comparison_data['IREAD Test N']

                # Need this in the case that '***' is in IREAD Test or Pass (which results in Nan when divided)
                k8_school_data['IREAD Pass %'].fillna('***', inplace=True)

            # filter to remove columns used to calculate the final proficiency (Total Tested and Total Proficient)
            k8_school_data = k8_school_data.filter(regex = r'\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$',axis=1)
            k8_corp_data = k8_corp_sum.filter(regex = r'\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$',axis=1)
            corp_rate_data = corp_rate_data.filter(regex = r'\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$',axis=1)
            k8_comparison_data = k8_comparison_data.filter(regex = r'\|ELA Proficient %$|\|Math Proficient %$|^IREAD Pass %|^Year$',axis=1)

            # add text info columns back
            k8_school_data = pd.concat([k8_school_data, k8_school_info], axis=1, join='inner')
            k8_comparison_data = pd.concat([k8_comparison_data, k8_comparison_info], axis=1, join='inner')

            # reset indecies
            k8_school_data = k8_school_data.reset_index(drop=True)
            k8_comparison_data = k8_comparison_data.reset_index(drop=True)

            # reverse order of corp data to ensure most recent year is at index 0 and reset index
            k8_corp_data = k8_corp_data.iloc[::-1]
            k8_corp_data = k8_corp_data.reset_index()
####
            corp_rate_data = corp_rate_data.reset_index()

            # ensure columns headers are strings
            k8_school_data.columns = k8_school_data.columns.astype(str)
            k8_corp_data.columns = k8_corp_data.columns.astype(str)
            corp_rate_data.columns = corp_rate_data.columns.astype(str)

            # save this version of corp_data for Academic Analysis page
            #academic_analysis_corp_dict = k8_corp_data.to_dict()
            
            academic_analysis_corp_dict = corp_rate_data.to_dict()
            academic_analysis_comp_dict = k8_comparison_data.to_dict()

            # State and Federal Letter Grades (K8)

            # if school_index['School Type'].values[0] == 'K8' or school_index['School Type'].values[0] == 'K12':
            grade_cols = ['State Grade','Federal Rating','Year']

            # filter dataframeh
            k8_letter_grade_data = k8_school_data[grade_cols]

            # replace 0 with NaN
            k8_letter_grade_data[grade_cols] = k8_letter_grade_data[grade_cols].replace({'0':np.nan, 0:np.nan})

            # transpose
            k8_letter_grade_data = k8_letter_grade_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()

            # no k8 academic data is available for 2020 - for display purposes, we need to add a 2020 letter grade placeholder
            # but only if 2021 exists in the data set AND the school otherwise had 2020 data
            if 2021 in k8_letter_grade_data.columns:
                new_col = ['No Grade','No Grade']
                idx = k8_letter_grade_data.columns.get_loc(2021)
                k8_letter_grade_data.insert(loc=idx+1, column=2020, value=new_col)

            # Ensure each df has same # of years - relies on each year having a single row
            k8_num_years = len(k8_school_data.index)

            # transpose dataframes and clean headers
            k8_school_data = k8_school_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
            k8_school_data = k8_school_data.iloc[:,:(k8_num_years+1)]     # Keep category and all available years of data

            k8_corp_data = k8_corp_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
            k8_corp_data = k8_corp_data.iloc[:,:(k8_num_years+1)]     # Keep category and all available years of data
####
            corp_rate_data = corp_rate_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
            corp_rate_data = corp_rate_data.iloc[:,:(k8_num_years+1)]     # Keep category and all available years of data

            # Drop State/Federal grade rows from school_data (used in 'about' tab, but not here)
            k8_school_data = k8_school_data[k8_school_data['Category'].str.contains('State Grade|Federal Rating|School Name') == False]
            k8_school_data = k8_school_data.reset_index(drop=True)

            # reverse order of corp_data columns (ignoring 'Category') so current year is first and
            # get clean list of years
            k8_year_cols = list(k8_school_data.columns[:0:-1])
            k8_year_cols.reverse()

            # Create copies of both (?) dataframes to use later for metric calculations
            # k8_corp_metric_data = k8_corp_data.copy()

            k8_school_metric_data = k8_school_data.copy()

            # add_suffix is applied to entire df. To hide columns we dont want renamed, set them as index and reset back after renaming.
            k8_corp_data = k8_corp_data.set_index(['Category']).add_suffix('Corp Rate').reset_index()
            corp_rate_data = corp_rate_data.set_index(['Category']).add_suffix('Corp Rate').reset_index()
            k8_school_data = k8_school_data.set_index(['Category']).add_suffix('School').reset_index()

            # Create list of alternating columns by year (School Value/Similar School Value)
            school_cols = list(k8_school_data.columns[:0:-1])
            school_cols.reverse()

            #corp_cols = list(k8_corp_data.columns[:0:-1])
            corp_cols = list(corp_rate_data.columns[:0:-1])
            corp_cols.reverse()

            result_cols = [str(s) + '+/-' for s in k8_year_cols]

            final_cols = list(itertools.chain(*zip(school_cols, corp_cols, result_cols)))
            final_cols.insert(0,'Category')

            merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
            merged_cols.insert(0,'Category')

            #merged_data = k8_school_data.merge(k8_corp_data, on ='Category', how='left')
            merged_data = k8_school_data.merge(corp_rate_data, on ='Category', how='left')            
            merged_data = merged_data[merged_cols]

            # temporarily drop 'Category' column to simplify calculating difference
            tmp_category = k8_school_data['Category']

            k8_school_data.drop('Category', inplace=True, axis=1)
            k8_corp_data.drop('Category', inplace=True, axis=1)
            corp_rate_data.drop('Category', inplace=True, axis=1)

            # calculate difference between school and corp dataframes (with mixed data types)
            def calculate_difference(value1,value2):
                return np.where(
                    (value1 == "***") | (value2 == "***"),"***",
                        np.where(value1.isna(),None,
                            pd.to_numeric(value1,errors='coerce') - pd.to_numeric(value2,errors='coerce')
                        )
                    )

            k8_result = pd.DataFrame()

            for c in k8_school_data.columns:
                c=c[0:4]
#                k8_result[c +'+/-'] = calculate_difference(k8_school_data[c + 'School'],k8_corp_data[c + 'Corp Avg'])
                k8_result[c +'+/-'] = calculate_difference(k8_school_data[c + 'School'],corp_rate_data[c + 'Corp Rate'])

            # add headers
            k8_result.set_axis(result_cols, axis=1,inplace=True)
            k8_result.insert(loc=0,column='Category',value = tmp_category)

            # combined merged (school and corp) and result dataframes and reorder (according to result columns)
            final_k8_academic_data = merged_data.merge(k8_result, on ='Category', how='left')

            final_k8_academic_data = final_k8_academic_data[final_cols]

            # drop 'Proficient %' from all 'Category' rows and remove whitespace
            final_k8_academic_data['Category'] = final_k8_academic_data['Category'].str.replace('Proficient %', '').str.strip()

            # rename IREAD Category
            final_k8_academic_data.loc[final_k8_academic_data['Category'] == 'IREAD Pass %', 'Category'] = 'IREAD Proficiency (Grade 3 only)'

            # convert to ordered_dict and then json
            k8_academic_data_dict = final_k8_academic_data.to_dict(into=OrderedDict)
            k8_academic_data_json = json.dumps(k8_academic_data_dict)

            k8_letter_grades_dict = k8_letter_grade_data.to_dict(into=OrderedDict)
            k8_letter_grades_json = json.dumps(k8_letter_grades_dict)

#### Academic Metrics (k8)

            # Store IREAD data separately (and drop from school df)
            # NOTE: Need to do this for any metric that isn't comparative (e.g., year over year or diff from school corp)
            iread_data = k8_school_metric_data[k8_school_metric_data['Category'] == 'IREAD Pass %']
            k8_school_metric_data = k8_school_metric_data.drop(k8_school_metric_data[k8_school_metric_data['Category'] == 'IREAD Pass %'].index)

            # Store category column and drop from both dataframes to simplify calculation
            category_header = k8_school_metric_data['Category']
            k8_school_metric_data.drop('Category', inplace=True, axis=1)

            # temporarily store last column (first year of data)
            first_year = pd.DataFrame()
            first_year[k8_school_metric_data.columns[-1]] = k8_school_metric_data[k8_school_metric_data.columns[-1]]

            # calculate year over year values
            # NOTE: There are some cases where a '0' result has a different meaning:
            # 1) When Total Tested is the same for two consecutive years and Total Proficient
            #   is *** -> this must be treated as a ***
            # 2) When Total Tested is the same for two consecutive years and Total Proficient is a
            #   number AND is the same (e.g.  2/10 (.20) – 2/20 (.20), the difference is also zero -> however, this
            #   must be treated as the number '0'
            # 3) When a school’s first tested year has NO calculation, none tested, none proficient (eg., NaN) and
            #   the school's second tested year is the number 0 (e.g., # tested, 0 proficient) -> this must
            #   somehow be flagged as different than '0' because the rating should be [DNMS] not [AS]
            # 4) Similarly, if a school goes from *** to 0 -> this must also be treated as [DNMS]
            # Flow:
            #   if None in Either Column -> None
            #   if *** in either column -> ***
            #   if # -> subtract
            #   if first value = 0 and second value is *** -> -***
            #   if first value = 0 and second value is NaN -> -***

            year_over_year_data = pd.DataFrame()

            def calculate_year_over_year(value1,value2):
                return np.where((value1 == 0) & ((value2.isna()) | (value2 == '***')),'-***',
                            np.where((value1 == "***") | (value2 == "***"),"***",
                                np.where((value1.isna()) & (value2.isna()),None,
                                    np.where((~value1.isna()) & (value2.isna()),value1,
                                        pd.to_numeric(value1,errors='coerce') - pd.to_numeric(value2,errors='coerce')
                                    )
                                )
                            )
                        )

            for y in range(0,(len(k8_school_metric_data.columns)-1)):
                year_over_year_data[k8_school_metric_data.columns[y]] = calculate_year_over_year(k8_school_metric_data.iloc[:,y],k8_school_metric_data.iloc[:,y+1])

            # Add back first_year data
            year_over_year_data[first_year.columns] = first_year

            # add headers
            year_over_year_data.set_axis(k8_year_cols, axis=1,inplace=True)
            year_over_year_data.insert(loc=0,column='Category',value = category_header)

            # calculate metrics for both categories (over year and as compared to corp)
            diff_to_corp = final_k8_academic_data.copy()
            diff_over_years = final_k8_academic_data.copy()

            diff_over_years.drop([col for col in diff_over_years.columns if 'Corp Rate' in col or '+/-' in col],axis=1,inplace=True)

            year_over_year_data = year_over_year_data.set_index(['Category']).add_suffix('+/-').reset_index()
            year_over_year_data['Category'] = year_over_year_data['Category'].str.replace('Proficient %', '').str.strip()

            # Create list of alternating columns by year (School Value/Similar School Value)
            school_years_cols = list(diff_over_years.columns[1:])
            # school_years_cols.reverse()
            
            year_over_year_data_cols = list(year_over_year_data.columns[1:])
            # year_over_year_data_cols = list(year_over_year_data.columns[:0:-1])
            # year_over_year_data_cols.reverse()
            
            merged_years_cols = [val for pair in zip(school_years_cols, year_over_year_data_cols) for val in pair]
            merged_years_cols.insert(0,'Category')

            diff_over_years = diff_over_years.merge(year_over_year_data, on ='Category', how='left')
            diff_over_years = diff_over_years[merged_years_cols]

            delta_limits = [.1,.02,0,0]     # metric thresholds for difference analysis
            years_limits = [.05,.02,0,0]    # metric thresholds for year over year analysis

            # this code (used several times in the app) iterates over each df, using the getRating() function to
            # calculate the appropriate rating the function takes: 1) the value to be rated from either the 'School'
            # column, if the value itself is rated (e.g., iread performance), or the '+/-' column, if there is an
            # additional calculation to be performed on the value (e.g., year over year or compared to corp); 2) a
            # list of the 'limits' to be used in the calculation; and 3) an integer 'flag' which tells the function
            # which calculation to use.
            [diff_to_corp.insert(i,str(diff_to_corp.columns[i-1])[:7 - 3] + 'Rating' + str(i), diff_to_corp.apply(lambda x : getRating(x[diff_to_corp.columns[i-1]], delta_limits,1), axis = 1)) for i in range(diff_to_corp.shape[1], 1, -3)]
            [diff_over_years.insert(i,str(diff_over_years.columns[i-1])[:7 - 3] + 'Rating' + str(i), diff_over_years.apply(lambda x : getRating(x[diff_over_years.columns[i-1]], years_limits,1), axis = 1)) for i in range(diff_over_years.shape[1], 1, -2)]

            # calculate IREAD metrics
            if not iread_data.empty:
                iread_limits = [.9,.8,.7,.7]    # metric thresholds for IREAD performance
                iread_data = iread_data.set_index(['Category']).add_suffix('School').reset_index()
                [iread_data.insert(i,str(iread_data.columns[i-1])[:7 - 3] + 'Rating' + str(i), iread_data.apply(lambda x : getRating(x[iread_data.columns[i-1]], iread_limits,1), axis = 1)) for i in range(iread_data.shape[1], 1, -1)]

            # Replace NaN
            diff_to_corp.fillna('No Data',inplace=True)
            diff_over_years.fillna('No Data',inplace=True)

            # ensure all column headers are strings
            diff_to_corp.columns = diff_to_corp.columns.astype(str)
            diff_over_years.columns = diff_over_years.columns.astype(str)

            # drop last year_data column ('Rating') and rename the remaining Year column - we don't use last Rating column
            # becase we cannot calculate a 'year over year'calculation for the first year - it is just the baseline
            diff_over_years = diff_over_years.iloc[: , :-2]
            diff_over_years.columns.values[-1] = diff_over_years.columns.values[-1] + ' (Initial Data Year)'

            diff_to_corp_dict = diff_to_corp.to_dict(into=OrderedDict)
            diff_to_corp_json = json.dumps(diff_to_corp_dict)

            # one last processing step is needed to ensure proper ratings. The GetRating function assigns a rating based on
            # the '+/-' difference value (either year over year or as compared to corp). For the year over year comparison
            # it is possible to get a rating of 'Approaches Standard' for a '+/-' value of '0.00%' when the yearly ratings
            # are both 0. E.g., both 2022 and 2021 proficiency are both 0%. However, there is no case where we want a school
            # to receive anything other than a 'DNMS' for a 0% proficiency. So we replace any rating in the Rating column
            # with 'DMNS' where the School value is '0.00%.'

            # can use school_years_cols for school headers, but need rating headers as well
            # combine them into list of tuples
            # NOTE: zip function stops at the end of the shortest list which automatically drops
            # the single 'Initial Year' column from the list. It returns an empty list if there is
            # school_years_cols only contains the Initial Year columns (because rating_cols will be empty)
            rating_cols = list(col for col in diff_over_years.columns if 'Rating' in col)
            col_pair = list(zip(school_years_cols, rating_cols))

            if col_pair:
                for k, v in col_pair:
                    diff_over_years[v] = np.where(diff_over_years[k] == 0, 'DNMS', diff_over_years[v])

            # create json for storage
            diff_over_years_dict = diff_over_years.to_dict(into=OrderedDict)
            diff_over_years_json = json.dumps(diff_over_years_dict)

            # NOTE: Separate df for IREAD
            iread_data.fillna('No Data',inplace=True)
            iread_data.columns = iread_data.columns.astype(str)

            iread_data_dict = iread_data.to_dict(into=OrderedDict)
            iread_data_json = json.dumps(iread_data_dict)

#### HS Academic Information ####

    if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'K12' or school_index['School Type'].values[0] == 'AHS':

        if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'AHS':
            k8_academic_data_json = diff_to_corp_json = diff_over_years_json = k8_letter_grades_json = \
             iread_data_json = academic_analysis_corp_dict = academic_analysis_comp_dict = ""

        if school_index['School Type'].values[0] == 'HS' or school_index['School Type'].values[0] == 'K12':
            ahs_metrics_data_json = {}

        # remove 'excluded_years' from dataframe based on Col 'Year'
        hs_all_data_included_years = all_academic_data_hs[~all_academic_data_hs['Year'].isin(excluded_years)]
        hs_school_data = hs_all_data_included_years.loc[hs_all_data_included_years['School ID'] == school]

        if len(hs_school_data.index) == 0:

            hs_academic_data_json = combined_grad_metrics_json = ahs_metrics_data_json = \
                 hs_letter_grades_json = academic_analysis_corp_dict = academic_analysis_comp_dict = {}

        else:

            hs_corp_data = hs_all_data_included_years.loc[(hs_all_data_included_years['Corp ID'] == school_index['GEO Corp'].values[0])]

            # tmp remove text columns from dataframe
            hs_school_info = hs_school_data[['School Name', 'State Grade','Federal Rating']].copy()

            # drop adult high schools (AHS) from corp avg df
            hs_corp_data = hs_corp_data[hs_corp_data['School Type'].str.contains('AHS') == False]

            ## AHS- temporarily pull AHS specific values (CCR and GradAll) that don't have corp equivalent.            
            if school_index['School Type'].values[0] == 'AHS':
                ahs_data = hs_school_data.filter(regex = r'GradAll$|CCR$',axis=1)

            # keep only those columns used in calculations
            hs_school_data = hs_school_data.filter(regex = r'Cohort Count$|Graduates$|Pass N|Test N|^Year$',axis=1)
            hs_corp_data = hs_corp_data.filter(regex = r'Cohort Count$|Graduates$|Pass N|Test N|^Year$',axis=1)

            # remove 'ELA & Math' columns (NOTE: Comment this out to retain 'ELA & Math' columns)
            hs_school_data.drop(list(hs_school_data.filter(regex = 'ELA & Math')), axis = 1, inplace = True)
            hs_corp_data.drop(list(hs_corp_data.filter(regex = 'ELA & Math')), axis = 1, inplace = True)

            # valid_mask returns a boolean series of columns where column is true if any element in the column is not equal to null
            valid_mask = ~pd.isnull(hs_school_data[hs_school_data.columns]).all()

            # create list of columns with no data (used in loop below)
            # missing_mask returns boolean series of columns where column is true if all elements in the column are equal to null
            missing_mask = pd.isnull(hs_school_data[hs_school_data.columns]).all()
            missing_cols = hs_school_data.columns[missing_mask].to_list()

            # use valid_mask keep only columns that have at least one value
            hs_school_data = hs_school_data[hs_school_data.columns[valid_mask]]
            hs_corp_data = hs_corp_data[hs_corp_data.columns[valid_mask]]

            # coerce corp values to numeric (not school values because the function to calculate differences
            # anticipates mixed dtypes

            # NOTE: this changes all indicators of insufficient n-size '***' (< than 10 students in the category)
            # into NaN which removes the school entirely from the average calculation. When calculating averages,
            # excluding '***' values entirely can heavily skew the results depending on the amount of suppressed data.
            # E.g., one '***' value out of 16 would have a minimum impact, while fourteen '***' values out of 16 could
            # have a dramatic impact.

            # TODO: Do not have a good alternative solution at this point.
            # See:
            # https://towardsdatascience.com/imputing-missing-data-with-simple-and-advanced-techniques-f5c7b157fb87
            # https://cardoai.com/handling-missing-data-with-python/

            for col in hs_corp_data.columns:
                hs_corp_data[col] = pd.to_numeric(hs_corp_data[col], errors='coerce')

            # group corp dataframe by year and sum all rows for each category
            hs_corp_data = hs_corp_data.groupby(['Year']).sum(numeric_only=True)

            # reverse order of rows (Year) and reset index to bring Year back as column
            hs_corp_data = hs_corp_data.loc[::-1].reset_index()

            # calculate graduation rate
            def calculate_grad_rate(graduate_col,cohort_col):
                return np.where(
                    (graduate_col == "***") | (cohort_col == "***"),"***",
                        np.where((graduate_col.isna()) & (cohort_col.isna()),None,
                                 np.where(graduate_col.isna(),0,
                                          pd.to_numeric(graduate_col,errors='coerce')/pd.to_numeric(cohort_col,errors='coerce'))
                    ))

            # list of categories for calculations
            
            # calculate grad rates
            grad_categories = ethnicity + status + ['Total']            
            for g in grad_categories:
                new_col = g + ' Graduation Rate'
                graduates = g + '|Graduates'
                cohort = g + '|Cohort Count'
                
                if cohort not in missing_cols:
                    hs_school_data[new_col] = calculate_grad_rate(hs_school_data[graduates],hs_school_data[cohort])
                    hs_corp_data[new_col] = hs_corp_data[graduates] / hs_corp_data[cohort]

            # calculate ECA rate
            def calculate_eca_rate(passN,testN):
                return np.where(
                    (passN == "***") | (testN == "***"),"***",
                        np.where((passN.isna()) & (testN.isna()),None,
                                 np.where(passN.isna(),0,
                                          pd.to_numeric(passN,errors='coerce')/pd.to_numeric(testN,errors='coerce'))
                    ))

            # calculate ECA averages ('Grade 10' + '|ELA/Math' + 'Test N' / 'Grade 10' + '|ELA/Math' + 'Pass N')
            # if none_categories includes 'Grade 10' - there is no ECA data available for the school for the selected Years
            eca_categories = ['Grade 10|ELA','Grade 10|Math']

            # checks to see if substring ('Grade 10') is in the list of missing cols
            # this performs substring search on a single combined string (separated by tabs):
            if 'Grade 10' not in '\t'.join(missing_cols):
                for e in eca_categories:
                    new_col = e + ' Pass Rate'
                    passN = e + ' Pass N'
                    testN = e + ' Test N'
                    
                    hs_school_data[new_col] = calculate_eca_rate(hs_school_data[passN],hs_school_data[testN])
                    hs_corp_data[new_col] = hs_corp_data[passN] / hs_corp_data[testN]

            # add 'non-waiver grad rate' ('Non-Waiver|Cohort Count' / 'Total|Cohort Count')
            # and 'strength of diploma' (Non-Waiver|Cohort Count` * 1.08) / `Total|Cohort Count`) calculation and average to both dataframes
            
            # if missing_cols includes 'Non-Waiver' - there is no data available for the school for the selected Years
            if 'Non-Waiver' not in '\t'.join(missing_cols):

                # NOTE: In spring of 2020, SBOE waived the GQE requirement for students in the 2020 cohort who where otherwise
                # on schedule to graduate, so, for the 2020 cohort, there were no waiver graduates (which means no non-waiver data).
                # so we replace 0 with NaN (to ensure a NaN result rather than 0)
                hs_corp_data['Non-Waiver|Cohort Count'] = hs_corp_data['Non-Waiver|Cohort Count'].replace({'0':np.nan, 0:np.nan})

                hs_corp_data['Non-Waiver Graduation Rate'] = hs_corp_data['Non-Waiver|Cohort Count'] / hs_corp_data['Total|Cohort Count']
                hs_corp_data['Strength of Diploma'] = (hs_corp_data['Non-Waiver|Cohort Count'] * 1.08) / hs_corp_data['Total|Cohort Count']
                
                # TODO: forcing conversion causes '***' values to be NaN. We are unlikely to have a '***' value
                # here, but it is possible and we may want to eventually account for this
                hs_school_data['Non-Waiver|Cohort Count'] = pd.to_numeric(hs_school_data['Non-Waiver|Cohort Count'],errors='coerce')
                hs_school_data['Total|Cohort Count'] = pd.to_numeric(hs_school_data['Total|Cohort Count'],errors='coerce')

                hs_school_data['Non-Waiver Graduation Rate'] = hs_school_data['Non-Waiver|Cohort Count'] / hs_school_data['Total|Cohort Count']
                hs_school_data['Strength of Diploma'] = (hs_school_data['Non-Waiver|Cohort Count'] * 1.08) / hs_school_data['Total|Cohort Count']

            # Calculate CCR Rate (AHS Only), add Year column and store in temporary dataframe
            # NOTE: ALl other values pulled from HS dataframe required for AHS calculations should happen here
            if school_index['School Type'].values[0] == 'AHS':
                ahs_school_data = pd.DataFrame()
                ahs_school_data['Year'] = hs_school_data['Year']

                ahs_data['AHS|CCR'] = pd.to_numeric(ahs_data['AHS|CCR'],errors='coerce')
                ahs_data['AHS|GradAll'] = pd.to_numeric(ahs_data['AHS|GradAll'],errors='coerce')
                ahs_school_data['CCR Percentage'] = ahs_data['AHS|CCR'] / ahs_data['AHS|GradAll']

                ahs_metric_data = ahs_school_data.copy()  # Keep original data for metric calculations
                ahs_metric_data = ahs_metric_data.reset_index(drop=True)

            # filter all columns keeping only the relevant ones (NOTE: comment this out to retain all columns)
            hs_school_data = hs_school_data.filter(regex = r'^Category|Graduation Rate$|Pass Rate$|^Strength of Diploma|^CCR Percentage|^Year$',axis=1)
            hs_corp_data = hs_corp_data.filter(regex = r'^Category|Graduation Rate$|Pass Rate$|^Strength of Diploma|^Year$',axis=1)

        ## State Avg Graduation Rate

            hs_all_data_included_years['Total|Graduates'] = pd.to_numeric(hs_all_data_included_years['Total|Graduates'], errors='coerce')
            hs_all_data_included_years['Total|Cohort Count'] = pd.to_numeric(hs_all_data_included_years['Total|Cohort Count'], errors='coerce')
            
            # NOTE: exclude AHS from graduation rate calculation due to the inapplicability of grad rates to the model
            hs_all_data_included_years['Total|Graduates'] = hs_all_data_included_years.loc[hs_all_data_included_years['School Type'] != 'AHS', 'Total|Graduates']
            hs_all_data_included_years['Total|Cohort Count'] = hs_all_data_included_years.loc[hs_all_data_included_years['School Type'] != 'AHS', 'Total|Cohort Count']

            state_grad_average = hs_all_data_included_years.groupby('Year', as_index=False).sum().eval('State_Grad_Average = `Total|Graduates` / `Total|Cohort Count`')

            # drop all other columns, invert rows (so most recent year at index [0]) & reset the index
            state_grad_average = state_grad_average[['Year','State_Grad_Average']]
            state_grad_average = state_grad_average.loc[::-1].reset_index(drop=True)

            # merge applicable years of grad_avg dataframe into hs_school df using an inner merge and rename the column
            # this merges data only where both dataframes share a common key, in this case 'Year')
            state_grad_average['Year'] = state_grad_average['Year'].astype(int)
            hs_corp_data = hs_corp_data.merge(state_grad_average, on='Year', how='inner')
            hs_corp_data.rename(columns={'State_Grad_Average':'Average State Graduation Rate'}, inplace=True)

            # duplicate 'Total Grad' row and name it 'State Average Graduation Rate' for comparison purposes
            hs_school_data['Average State Graduation Rate'] = hs_school_data['Total Graduation Rate']

            # reset indicies and concat
            hs_school_info = hs_school_info.reset_index(drop=True)
            hs_school_data = hs_school_data.reset_index(drop=True)
            hs_school_data = pd.concat([hs_school_data, hs_school_info], axis=1, join='inner')

            # ensure columns headers are strings
            hs_school_data.columns = hs_school_data.columns.astype(str)
            hs_corp_data.columns = hs_corp_data.columns.astype(str)

        ### State and Federal letter grades

            grade_cols = ['State Grade','Federal Rating','Year']

            hs_letter_grade_data = hs_school_data[grade_cols]

            # replace 0 with NaN
            hs_letter_grade_data[grade_cols] = hs_letter_grade_data[grade_cols].replace({'0':np.nan, 0:np.nan})

            hs_letter_grade_data = hs_letter_grade_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()

        ### Calculate difference (+/-) between school and corp grad rates

            hs_num_years = len(hs_school_data.index)

            # transpose dataframes and clean headers
            hs_school_data = hs_school_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
            hs_school_data = hs_school_data.iloc[:,:(hs_num_years+1)]     # Keep category and all available years of data

            hs_corp_data = hs_corp_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
            hs_corp_data = hs_corp_data.iloc[:,:(hs_num_years+1)]

            # Drop State/Federal grade rows from school_data (used in 'about' tab, but not here)
            hs_school_data = hs_school_data[hs_school_data['Category'].str.contains('State Grade|Federal Rating|School Name') == False]
            hs_school_data = hs_school_data.reset_index(drop=True)

            # get clean list of years
            hs_year_cols = list(hs_school_data.columns[:0:-1])
            hs_year_cols.reverse()

            # add_suffix is applied to entire df. To hide columns we dont want renamed, set them as index and reset back after renaming.
            hs_corp_data = hs_corp_data.set_index(['Category']).add_suffix('Corp Avg').reset_index()
            hs_school_data = hs_school_data.set_index(['Category']).add_suffix('School').reset_index()

            # have to do same things to ahs_data to be able to insert it back into hs_data file even though
            # there is no comparison data involved
            if school_index['School Type'].values[0] == 'AHS':
                ahs_school_data = ahs_school_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
                ahs_school_data = ahs_school_data.iloc[:,:(hs_num_years+1)]
                ahs_school_data = ahs_school_data.set_index(['Category']).add_suffix('School').reset_index()

            # Create list of alternating columns by year (School Value/Similar School Value)
            school_cols = list(hs_school_data.columns[:0:-1])
            school_cols.reverse()

            corp_cols = list(hs_corp_data.columns[:0:-1])
            corp_cols.reverse()

            result_cols = [str(s) + '+/-' for s in hs_year_cols]

            final_cols = list(itertools.chain(*zip(school_cols, corp_cols, result_cols)))
            final_cols.insert(0,'Category')

            merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
            merged_cols.insert(0,'Category')
            hs_merged_data = hs_school_data.merge(hs_corp_data, on ='Category', how='left')
            hs_merged_data = hs_merged_data[merged_cols]

            # temporarily drop 'Category' column to simplify calculating difference
            tmp_category = hs_school_data['Category']
            hs_school_data.drop('Category', inplace=True, axis=1)
            hs_corp_data.drop('Category', inplace=True, axis=1)

            # make sure there are no lingering NoneTypes to screw up the creation of hs_results
            hs_school_data = hs_school_data.fillna(value=np.nan)
            hs_corp_data = hs_corp_data.fillna(value=np.nan)

            # calculate graduation rate differences
            def calculate_graduation_rate_difference(school_col,corp_col):
                return np.where(
                    (school_col == "***") | (corp_col == "***"),"***",
                        # np.where((school_col.isna()) & (corp_col.isna()),None,
                        #          np.where(school_col.isna(),0,
                                  np.where(school_col.isna(),None,
                                          pd.to_numeric(school_col,errors='coerce') - pd.to_numeric(corp_col,errors='coerce'))
                    )#)

            # calculate difference between two dataframes
            hs_results = pd.DataFrame()
            for y in hs_year_cols:
                hs_results[y] = calculate_graduation_rate_difference(hs_school_data[y + 'School'],hs_corp_data[y + 'Corp Avg'])            

            # add headers
            hs_results.set_axis(result_cols, axis=1,inplace=True)
            hs_results.insert(loc=0,column='Category',value = tmp_category)

            final_hs_academic_data = hs_merged_data.merge(hs_results, on ='Category', how='left')
            final_hs_academic_data = final_hs_academic_data[final_cols]

            # Clean up for display for each category:
            # 1) replace negative values in School column with '***';
            # 2) replace either '1' or '1.08' in School column with '***';
            # 3) change '+/-' to '***' if school column is '***'; and
            # 4) change 'Corp Avg' & '+/-' columns to NaN if School column is NaN
            # NOTE: we test for 1.08 because of diploma strength calculation (-99 * 1.08 / -99)

            # for y in hs_year_cols:
            #     final_hs_academic_data[str(y) + 'School'] = np.where(final_hs_academic_data[str(y) + 'School'] < 0,'***', final_hs_academic_data[str(y) + 'School'])
            #     final_hs_academic_data[str(y) + 'School'] = np.where(final_hs_academic_data[str(y) + 'School'] == 1,'***', final_hs_academic_data[str(y) + 'School'])
            #     final_hs_academic_data[str(y) + 'School'] = np.where(final_hs_academic_data[str(y) + 'School'] == 1.08,'***', final_hs_academic_data[str(y) + 'School'])
            #     final_hs_academic_data[str(y) + '+/-'] = np.where(final_hs_academic_data[str(y) + 'School'] == '***','***', final_hs_academic_data[str(y) + '+/-'])
            #     final_hs_academic_data[str(y) + 'Corp Avg'] = np.where(final_hs_academic_data[str(y) + 'School'].isnull(), final_hs_academic_data[str(y) + '+/-'], final_hs_academic_data[str(y) + 'Corp Avg'])

            # If AHS - add CCR data to hs_data file
            if school_index['School Type'].values[0] == 'AHS':
                final_hs_academic_data = pd.concat([final_hs_academic_data, ahs_school_data], sort=False)#.fillna(0)
                final_hs_academic_data = final_hs_academic_data.reset_index(drop=True)

            hs_academic_data_dict = final_hs_academic_data.to_dict(into=OrderedDict)
            hs_academic_data_json = json.dumps(hs_academic_data_dict)

            hs_letter_grades_dict = hs_letter_grade_data.to_dict(into=OrderedDict)
            hs_letter_grades_json = json.dumps(hs_letter_grades_dict)

##### AHS/HS Academic Metrics ####

            if school_index['School Type'].values[0] == 'AHS':
                combined_grad_metrics_json = {}

                # transpose dataframe and clean headers
                ahs_metric_data = ahs_metric_data.set_index('Year').T.rename_axis('Category').rename_axis(None, axis=1).reset_index()
                ahs_metric_data = ahs_metric_data.iloc[:,:(hs_num_years+1)]     # Keep category and all available years of data
                ahs_metric_data.columns = ahs_metric_data.columns.astype(str)

                # format for multi-header display
                ahs_metric_cols = list(ahs_metric_data.columns[:0:-1])
                ahs_metric_cols.reverse()

                ahs_metric_data = ahs_metric_data.set_index(['Category']).add_suffix('School').reset_index()

                ahs_metric_data = ahs_metric_data.loc[ahs_metric_data['Category'] == 'CCR Percentage']
                ccr_limits = [.5,.499,.234]
                [ahs_metric_data.insert(i,str(ahs_metric_cols[i-2]) + 'Rating' + str(i), ahs_metric_data.apply(lambda x : getRating(x[ahs_metric_data.columns[i-1]], ccr_limits,2), axis = 1)) for i in range(ahs_metric_data.shape[1], 1, -1)]

                ahs_state_grades = hs_letter_grade_data.iloc[0:1 , :]
                ahs_state_grades.columns = ahs_state_grades.columns.astype(str)
                ahs_state_grades = ahs_state_grades.set_index(['Category']).add_suffix('School').reset_index()

                grade_limits = ['A','B','C','D','F']
                [ahs_state_grades.insert(i,str(ahs_metric_cols[i-2]) + 'Rating' + str(i), ahs_state_grades.apply(lambda x : getRating(x[ahs_state_grades.columns[i-1]], grade_limits,4), axis = 1)) for i in range(ahs_state_grades.shape[1], 1, -1)]

                # concatenate and add metric column
                ahs_metric_data = pd.concat([ahs_state_grades, ahs_metric_data])
                ahs_metric_data = ahs_metric_data.reset_index(drop=True)
                ahs_metric_nums = ['1.1.','1.3.']
                ahs_metric_data.insert(loc=0, column='Metric', value = ahs_metric_nums)

                ahs_school_metric_dict = ahs_metric_data.to_dict(into=OrderedDict)
                ahs_metrics_data_json = json.dumps(ahs_school_metric_dict)

            else:

                combined_hs_metrics = final_hs_academic_data.copy()

                # rename 'Corp Avg' to 'Avg'
                combined_hs_metrics.columns = combined_hs_metrics.columns.str.replace(r'Corp Avg', 'Avg')

                grad_limits_state = [0,.05,.15,.15]
                state_grad_metric = combined_hs_metrics.loc[combined_hs_metrics['Category'] == 'Average State Graduation Rate']

                [state_grad_metric.insert(i,str(state_grad_metric.columns[i-1])[:7 - 3] + 'Rating' + str(i), state_grad_metric.apply(lambda x : getRating(x[state_grad_metric.columns[i-1]], grad_limits_state,2), axis = 1)) for i in range(state_grad_metric.shape[1], 1, -3)]

                grad_limits_local = [0,.05,.10,.10]
                local_grad_metric = combined_hs_metrics[combined_hs_metrics['Category'].isin(['Total Graduation Rate', 'Non-Waiver Graduation Rate'])]
                [local_grad_metric.insert(i,str(local_grad_metric.columns[i-1])[:7 - 3] + 'Rating' + str(i), local_grad_metric.apply(lambda x : getRating(x[local_grad_metric.columns[i-1]], grad_limits_local,2), axis = 1)) for i in range(local_grad_metric.shape[1], 1, -3)]

                strength_diploma = combined_hs_metrics[combined_hs_metrics['Category'] == 'Strength of Diploma']
                strength_diploma = strength_diploma[[col for col in strength_diploma.columns if 'School' in col or 'Category' in col ]]

                ## TODO: NOT CURRENTLY DISPLAYED
                strength_diploma.loc[strength_diploma['Category'] == 'Strength of Diploma', 'Category'] = '1.7.e The school\'s strength of diploma indicator.'

                # combine dataframes and rename categories
                combined_grad_metrics = pd.concat([state_grad_metric, local_grad_metric], ignore_index=True)
                combined_grad_metrics.loc[combined_grad_metrics['Category'] == 'Average State Graduation Rate', 'Category'] = '1.7.a 4 year graduation rate compared with the State average'
                combined_grad_metrics.loc[combined_grad_metrics['Category'] == 'Total Graduation Rate', 'Category'] = '1.7.b 4 year graduation rate compared with school corporation average'
                combined_grad_metrics.loc[combined_grad_metrics['Category'] == 'Non-Waiver Graduation Rate', 'Category'] = '1.7.b 4 year non-waiver graduation rate  with school corporation average'

                combined_grad_metrics_dict = combined_grad_metrics.to_dict(into=OrderedDict)
                combined_grad_metrics_json = json.dumps(combined_grad_metrics_dict)

    # Demographic Data
    # Get demographic data for school & corp (matching school corporation of residence by corp id) and filter by selected year

    school_demographics = all_demographics.loc[(all_demographics['School ID'] == school) & (all_demographics['Year'] == demographic_year)]

    if len(school_demographics.index) == 0:    # if school is not in degmographic dataframe
        school_demographics_dict = {}
        corp_demographics_dict = {}

    else:
        school_demographics_dict = school_demographics.to_dict()

        corp_demographics = all_demographics.loc[(all_demographics['School ID'] == school_index['GEO Corp'].values[0]) & (all_demographics['Year'] == demographic_year)]
        corp_demographics_dict = corp_demographics.to_dict()

## Attendance Rate Data

    attendance_rate_school = all_demographics.loc[all_demographics['School ID'] == school][['Year','Avg Attendance']]
    attendance_rate_corp = all_demographics.loc[all_demographics['School ID'] == school_index['GEO Corp'].values[0]][['Year','Avg Attendance']]

    attendance_rate_school = attendance_rate_school.set_index('Year').T.rename_axis(None, axis=1).reset_index()
    attendance_rate_school.drop('index', inplace=True, axis=1)

    attendance_rate_corp = attendance_rate_corp.set_index('Year').T.rename_axis(None, axis=1).reset_index()
    attendance_rate_corp.drop('index', inplace=True, axis=1)

    # get 'clean' list of years of available data for school (used to add +/- col later in script)
    attendance_years = attendance_rate_school.columns.tolist()
    attendance_years = [str(s) for s in attendance_years]

    if attendance_rate_school.empty:

        attendance_data_json = {}
        attendance_data_metrics_json = {}

    else:

        # align corp df columns to school df (will drop years in corp df that aren't in school df)
        attendance_rate_corp = attendance_rate_corp[attendance_rate_school.columns]

        # drop columns where year matches any years in 'excluded years' list
        if excluded_years:
            attendance_rate_school = attendance_rate_school.loc[:, ~attendance_rate_school.columns.str.contains('|'.join(excluded_years))]
            attendance_rate_corp = attendance_rate_corp.loc[:, ~attendance_rate_corp.columns.str.contains('|'.join(excluded_years))]
            attendance_years = [x for x in attendance_years if x not in excluded_years]

        for col in attendance_rate_corp.columns:
            attendance_rate_corp[col] = pd.to_numeric(attendance_rate_corp[col], errors='coerce')

        for col in attendance_rate_school.columns:
            attendance_rate_school[col] = pd.to_numeric(attendance_rate_school[col], errors='coerce')

        attendance_rate_school.replace(0, np.nan, inplace=True)
        attendance_rate_school['Category'] = '1.1.a. Attendance Rate (compared to school corporation average)'
        last_col = attendance_rate_school.pop('Category')
        attendance_rate_school.insert(0,'Category', last_col)
        attendance_rate_corp['Category'] = '1.1.a. Attendance Rate (compared to school corporation average)'
        last_col = attendance_rate_corp.pop('Category')
        attendance_rate_corp.insert(0,'Category', last_col)

        attendance_rate_corp = attendance_rate_corp.set_index(['Category']).add_suffix('Corp Avg').reset_index()
        attendance_rate_school = attendance_rate_school.set_index(['Category']).add_suffix('School').reset_index()

        # Create list of alternating columns by year (School Value/Similar School Value)
        school_cols = list(attendance_rate_school.columns[:0:-1])
        school_cols.reverse()

        corp_cols = list(attendance_rate_corp.columns[:0:-1])
        corp_cols.reverse()

        # only time we use attendance_years var
        result_cols = [str(s) + '+/-' for s in attendance_years]

        final_cols = list(itertools.chain(*zip(school_cols, corp_cols, result_cols)))
        final_cols.insert(0,'Category')

        merged_cols = [val for pair in zip(school_cols, corp_cols) for val in pair]
        merged_cols.insert(0,'Category')
        merged_data = attendance_rate_school.merge(attendance_rate_corp, on ='Category', how='left')
        merged_data = merged_data[merged_cols]

        # temporarily drop 'Category' column to simplify calculating difference
        tmp_category = attendance_rate_school['Category']

        attendance_rate_school.drop('Category', inplace=True, axis=1)
        attendance_rate_corp.drop('Category', inplace=True, axis=1)

        # calculate difference between two dataframes
        k8_result = pd.DataFrame(attendance_rate_school.values - attendance_rate_corp.values)

        # add headers
        k8_result.set_axis(result_cols, axis=1,inplace=True)
        k8_result.insert(loc=0,column='Category',value = tmp_category)

        attendance_data = merged_data.merge(k8_result, on ='Category', how='left')
        attendance_data = attendance_data[final_cols]

        attendance_data_dict = attendance_data.to_dict(into=OrderedDict)

        # Calculate attendance data metrics
        attendance_data_metrics = attendance_data.copy()
        attendance_limits = [0,-.01,-.01]
        [attendance_data_metrics.insert(i,str(attendance_data_metrics.columns[i-1])[:7 - 3] + 'Rating' + str(i), attendance_data_metrics.apply(lambda x : getRating(x[attendance_data_metrics.columns[i-1]], attendance_limits,3), axis = 1)) for i in range(attendance_data_metrics.shape[1], 1, -3)]

        attendance_data_metrics_dict = attendance_data_metrics.to_dict(into=OrderedDict)

        attendance_data_json = json.dumps(attendance_data_dict)
        attendance_data_metrics_json = json.dumps(attendance_data_metrics_dict)

    # combine into dictionary of dictionarys for dcc.store
    ### TODO: NEEDS TO BE REORDereD FOR READABILITY
    dict_of_df = {}

    dict_of_df[0] = school_index_dict
    dict_of_df[1] = school_demographics_dict
    dict_of_df[2] = corp_demographics_dict
    dict_of_df[3] = k8_letter_grades_json
    dict_of_df[4] = hs_letter_grades_json
    dict_of_df[5] = school_adm_dict
    dict_of_df[6] = financial_info_json
    dict_of_df[7] = financial_metrics_json
    dict_of_df[8] = financial_indicators_json
#    dict_of_df[9] = federal_audit_findings_json
    dict_of_df[10] = k8_academic_data_json
    dict_of_df[11] = hs_academic_data_json
    dict_of_df[15] = organizational_indicators_json
    dict_of_df[16] = attendance_data_json
    dict_of_df[17] = diff_to_corp_json
    dict_of_df[18] = diff_over_years_json
    dict_of_df[19] = attendance_data_metrics_json
    dict_of_df[20] = combined_grad_metrics_json
    dict_of_df[21] = iread_data_json
    dict_of_df[22] = ahs_metrics_data_json
    dict_of_df[23] = academic_analysis_corp_dict
    dict_of_df[24] = academic_analysis_comp_dict

    return dict_of_df

@app.callback(
    Output('charter-dropdown', 'value'),
    Input('charter-dropdown', 'options')
)
def set_dropdown_value(charter_options):
    return charter_options[0]['value']

@app.callback(Output('tabs-content', 'children'),
                [Input('tabs', 'value'),
                Input('subtab2', 'value'),
                Input('subtab3', 'value')],
                Input('charter-dropdown', 'value')
)
def render_content(tab,subtab2,subtab3,value):

    if tab == 'tab-1':
        return about.layout
    if tab == 'tab-2':
        if subtab2 == 'subtab2-1':
            return financial_information.layout
        elif subtab2 == 'subtab2-2':
            return financial_metrics.layout
        elif subtab2 == 'subtab2-3':
            return financial_analysis.layout
    elif tab == 'tab-3':
        if subtab3 == 'subtab3-1':
            return academic_information_k12.layout
        elif subtab3 == 'subtab3-2':
            return academic_metrics.layout
        elif subtab3 == 'subtab3-3':
            return academic_analysis.layout
    elif tab == 'tab-4':
        return organizational_compliance.layout
    elif tab == 'tab-5':
        return print_page.layout

if __name__ == '__main__':
    app.run_server(debug=True)