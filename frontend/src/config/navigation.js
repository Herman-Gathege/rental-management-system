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
      { label: "Late Payments", path: "/owner/payments/late" },
    ],
  },

  { label: "Team", icon: FiKey, path: "/owner/team" },
  { label: "Settings", icon: FiSettings, path: "/owner/settings" },
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
];

/* ================= FINANCE =================
 * Guide Phase 8: Dashboard, Billing, Payments, Finance.
 * Paths use /finance/* (matches the finance mount in AppRoutes).
 */
export const financeNavigation = [
  { label: "Dashboard", icon: FiHome, path: "/finance" },
  { label: "Billing", icon: FiDollarSign, path: "/finance/billing" },
  { label: "Payments", icon: FiDollarSign, path: "/finance/payments" },
  { label: "Batch Upload", icon: FiDollarSign, path: "/finance/payments/batch" },
  { label: "Finance", icon: FiDollarSign, path: "/finance/finance" },
];

/* ================= TENANT =================
 * Guide Phase 8: Dashboard, My Lease, My Payments, My Charges.
 * Lease Checklist (Sprint 4.5 spinoff): read-only move-in / move-out
 * inspection records for the tenant.
 */
export const tenantNavigation = [
  { label: "Dashboard", icon: FiHome, path: "/tenant" },
  { label: "My Lease", icon: FiFileText, path: "/tenant/lease" },
  { label: "My Payments", icon: FiDollarSign, path: "/tenant/payments" },
  { label: "My Charges", icon: FiDollarSign, path: "/tenant/charges" },
  { label: "Lease Checklist", icon: FiCheckSquare, path: "/tenant/inspections" },
];

/* ================= SYSTEM / SUPER ADMIN ================= */
export const superAdminNavigation = [
  { label: "Dashboard", icon: FiHome, path: "/super-admin/dashboard" },
  { label: "Organizations", icon: FiUsers, path: "/super-admin/organizations" },
];
