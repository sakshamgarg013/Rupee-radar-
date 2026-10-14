import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, CircleDashed, LoaderCircle, AlertTriangle } from 'lucide-react';
import { api } from '../api/client';

const phaseSteps = [
  { key: 'pending', label: 'Uploading' },
  { key: 'parsing', label: 'Parsing' },
  { key: 'processing', label: 'Categorizing' },
  { key: 'ready', label: 'Ready' },
] as const;

export const ProcessingStatus: React.FC<{ sessionId?: string }> = ({ sessionId }) => {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['session-status', sessionId],
    queryFn: () => api.getSession(sessionId as string),
    enabled: !!sessionId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && status !== 'ready' && status !== 'failed' ? 2000 : false;
    },
  });

  const status = data?.status ?? 'pending';
  const currentIndex = phaseSteps.findIndex((step) => step.key === status);
  const activeIndex = currentIndex >= 0 ? currentIndex : 0;

  if (!sessionId) {
    return null;
  }

  if (isError || status === 'failed') {
    return (
      <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-4 text-sm text-rose-200">
        <div className="flex items-center gap-2 font-medium">
          <AlertTriangle className="h-4 w-4" />
          Processing failed
        </div>
        <p className="mt-2 text-rose-100/80">{data?.error_message ?? 'The statement could not be processed.'}</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#121824] p-4">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Processing</p>
          <h2 className="mt-1 text-lg font-semibold text-white">Statement analysis</h2>
        </div>
        {isLoading ? <LoaderCircle className="h-5 w-5 animate-spin text-blue-400" /> : <CheckCircle2 className="h-5 w-5 text-emerald-400" />}
      </div>

      <div className="grid gap-3 sm:grid-cols-4">
        {phaseSteps.map((step, index) => {
          const isDone = index < activeIndex || status === 'ready';
          const isCurrent = index === activeIndex && status !== 'ready';
          const Icon = isDone ? CheckCircle2 : CircleDashed;

          return (
            <div
              key={step.key}
              className={[
                'rounded-xl border p-3 transition-all',
                isCurrent ? 'border-blue-500/40 bg-blue-500/10 text-blue-100' : isDone ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100' : 'border-slate-700 bg-slate-900/60 text-slate-400',
              ].join(' ')}
            >
              <div className="flex items-center gap-2">
                <Icon className={['h-4 w-4', isCurrent && 'animate-pulse'].join(' ')} />
                <span className="text-sm font-medium">{step.label}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
