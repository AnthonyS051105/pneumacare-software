export type DetailTab = "vitals" | "trends" | "alerts" | "thresholds";

/** URL tab detail pasien. Referensi memakai ?tab=, di sini memakai segmen agar halaman statis. */
export function detailHref(id: string, tab: DetailTab = "vitals") {
  return tab === "vitals" ? `/clinician/patients/${id}` : `/clinician/patients/${id}/${tab}`;
}
