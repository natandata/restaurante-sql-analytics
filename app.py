"""Interface local. Artefatos técnicos continuam em centavos e chaves estáveis."""
from pathlib import Path
import base64
import pandas as pd
import streamlit as st
import altair as alt
from src.pipeline import create_connection,load,query,SQL
st.set_page_config(page_title='SQL para restaurantes',layout='wide')
_font=base64.b64encode((Path(__file__).parent/'assets/Inter.ttf').read_bytes()).decode()
st.markdown('<style>@font-face{font-family:Inter;src:url(data:font/ttf;base64,'+_font+')} html,body,h1,h2,h3,p,button,input,select,[data-testid=stApp]{font-family:Inter,Arial,sans-serif}h1,h2{letter-spacing:-.02em}.brand{color:#3f3cd8;font-size:24px;font-weight:800}</style>',unsafe_allow_html=True)
lang=st.sidebar.radio('Idioma' if st.session_state.get('language','PT')=='PT' else 'Language',['PT','EN'],key='language');en=lang=='EN'
def t(pt,eng):return eng if en else pt
def num(v,digits=0):
 s=f'{v:,.{digits}f}';return s if en else s.translate(str.maketrans(',.','.,'))
def money(v):return 'R$ '+num(v/100,2)
def revenue_chart(df,key,line=False):
 z=df.copy();z['brl']=z.revenue_cents/100
 expr="format(datum.value, ',.0f')" if en else "replace(format(datum.value, ',.0f'), ',', '.')"
 chart=alt.Chart(z).mark_line(color='#3f3cd8') if line else alt.Chart(z).mark_bar(color='#3f3cd8')
 chart=chart.encode(x=alt.X(key+':O',title=t('Mês','Month') if key=='month' else t('Restaurante','Restaurant')),y=alt.Y('brl:Q',title=t('Receita (R$)','Revenue (BRL)'),axis=alt.Axis(labelExpr=expr))).properties(height=300)
 st.altair_chart(chart,width='stretch')
labels={'restaurant_id':t('Restaurante','Restaurant'),'orders':t('Pedidos','Orders'),'revenue_cents':t('Receita (centavos)','Revenue (cents)'),'share_pct':t('Participação (%)','Share (%)'),'revenue_rank':t('Posição','Rank'),'month':t('Mês','Month'),'change_cents':t('Variação (centavos)','Change (cents)'),'product_id':t('Produto','Product'),'name':t('Nome','Name'),'units':t('Unidades','Units'),'contribution_cents':t('Contribuição (centavos)','Contribution (cents)'),'order_id':t('Pedido','Order'),'total_cents':t('Total (centavos)','Total (cents)'),'line_total_cents':t('Itens (centavos)','Lines (cents)'),'ticket_cents':t('Ticket (centavos)','Average ticket (cents)'),'min_ticket_cents':t('Ticket mínimo (centavos)','Minimum ticket (cents)'),'max_ticket_cents':t('Ticket máximo (centavos)','Maximum ticket (cents)')}
def view(df):
 df=df.copy()
 for c in df:
  if pd.api.types.is_numeric_dtype(df[c]):df[c]=df[c].map(lambda v:t('Não se aplica','Not applicable') if pd.isna(v) else num(v,3 if c=='share_pct' else 2 if c=='ticket_cents' else 0))
 return df.rename(columns=labels)
st.markdown('<div class="brand">data with natan</div>',unsafe_allow_html=True)
st.title(t('SQL para decisões de restaurante','SQL for restaurant decisions'))
st.info(t('Estudo independente. Todos os dados são sintéticos, sem clientes reais.','Independent study. Entirely synthetic data, no real clients.'))
seed=st.sidebar.number_input('Seed',value=20261111,min_value=0,max_value=2**31-1)
n=st.sidebar.slider(t('Pedidos','Orders'),100,1000,500,100)
@st.cache_data
def data(seed,n):
 c=create_connection();load(c,seed,n);frames={f:query(c,f) for f in ['02_reconcile.sql','03_restaurants.sql','04_monthly.sql','05_item_margin.sql','06_ticket.sql']};wrong=c.execute('SELECT SUM(o.total_cents) FROM orders o JOIN order_lines l USING(order_id)').fetchone()[0];c.close();return frames,wrong
frames,wrong=data(seed,n);rev=int(frames['02_reconcile.sql'].total_cents.sum())
a,b,c=st.columns(3);a.metric(t('Receita','Revenue'),money(rev));b.metric(t('Pedidos','Orders'),num(n));c.metric(t('Excesso do JOIN errado','Wrong JOIN overcount'),money(wrong-rev))
tabs=st.tabs([t('Restaurantes','Restaurants'),t('Meses','Months'),t('Margem','Margin'),t('Conciliar','Reconcile'),'SQL'])
with tabs[0]:
 rank=frames['03_restaurants.sql'];all_label=t('Todos','All');rid=st.selectbox(t('Filtrar restaurante','Restaurant filter'),[all_label]+rank.restaurant_id.astype(str).tolist());r=rank if rid==all_label else rank[rank.restaurant_id==int(rid)]
 revenue_chart(r,'restaurant_id');st.dataframe(view(r),hide_index=True)
 st.caption(t('Gráfico em R$, IDs no eixo horizontal. A participação se refere ao conjunto completo, antes do filtro.','Chart in BRL, restaurant IDs on the horizontal axis. Shares refer to the entire dataset before filtering.'))
with tabs[1]:revenue_chart(frames['04_monthly.sql'],'month',True);st.dataframe(view(frames['04_monthly.sql']),hide_index=True)
with tabs[2]:st.dataframe(view(frames['05_item_margin.sql']),hide_index=True);st.caption(t('Custos de ficha simulados; margem de contribuição não é lucro líquido.','Simulated recipe costs; contribution margin is not net profit.'))
with tabs[3]:
 r=frames['02_reconcile.sql'];st.success(t('Todos os pedidos reconciliados','All orders reconciled')) if (r.total_cents==r.line_total_cents).all() else st.error(t('Divergência','Mismatch'));st.dataframe(view(r),hide_index=True)
 st.download_button(t('Baixar conciliação','Download reconciliation'),r.to_csv(index=False).encode(),file_name='reconciliation.csv',mime='text/csv');st.caption(t('O CSV preserva os nomes técnicos e valores em centavos.','CSV retains technical field names and integer cents.'))
with tabs[4]:q=st.selectbox(t('Consulta','Query'),list(frames));st.code((SQL/q).read_text(),language='sql')
st.caption(t('Implementação original com assistência de IA. O painel não publica repositórios.','Original implementation with AI assistance. This app does not publish repositories.'))
