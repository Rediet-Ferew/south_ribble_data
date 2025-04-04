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

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dbc.NavbarSimple(
        children=[
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
        color="primary",
        dark=True,
        # Optional: Make the navbar taller to accommodate larger links
        style={'min-height': '60px'}
    ),
    dash.page_container
])

if __name__ == "__main__":
    app.run(debug=True)