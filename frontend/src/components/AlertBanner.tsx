import { AlertTriangle } from "lucide-react";

export default function AlertBanner({ risk, message }: { risk: string; message: string }) {
  const classes = risk === "High" ? "border-red-200 bg-red-50 text-red-900" : risk === "Medium" ? "border-amber-200 bg-amber-50 text-amber-900" : "border-green-200 bg-green-50 text-green-900";
  return (
    <div className={`flex items-start gap-3 rounded-lg border p-3 ${classes}`}>
      <AlertTriangle className="mt-0.5 shrink-0" size={18} />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}
