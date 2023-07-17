#############################################
# ICSB Dashboard - Database Queries (SQLite #
#############################################
# author:   jbetley
# version:  1.03
# date:     5/22/23

# Resources:
# https://realpython.com/python-sqlite-sqlalchemy/
# https://www.fullstackpython.com/blog/export-pandas-dataframes-sqlite-sqlalchemy.html
# https://community.plotly.com/t/sqlite-in-multi-page-dash-app/71879/19
# https://stackoverflow.com/questions/68139493/dash-app-connections-to-aws-postgres-db-very-slow
# https://stackoverflow.com/questions/61943505/when-trying-to-connect-to-mysql-db-using-ploty-dash-app-iam-getting-an-error
# https://stackoverflow.com/questions/53999681/using-flask-with-sqlalchemy-and-dash
# https://stackoverflow.com/questions/52286507/how-to-merge-flask-login-with-a-dash-application
# https://community.plotly.com/t/dash-interacting-with-sqlite-and-creating-a-table/11844

# Examples:
# https://github.com/plotly/dash-sqlite-uber-rides-demo/blob/master/uberDatabase.py
# https://github.com/plotly/dash-recipes/blob/master/sql_dash_dropdown.py
# https://github.com/plotly/dash-recipes/blob/master/dash_sqlite.py

### AWS LIVE DATABASE ###
# https://www.youtube.com/watch?v=DWqEVpOfYxE
# https://www.youtube.com/watch?v=zIHOOuCdLAM
# https://medium.com/@rodkey/deploying-a-flask-application-on-aws-a72daba6bb80
# https://stackoverflow.com/questions/14850341/connect-to-aws-rds-mysql-database-instance-with-flask-sqlalchemy?rq=1
# https://stackoverflow.com/questions/62059016/connecting-flask-to-aws-rds-using-flask-sqlalchemy

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text

# Create a simple database
engine = create_engine('sqlite:///data/db_all.db')

# consider
# import importlib.resources as resources
# with resources.path("dashboard_0123.db") as sqlite_filepath:
#     engine = create_engine(f"sqlite:///{sqlite_filepath}")

print('Database Engine Created . . .')

# Return Dataframe (read_sql is a convenience function wrapper around
# read_sql_query or read_sql_table depending on input)

# TODO: Can refactor, everything should passed in as a tuple of a dict for named placeholders, even if only a single
# TODO: value, so type should always be dict
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

# Only loads once, from 'load_globals.py'
def get_current_year():

    db = engine.raw_connection()
    cur = db.cursor()
    cur.execute(''' SELECT MAX(Year) FROM academic_data_k8 ''')
    year = cur.fetchone()[0]
    db.close()

    return year

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

def get_operational_dropdown_years(school_id):
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

        results = results.filter(regex='^\d{4}$')

        for col in results.columns:
            results[col] = pd.to_numeric(results[col], errors='coerce')

        mask = results.iloc[adm_index] > 0

        results = results.loc[:, mask]

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

def get_info(school_id):
    params = dict(id=school_id)

    q = text('''
        SELECT SchoolName, City, Principal, OpeningYear
            FROM school_index
            WHERE school_index.SchoolID = :id
        ''')

    return run_query(q, params)

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

def get_adult_high_school_metric_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT Year, "AHS|CCR", "AHS|GradAll"
            FROM academic_data_hs
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

# TODO: Table does not exist yet
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
	        FROM growth
	        WHERE MajorityEnrolledSchoolID = :id
        ''')    # WHERE TestedSchoolID = :id
    return run_query(q, params)
    
def get_high_school_academic_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
            FROM academic_data_hs
	        WHERE SchoolID = :id
        ''')
#    results = run_query(q, params)
#    results = results.sort_values(by = 'Year',ascending = False)
#    return results    
    return run_query(q, params)

# NOTE: gets corp level data - all other tables have school level data

# # TODO: Is there corp level data in this table? NO! Save all Corp level HS data in corporation_data_k8
# # use generic get corporation_academic_data_k8
# # and get corporation_academic_data_hs
# def get_high_school_corporation_academic_data(*args):
#     keys = ['id']
#     params = dict(zip(keys, args))

#     q = text('''
#         SELECT *
# 	        FROM academic_data_hs
# 	        WHERE CorporationID = (
# 		        SELECT GEOCorp
# 			        FROM school_index
# 			        WHERE SchoolID = :id)
#         ''')
#     return run_query(q, params)

def get_school_coordinates(*args):
    keys = ['year']
    params = dict(zip(keys, args))

    q = text('''
        SELECT Lat, Lon, SchoolID, SchoolName, HighGrade, LowGrade
            FROM academic_data_k8 
            WHERE Year = :year
        ''')
    
    return run_query(q, params)

def get_comparable_schools(*args):
    keys = ['schools','year']
    params = dict(zip(keys, args))

    school_str = ', '.join( [ str(int(v)) for v in params['schools'] ] )

    query_string = '''
        SELECT *
            FROM academic_data_k8
            WHERE Year = :year AND SchoolID IN ({})'''.format( school_str )

    q = text(query_string)

    return run_query(q, params)

