import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "../components/Layout";
import Library from "../pages/Library";
import Profiles from "../pages/Profiles";
import Calibrate from "../pages/Calibrate";
import Session from "../pages/Session";
import Settings from "../pages/Settings";
import { ROUTES } from "../utils/constants";

const AppRoutes = () => (
  <Routes>
    <Route element={<Layout />}>
      <Route path={ROUTES.profiles} element={<Profiles />} />
      <Route path={ROUTES.calibrate} element={<Calibrate />} />
      <Route path={ROUTES.session} element={<Session />} />
      <Route path={ROUTES.settings} element={<Settings />} />
      <Route path={ROUTES.library} element={<Library />} />
      <Route path="*" element={<Navigate to={ROUTES.session} replace />} />
    </Route>
  </Routes>
);

export default AppRoutes;
