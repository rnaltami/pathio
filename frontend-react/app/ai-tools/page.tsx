'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { API_URL } from '../../config';
import dynamic from 'next/dynamic';

function AIToolsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams?.get('q') || '';
  
  const [tools, setTools] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputText, setInputText] = useState('');
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (query) {
      searchTools();
    }
  }, [query]);

  const searchTools = async () => {
    setLoading(true);
    try {
      // For now, we'll use a mock response since we don't have an AI tools API yet
      // This would be replaced with actual API call when we implement it
      const mockTools = [
        {
          name: 'ChatGPT',
          description: 'AI assistant for writing, coding, and general tasks',
          category: 'Productivity',
          url: 'https://chat.openai.com',
          pricing: 'Free tier available'
        },
        {
          name: 'Midjourney',
          description: 'AI image generation for creative projects',
          category: 'Design',
          url: 'https://midjourney.com',
          pricing: '$10/month'
        },
        {
          name: 'Notion AI',
          description: 'AI writing assistant integrated into Notion',
          category: 'Writing',
          url: 'https://notion.so',
          pricing: '$8/month'
        }
      ];
      
      // Filter tools based on query
      const filteredTools = mockTools.filter(tool => 
        tool.name.toLowerCase().includes(query.toLowerCase()) ||
        tool.description.toLowerCase().includes(query.toLowerCase()) ||
        tool.category.toLowerCase().includes(query.toLowerCase())
      );
      
      setTools(filteredTools);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    
    router.push(`/ai-tools?q=${encodeURIComponent(inputText)}`);
  };

  if (!isClient) {
    return (
      <main className="min-h-screen bg-white">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-[0.9rem] text-[#707070]">Loading...</div>
        </div>
      </main>
    );
  }

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
          AI Tools for Your Goals
        </h1>

        {/* Search Input */}
        <div className="mb-8">
          <form onSubmit={handleSearch}>
            <div className="w-full" style={{ maxWidth: '680px', margin: '0 auto' }}>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="What do you want to build? (e.g., mobile app, website, content)"
                className="w-full text-[1rem] border-2 border-[#D8B4FE] focus:outline-none focus:border-[#A78BFA] transition-colors resize-none font-medium"
                style={{ borderRadius: '20px', padding: '18px 22px', background: '#FAFAF9' }}
                rows={3}
              />
              <div className="flex justify-center" style={{ marginTop: '8px' }}>
                <button
                  type="submit"
                  className="text-[0.85rem] hover:opacity-90 transition-opacity"
                  style={{
                    background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                    padding: '12px 36px',
                    borderRadius: '24px',
                    color: '#FFFFFF',
                    fontWeight: 'bold',
                    border: 'none',
                    cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)'
                  }}
                >
                  Find Tools →
                </button>
              </div>
            </div>
          </form>
        </div>

        {loading && (
          <div className="text-center text-[0.9rem] text-[#707070] mb-6">
            Finding AI tools...
          </div>
        )}

        {tools.length > 0 && (
          <>
            <div className="mb-4 text-[0.9rem] text-[#707070] text-center">
              {tools.length} AI tools found for "{query}"
            </div>

            {/* Tools Grid */}
            <div className="space-y-4">
              {tools.map((tool, index) => (
                <div 
                  key={index}
                  className="border border-[#E0E0E0] rounded-lg p-6 hover:shadow-md transition-shadow"
                  style={{ 
                    background: 'linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%)',
                    border: '2px solid #E2E8F0'
                  }}
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-[1.1rem] font-bold text-[#313338]">{tool.name}</h3>
                    <span className="text-[0.8rem] bg-[#7C3AED] text-white px-2 py-1 rounded-full">
                      {tool.category}
                    </span>
                  </div>
                  
                  <p className="text-[0.9rem] text-[#505050] mb-3 leading-relaxed">
                    {tool.description}
                  </p>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-[0.85rem] font-medium text-[#7C3AED]">
                      {tool.pricing}
                    </span>
                    <a
                      href={tool.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 text-[0.85rem] bg-[#7C3AED] text-white rounded-lg hover:opacity-90 transition-opacity"
                    >
                      Try Tool →
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {!loading && query && tools.length === 0 && (
          <div className="text-center text-[0.9rem] text-[#707070] py-8">
            No AI tools found for "{query}". Try a different search term.
          </div>
        )}

        {!query && (
          <div className="text-center text-[0.9rem] text-[#707070] py-8">
            Search for AI tools to help you build something amazing!
          </div>
        )}
      </div>
    </main>
  );
}

export default dynamic(() => Promise.resolve(AIToolsPage), { ssr: false });
