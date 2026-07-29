import { Outlet } from "react-router-dom";
import Header from "./Header";
import UndoBar from "./UndoBar";

const Layout = () => (
  <div className="flex h-full flex-col overflow-hidden">
    <Header />
    <main className="min-h-0 flex-1 overflow-y-auto">
      <Outlet />
    </main>
    <UndoBar />
  </div>
);

export default Layout;
