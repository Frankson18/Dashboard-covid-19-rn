import pandas as pd
import plotly.express as px
import streamlit as st

def carregar_dados(urls):
  df = pd.read_csv(urls[0],sep=';')
  #https://cidades.ibge.gov.br/brasil/sintese/rn?indicadores=29171
  with open(urls[1],'r',encoding="utf8") as arquivo:
    municipios = arquivo.read()
  geojson = pd.read_json(urls[2])
  serra_caiada=pd.read_json(urls[3])
  dados_idade = pd.read_csv(urls[4],sep=';')

  return df,municipios,geojson,serra_caiada,dados_idade

def calcular_media_movel_confirmados(df,rolling):
  df_data = df.groupby('data').sum('obitos')
  df_data[ f'media-confirmados-{rolling}dias' ] = df_data.confirmados.rolling(rolling).mean()
  df_data['data'] = df_data.index
  y_label=f"media-confirmados-{rolling}dias"
  fig = px.line(df_data, x='data', y=y_label)
  fig.update_layout(xaxis=dict(showgrid=False))
  fig.update_yaxes(showgrid=True, gridcolor='black')
  return fig
  
def calcular_media_movel_obitos(df,rolling):
  df_data = df.groupby('data').sum('obitos')
  df_data[f'media-obitos-{rolling}dias'] = df_data.obitos.rolling(rolling).mean()
  df_data['data'] = df_data.index
  fig = px.line(df_data, x='data', y=f"media-obitos-{rolling}dias")
  fig.update_layout(xaxis=dict(showgrid=False))
  fig.update_yaxes(showgrid=True, gridcolor='black')

  return fig

def municipios_obitos (df,municipios,serra_caiada,geojson):
  df_data_municipios = df.groupby('mun_residencia').sum('obitos')
  df_data_municipios['municipio'] = df_data_municipios.index
  df_data_municipios.rename(index={'Augusto Severo (Campo Grande)':'Augusto Severo','Januário Cicco (Boa Saúde)':'Januário Cicco'},inplace = True)
  df_data_municipios['municipio'][10] ='Augusto Severo'
  df_data_municipios['municipio'][55]= 'Januário Cicco'

  df_data_municipios.sort_values(by=['mun_residencia'],axis=0,inplace = True)

  municipios = municipios.split('\n')
  municipios_dados = []
  for i in range(len(municipios)):
    municipios_dados.append(municipios[i].replace('\tpotiguar, norte-rio-grandense, rio-grandense-do-norte',''))

  municipios_dados.pop()
  municipios_dados.pop()

  municipios_dados_corretos = []

  for i in range(len(municipios_dados)):
    municipios_dados_corretos.append(municipios_dados[i].replace('pessoas',''))

  municipios_list = []

  for i in range(len(municipios_dados_corretos)):
    municipios_list.append(municipios_dados_corretos[i].split('\t'))

  municipios_df = pd.DataFrame(municipios_list)
  municipios_df[0][12] = 'Augusto Severo'
  municipios_df.rename(columns={0:'municipio',1:'populacao'},inplace= True)
  municipios_df['populacao'] = municipios_df['populacao'].astype(int)
  municipios_df.sort_values(by=['municipio'],axis=0,inplace = True)
  municipios_df.set_index(df_data_municipios['municipio'],inplace=True)

  municipios_df = pd.concat([municipios_df['municipio'],df_data_municipios['obitos'],municipios_df['populacao']],axis=1)

  mortes_por_habitantes = pd.DataFrame((municipios_df['obitos']/municipios_df['populacao'])*100000)
  mortes_por_habitantes.rename(columns={0:'taxa de obitos por 100 habitantes'},inplace= True)
  mortes_por_habitantes.sort_values(by='taxa de obitos por 100 habitantes',inplace= True)
  mortes_por_habitantes['municipio'] = mortes_por_habitantes.index

  max = (mortes_por_habitantes['taxa de obitos por 100 habitantes'].idxmax(),mortes_por_habitantes['taxa de obitos por 100 habitantes'].max())
  min = (mortes_por_habitantes['taxa de obitos por 100 habitantes'].idxmin(),mortes_por_habitantes['taxa de obitos por 100 habitantes'].min())

  serra_caiada.features[0]['id'] = 'Serra Caiada'

  geojson_rn = {'features':[],'type': 'FeatureCollection'}
  for i in range(len(geojson.features)):
    geojson.features[i]['id'] = geojson.features[i]['properties']['name']
    geojson_rn['features'].append(geojson.features[i])

  geojson_rn['features'].append(serra_caiada.features[0])

  fig = px.choropleth_mapbox(mortes_por_habitantes,locations='municipio', color ='taxa de obitos por 100 habitantes',
                     geojson=geojson_rn,color_continuous_scale='blues',center={'lat':-5.68,'lon':-36.52},
                     opacity= 0.4,hover_data = {'taxa de obitos por 100 habitantes': True},width=1080,height=720)

  fig.update_layout(
     mapbox_style = 'carto-darkmatter'
  )

  return fig,max,min

def faixa_idade(dados_idade):
  for i in range(len(dados_idade["Grupo de Faixa Etária"])):
    dados_idade["Grupo de Faixa Etária"][i] = dados_idade["Grupo de Faixa Etária"][i].replace("-"," a ")

  fig = px.bar(dados_idade,x="Grupo de Faixa Etária",y=["Masculino","Feminino"])
  return fig

def main(): 
    urls = ['https://covid.lais.ufrn.br/dados/boletim/evolucao_municipios.csv',
        'municipios_dados.txt',
        'https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-24-mun.json',
        'https://servicodados.ibge.gov.br/api/v3/malhas/municipios/2410306?formato=application/vnd.geo+json&qualidade=maxima',
        'Faixa Etária dos Óbitos por Covid19.csv']

    df,municipios,geojson,serra_caiada,dados_idade = carregar_dados(urls)

    st.set_page_config(layout="wide")
    st.title("Covid-19 RN")
    option = st.selectbox('Média Móvel',('7', '5', '3'))
    col1,col2 = st.columns(2)

    col1.subheader('Casos Confirmados por Dia')
    fig1 = calcular_media_movel_confirmados(df,int(option))
    col1.plotly_chart(fig1,use_container_width=True)

    col2.subheader('Óbitos Confirmados por Dia')
    fig1_obitos = calcular_media_movel_obitos(df,int(option))
    col2.plotly_chart(fig1_obitos,use_container_width=True)

    st.subheader('Óbitos Confirmados')
    fig_muinicipios,max,min = municipios_obitos (df,municipios,serra_caiada,geojson)
    st.plotly_chart(fig_muinicipios,use_container_width=True)

    st.subheader('Faixa Étaria dos Obitos')
    fig_idade = faixa_idade(dados_idade)
    st.plotly_chart(fig_idade,use_container_width=True)

if __name__ == '__main__': 
    main()