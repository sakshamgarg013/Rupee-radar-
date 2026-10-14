import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, Donut } from 'lucide-react';
import { BarChart, Bar, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client';

const CATEGORY_COLORS = {
  Food: '#f97316',
  Travel: '#3b82f6',
  Shopping: '#a855f7',
  Bills: '#f59e0b',
  EMI: '#ef4444',
  Subscriptions: '#14b8a6',
  Salary: '#22c55e',
  Rent: '#8b5cf6',
  Investments: '#06b6d4',
  Other: '#94a3b8',
};

export const CategoryChart: React.FC<{ sessionId?: string }> = ({ sessionId }) => {
  const [mode, setMode] = useState<'donut' | 'bar'>('donut');

  const { data: analysis, isLoading } = useQuery({
    queryKey: ['analytics', sessionId],
    queryFn: () => api.getAnalytics(sessionId as string),
    enabled: !!sessionId,
  });

  const data = useMemo(() => {
    if (!analysis?.top_categories?.length) {
      return [] as Array<{ name: string; value: number; total: number; percentage: number }>;
    }

    return analysis.top_categories.map((item) => ({
      name: item.category,
      value: item.total,
      total: item.total,
      percentage: item.percentage,
    }));
  }, [analysis]);

  if (!sessionId) {
    return null;
  }

  if (isLoading) {
    return <div className="rounded-2xl border border-slate-800 bg-[#121824] p-5 text-sm text-slate-400">Loading category breakdown...</div>;
  }

  if (!data.length) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-700 bg-[#121824] p-6 text-sm text-slate-400">
        Category breakdown will appear once the statement is analyzed.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#121824] p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Breakdown</p>
          <h3 className="text-lg font-semibold text-white">Spending by category</h3>
        </div>

        <div className="flex rounded-lg border border-slate-700 bg-slate-950/60 p-1">
          <button
            type="button"
            onClick={() => setMode('donut')}
            className={['flex items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium transition-colors', mode === 'donut' ? 'bg-blue-500/20 text-blue-200' : 'text-slate-400 hover:text-slate-200'].join(' ')}
          >
            <Donut className="h-3.5 w-3.5" />
            Donut
          </button>
          <button
            type="button"
            onClick={() => setMode('bar')}
            className={['flex items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium transition-colors', mode === 'bar' ? 'bg-blue-500/20 text-blue-200' : 'text-slate-400 hover:text-slate-200'].join(' ')}
          >
            <BarChart3 className="h-3.5 w-3.5" />
            Bars
          </button>
        </div>
      </div>

      {mode === 'donut' ? (
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" innerRadius={65} outerRadius={95} paddingAngle={3}>
                {data.map((entry) => (
                  <Cell key={entry.name} fill={CATEGORY_COLORS[entry.name as keyof typeof CATEGORY_COLORS] ?? '#94a3b8'} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value?: number | string | readonly (number | string)[], name?: string | number) => [
                  `₹${Number(Array.isArray(value) ? value[0] : value ?? 0).toLocaleString('en-IN')}`,
                  String(name ?? 'Amount'),
                ]}
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: 12 }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <XAxis dataKey="name" tick={{ fill: '#cbd5e1', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(value?: number | string | readonly (number | string)[], name?: string | number) => [
                  `₹${Number(Array.isArray(value) ? value[0] : value ?? 0).toLocaleString('en-IN')}`,
                  String(name ?? 'Amount'),
                ]}
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: 12 }}
              />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {data.map((entry) => (
                  <Cell key={entry.name} fill={CATEGORY_COLORS[entry.name as keyof typeof CATEGORY_COLORS] ?? '#94a3b8'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {data.map((entry) => (
          <div key={entry.name} className="flex items-center justify-between rounded-xl border border-slate-700 bg-slate-950/40 px-3 py-2 text-xs text-slate-300">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[entry.name as keyof typeof CATEGORY_COLORS] ?? '#94a3b8' }} />
              <span>{entry.name}</span>
            </div>
            <span className="font-medium text-slate-100">₹{Number(entry.total).toLocaleString('en-IN')}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
