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
}

function JobSearchContent() {
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState('')
  const [jobType, setJobType] = useState('all')
  const [jobs, setJobs] = useState<Job[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isClient, setIsClient] = useState(false)

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
      performSearch(urlQuery, urlLocation || '', urlRemote === 'true' ? 'remote' : 'all')
    }
  }, [])

  const performSearch = async (searchQuery: string, searchLocation: string, searchJobType: string) => {
    if (!searchQuery.trim()) return

    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('http://localhost:8000/api/jobs/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          location: searchLocation || null,
          job_type: searchJobType === 'all' ? null : searchJobType,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to fetch jobs')
      }

      const data = await response.json()
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
      <div className="min-h-screen bg-gray-900 text-gray-100 pt-20 pb-20 flex items-center justify-center">
        <div className="text-center">
          <div className="text-purple-400 text-xl mb-4">Loading job search...</div>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400 mx-auto"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 pt-20 pb-20">
      <div className="w-full max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-600">
            Job Search
          </h1>
          <p className="text-gray-400 text-lg">
            Find your next career opportunity with real-time job listings
          </p>
        </div>

        {/* Search Form */}
        <div className="bg-gray-800 rounded-xl shadow-2xl p-6 mb-8 border border-gray-700">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Job title, keywords, or company..."
                className="flex-1 p-4 rounded-lg bg-gray-700 text-gray-100 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-400"
                disabled={isLoading}
              />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Location (e.g., San Francisco, CA)"
                className="flex-1 p-4 rounded-lg bg-gray-700 text-gray-100 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-400"
                disabled={isLoading}
              />
            </div>
            
            <div className="flex flex-col md:flex-row gap-4 items-center">
              <select
                value={jobType}
                onChange={(e) => setJobType(e.target.value)}
                className="p-4 rounded-lg bg-gray-700 text-gray-100 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500"
                disabled={isLoading}
              >
                <option value="all">All Job Types</option>
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
                <option value="onsite">On-site</option>
              </select>
              
              <button
                type="submit"
                className="w-full md:w-auto px-8 py-4 rounded-lg bg-purple-600 text-white font-semibold hover:bg-purple-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isLoading || !query.trim()}
              >
                {isLoading ? 'Searching...' : 'Search Jobs'}
              </button>
            </div>
          </form>
        </div>

        {/* Results */}
        {error && (
          <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {jobs.length > 0 && (
          <div className="mb-6">
            <p className="text-gray-400">
              Found {jobs.length} job{jobs.length !== 1 ? 's' : ''}
            </p>
          </div>
        )}

        {/* Job Cards */}
        <div className="space-y-4">
          {jobs.map((job, index) => (
            <div
              key={index}
              className="bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-700 hover:border-purple-500/50 transition-colors duration-200 cursor-pointer"
              onClick={() => {
                // Store job data and navigate to detail page
                localStorage.setItem('selectedJob', JSON.stringify(job))
                window.location.href = `/job-search/${index}`
              }}
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-white mb-2 hover:text-purple-400 transition-colors">
                    {job.title}
                  </h3>
                  <div className="flex items-center gap-4 text-gray-400 mb-2">
                    <span className="font-medium">{job.company}</span>
                    <span>•</span>
                    <span>{job.location}</span>
                    <span>•</span>
                    <span className="capitalize">{job.type}</span>
                  </div>
                  {formatSalary(job.salary_min, job.salary_max) && (
                    <p className="text-green-400 font-medium mb-3">
                      {formatSalary(job.salary_min, job.salary_max)}
                    </p>
                  )}
                </div>
                <div className="text-purple-400 text-sm font-medium">
                  View Details →
                </div>
              </div>
              
              <p className="text-gray-300 leading-relaxed">
                {truncateDescription(job.description)}
              </p>
              
              {job.url && (
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 text-sm font-medium"
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
        {!isLoading && jobs.length === 0 && query && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg mb-4">
              No jobs found for "{query}"
            </div>
            <p className="text-gray-600">
              Try adjusting your search terms or location
            </p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && jobs.length === 0 && !query && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg mb-4">
              Start your job search
            </div>
            <p className="text-gray-600">
              Enter a job title or keyword to find opportunities
            </p>
          </div>
        )}

        {/* Back to Home */}
        <div className="mt-8 text-center">
          <Link
            href="/"
            className="inline-flex items-center text-purple-400 hover:text-purple-300 transition-colors"
          >
            ← Back to Pathio
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function JobSearch() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-900 text-gray-100 pt-20 pb-20 flex items-center justify-center">
        <div className="text-center">
          <div className="text-purple-400 text-xl mb-4">Loading job search...</div>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400 mx-auto"></div>
        </div>
      </div>
    }>
      <JobSearchContent />
    </Suspense>
  )
}