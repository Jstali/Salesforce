from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from ..database import get_db
from ..auth import get_current_user
from .. import schemas, crud
from ..db_models import User

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def account_to_response(account) -> schemas.AccountResponse:
    return schemas.AccountResponse(
        id=account.id,
        name=account.name,
        phone=account.phone,
        website=account.website,
        industry=account.industry,
        description=account.description,
        billing_address=account.billing_address,
        owner_id=account.owner_id,
        created_at=account.created_at,
        updated_at=account.updated_at,
        owner_alias=account.owner.alias if account.owner else None
    )


@router.get("", response_model=schemas.PaginatedResponse)
async def list_accounts(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    owner_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skip = (page - 1) * page_size
    accounts, total = crud.get_accounts(
        db,
        skip=skip,
        limit=page_size,
        search=q,
        owner_id=owner_id,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return schemas.PaginatedResponse(
        items=[account_to_response(a) for a in accounts],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/{account_id}", response_model=schemas.AccountResponse)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = crud.get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Track recent record
    crud.add_recent_record(db, current_user.id, "account", account.id, account.name)

    return account_to_response(account)


@router.post("", response_model=schemas.AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: schemas.AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Set owner to current user if not specified
    if not account.owner_id:
        account.owner_id = current_user.id

    db_account = crud.create_account(db, account)
    return account_to_response(crud.get_account(db, db_account.id))


@router.put("/{account_id}", response_model=schemas.AccountResponse)
async def update_account(
    account_id: int,
    account: schemas.AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_account = crud.update_account(db, account_id, account)
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account_to_response(crud.get_account(db, account_id))


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = crud.delete_account(db, account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )


@router.put("/{account_id}/change-owner", response_model=schemas.AccountResponse)
async def change_account_owner(
    account_id: int,
    owner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = crud.update_account(db, account_id, schemas.AccountUpdate(owner_id=owner_id))
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account_to_response(crud.get_account(db, account_id))
