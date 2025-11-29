from sqlalchemy import create_engine, text
import pandas as pd

def min_to_string(minutes):
    h = int(abs(minutes) // 60)
    m = int(abs(minutes) % 60)
    sign = '-' if minutes < 0 else ''
    return f"{sign}{h}h {m}min" if h else f"{sign}{m}min"

class TrainsDB:
    
    def __init__(self, db_url):
        
        self.engine = create_engine(db_url)
    
    def update_filter(self, years, companies):
        
        self.years = list(map(int, years))
        self.companies = list(companies)
    
    def get_companies(self):
        query = text("SELECT DISTINCT company FROM trainsdb;")
        with self.engine.connect() as conn:
            result = conn.execute(query).fetchall()
        return sorted([row[0] for row in result if row[0] is not None])

    def get_years(self):
        query = text("SELECT DISTINCT EXTRACT(YEAR FROM departure) FROM trainsdb;")
        with self.engine.connect() as conn:
            result = conn.execute(query).fetchall()
        return sorted([int(row[0]) for row in result if row[0] is not None])
    
    def get_n_train(self):
        query = text("""
            SELECT COUNT(*) FROM trainsdb
            WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
              AND company = ANY(:companies)
        """)
        with self.engine.connect() as conn:
            return conn.execute(query, {"years": self.years, "companies": self.companies}).scalar()
    
    def get_sum(self, column):
        query = text(f"""
            SELECT SUM({column}) FROM trainsdb
            WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
              AND company = ANY(:companies)
        """)
        with self.engine.connect() as conn:
            return conn.execute(query, {"years": self.years, "companies": self.companies}).scalar()
    
    def get_max(self, column):

        query = text(f"""
            SELECT MAX({column}) FROM trainsdb
            WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
            AND company = ANY(:companies)
        """)
        with self.engine.connect() as conn:
            return conn.execute(query, {"years": self.years, "companies": self.companies}).scalar()
        
    def get_avg(self, column):
        query = text(f"""
            SELECT AVG({column}) FROM trainsdb
            WHERE EXTRACT(YEAR FROM Departure) = ANY(:years)
              AND Company = ANY(:companies)
        """)
        with self.engine.connect() as conn:
            return conn.execute(query, {"years": self.years, "companies": self.companies}).scalar()

    def get_median(self, column):
        query = text(f"""
            SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {column})
            FROM trainsdb
            WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
              AND company = ANY(:companies)
        """)
        with self.engine.connect() as conn:
            return conn.execute(query, {"years": self.years, "companies": self.companies}).scalar()
    
    def get_n_station(self):
        query = text("""
            SELECT COUNT(DISTINCT loc) FROM (
                SELECT origin AS loc FROM trainsdb
                WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
                  AND company = ANY(:companies)
                UNION
                SELECT destination AS loc FROM trainsdb
                WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
                  AND company = ANY(:companies)
            ) AS combined
        """)
        with self.engine.connect() as conn:
            return conn.execute(query, {"years": self.years, "companies": self.companies}).scalar()
        
    def get_monthly_train_counts(self):
        query = text("""
            SELECT 
                EXTRACT(YEAR FROM departure) AS year,
                EXTRACT(MONTH FROM departure) AS month,
                COUNT(*) AS count
            FROM trainsdb
            WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
            AND company = ANY(:companies)
            GROUP BY year, month
            ORDER BY year, month
        """)
        with self.engine.connect() as conn:
            result = conn.execute(query, {"years": self.years, "companies": self.companies}).fetchall()
        
        year_month = [f"{int(row.month):02d}-{int(row.year)}" for row in result]
        counts = [row.count for row in result]
        return year_month, counts
    
    def get_stat_table(self):
        columns = {
            "Delay [min]": "delay",
            "Relative duration": "relduration",
            "Distance [km]": "distance",
            "Travel time": "traveltime",
            "Speed [km/h]": "speed"
        }

        rows = []

        for label, col in columns.items():
            query = text(f"""
                SELECT 
                    MIN({col}) AS min,
                    MAX({col}) AS max,
                    AVG({col}) AS mean,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {col}) AS median
                FROM trainsdb
                WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
                AND company = ANY(:companies)
            """)
            with self.engine.connect() as conn:
                result = conn.execute(query, {"years": self.years, "companies": self.companies}).mappings().first()

            # Format values
            min_val = result["min"] if result["min"] is not None else "No data"
            max_val = result["max"] if result["max"] is not None else "No data"
            mean_val = round(result["mean"], 2) if result["mean"] is not None else "No data"
            median_val = round(result["median"], 2) if (result["median"] is not None) else "No data"

            if col == "relduration" and result["min"] is not None:
                min_val = f"{min_val}%"
                max_val = f"{max_val}%"
                mean_val = f"{mean_val}%"
                median_val = f"{median_val}%"
            elif (col == "traveltime" or col=="delay") and result["min"] is not None:
                min_val = min_to_string(min_val)
                max_val = min_to_string(max_val)
                mean_val = min_to_string(mean_val)
                median_val = min_to_string(median_val)

            rows.append([label, max_val, min_val, mean_val, median_val])

        return pd.DataFrame(rows, columns=[" ", "Max", "Min", "Mean", "Median"])
    
    def get_delay_categories(self):
        query = text("""
            SELECT category, COUNT(*) AS count FROM (
                SELECT CASE
                    WHEN delay < -1 THEN 'Early'
                    WHEN delay >= -1 AND delay < 1 THEN 'On time'
                    WHEN delay >= 1 AND delay < 5 THEN 'Low delay (<5 min)'
                    WHEN delay >= 5 AND delay < 10 THEN 'Delay (between 5 and 10)'
                    WHEN delay >= 10 AND delay < 30 THEN 'Big delay (between 10 and 30)'
                    WHEN delay >= 30 THEN 'Very big delay (>30 min)'
                END AS category
                FROM trainsdb
                WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
                AND company = ANY(:companies)
            ) AS categorized
            GROUP BY category
        """)
        with self.engine.connect() as conn:
            result = conn.execute(query, {"years": self.years, "companies": self.companies}).fetchall()

        # Reindex to ensure all categories are present
        labels = ['Early', 'On time', 'Low delay (<5 min)', 
                'Delay (between 5 and 10)', 'Big delay (between 10 and 30)', 'Very big delay (>30 min)']
        counts = {label: 0 for label in labels}
        for row in result:
            counts[row.category] = row.count

        return labels, [counts[label] for label in labels]
    
    def get_delay_evolution(self):
        query = text("""
            SELECT 
                EXTRACT(YEAR FROM departure) AS year,
                EXTRACT(MONTH FROM departure) AS month,
                CASE
                    WHEN delay < -1 THEN 'Early'
                    WHEN delay >= -1 AND delay < 1 THEN 'On time'
                    WHEN delay >= 1 AND delay < 5 THEN 'Low delay (<5 min)'
                    WHEN delay >= 5 AND delay < 10 THEN 'Delay (between 5 and 10)'
                    WHEN delay >= 10 AND delay < 30 THEN 'Big delay (between 10 and 30)'
                    WHEN delay >= 30 THEN 'Very big delay (>30 min)'
                END AS category,
                COUNT(*) AS count
            FROM trainsdb
            WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
            AND company = ANY(:companies)
            GROUP BY year, month, category
            ORDER BY year, month
        """)
        with self.engine.connect() as conn:
            result = conn.execute(query, {"years": self.years, "companies": self.companies}).fetchall()

        # Format en DataFrame
        df = pd.DataFrame(result, columns=["year", "month", "category", "count"])
        pivot = df.pivot_table(index=["month", "year"], columns="category", values="count", fill_value=0)
        pivot_percent = pivot.div(pivot.sum(axis=1), axis=0) * 100

        # Tri chronologique
        print(pivot_percent)
        pivot_percent = pivot_percent.sort_index(key=lambda x: [(y, m) for m, y in x])

        return pivot_percent
    
    def get_unic_station(self):
        query = text("""
            SELECT DISTINCT loc FROM (
                SELECT origin AS loc
                FROM trainsdb
                WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
                AND company = ANY(:companies)
                UNION
                SELECT destination AS loc
                FROM trainsdb
                WHERE EXTRACT(YEAR FROM departure) = ANY(:years)
                AND company = ANY(:companies)
            ) AS combined
            ORDER BY loc;
        """)
        with self.engine.connect() as conn:
            result = conn.execute(query, {"years": self.years, "companies": self.companies}).fetchall()
        return [row[0] for row in result if row[0] is not None]
