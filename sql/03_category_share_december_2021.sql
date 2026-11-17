WITH MonthlyExpenses AS (
    SELECT
        c.name AS category_name,
        SUM(ABS(f.amount)) AS category_total
    FROM fact_transactions f
    JOIN dim_categories c ON f.category_id = c.category_id
    JOIN dim_dates d ON f.date_id = d.date_id
    WHERE d.year = 2021 AND d.month = 12 AND f.amount > 0
    GROUP BY c.name
),
TotalExpense AS (
    SELECT SUM(category_total) as total FROM MonthlyExpenses
)
SELECT
    m.category_name,
    m.category_total,
    ROUND(((m.category_total / t.total) * 100)::numeric, 2) AS percentage
FROM MonthlyExpenses m
CROSS JOIN TotalExpense t
ORDER BY m.category_total DESC;
