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
      <div className="max-w-[680px] mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-12">
          <a href="/">
            <h1 className="text-3xl font-normal text-[#303030] tracking-tight cursor-pointer hover:opacity-70 transition-opacity">
              pathio
            </h1>
          </a>
        </header>

        {/* Back Button */}
        <button
          onClick={() => router.push('/')}
          className="mb-6 text-[0.85rem] text-[#707070] hover:text-[#303030] transition-colors flex items-center gap-1"
        >
          ← Back to job search
        </button>

        {/* Title */}
        <div className="mb-8">
          <h2 className="text-xl font-medium text-[#202020] mb-2">
            Your Tailored Application Materials
          </h2>
          <p className="text-[0.9rem] text-[#707070]">
            Review and download your personalized resume and cover letter
          </p>
        </div>


        {/* Tabs */}
        <div className="mb-6 border-b border-[#E0E0E0]">
          <div className="flex gap-6 overflow-x-auto">
            <button
              onClick={() => {
                setActiveTab('resume');
                setActiveChat(null);
              }}
              className={`pb-3 text-[0.9rem] transition-colors whitespace-nowrap ${
                activeTab === 'resume'
                  ? 'text-[#2563eb] border-b-2 border-[#2563eb]'
                  : 'text-[#707070] hover:text-[#303030]'
              }`}
            >
              Tailored Resume
            </button>
            <button
              onClick={() => {
                setActiveTab('cover');
                setActiveChat(null);
              }}
              className={`pb-3 text-[0.9rem] transition-colors whitespace-nowrap ${
                activeTab === 'cover'
                  ? 'text-[#2563eb] border-b-2 border-[#2563eb]'
                  : 'text-[#707070] hover:text-[#303030]'
              }`}
            >
              Cover Letter
            </button>
            <button
              onClick={() => {
                setActiveTab('changes');
                setActiveChat(null);
              }}
              className={`pb-3 text-[0.9rem] transition-colors whitespace-nowrap ${
                activeTab === 'changes'
                  ? 'text-[#2563eb] border-b-2 border-[#2563eb]'
                  : 'text-[#707070] hover:text-[#303030]'
              }`}
            >
              What Changed
            </button>
            <button
              onClick={() => {
                setActiveTab('tasks');
                setActiveChat(null);
              }}
              className={`pb-3 text-[0.9rem] transition-colors whitespace-nowrap ${
                activeTab === 'tasks'
                  ? 'text-[#2563eb] border-b-2 border-[#2563eb]'
                  : 'text-[#707070] hover:text-[#303030]'
              }`}
            >
              How to Stand Out
            </button>
          </div>
        </div>

        {/* Content Display */}
        <div className="mb-6">
          {(activeTab === 'resume' || activeTab === 'cover' || activeTab === 'changes') && (
            <div className="p-6 bg-[#FAFAFA] rounded-lg">
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
            <div className="space-y-6">
              {/* Intro explanation */}
              <div className="p-4 bg-[#F0F7FF] border border-[#D0E7FF] rounded-lg">
                <p className="text-[0.85rem] text-[#303030]">
                  Want to be a stronger candidate? Complete these tasks to improve your chances of landing this role.
                </p>
              </div>

              {/* Do Now Tasks */}
              {results.insights.do_now && results.insights.do_now.length > 0 && (
                <div className="p-6 bg-[#FAFAFA] rounded-lg">
                  <h3 className="text-[0.95rem] font-medium text-[#202020] mb-4">
                    📋 Do Before Applying
                  </h3>
                  <ul className="space-y-4">
                    {results.insights.do_now.map((task, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <span className="text-[#303030] text-[0.85rem] mt-0.5">•</span>
                        <div className="flex-1">
                          <span className="text-[0.85rem] block mb-1 text-[#303030]">
                            {task}
                          </span>
                          <button
                            onClick={() => handleShowMeHow(task)}
                            className="text-[0.8rem] text-[#2563eb] hover:opacity-70 transition-opacity"
                          >
                            Show me how →
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Long-term Tasks */}
              {results.insights.do_long && results.insights.do_long.length > 0 && (
                <div className="p-6 bg-[#FAFAFA] rounded-lg">
                  <h3 className="text-[0.95rem] font-medium text-[#202020] mb-4">
                    🎯 Longer-term Goals
                  </h3>
                  <p className="text-[0.8rem] text-[#707070] mb-4">
                    These take more time but will significantly boost your profile
                  </p>
                  <ul className="space-y-4">
                    {results.insights.do_long.map((task, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <span className="text-[#303030] text-[0.85rem] mt-0.5">•</span>
                        <div className="flex-1">
                          <span className="text-[0.85rem] block mb-1 text-[#303030]">
                            {task}
                          </span>
                          <button
                            onClick={() => handleShowMeHow(task)}
                            className="text-[0.8rem] text-[#2563eb] hover:opacity-70 transition-opacity"
                          >
                            Show me how →
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          {(activeTab === 'resume' || activeTab === 'cover') && (
            <button
              onClick={() => handleExport(activeTab)}
              className="w-full px-4 py-3 text-center text-[0.95rem] bg-[#2563eb] text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              Download {activeTab === 'resume' ? 'Resume' : 'Cover Letter'} (.docx) →
            </button>
          )}
        </div>

        {/* Inline Chat Section */}
        {activeChat && (
          <div className="mt-12 pt-8 border-t border-[#E0E0E0]">
            <div className="mb-6">
              <h3 className="text-[1rem] font-medium text-[#202020] mb-2">
                How to Complete This Task
              </h3>
              <p className="text-[0.85rem] text-[#707070] mb-4">
                {activeChat}
              </p>
              <button
                onClick={() => setActiveChat(null)}
                className="text-[0.8rem] text-[#707070] hover:text-[#303030] transition-colors"
              >
                ← Close
              </button>
            </div>

            {/* Chat Messages */}
            <div className="space-y-4 mb-6">
              {chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`${
                    msg.role === 'user'
                      ? 'ml-12 bg-[#F5F5F5]'
                      : 'mr-12 bg-white border border-[#E0E0E0]'
                  } p-4 rounded-lg`}
                >
                  <p className="text-[0.85rem] text-[#303030] whitespace-pre-wrap leading-relaxed">
                    {msg.content}
                  </p>
                </div>
              ))}
              
              {chatLoading && (
                <div className="mr-12 bg-white border border-[#E0E0E0] p-4 rounded-lg">
                  <p className="text-[0.85rem] text-[#707070]">Thinking...</p>
                </div>
              )}
            </div>

            {/* Chat Input */}
            <form onSubmit={handleChatSend} className="space-y-3">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask a follow-up question..."
                disabled={chatLoading}
                className="w-full px-4 py-3 text-[0.9rem] border border-[#D0D0D0] rounded-lg focus:outline-none focus:border-[#D0D0D0] disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!chatInput.trim() || chatLoading}
                className="w-full px-4 py-2.5 text-[0.9rem] bg-[#2563eb] text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
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

