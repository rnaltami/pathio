'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { API_URL } from '../../config';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

function ChatContent() {
  const searchParams = useSearchParams();
  const task = searchParams.get('task');
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // If there's a specific task, start the conversation
    if (task) {
      setMessages([
        {
          role: 'assistant',
          content: `I'll help you with this task: "${task}"\n\nLet me break down how to approach this step-by-step. What specific aspect would you like guidance on first?`
        }
      ]);
    } else {
      // General career guidance
      setMessages([
        {
          role: 'assistant',
          content: `Hi! I'm your career coach. I can help you with:\n\n• Job search strategies\n• Resume and cover letter tips\n• Interview preparation\n• Career transitions\n• Skill development\n\nWhat would you like to work on today?`
        }
      ]);
    }
  }, [task]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message
    const newMessages = [...messages, { role: 'user' as const, content: userMessage }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/coach`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: newMessages.map(m => ({ role: m.role, content: m.content })),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      // Add assistant response
      setMessages([...newMessages, { role: 'assistant', content: data.reply }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages([...newMessages, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-white">
      <div className="max-w-[680px] mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-8">
          <a href="/">
            <h1 className="text-3xl font-normal text-[#303030] tracking-tight cursor-pointer hover:opacity-70 transition-opacity">
              pathio
            </h1>
          </a>
        </header>

        {/* Title */}
        <div className="mb-6">
          <h2 className="text-xl font-medium text-[#202020] mb-2">
            {task ? 'Task Guidance' : 'Career Coach'}
          </h2>
          <p className="text-[0.9rem] text-[#707070]">
            {task ? 'Get step-by-step help completing this task' : 'Ask me anything about your career'}
          </p>
        </div>

        {/* Messages */}
        <div className="mb-6 space-y-4">
          {messages.map((msg, idx) => (
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
          
          {loading && (
            <div className="mr-12 bg-white border border-[#E0E0E0] p-4 rounded-lg">
              <p className="text-[0.85rem] text-[#707070]">Thinking...</p>
            </div>
          )}
        </div>

        {/* Input Form */}
        <form onSubmit={handleSend} className="sticky bottom-8">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything..."
              className="w-full px-4 py-3 text-[0.9rem] border border-[#E0E0E0] rounded-lg focus:outline-none focus:border-[#E0E0E0] pr-20"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 text-[0.85rem] bg-[#2563eb] text-white rounded-md hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </form>

        {/* Back link */}
        {task && (
          <div className="mt-6 text-center">
            <a
              href="/results"
              className="text-[0.85rem] text-[#707070] hover:opacity-70 transition-opacity"
            >
              ← Back to results
            </a>
          </div>
        )}
      </div>
    </main>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-[0.9rem] text-[#707070]">Loading...</div>
      </main>
    }>
      <ChatContent />
    </Suspense>
  );
}

