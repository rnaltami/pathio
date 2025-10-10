'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Job {
  title: string;
  company: string;
  location: string;
  type: string;
  description: string;
  requirements: string[];
  match_score: number;
  source: string;
  url: string;
}

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [filter, setFilter] = useState<'all' | 'remote' | 'fulltime' | 'contract'>('all');
  const [locationFilter, setLocationFilter] = useState('');
  const [expandedJobIndex, setExpandedJobIndex] = useState<number | null>(null);
  const router = useRouter();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setSearched(true);

    try {
      const response = await fetch(
        'https://pathio-c9yz.onrender.com/search-jobs',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            job_title: searchQuery,
          }),
        }
      );
      const data = await response.json();
      const jobsArray = Array.isArray(data) ? data : (data.jobs || []);
      setJobs(jobsArray);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-white">
      <div className="max-w-[680px] mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-12">
          <a href="/">
            <h1 className="text-3xl font-normal text-[#303030] tracking-tight cursor-pointer hover:opacity-70 transition-opacity">
              pathio
            </h1>
          </a>
        </header>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for a job... writer, data scientist, marketing manager"
              className="w-full px-4 py-3 text-[0.95rem] border border-[#E0E0E0] rounded-lg focus:outline-none focus:border-[#E0E0E0] transition-none"
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 text-sm border border-[#202020] rounded-md hover:opacity-70 transition-opacity bg-transparent"
            >
              Search
            </button>
          </div>
        </form>

        {/* Alternative Actions - Hide when results are shown */}
        {!searched && (
          <div className="space-y-3 text-[0.9rem] text-[#707070]">
            <a
              href="/chat"
              className="block hover:opacity-70 transition-opacity"
            >
              I need career guidance first →
            </a>
            <a
              href="/apply"
              className="block hover:opacity-70 transition-opacity"
            >
              I already have a job listing I want to apply to. Help me get it →
            </a>
          </div>
        )}

        {/* Job Results - Show on same page */}
        {searched && (
          <div className="mt-8">
            {loading && (
              <div className="text-[0.9rem] text-[#707070]">Searching...</div>
            )}

            {!loading && jobs.length > 0 && (
              <>
                <div className="mb-4 text-[0.9rem] text-[#707070]">
                  {(() => {
                    const filtered = jobs.filter(job => {
                      if (filter === 'remote') {
                        const searchText = `${job.title} ${job.location} ${job.type} ${job.description}`.toLowerCase();
                        return searchText.includes('remote');
                      }
                      if (filter === 'fulltime') {
                        const searchText = `${job.type} ${job.title}`.toLowerCase();
                        return searchText.includes('full') || searchText.includes('full-time');
                      }
                      if (filter === 'contract') {
                        const searchText = `${job.type} ${job.title}`.toLowerCase();
                        return searchText.includes('contract') || searchText.includes('contractor');
                      }
                      if (locationFilter) {
                        return job.location.toLowerCase().includes(locationFilter.toLowerCase());
                      }
                      return true;
                    });
                    return `${filtered.length} ${searchQuery} jobs found`;
                  })()}
                </div>

                {/* Filter Options - Clean inline style */}
                <div className="mb-6 pb-4 border-b border-[#E0E0E0]">
                  <div className="flex flex-wrap gap-3 mb-3 text-[0.85rem]">
                    <button
                      onClick={() => { setFilter('all'); setLocationFilter(''); }}
                      className={`px-3 py-1 rounded-full transition-all ${
                        filter === 'all' && !locationFilter
                          ? 'bg-[#202020] text-white'
                          : 'bg-[#F5F5F5] text-[#707070] hover:bg-[#E0E0E0]'
                      }`}
                    >
                      All
                    </button>
                    <button
                      onClick={() => { setFilter('remote'); setLocationFilter(''); }}
                      className={`px-3 py-1 rounded-full transition-all ${
                        filter === 'remote'
                          ? 'bg-[#202020] text-white'
                          : 'bg-[#F5F5F5] text-[#707070] hover:bg-[#E0E0E0]'
                      }`}
                    >
                      Remote
                    </button>
                    <button
                      onClick={() => { setFilter('fulltime'); setLocationFilter(''); }}
                      className={`px-3 py-1 rounded-full transition-all ${
                        filter === 'fulltime'
                          ? 'bg-[#202020] text-white'
                          : 'bg-[#F5F5F5] text-[#707070] hover:bg-[#E0E0E0]'
                      }`}
                    >
                      Full-time
                    </button>
                    <button
                      onClick={() => { setFilter('contract'); setLocationFilter(''); }}
                      className={`px-3 py-1 rounded-full transition-all ${
                        filter === 'contract'
                          ? 'bg-[#202020] text-white'
                          : 'bg-[#F5F5F5] text-[#707070] hover:bg-[#E0E0E0]'
                      }`}
                    >
                      Contract
                    </button>
                  </div>
                  
                  {/* Location filter */}
                  <input
                    type="text"
                    value={locationFilter}
                    onChange={(e) => { setLocationFilter(e.target.value); setFilter('all'); }}
                    placeholder="Filter by location..."
                    className="w-full px-3 py-2 text-[0.85rem] border border-[#E0E0E0] rounded-lg focus:outline-none focus:border-[#E0E0E0]"
                  />
                </div>

                {/* Job listings - with filtering */}
                <div>
                  {jobs
                    .filter(job => {
                      if (filter === 'remote') {
                        const searchText = `${job.title} ${job.location} ${job.type} ${job.description}`.toLowerCase();
                        return searchText.includes('remote');
                      }
                      if (filter === 'fulltime') {
                        const searchText = `${job.type} ${job.title}`.toLowerCase();
                        return searchText.includes('full') || searchText.includes('full-time');
                      }
                      if (filter === 'contract') {
                        const searchText = `${job.type} ${job.title}`.toLowerCase();
                        return searchText.includes('contract') || searchText.includes('contractor');
                      }
                      if (locationFilter) {
                        return job.location.toLowerCase().includes(locationFilter.toLowerCase());
                      }
                      return true;
                    })
                    .map((job, idx) => {
                      const isExpanded = expandedJobIndex === idx;
                      return (
                        <div
                          key={idx}
                          className="border-t border-[#E0E0E0]"
                        >
                          {/* Clickable job summary */}
                          <div
                            className="py-4 cursor-pointer hover:opacity-70 transition-opacity"
                            onClick={() => setExpandedJobIndex(isExpanded ? null : idx)}
                          >
                            {/* Job title - BLUE AND LEFT ALIGNED */}
                            <div className="text-[0.95rem] font-medium text-[#2563eb] mb-2 text-left">
                              {job.title} {isExpanded ? '▼' : '▶'}
                            </div>
                            {/* Company info - GREY AND LEFT ALIGNED */}
                            <div className="text-[0.85rem] text-[#707070] text-left">
                              {job.company} • {job.location} • {job.type}
                            </div>
                          </div>

                          {/* Expanded job details */}
                          {isExpanded && (
                            <div className="pb-6 px-4 bg-[#FAFAFA] rounded-lg mb-4">
                              {/* Description */}
                              <div className="mb-6">
                                <h3 className="text-[0.95rem] font-medium text-[#202020] mb-3">Description</h3>
                                <p className="text-[0.85rem] text-[#303030] leading-relaxed whitespace-pre-wrap">
                                  {job.description}
                                </p>
                              </div>

                              {/* Requirements */}
                              {job.requirements && job.requirements.length > 0 && (
                                <div className="mb-6">
                                  <h3 className="text-[0.95rem] font-medium text-[#202020] mb-3">Requirements</h3>
                                  <ul className="list-disc list-inside space-y-2">
                                    {job.requirements.map((req, reqIdx) => (
                                      <li key={reqIdx} className="text-[0.85rem] text-[#303030]">
                                        {req}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Action Buttons */}
                              <div className="space-y-3">
                                {job.url && (
                                  <a
                                    href={job.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="block w-full px-4 py-3 text-center text-[0.9rem] bg-[#2563eb] text-white rounded-lg hover:opacity-90 transition-opacity"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    Apply on {job.company}'s site →
                                  </a>
                                )}
                                
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    localStorage.setItem('jobToApply', JSON.stringify(job));
                                    router.push('/apply');
                                  }}
                                  className="block w-full px-4 py-3 text-center text-[0.9rem] border border-[#2563eb] text-[#2563eb] rounded-lg hover:bg-[#2563eb] hover:text-white transition-all"
                                >
                                  Help me get this job →
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                </div>

                {/* No results message */}
                {jobs.filter(job => {
                  if (filter === 'remote') {
                    const searchText = `${job.title} ${job.location} ${job.type} ${job.description}`.toLowerCase();
                    return searchText.includes('remote');
                  }
                  if (filter === 'fulltime') {
                    const searchText = `${job.type} ${job.title}`.toLowerCase();
                    return searchText.includes('full') || searchText.includes('full-time');
                  }
                  if (filter === 'contract') {
                    const searchText = `${job.type} ${job.title}`.toLowerCase();
                    return searchText.includes('contract') || searchText.includes('contractor');
                  }
                  if (locationFilter) {
                    return job.location.toLowerCase().includes(locationFilter.toLowerCase());
                  }
                  return true;
                }).length === 0 && (
                  <div className="text-[0.9rem] text-[#707070] py-8 text-center">
                    No jobs match your filters. Try adjusting them.
                  </div>
                )}
              </>
            )}

            {!loading && jobs.length === 0 && (
              <div className="text-[0.9rem] text-[#707070]">
                No jobs found. Try a different search.
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
