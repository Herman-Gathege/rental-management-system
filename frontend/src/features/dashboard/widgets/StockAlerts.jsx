//frontend/src/features/dashboard/widgets/StockAlerts.jsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getStockAlerts } from "../../../api/dashboard";



export default function StockAlerts() {
  const [alerts, setAlerts] = useState([]);
  const navigate = useNavigate();
  // const API_BASE = import.meta.env.VITE_API_URL;

  useEffect(() => {
  const fetchAlerts = async () => {
    try {
      const data = await getStockAlerts();
      setAlerts(data);
    } catch (err) {
      console.error(err);
    }
  };

  fetchAlerts();
}, []);


  const outOfStock = alerts.filter((i) => i.quantity === 0).length;
  const lowStock = alerts.filter(
    (i) => i.quantity > 0 && i.quantity <= i.min_stock_level
  ).length;

  
  return (
    <div
      className="card-w flex flex-col gap-sm cursor-pointer"
      onClick={() => navigate("/owner/stock")}
    >
      <h3 className="text-md text-bold">Stock Alerts</h3>

      <div className="flex flex-col gap-sm">
        {outOfStock > 0 && (
          <span className="text-error">
            🔴 {outOfStock} item(s) out of stock
          </span>
        )}

        {lowStock > 0 && (
          <span className="text-warning">
            🟧 {lowStock} item(s) running low
          </span>
        )}

        {outOfStock === 0 && lowStock === 0 && (
          <span className="text-success">
            ✅ All stock levels look good today
          </span>
        )}
      </div>

      <span className="text-sm text-muted">View stock →</span>
    </div>
  );
}
