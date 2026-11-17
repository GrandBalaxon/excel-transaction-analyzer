WITH RankedTransactions AS (
    SELECT
        c.name AS category_name,
        f.description,
        f.amount,
        ROW_NUMBER() OVER(PARTITION BY c.name ORDER BY f.amount ASC) AS rn
    FROM fact_transactions f
    JOIN dim_categories c ON f.category_id = c.category_id
    WHERE f.amount < 0
)
SELECT category_name, description, ABS(amount) AS amount
FROM RankedTransactions
WHERE rn <= 3
ORDER BY category_name, amount ASC;
