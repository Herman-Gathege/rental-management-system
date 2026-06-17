/* frontend/src/config/navigation.js */
//
// Single source of truth for sidebar + navbar menus (Sprint 4.5, Chunk 5).
// Sidebar.jsx and Navbar.jsx both render from these arrays — no menu is
// hardcoded in JSX anymore. Each role's menu follows the role-dashboard guide
// (Phase 8). Items with `children` render as collapsible groups; items with a
// `path` render as a single link.

import {
  FiHome,
  FiUsers,
  FiFileText,
  FiSettings,
  FiBriefcase,
  FiDollarSign,
  FiKey,
  FiLayers,
  FiCheckSquare,
  FiUser,
  FiUploadCloud,
  FiBarChart2,
} from "react-icons/fi";

/* ================= LANDLORD / PORTFOLIO OWNER =================
 * Reconciled to match the existing landlord sidebar exactly so this
 * refactor doesn't change the owner experience.
 */
export const ownerNavigation = [
  { label: "Dashboard", icon: FiHome, path: "/owner/dashboard" },

  {
    label: "Properties",
    icon: FiBriefcase,
    children: [
      { label: "All Properties", path: "/owner/properties" },
      { label: "Add Property", path: "/owner/properties/new" },
    ],
  },

  {
    label: "Units",
    icon: FiLayers,
    children: [
      { label: "All Units", path: "/owner/units" },
      { label: "Vacant Units", path: "/owner/units/vacant" },
      { label: "Add Unit", path: "/owner/units/add" },
    ],
  },

  {
    label: "Tenants",
    icon: FiUsers,
    children: [
      { label: "All Tenants", path: "/owner/tenants" },
      { label: "Add Tenant", path: "/owner/tenants/add" },
      { label: "Notices & Evictions", path: "/owner/tenants/notices" },
    ],
  },

  {
    label: "Leases",
    icon: FiFileText,
    children: [
      { label: "Active Leases", path: "/owner/leases" },
      { label: "Create Lease", path: "/owner/leases/create" },
      { label: "Expired Leases", path: "/owner/leases/expired" },
    ],
  },

  {
    label: "Rent & Payments",
    icon: FiDollarSign,
    children: [
      { label: "Rent Dashboard", path: "/owner/billing" },
      { label: "Payment History", path: "/owner/payments/history" },
      { label: "Batch Upload", path: "/owner/payments/batch" },
    ],
  },

  { label: "Team", icon: FiKey, path: "/owner/team" },
  { label: "Settings", icon: FiSettings, path: "/owner/settings" },
  { label: "Profile", icon: FiUser, path: "/owner/profile" },
];

/* ================= PROPERTY MANAGER =================
 * Guide Phase 8: Dashboard, Properties, Units, Tenants, Leases.
 * Paths use /manager/* (matches the StaffLayout mount in AppRoutes).
 */
export const staffNavigation = [
  { label: "Dashboard", icon: FiHome, path: "/manager/dashboard" },
  { label: "Properties", icon: FiBriefcase, path: "/manager/properties" },
  { label: "Units", icon: FiLayers, path: "/manager/units" },
  { label: "Tenants", icon: FiUsers, path: "/manager/tenants" },
  { label: "Leases", icon: FiFileText, path: "/manager/leases" },
  { label: "Profile", icon: FiUser, path: "/manager/profile" },
];

/* ================= FINANCE =================
 * Guide Phase 8: Dashboard, Billing, Payments, Finance.
 * Paths use /finance/* (matches the finance mount in AppRoutes).
 * Distinct icons per menu (was all FiDollarSign): Billing=invoices,
 * Payments=money in, Batch Upload=upload, Finance=analytics.
 */
export const financeNavigation = [
  { label: "Dashboard", icon: FiHome, path: "/finance" },
  { label: "Billing", icon: FiFileText, path: "/finance/billing" },
  { label: "Payments", icon: FiDollarSign, path: "/finance/payments" },
  { label: "Batch Upload", icon: FiUploadCloud, path: "/finance/payments/batch" },
  { label: "Finance", icon: FiBarChart2, path: "/finance/finance" },
  { label: "Profile", icon: FiUser, path: "/finance/profile" },
];

/* ================= TENANT =================
 * Guide Phase 8: Dashboard, My Lease, My Payments, My Charges.
 * Lease Checklist (Sprint 4.5 spinoff): read-only move-in / move-out
 * inspection records for the tenant.
 */
export const tenantNavigation = [
  { label: "Dashboard", icon: FiHome, path: "/tenant" },
  { label: "My Lease", icon: FiFileText, path: "/tenant/lease" },
  { label: "Lease Checklist", icon: FiCheckSquare, path: "/tenant/inspections" },
  { label: "My Payments", icon: FiDollarSign, path: "/tenant/payments" },
  { label: "My Charges", icon: FiDollarSign, path: "/tenant/charges" },
  { label: "Profile", icon: FiUser, path: "/tenant/profile" },
];

/* ================= SYSTEM / SUPER ADMIN ================= */
export const superAdminNavigation = [
  { label: "Dashboard", icon: FiHome, path: "/super-admin/dashboard" },
  { label: "Organizations", icon: FiUsers, path: "/super-admin/organizations" },
  { label: "Profile", icon: FiUser, path: "/super-admin/profile" },
];

/* ================= MOBILE BOTTOM NAV =================
 * Per-role quick links for the mobile bottom bar (rendered by
 * components/BottomNav.jsx). Keep to 3–4 high-traffic destinations; the full
 * menu stays reachable via the navbar. Paths must match the role's mount in
 * AppRoutes. `end: true` is for index paths that are a prefix of their siblings
 * (e.g. "/tenant" is a prefix of "/tenant/lease"), so they only highlight on an
 * exact match.
 */
export const ownerBottomNav = [
  { label: "Home", icon: FiHome, path: "/owner/dashboard" },
  { label: "Properties", icon: FiBriefcase, path: "/owner/properties" },
  { label: "Tenants", icon: FiUsers, path: "/owner/tenants" },
  { label: "Payments", icon: FiDollarSign, path: "/owner/payments/history" },
];

export const staffBottomNav = [
  { label: "Home", icon: FiHome, path: "/manager/dashboard" },
  { label: "Properties", icon: FiBriefcase, path: "/manager/properties" },
  { label: "Tenants", icon: FiUsers, path: "/manager/tenants" },
];

export const tenantBottomNav = [
  { label: "Home", icon: FiHome, path: "/tenant", end: true },
  { label: "Lease", icon: FiFileText, path: "/tenant/lease" },
  { label: "Payments", icon: FiDollarSign, path: "/tenant/payments" },
  { label: "Charges", icon: FiDollarSign, path: "/tenant/charges" },
];

export const financeBottomNav = [
  { label: "Home", icon: FiHome, path: "/finance", end: true },
  { label: "Billing", icon: FiFileText, path: "/finance/billing" },
  { label: "Payments", icon: FiDollarSign, path: "/finance/payments" },
  { label: "Finance", icon: FiBarChart2, path: "/finance/finance" },
];

export const superAdminBottomNav = [
  { label: "Home", icon: FiHome, path: "/super-admin/dashboard" },
  { label: "Orgs", icon: FiUsers, path: "/super-admin/organizations" },
];