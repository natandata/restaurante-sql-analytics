-- Granularidade: uma linha por pedido, inclusive pedido sem itens (zero).
SELECT o.order_id,o.total_cents,COALESCE(t.line_total_cents,0) AS line_total_cents
FROM orders o LEFT JOIN order_totals t USING(order_id) ORDER BY o.order_id;
