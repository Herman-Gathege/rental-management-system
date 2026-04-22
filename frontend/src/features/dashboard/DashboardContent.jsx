// frontend/src/features/dashboard/DashboardContent.jsx
import { useAuth } from "../../context/AuthContext";


export default function DashboardContent({ roleLabel }) {
  const { user, organization } = useAuth();

  if (!user) return null; // or a loading spinner

  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">
        Welcome, <span className="company-blue text-bold">{user.full_name}</span> 👋
      </div>

      
        

    </div>
  );
}

