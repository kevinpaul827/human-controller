import { useEffect, useRef } from "react";
import { Outlet } from "react-router-dom";
import useActiveProfile from "@/hooks/useActiveProfile";
import sessionBridge from "@/services/sessionBridge";
import Header from "./Header";
import UndoBar from "./UndoBar";

const Layout = () => {
  const { activeProfile } = useActiveProfile();
  const profileId = activeProfile?.patientId ?? null;
  const previousProfileId = useRef(profileId);

  useEffect(() => {
    if (previousProfileId.current === profileId) return;
    previousProfileId.current = profileId;
    void sessionBridge.stopSession().catch(() => {});
  }, [profileId]);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <Header />
      <main className="min-h-0 flex-1 overflow-y-auto">
        <Outlet />
      </main>
      <UndoBar />
    </div>
  );
};

export default Layout;
