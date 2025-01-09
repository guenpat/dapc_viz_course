import pandas as pd
import os
import plotly.express as px

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State

# ----------------------------------------------------------
# 1. Load CSV Data
# ----------------------------------------------------------
pivoted_data = pd.read_csv("pivoted.csv")
print("Columns in pivoted_data:", pivoted_data.columns)

# Decide which columns to offer in X/Y/Z axis dropdowns
dropdown_axis_options = [
    col for col in pivoted_data.columns
    if col not in ['country', 'ISO2', 'ISO3', 'un_region', 'Unnamed: 0']
]

# Gather unique countries & un_regions
unique_countries = sorted(pivoted_data['country'].dropna().unique())
unique_un_regions = sorted(pivoted_data['un_region'].dropna().unique())

# ----------------------------------------------------------
# 2. Initialize Dash App (Dark Theme)
# ----------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# ----------------------------------------------------------
# 3. Layout
# ----------------------------------------------------------
app.layout = dbc.Container(
    fluid=True,
    children=[
        # Title
        dbc.Row(
            dbc.Col(
                html.H1(
                    "DAPC PG Explorer",
                    className="text-center my-4"
                ),
                width=12
            )
        ),

        # Row of filters
        dbc.Row([
            # Country dropdown
            dbc.Col(
                [
                    html.Label(
                        "Select Country/ies:",
                        className="text-center d-block mb-2"
                    ),
                    dcc.Dropdown(
                        id='country-dropdown',
                        # We'll set the initial options to ALL countries
                        options=[{'label': c, 'value': c} for c in unique_countries],
                        value=[],  # no default selection
                        multi=True,
                        className='dark-dropdown',
                        style={'backgroundColor': '#444444', 'color': 'white'}
                    )
                ],
                width=6
            ),
            # UN Region dropdown
            dbc.Col(
                [
                    html.Label(
                        "Select UN Region(s):",
                        className="text-center d-block mb-2"
                    ),
                    dcc.Dropdown(
                        id='unregion-dropdown',
                        options=[{'label': r, 'value': r} for r in unique_un_regions],
                        value=[],  # no default selection
                        multi=True,
                        className='dark-dropdown',
                        style={'backgroundColor': '#444444', 'color': 'white'}
                    )
                ],
                width=6
            )
        ], className="mb-4"),

        # Row of axis selectors
        dbc.Row([
            dbc.Col(
                [
                    html.Label("X-axis Variable:", className="text-center d-block mb-2"),
                    dcc.Dropdown(
                        id='xaxis-dropdown',
                        options=[{'label': c, 'value': c} for c in dropdown_axis_options],
                        value='year',
                        clearable=False,
                        className='dark-dropdown',
                        style={'backgroundColor': '#444444', 'color': 'white'}
                    )
                ],
                width=4
            ),
            dbc.Col(
                [
                    html.Label("Y-axis Variable:", className="text-center d-block mb-2"),
                    dcc.Dropdown(
                        id='yaxis-dropdown',
                        options=[{'label': c, 'value': c} for c in dropdown_axis_options],
                        value='Greenhouse Gas Footprints (GHGFP): Principal indicators',
                        clearable=False,
                        className='dark-dropdown',
                        style={'backgroundColor': '#444444', 'color': 'white'}
                    )
                ],
                width=4
            ),
            dbc.Col(
                [
                    html.Label("Z-axis Variable:", className="text-center d-block mb-2"),
                    dcc.Dropdown(
                        id='zaxis-dropdown',
                        options=[{'label': c, 'value': c} for c in dropdown_axis_options],
                        value='Environmental goods trade balance',
                        clearable=False,
                        className='dark-dropdown',
                        style={'backgroundColor': '#444444', 'color': 'white'}
                    )
                ],
                width=4
            )
        ], className="mb-4"),

        # Main row: 3D scatter (8 columns) + scorecards (4 columns)
        dbc.Row([
            # 3D scatter (2/3 width)
            dbc.Col(
                dcc.Graph(id='3d-scatter'),
                width=8
            ),

            # Scorecards (1/3 width)
            dbc.Col(
                [
                    # Card: Count of Countries
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Count of Countries", className="card-title"),
                            html.P(id='count-countries', className="card-text")
                        ]),
                        className="mb-3"
                    ),
                    # Card: Sum of X
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Sum of X", className="card-title"),
                            html.P(id='sum-x', className="card-text")
                        ]),
                        className="mb-3"
                    ),
                    # Card: Sum of Y
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Sum of Y", className="card-title"),
                            html.P(id='sum-y', className="card-text")
                        ]),
                        className="mb-3"
                    ),
                    # Card: Sum of Z
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Sum of Z", className="card-title"),
                            html.P(id='sum-z', className="card-text")
                        ]),
                        className="mb-3"
                    ),
                ],
                width=4
            )
        ]),

        # Range Slider (Year) at bottom
        dbc.Row([
            dbc.Col(
                [
                    html.Label("Year Range:", className="d-block text-center mb-2"),
                    dcc.RangeSlider(
                        id='year-slider',
                        min=pivoted_data['year'].min(),
                        max=pivoted_data['year'].max(),
                        value=[pivoted_data['year'].min(), pivoted_data['year'].max()],
                        marks={str(y): str(y) for y in sorted(pivoted_data['year'].unique())},
                        allowCross=False
                    )
                ],
                width=12
            )
        ], className="my-4")
    ]
)

# ----------------------------------------------------------
# 4A. Callback: Update Country Dropdown Options Based on UN Region(s)
# ----------------------------------------------------------
@app.callback(
    Output('country-dropdown', 'options'),
    Output('country-dropdown', 'value'),
    Input('unregion-dropdown', 'value'),
    State('country-dropdown', 'value')
)
def update_country_options(selected_un_regions, current_countries):
    """
    This callback dynamically updates the 'country-dropdown' options 
    based on which UN regions are selected. 
    If no UN region is selected, all countries are shown. 
    Also, remove from 'current_countries' any that are not in the new list of valid countries.
    """
    if not selected_un_regions:
        # No region selected => show ALL countries
        new_options = [{'label': c, 'value': c} for c in unique_countries]
        # Keep the current_countries as is (they might be a subset or all)
        new_values = current_countries
    else:
        # Filter pivoted_data by the selected UN regions
        filtered_df = pivoted_data[pivoted_data['un_region'].isin(selected_un_regions)]
        valid_countries = sorted(filtered_df['country'].dropna().unique())
        # Build the new dropdown options
        new_options = [{'label': c, 'value': c} for c in valid_countries]
        # Remove any country that isn't in the valid list
        new_values = [c for c in current_countries if c in valid_countries]

    return new_options, new_values

# ----------------------------------------------------------
# 4B. Callback: Update Figure & Scorecards
# ----------------------------------------------------------
@app.callback(
    [
        Output('3d-scatter', 'figure'),
        Output('count-countries', 'children'),
        Output('sum-x', 'children'),
        Output('sum-y', 'children'),
        Output('sum-z', 'children'),
    ],
    [
        Input('year-slider', 'value'),
        Input('xaxis-dropdown', 'value'),
        Input('yaxis-dropdown', 'value'),
        Input('zaxis-dropdown', 'value'),
        Input('country-dropdown', 'value'),
        Input('unregion-dropdown', 'value')
    ]
)
def update_scatter_and_cards(
    selected_year_range,
    x_var, y_var, z_var,
    selected_countries,
    selected_un_regions
):
    start_year, end_year = selected_year_range

    # 1) Filter by year range
    filtered_df = pivoted_data[
        (pivoted_data['year'] >= start_year) & (pivoted_data['year'] <= end_year)
    ]

    # 2) Filter by un_region (if any)
    if selected_un_regions:
        filtered_df = filtered_df[filtered_df['un_region'].isin(selected_un_regions)]

    # 3) Filter by countries (if any)
    if selected_countries:
        filtered_df = filtered_df[filtered_df['country'].isin(selected_countries)]

    # 4) Drop rows missing data in x_var, y_var, z_var, or 'country'
    filtered_df = filtered_df.dropna(subset=[x_var, y_var, z_var, 'country'])

    # === Build the figure (3D Scatter) ===
    fig = px.scatter_3d(
        filtered_df,
        x=x_var,
        y=y_var,
        z=z_var,
        color='country',
        title=f"3D Scatter: {x_var} vs {y_var} vs {z_var}"
    )

    fig.update_layout(
        template='plotly_dark',
        scene=dict(
            xaxis=dict(title=x_var),
            yaxis=dict(title=y_var),
            zaxis=dict(title=z_var),
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    # === Build the Scorecards ===

    # (A) Count of Countries
    count_countries = filtered_df['country'].nunique()

    # (B) Sums of X, Y, Z, if numeric & not 'year'
    def sum_var(df, var):
        if var == 'year':
            return "N/A"
        if pd.api.types.is_numeric_dtype(df[var]):
            return f"{df[var].sum():,.0f}"
        else:
            return "N/A"

    sum_x = sum_var(filtered_df, x_var)
    sum_y = sum_var(filtered_df, y_var)
    sum_z = sum_var(filtered_df, z_var)

    return fig, str(count_countries), sum_x, sum_y, sum_z

# ----------------------------------------------------------
# 5. Run the App
# ----------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run_server(debug=False, host='0.0.0.0', port=port)
