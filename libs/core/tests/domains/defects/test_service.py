import pytest
from uuid import uuid4
from fastapi import HTTPException
from packages.core.domains.defects.models import DefectStatus, DefectSeverity, ImpactArea, DetectedBy
from packages.core.domains.defects.schemas import DefectCreate, DefectUpdate
from packages.core.domains.defects import service

def test_status_transition_validation(db_session):
    # Setup
    actor_id = uuid4()
    payload = DefectCreate(
        title="Test Defect",
        environment="dev",
        severity=DefectSeverity.S3,
        impact_area=ImpactArea.BACKEND,
        detected_by=DetectedBy.QA
    )
    defect = service.create_defect_with_audit(db_session, actor_id, payload)
    
    # Valid transition: OPEN -> TRIAGED
    update = DefectUpdate(status=DefectStatus.TRIAGED)
    updated = service.update_defect_with_rules(db_session, defect.id, actor_id, update)
    assert updated.status == DefectStatus.TRIAGED
    
    # Invalid transition: TRIAGED -> RESOLVED (must go through ASSIGNED, FIXING, TESTING)
    update = DefectUpdate(status=DefectStatus.RESOLVED)
    with pytest.raises(HTTPException) as exc:
        service.update_defect_with_rules(db_session, defect.id, actor_id, update)
    assert exc.value.status_code == 400
    assert "Invalid status transition" in exc.value.detail

def test_rca_enforcement_for_s1(db_session):
    actor_id = uuid4()
    payload = DefectCreate(
        title="Critical Bug",
        environment="prod",
        severity=DefectSeverity.S1,
        impact_area=ImpactArea.SECURITY,
        detected_by=DetectedBy.MONITORING
    )
    defect = service.create_defect_with_audit(db_session, actor_id, payload)
    
    # Move through statuses to RESOLVED
    defect.status = DefectStatus.RESOLVED
    db_session.add(defect)
    db_session.commit()
    
    # Attempt to CLOSE without root_cause
    update = DefectUpdate(status=DefectStatus.CLOSED, regression_test_added=True)
    with pytest.raises(HTTPException) as exc:
        service.update_defect_with_rules(db_session, defect.id, actor_id, update)
    assert exc.value.status_code == 400
    assert "Root cause analysis is mandatory" in exc.value.detail
    
    # Add root_cause and CLOSE
    update = DefectUpdate(status=DefectStatus.CLOSED, root_cause="Memory leak fixed", regression_test_added=True)
    updated = service.update_defect_with_rules(db_session, defect.id, actor_id, update)
    assert updated.status == DefectStatus.CLOSED

def test_regression_test_gate(db_session):
    actor_id = uuid4()
    payload = DefectCreate(
        title="Medium Bug",
        environment="stage",
        severity=DefectSeverity.S3,
        impact_area=ImpactArea.BOT,
        detected_by=DetectedBy.USER
    )
    defect = service.create_defect_with_audit(db_session, actor_id, payload)
    
    # Move to RESOLVED
    defect.status = DefectStatus.RESOLVED
    db_session.add(defect)
    db_session.commit()
    
    # Attempt to CLOSE without regression_test_added=True
    update = DefectUpdate(status=DefectStatus.CLOSED)
    with pytest.raises(HTTPException) as exc:
        service.update_defect_with_rules(db_session, defect.id, actor_id, update)
    assert exc.value.status_code == 400
    assert "Regression test must be added" in exc.value.detail
