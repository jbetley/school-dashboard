#########################
# ICSB School Dashboard #
#########################
# author:    jbetley
# date:         06.22.22

import dash

external_stylesheet = [
    'https://fonts.googleapis.com/css2?family=Roboto:400',
]
app = dash.Dash(
    __name__,
    external_stylesheets = external_stylesheet,
    external_scripts=[
        {'src': 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.0/html2canvas.min.js'}
    ],
    suppress_callback_exceptions = True
)
server = app.server
#app.css.config.serve_locally = True
app.config["suppress_callback_exceptions"] = True