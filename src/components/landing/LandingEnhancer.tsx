"use client";

import { useEffect } from "react";
import { mountStory } from "@/lib/story-motion";

/**
 * Satu-satunya JavaScript di landing: pengontrol cerita scroll, menu mobile, dan
 * scroll halus ke section. Seluruh markup landing tetap Server Component.
 */
export function LandingEnhancer() {
  useEffect(() => {
    const root = document.querySelector<HTMLElement>(".pneuma-landing");
    if (!root) return;
    const dispose = mountStory(root);
    const nav = root.querySelector<HTMLElement>("#public-nav");
    const menu = root.querySelector<HTMLButtonElement>("[data-menu]");
    const setMenu = (open: boolean) => {
      nav?.classList.toggle("open", open);
      menu?.setAttribute("aria-expanded", String(open));
      menu?.setAttribute("aria-label", open ? "Tutup menu" : "Buka menu");
    };
    const onClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const scroll = target.closest<HTMLElement>("[data-scroll]");
      if (scroll) {
        event.preventDefault();
        const reduced = matchMedia("(prefers-reduced-motion:reduce)").matches;
        document.getElementById(scroll.dataset.scroll!)?.scrollIntoView({ behavior: reduced ? "auto" : "smooth" });
        setMenu(false);
        return;
      }
      if (target.closest("[data-menu]")) setMenu(!nav?.classList.contains("open"));
    };
    root.addEventListener("click", onClick);
    return () => {
      dispose();
      root.removeEventListener("click", onClick);
    };
  }, []);
  return null;
}
