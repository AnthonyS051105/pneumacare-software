"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { Field } from "@/components/ui/Field";
import { CircleAlert, CircleCheck, Icon, X } from "@/components/ui/Icon";
import { btn, cn, Notice } from "@/components/ui/primitives";
import { PATIENT_RELOAD_EVENT } from "@/components/providers/PatientData";
import { ApiError } from "@/lib/api";
import { logout } from "@/lib/authApi";
import { addPatient } from "@/lib/clinicianApi";
import { CLINICIAN_RELOAD_EVENT } from "@/lib/clinicianPatients";
import { repairDevice } from "@/lib/patientApi";
import { focusFirstInvalid, validateForm, type FieldErrors } from "@/lib/validation";

export type ModalKind = "pair" | "add" | "forgot" | "logout";

type FeedbackContext = {
  openModal: (kind: ModalKind) => void;
  closeModal: () => void;
  toast: (text: string, error?: boolean) => void;
};

const Context = createContext<FeedbackContext | null>(null);

export function useFeedback() {
  const ctx = useContext(Context);
  if (!ctx) throw new Error("useFeedback harus dipakai di dalam <FeedbackProvider>");
  return ctx;
}

const TITLES: Record<ModalKind, string> = {
  pair: "Hubungkan Perangkat",
  add: "Tambah Pasien",
  forgot: "Bantuan Password",
  logout: "Keluar dari Akun?",
};

/** Dialog modal global + toast, padanan openModal()/toast() di referensi. */
export function FeedbackProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const originRef = useRef<HTMLElement | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const [kind, setKind] = useState<ModalKind | null>(null);
  const [session, setSession] = useState(0);
  const [toastState, setToastState] = useState<{ text: string; error: boolean; id: number } | null>(null);

  const toast = useCallback((text: string, error = false) => {
    clearTimeout(toastTimer.current);
    setToastState({ text, error, id: Date.now() });
    toastTimer.current = setTimeout(() => setToastState(null), 6500);
  }, []);

  const openModal = useCallback((next: ModalKind) => {
    originRef.current = document.activeElement as HTMLElement | null;
    setKind(next);
    setSession((s) => s + 1);
  }, []);

  const closeModal = useCallback(() => {
    const dialog = dialogRef.current;
    if (dialog?.open) dialog.close();
  }, []);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog || !kind) return;
    if (!dialog.open) dialog.showModal();
    const target = dialog.querySelector<HTMLElement>("input") ?? dialog.querySelector<HTMLElement>("button");
    target?.focus();
  }, [kind, session]);

  useEffect(() => () => clearTimeout(toastTimer.current), []);

  return (
    <Context.Provider value={{ openModal, closeModal, toast }}>
      {children}
      <dialog
        ref={dialogRef}
        aria-labelledby="modal-title"
        onClose={() => {
          setKind(null);
          originRef.current?.focus();
        }}
        className="m-auto p-0 border border-line rounded-[9px] w-[470px] max-w-[calc(100%-32px)] max-h-[calc(100svh-36px)] shadow-[0_18px_80px_#183b3433] text-ink bg-white backdrop:bg-[#173b465c]"
      >
        {kind && (
          <>
            <div className="flex justify-between items-center px-6 pt-[22px] pb-[18px] border-b border-line">
              <h3 id="modal-title">{TITLES[kind]}</h3>
              <button
                type="button"
                onClick={closeModal}
                aria-label="Tutup dialog"
                className="relative grid place-items-center size-[42px] rounded-[6px] border border-line bg-white text-black"
              >
                <Icon icon={X} />
              </button>
            </div>
            <div className="p-6">
              <ModalBody
                key={session}
                kind={kind}
                onClose={closeModal}
                onLogout={async () => {
                  try {
                    await logout();
                  } catch (error) {
                    // 401 = sesi sudah berakhir, tetap lanjut keluar. Selain itu (mis. server mati)
                    // sesi masih aktif di server, jadi jangan berpura-pura sudah keluar.
                    if (!(error instanceof ApiError && error.status === 401)) {
                      toast("Gagal keluar dari akun. Periksa koneksi ke server lalu coba lagi.", true);
                      return;
                    }
                  }
                  closeModal();
                  router.push("/login");
                }}
                toast={toast}
              />
            </div>
          </>
        )}
      </dialog>
      <div aria-live="polite">
        {toastState && (
          <div
            key={toastState.id}
            role={toastState.error ? "alert" : "status"}
            className={cn(
              "fixed bottom-[26px] right-[26px] z-100 bg-white border border-line border-l-[3px] rounded-[6px] px-[18px] py-4 shadow-[0_6px_30px_#173b4612] max-w-[420px] flex gap-3 items-center text-[12px] max-md:left-4 max-md:right-4 max-md:bottom-[90px] max-md:max-w-none",
              toastState.error ? "border-l-red" : "border-l-primary",
            )}
          >
            <Icon icon={toastState.error ? CircleAlert : CircleCheck} />
            <span>{toastState.text}</span>
            <button
              type="button"
              onClick={() => setToastState(null)}
              aria-label="Tutup pemberitahuan"
              className="bg-transparent border-0 ml-2.5 text-muted min-w-8 min-h-8 px-1.5 py-px"
            >
              <Icon icon={X} />
            </button>
          </div>
        )}
      </div>
    </Context.Provider>
  );
}

const modalActions = "flex justify-end gap-2.5 mt-6";

function ModalBody({
  kind,
  onClose,
  onLogout,
  toast,
}: {
  kind: ModalKind;
  onClose: () => void;
  onLogout: () => void | Promise<void>;
  toast: (text: string, error?: boolean) => void;
}) {
  const [errors, setErrors] = useState<FieldErrors>({});
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = event.currentTarget;
    const v = Object.fromEntries(new FormData(form)) as Record<string, string>;
    const next = validateForm(form);
    setErrors(next);
    if (Object.keys(next).length) return focusFirstInvalid(form, next);

    if (kind === "pair") {
      setBusy(true);
      try {
        const { device_id } = await repairDevice(v["modal-paircode"].trim().toUpperCase());
        onClose();
        window.dispatchEvent(new Event(PATIENT_RELOAD_EVENT));
        toast(`Perangkat ${device_id} berhasil dihubungkan.`);
      } catch (error) {
        setBusy(false);
        if (error instanceof ApiError && error.status === 404) {
          setErrors({ "modal-paircode": "Kode pairing tidak ditemukan. Periksa kembali kode." });
        } else if (error instanceof ApiError && error.status === 409) {
          setErrors({ "modal-paircode": "Kode pairing ini sudah digunakan." });
        } else {
          toast(
            error instanceof ApiError ? error.message : "Tidak dapat terhubung ke server. Coba lagi sebentar lagi.",
            true,
          );
        }
      }
      return;
    }
    if (kind === "add") {
      setBusy(true);
      try {
        const patient = await addPatient(v["modal-patient"].trim().toLowerCase());
        onClose();
        window.dispatchEvent(new Event(CLINICIAN_RELOAD_EVENT));
        toast(`${patient.name} ditambahkan ke daftar pemantauan.`);
      } catch (error) {
        setBusy(false);
        if (error instanceof ApiError && error.status === 404) {
          setErrors({ "modal-patient": "Tidak ada akun pasien dengan email tersebut." });
        } else if (error instanceof ApiError && error.status === 409) {
          setErrors({ "modal-patient": error.message.charAt(0).toUpperCase() + error.message.slice(1) + "." });
        } else {
          toast(error instanceof ApiError ? error.message : "Tidak dapat terhubung ke server. Coba lagi sebentar lagi.", true);
        }
      }
      return;
    }
    if (kind === "forgot") {
      onClose();
      toast("Demo: hubungi pengelola layanan untuk bantuan akun. Tidak ada email yang dikirim.");
    }
  }

  const cancel = (
    <button type="button" className={btn()} onClick={onClose}>
      Batal
    </button>
  );
  const fieldCls = "mb-[17px]";

  if (kind === "logout")
    return (
      <>
        <p className="text-muted">Anda akan kembali ke halaman login.</p>
        <div className={modalActions}>
          {cancel}
          <button
            type="button"
            disabled={busy}
            className={btn({ variant: "danger" })}
            onClick={async () => {
              setBusy(true);
              await onLogout();
              setBusy(false);
            }}
          >
            {busy ? "Keluar…" : "Keluar"}
          </button>
        </div>
      </>
    );

  return (
    <>
      <p className="text-muted mb-5">
        {kind === "pair"
          ? "Masukkan kode pairing yang tertera pada perangkat Anda."
          : kind === "add"
            ? "Masukkan email akun pasien yang sudah terdaftar. Pasien akan muncul di daftar pemantauan Anda."
            : "Masukkan email Anda untuk melihat petunjuk bantuan akun demo."}
      </p>
      <form noValidate onSubmit={submit}>
        {kind === "pair" && (
          <Field
            name="modal-paircode"
            label="Kode pairing"
            hint="Masukkan kode pada perangkat"
            required
            error={errors["modal-paircode"]}
            className={fieldCls}
          />
        )}
        {kind === "add" && (
          <>
            <Field
              name="modal-patient"
              label="Email pasien"
              type="email"
              hint="Contoh: pasien@example.com"
              required
              error={errors["modal-patient"]}
              className={fieldCls}
            />
          </>
        )}
        {kind === "forgot" && (
          <>
            <Field
              name="modal-email"
              label="Email"
              type="email"
              required
              error={errors["modal-email"]}
              className={fieldCls}
            />
            <Notice>
              Pengiriman email reset belum terhubung. Pada implementasi produksi, tautan aman dikirim melalui layanan
              autentikasi.
            </Notice>
          </>
        )}
        {kind !== "forgot" && <div role="alert" />}
        <div className={modalActions}>
          {cancel}
          <button type="submit" disabled={busy} className={btn({ variant: "primary" })}>
            {kind === "pair"
              ? busy
                ? "Menghubungkan…"
                : "Hubungkan"
              : kind === "add"
                ? busy
                  ? "Menambahkan…"
                  : "Tambah Pasien"
                : "Lanjut"}
          </button>
        </div>
      </form>
    </>
  );
}

/** Tombol pemicu modal untuk dipakai dari Server Component. */
export function ModalButton({
  kind,
  className,
  children,
}: {
  kind: ModalKind;
  className?: string;
  children: ReactNode;
}) {
  const { openModal } = useFeedback();
  return (
    <button type="button" className={className} onClick={() => openModal(kind)}>
      {children}
    </button>
  );
}

/** Tombol pemicu toast (lembar Modal & Validasi). */
export function ToastButton({
  text,
  error = false,
  className,
  children,
}: {
  text: string;
  error?: boolean;
  className?: string;
  children: ReactNode;
}) {
  const { toast } = useFeedback();
  return (
    <button type="button" className={className} onClick={() => toast(text, error)}>
      {children}
    </button>
  );
}
