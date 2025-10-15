'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { API_URL } from '../../config';

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
  salary_min?: number;
  salary_max?: number;
  salary_is_predicted?: boolean;
  job_type?: string;
}

export default function JobSearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';
  
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedJob, setExpandedJob] = useState<number | null>(null);
  const [filter, setFilter] = useState<'all' | 'remote' | 'hybrid' | 'onsite'>('remote');
  const [employmentType, setEmploymentType] = useState<string | null>(null);
  const [experienceLevel, setExperienceLevel] = useState<string | null>(null);
  const [locationFilter, setLocationFilter] = useState('');

  useEffect(() => {
    if (query) {
      searchJobs();
    }
  }, [query]);

  const searchJobs = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/search-jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          job_title: query,
          location: locationFilter || undefined,
          filter_type: filter,
          employment_types: employmentType,
          job_requirements: experienceLevel
        })
      });
      const data = await response.json();
      setJobs(data.jobs || []);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = async (newFilter: string, newEmploymentType?: string, newExperienceLevel?: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/search-jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          job_title: query,
          location: locationFilter || undefined,
          filter_type: newFilter,
          employment_types: newEmploymentType || employmentType,
          job_requirements: newExperienceLevel || experienceLevel
        })
      });
      const data = await response.json();
      setJobs(data.jobs || []);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTailorResume = (job: Job) => {
    router.push(`/tailor?job=${encodeURIComponent(JSON.stringify(job))}`);
  };

  return (
    <main className="min-h-screen bg-white">
      {/* Header */}
      <div style={{ position: 'fixed', top: '40px', left: '40px', zIndex: 100 }}>
        <a href="/" style={{ textDecoration: 'none' }}>
          <div className="flex flex-col">
            <span 
              className="text-[1.6rem] cursor-pointer hover:opacity-80 transition-opacity"
              style={{ fontWeight: '800', color: '#0A0A0A', letterSpacing: '-0.3px', marginBottom: '4px' }}
            >
              pathio
            </span>
            <span 
              className="text-[0.9rem]"
              style={{ fontWeight: '600', color: '#A78BFA' }}
            >
              smart career moves
            </span>
          </div>
        </a>
      </div>

      {/* Main Content */}
      <div className="max-w-[720px] mx-auto px-4 w-full" style={{ paddingBottom: '32px', paddingTop: '140px' }}>
        
        <h1 className="text-[1.6rem] text-center mb-6" style={{ fontWeight: '800', color: '#0A0A0A' }}>
          Job Search Results
        </h1>

        {loading && (
          <div className="text-center text-[0.9rem] text-[#707070] mb-6">
            Searching for jobs...
          </div>
        )}

        {jobs.length > 0 && (
          <>
            <div className="mb-4 text-[0.9rem] text-[#707070] text-center">
              {jobs.length} jobs found for "{query}"
            </div>

            {/* Job Filters */}
            <div className="mb-6 space-y-4">
              {/* Work Type Filters */}
              <div>
                <div className="text-[0.85rem] font-semibold text-[#313338] mb-2">Work Type</div>
                <div className="flex flex-wrap gap-2">
                  {[
                    { key: 'all', label: 'All' },
                    { key: 'remote', label: 'Remote' },
                    { key: 'hybrid', label: 'Hybrid' },
                    { key: 'onsite', label: 'Onsite' }
                  ].map((workType) => (
                    <button
                      key={workType.key}
                      onClick={() => {
                        setFilter(workType.key as any);
                        handleFilterChange(workType.key);
                      }}
                      className={`px-3 py-1 rounded-full text-[0.85rem] transition-all ${
                        filter === workType.key
                          ? 'bg-[#7C3AED] text-white'
                          : 'bg-[#F5F5F5] text-[#707070] hover:bg-[#E0E0E0]'
                      }`}
                    >
                      {workType.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Employment Type Filters */}
              <div>
                <div className="text-[0.85rem] font-semibold text-[#313338] mb-2">Employment Type</div>
                <div className="flex flex-wrap gap-2">
                  {[
                    { key: 'FULLTIME', label: 'Full-time' },
                    { key: 'CONTRACTOR', label: 'Contract' },
                    { key: 'PARTTIME', label: 'Part-time' },
                    { key: 'INTERN', label: 'Intern' }
                  ].map((type) => (
                    <button
                      key={type.key}
                      onClick={() => {
                        const newEmploymentType = employmentType === type.key ? null : type.key;
                        setEmploymentType(newEmploymentType);
                        handleFilterChange(filter, newEmploymentType || undefined);
                      }}
                      className={`px-3 py-1 rounded-full text-[0.85rem] transition-all ${
                        employmentType === type.key
                          ? 'bg-[#7C3AED] text-white'
                          : 'bg-[#F5F5F5] text-[#707070] hover:bg-[#E0E0E0]'
                      }`}
                    >
                      {type.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Experience Level Filters */}
              <div>
                <div className="text-[0.85rem] font-semibold text-[#313338] mb-2">Experience Level</div>
                <div className="flex flex-wrap gap-2">
                  {[
                    { key: 'no_experience', label: 'Entry Level' },
                    { key: 'under_3_years_experience', label: 'Mid Level' },
                    { key: 'more_than_3_years_experience', label: 'Senior Level' },
                    { key: 'no_degree', label: 'No Degree Required' }
                  ].map((level) => (
                    <button
                      key={level.key}
                      onClick={() => {
                        const newExperienceLevel = experienceLevel === level.key ? null : level.key;
                        setExperienceLevel(newExperienceLevel);
                        handleFilterChange(filter, employmentType || undefined, newExperienceLevel || undefined);
                      }}
                      className={`px-3 py-1 rounded-full text-[0.85rem] transition-all ${
                        experienceLevel === level.key
                          ? 'bg-[#7C3AED] text-white'
                          : 'bg-[#F5F5F5] text-[#707070] hover:bg-[#E0E0E0]'
                      }`}
                    >
                      {level.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Location Filter */}
              {(filter === 'hybrid' || filter === 'onsite') && (
                <div>
                  <div className="text-[0.85rem] font-semibold text-[#313338] mb-2">Location</div>
                  <input
                    type="text"
                    value={locationFilter}
                    onChange={(e) => setLocationFilter(e.target.value)}
                    placeholder="Enter city or state..."
                    className="w-full px-3 py-2 text-[0.85rem] border border-[#E0E0E0] rounded-lg focus:outline-none focus:border-[#7C3AED]"
                  />
                </div>
              )}
            </div>

            {/* Job Listings */}
            <div className="space-y-4">
              {jobs.map((job, idx) => (
                <div key={idx} className="border border-[#E0E0E0] rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div 
                    className="text-[0.95rem] font-medium text-[#2563eb] mb-2 cursor-pointer"
                    onClick={() => setExpandedJob(expandedJob === idx ? null : idx)}
                  >
                    {job.title} {expandedJob === idx ? '▼' : '▶'}
                  </div>
                  <div className="text-[0.85rem] text-[#707070] mb-2">
                    {job.company} • {job.location} • {job.type}
                    {job.salary_min && job.salary_max && (
                      <span style={{ color: '#7C3AED', fontWeight: '600' }}>
                        {' • $' + job.salary_min.toLocaleString() + ' - $' + job.salary_max.toLocaleString()}
                      </span>
                    )}
                  </div>
                  
                  {expandedJob === idx && (
                    <div className="mt-4 pt-4 border-t border-[#E0E0E0]">
                      <div 
                        className="text-[0.85rem] text-[#505050] leading-relaxed mb-4"
                        dangerouslySetInnerHTML={{ __html: job.description.replace(/\n/g, '<br>') }}
                      />
                      
                      <div className="flex gap-2">
                        {job.url && (
                          <a
                            href={job.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-4 py-2 text-[0.9rem] bg-[#2563eb] text-white rounded-lg hover:opacity-90 transition-opacity"
                          >
                            Apply Now →
                          </a>
                        )}
                        
                        <button
                          onClick={() => handleTailorResume(job)}
                          className="px-4 py-2 text-[0.9rem] border border-[#2563eb] text-[#2563eb] rounded-lg hover:bg-[#2563eb] hover:text-white transition-all"
                        >
                          Tailor My Resume For This Job →
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {!loading && jobs.length === 0 && (
          <div className="text-center text-[0.9rem] text-[#707070] py-8">
            No jobs found for "{query}". Try adjusting your search or filters.
          </div>
        )}
      </div>
    </main>
  );
}
