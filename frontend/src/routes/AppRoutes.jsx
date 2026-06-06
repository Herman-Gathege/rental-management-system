//frontend\src\routes\AppRoutes.jsx
import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import Home from "../pages/Home";
import Login from "../features/auth/Login";
import Register from "../features/auth/Register";
import DashboardDecision from "../features/dashboard/DashboardDecision";
import AcceptInvitation from "../features/team/AcceptInvitation";
import RegisterInvite from "../features/auth/RegisterInvite";

/* LANDLORD LAYOUT */
import DashboardLayout from "../features/dashboard/layout/DashboardLayout";
import OwnerDashboard from "../features/dashboard/OwnerDashboard";

/* SPRINT 2 — Properties & Team */
import Properties from "../features/properties/Properties";
import CreateProperty from "../features/properties/CreateProperty";
import PropertyDetail from "../features/properties/PropertyDetail";
import Team from "../features/team/Team";

/* SPRINT 3 — Units, Tenants, Leases */
import Units from "../features/units/Units";
import CreateUnit from "../features/units/CreateUnit";
import Tenants from "../features/tenants/Tenants";
import CreateTenant from "../features/tenants/CreateTenant";
import Leases from "../features/leases/Leases";
import CreateLease from "../features/leases/CreateLease";
import LeaseDetail from "../features/leases/LeaseDetail";

/* SPRINT 4 — Billing, Payments, Finance */
import Billing from "../features/billing/Billing";
import PaymentsList from "../features/payments/Payments";
import RecordPayment from "../features/payments/RecordPayment";
import FinancialDashboard from "../features/finance/FinancialDashboard";

/* Edit Pages */
import EditProperty from "../features/properties/EditProperty";
import EditUnit from "../features/units/EditUnit";
import EditTenant from "../features/tenants/EditTenant";

/* History / Audit */
import History from "../features/history/History";

/* Settings */
import Settings from "../features/settings/Settings";
import ChecklistTemplate from "../features/settings/ChecklistTemplate";

/* Inspections */
import ConductInspection from "../features/inspections/ConductInspection";

/* PROPERTY MANAGER */
import StaffLayout from "../features/dashboard/layout/StaffLayout";
import StaffDashboard from "../features/dashboard/StaffDashboard";

/* FINANCE */
import FinanceDashboard from "../features/dashboard/FinanceDashboard";

/* TENANT */
import TenantDashboard from "../features/dashboard/TenantDashboard";
import TenantPayments from "../features/dashboard/TenantPayments";
import TenantCharges from "../features/dashboard/TenantCharges";
import TenantLease from "../features/dashboard/TenantLease";

/* SUPER ADMIN (future SaaS owner) */
import SuperAdminLayout from "../features/dashboard/layout/SuperAdminLayout";
import SuperAdminDashboard from "../features/dashboard/SuperAdminDashboard";

/* Sprint 4.5 Chunk 5 — placeholder for not-yet-built role-scoped pages */
import ComingSoon from "../components/ComingSoon";

export default function AppRoutes() {
  return (
    <Routes>
      {/* PUBLIC */}
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/accept-invite/:token" element={<AcceptInvitation />} />
      <Route path="/register-invite/:token" element={<RegisterInvite />} />

      {/* ROLE DECIDER AFTER LOGIN */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardDecision />
          </ProtectedRoute>
        }
      />

      {/* ================= LANDLORD ================= */}
      <Route
        path="/owner/*"
        element={
          <ProtectedRoute allowedRoles={["LANDLORD"]}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<OwnerDashboard />} />
        <Route path="dashboard" element={<OwnerDashboard />} />

        {/* Sprint 2 routes */}
        <Route path="properties" element={<Properties />} />
        <Route path="properties/new" element={<CreateProperty />} />
        <Route path="properties/:propertyId" element={<PropertyDetail />} />
        <Route path="properties/:propertyId/edit" element={<EditProperty />} />
        <Route path="team" element={<Team />} />
        <Route path="staff" element={<Team />} />

        {/* Sprint 3 routes */}
        <Route path="units" element={<Units />} />
        <Route path="units/add" element={<CreateUnit />} />
        <Route path="units/:unitId/edit" element={<EditUnit />} />
        <Route path="units/vacant" element={<Units />} />
        <Route path="tenants" element={<Tenants />} />
        <Route path="tenants/add" element={<CreateTenant />} />
        <Route path="tenants/:tenantId" element={<EditTenant />} />
        <Route path="tenants/:tenantId/edit" element={<EditTenant />} />

        {/* Leases */}
        <Route path="leases" element={<Leases />} />
        <Route path="leases/expired" element={<Leases />} />
        <Route path="leases/create" element={<CreateLease />} />
        <Route path="leases/:leaseId" element={<LeaseDetail />} />

        {/* Inspections — under the lease */}
        <Route
          path="leases/:leaseId/inspections/:inspectionId"
          element={<ConductInspection />}
        />

        {/* Sprint 4 routes */}
        <Route path="billing" element={<Billing />} />
        <Route path="payments" element={<PaymentsList />} />
        <Route path="payments/record" element={<RecordPayment />} />
        <Route path="payments/history" element={<PaymentsList />} />
        <Route path="payments/late" element={<Billing />} />
        <Route path="finance" element={<FinancialDashboard />} />
        <Route path="finance/expenses" element={<FinancialDashboard />} />

        {/* History / Audit */}
        <Route path="history" element={<History />} />

        {/* Settings */}
        <Route path="settings" element={<Settings />} />
        <Route path="settings/checklist" element={<ChecklistTemplate />} />
      </Route>

      {/* ================= PROPERTY MANAGER ================= */}
      <Route
        path="/manager/*"
        element={
          <ProtectedRoute allowedRoles={["PROPERTY_MANAGER"]}>
            <StaffLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<StaffDashboard />} />
        <Route path="dashboard" element={<StaffDashboard />} />

        {/* Sprint 4.5 Chunk 5 — menu targets.
            These open placeholders for now; the real role-scoped pages
            (assigned properties only, etc.) come in Layer 2. */}
        <Route path="properties" element={<ComingSoon title="Properties" />} />
        <Route path="units" element={<ComingSoon title="Units" />} />
        <Route path="tenants" element={<ComingSoon title="Tenants" />} />
        <Route path="leases" element={<ComingSoon title="Leases" />} />
      </Route>

      {/* ================= FINANCE ================= */}
      <Route
        path="/finance/*"
        element={
          <ProtectedRoute allowedRoles={["FINANCE"]}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<FinanceDashboard />} />
        <Route path="dashboard" element={<FinanceDashboard />} />

        {/* Sprint 4.5 Chunk 5 — finance reuses the org-wide financial pages
            (finance is permitted to see all org money). */}
        <Route path="billing" element={<Billing />} />
        <Route path="payments" element={<PaymentsList />} />
        <Route path="finance" element={<FinancialDashboard />} />
      </Route>

      {/* ================= TENANT ================= */}
      <Route
        path="/tenant/*"
        element={
          <ProtectedRoute allowedRoles={["TENANT"]}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<TenantDashboard />} />

        {/* Sprint 4.5 tenant portal — all three sub-pages now live. */}
        <Route path="lease" element={<TenantLease />} />
        <Route path="payments" element={<TenantPayments />} />
        <Route path="charges" element={<TenantCharges />} />
      </Route>

      {/* ================= SUPER ADMIN ================= */}
      <Route
        path="/super-admin/*"
        element={
          <ProtectedRoute allowedRoles={["SYSTEM"]}>
            <SuperAdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<SuperAdminDashboard />} />
      </Route>
    </Routes>
  );
}
