# 🔋 Commodity Price Analyzer

> *Calculate the impact of commodity prices, exchange rates, and government regulations on product output price.*

[![Model](https://img.shields.io/badge/Model-Claude%20Haiku%204.5-blueviolet)](https://anthropic.com)
[![Orchestration](https://img.shields.io/badge/Orchestration-Airia-blue)](https://airia.com)
[![MCP Tools](https://img.shields.io/badge/MCP-AlphaVantage%20%7C%20Regulations.Gov-green)](#tools)
[![State](https://img.shields.io/badge/State-Preview-orange)](#)
[![Flow Version](https://img.shields.io/badge/Flow%20Version-3.00-lightgrey)](#)

---

## What It Does

GLI runs complex payables and offtake structures across Nickel (Ni), Cobalt (Co), Lithium (Li), and Mixed Hydroxide Precipitate (MHP). Monitoring those contract economics has historically been manual and slow. **Commodity Price Analyzer** turns term sheets into a living model that continuously re-prices GLI's contracts off real-time commodity curves.

The agent:

1. Pulls live Ni/Co/Li prices via **AlphaVantage MCP** and monitors regulatory risk via **Regulations.Gov MCP**
2. Applies GLI's encoded business rules — black mass payables, Primary Offtaker MHP offtake, lithium carbonate GTCs, and Li Cycle feedstock pricing
3. Returns a narrative interpretation: realized vs. theoretical payables, margin capture vs. WMC, profit-share trigger status, and index sensitivity

A single natural-language question such as:

> *"What's our Ni/Co margin vs Offtaker this month on Atoka output?"*

triggers the full pipeline: **Memory Load → AI Model → Python Code → AI Model 1 → Output + Memory Store**.

---

## Encoded Contract Structures

| Contract | Index Basis | Key Rules |
|---|---|---|
| **Black Mass Payables** | LME 3-month Ni/Co | 85% grade multiplier; counterparties: Atoka, Li-Cycle, Redwood |
| **Primary Offtaker MHP Offtake** | Fastmarkets MB CO-0005 monthly | 8% floor discount; 15% profit share above $20,000/mt Ni |
| **Lithium Carbonate GTC** | Fastmarkets Li₂CO₃ 99.5% CIF | Floor $20,000/mt · Ceiling $30,000/mt |
| **Li Cycle Feedstock** | Mixed Fastmarkets/LME composite | 92% Li @ 75% payable · 3% Ni @ 90% · 2% Co @ 90% |

---

## Repository Structure

```
commodity-price-analyzer/
├── README.md                   ← This file
├── ARCHITECTURE.md             ← Airia flow diagram, node-by-node reference
├── CONTRACT_LOGIC.md           ← Full Python business-rules code, annotated
├── DATA_SOURCES.md             ← MCP tool config, API endpoints, symbol maps
├── SETUP.md                    ← Installation and credential configuration
├── USAGE.md                    ← Example queries and response walkthrough
├── SECURITY.md                 ← Guardrails, key management, audit trail
├── CONTRIBUTING.md             ← How to extend contracts and data sources
├── CHANGELOG.md                ← Version history
└── flows/
    └── commodity_analyzer.json ← Airia orchestration flow (import via dashboard)
```

---

## Tech Stack

| Layer | Detail |
|---|---|
| **Orchestration** | Airia (Flow v3.00) |
| **Language Model** | Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) — both AI steps |
| **Market Data** | AlphaVantage MCP — NICKEL, COBALT, CURRENCY_EXCHANGE_RATE |
| **Regulatory Data** | Regulations.Gov MCP — `GET /v4/documents` |
| **Computation** | Python step — deterministic contract functions |
| **Memory (Load)** | `GLI Contract Parameters` — shared, persistent contract config |
| **Memory (Store)** | `Historical Pricing Data` — shared, persistent, append-mode audit log |
| **Deployment Mode** | Chat — FileUpload, Whiteboard, Code, Math input modes supported |

---

## Quick Start

See [SETUP.md](./SETUP.md) for full instructions.

```bash
git clone https://github.com/GLI/commodity-price-analyzer.git
# Configure credentials in Airia (see SETUP.md)
# Import flows/commodity_analyzer.json via Airia dashboard
```

Then ask the agent:
```
"What are our realized Ni payables on black mass this week vs LME?"
"Has the Primary Offtaker profit share triggered this month?"
"Show me our Li carbonate GTC position — is the floor or ceiling active?"
"Run sensitivity: what happens to MHP margins if Ni drops $1,000/mt?"
```

---

## Agent Metadata

| Field | Value |
|---|---|
| Agent ID | `20013153-1e89-4496-adf7-27f2924ac70d` |
| Export Version | `20260226132027_EditBraveNativeEntries` |
| Flow Version | `3.00` |
| State | Preview |
| Last Updated | 2026-03-01 |
| Contributor | Shyam Desigan |
| Department | Everyone |

---

## What's Next

- Add SMM and direct Fastmarkets MCP feeds; extend commodity coverage to Mn and Cu
- ERP/treasury integration for invoice reconciliation and real-time P&L variance alerts

---

## License

Proprietary — GLI Internal Use Only.
