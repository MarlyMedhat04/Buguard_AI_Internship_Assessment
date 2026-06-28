from sqlalchemy.orm import Query
from sqlalchemy import cast, String, or_, and_, desc
from app.db.models import Asset, Relationship
from app.chains.query_chain import QueryIntent
from datetime import datetime, timezone


def build_asset_query(base_query: Query, intent: QueryIntent) -> Query:
    """Constructs SQLAlchemy filters safely from a validated QueryIntent."""

    # 1. Base Asset Filters
    if intent.asset_type_filter:
        base_query = base_query.filter(Asset.type == intent.asset_type_filter)

    if intent.status:
        base_query = base_query.filter(Asset.status == intent.status)

    if intent.keyword:
        kw = f"%{intent.keyword}%"
        base_query = base_query.filter(
            (Asset.value.ilike(kw))
            | (cast(Asset.metadata_json, String).ilike(kw))
            | (cast(Asset.tags, String).ilike(kw))
        )

    if intent.environment_filter:
        env = f"%{intent.environment_filter}%"
        base_query = base_query.filter(
            (cast(Asset.metadata_json, String).ilike(env))
            | (cast(Asset.tags, String).ilike(env))
        )

    if intent.criticality_filter:
        crit = f"%{intent.criticality_filter}%"
        base_query = base_query.filter((cast(Asset.metadata_json, String).ilike(crit)))

    if intent.tag:
        tag_val = f"%{intent.tag}%"
        base_query = base_query.filter(cast(Asset.tags, String).ilike(tag_val))

    # 2. Expiration Checks
    if intent.requires_expiration_check:
        now_iso = datetime.now(timezone.utc).date().isoformat()
        base_query = base_query.filter(
            Asset.metadata_json.op("->>")("expires") < now_iso
        )

    if intent.requires_expiring_soon_check:
        now_iso = datetime.now(timezone.utc).date().isoformat()
        from datetime import timedelta

        future_iso = (
            (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
        )
        base_query = base_query.filter(
            Asset.metadata_json.op("->>")("expires") >= now_iso,
            Asset.metadata_json.op("->>")("expires") <= future_iso,
        )

    # 3. Relationship Joins
    if intent.requires_join:
        target_filters = []
        if getattr(intent, "relationship_target", None):
            target_filters.append(Asset.type == intent.relationship_target)

        if getattr(intent, "target_environment", None):
            env = f"%{intent.target_environment}%"
            target_filters.append(
                or_(
                    cast(Asset.metadata_json, String).ilike(env),
                    cast(Asset.tags, String).ilike(env),
                )
            )

        if getattr(intent, "target_tag", None):
            tag_val = f"%{intent.target_tag}%"
            target_filters.append(cast(Asset.tags, String).ilike(tag_val))

        rel_type_filter = []
        if getattr(intent, "relationship_type", None):
            rel_type_filter.append(
                Relationship.relationship_type == intent.relationship_type
            )

        if target_filters or rel_type_filter:
            # We must find assets that have relationships matching the target filters
            # Check outgoing
            outgoing_conds = (
                rel_type_filter + [Relationship.target_asset.has(and_(*target_filters))]
                if target_filters
                else rel_type_filter
            )
            has_outgoing = (
                Asset.outgoing_relationships.any(and_(*outgoing_conds))
                if outgoing_conds
                else False
            )

            # Check incoming
            incoming_conds = (
                rel_type_filter + [Relationship.source_asset.has(and_(*target_filters))]
                if target_filters
                else rel_type_filter
            )
            has_incoming = (
                Asset.incoming_relationships.any(and_(*incoming_conds))
                if incoming_conds
                else False
            )

            if has_outgoing is not False and has_incoming is not False:
                base_query = base_query.filter(or_(has_outgoing, has_incoming))
            elif has_outgoing is not False:
                base_query = base_query.filter(has_outgoing)
            elif has_incoming is not False:
                base_query = base_query.filter(has_incoming)

    # 4. Sorting & Limiting
    if intent.sort:
        sort_field = intent.sort.lower()
        if sort_field == "first_seen":
            base_query = base_query.order_by(Asset.first_seen.asc())
        elif sort_field == "last_seen":
            base_query = base_query.order_by(Asset.last_seen.desc())
        # Other sorts fallback to default

    if getattr(intent, "limit", None) and isinstance(intent.limit, int):
        base_query = base_query.limit(intent.limit)

    return base_query
