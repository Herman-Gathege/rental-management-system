/* frontend\src\config\navigation.js */
import {
  FiHome,
  FiUsers,
  FiFileText,
  FiSettings,
  FiBriefcase,
  FiDollarSign,
  FiKey,
  FiLayers,
} from "react-icons/fi";

/* ================= LANDLORD / PORTFOLIO OWNER ================= */
export const ownerNavigation = [
  {
    label: "Dashboard",
    icon: FiHome,
    path: "/owner/dashboard",
  },
  /* PROPERTIES */
  {
    label: "Properties",
    icon: FiBriefcase,
    children: [
      { label: "All Properties", path: "/owner/properties" },
      { label: "Add Property", path: "/owner/properties/new" },
    ],
  },
  /* UNITS */
  {
    label: "Units",
    icon: FiLayers,
    children: [
      { label: "All Units", path: "/owner/units" },
      { label: "Vacant Units", path: "/owner/units/vacant" },
      { label: "Add Unit", path: "/owner/units/add" },
    ],
  },
  /* TENANTS */
  {
    label: "Tenants",
    icon: FiUsers,
    children: [
      { label: "All Tenants", path: "/owner/tenants" },
      { label: "Add Tenant", path: "/owner/tenants/add" },
      { label: "Notice & Evictions", path: "/owner/tenants/notices" },
    ],
  },
  /* LEASES */
  {
    label: "Leases",
    icon: FiFileText,
    children: [
      { label: "Active Leases", path: "/owner/leases" },
      { label: "Create Lease", path: "/owner/leases/create" },
      { label: "Expired Leases", path: "/owner/leases/expired" },
    ],
  },
  /* RENT & PAYMENTS */
  {
    label: "Rent & Payments",
    icon: FiDollarSign,
    children: [
      { label: "Rent Dashboard", path: "/owner/payments" },
      { label: "Payment History", path: "/owner/payments/history" },
      { label: "Late Payments", path: "/owner/payments/late" },
    ],
  },
  /* FINANCE TEAM */
  {
    label: "Finance",
    icon: FiDollarSign,
    children: [
      { label: "Expenses", path: "/owner/finance/expenses" },
      { label: "Invoices", path: "/owner/finance/invoices" },
      { label: "Reports", path: "/owner/reports" },
    ],
  },
  /* TEAM - Sprint 2 */
  {
    label: "Team",
    icon: FiKey,
    children: [
      { label: "All Members", path: "/owner/team" },
      { label: "Invite Member", path: "/owner/team" },
    ],
  },
  {
    label: "Settings",
    icon: FiSettings,
    path: "/owner/settings",
  },
];

/* ================= PROPERTY MANAGER / STAFF =================
 * NOTE: paths use /manager/* to match AppRoutes.jsx which mounts
 * the StaffLayout at /manager/*. Earlier these used /staff/* which
 * 404'd silently.
 */
export const staffNavigation = [
  {
    label: "Dashboard",
    icon: FiHome,
    path: "/manager/dashboard",
  },
  {
    label: "Properties",
    icon: FiBriefcase,
    path: "/manager/properties",
  },
  {
    label: "Tenants",
    icon: FiUsers,
    path: "/manager/tenants",
  },
  {
    label: "Leases",
    icon: FiFileText,
    path: "/manager/leases",
  },
  {
    label: "Payments",
    icon: FiDollarSign,
    path: "/manager/payments",
  },
  {
    label: "My Profile",
    icon: FiUsers,
    path: "/manager/profile",
  },
  {
    label: "Change Password",
    icon: FiSettings,
    path: "/manager/password",
  },
];

/* ================= TENANT =================
 * Minimal tenant nav. Most paths route to TenantDashboard via the
 * /tenant/* index fallback today — real per-section pages can be
 * built out without changing this nav (just add the routes).
 */
export const tenantNavigation = [
  {
    label: "Dashboard",
    icon: FiHome,
    path: "/tenant",
  },
  {
    label: "My Lease",
    icon: FiFileText,
    path: "/tenant/lease",
  },
  {
    label: "My Payments",
    icon: FiDollarSign,
    path: "/tenant/payments",
  },
  {
    label: "My Profile",
    icon: FiUsers,
    path: "/tenant/profile",
  },
  {
    label: "Change Password",
    icon: FiSettings,
    path: "/tenant/password",
  },
];

/* ================= SYSTEM / SUPER ADMIN ================= */
export const superAdminNavigation = [
  {
    label: "Dashboard",
    icon: FiHome,
    path: "/super-admin/dashboard",
  },
  {
    label: "Organizations",
    icon: FiUsers,
    path: "/super-admin/organizations",
  },
];