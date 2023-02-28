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

# Caclulate metrics based on ICSB Accountability System financial framework
def calculate_metrics(metrics):

    metrics2 = metrics.copy()
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
        chNetAssMar.append(metrics.loc[metrics['Category'].isin(['Change in Net Assets'])][year[i]].values[0] / metrics.loc[metrics['Category'].isin(['Operating Revenues'])][year[i]].values[0])
        
        if ((y - i) <= 2):
            aggMar.append(-999)
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

## NOTE: REWORK STARTS HERE ##
## TODO: TEST FOR ALL YEARS - ERRORS:
#   IndexError: index -2 is out of bounds for axis 0 with size 1 (Many Schools - Early Years)
#   ValueError: Must have equal len keys and value when setting with an ndarray (Excel-Lafayette 2021)
#   
    # Need to handle pre-opening year data where there is financial activity
    # but school is not receiving state/federal grants. This 'easy' fix ignore
    # all columns (years) where the value in the State Grant column is equal to '0'
    metrics2 = metrics2.loc[:,~(metrics2.iloc[1]==0)]

    # TODO: A more precise fix would be to keep all columns (including those with
    # no value in grant columns), but ignore/except any calculation that requires
    # either grant revenue and adm

    columns = list(metrics2)

    # get year headers as array of strings in descending order
    year = columns
    del year[0]

    y = len(year)

    # convert all values to integers
    for col in columns:
        metrics2[col] = pd.to_numeric(metrics2[col], errors='coerce')

    metrics = (
        metrics2.set_index("Category")
        .T.rename_axis("Year")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    metric_grid = pd.DataFrame()

    # Current Ratio
    metric_grid['Current Ratio'] = metrics['Current Assets']/metrics['Current Liabilities']
    
    # returns true if 'Current Ratio' is > 1.1 or > 1 and CY > PY 
    def ratio_metric_calc(cur,diff):
        return 'MS' if ((cur > 1.1) | ((cur > 1) & (diff == True))) else 'DNMS'
    
    # create a temporary column that is shifted up for calculations
    metric_grid['Current Ratio Previous'] = metric_grid['Current Ratio'].shift(-1)

    metric_grid['Current Ratio Trend'] = metric_grid['Current Ratio'] > metric_grid['Current Ratio Previous']
    metric_grid['Current Ratio Metric'] = metric_grid.apply(lambda x: ratio_metric_calc(x['Current Ratio'], x['Current Ratio Trend']), axis=1)

    # Day's Cash
    metric_grid['Days Cash'] = metrics['Unrestricted Cash'] / ((metrics['Operating Expenses'] - metrics['Depreciation/Amortization'])/365)
   
    # returns true if day's cash is > 45 or >= 30 and CY > PY
    def days_cash_metric_calc(cur,diff):
        return 'MS' if ((cur > 45) | ((cur >= 30) & (diff == True))) else 'DNMS'
   
    metric_grid['Days Cash Previous'] = metric_grid['Days Cash'].shift(-1)
    metric_grid['Days Cash Trend'] = metric_grid['Days Cash'] > metric_grid['Days Cash Previous']
    metric_grid['Days Cash Metric'] = metric_grid.apply(lambda x: days_cash_metric_calc(x['Days Cash'], x['Days Cash Trend']), axis=1)

    # Annual Enrollment Change
    metric_grid['Annual Enrollment Change'] = (metrics['ADM Average'].shift() - metrics['ADM Average']) / metrics['ADM Average']
    
    # Any shift used as part of a calculation causes the calculated value to be offset by
    # the amount of the shift, so we account for this by shifting the calculated column up
    # by the amount of the original shift
    metric_grid['Annual Enrollment Change'] = metric_grid['Annual Enrollment Change'].shift(-1)
    metric_grid['Annual Enrollment Change Metric'] = metric_grid['Annual Enrollment Change'].apply(lambda x: 'MS' if (x > -0.1) else 'DNMS')    

    # if AEC is NaN (no calculation is possible), AEC Metric should be N/A
    metric_grid.loc[metric_grid['Annual Enrollment Change'].isnull(), 'Annual Enrollment Change Metric'] = 'N/A'

    # Primary Reserve Ratio
    metric_grid['Primary Reserve Ratio'] = metrics['Unrestricted Net Assets'] / metrics['Operating Expenses']
    metric_grid['Primary Reserve Ratio Metric'] = metric_grid['Primary Reserve Ratio'].apply(lambda x: 'MS' if (x > 0.25) else 'DNMS')

  
    # Change in Net Assets Margin/Aggregated Three-Year Margin
    metric_grid['Change in Net Assets Margin'] = metrics['Change in Net Assets'] / metrics['Operating Revenues'] 
    metric_grid['Aggregated Three-Year Margin'] = (metrics['Change in Net Assets'] + metrics['Change in Net Assets'].shift() + metrics['Change in Net Assets'].shift(2)) / \
        (metrics['Operating Revenues'] + metrics['Operating Revenues'].shift() + metrics['Operating Revenues'].shift(2))

    metric_grid['Aggregated Three-Year Margin'] = metric_grid['Aggregated Three-Year Margin'].shift(-2)

    # create temporary columns for calculations include values from previous year
    metric_grid['AgMar Previous'] = metric_grid['Aggregated Three-Year Margin'].shift(-1)
    metric_grid['AgMar Previous 2'] = metric_grid['Aggregated Three-Year Margin'].shift(-2)
    metric_grid['AgMar Trend'] = ((metric_grid['Aggregated Three-Year Margin'] > metric_grid['AgMar Previous']) & (metric_grid['AgMar Previous'] > metric_grid['AgMar Previous 2']))

    # A school meets standard if: Aggregated Three-Year Margin is positive and the most
    # recent year Change in Net Assets Margin is positive; or Aggregated Three-Year Margin
    # is greater than -1.5%, the trend is positive for the last two years, and Change in Net
    # Assets Margin for the most recent year is positive. For schools in their first and
    # second year of operation, the cumulative Change in Net Assets Margin must be positive.
    def asset_margin_calc(chcur,agcur,diff):
        return 'MS' if ((
            (chcur > 0) & (agcur > 0)) | \
            (((chcur > 0) & (agcur > .015)) & (diff == True)) \
        ) else 'DNMS'

    metric_grid['Aggregated Three-Year Margin Metric'] = metric_grid.apply(lambda x: asset_margin_calc(x['Change in Net Assets Margin'], x['Aggregated Three-Year Margin'],x['AgMar Trend']), axis=1)
    metric_grid['Change in Net Assets Margin Metric'] = metric_grid.apply(lambda x: asset_margin_calc(x['Change in Net Assets Margin'], x['Aggregated Three-Year Margin'],x['AgMar Trend']), axis=1)
    
    # if ATYM is NaN (no calculation is possible), ATYM Metric should be N/A
    metric_grid.loc[metric_grid['Aggregated Three-Year Margin'].isnull(), 'Aggregated Three-Year Margin Metric'] = 'N/A'

    print('Testing Error 1 - 1')

    # in the dataframe, each row is a year, with earliest years at the end. In YR 1 and Y2
    # CHNM Metric is 'MS' if the cumulative value of CHNM is > 0 (positive)
    if metric_grid.loc[metric_grid.index[-1],'Change in Net Assets Margin'] > 0:
        metric_grid.loc[metric_grid.index[-1], 'Change in Net Assets Margin Metric'] = 'MS'
    else:
        metric_grid.loc[metric_grid.index[-1], 'Change in Net Assets Margin Metric'] = 'DNMS'
    
    # CHNM Metric is 'MS' if first + second year value is > 0
    # Only test if there are at least 2 years of data
    if len(metric_grid.index) >= 2:
        if (metric_grid.loc[metric_grid.index[-1],'Change in Net Assets Margin'] + metric_grid.loc[metric_grid.index[-2],'Change in Net Assets Margin']) > 0:
            metric_grid.loc[metric_grid.index[-2],'Change in Net Assets Margin Metric'] = 'MS'
        else:
            metric_grid.loc[metric_grid.index[-2], 'Change in Net Assets Margin Metric'] = 'DNMS'

    # Debt to Asset Ratio
    metric_grid['Debt to Asset Ratio'] = metrics['Total Liabilities'] / metrics['Total Assets']
    metric_grid['Debt to Asset Ratio Metric'] = metric_grid['Debt to Asset Ratio'].apply(lambda x: 'MS' if (x < 0.9) else 'DNMS')    

    # Cash Flow and Multi-Year Cash Flow
    metric_grid['Cash Flow'] = metrics['Unrestricted Cash'].shift() - metrics['Unrestricted Cash']
    metric_grid['Cash Flow'] = metric_grid['Cash Flow'].shift(-1)

    # the YR1 value of 'Cash Flow' is equal to the YR1 value of 'Unrestricted Cash'
    metric_grid.loc[len(metric_grid['Cash Flow'])-1,'Cash Flow'] = metrics['Unrestricted Cash'].iloc[-1]

    metric_grid['Multi-Year Cash Flow'] = metrics['Unrestricted Cash'].shift(2) - metrics['Unrestricted Cash']
    metric_grid['Multi-Year Cash Flow'] = metric_grid['Multi-Year Cash Flow'].shift(-2)

    # A school meets standard if both CY Multi-Year Cash Flow and One Year Cash Flow
    # are positive and one out of the two previous One Year Cash Flows are positive
    # For schools in the first two years of operation, both years must have a positive
    # Cash Flow (for purposes of calculating Cash Flow, the school's Year 0 balance is
    # assumed to be zero).

    # NOTE: I am positive there is a more pythonic way to do this, but I'm to tired
    # to figure it out, maybe later

    for i in range(len(metric_grid['Cash Flow'])-2):
        # get current year value
        current_year_cash = metric_grid.loc[i,'Cash Flow']
        # determine if two previous years are greater than zero (TRUE or FALSE)
        previous_year_cash = metric_grid.loc[i+1,'Cash Flow'] > 0
        second_previous_year_cash = metric_grid.loc[i+2,'Cash Flow'] > 0

        # if current year Cash Flow value and current year Multi-Year Cash Flow
        # value are positive and at least one of the previous two years are
        # positive. int converts booleans to 0 (false) or 1 (true), if added
        # a value of 1 or 2 means one or both years were positive
        if (metric_grid.loc[i]['Multi-Year Cash Flow'] > 0) & (current_year_cash > 0) & \
            ((int(previous_year_cash) + int(second_previous_year_cash)) >= 1):
            
            metric_grid.loc[i,'Cash Flow Metric'] = 'MS'
            metric_grid.loc[i,'Multi-Year Cash Flow Metric'] = 'MS'            
        else:
            
            metric_grid.loc[i,'Multi-Year Cash Flow Metric'] = 'DNMS'
            metric_grid.loc[i,'Cash Flow Metric'] = 'DNMS'

    # A school meets standard if Cash Flow is positive in first two years (see above)
    # TODO: CHeck to see if need to set else as DNMS

    if metric_grid.loc[metric_grid.index[-1],'Cash Flow'] > 0:
        metric_grid.loc[metric_grid.index[-1], 'Cash Flow Metric'] = 'MS'
    else:
        metric_grid.loc[metric_grid.index[-2],'Cash Flow Metric'] = 'DNMS'

    # CHNM Metric is 'MS' if first + second year value is > 0
    # Only test if there are at least 2 years of data
    if len(metric_grid.index) >= 2:        
        if (metric_grid.loc[metric_grid.index[-1],'Cash Flow'] > 0) & (metric_grid.loc[metric_grid.index[-2],'Cash Flow'] > 0):
            metric_grid.loc[metric_grid.index[-2],'Cash Flow Metric'] = 'MS'
        else:
            metric_grid.loc[metric_grid.index[-2],'Cash Flow Metric'] = 'DNMS'

    # if Multi-Year Cash Flow is NaN (no calculation is possible), Multi-Year Cash FlowMetric should be N/A
    metric_grid.loc[metric_grid['Multi-Year Cash Flow'].isnull(), 'Multi-Year Cash Flow Metric'] = 'N/A'

    # Debt Service Coverage Ratio
    metric_grid['Debt Service Coverage Ratio'] = (metrics['Change in Net Assets'] + metrics['Lease/Mortgage Payments'] + metrics['Depreciation/Amortization'] + metrics['Interest Expense']) / (metrics['Lease/Mortgage Payments'] + metrics['Principal Payments'] + metrics['Interest Expense'])
    metric_grid['Debt Service Coverage Ratio Metric'] = metric_grid['Debt Service Coverage Ratio'].apply(lambda x: 'MS' if (x > 1) else 'DNMS')    
    
    # Drop all temporary (calculation) columns
    metric_grid = metric_grid.drop(columns=['Days Cash Previous','Days Cash Trend','Current Ratio Previous','Current Ratio Trend','AgMar Previous','AgMar Previous 2','AgMar Trend'], axis=1)

    metric_grid['Year'] = metrics['Year']

    # Transpose
    metric_grid = (
        metric_grid.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    # Because this is for display, we need to manually reorder the columns
    def sort_metrics(column):
        reorder = [
            'Current Ratio','Current Ratio Metric',
            'Days Cash','Days Cash Metric',
            'Annual Enrollment Change', 'Annual Enrollment Change Metric',
            'Primary Reserve Ratio', 'Primary Reserve Ratio Metric',
            'Change in Net Assets Margin', 'Change in Net Assets Margin Metric',
            'Aggregated Three-Year Margin', 'Aggregated Three-Year Margin Metric',
            'Debt to Asset Ratio', 'Debt to Asset Ratio Metric',
            'Cash Flow', 'Cash Flow Metric',
            'Multi-Year Cash Flow', 'Multi-Year Cash Flow Metric',
            'Debt Service Coverage Ratio', 'Debt Service Coverage Ratio Metric',
        ]
        # This also works:
        # mapper = {name: order for order, name in enumerate(reorder)}
        # return column.map(mapper)
        cat = pd.Categorical(column, categories=reorder, ordered=True)
        return pd.Series(cat)

    metric_grid_sorted = metric_grid.sort_values(by='Category', key=sort_metrics)

    final_grid = pd.DataFrame()

    # Restructure dataframe so that every other row (Metrics) become columns
    # https://stackoverflow.com/questions/36181622/moving-every-other-row-to-a-new-column-and-group-pandas-python
    cols=[i for i in metric_grid_sorted if i not in ['Category']]

    for col in cols:
        final_grid[col] = metric_grid_sorted[col].iloc[::2].values
        final_grid[col + 'Rating'] = metric_grid_sorted[col].iloc[1::2].values
 
    # Add the Categories Back without the Metric Rows
    new_cols = pd.DataFrame()
    new_cols['Category'] = metric_grid_sorted['Category']
    new_cols = new_cols[~new_cols['Category'].str.contains("Metric")]
    new_cols = new_cols.reset_index()

    final_grid.insert(0, "Category", new_cols['Category'])

    # Remove years String from Rating Columns
    final_grid.columns = final_grid.columns.str.replace(r'\d{4}Rating', 'Rating', regex=True)

    # Add 'Near Term|Long Term' titles
    # Why is the simple shit so hard?

    # add in between existing indexes, sorting and then resetting
    final_grid.loc[3.5,'Category'] = 'Long Term'
    final_grid = final_grid.sort_index().reset_index(drop=True)
    
    # because this is the first row, we use
    # indexing: setting with enlargement
    final_grid.loc[-1, 'Category'] = 'Near Term'
    final_grid.index = final_grid.index + 1
    final_grid = final_grid.sort_index() 

    print(final_grid)

    print('-----------')

    print(summary)

    return summary

def calculate_metrics2(data):
    """
    Caclulate financial metrics and financial accountability ratings
    based on ICSBs Accountability System financial framework
    """
    # TODO: ADM is incorrect because up to date ADM is in school_index and
    # not financial file

    # Need to handle pre-opening year data where there is financial activity
    # but school is not receiving state/federal grants. This 'easy' fix ignore
    # all columns (years) where the value in the State Grant column is equal to '0'
    data = data.loc[:,~(data.iloc[1]==0)]

    # TODO: A more precise fix would be to keep all columns (including those with
    # no value in grant columns), but ignore/except any calculation that requires
    # either grant revenue and adm

    columns = list(data)

    # get year headers as array of strings in descending order
    # year = columns
    # del year[0]

    # convert all values to integers
    for col in columns:
        data[col] = pd.to_numeric(data[col], errors='coerce')

    metrics = (
        data.set_index("Category")
        .T.rename_axis("Year")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    metric_grid = pd.DataFrame()

    # Current Ratio
    metric_grid['Current Ratio'] = metrics['Current Assets']/metrics['Current Liabilities']
    
    # returns true if 'Current Ratio' is > 1.1 or > 1 and CY > PY 
    def ratio_metric_calc(cur,diff):
        return 'MS' if ((cur > 1.1) | ((cur > 1) & (diff == True))) else 'DNMS'
    
    # create a temporary column that is shifted up for calculations
    metric_grid['Current Ratio Previous'] = metric_grid['Current Ratio'].shift(-1)

    metric_grid['Current Ratio Trend'] = metric_grid['Current Ratio'] > metric_grid['Current Ratio Previous']
    metric_grid['Current Ratio Metric'] = metric_grid.apply(lambda x: ratio_metric_calc(x['Current Ratio'], x['Current Ratio Trend']), axis=1)

    # Day's Cash
    metric_grid['Days Cash'] = metrics['Unrestricted Cash'] / ((metrics['Operating Expenses'] - metrics['Depreciation/Amortization'])/365)
   
    # returns true if day's cash is > 45 or >= 30 and CY > PY
    def days_cash_metric_calc(cur,diff):
        return 'MS' if ((cur > 45) | ((cur >= 30) & (diff == True))) else 'DNMS'
   
    metric_grid['Days Cash Previous'] = metric_grid['Days Cash'].shift(-1)
    metric_grid['Days Cash Trend'] = metric_grid['Days Cash'] > metric_grid['Days Cash Previous']
    metric_grid['Days Cash Metric'] = metric_grid.apply(lambda x: days_cash_metric_calc(x['Days Cash'], x['Days Cash Trend']), axis=1)

    # Annual Enrollment Change
    metric_grid['Annual Enrollment Change'] = (metrics['ADM Average'].shift() - metrics['ADM Average']) / metrics['ADM Average']
    
    # Any shift used as part of a calculation causes the calculated value to be offset by
    # the amount of the shift, so we account for this by shifting the calculated column up
    # by the amount of the original shift
    metric_grid['Annual Enrollment Change'] = metric_grid['Annual Enrollment Change'].shift(-1)
    metric_grid['Annual Enrollment Change Metric'] = metric_grid['Annual Enrollment Change'].apply(lambda x: 'MS' if (x > -0.1) else 'DNMS')    

    # Primary Reserve Ratio
    metric_grid['Primary Reserve Ratio'] = metrics['Unrestricted Net Assets'] / metrics['Operating Expenses']
    metric_grid['Primary Reserve Ratio Metric'] = metric_grid['Primary Reserve Ratio'].apply(lambda x: 'MS' if (x > 0.25) else 'DNMS')

    # Change in Net Assets Margin/Aggregated Three-Year Margin
    metric_grid['Change in Net Assets Margin'] = metrics['Change in Net Assets'] / metrics['Operating Revenues'] 
    metric_grid['Aggregated Three-Year Margin'] = (metrics['Change in Net Assets'] + metrics['Change in Net Assets'].shift() + metrics['Change in Net Assets'].shift(2)) / \
        (metrics['Operating Revenues'] + metrics['Operating Revenues'].shift() + metrics['Operating Revenues'].shift(2))

    metric_grid['Aggregated Three-Year Margin'] = metric_grid['Aggregated Three-Year Margin'].shift(-2)

    # create temporary columns for calculations include values from previous year
    metric_grid['AgMar Previous'] = metric_grid['Aggregated Three-Year Margin'].shift(-1)
    metric_grid['AgMar Previous 2'] = metric_grid['Aggregated Three-Year Margin'].shift(-2)
    metric_grid['AgMar Trend'] = ((metric_grid['Aggregated Three-Year Margin'] > metric_grid['AgMar Previous']) & (metric_grid['AgMar Previous'] > metric_grid['AgMar Previous 2']))

    # A school meets standard if: Aggregated Three-Year Margin is positive and the most
    # recent year Change in Net Assets Margin is positive; or Aggregated Three-Year Margin
    # is greater than -1.5%, the trend is positive for the last two years, and Change in Net
    # Assets Margin for the most recent year is positive. For schools in their first and
    # second year of operation, the cumulative Change in Net Assets Margin must be positive.
    def asset_margin_calc(chcur,agcur,diff):
        return 'MS' if ((
            (chcur > 0) & (agcur > 0)) | \
            (((chcur > 0) & (agcur > .015)) & (diff == True)) \
        ) else 'DNMS'

    metric_grid['Aggregated Three-Year Margin Metric'] = metric_grid.apply(lambda x: asset_margin_calc(x['Change in Net Assets Margin'], x['Aggregated Three-Year Margin'],x['AgMar Trend']), axis=1)
    metric_grid['Change in Net Assets Margin Metric'] = metric_grid.apply(lambda x: asset_margin_calc(x['Change in Net Assets Margin'], x['Aggregated Three-Year Margin'],x['AgMar Trend']), axis=1)
    
    # if ATYM is NaN (no calculation is possible), ATYM Metric should be N/A
    metric_grid.loc[metric_grid['Aggregated Three-Year Margin'].isnull(), 'Aggregated Three-Year Margin Metric'] = 'N/A'

    # in the dataframe, each row is a year, with earliest years at the end. In YR 1 and Y2
    # CHNM Metric is 'MS' if the cumulative value of CHNM is > 0 (positive)
    # TODO: CHeck to see if need to set else as DNMS
    if metric_grid.loc[metric_grid.index[-1],'Change in Net Assets Margin'] > 0:
        metric_grid.loc[metric_grid.index[-1], 'Change in Net Assets Margin Metric'] = 'MS'
    else:
        metric_grid.loc[metric_grid.index[-1], 'Change in Net Assets Margin Metric'] = 'DNMS'
    # CHNM Metric is 'MS' if first + second year value is > 0
    if (metric_grid.loc[metric_grid.index[-1],'Change in Net Assets Margin'] + metric_grid.loc[metric_grid.index[-2],'Change in Net Assets Margin']) > 0:
        metric_grid.loc[metric_grid.index[-2],'Change in Net Assets Margin Metric'] = 'MS'
    else:
        metric_grid.loc[metric_grid.index[-2], 'Change in Net Assets Margin Metric'] = 'DNMS'

    # Debt to Asset Ratio
    metric_grid['Debt to Asset Ratio'] = metrics['Total Liabilities'] / metrics['Total Assets']
    metric_grid['Debt to Asset Ratio Metric'] = metric_grid['Debt to Asset Ratio'].apply(lambda x: 'MS' if (x < 0.9) else 'DNMS')    

    # Cash Flow and Multi-Year Cash Flow
    metric_grid['Cash Flow'] = metrics['Unrestricted Cash'].shift() - metrics['Unrestricted Cash']
    metric_grid['Cash Flow'] = metric_grid['Cash Flow'].shift(-1)

    # the YR1 value of 'Cash Flow' is equal to the YR1 value of 'Unrestricted Cash'
    metric_grid.loc[len(metric_grid['Cash Flow'])-1,'Cash Flow'] = metrics['Unrestricted Cash'].iloc[-1]

    metric_grid['Multi-Year Cash Flow'] = metrics['Unrestricted Cash'].shift(2) - metrics['Unrestricted Cash']
    metric_grid['Multi-Year Cash Flow'] = metric_grid['Multi-Year Cash Flow'].shift(-2)

    # A school meets standard if both CY Multi-Year Cash Flow and One Year Cash Flow
    # are positive and one out of the two previous One Year Cash Flows are positive
    # For schools in the first two years of operation, both years must have a positive
    # Cash Flow (for purposes of calculating Cash Flow, the school's Year 0 balance is
    # assumed to be zero).

    # NOTE: I am positive there is a more pythonic way to do this, but I'm to tired
    # to figure it out, maybe later
    for i in range(len(metric_grid['Cash Flow'])-2):
        # get current year value
        current_year_cash = metric_grid.loc[i,'Cash Flow']
        # determine if two previous years are greater than zero (TRUE or FALSE)
        previous_year_cash = metric_grid.loc[i+1,'Cash Flow'] > 0
        second_previous_year_cash = metric_grid.loc[i+2,'Cash Flow'] > 0

        # if current year Cash Flow value and current year Multi-Year Cash Flow
        # value are positive and at least one of the previous two years are
        # positive. int converts booleans to 0 (false) or 1 (true), if added
        # a value of 1 or 2 means one or both years were positive
        if (metric_grid.loc[i]['Multi-Year Cash Flow'] > 0) & (current_year_cash > 0) & \
            ((int(previous_year_cash) + int(second_previous_year_cash)) >= 1):
            
            metric_grid.loc[i,'Cash Flow Metric'] = 'MS'
            metric_grid.loc[i,'Multi-Year Cash Flow Metric'] = 'MS'            
        else:
            
            metric_grid.loc[i,'Multi-Year Cash Flow Metric'] = 'DNMS'
            metric_grid.loc[i,'Cash Flow Metric'] = 'DNMS'

    # A school meets standard if Cash Flow is positive in first two years (see above)
    # TODO: CHeck to see if need to set else as DNMS
    if metric_grid.loc[metric_grid.index[-1],'Cash Flow'] > 0:
        metric_grid.loc[metric_grid.index[-1], 'Cash Flow Metric'] = 'MS'
    else:
        metric_grid.loc[metric_grid.index[-2],'Cash Flow Metric'] = 'DNMS'

    # CHNM Metric is 'MS' if first + second year value is > 0
    if (metric_grid.loc[metric_grid.index[-1],'Cash Flow'] > 0) & (metric_grid.loc[metric_grid.index[-2],'Cash Flow'] > 0):
        metric_grid.loc[metric_grid.index[-2],'Cash Flow Metric'] = 'MS'
    else:
        metric_grid.loc[metric_grid.index[-2],'Cash Flow Metric'] = 'DNMS'

    # if Multi-Year Cash Flow is NaN (no calculation is possible), Multi-Year Cash FlowMetric should be N/A
    metric_grid.loc[metric_grid['Multi-Year Cash Flow'].isnull(), 'Multi-Year Cash Flow Metric'] = 'N/A'

    # Debt Service Coverage Ratio
    metric_grid['Debt Service Coverage Ratio'] = (metrics['Change in Net Assets'] + metrics['Lease/Mortgage Payments'] + metrics['Depreciation/Amortization'] + metrics['Interest Expense']) / (metrics['Lease/Mortgage Payments'] + metrics['Principal Payments'] + metrics['Interest Expense'])
    metric_grid['Debt Service Coverage Ratio Metric'] = metric_grid['Debt Service Coverage Ratio'].apply(lambda x: 'MS' if (x > 1) else 'DNMS')    
    
    # Drop all temporary (calculation) columns
    metric_grid = metric_grid.drop(columns=['Days Cash Previous','Days Cash Trend','Current Ratio Previous','Current Ratio Trend','AgMar Previous','AgMar Previous 2','AgMar Trend'], axis=1)

    metric_grid['Year'] = metrics['Year']

    # Transpose
    metric_grid = (
        metric_grid.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    # Because this is for display, we need to manually reorder the columns
    def sort_metrics(column):
        reorder = [
            'Current Ratio','Current Ratio Metric',
            'Days Cash','Days Cash Metric',
            'Annual Enrollment Change', 'Annual Enrollment Change Metric',
            'Primary Reserve Ratio', 'Primary Reserve Ratio Metric',
            'Change in Net Assets Margin', 'Change in Net Assets Margin Metric',
            'Aggregated Three-Year Margin', 'Aggregated Three-Year Margin Metric',
            'Debt to Asset Ratio', 'Debt to Asset Ratio Metric',
            'Cash Flow', 'Cash Flow Metric',
            'Multi-Year Cash Flow', 'Multi-Year Cash Flow Metric',
            'Debt Service Coverage Ratio', 'Debt Service Coverage Ratio Metric',
        ]
        # This also works:
        # mapper = {name: order for order, name in enumerate(reorder)}
        # return column.map(mapper)
        cat = pd.Categorical(column, categories=reorder, ordered=True)
        return pd.Series(cat)

    metric_grid_sorted = metric_grid.sort_values(by='Category', key=sort_metrics)

    final_grid = pd.DataFrame()

    # Restructure dataframe so that every other row (Metrics) become columns
    # https://stackoverflow.com/questions/36181622/moving-every-other-row-to-a-new-column-and-group-pandas-python
    cols=[i for i in metric_grid_sorted if i not in ['Category']]

    for col in cols:
        final_grid[col] = metric_grid_sorted[col].iloc[::2].values
        final_grid[col + 'Rating'] = metric_grid_sorted[col].iloc[1::2].values
 
    # Add the Categories Back without the Metric Rows
    new_cols = pd.DataFrame()
    new_cols['Category'] = metric_grid_sorted['Category']
    new_cols = new_cols[~new_cols['Category'].str.contains("Metric")]
    new_cols = new_cols.reset_index()

    final_grid.insert(0, "Category", new_cols['Category'])

    final_grid.columns = final_grid.columns.str.replace(r'\d{4}Rating', 'Rating', regex=True)

    print(final_grid)

    print('HERE?')

    ## NOTE: See financial_metrics.py for formula definitions
    # mcolumns = [x for x in itertools.chain.from_iterable(itertools.zip_longest(columns,rating)) if x]
    # mcolumns.insert(0,'Metric')
    # subhead1 = ['Near Term']
    # subhead2 = ['Long Term']

    # summary = pd.DataFrame([subhead1,m1,m2,m3,m4,subhead2,m5,m6,m7,m8,m9,m10],columns=mcolumns)

    print('HERE!!')
    return final_grid