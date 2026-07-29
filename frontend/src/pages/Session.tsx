import { useNavigate } from "react-router-dom";
import { AlertTriangle } from "lucide-react";
import Page from "@/components/Page";
import GestureMapping from "@/components/GestureMapping";
import SessionCamera from "@/components/SessionCamera";
import { BrutalButton } from "@/components/ui/brutal-button";
import { useAppState } from "@/state/appStateContext";
import useActiveProfile from "@/hooks/useActiveProfile";
import { ROUTES } from "@/utils/constants";

const Session = () => {
  const navigate = useNavigate();
  const { activeProfile } = useActiveProfile();
  const { activePreset, readiness } = useAppState();

  return (
    <Page variant="fixed" width="wide">
      <header className="flex shrink-0 flex-wrap items-center justify-between gap-4">
        <h1 className="truncate text-2xl">
          {activePreset ? activePreset.name : "Session"}
        </h1>
        {activeProfile ? (
          <span className="text-sm font-semibold text-muted-foreground">
            {activeProfile.patientName}
          </span>
        ) : null}
      </header>

      {readiness.pending.length > 0 ? (
        <div className="flex shrink-0 flex-wrap items-center gap-3 rounded-base border-2 bg-accent px-4 py-3 text-accent-foreground shadow-brutal-sm">
          <AlertTriangle className="size-5 shrink-0" aria-hidden="true" />
          <p className="min-w-0 flex-1 text-sm font-bold">
            {readiness.pending.length} movement
            {readiness.pending.length === 1 ? "" : "s"} not recorded
          </p>
          <BrutalButton
            size="sm"
            variant="outline"
            onClick={() =>
              navigate(
                `${ROUTES.calibrate}?gesture=${readiness.pending[0].gestureId}`,
              )
            }
          >
            Record now
          </BrutalButton>
        </div>
      ) : null}

      <div className="grid gap-5 lg:min-h-0 lg:flex-1 lg:grid-cols-[minmax(20rem,0.8fr)_minmax(0,1.4fr)]">
        <SessionCamera />
        <GestureMapping />
      </div>
    </Page>
  );
};

export default Session;
