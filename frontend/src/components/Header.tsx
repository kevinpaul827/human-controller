import { Typography } from "@mui/material";
import styles from "../styles/header.module.css";

const Header = () => (
  <header className={styles.header}>
    <Typography variant="h5" component="div" className={styles.title}>
      Human Game Controller — Make Rehabilitation Fun!
    </Typography>
    <Typography variant="body1" component="div" className={styles.profile}>
      Profile: Patient A
    </Typography>
  </header>
);

export default Header;
