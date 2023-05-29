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

# Create a simple database
engine = create_engine('sqlite:///data/dashboard_0123.db')

# consider
# import importlib.resources as resources
# with resources.path("dashboard_0123.db") as sqlite_filepath:
#     engine = create_engine(f"sqlite:///{sqlite_filepath}")


# raw_connection works but gives following error:
# UserWarning: pandas only support SQLAlchemy connectable(engine/connection) or database string URI
# or sqlite3 DBAPI2 connectionother DBAPI2 objects are not tested, please consider using SQLAlchemy
# connection = engine.raw_connection()

print('DB CONNECTED')

# Return Dataframe (read_sql is a convenience function wrapper around read_sql_query or read_sql_table depending on input)
# TODO: Can refactor, everything should passed in as a tuple of a dict for named placeholders, even if only a single
# value, so type should always be dict
def run_query(q, *args):
    conditions = None

    with engine.connect() as conn:
        if args:
            conditions = args[0]

        df = pd.read_sql_query(q, conn, params=conditions)

        # sqlite column headers do not have spaces, but we need to add them back for display
        # purposes. Adding a space between any lowercase character and uppercase/number character
        # takes care of most of it. We need two other replace functions to catch edge cases.
        df.columns = df.columns.str.replace(r"([a-z])([A-Z1-9%])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace(r"([WAD])([ATPB])", r"\1 \2", regex=True)
        df.columns = df.columns.str.replace("or ", " or ")
        df.columns = df.columns.astype(str)

        return df
    
    #    return pd.read_sql_query(q, conn, params=conditions)

# NOTE: Table specific queries
# def show_tables():
#     q = text('''
#         SELECT
#             name
#         FROM sqlite_master
#         WHERE type IN ("table","view");
#         ''')
    
#     return run_query(q)

# def get_table_row_count(tablename):
#     q = '''
#         SELECT
#             COUNT(1)
#         FROM %s;
#         ''' % tablename
#     return run_query(q)["COUNT(1)"][0]

# tables = show_tables()
# tables["row_count"] = [get_table_row_count(t) for t in tables["name"]]

# Get school information
# Input: school_id
def get_info(school_id):
    params = dict(id=school_id)

    # Using text to pass 'textual' SQL string directly to database
    q = text('''
        SELECT SchoolName, City, Principal, OpeningYear
            FROM school_index
            WHERE school_index.SchoolID = :id
        ''')

    return run_query(q, params)

# info = get_info(pass_id)
# print(info)

# Get School Demographics
# Input: school_id, selected_year
def get_demographics(*args):
    keys = ['id','year']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
            FROM demographic_data
	        WHERE SchoolID = :id AND Year = :year
        ''')
    
    return run_query(q, params)

# Get School Letter Grades (all years)
# Input: school_id
def get_letter_grades(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT demographic_data.Year, demographic_data.StateGrade, demographic_data.FederalRating
            FROM demographic_data
	        WHERE SchoolID = :id
        ''')
    
    return run_query(q, params)

# Get Corporation Demographics
# Input: school_id, selected_year
def get_corp_demographics(*args):
    keys = ['id','year']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
            FROM demographic_data
	        WHERE SchoolID = (
		        SELECT GEOCorp
			        FROM school_index
			        WHERE SchoolID = :id AND Year = :year)
        ''')
    return run_query(q, params)

# demo2 = get_corp_demographics(pass_id,pass_year)
# print(demo2)

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
# NOTE: Can use for networks as well - just need a school_index query getting NetworkID by matching SchoolID and
# then passing NetworkID
# e.g., school_id = school_index.loc[school_index['School ID'] == school,['Network']].values[0][0]
def get_finance(school_id):
    params = dict(id=school_id)
    q = text('''
        SELECT * 
        FROM financial_data 
        WHERE SchoolID = :id
    ''')
    return run_query(q, params)

# Get School Academic Data
# Input: school_id, year
def get_school_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
            FROM charter_school_k8_data
	        WHERE SchoolID = :id
        ''')
    return run_query(q, params)

        # SELECT *
        #     FROM charter_school_k8_data
	    #     WHERE SchoolID = :id AND Year = :year
        # ''')

# Input: school_id, year
def get_hs_data(*args):
    keys = ['id']
    params = dict(zip(keys, args))

    q = text('''
        SELECT *
            FROM academic_data_hs
	        WHERE SchoolID = :id
        ''')
    return run_query(q, params)

# Get Corporation Rate Academic Data
# Input: school_id, year
def get_corp_data(*args):
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

# Get Corporation Rate Academic Data
# Input: school_id, year
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