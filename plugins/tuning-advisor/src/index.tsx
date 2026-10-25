import { definePlugin } from "@decky/api";
import { PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { FaSlidersH } from "react-icons/fa";

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
  name: "Tuning Advisor",
  titleView: <div className={staticClasses.Title}>Tuning Advisor</div>,
  content: <Content />,
  icon: <FaSlidersH />,
}));
