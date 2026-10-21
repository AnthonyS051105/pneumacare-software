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
import { VALID_PAIR_CODES } from "@/lib/demo-data";
import { updateDemo, useDemo } from "@/lib/demo-store";
import { focusFirstInvalid, isEmail, validateForm, type FieldErrors } from "@/lib/validation";

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
  const extra = useDemo((d) => d.extra);

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
                onLogout={() => {
                  closeModal();
                  router.push("/login");
                }}
                toast={toast}
                extraEmails={extra.map((p) => p.email ?? "")}
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
  extraEmails,
}: {
  kind: ModalKind;
  onClose: () => void;
  onLogout: () => void;
  toast: (text: string, error?: boolean) => void;
  extraEmails: string[];
}) {
  const [errors, setErrors] = useState<FieldErrors>({});

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const v = Object.fromEntries(new FormData(form)) as Record<string, string>;
    let next = validateForm(form);
    if (!Object.keys(next).length) {
      if (kind === "pair" && !VALID_PAIR_CODES.includes(v["modal-paircode"].toUpperCase()))
        next = { "modal-paircode": "Kode pairing tidak ditemukan. Periksa kembali kode." };
      if (kind === "add") {
        const code = v["modal-patient"];
        if (!isEmail(code) && !/^INV-\d{4}$/.test(code))
          next = { "modal-patient": "Gunakan email valid atau kode seperti INV-4821." };
        else if (extraEmails.includes(code)) next = { "modal-patient": "Pasien ini sudah ditambahkan." };
      }
    }
    setErrors(next);
    if (Object.keys(next).length) return focusFirstInvalid(form, next);

    if (kind === "pair") {
      onClose();
      toast("Perangkat PC-001 berhasil dihubungkan.");
    }
    if (kind === "add") {
      updateDemo((d) => ({
        ...d,
        extra: [
          ...d.extra,
          {
            id: "demo-" + Date.now(),
            name: v["modal-name"],
            email: v["modal-patient"],
            age: null,
            device: "Belum dipairing",
            hr: null,
            spo2: null,
            rr: null,
            status: "off",
            online: false,
          },
        ],
      }));
      onClose();
      toast("Pasien berhasil ditambahkan ke daftar pemantauan.");
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
          <button type="button" className={btn({ variant: "danger" })} onClick={onLogout}>
            Keluar
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
            ? "Gunakan email pasien atau kode undangan untuk menghubungkan akun."
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
              label="Email / kode pasien"
              hint="Contoh: pasien@example.com atau INV-4821"
              required
              error={errors["modal-patient"]}
              className={fieldCls}
            />
            <Field name="modal-name" label="Nama pasien" required error={errors["modal-name"]} className={fieldCls} />
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
          <button type="submit" className={btn({ variant: "primary" })}>
            {kind === "pair" ? "Hubungkan" : kind === "add" ? "Tambah Pasien" : "Lanjut"}
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
