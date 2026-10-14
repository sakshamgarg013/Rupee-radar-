import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowDownLeft, ArrowUpRight, PiggyBank, Percent } from 'lucide-react';
import { api } from '../api/client';

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(value);

export const SummaryCards: React.FC<{ sessionId?: string }> = ({ sessionId }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', sessionId],
    queryFn: () => api.getAnalytics(sessionId as string),
    enabled: !!sessionId,
  });

  if (!sessionId) {
    return null;
  }

  const metrics = data?.metrics;

  const cards = [
    {
      title: 'Total Income',
      value: metrics ? formatCurrency(metrics.total_income) : '₹0',
      helper: metrics && metrics.total_income > 0 ? 'Income recorded' : 'No income found',
      tone: 'emerald',
      Icon: ArrowUpRight,
    },
    {
      title: 'Total Spend',
      value: metrics ? formatCurrency(metrics.total_spend) : '₹0',
      helper: metrics && metrics.total_income > 0 ? `${Math.round((metrics.total_spend / Math.max(metrics.total_income, 1)) * 100)}% of income` : 'Expense total',
      tone: 'rose',
      Icon: ArrowDownLeft,
    },
    {
      title: 'Savings',
      value: metrics ? formatCurrency(metrics.savings) : '₹0',
      helper: metrics && metrics.savings >= 0 ? 'Positive cash flow' : 'Negative cash flow',
      tone: metrics && metrics.savings >= 0 ? 'blue' : 'amber',
      Icon: PiggyBank,
    },
    {
      title: 'Savings Rate',
      value: metrics ? `${metrics.savings_rate.toFixed(1)}%` : '0.0%',
      helper: 'Savings as % of income',
      tone: 'indigo',
      Icon: Percent,
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map(({ title, value, helper, tone, Icon }) => (
        <div key={title} className="rounded-2xl border border-slate-800 bg-[#121824] p-5 shadow-lg shadow-slate-950/20 transition-all duration-200 hover:-translate-y-0.5 hover:border-slate-700">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wide">{title}</span>
            <div
              className={[
                'flex h-9 w-9 items-center justify-center rounded-xl border',
                tone === 'emerald' && 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
                tone === 'rose' && 'border-rose-500/30 bg-rose-500/10 text-rose-300',
                tone === 'blue' && 'border-blue-500/30 bg-blue-500/10 text-blue-300',
                tone === 'amber' && 'border-amber-500/30 bg-amber-500/10 text-amber-300',
                tone === 'indigo' && 'border-indigo-500/30 bg-indigo-500/10 text-indigo-300',
              ].join(' ')}
            >
              <Icon className="h-4 w-4" />
            </div>
          </div>

          <div className="mt-5 text-2xl font-bold text-white">
            {isLoading ? 'Loading...' : value}
          </div>
          <div className="mt-2 text-xs text-slate-400">{helper}</div>
        </div>
      ))}
    </div>
  );
};
