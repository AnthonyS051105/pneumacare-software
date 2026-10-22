import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Jangan biarkan `next dev`/`next build` membuat AGENTS.md & CLAUDE.md di root repo —
  // instruksi agen proyek ini sudah ada di CLAUDE.local.md.
  agentRules: false,
  images: {
    // AVIF diutamakan (paling kecil), WebP sebagai fallback. Ilustrasi PNG 1,3–1,6 MB
    // dikonversi & di-resize otomatis sesuai lebar tampilan oleh optimizer Next.js.
    formats: ["image/avif", "image/webp"],
    qualities: [75],
  },
  experimental: {
    optimizePackageImports: ["lucide"],
  },
};

export default nextConfig;
