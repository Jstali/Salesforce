from pydantic import BaseModel

class QuotationCreate(BaseModel):
    account_id: int
    title: str
    amount: float
    tax_amount: float = 0

class InvoiceCreate(BaseModel):
    account_id: int
    description: str
    amount: float
    invoice_type: str = "Standard"
    tax_amount: float = 0

class ServiceAccountCreate(BaseModel):
    account_id: int
    warranty_status: str = "Active"
    service_level: str = "Silver"

class WarrantyExtensionCreate(BaseModel):
    service_account_id: int
    extension_start_date: str
    extension_end_date: str
    extension_cost: float = 0

class SLACreate(BaseModel):
    service_account_id: int
    name: str
    response_time_hours: int
    resolution_time_hours: int
    uptime_percentage: float = 99.9
    support_hours: str = "24/7"

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..auth import get_current_user
from ..db_models import User, ServiceAccount, ServiceLevelAgreement, Quotation, Invoice, WarrantyExtension
from ..logger import log_action

router = APIRouter(prefix="/api/service", tags=["service"])

# Service Accounts
@router.get("/accounts")
async def list_service_accounts(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    accounts = db.query(ServiceAccount).offset(skip).limit(limit).all()
    total = db.query(ServiceAccount).count()
    return {"items": accounts, "total": total}

@router.post("/accounts")
async def create_service_account(
    data: ServiceAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service_account = ServiceAccount(
        account_id=data.account_id,
        warranty_status=data.warranty_status,
        service_level=data.service_level,
        owner_id=current_user.id,
        created_at=datetime.now()
    )
    db.add(service_account)
    db.commit()
    db.refresh(service_account)
    
    log_action(
        action_type="CREATE_SERVICE_ACCOUNT",
        user=current_user.username,
        details=f"Service account created for account {data.account_id}",
        status="success"
    )
    
    return service_account

@router.get("/accounts/{account_id}")
async def get_service_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(ServiceAccount).filter(ServiceAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")
    return account

@router.put("/accounts/{account_id}")
async def update_service_account(
    account_id: int,
    warranty_status: Optional[str] = None,
    service_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(ServiceAccount).filter(ServiceAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")
    
    if warranty_status:
        account.warranty_status = warranty_status
    if service_level:
        account.service_level = service_level
    
    db.commit()
    db.refresh(account)
    
    log_action(
        action_type="UPDATE_SERVICE_ACCOUNT",
        user=current_user.username,
        details=f"Service account {account_id} updated",
        status="success"
    )
    
    return account

# Quotations
@router.get("/quotations")
async def list_quotations(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quotations = db.query(Quotation).offset(skip).limit(limit).all()
    total = db.query(Quotation).count()
    return {"items": quotations, "total": total}

@router.post("/quotations")
async def create_quotation(
    data: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        quotation = Quotation(
            quotation_number=f"QT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            account_id=data.account_id,
            title=data.title,
            amount=data.amount,
            tax_amount=data.tax_amount,
            total_amount=data.amount + data.tax_amount,
            status="Draft",
            owner_id=current_user.id,
            created_at=datetime.now()
        )
        db.add(quotation)
        db.commit()
        db.refresh(quotation)
        
        log_action(
            action_type="CREATE_QUOTATION",
            user=current_user.username,
            details=f"Quotation {quotation.quotation_number} created for £{data.amount}",
            status="success"
        )
        
        return quotation
    except Exception as e:
        db.rollback()
        print(f"Error creating quotation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quotations/{quotation_id}")
async def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return quotation

@router.put("/quotations/{quotation_id}")
async def update_quotation(
    quotation_id: int,
    status: Optional[str] = None,
    amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if status:
        quotation.status = status
    if amount:
        quotation.amount = amount
        quotation.total_amount = amount + quotation.tax_amount
    
    db.commit()
    db.refresh(quotation)
    
    log_action(
        action_type="UPDATE_QUOTATION",
        user=current_user.username,
        details=f"Quotation {quotation.quotation_number} updated",
        status="success"
    )
    
    return quotation

# Invoices
@router.get("/invoices")
async def list_invoices(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoices = db.query(Invoice).offset(skip).limit(limit).all()
    total = db.query(Invoice).count()
    return {"items": invoices, "total": total}

@router.post("/invoices")
async def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        invoice = Invoice(
            invoice_number=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            account_id=data.account_id,
            description=data.description,
            amount=data.amount,
            tax_amount=data.tax_amount,
            total_amount=data.amount + data.tax_amount,
            invoice_type=data.invoice_type,
            status="Draft",
            invoice_date=datetime.now(),
            owner_id=current_user.id,
            created_at=datetime.now()
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        log_action(
            action_type="CREATE_INVOICE",
            user=current_user.username,
            details=f"Invoice {invoice.invoice_number} created ({data.invoice_type}) for £{data.amount}",
            status="success"
        )
        
        return invoice
    except Exception as e:
        db.rollback()
        print(f"Error creating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.put("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: int,
    status: Optional[str] = None,
    amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if status:
        invoice.status = status
        if status == "Paid":
            invoice.paid_date = datetime.now()
    if amount:
        invoice.amount = amount
        invoice.total_amount = amount + invoice.tax_amount
    
    db.commit()
    db.refresh(invoice)
    
    log_action(
        action_type="UPDATE_INVOICE",
        user=current_user.username,
        details=f"Invoice {invoice.invoice_number} updated to {status}",
        status="success"
    )
    
    return invoice

# Warranty Extensions
@router.get("/warranty-extensions")
async def list_warranty_extensions(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    extensions = db.query(WarrantyExtension).offset(skip).limit(limit).all()
    total = db.query(WarrantyExtension).count()
    return {"items": extensions, "total": total}

@router.post("/warranty-extensions")
async def create_warranty_extension(
    data: WarrantyExtensionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    extension = WarrantyExtension(
        service_account_id=data.service_account_id,
        extension_start_date=datetime.fromisoformat(data.extension_start_date),
        extension_end_date=datetime.fromisoformat(data.extension_end_date),
        extension_cost=data.extension_cost,
        status="Active",
        owner_id=current_user.id,
        created_at=datetime.now()
    )
    db.add(extension)
    db.commit()
    db.refresh(extension)
    
    log_action(
        action_type="CREATE_WARRANTY_EXTENSION",
        user=current_user.username,
        details=f"Warranty extension created for service account {data.service_account_id}",
        status="success"
    )
    
    return extension

@router.get("/slas")
async def list_slas(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        slas = db.query(ServiceLevelAgreement).offset(skip).limit(limit).all()
        total = db.query(ServiceLevelAgreement).count()
        return {"items": slas, "total": total}
    except Exception as e:
        print(f"Error listing SLAs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/slas")
async def create_sla(
    data: SLACreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sla = ServiceLevelAgreement(
        service_account_id=data.service_account_id,
        name=data.name,
        response_time_hours=data.response_time_hours,
        resolution_time_hours=data.resolution_time_hours,
        uptime_percentage=data.uptime_percentage,
        support_hours=data.support_hours,
        created_at=datetime.now()
    )
    db.add(sla)
    db.commit()
    db.refresh(sla)
    
    log_action(
        action_type="CREATE_SLA",
        user=current_user.username,
        details=f"SLA '{data.name}' created for service account {data.service_account_id}",
        status="success"
    )
    
    return sla
