'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { API_URL } from '../config';

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
  job_type?: string; // remote, hybrid, onsite
}

export default function HomePage() {
  const router = useRouter();
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [careerAnalytics, setCareerAnalytics] = useState('');
  const [jobs, setJobs] = useState<Job[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [filter, setFilter] = useState<'all' | 'remote' | 'hybrid' | 'onsite'>('remote');
  const [employmentType, setEmploymentType] = useState<string | null>(null);
  const [experienceLevel, setExperienceLevel] = useState<string | null>(null);
  const [locationFilter, setLocationFilter] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/career-analytics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: inputText })
      });
      const data = await response.json();
      setCareerAnalytics(data.analytics);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleJobSearch = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/search-jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          job_title: inputText,
          location: locationFilter || undefined,
          filter_type: filter,
          employment_types: employmentType,
          job_requirements: experienceLevel
        })
      });
      const data = await response.json();
      setJobs(data.jobs || []);
      setHasSearched(true);
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
          job_title: inputText,
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
        
        {/* Career Analytics */}
        {careerAnalytics && (
          <div className="mb-8">
            <h1 className="text-[1.6rem] text-center mb-6" style={{ fontWeight: '800', color: '#0A0A0A' }}>
              Your Career Analytics
            </h1>
            <div 
              className="bg-white border border-[#E5E5E5] rounded-lg p-6"
              style={{ 
                background: 'linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%)',
                border: '2px solid #E2E8F0'
              }}
            >
              <div 
                className="text-[0.9rem] leading-relaxed"
                style={{ color: '#374151', lineHeight: '1.6' }}
                dangerouslySetInnerHTML={{ __html: careerAnalytics.replace(/\n/g, '<br>') }}
              />
            </div>
          </div>
        )}

        {/* Job Results */}
        {hasSearched && jobs.length > 0 && (
          <div className="mb-8">
            <h1 className="text-[1.6rem] text-center mb-6" style={{ fontWeight: '800', color: '#0A0A0A' }}>
              Job Results
            </h1>
            <div className="mb-4 text-[0.9rem] text-[#707070] text-center">
              {jobs.length} jobs found
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
            
            {/* Simple Job List */}
            <div className="space-y-4">
              {jobs.map((job, idx) => (
                <div key={idx} className="border border-[#E0E0E0] rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="text-[0.95rem] font-medium text-[#2563eb] mb-2">
                    {job.title}
                  </div>
                  <div className="text-[0.85rem] text-[#707070] mb-2">
                    {job.company} • {job.location} • {job.type}
                    {job.salary_min && job.salary_max && (
                      <span style={{ color: '#7C3AED', fontWeight: '600' }}>
                        {' • $' + job.salary_min.toLocaleString() + ' - $' + job.salary_max.toLocaleString()}
                      </span>
                    )}
                  </div>
                  <div className="text-[0.8rem] text-[#505050] line-clamp-3">
                    {job.description.substring(0, 200)}...
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Landing Page */}
        {!careerAnalytics && !hasSearched && (
          <>
            {/* Main Input */}
            <div className="flex flex-col items-center gap-4">
              <div className="w-full" style={{ maxWidth: '680px' }}>
                <form onSubmit={handleSubmit}>
                  <textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Start with your resume. Paste it here or upload..."
                    className="w-full text-[1rem] border-2 border-[#D8B4FE] focus:outline-none focus:border-[#A78BFA] transition-colors resize-none font-medium"
                    style={{ borderRadius: '20px', padding: '18px 22px', background: '#FAFAF9' }}
                    rows={4}
                  />
                  <div className="flex justify-center items-center" style={{ marginTop: '8px', gap: '12px' }}>
                    <button
                      type="submit"
                      disabled={loading}
                      className="text-[0.85rem] hover:opacity-90 transition-opacity"
                      style={{
                        background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                        padding: '12px 36px',
                        borderRadius: '24px',
                        color: '#FFFFFF',
                        fontWeight: 'bold',
                        border: 'none',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)',
                        opacity: loading ? 0.6 : 1
                      }}
                    >
                      {loading ? 'Analyzing...' : 'Analyze'}
                    </button>
                  </div>
                </form>
              </div>
            </div>

            {/* Action Links */}
            <div className="flex flex-col items-center" style={{ marginTop: '34px' }}>
              <div className="flex flex-wrap justify-center" style={{ maxWidth: '680px', gap: '8px' }}>
                <button
                  onClick={handleJobSearch}
                  className="text-[0.85rem] font-semibold px-5 py-2.5 rounded-xl transition-all"
                  style={{ background: '#F3E8FF', color: '#5B21B6' }}
                >
                  🔹 Find a job — the old-fashioned kind with paychecks.
                </button>
                <button
                  onClick={() => router.push('/apply')}
                  className="text-[0.85rem] font-semibold px-5 py-2.5 rounded-xl transition-all"
                  style={{ background: '#F3E8FF', color: '#5B21B6' }}
                >
                  🔹 Help me land a job — I already have a listing.
                </button>
                <button
                  onClick={() => router.push('/chat')}
                  className="text-[0.85rem] font-semibold px-5 py-2.5 rounded-xl transition-all"
                  style={{ background: '#F3E8FF', color: '#5B21B6' }}
                >
                  🔹 Find AI tools — so I can build my own thing instead.
                </button>
              </div>
            </div>
          </>
        )}
    </div>
    </main>
  );
}