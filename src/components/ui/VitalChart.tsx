import { values, type VitalKey } from "@/lib/demo-data";

type ChartOptions = {
  mini?: boolean;
  gap?: boolean;
  offline?: boolean;
  wave?: boolean;
  trend?: boolean;
  range?: string;
  center?: number;
  /** "grid" = grafik di halaman riwayat (.chart-grid .chart), tinggi minimum lebih besar. */
  variant?: "default" | "grid";
};

const chartClass = {
  default:
    "block w-full h-auto overflow-visible aspect-[620/210] min-h-[130px] max-tb:aspect-[620/220] max-md:aspect-[620/250] max-md:min-h-[145px]",
  grid: "block w-full h-auto overflow-visible aspect-[620/210] min-h-[160px] max-tb:aspect-[620/220] max-md:aspect-[620/250] max-md:min-h-[145px]",
  mini: "block w-full overflow-visible h-12 min-h-0 mt-[18px] mb-3.5 max-md:h-[30px] max-md:mt-[15px] max-md:mb-2 max-xs:m-0 max-xs:h-[35px]",
};

const RANGE_LABELS: Record<string, string[]> = {
  "7 hari": ["4 Okt", "5 Okt", "6 Okt", "7 Okt", "8 Okt", "9 Okt", "10 Okt"],
  "30 hari": ["11 Sep", "16 Sep", "21 Sep", "26 Sep", "1 Okt", "6 Okt", "10 Okt"],
  "24h": ["00.00", "04.00", "08.00", "12.00", "16.00", "20.00", "24.00"],
};

const TEXT_PROPS = { fill: "#68766b", fontSize: 11, fontFamily: "Arial, sans-serif" } as const;

/** Grafik SVG statis (port dari chart() di referensi). Murni — aman di Server Component. */
export function VitalChart({
  vital = "hr",
  mini = false,
  gap = false,
  offline = false,
  wave = false,
  trend = false,
  range = "24h",
  center,
  variant = "default",
}: ChartOptions & { vital?: VitalKey }) {
  const v = values[vital];
  let series = wave
    ? Array.from({ length: 60 }, (_, j) => Math.sin(j * 0.72) * 0.18 + (j % 10 === 6 ? 0.7 : 0))
    : v.series;
  const w = 620;
  const h = mini ? 70 : 210;
  const left = mini ? 2 : 36;
  const top = mini ? 6 : 16;
  const bottom = mini ? 64 : 177;
  const right = w - 10;
  let min = wave ? -0.5 : v.min;
  let max = wave ? 1 : v.max;
  if (center !== undefined && !wave) {
    series = series.map((a) => a + center - v.value);
    min = Math.min(v.min, ...series) - 1;
    max = Math.max(v.max, ...series) + 1;
  }
  const x = (j: number) => left + (j * (right - left)) / (series.length - 1);
  const y = (a: number) => bottom - ((a - min) / (max - min)) * (bottom - top);

  const pieces: [number, number][][] = [];
  let current: [number, number][] = [];
  series.forEach((a, j) => {
    if ((gap && j === 6) || (offline && j >= 8)) {
      if (current.length) pieces.push(current);
      current = [];
    } else current.push([x(j), y(a)]);
  });
  if (current.length) pieces.push(current);

  const label = `${v.label}: grafik pemantauan${gap ? ", terdapat jeda data" : ""}${offline ? ", data berhenti saat perangkat offline" : ""}`;
  const labels = mini ? [] : RANGE_LABELS[range] ?? RANGE_LABELS["24h"];

  return (
    <svg
      className={mini ? chartClass.mini : chartClass[variant]}
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      role="img"
      aria-label={label}
    >
      {!mini &&
        Array.from({ length: 4 }, (_, j) => {
          const yy = top + (j * (bottom - top)) / 3;
          return (
            <g key={`grid-${j}`}>
              <line stroke="#e7ece7" strokeWidth="1" x1={left} x2={right} y1={yy} y2={yy} />
              <text x="2" y={yy + 4} {...TEXT_PROPS}>
                {wave ? "" : Math.round(max - (j * (max - min)) / 3)}
              </text>
            </g>
          );
        })}
      {!mini && !wave && (
        <text x={left} y="11" {...TEXT_PROPS}>
          {v.unit}
        </text>
      )}
      {!wave &&
        pieces.map((p, i) => (
          <path
            key={`area-${i}`}
            d={`M${p[0][0]},${bottom} ${p.map((q) => "L" + q.join(",")).join(" ")} L${p.at(-1)![0]},${bottom} Z`}
            fill={v.color}
            opacity=".045"
          />
        ))}
      {pieces.map((p, i) => (
        <path
          key={`line-${i}`}
          d={p.map((q, j) => (j ? "L" : "M") + q.join(",")).join(" ")}
          fill="none"
          stroke={v.color}
          strokeWidth={mini ? 2 : 2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ))}
      {!wave &&
        !mini &&
        pieces.flat().map((q, i) => <circle key={`dot-${i}`} cx={q[0]} cy={q[1]} r="2.3" fill={v.color} />)}
      {trend && <path d="M36,145 L610,80" stroke="#0d7772" strokeWidth="2" strokeDasharray="6 5" fill="none" />}
      {offline && (
        <>
          <rect x="460" y="16" width="150" height="160" fill="#f0f4f5" opacity=".65" />
          <text x="482" y="90" {...TEXT_PROPS}>
            Tidak ada data
          </text>
        </>
      )}
      {labels.map((t, j) => (
        <text
          key={`label-${j}`}
          x={left + (j * (right - left)) / 6}
          y="202"
          textAnchor={j === 0 ? "start" : j === 6 ? "end" : "middle"}
          {...TEXT_PROPS}
        >
          {t}
        </text>
      ))}
    </svg>
  );
}
