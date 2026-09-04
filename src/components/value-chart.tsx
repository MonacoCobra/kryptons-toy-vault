import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { usd } from "@/lib/format";

export function ValueChart({ data }: { data: { label: string; value: number }[] }) {
  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="vaultFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ffd200" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#ffd200" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="label" tick={{ fill: "#8b9bb4", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis
            tick={{ fill: "#8b9bb4", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={56}
            tickFormatter={(v) => `$${Math.round(Number(v))}`}
          />
          <Tooltip
            contentStyle={{ background: "#0e1628", border: "1px solid #243454", borderRadius: 8 }}
            labelStyle={{ color: "#8b9bb4" }}
            formatter={(v) => usd(Number(v))}
          />
          <Area type="monotone" dataKey="value" stroke="#ffd200" strokeWidth={2} fill="url(#vaultFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
