import type { GameProfile, PatientProfile } from "../types/profile";
import styles from "../styles/patientCard.module.css";

const KEY_LABELS: Record<string, string> = {
  ArrowUp: "↑",
  ArrowDown: "↓",
  ArrowLeft: "←",
  ArrowRight: "→",
  Space: "Space",
};

const gestureKeyPreview = (gestures: GameProfile["gestures"], visible = 5) => {
  if (gestures.length === 0) {
    return "No bindings";
  }

  const shown = gestures.slice(0, visible).map((gesture) => KEY_LABELS[gesture.key] ?? gesture.key);
  const remaining = gestures.length - visible;
  return remaining > 0 ? `${shown.join(" ")}  + ${remaining} more` : shown.join(" ");
};

type PatientCardProps = {
  profile: PatientProfile;
  expanded: boolean;
  onExpandChange: (expanded: boolean) => void;
  onLoadLastSession: () => void;
  onGameLoad: (gameName: string) => void;
  onGameEdit: (gameName: string) => void;
  onAddGameProfile: () => void;
  onDelete: () => void;
};

const PatientCard = ({
  profile,
  expanded,
  onExpandChange,
  onLoadLastSession,
  onGameLoad,
  onGameEdit,
  onAddGameProfile,
  onDelete,
}: PatientCardProps) => {
  const gameCount = profile.gameProfiles.length;
  const gameLabel = `${gameCount} game profile${gameCount === 1 ? "" : "s"}`;

  return (
    <article className={`${styles.card} ${expanded ? styles.cardExpanded : ""}`}>
      <div className={styles.header}>
        <h2 className={styles.patientName}>👤 {profile.patientName}</h2>
        <span className={styles.gameCount}>{gameLabel}</span>
        {expanded ? (
          <button type="button" className={styles.buttonHeader} onClick={onAddGameProfile}>
            + Add Game Profile
          </button>
        ) : null}
      </div>

      {expanded ? (
        <div className={styles.body}>
          {profile.gameProfiles.map((game) => (
            <div key={game.gameName} className={styles.gameRow}>
              <div className={styles.gameInfo}>
                <h3 className={styles.gameTitle}>🎮 {game.gameName}</h3>
                <p className={styles.gesturePreview}>{gestureKeyPreview(game.gestures)}</p>
              </div>
              <span className={styles.badge}>{game.gestures.length} gestures</span>
              <div className={styles.rowActions}>
                <button
                  type="button"
                  className={styles.buttonPrimary}
                  onClick={() => onGameLoad(game.gameName)}
                >
                  Load
                </button>
                <button
                  type="button"
                  className={styles.buttonSecondary}
                  onClick={() => onGameEdit(game.gameName)}
                >
                  Edit
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : null}

      <div className={styles.actions}>
        {expanded ? (
          <>
            <button type="button" className={styles.buttonSecondary} onClick={() => onExpandChange(false)}>
              Close
            </button>
            <span className={styles.actionsSpacer} aria-hidden="true" />
            <button type="button" className={styles.buttonDanger} onClick={onDelete}>
              Delete
            </button>
          </>
        ) : (
          <>
            <button type="button" className={styles.buttonSecondary} onClick={() => onExpandChange(true)}>
              Expand
            </button>
            <button type="button" className={styles.buttonPrimary} onClick={onLoadLastSession}>
              Load Last Session
            </button>
            <button type="button" className={styles.buttonDanger} onClick={onDelete}>
              Delete
            </button>
          </>
        )}
      </div>
    </article>
  );
};

export default PatientCard;
