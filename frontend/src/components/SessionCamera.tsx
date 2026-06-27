import { Box, Button, Paper, Typography } from "@mui/material";
import styles from "../styles/session.module.css";

const SessionCamera = () => (
  <Paper className={`${styles.dashboardPanel} ${styles.cameraPanel}`}>
    <Box className={styles.cameraHeader}>
      <Typography variant="subtitle1" className={styles.cameraStatus}>
        Webcam Preview - Ready
      </Typography>
    </Box>

    <Box className={styles.cameraFeed}>
      <Box className={styles.cameraFeedContent}>
        <Typography className={styles.cameraPlaceholder}>
          Idle camera feed
        </Typography>
        <Button variant="contained" size="large" className={styles.startButton}>
          Start Session
        </Button>
      </Box>
    </Box>
  </Paper>
);

export default SessionCamera;
