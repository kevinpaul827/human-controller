import { HashRouter } from "react-router-dom";
import AppStateProvider from "./state/AppStateProvider";
import AppRoutes from "./routes/AppRoutes";

const App = () => (
  <AppStateProvider>
    <HashRouter>
      <AppRoutes />
    </HashRouter>
  </AppStateProvider>
);

export default App;
