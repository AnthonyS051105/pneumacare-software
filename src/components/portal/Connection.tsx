import { BatteryMedium, Icon, Signal, Wifi, WifiOff } from "@/components/ui/Icon";
import { Pill } from "@/components/ui/primitives";
import { formatClockWib, parseApiDate } from "@/lib/format";
import type { DeviceInfo } from "@/lib/patientApi";

export const connectionBar =
  "flex flex-wrap items-center gap-4 py-[13px] text-[12px] border-b border-line max-md:text-[11px] max-md:gap-2.5";

const SIGNAL_LABEL = { good: "baik", fair: "cukup", poor: "lemah" } as const;

/**
 * Strip status koneksi perangkat (padanan connection() di referensi).
 * `device`: data nyata dari API (null = belum ada rompi). Tanpa prop `device`
 * komponen memakai fixture demo (lembar pelengkap /demo).
 */
export function Connection({ offline = false, device }: { offline?: boolean; device?: DeviceInfo | null }) {
  const rowIcon = "max-md:size-4";

  if (device === null) {
    return (
      <div className={connectionBar}>
        <Icon icon={WifiOff} className="size-[17px] max-md:size-4" />
        <Pill tone="off">Belum ada rompi terhubung</Pill>
        <span>Hubungkan rompi Anda dari halaman Profil.</span>
      </div>
    );
  }

  if (device) {
    const online = device.status === "online";
    const signal = online
      ? device.signal_quality_ppg
        ? SIGNAL_LABEL[device.signal_quality_ppg]
        : "belum diketahui"
      : "tidak tersedia";
    return (
      <div className={connectionBar}>
        <Icon icon={online ? Wifi : WifiOff} className="size-[17px] max-md:size-4" />
        <Pill tone={online ? "" : "off"}>{online ? "Perangkat terhubung" : "Perangkat offline"}</Pill>
        <span>
          Rompi <b>{device.device_id}</b>
        </span>
        {device.last_seen_at && (
          <span>
            Terakhir terhubung: <b>{formatClockWib(parseApiDate(device.last_seen_at))}</b>
          </span>
        )}
        <span className="flex items-center gap-3">
          <Icon icon={BatteryMedium} className={rowIcon} />
          {device.battery_percent !== null ? `${Math.round(device.battery_percent)}%` : "—"}
        </span>
        <span className="flex items-center gap-3">
          <Icon icon={Signal} className={rowIcon} />
          Sinyal {signal}
        </span>
      </div>
    );
  }

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
