import { Box, Container, Paper, Typography } from "@mui/material";
import GestureMapping from "../components/GestureMapping";
import SessionCamera from "../components/SessionCamera";
import styles from "../styles/session.module.css";

const Session = () => (
  <Container maxWidth="xl" className={styles.container}>
    <Paper className={styles.paper}>
      <Box className={styles.header}>
        <Typography variant="h4" component="h1" className={styles.title}>
          Session Dashboard - Patient A
        </Typography>
        <Typography className={styles.subtitle}>
          Step 4 of 4: Complete Calibration
        </Typography>
        <Box className={styles.progressTrack} aria-hidden="true">
          {[0, 1, 2, 3].map((segment) => (
            <span key={segment} className={styles.progressSegment} />
          ))}
        </Box>
      </Box>

      <Box className={styles.dashboardGrid}>
        <SessionCamera />
        <GestureMapping />
      </Box>
    </Paper>
  </Container>
);

export default Session;
