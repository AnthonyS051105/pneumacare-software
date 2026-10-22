import { PortalFrame } from "@/components/portal/PortalFrame";
import { PatientDataProvider } from "@/components/providers/PatientData";

export default function PatientLayout({ children }: { children: React.ReactNode }) {
  return (
    <PatientDataProvider>
      <PortalFrame role="patient">{children}</PortalFrame>
    </PatientDataProvider>
  );
}
