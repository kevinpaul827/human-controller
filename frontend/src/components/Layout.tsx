import { useState } from "react";
import { Outlet } from "react-router-dom";
import Header from "./Header";
import NavBar from "./NavBar";
import styles from "../styles/layout.module.css";

const Layout = () => {
  const [isNavOpen, setIsNavOpen] = useState(true);

  return (
    <div className={styles.appShell}>
      <Header />
      <div className={styles.bodyShell}>
        <NavBar
          isOpen={isNavOpen}
          onToggle={() => setIsNavOpen((open) => !open)}
        />
        <main className={styles.mainContent}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
