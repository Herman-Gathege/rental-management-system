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
      case "LANDLORD":
        navigate("/owner");
        break;
      case "PROPERTY_MANAGER":
        navigate("/manager");
        break;
      case "FINANCE":
        navigate("/finance");
        break;
      case "TENANT":
        navigate("/tenant");
        break;
      case "SYSTEM":
        navigate("/super-admin");
        break;
      default:
        navigate("/");
    }
  }, [user, navigate]);

  return <p>Redirecting to your dashboard...</p>;
}
