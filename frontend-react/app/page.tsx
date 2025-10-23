'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

interface Message {
  id: number
  text: string
  isUser: boolean
  sources?: Array<{title: string, url: string}>
  marketData?: any
}

interface Job {
  title: string
  company: string
  location: string
  type: string
  description: string
  url: string
  salary_min?: number
  salary_max?: number
  posted_at?: string
}

interface CareerAnalysis {
  skills: string[]
  career_level: string
  experience_years: number
  current_role: string
  market_value: {
    estimated_salary_min: number
    estimated_salary_max: number
    market_demand: string
    growth_potential: string
  }
  salary_insights: {
    current_range: string
    next_level_range: string
    industry_average: string
  }
  recommendations: string[]
  skill_gaps: string[]
  industry_insights: {
    trending_skills: string[]
    growth_areas: string[]
    remote_opportunities: string
  }
}


export default function Home() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [selectedTab, setSelectedTab] = useState('chat')
  const [inputText, setInputText] = useState('')
  const [location, setLocation] = useState('')
  const [isClient, setIsClient] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [careerAnalysis, setCareerAnalysis] = useState<CareerAnalysis | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')

  // Handle client-side rendering
  useEffect(() => {
    setIsClient(true)
  }, [])

  // Reset chat state when component mounts or reset=true
  useEffect(() => {
    if (searchParams.get('reset') === 'true') {
      setSelectedTab('chat')
      setInputText('')
      setLocation('')
      setMessages([])
      setJobs([])
      setCareerAnalysis(null)
      setSelectedFile(null)
      setUploadStatus('')
      setError('')
    }
  }, [searchParams])

  const tabs = [
    { id: 'chat', label: 'Chat', placeholder: "ie. what is the top company to work for this year?" },
    { id: 'job-search', label: 'Job Search', placeholder: "software engineer remote" },
    { id: 'land-job', label: 'Help Me Apply', placeholder: "place the job you want" },
    { id: 'career-analytics', label: 'My Career Analytics', placeholder: "paste or upload your resume" },
    { id: 'ai-tools', label: 'AI Tools', placeholder: "writing tools for content creation" }
  ]

  const getPlaceholder = () => {
    // If we're in chat or ai-tools mode and have messages, show follow-up placeholder
    if ((selectedTab === 'chat' || selectedTab === 'ai-tools') && messages.length > 0) {
      return "Follow up"
    }
    
    const tab = tabs.find(t => t.id === selectedTab)
    return tab?.placeholder || "ie. what is the top company to work for this year?"
  }

  const showLocationField = selectedTab === 'job-search'
  const showUploadFile = selectedTab === 'career-analytics'

  const handleTabSelect = (tabId: string) => {
    // Handle all tabs on the same page
    setSelectedTab(tabId)
    setInputText('')
    setLocation('')
    if (tabId !== 'chat') {
      setMessages([])
    }
    if (tabId !== 'job-search') {
      setJobs([])
    }
    if (tabId !== 'career-analytics') {
      setCareerAnalysis(null)
      setSelectedFile(null)
      setUploadStatus('')
    }
    setError('')
  }

  const convertUrlsToLinks = (text: string) => {
    // Convert URLs to clickable links
    const urlRegex = /(https?:\/\/[^\s]+)/g
    const parts = text.split(urlRegex)
    
    return parts.map((part, index) => {
      if (urlRegex.test(part)) {
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 underline"
          >
            {part}
          </a>
        )
      }
      return part
    })
  }

  const formatAIToolsResponse = (text: string) => {
    // Safety check for undefined or null text
    if (!text || typeof text !== 'string') {
      return <div className="text-gray-500 italic">No response available</div>
    }
    
    // Split by lines and format without markdown
    const lines = text.split('\n')
    
    return (
      <div className="space-y-3">
        {lines.map((line, index) => {
          const trimmedLine = line.trim()
          
          if (!trimmedLine) {
            return <div key={index} className="h-2"></div> // Empty line spacing
          }
          
          // Check if it's a bullet point
          if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('• ')) {
            return (
              <div key={index} className="flex items-start ml-4">
                <span className="text-purple-600 mr-3 mt-1 text-sm">•</span>
                <span className="text-gray-700 leading-relaxed">
                  {convertUrlsToLinks(trimmedLine.replace(/^[-•]\s*/, ''))}
                </span>
              </div>
            )
          }
          
          // Check if it's a numbered list
          if (/^\d+\.\s/.test(trimmedLine)) {
            return (
              <div key={index} className="flex items-start ml-4">
                <span className="text-purple-600 mr-3 mt-1 text-sm font-medium">
                  {trimmedLine.match(/^\d+/)?.[0]}.
                </span>
                <span className="text-gray-700 leading-relaxed">
                  {convertUrlsToLinks(trimmedLine.replace(/^\d+\.\s*/, ''))}
                </span>
              </div>
            )
          }
          
          // Regular text
          return (
            <div key={index} className="text-gray-700 leading-relaxed">
              {convertUrlsToLinks(trimmedLine)}
            </div>
          )
        })}
      </div>
    )
  }

  const formatPerplexityResponse = (text: string) => {
    // Safety check for undefined or null text
    if (!text || typeof text !== 'string') {
      return <div className="text-gray-500 italic">No response available</div>
    }
    
    // Check if this response has the expected structured format
    const hasStructuredHeaders = /(\*\*Summary\*\*|\*\*Key Insights\*\*|\*\*Current Trends\*\*|\*\*Market Intelligence\*\*|\*\*Next Steps\*\*)/i.test(text)
    
    if (!hasStructuredHeaders) {
      // Simple markdown rendering for non-structured responses
      return (
        <div className="prose max-w-none text-gray-900">
          {text.split('\n').map((line, index) => {
            const trimmedLine = line.trim()
            if (trimmedLine.startsWith('- ')) {
              return (
                <div key={index} className="flex items-start mb-2 ml-4">
                  <span className="text-purple-600 mr-3 mt-1 text-sm">•</span>
                  <span className="text-gray-700 text-sm leading-relaxed">{trimmedLine.replace('- ', '')}</span>
                </div>
              )
            } else if (trimmedLine.startsWith('• ')) {
              return (
                <div key={index} className="flex items-start mb-2 ml-4">
                  <span className="text-purple-600 mr-3 mt-1 text-sm">•</span>
                  <span className="text-gray-700 text-sm leading-relaxed">{trimmedLine.replace('• ', '')}</span>
                </div>
              )
            } else if (trimmedLine.match(/^\d+\./)) {
              return (
                <div key={index} className="flex items-start mb-2 ml-4">
                  <span className="text-purple-600 mr-3 mt-1 text-sm font-medium">{trimmedLine.split('.')[0]}.</span>
                  <span className="text-gray-700 text-sm leading-relaxed">{trimmedLine.replace(/^\d+\.\s*/, '')}</span>
                </div>
              )
            } else if (trimmedLine) {
              return (
                <div key={index} className="text-gray-700 mb-3 text-sm leading-relaxed">
                  {trimmedLine}
                </div>
              )
            }
            return null
          })}
        </div>
      )
    }

    // Structured response parsing with better header detection
    const knownHeaders = ['Summary', 'Key Insights', 'Current Trends', 'Market Intelligence', 'Next Steps', 'Sources']
    const lines = text.split('\n')
    const formatted = []
    let currentSection = ''
    let currentContent = []
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      if (!line) continue
      
      // Check if this line is a known header
      const isHeader = knownHeaders.some(header => 
        line === `**${header}**` || 
        line === `### ${header}` ||
        line === header
      )
      
      if (isHeader) {
        // Process previous section if it exists
        if (currentSection && currentContent.length > 0) {
          formatted.push(renderSection(currentSection, currentContent, formatted.length))
        }
        
        // Start new section
        currentSection = line.replace(/\*\*/g, '').replace(/### /g, '')
        currentContent = []
      } else {
        // Add content to current section
        currentContent.push(line)
      }
    }
    
    // Process final section
    if (currentSection && currentContent.length > 0) {
      formatted.push(renderSection(currentSection, currentContent, formatted.length))
    }
    
    return formatted.length > 0 ? formatted : [<div key="fallback" className="text-gray-700">{text}</div>]
  }

  const renderSection = (sectionName: string, content: string[], keyOffset: number) => {
    return (
      <div key={`section-${keyOffset}`} className="mb-6">
        <div className="font-bold text-xl text-purple-600 mb-3 mt-6 first:mt-0">
          {sectionName}
        </div>
        <div className="space-y-2">
          {content.map((line, lineIndex) => {
            const trimmedLine = line.trim()
            if (trimmedLine.startsWith('- ')) {
              return (
                <div key={`${keyOffset}-${lineIndex}`} className="flex items-start mb-2 ml-4">
                  <span className="text-purple-600 mr-3 mt-1 text-sm">•</span>
                  <span className="text-gray-700 text-sm leading-relaxed">{trimmedLine.replace('- ', '')}</span>
                </div>
              )
            } else if (trimmedLine.startsWith('• ')) {
              return (
                <div key={`${keyOffset}-${lineIndex}`} className="flex items-start mb-2 ml-4">
                  <span className="text-purple-600 mr-3 mt-1 text-sm">•</span>
                  <span className="text-gray-700 text-sm leading-relaxed">{trimmedLine.replace('• ', '')}</span>
                </div>
              )
            } else if (trimmedLine.match(/^\d+\./)) {
              return (
                <div key={`${keyOffset}-${lineIndex}`} className="flex items-start mb-2 ml-4">
                  <span className="text-purple-600 mr-3 mt-1 text-sm font-medium">{trimmedLine.split('.')[0]}.</span>
                  <span className="text-gray-700 text-sm leading-relaxed">{trimmedLine.replace(/^\d+\.\s*/, '')}</span>
                </div>
              )
            } else if (trimmedLine) {
              return (
                <div key={`${keyOffset}-${lineIndex}`} className="text-gray-700 mb-3 text-sm leading-relaxed">
                  {trimmedLine}
                </div>
              )
            }
            return null
          })}
        </div>
      </div>
    )
  }

  const handleSubmit = async () => {
    console.log('handleSubmit called - inputText:', inputText, 'trimmed:', inputText.trim(), 'isLoading:', isLoading)
    if (!inputText.trim() || isLoading) {
      console.log('Submit blocked - inputText:', inputText.trim(), 'isLoading:', isLoading)
      return
    }

    if (selectedTab === 'chat') {
      // Store the input text before clearing it
      const messageText = inputText.trim()
      
      // Clear input immediately for better UX
      setInputText('')
      setIsLoading(true)
      
      // Add user message
      const userMessage: Message = {
        id: Date.now(),
        text: messageText,
        isUser: true
      }
      setMessages(prev => [...prev, userMessage])

      try {
        const response = await fetch('http://localhost:8000/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: messageText }),
        })
        const data = await response.json()
        
        
        const aiMessage: Message = {
          id: Date.now() + 1,
          text: data.reply,
          isUser: false,
          sources: data.sources,
          marketData: data.market_data
        }
        setMessages(prev => [...prev, aiMessage])
      } catch (error) {
        console.error('Error:', error)
        const errorMessage: Message = {
          id: Date.now() + 1,
          text: 'Sorry, there was an error. Please try again.',
          isUser: false
        }
        setMessages(prev => [...prev, errorMessage])
      } finally {
        setIsLoading(false)
      }
      return
    }

    if (selectedTab === 'land-job') {
      // Handle Help Me Apply - redirect to dedicated page
      const jobDescription = inputText.trim()
      
      if (!jobDescription) return
      
      // Store job description in localStorage
      localStorage.setItem('pastedJob', jobDescription)
      
      // Redirect to help-me-apply page
      window.location.href = `/help-me-apply?job=${encodeURIComponent(jobDescription)}`
      return
    }

    if (selectedTab === 'job-search') {
      // Handle job search on the same page
      const searchQuery = inputText.trim()
      const searchLocation = location.trim()
      
      // Clear inputs
      setInputText('')
      setLocation('')
      setIsLoading(true)
      setError('')
      
      // No user message for job search - just show results directly
      
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
        setJobs(data.jobs || [])
        
        // No AI message for job search - just show results directly
        
      } catch (error) {
        console.error('Job search error:', error)
        setError('Failed to fetch jobs. Please try again.')
        // No error message for job search - just show error state
      } finally {
        setIsLoading(false)
      }
      return
    }

    if (selectedTab === 'career-analytics') {
      // Handle career analytics on the same page
      const resumeText = inputText.trim()
      
      if (!resumeText) return
      
      setIsLoading(true)
      setError('')
      setUploadStatus('')
      
      try {
        const response = await fetch('http://localhost:8000/api/analytics/resume', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ resume_text: resumeText }),
        })

        if (!response.ok) {
          throw new Error('Failed to analyze resume')
        }

        const data = await response.json()
        setCareerAnalysis(data)
        setInputText('') // Clear the input after successful analysis
      } catch (error) {
        console.error('Career analytics error:', error)
        setError('Failed to analyze your resume. Please try again.')
      } finally {
        setIsLoading(false)
      }
      return
    }

    if (selectedTab === 'ai-tools') {
      // Handle AI Tools with chat-style approach
      const query = inputText.trim()
      
      if (!query || isLoading) return
      
      // Add user message
      const userMessage: Message = {
        id: Date.now(),
        text: `I need AI tools for: ${query}`,
        isUser: true
      }
      setMessages(prev => [...prev, userMessage])
      
      setIsLoading(true)
      setError('')
      
      try {
        const response = await fetch('http://localhost:8000/api/ai-tools', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            query: query
          }),
        })

        if (!response.ok) {
          throw new Error('Failed to get AI tools recommendations')
        }

        const data = await response.json()
        
        // Add AI response as a message
        const aiMessage: Message = {
          id: Date.now() + 1,
          text: data.response,
          isUser: false
        }
        setMessages(prev => [...prev, aiMessage])
        setInputText('')
      } catch (error) {
        console.error('AI Tools search error:', error)
        setError('Failed to get AI tools recommendations. Please try again.')
      } finally {
        setIsLoading(false)
      }
      return
    }

    // For other tabs, navigate with parameters
    const params = new URLSearchParams()
    params.set('query', inputText.trim())
    if (showLocationField && location.trim()) {
      params.set('location', location.trim())
    }

    router.push(`/${selectedTab}?${params.toString()}`)
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setSelectedFile(file)
    setIsUploading(true)
    setUploadStatus('Uploading file...')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:8000/api/analytics/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to upload file')
      }

      const data = await response.json()
      setInputText(data.resume_text)
      setUploadStatus('File uploaded successfully!')
    } catch (error) {
      console.error('Upload error:', error)
      setUploadStatus('Failed to upload file. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  if (!isClient) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">

      {/* Simple Job Search Form - At top when results are loaded */}
      {selectedTab === 'job-search' && jobs.length > 0 && (
        <div className="bg-white border-b border-gray-200 px-4 py-4 w-full">
          <div className="max-w-4xl mx-auto flex gap-4">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Job title"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={isLoading}
            />
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Location (optional)"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={isLoading}
            />
            <button
              onClick={handleSubmit}
              disabled={!inputText.trim() || isLoading}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Search
            </button>
          </div>
        </div>
      )}

      {/* Chat Messages - Show when there are messages and not on job search */}
      {messages.length > 0 && selectedTab !== 'job-search' && (
        <div className="flex-1 max-w-4xl mx-auto px-4 py-8 w-full">
          <div className="space-y-6">
            {messages.map((message) => (
              <div key={message.id}>
                {message.isUser ? (
                  <div className="text-right mb-4">
                    <div className="inline-block bg-purple-600 text-white px-4 py-2 rounded-lg">
                      {message.text}
                    </div>
                    {/* Show thinking indicator after the last user message */}
                    {isLoading && message.id === messages[messages.length - 1]?.id && (
                      <div className="mt-3 text-right">
                        <div className="inline-flex items-center space-x-2 text-gray-500 text-sm">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                          <span>Thinking...</span>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-gray-50 rounded-2xl border border-gray-200 p-6 mb-6">
                    {selectedTab === 'ai-tools' ? formatAIToolsResponse(message.text) : formatPerplexityResponse(message.text)}

                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-8 pt-6 border-t border-gray-200">
                        <h4 className="text-sm font-semibold text-gray-600 mb-4 flex items-center">
                          Sources
                          <span className="ml-2 text-purple-400">→</span>
                        </h4>
                        <ul className="list-none p-0 m-0 space-y-2">
                          {message.sources.map((source, idx) => (
                            <li key={idx}>
                              <a
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:text-blue-800 text-sm flex items-start"
                              >
                                <span className="text-gray-500 mr-2">{idx + 1}.</span>
                                {source.title}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Market Data */}
                    {message.marketData && !message.marketData.error && (message.marketData.adzuna_jobs_count || message.marketData.adzuna_average_salary) && (
                      <div className="mt-8 pt-6 border-t border-gray-200">
                        <h4 className="text-sm font-semibold text-gray-600 mb-4 flex items-center">
                          Market Data
                          <span className="ml-2 text-purple-400">→</span>
                        </h4>
                        <p className="text-gray-700 text-sm">
                          **Total Jobs:** {message.marketData.adzuna_jobs_count?.toLocaleString() || 'N/A'}
                        </p>
                        <p className="text-gray-700 text-sm">
                          **Average Salary:** {message.marketData.adzuna_average_salary ? `${message.marketData.adzuna_salary_currency || '$'}${message.marketData.adzuna_average_salary.toLocaleString()}` : 'N/A'}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Job Results - Show when there are jobs */}
      {selectedTab === 'job-search' && jobs.length > 0 && (
        <div className="max-w-4xl mx-auto px-4 py-8 w-full">
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
                    {(job.salary_min || job.salary_max) && (
                      <p className="text-green-600 font-medium mb-3">
                        {job.salary_min && job.salary_max 
                          ? `$${job.salary_min.toLocaleString()} - $${job.salary_max.toLocaleString()}`
                          : job.salary_min 
                          ? `$${job.salary_min.toLocaleString()}+`
                          : `Up to $${job.salary_max?.toLocaleString()}`
                        }
                      </p>
                    )}
                  </div>
                  <div className="text-purple-600 text-sm font-medium">
                    View Details →
                  </div>
                </div>
                
                <p className="text-gray-700 leading-relaxed">
                  {job.description.length > 200 
                    ? job.description.substring(0, 200) + '...'
                    : job.description
                  }
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
        </div>
      )}

      {/* Simple Career Analytics Form - Show when there are results */}
      {selectedTab === 'career-analytics' && careerAnalysis && (
        <div className="bg-white border-b border-gray-200 px-4 py-4 w-full">
          <div className="max-w-3xl mx-auto">
            <div className="bg-gray-50 rounded-2xl border border-gray-200 shadow-lg overflow-hidden">
              <div className="p-4">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Paste or upload your resume"
                  className="w-full bg-transparent text-lg text-gray-900 placeholder-gray-400 focus:outline-none"
                  disabled={isLoading}
                />
              </div>
              <div className="px-4 pb-4">
                <button
                  onClick={handleSubmit}
                  disabled={isLoading || !inputText.trim()}
                  className="w-full px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium hover:from-purple-700 hover:to-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Analyzing...' : 'Analyze Resume'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Career Analytics Results - Show when there's analysis */}
      {selectedTab === 'career-analytics' && careerAnalysis && (
        <div className="max-w-6xl mx-auto px-4 py-8 w-full">
          <div className="space-y-6">
            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl p-6 border border-purple-200">
                <h3 className="text-lg font-semibold text-purple-800 mb-2">Experience Level</h3>
                <p className="text-2xl font-bold text-purple-900">{careerAnalysis.experience_years} years</p>
                <p className="text-purple-700 text-sm">{careerAnalysis.career_level}</p>
              </div>
              
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl p-6 border border-green-200">
                <h3 className="text-lg font-semibold text-green-800 mb-2">Current Market Value</h3>
                <p className="text-xl font-bold text-green-900">${careerAnalysis.market_value.estimated_salary_min.toLocaleString()} - ${careerAnalysis.market_value.estimated_salary_max.toLocaleString()}</p>
                <p className="text-green-700 text-sm">Growth: {careerAnalysis.market_value.growth_potential}</p>
              </div>
              
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl p-6 border border-blue-200">
                <h3 className="text-lg font-semibold text-blue-800 mb-2">Salary Range</h3>
                <p className="text-xl font-bold text-blue-900">{careerAnalysis.salary_insights.current_range}</p>
                <p className="text-blue-700 text-sm">Next Level: {careerAnalysis.salary_insights.next_level_range}</p>
              </div>
            </div>

            {/* Skills Analysis */}
            <div className="bg-gray-50 rounded-2xl p-6 border border-gray-200">
              <h3 className="text-2xl font-semibold mb-6 text-gray-900">Skills Analysis</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div>
                  <h4 className="text-lg font-semibold mb-4 text-green-600">Your Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {careerAnalysis.skills.map((skill, index) => (
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
                    {careerAnalysis.skill_gaps.map((gap, index) => (
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
                {careerAnalysis.recommendations.map((rec, index) => (
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
                    {careerAnalysis.industry_insights.trending_skills.map((skill, index) => (
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
                    {careerAnalysis.industry_insights.growth_areas.map((area, index) => (
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
                    <div className={`w-3 h-3 rounded-full ${careerAnalysis.industry_insights.remote_opportunities === 'High' ? 'bg-green-600' : 'bg-yellow-500'}`}></div>
                    <span className="text-gray-700">{careerAnalysis.industry_insights.remote_opportunities}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}



      {/* Status Messages */}
      {uploadStatus && (
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="bg-blue-100 border border-blue-300 rounded-lg p-4">
            <p className="text-blue-700">{uploadStatus}</p>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="bg-red-100 border border-red-300 rounded-lg p-4">
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Main Landing Page Form - For all other cases */}
      {!(selectedTab === 'job-search' && jobs.length > 0) && !(selectedTab === 'career-analytics' && careerAnalysis) && (
        <div className={`${messages.length > 0 && (selectedTab === 'chat' || selectedTab === 'ai-tools') ? 'mt-auto flex flex-col items-center' : 'flex-1 flex flex-col items-center justify-center'} px-4 py-8 w-full`}>
          {/* Search Box Container - Always centered */}
          <div className="w-full max-w-3xl">
            <div className="relative">
              <div className="bg-gray-50 rounded-2xl border border-gray-200 shadow-2xl overflow-hidden">
                {/* Main Input */}
                <div className="p-6">
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={getPlaceholder()}
                    className="w-full bg-transparent text-xl text-gray-900 placeholder-gray-400 focus:outline-none"
                    disabled={isLoading}
                  />
                </div>

                {/* Additional Fields */}
                {showLocationField && (
                  <div className="border-t border-gray-200 p-6">
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="Location (optional)"
                      className="w-full bg-transparent text-xl text-gray-900 placeholder-gray-400 focus:outline-none"
                      disabled={isLoading}
                    />
                  </div>
                )}

                {showUploadFile && (
                  <div className="border-t border-gray-200 p-6 bg-gray-100">
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                      <p className="text-gray-500 mb-3">Or upload your resume</p>
                      <input
                        type="file"
                        accept=".pdf,.doc,.docx,.txt"
                        onChange={handleFileUpload}
                        className="block mx-auto text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-purple-600 file:text-white hover:file:bg-purple-700"
                        disabled={isUploading}
                      />
                      {selectedFile && (
                        <p className="text-sm text-gray-600 mt-2">
                          📄 Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Submit Button */}
                <div className="p-6 pt-0">
                  <button
                    onClick={handleSubmit}
                    disabled={!inputText.trim() || isLoading}
                    className="w-full py-4 px-6 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-medium hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
                    style={{ 
                      opacity: (!inputText.trim() || isLoading) ? 0.5 : 1,
                      cursor: (!inputText.trim() || isLoading) ? 'not-allowed' : 'pointer'
                    }}
                  >
                    {selectedTab === 'job-search' ? 'Get' : selectedTab === 'land-job' ? 'Next' : selectedTab === 'career-analytics' ? 'Analyze' : selectedTab === 'ai-tools' ? 'Search' : 'Ask'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Tab Chips - Show when no messages */}
          {messages.length === 0 && (
            <div className="flex flex-wrap justify-center gap-3 mt-8 w-full">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => handleTabSelect(tab.id)}
                  className={`px-6 py-3 rounded-full text-sm font-medium transition-all duration-200 ${
                    selectedTab === tab.id
                      ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/25'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border border-gray-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}