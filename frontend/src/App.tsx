import { HashRouter } from "react-router-dom";
import ActiveProfileProvider from "./context/ActiveProfileProvider";
import AppRoutes from "./routes/AppRoutes";

const App = () => (
  <HashRouter>
    <ActiveProfileProvider>
      <AppRoutes />
    </ActiveProfileProvider>
  </HashRouter>
);

export default App;
