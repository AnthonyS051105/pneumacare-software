import { Droplets, Heart, Icon, Wind } from "@/components/ui/Icon";
import { values, type VitalKey } from "@/lib/demo-data";

const ICONS = { heart: Heart, droplets: Droplets, wind: Wind };

/** Ikon tanda vital polos (warna mengikuti teks) untuk judul kartu grafik. */
export function ChartIcon({ vital }: { vital: VitalKey }) {
  return <Icon icon={ICONS[values[vital].icon]} />;
}
