import { BrutalButton } from "@/components/ui/brutal-button";
import { BrutalDialog } from "@/components/ui/brutal-dialog";

type SessionCameraErrorModalProps = {
  kind?: "camera" | "accessibility";
  message?: string;
  open: boolean;
  onCancel: () => void;
  onConfigure: () => void;
};

const SessionCameraErrorModal = ({
  message,
  kind = "camera",
  open,
  onCancel,
  onConfigure,
}: SessionCameraErrorModalProps) => (
  <BrutalDialog
    open={open}
    onOpenChange={(next) => {
      if (!next) {
        onCancel();
      }
    }}
    title={
      kind === "accessibility" ? "Keyboard access required" : "Camera error"
    }
    footer={
      <>
        <BrutalButton variant="outline" onClick={onCancel}>
          Dismiss
        </BrutalButton>
        <BrutalButton onClick={onConfigure}>
          {kind === "accessibility"
            ? "Open accessibility settings"
            : "Open camera settings"}
        </BrutalButton>
      </>
    }
  >
    <p className="text-sm font-semibold">
      {message ??
        (kind === "accessibility"
          ? "Allow the desktop app to send keyboard controls."
          : "The desktop app reported a camera error while opening the session camera.")}
    </p>
  </BrutalDialog>
);

export default SessionCameraErrorModal;
