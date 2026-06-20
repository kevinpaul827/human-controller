import { Outlet } from "react-router-dom";
import Header from "./Header";
import NavBar from "./NavBar";
import styles from "../styles/layout.module.css";

const Layout = () => (
  <div className={styles.appShell}>
    <Header />
    <div className={styles.bodyShell}>
      <NavBar />
      <main className={styles.mainContent}>
        <Outlet />
      </main>
    </div>
  </div>
);

export default Layout;
