"use client";

import { useFeedback } from "@/components/providers/Feedback";
import { AlertItem } from "@/components/portal/AlertItem";
import { notificationsCard } from "@/components/portal/layout";
import { usePatientData } from "@/components/providers/PatientData";
import { Bell } from "@/components/ui/Icon";
import { btn, cn, Empty, Notice, segmentButton, segments } from "@/components/ui/primitives";
import { updateDemo, useDemo, useUi } from "@/lib/demo-store";
import { toAlertView } from "@/lib/patientAlerts";

// Status "sudah dibaca" hanya urusan tampilan di perangkat ini (backend tidak menyimpannya),
// jadi tetap di localStorage lewat state demo.
export function PatientAlertsView() {
  const [filter, setFilter] = useUi("alertFilter");
  const read = useDemo((d) => d.read);
  const { toast } = useFeedback();
  const { alerts } = usePatientData();
  const own = alerts.map((a) => toAlertView(a));
  const list = own.filter((a) => filter !== "unread" || !read.includes(a.id));
  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5 *:min-w-0">
        <div className={segments}>
          <button type="button" className={segmentButton(filter === "all")} onClick={() => setFilter("all")}>
            Semua
          </button>
          <button type="button" className={segmentButton(filter === "unread")} onClick={() => setFilter("unread")}>
            Belum dibaca
          </button>
        </div>
        <button
          type="button"
          className={btn({ small: true })}
          onClick={() => {
            updateDemo((d) => ({ ...d, read: [...new Set([...d.read, ...own.map((a) => a.id)])] }));
            toast("Semua notifikasi ditandai dibaca.");
          }}
        >
          Tandai semua dibaca
        </button>
      </div>
      <Notice>
        Pemberitahuan membantu Anda mengenali perubahan. Ikuti arahan tenaga medis jika kondisi Anda memburuk.
      </Notice>
      <section className={cn(notificationsCard, "mt-6")}>
        {list.length ? (
          list.map((a) => <AlertItem key={a.id} alert={a} />)
        ) : own.length ? (
          <Empty icon={Bell} title="Tidak ada notifikasi belum dibaca" text="Semua pemberitahuan telah Anda baca." />
        ) : (
          <Empty icon={Bell} title="Belum ada notifikasi" text="Pemberitahuan pemantauan Anda akan muncul di sini." />
        )}
      </section>
    </>
  );
}
