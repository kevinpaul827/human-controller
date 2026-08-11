import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { RotateCcw, Trash2, Video } from "lucide-react";
import Page from "@/components/Page";
import { BrutalButton } from "@/components/ui/brutal-button";
import {
  BrutalCard,
  BrutalCardHeader,
  BrutalCardTitle,
} from "@/components/ui/brutal-card";
import { BrutalDialog } from "@/components/ui/brutal-dialog";
import { BrutalField, BrutalInput } from "@/components/ui/brutal-input";
import { useAppState } from "@/state/appStateContext";
import { ROUTES } from "@/utils/constants";

const EMPTY_NAME = "";
const NO_MOVEMENTS_MESSAGE = "No movements yet";
const MOVEMENT_NAME_PLACEHOLDER = "e.g. Right Arm Raise";
const ADD_MOVEMENT_TITLE = "Add movement";
const MOVEMENTS_TITLE = "Movements";

const Library = () => {
  const navigate = useNavigate();
  const { gestures, addGesture, deleteGesture } = useAppState();

  const [showAddDialog, setShowAddDialog] = useState(false);
  const [name, setName] = useState(EMPTY_NAME);

  const openAddDialog = () => setShowAddDialog(true);
  const closeAddDialog = () => setShowAddDialog(false);
  const getCalibrateRoute = (gestureId: string) =>
    `${ROUTES.calibrate}?gesture=${gestureId}`;

  const handleAdd = () => {
    const trimmed = name.trim();
    if (!trimmed) {
      return;
    }
    const gestureId = addGesture(trimmed);
    closeAddDialog();
    setName(EMPTY_NAME);

    navigate(getCalibrateRoute(gestureId));
  };

  return (
    <Page>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl sm:text-3xl">Movement library</h1>
        <BrutalButton size="lg" onClick={openAddDialog}>
          <Video aria-hidden="true" />
          Record new movement
        </BrutalButton>
      </header>

      <BrutalCard>
        <BrutalCardHeader>
          <BrutalCardTitle>{MOVEMENTS_TITLE}</BrutalCardTitle>
          <span className="text-sm font-semibold text-muted-foreground">
            {gestures.length} {gestures.length === 1 ? "movement" : "movements"}
          </span>
        </BrutalCardHeader>

        {gestures.length === 0 ? (
          <div className="p-10 text-center">
            <p className="text-sm font-semibold text-muted-foreground">
              {NO_MOVEMENTS_MESSAGE}
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-hairline">
            {gestures.map((gesture) => {
              const recorded = Boolean(gesture.calibratedAt);

              return (
                <li
                  key={gesture.gestureId}
                  className="flex flex-wrap items-center gap-x-4 gap-y-2 px-5 py-3"
                >
                  <span className="min-w-0 flex-1 truncate font-bold">
                    {gesture.name}
                  </span>

                  <BrutalButton
                    size="sm"
                    variant="outline"
                    onClick={() => navigate(getCalibrateRoute(gesture.gestureId))}
                  >
                    {recorded ? (
                      <RotateCcw aria-hidden="true" />
                    ) : (
                      <Video aria-hidden="true" />
                    )}
                    {recorded ? "Re-record" : "Record"}
                  </BrutalButton>

                  <BrutalButton
                    size="sm"
                    variant="outline"
                    aria-label={`Delete ${gesture.name}`}
                    onClick={() => deleteGesture(gesture.gestureId)}
                  >
                    <Trash2 aria-hidden="true" />
                  </BrutalButton>
                </li>
              );
            })}
          </ul>
        )}
      </BrutalCard>

      <BrutalDialog
        open={showAddDialog}
        onOpenChange={setShowAddDialog}
        title={ADD_MOVEMENT_TITLE}
        footer={
          <>
            <BrutalButton variant="outline" onClick={closeAddDialog}>
              Cancel
            </BrutalButton>
            <BrutalButton
              onClick={handleAdd}
              disabled={name.trim().length === 0}
            >
              Add and record
            </BrutalButton>
          </>
        }
      >
        <BrutalField label="Movement name" htmlFor="new-gesture-name">
          <BrutalInput
            id="new-gesture-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder={MOVEMENT_NAME_PLACEHOLDER}
            autoFocus
          />
        </BrutalField>
      </BrutalDialog>
    </Page>
  );
};

export default Library;
