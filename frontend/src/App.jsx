/*frontend\src\App.jsx*/

import AppRoutes from "./routes/AppRoutes";
import { PropertyProvider } from "./context/PropertyContext";
import "./index.css";
import "./styles/base.css";
import "./styles/layout.css";
import "./styles/components.css";
import "./styles/utilities.css";
import "./styles/dashboard.css";
import "./styles/customers.css";
import "./styles/pos.css";
import "./styles/properties.css";
import "./styles/team.css";
import "./styles/inspection.css";

function App() {
  return (
    <PropertyProvider>
      <AppRoutes />
    </PropertyProvider>
  );
}

export default App;
