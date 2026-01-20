from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class LeadStatus(str, enum.Enum):
    new = "New"
    contacted = "Contacted"
    qualified = "Qualified"
    unqualified = "Unqualified"
    converted = "Converted"


class CaseStatus(str, enum.Enum):
    new = "New"
    working = "Working"
    escalated = "Escalated"
    closed = "Closed"


class CasePriority(str, enum.Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class OpportunityStage(str, enum.Enum):
    prospecting = "Prospecting"
    qualification = "Qualification"
    needs_analysis = "Needs Analysis"
    proposal = "Proposal"
    negotiation = "Negotiation"
    closed_won = "Closed Won"
    closed_lost = "Closed Lost"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(20), default="user")
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owned_accounts = relationship("Account", back_populates="owner")
    owned_contacts = relationship("Contact", back_populates="owner")
    owned_leads = relationship("Lead", back_populates="owner")
    owned_opportunities = relationship("Opportunity", back_populates="owner")
    owned_cases = relationship("Case", back_populates="owner")
    activities = relationship("Activity", back_populates="created_by_user")

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.username

    @property
    def alias(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(50))
    website = Column(String(255))
    industry = Column(String(100))
    description = Column(Text)
    billing_address = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_accounts")
    contacts = relationship("Contact", back_populates="account")
    opportunities = relationship("Opportunity", back_populates="account")
    cases = relationship("Case", back_populates="account")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    title = Column(String(100))
    phone = Column(String(50))
    email = Column(String(255), index=True)
    mailing_address = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_contacts")
    account = relationship("Account", back_populates="contacts")
    cases = relationship("Case", back_populates="contact")

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100), nullable=False)
    company = Column(String(255))
    title = Column(String(100))
    phone = Column(String(50))
    email = Column(String(255), index=True)
    status = Column(String(50), default="New")
    score = Column(Integer, default=0)
    region = Column(String(100))
    source = Column(String(100))
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_converted = Column(Boolean, default=False)
    converted_account_id = Column(Integer, ForeignKey("accounts.id"))
    converted_contact_id = Column(Integer, ForeignKey("contacts.id"))
    converted_opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_leads")

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    amount = Column(Float, default=0)
    stage = Column(String(50), default="Prospecting")
    probability = Column(Integer, default=0)
    close_date = Column(DateTime(timezone=True))
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_opportunities")
    account = relationship("Account", back_populates="opportunities")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="New")
    priority = Column(String(50), default="Medium")
    account_id = Column(Integer, ForeignKey("accounts.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_escalated = Column(Boolean, default=False)
    escalated_at = Column(DateTime(timezone=True))
    sla_due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_cases")
    account = relationship("Account", back_populates="cases")
    contact = relationship("Contact", back_populates="cases")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(50), nullable=False)  # contact, account, lead, opportunity, case
    record_id = Column(Integer, nullable=False)
    activity_type = Column(String(50), nullable=False)  # call, email, meeting, note, task
    subject = Column(String(255))
    details = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    created_by_user = relationship("User", back_populates="activities")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), nullable=False)  # create, update, delete, view
    target_table = Column(String(50), nullable=False)
    target_id = Column(Integer)
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class RecentRecord(Base):
    __tablename__ = "recent_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_type = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    record_name = Column(String(255))
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())


class ServiceAccount(Base):
    __tablename__ = "service_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    warranty_status = Column(String(50), default="Active")  # Active, Expired, Extended
    warranty_start_date = Column(DateTime(timezone=True))
    warranty_end_date = Column(DateTime(timezone=True))
    warranty_extended_until = Column(DateTime(timezone=True))
    service_level = Column(String(50))  # Gold, Silver, Bronze
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account")
    owner = relationship("User")


class ServiceLevelAgreement(Base):
    __tablename__ = "service_level_agreements"

    id = Column(Integer, primary_key=True, index=True)
    service_account_id = Column(Integer, ForeignKey("service_accounts.id"), nullable=False)
    name = Column(String(255), nullable=False)
    response_time_hours = Column(Integer)  # Hours to respond
    resolution_time_hours = Column(Integer)  # Hours to resolve
    uptime_percentage = Column(Float, default=99.9)
    support_hours = Column(String(100))  # 24/7, 9-5, etc.
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    service_account = relationship("ServiceAccount")


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    quotation_number = Column(String(50), unique=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    service_account_id = Column(Integer, ForeignKey("service_accounts.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    amount = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    status = Column(String(50), default="Draft")  # Draft, Sent, Accepted, Rejected
    valid_until = Column(DateTime(timezone=True))
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account")
    service_account = relationship("ServiceAccount")
    owner = relationship("User")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    service_account_id = Column(Integer, ForeignKey("service_accounts.id"))
    quotation_id = Column(Integer, ForeignKey("quotations.id"))
    invoice_type = Column(String(50), default="Standard")  # Standard, Proforma, Credit Note
    description = Column(Text)
    amount = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    status = Column(String(50), default="Draft")  # Draft, Sent, Paid, Overdue
    invoice_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    paid_date = Column(DateTime(timezone=True))
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account")
    service_account = relationship("ServiceAccount")
    quotation = relationship("Quotation")
    owner = relationship("User")


class WarrantyExtension(Base):
    __tablename__ = "warranty_extensions"

    id = Column(Integer, primary_key=True, index=True)
    service_account_id = Column(Integer, ForeignKey("service_accounts.id"), nullable=False)
    extension_start_date = Column(DateTime(timezone=True), nullable=False)
    extension_end_date = Column(DateTime(timezone=True), nullable=False)
    extension_cost = Column(Float, default=0)
    status = Column(String(50), default="Active")  # Active, Expired, Cancelled
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    service_account = relationship("ServiceAccount")
    owner = relationship("User")
