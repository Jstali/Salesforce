from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from ..database import get_db
from ..auth import get_current_user
from .. import schemas, crud
from ..services import AssignmentService, CaseEscalationService, CaseMergeService
from ..db_models import User

router = APIRouter(prefix="/api/cases", tags=["cases"])


def case_to_response(case) -> schemas.CaseResponse:
    return schemas.CaseResponse(
        id=case.id,
        case_number=case.case_number,
        subject=case.subject,
        description=case.description,
        status=case.status,
        priority=case.priority,
        account_id=case.account_id,
        contact_id=case.contact_id,
        owner_id=case.owner_id,
        is_escalated=case.is_escalated,
        escalated_at=case.escalated_at,
        sla_due_date=case.sla_due_date,
        created_at=case.created_at,
        updated_at=case.updated_at,
        account_name=case.account.name if case.account else None,
        contact_name=case.contact.full_name if case.contact else None,
        owner_alias=case.owner.alias if case.owner else None
    )


@router.get("", response_model=schemas.PaginatedResponse)
async def list_cases(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    owner_id: Optional[int] = None,
    account_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skip = (page - 1) * page_size
    cases, total = crud.get_cases(
        db,
        skip=skip,
        limit=page_size,
        search=q,
        owner_id=owner_id,
        account_id=account_id,
        status=status,
        priority=priority,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return schemas.PaginatedResponse(
        items=[case_to_response(c) for c in cases],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/by-priority")
async def get_cases_by_priority(
    owner_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.get_cases_by_priority(db, owner_id)


@router.get("/{case_id}", response_model=schemas.CaseResponse)
async def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = crud.get_case(db, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Track recent record
    crud.add_recent_record(db, current_user.id, "case", case.id, f"{case.case_number}: {case.subject}")

    return case_to_response(case)


@router.post("", response_model=schemas.CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case: schemas.CaseCreate,
    auto_assign: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create the case first
    db_case = crud.create_case(db, case)

    # Apply assignment rules if auto_assign is True
    if auto_assign and not case.owner_id:
        assignment_service = AssignmentService(db)
        owner_id = assignment_service.apply_case_assignment(db_case)
        if owner_id:
            crud.update_case(db, db_case.id, schemas.CaseUpdate(owner_id=owner_id))

    return case_to_response(crud.get_case(db, db_case.id))


@router.put("/{case_id}", response_model=schemas.CaseResponse)
async def update_case(
    case_id: int,
    case: schemas.CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_case = crud.update_case(db, case_id, case)
    if not db_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    return case_to_response(crud.get_case(db, case_id))


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = crud.delete_case(db, case_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )


@router.post("/{case_id}/escalate", response_model=schemas.CaseResponse)
async def escalate_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    escalation_service = CaseEscalationService(db)

    try:
        case = escalation_service.escalate_case(case_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return case_to_response(crud.get_case(db, case_id))


@router.post("/merge", response_model=schemas.CaseResponse)
async def merge_cases(
    merge_data: schemas.CaseMerge,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    merge_service = CaseMergeService(db)

    try:
        master_case = merge_service.merge_cases(
            merge_data.case_ids,
            merge_data.master_case_id,
            current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return case_to_response(crud.get_case(db, master_case.id))


@router.put("/{case_id}/change-owner", response_model=schemas.CaseResponse)
async def change_case_owner(
    case_id: int,
    owner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = crud.update_case(db, case_id, schemas.CaseUpdate(owner_id=owner_id))
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    return case_to_response(crud.get_case(db, case_id))


@router.post("/check-sla")
async def check_and_escalate_overdue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to manually trigger SLA check and escalation."""
    escalation_service = CaseEscalationService(db)
    escalated = escalation_service.check_and_escalate_overdue_cases()

    return {
        "escalated_count": len(escalated),
        "escalated_cases": [c.case_number for c in escalated]
    }
