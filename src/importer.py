"""Carga CSV transacional com limpeza explícita, sem mutação fora do banco."""
from pathlib import Path
import csv
from datetime import date
TABLES={
 'restaurants':('restaurant_id','name'),
 'products':('product_id','name'),
 'menu':('restaurant_id','product_id','price_cents','cost_cents'),
 'orders':('order_id','restaurant_id','ordered_at','total_cents'),
 'order_lines':('order_id','product_id','restaurant_id','quantity','unit_cents'),
}
TEXT={'name','ordered_at'}
def parse_integer(s):
    s=str(s).strip()
    if not s or any(c not in '0123456789-' for c in s):raise ValueError('Inteiro invalido')
    return int(s)
def import_csv(con,directory):
    """Remove só duplicatas exatas e espaço em texto. Erro invalida lote todo.
    Arquivos: <table>.csv ou input_<table>.csv, sem substituir tabelas existentes.
    Auditoria retornada apenas para carga bem-sucedida. Não escolhe 'a última'
    versão de uma chave conflitante nem inventa moeda ausente.
    """
    directory=Path(directory);audit=[]
    try:
        con.execute('BEGIN')
        for table,cols in TABLES.items():
            f=directory/(table+'.csv')
            if not f.exists():f=directory/('input_'+table+'.csv')
            with f.open(newline='',encoding='utf-8') as stream:
                reader=csv.DictReader(stream)
                if set(reader.fieldnames or [])!=set(cols):raise ValueError('Cabecalho invalido: '+table)
                seen=set()
                for line,row in enumerate(reader,2):
                    values=tuple(row[c].strip() if c in TEXT else parse_integer(row[c]) for c in cols)
                    if values in seen:
                        audit.append(dict(table=table,line=line,reason='duplicate_exact_removed'));continue
                    seen.add(values)
                    if 'name' in cols and not values[cols.index('name')]:raise ValueError('Nome vazio')
                    if 'ordered_at' in cols:
                        s=values[cols.index('ordered_at')]
                        if date.fromisoformat(s).isoformat()!=s:raise ValueError('Data nao canonica')
                    con.execute('INSERT INTO '+table+' VALUES('+','.join('?' for _ in cols)+')',values)
        if con.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Chave estrangeira invalida')
        bad=con.execute('SELECT COUNT(*) FROM orders o LEFT JOIN order_totals t USING(order_id) WHERE o.total_cents != COALESCE(t.line_total_cents,0)').fetchone()[0]
        if bad:raise ValueError('Pedidos nao reconciliados: '+str(bad))
        con.commit();return audit
    except Exception:
        con.rollback();raise
