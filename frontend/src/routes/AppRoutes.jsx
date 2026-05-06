//frontend/src/routes/AppRoutes.jsx
import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";

import Home from "../pages/Home";
import Login from "../features/auth/Login";
import Register from "../features/auth/Register";
import DashboardDecision from "../features/dashboard/DashboardDecision";

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

/* PROPERTY MANAGER */
import StaffLayout from "../features/dashboard/layout/StaffLayout";
import StaffDashboard from "../features/dashboard/StaffDashboard";

/* FINANCE */
import FinanceDashboard from "../features/dashboard/FinanceDashboard";

/* TENANT */
import TenantDashboard from "../features/dashboard/TenantDashboard";

/* SUPER ADMIN (future SaaS owner) */
import SuperAdminLayout from "../features/dashboard/layout/SuperAdminLayout";
import SuperAdminDashboard from "../features/dashboard/SuperAdminDashboard";

export default function AppRoutes() {
  return (
    <Routes>
      {/* PUBLIC */}
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

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
        <Route path="team" element={<Team />} />
        <Route path="staff" element={<Team />} />

        {/* Sprint 3 routes */}
        <Route path="units" element={<Units />} />
        <Route path="units/add" element={<CreateUnit />} />
        <Route path="units/vacant" element={<Units />} />
        <Route path="tenants" element={<Tenants />} />
        <Route path="tenants/add" element={<CreateTenant />} />
        <Route path="leases" element={<Leases />} />
        <Route path="leases/create" element={<CreateLease />} />
        <Route path="leases/:leaseId" element={<LeaseDetail />} />
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
