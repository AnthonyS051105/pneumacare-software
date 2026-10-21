import { PortalFrame } from "@/components/portal/PortalFrame";

export default function PatientLayout({ children }: { children: React.ReactNode }) {
  return <PortalFrame role="patient">{children}</PortalFrame>;
}
