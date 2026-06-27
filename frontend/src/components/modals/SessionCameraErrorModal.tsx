import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";

type SessionCameraErrorModalProps = {
  message?: string;
  open: boolean;
  onCancel: () => void;
  onConfigure: () => void;
};

const SessionCameraErrorModal = ({
  message,
  open,
  onCancel,
  onConfigure,
}: SessionCameraErrorModalProps) => (
  <Dialog
    open={open}
    onClose={onCancel}
    aria-labelledby="session-camera-error-title"
    PaperProps={{
      sx: {
        borderRadius: 3,
        color: "#1f2937",
        px: 1,
        py: 0.5,
      },
    }}
  >
    <DialogTitle
      id="session-camera-error-title"
      sx={{ color: "#1f2937", fontWeight: 700 }}
    >
      Session camera error
    </DialogTitle>
    <DialogContent>
      <Typography sx={{ color: "#334155" }}>
        {message ??
          "The desktop app reported a camera error while starting the session."}
      </Typography>
    </DialogContent>
    <DialogActions sx={{ px: 3, pb: 2.5 }}>
      <Button onClick={onCancel} sx={{ color: "#334155", fontWeight: 700 }}>
        Cancel
      </Button>
      <Button
        variant="contained"
        onClick={onConfigure}
        sx={{
          background: "linear-gradient(135deg, #4073ff, #2d5ddd)",
          color: "#f8fafc",
          fontWeight: 700,
          textTransform: "none",
          boxShadow: "none",
          "&:hover": {
            background: "linear-gradient(135deg, #3669f5, #234fc5)",
            boxShadow: "none",
          },
        }}
      >
        Configure
      </Button>
    </DialogActions>
  </Dialog>
);

export default SessionCameraErrorModal;
