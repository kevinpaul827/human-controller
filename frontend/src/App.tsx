import { HashRouter } from "react-router-dom";
import AppStateProvider from "./state/AppStateProvider";
import ActiveProfileProvider from "./context/ActiveProfileProvider";
import AppRoutes from "./routes/AppRoutes";

const App = () => (
  <HashRouter>
    <AppStateProvider>
      <ActiveProfileProvider>
        <AppRoutes />
      </ActiveProfileProvider>
    </AppStateProvider>
  </HashRouter>
);

export default App;
