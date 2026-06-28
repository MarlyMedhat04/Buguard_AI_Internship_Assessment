import pytest
from app.db.models import Asset
from app.chains.query_chain import QueryIntent
from datetime import datetime, timezone, timedelta

def test_enrich_endpoint(client, db_session, monkeypatch):
    """
    Test the /enrich Endpoint (Core Capability 3).
    Ensures that an ip_address without prior DB existence can be passed and dynamically enriched.
    """
    def mock_evaluate(context):
        from app.chains.enrich_chain import EnrichmentResult
        return EnrichmentResult(
            environment="internal/dev",
            criticality="low",
            category="network_infrastructure",
            confidence="HIGH",
            evidence=["Recognized as private IP range 10.x.x.x"]
        )
    monkeypatch.setattr("app.chains.enrich_chain.evaluate_enrichment_chain", mock_evaluate)

    payload = {
        "tenant_id": "org_alpha",
        "type": "ip_address",
        "value": "10.0.0.50"
    }
    
    resp = client.post("/enrich", json=payload)
    assert resp.status_code == 200
    
    # Verify the asset was created and enriched
    asset = db_session.query(Asset).filter(Asset.value == "10.0.0.50", Asset.tenant_id == "org_alpha").first()
    assert asset is not None
    assert "ai_enrichment" in asset.metadata_json
    assert asset.metadata_json["ai_enrichment"]["result"]["environment"] == "internal/dev"


def test_expiring_soon_certificate(client, db_session, monkeypatch):
    """
    Test the "Expiring Soon" Edge Case.
    """
    def mock_evaluate(q):
        return QueryIntent(
            query_type="VALID",
            asset_type_filter="certificate",
            requires_expiring_soon_check=True,
            confidence="HIGH"
        )
    monkeypatch.setattr("app.chains.query_chain.evaluate_query_chain", mock_evaluate)

    future_7_days = (datetime.now(timezone.utc) + timedelta(days=7)).replace(microsecond=0).isoformat()
    past_date = "2020-01-01T00:00:00+00:00"
    far_future_date = "2029-01-01T00:00:00+00:00"

    payload = {
        "tenant_id": "org_alpha",
        "assets": [
            {"type": "certificate", "value": "expired.com", "metadata": {"expires": past_date}},
            {"type": "certificate", "value": "active.com", "metadata": {"expires": far_future_date}},
            {"type": "certificate", "value": "CN=expiring.buguard-demo.com", "source": "scan", "metadata": {"expires": future_7_days, "issuer": "Let's Encrypt"}}
        ]
    }
    client.post("/import", json=payload)
    
    resp = client.post("/query", json={"tenant_id": "org_alpha", "question": "Which certificates are expiring soon?"})
    print("QUERY RESP:", resp.json())
    assert resp.status_code == 200
    assets = resp.json().get("assets", [])
    
    assert len(assets) == 1
    assert assets[0]["value"] == "CN=expiring.buguard-demo.com"


def test_multi_tenant_isolation(client, db_session, monkeypatch):
    """
    Test Verifying the Multi-Tenant Isolation.
    """
    def mock_evaluate(q):
        return QueryIntent(
            query_type="VALID",
            asset_type_filter="domain",
            confidence="HIGH"
        )
    monkeypatch.setattr("app.chains.query_chain.evaluate_query_chain", mock_evaluate)

    # Import to org_alpha
    client.post("/import", json={
        "tenant_id": "org_alpha",
        "assets": [{"type": "domain", "value": "buguard-demo.com"}]
    })

    # Import to org_beta
    client.post("/import", json={
        "tenant_id": "org_beta",
        "assets": [{"type": "domain", "value": "secret-beta-project.com"}]
    })

    # Query org_beta
    resp = client.post("/query", json={"tenant_id": "org_beta", "question": "Show me all of my domains."})
    assert resp.status_code == 200
    assets = resp.json().get("assets", [])
    
    assert len(assets) == 1
    assert assets[0]["value"] == "secret-beta-project.com"
