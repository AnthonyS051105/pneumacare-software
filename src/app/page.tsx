import type { Metadata } from "next";
import { Landing } from "@/components/landing/Landing";

export const metadata: Metadata = { title: "Landing Page" };

export default function HomePage() {
  return <Landing />;
}
