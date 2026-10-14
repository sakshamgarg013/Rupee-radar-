import React, { useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import {
  UploadCloud,
  FileSpreadsheet,
  Cpu,
  Repeat,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  LoaderCircle,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const {
    data: health,
    isLoading: healthLoading,
    isError: healthError,
  } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 30000,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadStatement(file),
    onSuccess: (result) => {
      const sessionId = result.session_id ?? result.id ?? '';
      if (!sessionId) {
        setError('Upload succeeded but no session was returned. Please try again.');
        return;
      }

      navigate(`/analysis/${sessionId}`);
    },
    onError: (uploadError: unknown) => {
      const message =
        uploadError instanceof Error && 'response' in uploadError
          ? (uploadError as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? uploadError.message
          : 'Unable to process the statement right now.';
      setError(message);
    },
  });

  const handleFileSelection = (file?: File | null) => {
    if (!file) {
      return;
    }

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Only CSV files are supported for Phase 2 uploads.');
      return;
    }

    setSelectedFile(file);
    setError(null);
  };

  const handleUpload = () => {
    if (!selectedFile) {
      setError('Please choose a CSV file before uploading.');
      return;
    }

    uploadMutation.mutate(selectedFile);
  };

  return (
    <div className="min-h-screen bg-[#0a0d14] text-slate-100 flex flex-col selection:bg-blue-600 selection:text-white">
      <header className="border-b border-slate-800/80 bg-[#0d121c]/70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <span className="text-xl font-bold text-white tracking-tight">₹</span>
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                RupeeRadar
              </span>
              <span className="ml-2 text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Phase 2 Active
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-400">API Status:</span>
            {healthLoading ? (
              <span className="flex items-center text-amber-400">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping mr-1.5" />
                Connecting...
              </span>
            ) : healthError ? (
              <span className="flex items-center text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-md border border-rose-500/20">
                <AlertCircle className="w-3.5 h-3.5 mr-1" />
                Backend Offline
              </span>
            ) : (
              <span className="flex items-center text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                {health?.app} (v{health?.version})
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 flex flex-col items-center">
        <div className="text-center max-w-3xl space-y-4 mb-12">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-medium mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI-Powered Personal Finance Assistant for Indian Professionals</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Stop Guessing{' '}
            <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-emerald-400 bg-clip-text text-transparent">
              Where Your Money Goes
            </span>
          </h1>

          <p className="text-slate-400 text-base sm:text-lg max-w-2xl mx-auto">
            Transform messy UPI narrations, card charges, and bank statement CSVs into categorized expenses, detected recurring subscriptions, and actionable financial insights.
          </p>
        </div>

        <div
          className={`w-full max-w-2xl bg-gradient-to-b from-[#151d2c] to-[#0f1521] border rounded-2xl p-8 shadow-2xl shadow-black/40 text-center relative overflow-hidden group ${isDragging ? 'border-blue-500/70 ring-2 ring-blue-500/30' : 'border-slate-800'}`}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            const file = event.dataTransfer.files?.[0];
            handleFileSelection(file ?? null);
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={(event) => handleFileSelection(event.target.files?.[0] ?? null)}
          />

          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

          <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mx-auto mb-4 text-blue-400 group-hover:scale-105 transition-transform duration-200">
            <UploadCloud className="w-8 h-8" />
          </div>

          <h3 className="text-lg font-semibold text-white mb-2">Upload Bank Statement</h3>
          <p className="text-slate-400 text-sm mb-6 max-w-md mx-auto">
            Drag & drop your bank statement CSV (HDFC, ICICI, SBI, or generic). Data is processed ephemerally with zero persistent file storage.
          </p>

          {selectedFile ? (
            <div className="mb-5 rounded-xl border border-emerald-500/30 bg-emerald-500/5 px-4 py-3 text-sm text-emerald-100 flex items-center justify-center gap-2">
              <FileSpreadsheet className="h-4 w-4 text-emerald-300" />
              {selectedFile.name}
            </div>
          ) : null}

          {error ? (
            <div className="mb-4 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-100 text-left">
              {error}
            </div>
          ) : null}

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                fileInputRef.current?.click();
              }}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-100 font-medium text-sm transition-colors border border-slate-700/50 cursor-pointer"
            >
              Choose CSV File
            </button>
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                handleUpload();
              }}
              disabled={!selectedFile || uploadMutation.isPending}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-sm transition-all shadow-lg shadow-blue-600/25 flex items-center justify-center space-x-2 cursor-pointer disabled:cursor-not-allowed disabled:opacity-60"
            >
              {uploadMutation.isPending ? (
                <>
                  <LoaderCircle className="w-4 h-4 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <span>Upload & Analyze</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          <div className="mt-6 pt-6 border-t border-slate-800/60 flex items-center justify-center space-x-6 text-xs text-slate-500">
            <span className="flex items-center">
              <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-500" />
              Privacy-First (No PII)
            </span>
            <span className="flex items-center">
              <Cpu className="w-3.5 h-3.5 mr-1 text-blue-400" />
              Groq LLM Powered
            </span>
            <span className="flex items-center">
              <FileSpreadsheet className="w-3.5 h-3.5 mr-1 text-indigo-400" />
              CSV Format
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full mt-16">
          <div className="bg-[#121824] border border-slate-800/80 p-6 rounded-xl space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h4 className="text-base font-semibold text-white">Smart Normalization</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Cleans messy UPI references (e.g. <code>UPI/DR/123456/SWIGGY</code>), extracts merchant names, and standardizes amounts and ISO dates.
            </p>
          </div>

          <div className="bg-[#121824] border border-slate-800/80 p-6 rounded-xl space-y-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Repeat className="w-5 h-5" />
            </div>
            <h4 className="text-base font-semibold text-white">Recurring Detection</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Identifies monthly OTT subscriptions, SIPs, loan EMIs, rent, and utility bills using frequency and tolerance cadence heuristics.
            </p>
          </div>

          <div className="bg-[#121824] border border-slate-800/80 p-6 rounded-xl space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <h4 className="text-base font-semibold text-white">Groq AI Insights</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Generates personalized financial observations that cite exact rupee amounts without sending sensitive account numbers to external APIs.
            </p>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        RupeeRadar Personal Finance Assistant &copy; 2026. Built with FastAPI, SQLite, React, Vite & Groq.
      </footer>
    </div>
  );
};
