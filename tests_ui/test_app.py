from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest
class AppTests(unittest.TestCase):
 def test_load_language_and_scenario(self):
  at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
  self.assertEqual(len(at.exception),0)
  self.assertEqual(at.metric[0].label,'Receita');self.assertEqual(at.metric[0].value,'R$ 44.592,00')
  at.radio[0].set_value("EN").run();self.assertEqual(len(at.exception),0)
  self.assertEqual(at.metric[0].label,'Revenue');self.assertEqual(at.metric[0].value,'R$ 44,592.00')
  at.slider[0].set_value(700).run();self.assertEqual(at.metric[1].value,'700');at.selectbox[0].set_value('1').run();self.assertEqual(len(at.exception),0)
if __name__=="__main__":unittest.main()
