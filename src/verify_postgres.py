"""Integração PostgreSQL em instância temporária privada. Não acessa contas.
Execute após pip install -r requirements-postgres.txt. Não instala servidor no SO.
"""
import tempfile
import json
from pathlib import Path
import pandas as pd
from .pipeline import create_connection,load,SQL,query
from .common import save_json
from .importer import TABLES

def verify():
    import pgserver,psycopg
    c=create_connection();load(c)
    with tempfile.TemporaryDirectory(prefix='sql-study-') as d:
        server=pgserver.get_server(Path(d)/'pgdata',cleanup_mode='stop')
        try:
            with psycopg.connect(server.get_uri()) as con:
                con.execute((SQL/'01_schema.sql').read_text())
                for table,cols in TABLES.items():
                    data=c.execute('SELECT * FROM '+table).fetchall()
                    with con.cursor() as cur:cur.executemany('INSERT INTO '+table+' VALUES('+','.join('%s' for _ in cols)+')',data)
                version=con.execute('SELECT version()').fetchone()[0]
                comparisons=[]
                for filename in ['02_reconcile.sql','03_restaurants.sql','04_monthly.sql','05_item_margin.sql','06_ticket.sql']:
                    cur=con.execute((SQL/filename).read_text());pg=pd.DataFrame(cur.fetchall(),columns=[x.name for x in cur.description]);local=query(c,filename)
                    # Numeric/Decimal versus float: compare numbers at displayed precision.
                    for col in local:
                        if pd.api.types.is_numeric_dtype(local[col]):
                            a=pd.to_numeric(pg[col],errors='coerce').astype(float);b=local[col].astype(float)
                            import numpy as np
                            if not np.allclose(a,b,equal_nan=True,atol=1e-8):raise AssertionError(filename+':'+col)
                        elif pg[col].tolist()!=local[col].tolist():raise AssertionError(filename+':'+col)
                    comparisons.append(dict(query=filename,rows=len(pg),matches_sqlite=True))
                # Testa restrições com SAVEPOINT, sem invalidar toda a transação.
                violations=[]
                for label,sql in [('fk',"INSERT INTO orders VALUES(9999,99,'2025-01-01',0)"),('pk',"INSERT INTO products VALUES(1,'Outro')"),('check',"UPDATE order_lines SET quantity=-1 WHERE order_id=1")]:
                    con.execute('SAVEPOINT constraint_test')
                    try:con.execute(sql)
                    except psycopg.IntegrityError:violations.append(label)
                    else:raise AssertionError('Restricao nao aplicada: '+label)
                    finally:con.execute('ROLLBACK TO SAVEPOINT constraint_test')
                result=dict(postgres_version=version,queries=comparisons,constraints_rejected=violations)
                save_json('postgres_verified.json',result);print(json.dumps(result,ensure_ascii=False,indent=2));return result
        finally:
            server.cleanup();c.close()
if __name__=='__main__':verify()
