##############################################
# ICSB Dashboard - Database Queries (SQLite) #
##############################################
# author:   jbetley
# version:  1.10
# date:     08/31/23

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text

# global variables
max_display_years = 5

subject = ["Math", "ELA"]

info_categories = ["School Name","Low Grade","High Grade"]

ethnicity = [
    "American Indian",
    "Asian",
    "Black",
    "Hispanic",
    "Multiracial",
    "Native Hawaiian or Other Pacific Islander",
    "White",
]

subgroup = [
    "Special Education",
    "General Education",
    "Paid Meals",
    "Free or Reduced Price Meals",
    "English Language Learners",
    "Non English Language Learners",
]

grades = [
    "Grade 3",
    "Grade 4",
    "Grade 5",
    "Grade 6",
    "Grade 7",
    "Grade 8"
]

grades_all = [
    "Grade 3",
    "Grade 4",
    "Grade 5",
    "Grade 6",
    "Grade 7",
    "Grade 8",
    "Total"
]

grades_ordinal = [
    "3rd",
    "4th",
    "5th",
    "6th",
    "7th",
    "8th"
]

engine = create_engine('sqlite:///data/db_all.db')
print('Database Engine Created . . .')

def get_current_year():
    db = engine.raw_connection()
    cur = db.cursor()
    cur.execute(''' SELECT MAX(Year) FROM academic_data_k8 ''')
    year = cur.fetchone()[0]
    db.close()

    return year

current_academic_year = get_current_year()

# TODO: Refactor so everything passed in as a tuple of a dict for named placeholders, even if only a single val
# Return Dataframe (read_sql is a convenience function wrapper around read_sql_query)
# If no data matches query, returns an empty dataframe
def run_query(q, *args):
    conditions = None

    with engine.connect() as conn:
        if args:
            conditions = args[0]

        df = pd.read_sql_query(q, conn, params=conditions)

        # sqlite column headers do not have spaces between words. But we need to display the column names,
        # so we have to do a bunch of str.replace to account for all conditions. May be a better way, but
        # this is pretty fast. Adding a space between any lowercase character and any  uppercase/number
        # character takes care of most of it. The other replace functions catch edge cases.           
        df.columns = df.columns.str.replace(r"([a-z])([A-Z1-9%])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace(r"([WADTO])([CATPB&])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace(r"([A])([a])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace(r"([1-9])([(])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace("or ", " or ")
        df.columns = df.columns.astype(str)

        return df

def get_academic_dropdown_years(*args):
    keys = ['id','type']
    params = dict(zip(keys, args))

    if params['type'] == 'K8' or params['type'] == 'K12':
        q = text(''' 
            SELECT DISTINCT	Year
            FROM academic_data_k8
            WHERE SchoolID = :id
        ''')
    else:
        q = text('''
            SELECT DISTINCT	Year
            FROM academic_data_hs
            WHERE SchoolID = :id
        ''')
        
    result = run_query(q, params)
    
    years = result['Year'].tolist()
    years.sort(reverse=True)
    
    return years

def get_financial_info_dropdown_years(school_id):
    params = dict(id=school_id)
    q = text('''
        SELECT * 
        FROM financial_data 
        WHERE SchoolID = :id
    ''')
    
    results = run_query(q, params)

    # Processes financial df and returns a list of Year column names for
    # each year for which ADM Average is greater than '0'
    if len(results.columns) > 3:

        adm_index = results.index[results['Category'] == 'ADM Average'].values[0]

        results = results.filter(regex='^\d{4}') # adding '$' to the end of the regex will skip (Q#) years

        for col in results.columns:
            results[col] = pd.to_numeric(results[col], errors='coerce')

        mask = results.iloc[adm_index] > 0

        results = results.loc[:, mask]

        # trim excess info (Q#) if present
        years = [x[:4] for x in results.columns.to_list()]

    else:
        years = []

    return years

def get_financial_analysis_dropdown_years(school_id):
    params = dict(id=school_id)
    q = text('''
        SELECT * 
        FROM financial_data 
        WHERE SchoolID = :id
    ''')
    
    results = run_query(q, params)

    # Processes financial df and returns a list of Year column names for
    # each year for which ADM Average is greater than '0'
    if len(results.columns) > 3:

        adm_index = results.index[results['Category'] == 'ADM Average'].values[0]

        # adding '$' to the end of the regex skips (Q#) years
        results = results.filter(regex='^\d{4}$') 

        for col in results.columns:
            results[col] = pd.to_numeric(results[col], errors='coerce')

        mask = results.iloc[adm_index] > 0

        results = results.loc[:, mask]

        # trim excess info (Q#) if present
        years = results.columns.to_list()

    else:
        years = []

    return years

def get_school_dropdown_list():
    q = text('''
        SELECT SchoolName, SchoolID, SchoolType
        FROM school_index '''
    )

    with engine.connect() as conn:
        schools = pd.read_sql_query(q, conn)

    schools = schools.astype(str)

    return schools

def get_graduation_data():
    params = dict(id='')

    q = text('''
        SELECT
            Year,
            SUM("Total|Graduates") / SUM("Total|CohortCount") AS "State Graduation Average"
        FROM academic_data_hs
        WHERE SchoolType != "AHS"
        GROUP BY
            Year
        ''')

    return run_query(q, params)

def get_school_index(school_id):
    params = dict(id=school_id)

    q = text('''
        SELECT *
            FROM school_index
            WHERE school_index.SchoolID = :id
        ''')

    return run_query(q, params)

# def get_school_info(school_id):
#     params = dict(id=school_id)

#     q = text('''
#         SELECT SchoolName, City, Principal, OpeningYear
#             FROM school_index
#             WHERE school_index.SchoolID = :id
#         ''')

#     return run_query(q, params)

def get_financial_data(school_id):
    params = dict(id=school_id)
    q = text('''
        SELECT * 
        FROM financial_data 
        WHERE SchoolID = :id
    ''')
    return run_query(q, params)

def get_financial_ratios(corp_id):
    params = dict(id=corp_id)
    q = text('''
        SELECT * 
        FROM financial_ratios 
        WHERE CorporationID = :id
    ''')
    return run_query(q, params)

# for school corporations, SchoolID and CorpID are the same
def get_demographic_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
            FROM demographic_data
	        WHERE SchoolID = :id
        ''')
    
    return run_query(q, params)

def get_letter_grades(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT demographic_data.Year, demographic_data.StateGrade, demographic_data.FederalRating
            FROM demographic_data
	        WHERE SchoolID = :id
        ''')
    
    return run_query(q, params)

def get_k8_school_academic_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
            FROM academic_data_k8
	        WHERE SchoolID = :id
        ''')
    
    results = run_query(q, params)
    results = results.sort_values(by = 'Year',ascending = False)

    return results

def get_k8_corporation_academic_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
	        FROM corporation_data_k8
	        WHERE CorporationID = (
		        SELECT GEOCorp
			        FROM school_index
			        WHERE SchoolID = :id)
        ''')

    results = run_query(q, params)
    results = results.sort_values(by = 'Year',ascending = False)

    return results

def get_high_school_academic_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
            FROM academic_data_hs
	        WHERE SchoolID = :id
        ''')

    return run_query(q, params)

def get_hs_corporation_academic_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
	        FROM corporation_data_hs
	        WHERE CorporationID = (
		        SELECT GEOCorp
			        FROM school_index
			        WHERE SchoolID = :id)
        ''')

    results = run_query(q, params)
    results = results.sort_values(by = 'Year',ascending = False)

    return results

def get_growth_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
	        FROM growth_data
	        WHERE MajorityEnrolledSchoolID = :id
        ''')
    return run_query(q, params)

# "SchoolTotal|ELATotalTested" is a proxy for school size for k8 schools. 
def get_school_coordinates(*args):
    keys = ['year','type']
    params = dict(zip(keys, args))

    if params['type'] == 'HS':
        q = text('''
            SELECT Lat, Lon, SchoolID, SchoolName, HighGrade, LowGrade
                FROM academic_data_hs 
                WHERE Year = :year
        ''')
    elif params['type'] == 'AHS':
        q = text('''
            SELECT Lat, Lon, SchoolID, SchoolName, HighGrade, LowGrade
                FROM academic_data_hs 
                WHERE Year = :year and SchoolType = "AHS"
        ''')
    else:
        q = text('''
            SELECT Lat, Lon, SchoolID, SchoolName, HighGrade, LowGrade, "SchoolTotal|ELATotalTested"
                FROM academic_data_k8 
                WHERE Year = :year
        ''')

    return run_query(q, params)

def get_comparable_schools(*args):
    keys = ['schools','year','type']
    params = dict(zip(keys, args))

    school_str = ', '.join( [ str(int(v)) for v in params['schools'] ] )

    if params['type'] == 'HS':
        query_string = '''
            SELECT *
                FROM academic_data_hs
                WHERE Year = :year AND SchoolID IN ({})'''.format( school_str )
    
    elif params['type'] == 'AHS':
        query_string = '''
            SELECT *
                FROM academic_data_hs
                WHERE Year = :year AND SchoolType = "AHS" AND SchoolID IN ({})'''.format( school_str )
    else:   # K8
        query_string = '''
            SELECT *
                FROM academic_data_k8
                WHERE Year = :year AND SchoolID IN ({})'''.format( school_str )
        
    q = text(query_string)

    return run_query(q, params)