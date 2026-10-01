import React from 'react';
import { Layers, Cpu, Sparkles, Clock } from 'lucide-react';

export default function StatsCards({ stats, isScraping }) {
  const cards = [
    {
      title: 'Total Tenders',
      value: stats?.total_tenders ?? 0,
      subtext: 'Across 6 Kerala Govt Sources',
      icon: Layers,
      color: 'from-blue-600 to-indigo-600',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600',
      borderColor: 'border-blue-100',
    },
    {
      title: 'IT Tenders',
      value: stats?.it_tenders ?? 0,
      subtext: 'Classified software & tech',
      icon: Cpu,
      color: 'from-emerald-600 to-teal-600',
      bgColor: 'bg-emerald-50',
      textColor: 'text-emerald-600',
      borderColor: 'border-emerald-100',
      highlight: true,
    },
    {
      title: 'New Tenders',
      value: stats?.new_tenders ?? 0,
      subtext: 'Added in recent cycle',
      icon: Sparkles,
      color: 'from-amber-600 to-orange-600',
      bgColor: 'bg-amber-50',
      textColor: 'text-amber-600',
      borderColor: 'border-amber-100',
    },
    {
      title: 'Last Scrape',
      value: stats?.last_scrape || 'Not yet run',
      subtext: isScraping ? 'Scraping in progress...' : 'Automatic & on-demand sync',
      icon: Clock,
      color: 'from-purple-600 to-indigo-600',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-600',
      borderColor: 'border-purple-100',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`relative overflow-hidden bg-white border ${card.borderColor} rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between`}
          >
            {card.highlight && (
              <div className="absolute top-0 right-0 w-16 h-16 pointer-events-none overflow-hidden">
                <div className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-[10px] font-bold py-1 px-4 transform rotate-45 translate-x-3 -translate-y-1 shadow-xs text-center">
                  IT
                </div>
              </div>
            )}
            
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                {card.title}
              </span>
              <div className={`p-2.5 rounded-lg ${card.bgColor} ${card.textColor}`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>

            <div>
              <div className="text-2xl lg:text-3xl font-bold tracking-tight text-slate-900">
                {card.value}
              </div>
              <p className="text-xs text-slate-500 mt-1 font-medium">
                {card.subtext}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
