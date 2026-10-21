import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
