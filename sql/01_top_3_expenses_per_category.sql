WITH RankedTransactions AS (
    SELECT
        c.name AS category_name,
        f.description,
        f.amount_rub,
        ROW_NUMBER() OVER(PARTITION BY c.name ORDER BY f.amount_rub ASC) AS rn
    FROM fact_transactions f
    JOIN dim_categories c ON f.category_id = c.category_id
    WHERE f.amount_rub < 0
)
SELECT category_name, description, ABS(amount_rub) AS amount
FROM RankedTransactions
WHERE rn <= 3
ORDER BY category_name, amount DESC;
