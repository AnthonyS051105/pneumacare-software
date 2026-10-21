import { createElement, type SVGProps } from "react";
import type { IconNode } from "lucide";

export {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  AudioLines,
  BatteryMedium,
  Bell,
  ChartNoAxesCombined,
  Check,
  ChevronRight,
  CircleAlert,
  CircleCheck,
  CircleHelp,
  Clock3,
  Download,
  Droplets,
  Eye,
  EyeOff,
  Heart,
  House,
  Info,
  KeyRound,
  Link as LinkIcon,
  LogOut,
  Menu,
  Plus,
  RotateCw,
  Save,
  Search,
  Signal,
  Stethoscope,
  TriangleAlert,
  UserPlus,
  UserRound,
  Users,
  Wifi,
  WifiOff,
  Wind,
  X,
} from "lucide";

type IconProps = Omit<SVGProps<SVGSVGElement>, "children"> & { icon: IconNode };

/**
 * Render ikon Lucide sebagai SVG statis. Tidak memakai hooks/context, jadi di Server
 * Component ikon tidak menambah JavaScript sama sekali (beda dengan lucide-react v1
 * yang merupakan Client Component). Kelas `.icon` (globals.css) memberi ukuran dasar 20px.
 */
export function Icon({ icon, className, ...rest }: IconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className ? `icon ${className}` : "icon"}
      {...rest}
    >
      {icon.map(([tag, attrs], index) => createElement(tag, { key: index, ...attrs }))}
    </svg>
  );
}

/** Ikon paru khusus landing (pengganti droplets untuk SpO₂). */
export function LungIcon({ className }: { className?: string }) {
  return (
    <svg className={className ? `icon ${className}` : "icon"} viewBox="0 0 44 44" fill="none" aria-hidden="true">
      <path
        d="M20 5v15l-7-8C8 14 4 22 4 30c0 5 3 8 7 8 5 0 8-4 8-9v-9M24 5v15l7-8c5 2 9 10 9 18 0 5-3 8-7 8-5 0-8-4-8-9v-9M15 23l7-5 7 5"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
