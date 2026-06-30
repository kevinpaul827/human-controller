import { useEffect, useRef, useState } from "react";
import {
  Box,
  Button,
  Chip,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import { usePose } from "../demo/usePose";
import { useMatcher, type Angles, type Mode } from "../demo/useMatcher";
import {
  ALL_BODY_REGIONS,
  BODY_REGION_GROUPS,
  BODY_REGION_HINTS,
  BODY_REGION_LABELS,
  MEASURABLE_REGIONS,
  hasMeasurableSelection,
  isMeasurableRegion,
  type BodyRegionGroupId,
  type BodyRegionId,
} from "../demo/bodyRegions";

const REPS_TARGET = 3;

const summariseRep = (rep: Angles) =>
  Object.entries(rep)
    .filter(([, v]) => v != null)
    .map(([k, v]) => `${k} ${v}°`)
    .join(" · ") || "no visible joints";

const Calibrate = () => {
  const matcher = useMatcher();
  const { videoRef, canvasRef, ready, error: poseError } = usePose(
    matcher.sendFrame,
    matcher.focusRegions,
  );
  const [mode, setModeState] = useState<Mode>("idle");
  const [name, setName] = useState("");
  const [countdown, setCountdown] = useState<number | null>(null);
  const timer = useRef<number | null>(null);
  const angles = matcher.angles;

  useEffect(() => () => {
    if (timer.current) window.clearInterval(timer.current);
  }, []);

  const changeMode = (m: Mode) => {
    setModeState(m);
    if (m === "calibrate") matcher.startCalibration();
    else matcher.setMode(m);
  };

  const startCapture = () => {
    if (countdown !== null) return;
    let n = 3;
    setCountdown(n);
    timer.current = window.setInterval(() => {
      n -= 1;
      if (n <= 0) {
        if (timer.current) window.clearInterval(timer.current);
        timer.current = null;
        setCountdown(null);
        matcher.captureRep();
      } else {
        setCountdown(n);
      }
    }, 700);
  };

  const allRegionsSelected = matcher.focusRegions.length === ALL_BODY_REGIONS.length;
  const measurableSelected = hasMeasurableSelection(matcher.focusRegions);
  const canCapture = measurableSelected && countdown === null;
  const canSave = name.trim() !== "" && matcher.reps.length >= 1 && measurableSelected;
  const matched = mode === "match" && matcher.match?.matched;
  const trackedJointCount = matcher.focusRegions.filter(isMeasurableRegion).length;

  const save = () => {
    if (!canSave) return;
    matcher.saveGesture(name.trim());
    setName("");
    setModeState("idle");
  };

  const toggleRegion = (region: BodyRegionId) => {
    const current = matcher.focusRegions;
    const next = current.includes(region)
      ? current.filter((r) => r !== region)
      : [...current, region];
    matcher.setFocusRegions(next.length > 0 ? next : [region]);
  };

  const setGroupRegions = (groupId: BodyRegionGroupId, selected: boolean) => {
    const groupRegions = BODY_REGION_GROUPS.find((g) => g.id === groupId)?.regions ?? [];
    const current = new Set(matcher.focusRegions);
    for (const region of groupRegions) {
      if (selected) current.add(region);
      else current.delete(region);
    }
    const next = [...current];
    matcher.setFocusRegions(next.length > 0 ? next : [groupRegions[0]]);
  };

  const groupFullySelected = (groupId: BodyRegionGroupId) => {
    const groupRegions = BODY_REGION_GROUPS.find((g) => g.id === groupId)?.regions ?? [];
    return groupRegions.every((r) => matcher.focusRegions.includes(r));
  };

  return (
    <Box
      sx={{
        p: 1.5,
        maxWidth: 1280,
        mx: "auto",
        height: "calc(100vh - 89px)",
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
      }}
    >
      <Stack direction="row" spacing={0.75} alignItems="center" sx={{ mb: 1, flexShrink: 0 }}>
        <Typography variant="h5" sx={{ flexGrow: 1, lineHeight: 1.2 }}>
          Gesture Demo
        </Typography>
        <Chip
          label={matcher.connected ? "connected" : "offline"}
          color={matcher.connected ? "success" : "error"}
          size="small"
        />
        <Chip label={ready ? "live" : "camera…"} size="small" />
      </Stack>

      {(poseError || matcher.error) && (
        <Paper sx={{ px: 1.5, py: 1, mb: 1, bgcolor: "error.dark", color: "#fff", flexShrink: 0 }}>
          <Typography variant="body2">{poseError ?? matcher.error}</Typography>
        </Paper>
      )}

      <Box sx={{ display: "flex", gap: 1.5, flex: 1, minHeight: 0 }}>
        <Box
          sx={{
            flex: "1 1 58%",
            minWidth: 0,
            minHeight: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Box
            sx={{
              position: "relative",
              width: "100%",
              maxHeight: "100%",
              aspectRatio: "4 / 3",
              borderRadius: 1,
              overflow: "hidden",
              bgcolor: "#000",
            }}
          >
            <video
              ref={videoRef}
              playsInline
              muted
              style={{
                display: "block",
                width: "100%",
                height: "100%",
                transform: "scaleX(-1)",
              }}
            />
            <canvas
              ref={canvasRef}
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                transform: "scaleX(-1)",
                pointerEvents: "none",
              }}
            />
            {mode === "match" && (
              <Box
                sx={{
                  position: "absolute",
                  inset: 0,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  border: matched ? "4px solid #2e7d32" : "2px solid rgba(255,255,255,0.3)",
                  bgcolor: matched ? "rgba(46,125,50,0.25)" : "transparent",
                  transition: "all 120ms",
                  pointerEvents: "none",
                }}
              >
                {matched ? (
                  <Typography
                    variant="h3"
                    sx={{ color: "#fff", fontWeight: 800, textShadow: "0 2px 8px #000" }}
                  >
                    ✓ {matcher.match?.name}
                  </Typography>
                ) : (
                  <Typography
                    variant="h6"
                    sx={{ color: "rgba(255,255,255,0.85)", textShadow: "0 2px 8px #000" }}
                  >
                    strike a saved pose…
                  </Typography>
                )}
                {matcher.match && (
                  <Typography variant="body2" sx={{ color: "#fff", mt: 0.5, textShadow: "0 2px 8px #000" }}>
                    best: {matcher.match.name} ({matcher.match.score.toFixed(2)})
                  </Typography>
                )}
              </Box>
            )}
            {countdown !== null && (
              <Box
                sx={{
                  position: "absolute",
                  inset: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  pointerEvents: "none",
                }}
              >
                <Typography
                  sx={{ fontSize: 96, fontWeight: 800, color: "#fff", textShadow: "0 2px 16px #000" }}
                >
                  {countdown}
                </Typography>
              </Box>
            )}
          </Box>
        </Box>

        <Paper
          variant="outlined"
          sx={{
            flex: "1 1 42%",
            maxWidth: 400,
            display: "flex",
            flexDirection: "column",
            minHeight: 0,
            overflow: "hidden",
          }}
        >
          <Box sx={{ overflowY: "auto", flex: 1, px: 1.25, py: 1 }}>
            <Stack direction="row" spacing={0.5} sx={{ mb: 1 }}>
              <Button
                size="small"
                variant={mode === "idle" ? "contained" : "outlined"}
                onClick={() => changeMode("idle")}
                sx={{ flex: 1, minWidth: 0, py: 0.5 }}
              >
                Idle
              </Button>
              <Button
                size="small"
                variant={mode === "calibrate" ? "contained" : "outlined"}
                onClick={() => changeMode("calibrate")}
                sx={{ flex: 1, minWidth: 0, py: 0.5, fontSize: 11 }}
              >
                Calibrate
              </Button>
              <Button
                size="small"
                variant={mode === "match" ? "contained" : "outlined"}
                onClick={() => changeMode("match")}
                disabled={matcher.gestures.length === 0}
                sx={{ flex: 1, minWidth: 0, py: 0.5 }}
              >
                Match
              </Button>
            </Stack>

            <Typography variant="subtitle2" sx={{ mb: 0.5, fontSize: 12 }}>
              Body focus
            </Typography>
            <Chip
              label="Whole body"
              size="small"
              color={allRegionsSelected ? "primary" : "default"}
              variant={allRegionsSelected ? "filled" : "outlined"}
              onClick={() => matcher.setFocusRegions([...ALL_BODY_REGIONS])}
              sx={{ fontWeight: 600, mb: 0.75 }}
            />

            <Stack spacing={1} sx={{ mb: 1 }}>
              {BODY_REGION_GROUPS.map((group) => (
                <Box key={group.id}>
                  <Stack direction="row" spacing={0.5} alignItems="center" sx={{ mb: 0.25 }}>
                    <Typography variant="caption" fontWeight={600}>
                      {group.label}
                    </Typography>
                    <Button
                      size="small"
                      variant="text"
                      sx={{ minWidth: 0, px: 0.5, py: 0, fontSize: 11, lineHeight: 1.2 }}
                      onClick={() => setGroupRegions(group.id, true)}
                      disabled={groupFullySelected(group.id)}
                    >
                      All
                    </Button>
                    <Button
                      size="small"
                      variant="text"
                      sx={{ minWidth: 0, px: 0.5, py: 0, fontSize: 11, lineHeight: 1.2 }}
                      onClick={() => setGroupRegions(group.id, false)}
                    >
                      None
                    </Button>
                  </Stack>
                  <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                    {group.regions.map((region) => {
                      const selected = matcher.focusRegions.includes(region);
                      return (
                        <Chip
                          key={region}
                          label={BODY_REGION_LABELS[region]}
                          title={BODY_REGION_HINTS[region]}
                          size="small"
                          color={selected ? "primary" : "default"}
                          variant={selected ? "filled" : "outlined"}
                          onClick={() => toggleRegion(region)}
                          sx={{ height: 24, "& .MuiChip-label": { px: 0.75, fontSize: 11 } }}
                        />
                      );
                    })}
                  </Stack>
                </Box>
              ))}
            </Stack>

            {!measurableSelected && (
              <Typography sx={{ mb: 1, color: "warning.main", fontSize: 11 }}>
                Select at least one joint (shoulder, elbow, hip, knee, or ankle).
              </Typography>
            )}

            <Divider sx={{ my: 1 }} />

            <Typography variant="subtitle2" sx={{ mb: 0.5, fontSize: 12 }}>
              Live angles
              {trackedJointCount < MEASURABLE_REGIONS.length && (
                <Typography component="span" sx={{ ml: 0.5, fontSize: 11, color: "text.secondary" }}>
                  ({trackedJointCount} joint{trackedJointCount === 1 ? "" : "s"})
                </Typography>
              )}
            </Typography>
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: "1fr",
                rowGap: 0.25,
                fontFamily: "monospace",
                fontSize: 11,
                mb: 1,
              }}
            >
              {Object.entries(angles).map(([key, v]) => (
                <Box key={key} sx={{ display: "flex", justifyContent: "space-between", gap: 1 }}>
                  <span style={{ color: "#888" }}>{key}</span>
                  <span style={{ color: v == null ? "#bbb" : "inherit" }}>
                    {v == null ? "—" : `${v}°`}
                  </span>
                </Box>
              ))}
              {Object.keys(angles).length === 0 && (
                <span style={{ color: "#bbb" }}>waiting for pose…</span>
              )}
            </Box>

            {mode === "calibrate" && (
              <>
                <Divider sx={{ my: 1 }} />
                <Typography variant="subtitle2" sx={{ mb: 0.5, fontSize: 12 }}>
                  Calibrate: {matcher.reps.length}/{REPS_TARGET} reps
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.75 }}>
                  For each calibration rep:
                  <br />
                  1. Perform the gesture to completion
                  <br />
                  2. Hold the final pose and press the capture button
                  <br />
                  3. wait for the 3-2-1 countdown to capture the rep
                  <br />
                  4. repeat for the next rep
                  <br />
                </Typography>
                <Stack direction="row" spacing={0.5} sx={{ mb: 0.75 }}>
                  <Button
                    size="small"
                    variant="contained"
                    onClick={startCapture}
                    disabled={!canCapture}
                    sx={{ flex: 1 }}
                  >
                    {countdown !== null ? `Hold… ${countdown}` : `Capture ${matcher.reps.length + 1}`}
                  </Button>
                  <Button
                    size="small"
                    variant="text"
                    onClick={() => matcher.startCalibration()}
                    disabled={matcher.reps.length === 0}
                  >
                    Reset
                  </Button>
                </Stack>
                {matcher.reps.map((rep, i) => (
                  <Typography
                    key={i}
                    sx={{ fontFamily: "monospace", fontSize: 10, color: "text.secondary", mb: 0.25 }}
                  >
                    rep {i + 1}: {summariseRep(rep)}
                  </Typography>
                ))}
                <Stack direction="row" spacing={0.5} sx={{ mt: 0.75 }}>
                  <TextField
                    size="small"
                    label="Name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && save()}
                    sx={{ flex: 1, "& .MuiInputBase-root": { fontSize: 13 } }}
                  />
                  <Button size="small" variant="contained" onClick={save} disabled={!canSave}>
                    Save
                  </Button>
                </Stack>
              </>
            )}

            <Divider sx={{ my: 1 }} />

            <Typography variant="subtitle2" sx={{ mb: 0.5, fontSize: 12 }}>
              Saved ({matcher.gestures.length})
            </Typography>
            <List dense disablePadding>
              {matcher.gestures.map((g) => (
                <ListItem
                  key={g.gesture_id}
                  dense
                  disableGutters
                  secondaryAction={
                    <IconButton edge="end" size="small" onClick={() => matcher.deleteGesture(g.gesture_id)}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  }
                  sx={{ py: 0.25 }}
                >
                  <ListItemText
                    primary={g.name}
                    primaryTypographyProps={{ fontSize: 13 }}
                    secondary={
                      Object.keys(g.target_angles).length === 0
                        ? "⚠ no angles"
                        : Object.entries(g.target_angles)
                            .map(([k, v]) => `${k} ${v}°`)
                            .join(" · ")
                    }
                    secondaryTypographyProps={{ fontSize: 10, noWrap: true }}
                  />
                </ListItem>
              ))}
              {matcher.gestures.length === 0 && (
                <Typography variant="caption" color="text.secondary">
                  None yet
                </Typography>
              )}
            </List>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
};

export default Calibrate;
