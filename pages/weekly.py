import dash
from dash import dcc, html, dash_table, ctx
import plotly.express as px
import pandas as pd
import io
import base64   
import json
import os
from dash.dependencies import Input, Output, State
import time
from dash import dcc, html, dash_table, Input, Output, callback

dash.register_page(__name__, path="/weekly", name="Weekly Data")

# Define file path for storing processed data
PROCESSED_DATA_FILE = os.path.join(os.getcwd(), "assets", "weekly_output_data.json")


def load_processed_data():
    if os.path.exists(PROCESSED_DATA_FILE):
        with open(PROCESSED_DATA_FILE, 'r') as f:
            return json.load(f)
    return None

# load_processed_data()
# Store uploaded data persistently
layout = html.Div([

    dcc.Store(id='weekly-stored-data'),
    html.H2("📆 Weekly Breakdown"),

    dcc.Upload(
        id="upload-data-weekly",
        children=html.Button("Upload CSV", className="btn btn-primary"),
        multiple=False,
    ),

    html.Div(id="file-name-weekly", style={"margin": "10px 0"}),

    dcc.Tabs([
        dcc.Tab(label='📊 Breakdown', children=[
            dcc.Loading(
                id="loading-breakdown-weekly",
                type="default",
                children=[
                    html.Div(id="summary-cards-weekly", className="summary-cards"),
                    html.Div(id="weekly-graph-container"),
                    html.Div(id="weekly-table-container"),
                ],
            )
        ])
    ])
])
# Function to clean and merge CSV data
def clean_and_merge_data(contents_list):
    dfs = []
    for content in contents_list:
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), index_col=False)
        dfs.append(df)

    merged_df = pd.concat(dfs, ignore_index=True)
    df_needed = merged_df[['PHONE NO', 'DRIVER PRICE', 'JOB DATE']]
    df_needed.columns = ['phone', 'price', 'job_date']
    df_cleaned = df_needed[df_needed["phone"].notna() & (df_needed["phone"] != "")]

    df_cleaned.loc[:, "job_date"] = pd.to_datetime(df_cleaned["job_date"], format="%d/%m/%y %H:%M:%S", errors='coerce', dayfirst=True).dt.date

    return df_cleaned


def weekly_breakdown(df):

    # Ensure date is datetime and sort
    df['job_date'] = pd.to_datetime(df['job_date'], errors='coerce')
    df = df.sort_values('job_date')

    # Filter out dates before first Monday (2023-01-02)
    df = df[df['job_date'] >= pd.to_datetime('2023-01-02')]

    # Assign week buckets starting from each Monday
    start_date = df['job_date'].min()
    end_date = df['job_date'].max()

    week_starts = pd.date_range(start=start_date, end=end_date, freq='W-MON')
    week_ends = week_starts + pd.Timedelta(days=6)

    week_labels = [f"{s.strftime('%b %d, %Y')} - {e.strftime('%b %d, %Y')}" for s, e in zip(week_starts, week_ends)]

    df['week_start'] = pd.cut(
        df['job_date'],
        bins=[start_date - pd.Timedelta(days=1)] + list(week_starts[1:]) + [end_date + pd.Timedelta(days=1)],
        labels=week_labels,
        right=False
    )
    df['week_label'] = df['week_start']

    # Identify first visit week per customer
    first_visits = df.groupby('phone')['job_date'].min().reset_index()
    first_visits.columns = ['phone', 'first_visit_date']
    df = df.merge(first_visits, on='phone', how='left')

    first_visits['first_visit_week'] = pd.cut(
        first_visits['first_visit_date'],
        bins=[start_date - pd.Timedelta(days=1)] + list(week_starts[1:]) + [end_date + pd.Timedelta(days=1)],
        labels=week_labels,
        right=False
    )
    df = df.merge(first_visits[['phone', 'first_visit_week']], on='phone', how='left')

    weekly_results = []

    for week in sorted(df['week_label'].dropna().unique(), key=lambda x: week_labels.index(x)):
        week_data = df[df['week_label'] == week]

        total_customers = week_data['phone'].nunique()
        new_customers = week_data[week_data['week_label'] == week_data['first_visit_week']]['phone'].nunique()
        returning_customers = total_customers - new_customers

        new_percentage = round((new_customers / total_customers * 100), 2) if total_customers > 0 else 0
        returning_percentage = round((returning_customers / total_customers * 100), 2) if total_customers > 0 else 0

        total_revenue = week_data['price'].sum()
        new_revenue = week_data[week_data['week_label'] == week_data['first_visit_week']]['price'].sum()
        returning_revenue = total_revenue - new_revenue

        weekly_results.append({
            'week': week,
            'total_customers': total_customers,
            'new_customers': new_customers,
            'returning_customers': returning_customers,
            'new_percentage': new_percentage,
            'returning_percentage': returning_percentage,
            'total_revenue': total_revenue,
            'new_customer_revenue': new_revenue,
            'returning_customer_revenue': returning_revenue
        })

    weekly_df = pd.DataFrame(weekly_results)

    
    return {
        'weekly_breakdown': weekly_df,
        
    }


def generate_visuals(df):
    # Increase figure size and adjust layout
    fig_line = px.line(df, x='week', y=['new_customers', 'returning_customers'], markers=True)
    fig_line.update_layout(width=2000, height=500, margin={"r": 20, "t": 20, "l": 20, "b": 50})

    # Increase bar width and ensure bars are not too thin
    fig_bar = px.bar(
        df,
        x='week',
        y=['total_revenue', 'new_customer_revenue', 'returning_customer_revenue'],
        barmode='group'
    )
    fig_bar.update_layout(
        width=2500,
        height=600,
        margin={"r": 20, "t": 20, "l": 20, "b": 100},
        bargap=0.2,
        xaxis=dict(tickangle=45),
    )

    return html.Div([
        html.H2("📊 Data Table"),
        dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in df.columns],
            data=df.round(2).to_dict('records'),
            style_table={'overflowX': 'auto'}
        ),
        html.H2("📈 Weekly Trends"),

        dcc.Graph(figure=fig_line),

        html.Div(
            dcc.Graph(figure=fig_bar),
            style={'overflowX': 'scroll', 'width': '100%', 'whiteSpace': 'nowrap'}
        ),
    ])


@dash.callback(
    [Output('weekly-stored-data', 'data'),
     Output('file-name-weekly', 'children', allow_duplicate=True),
     Output('weekly-graph-container', 'children'),
     Output('weekly-table-container', 'children')],
    [Input('upload-data-weekly', 'contents'),
     Input('url', 'pathname')],
    [State('weekly-stored-data', 'data')],
    prevent_initial_call='initial_duplicate'
)
def unified_callback(contents, pathname, stored_data):
    ctx = dash.callback_context
    
    # Default returns
    new_stored_data = dash.no_update
    file_message = dash.no_update
    graphs = "📥 Upload a file to see graphs"
    table = ""
    
    
    if not ctx.triggered:
        existing_data = load_processed_data()
        if existing_data:
           
            weekly_df = pd.DataFrame(existing_data['weekly_breakdown'])
            graphs = generate_visuals(weekly_df)
            
        else:
            file_message = "📭 No data available"
        return new_stored_data, file_message, graphs, table
    
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger == 'upload-data-weekly' and contents:
        try:
            new_df = clean_and_merge_data([contents])
            existing_data = load_processed_data() or {}
            
            
            processed_data = weekly_breakdown(new_df)

            new_weekly_breakdown = processed_data['weekly_breakdown'].to_dict(orient='records')
            existing_data = load_processed_data()
            if existing_data:
                existing_weekly_breakdown = existing_data.get('weekly_breakdown', [])
                
                # Ensure existing_weekly_breakdown is a list before appending
                if not isinstance(existing_weekly_breakdown, list):
                    existing_weekly_breakdown = []
                
                # Append new data
                processed_data['weekly_breakdown'] = existing_weekly_breakdown + new_weekly_breakdown
            else:
                processed_data['weekly_breakdown'] = new_weekly_breakdown

            # Save the processed data to file
            with open(PROCESSED_DATA_FILE, 'w') as f:
                json.dump(processed_data, f, indent=4)  # Pretty print for readability
            
            
            final_data = load_processed_data()
            
            file_message = "✅ File uploaded & processed!"
            
            # Convert back to DataFrame for display
            weekly_df = pd.DataFrame(final_data['weekly_breakdown'])
            graphs = generate_visuals(weekly_df)
       
            
        except Exception as e:
            file_message = f"⚠️ Error: {str(e)}"
            return dash.no_update, file_message, dash.no_update, dash.no_update, dash.no_update
    
    elif trigger == 'url':
        existing_data = load_processed_data()
        if existing_data:
           
            file_message = "✅ Loaded existing data"
            
            # Convert back to DataFrame for display
            weekly_df = pd.DataFrame(existing_data['weekly_breakdown'])
            graphs = generate_visuals(weekly_df)
            
        else:
            file_message = "📭 No data available"
    
    return new_stored_data, file_message, graphs, table
