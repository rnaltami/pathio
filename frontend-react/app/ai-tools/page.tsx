'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface AITool {
  name: string
  description: string
  category: string
  pricing: string
  website: string
  features: string[]
  rating: number
}

interface AIToolSearchResponse {
  tools: AITool[]
  total: number
  category: string
  search_query: string
}

export default function AITools() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('General')
  const [tools, setTools] = useState<AITool[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [categories, setCategories] = useState<string[]>([])
  const [hasSearched, setHasSearched] = useState(false)

  // Load categories on component mount
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/ai-tools/categories')
        if (response.ok) {
          const data = await response.json()
          setCategories(data.categories)
        }
      } catch (err) {
        console.error('Failed to load categories:', err)
      }
    }
    loadCategories()
  }, [])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    setIsLoading(true)
    setError('')
    setHasSearched(true)

    try {
      const response = await fetch('http://localhost:8000/api/ai-tools/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          category: selectedCategory === 'General' ? null : selectedCategory,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to search AI tools')
      }

      const data: AIToolSearchResponse = await response.json()
      setTools(data.tools)
    } catch (err) {
      setError('Failed to search AI tools. Please try again.')
      console.error('Search error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const getPricingColor = (pricing: string) => {
    switch (pricing.toLowerCase()) {
      case 'free':
        return 'bg-green-600/20 text-green-400 border-green-600/30'
      case 'freemium':
        return 'bg-yellow-600/20 text-yellow-400 border-yellow-600/30'
      case 'paid':
        return 'bg-blue-600/20 text-blue-400 border-blue-600/30'
      default:
        return 'bg-gray-600/20 text-gray-400 border-gray-600/30'
    }
  }

  const renderStars = (rating: number) => {
    const stars = []
    const fullStars = Math.floor(rating)
    const hasHalfStar = rating % 1 >= 0.5

    for (let i = 0; i < fullStars; i++) {
      stars.push(<span key={i} className="text-yellow-400">★</span>)
    }
    if (hasHalfStar) {
      stars.push(<span key="half" className="text-yellow-400">☆</span>)
    }
    const emptyStars = 5 - Math.ceil(rating)
    for (let i = 0; i < emptyStars; i++) {
      stars.push(<span key={`empty-${i}`} className="text-gray-600">★</span>)
    }
    return stars
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 pt-20 pb-20">
      <div className="w-full max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-600">
            AI Tools Discovery
          </h1>
          <p className="text-gray-400 text-lg">
            Find the perfect AI tools for your needs with real-time search
          </p>
        </div>

        {/* Search Form */}
        <div className="bg-gray-800 rounded-xl shadow-2xl p-6 mb-8 border border-gray-700">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="What AI tools are you looking for? (e.g., writing, design, coding...)"
                className="flex-1 p-4 rounded-lg bg-gray-700 text-gray-100 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-400"
                disabled={isLoading}
              />
              
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="p-4 rounded-lg bg-gray-700 text-gray-100 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 min-w-[200px]"
                disabled={isLoading}
              >
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>
            
            <button
              type="submit"
              className="w-full md:w-auto px-8 py-4 rounded-lg bg-purple-600 text-white font-semibold hover:bg-purple-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading || !searchQuery.trim()}
            >
              {isLoading ? 'Searching AI Tools...' : 'Search AI Tools'}
            </button>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Results Header */}
        {hasSearched && (
          <div className="mb-6">
            <h2 className="text-2xl font-semibold text-white mb-2">
              {isLoading ? 'Searching...' : `Found ${tools.length} AI Tools`}
            </h2>
            <p className="text-gray-400">
              {isLoading ? 'Discovering the latest AI tools...' : `Results for "${searchQuery}" in ${selectedCategory}`}
            </p>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400 mx-auto mb-4"></div>
            <p className="text-gray-400">Searching for AI tools...</p>
          </div>
        )}

        {/* Tools Grid */}
        {!isLoading && tools.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tools.map((tool, index) => (
              <div
                key={index}
                className="bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-700 hover:border-purple-500/50 transition-colors duration-200"
              >
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-semibold text-white mb-2 hover:text-purple-400 transition-colors">
                    {tool.name}
                  </h3>
                  <div className="flex items-center gap-1">
                    {renderStars(tool.rating)}
                    <span className="text-gray-400 text-sm ml-1">({tool.rating.toFixed(1)})</span>
                  </div>
                </div>
                
                <p className="text-gray-300 mb-4 leading-relaxed">
                  {tool.description}
                </p>
                
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-400 text-sm">Category:</span>
                    <span className="text-purple-400 text-sm font-medium">{tool.category}</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="text-gray-400 text-sm">Pricing:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPricingColor(tool.pricing)}`}>
                      {tool.pricing}
                    </span>
                  </div>
                  
                  {tool.features.length > 0 && (
                    <div>
                      <span className="text-gray-400 text-sm">Features:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {tool.features.map((feature, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded-full"
                          >
                            {feature}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="pt-3 border-t border-gray-700">
                    <a
                      href={tool.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
                    >
                      Visit Website →
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* No Results */}
        {!isLoading && hasSearched && tools.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg mb-4">
              No AI tools found for "{searchQuery}"
            </div>
            <p className="text-gray-600">
              Try different keywords or browse by category
            </p>
          </div>
        )}

        {/* Empty State */}
        {!hasSearched && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg mb-4">
              Discover AI Tools
            </div>
            <p className="text-gray-600">
              Search for AI tools by category or specific needs
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {['writing', 'design', 'coding', 'marketing', 'productivity'].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setSearchQuery(suggestion)}
                  className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors text-sm"
                >
                  {suggestion}
                </button>
              ))}
            </div>
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
