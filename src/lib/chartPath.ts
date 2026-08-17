// Konversi array nilai numerik -> SVG path string, untuk dipakai VitalTrendCard
// (chartPath prop). Komponen tsb sebelumnya diisi string SVG path hardcoded
// (mis. "M0,35 Q10,32 20,38 T40,25..."); fungsi ini menghitung path yang setara
// dari data readings_vital sungguhan, TANPA mengubah struktur VitalTrendCard.
//
// viewBox default VitalTrendCard adalah "0 0 100 50" — path dinormalisasi ke
// rentang x:[0,100], y:[0,height] dengan y dibalik (SVG y=0 di atas, nilai
// tinggi harus berada di y kecil).

export function buildLinePath(
  values: (number | null)[],
  options?: { height?: number; padding?: number }
): string {
  const height = options?.height ?? 50;
  const padding = options?.padding ?? 4;

  const validPoints = values
    .map((value, index) => ({ value, index }))
    .filter((point): point is { value: number; index: number } => point.value !== null);

  if (validPoints.length === 0) {
    return `M0,${height / 2} L100,${height / 2}`; // garis datar di tengah bila tidak ada data
  }

  if (validPoints.length === 1) {
    const y = height / 2;
    return `M0,${y} L100,${y}`;
  }

  const min = Math.min(...validPoints.map((p) => p.value));
  const max = Math.max(...validPoints.map((p) => p.value));
  const range = max - min || 1; // hindari divide-by-zero saat semua nilai sama

  const lastIndex = values.length - 1;

  const coords = validPoints.map(({ value, index }) => {
    const x = lastIndex === 0 ? 0 : (index / lastIndex) * 100;
    const normalized = (value - min) / range; // 0..1
    const y = padding + (1 - normalized) * (height - padding * 2);
    return { x, y };
  });

  return coords
    .map((point, i) => `${i === 0 ? "M" : "L"}${point.x.toFixed(1)},${point.y.toFixed(1)}`)
    .join(" ");
}
