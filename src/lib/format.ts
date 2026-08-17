// Backend mengirim patient_id sebagai UUID penuh (36 karakter) — terlalu panjang
// untuk kolom sempit di PatientSidebar. Dipendekkan jadi 8 karakter pertama,
// huruf besar, murni untuk tampilan (bukan untuk lookup/pencarian sungguhan).
export function formatShortId(uuid: string): string {
  return uuid.slice(0, 8).toUpperCase();
}
