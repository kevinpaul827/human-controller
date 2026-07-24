import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import { Box, Button, Paper, Typography } from "@mui/material";
import type { SessionGestureMapping } from "../types/session";
import { formatKey } from "../utils/keyboard";
import styles from "../styles/session.module.css";

// type GestureMappingItem = {
//   gesture: string;
//   keycap: string;
//   confidence: number;
// };

type GestureMappingProps = {
  gestures: SessionGestureMapping[];
  errorMessage?: string | null;
  onCalibrateNewGesture: () => void;
};

const GestureMapping = ({
  gestures,
  errorMessage,
  onCalibrateNewGesture,
}: GestureMappingProps) => {
  const visibleGestureCount = Math.min(gestures.length, 8);

  return (
    <Paper className={`${styles.dashboardPanel} ${styles.mappingPanel}`}>
      <Box className={styles.mappingHeader}>
        <Typography variant="h6" component="h2">
          Gesture Mappings ({gestures.length})
        </Typography>
        {gestures.length > 8 ? (
          <Box className={styles.scrollHint}>
            <Typography variant="body2">scroll</Typography>
            <KeyboardArrowDownIcon fontSize="small" />
          </Box>
        ) : null}
      </Box>

      <Box className={styles.mappingList}>
        {errorMessage ? (
          <Box className={styles.mappingRow}>
            <Typography>{errorMessage}</Typography>
          </Box>
        ) : null}
        {gestures.length > 0 ? (
          gestures.map((gesture) => (
            <Box key={gesture.gestureId} className={styles.mappingRow}>
              <Box className={styles.mappingInfo}>
                <Typography variant="body1">{gesture.name}</Typography>
              </Box>
              <Typography className={styles.keycap}>
                {formatKey(gesture.key)}
              </Typography>
            </Box>
          ))
        ) : errorMessage ? null : (
          <Box className={styles.mappingRow}>
            <Box className={styles.mappingInfo}>
              <Typography variant="body1">No gestures loaded</Typography>
            </Box>

            <Typography variant="body2">
              Assign calibrated movements in Profiles first
            </Typography>
          </Box>
        )}
      </Box>

      <Box className={styles.mappingFooter}>
        <Typography variant="body2" className={styles.footerCopy}>
          {gestures.length == 0
            ? "No gestures loaded for this session"
            : gestures.length > 8
              ? `Showing ${visibleGestureCount} of ${gestures.length} · scroll for more`
              : `${gestures.length} gestures${gestures.length == 1 ? "" : "s"} loaded`}
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
};

export default GestureMapping;
