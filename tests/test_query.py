import pytest
from app.db.models import Asset, Relationship
from app.chains.query_chain import QueryIntent

def test_query_grounding_and_hallucination_trap(client, db_session, monkeypatch):
    # Mock LLM
    def mock_evaluate(q):
        if "kubernetes" in q.lower():
            return QueryIntent(query_type="VALID", asset_type="cluster", confidence="HIGH")
        return QueryIntent(query_type="VALID", asset_type="certificate", status="expired", confidence="HIGH")
    monkeypatch.setattr("app.chains.query_chain.evaluate_query_chain", mock_evaluate)

    # Setup DB
    client.post("/import", json={"tenant_id": "tenant_1", "assets": [{"type": "certificate", "value": "cert_xyz", "status": "expired"}]})
    
    # 1. Valid Query
    resp = client.post("/query", json={"tenant_id": "tenant_1", "question": "show expired certificates"})
    assert resp.status_code == 200
    assert "assets" in resp.json()
    assert resp.json()["assets"][0]["value"] == "cert_xyz"
    
    # 2. Hallucination Trap
    resp_trap = client.post("/query", json={"tenant_id": "tenant_1", "question": "Show me all kubernetes clusters."})
    assert resp_trap.status_code == 200
    assert resp_trap.json()["query_type"] == "AMBIGUOUS"

def test_graph_query(client, db_session, monkeypatch):
    def mock_evaluate(q):
        return QueryIntent(
            query_type="VALID",
            asset_type_filter="certificate",
            requires_expiration_check=True,
            requires_join=True,
            relationship_type="covers",
            relationship_target="subdomain",
            target_environment="prod",
            confidence="HIGH"
        )
    monkeypatch.setattr("app.chains.query_chain.evaluate_query_chain", mock_evaluate)

    payload = {
        "tenant_id": "tenant_A",
        "assets": [
            {"type": "certificate", "value": "cert.com", "status": "active", "metadata": {"expires": "2020-01-01T00:00:00Z"}},
            {"type": "subdomain", "value": "api.cert.com", "tags": ["prod"]}
        ],
        "relationships": [
            {"source": "cert.com", "target": "api.cert.com", "type": "covers"}
        ]
    }
    client.post("/import", json=payload)
    resp = client.post("/query", json={"tenant_id": "tenant_A", "question": "show expired certificates on production subdomains"})
    assert resp.status_code == 200
    assert "assets" in resp.json()
    assert len(resp.json()["assets"]) > 0
    assert resp.json()["assets"][0]["value"] == "cert.com"
