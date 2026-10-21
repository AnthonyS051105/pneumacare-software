import { PasswordToggle } from "@/components/ui/PasswordToggle";
import { cn } from "@/components/ui/primitives";

export const inputClass =
  "w-full border border-[#cdd8cf] rounded-[5px] px-3 py-[11px] bg-white text-ink min-h-[45px] leading-[1.5]";
export const inputInvalidClass = "border-red bg-[#fffafa]";

type FieldProps = {
  name: string;
  label: string;
  type?: "text" | "email" | "password" | "number" | "date";
  defaultValue?: string;
  hint?: string;
  required?: boolean;
  error?: string;
  autoComplete?: string;
  className?: string;
};

/** Padanan fungsi field() di referensi: label, input, hint, dan slot pesan error. */
export function Field({
  name,
  label,
  type = "text",
  defaultValue = "",
  hint,
  required = false,
  error,
  autoComplete,
  className,
}: FieldProps) {
  const password = type === "password";
  const auto =
    autoComplete ??
    (password
      ? name === "current"
        ? "current-password"
        : "new-password"
      : type === "email"
        ? "email"
        : type === "text" && name === "name"
          ? "name"
          : undefined);
  return (
    <div className={cn("block min-w-0", className)}>
      <label htmlFor={name} className="block font-medium text-[12px] mb-[7px]">
        {label}
        {required && (
          <>
            {" "}
            <span aria-label="wajib">*</span>
          </>
        )}
      </label>
      <div className={password ? "relative" : undefined}>
        <input
          id={name}
          name={name}
          type={type}
          defaultValue={defaultValue}
          required={required}
          autoComplete={auto}
          minLength={password ? 8 : undefined}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${name}-error` : hint ? `${name}-hint` : undefined}
          className={cn(inputClass, password && "pr-[46px]", error && inputInvalidClass)}
        />
        {password && <PasswordToggle target={name} />}
      </div>
      {hint && (
        <div className="text-[11px] text-muted mt-[5px]" id={`${name}-hint`}>
          {hint}
        </div>
      )}
      <div className="text-[11px] text-red mt-1" id={`${name}-error`}>
        {error}
      </div>
    </div>
  );
}
