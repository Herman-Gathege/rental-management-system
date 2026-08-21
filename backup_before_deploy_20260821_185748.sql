--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13 (Debian 15.13-1.pgdg130+1)
-- Dumped by pg_dump version 15.13 (Debian 15.13-1.pgdg130+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO rental_user;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.audit_logs (
    id character varying NOT NULL,
    organization_id character varying,
    user_id character varying,
    action character varying NOT NULL,
    entity_type character varying NOT NULL,
    entity_id character varying NOT NULL,
    description character varying NOT NULL,
    old_values text,
    new_values text,
    created_at timestamp without time zone,
    ip_address character varying
);


ALTER TABLE public.audit_logs OWNER TO rental_user;

--
-- Name: charges; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.charges (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    lease_id character varying NOT NULL,
    amount numeric(10,2) NOT NULL,
    due_date date NOT NULL,
    billing_month date NOT NULL,
    status character varying DEFAULT 'pending'::character varying NOT NULL,
    created_at timestamp without time zone,
    amount_paid numeric(10,2) DEFAULT '0'::numeric NOT NULL,
    charge_type character varying NOT NULL
);


ALTER TABLE public.charges OWNER TO rental_user;

--
-- Name: checklist_item_templates; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.checklist_item_templates (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    item_name character varying NOT NULL,
    sort_order integer DEFAULT 0,
    is_default boolean DEFAULT false,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone
);


ALTER TABLE public.checklist_item_templates OWNER TO rental_user;

--
-- Name: expense_attachments; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.expense_attachments (
    id character varying NOT NULL,
    expense_id character varying NOT NULL,
    filename character varying,
    file_url character varying NOT NULL,
    uploaded_by character varying,
    created_at timestamp without time zone
);


ALTER TABLE public.expense_attachments OWNER TO rental_user;

--
-- Name: expense_categories; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.expense_categories (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    name character varying NOT NULL,
    description character varying,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.expense_categories OWNER TO rental_user;

--
-- Name: expenses; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.expenses (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    property_id character varying NOT NULL,
    unit_id character varying,
    vendor_id character varying,
    category_id character varying NOT NULL,
    created_by character varying NOT NULL,
    approved_by character varying,
    title character varying NOT NULL,
    description text,
    amount numeric(12,2) NOT NULL,
    expense_date date NOT NULL,
    payment_method character varying,
    reference_number character varying,
    status character varying DEFAULT 'draft'::character varying NOT NULL,
    receipt_number character varying,
    notes text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.expenses OWNER TO rental_user;

--
-- Name: inspection_items; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.inspection_items (
    id character varying NOT NULL,
    inspection_id character varying NOT NULL,
    item_name character varying NOT NULL,
    sort_order integer DEFAULT 0,
    condition character varying,
    comments text,
    photo_urls text DEFAULT '[]'::text,
    deduction_amount numeric(12,2) DEFAULT '0'::numeric,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.inspection_items OWNER TO rental_user;

--
-- Name: inspection_notes; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.inspection_notes (
    id character varying NOT NULL,
    inspection_id character varying NOT NULL,
    user_id character varying,
    note text NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.inspection_notes OWNER TO rental_user;

--
-- Name: lease_inspections; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.lease_inspections (
    id character varying NOT NULL,
    lease_id character varying NOT NULL,
    inspection_type character varying NOT NULL,
    inspection_date date,
    inspector_user_id character varying,
    tenant_signature_data text,
    tenant_signed_name character varying,
    tenant_signed_at timestamp without time zone,
    status character varying DEFAULT 'draft'::character varying,
    total_deduction_amount numeric(12,2) DEFAULT '0'::numeric,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    deposit_held numeric(12,2),
    deposit_refunded numeric(12,2),
    deposit_shortfall numeric(12,2)
);


ALTER TABLE public.lease_inspections OWNER TO rental_user;

--
-- Name: leases; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.leases (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    unit_id character varying NOT NULL,
    tenant_id character varying NOT NULL,
    start_date date NOT NULL,
    end_date date,
    rent_amount numeric(12,2) NOT NULL,
    deposit_amount numeric(12,2),
    billing_day integer DEFAULT 1,
    status character varying DEFAULT 'active'::character varying,
    created_at timestamp without time zone,
    move_in_date date,
    signed_on_behalf_of character varying,
    signed_lease_urls json,
    custom_fields json
);


ALTER TABLE public.leases OWNER TO rental_user;

--
-- Name: messages; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.messages (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    phone_number character varying NOT NULL,
    direction character varying NOT NULL,
    message_type character varying DEFAULT 'notification'::character varying NOT NULL,
    content text NOT NULL,
    template_name character varying,
    status character varying DEFAULT 'queued'::character varying NOT NULL,
    provider_message_id character varying,
    error_message text,
    channel character varying DEFAULT 'whatsapp'::character varying NOT NULL,
    triggered_by_user_id character varying,
    tenant_id character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    ticket_id character varying
);


ALTER TABLE public.messages OWNER TO rental_user;

--
-- Name: notification_preferences; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.notification_preferences (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    user_id character varying NOT NULL,
    email_enabled boolean DEFAULT false NOT NULL,
    whatsapp_enabled boolean DEFAULT true NOT NULL,
    sms_enabled boolean DEFAULT false NOT NULL,
    in_app_enabled boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.notification_preferences OWNER TO rental_user;

--
-- Name: notifications; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.notifications (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    user_id character varying NOT NULL,
    title character varying NOT NULL,
    body text,
    notification_type character varying NOT NULL,
    is_read boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.notifications OWNER TO rental_user;

--
-- Name: organization_invitations; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.organization_invitations (
    id character varying NOT NULL,
    email character varying NOT NULL,
    role_id character varying,
    organization_id character varying,
    token character varying NOT NULL,
    status character varying,
    created_at timestamp without time zone,
    phone character varying
);


ALTER TABLE public.organization_invitations OWNER TO rental_user;

--
-- Name: organization_members; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.organization_members (
    id character varying NOT NULL,
    user_id character varying,
    organization_id character varying,
    role_id character varying,
    created_at timestamp without time zone
);


ALTER TABLE public.organization_members OWNER TO rental_user;

--
-- Name: organizations; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.organizations (
    id character varying NOT NULL,
    name character varying NOT NULL,
    owner_id character varying NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.organizations OWNER TO rental_user;

--
-- Name: otp_verifications; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.otp_verifications (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    purpose character varying DEFAULT 'phone_verification'::character varying NOT NULL,
    phone character varying,
    code_hash character varying NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    attempts integer DEFAULT 0 NOT NULL,
    last_sent_at timestamp without time zone,
    consumed_at timestamp without time zone,
    created_at timestamp without time zone
);


ALTER TABLE public.otp_verifications OWNER TO rental_user;

--
-- Name: password_history; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.password_history (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    password_hash character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.password_history OWNER TO rental_user;

--
-- Name: payment_review_items; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.payment_review_items (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    amount numeric(10,2) NOT NULL,
    payment_date date,
    reference character varying,
    payer_phone character varying,
    payer_name character varying,
    raw_transaction text,
    tenant_id character varying,
    lease_id character varying,
    status character varying DEFAULT 'pending_review'::character varying NOT NULL,
    flag_reason character varying NOT NULL,
    notes text,
    resolved_at timestamp without time zone,
    resolved_by_user_id character varying,
    resolution_payment_id character varying,
    rejection_reason character varying,
    created_at timestamp without time zone DEFAULT now(),
    created_by_user_id character varying,
    source character varying,
    source_message_id character varying,
    extracted_reference character varying,
    extracted_amount numeric(10,2),
    message_timestamp timestamp without time zone,
    payer_phone_hash character varying(64)
);


ALTER TABLE public.payment_review_items OWNER TO rental_user;

--
-- Name: payments; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.payments (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    tenant_id character varying NOT NULL,
    lease_id character varying NOT NULL,
    amount numeric(10,2) NOT NULL,
    payment_method character varying DEFAULT 'cash'::character varying NOT NULL,
    reference character varying,
    payment_date date NOT NULL,
    created_at timestamp without time zone,
    payment_type character varying NOT NULL
);


ALTER TABLE public.payments OWNER TO rental_user;

--
-- Name: properties; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.properties (
    id character varying NOT NULL,
    name character varying NOT NULL,
    address character varying NOT NULL,
    city character varying NOT NULL,
    country character varying NOT NULL,
    organization_id character varying,
    created_at timestamp without time zone
);


ALTER TABLE public.properties OWNER TO rental_user;

--
-- Name: property_finance_managers; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.property_finance_managers (
    id character varying NOT NULL,
    property_id character varying,
    user_id character varying
);


ALTER TABLE public.property_finance_managers OWNER TO rental_user;

--
-- Name: property_managers; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.property_managers (
    id character varying NOT NULL,
    property_id character varying,
    user_id character varying
);


ALTER TABLE public.property_managers OWNER TO rental_user;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.roles (
    id character varying NOT NULL,
    name character varying NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.roles OWNER TO rental_user;

--
-- Name: tenant_documents; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.tenant_documents (
    id character varying NOT NULL,
    tenant_id character varying NOT NULL,
    document_type character varying NOT NULL,
    file_url character varying NOT NULL,
    original_filename character varying,
    uploaded_by_user_id character varying,
    uploaded_at timestamp without time zone
);


ALTER TABLE public.tenant_documents OWNER TO rental_user;

--
-- Name: tenants; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.tenants (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    full_name character varying NOT NULL,
    email character varying,
    phone character varying NOT NULL,
    id_number character varying,
    emergency_contact character varying,
    created_at timestamp without time zone,
    alternative_phone character varying,
    next_of_kin_name character varying,
    next_of_kin_relationship character varying,
    next_of_kin_phone character varying,
    next_of_kin_alt_phone character varying,
    next_of_kin_email character varying,
    employer_name character varying,
    employer_location character varying,
    employer_phone character varying,
    employer_email character varying,
    user_id character varying,
    phone_hash character varying(64),
    alternative_phone_hash character varying(64),
    email_hash character varying(64),
    id_number_hash character varying(64)
);


ALTER TABLE public.tenants OWNER TO rental_user;

--
-- Name: ticket_assignments; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.ticket_assignments (
    id character varying NOT NULL,
    ticket_id character varying NOT NULL,
    assigned_from character varying,
    assigned_to character varying,
    reason text,
    assigned_at timestamp without time zone
);


ALTER TABLE public.ticket_assignments OWNER TO rental_user;

--
-- Name: ticket_attachments; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.ticket_attachments (
    id character varying NOT NULL,
    ticket_id character varying NOT NULL,
    uploaded_by character varying,
    file_name character varying,
    file_url character varying NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.ticket_attachments OWNER TO rental_user;

--
-- Name: ticket_messages; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.ticket_messages (
    id character varying NOT NULL,
    ticket_id character varying NOT NULL,
    sender_id character varying,
    message text NOT NULL,
    is_internal boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone,
    recipient_id character varying
);


ALTER TABLE public.ticket_messages OWNER TO rental_user;

--
-- Name: tickets; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.tickets (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    tenant_id character varying,
    source_phone character varying,
    source_message_id character varying,
    description text NOT NULL,
    status character varying DEFAULT 'open'::character varying NOT NULL,
    source character varying DEFAULT 'whatsapp'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    property_id character varying,
    unit_id character varying,
    created_by character varying,
    assigned_to character varying,
    priority character varying DEFAULT 'medium'::character varying NOT NULL,
    category character varying,
    opened_at timestamp without time zone,
    resolved_at timestamp without time zone,
    closed_at timestamp without time zone,
    title character varying NOT NULL
);


ALTER TABLE public.tickets OWNER TO rental_user;

--
-- Name: units; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.units (
    id character varying NOT NULL,
    property_id character varying NOT NULL,
    name character varying NOT NULL,
    description character varying,
    bedrooms integer,
    bathrooms integer,
    size_sqm double precision,
    rent_amount numeric(10,2) NOT NULL,
    is_active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.units OWNER TO rental_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.users (
    id character varying NOT NULL,
    email character varying NOT NULL,
    password_hash character varying NOT NULL,
    is_active boolean,
    refresh_token character varying,
    reset_token character varying,
    reset_token_expiry timestamp without time zone,
    role_id character varying,
    full_name character varying,
    phone character varying,
    phone_verified boolean NOT NULL,
    failed_login_count integer DEFAULT 0 NOT NULL,
    locked_until timestamp without time zone
);


ALTER TABLE public.users OWNER TO rental_user;

--
-- Name: vendors; Type: TABLE; Schema: public; Owner: rental_user
--

CREATE TABLE public.vendors (
    id character varying NOT NULL,
    organization_id character varying NOT NULL,
    vendor_name character varying NOT NULL,
    contact_person character varying,
    phone character varying,
    email character varying,
    kra_pin character varying,
    address character varying,
    notes character varying,
    created_at timestamp without time zone
);


ALTER TABLE public.vendors OWNER TO rental_user;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.alembic_version (version_num) FROM stdin;
a1b2c3d4e5f6
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.audit_logs (id, organization_id, user_id, action, entity_type, entity_id, description, old_values, new_values, created_at, ip_address) FROM stdin;
58d3147e-7807-4807-9372-c3750a8fa523	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	user	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	New account registered: remingtonherman7@gmail.com	\N	\N	2026-07-18 07:11:49.943917	172.18.0.1
1ff69d1f-e20e-4cf8-8e08-a47271cee993	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	login	user	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	User logged in: remingtonherman7@gmail.com	\N	\N	2026-07-18 07:11:50.921204	172.18.0.1
c554739d-a5ef-4d2b-a580-0358743de31d	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	property	6eaa0fc0-4a8e-47e1-89a6-3a145ff5b1af	Created property: Wellness One Heights	\N	{"name": "Wellness One Heights", "address": "00100 177", "city": "Embakasi", "country": "Kenya"}	2026-07-18 07:13:40.74682	\N
97c232f1-ff11-4a3f-9e12-b0b924758c52	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	property	c711e652-6b53-454f-a108-93947b0c227f	Created property: Sunset Homes	\N	{"name": "Sunset Homes", "address": "00100 177", "city": "Syokimau", "country": "Kenya"}	2026-07-18 07:14:20.995733	\N
da9a8061-4fcf-40aa-bed6-64c9a199b14b	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	unit	c463840b-a13c-41bf-baaf-bb0e69b848c2	Created unit: A1 in Wellness One Heights	\N	{"name": "A1", "rent_amount": 20000.0}	2026-07-18 07:15:08.556471	\N
d1009609-576d-4de4-a513-8e9a3e9674a9	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	tenant	8ab4decf-2b05-4862-8ea8-0e6325408638	Created tenant: Herman Remington	\N	{"full_name": "Herman Remington", "phone": "0725325915", "email": "remingtonherman7@gmail.com"}	2026-07-18 07:16:10.800652	\N
53bc652f-0ff4-4f57-9321-32cbb4d4231c	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	lease	1f1b5410-9b24-4ba9-aad8-77679b7199a0	Created lease: Herman Remington → A1	\N	{"tenant": "Herman Remington", "unit": "A1", "rent_amount": 20000.0, "deposit_amount": 20000.0, "start_date": "2026-07-19", "auto_created_inspection_id": "005f18c5-ee78-44d7-af5c-39d44e7c5cd5"}	2026-07-18 07:17:10.190555	\N
e7b229fa-11cb-4f3a-b89a-4e9240eb5bd9	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	billing	charge	batch	Generated 1 monthly charges for 2026-07-01	\N	\N	2026-07-18 07:19:05.932009	\N
4ece35b5-6d76-410e-8108-76553a4f77c0	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	payment	payment	5d3095d3-3b81-421c-86a8-d5de9fbe05b0	Rent payment of 20000.0 recorded for Herman Remington via mpesa	\N	{"amount": 20000.0, "payment_method": "mpesa", "payment_type": "rent", "reference": "asd21233", "tenant": "Herman Remington"}	2026-07-18 07:19:36.98013	\N
3a11fc98-98db-43ef-9d18-0bed3bf83a21	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	payment	payment	7e850f5d-7450-4a52-866b-bdd458295f28	Deposit payment of 20000.0 recorded for Herman Remington via mpesa	\N	{"amount": 20000.0, "payment_method": "mpesa", "payment_type": "deposit", "reference": "34eewfwe", "tenant": "Herman Remington"}	2026-07-18 07:19:59.826726	\N
b408281c-3aab-4d83-b4e6-4c031edc0748	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	expense_category	d731cd99-546f-458b-ae4b-d3b05f9160b4	Created expense category: swimming pool	\N	{"name": "swimming pool"}	2026-07-18 07:29:42.751067	\N
836c553c-1714-46fe-ab9b-073d2fa1dc33	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	vendor	bb32b74b-6ae7-40d0-93de-0a7c34f45a1a	Created vendor: green waste collection	\N	{"vendor_name": "green waste collection"}	2026-07-18 07:30:51.964624	\N
edeffb56-e65e-4b02-bb64-ff5804d7ef64	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	expense	22e48dcb-a994-43c2-b042-398310ea79c9	Created expense: waste collectors	\N	{"title": "waste collectors", "amount": 1000.0, "property_id": "6eaa0fc0-4a8e-47e1-89a6-3a145ff5b1af", "category_id": "bdf76b07-1c61-4597-b8df-0ff112f4dd38", "status": "draft"}	2026-07-18 07:32:14.642324	\N
d00f16bf-c7f6-4a65-afb4-9cc66ac93751	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	expense_attachment	7d95767e-2365-4ee3-afcd-5a1b7814b8b7	Attached a receipt to expense: waste collectors	\N	{"filename": "_.jpeg"}	2026-07-18 07:32:14.815975	\N
5aaca759-616a-4aa2-86aa-613c5440d9df	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	submit	expense	22e48dcb-a994-43c2-b042-398310ea79c9	Submitted expense for approval: waste collectors	{"status": "draft"}	{"status": "submitted"}	2026-07-18 07:32:28.594051	\N
e7ac45f8-f4d4-42b7-93b2-7f24e0b749d9	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	approve	expense	22e48dcb-a994-43c2-b042-398310ea79c9	Approved expense: waste collectors	{"status": "submitted"}	{"status": "approved"}	2026-07-18 07:33:13.82592	\N
4f1fce76-5f03-4fcf-ad50-b972d06ccf39	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	pay	expense	22e48dcb-a994-43c2-b042-398310ea79c9	Marked expense paid: waste collectors	{"status": "approved"}	{"status": "paid"}	2026-07-18 07:33:17.547829	\N
d9aadb1f-1a4b-49fa-9f33-4e12b9ed2387	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	update	checklist_item	batch	Reset checklist to defaults (13 items)	\N	\N	2026-07-18 07:36:28.216477	\N
6c471516-1d16-4e93-b8fd-32cff8193414	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	update	inspection	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Signed move_in inspection for lease 1f1b5410-9b24-4ba9-aad8-77679b7199a0	\N	{"tenant_signed_name": "anne waithaka", "type": "move_in", "lease_terminated": false}	2026-07-18 07:38:00.647552	\N
5f01d6ef-5439-4e31-87ee-a28b5e430052	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	checklist_item	b5604767-0d82-470c-913f-925d0da3c60f	Added checklist item: swimming pool	\N	{"item_name": "swimming pool"}	2026-07-18 07:38:27.190839	\N
7c5af570-63fe-4574-9514-f6e91ffbf4fa	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	inspection	6c23883d-c153-48da-a9bd-1b0856f0078d	Initiated move-out inspection for lease 1f1b5410-9b24-4ba9-aad8-77679b7199a0	\N	\N	2026-07-18 07:38:38.480633	\N
8a76073e-47df-4d82-8248-b5330482af15	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	unit	0605af17-ffd0-4741-a890-aa40ba08fd30	Created unit: A01 in Sunset Homes	\N	{"name": "A01", "rent_amount": 11000.0}	2026-07-18 07:44:03.384076	\N
9f81c146-8d3f-4516-bb4c-d3c2fa6a13a6	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	tenant	72235713-77ba-4f6c-b9d1-05cfd9335224	Created tenant: mark volt	\N	{"full_name": "mark volt", "phone": "0732808098", "email": "mark@gmail.com"}	2026-07-18 07:46:23.564614	\N
bf3611da-2457-4912-987a-f94cdeffcbae	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	tenant_document	999e1048-0509-49a8-a854-8ce3f256fede	Uploaded national_id_front for tenant mark volt	\N	{"filename": "_.jpeg", "document_type": "national_id_front"}	2026-07-18 07:46:23.656414	\N
e9dba838-a305-4d84-9eb8-2f7f61bdd940	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	lease	91886e76-0ac5-4e2f-ae95-93d201c7ffc6	Created lease: mark volt → A01	\N	{"tenant": "mark volt", "unit": "A01", "rent_amount": 11000.0, "deposit_amount": 11000.0, "start_date": "2026-07-19", "auto_created_inspection_id": "f9b9b66a-4f58-4d47-adeb-a342c94725db"}	2026-07-18 07:47:12.853499	\N
43e4951b-5c54-423a-9df0-7c848b5407f5	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	invite	invitation	84cf09f1-5c5d-40b0-b707-4a6e2c6d776c	Invited mark@gmail.com as TENANT	\N	{"email": "mark@gmail.com", "role": "TENANT", "phone_provided": true}	2026-07-18 07:47:33.367575	172.18.0.1
e226e719-d919-44e5-ba23-6e22787bdaef	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	invite	invitation	6282cf9c-cf5e-4c79-9a23-90cb892faefc	Invited 1mark@gmail.com as TENANT	\N	{"email": "1mark@gmail.com", "role": "TENANT", "phone_provided": true}	2026-07-18 07:52:12.274397	172.18.0.1
8f1cd7be-b9bc-4422-b0cc-5d01fe5e78e2	a577ea7c-4f39-4e3a-888e-22ed4705304b	8fbc3c86-e87c-48f8-a212-3a8662ea3340	create	user	8fbc3c86-e87c-48f8-a212-3a8662ea3340	New account registered via invite: 1mark@gmail.com	\N	{"email": "1mark@gmail.com", "role": "TENANT"}	2026-07-18 07:53:28.532388	172.18.0.1
7688ee6d-88ee-4621-9021-dc8bea4fb060	a577ea7c-4f39-4e3a-888e-22ed4705304b	8fbc3c86-e87c-48f8-a212-3a8662ea3340	login	user	8fbc3c86-e87c-48f8-a212-3a8662ea3340	User logged in: 1mark@gmail.com	\N	\N	2026-07-18 07:53:45.491909	172.18.0.1
fbe99c3d-8f22-4b8e-b98b-c37b3ec68736	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	unit	218b7818-10a5-4701-9dc9-d523327f0f1c	Created unit: B1 in Wellness One Heights	\N	{"name": "B1", "rent_amount": 16000.0}	2026-07-18 07:54:40.924958	\N
336b0c1f-5e94-42f5-bedc-c43155025ab6	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	tenant	def8f38c-4ece-4ea0-84aa-1bb3ca2a56b9	Created tenant: mark 1	\N	{"full_name": "mark 1", "phone": "0725325876", "email": "1mark@gmail.com"}	2026-07-18 07:55:21.157329	\N
0c8aa0a1-ffb9-4de8-96d7-db7ebda8bc4e	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	lease	660b879e-a048-43a1-98e8-68d74725bbe4	Created lease: mark 1 → B1	\N	{"tenant": "mark 1", "unit": "B1", "rent_amount": 16000.0, "deposit_amount": 16000.0, "start_date": "2026-07-19", "auto_created_inspection_id": "8e1f553b-8aee-4075-9089-f6e4fbb05057"}	2026-07-18 07:55:44.365918	\N
62fefab1-92e8-4a05-a2ec-84caf911c502	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	update	inspection	8e1f553b-8aee-4075-9089-f6e4fbb05057	Signed move_in inspection for lease 660b879e-a048-43a1-98e8-68d74725bbe4	\N	{"tenant_signed_name": "1 mark", "type": "move_in", "lease_terminated": false}	2026-07-18 07:56:40.228009	\N
b056e30b-ae84-468b-86b5-c2ff483ca6d5	a577ea7c-4f39-4e3a-888e-22ed4705304b	8fbc3c86-e87c-48f8-a212-3a8662ea3340	login	user	8fbc3c86-e87c-48f8-a212-3a8662ea3340	User logged in: 1mark@gmail.com	\N	\N	2026-07-18 07:57:18.870181	172.18.0.1
760f204d-0eb1-41f8-99c7-05f279ab3919	a577ea7c-4f39-4e3a-888e-22ed4705304b	8fbc3c86-e87c-48f8-a212-3a8662ea3340	create	ticket	3023bcf9-f40c-45e6-a438-395f0b2b9ed8	Ticket created: Kitchen Tap	\N	\N	2026-07-18 07:58:29.11682	\N
d084a259-ebca-4a54-9345-adc9bdf63944	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	ticket_message	8d4a552e-b1dc-4b94-85e0-582489fb3cf9	Message added to ticket 3023bcf9	\N	\N	2026-07-18 07:59:19.552668	\N
d9d98e73-deda-4111-92e1-ec1a206514fa	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	ticket_message	2a258b40-f527-4ed4-8971-a1d43d1c4900	[Internal] Message added to ticket 3023bcf9	\N	\N	2026-07-18 07:59:58.322167	\N
e62c8571-3854-4789-aa62-533c1b2b2145	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	login	user	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	User logged in: remingtonherman7@gmail.com	\N	\N	2026-07-20 05:17:33.906315	172.18.0.1
a87b1a3d-5b1a-4b9f-bf79-95129333557f	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	billing	charge	batch	Generated 2 monthly charges for 2026-07-01	\N	\N	2026-07-20 05:23:59.641778	\N
8d2e4ff9-ebe4-4ea3-956e-fe84884893bf	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	login	user	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	User logged in: remingtonherman7@gmail.com	\N	\N	2026-07-20 06:26:33.77028	172.18.0.1
f1a75037-639e-469c-8a1b-06dabca5669c	a577ea7c-4f39-4e3a-888e-22ed4705304b	8fbc3c86-e87c-48f8-a212-3a8662ea3340	login	user	8fbc3c86-e87c-48f8-a212-3a8662ea3340	User logged in: 1mark@gmail.com	\N	\N	2026-07-20 06:29:00.685496	172.18.0.1
ce8e5273-ea5a-4026-9ab3-a33cf7ab3fea	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	login	user	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	User logged in: remingtonherman7@gmail.com	\N	\N	2026-07-23 06:50:53.385361	172.18.0.1
ebf4abb2-66bb-4824-ae61-69e7e9cc9d87	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	login	user	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	User logged in: remingtonherman7@gmail.com	\N	\N	2026-07-23 06:50:55.858907	172.18.0.1
ea10c941-bef9-481d-ad93-38cb6281d834	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	payment	payment	d83208f6-7b98-401b-b266-04168c8ca9dd	Batch payment of 26000.0 recorded for Herman Remington via mpesa (ref UDTQS2OHFR)	\N	{"amount": 26000.0, "payment_method": "mpesa", "reference": "UDTQS2OHFR", "tenant": "Herman Remington", "batch": true}	2026-07-23 06:54:56.371172	\N
82a7a0ad-034f-4f15-bb8c-23c52eac2d66	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	payment	payment	ed1e7794-62d4-4de8-9a56-7f26e95249af	Batch payment of 15500.0 recorded for Herman Remington via mpesa (ref UDTQS2OHG1)	\N	{"amount": 15500.0, "payment_method": "mpesa", "reference": "UDTQS2OHG1", "tenant": "Herman Remington", "batch": true}	2026-07-23 06:54:56.424092	\N
2f0a6698-926f-4f83-ae30-084e0a6129e8	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	save_for_review	payment_review	18d935af-59cd-400b-8a19-c6eae4429f06	Saved 1 payment(s) for later review (skipped 0)	\N	{"saved": 1, "skipped": 0}	2026-07-23 06:55:00.679939	\N
fc168117-5c7e-4a9f-966a-e56573c9aa6c	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	payment	payment	539c353b-c76a-4572-be8d-863b42b7da52	Rent payment of 32000.0 recorded for Herman Remington via mpesa (from review queue, ref UDTQS2OHG5)	\N	{"amount": 32000.0, "payment_method": "mpesa", "payment_type": "rent", "reference": "UDTQS2OHG5", "tenant": "Herman Remington", "review_item_id": "3d2243df-bc1f-43f2-916a-2b4160cc4330"}	2026-07-23 06:56:32.108134	\N
f6f9218d-663a-4df6-8323-01dfeacb927f	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	apply_review	payment_review	3d2243df-bc1f-43f2-916a-2b4160cc4330	Applied review item — created payment 539c353b-c76a-4572-be8d-863b42b7da52	\N	{"payment_id": "539c353b-c76a-4572-be8d-863b42b7da52", "amount": 32000.0, "tenant_id": "8ab4decf-2b05-4862-8ea8-0e6325408638", "lease_id": "1f1b5410-9b24-4ba9-aad8-77679b7199a0"}	2026-07-23 06:56:32.108141	\N
e36a9b1f-dc53-410d-b546-db77ce1032e3	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	bulk_create	property	25d16482-651c-46ae-9eef-09630b3d7a14	Bulk property upload: 2 imported, 0 skipped, 2 total	\N	{"imported_count": 2, "skipped_count": 0, "total_rows": 2}	2026-07-23 06:59:54.595212	\N
caa74a24-fd03-4237-971f-e1a7d64d4b1b	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	bulk_create	unit	d4328102-1d83-437f-bb00-b3f7c65d6a29	Bulk unit upload: 3 imported, 0 skipped, 3 total	\N	{"imported_count": 3, "skipped_count": 0, "total_rows": 3}	2026-07-23 07:00:45.401699	\N
bc907d43-8f5b-4854-9726-e17050c3e59f	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	login	user	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	User logged in: remingtonherman7@gmail.com	\N	\N	2026-07-24 05:34:52.521037	172.18.0.1
b01b733a-5fab-43f7-a119-e614ee9cf3a5	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	invite	invitation	2a6ab4a8-63ae-42ec-be0a-a42db564bb8a	Invited sharon@gmail.com as PROPERTY_MANAGER	\N	{"email": "sharon@gmail.com", "role": "PROPERTY_MANAGER", "phone_provided": true}	2026-07-24 06:56:44.961178	172.18.0.1
09886d6a-4dbb-4e03-8cc5-d694567080fa	\N	\N	failed_login	user	sharon@gmail.com	Failed login attempt (unknown email): sharon@gmail.com	\N	\N	2026-07-24 06:58:20.834081	172.18.0.1
f507b44a-9d26-43cd-ac9c-437c2a8c12e9	\N	\N	failed_login	user	sharon@gmail.com	Failed login attempt (unknown email): sharon@gmail.com	\N	\N	2026-07-24 06:58:34.305597	172.18.0.1
c5efecf4-d1f4-4039-9f34-add78e7c03d4	\N	\N	failed_login	user	sharon@gmail.com	Failed login attempt (unknown email): sharon@gmail.com	\N	\N	2026-07-24 06:59:23.660077	172.18.0.1
64e922a9-5451-43bb-a728-fc9c1fd253b1	a577ea7c-4f39-4e3a-888e-22ed4705304b	95c955b7-a435-4bd7-b346-32d4d93277d0	create	user	95c955b7-a435-4bd7-b346-32d4d93277d0	New account registered via invite: sharon@gmail.com	\N	{"email": "sharon@gmail.com", "role": "PROPERTY_MANAGER"}	2026-07-24 07:00:37.889007	172.18.0.1
c66ea85a-8b77-417d-b6de-662e63df76d3	a577ea7c-4f39-4e3a-888e-22ed4705304b	95c955b7-a435-4bd7-b346-32d4d93277d0	failed_login	user	95c955b7-a435-4bd7-b346-32d4d93277d0	Failed login attempt (invalid password): sharon@gmail.com	\N	\N	2026-07-24 07:00:51.702279	172.18.0.1
0ff5850b-7fd4-4da4-b45a-da2f2712ff81	a577ea7c-4f39-4e3a-888e-22ed4705304b	95c955b7-a435-4bd7-b346-32d4d93277d0	login	user	95c955b7-a435-4bd7-b346-32d4d93277d0	User logged in: sharon@gmail.com	\N	\N	2026-07-24 07:01:01.021535	172.18.0.1
a19ce07b-cb13-4a40-95d1-935b0885ec58	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	tenant	cedbb0ae-6d00-4b5e-a938-11162db1a492	Created tenant: sharon kendi	\N	{"full_name": "sharon kendi", "phone": "0759564080", "email": "sharon@gmail.com"}	2026-07-24 07:02:10.647594	\N
e1b4a9ed-b87a-4b25-97df-02d28e5a1c44	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	update	unit	c90fe656-0c5a-4b35-9e5f-0151f8f442c5	Updated unit: A1	{"name": "A1", "rent_amount": 35000.0, "description": "Corner unit, ground floor", "bedrooms": 2, "bathrooms": 1}	{"name": "A1", "description": "Corner unit, ground floor", "bedrooms": 2, "bathrooms": 1, "size_sqm": 65.5, "rent_amount": 35000.0, "is_active": true}	2026-07-24 07:02:29.18082	\N
3d21e565-05fd-445b-9cc6-296ef65ad6de	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	lease	9f655e89-df15-471e-8b94-0c2fc900936b	Created lease: sharon kendi → A1	\N	{"tenant": "sharon kendi", "unit": "A1", "rent_amount": 35000.0, "deposit_amount": 35000.0, "start_date": "2026-07-25", "auto_created_inspection_id": "6030079d-b87c-491c-a58e-b26314df453d"}	2026-07-24 07:02:58.39362	\N
80870d6e-1c3b-4f92-8917-d5ba559403ac	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	update	inspection	6030079d-b87c-491c-a58e-b26314df453d	Signed move_in inspection for lease 9f655e89-df15-471e-8b94-0c2fc900936b	\N	{"tenant_signed_name": "sharon kendi", "type": "move_in", "lease_terminated": false}	2026-07-24 07:04:57.671298	\N
d0669c0c-fb81-47e8-aeca-6be090ecca85	a577ea7c-4f39-4e3a-888e-22ed4705304b	95c955b7-a435-4bd7-b346-32d4d93277d0	login	user	95c955b7-a435-4bd7-b346-32d4d93277d0	User logged in: sharon@gmail.com	\N	\N	2026-07-24 07:05:53.972939	172.18.0.1
3456425c-d2d5-42f3-adda-5359639e07ab	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	create	property_manager	2c505bab-da6f-4502-84c6-ffa2c00df09a	Assigned sharon@gmail.com to Wellness One Heights	\N	\N	2026-07-24 07:12:04.245545	\N
4b387919-3e06-426b-9c9e-5347e0588edb	a577ea7c-4f39-4e3a-888e-22ed4705304b	8fbc3c86-e87c-48f8-a212-3a8662ea3340	login	user	8fbc3c86-e87c-48f8-a212-3a8662ea3340	User logged in: 1mark@gmail.com	\N	\N	2026-07-24 07:14:10.786202	172.18.0.1
4a6dbc88-8dcf-4cc1-a32e-56bf41223c3f	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	billing	charge	batch	Generated 1 monthly charges for 2026-07-01	\N	\N	2026-07-24 07:14:36.726774	\N
3a44ccde-848a-4e2c-a7ff-6774c72afc2f	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	update	unit	c463840b-a13c-41bf-baaf-bb0e69b848c2	Updated unit: A1	{"name": "A1", "rent_amount": 20000.0, "description": "First floor", "bedrooms": 2, "bathrooms": 2}	{"name": "A1", "description": "First floor", "bedrooms": 2, "bathrooms": 2, "size_sqm": 400.0, "rent_amount": 25000.0, "is_active": true}	2026-07-24 07:19:26.999928	\N
7563ca23-a0fa-4bdc-89b9-f064ee18a3e6	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	terminate	lease	1f1b5410-9b24-4ba9-aad8-77679b7199a0	Lease terminated via signed move-out inspection	{"status": "active"}	{"status": "terminated"}	2026-07-24 07:42:12.184543	\N
a35e3e91-588e-4e51-b664-89d80c7441a8	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	update	inspection	6c23883d-c153-48da-a9bd-1b0856f0078d	Signed move_out inspection for lease 1f1b5410-9b24-4ba9-aad8-77679b7199a0 — lease terminated	\N	{"tenant_signed_name": "HERMAN", "type": "move_out", "lease_terminated": true}	2026-07-24 07:42:12.184559	\N
\.


--
-- Data for Name: charges; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.charges (id, organization_id, lease_id, amount, due_date, billing_month, status, created_at, amount_paid, charge_type) FROM stdin;
8cb52945-af11-477c-9e3b-603c775ca46a	a577ea7c-4f39-4e3a-888e-22ed4705304b	1f1b5410-9b24-4ba9-aad8-77679b7199a0	20000.00	2026-07-01	2026-07-01	paid	2026-07-18 07:19:05.912803	20000.00	rent
522d1250-ca58-4f81-acef-696353745d09	a577ea7c-4f39-4e3a-888e-22ed4705304b	1f1b5410-9b24-4ba9-aad8-77679b7199a0	20000.00	2026-07-18	2026-07-18	paid	2026-07-18 07:17:10.056847	20000.00	deposit
49e3a3e7-0c8e-404f-8f66-2808ba87a4bc	a577ea7c-4f39-4e3a-888e-22ed4705304b	660b879e-a048-43a1-98e8-68d74725bbe4	16000.00	2026-07-18	2026-07-18	overdue	2026-07-18 07:55:44.345929	0.00	deposit
f5fc8dda-3cbd-48a4-8aca-80544da71bdb	a577ea7c-4f39-4e3a-888e-22ed4705304b	91886e76-0ac5-4e2f-ae95-93d201c7ffc6	11000.00	2026-07-18	2026-07-18	overdue	2026-07-18 07:47:12.836478	0.00	deposit
03ce3ecb-8e72-4496-b4f7-b8aaef355b03	a577ea7c-4f39-4e3a-888e-22ed4705304b	660b879e-a048-43a1-98e8-68d74725bbe4	16000.00	2026-07-01	2026-07-01	overdue	2026-07-20 05:23:59.573404	0.00	rent
ad84f44d-1ae8-42e6-9269-176030295e0d	a577ea7c-4f39-4e3a-888e-22ed4705304b	91886e76-0ac5-4e2f-ae95-93d201c7ffc6	11000.00	2026-07-01	2026-07-01	overdue	2026-07-20 05:23:59.573393	0.00	rent
cca25f50-144b-4dfd-a80f-08066ede6299	a577ea7c-4f39-4e3a-888e-22ed4705304b	9f655e89-df15-471e-8b94-0c2fc900936b	35000.00	2026-07-24	2026-07-24	pending	2026-07-24 07:02:58.298294	0.00	deposit
b9ba0123-67f6-44b4-a378-234cf3138424	a577ea7c-4f39-4e3a-888e-22ed4705304b	9f655e89-df15-471e-8b94-0c2fc900936b	35000.00	2026-07-01	2026-07-01	overdue	2026-07-24 07:14:36.709121	0.00	rent
\.


--
-- Data for Name: checklist_item_templates; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.checklist_item_templates (id, organization_id, item_name, sort_order, is_default, is_active, created_at) FROM stdin;
30d9bb01-b60f-45ee-8cb4-268c258a42c0	a577ea7c-4f39-4e3a-888e-22ed4705304b	Doors, windows, glass, handles, hinges, and locks	0	t	t	2026-07-18 07:36:28.220807
c83eb88e-cfcf-4537-8cb1-586edadd84d7	a577ea7c-4f39-4e3a-888e-22ed4705304b	Floor finishes (tiles/terrazzo)	1	t	t	2026-07-18 07:36:28.220812
3395b065-c6ba-4270-82ac-28ad666a27ef	a577ea7c-4f39-4e3a-888e-22ed4705304b	Walls and paint finish	2	t	t	2026-07-18 07:36:28.220814
b95385ad-eced-4e52-9a85-3e330719ac03	a577ea7c-4f39-4e3a-888e-22ed4705304b	Door locks and keys issued (list keys)	3	t	t	2026-07-18 07:36:28.220815
d723c996-2af0-4e29-8e3e-2534f8ace4a8	a577ea7c-4f39-4e3a-888e-22ed4705304b	Electricity switches, sockets, and light fittings	4	t	t	2026-07-18 07:36:28.220816
b2f69f5d-bb27-4bc8-ad0c-27d538e55566	a577ea7c-4f39-4e3a-888e-22ed4705304b	Water taps and plumbing visible fittings (note any defects/leaks)	5	t	t	2026-07-18 07:36:28.220818
d68398da-20f4-43e5-8303-62fd9a768b5e	a577ea7c-4f39-4e3a-888e-22ed4705304b	Hot water heater / shower	6	t	t	2026-07-18 07:36:28.221035
02e34882-f20f-4ad3-98e1-889ea7e30b8f	a577ea7c-4f39-4e3a-888e-22ed4705304b	Sinks and drain points (note any defects/leaks)	7	t	t	2026-07-18 07:36:28.221038
2f0ac73f-f5cf-456c-8b9e-dfcf928b93a8	a577ea7c-4f39-4e3a-888e-22ed4705304b	Kitchen cabinets/cupboards, drawers, and shelves	8	t	t	2026-07-18 07:36:28.22104
9add8825-00b4-441a-ab55-a4979d5139e8	a577ea7c-4f39-4e3a-888e-22ed4705304b	Bedroom wardrobes, drawers, and shelves	9	t	t	2026-07-18 07:36:28.221041
32994f36-8842-45eb-84af-74e3154de501	a577ea7c-4f39-4e3a-888e-22ed4705304b	Bathroom and bedroom mirrors	10	t	t	2026-07-18 07:36:28.221042
3ad435a9-eb27-47c9-88c7-06201c8c0800	a577ea7c-4f39-4e3a-888e-22ed4705304b	Bathroom soap holder, toilet paper holder, and robe/towel holders	11	t	t	2026-07-18 07:36:28.221043
1f964921-c1ea-4d2c-9194-150d45ccd86c	a577ea7c-4f39-4e3a-888e-22ed4705304b	Toilet (bowl, cistern, and flushing mechanism) (note any defects/leaks)	12	t	t	2026-07-18 07:36:28.221044
b5604767-0d82-470c-913f-925d0da3c60f	a577ea7c-4f39-4e3a-888e-22ed4705304b	swimming pool	13	f	t	2026-07-18 07:38:27.187546
\.


--
-- Data for Name: expense_attachments; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.expense_attachments (id, expense_id, filename, file_url, uploaded_by, created_at) FROM stdin;
7d95767e-2365-4ee3-afcd-5a1b7814b8b7	22e48dcb-a994-43c2-b042-398310ea79c9	_.jpeg	http://localhost:8000/uploads/expense-receipts/22e48dcb-a994-43c2-b042-398310ea79c9/93d751fb-a300-4a0c-a38a-7ca61f2763dd-_.jpeg	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	2026-07-18 07:32:14.811142
\.


--
-- Data for Name: expense_categories; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.expense_categories (id, organization_id, name, description, is_active, created_at, updated_at) FROM stdin;
4156eec5-d160-4d9a-98c4-3bc42b97a946	a577ea7c-4f39-4e3a-888e-22ed4705304b	Repairs	\N	t	2026-07-18 07:11:48.438893	2026-07-18 07:11:48.438897
963091f6-a5d9-41e3-b53b-51255a6e0dfb	a577ea7c-4f39-4e3a-888e-22ed4705304b	Maintenance	\N	t	2026-07-18 07:11:48.438898	2026-07-18 07:11:48.438898
defe5747-1154-4e88-ad5d-eeffc3732eab	a577ea7c-4f39-4e3a-888e-22ed4705304b	Cleaning	\N	t	2026-07-18 07:11:48.438899	2026-07-18 07:11:48.438899
64bc15a7-79c7-48ff-b9b2-4ad61f9e6fee	a577ea7c-4f39-4e3a-888e-22ed4705304b	Water	\N	t	2026-07-18 07:11:48.4389	2026-07-18 07:11:48.438901
626e5c90-ed6c-405d-8b74-757d44f619d8	a577ea7c-4f39-4e3a-888e-22ed4705304b	Electricity	\N	t	2026-07-18 07:11:48.438901	2026-07-18 07:11:48.438902
c8813195-287e-4cd0-b137-c851c431826d	a577ea7c-4f39-4e3a-888e-22ed4705304b	Security	\N	t	2026-07-18 07:11:48.438902	2026-07-18 07:11:48.438903
7f379f81-05c9-4706-9a5b-8e4e6ab89ead	a577ea7c-4f39-4e3a-888e-22ed4705304b	Salaries	\N	t	2026-07-18 07:11:48.438903	2026-07-18 07:11:48.438904
3d2589a0-3a80-48b7-9dae-ff5645f1571f	a577ea7c-4f39-4e3a-888e-22ed4705304b	Marketing	\N	t	2026-07-18 07:11:48.438904	2026-07-18 07:11:48.438905
5ed78183-98ff-46df-86e4-4cf37c419d8d	a577ea7c-4f39-4e3a-888e-22ed4705304b	Internet	\N	t	2026-07-18 07:11:48.438905	2026-07-18 07:11:48.438906
0f3ba954-4ccc-4965-bf39-6d41e3de46ef	a577ea7c-4f39-4e3a-888e-22ed4705304b	Legal	\N	t	2026-07-18 07:11:48.438906	2026-07-18 07:11:48.438907
b4558982-4db4-4066-a729-00a507fc9cf5	a577ea7c-4f39-4e3a-888e-22ed4705304b	Insurance	\N	t	2026-07-18 07:11:48.438907	2026-07-18 07:11:48.438908
7501e3af-03f6-47ba-b523-adbe8246093b	a577ea7c-4f39-4e3a-888e-22ed4705304b	Fuel	\N	t	2026-07-18 07:11:48.438908	2026-07-18 07:11:48.438909
d7914799-8c61-4255-bb66-40591a2f831f	a577ea7c-4f39-4e3a-888e-22ed4705304b	Office Supplies	\N	t	2026-07-18 07:11:48.438909	2026-07-18 07:11:48.43891
0217d44a-db3d-4508-8399-fc1f52f85cd2	a577ea7c-4f39-4e3a-888e-22ed4705304b	Landscaping	\N	t	2026-07-18 07:11:48.43891	2026-07-18 07:11:48.438911
bdf76b07-1c61-4597-b8df-0ff112f4dd38	a577ea7c-4f39-4e3a-888e-22ed4705304b	Waste Collection	\N	t	2026-07-18 07:11:48.438911	2026-07-18 07:11:48.438912
ca02cad6-62fa-487d-b327-562ee55c9650	a577ea7c-4f39-4e3a-888e-22ed4705304b	Other	\N	t	2026-07-18 07:11:48.438912	2026-07-18 07:11:48.438913
d731cd99-546f-458b-ae4b-d3b05f9160b4	a577ea7c-4f39-4e3a-888e-22ed4705304b	swimming pool	\N	t	2026-07-18 07:29:42.708005	2026-07-18 07:29:42.708013
\.


--
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.expenses (id, organization_id, property_id, unit_id, vendor_id, category_id, created_by, approved_by, title, description, amount, expense_date, payment_method, reference_number, status, receipt_number, notes, created_at, updated_at) FROM stdin;
22e48dcb-a994-43c2-b042-398310ea79c9	a577ea7c-4f39-4e3a-888e-22ed4705304b	6eaa0fc0-4a8e-47e1-89a6-3a145ff5b1af	\N	bb32b74b-6ae7-40d0-93de-0a7c34f45a1a	bdf76b07-1c61-4597-b8df-0ff112f4dd38	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	waste collectors	clearerd	1000.00	2026-07-18	M-Pesa	dfsdfsd122345	paid	0987	clearerd	2026-07-18 07:32:14.618385	2026-07-18 07:33:17.546816
\.


--
-- Data for Name: inspection_items; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.inspection_items (id, inspection_id, item_name, sort_order, condition, comments, photo_urls, deduction_amount, created_at, updated_at) FROM stdin;
f590e32a-c062-43dd-9343-38a60fcc8ec1	6c23883d-c153-48da-a9bd-1b0856f0078d	Doors, windows, glass, handles, hinges, and locks	0	working	\N	[]	0.00	2026-07-18 07:38:38.484361	2026-07-24 07:23:32.926472
3d28580f-8bf0-4d8d-8037-09334bb36bd7	6c23883d-c153-48da-a9bd-1b0856f0078d	Bedroom wardrobes, drawers, and shelves	9	working	\N	[]	0.00	2026-07-18 07:38:38.484384	2026-07-24 07:24:36.226023
cda4ca18-8151-46c7-b56c-5654c6f14f1a	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Doors, windows, glass, handles, hinges, and locks	0	working	jkjkhjk	["http://localhost:8000/uploads/inspection-photos/005f18c5-ee78-44d7-af5c-39d44e7c5cd5/cda4ca18-8151-46c7-b56c-5654c6f14f1a/11d28ada-11e8-4b2b-a0a7-ed0f7af7bd17-_.jpeg"]	0.00	2026-07-18 07:36:35.849532	2026-07-18 07:36:55.608425
30625275-01cc-4f3f-b749-fae838f4b295	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Floor finishes (tiles/terrazzo)	1	working	\N	[]	0.00	2026-07-18 07:36:35.84954	2026-07-18 07:36:58.558806
20d06e96-4337-45d9-a121-441d047dd971	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Walls and paint finish	2	working	\N	[]	0.00	2026-07-18 07:36:35.849541	2026-07-18 07:37:00.578441
748c5633-c5ef-4d96-bef3-90ed3bb3193d	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Door locks and keys issued (list keys)	3	working	\N	[]	0.00	2026-07-18 07:36:35.849543	2026-07-18 07:37:02.478274
a83c8b2e-4aad-4797-9a34-ad057e128376	6c23883d-c153-48da-a9bd-1b0856f0078d	Floor finishes (tiles/terrazzo)	1	faulty	\N	[]	1000.00	2026-07-18 07:38:38.484368	2026-07-24 07:24:01.633518
90b8c1d2-8d34-4424-a982-86062ff60a34	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Electricity switches, sockets, and light fittings	4	needs_repair	wall socket sitting room	[]	0.00	2026-07-18 07:36:35.849545	2026-07-18 07:37:18.726354
47a56d51-e40a-4114-8820-0b735b17bec9	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Water taps and plumbing visible fittings (note any defects/leaks)	5	working	\N	[]	0.00	2026-07-18 07:36:35.849547	2026-07-18 07:37:18.870797
3ffaab91-6cc4-4251-94cd-1696e71906b5	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Hot water heater / shower	6	working	\N	[]	0.00	2026-07-18 07:36:35.849548	2026-07-18 07:37:20.678085
46b3d129-2cb2-483a-84c6-76340ad0c415	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Sinks and drain points (note any defects/leaks)	7	working	\N	[]	0.00	2026-07-18 07:36:35.849549	2026-07-18 07:37:23.72139
3e64daf9-1759-4d64-aa6c-19a2cbb575a5	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Kitchen cabinets/cupboards, drawers, and shelves	8	working	\N	[]	0.00	2026-07-18 07:36:35.849551	2026-07-18 07:37:25.929959
597bf122-55ec-4478-8646-9e40ce4a5b4d	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Bedroom wardrobes, drawers, and shelves	9	working	\N	[]	0.00	2026-07-18 07:36:35.849552	2026-07-18 07:37:29.328044
9497e89e-67ed-4e94-94d1-37d62277bcb2	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Bathroom and bedroom mirrors	10	working	\N	[]	0.00	2026-07-18 07:36:35.849554	2026-07-18 07:37:31.599522
1bcd49a1-c9ea-48fb-96f1-1dc06ecc541a	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Bathroom soap holder, toilet paper holder, and robe/towel holders	11	working	\N	[]	0.00	2026-07-18 07:36:35.849555	2026-07-18 07:37:33.908504
9b3366ca-7f88-4086-b62c-205cd9592380	005f18c5-ee78-44d7-af5c-39d44e7c5cd5	Toilet (bowl, cistern, and flushing mechanism) (note any defects/leaks)	12	working	\N	[]	0.00	2026-07-18 07:36:35.849556	2026-07-18 07:37:35.713044
45395f1e-a27c-4ad6-bf4c-73a258e3720e	6c23883d-c153-48da-a9bd-1b0856f0078d	Bathroom and bedroom mirrors	10	working	\N	[]	0.00	2026-07-18 07:38:38.484386	2026-07-24 07:24:39.102981
33184ee0-5eac-4507-a8c0-d4711e397d1a	6c23883d-c153-48da-a9bd-1b0856f0078d	Walls and paint finish	2	working	\N	[]	0.00	2026-07-18 07:38:38.48437	2026-07-24 07:24:03.496208
e23f0a64-be19-4147-b3af-ce34ffa0177c	6c23883d-c153-48da-a9bd-1b0856f0078d	Door locks and keys issued (list keys)	3	working	\N	[]	0.00	2026-07-18 07:38:38.484372	2026-07-24 07:24:05.662305
b756b1c2-168c-441f-a1d8-c31498d9ce92	6c23883d-c153-48da-a9bd-1b0856f0078d	Bathroom soap holder, toilet paper holder, and robe/towel holders	11	working	\N	[]	0.00	2026-07-18 07:38:38.484389	2026-07-24 07:24:42.734111
11d9dd15-de85-4d57-bd08-770dd84715be	6c23883d-c153-48da-a9bd-1b0856f0078d	Electricity switches, sockets, and light fittings	4	faulty	\N	[]	1000.00	2026-07-18 07:38:38.484374	2026-07-24 07:24:16.5017
f1d47cb3-85c5-4cd0-8bb6-86fb96b2ab34	6c23883d-c153-48da-a9bd-1b0856f0078d	Water taps and plumbing visible fittings (note any defects/leaks)	5	working	\N	[]	0.00	2026-07-18 07:38:38.484376	2026-07-24 07:24:16.631191
8a91f0f5-3d07-4406-86c8-991aede48c70	6c23883d-c153-48da-a9bd-1b0856f0078d	Hot water heater / shower	6	working	\N	[]	0.00	2026-07-18 07:38:38.484378	2026-07-24 07:24:18.785268
18b1d3c4-17f9-41f0-9555-d84861775fb9	6c23883d-c153-48da-a9bd-1b0856f0078d	Sinks and drain points (note any defects/leaks)	7	working	\N	[]	0.00	2026-07-18 07:38:38.48438	2026-07-24 07:24:22.316014
bf711f04-c2f3-4401-9366-a28362d0d3c1	6c23883d-c153-48da-a9bd-1b0856f0078d	Kitchen cabinets/cupboards, drawers, and shelves	8	working	\N	[]	0.00	2026-07-18 07:38:38.484382	2026-07-24 07:24:25.630985
e7878a01-ecfb-4682-a724-526bbea34169	6c23883d-c153-48da-a9bd-1b0856f0078d	Toilet (bowl, cistern, and flushing mechanism) (note any defects/leaks)	12	working	\N	[]	0.00	2026-07-18 07:38:38.484391	2026-07-24 07:24:46.806122
2b2676c4-6e71-45be-9d08-d8460f807991	f9b9b66a-4f58-4d47-adeb-a342c94725db	Doors, windows, glass, handles, hinges, and locks	0	\N	\N	[]	0.00	2026-07-18 07:47:12.855002	2026-07-18 07:47:12.855007
d9247e53-a62f-4f2f-b2a2-65b93ebd027c	f9b9b66a-4f58-4d47-adeb-a342c94725db	Floor finishes (tiles/terrazzo)	1	\N	\N	[]	0.00	2026-07-18 07:47:12.855008	2026-07-18 07:47:12.855008
d22663db-17e1-4992-bafa-c46969680705	f9b9b66a-4f58-4d47-adeb-a342c94725db	Walls and paint finish	2	\N	\N	[]	0.00	2026-07-18 07:47:12.855009	2026-07-18 07:47:12.855009
88e236c7-ad42-4219-a0cc-ee70e55dfb81	f9b9b66a-4f58-4d47-adeb-a342c94725db	Door locks and keys issued (list keys)	3	\N	\N	[]	0.00	2026-07-18 07:47:12.85501	2026-07-18 07:47:12.85501
05ccffbd-5794-40c0-b42c-ff40744a65e9	f9b9b66a-4f58-4d47-adeb-a342c94725db	Electricity switches, sockets, and light fittings	4	\N	\N	[]	0.00	2026-07-18 07:47:12.855011	2026-07-18 07:47:12.855011
63c2ca73-752c-4b24-8061-3da41ca7535e	f9b9b66a-4f58-4d47-adeb-a342c94725db	Water taps and plumbing visible fittings (note any defects/leaks)	5	\N	\N	[]	0.00	2026-07-18 07:47:12.855012	2026-07-18 07:47:12.855012
3b2bb7ad-c520-4c30-9274-7d96a3839b31	f9b9b66a-4f58-4d47-adeb-a342c94725db	Hot water heater / shower	6	\N	\N	[]	0.00	2026-07-18 07:47:12.855013	2026-07-18 07:47:12.855014
d3ba0f43-0c7d-4d8f-be95-51d6eedea5e5	f9b9b66a-4f58-4d47-adeb-a342c94725db	Sinks and drain points (note any defects/leaks)	7	\N	\N	[]	0.00	2026-07-18 07:47:12.855014	2026-07-18 07:47:12.855015
11c2b634-0b11-42bb-90b1-e5ecddc1f5c1	f9b9b66a-4f58-4d47-adeb-a342c94725db	Kitchen cabinets/cupboards, drawers, and shelves	8	\N	\N	[]	0.00	2026-07-18 07:47:12.855016	2026-07-18 07:47:12.855016
7e9c9ca3-8154-4a6d-83f2-564e4d035468	f9b9b66a-4f58-4d47-adeb-a342c94725db	Bedroom wardrobes, drawers, and shelves	9	\N	\N	[]	0.00	2026-07-18 07:47:12.855017	2026-07-18 07:47:12.855017
9e6e7afe-6c23-4e6c-aa67-631d72b4aac1	f9b9b66a-4f58-4d47-adeb-a342c94725db	Bathroom and bedroom mirrors	10	\N	\N	[]	0.00	2026-07-18 07:47:12.855017	2026-07-18 07:47:12.855018
534b110b-e931-46cc-8654-ff78627c33d4	f9b9b66a-4f58-4d47-adeb-a342c94725db	Bathroom soap holder, toilet paper holder, and robe/towel holders	11	\N	\N	[]	0.00	2026-07-18 07:47:12.855019	2026-07-18 07:47:12.855019
c0d9a5e4-6019-43ff-aafd-be8d0271ad39	f9b9b66a-4f58-4d47-adeb-a342c94725db	Toilet (bowl, cistern, and flushing mechanism) (note any defects/leaks)	12	\N	\N	[]	0.00	2026-07-18 07:47:12.85502	2026-07-18 07:47:12.85502
17b8be63-7c75-4647-876b-d2e7cac97a60	f9b9b66a-4f58-4d47-adeb-a342c94725db	swimming pool	13	\N	\N	[]	0.00	2026-07-18 07:47:12.855021	2026-07-18 07:47:12.855021
92163b1c-8953-4d19-9867-497bce8c69b9	8e1f553b-8aee-4075-9089-f6e4fbb05057	Doors, windows, glass, handles, hinges, and locks	0	working	\N	[]	0.00	2026-07-18 07:55:44.369994	2026-07-18 07:56:05.004484
8f6a9fcc-f043-4ccb-9e60-f509bdd80822	8e1f553b-8aee-4075-9089-f6e4fbb05057	Floor finishes (tiles/terrazzo)	1	working	\N	[]	0.00	2026-07-18 07:55:44.370001	2026-07-18 07:56:06.898657
54bc7f57-e89d-48c4-964a-17c9c8e3f3da	8e1f553b-8aee-4075-9089-f6e4fbb05057	Walls and paint finish	2	working	\N	[]	0.00	2026-07-18 07:55:44.370004	2026-07-18 07:56:08.484522
d13c89f4-a688-46d6-a29f-c9d2a51b8603	8e1f553b-8aee-4075-9089-f6e4fbb05057	Door locks and keys issued (list keys)	3	working	\N	[]	0.00	2026-07-18 07:55:44.370007	2026-07-18 07:56:09.855217
76eefa34-3ca7-43be-9a1a-0293d1e68a93	8e1f553b-8aee-4075-9089-f6e4fbb05057	Electricity switches, sockets, and light fittings	4	working	\N	[]	0.00	2026-07-18 07:55:44.370009	2026-07-18 07:56:11.298803
5344d62a-6873-4e69-bebf-21eec86f1496	8e1f553b-8aee-4075-9089-f6e4fbb05057	Water taps and plumbing visible fittings (note any defects/leaks)	5	working	\N	[]	0.00	2026-07-18 07:55:44.370013	2026-07-18 07:56:12.976987
5eb764f7-bcbf-48f3-b689-6d998e77ef68	8e1f553b-8aee-4075-9089-f6e4fbb05057	Hot water heater / shower	6	working	\N	[]	0.00	2026-07-18 07:55:44.370016	2026-07-18 07:56:15.553712
212caeba-7b3a-4a74-93d6-16de25836400	8e1f553b-8aee-4075-9089-f6e4fbb05057	Sinks and drain points (note any defects/leaks)	7	working	\N	[]	0.00	2026-07-18 07:55:44.370018	2026-07-18 07:56:17.210642
eab6993f-450e-4ae9-b06d-d8972c56027c	8e1f553b-8aee-4075-9089-f6e4fbb05057	Kitchen cabinets/cupboards, drawers, and shelves	8	working	\N	[]	0.00	2026-07-18 07:55:44.370021	2026-07-18 07:56:18.666592
77f4a4f6-6b3d-4e80-ae3d-b6213b98bdb5	8e1f553b-8aee-4075-9089-f6e4fbb05057	Bedroom wardrobes, drawers, and shelves	9	working	\N	[]	0.00	2026-07-18 07:55:44.370023	2026-07-18 07:56:20.401509
49b94bdd-c024-4634-b6b2-daa5d0987c12	8e1f553b-8aee-4075-9089-f6e4fbb05057	Bathroom and bedroom mirrors	10	working	\N	[]	0.00	2026-07-18 07:55:44.370026	2026-07-18 07:56:21.972311
0dbdf9cb-5dc9-495c-8953-3bd890e33136	8e1f553b-8aee-4075-9089-f6e4fbb05057	Bathroom soap holder, toilet paper holder, and robe/towel holders	11	working	\N	[]	0.00	2026-07-18 07:55:44.370028	2026-07-18 07:56:23.461988
c4cb13f2-9183-4bc4-a857-ffd56ab0c808	8e1f553b-8aee-4075-9089-f6e4fbb05057	Toilet (bowl, cistern, and flushing mechanism) (note any defects/leaks)	12	working	\N	[]	0.00	2026-07-18 07:55:44.370031	2026-07-18 07:56:24.910288
4be2a724-56d5-4520-b989-8e28ce3a6fe3	8e1f553b-8aee-4075-9089-f6e4fbb05057	swimming pool	13	working	\N	[]	0.00	2026-07-18 07:55:44.370033	2026-07-18 07:56:26.785883
40205eaa-fc08-4c94-ac27-5610753de535	6030079d-b87c-491c-a58e-b26314df453d	Doors, windows, glass, handles, hinges, and locks	0	working	\N	[]	0.00	2026-07-24 07:02:58.40105	2026-07-24 07:04:14.568478
0c528184-6ab3-48de-b503-e2ecbf74bfc9	6030079d-b87c-491c-a58e-b26314df453d	Floor finishes (tiles/terrazzo)	1	working	\N	[]	0.00	2026-07-24 07:02:58.401058	2026-07-24 07:04:16.455328
a5b2a63e-bff0-40d2-99b4-c836bba9a1b9	6030079d-b87c-491c-a58e-b26314df453d	Walls and paint finish	2	working	\N	[]	0.00	2026-07-24 07:02:58.40106	2026-07-24 07:04:18.031824
69c7d8dc-f5f5-4f74-9682-43dacc310607	6030079d-b87c-491c-a58e-b26314df453d	Door locks and keys issued (list keys)	3	working	\N	[]	0.00	2026-07-24 07:02:58.401062	2026-07-24 07:04:19.824666
11605f26-b896-4a69-a0f3-8a6e03f42c1b	6030079d-b87c-491c-a58e-b26314df453d	Electricity switches, sockets, and light fittings	4	working	\N	[]	0.00	2026-07-24 07:02:58.401064	2026-07-24 07:04:21.675771
d63a86c4-e547-4e94-ab6a-d481cf2644f0	6030079d-b87c-491c-a58e-b26314df453d	Water taps and plumbing visible fittings (note any defects/leaks)	5	working	\N	[]	0.00	2026-07-24 07:02:58.401066	2026-07-24 07:04:23.528467
e9a136a3-b491-4ad9-aa57-e8b6695fbcd2	6030079d-b87c-491c-a58e-b26314df453d	Hot water heater / shower	6	working	\N	[]	0.00	2026-07-24 07:02:58.401069	2026-07-24 07:04:25.499769
075975f7-6b51-425f-a0f9-4a420a2c1d46	6030079d-b87c-491c-a58e-b26314df453d	Sinks and drain points (note any defects/leaks)	7	working	\N	[]	0.00	2026-07-24 07:02:58.401071	2026-07-24 07:04:27.572327
fb991a63-8286-404b-b94e-b95a67792a6c	6030079d-b87c-491c-a58e-b26314df453d	Kitchen cabinets/cupboards, drawers, and shelves	8	working	\N	[]	0.00	2026-07-24 07:02:58.401073	2026-07-24 07:04:29.86761
d9a7fa34-02a0-41c0-8e02-39411538e41d	6030079d-b87c-491c-a58e-b26314df453d	Bedroom wardrobes, drawers, and shelves	9	working	\N	[]	0.00	2026-07-24 07:02:58.401076	2026-07-24 07:04:31.662719
69eacd5b-63b4-474c-a0a4-05577977bdcd	6030079d-b87c-491c-a58e-b26314df453d	Bathroom and bedroom mirrors	10	working	\N	[]	0.00	2026-07-24 07:02:58.401078	2026-07-24 07:04:33.990743
7548e3e6-ab67-429b-982c-2211b031fea9	6c23883d-c153-48da-a9bd-1b0856f0078d	swimming pool	13	working	\N	[]	0.00	2026-07-18 07:38:38.484393	2026-07-24 07:24:49.667127
c01d51d9-ae0c-4116-94dd-2667cc403f60	6030079d-b87c-491c-a58e-b26314df453d	Bathroom soap holder, toilet paper holder, and robe/towel holders	11	working	\N	[]	0.00	2026-07-24 07:02:58.40108	2026-07-24 07:04:35.870008
81835a49-138c-49e6-887b-6f37f163eca9	6030079d-b87c-491c-a58e-b26314df453d	Toilet (bowl, cistern, and flushing mechanism) (note any defects/leaks)	12	working	\N	[]	0.00	2026-07-24 07:02:58.401082	2026-07-24 07:04:37.694351
fb2d21ee-7337-4a81-bc05-d637b4ec6ad0	6030079d-b87c-491c-a58e-b26314df453d	swimming pool	13	working	\N	[]	0.00	2026-07-24 07:02:58.401084	2026-07-24 07:04:40.277403
\.


--
-- Data for Name: inspection_notes; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.inspection_notes (id, inspection_id, user_id, note, created_at) FROM stdin;
\.


--
-- Data for Name: lease_inspections; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.lease_inspections (id, lease_id, inspection_type, inspection_date, inspector_user_id, tenant_signature_data, tenant_signed_name, tenant_signed_at, status, total_deduction_amount, created_at, updated_at, deposit_held, deposit_refunded, deposit_shortfall) FROM stdin;
6030079d-b87c-491c-a58e-b26314df453d	9f655e89-df15-471e-8b94-0c2fc900936b	move_in	2026-07-24	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	data:image/png;base64,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	sharon kendi	2026-07-24 07:04:57.670133	signed	0.00	2026-07-24 07:02:58.358138	2026-07-24 07:04:57.670168	\N	\N	\N
005f18c5-ee78-44d7-af5c-39d44e7c5cd5	1f1b5410-9b24-4ba9-aad8-77679b7199a0	move_in	2026-07-18	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	data:image/png;base64,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	anne waithaka	2026-07-18 07:38:00.645936	signed	0.00	2026-07-18 07:17:10.087022	2026-07-18 07:38:00.645964	\N	\N	\N
f9b9b66a-4f58-4d47-adeb-a342c94725db	91886e76-0ac5-4e2f-ae95-93d201c7ffc6	move_in	\N	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	\N	\N	\N	draft	0.00	2026-07-18 07:47:12.848973	2026-07-18 07:47:12.848976	\N	\N	\N
6c23883d-c153-48da-a9bd-1b0856f0078d	1f1b5410-9b24-4ba9-aad8-77679b7199a0	move_out	2026-07-24	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	data:image/png;base64,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	HERMAN	2026-07-24 07:42:12.123516	signed	2000.00	2026-07-18 07:38:38.470431	2026-07-24 07:42:12.123832	20000.00	18000.00	0.00
8e1f553b-8aee-4075-9089-f6e4fbb05057	660b879e-a048-43a1-98e8-68d74725bbe4	move_in	2026-07-18	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	data:image/png;base64,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	1 mark	2026-07-18 07:56:40.22698	signed	0.00	2026-07-18 07:55:44.360111	2026-07-18 07:56:40.227016	\N	\N	\N
\.


--
-- Data for Name: leases; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.leases (id, organization_id, unit_id, tenant_id, start_date, end_date, rent_amount, deposit_amount, billing_day, status, created_at, move_in_date, signed_on_behalf_of, signed_lease_urls, custom_fields) FROM stdin;
91886e76-0ac5-4e2f-ae95-93d201c7ffc6	a577ea7c-4f39-4e3a-888e-22ed4705304b	0605af17-ffd0-4741-a890-aa40ba08fd30	72235713-77ba-4f6c-b9d1-05cfd9335224	2026-07-19	\N	11000.00	11000.00	1	active	2026-07-18 07:47:12.832829	2026-07-19	\N	[]	[]
660b879e-a048-43a1-98e8-68d74725bbe4	a577ea7c-4f39-4e3a-888e-22ed4705304b	218b7818-10a5-4701-9dc9-d523327f0f1c	def8f38c-4ece-4ea0-84aa-1bb3ca2a56b9	2026-07-19	\N	16000.00	16000.00	1	active	2026-07-18 07:55:44.342788	2026-07-19	\N	[]	[]
9f655e89-df15-471e-8b94-0c2fc900936b	a577ea7c-4f39-4e3a-888e-22ed4705304b	c90fe656-0c5a-4b35-9e5f-0151f8f442c5	cedbb0ae-6d00-4b5e-a938-11162db1a492	2026-07-25	\N	35000.00	35000.00	1	active	2026-07-24 07:02:58.230328	2026-07-25	\N	[]	[]
1f1b5410-9b24-4ba9-aad8-77679b7199a0	a577ea7c-4f39-4e3a-888e-22ed4705304b	c463840b-a13c-41bf-baaf-bb0e69b848c2	8ab4decf-2b05-4862-8ea8-0e6325408638	2026-07-19	2028-07-19	20000.00	20000.00	1	terminated	2026-07-18 07:17:10.044858	2026-07-19	\N	[]	[]
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.messages (id, organization_id, phone_number, direction, message_type, content, template_name, status, provider_message_id, error_message, channel, triggered_by_user_id, tenant_id, created_at, updated_at, ticket_id) FROM stdin;
976f4eb9-e30e-45fb-8530-80dbeba42a30	a577ea7c-4f39-4e3a-888e-22ed4705304b	0725325915	outgoing	otp	Your verification code is 533812. It expires in 10 minutes. If you didn't request this, ignore this message.	\N	sent	wamid.HBgMMjU0NzI1MzI1OTE1FQIAERgSQjY1RjVGRjgzOEVGQUUzRDlGAA==	\N	whatsapp	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	\N	2026-07-18 07:11:48.459956	2026-07-18 07:11:49.93958	\N
bb2a95c6-3b9c-4cd8-967c-56d04211050f	a577ea7c-4f39-4e3a-888e-22ed4705304b	0725325915	outgoing	notification	Hi Herman Remington, welcome to Wellness One Heights!\n\nYour unit A1 is ready. We're glad to have you.	lease_welcome	sent	wamid.HBgMMjU0NzI1MzI1OTE1FQIAERgSNDZFQkJFMTUwNTdFMEE5QTgwAA==	\N	whatsapp	\N	8ab4decf-2b05-4862-8ea8-0e6325408638	2026-07-18 07:17:10.277919	2026-07-18 07:17:11.5308	\N
09f98910-1a3e-4302-946d-4c2c45d648af	a577ea7c-4f39-4e3a-888e-22ed4705304b	0725325915	outgoing	notification	Hi Herman Remington, your rent of KES 20,000 is due on 01 Jul 2026. Please ensure payment is made on time. Thank you.	rent_due_reminder	sent	wamid.HBgMMjU0NzI1MzI1OTE1FQIAERgSRTcyMzZDNzZEODYyRTU4RjI0AA==	\N	whatsapp	\N	8ab4decf-2b05-4862-8ea8-0e6325408638	2026-07-18 07:19:06.000281	2026-07-18 07:19:06.753017	\N
39309e45-d117-4698-9626-d26ee40db699	a577ea7c-4f39-4e3a-888e-22ed4705304b	0725325915	outgoing	notification	Payment received ✔\n\nHi Herman Remington, we've received your payment of KES 20,000 on 18 Jul 2026. Thank you!	payment_receipt	sent	wamid.HBgMMjU0NzI1MzI1OTE1FQIAERgSRjU2NzdFOUU5MTJDQkM2QUMwAA==	\N	whatsapp	\N	8ab4decf-2b05-4862-8ea8-0e6325408638	2026-07-18 07:19:37.022542	2026-07-18 07:19:38.217782	\N
2e3ab3d8-ba95-4ce5-95d9-6fb6bd5becfd	a577ea7c-4f39-4e3a-888e-22ed4705304b	0725325915	outgoing	notification	Payment received ✔\n\nHi Herman Remington, we've received your payment of KES 20,000 on 18 Jul 2026. Thank you!	payment_receipt	sent	wamid.HBgMMjU0NzI1MzI1OTE1FQIAERgSMEIzRTQ2Q0Y3QUU3RjQ4RTgxAA==	\N	whatsapp	\N	8ab4decf-2b05-4862-8ea8-0e6325408638	2026-07-18 07:19:59.88551	2026-07-18 07:20:01.033722	\N
ec826b78-e7ab-49fd-bc90-8b0bf7fb3760	a577ea7c-4f39-4e3a-888e-22ed4705304b	0732808098	outgoing	notification	Hi mark volt, welcome to Sunset Homes!\n\nYour unit A01 is ready. We're glad to have you.	lease_welcome	sent	wamid.HBgMMjU0NzMyODA4MDk4FQIAERgSNzYwRTcwOUQwREFFNkI5OUQ1AA==	\N	whatsapp	\N	72235713-77ba-4f6c-b9d1-05cfd9335224	2026-07-18 07:47:12.904279	2026-07-18 07:47:14.185033	\N
da1ff4f0-e616-4e28-8e55-c68ad14378ef	a577ea7c-4f39-4e3a-888e-22ed4705304b	0732808098	outgoing	invite	Hi! You've been invited to join Wellness One as a TENANT.\n\nAccept your invitation here: http://localhost:5173/accept-invite/77694a84-5adc-4c5e-91be-ed6c525adb19	staff_invite	sent	wamid.HBgMMjU0NzMyODA4MDk4FQIAERgSNzlCQzg2OTU5OUU1Rjg0MTVDAA==	\N	whatsapp	\N	\N	2026-07-18 07:47:33.431329	2026-07-18 07:47:34.658962	\N
d85001e5-bd95-424f-93fe-8198ae9a9414	a577ea7c-4f39-4e3a-888e-22ed4705304b	0725325915	outgoing	invite	Hi! You've been invited to join Wellness One as a TENANT.\n\nAccept your invitation here: http://localhost:5173/accept-invite/1159e096-6ea3-496c-a8f8-756737bde12a	staff_invite	sent	wamid.HBgMMjU0NzI1MzI1OTE1FQIAERgSRTg1MzM1ODFDRTA5RDU0NzhGAA==	\N	whatsapp	\N	\N	2026-07-18 07:52:12.379	2026-07-18 07:52:13.755839	\N
ef456d2e-202c-4020-82ab-189745873618	a577ea7c-4f39-4e3a-888e-22ed4705304b	0725325876	outgoing	notification	Hi mark 1, welcome to Wellness One Heights!\n\nYour unit B1 is ready. We're glad to have you.	lease_welcome	failed	\N	WhatsApp API error: (#131030) Recipient phone number not in allowed list	whatsapp	\N	def8f38c-4ece-4ea0-84aa-1bb3ca2a56b9	2026-07-18 07:55:44.466493	2026-07-18 07:55:45.397866	\N
e9937b75-1d1c-474f-be86-d31fb9461c5a	a577ea7c-4f39-4e3a-888e-22ed4705304b	0725325876	outgoing	notification	Your maintenance request has been received. Ticket ID: 3023bcf9\n\nWe'll be in touch shortly.	ticket_received	failed	\N	WhatsApp API error: (#131030) Recipient phone number not in allowed list	whatsapp	\N	def8f38c-4ece-4ea0-84aa-1bb3ca2a56b9	2026-07-18 07:58:29.230382	2026-07-18 07:58:30.135303	\N
fa3db80f-696d-4ec7-915f-fe1b6ab8c9bc	a577ea7c-4f39-4e3a-888e-22ed4705304b	0732808098	outgoing	notification	Hi mark volt, your rent of KES 11,000 is due on 01 Jul 2026. Please ensure payment is made on time. Thank you.	rent_due_reminder	failed	\N	WhatsApp API error: Authentication Error	whatsapp	\N	72235713-77ba-4f6c-b9d1-05cfd9335224	2026-07-20 05:23:59.727232	2026-07-20 05:24:01.202573	\N
ee1db52e-6fd9-4788-815a-3a690f8e1963	a577ea7c-4f39-4e3a-888e-22ed4705304b	0725325876	outgoing	notification	Hi mark 1, your rent of KES 16,000 is due on 01 Jul 2026. Please ensure payment is made on time. Thank you.	rent_due_reminder	failed	\N	WhatsApp API error: Authentication Error	whatsapp	\N	def8f38c-4ece-4ea0-84aa-1bb3ca2a56b9	2026-07-20 05:24:01.260849	2026-07-20 05:24:02.041303	\N
0def853b-b1bb-4b76-a5e0-d4dc1b1103a4	a577ea7c-4f39-4e3a-888e-22ed4705304b	0759564080	outgoing	invite	Hi! You've been invited to join Wellness One as a PROPERTY_MANAGER.\n\nAccept your invitation here: http://localhost:5173/accept-invite/aa43c938-1fe6-46c9-9c5a-5279f64e7561	staff_invite	sent	wamid.HBgMMjU0NzU5NTY0MDgwFQIAERgSRjEwRkE1NkZGRjEwNTY5RUQ2AA==	\N	whatsapp	\N	\N	2026-07-24 06:56:45.041719	2026-07-24 06:56:47.08546	\N
255bb907-154a-4a48-b425-8cde65d3825e	a577ea7c-4f39-4e3a-888e-22ed4705304b	0759564080	outgoing	notification	Hi sharon kendi, welcome to Silverleaf Apartments!\n\nYour unit A1 is ready. We're glad to have you.	lease_welcome	sent	wamid.HBgMMjU0NzU5NTY0MDgwFQIAERgSQTAzQUYxQTQ3QTg1OTNFMzI5AA==	\N	whatsapp	\N	cedbb0ae-6d00-4b5e-a938-11162db1a492	2026-07-24 07:02:58.503021	2026-07-24 07:03:00.131319	\N
d7d5f4b0-5c65-44dc-8a1b-2b32f2142af9	a577ea7c-4f39-4e3a-888e-22ed4705304b	0759564080	outgoing	notification	Hi sharon kendi, your rent of KES 35,000 is due on 01 Jul 2026. Please ensure payment is made on time. Thank you.	rent_due_reminder	sent	wamid.HBgMMjU0NzU5NTY0MDgwFQIAERgSOUZBOEE5MzJDODM3OTkxOERFAA==	\N	whatsapp	\N	cedbb0ae-6d00-4b5e-a938-11162db1a492	2026-07-24 07:14:36.788286	2026-07-24 07:14:38.351693	\N
\.


--
-- Data for Name: notification_preferences; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.notification_preferences (id, organization_id, user_id, email_enabled, whatsapp_enabled, sms_enabled, in_app_enabled, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.notifications (id, organization_id, user_id, title, body, notification_type, is_read, created_at) FROM stdin;
a3b6a898-c262-4fac-8c0d-be231cd3fafa	a577ea7c-4f39-4e3a-888e-22ed4705304b	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	New ticket #3023bcf9	Kitchen Tap	ticket_created	t	2026-07-18 07:58:30.157942
\.


--
-- Data for Name: organization_invitations; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.organization_invitations (id, email, role_id, organization_id, token, status, created_at, phone) FROM stdin;
84cf09f1-5c5d-40b0-b707-4a6e2c6d776c	mark@gmail.com	d1a5193a-8889-45f0-81b5-55b2399a883c	a577ea7c-4f39-4e3a-888e-22ed4705304b	77694a84-5adc-4c5e-91be-ed6c525adb19	pending	2026-07-18 07:47:33.364756	0732808098
6282cf9c-cf5e-4c79-9a23-90cb892faefc	1mark@gmail.com	d1a5193a-8889-45f0-81b5-55b2399a883c	a577ea7c-4f39-4e3a-888e-22ed4705304b	1159e096-6ea3-496c-a8f8-756737bde12a	accepted	2026-07-18 07:52:12.271728	0725325915
2a6ab4a8-63ae-42ec-be0a-a42db564bb8a	sharon@gmail.com	a0689163-1b94-4d9f-917b-d2c90a8ffd59	a577ea7c-4f39-4e3a-888e-22ed4705304b	aa43c938-1fe6-46c9-9c5a-5279f64e7561	accepted	2026-07-24 06:56:44.9047	0759564080
\.


--
-- Data for Name: organization_members; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.organization_members (id, user_id, organization_id, role_id, created_at) FROM stdin;
90d8ced9-9828-4b5a-8592-5086a8a35090	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	a577ea7c-4f39-4e3a-888e-22ed4705304b	c8d842c2-9248-4d56-958b-5ca5a54de1d7	2026-07-18 07:11:48.489942
39775897-dcbc-4bc2-88b7-6460dfc14474	8fbc3c86-e87c-48f8-a212-3a8662ea3340	a577ea7c-4f39-4e3a-888e-22ed4705304b	d1a5193a-8889-45f0-81b5-55b2399a883c	2026-07-18 07:53:28.535298
667580e1-6f01-4f89-81ab-375ec5898b78	95c955b7-a435-4bd7-b346-32d4d93277d0	a577ea7c-4f39-4e3a-888e-22ed4705304b	a0689163-1b94-4d9f-917b-d2c90a8ffd59	2026-07-24 07:00:37.891755
\.


--
-- Data for Name: organizations; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.organizations (id, name, owner_id, created_at) FROM stdin;
a577ea7c-4f39-4e3a-888e-22ed4705304b	Wellness One	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	2026-07-18 07:11:48.038153
\.


--
-- Data for Name: otp_verifications; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.otp_verifications (id, user_id, purpose, phone, code_hash, expires_at, attempts, last_sent_at, consumed_at, created_at) FROM stdin;
9aad92c6-8f0b-43d8-909c-a27fb9964fef	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	phone_verification	0725325915	$2b$12$.KP70C4Mq1XJCgfY0WL/ju949uQSAWVTBvYU08GL6h6l0XZhXdCJe	2026-07-18 07:21:48.076791	0	2026-07-18 07:11:48.076791	2026-07-18 07:12:07.659085	2026-07-18 07:11:48.493254
\.


--
-- Data for Name: password_history; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.password_history (id, user_id, password_hash, created_at) FROM stdin;
35d6c6aa-18b9-4903-a114-c81e487033ca	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	$2b$12$57yYPlCxo5mvN5gJ2PsHi.17hoYNzSuB8BdcRRxAVFYfgNFkkjHk.	2026-07-18 07:11:47.971303
b07d77c1-d448-43ae-be72-a837e5c10942	8fbc3c86-e87c-48f8-a212-3a8662ea3340	$2b$12$qvQtrCb8sINXf3mKVEgbcuOiQwiR/E7bqyRUG2apdOcbJc8oedx1e	2026-07-18 07:53:28.514195
b9e86ac0-6c82-44e5-907b-171c2ec460d0	95c955b7-a435-4bd7-b346-32d4d93277d0	$2b$12$01u4Rj5.8FIcw8kBlYnRiuBSf6FHuLulLTr7AkcXfRRoeTLI9mo4W	2026-07-24 07:00:37.82469
\.


--
-- Data for Name: payment_review_items; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.payment_review_items (id, organization_id, amount, payment_date, reference, payer_phone, payer_name, raw_transaction, tenant_id, lease_id, status, flag_reason, notes, resolved_at, resolved_by_user_id, resolution_payment_id, rejection_reason, created_at, created_by_user_id, source, source_message_id, extracted_reference, extracted_amount, message_timestamp, payer_phone_hash) FROM stdin;
3d2243df-bc1f-43f2-916a-2b4160cc4330	a577ea7c-4f39-4e3a-888e-22ed4705304b	32000.00	2026-08-09	UDTQS2OHG5	254725325965	\N	MPESA TO ACC 0100316372900 UDTQS2OHG5 TIMESTAMP: 254725325965 TO 0100316372900	\N	\N	applied	unmatched	\N	2026-07-23 06:56:32.105725	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	539c353b-c76a-4572-be8d-863b42b7da52	\N	2026-07-23 06:55:00.663114	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.payments (id, organization_id, tenant_id, lease_id, amount, payment_method, reference, payment_date, created_at, payment_type) FROM stdin;
5d3095d3-3b81-421c-86a8-d5de9fbe05b0	a577ea7c-4f39-4e3a-888e-22ed4705304b	8ab4decf-2b05-4862-8ea8-0e6325408638	1f1b5410-9b24-4ba9-aad8-77679b7199a0	20000.00	mpesa	asd21233	2026-07-18	2026-07-18 07:19:36.955594	rent
7e850f5d-7450-4a52-866b-bdd458295f28	a577ea7c-4f39-4e3a-888e-22ed4705304b	8ab4decf-2b05-4862-8ea8-0e6325408638	1f1b5410-9b24-4ba9-aad8-77679b7199a0	20000.00	mpesa	34eewfwe	2026-07-18	2026-07-18 07:19:59.809535	deposit
d83208f6-7b98-401b-b266-04168c8ca9dd	a577ea7c-4f39-4e3a-888e-22ed4705304b	8ab4decf-2b05-4862-8ea8-0e6325408638	1f1b5410-9b24-4ba9-aad8-77679b7199a0	26000.00	mpesa	UDTQS2OHFR	2026-08-29	2026-07-23 06:54:56.33463	rent
ed1e7794-62d4-4de8-9a56-7f26e95249af	a577ea7c-4f39-4e3a-888e-22ed4705304b	8ab4decf-2b05-4862-8ea8-0e6325408638	1f1b5410-9b24-4ba9-aad8-77679b7199a0	15500.00	mpesa	UDTQS2OHG1	2026-08-01	2026-07-23 06:54:56.405095	rent
539c353b-c76a-4572-be8d-863b42b7da52	a577ea7c-4f39-4e3a-888e-22ed4705304b	8ab4decf-2b05-4862-8ea8-0e6325408638	1f1b5410-9b24-4ba9-aad8-77679b7199a0	32000.00	mpesa	UDTQS2OHG5	2026-08-09	2026-07-23 06:56:32.095486	rent
\.


--
-- Data for Name: properties; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.properties (id, name, address, city, country, organization_id, created_at) FROM stdin;
6eaa0fc0-4a8e-47e1-89a6-3a145ff5b1af	Wellness One Heights	00100 177	Embakasi	Kenya	a577ea7c-4f39-4e3a-888e-22ed4705304b	2026-07-18 07:13:40.741117
c711e652-6b53-454f-a108-93947b0c227f	Sunset Homes	00100 177	Syokimau	Kenya	a577ea7c-4f39-4e3a-888e-22ed4705304b	2026-07-18 07:14:20.994397
599aac43-7726-4284-906e-fe2d91d8471f	Silverleaf Apartments	123 Riverside Drive	Nairobi	Kenya	a577ea7c-4f39-4e3a-888e-22ed4705304b	2026-07-23 06:59:54.60012
405470f3-d6a0-4e8d-b18d-b3bbd73d31b1	Baobab Court	45 Ngong Road	Nairobi	Kenya	a577ea7c-4f39-4e3a-888e-22ed4705304b	2026-07-23 06:59:54.600134
\.


--
-- Data for Name: property_finance_managers; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.property_finance_managers (id, property_id, user_id) FROM stdin;
\.


--
-- Data for Name: property_managers; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.property_managers (id, property_id, user_id) FROM stdin;
2c505bab-da6f-4502-84c6-ffa2c00df09a	6eaa0fc0-4a8e-47e1-89a6-3a145ff5b1af	95c955b7-a435-4bd7-b346-32d4d93277d0
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.roles (id, name, created_at) FROM stdin;
c8d842c2-9248-4d56-958b-5ca5a54de1d7	LANDLORD	2026-07-18 06:41:46.030025
a0689163-1b94-4d9f-917b-d2c90a8ffd59	PROPERTY_MANAGER	2026-07-18 06:41:46.030039
2f6ff036-802c-4b49-b5d2-6be5a69d85bf	FINANCE	2026-07-18 06:41:46.030051
d1a5193a-8889-45f0-81b5-55b2399a883c	TENANT	2026-07-18 06:41:46.030066
98e77e5b-65fc-4323-8158-9a0111142673	SYSTEM	2026-07-18 06:41:46.030075
\.


--
-- Data for Name: tenant_documents; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.tenant_documents (id, tenant_id, document_type, file_url, original_filename, uploaded_by_user_id, uploaded_at) FROM stdin;
999e1048-0509-49a8-a854-8ce3f256fede	72235713-77ba-4f6c-b9d1-05cfd9335224	national_id_front	http://localhost:8000/uploads/tenant-documents/72235713-77ba-4f6c-b9d1-05cfd9335224/a41dcced-988d-470a-9f7d-29f30d2a0f9e-_.jpeg	_.jpeg	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	2026-07-18 07:46:23.650833
\.


--
-- Data for Name: tenants; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.tenants (id, organization_id, full_name, email, phone, id_number, emergency_contact, created_at, alternative_phone, next_of_kin_name, next_of_kin_relationship, next_of_kin_phone, next_of_kin_alt_phone, next_of_kin_email, employer_name, employer_location, employer_phone, employer_email, user_id, phone_hash, alternative_phone_hash, email_hash, id_number_hash) FROM stdin;
8ab4decf-2b05-4862-8ea8-0e6325408638	a577ea7c-4f39-4e3a-888e-22ed4705304b	Herman Remington	gAAAAABqWyg6vWttMw6SqB1rVt22l-cw6osEc2vvwEwQFUr7ht6QfqTsW1KA2bHx2Mn8cP4cpjstXlew-2pwHrf5soxTFFAGGjcSB77j1BFQ5PmmBsRBY4c=	gAAAAABqWyg652FT1mlHzrk5nT0WFiYz1t1Z-4RucpMiLY0pwiBIzb51_LF3J6ViZnyBxapGDWZFogDPNsyDST_FQzeHDrBsoA==	gAAAAABqWyg6gzzUqFblrCFamXZs0e27jO_8eNRJ9GfmJH6z1PMS2p_BP6DGymh_BSIsaanZ78fMUTpOdTU5fBGx6Afq_NY8ZQ==	\N	2026-07-18 07:16:10.723955	gAAAAABqWyg62Hc3VxZPG13lDOHNyJh3PC0EiEmkhOwdP-owKXXdKVbOcMVTrWPsFEpPY4OmB9-juzyBtAnSMXq-VRxatJKkZA==	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	43e6780f6adfae01defc987d53bef8a6fc7007c37ab9b35e5dbcaa98001f3cff	7fb08f9f75dffd25d71c5d282adc2ca23d5823b27d8a2ebafbce284853995d96	8eab4b19f317c874d28a68a70ed88fe781401ba361f99b0f473e33cf3468724e	b8661c51c8db999a84452d123388b48cf209db42eab35ece4da67b59e5adb149
72235713-77ba-4f6c-b9d1-05cfd9335224	a577ea7c-4f39-4e3a-888e-22ed4705304b	mark volt	gAAAAABqWy9PxLhoyBAo3vKfjN2aP9I29we0JSdOof93m1N0EHHoB5QVhVbxcrP6IYxXJdRq0Sj9PftT8MNEpd4nvB1kD1Uw9Q==	gAAAAABqWy9PT1fiyesrlRUrXilYmetU-BAVYTm3MwcOFkZyiRHXXLMRuZM6r9Zaxs4lIgZfKpH5VnXS9yt-PefeOR7kD4JVBA==	gAAAAABqWy9PUSf7dCaDYDLSVfhhndkA2ZgZBW82JSxodJXXuGcu7lXiFkPBB4waMRFdsyzujk9k2LMHxXfZWihrSZle2pJ-9g==	\N	2026-07-18 07:46:23.530957	gAAAAABqWy9PlDxKda-GKi7Q1AdzAQBn1W6ijCjB92PkqQXJUaCAyAtWQ0USqfGZIluVSWQ4mpS9IdBJ3bdGhB6nuKUNh7n25A==	gAAAAABqWy9P__UKbUzGUlaKKWWm2Jle85UOVynkUlsm-DjNnaTiNLSSABYm5FeZO2bpYYfy3vlE91aHg2Zodh_XYfqkzvvjpw==	spouce	gAAAAABqWy9PLfygG6dxeQEO09KYZ7Ngi-X84Wdix2s4GY9CdBSPIOQK_jYVT4JKxEjhbJJu7Hqi-t2M6Mmu2hoAdSS3zj-cBw==	\N	gAAAAABqWy9P8r-dgOCM2lirZ1ZId3-NY5VS4i7CZ3MMJyqFICg0boyEBYFz7UmwAzobPigt_LzMV1ZACP7u-oFx-8icpRMOkg==	villa Homes	embu	0725354315	villahomes@gmail.com	\N	d8cbf04166bd762117f10c75f292bc71992032aca827790c135d3cb404c886f6	3a061e7208737319cf9651edca753e73af638c1930a60e6027fa2dd8e256f85f	524c8e2fa0112f181165b7212173d59f75b29403fef77103cffa0e6f72d4c4a1	96cd3b6bbb2c31e6a99772e0c296b28545eabb821fe0e71cfe61b77bdff2b142
def8f38c-4ece-4ea0-84aa-1bb3ca2a56b9	a577ea7c-4f39-4e3a-888e-22ed4705304b	mark 1	gAAAAABqWzFpLDpeV3KVNp5EWs-arIaGfaziXpdY6gB60iFDMbc1d3Y2Wu-fHCKNErE4Q_gTD0LoVwCaPWL1gcW-wnGs1kBCbw==	gAAAAABqWzFpg5bVigpNizi5kfQ3lgBb0hn9FwpHQQc7WtP166-cSKX_x6sUL78pnq0BkHkjHU5dKlZpXXQzkxcLt_TlTbs6VQ==	gAAAAABqWzFp30o9kEjZQ0PvkcnUqKgrUf8O_vEJtc4yAMZSfZ-spQ8pfgPnMLyXe9R_cjHodMmSYjdJu-eawOSKl7RLSU0Jmw==	\N	2026-07-18 07:55:21.152449	gAAAAABqWzFpkjjDQGk7rwhdThz4YAX5WoGCjSzxj11y9Hu8DcinUd6YeOPEHcpJuac1qRHTJSYfR1UxD1T43Q7IhCZGNpnHyQ==	\N	\N	\N	\N	\N	\N	\N	\N	\N	8fbc3c86-e87c-48f8-a212-3a8662ea3340	bb616dba2e2a6510bcc1a28797ee3d661ed887169294e37f08f467f57dfa5233	1d0a7eb4d328ab46868115245f3cb996553d7cc50632d94c73397426dc201f3c	67a42b93f5369fa09e03ee110c256a28b9e41e1ac8ff881e94a1095a046588a6	ad0c8230fa508b7c929046c4c175db7f0d22a4c8b61561fddf1e9fd36d06b7e9
cedbb0ae-6d00-4b5e-a938-11162db1a492	a577ea7c-4f39-4e3a-888e-22ed4705304b	sharon kendi	gAAAAABqYw3yJDLw4hzCR5j7sdYj8fcdHb03MUIA2uJYHh4hBcozlu4exr_x4KhPLtbC3kDlGQm_r1e9pq_JwMtLQoGCwFJQURhKOf_j0eeAOhc5ifsDews=	gAAAAABqYw3yB7eNDn0z9uRU0F1-fd6s_2K2ngK58JnDjz3S0RplFCa4q4EAyNv-fe4k72CtLFWaxBQwc_kbCiHD0g6W9WVfHg==	gAAAAABqYw3y8TPhIrpo34YBKbJcx_OPeqCJH1Qmmk5L1b_LhE6pc9p1qMN4N4pKMasIztccwhoIawnq7NeqSRX8LrCzYUQNdQ==	\N	2026-07-24 07:02:10.623199	gAAAAABqYw3yptZo-w2-H45jtvk23eohgFwkMLaP4Pud3tRgjFaVJrOdlGRXqIdhfGKbLT0s3JaiKuy9KC7g7eswpiKRX9HB5A==	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	d2a799f20825c8ce4f6740ce661434aeeb4fbbb401ae9fba0dd59e5ca5f2ad39	ce128217de0b28d79aa868262e760ddc57c049937ccdda0ffc569600cdafd8c1	b990efcd0098fc6d2fbcc600704f826a384ab97b2f1c3934cb0cf0a29713a14a	d7352557f70f6b7b12e262e137cddabc9a96b973249fd15b00722fd928c138be
\.


--
-- Data for Name: ticket_assignments; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.ticket_assignments (id, ticket_id, assigned_from, assigned_to, reason, assigned_at) FROM stdin;
\.


--
-- Data for Name: ticket_attachments; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.ticket_attachments (id, ticket_id, uploaded_by, file_name, file_url, created_at) FROM stdin;
\.


--
-- Data for Name: ticket_messages; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.ticket_messages (id, ticket_id, sender_id, message, is_internal, created_at, recipient_id) FROM stdin;
8d4a552e-b1dc-4b94-85e0-582489fb3cf9	3023bcf9-f40c-45e6-a438-395f0b2b9ed8	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	hello on it	f	2026-07-18 07:59:19.515508	\N
2a258b40-f527-4ed4-8971-a1d43d1c4900	3023bcf9-f40c-45e6-a438-395f0b2b9ed8	66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	we need this done	t	2026-07-18 07:59:58.319194	\N
\.


--
-- Data for Name: tickets; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.tickets (id, organization_id, tenant_id, source_phone, source_message_id, description, status, source, created_at, updated_at, property_id, unit_id, created_by, assigned_to, priority, category, opened_at, resolved_at, closed_at, title) FROM stdin;
3023bcf9-f40c-45e6-a438-395f0b2b9ed8	a577ea7c-4f39-4e3a-888e-22ed4705304b	def8f38c-4ece-4ea0-84aa-1bb3ca2a56b9	\N	\N	The kitchen tap is faulty	open	tenant_portal	2026-07-18 07:58:29.107492	2026-07-18 07:58:29.107497	6eaa0fc0-4a8e-47e1-89a6-3a145ff5b1af	\N	8fbc3c86-e87c-48f8-a212-3a8662ea3340	\N	high	repairs	2026-07-18 07:58:29.10325	\N	\N	Kitchen Tap
\.


--
-- Data for Name: units; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.units (id, property_id, name, description, bedrooms, bathrooms, size_sqm, rent_amount, is_active, created_at) FROM stdin;
0605af17-ffd0-4741-a890-aa40ba08fd30	c711e652-6b53-454f-a108-93947b0c227f	A01	First floor	1	1	400	11000.00	t	2026-07-18 07:44:03.379704
218b7818-10a5-4701-9dc9-d523327f0f1c	6eaa0fc0-4a8e-47e1-89a6-3a145ff5b1af	B1	First floor	1	1	400	16000.00	t	2026-07-18 07:54:40.921072
c90fe656-0c5a-4b35-9e5f-0151f8f442c5	599aac43-7726-4284-906e-fe2d91d8471f	A1	Corner unit, ground floor	2	1	65.5	35000.00	t	2026-07-23 07:00:45.408453
81a4626e-edb1-493e-9c4d-32bbf1fa73ce	599aac43-7726-4284-906e-fe2d91d8471f	A2	\N	1	1	45	25000.00	t	2026-07-23 07:00:45.408462
85c29c00-5e4e-48ad-8d76-01da7aaf1633	405470f3-d6a0-4e8d-b18d-b3bbd73d31b1	House 3	\N	3	2	120	60000.00	t	2026-07-23 07:00:45.408463
c463840b-a13c-41bf-baaf-bb0e69b848c2	6eaa0fc0-4a8e-47e1-89a6-3a145ff5b1af	A1	First floor	2	2	400	25000.00	t	2026-07-18 07:15:08.509646
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.users (id, email, password_hash, is_active, refresh_token, reset_token, reset_token_expiry, role_id, full_name, phone, phone_verified, failed_login_count, locked_until) FROM stdin;
66c8d44d-6b7d-4a59-b8f8-3b7526fd4853	remingtonherman7@gmail.com	$2b$12$57yYPlCxo5mvN5gJ2PsHi.17hoYNzSuB8BdcRRxAVFYfgNFkkjHk.	t	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NmM4ZDQ0ZC02YjdkLTRhNTktYjhmOC0zYjc1MjZmZDQ4NTMiLCJleHAiOjE3ODU0NzYwOTJ9.Q9gYIvySBQVoKrWJNG-xfO_TCEPotEjr1JS5wA80C7U	\N	\N	\N	Herman Remington	0725325915	t	0	\N
95c955b7-a435-4bd7-b346-32d4d93277d0	sharon@gmail.com	$2b$12$01u4Rj5.8FIcw8kBlYnRiuBSf6FHuLulLTr7AkcXfRRoeTLI9mo4W	t	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5NWM5NTViNy1hNDM1LTRiZDctYjM0Ni0zMmQ0ZDkzMjc3ZDAiLCJleHAiOjE3ODU0ODE1NTN9.vfF85p4zleh2dyx6jJBW5oF0riJQCJgPW1aUj9gUyDg	\N	\N	a0689163-1b94-4d9f-917b-d2c90a8ffd59	\N	\N	f	0	\N
8fbc3c86-e87c-48f8-a212-3a8662ea3340	1mark@gmail.com	$2b$12$qvQtrCb8sINXf3mKVEgbcuOiQwiR/E7bqyRUG2apdOcbJc8oedx1e	t	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4ZmJjM2M4Ni1lODdjLTQ4ZjgtYTIxMi0zYTg2NjJlYTMzNDAiLCJleHAiOjE3ODU0ODIwNTB9.64wxexu_RnD6vNwX_5UtxLBZDlxVnsMGhnS7yzZt468	\N	\N	d1a5193a-8889-45f0-81b5-55b2399a883c	\N	\N	f	0	\N
6d4d1538-9877-46d6-851e-7f67d55a644d	1remingtonherman7@gmail.com	$2b$12$G2g7gTsTnG8lP6cJfa.ZT.3pV6k3AHDCjBIU8Ew7Qwk4dNbwBz5Ee	t	\N	\N	\N	c8d842c2-9248-4d56-958b-5ca5a54de1d7	Erick Sirali	+254765000000	t	0	\N
\.


--
-- Data for Name: vendors; Type: TABLE DATA; Schema: public; Owner: rental_user
--

COPY public.vendors (id, organization_id, vendor_name, contact_person, phone, email, kra_pin, address, notes, created_at) FROM stdin;
bb32b74b-6ae7-40d0-93de-0a7c34f45a1a	a577ea7c-4f39-4e3a-888e-22ed4705304b	green waste collection	Herman Remington	0725325915	remingtonherman7@gmail.com	ghf12345	00100 177	good people	2026-07-18 07:30:51.960989
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: charges charges_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.charges
    ADD CONSTRAINT charges_pkey PRIMARY KEY (id);


--
-- Name: checklist_item_templates checklist_item_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.checklist_item_templates
    ADD CONSTRAINT checklist_item_templates_pkey PRIMARY KEY (id);


--
-- Name: expense_attachments expense_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expense_attachments
    ADD CONSTRAINT expense_attachments_pkey PRIMARY KEY (id);


--
-- Name: expense_categories expense_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expense_categories
    ADD CONSTRAINT expense_categories_pkey PRIMARY KEY (id);


--
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);


--
-- Name: inspection_items inspection_items_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.inspection_items
    ADD CONSTRAINT inspection_items_pkey PRIMARY KEY (id);


--
-- Name: inspection_notes inspection_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.inspection_notes
    ADD CONSTRAINT inspection_notes_pkey PRIMARY KEY (id);


--
-- Name: lease_inspections lease_inspections_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.lease_inspections
    ADD CONSTRAINT lease_inspections_pkey PRIMARY KEY (id);


--
-- Name: leases leases_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.leases
    ADD CONSTRAINT leases_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: notification_preferences notification_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.notification_preferences
    ADD CONSTRAINT notification_preferences_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: organization_invitations organization_invitations_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.organization_invitations
    ADD CONSTRAINT organization_invitations_pkey PRIMARY KEY (id);


--
-- Name: organization_invitations organization_invitations_token_key; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.organization_invitations
    ADD CONSTRAINT organization_invitations_token_key UNIQUE (token);


--
-- Name: organization_members organization_members_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.organization_members
    ADD CONSTRAINT organization_members_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: otp_verifications otp_verifications_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.otp_verifications
    ADD CONSTRAINT otp_verifications_pkey PRIMARY KEY (id);


--
-- Name: password_history password_history_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.password_history
    ADD CONSTRAINT password_history_pkey PRIMARY KEY (id);


--
-- Name: payment_review_items payment_review_items_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payment_review_items
    ADD CONSTRAINT payment_review_items_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: properties properties_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.properties
    ADD CONSTRAINT properties_pkey PRIMARY KEY (id);


--
-- Name: property_finance_managers property_finance_managers_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.property_finance_managers
    ADD CONSTRAINT property_finance_managers_pkey PRIMARY KEY (id);


--
-- Name: property_managers property_managers_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.property_managers
    ADD CONSTRAINT property_managers_pkey PRIMARY KEY (id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: tenant_documents tenant_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tenant_documents
    ADD CONSTRAINT tenant_documents_pkey PRIMARY KEY (id);


--
-- Name: tenants tenants_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_pkey PRIMARY KEY (id);


--
-- Name: ticket_assignments ticket_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.ticket_assignments
    ADD CONSTRAINT ticket_assignments_pkey PRIMARY KEY (id);


--
-- Name: ticket_attachments ticket_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.ticket_attachments
    ADD CONSTRAINT ticket_attachments_pkey PRIMARY KEY (id);


--
-- Name: ticket_messages ticket_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.ticket_messages
    ADD CONSTRAINT ticket_messages_pkey PRIMARY KEY (id);


--
-- Name: tickets tickets_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_pkey PRIMARY KEY (id);


--
-- Name: units units_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.units
    ADD CONSTRAINT units_pkey PRIMARY KEY (id);


--
-- Name: expense_categories uq_expense_category_org_name; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expense_categories
    ADD CONSTRAINT uq_expense_category_org_name UNIQUE (organization_id, name);


--
-- Name: notification_preferences uq_notification_preferences_user; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.notification_preferences
    ADD CONSTRAINT uq_notification_preferences_user UNIQUE (user_id);


--
-- Name: property_finance_managers uq_property_finance_manager; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.property_finance_managers
    ADD CONSTRAINT uq_property_finance_manager UNIQUE (property_id, user_id);


--
-- Name: property_managers uq_property_manager; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.property_managers
    ADD CONSTRAINT uq_property_manager UNIQUE (property_id, user_id);


--
-- Name: organization_members uq_user_org; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.organization_members
    ADD CONSTRAINT uq_user_org UNIQUE (user_id, organization_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: vendors vendors_pkey; Type: CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.vendors
    ADD CONSTRAINT vendors_pkey PRIMARY KEY (id);


--
-- Name: ix_audit_logs_created_at; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: ix_audit_logs_entity_type; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_audit_logs_entity_type ON public.audit_logs USING btree (entity_type);


--
-- Name: ix_audit_logs_org_created; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_audit_logs_org_created ON public.audit_logs USING btree (organization_id, created_at);


--
-- Name: ix_audit_logs_organization_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_audit_logs_organization_id ON public.audit_logs USING btree (organization_id);


--
-- Name: ix_charges_due_date; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_charges_due_date ON public.charges USING btree (due_date);


--
-- Name: ix_charges_lease_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_charges_lease_id ON public.charges USING btree (lease_id);


--
-- Name: ix_charges_org_due; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_charges_org_due ON public.charges USING btree (organization_id, due_date);


--
-- Name: ix_charges_organization_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_charges_organization_id ON public.charges USING btree (organization_id);


--
-- Name: ix_expenses_expense_date; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_expenses_expense_date ON public.expenses USING btree (expense_date);


--
-- Name: ix_expenses_organization_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_expenses_organization_id ON public.expenses USING btree (organization_id);


--
-- Name: ix_expenses_property_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_expenses_property_id ON public.expenses USING btree (property_id);


--
-- Name: ix_expenses_status; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_expenses_status ON public.expenses USING btree (status);


--
-- Name: ix_messages_phone_number; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_messages_phone_number ON public.messages USING btree (phone_number);


--
-- Name: ix_messages_provider_message_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_messages_provider_message_id ON public.messages USING btree (provider_message_id);


--
-- Name: ix_messages_ticket_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_messages_ticket_id ON public.messages USING btree (ticket_id);


--
-- Name: ix_notifications_is_read; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_notifications_is_read ON public.notifications USING btree (is_read);


--
-- Name: ix_notifications_organization_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_notifications_organization_id ON public.notifications USING btree (organization_id);


--
-- Name: ix_notifications_user_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: ix_organization_invitations_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_organization_invitations_id ON public.organization_invitations USING btree (id);


--
-- Name: ix_organization_members_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_organization_members_id ON public.organization_members USING btree (id);


--
-- Name: ix_otp_verifications_user_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_otp_verifications_user_id ON public.otp_verifications USING btree (user_id);


--
-- Name: ix_password_history_user_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_password_history_user_id ON public.password_history USING btree (user_id);


--
-- Name: ix_payment_review_items_org_status; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_payment_review_items_org_status ON public.payment_review_items USING btree (organization_id, status);


--
-- Name: ix_payment_review_items_payer_phone_hash; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_payment_review_items_payer_phone_hash ON public.payment_review_items USING btree (payer_phone_hash);


--
-- Name: ix_payment_review_items_source; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_payment_review_items_source ON public.payment_review_items USING btree (source);


--
-- Name: ix_payments_lease_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_payments_lease_id ON public.payments USING btree (lease_id);


--
-- Name: ix_payments_org_date; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_payments_org_date ON public.payments USING btree (organization_id, payment_date);


--
-- Name: ix_payments_organization_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_payments_organization_id ON public.payments USING btree (organization_id);


--
-- Name: ix_payments_payment_date; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_payments_payment_date ON public.payments USING btree (payment_date);


--
-- Name: ix_payments_tenant_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_payments_tenant_id ON public.payments USING btree (tenant_id);


--
-- Name: ix_properties_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_properties_id ON public.properties USING btree (id);


--
-- Name: ix_tenants_alternative_phone_hash; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tenants_alternative_phone_hash ON public.tenants USING btree (alternative_phone_hash);


--
-- Name: ix_tenants_email_hash; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tenants_email_hash ON public.tenants USING btree (email_hash);


--
-- Name: ix_tenants_id_number_hash; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tenants_id_number_hash ON public.tenants USING btree (id_number_hash);


--
-- Name: ix_tenants_phone_hash; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tenants_phone_hash ON public.tenants USING btree (phone_hash);


--
-- Name: ix_tenants_user_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tenants_user_id ON public.tenants USING btree (user_id);


--
-- Name: ix_ticket_assignments_ticket_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_ticket_assignments_ticket_id ON public.ticket_assignments USING btree (ticket_id);


--
-- Name: ix_ticket_attachments_ticket_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_ticket_attachments_ticket_id ON public.ticket_attachments USING btree (ticket_id);


--
-- Name: ix_ticket_messages_recipient_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_ticket_messages_recipient_id ON public.ticket_messages USING btree (recipient_id);


--
-- Name: ix_ticket_messages_ticket_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_ticket_messages_ticket_id ON public.ticket_messages USING btree (ticket_id);


--
-- Name: ix_tickets_assigned_to; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tickets_assigned_to ON public.tickets USING btree (assigned_to);


--
-- Name: ix_tickets_created_at; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tickets_created_at ON public.tickets USING btree (created_at);


--
-- Name: ix_tickets_org_created; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tickets_org_created ON public.tickets USING btree (organization_id, created_at);


--
-- Name: ix_tickets_organization_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tickets_organization_id ON public.tickets USING btree (organization_id);


--
-- Name: ix_tickets_property_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tickets_property_id ON public.tickets USING btree (property_id);


--
-- Name: ix_tickets_source_phone; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tickets_source_phone ON public.tickets USING btree (source_phone);


--
-- Name: ix_tickets_status; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tickets_status ON public.tickets USING btree (status);


--
-- Name: ix_tickets_tenant_id; Type: INDEX; Schema: public; Owner: rental_user
--

CREATE INDEX ix_tickets_tenant_id ON public.tickets USING btree (tenant_id);


--
-- Name: audit_logs audit_logs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: charges charges_lease_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.charges
    ADD CONSTRAINT charges_lease_id_fkey FOREIGN KEY (lease_id) REFERENCES public.leases(id) ON DELETE CASCADE;


--
-- Name: charges charges_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.charges
    ADD CONSTRAINT charges_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: checklist_item_templates checklist_item_templates_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.checklist_item_templates
    ADD CONSTRAINT checklist_item_templates_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: expense_attachments expense_attachments_expense_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expense_attachments
    ADD CONSTRAINT expense_attachments_expense_id_fkey FOREIGN KEY (expense_id) REFERENCES public.expenses(id) ON DELETE CASCADE;


--
-- Name: expense_attachments expense_attachments_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expense_attachments
    ADD CONSTRAINT expense_attachments_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id);


--
-- Name: expense_categories expense_categories_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expense_categories
    ADD CONSTRAINT expense_categories_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: expenses expenses_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: expenses expenses_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.expense_categories(id);


--
-- Name: expenses expenses_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: expenses expenses_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: expenses expenses_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE;


--
-- Name: expenses expenses_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES public.units(id) ON DELETE SET NULL;


--
-- Name: expenses expenses_vendor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendors(id) ON DELETE SET NULL;


--
-- Name: messages fk_messages_ticket_id_tickets; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT fk_messages_ticket_id_tickets FOREIGN KEY (ticket_id) REFERENCES public.tickets(id) ON DELETE SET NULL;


--
-- Name: payment_review_items fk_payment_review_items_source_message_id; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payment_review_items
    ADD CONSTRAINT fk_payment_review_items_source_message_id FOREIGN KEY (source_message_id) REFERENCES public.messages(id) ON DELETE SET NULL;


--
-- Name: tenants fk_tenants_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT fk_tenants_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: ticket_messages fk_ticket_messages_recipient_id_users; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.ticket_messages
    ADD CONSTRAINT fk_ticket_messages_recipient_id_users FOREIGN KEY (recipient_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: tickets fk_tickets_assigned_to; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT fk_tickets_assigned_to FOREIGN KEY (assigned_to) REFERENCES public.users(id);


--
-- Name: tickets fk_tickets_created_by; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT fk_tickets_created_by FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: tickets fk_tickets_property_id; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT fk_tickets_property_id FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE SET NULL;


--
-- Name: tickets fk_tickets_unit_id; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT fk_tickets_unit_id FOREIGN KEY (unit_id) REFERENCES public.units(id) ON DELETE SET NULL;


--
-- Name: inspection_items inspection_items_inspection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.inspection_items
    ADD CONSTRAINT inspection_items_inspection_id_fkey FOREIGN KEY (inspection_id) REFERENCES public.lease_inspections(id) ON DELETE CASCADE;


--
-- Name: inspection_notes inspection_notes_inspection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.inspection_notes
    ADD CONSTRAINT inspection_notes_inspection_id_fkey FOREIGN KEY (inspection_id) REFERENCES public.lease_inspections(id) ON DELETE CASCADE;


--
-- Name: inspection_notes inspection_notes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.inspection_notes
    ADD CONSTRAINT inspection_notes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: lease_inspections lease_inspections_inspector_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.lease_inspections
    ADD CONSTRAINT lease_inspections_inspector_user_id_fkey FOREIGN KEY (inspector_user_id) REFERENCES public.users(id);


--
-- Name: lease_inspections lease_inspections_lease_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.lease_inspections
    ADD CONSTRAINT lease_inspections_lease_id_fkey FOREIGN KEY (lease_id) REFERENCES public.leases(id) ON DELETE CASCADE;


--
-- Name: leases leases_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.leases
    ADD CONSTRAINT leases_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: leases leases_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.leases
    ADD CONSTRAINT leases_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: leases leases_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.leases
    ADD CONSTRAINT leases_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES public.units(id);


--
-- Name: messages messages_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: messages messages_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE SET NULL;


--
-- Name: messages messages_triggered_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_triggered_by_user_id_fkey FOREIGN KEY (triggered_by_user_id) REFERENCES public.users(id);


--
-- Name: notification_preferences notification_preferences_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.notification_preferences
    ADD CONSTRAINT notification_preferences_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: notification_preferences notification_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.notification_preferences
    ADD CONSTRAINT notification_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: organization_invitations organization_invitations_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.organization_invitations
    ADD CONSTRAINT organization_invitations_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: organization_invitations organization_invitations_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.organization_invitations
    ADD CONSTRAINT organization_invitations_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: organization_members organization_members_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.organization_members
    ADD CONSTRAINT organization_members_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: organization_members organization_members_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.organization_members
    ADD CONSTRAINT organization_members_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: organization_members organization_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.organization_members
    ADD CONSTRAINT organization_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: organizations organizations_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: otp_verifications otp_verifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.otp_verifications
    ADD CONSTRAINT otp_verifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: password_history password_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.password_history
    ADD CONSTRAINT password_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: payment_review_items payment_review_items_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payment_review_items
    ADD CONSTRAINT payment_review_items_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: payment_review_items payment_review_items_lease_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payment_review_items
    ADD CONSTRAINT payment_review_items_lease_id_fkey FOREIGN KEY (lease_id) REFERENCES public.leases(id) ON DELETE SET NULL;


--
-- Name: payment_review_items payment_review_items_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payment_review_items
    ADD CONSTRAINT payment_review_items_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: payment_review_items payment_review_items_resolution_payment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payment_review_items
    ADD CONSTRAINT payment_review_items_resolution_payment_id_fkey FOREIGN KEY (resolution_payment_id) REFERENCES public.payments(id) ON DELETE SET NULL;


--
-- Name: payment_review_items payment_review_items_resolved_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payment_review_items
    ADD CONSTRAINT payment_review_items_resolved_by_user_id_fkey FOREIGN KEY (resolved_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: payment_review_items payment_review_items_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payment_review_items
    ADD CONSTRAINT payment_review_items_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE SET NULL;


--
-- Name: payments payments_lease_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_lease_id_fkey FOREIGN KEY (lease_id) REFERENCES public.leases(id) ON DELETE CASCADE;


--
-- Name: payments payments_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: payments payments_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: properties properties_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.properties
    ADD CONSTRAINT properties_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: property_finance_managers property_finance_managers_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.property_finance_managers
    ADD CONSTRAINT property_finance_managers_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE;


--
-- Name: property_finance_managers property_finance_managers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.property_finance_managers
    ADD CONSTRAINT property_finance_managers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: property_managers property_managers_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.property_managers
    ADD CONSTRAINT property_managers_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE;


--
-- Name: property_managers property_managers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.property_managers
    ADD CONSTRAINT property_managers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: tenant_documents tenant_documents_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tenant_documents
    ADD CONSTRAINT tenant_documents_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: tenant_documents tenant_documents_uploaded_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tenant_documents
    ADD CONSTRAINT tenant_documents_uploaded_by_user_id_fkey FOREIGN KEY (uploaded_by_user_id) REFERENCES public.users(id);


--
-- Name: tenants tenants_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: ticket_assignments ticket_assignments_assigned_from_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.ticket_assignments
    ADD CONSTRAINT ticket_assignments_assigned_from_fkey FOREIGN KEY (assigned_from) REFERENCES public.users(id);


--
-- Name: ticket_assignments ticket_assignments_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.ticket_assignments
    ADD CONSTRAINT ticket_assignments_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id);


--
-- Name: ticket_assignments ticket_assignments_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.ticket_assignments
    ADD CONSTRAINT ticket_assignments_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.tickets(id) ON DELETE CASCADE;


--
-- Name: ticket_attachments ticket_attachments_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.ticket_attachments
    ADD CONSTRAINT ticket_attachments_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.tickets(id) ON DELETE CASCADE;


--
-- Name: ticket_attachments ticket_attachments_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.ticket_attachments
    ADD CONSTRAINT ticket_attachments_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id);


--
-- Name: ticket_messages ticket_messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.ticket_messages
    ADD CONSTRAINT ticket_messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id);


--
-- Name: ticket_messages ticket_messages_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.ticket_messages
    ADD CONSTRAINT ticket_messages_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.tickets(id) ON DELETE CASCADE;


--
-- Name: tickets tickets_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: tickets tickets_source_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_source_message_id_fkey FOREIGN KEY (source_message_id) REFERENCES public.messages(id) ON DELETE SET NULL;


--
-- Name: tickets tickets_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE SET NULL;


--
-- Name: units units_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.units
    ADD CONSTRAINT units_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE;


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: vendors vendors_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: rental_user
--

ALTER TABLE ONLY public.vendors
    ADD CONSTRAINT vendors_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

