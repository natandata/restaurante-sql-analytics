"""Modelo relacional independente. SQLite local, valores em centavos."""
import sqlite3
from datetime import date,timedelta
import numpy as np
import pandas as pd
from .common import *
SQL=BASE/'sql'
def create_connection():
    con=sqlite3.connect(':memory:');con.execute('PRAGMA foreign_keys=ON');con.executescript((SQL/'01_schema.sql').read_text());return con
def load(con,seed=SEED,n=500):
    rng=np.random.default_rng(seed)
    con.executemany('INSERT INTO restaurants VALUES(?,?)',[(i,'Restaurante ficticio '+str(i)) for i in range(1,6)])
    con.executemany('INSERT INTO products VALUES(?,?)',[(i,s) for i,s in enumerate(['Prato','Bebida','Sobremesa','Salada'],1)])
    con.executemany('INSERT INTO menu VALUES(?,?,?,?)',[(r,p,1500+200*p+100*r,500+70*p) for r in range(1,6) for p in range(1,5)])
    for i in range(1,n+1):
        r=int(rng.integers(1,6));day=date(2025,1,1)+timedelta(days=int(rng.integers(0,180)))
        items=rng.choice([1,2,3,4],int(rng.integers(1,4)),replace=False)
        lines=[(i,int(p),r,int(rng.integers(1,4)),1500+200*int(p)+100*r) for p in items]
        total=sum(row[3]*row[4] for row in lines)
        con.execute('INSERT INTO orders VALUES(?,?,?,?)',(i,r,day.isoformat(),total))
        con.executemany('INSERT INTO order_lines VALUES(?,?,?,?,?)',lines)
    con.commit()
def query(con,name):return pd.read_sql_query((SQL/name).read_text(),con)
def run():
    con=create_connection();load(con)
    tables={}
    for name in ['02_reconcile.sql','03_restaurants.sql','04_monthly.sql','05_item_margin.sql','06_ticket.sql']:
        tables[name]=query(con,name);save_csv(name.replace('.sql','.csv'),tables[name])
    rec=tables['02_reconcile.sql'];assert (rec.total_cents==rec.line_total_cents).all()
    true_total=con.execute('SELECT SUM(total_cents) FROM orders').fetchone()[0]
    wrong_total=con.execute('SELECT SUM(o.total_cents) FROM orders o JOIN order_lines l USING(order_id)').fetchone()[0]
    stats=dict(environment=environment(),orders=len(rec),revenue_cents=true_total,reconciled=True,foreign_key_errors=con.execute('PRAGMA foreign_key_check').fetchall(),naive_join_total_cents=wrong_total,join_overcount_cents=wrong_total-true_total)
    save_json('metrics.json',stats)
    for table in ['restaurants','products','menu','orders','order_lines']:save_csv('input_'+table+'.csv',pd.read_sql_query('SELECT * FROM '+table,con))
    backup=sqlite3.connect(outdir()/'analytics.sqlite');con.backup(backup);backup.close();con.close()
    plt=setup_plot();fig,ax=plt.subplots(figsize=(8,4));t=tables['03_restaurants.sql'];ax.bar(t.restaurant_id.astype(str),t.revenue_cents/100);ax.set(xlabel='ID fictício',ylabel='R$ sintéticos',title='Receita reconciliada por restaurante');fig.tight_layout();fig.savefig(outdir()/'revenue.png');plt.close(fig)
    dashboard('SQL para decisões de restaurante','Cinco consultas conciliam o caixa e mostram por que somar pedidos após um JOIN de itens duplica receita.',{'Pedidos':stats['orders'],'Receita R$':f"{true_total/100:.2f}",'Excesso do JOIN errado R$':f"{stats['join_overcount_cents']/100:.2f}",'Erros FK':len(stats['foreign_key_errors'])},{'Ranking de restaurantes':t,'Vendas por mês':tables['04_monthly.sql'],'Margem simulada':tables['05_item_margin.sql'],'Ticket':tables['06_ticket.sql']},[('revenue.png','Comparação de cinco restaurantes fictícios')]);print(stats);return stats
if __name__=='__main__':run()
