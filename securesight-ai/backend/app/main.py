import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from .auth import current_membership, current_user, make_token, verify_password
from .ai_gateway import AIConfigurationError, AIServiceError, UnsafePromptError, get_provider, request_limit, sanitize_question
from .agent_tools import execute_security_tool
from .database import Base, engine, get_db
from .models import Asset, Incident, Organization, OrganizationMember, SecurityEvent, User
from .schemas import AIAnalysisRequest, AIAnalysisResponse, AssetCreate, AssetResponse, LoginRequest, OrganizationResponse, TokenResponse

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    if os.getenv("SEED_DEMO", "false").lower() == "true":
        seed_demo()
    yield

app = FastAPI(title="SecureSight AI API", version="0.1.0", lifespan=lifespan)

def seed_demo():
    username = os.getenv("SEED_DEMO_USERNAME", "Supriya").strip().casefold()
    password = os.getenv("SEED_DEMO_PASSWORD", "")
    if not password:
        raise RuntimeError("SEED_DEMO_PASSWORD must be set when SEED_DEMO=true")
    from .auth import hash_password
    from .database import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email.in_([username, "admin@securesight.local"])).first()
        if user:
            user.email = username
            user.password_hash = hash_password(password)
        else:
            org = Organization(name="SecureSight Demo")
            user = User(email=username, password_hash=hash_password(password))
            db.add_all([org, user]); db.flush()
        membership = db.query(OrganizationMember).filter_by(user_id=user.id).first()
        if membership is None:
            org = db.query(Organization).filter_by(name="SecureSight Demo").first()
            if org is None:
                org = Organization(name="SecureSight Demo")
                db.add(org)
                db.flush()
            membership = OrganizationMember(organization_id=org.id, user_id=user.id, role="owner")
            db.add(membership)
            db.flush()

        organization_id = membership.organization_id
        asset_specs = [
            ("Demo Customer API", "API", "api.demo.invalid"),
            ("Demo Web Console", "Web application", "console.demo.invalid"),
            ("Demo Linux Host", "Server", "linux-01.demo.invalid"),
            ("Demo PostgreSQL", "Database", "postgres.demo.invalid"),
        ]
        for name, asset_type, identifier in asset_specs:
            if not db.query(Asset).filter_by(organization_id=organization_id, identifier=identifier).first():
                db.add(Asset(organization_id=organization_id, name=name, asset_type=asset_type, identifier=identifier))
        db.flush()
        assets = {asset.identifier: asset for asset in db.query(Asset).filter_by(organization_id=organization_id).all()}

        now = datetime.now(timezone.utc)
        event_specs = [
            ("demo-event-auth-001", "Wazuh", "authentication_failure_burst", "high", "Several failed SSH logins were observed on the demo Linux host.", "linux-01.demo.invalid", 8),
            ("demo-event-net-002", "Suricata", "port_scan_pattern", "medium", "A synthetic port-scan pattern was detected against the demo API.", "api.demo.invalid", 21),
            ("demo-event-app-003", "Application IDS", "api_rate_anomaly", "medium", "Request volume briefly exceeded the demo API baseline.", "api.demo.invalid", 39),
            ("demo-event-auth-004", "Application IDS", "new_admin_location", "low", "A demo administrator sign-in came from a new location.", "console.demo.invalid", 65),
        ]
        for key, source, event_type, severity, summary, identifier, minutes_ago in event_specs:
            if not db.query(SecurityEvent).filter_by(organization_id=organization_id, event_key=key).first():
                asset = assets.get(identifier)
                db.add(SecurityEvent(organization_id=organization_id, asset_id=asset.id if asset else None, event_key=key, source=source, event_type=event_type, severity=severity, summary=summary, occurred_at=now - timedelta(minutes=minutes_ago), is_synthetic=True))

        incident_specs = [
            ("demo-incident-auth-001", "Repeated SSH authentication failures", "Credential access", "high", "open", 0.91, "linux-01.demo.invalid", 14),
            ("demo-incident-api-002", "Unusual API request burst", "API abuse", "medium", "investigating", 0.78, "api.demo.invalid", 42),
        ]
        for key, title, category, severity, status, confidence, identifier, minutes_ago in incident_specs:
            if not db.query(Incident).filter_by(organization_id=organization_id, incident_key=key).first():
                asset = assets.get(identifier)
                db.add(Incident(organization_id=organization_id, asset_id=asset.id if asset else None, incident_key=key, title=title, category=category, severity=severity, status=status, confidence=confidence, created_at=now - timedelta(minutes=minutes_ago), is_synthetic=True))
        db.commit()
    finally:
        db.close()

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "securesight-api"}

@app.post("/api/ai/analyze", response_model=AIAnalysisResponse)
def analyze_with_ai(payload: AIAnalysisRequest, membership: OrganizationMember = Depends(current_membership), db: Session = Depends(get_db)):
    try:
        question = sanitize_question(payload.question)
    except UnsafePromptError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not request_limit.check(membership.organization_id):
        raise HTTPException(status_code=429, detail="AI request limit reached for this organization. Try again later.")
    try:
        provider = get_provider()
        result = provider.analyze(question, lambda name, args: execute_security_tool(name, args, db, membership.organization_id))
        return AIAnalysisResponse(answer=result.answer, provider=provider.provider_name, model=provider.model_name, tools_used=result.tools_used)
    except AIConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.username.strip().casefold()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return TokenResponse(access_token=make_token(user))

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "username": user.email}

@app.get("/api/organization", response_model=OrganizationResponse)
def organization(membership: OrganizationMember = Depends(current_membership), db: Session = Depends(get_db)):
    org = db.get(Organization, membership.organization_id)
    return OrganizationResponse(id=org.id, name=org.name, role=membership.role)

@app.get("/api/overview")
def overview(membership: OrganizationMember = Depends(current_membership), db: Session = Depends(get_db)):
    organization_id = membership.organization_id
    event_count = db.query(func.count(SecurityEvent.id)).filter_by(organization_id=organization_id).scalar() or 0
    open_count = db.query(func.count(Incident.id)).filter(Incident.organization_id == organization_id, Incident.status != "closed").scalar() or 0
    incidents = db.query(Incident).filter_by(organization_id=organization_id).order_by(Incident.created_at.desc()).limit(5).all()
    events = db.query(SecurityEvent).filter_by(organization_id=organization_id).order_by(SecurityEvent.occurred_at.desc()).limit(5).all()
    severity_counts = {level: 0 for level in ("critical", "high", "medium", "low")}
    for severity, count in db.query(Incident.severity, func.count(Incident.id)).filter(Incident.organization_id == organization_id, Incident.status != "closed").group_by(Incident.severity).all():
        if severity in severity_counts:
            severity_counts[severity] = count
    synthetic_flags = [row.is_synthetic for row in incidents] + [row.is_synthetic for row in events]
    data_mode = "empty" if not synthetic_flags else ("synthetic" if all(synthetic_flags) else ("mixed" if any(synthetic_flags) else "live"))
    return {
        "data_mode": data_mode,
        "events_analyzed": event_count,
        "open_incidents": open_count,
        "severity_counts": severity_counts,
        "incidents": [{"id": row.id, "title": row.title, "category": row.category, "severity": row.severity, "status": row.status, "confidence": row.confidence, "asset": db.get(Asset, row.asset_id).name if row.asset_id and db.get(Asset, row.asset_id) else "Unknown asset", "created_at": row.created_at.isoformat(), "is_synthetic": row.is_synthetic} for row in incidents],
        "recent_events": [{"id": row.id, "source": row.source, "event_type": row.event_type, "severity": row.severity, "summary": row.summary, "occurred_at": row.occurred_at.isoformat(), "is_synthetic": row.is_synthetic} for row in events],
    }

@app.get("/api/assets", response_model=list[AssetResponse])
def list_assets(membership: OrganizationMember = Depends(current_membership), db: Session = Depends(get_db)):
    return db.query(Asset).filter_by(organization_id=membership.organization_id).order_by(Asset.created_at.desc()).all()

@app.post("/api/assets", response_model=AssetResponse, status_code=201)
def create_asset(payload: AssetCreate, membership: OrganizationMember = Depends(current_membership), db: Session = Depends(get_db)):
    asset = Asset(organization_id=membership.organization_id, **payload.model_dump())
    db.add(asset); db.commit(); db.refresh(asset)
    return asset

@app.delete("/api/assets/{asset_id}", status_code=204)
def delete_asset(asset_id: str, membership: OrganizationMember = Depends(current_membership), db: Session = Depends(get_db)):
    asset = db.query(Asset).filter_by(id=asset_id, organization_id=membership.organization_id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(asset); db.commit()
    return Response(status_code=204)
