import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings

warnings.filterwarnings("ignore")

# Load the data
url = 'https://drive.google.com/file/d/1yQnLfjiEoljn88_EbY0sYTx3SxAKJfUF/view?usp=sharing'
file_id = url.split('/')[-2]
download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
data = pd.read_csv(download_url)

# Data Preprocessing and Calculation (based on your notebook)
data['Fecha'] = pd.to_datetime(data['Fecha'])
data['Ingresos'] = data['Unidades Vendidas'] * data['Precio'] # Assuming 'Ingresos' was calculated here based on previous cells

# Calculate aggregated data needed for the dashboard
# Calculate total units sold per product
product_sales = data.groupby('Producto')['Unidades Vendidas'].sum().reset_index()

# Calculate total revenue per product
ingresos_por_producto = data.groupby('Producto')['Ingresos'].sum().reset_index()
ingresos_por_producto['Producto_Corto'] = ingresos_por_producto['Producto'].apply(lambda x: x.split()[0])
ingresos_por_producto = ingresos_por_producto.sort_values(by='Ingresos', ascending=False)

# Calculate total revenue per seller
ingresos_por_vendedor = data.groupby('Vendedor')['Ingresos'].sum().reset_index()
ingresos_por_vendedor = ingresos_por_vendedor.sort_values(by='Ingresos', ascending=False)
# Add a 'Rank' column to the seller revenue data for the ranking chart
ingresos_por_vendedor['Rank'] = ingresos_por_vendedor['Ingresos'].rank(method='dense', ascending=False).astype(int)

# Calculate daily sales
daily_sales = data.groupby('Fecha')[['Unidades Vendidas', 'Ingresos']].sum().reset_index()

# Calculate the product indicators
producto_mas_vendido_unidades = product_sales.loc[product_sales['Unidades Vendidas'].idxmax()]
producto_menos_vendido_unidades = product_sales.loc[product_sales['Unidades Vendidas'].idxmin()]
producto_mas_ingresos = ingresos_por_producto.loc[ingresos_por_producto['Ingresos'].idxmax()]
producto_menos_ingresos = ingresos_por_producto.loc[ingresos_por_producto['Ingresos'].idxmin()]


# Define the color palette
colores_contraste = ['#E6A57E', '#B07D62', '#A7BFA7', '#CFC2A4']

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server # This is needed for deployment on platforms like Heroku

# Define the layout of the app
app.layout = dbc.Container([
    html.H1("Análisis de Ventas - Tienda de Abarrotes (Enero 2024)", className="text-center my-4"),

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
                    value=ingresos_por_vendedor['Vendedor'].iloc[0],
                    clearable=False,
                    className="mb-3"
                ),
                dcc.Loading(
                    id="loading-seller-card",
                    type="default",
                    children=[html.Div(id="seller-performance-card")]
                )
            ],
            width=12
        ),
    ]),

], fluid=True)

# Define callbacks to update graphs
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
                 template='plotly_white',
                 color='Producto_Corto',
                 color_discrete_sequence=colores_contraste)
    fig.update_layout(xaxis_tickangle=-45)
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
                 template='plotly_white',
                 color_discrete_sequence=colores_contraste)
    fig.update_traces(textposition='inside', textinfo='percent+label',
                      hovertemplate="<b>%{label}</b><br>Ingresos: %{value:,.0f}<br>Porcentaje: %{percent}")
    return fig

@app.callback(
    Output('daily-sales-line', 'figure'),
    Input('daily-sales-line', 'id') # Dummy input
)
def update_daily_sales_line(_):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily_sales['Fecha'], y=daily_sales['Ingresos'], mode='lines+markers', name='Ingresos Diarios', line=dict(color=colores_contraste[0])))
    fig.add_trace(go.Scatter(x=daily_sales['Fecha'], y=daily_sales['Unidades Vendidas'], mode='lines+markers', name='Unidades Vendidas Diarias', yaxis='y2', line=dict(color=colores_contraste[1])))

    fig.update_layout(
        title='Ingresos y Unidades Vendidas Diarias',
        xaxis_title='Fecha',
        yaxis_title='Ingresos',
        yaxis2=dict(
            title='Unidades Vendidas',
            overlaying='y',
            side='right'
        ),
        template='plotly_white'
    )
    return fig

@app.callback(
    Output('ingresos-por-vendedor-bar', 'figure'),
    Input('ingresos-por-vendedor-bar', 'id') # Dummy input
)
def update_ingresos_por_vendedor_bar(_):
    ingresos_por_vendedor_ranked = data.groupby('Vendedor')['Ingresos'].sum().reset_index()
    ingresos_por_vendedor_ranked = ingresos_por_vendedor_ranked.sort_values(by='Ingresos', ascending=False).reset_index(drop=True)
    ingresos_por_vendedor_ranked['Rank'] = ingresos_por_vendedor_ranked.index + 1

    ingresos_por_vendedor_ranked['Text_Label'] = ingresos_por_vendedor_ranked.apply(
        lambda row: f"#{row['Rank']}<br>${row['Ingresos']:,.0f}".replace(',', '.'), axis=1
    )

    fig = px.bar(ingresos_por_vendedor_ranked,
                 x='Vendedor',
                 y='Ingresos',
                 text='Text_Label',
                 title='Ranking de Ingresos Totales por Vendedor',
                 labels={'Vendedor': 'Vendedor', 'Ingresos': 'Ingresos'},
                 template='plotly_white',
                 color='Vendedor',
                 color_discrete_sequence=colores_contraste)
    fig.update_layout(xaxis_tickangle=-45)
    fig.update_traces(textposition='outside')
    return fig

@app.callback(
    Output('product-performance-indicators', 'figure'),
    Input('product-performance-indicators', 'id') # Dummy input
)
def update_product_indicators(_):
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="number",
        value=producto_mas_vendido_unidades['Unidades Vendidas'],
        title={"text": f"Producto Más Vendido<br><span style='font-size:0.8em;color:gray'>({producto_mas_vendido_unidades['Producto']})</span>"},
        domain={'x': [0, 0.25], 'y': [0.5, 1]}
    ))

    fig.add_trace(go.Indicator(
        mode="number",
        value=producto_menos_vendido_unidades['Unidades Vendidas'],
        title={"text": f"Producto Menos Vendido<br><span style='font-size:0.8em;color:gray'>({producto_menos_vendido_unidades['Producto']})</span>"},
        domain={'x': [0.35, 0.60], 'y': [0.5, 1]}
    ))

    fig.add_trace(go.Indicator(
        mode="number",
        value=producto_mas_ingresos['Ingresos'],
        title={"text": f"Producto con Más Ingresos<br><span style='font-size:0.8em;color:gray'>({producto_mas_ingresos['Producto']})</span>"},
         number={'prefix': "$", 'valueformat': '.,0f'},
        domain={'x': [0, 0.25], 'y': [0, 0.45]}
    ))

    fig.add_trace(go.Indicator(
        mode="number",
        value=producto_menos_ingresos['Ingresos'],
        title={"text": f"Producto con Menos Ingresos<br><span style='font-size:0.8em;color:gray'>({producto_menos_ingresos['Producto']})</span>"},
         number={'prefix': "$", 'valueformat': '.,0f'},
        domain={'x': [0.35, 0.60], 'y': [0, 0.45]}
    ))

    fig.update_layout(
        grid = {'rows': 2, 'columns': 2, 'pattern': "independent"},
        title="Indicadores Clave de Ventas por Producto"
    )

    return fig

@app.callback(
    Output('seller-performance-card', 'children'),
    Input('seller-dropdown', 'value')
)
def update_seller_performance_card(selected_seller):
    if not selected_seller:
        return html.Div("Seleccione un vendedor para ver su rendimiento.", className="text-center")

    # Filter data for the selected seller
    data_vendedor = data[data['Vendedor'] == selected_seller]

    if data_vendedor.empty:
        return html.Div(f"No hay datos disponibles para el vendedor {selected_seller}", className="text-center")

    # Calculate total revenue for the selected seller
    ingresos_totales_vendedor = data_vendedor['Ingresos'].sum()

    # Calculate the mean income across all sellers for the delta reference
    mean_ingresos_all_sellers = data.groupby('Vendedor')['Ingresos'].sum().mean()

    # Calculate the revenue per product for this seller
    ingresos_productos_vendedor = data_vendedor.groupby('Producto')['Ingresos'].sum().reset_index()
    ingresos_productos_vendedor = ingresos_productos_vendedor.sort_values(by='Ingresos', ascending=False)

    # Create the figure for the seller card
    fig = go.Figure(go.Indicator(
        mode = "number+delta",
        value = ingresos_totales_vendedor,
        number = {'prefix': "$", 'valueformat': '.,0f'},
        delta = {'reference': mean_ingresos_all_sellers, 'relative': True, 'valueformat': '.1%'},
        title = {"text": f"Ingresos Totales: {selected_seller}"},
        domain = {'x': [0, 1], 'y': [0.6, 1]}
    ))

    # Create the table with the product details for the seller
    fig.add_trace(go.Table(
        header=dict(values=['Producto', 'Ingresos'],
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[ingresos_productos_vendedor['Producto'],
                           ingresos_productos_vendedor['Ingresos'].apply(lambda x: f"${x:,.0f}")],
                   fill_color='lavender',
                   align='left'),
        domain = {'x': [0, 1], 'y': [0, 0.5]}
    ))

    fig.update_layout(
        title_text=f'Performance de Ventas de {selected_seller}',
        height=400
    )

    return dcc.Graph(figure=fig)

if __name__ == '__main__':
    app.run_server(debug=True, mode='external') # Use mode='external' for Colab environment
