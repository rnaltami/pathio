'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
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

export default function JobDetail() {
  const params = useParams()
  const router = useRouter()
  const [job, setJob] = useState<Job | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // For now, we'll get the job data from localStorage or URL params
    // In a real app, this would be an API call with the job ID
    const jobData = localStorage.getItem('selectedJob')
    if (jobData) {
      setJob(JSON.parse(jobData))
    }
    setIsLoading(false)
  }, [])

  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return 'Salary not specified'
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`
    if (min) return `$${min.toLocaleString()}+`
    if (max) return `Up to $${max.toLocaleString()}`
    return 'Salary not specified'
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white text-gray-900 pt-20 pb-20 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading job details...</p>
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-white text-gray-900 pt-20 pb-20">
        <div className="w-full max-w-4xl mx-auto px-4">
          <div className="text-center py-12">
            <h1 className="text-2xl font-bold text-gray-700 mb-4">Job Not Found</h1>
            <p className="text-gray-500 mb-8">The job you're looking for could not be found.</p>
            <Link
              href="/job-search"
              className="inline-flex items-center px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              ← Back to Job Search
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-gray-900 pt-20 pb-20">
      <div className="w-full max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/job-search"
            className="inline-flex items-center text-purple-600 hover:text-purple-700 transition-colors mb-6"
          >
            ← Back to Job Search
          </Link>
          
          <h1 className="text-4xl font-bold text-gray-900 mb-4">{job.title}</h1>
          <div className="flex items-center gap-4 text-gray-600 mb-6">
            <span className="text-xl font-semibold text-purple-600">{job.company}</span>
            <span>•</span>
            <span>{job.location}</span>
            <span>•</span>
            <span className="capitalize">{job.type}</span>
          </div>
          
          <div className="bg-green-100 border border-green-300 rounded-lg p-4 mb-6">
            <p className="text-green-700 font-medium text-lg">
              {formatSalary(job.salary_min, job.salary_max)}
            </p>
          </div>
        </div>

        {/* Job Description */}
        <div className="bg-gray-50 rounded-2xl shadow-lg p-8 border border-gray-200 mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Job Description</h2>
          <div className="prose max-w-none">
            <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              {job.description}
            </div>
          </div>
        </div>

        {/* Apply Section */}
        <div className="bg-gray-50 rounded-2xl shadow-lg p-8 border border-gray-200">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Apply for this Position</h2>
          <div className="space-y-4">
            <p className="text-gray-700">
              Ready to apply? Click the button below to visit the company's application page.
            </p>
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-8 py-4 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 transition-colors"
            >
              Apply on Company Website →
            </a>
          </div>
        </div>

        {/* Raw JSON (for development) */}
        <details className="mt-8 bg-gray-50 rounded-2xl shadow-lg border border-gray-200">
          <summary className="p-6 cursor-pointer text-purple-600 hover:text-purple-700 font-medium">
            View Raw Job Data (Development)
          </summary>
          <div className="p-6 border-t border-gray-200">
            <pre className="text-sm text-gray-700 overflow-x-auto">
              {JSON.stringify(job, null, 2)}
            </pre>
          </div>
        </details>
      </div>
    </div>
  )
}

