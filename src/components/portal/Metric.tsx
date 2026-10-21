import { Droplets, Heart, Icon, Wind } from "@/components/ui/Icon";
import { card, cn } from "@/components/ui/primitives";
import { VitalChart } from "@/components/ui/VitalChart";
import { values, type VitalKey } from "@/lib/demo-data";

const ICONS = { heart: Heart, droplets: Droplets, wind: Wind };
const ICON_COLOR: Record<VitalKey, string> = { hr: "text-rose", spo2: "text-blue", rr: "text-primary" };
/* Referensi: kelas global .blue/.teal pada kartu ikut mewarnai angka & grafik mini. */
const CARD_COLOR: Record<VitalKey, string> = { hr: "", spo2: "text-blue", rr: "text-teal" };

/** Grid tiga kartu vital (.grid.g3.metrics). */
export const metricsGrid =
  "grid min-w-0 grid-cols-3 gap-[22px] max-tb:gap-3.5 max-md:gap-[9px] max-xs:grid-cols-[1fr]";

/** Kartu tanda vital (padanan metric() di referensi). */
export function Metric({
  vital,
  clinical = false,
  unknown = false,
  val,
  lab = false,
}: {
  vital: VitalKey;
  clinical?: boolean;
  unknown?: boolean;
  val?: number | null;
  /** Di lembar pelengkap: <small> terakhir kartu bergaya monospace (.gallery .card>small:last-child). */
  lab?: boolean;
}) {
  const v = values[vital];
  const n = val ?? v.value;
  return (
    <article
      className={cn(
        card,
        CARD_COLOR[vital],
        "relative overflow-hidden p-[22px] max-2xl:p-5 max-tb:p-[17px] max-md:px-[11px] max-md:py-3.5",
        "max-xs:grid max-xs:grid-cols-[1.3fr_.8fr_1fr] max-xs:items-center max-xs:gap-x-3 max-xs:p-[17px]",
      )}
    >
      <div className="flex items-center justify-between gap-2.5 max-md:items-start max-md:min-h-[34px] max-md:gap-[5px] max-xs:min-h-0 max-xs:items-center max-xs:justify-start max-xs:gap-[9px]">
        <h4 className="text-[14px] text-[#556a5e] font-medium max-tb:text-[12px] max-md:text-[11px] max-md:max-w-[9ch] max-xs:max-w-[10ch]">
          {clinical ? v.technical : v.label}
        </h4>
        <span className={cn("inline-flex", ICON_COLOR[vital])}>
          <Icon icon={ICONS[v.icon]} className="size-[23px] max-md:size-[17px]" />
        </span>
      </div>
      <div className="mt-[17px] flex items-baseline gap-2 max-md:block max-md:mt-2.5 max-xs:m-0">
        <strong className="text-[45px] leading-[1.1] tracking-[-1.5px] font-medium tabular-nums 3xl:text-[49px] max-2xl:text-[39px] max-md:text-[33px]">
          {unknown ? "N/A" : n}
        </strong>
        <span className="text-[12px] text-muted max-2xl:text-[11px] max-tb:text-[10px] max-md:block max-md:mt-[3px] max-md:min-h-4">
          {v.unit}
        </span>
      </div>
      {unknown ? (
        <p className="text-muted mt-6">Belum ada data terkini</p>
      ) : (
        <VitalChart vital={vital} mini center={n} />
      )}
      <small className={cn(lab ? "font-mono text-[10px] pt-3.5 max-xs:mt-auto" : "text-[11px] max-md:text-[9px] max-xs:mt-2.5", "max-md:leading-[1.4] max-md:block max-xs:col-span-full")}>
        {unknown ? "Kondisi belum diketahui" : "Pembaruan 09.30 WIB"}
      </small>
    </article>
  );
}
