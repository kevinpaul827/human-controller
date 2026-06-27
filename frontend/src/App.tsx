import { HashRouter } from "react-router-dom";
import AppRoutes from "./routes/AppRoutes";

const App = () => (
  <HashRouter>
    <AppRoutes />
  </HashRouter>
);

export default App;
