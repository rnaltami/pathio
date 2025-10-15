'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { API_URL } from '../../config';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialQuery) {
      handleInitialQuery();
    }
  }, [initialQuery]);

  const handleInitialQuery = async () => {
    if (!initialQuery.trim()) return;
    
    setLoading(true);
    setChatMessages([{ role: 'user', content: initialQuery }]);
    
    try {
      const response = await fetch(`${API_URL}/coach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: initialQuery
        })
      });
      const data = await response.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (error) {
      console.error('Error:', error);
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const userMessage = { role: 'user' as const, content: inputText };
    setChatMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/coach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: inputText
        })
      });
      const data = await response.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (error) {
      console.error('Error:', error);
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
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
        
        <h1 className="text-[1.6rem] text-center mb-6" style={{ fontWeight: '800', color: '#0A0A0A' }}>
          Career Chat
        </h1>

        {/* Chat Messages */}
        <div className="space-y-6 mb-8">
          {chatMessages.map((message, index) => (
            <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div 
                className={`max-w-[80%] p-4 rounded-lg ${
                  message.role === 'user' 
                    ? 'bg-[#7C3AED] text-white' 
                    : 'bg-[#F8FAFC] border border-[#E5E5E5] text-[#374151]'
                }`}
              >
                <div 
                  className="text-[0.9rem] leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: message.content.replace(/\n/g, '<br>') }}
                />
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-[#F8FAFC] border border-[#E5E5E5] p-4 rounded-lg">
                <div className="text-[0.9rem] text-[#707070]">
                  Thinking...
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Fixed Bottom Chat Input */}
        <div style={{ position: 'fixed', bottom: '0', left: '0', right: '0', background: '#FFFFFF', borderTop: '1px solid #E5E5E5', boxShadow: '0 -4px 20px rgba(0,0,0,0.08)', zIndex: 9999, padding: '20px 0' }}>
          <div className="max-w-[720px] mx-auto px-4 w-full">
            <div className="flex flex-col items-center gap-4">
              <div className="w-full" style={{ maxWidth: '680px' }}>
                <form onSubmit={handleSubmit}>
                  <div style={{ marginTop: '8px', paddingLeft: '4px', paddingRight: '4px', gap: '12px' }} className="flex justify-center items-center">
                    <button
                      type="submit"
                      disabled={loading || !inputText.trim()}
                      className="text-[0.85rem] hover:opacity-90 transition-opacity"
                      style={{
                        background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                        padding: '12px 36px',
                        borderRadius: '24px',
                        color: '#FFFFFF',
                        fontWeight: 'bold',
                        border: 'none',
                        cursor: loading || !inputText.trim() ? 'not-allowed' : 'pointer',
                        boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)',
                        opacity: loading || !inputText.trim() ? 0.6 : 1,
                        fontSize: '0.85rem',
                        fontFamily: 'inherit',
                        lineHeight: '1',
                        textAlign: 'center',
                        textDecoration: 'none',
                        display: 'inline-block',
                        transition: 'opacity 0.2s'
                      }}
                    >
                      →
                    </button>
                  </div>
                  <textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Follow up..."
                    className="w-full text-[0.9rem] resize-none"
                    style={{
                      background: '#FAFAF9',
                      padding: '18px 22px',
                      border: '2px solid #D8B4FE',
                      borderRadius: '20px',
                      fontWeight: '500',
                      minHeight: '60px',
                      outline: 'currentcolor',
                      transition: 'border-color 0.2s',
                      opacity: 1
                    }}
                    rows={2}
                  />
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}