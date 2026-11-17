WITH DailyExpenses AS (
    SELECT
        d.date_id,
        SUM(ABS(f.amount)) AS daily_amount
    FROM fact_transactions f
    JOIN dim_dates d ON f.date_id = d.date_id
    WHERE f.amount > 0
    GROUP BY d.date_id
)
SELECT
    date_id,
    daily_amount,
    SUM(daily_amount) OVER (
        ORDER BY date_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM DailyExpenses
ORDER BY date_id;
