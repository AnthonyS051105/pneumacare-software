import { DetailHeader } from "@/components/portal/PatientDetail";
import { Topbar } from "@/components/portal/Shell";
import { patients } from "@/lib/demo-data";

// Enam pasien fixture di-prerender statis; pasien tambahan (localStorage) dirender saat diminta.
export function generateStaticParams() {
  return patients.map((p) => ({ id: p.id }));
}

export default async function PatientDetailLayout({ children, params }: LayoutProps<"/clinician/patients/[id]">) {
  const { id } = await params;
  return (
    <>
      <Topbar role="clinician" title="Detail Pasien" subtitle="Pemantauan kardio-respirasi dan peninjauan klinis." />
      <DetailHeader id={id} />
      {children}
    </>
  );
}
