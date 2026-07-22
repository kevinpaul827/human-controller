import { Typography } from "@mui/material";
import useActiveProfile from "../hooks/useActiveProfile";
import styles from "../styles/header.module.css";

const Header = () => {
  const { activeProfile } = useActiveProfile();

  return (
    <header className={styles.header}>
      <Typography variant="h5" component="div" className={styles.title}>
        Human Game Controller — Make Rehabilitation Fun!
      </Typography>
      <Typography variant="body1" component="div" className={styles.profile}>
        Profile: {activeProfile?.patientName ?? "No profile selected"}
      </Typography>
    </header>
  );
};

export default Header;
