"""
Microsoft Fabric Notebook: Commodity Price Ingestion & AI Analysis

This notebook is designed to run inside Microsoft Fabric.
It ingests commodity data, runs GLI business rules, and generates
AI-powered insights using Azure AI Foundry (Kimi K2.6).

Setup Instructions:
1. Create a Lakehouse in your Fabric workspace
2. Add your Azure AI key to Fabric Workspace Settings > Secrets
3. Run each cell in order
"""

# =============================================================================
# CELL 1: Configuration & Authentication
# =============================================================================

import os
import json
from datetime import datetime

# In Fabric, secrets are managed via Workspace Settings or Key Vault
# For notebook development, set them here:
AZURE_AI_ENDPOINT = "https://samd-5839-resource.services.ai.azure.com/openai/v1"
# AZURE_AI_KEY = mssparkutils.credentials.getSecret("fabric-keyvault", "azure-ai-key")
AZURE_AI_KEY = os.getenv("AZURE_AI_KEY", "YOUR_KEY_HERE")
AZURE_AI_DEPLOYMENT = "Kimi-K2.6"

print(f"Configuration loaded at {datetime.utcnow().isoformat()}")
print(f"AI Endpoint: {AZURE_AI_ENDPOINT}")
print(f"Deployment: {AZURE_AI_DEPLOYMENT}")

# =============================================================================
# CELL 2: AI Analyzer Class (Azure AI Foundry)
# =============================================================================

from openai import OpenAI

class FabricAIAnalyzer:
    """Azure AI Foundry analyzer optimized for Fabric notebooks."""

    def __init__(self):
        self.client = OpenAI(
            base_url=AZURE_AI_ENDPOINT,
            api_key=AZURE_AI_KEY
        )
        self.deployment = AZURE_AI_DEPLOYMENT

    def analyze(self, system_prompt: str, user_content: str, temperature: float = 0.3) -> str:
        """Send analysis request to Kimi K2.6."""
        try:
            completion = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=temperature
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"AI Analysis Error: {str(e)}"

ai = FabricAIAnalyzer()
print("AI Analyzer initialized successfully.")

# =============================================================================
# CELL 3: Load Data from Fabric Lakehouse
# =============================================================================

# In Fabric, Spark is available by default
# Load commodity prices from the Lakehouse Delta table
try:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()

    # Load from Delta table (create table first if it doesn't exist)
    df_prices = spark.read.format("delta").load("Tables/CommodityPrices").toPandas()
    print(f"Loaded {len(df_prices)} price records from Lakehouse")
    print(df_prices.tail(5))
except Exception as e:
    print(f"Note: Lakehouse table not yet available ({e})")
    print("Using sample data for initial setup...")

    # Sample data for initial testing
    import pandas as pd
    df_prices = pd.DataFrame({
        'timestamp': [datetime.utcnow().isoformat()],
        'metal': ['Nickel', 'Cobalt', 'Lithium'],
        'price': [18500.0, 32000.0, 25000.0],
        'unit': ['USD/mt', 'USD/mt', 'USD/mt'],
        'source': ['AlphaVantage', 'AlphaVantage', 'AlphaVantage']
    })
    print(df_prices)

# =============================================================================
# CELL 4: GLI Business Rules (Contract Calculations)
# =============================================================================

# GLI Contract Constants
GRADE_MULTIPLIER = 0.85
THRESHOLD_PRICE_PER_MT = 20000
FLOOR_DISCOUNT = 0.08
PROFIT_SHARE = 0.15

def calculate_all(ni_price, co_price, li_price):
    """Run all GLI contract calculations."""

    # Black Mass Payables
    black_mass = {
        "ni_payable": round(ni_price * GRADE_MULTIPLIER, 2),
        "co_payable": round(co_price * GRADE_MULTIPLIER, 2),
        "total_value": round((ni_price + co_price) * GRADE_MULTIPLIER, 2),
    }

    # Primary Offtaker MHP
    floor_ni = ni_price * (1 - FLOOR_DISCOUNT)
    floor_co = co_price * (1 - FLOOR_DISCOUNT)
    profit_share_triggered = ni_price > THRESHOLD_PRICE_PER_MT
    incremental = max(0, ni_price - THRESHOLD_PRICE_PER_MT)
    profit_share_amt = incremental * PROFIT_SHARE if profit_share_triggered else 0

    mhp = {
        "floor_ni": round(floor_ni, 2),
        "floor_co": round(floor_co, 2),
        "profit_share_triggered": profit_share_triggered,
        "profit_share_amount": round(profit_share_amt, 2),
        "realized_ni": round(floor_ni - profit_share_amt, 2),
    }

    # Lithium Carbonate GTC
    effective_li = max(20000, min(li_price, 30000))
    li_gtc = {
        "spot_price": li_price,
        "effective_price": effective_li,
        "floor_active": li_price < 20000,
        "ceiling_active": li_price > 30000,
    }

    # Li Cycle Feedstock
    li_cycle = {
        "li_payable": round(li_price * 0.92 * 0.75, 2),
        "ni_payable": round(ni_price * 0.03 * 0.90, 2),
        "co_payable": round(co_price * 0.02 * 0.90, 2),
        "total_value": round(li_price * 0.92 * 0.75 + ni_price * 0.03 * 0.90 + co_price * 0.02 * 0.90, 2),
    }

    return {
        "black_mass": black_mass,
        "mhp_offtaker": mhp,
        "lithium_gtc": li_gtc,
        "li_cycle": li_cycle,
        "timestamp": datetime.utcnow().isoformat(),
    }

# Get latest prices
ni = df_prices[df_prices['metal'].str.lower() == 'nickel']['price'].iloc[-1] if len(df_prices) > 0 else 18500
co = df_prices[df_prices['metal'].str.lower() == 'cobalt']['price'].iloc[-1] if len(df_prices) > 0 else 32000
li = df_prices[df_prices['metal'].str.lower() == 'lithium']['price'].iloc[-1] if len(df_prices) > 0 else 25000

results = calculate_all(ni, co, li)
print("GLI Contract Calculations:")
print(json.dumps(results, indent=2))

# =============================================================================
# CELL 5: AI-Powered Analysis (Kimi K2.6)
# =============================================================================

system_prompt = (
    "You are a Financial Analyst for GLI (Global Lithium Innovations), "
    "a battery metals recycling company. Analyze the contract economics "
    "and provide actionable insights."
)

user_content = f"""
## Current Commodity Prices (USD/mt)
- Nickel: ${ni:,.2f}
- Cobalt: ${co:,.2f}
- Lithium Carbonate: ${li:,.2f}

## GLI Contract Calculations
{json.dumps(results, indent=2)}

Please provide:
1. Executive Summary (2-3 sentences)
2. Contract Performance Analysis
3. Key Insights & Triggers
4. Risk Exposure & Recommendations
"""

analysis = ai.analyze(system_prompt, user_content, temperature=0.4)
print("=" * 60)
print("AI ANALYSIS (Kimi K2.6 via Azure AI Foundry)")
print("=" * 60)
print(analysis)

# =============================================================================
# CELL 6: Write Results Back to Lakehouse
# =============================================================================

# Create a DataFrame with the analysis results
analysis_df = spark.createDataFrame([{
    "timestamp": datetime.utcnow().isoformat(),
    "ni_price": ni,
    "co_price": co,
    "li_price": li,
    "black_mass_value": results["black_mass"]["total_value"],
    "mhp_profit_share_triggered": results["mhp_offtaker"]["profit_share_triggered"],
    "li_floor_active": results["lithium_gtc"]["floor_active"],
    "li_ceiling_active": results["lithium_gtc"]["ceiling_active"],
    "ai_analysis": analysis,
}])

# Write to Delta table
analysis_df.write.format("delta").mode("append").saveAsTable("ContractAnalysis")
print("Analysis results written to Lakehouse table: ContractAnalysis")
print(f"Total records: {spark.read.format('delta').load('Tables/ContractAnalysis').count()}")

# =============================================================================
# CELL 7: Display Latest Analysis Summary
# =============================================================================

latest = spark.read.format("delta").load("Tables/ContractAnalysis") \
    .orderBy("timestamp", ascending=False) \
    .limit(1) \
    .toPandas()

if len(latest) > 0:
    row = latest.iloc[0]
    print(f"Latest Analysis: {row['timestamp']}")
    print(f"  Ni: ${row['ni_price']:,.2f}/mt | Co: ${row['co_price']:,.2f}/mt | Li: ${row['li_price']:,.2f}/mt")
    print(f"  Black Mass Value: ${row['black_mass_value']:,.2f}/mt")
    print(f"  MHP Profit Share: {'TRIGGERED' if row['mhp_profit_share_triggered'] else 'Not Triggered'}")
    print(f"  Li Floor: {'ACTIVE' if row['li_floor_active'] else 'Inactive'}")
    print(f"  Li Ceiling: {'ACTIVE' if row['li_ceiling_active'] else 'Inactive'}")
