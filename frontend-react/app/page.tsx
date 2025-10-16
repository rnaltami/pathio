'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { API_URL } from '../config';

export default function HomePage() {
  const router = useRouter();
  const [selectedTab, setSelectedTab] = useState<'chat' | 'job-search' | 'land-job' | 'ai-tools'>('chat');
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  const getPlaceholder = () => {
    switch (selectedTab) {
      case 'chat': return 'Ask me anything about your future...';
      case 'job-search': return 'What job are you looking for? (e.g., writer, data scientist)';
      case 'land-job': return 'Paste the job listing here...';
      case 'ai-tools': return 'What do you want to build? (e.g., mobile app, website)';
      default: return 'Ask me anything about your future...';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    setLoading(true);
    
    try {
      switch (selectedTab) {
        case 'chat':
          // Navigate to chat page with the query
          router.push(`/chat?q=${encodeURIComponent(inputText.trim())}`);
          break;
          
        case 'job-search':
          // Navigate to job search page with the query
          router.push(`/job-search?q=${encodeURIComponent(inputText.trim())}`);
          break;
          
        case 'land-job':
          // Navigate to tailor page with the job listing
          router.push(`/tailor?job=${encodeURIComponent(inputText.trim())}`);
          break;
          
        case 'ai-tools':
          // Navigate to AI tools page with the query
          router.push(`/ai-tools?q=${encodeURIComponent(inputText.trim())}`);
          break;
      }
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
        
        {/* Main Input Field */}
        <div className="flex flex-col items-center gap-4">
          <div className="w-full" style={{ maxWidth: '680px' }}>
            <form onSubmit={handleSubmit}>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder={getPlaceholder()}
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
                  {loading ? 'Working...' : '→'}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex flex-col items-center" style={{ marginTop: '34px' }}>
          <div className="flex flex-wrap justify-center" style={{ maxWidth: '680px', gap: '8px' }}>
            <button
              onClick={() => setSelectedTab('chat')}
              className="text-[0.85rem] font-semibold px-5 py-2.5 rounded-xl transition-all"
              style={{ 
                background: selectedTab === 'chat' ? '#7C3AED' : '#F3E8FF', 
                color: selectedTab === 'chat' ? '#FFFFFF' : '#5B21B6' 
              }}
            >
              Chat
            </button>
            <button
              onClick={() => setSelectedTab('job-search')}
              className="text-[0.85rem] font-semibold px-5 py-2.5 rounded-xl transition-all"
              style={{ 
                background: selectedTab === 'job-search' ? '#7C3AED' : '#F3E8FF', 
                color: selectedTab === 'job-search' ? '#FFFFFF' : '#5B21B6' 
              }}
            >
              🔹 Find a job — the old-fashioned kind with paychecks.
            </button>
            <button
              onClick={() => setSelectedTab('land-job')}
              className="text-[0.85rem] font-semibold px-5 py-2.5 rounded-xl transition-all"
              style={{ 
                background: selectedTab === 'land-job' ? '#7C3AED' : '#F3E8FF', 
                color: selectedTab === 'land-job' ? '#FFFFFF' : '#5B21B6' 
              }}
            >
              🔹 I have a job in mind I want to apply to. Help me land it.
            </button>
            <button
              onClick={() => setSelectedTab('ai-tools')}
              className="text-[0.85rem] font-semibold px-5 py-2.5 rounded-xl transition-all"
              style={{ 
                background: selectedTab === 'ai-tools' ? '#7C3AED' : '#F3E8FF', 
                color: selectedTab === 'ai-tools' ? '#FFFFFF' : '#5B21B6' 
              }}
            >
              🔹 I want to do my own thing. Find AI tools to help me.
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}