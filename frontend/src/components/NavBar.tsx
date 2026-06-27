import HomeOutlinedIcon from "@mui/icons-material/HomeOutlined";
import MenuIcon from "@mui/icons-material/Menu";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import SportsEsportsOutlinedIcon from "@mui/icons-material/SportsEsportsOutlined";
import TuneOutlinedIcon from "@mui/icons-material/TuneOutlined";
import { Box, Button, IconButton } from "@mui/material";
import type { ReactElement } from "react";
import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "../utils/constants";
import styles from "../styles/navigation.module.css";

type NavBarProps = {
  isOpen: boolean;
  onToggle: () => void;
};

const navIcons: Record<string, ReactElement> = {
  Home: <HomeOutlinedIcon />,
  Profiles: <PersonOutlineOutlinedIcon />,
  Calibrate: <TuneOutlinedIcon />,
  Session: <SportsEsportsOutlinedIcon />,
  Settings: <SettingsOutlinedIcon />,
};

const NavBar = ({ isOpen, onToggle }: NavBarProps) => (
  <aside
    className={`${styles.sidebar} ${!isOpen ? styles.sidebarCollapsed : ""}`}
  >
    <Box className={styles.sidebarHeader}>
      <IconButton
        edge="start"
        aria-label={isOpen ? "Collapse navigation" : "Expand navigation"}
        aria-expanded={isOpen}
        onClick={onToggle}
        className={styles.menuButton}
      >
        <MenuIcon className={styles.menuIcon} />
      </IconButton>
    </Box>
    <Box className={styles.navActions}>
      {NAV_ITEMS.map((item) => (
        <Button
          key={item.path}
          component={NavLink}
          to={item.path}
          className={`${styles.navButton} ${!isOpen ? styles.navButtonCollapsed : ""}`}
          startIcon={navIcons[item.label]}
          aria-label={item.label}
        >
          {isOpen ? (
            <span className={styles.navLabel}>{item.label}</span>
          ) : null}
        </Button>
      ))}
    </Box>
  </aside>
);

export default NavBar;
