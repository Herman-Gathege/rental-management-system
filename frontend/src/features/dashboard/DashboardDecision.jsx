//frontend/src/features/dashboard/DashboardDecision.jsx
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function DashboardDecision() {
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) return;

    switch (user.role) {
      case "landlord":
        navigate("/owner");
        break;
      case "property_manager":
        navigate("/manager");
        break;
      case "finance":
        navigate("/finance");
        break;
      case "tenant":
        navigate("/tenant");
        break;
      case "super_admin":
        navigate("/super-admin");
        break;
      default:
        navigate("/");
    }
  }, [user, navigate]);

  return <p>Redirecting to your dashboard...</p>;
}