from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.db.models import Asset, Relationship


class ContextValidationError(Exception):
    pass


class ContextBuilder:
    CONTEXT_VERSION = "1.0"

    @classmethod
    def _normalize_asset(cls, asset: Asset) -> Dict[str, Any]:
        """Convert SQLAlchemy Asset to a dictionary."""
        normalized = {
            "id": str(asset.id),
            "tenant_id": str(asset.tenant_id),
            "type": (
                asset.type.value if hasattr(asset.type, "value") else str(asset.type)
            ),
            "value": str(asset.value),
            "status": (
                asset.status.value
                if hasattr(asset.status, "value")
                else str(asset.status)
            ),
            "source": str(asset.source),
            "first_seen": asset.first_seen.isoformat() if asset.first_seen else None,
            "last_seen": asset.last_seen.isoformat() if asset.last_seen else None,
            "tags": list(asset.tags) if asset.tags else [],
            "metadata": dict(asset.metadata_json) if asset.metadata_json else {},
        }
        return normalized

    @classmethod
    def _normalize_relationship(cls, rel: Relationship) -> Dict[str, Any]:
        return {
            "source_id": str(rel.source_asset_id),
            "target_id": str(rel.target_asset_id),
            "type": str(rel.relationship_type),
        }

    @classmethod
    def _compress_data(cls, data: Any) -> Any:
        """Recursively removes None, empty lists, empty dicts, and empty strings."""
        if isinstance(data, dict):
            compressed = {}
            for k, v in data.items():
                compressed_v = cls._compress_data(v)
                if (
                    compressed_v is not None
                    and compressed_v != ""
                    and compressed_v != []
                    and compressed_v != {}
                ):
                    compressed[k] = compressed_v
            return compressed
        elif isinstance(data, list):
            compressed_list = []
            for item in data:
                compressed_item = cls._compress_data(item)
                if (
                    compressed_item is not None
                    and compressed_item != ""
                    and compressed_item != []
                    and compressed_item != {}
                ):
                    compressed_list.append(compressed_item)
            return compressed_list
        else:
            return data

    @classmethod
    def _order_asset_keys(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures stable token optimization ordering: id -> type -> value -> status -> metadata."""
        priority_keys = ["id", "type", "value", "status", "metadata"]
        ordered = {}
        for k in priority_keys:
            if k in data:
                ordered[k] = data[k]
        for k, v in data.items():
            if k not in priority_keys:
                ordered[k] = v
        return ordered

    @classmethod
    def _validate_semantic_and_schema(cls, asset: Dict[str, Any]):
        """Schema & Semantic validation."""
        required = ["id", "type", "value", "status"]
        for req in required:
            if req not in asset:
                raise ContextValidationError(
                    f"Missing required schema field: {req} in asset {asset.get('id')}"
                )

        first_seen_str = asset.get("first_seen")
        last_seen_str = asset.get("last_seen")

        if first_seen_str and last_seen_str:
            try:
                first = datetime.fromisoformat(first_seen_str)
                last = datetime.fromisoformat(last_seen_str)
                if first.tzinfo is None:
                    first = first.replace(tzinfo=timezone.utc)
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                if first > last:
                    raise ContextValidationError(
                        f"Semantic Error: first_seen ({first}) is after last_seen ({last}) for asset {asset['id']}"
                    )
            except ValueError:
                pass

        if asset["type"] == "certificate":
            pass  # Removed invalid assumption that certs can't expire before they are discovered

    @classmethod
    def build_common_context(
        cls,
        assets: List[Asset],
        analysis_type: str,
        relationships: Optional[List[Relationship]] = None,
        include_relationships: bool = False,
    ) -> Dict[str, Any]:
        """Base method that Normalizes -> Compresses -> Validates -> Specializes."""
        normalized_assets = []
        for a in assets:
            norm = cls._normalize_asset(a)
            comp = cls._compress_data(norm)
            comp = cls._order_asset_keys(comp)
            cls._validate_semantic_and_schema(comp)
            normalized_assets.append(comp)

        context = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "context_version": cls.CONTEXT_VERSION,
                "asset_count": len(normalized_assets),
                "analysis_type": analysis_type,
            },
            "assets": normalized_assets,
        }

        if include_relationships and relationships:
            norm_rels = [
                cls._compress_data(cls._normalize_relationship(r))
                for r in relationships
            ]
            context["relationships"] = norm_rels

        return context

    @classmethod
    def build_query_context(cls, assets: List[Asset]) -> Dict[str, Any]:
        """Context tailored for natural language queries."""
        return cls.build_common_context(assets, analysis_type="query")

    @classmethod
    def build_risk_context(
        cls,
        assets: List[Asset],
        evidence: Dict[str, Any],
        relationships: Optional[List[Relationship]] = None,
        include_relationships: bool = False,
    ) -> Dict[str, Any]:
        """Context tailored for risk analysis, explicitly including evidence."""
        ctx = cls.build_common_context(
            assets,
            analysis_type="risk",
            relationships=relationships,
            include_relationships=include_relationships,
        )

        clean_evidence = cls._compress_data(evidence)
        ctx["evidence"] = clean_evidence

        return ctx

    @classmethod
    def build_enrichment_context(
        cls,
        asset: Asset,
        evidence: Dict[str, Any],
        relationships: Optional[List[Relationship]] = None,
        include_relationships: bool = False,
    ) -> Dict[str, Any]:
        """Context tailored for enriching a single asset, including explicitly extracted evidence."""
        ctx = cls.build_common_context(
            [asset],
            analysis_type="enrichment",
            relationships=relationships,
            include_relationships=include_relationships,
        )
        ctx["evidence"] = cls._compress_data(evidence)
        return ctx

    @classmethod
    def build_report_context(cls, db_aggregates: Dict[str, Any]) -> Dict[str, Any]:
        """Context tailored for report generation. Relies purely on DB aggregates."""
        clean_aggregates = cls._compress_data(db_aggregates)

        context = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "context_version": cls.CONTEXT_VERSION,
                "asset_count": clean_aggregates.get("total_assets", 0),
                "analysis_type": "report",
            },
            "statistics": clean_aggregates,
        }
        return context
