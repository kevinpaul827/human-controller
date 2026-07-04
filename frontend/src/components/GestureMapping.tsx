import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import { Box, Button, Paper, Typography } from "@mui/material";
import type { ReactElement } from "react";
import styles from "../styles/session.module.css";

type GestureMappingItem = {
  gesture: string;
  keycap: string;
  confidence: number;
};

type GestureMappingProps = {
  onCalibrateNewGesture: () => void;
};

const gestureMappings: GestureMappingItem[] = [
  { gesture: "Right Arm Raise", keycap: "up", confidence: 87 },
  { gesture: "Squat", keycap: "down", confidence: 82 },
  { gesture: "Lean Left", keycap: "left", confidence: 79 },
  { gesture: "Lean Right", keycap: "right", confidence: 81 },
  { gesture: "Hold Pose", keycap: "Space", confidence: 90 },
  { gesture: "Dash", keycap: "Shift", confidence: 76 },
  { gesture: "Interact", keycap: "E", confidence: 74 },
  { gesture: "Attack", keycap: "Z", confidence: 71 },
  { gesture: "Special", keycap: "X", confidence: 68 },
  { gesture: "Crouch", keycap: "Ctrl", confidence: 85 },
  { gesture: "Ability 1", keycap: "Q", confidence: 72 },
  { gesture: "Ability 2", keycap: "R", confidence: 70 },
];

const keycapIcons: Record<string, ReactElement> = {
  up: <ArrowUpwardIcon fontSize="inherit" />,
  down: <ArrowDownwardIcon fontSize="inherit" />,
  left: <ArrowBackIcon fontSize="inherit" />,
  right: <ArrowForwardIcon fontSize="inherit" />,
};

const GestureMapping = ({ onCalibrateNewGesture }: GestureMappingProps) => (
  <Paper className={`${styles.dashboardPanel} ${styles.mappingPanel}`}>
    <Box className={styles.mappingHeader}>
      <Typography variant="h6" component="h2">
        Gesture Mappings (12)
      </Typography>
      <Box className={styles.scrollHint}>
        <Typography variant="body2">scroll</Typography>
        <KeyboardArrowDownIcon fontSize="small" />
      </Box>
    </Box>

    <Box className={styles.mappingList}>
      {gestureMappings.map((mapping) => (
        <Box key={mapping.gesture} className={styles.mappingRow}>
          <Box className={styles.mappingInfo}>
            <Box className={styles.keycap} aria-hidden="true">
              {keycapIcons[mapping.keycap.toLowerCase()] ?? mapping.keycap}
            </Box>
            <Typography variant="body1">{mapping.gesture}</Typography>
          </Box>
          <Typography className={styles.confidenceText}>
            {mapping.confidence}%
          </Typography>
        </Box>
      ))}
    </Box>

    <Box className={styles.mappingFooter}>
      <Typography variant="body2" className={styles.footerCopy}>
        Showing 8 of 12 · scroll for more
      </Typography>
      <Button
        variant="outlined"
        className={styles.secondaryButton}
        onClick={onCalibrateNewGesture}
      >
        Calibrate New Gesture
      </Button>
    </Box>
  </Paper>
);

export default GestureMapping;
