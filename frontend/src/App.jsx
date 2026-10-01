import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import {
  Play,
  Loader2,
  RefreshCw,
  Terminal,
  Activity,
  ShieldCheck,
  CheckCircle2,
  Info,
} from 'lucide-react';

import StatsCards from './components/StatsCards';
import ScraperStatusBanner from './components/ScraperStatusBanner';
import FilterBar from './components/FilterBar';
import TenderTable from './components/TenderTable';
import TenderDetailModal from './components/TenderDetailModal';

export default function App() {
  // Stats & Sources
  const [stats, setStats] = useState(null);
  const [sourcesList, setSourcesList] = useState([]);
  const [organisationsList, setOrganisationsList] = useState([]);
  const [categoriesList, setCategoriesList] = useState([]);

  // Filters State
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [source, setSource] = useState('All Sources');
  const [organisation, setOrganisation] = useState('All Organisations');
  const [category, setCategory] = useState('All Categories');
  const [itOnly, setItOnly] = useState(true); // Default to IT-only per requirement

  // Pagination & Sorting State
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const [sortBy, setSortBy] = useState('scraped_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Table Data State
  const [tenders, setTenders] = useState([]);
  const [totalTenders, setTotalTenders] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isTableLoading, setIsTableLoading] = useState(false);

  // Scraper State
  const [scraperStatus, setScraperStatus] = useState(null);
  const [isScraping, setIsScraping] = useState(false);

  // Selected Tender for Modal
  const [selectedTender, setSelectedTender] = useState(null);

  // Polling ref
  const pollIntervalRef = useRef(null);

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // Reset to first page on search change
    }, 300);
    return () => clearTimeout(handler);
  }, [search]);

  // Fetch Dashboard Stats
  const fetchStats = async () => {
    try {
      const res = await axios.get('/api/stats');
      setStats(res.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  // Fetch Available Filter Options
  const fetchSources = async () => {
    try {
      const res = await axios.get('/api/sources');
      setSourcesList(res.data.sources || []);
      setOrganisationsList(res.data.organisations || []);
      setCategoriesList(res.data.categories || []);
    } catch (err) {
      console.error('Error fetching sources:', err);
    }
  };

  // Fetch Tenders with active filters
  const fetchTenders = useCallback(async () => {
    setIsTableLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        it_only: itOnly,
        sort_by: sortBy,
        sort_order: sortOrder,
      };

      if (debouncedSearch.trim()) params.search = debouncedSearch.trim();
      if (source && source !== 'All Sources') params.source = source;
      if (organisation && organisation !== 'All Organisations') params.organisation = organisation;
      if (category && category !== 'All Categories') params.category = category;

      const res = await axios.get('/api/tenders', { params });
      setTenders(res.data.items || []);
      setTotalTenders(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      console.error('Error fetching tenders:', err);
    } finally {
      setIsTableLoading(false);
    }
  }, [page, pageSize, itOnly, sortBy, sortOrder, debouncedSearch, source, organisation, category]);

  // Check Scraper Status
  const checkScraperStatus = async () => {
    try {
      const res = await axios.get('/api/scrape/status');
      setScraperStatus(res.data);
      const running = res.data.status === 'running';
      setIsScraping(running);

      if (!running && pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
        // Refresh data once scraping finishes
        fetchStats();
        fetchSources();
        fetchTenders();
      }
    } catch (err) {
      console.error('Error checking scraper status:', err);
    }
  };

  // Trigger Scraper Run
  const handleRunScraper = async () => {
    if (isScraping) return;
    try {
      setIsScraping(true);
      const res = await axios.post('/api/scrape');
      setScraperStatus(res.data);

      // Start polling status every 2 seconds
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = setInterval(checkScraperStatus, 2000);
    } catch (err) {
      console.error('Error starting scraper:', err);
      setIsScraping(false);
    }
  };

  // Reset Filters
  const handleResetFilters = () => {
    setSearch('');
    setDebouncedSearch('');
    setSource('All Sources');
    setOrganisation('All Organisations');
    setCategory('All Categories');
    setItOnly(true);
    setPage(1);
  };

  // Sort change handler
  const handleSortChange = (colKey) => {
    if (sortBy === colKey) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(colKey);
      setSortOrder('desc');
    }
  };

  // Initial load
  useEffect(() => {
    fetchStats();
    fetchSources();
    checkScraperStatus();
  }, []);

  // Fetch tenders on filter/pagination change
  useEffect(() => {
    fetchTenders();
  }, [fetchTenders]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-16">
      {/* Top Navigation / Header */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 via-indigo-600 to-emerald-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
                  Kerala IT Tender Monitor
                </h1>
                <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  Active Scanner
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                Kerala Government Public IT & Software Procurement Intelligence
              </p>
            </div>
          </div>

          {/* Action Button: Run Scraper */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleRunScraper}
              disabled={isScraping}
              className={`relative flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-xs sm:text-sm text-white shadow-md transition-all cursor-pointer ${
                isScraping
                  ? 'bg-blue-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 active:scale-98 shadow-blue-500/20 hover:shadow-lg'
              }`}
            >
              {isScraping ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Scraping Sources...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Run Scraper</span>
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {/* KPI Summary Cards */}
        <StatsCards stats={stats} isScraping={isScraping} />

        {/* Real-time Scraper Progress Banner */}
        <ScraperStatusBanner status={scraperStatus} />

        {/* Search & Filters */}
        <FilterBar
          search={search}
          setSearch={setSearch}
          source={source}
          setSource={(s) => {
            setSource(s);
            setPage(1);
          }}
          organisation={organisation}
          setOrganisation={(org) => {
            setOrganisation(org);
            setPage(1);
          }}
          category={category}
          setCategory={(cat) => {
            setCategory(cat);
            setPage(1);
          }}
          itOnly={itOnly}
          setItOnly={(val) => {
            setItOnly(val);
            setPage(1);
          }}
          sourcesList={sourcesList}
          organisationsList={organisationsList}
          categoriesList={categoriesList}
          onReset={handleResetFilters}
          totalResults={totalTenders}
        />

        {/* TanStack Table */}
        <TenderTable
          data={tenders}
          total={totalTenders}
          page={page}
          pageSize={pageSize}
          totalPages={totalPages}
          onPageChange={setPage}
          onPageSizeChange={(newSize) => {
            setPageSize(newSize);
            setPage(1);
          }}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSortChange={handleSortChange}
          onSelectTender={setSelectedTender}
          isLoading={isTableLoading}
        />
      </main>

      {/* Tender Detail Modal */}
      {selectedTender && (
        <TenderDetailModal
          tender={selectedTender}
          onClose={() => setSelectedTender(null)}
        />
      )}
    </div>
  );
}
