-- Agrega pedidos antes de calcular participação. Desempate explícito.
WITH revenue AS (SELECT restaurant_id,COUNT(*) AS orders,SUM(total_cents) AS revenue_cents FROM orders GROUP BY restaurant_id)
SELECT *,ROUND(100.0*revenue_cents/SUM(revenue_cents) OVER(),3) AS share_pct,
DENSE_RANK() OVER(ORDER BY revenue_cents DESC) AS revenue_rank
FROM revenue ORDER BY revenue_cents DESC,restaurant_id LIMIT 5;
