import type { Metadata, Viewport } from "next";
import "./globals.css";

// Tanpa web font: Arial/Helvetica bawaan perangkat (sesuai design-tokens referensi),
// jadi tidak ada request font eksternal yang memblokir render.
export const metadata: Metadata = {
  title: { default: "PNEUMACARE", template: "%s | PNEUMACARE" },
  description: "PNEUMACARE: pemantauan kardio-respirasi dari rumah, responsif untuk pasien dan tenaga medis.",
};

export const viewport: Viewport = {
  themeColor: "#167d76",
  viewportFit: "cover",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
