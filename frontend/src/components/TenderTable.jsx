import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
} from '@tanstack/react-table';
import {
  ArrowUpDown,
  ExternalLink,
  FileText,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  ShieldCheck,
  Building,
  Calendar,
  Layers,
} from 'lucide-react';

export default function TenderTable({
  data,
  total,
  page,
  pageSize,
  totalPages,
  onPageChange,
  onPageSizeChange,
  sortBy,
  sortOrder,
  onSortChange,
  onSelectTender,
  isLoading,
}) {
  const columns = useMemo(
    () => [
      {
        accessorKey: 'title',
        header: 'Tender Name',
        cell: (info) => {
          const tender = info.row.original;
          const kws = tender.matched_keywords || [];
          return (
            <div className="max-w-md">
              <button
                type="button"
                onClick={() => onSelectTender(tender)}
                className="text-left font-semibold text-slate-900 hover:text-blue-600 transition-colors line-clamp-2 cursor-pointer leading-snug"
                title={tender.title}
              >
                {tender.title}
              </button>
              {tender.is_it_related && kws.length > 0 && (
                <div className="flex flex-wrap items-center gap-1 mt-1.5">
                  {kws.slice(0, 3).map((kw, i) => (
                    <span
                      key={i}
                      className="text-[10px] bg-slate-100 text-slate-700 font-medium px-1.5 py-0.5 rounded border border-slate-200"
                    >
                      {kw}
                    </span>
                  ))}
                  {kws.length > 3 && (
                    <span className="text-[10px] text-slate-500 font-medium">
                      +{kws.length - 3} more
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: 'organisation',
        header: 'Organisation',
        cell: (info) => {
          const val = info.getValue();
          return (
            <div className="text-xs text-slate-700 max-w-[180px] truncate flex items-center gap-1.5" title={val || 'Govt of Kerala'}>
              <Building className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span className="truncate">{val || 'Govt of Kerala'}</span>
            </div>
          );
        },
      },
      {
        accessorKey: 'source_name',
        header: 'Source',
        cell: (info) => {
          const src = info.getValue();
          let badgeColor = 'bg-slate-100 text-slate-700 border-slate-200';
          if (src?.includes('e-Procurement')) {
            badgeColor = 'bg-blue-50 text-blue-700 border-blue-200';
          } else if (src?.includes('KSITM')) {
            badgeColor = 'bg-emerald-50 text-emerald-700 border-emerald-200';
          } else if (src?.includes('C-DIT')) {
            badgeColor = 'bg-purple-50 text-purple-700 border-purple-200';
          } else if (src?.includes('Industries')) {
            badgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
          } else if (src?.includes('K-DISC')) {
            badgeColor = 'bg-teal-50 text-teal-700 border-teal-200';
          }

          return (
            <span
              className={`inline-block text-[11px] font-medium px-2 py-0.5 rounded-full border ${badgeColor} max-w-[140px] truncate`}
              title={src}
            >
              {src}
            </span>
          );
        },
      },
      {
        accessorKey: 'published_date',
        header: 'Published',
        cell: (info) => {
          const val = info.getValue();
          return (
            <div className="text-xs text-slate-600 whitespace-nowrap flex items-center gap-1">
              <Calendar className="w-3 h-3 text-slate-400" />
              {val || '—'}
            </div>
          );
        },
      },
      {
        accessorKey: 'closing_date',
        header: 'Closing Date',
        cell: (info) => {
          const val = info.getValue();
          return (
            <div className="text-xs font-medium text-slate-800 whitespace-nowrap flex items-center gap-1">
              <Calendar className="w-3 h-3 text-rose-400" />
              <span className={val ? 'text-rose-700' : 'text-slate-400'}>{val || '—'}</span>
            </div>
          );
        },
      },
      {
        accessorKey: 'category',
        header: 'Category',
        cell: (info) => {
          const cat = info.getValue();
          return (
            <span className="text-xs text-slate-600 max-w-[120px] truncate block" title={cat || 'General'}>
              {cat || 'General'}
            </span>
          );
        },
      },
      {
        accessorKey: 'relevance_score',
        header: 'IT Score',
        cell: (info) => {
          const tender = info.row.original;
          const score = tender.relevance_score || 0;
          const pct = Math.round(score * 100);

          if (!tender.is_it_related) {
            return (
              <span className="text-[11px] text-slate-400 font-normal">
                0%
              </span>
            );
          }

          let scoreBadge = 'bg-emerald-50 text-emerald-700 border-emerald-200';
          if (score < 0.4) {
            scoreBadge = 'bg-teal-50 text-teal-700 border-teal-200';
          }

          return (
            <div className="flex items-center gap-1.5">
              <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-md border ${scoreBadge}`}>
                <ShieldCheck className="w-3 h-3 text-emerald-600" />
                {pct}%
              </span>
            </div>
          );
        },
      },
      {
        id: 'tender_link',
        header: 'Tender',
        cell: (info) => {
          const url = info.row.original.tender_url;
          if (!url) return <span className="text-slate-300 text-xs">—</span>;
          return (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center justify-center p-1.5 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
              title="Open External Tender Page"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          );
        },
      },
      {
        id: 'document_link',
        header: 'PDF',
        cell: (info) => {
          const docUrl = info.row.original.document_url;
          if (!docUrl) return <span className="text-slate-300 text-xs">—</span>;
          return (
            <a
              href={docUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center justify-center p-1.5 text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-md transition-colors"
              title="Open PDF Document"
            >
              <FileText className="w-4 h-4" />
            </a>
          );
        },
      },
    ],
    [onSelectTender]
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount: totalPages,
  });

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                {headerGroup.headers.map((header) => {
                  const canSort = ['title', 'relevance_score', 'closing_date', 'published_date'].includes(header.id);
                  return (
                    <th
                      key={header.id}
                      className="px-4 py-3 whitespace-nowrap"
                    >
                      {canSort ? (
                        <button
                          type="button"
                          onClick={() => onSortChange(header.id)}
                          className="flex items-center gap-1.5 hover:text-slate-900 transition-colors cursor-pointer group"
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          <ArrowUpDown className={`w-3.5 h-3.5 ${sortBy === header.id ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-600'}`} />
                        </button>
                      ) : (
                        flexRender(header.column.columnDef.header, header.getContext())
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-slate-100 text-sm">
            {isLoading ? (
              // Loading Skeleton
              Array.from({ length: 6 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td className="px-4 py-4">
                    <div className="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-slate-100 rounded w-1/2"></div>
                  </td>
                  <td className="px-4 py-4"><div className="h-4 bg-slate-100 rounded w-24"></div></td>
                  <td className="px-4 py-4"><div className="h-4 bg-slate-100 rounded w-20"></div></td>
                  <td className="px-4 py-4"><div className="h-4 bg-slate-100 rounded w-16"></div></td>
                  <td className="px-4 py-4"><div className="h-4 bg-slate-100 rounded w-16"></div></td>
                  <td className="px-4 py-4"><div className="h-4 bg-slate-100 rounded w-20"></div></td>
                  <td className="px-4 py-4"><div className="h-4 bg-slate-100 rounded w-12"></div></td>
                  <td className="px-4 py-4"><div className="h-6 w-6 bg-slate-100 rounded"></div></td>
                  <td className="px-4 py-4"><div className="h-6 w-6 bg-slate-100 rounded"></div></td>
                </tr>
              ))
            ) : table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => onSelectTender(row.original)}
                  className="hover:bg-blue-50/40 transition-colors cursor-pointer"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3.5 align-middle">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              // Empty State
              <tr>
                <td colSpan={columns.length} className="px-6 py-14 text-center">
                  <div className="max-w-sm mx-auto space-y-2">
                    <div className="p-3 bg-slate-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto text-slate-500">
                      <Layers className="w-6 h-6" />
                    </div>
                    <h4 className="text-base font-semibold text-slate-800">
                      No tenders match your filter
                    </h4>
                    <p className="text-xs text-slate-500">
                      Try clearing search keywords, switching to "All Tenders", or resetting the portal source filter.
                    </p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* TanStack Pagination Footer */}
      <div className="px-4 py-3.5 border-t border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="bg-white border border-slate-200 rounded-md px-2 py-1 text-slate-700 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value={10}>10</option>
            <option value={15}>15</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
          <span className="text-slate-400">|</span>
          <span>
            Total: <strong className="text-slate-800">{total}</strong> tenders
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="mr-2">
            Page <strong className="text-slate-900">{page}</strong> of{' '}
            <strong className="text-slate-900">{totalPages || 1}</strong>
          </span>

          <button
            onClick={() => onPageChange(1)}
            disabled={page <= 1 || isLoading}
            className="p-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
            title="First page"
          >
            <ChevronsLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1 || isLoading}
            className="p-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
            title="Previous page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages || isLoading}
            className="p-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
            title="Next page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => onPageChange(totalPages)}
            disabled={page >= totalPages || isLoading}
            className="p-1.5 rounded-md border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
            title="Last page"
          >
            <ChevronsRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
