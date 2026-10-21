import Image, { getImageProps } from "next/image";
import Link from "next/link";
import careClinician from "@/assets/care-clinician.png";
import heroHome from "@/assets/care-hero-home.png";
import carePatient from "@/assets/care-patient.png";
import { LandingEnhancer } from "@/components/landing/LandingEnhancer";
import {
  ArrowRight,
  ArrowUpRight,
  ChartNoAxesCombined,
  Check,
  Clock3,
  Droplets,
  Heart,
  House,
  Icon,
  LungIcon,
  Menu,
  Plus,
  Stethoscope,
  UserRound,
  Wind,
} from "@/components/ui/Icon";
import { Brand, cn } from "@/components/ui/primitives";

/* Lebar container: .lp-container dan varian header/hero/strip yang lebih sempit. */
const lpWide = "mx-auto w-[min(1280px,calc(100%-80px))] max-xl:w-[calc(100%-56px)] max-md:w-[calc(100%-40px)]";
const lpNarrow = "mx-auto w-[min(1200px,calc(100%-64px))] max-lg:w-[calc(100%-48px)] max-xxs:w-[calc(100%-32px)]";

const btnCore =
  "inline-flex items-center justify-center gap-[9px] border font-semibold leading-[1.4] transition-[background,border-color] duration-180 ease-[ease] hover:no-underline";
const sectionTitle =
  "text-[34px] leading-[1.23] font-semibold tracking-[-1px] max-md:text-[28px] max-md:tracking-[-.7px]";
const textLink = "inline-flex items-center gap-3.5 text-[13px] font-semibold text-teal py-1 max-md:text-[12px]";

/* 1×1 GIF transparan: mencegah unduhan gambar yang memang tersembunyi di breakpoint tertentu. */
const BLANK = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";

type Tone = "rose" | "blue" | "teal";
const VITALS: [typeof Heart | "lung", string, string, string, string, Tone][] = [
  [Heart, "HR", "Detak jantung", "78", "bpm", "rose"],
  ["lung", "SpO₂", "Kadar oksigen", "96", "%", "blue"],
  [Wind, "RR", "Laju napas", "18", "/menit", "teal"],
];
/* Warna cerah khusus ringkasan hero & strip vital (.care-summary .rose, dst.). */
const BRIGHT: Record<Tone, string> = { rose: "text-[#ff6c6a]", blue: "text-[#24a1fa]", teal: "text-[#10a78f]" };
const SPARKS: Record<Tone, string> = {
  rose: "M2 20C10 15 14 28 25 24S40 17 48 20 62 29 73 23 92 9 101 14 116 24 126 18 139 15 148 18 161 17 178 15",
  blue: "M2 14C10 8 17 27 27 22S40 10 49 16 60 23 70 14 83 7 92 9 110 28 121 18 132 3 142 14 157 27 167 19 174 18 178 17",
  teal: "M2 26C10 25 14 9 23 15S33 29 42 21 51 20 60 23 74 21 82 18 94 0 103 14 115 28 123 14 134 5 142 20 155 21 163 18 172 21 178 21",
};

function VitalIcon({ icon, className }: { icon: (typeof VITALS)[number][0]; className: string }) {
  return icon === "lung" ? <LungIcon className={className} /> : <Icon icon={icon} className={className} />;
}

function Summary() {
  return (
    <div className="relative z-[1] bg-white border border-[#e1eeeb] rounded-[12px] shadow-[0_8px_24px_#214e4710] text-[#12394a] w-[94%] ml-auto -mt-[22px] pt-[13px] px-4 pb-[15px] sm:max-xl:w-[96%] sm:max-xl:pt-3 sm:max-xl:px-3.5 sm:max-xl:pb-3.5 md:max-xl:-mt-4 max-md:mt-[18px] max-md:mx-auto max-md:rounded-[10px] max-md:shadow-[0_5px_18px_#214e470a] max-sm:w-full max-sm:max-w-[440px] max-sm:pt-3 max-sm:px-[13px] max-sm:pb-[13px]">
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        <h3 className="text-[14px] font-bold text-[#0c5361] tracking-[-.3px] max-xl:text-[13px]">Ringkasan hari ini</h3>
      </div>
      <div className="grid grid-cols-3 gap-3 mt-[13px] max-xl:gap-[9px] sm:max-xl:mt-3 max-sm:mt-[11px]">
        {VITALS.map(([icon, key, , value, unit, tone]) => (
          <div
            key={key}
            className={cn(
              "min-w-0 not-first:border-l not-first:border-[#e0e8ec] not-first:pl-3 max-xl:not-first:pl-[9px]",
              BRIGHT[tone],
            )}
          >
            <div className="flex gap-[7px] items-start max-xl:block">
              <VitalIcon
                icon={icon}
                className="size-5 stroke-[1.5] max-xl:float-left max-xl:w-[17px] max-xl:h-[18px] lg:max-xl:mr-1.5 max-lg:mr-[5px] max-sm:w-4 max-sm:h-[17px]"
              />
              <div className="min-w-0 max-xl:contents">
                <span className="block text-[12px] leading-[1.4] text-[#183b4e] max-xl:text-[11px] max-lg:leading-[18px] max-sm:leading-[17px]">
                  {key}
                </span>
                <strong className="block text-[27px] leading-[1.25] tracking-[-.5px] font-bold mt-0.5 text-[#102e42] tabular-nums max-xl:clear-both max-xl:pt-[3px] max-xl:text-[25px] max-sm:text-[24px] max-sm:pt-0.5">
                  {value}
                  <small className="inline-block text-[11px] tracking-normal font-normal ml-[3px] text-[#254255] max-xl:text-[10px]">
                    {unit}
                  </small>
                </strong>
              </div>
            </div>
            <svg
              viewBox="0 0 180 46"
              aria-hidden="true"
              className="block w-full h-[25px] mt-[11px] overflow-hidden max-sm:h-[22px] max-sm:mt-[9px]"
            >
              <path d={`${SPARKS[tone]}L178 46H2Z`} fill="currentColor" opacity=".055" />
              <path d={SPARKS[tone]} fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <div aria-hidden="true" className="flex justify-between text-[8px] text-[#7c899a] leading-[1.5] mt-[3px]">
              <span>00</span>
              <span>06</span>
              <span>12</span>
              <span>18</span>
              <span>24</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Header() {
  const navLink = "text-navy max-md:py-3 max-md:min-h-11";
  return (
    <header className="relative z-40 h-[72px] bg-white max-md:h-16">
      <div className={cn(lpNarrow, "h-full flex items-center justify-between gap-3 *:min-w-0")}>
        <Brand variant="header" />
        <nav
          id="public-nav"
          aria-label="Navigasi website"
          className="flex items-center gap-7 text-[14px] max-xl:gap-[23px] max-md:hidden max-md:absolute max-md:top-[63px] max-md:inset-x-0 max-md:bg-white max-md:p-5 max-md:border-b max-md:border-line max-md:items-stretch max-md:[&.open]:flex max-md:[&.open]:flex-col max-md:[&.open]:gap-[3px]"
        >
          <a href="#cara-kerja" data-scroll="cara-kerja" className={navLink}>
            Cara kerja
          </a>
          <a href="#manfaat" data-scroll="manfaat" className={navLink}>
            Manfaat
          </a>
          <a href="#faq" data-scroll="faq" className={navLink}>
            FAQ
          </a>
          <Link href="/login" className={navLink}>
            Masuk
          </Link>
          <Link
            href="/signup"
            className={cn(
              btnCore,
              "rounded-[7px] border-[#0b4855] bg-[#0b4855] text-white text-[13px] min-h-11 px-[23px] py-2.5 hover:bg-navy hover:border-navy max-md:text-[14px] max-md:p-3 max-md:mt-2.5",
            )}
          >
            Daftar
          </Link>
        </nav>
        <button
          type="button"
          data-menu
          aria-controls="public-nav"
          aria-label="Buka menu"
          aria-expanded="false"
          className="hidden max-md:grid place-items-center relative size-[42px] rounded-[6px] border border-line bg-white text-black"
        >
          <Icon icon={Menu} />
        </button>
      </div>
    </header>
  );
}

function Hero() {
  const {
    props: { srcSet: backdropSet, ...backdrop },
  } = getImageProps({
    src: heroHome,
    alt: "",
    sizes: "(max-width: 1600px) 100vw, 1600px",
    loading: "eager",
    fetchPriority: "high",
  });
  const {
    props: { srcSet: mobileSet, sizes: mobileSizes },
  } = getImageProps({
    src: carePatient,
    alt: "",
    sizes: "(max-width: 480px) calc(100vw - 40px), 440px",
  });
  const action = "min-h-12 px-[22px] py-3 text-[14px] rounded-[7px] whitespace-normal lg:max-xl:px-4 lg:max-xl:text-[13px] max-lg:min-h-[46px] max-lg:py-[11px] sm:max-lg:px-[13px] sm:max-lg:text-[12px] max-sm:px-4 max-sm:text-[13px] max-xxs:px-3 max-xxs:text-[12px]";

  return (
    <section aria-labelledby="care-title" className="relative isolate overflow-hidden bg-[#edf8f5]">
      <picture>
        <source media="(max-width: 767px)" srcSet={BLANK} />
        <img
          {...backdrop}
          srcSet={backdropSet}
          alt=""
          aria-hidden="true"
          className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-full max-w-[1600px] h-full object-cover object-[center_35%] pointer-events-none z-0 max-md:hidden"
        />
      </picture>
      <div
        className={cn(
          lpNarrow,
          "relative z-[1] grid grid-cols-2 gap-11 items-center py-[42px] min-h-[490px] lg:max-xl:gap-7 lg:max-xl:py-9 lg:shorter:py-[26px] lg:shorter:min-h-0 max-lg:min-h-0 md:max-lg:gap-6 sm:max-lg:py-8 max-sm:py-7 max-md:grid-cols-1 max-md:gap-5 max-md:max-w-[600px]",
        )}
      >
        <div className="relative min-w-0">
          <h1
            id="care-title"
            className="text-[clamp(34px,3.55vw,50px)] leading-[1.18] tracking-[-1.8px] font-bold text-[#0b303e] [overflow-wrap:break-word] lg:max-xl:text-[34px] lg:max-xl:tracking-[-1.3px] lg:shorter:text-[clamp(34px,3.3vw,46px)] md:max-lg:text-[clamp(28px,3.8vw,34px)] sm:max-lg:tracking-[-1px] max-md:text-[clamp(27px,7.2vw,34px)] max-md:leading-[1.22] max-sm:tracking-[-.9px]"
          >
            Napas lebih terpantau.
            <br />
            <span>Hari-hari lebih tenang.</span>
          </h1>
          <p className="text-[18px] leading-[1.7] text-[#587782] mt-[23px] max-w-[40ch] lg:max-xl:text-[16px] max-lg:text-[15px] max-lg:leading-[1.65] max-lg:mt-[18px]">
            Pantau kondisi pernapasan dari rumah,
            <br className="max-lg:hidden" /> bersama tenaga medis Anda.
          </p>
          <div className="flex flex-wrap items-center gap-3.5 mt-7 max-xl:gap-2.5 max-lg:mt-[22px] max-md:mt-5 max-xxs:gap-2">
            <Link
              href="/signup"
              className={cn(btnCore, action, "bg-[#108493] border-[#108493] text-white hover:bg-navy hover:border-navy")}
            >
              Mulai pemantauan
            </Link>
            <button
              type="button"
              data-scroll="cara-kerja"
              className={cn(
                btnCore,
                action,
                "bg-transparent border-[#137e8b] text-[#086473] hover:bg-[#f0f7f4] hover:border-[#9caea4]",
              )}
            >
              Lihat cara kerja
            </button>
          </div>
        </div>
        <div className="relative isolate min-w-0 max-lg:w-full max-lg:max-w-[600px] max-lg:mx-auto max-md:flex max-md:flex-col max-md:items-stretch">
          <div className="relative overflow-hidden h-[305px] lg:shorter:h-[265px] md:max-lg:h-60 max-md:h-auto max-md:aspect-[3/2] max-md:w-full max-md:max-w-[440px] max-md:mx-auto max-md:rounded-[10px] max-md:bg-mint max-md:mt-[5px]">
            <picture className="max-md:block max-md:w-full max-md:h-full">
              <source media="(max-width: 767px)" srcSet={mobileSet} sizes={mobileSizes} />
              <img
                src={BLANK}
                alt="Pasien memantau kondisi dari ponsel di rumah"
                width={1536}
                height={1024}
                fetchPriority="high"
                decoding="async"
                className="hidden max-md:block max-md:w-full max-md:h-full max-md:object-contain max-md:object-center"
              />
            </picture>
          </div>
          <Summary />
        </div>
      </div>
    </section>
  );
}

function VitalStrip() {
  const copy: Record<string, [string, string]> = {
    HR: ["Memantau denyut jantung", "untuk melihat kondisi tubuh Anda."],
    "SpO₂": ["Memantau kadar oksigen", "dalam darah."],
    RR: ["Memantau frekuensi napas", "untuk mendukung kesehatan pernapasan."],
  };
  return (
    <section aria-label="Tiga tanda vital pemantauan" className="bg-white border-b border-[#e6efeb] py-7 max-md:py-6">
      <div className={cn(lpNarrow, "grid grid-cols-3 gap-7 max-xl:gap-[18px] max-md:grid-cols-1 max-md:gap-5")}>
        {VITALS.map(([icon, key, name, , , tone]) => (
          <div
            key={key}
            className="flex gap-[19px] items-center min-w-0 not-first:border-l not-first:border-[#dce4e9] not-first:pl-7 lg:max-xl:gap-[13px] max-xl:not-first:pl-[18px] max-lg:block max-md:flex max-md:gap-[17px] max-md:not-first:border-l-0 max-md:not-first:pl-0"
          >
            <span className={cn("shrink-0 max-lg:block max-lg:mb-[9px] max-md:m-0", BRIGHT[tone])}>
              <VitalIcon icon={icon} className="size-[38px] stroke-[1.5] max-xl:size-[30px] max-md:size-[33px]" />
            </span>
            <div>
              <h3 className="text-[15px] text-[#173447] font-bold max-lg:text-[14px]">{name}</h3>
              <p className="text-[12px] leading-[1.6] text-[#758594] mt-1 max-md:mt-[3px]">
                {/* Spasi ini tidak ada di referensi: tanpa spasi, teks menyatu saat <br> disembunyikan (<=900px). */}
                {copy[key][0]}{" "}
                <br className="max-lg:hidden" />
                {copy[key][1]}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

const STEPS = [
  [
    "Jalani hari di rumah",
    "Pemantauan menyertai keseharian Anda. Lihat pembacaan terbaru dan status koneksi saat membuka dashboard.",
  ],
  [
    "Kenali perubahan kondisi",
    "Riwayat detak jantung, kadar oksigen, dan laju napas membantu Anda melihat perubahan dari waktu ke waktu.",
  ],
  [
    "Tetap didampingi",
    "Tenaga medis meninjau data dan peringatan untuk mendukung pemantauan sesuai kebutuhan Anda.",
  ],
];

const scene =
  "absolute inset-0 overflow-hidden rounded-[12px] pointer-events-none [transition:opacity_.4s,transform_.5s]";
const sceneHidden = "opacity-0 [transform:translateY(10px)]";
const storyArtSizes = "(max-width: 767px) min(360px, calc(100vw - 40px)), (max-width: 1100px) 50vw, 640px";

function Story() {
  return (
    <section
      id="cara-kerja"
      data-story
      data-stage="0"
      aria-labelledby="care-story-title"
      className="group/deck relative h-[300svh] bg-[#f5faf8] text-navy max-md:h-auto reduced:h-auto"
    >
      <div
        data-story-pin
        className="sticky top-0 h-svh min-h-[640px] pt-[38px] pb-[85px] overflow-hidden md:short:min-h-[600px] md:short:pt-[27px] max-md:relative max-md:h-auto max-md:min-h-0 max-md:pt-7 max-md:pb-8 max-md:overflow-visible reduced:relative reduced:h-auto reduced:min-h-0 reduced:pb-[95px] max-md:reduced:pb-8"
      >
        <div className={lpWide}>
          <div className="flex items-end justify-between gap-10 max-md:gap-4">
            <div>
              <p className="text-[10px] font-semibold tracking-[1.6px] uppercase text-[#548b81] mb-[13px] md:short:mb-[9px] max-md:text-[9px] max-md:mb-2.5 max-md:tracking-[1.3px]">
                DALAM KESEHARIAN ANDA
              </p>
              <h2
                id="care-story-title"
                className="text-[36px] leading-[1.2] font-semibold tracking-[-1px] max-xl:text-[33px] md:short:text-[31px] max-md:text-[29px] max-md:tracking-[-.7px]"
              >
                Menjalani hari,
                <br />
                tetap terpantau.
              </h2>
            </div>
            <p className="text-[14px] leading-[1.8] text-muted ml-auto max-md:hidden">
              Pemantauan yang mudah diikuti,
              <br />
              untuk Anda dan tenaga medis.
            </p>
            <div className="flex items-baseline gap-2 max-md:gap-[5px]">
              <b data-story-count className="text-[31px] font-medium text-[#2d8177] max-md:text-[27px]">
                01
              </b>
              <small className="max-md:text-[10px]">/ 03</small>
            </div>
          </div>
          <div className="grid grid-cols-[1.25fr_1fr] gap-[65px] items-center mt-[26px] max-xl:gap-[35px] md:short:mt-5 max-md:grid-cols-[1fr] max-md:gap-5 max-md:mt-5">
            <div className="min-w-0">
              <div
                data-velocity=".12"
                className="relative h-[clamp(260px,43svh,390px)] bg-mint rounded-[12px] will-change-transform max-xl:h-80 md:short:h-[290px] max-md:h-[clamp(190px,54vw,250px)] max-md:w-full max-md:max-w-[360px] max-md:mx-auto reduced:[transform:none]!"
              >
                <div
                  className={cn(
                    scene,
                    "opacity-100 [transform:none] max-md:bg-mint group-data-[stage=1]/deck:opacity-0 group-data-[stage=1]/deck:[transform:translateY(-10px)] group-data-[stage=2]/deck:opacity-0 group-data-[stage=2]/deck:[transform:translateY(-10px)]",
                  )}
                >
                  <Image
                    src={carePatient}
                    alt="Pasien menjalani pemantauan dari rumah"
                    sizes={storyArtSizes}
                    className="h-full w-full object-contain"
                  />
                </div>
                <div
                  className={cn(
                    scene,
                    sceneHidden,
                    "group-data-[stage=1]/deck:opacity-100 group-data-[stage=1]/deck:[transform:none] bg-white border border-[#dcebe6] flex flex-col gap-0 px-6 py-5 max-md:px-4 max-md:py-[13px] max-md:shortest:px-[13px] max-md:shortest:py-2.5",
                  )}
                >
                  <div className="flex justify-between items-center gap-4 shrink-0 max-md:gap-2">
                    <h3 className="text-[15px] leading-[1.35] max-md:text-[12px]">Perubahan kondisi Anda</h3>
                    <span className="text-[10px] text-muted max-md:text-[8px]">24 jam terakhir</span>
                  </div>
                  <div className="mt-3 shrink-0 max-md:mt-[7px] max-md:shortest:mt-1">
                    <span className="flex items-center gap-2 text-[12px] text-rose max-md:text-[10px]">
                      <Icon icon={Heart} className="size-[17px] max-md:size-3.5" />
                      Detak jantung
                    </span>
                    <strong className="block text-[32px] leading-[1.15] tracking-[-1px] font-medium mt-1 max-md:text-[25px] max-md:mt-0.5 max-md:leading-[1.1] max-md:shortest:text-[23px]">
                      78 <small className="text-[12px] tracking-normal font-normal max-md:text-[10px]">bpm</small>
                    </strong>
                    <p className="text-[10px] leading-[1.4] text-muted mt-[3px] max-md:text-[8px] max-md:mt-0.5">
                      Pembacaan terakhir pukul 09.30 WIB
                    </p>
                  </div>
                  <svg
                    viewBox="0 0 540 160"
                    preserveAspectRatio="none"
                    role="img"
                    aria-label="Riwayat detak jantung"
                    className="block w-full flex-[1_1_70px] min-h-[38px] h-auto mt-2.5 overflow-visible max-md:min-h-7 max-md:basis-9 max-md:mt-1.5 max-md:shortest:min-h-5 max-md:shortest:basis-[25px] max-md:shortest:mt-1"
                  >
                    <path d="M0 30H540M0 80H540M0 130H540" stroke="#e7efed" strokeWidth="1" fill="none" />
                    <path
                      d="M0 93L28 87L56 98L84 80L112 92L140 85L168 89L196 60L224 82L252 88L280 79L308 90L336 74L364 88L392 72L420 85L448 80L476 90L504 85L540 86"
                      stroke="var(--color-rose)"
                      strokeWidth="2.1"
                      fill="none"
                      strokeLinejoin="round"
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="flex justify-between text-[9px] text-muted shrink-0 leading-[1.4] mt-1 max-md:text-[8px] max-md:mt-[3px]">
                    <span>00.00</span>
                    <span>06.00</span>
                    <span>12.00</span>
                    <span>18.00</span>
                    <span>24.00</span>
                  </div>
                  <div className="flex items-center gap-2 border-t border-line shrink-0 pt-2 mt-2.5 text-[10px] leading-[1.4] text-[#5d7975] max-md:hidden">
                    <Icon icon={Clock3} className="size-[15px]" />
                    Lihat riwayat, pahami perubahan.
                  </div>
                </div>
                <div
                  className={cn(
                    scene,
                    sceneHidden,
                    "group-data-[stage=2]/deck:opacity-100 group-data-[stage=2]/deck:[transform:none]",
                  )}
                >
                  <Image
                    src={careClinician}
                    alt="Tenaga medis meninjau informasi pemantauan pasien di laptop"
                    sizes={storyArtSizes}
                    className="h-full w-full object-contain"
                  />
                  <div className="absolute bottom-[18px] left-5 right-5 bg-white border border-line rounded-[7px] px-[15px] py-[11px] text-[12px] text-teal flex gap-2.5 items-center max-md:bottom-2 max-md:left-2.5 max-md:right-2.5 max-md:px-2.5 max-md:py-[7px] max-md:text-[10px] max-md:shortest:text-[9px] max-md:shortest:px-2 max-md:shortest:py-1.5">
                    <Icon icon={Stethoscope} className="size-[18px] max-md:size-[15px]" />
                    Pendampingan tenaga medis
                  </div>
                </div>
              </div>
              <p
                data-story-note
                className="mt-[13px] text-[11px] text-muted text-center min-h-[18px] max-md:text-[10px] max-md:leading-[1.5] max-md:mt-2.5 max-md:min-h-[15px]"
              >
                Pemantauan mengikuti aktivitas Anda di rumah.
              </p>
            </div>
            <div className="relative pl-[26px] min-w-0 max-md:pl-[17px]">
              <div className="absolute top-2.5 bottom-2 left-0 w-0.5 bg-[#dce9e3] overflow-hidden rounded-[2px] max-md:top-2">
                <span data-story-rail className="block bg-[#1d8b7e] w-full h-0" />
              </div>
              {STEPS.map(([title, text], j) => (
                <button
                  key={title}
                  type="button"
                  data-story-jump={j}
                  aria-current={j === 0 ? "step" : undefined}
                  className="group/step flex gap-[17px] py-4 min-h-[102px] w-full text-left border-0 border-b border-[#dfeae6] last-of-type:border-b-0 bg-transparent text-[#58777d] opacity-[.78] transition-[color,opacity] duration-200 ease-[ease] aria-[current=step]:opacity-100 aria-[current=step]:text-navy md:short:py-3 md:short:min-h-[87px] max-md:py-3 max-md:min-h-11 max-md:gap-3"
                >
                  <span className="text-[17px] leading-[1.5] text-[#6f9d94] font-medium group-aria-[current=step]/step:text-primary max-md:text-[14px]">
                    0{j + 1}
                  </span>
                  <span>
                    <strong className="block text-[19px] leading-[1.3] font-medium tracking-[-.4px] max-md:text-[15px]">
                      {title}
                    </strong>
                    <span className="block text-[13px] leading-[1.7] text-[#667d80] mt-[9px] max-w-[40ch] max-xl:text-[12px] md:short:text-[11px] md:short:leading-[1.6] max-md:hidden max-md:group-aria-[current=step]/step:block max-md:text-[12px] max-md:leading-[1.7] max-md:mt-1.5 max-md:max-w-none">
                      {text}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-[repeat(3,1fr)] gap-[25px] border-t border-[#dce9e3] pt-[22px] mt-[25px] md:short:pt-[17px] md:short:mt-5 max-md:grid-cols-3 max-md:gap-2.5 max-md:pt-[15px] max-md:mt-[22px]">
            {(
              [
                [House, "Dari rumah"],
                [ChartNoAxesCombined, "Riwayat lebih jelas"],
                [Stethoscope, "Tetap didampingi"],
              ] as const
            ).map(([icon, label], j) => (
              <div
                key={label}
                data-tech={j}
                data-active={j === 0 ? "" : undefined}
                className="flex gap-3.5 items-center text-[18px] font-semibold leading-[1.4] text-[#547772] data-active:text-teal md:max-xl:text-[16px] md:max-xl:gap-[11px] md:short:text-[16px] max-md:flex-col max-md:gap-[7px] max-md:text-[13px] max-md:text-center max-md:justify-start max-md:items-center"
              >
                <Icon
                  icon={icon}
                  className="size-7 stroke-[1.6] md:max-xl:size-[25px] md:short:size-[26px] max-md:size-6"
                />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function Benefits() {
  const audiences = [
    {
      icon: UserRound,
      title: "Untuk pasien",
      text: "Ketahui kondisi dari pembacaan terbaru tanpa harus memahami istilah yang rumit.",
      items: [
        "Ringkasan tanda vital yang mudah dibaca",
        "Riwayat pemantauan dan pemberitahuan",
        "Status koneksi dan waktu pembaruan yang jelas",
      ],
      href: "/signup/patient",
      cta: "Daftar sebagai pasien",
    },
    {
      icon: Stethoscope,
      title: "Untuk tenaga medis",
      text: "Tinjau perubahan, lihat konteks riwayat, dan tentukan pasien yang perlu mendapat perhatian.",
      items: [
        "Daftar pasien berdasarkan prioritas perhatian",
        "Tanda vital, analisis tren, dan riwayat alert",
        "Peninjauan dan konfigurasi pemantauan per pasien",
      ],
      href: "/signup/clinician",
      cta: "Daftar sebagai tenaga medis",
    },
  ];
  return (
    <section
      id="manfaat"
      data-overlap
      className="relative z-[5] bg-white pt-[70px] pb-20 -mt-10 rounded-t-[20px] origin-top border-t border-[#e1ebe6] max-md:pt-[45px] max-md:pb-[50px] max-md:mt-0 max-md:rounded-t-[16px] reduced:[transform:none]!"
    >
      <div className={lpWide}>
        <div className="flex justify-between items-end gap-10 max-md:block">
          <h2 className={cn(sectionTitle, "max-md:leading-[1.25] max-md:tracking-[-.6px]")}>
            Satu layanan,
            <br />
            untuk saling terhubung.
          </h2>
          <p className="text-[14px] leading-[1.8] text-muted max-md:text-[13px] max-md:mt-[18px]">
            Pengalaman yang sederhana untuk pasien,
            <br />
            informasi yang tertata untuk tenaga medis.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-7 mt-9 max-md:grid-cols-[1fr] max-md:gap-[19px] max-md:mt-7">
          {audiences.map((a, i) => (
            <article
              key={a.title}
              className={cn(
                "border rounded-[12px] p-[30px] max-xl:p-[25px] max-md:p-[23px]",
                i === 0 ? "bg-[#f2f9f6] border-[#deeee6]" : "bg-[#f3f8fb] border-[#e0eaf0]",
              )}
            >
              <div className="flex items-center gap-3">
                <span
                  className={cn(
                    "grid place-items-center size-[42px] rounded-[10px]",
                    i === 0 ? "text-teal bg-[#e0f0e9]" : "text-blue bg-[#e5eff5]",
                  )}
                >
                  <Icon icon={a.icon} className="size-[22px]" />
                </span>
                <h3 className="text-[20px] font-semibold max-md:text-[18px]">{a.title}</h3>
              </div>
              <p className="text-[14px] text-[#627e7d] leading-[1.8] mt-5 max-w-[44ch] max-md:text-[13px] max-md:mt-[18px]">
                {a.text}
              </p>
              <ul className="list-none p-0 mt-6 mb-[26px] grid gap-[13px] text-[13px] text-[#456b65] max-md:text-[12px] max-md:mt-5 max-md:gap-3">
                {a.items.map((item) => (
                  <li key={item} className="flex gap-2.5 items-start">
                    <Icon icon={Check} className="text-teal size-[17px] mt-0.5" />
                    {item}
                  </li>
                ))}
              </ul>
              <Link href={a.href} className={textLink}>
                {a.cta} <Icon icon={ArrowRight} className="size-4" />
              </Link>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function Monitor() {
  const items: [typeof Heart, string, string, string, string][] = [
    [Heart, "Detak jantung", "HR (bpm)", "Jumlah denyut jantung per menit, ditampilkan untuk melihat perubahan sepanjang pemantauan.", "text-rose"],
    [Droplets, "Kadar oksigen", "SpO₂ (%)", "Perkiraan saturasi oksigen dalam darah, disajikan bersama waktu pembacaan dan riwayatnya.", "text-blue"],
    [Wind, "Laju napas", "RR (napas/menit)", "Frekuensi napas untuk membantu peninjauan pola pernapasan oleh tenaga medis.", "text-teal"],
  ];
  return (
    <section className="bg-[#f5faf8] py-[70px] max-md:py-12">
      <div className={cn(lpWide, "grid grid-cols-[1fr_1.15fr] gap-[90px] max-xl:gap-[55px] max-md:grid-cols-[1fr] max-md:gap-[30px]")}>
        <div>
          <h2 className={sectionTitle}>
            Apa yang dapat
            <br />
            Anda pantau?
          </h2>
          <p className="text-[14px] leading-[1.8] text-muted my-[23px] max-w-[37ch] max-md:text-[13px] max-md:max-w-[44ch] max-md:my-5">
            Tiga tanda vital ditampilkan bersama riwayatnya. Saat data terputus, Anda akan melihat status koneksi dan
            waktu pembacaan terakhir.
          </p>
          <Link href="/login" className={textLink}>
            Buka dashboard <Icon icon={ArrowRight} className="size-4" />
          </Link>
        </div>
        <div>
          {items.map(([icon, title, unit, text, color]) => (
            <article
              key={title}
              className="flex gap-[22px] py-6 border-t border-line first:pt-0 first:border-t-0 max-md:py-[22px] max-md:gap-[17px] max-md:first:pt-0"
            >
              <span className={color}>
                <Icon icon={icon} className="size-[25px]" />
              </span>
              <div>
                <h3 className="text-[17px] font-semibold max-md:text-[16px]">{title}</h3>
                <small className="text-[11px] block mt-[3px]">{unit}</small>
                <p className="text-[13px] text-muted leading-[1.8] mt-3 max-w-[45ch]">{text}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

const FAQ: [string, string][] = [
  [
    "Untuk siapa PNEUMACARE dibuat?",
    "PNEUMACARE ditujukan untuk pemantauan pasien PPOK dari rumah dan peninjauan oleh tenaga medis. Penggunaan perangkat mengikuti arahan pengelola dan tenaga medis.",
  ],
  [
    "Apakah PNEUMACARE menggantikan diagnosis dokter?",
    "PNEUMACARE membantu pemantauan kondisi pernapasan. Penilaian kondisi dan keputusan perawatan tetap dilakukan oleh tenaga medis.",
  ],
  [
    "Apa yang terjadi jika koneksi perangkat terputus?",
    "Dashboard menampilkan status offline dan waktu pembacaan terakhir. Periode tanpa data ditampilkan sebagai jeda, bukan dianggap sebagai kondisi yang stabil.",
  ],
  [
    "Bagaimana cara kerja teknologi di dalamnya?",
    "Sensor rompi mengumpulkan sinyal melalui sistem benam. Sistem kecerdasan mengolah sinyal tersebut menjadi informasi kardio-respirasi, kemudian IoT menghubungkannya dengan dashboard pemantauan.",
  ],
  [
    "Bagaimana saya mulai melakukan pemantauan?",
    "Daftarkan akun, hubungkan rompi menggunakan kode pairing, dan ikuti arahan tenaga medis pendamping Anda.",
  ],
];

function Faq() {
  return (
    <section id="faq" className="bg-white py-[75px] max-md:py-12">
      <div className={cn(lpWide, "grid grid-cols-[1fr_1.25fr] gap-[90px] max-xl:gap-[55px] max-md:grid-cols-[1fr] max-md:gap-7")}>
        <div>
          <h2 className={sectionTitle}>
            Ada yang ingin
            <br />
            Anda ketahui?
          </h2>
          <p className="text-[14px] leading-[1.8] text-muted max-w-[28ch] mt-[22px] max-md:text-[13px] max-md:mt-[18px] max-md:max-w-[40ch]">
            Informasi sebelum mulai menggunakan PNEUMACARE.
          </p>
        </div>
        <div>
          {FAQ.map(([q, a]) => (
            <details key={q} className="group/faq py-[21px] border-t border-line last:border-b max-md:py-[19px]">
              <summary className="flex items-center justify-between gap-5 text-[14px] cursor-pointer list-none [&::-webkit-details-marker]:hidden max-md:text-[13px]">
                {q}
                <Icon icon={Plus} className="size-4 transition-transform duration-200 ease-[ease] group-open/faq:rotate-45" />
              </summary>
              <p className="text-[13px] leading-[1.8] text-muted mt-4 pr-[18px]">{a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

function Cta() {
  return (
    <section className="bg-[#e5f3ed] py-[52px] max-md:py-10">
      <div className={cn(lpWide, "flex items-center justify-between gap-10 max-md:block")}>
        <div>
          <h2 className="text-[31px] leading-[1.25] tracking-[-.8px] font-semibold max-md:text-[28px] max-md:tracking-[-.7px]">
            Pemantauan lebih dekat,
            <br />
            mulai dari rumah.
          </h2>
          <p className="text-[14px] mt-[17px] text-[#557971] max-md:text-[13px] max-md:leading-[1.8] max-md:max-w-[38ch]">
            Jelajahi pengalaman pasien dan tenaga medis di PNEUMACARE.
          </p>
        </div>
        <Link
          href="/signup"
          className={cn(
            btnCore,
            "rounded-[8px] bg-primary border-primary text-white text-[13px] min-h-11 px-[22px] py-3.5 whitespace-nowrap hover:bg-navy hover:border-navy max-md:mt-6",
          )}
        >
          Mulai pemantauan <Icon icon={ArrowRight} />
        </Link>
      </div>
    </section>
  );
}

function Footer() {
  const navLink = "min-h-6 content-center max-md:min-h-11 max-md:inline-flex max-md:items-center";
  return (
    <footer className="bg-white py-[38px] max-md:py-8">
      <div className={cn(lpWide, "flex justify-between items-start gap-[30px] max-md:flex-col max-md:gap-3")}>
        <div>
          <Brand />
          <p className="text-[11px] leading-[1.8] text-muted mt-3.5 max-md:mt-[11px]">
            Pemantauan kardio-respirasi dari rumah.
            <br />
            Tim PNEUMA, Universitas Gadjah Mada.
          </p>
        </div>
        <nav
          aria-label="Navigasi footer"
          className="grid gap-[9px] text-[12px] leading-[1.6] max-md:flex max-md:flex-wrap max-md:gap-x-6 max-md:gap-y-2.5"
        >
          <a href="#cara-kerja" data-scroll="cara-kerja" className={navLink}>
            Cara kerja
          </a>
          <a href="#manfaat" data-scroll="manfaat" className={navLink}>
            Manfaat
          </a>
          <a href="#faq" data-scroll="faq" className={navLink}>
            Pertanyaan umum
          </a>
        </nav>
        <div className="flex flex-col items-start gap-3.5 max-md:gap-[5px]">
          <Link
            href="/login"
            className="flex items-center gap-3 text-[12px] min-h-6 content-center max-md:text-[11px] max-md:min-h-11 max-md:inline-flex"
          >
            Masuk ke akun <Icon icon={ArrowUpRight} className="size-4" />
          </Link>
          <p className="text-[11px] leading-[1.8] text-muted">© {new Date().getFullYear()} PNEUMACARE</p>
        </div>
      </div>
    </footer>
  );
}

/** Landing publik (Server Component). Interaksi ditangani <LandingEnhancer />. */
export function Landing() {
  return (
    <div className="pneuma-landing bg-white text-navy">
      <a href="#main-content" data-scroll="main-content" className="fixed left-[15px] -top-20 z-200 bg-navy text-white px-[18px] py-2.5 focus:top-3">
        Langsung ke konten
      </a>
      <Header />
      <main id="main-content" tabIndex={-1}>
        <Hero />
        <VitalStrip />
        <Story />
        <Benefits />
        <Monitor />
        <Faq />
        <Cta />
      </main>
      <Footer />
      <LandingEnhancer />
    </div>
  );
}
