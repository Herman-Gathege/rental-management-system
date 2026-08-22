#backend/app/models/__init__.py
from app.models.users import User
from app.models.role import Role
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.organization_invitation import OrganizationInvitation
from app.models.property import Property
from app.models.property_manager import PropertyManager
from app.models.unit import Unit
from app.models.tenant import Tenant
from app.models.tenant_document import TenantDocument
from app.models.lease import Lease
from app.models.charge import Charge
from app.models.payment import Payment
from app.models.audit_log import AuditLog
from app.models.checklist_item_template import ChecklistItemTemplate
from app.models.lease_inspection import LeaseInspection
from app.models.inspection_item import InspectionItem
from app.models.inspection_note import InspectionNote
from app.models.message import Message
from app.models.ticket import Ticket

# Expense management (Sprint 5)
from app.models.expense_category import ExpenseCategory
from app.models.vendor import Vendor
from app.models.expense import Expense
from app.models.expense_attachment import ExpenseAttachment

# Communication & support hub (Sprint 6)
# Ticket itself is imported above (it already existed from WhatsApp Phase 2 and
# was evolved in place). These are the new child + notification tables.
from app.models.ticket_message import TicketMessage
from app.models.ticket_attachment import TicketAttachment
from app.models.ticket_assignment import TicketAssignment
from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference

# Phone verification (Sprint 6.2 #6)
from app.models.otp_verification import OtpVerification

# WhatsApp integration routing (environment-aware org resolution)
from app.models.whatsapp_integration import WhatsAppIntegration
