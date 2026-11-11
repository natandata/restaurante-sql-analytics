# SQL para decisões de restaurante

Estudo independente de dados relacionais para cinco restaurantes fictícios. Implementação original com assistência de IA. Não é trabalho para cliente real nem reprodução literal do Zomato.

**Estado:** implementado, executado localmente e publicado em repositório público após revisão de nomes e conteúdo em 11/11/2026. Não foi adicionada licença de reutilização ao código próprio. A fonte Inter mantém SIL OFL em `assets/`.

## O que faz

- Cinco tabelas com PK/FK/CHECK e moeda em centavos: restaurantes, produtos, cardápio, pedidos e itens.
- Gerador reproduzível de 500 pedidos com seed 20261111, sem pessoas ou senhas.
- Carga CSV transacional, auditoria de duplicata exata e rollback de lote inválido.
- Cinco consultas: conciliação, ranking/participação, mês/LAG, contribuição e ticket.
- Relatório offline, notebook executado e painel local Streamlit PT/EN.
- Integração PostgreSQL 16.2 temporária realmente executada; mesmas cinco consultas e restrições verificadas.

## Resultado de referência

500 pedidos, receita de **R$ 44.592,00**. O JOIN errado somaria R$ 102.775,00, um excesso artificial de R$ 58.183,00. A receita correta foi conciliada com as linhas. São números sintéticos, sem resultado comercial real.

20 testes de domínio/carga passam em Python 3.10.12 e 3.12.15. Teste de interface separado: carregamento, EN, 700 pedidos e filtro. Layout inspecionado em 320/390/1280 px. PostgreSQL verificado em Linux; não instalado/testado no Dell. GitHub Actions concluído com sucesso em Python 3.10 e 3.12; execução identificada em `docs/CI.md`.

## Rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.pipeline
```

No PowerShell, use `.venv\Scripts\python.exe` no lugar de `python` se não ativar o ambiente; não mude política global do Windows. Windows nativo ainda não foi testado.

```bash
# Interface local, sem conta ou cobrança
python -m pip install -r requirements-app.txt
python -m streamlit run app.py
# Verificações de interface
python -m unittest discover -s tests_ui -v
# PostgreSQL temporário, sem conexão a banco pessoal
python -m pip install -r requirements-postgres.txt
python -m src.verify_postgres
# Reexecutar notebook
python -m pip install -r requirements-notebook.txt
python scripts/execute_notebook.py
```

Os requisitos principais não incluem Streamlit, Jupyter ou PostgreSQL. Instale as camadas opcionais só para o uso correspondente. O app usa localhost e estatísticas de uso desativadas. Não exponha a porta na internet sem revisão de segurança.

## Onde ler

- [Explicação completa por módulo](docs/EXPLICACAO_COMPLETA.md)
- [Limites e estado verificado](docs/STATUS.md)
- [Notebook executado](notebooks/01_implementacao_explicada.ipynb)
- [Modelo relacional](docs/modelo.mmd)
- [Créditos e direitos](THIRD_PARTY_NOTICES.md)
- `sql/`: esquema e cinco consultas.
- `src/`: pipeline, importador, verificação PostgreSQL e saídas.
- `reports/`: CSVs, métricas, figura, HTML e evidências dos testes.

O arquivo SQLite gerado é ignorado pelo Git, mas pode ser reconstruído. Não distribua um banco real. O custo de ficha é fixo e simulado; contribuição não é lucro. O importador não é UPSERT e rejeita nova carga sobre chaves já presentes. Cancelamentos, estornos, descontos e mudanças históricas de custo estão fora do modelo.

## Inspiração

https://github.com/ShaikhBorhanUddin/Zomato-Data-Analysis . Nenhum código, CSV ou tabela de usuários da referência foi copiado. A MIT da referência não foi aplicada automaticamente a esta implementação. Dependências mantêm suas próprias licenças. O manual privado de marca não integra o pacote.

---

# SQL for restaurant decisions

Independent relational-data study for five fictional restaurants. Original implementation with AI assistance. This is not client work or a literal Zomato reproduction.

**Status:** implemented, executed locally and published in a public repository after name and content review on 11 November 2026. No reuse license is added for original code. The bundled Inter font retains SIL OFL in `assets/`.

## What it does

- Five PK/FK/CHECK-constrained tables with integer cents: restaurants, products, menu, orders and order lines.
- Reproducible500-order generator, seed 20261111, with no people or passwords.
- Transactional CSV import, exact-duplicate audit and whole-batch rollback on invalid data.
- Five queries: reconciliation, ranking/shares, month/LAG, contribution and average order value.
- Offline report, executed notebook and local PT/EN Streamlit app.
- Temporary PostgreSQL 16.2 integration actually executed, with all five queries and constraints checked.

## Reference result

500 orders and **BRL 44,592.00** revenue. The incorrect JOIN would total BRL 102,775.00, an artificial BRL 58,183.00 excess. Correct revenue reconciles against line totals. All figures are synthetic, not real business outcomes.

20 domain/import tests pass on Python 3.10.12 and 3.12.15. Separate UI test covers initial load, EN,700 orders and restaurant filtering. Layout inspected at 320/390/1280 px. PostgreSQL verified on Linux, not installed or tested on the owner's Dell. GitHub Actions completed successfully on Python 3.10 and 3.12; see `docs/CI.md` for the exact run.

## Run

Use the same commands above from the repository root. The first block creates a virtual environment, installs minimal dependencies, runs tests and regenerates reports. On PowerShell, use `.venv\Scripts\python.exe` if activation is unavailable; do not change global execution policy. Native Windows is not yet tested.

The optional blocks install the local app, UI tests, temporary PostgreSQL integration and notebook execution. Minimal requirements do not include Streamlit, Jupyter or PostgreSQL. Install only the layer you need. The app binds to localhost with usage statistics disabled. Do not expose its port publicly without a security review.

## Read and inspect

The complete module explanation is in `docs/EXPLICACAO_COMPLETA.md`; verified status in `docs/STATUS.md`; executed notebook in `notebooks/`; diagram in `docs/modelo.mmd`; rights in `THIRD_PARTY_NOTICES.md`. English documentation is `docs/EXPLANATION.md`. `sql/` holds schema and queries, `src/` holds implementation, and `reports/` holds results and test evidence.

The generated SQLite file is Git-ignored and can be rebuilt. Do not distribute a real operational database. Recipe costs are static and simulated; contribution is not profit. The importer is not an UPSERT and rejects existing keys. Cancellations, refunds, discounts and historical cost changes are outside this model.

## Inspiration

https://github.com/ShaikhBorhanUddin/Zomato-Data-Analysis . No reference code, CSVs or user table were copied. Its MIT license was not automatically applied to this independent implementation. Dependencies retain their own licenses. The private brand manual is not bundled.
