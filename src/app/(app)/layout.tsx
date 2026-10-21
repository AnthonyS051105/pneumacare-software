import { FeedbackProvider } from "@/components/providers/Feedback";

// Semua halaman aplikasi (auth, portal, lembar pelengkap) berbagi modal & toast.
// Landing tidak memakainya sehingga JavaScript-nya tetap minimal.
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <FeedbackProvider>{children}</FeedbackProvider>;
}
