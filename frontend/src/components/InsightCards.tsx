import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, PiggyBank, TrendingUp, Sparkles } from 'lucide-react';
import { api } from '../api/client';

const iconMap = {
  spend: TrendingUp,
  savings: PiggyBank,
  default: Sparkles,
};

export const InsightCards: React.FC<{ sessionId?: string }> = ({ sessionId }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['insights', sessionId],
    queryFn: () => api.getInsights(sessionId as string),
    enabled: !!sessionId,
  });

  if (!sessionId) {
    return null;
  }

  const items = data?.insights ?? [];

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#121824] p-5">
      <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
        <Sparkles className="h-4 w-4 text-emerald-400" />
        <span>Personalized insights</span>
      </div>

      {isLoading ? (
        <div className="animate-pulse space-y-3">
          <div className="h-20 rounded-xl bg-slate-800/80" />
          <div className="h-20 rounded-xl bg-slate-800/80" />
          <div className="h-20 rounded-xl bg-slate-800/80" />
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-3">
          {items.length ? (
            items.slice(0, 3).map((insight: string, index: number) => {
              const Icon = iconMap[index % 2 === 0 ? 'spend' : 'savings'];
              return (
                <div key={`${insight}-${index}`} className="rounded-xl border border-slate-700 bg-slate-950/50 p-4 text-sm text-slate-200">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500/20 to-emerald-500/20 text-blue-200">
                      <Icon className="h-4 w-4" />
                    </span>
                    <ArrowRight className="h-4 w-4 text-slate-500" />
                  </div>
                  <p className="leading-relaxed text-slate-300">{insight}</p>
                </div>
              );
            })
          ) : (
            <div className="rounded-xl border border-slate-700 bg-slate-950/40 p-4 text-sm text-slate-400">
              No insights available yet for this statement.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
