WITH monthly AS (SELECT SUBSTR(ordered_at,1,7) AS month,SUM(total_cents) AS revenue_cents,COUNT(*) AS orders FROM orders GROUP BY SUBSTR(ordered_at,1,7))
SELECT *,revenue_cents-LAG(revenue_cents) OVER(ORDER BY month) AS change_cents FROM monthly ORDER BY month;
