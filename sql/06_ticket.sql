SELECT restaurant_id,COUNT(*) AS orders,ROUND(AVG(total_cents),2) AS ticket_cents,
MIN(total_cents) AS min_ticket_cents,MAX(total_cents) AS max_ticket_cents
FROM orders GROUP BY restaurant_id ORDER BY restaurant_id;
