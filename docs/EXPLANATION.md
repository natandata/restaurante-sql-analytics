# SQL for restaurant decisions

Implementation and study document, published version dated 11 November 2026. Project 2 of the guide. Independent code with AI assistance, not copied Zomato code, real client work or a claim that Natan implemented everything without assistance. All tables, names, prices and orders are fictional.

## 1. Decision and evidence

The business questions are which restaurants sell more, how monthly revenue changes, average order value and product contribution. Before plotting, the implementation asks whether revenue stays unchanged after joining tables. This invariant is the center of the project.

The default run uses seed 20261111, five restaurants, four products and 500 orders. Reconciled revenue is 4,459,200 cents, or BRL 44,592.00. A naive order-to-line JOIN totals 10,277,500 cents, an artificial BRL 58,183.00 excess. Each order total was repeated for its lines. This measures a calculation error in a synthetic example, not money lost by a company.

20 automated domain/import tests ran on Python 3.10.12 and 3.12.15. Actual integration with temporary PostgreSQL 16.2 confirmed the five queries and PK/FK/CHECK constraints. SQLite is the lightweight local path; PostgreSQL is tested compatibility, not a service installed on the owner's computer.

## 2. Implementation map

`src.pipeline.run()` creates an in-memory database, applies `sql/01_schema.sql`, generates data, runs queries, requires reconciliation and writes artifacts. `app.py` reuses creation, loading and query functions but does not overwrite versioned reports when controls change.

`src/importer.py` accepts five schema-defined CSVs, loads transactionally, audits removal of exact duplicates and rejects conflicts. `src/verify_postgres.py` starts a private temporary PostgreSQL instance for verification, loads the same rows, compares results and stops the instance. It does not discover personal databases or change an existing account.

`src/common.py` writes JSON without NaN, CSVs, figures and standalone HTML. Inter is bundled with SIL OFL, not the private brand manual. `notebooks/` explains the implementation through executed cells. `tests/` is an executable specification, not merely a picture of successful output.

## 3. Grain before SQL

Each `restaurants` row is one fictional restaurant, identified by its primary key rather than its display name. Each `products` row is a catalog product. Product names are unique in this small model; restaurant names are not used for joins.

Each `menu` row is a restaurant/product offering with price and recipe cost in cents. Its composite key permits different prices for the same product at different locations. Each `orders` row is a whole order with date, restaurant and total. That total is no longer safely additive after expansion to line grain.

Each `order_lines` row is one product within one order. Its order/product key combines repeated quantities into one line. A real operation that permits modifiers or different prices for the same product would need a line identifier instead. This modeling choice must not be reused without checking that assumption.

There are five tables and no user, email, password, customer name, courier or address fields. These data are unnecessary for the chosen questions. Their absence is deliberate minimization, not anonymization of a private dataset.

## 4. Constraints as a contract

Primary keys prevent conflicting identities. The order-to-restaurant FK prevents orders for nonexistent stores. A composite line-to-order FK verifies both order and restaurant. Another composite FK verifies that the product is offered in that restaurant's menu. Checking the product alone would not establish that it belongs to the correct store.

CHECK constraints require positive quantity and line price, nonnegative recipe cost and nonnegative order total. Equality between an order and its line sum is a cross-table rule. It is checked by reconciliation and before CSV import commits, not misrepresented as a single-column CHECK.

SQLite needs `PRAGMA foreign_keys=ON` on every connection; `create_connection()` sets it and tests provoke a failure when a referenced restaurant does not exist. PostgreSQL applies its declared FKs without that SQLite-specific setting.

Amounts are integer cents so quantity-times-price is exact. Average order value can be fractional because it is a division. Display rounding does not change source totals.1999 means BRL 19.99, not BRL 1,999; storing each price as floating point would add unnecessary binary rounding risk.

## 5. Generation and loading

`load()` uses a local `numpy.random.default_rng(seed)`, creates dimensions and menu before facts, then creates orders and lines. Products are selected without replacement within an order, matching the composite line key. Quantities range from 1 to 3 and totals are derived from lines, not independently sampled.

Dates cover six months of 2025. They are historical simulation dates, not current November 2026 sales. Sampling exercises aggregations; it was not fitted to a population and cannot establish real average tickets, seasonality or product mix.

The importer accepts `restaurants.csv`, `products.csv`, `menu.csv`, `orders.csv`, `order_lines.csv`, or the generated `input_...` names. It requires exact column sets, integer values and canonical ISO dates, trims text whitespace and rejects invalid headers, numbers, dates, references, keys or totals. It does not guess what an ambiguous 01/02/25 means.

Exact duplicate CSV rows are removed and audited. Rows sharing a key but disagreeing elsewhere fail the batch. There is no hidden last-write-wins rule. An actual update policy would need a separate contract and tests.

The transaction starts before the first table. If final reconciliation fails, rollback removes dimension rows as well as facts inserted earlier. Existing tables are not replaced. This is not an idempotent UPSERT: loading the same keys into a populated database fails. Reprocessing behavior must be designed before connecting a real source.

```python
from src.pipeline import create_connection
from src.importer import import_csv
con = create_connection()
audit = import_csv(con, 'reports')
print(audit)
con.close()
```

This example imports only generated synthetic CSVs. A filesystem path does not authorize publication of real customer exports. Rights, privacy and secrets must be reviewed before substituting real data.

## 6. Reconciliation

`order_totals` groups lines by order and sums quantity times unit cents. `02_reconcile.sql` LEFT JOINs whole orders with that already aggregated view, aligning one-order grain on both sides.

LEFT JOIN exposes an order without lines instead of hiding it as INNER JOIN would. COALESCE treats its missing line sum as zero for comparison. A zero-total order without lines can therefore pass numerical reconciliation; if business rules forbid it, add a minimum-line-count check. The generator always creates at least one line.

Manual case: two dishes at 1000 cents yield 2000 cents revenue. At 300 cents recipe cost per dish, contribution is 1400 cents. Test 19 checks revenue, contribution and ticket for this small independent case rather than deriving expected values from the same 500-order generator.

## 7. Ranking and shares

`03_restaurants.sql` first aggregates orders by restaurant in a CTE, a named query stage. `SUM(revenue_cents) OVER()` then supplies the all-store denominator without reducing those restaurant rows. GROUP BY changes grain; a window calculation preserves the grouped rows.

`DENSE_RANK()` gives equal revenues equal ranks. Explicit revenue-descending, restaurant-ID ordering precedes LIMIT 5, giving stable display tie-breaking. LIMIT does not imply any ordering on its own.

Restaurant 1 has BRL 10,246.00 from 120 orders; restaurant 5 has BRL 9,338.00 from 91. This does not establish better efficiency: the generator assigned more orders to store 1. Real comparisons would need capacity, hours, location, costs and history. The query answers which total is larger, not why.

## 8. Months and average order value

`04_monthly.sql` extracts the month from ISO dates, aggregates orders and revenue, and uses LAG for the previous month. The first difference is null because no prior month exists in the slice. Null is not zero. The report shows not applicable rather than inventing a prior zero-revenue month.

The date index prepares period filtering, but no performance benchmark is claimed for this small workload. EXPLAIN and larger datasets would be necessary to demonstrate impact. Indexes also cost writes and storage.

`06_ticket.sql` calculates average, minimum and maximum from whole orders. Averaging item prices would answer a different question. Cancellations, refunds, taxes and discounts require explicit eligibility and gross/net definitions before these queries could be reused operationally.

## 9. Contribution is not profit

`05_item_margin.sql` joins both parts of the menu key and computes product revenue and contribution. Salad leads synthetic contribution at 845,840 cents; this is not an actionable menu recommendation for a real business.

Recipe cost is static. Historical cost changes would require the cost effective at sale time, perhaps stored on the line or resolved through a historical dimension. Repricing old sales with current costs would rewrite past margins. Rent, labor, tax, commission and waste are absent, so the result is contribution, not net profit.

## 10. SQLite and PostgreSQL

SQLite requires no account, daemon or open network port for the main path. `reports/analytics.sqlite` is a local result copy, not a production database. It is Git-ignored; source code and CSVs rebuild it.

The same schema and five queries ran on PostgreSQL 16.2. The verifier loads the same rows, compares values and order, and provokes expected FK/PK/CHECK errors. Decimal-versus-float differences are handled only for numeric comparison at reported precision; integer totals are not rounded to hide disagreement.

The optional `pgserver` distribution starts and stops its temporary server in a finally block. Its binaries are not bundled in the repository. Version 16.2 is old for a new deployment: this is SQL compatibility evidence, not a recommendation to expose this test server. Production needs a maintained version, authentication/TLS, backups, migrations and permissions. None are implied by this study.

## 11. Reports, app and notebook

Offline HTML preserves the reference result. Streamlit allows seed, order count, PT/EN and restaurant selection. Other tabs show months, margin, reconciliation and the actual SQL. There is no arbitrary-SQL input, GitHub publication or external data API.

The HTML is frozen output; the app is exploration. A filtered restaurant still displays its share of the original universe because the share was calculated before the UI filter. Graph revenue is BRL, while CSVs keep integer cents.

Run notebook cells in order in a fresh session. They call `src` functions to avoid maintaining two different implementations. Distributed outputs were actually executed; the notebook is not the only source of business logic.

## 12. Tests and limits of evidence

The 20 tests cover deterministic generation, referential integrity, per-order and joined reconciliation, share totals, months, PK/FK/CHECK rejection, composite FK, margins, incorrect JOIN, ranking, CSV roundtrip, duplicate audit, rollback, noninteger rejection, empty queries, the manual example and conflicting import. PostgreSQL verification is additional evidence, not another claimed 20 tests.

UI checks covered initial load, English,700 orders and restaurant filtering. Layout was inspected at 320/390/1280 pixels. This is not universal browser coverage, an accessibility audit or a Windows deployment. This project was not installed on the Dell.

## 13. Reproduction

Use Python 3.10 or 3.12 in a dedicated folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.pipeline
```

PowerShell activation uses `.venv\Scripts\Activate.ps1`. If execution policy blocks it, call `.venv\Scripts\python.exe` directly instead of changing global policy. Native Windows is not tested.

Install `requirements-app.txt` for `python -m streamlit run app.py`; the app binds to localhost with usage statistics disabled. Install `requirements-notebook.txt` for notebook execution. Install `requirements-postgres.txt` for `python -m src.verify_postgres`, tested on Linux rather than the Dell. The published workflow runs these checks remotely. See `CI.md` for its verified result.

## 14. Modifying safely

New products need dimension and menu rows plus FK checks. Modifiers require a line identifier and tests with the same product at different prices. Discounts need a declared order-level or line-level grain; never subtract a whole-order discount once per line.

Incremental persistence needs batch IDs, idempotency keys and correction policy. The current importer rejects existing keys. Real sources would also need separate receipt, validation, staging and publication with counts and hashes per batch.

For an FDE interview, explain the invariant first: revenue must reconcile before and after joins. Show the counterexample, pre-aggregation fix, manual case and rollback. That demonstrates translating business intent into contracts and tests. Do not describe synthetic study as client deployment experience.

## 15. Rights and publication

The thematic reference is https://github.com/ShaikhBorhanUddin/Zomato-Data-Analysis . No code, CSV, password or user table was copied. The reference MIT license was not automatically assigned to independent code. No original-code reuse license has been added.

Public repository `natandata/restaurante-sql-analytics`, published after name and content approval on 11 November 2026. No original-code reuse license has been added.

Technical sources: https://docs.python.org/3/library/sqlite3.html ; https://www.postgresql.org/docs/16/ ; https://www.sqlite.org/foreignkeys.html . Metrics come from this implementation, not the reference.
