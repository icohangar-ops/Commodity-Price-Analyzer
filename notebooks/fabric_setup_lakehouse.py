"""
Microsoft Fabric Notebook: Data Pipeline Setup

Run this notebook FIRST to set up the Lakehouse tables
before running the main analysis notebook.
"""

# =============================================================================
# CELL 1: Initialize Lakehouse Tables
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, BooleanType, TimestampType
)
from datetime import datetime

spark = SparkSession.builder.getOrCreate()
print("Spark session initialized.")

# =============================================================================
# CELL 2: Create CommodityPrices Table
# =============================================================================

price_schema = StructType([
    StructField("timestamp", StringType(), False),
    StructField("metal", StringType(), False),
    StructField("price", DoubleType(), False),
    StructField("unit", StringType(), True),
    StructField("source", StringType(), True),
    StructField("change_pct", DoubleType(), True),
])

# Seed with initial data
initial_prices = [
    (datetime.utcnow().isoformat(), "Nickel", 18500.0, "USD/mt", "AlphaVantage", 0.0),
    (datetime.utcnow().isoformat(), "Cobalt", 32000.0, "USD/mt", "AlphaVantage", 0.0),
    (datetime.utcnow().isoformat(), "Lithium", 25000.0, "USD/mt", "AlphaVantage", 0.0),
    (datetime.utcnow().isoformat(), "Copper", 8500.0, "USD/mt", "AlphaVantage", 0.0),
    (datetime.utcnow().isoformat(), "Manganese", 3200.0, "USD/mt", "AlphaVantage", 0.0),
]

df_prices = spark.createDataFrame(initial_prices, price_schema)
df_prices.write.format("delta").mode("overwrite").saveAsTable("CommodityPrices")
print("Table 'CommodityPrices' created and seeded.")

# =============================================================================
# CELL 3: Create ContractCalculations Table
# =============================================================================

calc_schema = StructType([
    StructField("timestamp", StringType(), False),
    StructField("contract_type", StringType(), False),
    StructField("values_json", StringType(), False),
])

# Seed with empty record
df_calc = spark.createDataFrame([], calc_schema)
df_calc.write.format("delta").mode("overwrite").saveAsTable("ContractCalculations")
print("Table 'ContractCalculations' created.")

# =============================================================================
# CELL 4: Create ContractAnalysis Table
# =============================================================================

analysis_schema = StructType([
    StructField("timestamp", StringType(), False),
    StructField("ni_price", DoubleType(), False),
    StructField("co_price", DoubleType(), False),
    StructField("li_price", DoubleType(), False),
    StructField("black_mass_value", DoubleType(), True),
    StructField("mhp_profit_share_triggered", BooleanType(), True),
    StructField("li_floor_active", BooleanType(), True),
    StructField("li_ceiling_active", BooleanType(), True),
    StructField("ai_analysis", StringType(), True),
])

df_analysis = spark.createDataFrame([], analysis_schema)
df_analysis.write.format("delta").mode("overwrite").saveAsTable("ContractAnalysis")
print("Table 'ContractAnalysis' created.")

# =============================================================================
# CELL 5: Create RegulatoryAlerts Table
# =============================================================================

reg_schema = StructType([
    StructField("timestamp", StringType(), False),
    StructField("regulation_id", StringType(), True),
    StructField("title", StringType(), True),
    StructField("agency", StringType(), True),
    StructField("relevance_score", DoubleType(), True),
    StructField("summary", StringType(), True),
])

df_reg = spark.createDataFrame([], reg_schema)
df_reg.write.format("delta").mode("overwrite").saveAsTable("RegulatoryAlerts")
print("Table 'RegulatoryAlerts' created.")

# =============================================================================
# CELL 6: Verify All Tables
# =============================================================================

tables = spark.catalog.listTables()
print("\nLakehouse Tables Created:")
print("-" * 40)
for table in tables:
    count = spark.table(table.name).count()
    print(f"  {table.name}: {count} records")

print("\nSetup complete! You can now run the main analysis notebook.")
