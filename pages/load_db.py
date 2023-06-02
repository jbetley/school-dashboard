# SAMPLE SQL QUERIES
# SQLAlchemy version
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
import time

# Create a simple database
engine = create_engine('sqlite:///data/db_all.db')

# consider
# import importlib.resources as resources
# with resources.path("dashboard_0123.db") as sqlite_filepath:
#     engine = create_engine(f"sqlite:///{sqlite_filepath}")

print('Engine Created . . .')


# Return Dataframe (read_sql is a convenience function wrapper around read_sql_query or read_sql_table depending on input)
# TODO: Can refactor, everything should passed in as a tuple of a dict for named placeholders, even if only a single
# value, so type should always be dict
def run_query(q, *args):
    conditions = None
    t2 = time.process_time()

    with engine.connect() as conn:
        if args:
            conditions = args[0]

        df = pd.read_sql_query(q, conn, params=conditions)

        # sqlite column headers do not have spaces between words. But we need to display them,
        # so we have to do a bunch of str.replace to account for all conditions. Maybe a better
        # way, but this is pretty fast. Adding a space between any lowercase character and any 
        # uppercase/number character takes care of most of it. The other replace functions catch
        # edge cases.
        df.columns = df.columns.str.replace(r"([a-z])([A-Z1-9%])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace(r"([WADT])([ATPB&])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace(r"([&])([M])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace("or ", " or ")
        df.columns = df.columns.astype(str)

        db_load_time = time.process_time() - t2
        num_cols = len(df.columns)
        
        print(f'Time to load ' + str(num_cols) + ' columns is: ' + str(db_load_time))
        
        return df

# Only loads once, from 'load_globals.py'
def get_current_year():

    db = engine.raw_connection()
    cur = db.cursor()
    cur.execute(''' SELECT MAX(Year) FROM academic_data_k8 ''')
    year = cur.fetchone()[0]
    db.close()

    return year

def get_info(school_id):
    params = dict(id=school_id)

    q = text('''
        SELECT SchoolName, City, Principal, OpeningYear
            FROM school_index
            WHERE school_index.SchoolID = :id
        ''')

    return run_query(q, params)

def get_demographics(*args):
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

def get_corp_demographics(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
            FROM demographic_data
	        WHERE SchoolID = (
		        SELECT GEOCorp
			        FROM school_index
			        WHERE SchoolID = :id)
        ''')
    return run_query(q, params)

# Get ADM
# Input: school_id
def get_adm(school_id):
    params = dict(id=school_id)
    q = text('''
        SELECT school_index.SchoolName, icsb_school_adm.*
            FROM school_index
            INNER JOIN icsb_school_adm ON school_index.SchoolID=icsb_school_adm.SchoolID
            WHERE school_index.SchoolID = :id
        ''')
    return run_query(q, params)

# adm = get_adm(pass_id)
# print(adm)

# Get Financial Data
# Input: school_id
def get_finance(school_id):
    params = dict(id=school_id)
    q = text('''
        SELECT * 
        FROM financial_data 
        WHERE SchoolID = :id
    ''')
    return run_query(q, params)

# School Academic Data (k8)
def get_school_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
            FROM academic_data_k8
	        WHERE SchoolID = :id
        ''')
    return run_query(q, params)

# School Academic Data (hs)
def get_hs_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
            FROM academic_data_hs
	        WHERE SchoolID = :id
        ''')
    return run_query(q, params)

# Corporation Rate Academic Data (k8)
def get_corporation_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
	        FROM corporation_k8_data
	        WHERE CorporationID = (
		        SELECT GEOCorp
			        FROM school_index
			        WHERE SchoolID = :id)
        ''')
    return run_query(q, params)

# Corporation Rate Academic Data (hs)
def get_hs_corp_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
	        FROM academic_data_hs
	        WHERE CorporationID = (
		        SELECT GEOCorp
			        FROM school_index
			        WHERE SchoolID = :id)
        ''')
    return run_query(q, params)

## TODO: Working Section below - Need to import all_academic_data_k8 to db
# Get Lat and Lon Data (for given year)
def get_location_data(year):
    params = dict(year=year)
    q = text('''
        SELECT Lat, Lon, SchoolID
            FROM all_k8_data
            Where Year = :year)
        ''')
    return run_query(q, params)

# Get Comparison School Academic Data (For dropdown)
# After getting Lat/Lon data, run nearest() and the results will be in a list
# get all schools in the list
# = filtered_academic_data_k8[filtered_academic_data_k8.index.isin(index_list)]
# See: https://stackoverflow.com/questions/36840438/binding-list-to-params-in-pandas-read-sql-query-with-other-params
# https://stackoverflow.com/questions/42123335/passing-a-list-of-values-from-python-to-the-in-clause-of-an-sql-query

# Input: school_id

def get_comparison_data(school_list):
    params = dict(id=school_list)
    q = text('''
        SELECT *
            FROM all_k8_data
            WHERE SchoolID IN :school_list)
    ''')
    return run_query(q, params)

# TODO: Missing: financial_ratios?