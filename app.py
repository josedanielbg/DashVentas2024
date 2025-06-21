import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# --- Data Loading and Preprocessing ---
# In a real application, you would typically load data from a persistent source
# For this example, we'll assume the CSV file is in the same directory as app.py
# If your data is in Google Drive, you'll need to adapt the loading mechanism
# when running outside of Colab (e.g., download the file or use a different method).

# Try to load the data from a local CSV file
try:
    data = pd.read_csv('ventas2024_completo.csv', parse_dates=['Fecha'])
except FileNotFoundError:
    print("Error: ventas2024_completo.csv not found. Please make sure the data file is in the same directory as app.py")
    # Exit or handle the error appropriately
    exit() # Or raise an exception

# Calculate aggregated data needed for the dashboard

# Calculate total units sold per product
product_sales = data.groupby('Producto')['Unidades Vendidas'].sum().reset_index()

# Calculate total revenue per product
ingresos_por_producto = data.groupby('Producto')['Ingresos'].sum().reset_index()
# Handle potential missing values before applying split()
ingresos_por_producto['Producto_Corto'] = ingresos_por_producto['Producto'].apply(lambda x: x.split()[0] if isinstance(x, str) else x)
ingresos_por_producto = ingresos_por_producto.sort_values(by='Ingresos', ascending=False)

# Calculate total revenue per seller
ingresos_por_vendedor = data.groupby('Vendedor')['Ingresos'].sum().reset_index()
ingresos_por_vendedor = ingresos_por_vendedor.sort_values(by='Ingresos', ascending=False)

# Calculate daily sales
daily_sales = data.groupby('Fecha')[['Unidades Vendidas', 'Ingresos']].sum().reset_index()


# --- Dash App Definition ---

# Create the Dash app
# Use __name__ as the first argument to the Dash constructor
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server # This is needed for deployment

# Define the layout of the app
app.layout = dbc.Container([
    html.H1("Análisis de Ventas - Tienda de Abarrotes (Diciembre 2024)", className="text-center my-4"),

    dbc.Row([
        dbc.Col(
            dcc.Graph(id='ingresos-por-producto'),
            width=6
        ),
        dbc.Col(
            dcc.Graph(id='ingresos-por-vendedor-pie'),
            width=6
        ),
    ]),

    dbc.Row([
        dbc.Col(
            dcc.Graph(id='daily-sales-line'),
            width=12
        ),
    ]),

    dbc.Row([
        dbc.Col(
            dcc.Graph(id='ingresos-por-vendedor-bar'),
            width=12
        )
    ]),

    dbc.Row([
        dbc.Col(
            dcc.Graph(id='product-performance-indicators'),
            width=12
        ),
    ]),

    dbc.Row([
         dbc.Col(
            [
                html.H3("Análisis por Vendedor", className="text-center"),
                dcc.Dropdown(
                    id='seller-dropdown',
                    options=[{'label': seller, 'value': seller} for seller in ingresos_por_vendedor['Vendedor']],
                    value=ingresos_por_vendedor['Vendedor'].iloc[0] if not ingresos_por_vendedor.empty else None, # Default value to the top seller, handle empty case
                    clearable=False,
                    className="mb-3"
                ),
                dcc.Graph(id='seller-product-distribution')
            ],
            width=12
        ),
    ]),


], fluid=True)

# --- Callbacks to Update Graphs ---

@app.callback(
    Output('ingresos-por-producto', 'figure'),
    Input('ingresos-por-producto', 'id') # Dummy input
)
def update_ingresos_por_producto_graph(_):
    fig = px.bar(ingresos_por_producto,
                 x='Producto_Corto',
                 y='Ingresos',
                 title='Ingresos por Producto',
                 labels={'Producto_Corto': 'Producto', 'Ingresos': 'Ingresos'},
                 template='plotly_white')
    fig.update_layout(xaxis_tickangle=-45)
    # Update text position for better visibility if bars are short
    fig.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
    return fig

@app.callback(
    Output('ingresos-por-vendedor-pie', 'figure'),
    Input('ingresos-por-vendedor-pie', 'id') # Dummy input
)
def update_ingresos_por_vendedor_pie(_):
    fig = px.pie(ingresos_por_vendedor,
                 values='Ingresos',
                 names='Vendedor',
                 title='Distribución de Ingresos por Vendedor',
                 hover_data=['Ingresos'],
                 labels={'Ingresos':'Ingresos Totales'},
                 template='plotly_white')
    fig.update_traces(textposition='inside', textinfo='percent+label',
                      hovertemplate="<b>%{label}</b><br>Ingresos: %{value:,.0f}<br>Porcentaje: %{percent}")
    return fig

@app.callback(
    Output('daily-sales-line', 'figure'),
    Input('daily-sales-line', 'id') # Dummy input
)
def update_daily_sales_line(_):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily_sales['Fecha'], y=daily_sales['Ingresos'], mode='lines+markers', name='Ingresos Diarios'))
    fig.add_trace(go.Scatter(x=daily_sales['Fecha'], y=daily_sales['Unidades Vendidas'], mode='lines+markers', name='Unidades Vendidas Diarias', yaxis='y2'))

    fig.update_layout(
        title='Ingresos y Unidades Vendidas Diarias',
        xaxis_title='Fecha',
        yaxis_title='Ingresos',
        yaxis2=dict(
            title='Unidades Vendidas',
            overlaying='y',
            side='right'
        ),
        template='plotly_white',
        hovermode='x unified' # Improve hover experience
    )
    return fig


@app.callback(
    Output('ingresos-por-vendedor-bar', 'figure'),
    Input('ingresos-por-vendedor-bar', 'id') # Dummy input
)
def update_ingresos_por_vendedor_bar(_):
    fig = px.bar(ingresos_por_vendedor,
                 x='Vendedor',
                 y='Ingresos',
                 title='Ingresos Totales por Vendedor',
                 labels={'Vendedor': 'Vendedor', 'Ingresos': 'Ingresos'},
                 template='plotly_white')
    fig.update_layout(xaxis_tickangle=-45)
    fig.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
    return fig


@app.callback(
    Output('product-performance-indicators', 'figure'),
    Input('product-performance-indicators', 'id') # Dummy input
)
def update_product_indicators(_):
    # Handle cases where product_sales or ingresos_por_producto might be empty
    producto_mas_vendido_unidades = product_sales.loc[product_sales['Unidades Vendidas'].idxmax()] if not product_sales.empty else {'Producto': 'N/A', 'Unidades Vendidas': 0}
    producto_menos_vendido_unidades = product_sales.loc[product_sales['Unidades Vendidas'].idxmin()] if not product_sales.empty else {'Producto': 'N/A', 'Unidades Vendidas': 0}
    producto_mas_ingresos = ingresos_por_producto.loc[ingresos_por_producto['Ingresos'].idxmax()] if not ingresos_por_producto.empty else {'Producto': 'N/A', 'Ingresos': 0}
    producto_menos_ingresos = ingresos_por_producto.loc[ingresos_por_producto['Ingresos'].idxmin()] if not ingresos_por_producto.empty else {'Producto': 'N/A', 'Ingresos': 0}
    promedio_ingresos = ingresos_por_vendedor['Ingresos'].mean() if not ingresos_por_vendedor.empty else 0


    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="number",
        value=producto_mas_vendido_unidades['Unidades Vendidas'],
        title={"text": f"Producto Más Vendido<br><span style='font-size:0.8em;color:gray'>({producto_mas_vendido_unidades['Producto']})</span>"},
        domain={'x': [0, 0.5], 'y': [0.5, 1]}
    ))

    fig.add_trace(go.Indicator(
        mode="number",
        value=producto_menos_vendido_unidades['Unidades Vendidas'],
        title={"text": f"Producto Menos Vendido<br><span style='font-size:0.8em;color:gray'>({producto_menos_vendido_unidades['Producto']})</span>"},
        domain={'x': [0.5, 1], 'y': [0.5, 1]}
    ))

    fig.add_trace(go.Indicator(
        mode="number",
        value=producto_mas_ingresos['Ingresos'],
        title={"text": f"Producto con Más Ingresos<br><span style='font-size:0.8em;color:gray'>({producto_mas_ingresos['Producto']})</span>"},
         number={'prefix': "$", 'valueformat': '.,0f'},
        domain={'x': [0, 0.5], 'y': [0, 0.45]}
    ))

    fig.add_trace(go.Indicator(
        mode="number",
        value=producto_menos_ingresos['Ingresos'],
        title={"text": f"Producto con Menos Ingresos<br><span style='font-size:0.8em;color:gray'>({producto_menos_ingresos['Producto']})</span>"},
         number={'prefix': "$", 'valueformat': '.,0f'},
        domain={'x': [0.5, 1], 'y': [0, 0.45]}
    ))

    fig.update_layout(
        grid = {'rows': 2, 'columns': 2, 'pattern': "independent"},
        title="Indicadores Clave de Ventas por Producto",
        template='plotly_white'
    )
    return fig


@app.callback(
    Output('seller-product-distribution', 'figure'),
    Input('seller-dropdown', 'value')
)
def update_seller_product_distribution(selected_seller):
    if selected_seller is None:
        return go.Figure() # Return an empty figure if no seller is selected

    filtered_data = data[data['Vendedor'] == selected_seller]
    ingresos_productos_vendedor = filtered_data.groupby('Producto')['Ingresos'].sum().reset_index()
    ingresos_productos_vendedor = ingresos_productos_vendedor.sort_values(by='Ingresos', ascending=False)

    fig = px.bar(ingresos_productos_vendedor,
                 x='Producto',
                 y='Ingresos',
                 title=f'Distribución de Ingresos por Producto para {selected_seller}',
                 labels={'Producto': 'Producto', 'Ingresos': 'Ingresos'},
                 template='plotly_white')
    fig.update_layout(xaxis_tickangle=-45)
    fig.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
    return fig


# --- Run the app ---
if __name__ == '__main__':
    # When running locally, use debug=True
    # When deploying, set debug=False and use the server object
    app.run_server(debug=True)
