import { PortalFrame } from "@/components/portal/PortalFrame";

export default function ClinicianLayout({ children }: { children: React.ReactNode }) {
  return <PortalFrame role="clinician">{children}</PortalFrame>;
}
