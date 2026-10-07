# Setup Guide

This guide covers everything required to import and run the Commodity Price Analyzer in your Airia environment.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Airia account with MCP Gateway enabled | Contact your Airia administrator to confirm gateway access |
| AlphaVantage API key (Premium tier) | Commodity data requires Premium; free tier does not include metals (`NICKEL`, `COBALT`) |
| Regulations.Gov API key | Free; register at [api.data.gov](https://api.data.gov/signup/) |
| Access to this repository | Clone or download the `flows/` directory |

---

## Step 1 — Import the Airia Flow

1. Log into your Airia dashboard
2. Navigate to **Agents → Import**
3. Upload `commodity_price_analyzer.json` from the repository root
4. The flow will be imported with the name **"Commodity Price Analyzer"** (agent ID `20013153-1e89-4496-adf7-27f2924ac70d`)

After import, the following components will be present in your workspace:

| Component | Name | Notes |
|---|---|---|
| AI Model step | `AI Model` | Amazon Nova Lite on Bedrock (`us.amazon.nova-lite-v1:0`, us-east-1), temp 0.2 |
| Python step | `Python Code` | Business rules engine |
| AI Model step | `AI Model 1` | Amazon Nova Lite on Bedrock (`us.amazon.nova-lite-v1:0`, us-east-1), temp 0.7 |
| Memory | `OpCo Contract Parameters` | Shared, persistent — must be populated (Step 3) |
| Memory | `Historical Pricing Data` | Shared, persistent — auto-populated on first run |
| Tool | `Sector Information` | AlphaVantage — requires credential setup (Step 2) |
| Tool | `Regulations GOV` | Regulations.Gov — requires credential setup (Step 2) |

---

## Step 2 — Configure API Credentials

Credentials are stored in Airia's credential vault and are **never embedded in the flow JSON**. Each user configures their own keys.

### AlphaVantage

1. In Airia, go to **Settings → Credentials → Add Credential**
2. Select type: **AlphaVantage**
3. Enter your AlphaVantage Premium API key
4. Save — the key will be automatically used by the `Sector Information` tool

> ⚠️ **Important:** If you are importing a flow that previously had an API key visible in an annotation or comment field, rotate that key immediately. See [SECURITY.md](./SECURITY.md) for details.

### Regulations.Gov

1. In Airia, go to **Settings → Credentials → Add Credential**
2. Select type: **GovRegulationsApiKey**
3. Enter your Regulations.Gov API key (obtainable free from [api.data.gov](https://api.data.gov/signup/))
4. Save

### Amazon Bedrock (Amazon Nova Lite)

The AI steps call **Amazon Nova Lite** through Airia's Bedrock provider. Airia does not store AWS keys in the flow export (`credentialExportOption` is `Placeholder`), so each workspace attaches its own Bedrock credential after import.

1. In AWS, confirm the cross-region inference profile `us.amazon.nova-lite-v1:0` is available in **us-east-1**. Amazon Nova is enabled on first use; it does not need the Anthropic use-case form.
2. Create an IAM user or role that can call `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on both `arn:aws:bedrock:*::foundation-model/*` and `arn:aws:bedrock:*:*:inference-profile/*`. The inference-profile ARN is required because `us.amazon.nova-lite-v1:0` is a cross-region profile, not a foundation-model id.
3. In Airia, go to **Settings → Credentials → Add Credential** (or **Models → Provide my own key**).
4. Type: **AWS Bedrock**. Region: **us-east-1**. Use either an access key on that IAM user, or Role ARN assumption, as described in [Airia's Bedrock guide](https://airia.ai/docs/integrations/Tools/aws-bedrock).
5. After the flow import (Step 4), bind this credential to the **Amazon Nova Lite** model.

---

## Step 3 — Populate the `OpCo Contract Parameters` Memory

The `OpCo Contract Parameters` memory (`id: f18b7405-05c6-4efd-bb52-2d9530509fa8`) is loaded at the start of every run. It provides the AI Model with current contract context — counterparty names, payable percentages, index assignments, floor/ceiling values, and grade bands.

This memory must be populated before the agent can run correctly.

### What to Store

Add a structured document to the memory containing your active contract parameters. Suggested format:

```
OpCo CONTRACT PARAMETERS — Current as of [DATE]

BLACK MASS PAYABLES
- Grade multiplier: 80% of LME 3-month Ni/Co
- Active counterparties: Counterparty A, Counterparty B, Counterparty C
- Pricing basis: LME 3-month average

PRIMARY OFFTAKER MHP OFFTAKE
- Counterparty: [Primary Offtaker Name]
- Floor discount: 5% below Fastmarkets MB
- Profit share threshold: $18,000/mt Ni
- Profit share rate: 10% above threshold
- Pricing basis: Fastmarkets MB CO-0005 monthly average

LITHIUM CARBONATE GTC
- Floor: $18,000/mt
- Ceiling: $25,000/mt
- Pricing basis: Fastmarkets Li₂CO₃ 99.5% CIF

Counterparty B FEEDSTOCK
- Li content: 90% grade @ 70% payable
- Ni content: 3% @ 90% payable
- Co content: 2% @ 90% payable
- Pricing basis: Mixed Fastmarkets/LME composite
```

### How to Populate

1. In Airia, navigate to **Memory → OpCo Contract Parameters**
2. Add the contract parameters document as memory content
3. This memory is shared (not user-specific) — all users of the agent will access the same parameters

---

## Step 4 — Bind Amazon Nova Lite

Both AI Model steps share one model record (`988d449f-5ed2-4f52-8ebf-ee823714c3fe`):

| Field | Value |
|---|---|
| Display name | Amazon Nova Lite |
| Model ID | `us.amazon.nova-lite-v1:0` |
| Provider | Bedrock |
| Endpoint | `https://bedrock.us-east-1.amazonaws.com` |
| Region | `us-east-1` |
| Source | Custom Bedrock model (no Airia library catalog id) |

Airia supports Amazon Bedrock in the model library (**Models → filter by Provider Bedrock**) and as a custom model (provider **AWS Bedrock**, model ID = the Bedrock inference profile). The AI Gateway documents `us.amazon.nova-lite-v1:0` as a Bedrock model id and invokes it with the Converse API. This export uses that path and keeps the existing AI Model steps, including their prompts, temperatures, and MCP tools.

The previous Claude Haiku library id is cleared on purpose. A published Airia catalog UUID for Nova Lite is not part of this export, so the model is marked `sourceType: custom` with `libraryModelId: null`. Import therefore cannot resolve the step back to Claude Haiku 4.5.

After import:

1. Open **Models** and select **Amazon Nova Lite**.
2. Confirm the model ID is `us.amazon.nova-lite-v1:0`, the provider is **Bedrock**, and the endpoint is `https://bedrock.us-east-1.amazonaws.com`.
3. Set credentials to **I have my own key** and select the us-east-1 Bedrock credential from Step 2.
4. Open both **AI Model** and **AI Model 1** and confirm they still point at **Amazon Nova Lite**.

If the importer drops the custom model, add it once from **Models → Custom Model** (provider AWS Bedrock, model ID `us.amazon.nova-lite-v1:0`, endpoint `https://bedrock.us-east-1.amazonaws.com`) and select it on both AI steps. If your tenant's model library already lists Amazon Nova Lite, you can select that library entry instead — the model ID must still be `us.amazon.nova-lite-v1:0`.

Nova Lite v1 has no extended-thinking control. Stage 1 no longer sets a reasoning effort; temperature `0.2` is what keeps price fetching and JSON dispatch stable. Stage 2 stays at temperature `0.7` for the narrative.

---

## Step 5 — Test the Agent

Once credentials are configured and the OpCo Contract Parameters memory is populated, run a test query:

**Simple test:**
```
What is the current Ni price and what does it mean for our black mass payables?
```

**Expected flow:** Memory loads → AI Model fetches NICKEL price from AlphaVantage → Python computes black mass payables → AI Model 1 returns a narrative with the calculated payable value.

**Profit-share test (if Ni > $18,000/mt):**
```
Has the Primary Offtaker profit share triggered this month?
```

**Li carbonate floor/ceiling test:**
```
Is our Li carbonate GTC floor or ceiling currently active?
```

---

## Step 6 — Configure Deployment (Optional)

The flow is pre-configured as a **Chat** deployment with these input modes enabled: FileUpload, Whiteboard, Code, Math.

To adjust deployment settings, navigate to **Agents → Commodity Price Analyzer → Deployment** in the Airia dashboard.

---

## Updating Contract Parameters

When OpCo amends a contract:

1. Update the `OpCo Contract Parameters` memory with the new terms
2. If the change affects the Python computation logic (e.g., a new payable percentage, a new floor value), update the relevant constants in the Python Code step:
   - `FLOOR_DISCOUNT` — currently `0.05`
   - `THRESHOLD_PRICE_PER_MT` — currently `18000`
   - `PROFIT_SHARE` — currently `0.10`
   - `contract_floor` / `contract_ceiling` in `calculate_lithium_carbonate_gtc` — currently `18000` / `25000`
3. Document the change in [CHANGELOG.md](./CHANGELOG.md)

See [CONTRIBUTING.md](./CONTRIBUTING.md) for instructions on adding entirely new contract types.
