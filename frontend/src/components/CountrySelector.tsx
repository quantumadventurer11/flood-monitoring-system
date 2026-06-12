import type { Region } from "../api/client";

export type Country = Pick<Region, "country" | "lat" | "lon"> & Partial<Region>;

export const countries: Country[] = [
  { country: "Bangladesh", lat: 23.685, lon: 90.3563, risk_baseline: 0.82 },
  { country: "India", lat: 20.5937, lon: 78.9629, risk_baseline: 0.68 },
  { country: "USA", lat: 37.0902, lon: -95.7129, risk_baseline: 0.42 },
];

export function countryFlag(country: string) {
  const flags: Record<string, string> = {
    Bangladesh: "🇧🇩",
    India: "🇮🇳",
    Pakistan: "🇵🇰",
    Nigeria: "🇳🇬",
    Mozambique: "🇲🇿",
    Indonesia: "🇮🇩",
    Philippines: "🇵🇭",
    Vietnam: "🇻🇳",
    China: "🇨🇳",
    Brazil: "🇧🇷",
    Peru: "🇵🇪",
    USA: "🇺🇸",
    Canada: "🇨🇦",
    Germany: "🇩🇪",
    Netherlands: "🇳🇱",
    Australia: "🇦🇺",
    Japan: "🇯🇵",
    Myanmar: "🇲🇲",
    Thailand: "🇹🇭",
    Cambodia: "🇰🇭",
    "South Sudan": "🇸🇸",
    Somalia: "🇸🇴",
    Ethiopia: "🇪🇹",
    Ghana: "🇬🇭",
    Mexico: "🇲🇽",
    Colombia: "🇨🇴",
    Bolivia: "🇧🇴",
  };
  return flags[country] ?? "🌍";
}

export default function CountrySelector({
  value,
  regions,
  onChange,
  label = "Country",
}: {
  value: Country;
  regions?: Country[];
  onChange: (country: Country) => void;
  label?: string;
}) {
  const options = regions?.length ? regions : countries;
  const selectId = `${label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-select`;
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">{label}</span>
      <select
        id={selectId}
        aria-label={label}
        className="form-control"
        value={value.country}
        onChange={(event) => {
          const match = options.find((item) => item.country === event.target.value);
          if (match) onChange(match);
        }}
      >
        {options.map((item) => (
          <option key={item.country} value={item.country}>
            {countryFlag(item.country)} {item.country}
          </option>
        ))}
      </select>
    </label>
  );
}
