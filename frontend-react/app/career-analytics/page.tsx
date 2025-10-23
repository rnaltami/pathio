'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface ResumeAnalysis {
  skills: string[]
  experience_years: number
  current_role: string
  career_level: string
  market_value: {
    estimated_salary_min: number
    estimated_salary_max: number
    market_demand: string
    growth_potential: string
  }
  recommendations: string[]
  skill_gaps: string[]
  salary_insights: {
    current_range: string
    next_level_range: string
    industry_average: string
  }
  industry_insights: {
    trending_skills: string[]
    growth_areas: string[]
    remote_opportunities: string
  }
}

export default function CareerAnalytics() {
  const [resumeText, setResumeText] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null)
  const [error, setError] = useState('')
  const [uploadStatus, setUploadStatus] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleAnalyze = async () => {
    if (!resumeText.trim()) {
      setError('Please enter your resume text')
      return
    }

    setIsAnalyzing(true)
    setError('')

    try {
      const response = await fetch('http://localhost:8000/api/analytics/resume', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resume_text: resumeText
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to analyze resume')
      }

      const data = await response.json()
      setAnalysis(data)
    } catch (err) {
      setError('Failed to analyze resume. Please try again.')
      console.error('Analysis error:', err)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Clear previous states
    setError('')
    setUploadStatus('')
    setAnalysis(null)
    setSelectedFile(file)

    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
    if (!allowedTypes.includes(file.type)) {
      setError('Please upload a PDF, DOCX, or TXT file')
      return
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB')
      return
    }

    // Show upload status
    setIsUploading(true)
    setUploadStatus(`Uploading ${file.name}...`)

    try {
      const formData = new FormData()
      formData.append('file', file)

      setUploadStatus('Processing file and extracting text...')

      const response = await fetch('http://localhost:8000/api/analytics/resume-upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to analyze resume file')
      }

      setUploadStatus('Analyzing resume with AI...')
      setIsUploading(false)
      setIsAnalyzing(true)

      const data = await response.json()
      setAnalysis(data)
      
      // Show success message
      setUploadStatus('✅ Resume uploaded and analyzed successfully!')
      setResumeText(`Resume uploaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`)
    } catch (err) {
      setError('Failed to analyze resume file. Please try again.')
      setUploadStatus('')
      console.error('File upload error:', err)
    } finally {
      setIsUploading(false)
      setIsAnalyzing(false)
    }
  }

  const formatSalary = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <div className="min-h-screen bg-white text-gray-900">
      <div className="w-full max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold mb-4 text-gray-900">
            My Career Analytics
          </h1>
          <p className="text-gray-600 text-lg">
            Get personalized insights about your career path and market value
          </p>
        </div>

        {/* Resume Input */}
        <div className="bg-gray-50 rounded-2xl border border-gray-200 shadow-2xl p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Upload Your Resume</h2>
          <div className="space-y-4">
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              placeholder="Paste your resume text here... (or upload a file)"
              className="w-full h-40 p-4 rounded-lg bg-white text-gray-900 border border-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-400 resize-none"
              disabled={isAnalyzing}
            />
            
            <div className="space-y-4">
              <div className="flex gap-4">
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || isUploading || !resumeText.trim()}
                  className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium hover:from-purple-700 hover:to-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAnalyzing ? 'Analyzing...' : 'Analyze My Resume'}
                </button>
                
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  className="hidden"
                  id="file-upload"
                  onChange={handleFileUpload}
                  disabled={isAnalyzing}
                />
                <label
                  htmlFor="file-upload"
                  className={`px-6 py-3 rounded-xl font-medium transition-all duration-200 cursor-pointer ${
                    isUploading || isAnalyzing
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
                  }`}
                >
                  {isUploading ? 'Uploading...' : 'Upload File'}
                </label>
              </div>
              
              {selectedFile && (
                <div className="text-sm text-gray-600 bg-gray-100 rounded-lg p-3">
                  📄 Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Status Messages */}
        {uploadStatus && (
          <div className="bg-blue-100 border border-blue-300 rounded-lg p-4 mb-6">
            <p className="text-blue-700">{uploadStatus}</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-300 rounded-lg p-4 mb-6">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Analysis Results */}
        {analysis && (
          <div className="space-y-6">
            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl p-6 text-white">
                <h3 className="text-lg font-semibold mb-2">Experience</h3>
                <p className="text-3xl font-bold">{analysis.experience_years} years</p>
                <p className="text-purple-200 text-sm">{analysis.career_level}</p>
              </div>
              
              <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 text-white">
                <h3 className="text-lg font-semibold mb-2">Current Role</h3>
                <p className="text-xl font-bold">{analysis.current_role}</p>
                <p className="text-blue-200 text-sm">Market Demand: {analysis.market_value.market_demand}</p>
              </div>
              
              <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl p-6 text-white">
                <h3 className="text-lg font-semibold mb-2">Salary Range</h3>
                <p className="text-xl font-bold">
                  {formatSalary(analysis.market_value.estimated_salary_min)} - {formatSalary(analysis.market_value.estimated_salary_max)}
                </p>
                <p className="text-green-200 text-sm">Industry Avg: {analysis.salary_insights.industry_average}</p>
              </div>
              
              <div className="bg-gradient-to-br from-orange-600 to-orange-700 rounded-xl p-6 text-white">
                <h3 className="text-lg font-semibold mb-2">Growth Potential</h3>
                <p className="text-xl font-bold">{analysis.market_value.growth_potential}</p>
                <p className="text-orange-200 text-sm">Next Level: {analysis.salary_insights.next_level_range}</p>
              </div>
            </div>

            {/* Skills Analysis */}
            <div className="bg-gray-50 rounded-2xl p-6 border border-gray-200">
              <h3 className="text-2xl font-semibold mb-6 text-gray-900">Skills Analysis</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div>
                  <h4 className="text-lg font-semibold mb-4 text-green-600">Your Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.skills.map((skill, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm border border-green-300"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="text-lg font-semibold mb-4 text-red-600">Skill Gaps</h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.skill_gaps.map((gap, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm border border-red-300"
                      >
                        {gap}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendations */}
            <div className="bg-gray-50 rounded-2xl p-6 border border-gray-200">
              <h3 className="text-2xl font-semibold mb-6 text-gray-900">Career Recommendations</h3>
              <div className="space-y-4">
                {analysis.recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start gap-3 p-4 bg-white rounded-lg border border-gray-200">
                    <div className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0 mt-0.5">
                      {index + 1}
                    </div>
                    <p className="text-gray-700">{rec}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Industry Insights */}
            <div className="bg-gray-50 rounded-2xl p-6 border border-gray-200">
              <h3 className="text-2xl font-semibold mb-6 text-gray-900">Industry Insights</h3>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div>
                  <h4 className="text-lg font-semibold mb-3 text-blue-600">Trending Skills</h4>
                  <div className="space-y-2">
                    {analysis.industry_insights.trending_skills.map((skill, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <span className="text-gray-700">{skill}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="text-lg font-semibold mb-3 text-green-600">Growth Areas</h4>
                  <div className="space-y-2">
                    {analysis.industry_insights.growth_areas.map((area, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        <span className="text-gray-700">{area}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="text-lg font-semibold mb-3 text-purple-600">Remote Opportunities</h4>
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${analysis.industry_insights.remote_opportunities === 'High' ? 'bg-green-600' : 'bg-yellow-500'}`}></div>
                    <span className="text-gray-700">{analysis.industry_insights.remote_opportunities}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Back to Home */}
        <div className="mt-8 text-center">
          <Link
            href="/"
            className="inline-flex items-center text-purple-600 hover:text-purple-700 transition-colors"
          >
            ← Back to Pathio
          </Link>
        </div>
      </div>
    </div>
  )
}
