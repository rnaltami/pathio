'use client'

import { useState, useEffect, Suspense } from 'react'
import Link from 'next/link'

interface Job {
  title: string
  company: string
  location: string
  type: string
  description: string
  url: string
  salary_min?: number
  salary_max?: number
  job_type: string
  posted_at?: string
  posted_timestamp?: number
}

function JobSearchContent() {
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState('')
  const [jobType, setJobType] = useState('all')
  const [jobs, setJobs] = useState<Job[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isClient, setIsClient] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  // Handle client-side hydration and URL parameters
  useEffect(() => {
    setIsClient(true)
    
    // Use window.location.search for reliable URL parameter parsing
    const urlParams = new URLSearchParams(window.location.search)
    const urlQuery = urlParams.get('query')
    const urlLocation = urlParams.get('location')
    const urlRemote = urlParams.get('remote')
    
    console.log('URL params:', { urlQuery, urlLocation, urlRemote })
    
    if (urlQuery) {
      setQuery(urlQuery)
      setLocation(urlLocation || '')
      setJobType(urlRemote === 'true' ? 'remote' : 'all')
      
      // Auto-search when URL parameters are present
      performSearch(urlQuery, urlLocation || '')
    }
  }, [])

  const performSearch = async (searchQuery: string, searchLocation: string, searchJobType: string) => {
    if (!searchQuery.trim()) return

    setIsLoading(true)
    setError('')
    setHasSearched(true)

    try {
      const response = await fetch('http://localhost:8000/api/jobs/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          location: searchLocation || null,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to fetch jobs')
      }

      const data = await response.json()
      console.log('First job data structure:', data.jobs?.[0])
      setJobs(data.jobs || [])
    } catch (err) {
      setError('Failed to fetch jobs. Please try again.')
      console.error('Job search error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    await performSearch(query, location, jobType)
  }

  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return ''
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`
    if (min) return `$${min.toLocaleString()}+`
    if (max) return `Up to $${max.toLocaleString()}`
    return ''
  }

  const truncateDescription = (description: string, maxLength: number = 200) => {
    if (description.length <= maxLength) return description
    return description.substring(0, maxLength) + '...'
  }

  // Show loading state until client-side hydration is complete
  if (!isClient) {
    return (
      <div className="min-h-screen bg-white text-gray-900 pt-20 pb-20 flex items-center justify-center">
        <div className="text-center">
          <div className="text-purple-600 text-xl mb-4">Loading job search...</div>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-gray-900 pt-20 pb-20">
      <div className="w-full max-w-6xl mx-auto px-4">
        {/* Search Form - Matching Landing Page Style */}
        <div className="w-full max-w-3xl mx-auto">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 mb-8">
          <form onSubmit={handleSearch}>
            {/* Main Input - Same as Landing Page */}
            <div className="p-6">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Job title, keywords, or company..."
                className="w-full bg-transparent text-xl text-gray-900 placeholder-gray-400 focus:outline-none"
                disabled={isLoading}
              />
            </div>

            {/* Location Field - Same as Landing Page */}
            <div className="border-t border-gray-200 p-6 bg-gray-100">
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Location (optional)"
                className="w-full bg-white text-gray-900 placeholder-gray-500 px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
                disabled={isLoading}
              />
            </div>

            {/* Search Button - Same as Landing Page */}
            <div className="p-6 pt-0">
              <button
                type="submit"
                disabled={!query.trim() || isLoading}
                className="w-full py-4 px-6 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-medium hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                {isLoading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </form>
          </div>
        </div>

        {/* Tab Chips - Below Search Form, Same as Landing Page */}
        <div className="flex flex-wrap justify-center gap-3 mt-8 w-full">
          <button
            onClick={() => window.location.href = '/'}
            className="px-6 py-3 rounded-full text-sm font-medium transition-all duration-200 bg-gray-100 text-gray-600 hover:bg-gray-200 border border-gray-200"
          >
            Chat
          </button>
          <button
            className="px-6 py-3 rounded-full text-sm font-medium transition-all duration-200 bg-purple-600 text-white shadow-lg shadow-purple-600/25"
          >
            Job Search
          </button>
          <button
            onClick={() => window.location.href = '/ai-tools'}
            className="px-6 py-3 rounded-full text-sm font-medium transition-all duration-200 bg-gray-100 text-gray-600 hover:bg-gray-200 border border-gray-200"
          >
            Help Me Apply
          </button>
          <button
            onClick={() => window.location.href = '/career-analytics'}
            className="px-6 py-3 rounded-full text-sm font-medium transition-all duration-200 bg-gray-100 text-gray-600 hover:bg-gray-200 border border-gray-200"
          >
            My Career Analytics
          </button>
          <button
            onClick={() => window.location.href = '/ai-tools'}
            className="px-6 py-3 rounded-full text-sm font-medium transition-all duration-200 bg-gray-100 text-gray-600 hover:bg-gray-200 border border-gray-200"
          >
            AI Tools
          </button>
        </div>

        {/* Results */}
        {error && (
          <div className="bg-red-100 border border-red-300 rounded-lg p-4 mb-6">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {jobs.length > 0 && (
          <div className="mb-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <p className="text-gray-600">
                Found {jobs.length} job{jobs.length !== 1 ? 's' : ''}
              </p>
              
              {/* Simple sorting filters */}
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => {
                    const sorted = [...jobs].sort((a, b) => {
                      const dateA = new Date(a.posted_at || 0).getTime();
                      const dateB = new Date(b.posted_at || 0).getTime();
                      return dateB - dateA; // Newest first
                    });
                    setJobs(sorted);
                  }}
                  className="px-4 py-2 rounded-full text-sm font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
                >
                  Sort by Date
                </button>
                <button
                  onClick={() => {
                    const sorted = [...jobs].sort((a, b) => {
                      const salaryA = a.salary_max || a.salary_min || 0;
                      const salaryB = b.salary_max || b.salary_min || 0;
                      return salaryB - salaryA; // Highest first
                    });
                    setJobs(sorted);
                  }}
                  className="px-4 py-2 rounded-full text-sm font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
                >
                  Sort by Salary
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Job Cards */}
        <div className="space-y-4">
          {jobs.map((job, index) => (
            <div
              key={index}
              className="bg-gray-50 rounded-2xl shadow-lg p-6 border border-gray-200 hover:border-purple-500/50 transition-colors duration-200 cursor-pointer"
              onClick={() => {
                // Store job data and navigate to detail page
                localStorage.setItem('selectedJob', JSON.stringify(job))
                window.location.href = `/job-search/${index}`
              }}
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2 hover:text-purple-600 transition-colors">
                    {job.title}
                  </h3>
                  <div className="flex items-center gap-4 text-gray-600 mb-2">
                    <span className="font-semibold text-purple-600">{job.company}</span>
                    <span>•</span>
                    <span>{job.location}</span>
                    {job.type && (
                      <>
                        <span>•</span>
                        <span className="capitalize">{job.type}</span>
                      </>
                    )}
                    {job.posted_at && (
                      <>
                        <span>•</span>
                        <span className="text-blue-600 text-sm">Posted {job.posted_at}</span>
                      </>
                    )}
                  </div>
                  {formatSalary(job.salary_min, job.salary_max) && (
                    <p className="text-green-600 font-medium mb-3">
                      {formatSalary(job.salary_min, job.salary_max)}
                    </p>
                  )}
                </div>
                <div className="text-purple-600 text-sm font-medium">
                  View Details →
                </div>
              </div>
              
              <p className="text-gray-700 leading-relaxed">
                {truncateDescription(job.description)}
              </p>
              
              {job.url && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Apply on Company Website →
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* No Results */}
        {!isLoading && hasSearched && jobs.length === 0 && query && (
          <div className="text-center py-12">
            <div className="text-gray-600 text-lg mb-4">
              No jobs found for "{query}"
            </div>
            <p className="text-gray-500">
              Try adjusting your search terms or location
            </p>
          </div>
        )}


      </div>
    </div>
  )
}

export default function JobSearch() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white text-gray-900 pt-20 pb-20 flex items-center justify-center">
        <div className="text-center">
          <div className="text-purple-600 text-xl mb-4">Loading job search...</div>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
        </div>
      </div>
    }>
      <JobSearchContent />
    </Suspense>
  )
}