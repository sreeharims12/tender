import React, { useEffect } from 'react';
import { X, ExternalLink, FileText, Globe, Building2, Calendar, Tag, ShieldCheck, Hash, MapPin, DollarSign } from 'lucide-react';

export default function TenderDetailModal({ tender, onClose }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!tender) return null;

  const scorePct = Math.round((tender.relevance_score || 0) * 100);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-3xl max-h-[90vh] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 sm:p-6 border-b border-slate-100 flex items-start justify-between gap-4 bg-slate-50/50">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700">
                {tender.source_name}
              </span>
              {tender.is_it_related ? (
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  IT-Related ({scorePct}% match)
                </span>
              ) : (
                <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600">
                  General Tender
                </span>
              )}
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-slate-900 leading-snug">
              {tender.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-full transition-colors cursor-pointer shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-6 text-sm">
          {/* IT Relevance Score Bar */}
          {tender.is_it_related && (
            <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200/80">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-emerald-900 uppercase tracking-wider">
                  IT Relevance Score: {tender.relevance_score?.toFixed(2)} ({scorePct}%)
                </span>
                <span className="text-xs text-emerald-700 font-medium">
                  Keyword-Based Classifier
                </span>
              </div>
              <div className="w-full bg-emerald-200 rounded-full h-2 mb-3">
                <div
                  className="bg-emerald-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.max(10, scorePct))}%` }}
                ></div>
              </div>
              {tender.matched_keywords && tender.matched_keywords.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-xs font-medium text-emerald-800">Matched IT Keywords:</span>
                  {tender.matched_keywords.map((kw, i) => (
                    <span
                      key={i}
                      className="text-xs bg-emerald-100/90 text-emerald-800 font-medium px-2 py-0.5 rounded-md border border-emerald-200"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Details Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
              <Building2 className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
              <div>
                <span className="block text-xs font-medium text-slate-500">Organisation</span>
                <span className="text-sm font-semibold text-slate-800">
                  {tender.organisation || 'Government of Kerala'}
                </span>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
              <Hash className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
              <div>
                <span className="block text-xs font-medium text-slate-500">Tender ID / Ref</span>
                <span className="text-sm font-semibold text-slate-800 font-mono">
                  {tender.tender_id || tender.tender_reference || 'N/A'}
                </span>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
              <Tag className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
              <div>
                <span className="block text-xs font-medium text-slate-500">Category & Type</span>
                <span className="text-sm font-semibold text-slate-800">
                  {tender.category || 'General'} ({tender.tender_type || 'Open'})
                </span>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
              <MapPin className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
              <div>
                <span className="block text-xs font-medium text-slate-500">Location</span>
                <span className="text-sm font-semibold text-slate-800">
                  {tender.location || 'Kerala'}
                </span>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
              <Calendar className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
              <div>
                <span className="block text-xs font-medium text-slate-500">Published Date</span>
                <span className="text-sm font-semibold text-slate-800">
                  {tender.published_date || 'N/A'}
                </span>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
              <Calendar className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
              <div>
                <span className="block text-xs font-medium text-slate-500">Closing Date</span>
                <span className="text-sm font-semibold text-rose-700">
                  {tender.closing_date || 'N/A'}
                </span>
              </div>
            </div>

            {tender.estimated_value && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100 sm:col-span-2">
                <DollarSign className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <span className="block text-xs font-medium text-slate-500">Estimated Value</span>
                  <span className="text-sm font-semibold text-slate-800">
                    {tender.estimated_value}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Description */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              Tender Description / Work Particulars
            </h3>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 text-xs sm:text-sm leading-relaxed whitespace-pre-wrap">
              {tender.description || 'No detailed description provided in initial portal notice.'}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 sm:p-5 border-t border-slate-100 bg-slate-50 flex flex-wrap items-center justify-end gap-2.5">
          {tender.source_url && (
            <a
              href={tender.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-2xs"
            >
              <Globe className="w-3.5 h-3.5 text-slate-500" />
              Open Source Portal
            </a>
          )}

          {tender.document_url && (
            <a
              href={tender.document_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors"
            >
              <FileText className="w-3.5 h-3.5 text-indigo-600" />
              Open Document / PDF
            </a>
          )}

          {tender.tender_url && (
            <a
              href={tender.tender_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors shadow-xs"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Open Tender Link
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
