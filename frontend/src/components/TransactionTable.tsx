import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { api } from '../api/client';
import type { Category, Transaction } from '../types';

const categoryColors: Record<Category, string> = {
  Food: 'bg-orange-500/10 text-orange-300 border-orange-500/20',
  Travel: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
  Shopping: 'bg-violet-500/10 text-violet-300 border-violet-500/20',
  Bills: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
  EMI: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
  Subscriptions: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20',
  Salary: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
  Rent: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20',
  Investments: 'bg-sky-500/10 text-sky-300 border-sky-500/20',
  Other: 'bg-slate-500/10 text-slate-300 border-slate-500/20',
};

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);

export const TransactionTable: React.FC<{ sessionId?: string }> = ({ sessionId }) => {
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<'date' | 'amount' | 'category'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [categoryFilter, setCategoryFilter] = useState<'All' | Category>('All');
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['transactions', sessionId, page, categoryFilter, sortBy, sortOrder],
    queryFn: () =>
      api.getTransactions(sessionId as string, {
        page,
        per_page: 10,
        category: categoryFilter === 'All' ? undefined : categoryFilter,
        sort_by: sortBy,
        order: sortOrder,
      }),
    enabled: !!sessionId,
  });

  const filteredRows = useMemo(() => {
    const rows = data?.data ?? [];
    if (!search.trim()) {
      return rows;
    }

    const q = search.trim().toLowerCase();
    return rows.filter((row) => {
      const haystack = `${row.description_clean ?? row.description_raw}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [data, search]);

  const categoryOptions = useMemo(
    () => ['All', 'Food', 'Travel', 'Shopping', 'Bills', 'EMI', 'Subscriptions', 'Salary', 'Rent', 'Investments', 'Other'] as const,
    [],
  );

  const handleSort = (key: 'date' | 'amount' | 'category') => {
    if (sortBy === key) {
      setSortOrder((current) => (current === 'asc' ? 'desc' : 'asc'));
      return;
    }

    setSortBy(key);
    setSortOrder(key === 'amount' ? 'desc' : 'asc');
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#121824] p-5">
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Ledger</p>
          <h3 className="text-lg font-semibold text-white">Transaction history</h3>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <label className="relative block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search description"
              className="w-full rounded-xl border border-slate-700 bg-slate-950/60 py-2 pl-9 pr-3 text-sm text-slate-200 outline-none placeholder:text-slate-500 focus:border-blue-500 sm:w-52"
            />
          </label>

          <select
            value={categoryFilter}
            onChange={(event) => {
              setCategoryFilter(event.target.value as 'All' | Category);
              setPage(1);
            }}
            className="rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
          >
            {categoryOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <div className="h-12 animate-pulse rounded-lg bg-slate-800/80" />
          <div className="h-12 animate-pulse rounded-lg bg-slate-800/80" />
          <div className="h-12 animate-pulse rounded-lg bg-slate-800/80" />
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-800 text-slate-400">
                <tr>
                  <th className="px-3 py-3 font-medium">
                    <button type="button" onClick={() => handleSort('date')} className="inline-flex items-center gap-1 text-left">
                      Date
                      {sortBy === 'date' && <span>{sortOrder === 'asc' ? <ArrowUp className="h-3.5 w-3.5" /> : <ArrowDown className="h-3.5 w-3.5" />}</span>}
                    </button>
                  </th>
                  <th className="px-3 py-3 font-medium">Description</th>
                  <th className="px-3 py-3 font-medium">
                    <button type="button" onClick={() => handleSort('amount')} className="inline-flex items-center gap-1 text-left">
                      Amount
                      {sortBy === 'amount' && <span>{sortOrder === 'asc' ? <ArrowUp className="h-3.5 w-3.5" /> : <ArrowDown className="h-3.5 w-3.5" />}</span>}
                    </button>
                  </th>
                  <th className="px-3 py-3 font-medium">
                    <button type="button" onClick={() => handleSort('category')} className="inline-flex items-center gap-1 text-left">
                      Category
                      {sortBy === 'category' && <span>{sortOrder === 'asc' ? <ArrowUp className="h-3.5 w-3.5" /> : <ArrowDown className="h-3.5 w-3.5" />}</span>}
                    </button>
                  </th>
                  <th className="px-3 py-3 font-medium">Type</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.length ? (
                  filteredRows.map((row: Transaction) => (
                    <tr key={row.id} className="border-b border-slate-800/70 text-slate-200 hover:bg-slate-900/40">
                      <td className="px-3 py-3 whitespace-nowrap text-slate-300">{new Date(row.date).toLocaleDateString('en-IN')}</td>
                      <td className="px-3 py-3">
                        <div className="max-w-sm truncate" title={row.description_raw}>
                          {row.description_clean ?? row.description_raw}
                        </div>
                      </td>
                      <td className={`px-3 py-3 font-medium ${row.amount >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                        {row.amount >= 0 ? '+' : '-'}{formatCurrency(Math.abs(row.amount))}
                      </td>
                      <td className="px-3 py-3">
                        <span className={`inline-flex rounded-full border px-2 py-1 text-[11px] font-medium ${categoryColors[row.category] ?? categoryColors.Other}`}>
                          {row.category}
                        </span>
                      </td>
                      <td className="px-3 py-3">
                        <span className={`inline-flex rounded-full px-2 py-1 text-[11px] font-medium ${row.type === 'credit' ? 'bg-emerald-500/10 text-emerald-300' : 'bg-rose-500/10 text-rose-300'}`}>
                          {row.type}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="px-3 py-10 text-center text-slate-400">
                      No transactions match the current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {data && data.total > 10 && (
            <div className="mt-4 flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={page === 1}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-300 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </button>
              <span className="text-sm text-slate-400">
                Page {page} of {Math.max(1, Math.ceil(data.total / 10))}
              </span>
              <button
                type="button"
                onClick={() => setPage((current) => current + 1)}
                disabled={page >= Math.ceil(data.total / 10)}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-300 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};
