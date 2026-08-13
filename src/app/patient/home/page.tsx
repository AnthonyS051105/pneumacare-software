import { PatientSidebar } from "@/components/patient/PatientSidebar";
import { PatientTopBar } from "@/components/patient/PatientTopBar";
import { PatientBottomNav } from "@/components/patient/PatientBottomNav";
import { StatusHeroCard } from "@/components/patient/StatusHeroCard";
import { DeviceStatusStrip } from "@/components/patient/DeviceStatusStrip";
import { VitalSummaryCard } from "@/components/patient/VitalSummaryCard";
import { WearComplianceCard } from "@/components/patient/WearComplianceCard";
import { QuickLinks } from "@/components/patient/QuickLinks";

// TODO_NATHANAEL_CONFIRM: data dummy untuk demo — belum terhubung ke readings_vital/devices sungguhan.
const DUMMY_PATIENT = {
  name: "Samantha W.",
  patientId: "9821",
  statusLabel: "Stable",
};

const DUMMY_DEVICE = {
  connected: true,
  signalLabel: "Sinyal perangkat baik",
  batteryPercent: 85,
};

const DUMMY_VITALS = [
  {
    label: "Detak Jantung",
    icon: "favorite",
    iconBgClass: "bg-error-container/50",
    iconColorClass: "text-status-error",
    value: 78,
    unit: "bpm",
    rangeLabel: "hari ini 65–92 bpm",
  },
  {
    label: "Oksigen (SpO2)",
    icon: "air",
    iconBgClass: "bg-accent-blue/10",
    iconColorClass: "text-accent-blue",
    value: 98,
    unit: "%",
    rangeLabel: "hari ini 96–99%",
  },
  {
    label: "Laju Napas",
    icon: "waves",
    iconBgClass: "bg-tertiary-container/30",
    iconColorClass: "text-tertiary",
    value: 16,
    unit: "/mnt",
    rangeLabel: "hari ini 14–18 /mnt",
  },
];

export default function PatientHomePage() {
  return (
    <div className="min-h-screen bg-background pb-24 md:pb-0">
      <PatientSidebar
        patientName={DUMMY_PATIENT.name}
        patientId={DUMMY_PATIENT.patientId}
        statusLabel={DUMMY_PATIENT.statusLabel}
        activeHref="/patient/home"
      />
      <PatientTopBar patientName={DUMMY_PATIENT.name} />

      <main className="mx-auto flex max-w-5xl flex-col gap-6 p-4 md:ml-sidebar-width md:p-6 lg:p-8">
        <StatusHeroCard level="stable" lastUpdatedLabel="5 menit yang lalu" />

        <DeviceStatusStrip
          connected={DUMMY_DEVICE.connected}
          signalLabel={DUMMY_DEVICE.signalLabel}
          batteryPercent={DUMMY_DEVICE.batteryPercent}
        />

        <section>
          <h3 className="mb-4 text-xl font-bold">Ringkasan Hari Ini</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {DUMMY_VITALS.map((vital) => (
              <VitalSummaryCard key={vital.label} {...vital} />
            ))}
          </div>
        </section>

        <WearComplianceCard hoursWorn={6.2} targetHours={8} />

        <QuickLinks />

        <p className="text-center text-xs text-on-surface-variant">
          Data Simulasi &mdash; belum terhubung ke perangkat fisik.
        </p>
      </main>

      <PatientBottomNav activeHref="/patient/home" />
    </div>
  );
}
