import { useContext } from "react";
import ActiveProfileContext from "../context/ActiveProfileContext";

const useActiveProfile = () => {
  const context = useContext(ActiveProfileContext);
  if (!context) {
    throw new Error(
      "useActiveProfile must be used within an ActiveProfileProvider.",
    );
  }
  return context;
};

export default useActiveProfile;
