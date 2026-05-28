const countries = [
  { country: "Bangladesh", lat: 23.8103, lon: 90.4125 },
  { country: "India", lat: 20.5937, lon: 78.9629 },
  { country: "United States", lat: 37.0902, lon: -95.7129 },
  { country: "Rwanda", lat: -1.9403, lon: 29.8739 },
  { country: "Brazil", lat: -14.235, lon: -51.9253 },
];

export type Country = (typeof countries)[number];

export default function CountrySelector({ value, onChange }: { value: Country; onChange: (country: Country) => void }) {
  return (
    <select
      className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
      value={value.country}
      onChange={(event) => onChange(countries.find((item) => item.country === event.target.value) ?? countries[0])}
    >
      {countries.map((item) => <option key={item.country}>{item.country}</option>)}
    </select>
  );
}

export { countries };
