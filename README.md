# school-dashboard
Note: This version is essentially the same as main branch other than it uses SQLite for data storage
rather than multiple csv files.

Dashboard created in Plotly Dash (python) to measure School Performance

The dashboard was created to provide academic and financial information for selected schools using both school provided
and publically available financial and academic data. It runs these data through a number of defined KPI calculations, displays the school's
performance against those financial and academic metrics, and displays a number of charts showing comparative data.

The app uses flask-login to control access to the dashboard by individual schools, although all of the data used is public under State law.

It is a work in progress.
