import { Link } from "react-router-dom";
import styles from "../styles/quickAccessCard.module.css";

type QuickAccessCardProps = {
  title: string;
  description: string;
  buttonLabel: string;
  buttonTo: string;
  variant?: "primary" | "secondary";
};

const QuickAccessCard = ({
  title,
  description,
  buttonLabel,
  buttonTo,
  variant = "secondary",
}: QuickAccessCardProps) => (
  <article className={styles.card}>
    <h2 className={styles.title}>{title}</h2>
    <p className={styles.description}>{description}</p>
    <Link
      to={buttonTo}
      className={`${styles.button} ${variant === "primary" ? styles.buttonPrimary : styles.buttonSecondary}`}
    >
      {buttonLabel}
    </Link>
  </article>
);

export default QuickAccessCard;
