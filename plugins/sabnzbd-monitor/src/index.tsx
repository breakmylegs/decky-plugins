import { definePlugin } from "@decky/api";
import { PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { FaDownload } from "react-icons/fa";

function Content() {
  return (
    <PanelSection>
      <PanelSectionRow>
        <div style={{ fontSize: 12 }}>Not built yet. This is a scaffold.</div>
      </PanelSectionRow>
    </PanelSection>
  );
}

export default definePlugin(() => ({
  name: "SABnzbd Monitor",
  titleView: <div className={staticClasses.Title}>SABnzbd Monitor</div>,
  content: <Content />,
  icon: <FaDownload />,
}));
