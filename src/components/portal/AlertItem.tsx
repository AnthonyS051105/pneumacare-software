"use client";

import Link from "next/link";
import { useFeedback } from "@/components/providers/Feedback";
import { Check, CircleAlert, Icon, TriangleAlert, Wifi } from "@/components/ui/Icon";
import { btn, cn, Pill } from "@/components/ui/primitives";
import { patients, type Alert } from "@/lib/demo-data";
import { updateDemo, useDemo } from "@/lib/demo-store";
import { detailHref } from "@/lib/routes";

const ICON_TONE = {
  urgent: "bg-[#fae9e6] text-red",
  warn: "bg-[#faf2e0] text-amber",
  info: "bg-[#eaf0e9] text-teal",
};

const metaPill = "max-md:text-[10px] max-md:leading-[1.5] max-md:px-[7px] max-md:py-1";
const mobileAction =
  "max-md:col-start-2 max-md:row-start-2 max-md:m-0 max-md:w-full max-md:min-h-11 max-md:px-3.5 max-md:py-2.5 max-md:border-line max-md:bg-white max-md:hover:bg-[#edf7f3] max-md:hover:border-line max-md:whitespace-normal max-md:text-center";

function patientMessage(id: string) {
  if (id === "a2") return "Nilai terbaru Anda telah kembali ke rentang pemantauan. Tetap ikuti arahan tenaga medis.";
  if (id === "a4") return "Koneksi rompi sudah pulih dan pemantauan kembali tersedia.";
  return "Pemberitahuan ini tercatat untuk membantu pemantauan Anda.";
}

/** Item notifikasi/alert (padanan alertItem() di referensi). */
export function AlertItem({ alert: a, clinical = false }: { alert: Alert; clinical?: boolean }) {
  const readList = useDemo((d) => d.read);
  const ackList = useDemo((d) => d.ack);
  const { toast } = useFeedback();
  const patient = patients.find((p) => p.id === a.patient);
  const ack = a.ack || ackList.includes(a.id);
  const read = readList.includes(a.id);
  const unread = !read && !clinical;

  return (
    <article className="flex items-start gap-3.5 py-5 border-b border-line last:border-0 last:pb-0 max-md:grid max-md:grid-cols-[32px_minmax(0,1fr)] max-md:gap-x-3 max-md:gap-y-3">
      <span
        className={cn(
          "grid place-items-center size-8 rounded-[5px] shrink-0 max-md:col-start-1 max-md:row-start-1",
          ICON_TONE[a.level],
        )}
      >
        <Icon icon={a.level === "urgent" ? CircleAlert : a.level === "info" ? Wifi : TriangleAlert} className="size-[18px]" />
      </span>
      <div className="flex-1 min-w-0 max-md:col-start-2 max-md:row-start-1">
        <div className="flex flex-wrap items-center justify-between gap-3 *:min-w-0 max-md:flex-col max-md:items-start max-md:justify-start max-md:gap-1.5">
          <h4
            className={cn(
              "text-[13px] max-md:text-[14px] max-md:leading-[1.5] max-md:break-words",
              unread &&
                "after:content-[''] after:inline-block after:size-[5px] after:rounded-full after:bg-primary after:ml-2",
            )}
          >
            {clinical ? a.title : a.plain}
          </h4>
          <small className="text-[11px] max-md:leading-[1.5]">{a.time}</small>
        </div>
        <p className="text-[12px] text-muted mt-[5px] max-w-[75ch] max-md:text-[13px] max-md:leading-[1.7] max-md:mt-[9px] max-md:max-w-none max-md:break-words">
          {clinical ? a.detail : patientMessage(a.id)}
        </p>
        <div className="flex flex-wrap items-center gap-2 mt-3 max-md:gap-1.5">
          <Pill tone={a.level === "urgent" ? "urgent" : a.level === "warn" ? "warn" : ""} className={metaPill}>
            {a.level === "urgent" ? "Urgent" : a.level === "warn" ? "Warning" : "Info"}
          </Pill>
          {clinical && patient && (
            <Link href={detailHref(a.patient, "alerts")} className="text-[12px]">
              {patient.name}
            </Link>
          )}
          <Pill tone={ack ? "" : "off"} className={metaPill}>
            {ack ? "Sudah ditinjau" : "Belum ditinjau"}
          </Pill>
          {a.resolved && (
            <Pill tone="off" className={metaPill}>
              Peristiwa sebelumnya
            </Pill>
          )}
        </div>
        {!clinical && (
          <details className="mt-6 text-[12px] max-md:mt-2.5">
            <summary className="cursor-pointer text-teal max-md:min-h-11 max-md:py-3 max-md:leading-[1.6]">
              Detail pemberitahuan
            </summary>
            <p className="text-[12px] text-muted mt-[5px] max-w-[75ch] max-md:text-[13px] max-md:leading-[1.7] max-md:mt-1 max-md:max-w-none">
              {a.id === "a2"
                ? "Kejadian pukul 09.05 WIB. Pembacaan terbaru pukul 09.30 WIB."
                : "Waktu dan status peninjauan tercatat pada pemberitahuan."}
            </p>
            <small className="text-[11px] max-md:block max-md:leading-[1.6] max-md:mt-2">
              Peninjauan tenaga medis tidak menentukan pemulihan kondisi.
            </small>
          </details>
        )}
      </div>
      {clinical
        ? !ack && (
            <button
              type="button"
              className={cn(btn({ small: true }), mobileAction)}
              onClick={() => {
                updateDemo((d) => (d.ack.includes(a.id) ? d : { ...d, ack: [...d.ack, a.id] }));
                toast("Alert ditandai sudah ditinjau. Status kondisi pasien tidak diubah.");
              }}
            >
              <Icon icon={Check} />
              Tandai ditinjau
            </button>
          )
        : !read && (
            <button
              type="button"
              className={cn(btn({ variant: "ghost", small: true }), mobileAction)}
              onClick={() => updateDemo((d) => ({ ...d, read: [...d.read, a.id] }))}
            >
              Tandai dibaca
            </button>
          )}
    </article>
  );
}
