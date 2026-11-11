-- Custo de ficha é sintético e constante, não custo contábil real.
SELECT l.product_id,p.name,SUM(l.quantity) AS units,SUM(l.quantity*l.unit_cents) AS revenue_cents,
SUM(l.quantity*(l.unit_cents-m.cost_cents)) AS contribution_cents
FROM order_lines l JOIN products p USING(product_id)
JOIN menu m ON m.restaurant_id=l.restaurant_id AND m.product_id=l.product_id
GROUP BY l.product_id,p.name ORDER BY contribution_cents DESC,l.product_id;
