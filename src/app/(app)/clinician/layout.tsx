import { PortalFrame } from "@/components/portal/PortalFrame";
import { ClinicianGuard } from "@/components/providers/ClinicianGuard";

export default function ClinicianLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClinicianGuard>
      <PortalFrame role="clinician">{children}</PortalFrame>
    </ClinicianGuard>
  );
}
