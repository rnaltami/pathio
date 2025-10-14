'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { API_URL } from '../../config';

interface TailoredResults {
  tailored_resume_md: string;
  cover_letter_md: string;
  what_changed_md: string;
  llm_ok: boolean;
  error: string | null;
  insights: {
    engine: string;
    match_score: number;
    missing_keywords: string[];
    present_keywords: string[];
    ats_flags: string[];
    do_now: string[];
    do_long: string[];
  };
}

export default function ResultsPage() {
  const router = useRouter();
  const [results, setResults] = useState<TailoredResults | null>(null);
  const [originalResume, setOriginalResume] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'resume' | 'cover' | 'changes' | 'tasks'>('resume');
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<Array<{role: string, content: string}>>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatInput, setChatInput] = useState('');

  useEffect(() => {
    // Load results from localStorage
    const savedResults = localStorage.getItem('tailoredResults');
    if (savedResults) {
      const data = JSON.parse(savedResults);
      console.log('Loaded results:', data);
      console.log('Tailored resume:', data.tailored_resume_md);
      console.log('Cover letter:', data.cover_letter_md);
      console.log('What changed:', data.what_changed_md);
      setResults(data);
      // Store original resume for export
      setOriginalResume(data.tailored_resume_md);
    } else {
      // No results, redirect to home
      router.push('/');
    }
  }, [router]);

  const handleShowMeHow = async (task: string) => {
    setActiveChat(task);
    const initialMessages = [{
      role: 'user',
      content: `How do I complete this task: ${task}`
    }];
    setChatMessages(initialMessages);
    setChatLoading(true);

    try {
      const response = await fetch(`${API_URL}/coach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: 'You are a helpful career coach. Provide specific, actionable guidance.' },
            ...initialMessages
          ]
        })
      });

      const data = await response.json();
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply || 'Sorry, I could not generate a response.'
      }]);
    } catch (error) {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error. Please try again.'
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleChatSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userMessage = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatLoading(true);

    try {
      const response = await fetch(`${API_URL}/coach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: 'You are a helpful career coach. Provide specific, actionable guidance.' },
            ...chatMessages,
            userMessage
          ]
        })
      });

      const data = await response.json();
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply || 'Sorry, I could not generate a response.'
      }]);
    } catch (error) {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error. Please try again.'
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleExport = async (type: 'resume' | 'cover') => {
    if (!results) return;

    try {
      const contentToExport = type === 'resume' 
        ? (originalResume || results.tailored_resume_md)
        : results.cover_letter_md;
      
      console.log('Exporting:', type);
      console.log('Content length:', contentToExport.length);
      console.log('First 200 chars:', contentToExport.substring(0, 200));

      const response = await fetch(`${API_URL}/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tailored_resume_md: type === 'resume' ? contentToExport : '',
          cover_letter_md: type === 'cover' ? contentToExport : '',
          which: type,
        }),
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `pathio_${type}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export. Please try again.');
    }
  };

  if (!results) {
    return (
      <main className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-[0.9rem] text-[#707070]">Loading...</div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-white">
      <div className="max-w-[720px] mx-auto px-4 pt-16 pb-8">
        {/* Header */}
        <header className="text-center mb-16">
          <a href="/">
            <h1 className="text-[2rem] font-light text-[#202020] tracking-tight cursor-pointer hover:opacity-60 transition-opacity">
              pathio
            </h1>
          </a>
        </header>

        {/* Back Button */}
        <button
          onClick={() => router.push('/')}
          className="mb-8 text-[0.85rem] text-[#909090] hover:text-[#505050] transition-colors"
        >
          ← Back
        </button>

        {/* Tabs - Minimal style */}
        <div className="mb-10">
          <div className="flex gap-4 overflow-x-auto border-b border-[#F0F0F0]">
            <button
              onClick={() => {
                setActiveTab('resume');
                setActiveChat(null);
              }}
              className={`pb-3 text-[0.85rem] transition-colors whitespace-nowrap ${
                activeTab === 'resume'
                  ? 'text-[#202020] border-b-2 border-[#202020]'
                  : 'text-[#909090] hover:text-[#505050]'
              }`}
            >
              Resume
            </button>
            <button
              onClick={() => {
                setActiveTab('cover');
                setActiveChat(null);
              }}
              className={`pb-3 text-[0.85rem] transition-colors whitespace-nowrap ${
                activeTab === 'cover'
                  ? 'text-[#202020] border-b-2 border-[#202020]'
                  : 'text-[#909090] hover:text-[#505050]'
              }`}
            >
              Cover Letter
            </button>
            <button
              onClick={() => {
                setActiveTab('changes');
                setActiveChat(null);
              }}
              className={`pb-3 text-[0.85rem] transition-colors whitespace-nowrap ${
                activeTab === 'changes'
                  ? 'text-[#202020] border-b-2 border-[#202020]'
                  : 'text-[#909090] hover:text-[#505050]'
              }`}
            >
              Changes
            </button>
            <button
              onClick={() => {
                setActiveTab('tasks');
                setActiveChat(null);
              }}
              className={`pb-3 text-[0.85rem] transition-colors whitespace-nowrap ${
                activeTab === 'tasks'
                  ? 'text-[#202020] border-b-2 border-[#202020]'
                  : 'text-[#909090] hover:text-[#505050]'
              }`}
            >
              Stand Out
            </button>
          </div>
        </div>

        {/* Content Display */}
        <div className="mb-8">
          {(activeTab === 'resume' || activeTab === 'cover' || activeTab === 'changes') && (
            <div className="py-4">
              <pre className="whitespace-pre-wrap text-[0.85rem] text-[#303030] font-sans leading-relaxed">
                {activeTab === 'resume' && results.tailored_resume_md
                  .replace(/###\s*/g, '')
                  .replace(/##\s*/g, '')
                  .replace(/#\s*/g, '')
                  .replace(/\*\*/g, '')
                  .replace(/\*/g, '')}
                {activeTab === 'cover' && results.cover_letter_md
                  .replace(/###\s*/g, '')
                  .replace(/##\s*/g, '')
                  .replace(/#\s*/g, '')
                  .replace(/\*\*/g, '')
                  .replace(/\*/g, '')}
                {activeTab === 'changes' && results.what_changed_md
                  .replace(/###\s*/g, '')
                  .replace(/##\s*/g, '')
                  .replace(/#\s*/g, '')
                  .replace(/\*\*/g, '')
                  .replace(/\*/g, '')}
              </pre>
            </div>
          )}

          {activeTab === 'tasks' && results.insights && (
            <div className="py-4 space-y-10">
              {/* Intro - Minimal */}
              <p className="text-[0.9rem] text-[#606060] leading-relaxed">
                Complete these tasks to strengthen your application and stand out from other candidates.
              </p>

              {/* Do Now Tasks */}
              {results.insights.do_now && results.insights.do_now.length > 0 && (
                <div>
                  <h3 className="text-[0.95rem] font-normal text-[#202020] mb-5">
                    Do today (1-4 hours)
                  </h3>
                  <ul className="space-y-5">
                    {results.insights.do_now.map((task, idx) => (
                      <li key={idx} className="pl-5 border-l-2 border-[#F0F0F0]">
                        <div className="text-[0.9rem] text-[#303030] mb-2 leading-relaxed">
                          {task}
                        </div>
                        <button
                          onClick={() => handleShowMeHow(task)}
                          className="text-[0.8rem] text-[#2563eb] hover:text-[#1a4fd6] transition-colors"
                        >
                          Show me how →
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Long-term Tasks */}
              {results.insights.do_long && results.insights.do_long.length > 0 && (
                <div>
                  <h3 className="text-[0.95rem] font-normal text-[#202020] mb-2">
                    Do this month (1-4 weeks)
                  </h3>
                  <p className="text-[0.8rem] text-[#909090] mb-5">
                    These will significantly boost your profile
                  </p>
                  <ul className="space-y-5">
                    {results.insights.do_long.map((task, idx) => (
                      <li key={idx} className="pl-5 border-l-2 border-[#F0F0F0]">
                        <div className="text-[0.9rem] text-[#303030] mb-2 leading-relaxed">
                          {task}
                        </div>
                        <button
                          onClick={() => handleShowMeHow(task)}
                          className="text-[0.8rem] text-[#2563eb] hover:text-[#1a4fd6] transition-colors"
                        >
                          Show me how →
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        {(activeTab === 'resume' || activeTab === 'cover') && (
          <button
            onClick={() => handleExport(activeTab)}
            className="px-6 py-3 text-[0.9rem] bg-[#202020] text-white rounded-full hover:opacity-80 transition-opacity"
          >
            Download {activeTab === 'resume' ? 'resume' : 'cover letter'}
          </button>
        )}

        {/* Inline Chat Section */}
        {activeChat && (
          <div className="mt-12 pt-10 border-t border-[#F0F0F0]">
            <div className="mb-6">
              <button
                onClick={() => setActiveChat(null)}
                className="text-[0.8rem] text-[#909090] hover:text-[#505050] transition-colors mb-4"
              >
                ← Close
              </button>
              <p className="text-[0.85rem] text-[#606060] leading-relaxed">
                {activeChat}
              </p>
            </div>

            {/* Chat Messages */}
            <div className="space-y-4 mb-6">
              {chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`${
                    msg.role === 'user'
                      ? 'text-right'
                      : ''
                  }`}
                >
                  <div className={`inline-block max-w-[85%] ${
                    msg.role === 'user'
                      ? 'bg-[#F8F8F8] px-4 py-3 rounded-2xl'
                      : ''
                  }`}>
                    <p className="text-[0.85rem] text-[#303030] whitespace-pre-wrap leading-relaxed">
                      {msg.content}
                    </p>
                  </div>
                </div>
              ))}
              
              {chatLoading && (
                <div className="text-[0.85rem] text-[#909090]">Thinking...</div>
              )}
            </div>

            {/* Chat Input */}
            <form onSubmit={handleChatSend} className="relative">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask a follow-up question..."
                disabled={chatLoading}
                className="w-full px-5 py-4 pr-20 text-[0.9rem] border border-[#E0E0E0] rounded-full focus:outline-none focus:border-[#B0B0B0] disabled:opacity-50 transition-colors"
              />
              <button
                type="submit"
                disabled={!chatInput.trim() || chatLoading}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 text-[0.85rem] text-[#606060] hover:text-[#202020] transition-colors disabled:opacity-30"
              >
                Send
              </button>
            </form>
          </div>
        )}
      </div>
    </main>
  );
}

