import QuickAccessCard from "../components/QuickAccessCard";
import { ROUTES } from "../utils/constants";
import styles from "../styles/home.module.css";

const Home = () => (
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
        description="3 saved patient profiles"
        buttonLabel="View Profiles →"
        buttonTo={ROUTES.profiles}
      />
      <QuickAccessCard
        title="Start Session"
        description="Continue with Patient A"
        buttonLabel="Start Session →"
        buttonTo={ROUTES.session}
        variant="primary"
      />
    </div>

    <p className={styles.recent}>Recent: Patient A — last session 2 days ago</p>
  </div>
);

export default Home;
