/*frontend\src\config\navigation.js */
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

  /* TEAM — Sprint 2 */
  {
    label: "Team",
    icon: FiKey,
    children: [
      { label: "Team", path: "/owner/team" },
      { label: "Invite Team Member", path: "/owner/team/invite" },
    ],
  },

  {
    label: "Settings",
    icon: FiSettings,
    path: "/owner/settings",
  },
];

/* ================= PROPERTY MANAGER / STAFF ================= */

export const staffNavigation = [
  {
    label: "Dashboard",
    icon: FiHome,
    path: "/staff",
  },
  {
    label: "Properties",
    icon: FiBriefcase,
    path: "/staff/properties",
  },
  {
    label: "Tenants",
    icon: FiUsers,
    path: "/staff/tenants",
  },
  {
    label: "Leases",
    icon: FiFileText,
    path: "/staff/leases",
  },
  {
    label: "Payments",
    icon: FiDollarSign,
    path: "/staff/payments",
  },
  {
    label: "My Profile",
    icon: FiUsers,
    path: "/staff/profile",
  },
  {
    label: "Change Password",
    icon: FiSettings,
    path: "/staff/password",
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
