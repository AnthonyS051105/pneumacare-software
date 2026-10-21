"use client";

import { useState } from "react";
import { Eye, EyeOff, Icon } from "@/components/ui/Icon";

/** Tombol tampilkan/sembunyikan password; mengubah tipe input target secara langsung. */
export function PasswordToggle({ target }: { target: string }) {
  const [visible, setVisible] = useState(false);
  return (
    <button
      type="button"
      data-password-toggle={target}
      aria-label={visible ? "Sembunyikan password" : "Tampilkan password"}
      onClick={() => {
        const input = document.getElementById(target) as HTMLInputElement | null;
        if (!input) return;
        input.type = input.type === "password" ? "text" : "password";
        setVisible(input.type === "text");
      }}
      className="absolute right-1 top-[3px] bg-transparent border-0 text-muted p-[9px] min-w-10 min-h-10"
    >
      <Icon icon={visible ? EyeOff : Eye} />
    </button>
  );
}
