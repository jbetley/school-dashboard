'''
Calculation Functions for ICSB Dashboard
'''
import pandas as pd
import numpy as np
import itertools
import scipy.spatial as spatial


def set_academic_rating(data, threshold, flag):
    """
    Takes a value (string, numeric, nonetype), a list of the thresholds,
    which varies from type to type and a 'flag' integer that tells the
    function which switch to use.
    Returns a string.
    """

    # if data is a string
    if data == "***" or data == "No Grade":
        indicator = "NA"
        return indicator

    if data == "-***":
        indicator = "DNMS"
        return indicator

    # if data is NoneType
    if data is None:
        indicator = "NA"
        return indicator

    # letter_grade ratings (type string)
    if flag == 4:  # lettergrade ratings
        if data == threshold[0]:
            indicator = "ES"
        elif data == threshold[1]:
            indicator = "MS"
        elif data == threshold[2]:
            indicator = "AS"
        else:
            indicator = "DNMS"
        return indicator

    # numeric checks - ensure type is float
    data = float(data)

    # if data is NaN
    if np.isnan(data):
        indicator = "NA"
        return indicator

    # academic ratings (numeric)
    if flag == 1:
        if data >= threshold[0]:
            indicator = "ES"
        elif data > threshold[1]:
            indicator = "MS"
        elif data >= threshold[2]:
            indicator = "AS"
        elif data <= threshold[3]:
            indicator = "DNMS"

    # graduation rate ratings (numeric)
    if flag == 2:
        if data >= threshold[0]:
            indicator = "ES"
        elif data < threshold[0] and data >= threshold[1]:
            indicator = "MS"
        elif data < threshold[1] and data >= threshold[2]:
            indicator = "AS"
        else:
            indicator = "DNMS"

    # attendance rate ratings (numeric)
    if flag == 3:
        if data > threshold[0]:
            indicator = "ES"
        elif data < threshold[0] and data >= threshold[1]:
            indicator = "MS"
        # elif data < threshold[1]:
        #     indicator = 'AS'
        else:
            indicator = "DNMS"

    return indicator


def round_percentages(percentages):
    """
    https://github.com/simondo92/round-percentages
    Given an iterable of percentages that add up to 100 (or decimals that add up
    to 1), round them to the nearest integer such that the rounded percentages
    also add up to 100. Uses the largest remainder method. 
    E.g. round_percentages([13.626332, 47.989636, 9.596008, 28.788024])
    -> [14, 48, 9, 29]
    """

    # if numbers are in decimal format (e.g. .57, .90) then the sum of the numbers should
    # bet at or near (1). To be safe we test to see if sum is less than 2. If it is, we
    # multiple all of the numbers in the list by 100 (e.g., 57, 90)
    if sum(percentages) < 2:
        percentages = [x * 100 for x in percentages]

    result = []
    sum_of_integer_parts = 0

    for index, percentage in enumerate(percentages):
        integer, decimal = str(float(percentage)).split(".")
        integer = int(integer)
        decimal = int(decimal)

        result.append([integer, decimal, index])
        sum_of_integer_parts += integer

    result.sort(key=lambda x: x[1], reverse=True)
    difference = 100 - sum_of_integer_parts

    for percentage in result:
        if difference == 0:
            break
        percentage[0] += 1
        difference -= 1

    # order by the original order
    result.sort(key=lambda x: x[2])

    # return just the percentage
    return [percentage[0] for percentage in result]

# Find nearest schools in miles using a KDTree
def find_nearest(school_idx,data):
    """
    Based on https://stackoverflow.com/q/43020919/190597
    Uses scipy.spatial KDTree method to find the nearest schools to the
    selected school
 
    Takes Lat and Lon for selected school (school_idx) and Lat and Lon
    for comparison schools (data).
    Returns an index list of the schools and the distances

    https://stackoverflow.com/questions/45127141/find-the-nearest-point-in-distance-for-all-the-points-in-the-dataset-python
    https://stackoverflow.com/questions/43020919/scipy-how-to-convert-kd-tree-distance-from-query-to-kilometers-python-pandas
    https://kanoki.org/2020/08/05/find-nearest-neighbor-using-kd-tree/
    """
    # the radius of earth in miles. For kilometers use 6372.8 km
    R = 3959.87433 

    # as the selected school already exists in the 'data' df,
    # just pass in index and use that to find it
    data = data.apply(pd.to_numeric)

    phi = np.deg2rad(data['Lat'])
    theta = np.deg2rad(data['Lon'])
    data['x'] = R * np.cos(phi) * np.cos(theta)
    data['y'] = R * np.cos(phi) * np.sin(theta)
    data['z'] = R * np.sin(phi)
    tree = spatial.KDTree(data[['x', 'y','z']])

    num_hits = 30

    # gets a list of the indexes and distances in the data tree that
    # match the [num_hits] number of 'nearest neighbor' schools
    distance, index = tree.query(data.iloc[school_idx][['x', 'y','z']], k = num_hits)
    
    return index, distance

def filter_grades(row, compare):
    """
    Takes two dataframes, of school and comparison school data that
    includes the Low and High Grades for each. Creates a boolean
    mask of the comparison schools where there is a grade overlap
    based on an integer list created from the Low Grade and High
    Grade values.
    
    If there is a grade range overlap, the function returns True,
    If there is no grade range overlap, the function returns False.
    """

    row[['Low Grade', 'High Grade']] = row[['Low Grade', 'High Grade']].astype(int)
    row_grade_range = list(range(row['Low Grade'], row['High Grade']+1))

    if (set(compare) & set(row_grade_range)):
        return True
    else:
        return False


def calculate_metrics(metrics):
    """
    Caclulate financial metrics and financial accountability ratings
    based on ICSBs Accountability System financial framework
    """
#TODO: Going to refactor this

# Currently uses a loop. Need to vectorize. Also is one large confusing
# fucntion. Need to break down into smaller chunks
# Also ADM is incorrect because up to date ADM is in school_index and
# not financial file

    # Need to handle pre-opening year data where there is financial activity
    # but school is not receiving state/federal grants. This 'easy' fix ignore
    # all columns (years) where the value in the State Grant column is equal to '0'
    metrics = metrics.loc[:,~(metrics.iloc[1]==0)]

    # TODO: A more precise fix would be to keep all columns (including those with
    # no value in grant columns), but ignore/except any calculation that requires
    # either grant revenue and adm

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

    test_metrics = (
        metrics.set_index("Category")
        .T.rename_axis("Year")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    test = pd.DataFrame()
    tmp = pd.DataFrame()

#https://stackoverflow.com/questions/13331698/how-to-apply-a-function-to-two-columns-of-pandas-dataframe
    # Current Ratio
    test['Current Ratio'] = test_metrics['Current Assets']/test_metrics['Current Liabilities']
    # returns true if raio is greater than 1.1 or greater than 1 and 
    # greater than the previous year
    def ratio_metric_calc(cur,diff):
        return 'MS' if ((cur > 1.1) | ((cur > 1) & (diff == True))) else 'DNMS'
    test['Current Ratio Previous'] = test['Current Ratio'].shift(-1)
    test['Current Ratio Trend'] = test['Current Ratio'] > test['Current Ratio Previous']
    test['Current Ratio Metric'] = test.apply(lambda x: ratio_metric_calc(x['Current Ratio'], x['Current Ratio Trend']), axis=1)
    test = test.drop(columns=['Current Ratio Previous','Current Ratio Trend'], axis=1)


    # Day's Cash
    test['Days Cash'] = test_metrics['Unrestricted Cash'] / ((test_metrics['Operating Expenses'] - test_metrics['Depreciation/Amortization'])/365)
    # returns true if day's cash is > 45 or greater or equal to 30 and is greater
    # than the previous year
    def days_cash_metric_calc(cur,diff):
        return 'MS' if ((cur > 45) | ((cur >= 30) & (diff == True))) else 'DNMS'
    test['Days Cash Previous'] = test['Days Cash'].shift(-1)
    test['Days Cash Trend'] = test['Days Cash'] > test['Days Cash Previous']
    test['Days Cash Metric'] = test.apply(lambda x: days_cash_metric_calc(x['Days Cash'], x['Days Cash Trend']), axis=1)
    test = test.drop(columns=['Days Cash Previous','Days Cash Trend'], axis=1)


    # Annual Enrollment Change
    test['Annual Enrollment Change'] = (test_metrics['ADM Average'].shift() - test_metrics['ADM Average']) / test_metrics['ADM Average']
    # need to shift the column up as a result of the above shift calculation
    test['Annual Enrollment Change'] = test['Annual Enrollment Change'].shift(-1)
    test['Annual Enrollment Change Metric'] = test['Annual Enrollment Change'].apply(lambda x: 'MS' if (x > -0.1) else 'DNMS')    


    # Primary Reserve Ratio
    test['Primary Reserve Ratio'] = test_metrics['Unrestricted Net Assets'] / test_metrics['Operating Expenses']
    test['Primary Reserve Ratio Metric'] = test['Primary Reserve Ratio'].apply(lambda x: 'MS' if (x > 0.25) else 'DNMS')


    # Change in Net ASsets Margin/Aggregated Three-Year Margin
    test['Change in Net Assets Margin'] = test_metrics['Change in Net Assets'] / test_metrics['Operating Revenues'] 
    test['Aggregated Three-Year Margin'] = (test_metrics['Change in Net Assets'] + test_metrics['Change in Net Assets'].shift() + test_metrics['Change in Net Assets'].shift(2)) / \
        (test_metrics['Operating Revenues'] + test_metrics['Operating Revenues'].shift() + test_metrics['Operating Revenues'].shift(2))
    # need to shift the column up as a result of the above shift calculation
    test['Aggregated Three-Year Margin'] = test['Aggregated Three-Year Margin'].shift(-2)

    test['AgMar Previous'] = test['Aggregated Three-Year Margin'].shift(-1)
    test['AgMar Previous 2'] = test['Aggregated Three-Year Margin'].shift(-2)
    test['AgMar Trend'] = ((test['Aggregated Three-Year Margin'] > test['AgMar Previous']) & (test['AgMar Previous'] > test['AgMar Previous 2']))

    # Aggregated Three-Year Margin is positive and the most recent year Change
    # in Net Assets Margin is positive; or Aggregated Three-Year Margin is greater
    # than -1.5%, the trend is positive for the last two years, and Change in Net
    # Assets Margin for the most recent year is positive. For schools in their
    # first and second year of operation, the cumulative Change in Net Assets
    # Margin must be positive.
    def asset_margin_calc(chcur,agcur,diff):
        return 'MS' if ((
            (chcur > 0) & (agcur > 0)) | \
            (((chcur > 0) & (agcur > .015)) & (diff == True)) \
        ) else 'DNMS'

    test['Aggregated Three-Year Margin Metric'] = test.apply(lambda x: asset_margin_calc(x['Change in Net Assets Margin'], x['Aggregated Three-Year Margin'],x['AgMar Trend']), axis=1)
    
    # TODO:
    # If test['Aggregated Three-Year Margin'].isnan
    # then test['Aggregated Three-Year Margin Metric'] = N/A

    # TODO:
    # If Y1 or Y2 and CHNM is > 0 then  test['Change in Net Assets Margin Metric']
    # should be MS  
    print(test.T)

    # TODO: Need to figure out the "Must have equal len keys and value when
    # setting with an ndarray" error
    # TODO: Account for the First two years CHNM positive

    test['Change in Net Assets Margin Metric'] = test['Change in Net Assets Margin'].apply(lambda x: 'MS' if (x > 0) else 'DNMS')
    
    # Create a separate df to do the accountabilities calcuations
    # tmp['Aggregated Three-Year Margin'] = test['Aggregated Three-Year Margin'].copy()
    
    # # create temporary columns with shifted values to do comparisons
    # tmp['P'] = tmp['Aggregated Three-Year Margin'].shift(-1)
    # tmp['P2'] = tmp['Aggregated Three-Year Margin'].shift(-2)
    # # create temporary column that is true if the trend is positive for the last
    # # two years (e.g., CY > PY and PY > PY2)
    # tmp['Meets'] = (tmp['Aggregated Three-Year Margin'] > tmp['P']) & (tmp['P'] > tmp['P2'])

    # # delete first two rows (caused by shifting)
    # tmp = tmp.iloc[2:]
    # tmp=tmp.reset_index(drop=True)

    # # drop ATYM column from df and add the tmp columns instead
    # test = test.drop(columns=['Aggregated Three-Year Margin'], axis=1)
    # test = test.join(tmp[['Aggregated Three-Year Margin','Meets']])

    # # the test
    # test['Acctbility Standard'] = ((test['Change in Net Assets Margin'] > 0) & (test['Aggregated Three-Year Margin'] > 0)) | \
    #     ((test['Change in Net Assets Margin'] > 0) & (test['Aggregated Three-Year Margin'] > -.015) & (test['Meets'] == True))

    # # drop last temp column
    # test = test.drop(columns=['Meets'], axis=1)

    #test['Change in Net Assets Margin Metric'] = test['Change in Net Assets Margin'].apply(lambda x: 'MS' if (x > 0) else 'DNMS')


    # Debt to Asset Ratio
    test['Debt to Asset Ratio'] = test_metrics['Total Liabilities'] / test_metrics['Total Assets']
    test['Debt to Asset Ratio Metric'] = test['Debt to Asset Ratio'].apply(lambda x: 'MS' if (x < 0.9) else 'DNMS')    


    # Cash Flow and Multi-Year Cash Flow
    # Multi-Year Cash Flow is positive and One Year Cash Flow is positive in two
    # out of three years, including the most recent year. For schools in the first
    # two years of operation, both years must have a positive Cash Flow (for
    # purposes of calculating Cash Flow, the school's Year 0 balance is assumed
    # to be zero).

    test['Cash Flow'] = test_metrics['Unrestricted Cash'].shift() - test_metrics['Unrestricted Cash']
    # need to shift the column up as a result of the above shift calculation
    test['Cash Flow'] = test['Cash Flow'].shift(-1)

    # first value in cash flow will always be the value of the first
    # year of unrestricted cash - so add last value of unrestricted cash
    # to last value of Cash Flow (not added as new row, replacing last row)
    test.loc[len(test['Cash Flow'])-1,'Cash Flow'] = test_metrics['Unrestricted Cash'].iloc[-1]
    #test = test.append({'Cash Flow':test_metrics['Unrestricted Cash'].iloc[-1]}, ignore_index=True)

    test['Multi-Year Cash Flow'] = test_metrics['Unrestricted Cash'].shift(2) - test_metrics['Unrestricted Cash']
    # need to shift the column up twice as a result of the above shift calculation
    test['Multi-Year Cash Flow'] = test['Multi-Year Cash Flow'].shift(-2)

    # Debt Service Coverage Ratio
    test['Debt Service Coverage Ratio'] = (test_metrics['Change in Net Assets'] + test_metrics['Lease/Mortgage Payments'] + test_metrics['Depreciation/Amortization'] + test_metrics['Interest Expense']) / (test_metrics['Lease/Mortgage Payments'] + test_metrics['Principal Payments'] + test_metrics['Interest Expense'])
    test['Debt Service Coverage Ratio Metric'] = test['Debt Service Coverage Ratio'].apply(lambda x: 'MS' if (x > 1) else 'DNMS')    
    
    # print(test.T)

    test.T.to_csv('calc_test.csv', index=True)

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

            aggregated_3_year_margin = \
                (metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0]) / \
                (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0])
            
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
        elif ((y - i) >= 3 and ((y - i) <= 4)):
            if (chNetAssMar[i] > 0 and aggMar[i] > 0):
                r_assetMar.append("MS")
                r_aggMar.append("MS")
            else:
                r_assetMar.append("DNMS")
                r_aggMar.append("DNMS")
        else:

            # NOTE: The calculation for Aggregated Three-Year Margin is: 1) ATYM is positive and the
            # most recent year Change in Net Assets Margin is positive; or 2) Aggregated Three-Year
            # Margin is greater than -1.5%, the trend is positive for the last two years, and Change
            # in Net Assets Margin for the most recent year is positive.
            # The algorithm in use considers "two year trend" to mean: CY < PY and PY < PY2 
            
            # Commented out code treats trend as: CY < PY
            # if ((chNetAssMar[i] > 0 and aggMar[i] > 0) or ((chNetAssMar[i] > 0 and aggMar[i] > -.015) and
            # (aggMar[i] > ((metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0]) / (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0] + metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+3]].values[0]))))):

            aggregated_3_year_margin_previous_year = \
                (metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+1]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0]) / \
                (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+1]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+3]].values[0])

            aggregated_3_year_margin_previous_year_2 = \
                (metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+2]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+3]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i+4]].values[0]) / \
                (metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+2]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+3]].values[0] + 
                metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i+4]].values[0])

            if (
                    (chNetAssMar[i] > 0 and aggMar[i] > 0) or
                    (
                        (chNetAssMar[i] > 0 and aggMar[i] > -.015) and
                        (aggMar[i] > aggregated_3_year_margin_previous_year) and
                        (aggregated_3_year_margin_previous_year > aggregated_3_year_margin_previous_year_2)
                    )
                ):

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