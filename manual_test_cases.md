# Manual Test Cases for FastAPI

You can run these tests either via cURL commands in your terminal or by pasting the JSON payloads directly into the interactive Swagger UI at `http://127.0.0.1:8000/docs`.

---

## 1. Import Test Data

First, seed the database with test assets spanning different tenants, environments, and lifecycles.

**Endpoint**: `POST /import`

**JSON Payload**:
```json
{
  "tenant_id": "tenant_A",
  "assets": [
    {
      "type": "domain",
      "value": "buguard-demo.com",
      "tags": ["production"]
    },
    {
      "type": "subdomain",
      "value": "api.buguard-demo.com",
      "tags": ["prod"]
    },
    {
      "type": "subdomain",
      "value": "dev-db.buguard-demo.com",
      "tags": ["development"]
    },
    {
      "type": "certificate",
      "value": "CN=expired.buguard-demo.com",
      "metadata": {"expires": "2020-01-01T00:00:00Z", "issuer": "Let's Encrypt"}
    },
    {
      "type": "certificate",
      "value": "CN=active.buguard-demo.com",
      "metadata": {"expires": "2029-01-01T00:00:00Z", "issuer": "DigiCert"}
    },
    {
      "type": "technology",
      "value": "nginx"
    },
    {
      "type": "technology",
      "value": "PostgreSQL 9.6"
    }
  ],
  "relationships": [
    {"source": "api.buguard-demo.com", "target": "buguard-demo.com", "type": "subdomain_of"},
    {"source": "nginx", "target": "api.buguard-demo.com", "type": "runs_on"},
    {"source": "PostgreSQL 9.6", "target": "dev-db.buguard-demo.com", "type": "runs_on"}
  ]
}
```

**Expected Output**:
```json
{
  "message": "Successfully imported 7 assets and 3 relationships.",
  "tenant_id": "tenant_A"
}
```

---

## 2. Natural Language Query: Joins & Context

Test the system's ability to understand implicit joins (databases running on development subdomains).

**Endpoint**: `POST /query`

**JSON Payload**:
```json
{
  "tenant_id": "tenant_A",
  "question": "Show me databases on development subdomains"
}
```

**Expected Output**:
The LLM will translate this to find the `technology` (PostgreSQL 9.6) where `relationship_target` is a `subdomain` and `target_environment` is `development`.
```json
{
  "query_type": "VALID",
  "assets": [
    {
      "id": "...",
      "tenant_id": "tenant_A",
      "type": "technology",
      "value": "PostgreSQL 9.6",
      "status": "active",
      "tags": [],
      "metadata": {}
    }
  ]
}
```

---

## 3. Natural Language Query: Expiring Soon

Test the date-range evaluation capabilities of the SQL Builder.

**Endpoint**: `POST /query`

**JSON Payload**:
```json
{
  "tenant_id": "tenant_A",
  "question": "Which certificates are expired?"
}
```

**Expected Output**:
It will filter strictly for the certificate that expired in 2020.
```json
{
  "query_type": "VALID",
  "assets": [
    {
      "type": "certificate",
      "value": "CN=expired.buguard-demo.com"
      // ...
    }
  ]
}
```

---

## 4. Single-Asset Enrichment

Test the AI's ability to take a raw asset (e.g., an IP address or a technology) and dynamically infer its context without prior DB ingestion.

**Endpoint**: `POST /enrich`

**JSON Payload**:
```json
{
  "tenant_id": "tenant_A",
  "type": "ip_address",
  "value": "10.0.0.50"
}
```

**Expected Output**:
The LLM should recognize `10.0.0.50` as a private, internal IP address and build the envelope.
```json
{
  "message": "Enrichment completed successfully.",
  "results": [
    {
      "value": "10.0.0.50",
      "enrichment": {
        "environment": "internal/dev",
        "criticality": "low",
        "category": "network_infrastructure",
        "confidence": "HIGH",
        "evidence": [
           "Recognized as private IP range 10.x.x.x"
        ]
      }
    }
  ]
}
```

---

## 5. Global Risk Assessment

Ask the LLM to summarize the entire attack surface and flag critical vulnerabilities (e.g., the missing owner, the expired certificate, the EOL PostgreSQL 9.6).

**Endpoint**: `POST /risk`

**JSON Payload**:
```json
{
  "tenant_id": "tenant_A"
}
```

**Expected Output**:
A comprehensive executive summary detailing the aggregate score and flagging specific assets.
```json
{
  "tenant_id": "tenant_A",
  "aggregate_score": 75,
  "summary": "The environment has significant risks including an expired certificate (CN=expired.buguard-demo.com), an End-of-Life database (PostgreSQL 9.6), and assets with missing ownership tracking.",
  "critical_assets": [
    {
      "asset_value": "PostgreSQL 9.6",
      "risk_reason": "Outdated technology version detected."
    },
    {
      "asset_value": "CN=expired.buguard-demo.com",
      "risk_reason": "Certificate has expired."
    }
  ]
}
```

---

## 6. Multi-Tenant Isolation

Ensure data from `tenant_A` does not leak into `tenant_B`.

**Endpoint**: `POST /query`

**JSON Payload**:
```json
{
  "tenant_id": "tenant_B",
  "question": "Show me all of my domains."
}
```

**Expected Output**:
```json
{
  "query_type": "VALID",
  "message": "No matching assets found in the dataset.",
  "assets": []
}
```
