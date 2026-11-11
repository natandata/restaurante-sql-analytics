import unittest,sqlite3,tempfile,csv
from pathlib import Path
import pandas as pd
from src.pipeline import create_connection,load,query
from src.importer import import_csv,parse_integer,TABLES
class SQLTests(unittest.TestCase):
 def setUp(self):self.c=create_connection();load(self.c)
 def tearDown(self):self.c.close()
 def test_01_deterministic(self):
  other=create_connection();load(other)
  self.assertEqual(self.c.execute('SELECT * FROM orders').fetchall(),other.execute('SELECT * FROM orders').fetchall());other.close()
 def test_02_fk_clean(self):self.assertEqual(self.c.execute('PRAGMA foreign_key_check').fetchall(),[])
 def test_03_reconciliation(self):
  r=query(self.c,'02_reconcile.sql');self.assertTrue((r.total_cents==r.line_total_cents).all());self.assertEqual(len(r),500)
 def test_04_joins_preserve_revenue(self):
  total=self.c.execute('SELECT SUM(total_cents) FROM orders').fetchone()[0]
  self.assertEqual(total,int(query(self.c,'03_restaurants.sql').revenue_cents.sum()));self.assertEqual(total,int(query(self.c,'05_item_margin.sql').revenue_cents.sum()))
 def test_05_shares(self):self.assertAlmostEqual(query(self.c,'03_restaurants.sql').share_pct.sum(),100,places=2)
 def test_06_months(self):
  r=query(self.c,'04_monthly.sql');self.assertEqual(len(r),6);self.assertTrue(pd.isna(r.change_cents.iloc[0]));self.assertEqual(list(r.month),sorted(r.month))
 def test_07_foreign_key_enforced(self):
  with self.assertRaises(sqlite3.IntegrityError):self.c.execute("INSERT INTO orders VALUES(9999,99,'2025-01-01',200)")
 def test_08_pk_conflict(self):
  with self.assertRaises(sqlite3.IntegrityError):self.c.execute("INSERT INTO products VALUES(1,'Outro')")
 def test_09_quantity_check(self):
  r=self.c.execute('SELECT order_id,product_id,restaurant_id,unit_cents FROM order_lines LIMIT 1').fetchone()
  with self.assertRaises(sqlite3.IntegrityError):self.c.execute('UPDATE order_lines SET quantity=-1 WHERE order_id=? AND product_id=?',r[:2])
 def test_10_composite_fk(self):
  order,rest=self.c.execute('SELECT order_id,restaurant_id FROM orders LIMIT 1').fetchone()
  with self.assertRaises(sqlite3.IntegrityError):self.c.execute('INSERT INTO order_lines VALUES(?,?,?,?,?)',(order,4,rest%5+1,1,200))
 def test_11_cost_margin(self):
  r=query(self.c,'05_item_margin.sql');self.assertTrue((r.contribution_cents<=r.revenue_cents).all());self.assertTrue((r.contribution_cents>0).all())
 def test_12_wrong_join_is_wrong(self):
  self.assertGreater(self.c.execute('SELECT SUM(o.total_cents) FROM orders o JOIN order_lines l USING(order_id)').fetchone()[0],self.c.execute('SELECT SUM(total_cents) FROM orders').fetchone()[0])
 def test_13_explicit_ranking(self):
  r=query(self.c,'03_restaurants.sql');self.assertEqual(r.revenue_cents.tolist(),sorted(r.revenue_cents,reverse=True))
 def write_csv(self,d):
  for table in TABLES:
   frame=pd.read_sql_query('SELECT * FROM '+table,self.c);frame.to_csv(Path(d)/(table+'.csv'),index=False)
 def test_14_csv_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   self.write_csv(d);c=create_connection();self.assertEqual(import_csv(c,d),[]);self.assertEqual(c.execute('SELECT SUM(total_cents) FROM orders').fetchone(),self.c.execute('SELECT SUM(total_cents) FROM orders').fetchone());c.close()
 def test_15_duplicate_audited(self):
  with tempfile.TemporaryDirectory() as d:
   self.write_csv(d);f=Path(d)/'products.csv';rows=f.read_text().splitlines();f.write_text('\n'.join(rows+[rows[1]])+'\n');c=create_connection();a=import_csv(c,d);self.assertEqual(len(a),1);self.assertEqual(c.execute('SELECT COUNT(*) FROM products').fetchone()[0],4);c.close()
 def test_16_transaction_rollback(self):
  with tempfile.TemporaryDirectory() as d:
   self.write_csv(d);f=Path(d)/'orders.csv';r=pd.read_csv(f);r.loc[0,'total_cents']+=1;r.to_csv(f,index=False);c=create_connection()
   with self.assertRaises(ValueError):import_csv(c,d)
   self.assertEqual(c.execute('SELECT COUNT(*) FROM restaurants').fetchone()[0],0);c.close()
 def test_17_noninteger_rejected(self):
  for s in ['1.5','nan','1e3','', 'R$ 10']:
   with self.assertRaises(ValueError):parse_integer(s)
 def test_18_empty_queries(self):
  c=create_connection()
  for f in ['02_reconcile.sql','03_restaurants.sql','04_monthly.sql','05_item_margin.sql','06_ticket.sql']:self.assertEqual(len(query(c,f)),0)
  c.close()
 def test_19_hand_calculated(self):
  c=create_connection();c.executescript("INSERT INTO restaurants VALUES(1,'Ficticio');INSERT INTO products VALUES(1,'Prato');INSERT INTO menu VALUES(1,1,1000,300);INSERT INTO orders VALUES(1,1,'2025-01-01',2000);INSERT INTO order_lines VALUES(1,1,1,2,1000);")
  m=query(c,'05_item_margin.sql').iloc[0];self.assertEqual(m.revenue_cents,2000);self.assertEqual(m.contribution_cents,1400);self.assertEqual(query(c,'06_ticket.sql').ticket_cents.iloc[0],2000);c.close()
 def test_20_import_conflict_fails(self):
  with tempfile.TemporaryDirectory() as d:
   self.write_csv(d);f=Path(d)/'products.csv';f.write_text(f.read_text()+'1,Nome divergente\n');c=create_connection()
   with self.assertRaises(sqlite3.IntegrityError):import_csv(c,d)
   self.assertEqual(c.execute('SELECT COUNT(*) FROM products').fetchone()[0],0);c.close()
if __name__=='__main__':unittest.main()
