import MenuIcon from "@mui/icons-material/Menu";
import { Box, Button, IconButton } from "@mui/material";
import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "../utils/constants";
import styles from "../styles/navigation.module.css";

const NavBar = () => (
  <aside className={styles.sidebar}>
    <Box className={styles.sidebarHeader}>
      <IconButton edge="start" aria-label="menu" className={styles.menuButton}>
        <MenuIcon className={styles.menuIcon} />
      </IconButton>
    </Box>
    <Box className={styles.navActions}>
      {NAV_ITEMS.map((item) => (
        <Button
          key={item.path}
          component={NavLink}
          to={item.path}
          className={styles.navButton}
        >
          {item.label}
        </Button>
      ))}
    </Box>
  </aside>
);

export default NavBar;
