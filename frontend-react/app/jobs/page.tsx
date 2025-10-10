'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

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

export default function JobsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const query = searchParams.get('q') || '';
  
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'remote' | 'location'>('all');
  const [locationFilter, setLocationFilter] = useState('');

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          'https://pathio-c9yz.onrender.com/search-jobs',
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              job_title: query,
            }),
          }
        );
        const data = await response.json();
        // Handle both array and object responses
        const jobsArray = Array.isArray(data) ? data : (data.jobs || []);
        setJobs(jobsArray);
      } catch (error) {
        console.error('Error fetching jobs:', error);
        setJobs([]);
      } finally {
        setLoading(false);
      }
    };

    if (query) {
      fetchJobs();
    }
  }, [query]);

  const filteredJobs = jobs.filter(job => {
    if (filter === 'remote') {
      return job.location.toLowerCase().includes('remote') || 
             job.type.toLowerCase().includes('remote');
    }
    if (filter === 'location' && locationFilter) {
      return job.location.toLowerCase().includes(locationFilter.toLowerCase());
    }
    return true;
  });

  return (
    <main className="min-h-screen bg-white">
      <div className="max-w-[680px] mx-auto px-4 py-8">
        {/* Header with back button */}
        <button
          onClick={() => router.push('/')}
          className="mb-6 text-[0.9rem] text-[#707070] hover:opacity-70 transition-opacity"
        >
          ← Back to search
        </button>

        {/* Results header */}
        {!loading && (
          <div className="mb-4 text-[0.9rem] text-[#707070]">
            {filteredJobs.length} {query} jobs found
          </div>
        )}

        {/* Filter options - Radio buttons */}
        <div className="flex gap-4 mb-6 text-[0.9rem]">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              checked={filter === 'all'}
              onChange={() => setFilter('all')}
              className="cursor-pointer"
            />
            <span className="text-[#707070]">All Jobs</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              checked={filter === 'remote'}
              onChange={() => setFilter('remote')}
              className="cursor-pointer"
            />
            <span className="text-[#707070]">Remote Only</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              checked={filter === 'location'}
              onChange={() => setFilter('location')}
              className="cursor-pointer"
            />
            <span className="text-[#707070]">By Location</span>
          </label>
        </div>

        {/* Location filter input */}
        {filter === 'location' && (
          <input
            type="text"
            value={locationFilter}
            onChange={(e) => setLocationFilter(e.target.value)}
            placeholder="e.g., San Francisco, New York"
            className="w-full mb-6 px-4 py-2 text-[0.9rem] border border-[#E0E0E0] rounded-lg focus:outline-none focus:border-[#E0E0E0]"
          />
        )}

        {/* Loading state */}
        {loading && (
          <div className="text-[0.9rem] text-[#707070]">Searching...</div>
        )}

        {/* Job listings - GUARANTEED BLUE AND LEFT ALIGNED! */}
        {!loading && filteredJobs.length > 0 && (
          <div>
            {filteredJobs.map((job, idx) => (
              <div
                key={idx}
                className="py-4 border-t border-[#E0E0E0] cursor-pointer hover:opacity-70 transition-opacity"
                onClick={() => {
                  // Store job in localStorage for detail page
                  localStorage.setItem('selectedJob', JSON.stringify(job));
                  router.push(`/jobs/${idx}`);
                }}
              >
                {/* Job title - BLUE AND LEFT ALIGNED */}
                <div className="text-[0.95rem] font-medium text-[#2563eb] mb-2 text-left">
                  {job.title}
                </div>
                {/* Company info - GREY AND LEFT ALIGNED */}
                <div className="text-[0.85rem] text-[#707070] text-left">
                  {job.company} • {job.location} • {job.type}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* No results */}
        {!loading && filteredJobs.length === 0 && jobs.length > 0 && (
          <div className="text-[0.9rem] text-[#707070]">
            No jobs found with current filters. Try adjusting your filters.
          </div>
        )}

        {!loading && jobs.length === 0 && (
          <div className="text-[0.9rem] text-[#707070]">
            No jobs found. Try a different search.
          </div>
        )}
      </div>
    </main>
  );
}

