# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.dependencies import get_db_session
from cyberlens.incidents.schemas import (
    CaseCommentRequest,
    CaseCreateRequest,
    CaseDetail,
    CaseEventDetail,
    CaseFromAlertRequest,
    CaseListResponse,
    CaseUpdateRequest,
    EvidenceUploadResponse,
    PlaybookRunRequest,
    PlaybookRunResponse,
    ResponseActionDetail,
    ResponseActionRequest,
)
from cyberlens.incidents.service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


async def get_incident_service(
    session: AsyncSession = Depends(get_db_session),
) -> IncidentService:
    return IncidentService(session=session)


@router.get("/status")
async def incidents_status() -> dict[str, str]:
    return {"status": "ready", "message": "Incident workflow endpoints are available."}


@router.get("", response_model=CaseListResponse)
async def list_cases(
    service: IncidentService = Depends(get_incident_service),
) -> CaseListResponse:
    return await service.list_cases()


@router.post("", response_model=CaseDetail)
async def create_case(
    payload: CaseCreateRequest,
    service: IncidentService = Depends(get_incident_service),
) -> CaseDetail:
    return await service.create_case(payload)


@router.get("/{case_uid}", response_model=CaseDetail)
async def get_case(
    case_uid: str,
    service: IncidentService = Depends(get_incident_service),
) -> CaseDetail:
    return await service.get_case(case_uid)


@router.patch("/{case_uid}", response_model=CaseDetail)
async def update_case(
    case_uid: str,
    payload: CaseUpdateRequest,
    service: IncidentService = Depends(get_incident_service),
) -> CaseDetail:
    return await service.update_case(case_uid, payload)


@router.post("/from-alerts/{alert_id}", response_model=CaseDetail)
async def create_case_from_alert(
    alert_id: int,
    payload: CaseFromAlertRequest,
    service: IncidentService = Depends(get_incident_service),
) -> CaseDetail:
    return await service.create_case_from_alert(alert_id, payload)


@router.post("/{case_uid}/comments", response_model=CaseEventDetail)
async def add_comment(
    case_uid: str,
    payload: CaseCommentRequest,
    service: IncidentService = Depends(get_incident_service),
) -> CaseEventDetail:
    return await service.add_comment(case_uid, payload)


@router.post("/{case_uid}/playbook/run", response_model=PlaybookRunResponse)
async def run_playbook(
    case_uid: str,
    payload: PlaybookRunRequest,
    service: IncidentService = Depends(get_incident_service),
) -> PlaybookRunResponse:
    return await service.run_playbook(case_uid, payload)


@router.get("/{case_uid}/response-actions", response_model=list[ResponseActionDetail])
async def list_response_actions(
    case_uid: str,
    service: IncidentService = Depends(get_incident_service),
) -> list[ResponseActionDetail]:
    return await service.list_response_actions(case_uid)


@router.post("/{case_uid}/response-actions", response_model=ResponseActionDetail)
async def execute_response_action(
    case_uid: str,
    payload: ResponseActionRequest,
    service: IncidentService = Depends(get_incident_service),
) -> ResponseActionDetail:
    return await service.execute_response_action(case_uid, payload)


@router.post("/{case_uid}/evidence", response_model=EvidenceUploadResponse)
async def upload_evidence(
    case_uid: str,
    actor: str = Form(default="analyst"),
    file: UploadFile = File(...),
    service: IncidentService = Depends(get_incident_service),
) -> EvidenceUploadResponse:
    return await service.upload_evidence(case_uid, actor, file)
