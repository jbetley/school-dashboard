'''
Calculation Functions for ICSB Dashboard
'''
import pandas as pd
import numpy as np
# import itertools
import scipy.spatial as spatial

def calculate_percentage(numerator,denominator):
    """
    Calculates a percentage taking into account a string representing insufficent n-size ('***') and
    special cases where a '0' result has a different meaning. The function does the following:
        1) When either the numerator or the denominator is equal to '***', the function returns '****'
        2) When either the numerator or the denominator is null/nan, the function returns 'None'
        3) When the numerator is null/nan, but the denominatir is not, the function returns '0'
        4) if none of the above are true, the function divides the numerator by the denominator.
    """
    return np.where(
        (numerator == "***") | (denominator == "***"),
        "***",
        np.where(
            (numerator.isna()) & (denominator.isna()),
            None,
            np.where(
                numerator.isna(),
                0,
                pd.to_numeric(numerator, errors="coerce")
                / pd.to_numeric(denominator, errors="coerce"),
            ),
        ),
    )


def calculate_difference(value1, value2):
    """
    Calculate difference between two dataframes with specific mixed datatypes
    and conditions.
    """
    return np.where(
        (value1 == "***") | (value2 == "***"),
        "***",
        np.where(
            value1.isna(),
            None,
            pd.to_numeric(value1, errors="coerce")
            - pd.to_numeric(value2, errors="coerce"),
        ),
    )

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
# NOTE: This was refactored (03.01.23) to use vectorized operations. Not sure
# that the refactored version is easier to comprehend than the previous
# loop version. it is also longer.

## TODO: TEST FOR ALL YEARS - ERRORS:
#   IndexError: index -2 is out of bounds for axis 0 with size 1 (Many Schools - Early Years) Excel Elkhart
#   ValueError: Must have equal len keys and value when setting with an ndarray (Excel-Lafayette 2021)

def calculate_metrics(data):
    # Some schools have 'pre-opening' financial activity before the school
    # begins to operate and receive state/federal grants. The below code
    # ignores all columns (years) where the value in the State Grant column
    # is equal to '0'. Any pre-opening data will be lost
    operating_data = data.loc[:,~(data.iloc[1]==0)].copy()

    # print(operating_data)
    # TODO: A more precise fix would be to keep all columns (including those with
    # no value in grant columns), but ignore/except (N/A) any calculation that requires
    # either grant revenue or adm. Need to test

# https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas

    cols = [i for i in operating_data.columns if i not in ['Category']]

    for col in cols:
        operating_data[col] = pd.to_numeric(operating_data[col], errors='coerce')

    # transpose financial information
    metrics = (
        operating_data.set_index("Category")
        .T.rename_axis("Year")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    # create a dataframe for the financial metric table
    metric_grid = pd.DataFrame()

    # Current Ratio calculation
    metric_grid['Current Ratio'] = metrics['Current Assets']/metrics['Current Liabilities']
    
    # returns true if 'Current Ratio' is > 1.1 or > 1 and CY > PY 
    def ratio_metric_calc(cur,diff):
        return 'MS' if ((cur > 1.1) | ((cur > 1) & (diff == True))) else 'DNMS'
    
    # NOTE: The vectorized way to run calculations between different rows of the
    # same column is to shift a copy of the column either up or down using
    # shift. Shift(-1) moves the column up one row. Shift(1) moves the column
    # down one row. In some cases, this causes the calculated value to be offset by
    # the amount of the shift. For display purposes, we need to account for this by
    # shifting the calculated column up by the amount of the original shift
    metric_grid['Current Ratio Previous'] = metric_grid['Current Ratio'].shift(-1)

    metric_grid['Current Ratio Trend'] = \
        metric_grid['Current Ratio'] > metric_grid['Current Ratio Previous']
    
    metric_grid['Current Ratio Metric'] = \
        metric_grid.apply(lambda x: ratio_metric_calc(x['Current Ratio'], x['Current Ratio Trend']), axis=1)

    # Day's Cash calculation
    metric_grid['Days Cash on Hand'] = \
        metrics['Unrestricted Cash'] / ((metrics['Operating Expenses'] - metrics['Depreciation/Amortization'])/365)
   
    # returns true if day's cash is > 45 or >= 30 and CY > PY
    def days_cash_metric_calc(cur,diff):
        return 'MS' if ((cur > 45) | ((cur >= 30) & (diff == True))) else 'DNMS'
   
    metric_grid['Days Cash Previous'] = metric_grid['Days Cash on Hand'].shift(-1)
    metric_grid['Days Cash Trend'] = metric_grid['Days Cash on Hand'] > metric_grid['Days Cash Previous']
    
    metric_grid['Days Cash Metric'] = \
        metric_grid.apply(lambda x: days_cash_metric_calc(x['Days Cash on Hand'], x['Days Cash Trend']), axis=1)

    # Annual Enrollment Change calculation
    metric_grid['Annual Enrollment Change'] = \
         (metrics['ADM Average'].shift(1) - metrics['ADM Average']) / metrics['ADM Average']
    
    # See above, because we used a shift down in the above calculation, we have to shift the
    # row back up post calculation
    metric_grid['Annual Enrollment Change'] = metric_grid['Annual Enrollment Change'].shift(-1)
    metric_grid['Annual Enrollment Change Metric'] = \
        metric_grid['Annual Enrollment Change'].apply(lambda x: 'MS' if (x > -0.1) else 'DNMS')    

    # if the result is NaN (no calculation is possible), the Metric should be N/A
    metric_grid.loc[metric_grid['Annual Enrollment Change'].isnull(), 'Annual Enrollment Change Metric'] = 'N/A'

    # Primary Reserve Ratio calculation
    metric_grid['Primary Reserve Ratio'] = metrics['Unrestricted Net Assets'] / metrics['Operating Expenses']
    metric_grid['Primary Reserve Ratio Metric'] = \
        metric_grid['Primary Reserve Ratio'].apply(lambda x: 'MS' if (x > 0.25) else 'DNMS')

      # Change in Net Assets Margin/Aggregated Three-Year Margin
    metric_grid['Change in Net Assets Margin'] = metrics['Change in Net Assets'] / metrics['Operating Revenues'] 
    metric_grid['Aggregated Three-Year Margin'] = (
        metrics['Change in Net Assets'] + metrics['Change in Net Assets'].shift() + metrics['Change in Net Assets'].shift(2)
        ) / (
        metrics['Operating Revenues'] + metrics['Operating Revenues'].shift() + metrics['Operating Revenues'].shift(2)
        )

    metric_grid['Aggregated Three-Year Margin'] = metric_grid['Aggregated Three-Year Margin'].shift(-2)

    # create temporary columns for calculations include values from previous year
    metric_grid['AgMar Previous'] = metric_grid['Aggregated Three-Year Margin'].shift(-1)
    metric_grid['AgMar Previous 2'] = metric_grid['Aggregated Three-Year Margin'].shift(-2)
    metric_grid['AgMar Trend'] = (
        (metric_grid['Aggregated Three-Year Margin'] > metric_grid['AgMar Previous']) &
        (metric_grid['AgMar Previous'] > metric_grid['AgMar Previous 2']))

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

    metric_grid['Aggregated Three-Year Margin Metric'] = \
        metric_grid.apply(lambda x: asset_margin_calc(x['Change in Net Assets Margin'], x['Aggregated Three-Year Margin'],x['AgMar Trend']), axis=1)
    metric_grid['Change in Net Assets Margin Metric'] = \
        metric_grid.apply(lambda x: asset_margin_calc(x['Change in Net Assets Margin'], x['Aggregated Three-Year Margin'],x['AgMar Trend']), axis=1)
    
    # if value is NaN (no calculation is possible), the Metric should be N/A
    metric_grid.loc[metric_grid['Aggregated Three-Year Margin'].isnull(), 'Aggregated Three-Year Margin Metric'] = 'N/A'

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
    metric_grid['Debt to Asset Ratio Metric'] = \
        metric_grid['Debt to Asset Ratio'].apply(lambda x: 'MS' if (x < 0.9) else 'DNMS')    

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

        # school meets standard if current year Cash Flow value and current
        # year Multi-Year Cash Flow value are positive and at least one of 
        # the previous two years are positive. converting a boolean to int
        # results in either 0 (false) or 1 (true). when added together, a
        #  value of 1 or 2 means one or both years were positive
        if (metric_grid.loc[i]['Multi-Year Cash Flow'] > 0) & (current_year_cash > 0) & \
            ((int(previous_year_cash) + int(second_previous_year_cash)) >= 1):
            
            metric_grid.loc[i,'Cash Flow Metric'] = 'MS'
            metric_grid.loc[i,'Multi-Year Cash Flow Metric'] = 'MS'

        else:
            metric_grid.loc[i,'Multi-Year Cash Flow Metric'] = 'DNMS'
            metric_grid.loc[i,'Cash Flow Metric'] = 'DNMS'

    # A school meets standard if Cash Flow is positive in first two years (see above)
    if metric_grid.loc[metric_grid.index[-1],'Cash Flow'] > 0:
        metric_grid.loc[metric_grid.index[-1], 'Cash Flow Metric'] = 'MS'
    else:
        metric_grid.loc[metric_grid.index[-1],'Cash Flow Metric'] = 'DNMS'

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
    metric_grid['Debt Service Coverage Ratio'] = \
        (metrics['Change in Net Assets'] + metrics['Lease/Mortgage Payments'] + metrics['Depreciation/Amortization'] + metrics['Interest Expense']) / (metrics['Lease/Mortgage Payments'] + metrics['Principal Payments'] + metrics['Interest Expense'])

    metric_grid['Debt Service Coverage Ratio Metric'] = \
        metric_grid['Debt Service Coverage Ratio'].apply(lambda x: 'MS' if (x > 1) else 'DNMS')    
    
    # Drop all temporary (calculation) columns
    metric_grid = metric_grid.drop(columns=['Days Cash Previous','Days Cash Trend','Current Ratio Previous','Current Ratio Trend','AgMar Previous','AgMar Previous 2','AgMar Trend'], axis=1)

    metric_grid['Year'] = metrics['Year']

    # Transpose Again
    metric_grid = (
        metric_grid.set_index("Year")
        .T.rename_axis("Category")
        .rename_axis(None, axis=1)
        .reset_index()
    )

    # A helper function in the helper function
    # Because this is for display, we need to manually reorder the columns
    def sort_metrics(column):
        reorder = [
            'Current Ratio','Current Ratio Metric',
            'Days Cash on Hand','Days Cash Metric',
            'Annual Enrollment Change', 'Annual Enrollment Change Metric',
            'Primary Reserve Ratio', 'Primary Reserve Ratio Metric',
            'Change in Net Assets Margin', 'Change in Net Assets Margin Metric',
            'Aggregated Three-Year Margin', 'Aggregated Three-Year Margin Metric',
            'Debt to Asset Ratio', 'Debt to Asset Ratio Metric',
            'Cash Flow', 'Cash Flow Metric',
            'Multi-Year Cash Flow', 'Multi-Year Cash Flow Metric',
            'Debt Service Coverage Ratio', 'Debt Service Coverage Ratio Metric',
        ]
        cat = pd.Categorical(column, categories=reorder, ordered=True)
        return pd.Series(cat)

    metric_grid_sorted = metric_grid.sort_values(by='Category', key=sort_metrics)

    final_grid = pd.DataFrame()

    # Restructure dataframe so that every other row (Metrics) become columns
    # https://stackoverflow.com/questions/36181622/moving-every-other-row-to-a-new-column-and-group-pandas-python
    all_cols = [i for i in metric_grid_sorted if i not in ['Category']]

    for col in all_cols:
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

    # Add new rows for 'Near Term|Long Term' titles
    # it baffles me why this is so difficult
    
    # add row between existing indexes, sort and then reset
    final_grid.loc[3.5,'Category'] = 'Long Term'
    final_grid = final_grid.sort_index().reset_index(drop=True)
    
    # because this is the first row, we use indexing: setting with enlargement
    final_grid.loc[-1, 'Category'] = 'Near Term'
    final_grid.index = final_grid.index + 1
    final_grid = final_grid.sort_index() 
    final_grid = final_grid.rename(columns = {'Category': 'Metric'})

    # convert all values to numeric
    year_cols = [i for i in final_grid.columns if i not in ['Metric','Rating']]

    # Add integer to Rating columns (needed for dash data_table in order to
    # distinguish columns)
    final_grid.columns = [f'{x} {i}' if x in 'Rating' else f'{x}' for i, x in enumerate(final_grid.columns, 1)]
   
    # force year columns to numeric and round
    for col in year_cols:
        final_grid[col] = pd.to_numeric(final_grid[col], errors='coerce').round(2) #.fillna(final_grid[col])

    return final_grid