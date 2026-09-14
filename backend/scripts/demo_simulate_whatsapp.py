import sys, uuid
from datetime import date, datetime, timedelta
sys.path.insert(0, "/app")

from app.db.session import SessionLocal
from app.core.encryption import blind_index
from app.models.tenant import Tenant
from app.models.organization import Organization
from app.models.lease import Lease
from app.models.charge import Charge
from app.models.payment import Payment
from app.models.message import Message
from app.models.payment_review_item import PaymentReviewItem
from app.services.billing_service import recompute_lease_settlement

ORG_NAME = "Riverside Property Management"

# reference | tenant name | payer phone | amount (KES)
DEMO_DATA = [
    ("UI7BD6170U", "Grace Mwangi",   "+254700000001", 12000),
    ("UI7FK5VY2Z", "David Kimani",   "+254700000002", 30000),
    ("UI6QI57NHU", "Sarah Wanjiku",  "+254700000003", 25000),
    ("UPTR5Q7VNK", "Peter Otieno",   "+254700000004", 12000),
    ("UMAC2R6HGB", "Mary Achieng",   "+254700000005", 10000),
]

# Mary's prior deposit payment (already settled before the demo)
MARY_PRIOR_DEPOSIT_REF = "PRIORDPST01"
MARY_PRIOR_DEPOSIT_AMOUNT = 10000

def mpesa_sms(ref, amount, landlord_name="RIVERSIDE PROPERTY"):
    return (
        f"{ref} Confirmed. Ksh{amount:,}.00 sent to {landlord_name} "
        f"for account 0100316372900 on {date.today().strftime('%d/%m/%y')} "
        f"at 10:30 AM. New M-PESA balance is Ksh500.00. "
        f"Transaction cost, Ksh0.00."
    )

db = SessionLocal()
try:
    org = db.query(Organization).filter(Organization.name == ORG_NAME).first()
    if not org:
        print(f"Org '{ORG_NAME}' not found. Run demo_create_org.py first.")
        sys.exit(1)

    # Generate current month's rent charge for every lease under this org
    # so the demo shows rent charges + arrears / credit clearly.
    today = date.today()
    billing_month = today.replace(day=1)

    leases = db.query(Lease).filter(
        Lease.organization_id == org.id,
        Lease.status == "active",
    ).all()

    rent_charges_created = 0
    for lease in leases:
        existing_rent = db.query(Charge).filter(
            Charge.lease_id == lease.id,
            Charge.charge_type == "rent",
            Charge.billing_month == billing_month,
        ).first()
        if existing_rent:
            continue
        try:
            due = today.replace(day=lease.billing_day)
        except ValueError:
            due = today.replace(day=28)
        rent_charge = Charge(
            id=str(uuid.uuid4()),
            organization_id=org.id, lease_id=lease.id,
            amount=lease.rent_amount, amount_paid=0,
            charge_type="rent",
            due_date=due, billing_month=billing_month,
            status="pending",
        )
        db.add(rent_charge)
        rent_charges_created += 1
    db.flush()
    print(f"Created {rent_charges_created} rent charge(s) for current month.")

    # Handle Mary's pre-paid deposit BEFORE simulating her WhatsApp forward.
    mary = db.query(Tenant).filter(
        Tenant.organization_id == org.id,
        Tenant.full_name == "Mary Achieng",
    ).first()
    if mary:
        mary_lease = db.query(Lease).filter(
            Lease.tenant_id == mary.id, Lease.status == "active",
        ).first()
        if mary_lease:
            already_paid = db.query(Payment).filter(
                Payment.lease_id == mary_lease.id,
                Payment.reference == MARY_PRIOR_DEPOSIT_REF,
            ).first()
            if not already_paid:
                prior_payment = Payment(
                    id=str(uuid.uuid4()),
                    organization_id=org.id,
                    tenant_id=mary.id, lease_id=mary_lease.id,
                    amount=MARY_PRIOR_DEPOSIT_AMOUNT,
                    payment_method="cash",
                    payment_type="deposit",
                    reference=MARY_PRIOR_DEPOSIT_REF,
                    payment_date=today - timedelta(days=30),
                )
                db.add(prior_payment)
                db.flush()
                recompute_lease_settlement(db, mary_lease.id)
                print(f"Mary's prior deposit of KES {MARY_PRIOR_DEPOSIT_AMOUNT:,} settled.")

    # Simulate WhatsApp forwards for all 5 tenants
    created = 0
    for ref, tenant_name, phone, amount in DEMO_DATA:
        tenant = db.query(Tenant).filter(
            Tenant.organization_id == org.id,
            Tenant.full_name == tenant_name,
        ).first()
        if not tenant:
            print(f"  Skipping {tenant_name} — tenant not found in DB.")
            continue

        # Skip if a review item for this reference already exists (idempotent).
        exists = db.query(PaymentReviewItem).filter(
            PaymentReviewItem.reference == ref,
        ).first()
        if exists:
            print(f"  Skipping {tenant_name} — review item for {ref} already exists.")
            continue

        lease = db.query(Lease).filter(
            Lease.tenant_id == tenant.id, Lease.status == "active",
        ).first()

        sms_body = mpesa_sms(ref, amount)

        message = Message(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            phone_number=phone,
            direction="incoming",
            message_type="ticket",
            content=sms_body,
            status="received",
            channel="whatsapp",
            provider_message_id=f"demo_wamid_{ref}",
            tenant_id=tenant.id,
        )
        db.add(message)
        db.flush()

        review_item = PaymentReviewItem(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            source="whatsapp",
            source_message_id=message.id,
            tenant_id=tenant.id,
            lease_id=lease.id if lease else None,
            amount=amount,
            reference=ref,
            payer_phone=phone,
            payer_phone_hash=blind_index(phone),
            payer_name=tenant.full_name,
            raw_transaction=sms_body,
            extracted_reference=ref,
            extracted_amount=amount,
            message_timestamp=datetime.utcnow(),
            status="pending_review",
            flag_reason="manual_flag",
        )
        db.add(review_item)
        created += 1
        print(f"  {tenant_name}: ref {ref}, amount KES {amount:,}")

    db.commit()
    print()
    print("=" * 60)
    print(f"Simulated {created} WhatsApp forward(s).")
    print("Now upload demo-bank-statement.csv via Batch Payment Upload.")
    print("=" * 60)
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
    sys.exit(1)
finally:
    db.close()