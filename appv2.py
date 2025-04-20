import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import json
import requests

# Configurações iniciais
st.set_page_config(layout="wide", page_title="Dashboard Titan Fuel")
st.markdown(
    """
    <style>
        .main {
            background-color: #0e1117;
            color: white;
        }
        [data-testid="stMetric"] {
            background-color: #b30000;
            border-radius: 10px;
            padding: 15px;
            margin: 5px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Carrega os dados
df = pd.read_excel("titan_fuel_vendas.xlsx")
df['Data'] = pd.to_datetime(df['Data'])

# Filtros
st.sidebar.header("Filtros")
data_inicio = st.sidebar.date_input("Data Inicial", df['Data'].min())
data_fim = st.sidebar.date_input("Data Final", df['Data'].max())
estado_sel = st.sidebar.multiselect("Estado", df['Estado'].unique(), default=df['Estado'].unique())
produto_sel = st.sidebar.multiselect("Produto", df['Produto'].unique(), default=df['Produto'].unique())

df_filtrado = df[
    (df['Data'] >= pd.to_datetime(data_inicio)) &
    (df['Data'] <= pd.to_datetime(data_fim)) &
    (df['Estado'].isin(estado_sel)) &
    (df['Produto'].isin(produto_sel))
]

# Função para formatar valores grandes
def formatar_valor(valor):
    if valor >= 1_000_000:
        return f"R$ {valor / 1_000_000:.1f} mi"
    elif valor >= 1_000:
        return f"R$ {valor / 1_000:.0f} mil"
    else:
        return f"R$ {valor:,.2f}"

# KPIs
receita_total = df_filtrado['Receita Total'].sum()
total_vendas = df_filtrado['Quantidade Vendida'].sum()
lucro_total = df_filtrado['Lucro'].sum()
ticket_medio = receita_total / total_vendas if total_vendas > 0 else 0

st.title("📊 Dashboard de Vendas - Titan Fuel")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Receita Total", formatar_valor(receita_total))
col2.metric("📦 Total de Vendas", f"{total_vendas}")
col3.metric("📈 Lucro Total", formatar_valor(lucro_total))
col4.metric("🎫 Ticket Médio", f"R$ {ticket_medio:,.2f}")


# Mapa interativo com todos os estados e contorno do Brasil
st.markdown("### 📍 Receita por Estado (Mapa Interativo)")

sigla_para_estado = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins"
}

# DataFrame com todos os estados por extenso
todos_os_estados = pd.DataFrame.from_dict(sigla_para_estado, orient='index', columns=['Estado_Nome']).reset_index()
todos_os_estados.columns = ['Estado', 'Estado_Nome']

# Receita total por estado com todos presentes
vendas_por_estado = df_filtrado.groupby("Estado")["Receita Total"].sum().reset_index()
vendas_por_estado = todos_os_estados.merge(vendas_por_estado, on="Estado", how="left")
vendas_por_estado["Receita Total"] = vendas_por_estado["Receita Total"].fillna(0)

# GeoJSON dos estados do Brasil
geojson_url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
geojson_data = requests.get(geojson_url).json()

# Gráfico
fig_mapa = px.choropleth(
    vendas_por_estado,
    geojson=geojson_data,
    featureidkey="properties.name",
    locations="Estado_Nome",
    color="Receita Total",
    color_continuous_scale="Reds",
    range_color=(0, vendas_por_estado["Receita Total"].max())
)

fig_mapa.update_geos(
    fitbounds="locations",
    visible=True,
    showcountries=True,
    showcoastlines=True,
    showland=True,
    landcolor="#0e1117"
)
fig_mapa.update_layout(
    paper_bgcolor='#0e1117',
    plot_bgcolor='#0e1117',
    font_color='white',
    margin={"r":0,"t":0,"l":0,"b":0}
)

st.plotly_chart(fig_mapa, use_container_width=True)

# Lucro por estado
st.subheader("🧠 Lucro por Estado")
lucro_estado = df_filtrado.groupby("Estado")["Lucro"].sum().reset_index().sort_values(by="Lucro")
fig_lucro_estado = px.bar(
    lucro_estado,
    x="Estado",
    y="Lucro",
    color="Lucro",
    color_continuous_scale="Reds"
)
fig_lucro_estado.update_layout(paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font_color='white')
st.plotly_chart(fig_lucro_estado, use_container_width=True)

# Margem de lucro por produto
st.subheader("💡 Margem de Lucro por Produto")
margem_produto = df_filtrado.groupby("Produto").agg({'Lucro': 'sum', 'Receita Total': 'sum'}).reset_index()
margem_produto['Margem (%)'] = (margem_produto['Lucro'] / margem_produto['Receita Total']) * 100
margem_produto = margem_produto.sort_values(by="Margem (%)")

fig_margem = px.bar(
    margem_produto,
    x="Produto",
    y="Margem (%)",
    color="Margem (%)",
    color_continuous_scale="Reds"
)
fig_margem.update_layout(paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font_color='white')
st.plotly_chart(fig_margem, use_container_width=True)

# Receita ao longo do tempo
st.subheader("📅 Receita ao Longo do Tempo")
receita_tempo = df_filtrado.groupby("Data")["Receita Total"].sum().reset_index()
fig_receita = px.line(
    receita_tempo,
    x="Data",
    y="Receita Total",
    markers=True,
    line_shape="spline"
)
fig_receita.update_traces(line_color='red')
fig_receita.update_layout(paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font_color='white')
st.plotly_chart(fig_receita, use_container_width=True)

# Receita por categoria
st.subheader("📦 Receita por Categoria de Produto")
receita_categoria = df_filtrado.groupby("Categoria")["Receita Total"].sum().reset_index().sort_values(by="Receita Total")
fig_cat = px.bar(
    receita_categoria,
    x="Categoria",
    y="Receita Total",
    color="Receita Total",
    color_continuous_scale="Reds"
)
fig_cat.update_layout(paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font_color='white')
st.plotly_chart(fig_cat, use_container_width=True)
