#backend\app\services\messaging\templates.py
"""
Message templates.

These define the canonical text + parameters for every notification the
system sends. They serve two purposes:

  1) When WHATSAPP_USE_TEMPLATES=false (dev mode), we render the body
     locally with .format() and send as free-form text. This works for
     development against test numbers.

  2) When WHATSAPP_USE_TEMPLATES=true (production), the template_name
     and ordered parameter list are sent to Meta. The template must
     already be registered AND approved in Meta's WhatsApp Manager,
     with body text matching what's shown here.

When registering a template with Meta, use the template_body_meta value
as the body text (with the {{1}}, {{2}}... placeholders). Meta requires
positional parameters, not named ones, hence the param_order list.
"""

# All templates registered here. Add new ones as the system grows.

TEMPLATES = {

    # ─── Tenant invitation ───
    "tenant_invite": {
        "param_order": ["property_name", "link"],
        "template_body_freeform": (
            "Welcome to {property_name}.\n\n"
            "You've been invited to the tenant portal. "
            "Click here to join: {link}"
        ),
        "template_body_meta": (
            "Welcome to {{1}}.\n\n"
            "You've been invited to the tenant portal. "
            "Click here to join: {{2}}"
        ),
        "language_code": "en_US",
    },

    # ─── Staff (property manager / finance) invitation ───
    "staff_invite": {
        "param_order": ["org_name", "role", "link"],
        "template_body_freeform": (
            "Hi! You've been invited to join {org_name} as a {role}.\n\n"
            "Accept your invitation here: {link}"
        ),
        "template_body_meta": (
            "Hi! You've been invited to join {{1}} as a {{2}}.\n\n"
            "Accept your invitation here: {{3}}"
        ),
        "language_code": "en_US",
    },

    # ─── New lease welcome ───
    "lease_welcome": {
        "param_order": ["tenant_name", "property_name", "unit_name"],
        "template_body_freeform": (
            "Hi {tenant_name}, welcome to {property_name}!\n\n"
            "Your unit {unit_name} is ready. We're glad to have you."
        ),
        "template_body_meta": (
            "Hi {{1}}, welcome to {{2}}!\n\n"
            "Your unit {{3}} is ready. We're glad to have you."
        ),
        "language_code": "en_US",
    },

    # ─── Rent due reminder (sent T-5 days) ───
    "rent_due_reminder": {
        "param_order": ["tenant_name", "amount", "due_date"],
        "template_body_freeform": (
            "Hi {tenant_name}, your rent of KES {amount} is due on {due_date}. "
            "Please ensure payment is made on time. Thank you."
        ),
        "template_body_meta": (
            "Hi {{1}}, your rent of KES {{2}} is due on {{3}}. "
            "Please ensure payment is made on time. Thank you."
        ),
        "language_code": "en_US",
    },

    # ─── Payment receipt ───
    "payment_receipt": {
        "param_order": ["tenant_name", "amount", "date"],
        "template_body_freeform": (
            "Payment received ✔\n\n"
            "Hi {tenant_name}, we've received your payment of KES {amount} on {date}. "
            "Thank you!"
        ),
        "template_body_meta": (
            "Payment received ✔\n\n"
            "Hi {{1}}, we've received your payment of KES {{2}} on {{3}}. "
            "Thank you!"
        ),
        "language_code": "en_US",
    },

    # ─── Overdue notice ───
    "overdue_notice": {
        "param_order": ["tenant_name", "amount", "days_overdue"],
        "template_body_freeform": (
            "Hi {tenant_name}, your rent of KES {amount} is now {days_overdue} day(s) overdue. "
            "Please settle the balance as soon as possible to avoid further action."
        ),
        "template_body_meta": (
            "Hi {{1}}, your rent of KES {{2}} is now {{3}} day(s) overdue. "
            "Please settle the balance as soon as possible to avoid further action."
        ),
        "language_code": "en_US",
    },

    # ─── Ticket received confirmation ───
    "ticket_received": {
        "param_order": ["ticket_id"],
        "template_body_freeform": (
            "Your maintenance request has been received. "
            "Ticket ID: {ticket_id}\n\n"
            "We'll be in touch shortly."
        ),
        "template_body_meta": (
            "Your maintenance request has been received. "
            "Ticket ID: {{1}}\n\n"
            "We'll be in touch shortly."
        ),
        "language_code": "en_US",
    },

    # ─── Ticket assigned (tenant) ───
    # Sent when a staff member is assigned to work on the tenant's ticket.
    "ticket_assigned": {
        "param_order": ["ticket_id", "ticket_title"],
        "template_body_freeform": (
            "✅ Update on your request (Ticket {ticket_id}):\n\n"
            "{ticket_title}\n\n"
            "Your issue has been assigned and someone will be in touch soon."
        ),
        "template_body_meta": (
            "✅ Update on your request (Ticket {{1}}):\n\n"
            "{{2}}\n\n"
            "Your issue has been assigned and someone will be in touch soon."
        ),
        "language_code": "en_US",
    },

    # ─── Ticket in progress (tenant) ───
    # Sent when work actually starts on the ticket.
    "ticket_in_progress": {
        "param_order": ["ticket_id", "ticket_title"],
        "template_body_freeform": (
            "🔧 Work in progress (Ticket {ticket_id}):\n\n"
            "{ticket_title}\n\n"
            "We're actively working on your issue."
        ),
        "template_body_meta": (
            "🔧 Work in progress (Ticket {{1}}):\n\n"
            "{{2}}\n\n"
            "We're actively working on your issue."
        ),
        "language_code": "en_US",
    },

    # ─── Ticket resolved (tenant) ───
    # Sent when the issue is marked resolved. Asks tenant to confirm.
    "ticket_resolved": {
        "param_order": ["ticket_id", "ticket_title"],
        "template_body_freeform": (
            "✔ Issue resolved (Ticket {ticket_id}):\n\n"
            "{ticket_title}\n\n"
            "We've marked your issue as resolved. "
            "Please let us know if it hasn't been fixed and we'll follow up."
        ),
        "template_body_meta": (
            "✔ Issue resolved (Ticket {{1}}):\n\n"
            "{{2}}\n\n"
            "We've marked your issue as resolved. "
            "Please let us know if it hasn't been fixed and we'll follow up."
        ),
        "language_code": "en_US",
    },

    # ─── Ticket closed (tenant) ───
    "ticket_closed": {
        "param_order": ["ticket_id", "ticket_title"],
        "template_body_freeform": (
            "🎉 Ticket closed (Ticket {ticket_id}):\n\n"
            "{ticket_title}\n\n"
            "This request has been closed. Thank you for your patience!"
        ),
        "template_body_meta": (
            "🎉 Ticket closed (Ticket {{1}}):\n\n"
            "{{2}}\n\n"
            "This request has been closed. Thank you for your patience!"
        ),
        "language_code": "en_US",
    },

    # ─── Account lockout alert (Sprint 7 follow-up) ───
    # Sent to a user whose account has just been temporarily locked after
    # 5 failed login attempts. The generic 400 response to the attacker
    # gives no signal that the account was locked; this out-of-band
    # notification is how the real user finds out.
    "account_locked": {
        "param_order": ["user_email", "unlock_time"],
        "template_body_freeform": (
            "🔒 Security alert\n\n"
            "Someone tried to sign in to {user_email} and failed too many times. "
            "Your account is temporarily locked until {unlock_time}.\n\n"
            "If this wasn't you, we recommend resetting your password once the "
            "lock lifts."
        ),
        "template_body_meta": (
            "🔒 Security alert\n\n"
            "Someone tried to sign in to {{1}} and failed too many times. "
            "Your account is temporarily locked until {{2}}.\n\n"
            "If this wasn't you, we recommend resetting your password once the "
            "lock lifts."
        ),
        "language_code": "en_US",
    },
}


def render_freeform(template_name: str, variables: dict) -> str:
    """
    Render a template's free-form body with the given variables.

    Used when WHATSAPP_USE_TEMPLATES=false (dev mode).
    Raises KeyError if the template is unknown.
    Raises ValueError if any required variable is missing.
    """
    if template_name not in TEMPLATES:
        raise KeyError(f"Unknown template: {template_name}")

    tmpl = TEMPLATES[template_name]
    try:
        return tmpl["template_body_freeform"].format(**variables)
    except KeyError as e:
        raise ValueError(f"Missing variable for template '{template_name}': {e}")


def get_template_params(template_name: str, variables: dict) -> list:
    """
    Build the ordered parameter list a Meta template expects.

    Used when WHATSAPP_USE_TEMPLATES=true (production mode).
    """
    if template_name not in TEMPLATES:
        raise KeyError(f"Unknown template: {template_name}")

    tmpl = TEMPLATES[template_name]
    try:
        return [variables[k] for k in tmpl["param_order"]]
    except KeyError as e:
        raise ValueError(f"Missing variable for template '{template_name}': {e}")


def get_template_language(template_name: str) -> str:
    """Return the language code for a template."""
    if template_name not in TEMPLATES:
        raise KeyError(f"Unknown template: {template_name}")
    return TEMPLATES[template_name]["language_code"]
