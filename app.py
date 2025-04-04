import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import os
# Initialize app
app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)
server = app.server

# Flask routes
@server.route("/")
def home():
    return app.index()

@server.route("/<path:path>")
def serve_all(path):
    return app.index()

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dcc.Link(
                "HOME",
                href="/",
                className="nav-link",
                style={
                    'font-size': '18px',
                    'color': 'white',
                    'font-weight': 'bold',
                    'margin-right': '15px'
                }
            )),
            dbc.NavItem(dcc.Link(
                "WEEKLY",
                href="/weekly",
                className="nav-link",
                style={
                    'font-size': '18px',
                    'color': 'white',
                    'font-weight': 'bold',
                    'margin-right': '15px'
                }
            )),
            dbc.NavItem(dcc.Link(
                "MONTHLY",
                href="/monthly",
                className="nav-link",
                style={
                    'font-size': '18px',
                    'color': 'white',
                    'font-weight': 'bold',
                    'margin-right': '15px'
                }
            )),
        ],
        brand="South Ribble Data Analysis",
        brand_href="/",  # Make brand clickable to return home
        color="primary",
        dark=True,
        style={'min-height': '60px'}
    ),
    html.Div([  # Welcome message container
        html.H2("Welcome to South Ribble Data Dashboard", className="text-center mt-4"),
        html.Div([
            html.P("📊 Explore your data using the navigation bar above:"),
            html.Ul([
                html.Li("Click WEEKLY for weekly metrics"),
                html.Li("Click MONTHLY for monthly trends")
            ]),
            html.P("💾 Remember to upload your CSV files using the upload button (if implemented)"),
            html.P("🔍 Data updates may take a few moments to process")
        ], style={
            'max-width': '800px',
            'margin': '40px auto',
            'padding': '20px',
            'border': '2px solid #0275d8',
            'border-radius': '10px',
            'background-color': '#f8f9fa'
        })
    ], id="welcome-message"),
    dash.page_container
])

if __name__ == "__main__":
    app.run(debug=True)
