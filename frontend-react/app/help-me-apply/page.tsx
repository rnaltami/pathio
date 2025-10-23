'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'

interface JobAnalysis {
  jobTitle: string
  matchScore: number
  improvements: string[]
  dailyTasks: string[]
  canTailor: boolean
}

export default function HelpMeApplyPage() {
  const [jobDescription, setJobDescription] = useState('')
  const [resume, setResume] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [analysis, setAnalysis] = useState<JobAnalysis | null>(null)
  const [error, setError] = useState('')
  const [tailoredResume, setTailoredResume] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const searchParams = useSearchParams()

  useEffect(() => {
    // Get job description from URL params or localStorage
    const jobFromParams = searchParams.get('job')
    const jobFromStorage = localStorage.getItem('pastedJob')
    
    if (jobFromParams) {
      setJobDescription(decodeURIComponent(jobFromParams))
    } else if (jobFromStorage) {
      setJobDescription(jobFromStorage)
    }
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!jobDescription.trim() || !resume.trim()) return

    setIsLoading(true)
    setError('')
    
    try {
      const response = await fetch('http://localhost:8000/api/help-me-apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jobDescription,
          resume
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to analyze job match')
      }

      const data = await response.json()
      setAnalysis(data)
    } catch (error) {
      setError('Failed to analyze your resume against this job. Please try again.')
      console.error('Error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        setResume(event.target?.result as string)
      }
      reader.readAsText(file)
    }
  }

  const handleTailorResume = async () => {
    if (!analysis) return
    
    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/tailor-resume', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jobDescription,
          resume,
          analysis
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to tailor resume')
      }

      const tailoredResumeText = await response.text()
      setTailoredResume(tailoredResumeText)
      setIsEditing(false)
    } catch (error) {
      setError('Failed to tailor your resume. Please try again.')
      console.error('Error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownloadResume = () => {
    const blob = new Blob([tailoredResume], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'tailored-resume.txt'
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  // Extract job title from job description (simple extraction)
  const getJobTitle = (description: string) => {
    const lines = description.split('\n')
    const firstLine = lines[0]?.trim()
    if (firstLine && firstLine.length < 100) {
      return firstLine
    }
    return 'This Position'
  }

  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-lg font-semibold text-gray-900">
            Help Me Apply for "{getJobTitle(jobDescription)}"
          </h1>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {!analysis ? (
          /* Resume Upload Form */
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="resume" className="block text-sm font-medium text-gray-700 mb-2">
                Paste or Upload Your Resume
              </label>
              <textarea
                id="resume"
                value={resume}
                onChange={(e) => setResume(e.target.value)}
                placeholder="Paste your resume here or upload a file below..."
                className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700 mb-2">
                Or Upload Resume File
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                <input
                  type="file"
                  id="file-upload"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={handleFileUpload}
                  className="block mx-auto text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-purple-600 file:text-white hover:file:bg-purple-700"
                  disabled={isLoading}
                />
                <p className="text-gray-500 mt-2">PDF, DOC, DOCX, or TXT files accepted</p>
              </div>
            </div>

            <button
              type="submit"
              disabled={!resume.trim() || isLoading}
              className="w-full py-3 px-6 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Analyzing...' : 'Analyze My Match'}
            </button>

            {error && (
              <div className="bg-red-100 border border-red-300 rounded-lg p-4">
                <p className="text-red-700">{error}</p>
              </div>
            )}
          </form>
        ) : (
          /* Analysis Results */
          <div className="space-y-6">
            {/* Match Score */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Your Match Score</h2>
              <div className="flex items-center space-x-4">
                <div className="text-4xl font-bold text-purple-600">
                  {analysis.matchScore}%
                </div>
                <div className="flex-1">
                  <div className="w-full bg-gray-200 rounded-full h-4">
                    <div 
                      className={`h-4 rounded-full ${
                        analysis.matchScore >= 80 ? 'bg-green-500' :
                        analysis.matchScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${analysis.matchScore}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {analysis.matchScore >= 80 ? 'Great match!' :
                     analysis.matchScore >= 60 ? 'Good match with room for improvement' :
                     'Needs significant improvement'}
                  </p>
                </div>
              </div>
            </div>

            {/* Improvements */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">3 Things to Improve Your Chances</h2>
              <div className="space-y-4">
                {analysis.improvements.map((improvement, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center">
                      <span className="text-purple-600 font-medium text-sm">{index + 1}</span>
                    </div>
                    <p className="text-gray-700">{improvement}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Daily Tasks */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Do These Today to Improve Your Chances</h2>
              <div className="space-y-4">
                {analysis.dailyTasks.map((task, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-medium text-sm">{index + 1}</span>
                    </div>
                    <p className="text-gray-700">{task}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Tailored Resume Section */}
            {tailoredResume && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-medium text-gray-900">Your Tailored Resume</h2>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setIsEditing(!isEditing)}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                    >
                      {isEditing ? 'Done Editing' : 'Edit'}
                    </button>
                    <button
                      onClick={handleDownloadResume}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                    >
                      Download
                    </button>
                  </div>
                </div>
                
                {isEditing ? (
                  <textarea
                    value={tailoredResume}
                    onChange={(e) => setTailoredResume(e.target.value)}
                    className="w-full h-96 p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-sm font-mono"
                    placeholder="Your tailored resume will appear here..."
                  />
                ) : (
                  <div className="bg-white border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed">
                      {tailoredResume}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            {!tailoredResume && (
              <div className="flex space-x-4">
                <button
                  onClick={() => setAnalysis(null)}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Try Different Resume
                </button>
                
                {analysis.canTailor && (
                  <button
                    onClick={handleTailorResume}
                    disabled={isLoading}
                    className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Tailoring...' : 'Tailor My Resume to This Job'}
                  </button>
                )}
              </div>
            )}

            {error && (
              <div className="bg-red-100 border border-red-300 rounded-lg p-4">
                <p className="text-red-700">{error}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
