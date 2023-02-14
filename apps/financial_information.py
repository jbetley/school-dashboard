#######################
# Financial Dashboard #
#######################
# author:   jbetley
# rev:     06.01.22

from dash import html, dash_table, Input, Output
from dash.dash_table import FormatTemplate
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np

from app import app

# np.warnings.filterwarnings('ignore')


## Callback ##
@app.callback(
    Output("financial-information-table", "children"),
    Input("charter-dropdown", "value"),
    Input("dash-session", "data"),
)
def update_finfo_page(school, data):
    if not school:
        raise PreventUpdate

    ## TODO: Figure out why dictionary is reversed when passed through callback (happens after dcc store storage)
    finance_info = pd.DataFrame.from_dict(data["1"])
    finance_info = finance_info.iloc[:, ::-1]  # flip dataframe back to normal
    finance_info.index = finance_info.index.astype(int)  # convert index to int

    if len(finance_info.index) == 0:
        return [
            dash_table.DataTable(
                columns=[
                    {"id": "emptytable", "name": "No Data to Display"},
                ],
                style_header={
                    "fontSize": "14px",
                    "border": "none",
                    "textAlign": "center",
                    "color": "#4682b4",
                    "fontFamily": "Open Sans, sans-serif",
                },
            )
        ]

    else:
        for col in finance_info.columns:
            finance_info[col] = (
                pd.to_numeric(finance_info[col], errors="coerce")
                .fillna(finance_info[col])
                .tolist()
            )

        years = finance_info.columns.tolist()
        years.pop(0)
        years.reverse()

        ## Create Financial Information table ##
        fin_table = finance_info.drop(finance_info.index[43:])

        # Clean and Format data #
        fin_table = fin_table.replace(np.nan, "", regex=True)

        for col in fin_table.columns:
            fin_table[col] = fin_table[col].replace(0.0, "")

        # Changes last 7 rows to type str so they aren't formatted by FormatTemplate (which affects all rows)
        # Can also do this by formatting rows directly - see Alt below
        for p in range(36, 43):
            fin_table.loc[p] = fin_table.loc[p].astype(str)

        # Strip trailing zero from audit year (YYYY) - gets added during string conversion
        def stripper(val):
            if "20" in val:
                return val[:-2]
            else:
                return val

        fin_table.loc[42] = fin_table.loc[42].apply(stripper)

        # Alt:
        # for x in range(1,len(all_metrics.columns),2):
        #    if all_metrics.iat[3,x]:
        #        all_metrics.iat[3,x] = '{:.0%}'.format(all_metrics.iat[3,x])
        #    if all_metrics.iat[9,x]:
        #        all_metrics.iat[9,x] = '{:,.2f}'.format(all_metrics.iat[9,x])

        return [
            dash_table.DataTable(
                fin_table.to_dict("records"),
                columns=[
                    {
                        "name": i,
                        "id": i,
                        "type": "numeric",
                        "format": FormatTemplate.money(2),
                    }
                    for i in fin_table.columns
                ],
                export_format="xlsx",
                style_data={
                    "fontSize": "12px",
                    "fontFamily": "Roboto, sans-serif",
                    "border": "none",
                },
                style_data_conditional=[
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "#eeeeee",
                    },
                    {
                        "if": {
                            "filter_query": '{Category} eq "Revenue" || {Category} eq "Financial Position" || {Category} eq "Financial Activities" || {Category} eq "Supplemental Information" || {Category} eq "Enrollment Information" || {Category} eq "Audit Information"'
                        },
                        "paddingLeft": "10px",
                        "text-decoration": "underline",
                        "fontWeight": "bold",
                    },
                ],
                style_header={
                    "backgroundColor": "#ffffff",
                    "fontSize": "12px",
                    "fontFamily": "Roboto, sans-serif",
                    "color": "#6783a9",
                    "textAlign": "center",
                    "fontWeight": "bold",
                },
                style_cell={
                    "whiteSpace": "normal",
                    #                            'height': 'auto',
                    "textAlign": "center",
                    "color": "#6783a9",
                    "boxShadow": "0 0",
                    "minWidth": "25px",
                    "width": "25px",
                    "maxWidth": "25px",
                },
                style_cell_conditional=[
                    {
                        "if": {"column_id": "Category"},
                        "textAlign": "left",
                        "fontWeight": "500",
                        "paddingLeft": "20px",
                    },
                ],
                style_as_list_view=True,
            )
        ]


## Layout
label_style = {
    "height": "20px",
    "backgroundColor": "#6783a9",
    "fontSize": "12px",
    "fontFamily": "Roboto, sans-serif",
    "color": "#ffffff",
    "textAlign": "center",
    "fontWeight": "bold",
    "paddingBottom": "5px",
    "paddingTop": "5px",
}

layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Audited Financial Information", style=label_style),
                        html.Div(id="financial-information-table"),
                    ],
                    className="pretty_container ten columns",
                ),
            ],
            className="bare_container twelve columns",
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
