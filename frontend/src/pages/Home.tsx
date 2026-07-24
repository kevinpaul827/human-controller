import QuickAccessCard from "../components/QuickAccessCard";
import useActiveProfile from "../hooks/useActiveProfile";
import { ROUTES } from "../utils/constants";
import styles from "../styles/home.module.css";

const Home = () => {
  const { activeProfile } = useActiveProfile();

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.heading}>Welcome back, Clinician</h1>
        <p className={styles.subheading}>
          Set up a rehabilitation session in under 2 minutes.
        </p>
      </header>

      <div className={styles.cardGrid}>
        <QuickAccessCard
          title="Profiles"
          description="Manage saved patient profiles"
          buttonLabel="View Profiles →"
          buttonTo={ROUTES.profiles}
        />
        <QuickAccessCard
          title="Start Session"
          description={
            activeProfile
              ? `Continue with ${activeProfile.patientName}`
              : "Start without a profile (Unassigned)"
          }
          buttonLabel="Start Session →"
          buttonTo={ROUTES.session}
          variant="primary"
        />
      </div>

      <p className={styles.recent}>
        {activeProfile
          ? `Active profile: ${activeProfile.patientName}`
          : "No patient profile selected."}
      </p>
    </div>
  );
};

export default Home;
