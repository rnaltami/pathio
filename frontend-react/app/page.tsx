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

export default function Home() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [selectedTab, setSelectedTab] = useState('chat')
  const [inputText, setInputText] = useState('')
  const [location, setLocation] = useState('')
  const [isRemote, setIsRemote] = useState(false)
  const [isClient, setIsClient] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)

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
      setIsRemote(false)
      setMessages([])
    }
  }, [searchParams])

  const tabs = [
    { id: 'chat', label: 'Chat', placeholder: "Let's talk about the future" },
    { id: 'job-search', label: 'Job Search', placeholder: "Let's find your next role — enter a job title or keyword." },
    { id: 'land-job', label: 'Help Me Apply', placeholder: "Let's get you ready — paste the job listing you want to apply to." },
    { id: 'career-analytics', label: 'My Career Analytics', placeholder: "Let's analyze your path — paste or upload your resume." },
    { id: 'ai-tools', label: 'AI Tools', placeholder: "Let's find AI tools to help you build, create, or automate." }
  ]

  const getPlaceholder = () => {
    const tab = tabs.find(t => t.id === selectedTab)
    return tab?.placeholder || "Let's talk about the future"
  }

  const showLocationField = selectedTab === 'job-search'
  const showUploadFile = selectedTab === 'career-analytics'

  const handleTabSelect = (tabId: string) => {
    setSelectedTab(tabId)
    setInputText('')
    setLocation('')
    setIsRemote(false)
    if (tabId !== 'chat') {
      setMessages([])
    }
  }

  const formatPerplexityResponse = (text: string) => {
    // Split by section headers (both **Header** and ### Header formats)
    const sections = text.split(/(\*\*[^*]+\*\*|### [^\n]+)/g)
    const formatted = []
    
    for (let i = 0; i < sections.length; i++) {
      const section = sections[i].trim()
      if (!section) continue
      
      if (section.startsWith('**') && section.endsWith('**')) {
        // This is a header
        const headerText = section.replace(/\*\*/g, '')
        formatted.push(
          <div key={i} className="font-bold text-xl text-purple-400 mb-3 mt-6 first:mt-0">
            {headerText}
          </div>
        )
      } else if (section.startsWith('### ')) {
        // This is a subheader
        const headerText = section.replace(/### /g, '')
        formatted.push(
          <div key={i} className="font-semibold text-lg text-blue-400 mb-2 mt-4">
            {headerText}
          </div>
        )
      } else {
        // This is content
        const lines = section.split('\n').filter(line => line.trim())
        lines.forEach((line, lineIndex) => {
          const trimmedLine = line.trim()
          if (trimmedLine.startsWith('- ')) {
            // Bullet point
            formatted.push(
              <div key={`${i}-${lineIndex}`} className="flex items-start mb-2 ml-4">
                <span className="text-purple-400 mr-3 mt-1 text-sm">•</span>
                <span className="text-gray-300 text-sm leading-relaxed">{trimmedLine.replace('- ', '')}</span>
              </div>
            )
          } else if (trimmedLine.startsWith('• ')) {
            // Alternative bullet point
            formatted.push(
              <div key={`${i}-${lineIndex}`} className="flex items-start mb-2 ml-4">
                <span className="text-purple-400 mr-3 mt-1 text-sm">•</span>
                <span className="text-gray-300 text-sm leading-relaxed">{trimmedLine.replace('• ', '')}</span>
              </div>
            )
          } else if (trimmedLine.match(/^\d+\./)) {
            // Numbered list
            formatted.push(
              <div key={`${i}-${lineIndex}`} className="flex items-start mb-2 ml-4">
                <span className="text-purple-400 mr-3 mt-1 text-sm font-medium">{trimmedLine.split('.')[0]}.</span>
                <span className="text-gray-300 text-sm leading-relaxed">{trimmedLine.replace(/^\d+\.\s*/, '')}</span>
              </div>
            )
          } else if (trimmedLine) {
            // Regular paragraph
            formatted.push(
              <div key={`${i}-${lineIndex}`} className="text-gray-300 mb-3 text-sm leading-relaxed">
                {trimmedLine}
              </div>
            )
          }
        })
      }
    }
    
    return formatted.length > 0 ? formatted : [<div key="fallback" className="text-gray-300">{text}</div>]
  }

  const handleSubmit = async () => {
    if (!inputText.trim()) return

    if (selectedTab === 'chat') {
      // Add user message
      const userMessage: Message = {
        id: Date.now(),
        text: inputText,
        isUser: true
      }
      setMessages(prev => [...prev, userMessage])
      setInputText('')
      setIsLoading(true)

      try {
        const response = await fetch('http://localhost:8000/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: inputText }),
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

    // For other tabs, navigate with parameters
    const params = new URLSearchParams()
    params.set('query', inputText.trim())
    if (showLocationField && location.trim()) {
      params.set('location', location.trim())
    }
    if (showLocationField && isRemote) {
      params.set('remote', 'true')
    }

    router.push(`/${selectedTab}?${params.toString()}`)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  if (!isClient) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-4xl mx-auto px-4 py-16">
        {/* Perplexity-style centered content */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            What would you like to do today?
          </h1>
          <p className="text-xl text-gray-400 mb-12">
            Choose your path and let's get started
          </p>
        </div>

        {/* Tab Chips - Perplexity style */}
        <div className="flex flex-wrap justify-center gap-3 mb-12">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabSelect(tab.id)}
              className={`px-6 py-3 rounded-full text-sm font-medium transition-all duration-200 ${
                selectedTab === tab.id
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/25'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Main Search Box - Perplexity style */}
        <div className="max-w-3xl mx-auto">
          <div className="relative">
            <div className="bg-gray-900 rounded-2xl border border-gray-700 shadow-2xl overflow-hidden">
              {/* Main Input */}
              <div className="p-6">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={getPlaceholder()}
                  className="w-full bg-transparent text-xl text-white placeholder-gray-400 focus:outline-none"
                  disabled={isLoading}
                />
              </div>

              {/* Additional Fields */}
              {(showLocationField || showUploadFile) && (
                <div className="border-t border-gray-700 p-6 bg-gray-800/50">
                  {showLocationField && (
                    <div className="flex gap-4 mb-4">
                      <input
                        type="text"
                        value={location}
                        onChange={(e) => setLocation(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Location (optional)"
                        className="flex-1 bg-gray-700 text-white placeholder-gray-400 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                      <label className="flex items-center gap-3 px-4 py-3 bg-gray-700 rounded-lg hover:bg-gray-600 cursor-pointer transition-colors">
                        <input
                          type="checkbox"
                          checked={isRemote}
                          onChange={(e) => setIsRemote(e.target.checked)}
                          className="rounded border-gray-500 bg-gray-700 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-sm text-gray-300">Remote</span>
                      </label>
                    </div>
                  )}

                  {showUploadFile && (
                    <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center hover:border-gray-500 transition-colors">
                      <p className="text-gray-400 mb-3">Or upload your resume</p>
                      <input
                        type="file"
                        accept=".pdf,.doc,.docx"
                        className="block mx-auto text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-purple-600 file:text-white hover:file:bg-purple-700"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Submit Button */}
              <div className="p-6 pt-0">
                <button
                  onClick={handleSubmit}
                  disabled={!inputText.trim() || isLoading}
                  className="w-full py-4 px-6 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-medium hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  {isLoading ? 'Thinking...' : (selectedTab === 'chat' ? 'Ask AI' : 'Get Started')}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Chat Messages */}
        {selectedTab === 'chat' && messages.length > 0 && (
          <div className="max-w-4xl mx-auto mt-12 space-y-6">
            {messages.map((message) => (
              <div key={message.id} className="bg-gray-900 rounded-2xl border border-gray-700 p-6">
                {message.isUser ? (
                  <div className="text-right">
                    <div className="inline-block bg-purple-600 text-white px-4 py-2 rounded-lg">
                      {message.text}
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="prose prose-invert max-w-none">
                      {formatPerplexityResponse(message.text)}
                    </div>
                    
                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-8 pt-6 border-t border-gray-700">
                        <h4 className="text-sm font-semibold text-gray-400 mb-4 flex items-center">
                          <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                          Sources
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {message.sources.map((source, index) => (
                            <a
                              key={index}
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="group flex items-start p-3 rounded-lg bg-gray-800 hover:bg-gray-750 border border-gray-600 hover:border-blue-500/50 transition-all duration-200"
                            >
                              <span className="text-xs font-medium text-blue-400 mr-3 mt-0.5 group-hover:text-blue-300">
                                {index + 1}
                              </span>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm text-gray-300 group-hover:text-white transition-colors line-clamp-2">
                                  {source.title}
                                </p>
                                <p className="text-xs text-gray-500 mt-1 truncate">
                                  {new URL(source.url).hostname}
                                </p>
                              </div>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Market Data */}
                    {message.marketData && !message.marketData.error && (
                      <div className="mt-8 pt-6 border-t border-gray-700">
                        <h4 className="text-sm font-semibold text-gray-400 mb-4 flex items-center">
                          <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                          Live Market Data
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {message.marketData.total_jobs && (
                            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
                              <p className="text-xs text-gray-400 mb-1">Active Positions</p>
                              <p className="text-lg font-semibold text-green-400">{message.marketData.total_jobs.toLocaleString()}</p>
                            </div>
                          )}
                          {message.marketData.salary_info && message.marketData.salary_info.min && (
                            <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
                              <p className="text-xs text-gray-400 mb-1">Salary Range</p>
                              <p className="text-lg font-semibold text-green-400">
                                ${message.marketData.salary_info.min.toLocaleString()} - ${message.marketData.salary_info.max.toLocaleString()}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="bg-gray-900 rounded-2xl border border-gray-700 p-6">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-400"></div>
                  <span className="text-gray-400">Analyzing market data and generating insights...</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}