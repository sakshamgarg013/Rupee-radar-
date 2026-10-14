import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles } from 'lucide-react';
import { ProcessingStatus } from '../components/ProcessingStatus';
import { SummaryCards } from '../components/SummaryCards';
import { CategoryChart } from '../components/CategoryChart';
import { TransactionTable } from '../components/TransactionTable';
import { InsightCards } from '../components/InsightCards';
import { api } from '../api/client';
import { useQuery } from '@tanstack/react-query';

export const AnalysisPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const { data: session } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => api.getSession(sessionId as string),
    enabled: !!sessionId,
  });

  const analysisReady = session?.status === 'ready';

  return (
    <div className="min-h-screen bg-[#0a0d14] text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 bg-[#0d121c]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex items-center justify-center cursor-pointer"
            title="Back to Upload"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-lg font-bold text-white leading-tight">Financial Analysis Dashboard</h1>
            <p className="text-xs text-slate-400">
              Session ID: <code className="text-blue-400 font-mono text-[11px]">{sessionId || 'unknown'}</code>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-xs px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
            {session?.status ?? 'pending'}
          </span>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-8">
        {sessionId ? (
          <>
            <ProcessingStatus sessionId={sessionId} />

            {analysisReady && (
              <>
                <SummaryCards sessionId={sessionId} />

                <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
                  <CategoryChart sessionId={sessionId} />
                  <InsightCards sessionId={sessionId} />
                </div>

                <TransactionTable sessionId={sessionId} />
              </>
            )}
          </>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-700 bg-[#121824] p-8 text-center text-slate-400">
            No session selected. Return to the landing page to upload a statement.
          </div>
        )}

        {!analysisReady && sessionId && (
          <div className="rounded-2xl border border-slate-800 bg-[#121824] p-6 text-sm text-slate-300">
            <div className="flex items-center gap-2 text-white">
              <Sparkles className="h-4 w-4 text-emerald-400" />
              Analysis will appear automatically once the statement has finished processing.
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
