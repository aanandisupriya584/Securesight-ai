"""Small allowlist of read-only, organization-scoped analyst tools."""
import json
import re

from sqlalchemy.orm import Session

from .models import Asset, Incident, SecurityEvent

TOOL_DEFINITIONS = [
    {"type": "function", "name": "search_incidents", "description": "Search this organization's incidents by text, severity, and status.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "maxLength": 120}, "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]}, "status": {"type": "string", "enum": ["open", "investigating", "contained", "closed"]}}, "additionalProperties": False}},
    {"type": "function", "name": "search_security_events", "description": "Search this organization's security event summaries and severity.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "maxLength": 120}, "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]}}, "additionalProperties": False}},
    {"type": "function", "name": "list_assets", "description": "List this organization's assets by name or type. Does not return identifiers.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "maxLength": 120}}, "additionalProperties": False}},
]

_SECRET = re.compile(r"(?i)\b(?:password|passwd|passphrase|api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*[^\s,;]+|\bbearer\s+[a-z0-9._~+/=-]{12,}|\bAKIA[A-Z0-9]{16}\b")
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)

def _safe_text(value: str) -> str:
    return _EMAIL.sub("[redacted email]", _SECRET.sub("[redacted credential]", value))[:240]

def execute_security_tool(name: str, arguments: dict, db: Session, organization_id: str) -> str:
    """Execute only fixed SELECT queries. Tenant ID always comes from auth context."""
    if not isinstance(arguments, dict) or set(arguments) - {"query", "severity", "status"}:
        raise ValueError("Invalid tool arguments")
    query = arguments.get("query", "")
    if not isinstance(query, str) or len(query) > 120:
        raise ValueError("Invalid search query")
    severity = arguments.get("severity")
    if severity is not None and severity not in {"critical", "high", "medium", "low"}:
        raise ValueError("Invalid severity")
    pattern = f"%{query.strip()}%" if query.strip() else None
    rows = []
    if name == "search_incidents":
        status = arguments.get("status")
        if status is not None and status not in {"open", "investigating", "contained", "closed"}:
            raise ValueError("Invalid status")
        stmt = db.query(Incident).filter(Incident.organization_id == organization_id)
        if severity: stmt = stmt.filter(Incident.severity == severity)
        if status: stmt = stmt.filter(Incident.status == status)
        if pattern: stmt = stmt.filter(Incident.title.ilike(pattern) | Incident.category.ilike(pattern))
        rows = [{"id": r.id, "title": _safe_text(r.title), "category": _safe_text(r.category), "severity": r.severity, "status": r.status, "confidence": r.confidence, "created_at": r.created_at.isoformat(), "synthetic": r.is_synthetic} for r in stmt.order_by(Incident.created_at.desc()).limit(8).all()]
    elif name == "search_security_events":
        stmt = db.query(SecurityEvent).filter(SecurityEvent.organization_id == organization_id)
        if severity: stmt = stmt.filter(SecurityEvent.severity == severity)
        if pattern: stmt = stmt.filter(SecurityEvent.summary.ilike(pattern) | SecurityEvent.event_type.ilike(pattern) | SecurityEvent.source.ilike(pattern))
        rows = [{"id": r.id, "source": _safe_text(r.source), "event_type": _safe_text(r.event_type), "severity": r.severity, "summary": _safe_text(r.summary), "occurred_at": r.occurred_at.isoformat(), "synthetic": r.is_synthetic} for r in stmt.order_by(SecurityEvent.occurred_at.desc()).limit(8).all()]
    elif name == "list_assets":
        stmt = db.query(Asset).filter(Asset.organization_id == organization_id)
        if pattern: stmt = stmt.filter(Asset.name.ilike(pattern) | Asset.asset_type.ilike(pattern))
        rows = [{"id": r.id, "name": _safe_text(r.name), "type": _safe_text(r.asset_type)} for r in stmt.order_by(Asset.created_at.desc()).limit(8).all()]
    else:
        raise ValueError("Tool is not allowlisted")
    return json.dumps({"count": len(rows), "results": rows}, ensure_ascii=False)
