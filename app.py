import pandas as pd
import os
import plotly.express as px
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State

# Load CSV
pivoted_data = pd.read_csv("pivoted.csv")

# Decide which columns to offer in X/Y/Z axis dropdowns
dropdown_axis_options = [
    col for col in pivoted_data.columns
    if col not in ['country', 'ISO2', 'ISO3', 'un_region', 'Unnamed: 0']
]
unique_countries = sorted(pivoted_data['country'].dropna().unique())
unique_un_regions = sorted(pivoted_data['un_region'].dropna().unique())

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

app.layout = dbc.Container(
    fluid=True,
    children=[

        # Title
        dbc.Row(
            dbc.Col(
                html.H1("DAPC PG Explorer", className="text-center my-4"),
                width=12
            )
        ),

        # Row of filters (Country, UN Region)
        dbc.Row([
            dbc.Col(
                [
                    html.Label("Select Country/ies:", className="text-center d-block mb-2"),
                    dcc.Dropdown(
                        id='country-dropdown',
                        options=[{'label': c, 'value': c} for c in unique_countries],
                        value=[],
                        multi=True,
                        className='dark-dropdown',
                        style={'backgroundColor': '#444444', 'color': 'white'}
                    )
                ],
                width=6
            ),
            dbc.Col(
                [
                    html.Label("Select UN Region(s):", className="text-center d-block mb-2"),
                    dcc.Dropdown(
                        id='unregion-dropdown',
                        options=[{'label': r, 'value': r} for r in unique_un_regions],
                        value=[],
                        multi=True,
                        className='dark-dropdown',
                        style={'backgroundColor': '#444444', 'color': 'white'}
                    )
                ],
                width=6
            )
        ], className="mb-4"),

        # Row of axis selectors (X, Y, Z)
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

        # 3D scatter + Scorecards
        dbc.Row([
            dbc.Col(
                dcc.Graph(id='3d-scatter'),
                width=8
            ),
            dbc.Col(
                [
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(id='sum-x-title', className="card-title"),
                            html.P(id='sum-x', className="card-text")
                        ]),
                        className="mb-3"
                    ),
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(id='sum-y-title', className="card-title"),
                            html.P(id='sum-y', className="card-text")
                        ]),
                        className="mb-3"
                    ),
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(id='sum-z-title', className="card-title"),
                            html.P(id='sum-z', className="card-text")
                        ]),
                        className="mb-3"
                    ),
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Count of Countries", className="card-title"),
                            html.P(id='count-countries', className="card-text")
                        ]),
                        className="mb-3"
                    ),
                ],
                width=4
            )
        ]),

        # Year slider
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
        ], className="my-4"),

        # 2D chart toggle + 2D graph
dbc.Row([
    dbc.Col(
        [
            html.Label("2D Chart Type:", className="text-center d-block mb-2"),
            dcc.RadioItems(
                id='2d-graph-type',
                options=[
                    {'label': 'Scatter ', 'value': 'scatter'},
                    {'label': 'Line', 'value': 'line'}
                ],
                value='scatter',
                inline=True,
                inputStyle={"margin-right": "10px", "margin-left": "10px"}  # Space around each option
            ),
            dcc.Graph(id='2d-graph')
        ],
        width=12
    )
])
    ]
)



@app.callback(
    [
        Output('country-dropdown', 'options'),
        Output('country-dropdown', 'value')
    ],
    Input('unregion-dropdown', 'value'),
    State('country-dropdown', 'value')
)
def update_country_options(selected_un_regions, current_countries):
    if not selected_un_regions:
        new_options = [{'label': c, 'value': c} for c in unique_countries]
        new_values = current_countries
    else:
        filtered_df = pivoted_data[pivoted_data['un_region'].isin(selected_un_regions)]
        valid_countries = sorted(filtered_df['country'].dropna().unique())
        new_options = [{'label': c, 'value': c} for c in valid_countries]
        new_values = [c for c in current_countries if c in valid_countries]
    return new_options, new_values

@app.callback(
    [
        Output('3d-scatter', 'figure'),
        Output('count-countries', 'children'),
        Output('sum-x', 'children'),
        Output('sum-y', 'children'),
        Output('sum-z', 'children'),
        Output('sum-x-title', 'children'),
        Output('sum-y-title', 'children'),
        Output('sum-z-title', 'children'),
        Output('2d-graph', 'figure')
    ],
    [
        Input('year-slider', 'value'),
        Input('xaxis-dropdown', 'value'),
        Input('yaxis-dropdown', 'value'),
        Input('zaxis-dropdown', 'value'),
        Input('country-dropdown', 'value'),
        Input('unregion-dropdown', 'value'),
        Input('2d-graph-type', 'value')
    ]
)
def update_scatter_and_cards(
    selected_year_range,
    x_var, y_var, z_var,
    selected_countries,
    selected_un_regions,
    graph_type_2d
):
    start_year, end_year = selected_year_range

    filtered_df = pivoted_data[
        (pivoted_data['year'] >= start_year) & (pivoted_data['year'] <= end_year)
    ]
    if selected_un_regions:
        filtered_df = filtered_df[filtered_df['un_region'].isin(selected_un_regions)]
    if selected_countries:
        filtered_df = filtered_df[filtered_df['country'].isin(selected_countries)]
    filtered_df = filtered_df.dropna(subset=[x_var, y_var, z_var, 'country'])

    fig_3d = px.scatter_3d(
        filtered_df,
        x=x_var,
        y=y_var,
        z=z_var,
        color='country',
        title=f"3D Scatter: {x_var} vs {y_var} vs {z_var}"
    )
    fig_3d.update_layout(
        template='plotly_dark',
        scene=dict(
            xaxis=dict(title=x_var),
            yaxis=dict(title=y_var),
            zaxis=dict(title=z_var),
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    count_countries = filtered_df['country'].nunique()

    def sum_var(df, var):
        if var == 'year':
            return "N/A"
        if pd.api.types.is_numeric_dtype(df[var]):
            return f"{df[var].sum():,.0f}"
        return "N/A"

    sum_x_val = sum_var(filtered_df, x_var)
    sum_y_val = sum_var(filtered_df, y_var)
    sum_z_val = sum_var(filtered_df, z_var)

    sum_x_title = f"Sum of {x_var}"
    sum_y_title = f"Sum of {y_var}"
    sum_z_title = f"Sum of {z_var}"

    # Build 2D figure (only uses x_var, y_var)
    df_2d = filtered_df.dropna(subset=[x_var, y_var, 'country'])
    if graph_type_2d == 'scatter':
        fig_2d = px.scatter(
            df_2d,
            x=x_var,
            y=y_var,
            color='country',
            title=f"2D {graph_type_2d.capitalize()}: {x_var} vs {y_var}"
        )
    else:
        fig_2d = px.line(
            df_2d,
            x=x_var,
            y=y_var,
            color='country',
            title=f"2D {graph_type_2d.capitalize()}: {x_var} vs {y_var}"
        )
    fig_2d.update_layout(template='plotly_dark')

    return (
        fig_3d,
        str(count_countries),
        sum_x_val,
        sum_y_val,
        sum_z_val,
        sum_x_title,
        sum_y_title,
        sum_z_title,
        fig_2d
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run_server(debug=False, host='0.0.0.0', port=port)
