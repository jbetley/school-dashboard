from werkzeug.middleware.profiler import ProfilerMiddleware

from app import app

PROF_DIR = 'C:\scripts\projects\icsb-dashboard-db\profiles'

app.server.config['PROFILE'] = True
app.server.wsgi_app = ProfilerMiddleware(
    app.server.wsgi_app,
    sort_by=["cumtime"], 
    restrictions=[50],
    stream=None,
    profile_dir=PROF_DIR
)  

app.server.run(debug = True)