import { BatteryMedium, Icon, Signal, Wifi, WifiOff } from "@/components/ui/Icon";
import { Pill } from "@/components/ui/primitives";

export const connectionBar =
  "flex flex-wrap items-center gap-4 py-[13px] text-[12px] border-b border-line max-md:text-[11px] max-md:gap-2.5";

/** Strip status koneksi perangkat (padanan connection() di referensi). */
export function Connection({ offline = false }: { offline?: boolean }) {
  const rowIcon = "max-md:size-4";
  return (
    <div className={connectionBar}>
      <Icon icon={offline ? WifiOff : Wifi} className="size-[17px] max-md:size-4" />
      <Pill tone={offline ? "off" : ""}>{offline ? "Perangkat offline" : "Perangkat terhubung"}</Pill>
      <span>
        Rompi <b>PC-001</b>
      </span>
      <span>
        Terakhir diperbarui: <b>{offline ? "09.10" : "09.30"} WIB</b>
      </span>
      <span className="flex items-center gap-3">
        <Icon icon={BatteryMedium} className={rowIcon} />
        78%
      </span>
      <span className="flex items-center gap-3">
        <Icon icon={Signal} className={rowIcon} />
        Sinyal {offline ? "tidak tersedia" : "baik"}
      </span>
    </div>
  );
}
