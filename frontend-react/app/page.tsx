'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { API_URL } from '../config';

interface Job {
  title: string;
  company: string;
  location: string;
  type: string;
  description: string;
  requirements: string[];
  match_score: number;
  source: string;
  url: string;
}

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

type Intent = 'find-job' | 'land-job' | 'ai-tools';

export default function Home() {
  // Core state
  const [intent, setIntent] = useState<Intent>('find-job');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  
  // Job search state
  const [jobs, setJobs] = useState<Job[]>([]);
  const [filter, setFilter] = useState<'all' | 'remote' | 'fulltime' | 'contract'>('all');
  const [locationFilter, setLocationFilter] = useState('');
  const [expandedJobIndex, setExpandedJobIndex] = useState<number | null>(null);
  
  // Tailoring flow state
  const [jobDescription, setJobDescription] = useState('');
  const [resume, setResume] = useState('');
  const [tailoredResults, setTailoredResults] = useState<TailoredResults | null>(null);
  const [tailoredJobTitle, setTailoredJobTitle] = useState('');
  
  // Chat state
  const [chatMessages, setChatMessages] = useState<Array<{role: string, content: string}>>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [coverLetter, setCoverLetter] = useState<string>('');
  const [hasDownloaded, setHasDownloaded] = useState(false);
  
  // Career analytics state
  const [careerAnalytics, setCareerAnalytics] = useState<any>(null);
  const [analyticsChatMessages, setAnalyticsChatMessages] = useState<Array<{role: string, content: string}>>([]);
  const [analyticsChatInput, setAnalyticsChatInput] = useState('');
  const [analyticsChatLoading, setAnalyticsChatLoading] = useState(false);
  const [generalChatInput, setGeneralChatInput] = useState('');
  const [generalChatLoading, setGeneralChatLoading] = useState(false);
  
  // Unified landing page state
  const [selectedAction, setSelectedAction] = useState<'chat' | 'career-analytics' | 'find-job' | 'land-job' | 'ai-tools' | null>('chat');
  const [actionFlowInput, setActionFlowInput] = useState('');
  const [actionFlowLoading, setActionFlowLoading] = useState(false);
  const [aiToolsMessages, setAiToolsMessages] = useState<Array<{role: string, content: string}>>([]);
  const [activeActionFlow, setActiveActionFlow] = useState<string | null>(null);
  const [lastJobSearchQuery, setLastJobSearchQuery] = useState('');
  const [selectedJobForTailoring, setSelectedJobForTailoring] = useState<Job | null>(null);
  
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const analyticsChatContainerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();


  // Auto-scroll to latest message
  useEffect(() => {
    if (chatMessages.length > 0) {
      setTimeout(() => {
        window.scrollTo({ 
          top: document.body.scrollHeight, 
          behavior: 'smooth' 
        });
      }, 200);
    }
  }, [chatMessages]);

  // Auto-scroll for analytics chat
  useEffect(() => {
    if (analyticsChatMessages.length > 0) {
      setTimeout(() => {
        window.scrollTo({ 
          top: document.body.scrollHeight, 
          behavior: 'smooth' 
        });
      }, 200);
    }
  }, [analyticsChatMessages]);

  // Get search placeholder based on intent
  const getUnifiedPlaceholder = () => {
    switch (selectedAction) {
      case 'chat':
        return "Ask anything about your future";
      case 'career-analytics':
        return "Paste your resume here...";
      case 'find-job':
        return "Find a job ie. writer, data scientist, etc....";
      case 'land-job':
        return "Paste the job listing here";
      case 'ai-tools':
        return "What do you want to build? (e.g., a pitch deck for my startup, a portfolio website)";
      default:
        return "Ask anything about your future";
    }
  };

  // Helper to generate cover letter
  const generateCoverLetter = async (): Promise<string> => {
    if (!tailoredResults) return '';
    try {
      const response = await fetch(`${API_URL}/coach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: 'You are a professional cover letter writer. Generate a compelling, professional cover letter.' },
            { role: 'user', content: `Write a professional cover letter based on this resume:\n\n${tailoredResults.tailored_resume_md}` }
          ]
        })
      });
      const data = await response.json();
      return (data.reply || '').replace(/\*\*/g, '');
    } catch (error) {
      return 'Failed to generate cover letter.';
    }
  };

  // Unified search handler
  const handleUnifiedSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setHasSearched(true);

    try {
      if (intent === 'find-job') {
        // Job search flow
        const response = await fetch(`${API_URL}/search-jobs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_title: searchQuery })
        });
        const data = await response.json();
        const jobsArray = Array.isArray(data) ? data : (data.jobs || []);
        setJobs(jobsArray);
      } else if (intent === 'land-job') {
        // Store job listing and ask for resume
        setJobDescription(searchQuery);
        setChatMessages([{
          role: 'assistant',
          content: `Got your job listing! Now paste your resume below.`
        }]);
      } else if (intent === 'ai-tools') {
        // AI tools - coming soon
        setChatMessages([{
          role: 'assistant',
          content: `🚀 AI tools discovery is coming soon!`
        }]);
      }
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Conversational chat handler with smart commands
  const handleChatSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userMessage = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMessage]);
    const userInput = chatInput.toLowerCase();
    setChatInput('');
    setChatLoading(true);

    // Detect commands
    const isDownloadRequest = userInput.includes('download') && (userInput.includes('resume') || userInput.includes('my resume') || (!userInput.includes('cover') && chatInput.includes('download')));
    const isDownloadCoverRequest = userInput.includes('download') && userInput.includes('cover');
    const isCoverLetterRequest = (userInput.includes('cover letter') || userInput.includes('generate cover')) && !coverLetter;
    const isResumeRequest = !tailoredResults && userInput.length > 50; // Long text = resume paste

    try {
      // Resume paste for land-job flow
      if (isResumeRequest && jobDescription && intent === 'land-job') {
        const response = await fetch(`${API_URL}/quick-tailor`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            job_text: jobDescription,
            resume_text: chatInput
          })
        });
        const data = await response.json();
        setTailoredResults(data);
        const resumeContent = data.tailored_resume_md?.replace(/\*\*/g, '') || '';
        setChatMessages([{
          role: 'assistant',
          content: resumeContent
        }]);
        setChatLoading(false);
        return;
      }

      // Download requests
      if (isDownloadRequest || isDownloadCoverRequest) {
        if (!tailoredResults) {
          setChatMessages(prev => [...prev, {
            role: 'assistant',
            content: 'Please generate a resume first!'
          }]);
          setChatLoading(false);
          return;
        }

        const which = isDownloadCoverRequest ? 'cover' : 'resume';
        const response = await fetch(`${API_URL}/export`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            tailored_resume_md: tailoredResults.tailored_resume_md,
            cover_letter_md: coverLetter || tailoredResults.cover_letter_md || '',
            which
          })
        });
        
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `pathio_${which}.docx`;
          a.click();
          window.URL.revokeObjectURL(url);
          setHasDownloaded(true);
          setChatMessages(prev => [...prev, {
            role: 'assistant',
            content: `✅ Downloaded! Good luck! 🎉`
          }]);
        }
        setChatLoading(false);
        return;
      }

      // Cover letter generation
      if (isCoverLetterRequest && tailoredResults) {
        const letter = tailoredResults.cover_letter_md?.replace(/\*\*/g, '') || await generateCoverLetter();
        setCoverLetter(letter);
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: letter
        }]);
        setChatLoading(false);
        return;
      }

      // Regular conversation with AI coach
      if (tailoredResults) {
        const response = await fetch(`${API_URL}/coach`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: [
              { 
                role: 'system', 
                content: `You are Pathio, a career coach. Current resume:\n\n${tailoredResults.tailored_resume_md}\n\nWhat changed:\n${tailoredResults.what_changed_md || 'N/A'}\n\nAction items:\nQuick: ${tailoredResults.insights?.do_now?.join(', ') || 'None'}\nLong-term: ${tailoredResults.insights?.do_long?.join(', ') || 'None'}\n\nHelp the user. No markdown bold (**).` 
              },
              ...chatMessages,
              userMessage
            ]
          })
        });
        const data = await response.json();
        const cleanContent = (data.reply || 'Sorry, could not respond.').replace(/\*\*/g, '');
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: cleanContent
        }]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, error occurred.'
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Helper function to clean HTML from job descriptions while preserving formatting
  const cleanHTML = (html: string): string => {
    if (!html) return '';
    
    return html
      // Convert common HTML tags to line breaks
      .replace(/<\/p>/gi, '\n\n')
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/li>/gi, '\n')
      .replace(/<\/h[1-6]>/gi, '\n\n')
      .replace(/<li[^>]*>/gi, '• ')
      // Convert strong/bold tags to text emphasis
      .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '$1')
      .replace(/<b[^>]*>(.*?)<\/b>/gi, '$1')
      // Remove all other HTML tags
      .replace(/<[^>]*>/g, '')
      // Decode HTML entities
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&rsquo;/g, "'")
      .replace(/&lsquo;/g, "'")
      .replace(/&rdquo;/g, '"')
      .replace(/&ldquo;/g, '"')
      // Clean up excessive whitespace but preserve intentional line breaks
      .replace(/[ \t]+/g, ' ') // Multiple spaces/tabs to single space
      .replace(/\n\s+\n/g, '\n\n') // Clean up lines with only whitespace
      .replace(/\n{3,}/g, '\n\n') // Max 2 consecutive line breaks
      .trim();
  };

  // Handle job search flow
  const handleJobSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionFlowInput.trim() || actionFlowLoading) return;

    console.log('=== JOB SEARCH STARTED ===');
    console.log('Query:', actionFlowInput);
    
    setActionFlowLoading(true);
    const jobQuery = actionFlowInput;
    setIntent('find-job');
    
    try {
      const url = `${API_URL}/search-jobs`;
      console.log('Fetching from:', url);
      console.log('Request body:', { query: jobQuery });
      
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_title: jobQuery })
      });
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Job search results:', data);
      console.log('Jobs array:', data.jobs);
      console.log('Jobs count:', data.jobs?.length || 0);
      
      setJobs(data.jobs || []);
      setHasSearched(true);
      setLastJobSearchQuery(jobQuery); // Store the search query
      // DON'T set searchQuery - that's for resume upload only
      setActiveActionFlow(null); // Close the panel
      setActionFlowInput('');
      
      console.log('=== JOB SEARCH COMPLETE ===');
      console.log('hasSearched:', true);
      console.log('intent:', 'find-job');
      console.log('jobs.length:', data.jobs?.length || 0);
    } catch (error) {
      console.error('=== JOB SEARCH ERROR ===');
      console.error('Error details:', error);
      alert(`Error searching for jobs: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setActionFlowLoading(false);
      console.log('Loading state set to false');
    }
  };

  // Handle land job flow
  const handleLandJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionFlowInput.trim() || actionFlowLoading) return;

    // Store job description and ask for resume
    setJobDescription(actionFlowInput);
    setActiveActionFlow(null); // Close the panel
    
    // Prompt for resume in a new fixed panel or alert
    const resumeText = prompt('Now paste your resume:');
    if (resumeText) {
      setResume(resumeText);
      setActionFlowLoading(true);
      
      try {
        const response = await fetch(`${API_URL}/quick-tailor`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            job_description: actionFlowInput,
            resume_text: resumeText
          })
        });
        const data = await response.json();
        setTailoredResults(data);
        
        // Add initial message
        const cleanResume = data.tailored_resume_md?.replace(/\*\*/g, '') || '';
        setChatMessages([{
          role: 'assistant',
          content: cleanResume
        }]);
      } catch (error) {
        console.error('Tailoring error:', error);
        alert('Error tailoring resume. Please try again.');
      } finally {
        setActionFlowLoading(false);
        setActionFlowInput('');
      }
    }
  };

  // Handle resume submission for tailoring
  const handleTailorResumeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionFlowInput.trim() || actionFlowLoading || !selectedJobForTailoring) return;

    console.log('=== TAILORING RESUME ===');
    console.log('Job:', selectedJobForTailoring.title);
    console.log('Resume length:', actionFlowInput.length);

    setActionFlowLoading(true);
    const resumeText = actionFlowInput;
    setResume(resumeText);
    
    // Store job title for display
    setTailoredJobTitle(selectedJobForTailoring.title);
    
    try {
      const response = await fetch(`${API_URL}/quick-tailor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_text: selectedJobForTailoring.description,
          resume_text: resumeText
        })
      });
      
      const data = await response.json();
      console.log('Tailored results:', data);
      
      setTailoredResults(data);
      
      // Display both resume and cover letter
      const cleanResume = data.tailored_resume_md?.replace(/\*\*/g, '') || '';
      const cleanCoverLetter = data.cover_letter_md?.replace(/\*\*/g, '') || '';
      console.log('Clean resume length:', cleanResume.length);
      console.log('Clean cover letter length:', cleanCoverLetter.length);
      
      // Set initial messages with both documents
      const messages = [];
      if (cleanResume) {
        messages.push({
          role: 'assistant',
          content: cleanResume,
          type: 'resume'
        });
      }
      if (cleanCoverLetter) {
        messages.push({
          role: 'assistant',
          content: cleanCoverLetter,
          type: 'cover_letter'
        });
      }
      
      setChatMessages(messages as any);
      
      // Clear the job search and tailoring flow to show tailored results page
      setSelectedJobForTailoring(null);
      setActionFlowInput('');
      setHasSearched(false); // Hide job results
      setJobs([]); // Clear jobs
      
      console.log('=== TAILORING COMPLETE ===');
      console.log('tailoredResults set:', !!data);
      console.log('chatMessages length:', 1);
    } catch (error) {
      console.error('Tailoring error:', error);
      alert('Error tailoring resume. Please try again.');
    } finally {
      setActionFlowLoading(false);
    }
  };

  // Handle AI tools flow
  const handleAiTools = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionFlowInput.trim() || actionFlowLoading) return;

    const userMessage = { role: 'user', content: actionFlowInput };
    setAiToolsMessages(prev => [...prev, userMessage]);
    setActionFlowInput('');
    setActionFlowLoading(true);

    try {
      const response = await fetch(`${API_URL}/coach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { 
              role: 'system', 
              content: `You are Pathio, an AI tools discovery assistant for Gen Z/Alpha. Help users find the LATEST, most relevant AI tools for their projects. Be specific about tool names, what they do, and why they're useful. Focus on tools that are currently available and widely used. No markdown bold (**).` 
            },
            ...aiToolsMessages,
            userMessage
          ]
        })
      });
      
      const data = await response.json();
      const cleanContent = (data.reply || 'Sorry, could not respond.').replace(/\*\*/g, '');
      setAiToolsMessages(prev => [...prev, {
        role: 'assistant',
        content: cleanContent
      }]);
    } catch (error) {
      console.error('AI tools error:', error);
      setAiToolsMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, an error occurred. Please try again.'
      }]);
    } finally {
      setActionFlowLoading(false);
    }
  };

  // Unified form handler for initial actions + chat
  const handleUnifiedSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const inputText = searchQuery.trim();
    
    if (!inputText) return;
    
    // If chat action selected, treat as general career coach chat
    if (selectedAction === 'chat') {
      setLoading(true);
      try {
        // Add user message to chat
        const userMessage = { role: 'user', content: inputText };
        setChatMessages(prev => [...prev, userMessage]);
        
        // Send to career coach
        const response = await fetch(`${API_URL}/coach`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: [
              { 
                role: 'system', 
                content: `You are Pathio, a career coach for Gen Z/Alpha. Help users with career guidance, job search, resume advice, and future planning. Be encouraging, specific, and actionable.` 
              },
              ...chatMessages,
              userMessage
            ]
          })
        });
        
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Add assistant response to chat
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply
      }]);
      
      // Clear the input
      setSearchQuery('');
    } catch (error) {
      console.error('Career coach error:', error);
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Sorry, an error occurred. Please try again.'
        }]);
      } finally {
        setLoading(false);
      }
      return;
    }
    
    setLoading(true);
    try {
      if (selectedAction === 'career-analytics') {
        // Handle career analytics
        const response = await fetch(`${API_URL}/career-analytics`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ resume_text: inputText })
        });
        const data = await response.json();
        setCareerAnalytics(data);
        setResume(inputText);
        // Enable chat for follow-up questions
        setChatMessages([{ role: 'user', content: inputText }]);
      } else if (selectedAction === 'find-job') {
        // Handle job search
        const response = await fetch(`${API_URL}/search-jobs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_title: inputText })
        });
        const data = await response.json();
        setJobs(data.jobs || []);
        setHasSearched(true);
        setLastJobSearchQuery(inputText);
        // Enable chat for follow-up questions
        setChatMessages([{ role: 'user', content: inputText }]);
      } else if (selectedAction === 'land-job') {
        // Handle job landing - store job description and ask for resume
        setJobs([{ description: inputText } as Job]);
        setHasSearched(true);
        setLastJobSearchQuery('Custom Job');
        // Enable chat for follow-up questions
        setChatMessages([{ role: 'user', content: inputText }]);
      } else if (selectedAction === 'ai-tools') {
        // Handle AI tools - start with career coach
        const userMessage = { role: 'user', content: inputText };
        setChatMessages([userMessage]);
        
        const response = await fetch(`${API_URL}/coach`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: [
              { 
                role: 'system', 
                content: `You are Pathio, a career coach for Gen Z/Alpha. Help users with AI tools for their career goals. Be encouraging, specific, and actionable.` 
              },
              userMessage
            ]
          })
        });
        
        const data = await response.json();
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: data.reply
        }]);
      }
      
      // Clear the input and reset action
      setSearchQuery('');
      setSelectedAction(null);
    } catch (error) {
      console.error('Error:', error);
      alert('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle general career chat (from fixed chat input)
  const handleGeneralChatSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!generalChatInput.trim() || generalChatLoading) return;

    setGeneralChatLoading(true);
    const userMessage = { role: 'user', content: generalChatInput.trim() };
    
    try {
      // Add user message
      setChatMessages(prev => [...prev, userMessage]);
      setGeneralChatInput('');

      // Send to career coach
      const response = await fetch(`${API_URL}/coach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { 
              role: 'system', 
              content: `You are Pathio, a career coach for Gen Z/Alpha. Help users with career guidance, job search, resume advice, and future planning. Be encouraging, specific, and actionable.` 
            },
            ...chatMessages,
            userMessage
          ]
        })
      });

      const data = await response.json();

      // Add assistant response
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply
      }]);
    } catch (error) {
      console.error('General chat error:', error);
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, an error occurred. Please try again.'
      }]);
    } finally {
      setGeneralChatLoading(false);
    }
  };

  // Handle analytics chat
  const handleAnalyticsChatSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!analyticsChatInput.trim() || analyticsChatLoading || !careerAnalytics) return;

    const userMessage = { role: 'user', content: analyticsChatInput };
    setAnalyticsChatMessages(prev => [...prev, userMessage]);
    setAnalyticsChatInput('');
    setAnalyticsChatLoading(true);

    try {
      // Build context from analytics
      const analyticsContext = `
Career Analytics Summary:
- Industries: ${Object.entries(careerAnalytics.creative_focus || {}).map(([k, v]) => `${k} (${v}%)`).join(', ')}
- Core Strengths: ${(careerAnalytics.core_strength_zones || []).join(', ')}
- Experience: ${careerAnalytics.experience_depth_years || 0} years
- Momentum: ${(careerAnalytics.momentum_indicators || []).join(', ')}
- Recommended Focus: ${(careerAnalytics.recommended_focus_next || []).join(', ')}
- Adjacent Opportunities: ${(careerAnalytics.adjacent_opportunities || []).map((opp: any) => `${opp.skill_combo} → ${opp.opportunity}`).join(' | ')}
- AI Skills to Explore: ${(careerAnalytics.ai_skills_to_explore || []).join(', ')}

Original Resume:
${resume}
`;

      const response = await fetch(`${API_URL}/coach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { 
              role: 'system', 
              content: `You are Pathio, a career intelligence assistant for Gen Z/Alpha. You help users understand their career analytics and explore future-proof opportunities. Be encouraging, specific, and strategic. No markdown bold (**).

${analyticsContext}

Answer their questions about career paths, skills to learn, adjacent opportunities, or anything related to their career analytics. Be conversational and helpful.` 
            },
            ...analyticsChatMessages,
            userMessage
          ]
        })
      });
      
      const data = await response.json();
      const cleanContent = (data.reply || 'Sorry, could not respond.').replace(/\*\*/g, '');
      setAnalyticsChatMessages(prev => [...prev, {
        role: 'assistant',
        content: cleanContent
      }]);
    } catch (error) {
      console.error('Analytics chat error:', error);
      setAnalyticsChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, an error occurred. Please try again.'
      }]);
    } finally {
      setAnalyticsChatLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-white" style={{ 
      display: 'flex', 
      alignItems: careerAnalytics || tailoredResults ? 'flex-start' : 'center'
    }}>
      {/* Top-Left Header */}
      <div style={{
        position: 'fixed',
        top: '40px',
        left: '40px',
        zIndex: 100
      }}>
        <a href="/" style={{ textDecoration: 'none' }} onClick={(e) => {
          if (careerAnalytics || tailoredResults) {
            e.preventDefault();
            setCareerAnalytics(null);
            setTailoredResults(null);
            setJobs([]);
            setHasSearched(false);
            setSearchQuery('');
            setChatMessages([]);
            setCoverLetter('');
            setHasDownloaded(false);
          }
        }}>
          <div className="flex flex-col">
            <span className="text-[1.6rem] cursor-pointer hover:opacity-80 transition-opacity" style={{ 
              fontWeight: '800',
              color: '#0A0A0A',
              letterSpacing: '-0.3px',
              marginBottom: '4px'
            }}>
              pathio
            </span>
            {!careerAnalytics && !tailoredResults && !(hasSearched && jobs.length > 0) && chatMessages.length === 0 && (
              <span className="text-[0.9rem]" style={{ fontWeight: '600', color: '#A78BFA' }}>
                smart career moves
              </span>
            )}
          </div>
        </a>
      </div>

      <div className="max-w-[720px] mx-auto px-4 w-full" style={{ paddingBottom: '32px', paddingTop: careerAnalytics || tailoredResults || (hasSearched && jobs.length > 0) || chatMessages.length > 0 ? '140px' : '0' }}>

        {/* Show job results if available */}
        {hasSearched && jobs.length > 0 ? (
          <div style={{ marginTop: '0', marginBottom: '200px' }}>
            <h2 className="text-[1.6rem] text-center" style={{ 
              fontWeight: '800',
              color: '#0A0A0A',
              marginBottom: '16px'
            }}>
              Job Results
            </h2>
            
            {/* Job Count */}
            <div style={{ 
              fontSize: '0.9rem',
              fontWeight: '500',
              color: '#707070',
              textAlign: 'center',
              marginBottom: '32px'
            }}>
              {jobs.length} {lastJobSearchQuery} jobs found
            </div>

            {/* Filter Options */}
            <div style={{ marginBottom: '32px' }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', justifyContent: 'center' }}>
                <button
                  onClick={() => { setFilter('all'); setLocationFilter(''); }}
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    padding: '10px 20px',
                    borderRadius: '20px',
                    background: filter === 'all' && !locationFilter ? 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)' : '#FAFAF9',
                    color: filter === 'all' && !locationFilter ? '#FFFFFF' : '#313338',
                    border: `2px solid ${filter === 'all' && !locationFilter ? '#7C3AED' : '#D8B4FE'}`,
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  All
                </button>
                <button
                  onClick={() => { setFilter('remote'); setLocationFilter(''); }}
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    padding: '10px 20px',
                    borderRadius: '20px',
                    background: filter === 'remote' ? 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)' : '#FAFAF9',
                    color: filter === 'remote' ? '#FFFFFF' : '#313338',
                    border: `2px solid ${filter === 'remote' ? '#7C3AED' : '#D8B4FE'}`,
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  Remote
                </button>
                <button
                  onClick={() => { setFilter('fulltime'); setLocationFilter(''); }}
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    padding: '10px 20px',
                    borderRadius: '20px',
                    background: filter === 'fulltime' ? 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)' : '#FAFAF9',
                    color: filter === 'fulltime' ? '#FFFFFF' : '#313338',
                    border: `2px solid ${filter === 'fulltime' ? '#7C3AED' : '#D8B4FE'}`,
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  Full-time
                </button>
                <button
                  onClick={() => { setFilter('contract'); setLocationFilter(''); }}
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    padding: '10px 20px',
                    borderRadius: '20px',
                    background: filter === 'contract' ? 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)' : '#FAFAF9',
                    color: filter === 'contract' ? '#FFFFFF' : '#313338',
                    border: `2px solid ${filter === 'contract' ? '#7C3AED' : '#D8B4FE'}`,
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  Contract
                </button>
              </div>
            </div>

            {/* Job Listings */}
            <div className="space-y-4">
              {jobs
                .filter(job => {
                  if (filter === 'remote') {
                    const searchText = `${job.title} ${job.location} ${job.type} ${job.description}`.toLowerCase();
                    return searchText.includes('remote');
                  }
                  if (filter === 'fulltime') {
                    const searchText = `${job.type} ${job.title}`.toLowerCase();
                    return searchText.includes('full') || searchText.includes('full-time');
                  }
                  if (filter === 'contract') {
                    const searchText = `${job.type} ${job.title}`.toLowerCase();
                    return searchText.includes('contract') || searchText.includes('contractor');
                  }
                  if (locationFilter) {
                    return job.location.toLowerCase().includes(locationFilter.toLowerCase());
                  }
                  return true;
                })
                .map((job, index) => (
                  <div key={index} style={{ 
                    padding: '24px',
                    borderRadius: '20px',
                    background: '#FAFAF9',
                    border: '2px solid #D8B4FE',
                    marginBottom: '16px',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onClick={() => setExpandedJobIndex(expandedJobIndex === index ? null : index)}
                  onMouseEnter={(e) => e.currentTarget.style.borderColor = '#A78BFA'}
                  onMouseLeave={(e) => e.currentTarget.style.borderColor = '#D8B4FE'}
                  >
                    <div>
                      <h3 style={{ 
                        fontSize: '1.1rem',
                        fontWeight: '700',
                        color: '#7C3AED',
                        marginBottom: '8px'
                      }}>
                        {job.title}
                      </h3>
                      <div style={{ 
                        fontSize: '0.85rem',
                        fontWeight: '500',
                        color: '#707070',
                        marginBottom: '4px'
                      }}>
                        {job.company} • {job.location} • {job.type}
                      </div>
                    </div>

                    {expandedJobIndex === index && (
                      <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '2px solid #E9D5FF' }}>
                        <h4 style={{ 
                          fontSize: '0.95rem',
                          fontWeight: '700',
                          color: '#0A0A0A',
                          marginBottom: '12px'
                        }}>
                          Description
                        </h4>
                        <p style={{ 
                          fontSize: '0.9rem',
                          color: '#505050',
                          lineHeight: '1.7',
                          marginBottom: '20px',
                          whiteSpace: 'pre-wrap'
                        }}>
                          {cleanHTML(job.description)}
                        </p>
                        <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                          <a 
                            href={job.url} 
            target="_blank"
            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            style={{ 
                              fontSize: '0.85rem',
                              background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                              padding: '12px 28px',
                              borderRadius: '24px',
                              color: '#FFFFFF',
                              fontWeight: 'bold',
                              textDecoration: 'none',
                              display: 'inline-block',
                              boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)',
                              transition: 'opacity 0.2s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.opacity = '0.9'}
                            onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
                          >
                            Apply Now
                          </a>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedJobForTailoring(job);
                              setJobDescription(job.description);
                              setActionFlowInput(''); // Clear any existing input
                            }}
                            style={{ 
                              fontSize: '0.85rem',
                              background: '#FFFFFF',
                              padding: '12px 28px',
                              borderRadius: '24px',
                              color: '#7C3AED',
                              fontWeight: 'bold',
                              border: '2px solid #D8B4FE',
                              cursor: 'pointer',
                              transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.background = 'linear-gradient(135deg, #F3E8FF 0%, #E9D5FF 100%)';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.background = '#FFFFFF';
                            }}
                          >
                            Tailor My Resume For This Job
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
            </div>
          </div>
        ) : careerAnalytics ? (
          <div style={{ marginTop: '0', marginBottom: '200px' }}>
            <h2 className="text-[1.6rem] text-center" style={{ 
              fontWeight: '800',
              color: '#0A0A0A',
              marginBottom: '48px'
            }}>
              Your Career Analytics
            </h2>

            {/* Creative Focus */}
            <div style={{ marginBottom: '40px' }}>
              <h3 style={{ 
                fontSize: '1rem',
                fontWeight: '700',
                color: '#0A0A0A',
                marginBottom: '20px'
              }}>
                Creative Focus
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {Object.entries(careerAnalytics.creative_focus || {}).map(([industry, percentage]) => (
                  <div key={industry}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.9rem', fontWeight: '500', color: '#313338' }}>{industry}</span>
                      <span style={{ fontSize: '0.9rem', fontWeight: '700', color: '#7C3AED' }}>{String(percentage)}%</span>
                    </div>
                    <div style={{ width: '100%', background: '#F2F3F5', borderRadius: '20px', height: '10px' }}>
                      <div 
                        style={{ 
                          height: '10px',
                          borderRadius: '20px',
                          width: `${percentage}%`,
                          background: 'linear-gradient(90deg, #7C3AED 0%, #A78BFA 100%)',
                          transition: 'width 0.3s ease'
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Core Strengths */}
            <div style={{ marginBottom: '40px' }}>
              <h3 style={{ 
                fontSize: '1rem',
                fontWeight: '700',
                color: '#0A0A0A',
                marginBottom: '20px'
              }}>
                Core Strength Zones
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                {(careerAnalytics.core_strength_zones || []).map((strength: string, i: number) => (
                  <span key={i} style={{
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    padding: '10px 20px',
                    borderRadius: '20px',
                    background: '#F3E8FF',
                    color: '#5B21B6',
                    border: '2px solid #D8B4FE'
                  }}>
                    {strength}
                  </span>
                ))}
              </div>
            </div>

            {/* Experience & Skills */}
            <div style={{ marginBottom: '40px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div style={{ 
                padding: '24px',
                borderRadius: '20px',
                background: '#FAFAF9',
                border: '2px solid #D8B4FE'
              }}>
                <h3 style={{ 
                  fontSize: '1rem',
                  fontWeight: '700',
                  color: '#0A0A0A',
                  marginBottom: '12px'
                }}>
                  Experience
                </h3>
                <div style={{ 
                  fontSize: '3rem',
                  fontWeight: '900',
                  background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}>
                  {careerAnalytics.experience_depth_years}+
                </div>
                <div style={{ fontSize: '0.85rem', fontWeight: '500', color: '#313338' }}>years</div>
              </div>
              <div style={{ 
                padding: '24px',
                borderRadius: '20px',
                background: '#FAFAF9',
                border: '2px solid #D8B4FE'
              }}>
                <h3 style={{ 
                  fontSize: '1rem',
                  fontWeight: '700',
                  color: '#0A0A0A',
                  marginBottom: '16px'
                }}>
                  Skill Stack
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {Object.entries(careerAnalytics.skill_stack_health || {}).map(([bucket, percentage]) => (
                    <div key={bucket} style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: '500', color: '#313338' }}>{bucket}</span>
                      <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#7C3AED' }}>{String(percentage)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Momentum */}
            <div style={{ marginBottom: '40px' }}>
              <h3 style={{ 
                fontSize: '1rem',
                fontWeight: '700',
                color: '#0A0A0A',
                marginBottom: '20px'
              }}>
                Momentum Indicators 🚀
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {(careerAnalytics.momentum_indicators || []).map((indicator: string, i: number) => (
                  <div key={i} style={{ 
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '16px 20px',
                    borderRadius: '20px',
                    background: '#FAFAF9',
                    border: '2px solid #D8B4FE'
                  }}>
                    <span style={{ fontSize: '1.2rem', color: '#7C3AED' }}>→</span>
                    <span style={{ fontSize: '0.9rem', fontWeight: '500', color: '#313338' }}>{indicator}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Focus */}
            <div style={{ marginBottom: '40px' }}>
              <h3 style={{ 
                fontSize: '1rem',
                fontWeight: '700',
                color: '#0A0A0A',
                marginBottom: '20px'
              }}>
                Recommended Focus Next
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {(careerAnalytics.recommended_focus_next || []).map((focus: string, i: number) => (
                  <div key={i} style={{ 
                    padding: '16px 20px',
                    borderRadius: '20px',
                    background: '#FAFAF9',
                    border: '2px solid #D8B4FE'
                  }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: '500', color: '#313338' }}>{focus}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Potential New Skills */}
            <div style={{ marginBottom: '40px' }}>
              <h3 style={{ 
                fontSize: '1rem',
                fontWeight: '700',
                color: '#0A0A0A',
                marginBottom: '20px'
              }}>
                Potential New Skills ✨
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                {(careerAnalytics.potential_new_skills || []).map((skill: string, i: number) => (
                  <span key={i} style={{
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    padding: '10px 20px',
                    borderRadius: '20px',
                    background: '#FFFFFF',
                    color: '#5B21B6',
                    border: '2px solid #D8B4FE'
                  }}>
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* AI Skills to Explore */}
            {careerAnalytics.ai_skills_to_explore && careerAnalytics.ai_skills_to_explore.length > 0 && (
              <div style={{ marginBottom: '40px' }}>
                <h3 style={{ 
                  fontSize: '1rem',
                  fontWeight: '700',
                  color: '#0A0A0A',
                  marginBottom: '20px'
                }}>
                  AI Skills to Explore 🤖
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                  {careerAnalytics.ai_skills_to_explore.map((skill: string, i: number) => (
                    <span key={i} style={{
                      fontSize: '0.85rem',
                      fontWeight: '600',
                      padding: '10px 20px',
                      borderRadius: '20px',
                      background: 'linear-gradient(135deg, #F3E8FF 0%, #E9D5FF 100%)',
                      color: '#5B21B6',
                      border: '2px solid #A78BFA'
                    }}>
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Adjacent Opportunities - Career Adjacency Intelligence */}
            {careerAnalytics.adjacent_opportunities && careerAnalytics.adjacent_opportunities.length > 0 && (
              <div style={{ marginBottom: '40px' }}>
                <h3 style={{ 
                  fontSize: '1rem',
                  fontWeight: '700',
                  color: '#0A0A0A',
                  marginBottom: '8px'
                }}>
                  Adjacent Opportunities
                </h3>
                <p style={{ 
                  fontSize: '0.85rem',
                  color: '#707070',
                  marginBottom: '20px',
                  fontStyle: 'italic'
                }}>
                  What else can you do? Here are transferable career paths based on your skills.
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {careerAnalytics.adjacent_opportunities.map((opp: any, i: number) => (
                    <div key={i} style={{ 
                      padding: '20px 24px',
                      borderRadius: '20px',
                      background: 'linear-gradient(135deg, #FAFAF9 0%, #F3F4F6 100%)',
                      border: '2px solid #D8B4FE',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}>
                      <div style={{ 
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        color: '#7C3AED',
                        letterSpacing: '0.3px'
                      }}>
                        {opp.skill_combo}
                      </div>
                      <div style={{ 
                        fontSize: '0.95rem',
                        fontWeight: '600',
                        color: '#0A0A0A'
                      }}>
                        → {opp.opportunity}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Analytics Chat Messages */}
            {analyticsChatMessages.length > 0 && (
              <div ref={analyticsChatContainerRef} style={{ marginTop: '60px', marginBottom: '220px' }}>
                <h2 className="text-[1.6rem] text-center" style={{ 
                  fontWeight: '800',
                  color: '#0A0A0A',
                  marginBottom: '48px'
                }}>
                  Career Conversation
                </h2>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  {analyticsChatMessages.map((msg, i) => (
                    <div
                      key={i}
                      className={msg.role === 'user' ? '' : 'bg-white border border-[#E5E5E5] rounded-lg'}
                      style={{
                        animation: 'slideUp 0.4s ease-out',
                        padding: msg.role === 'user' ? '20px 0' : '16px'
                      }}
                    >
                      {msg.role === 'user' ? (
                        <div style={{ 
                          fontSize: '1.1rem', 
                          fontWeight: '500', 
                          color: '#202020'
                        }}>
                          {msg.content}
                        </div>
                      ) : (
                        <div style={{ 
                          fontSize: '0.9rem', 
                          color: '#303030', 
                          lineHeight: '1.7',
                          whiteSpace: 'pre-wrap'
                        }}>
                          {msg.content}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : tailoredResults ? (
          <>
            {/* Loading */}
            {!chatMessages.length && (
              <div style={{
                textAlign: 'center',
                padding: '60px 0',
                animation: 'pulse 1.5s ease-in-out infinite'
              }}>
                <div className="text-[0.95rem] text-[#505050] mb-3">Generating your tailored resume...</div>
                <div className="text-[0.85rem] text-[#909090]">This may take a few moments</div>
              </div>
            )}

            {/* Tailored Resume Display */}
            {chatMessages.length > 0 && (
              <div ref={chatContainerRef} style={{ marginTop: '0', marginBottom: '220px' }}>
                {/* Job Title as Main Header */}
                {tailoredJobTitle && (
                  <h2 className="text-[1.6rem] text-center" style={{ 
                    fontWeight: '800',
                    color: '#0A0A0A',
                    marginBottom: '48px'
                  }}>
                    {tailoredJobTitle}
                  </h2>
                )}
                
                {/* Documents Display */}
                <div className="space-y-12">
                  {chatMessages.map((msg, i) => {
                    const isResume = (msg as any).type === 'resume';
                    const isCoverLetter = (msg as any).type === 'cover_letter';
                    const isUser = msg.role === 'user';
                    
                    return (
                      <div key={i} style={{ animation: 'slideUp 0.4s ease-out' }}>
                        {/* Document Card */}
                        {(isResume || isCoverLetter) ? (
                          <div style={{
                            background: 'linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%)',
                            border: '2px solid #E9D5FF',
                            borderRadius: '24px',
                            padding: '32px',
                            boxShadow: '0 4px 20px rgba(124, 58, 237, 0.08)'
                          }}>
                            {/* Document Header */}
                            <div style={{
                              background: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)',
                              borderRadius: '16px',
                              padding: '20px 24px',
                              marginBottom: '24px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between'
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <span style={{ fontSize: '1.5rem' }}>
                                  {isResume ? '📄' : '✉️'}
                                </span>
                                <h3 style={{
                                  fontSize: '1.1rem',
                                  fontWeight: '700',
                                  color: '#FFFFFF',
                                  margin: 0,
                                  letterSpacing: '-0.3px'
                                }}>
                                  {isResume ? 'Your Tailored Resume' : 'Your Cover Letter'}
                                </h3>
                              </div>
                              
                              {/* Download Button */}
                              <button
                                onClick={async (e) => {
                                  e.stopPropagation();
                                  const which = isResume ? 'resume' : 'cover_letter';
                                  
                                  try {
                                    const response = await fetch(`${API_URL}/export`, {
                                      method: 'POST',
                                      headers: { 'Content-Type': 'application/json' },
                                      body: JSON.stringify({
                                        which: which,
                                        tailored_resume_md: tailoredResults?.tailored_resume_md || '',
                                        cover_letter_md: tailoredResults?.cover_letter_md || ''
                                      })
                                    });
                                    
                                    if (response.ok) {
                                      const blob = await response.blob();
                                      const url = URL.createObjectURL(blob);
                                      const a = document.createElement('a');
                                      a.href = url;
                                      a.download = `pathio_${which}.docx`;
                                      document.body.appendChild(a);
                                      a.click();
                                      document.body.removeChild(a);
                                      URL.revokeObjectURL(url);
                                    }
                                  } catch (error) {
                                    console.error('Download error:', error);
                                  }
                                }}
                                className="hover:opacity-80 transition-opacity"
                                style={{
                                  background: '#FFFFFF',
                                  color: '#7C3AED',
                                  border: 'none',
                                  borderRadius: '12px',
                                  padding: '8px 20px',
                                  fontSize: '0.85rem',
                                  fontWeight: '600',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '6px'
                                }}
                              >
                                <span>↓</span> Download
                              </button>
                            </div>
                            
                            {/* Document Content */}
                            <div style={{
                              background: '#FFFFFF',
                              borderRadius: '16px',
                              padding: '28px',
                              border: '1px solid #F3E8FF'
                            }}>
                              <p className="whitespace-pre-wrap" style={{
                                fontSize: '0.9rem',
                                color: '#303030',
                                lineHeight: '1.8',
                                margin: 0
                              }}>
                                {msg.content}
                              </p>
                            </div>
                          </div>
                        ) : (
                          /* User messages or AI responses */
                          <div
                            className={isUser ? '' : 'bg-white border border-[#E5E5E5] rounded-lg'}
                            style={{
                              padding: isUser ? '20px 0' : '24px'
                            }}
                          >
                            <p className={`whitespace-pre-wrap ${isUser ? 'text-[1.1rem] font-medium text-[#202020]' : 'text-[0.9rem] text-[#303030]'}`} style={{ 
                              lineHeight: isUser ? '1.6' : '1.7'
                            }}>
                              {msg.content}
                            </p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {chatLoading && (
                    <div className="p-4 rounded-lg bg-white border border-[#E5E5E5] text-[#909090]">
                      <p className="text-[0.9rem]">Thinking...</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        ) : !careerAnalytics && !tailoredResults && !(hasSearched && jobs.length > 0) && chatMessages.length === 0 ? (
          <>
        {/* Resume Upload Area */}
        <div className="mb-6">
          <div className="flex flex-col items-center gap-4">
            {/* Textarea with file upload option */}
            <div className="w-full" style={{ maxWidth: '680px' }}>
              <form onSubmit={handleUnifiedSubmit}>
                <textarea
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={getUnifiedPlaceholder()}
                  className="w-full text-[1rem] border-2 border-[#D8B4FE] focus:outline-none focus:border-[#A78BFA] transition-colors resize-none font-medium"
                  rows={6}
                  style={{ borderRadius: '20px', padding: '18px 22px', background: '#FAFAF9' }}
                />
              <div className="flex justify-center items-center" style={{ marginTop: '8px', paddingLeft: '4px', paddingRight: '4px', gap: '12px' }}>
                {(selectedAction === 'career-analytics' || selectedAction === 'land-job') && (
                  <>
                    <input
                      type="file"
                      accept=".txt,.pdf,.doc,.docx"
                      onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          const text = await file.text();
                          setSearchQuery(text);
                        }
                      }}
                      style={{ display: 'none' }}
                      id="resume-upload"
                    />
                    <label
                      htmlFor="resume-upload"
                      className="text-[0.9rem] hover:opacity-80 cursor-pointer transition-opacity"
                      style={{ textDecoration: 'none', fontWeight: '600', color: '#5B21B6' }}
                    >
                      Upload file
                    </label>
                  </>
                )}
                <button
                  type="submit"
                  disabled={loading || !searchQuery.trim()}
                  style={{ 
                    background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                    padding: '12px 36px',
                    borderRadius: '24px',
                    color: '#FFFFFF',
                    fontWeight: 'bold',
                    border: 'none',
                    cursor: (loading || !searchQuery.trim()) ? 'not-allowed' : 'pointer',
                    boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)',
                    opacity: (loading || !searchQuery.trim()) ? 0.6 : 1,
                    fontSize: '0.85rem',
                    fontFamily: 'inherit',
                    lineHeight: '1',
                    textAlign: 'center',
                    textDecoration: 'none',
                    display: 'inline-block',
                    transition: 'opacity 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (!loading && searchQuery.trim()) {
                      e.currentTarget.style.opacity = '0.9';
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.opacity = (loading || !searchQuery.trim()) ? '0.6' : '1';
                  }}
                >
                  {loading ? 'Thinking...' : '→'}
                </button>
              </div>
              </form>
            </div>
          </div>
        </div>

        {/* Suggestion Chips - Perplexity style */}
        {!loading && !careerAnalytics && chatMessages.length === 0 && (
          <div className="flex flex-col items-center" style={{ marginTop: '34px' }}>
            <div className="flex flex-wrap justify-center" style={{ maxWidth: '680px', gap: '8px' }}>
              <button
                onClick={() => setSelectedAction('chat')}
                style={{ 
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  padding: '10px 20px',
                  borderRadius: '20px',
                  background: selectedAction === 'chat' ? '#7C3AED' : '#F3E8FF',
                  color: selectedAction === 'chat' ? '#FFFFFF' : '#5B21B6',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                Chat
              </button>
              <button
                onClick={() => setSelectedAction('career-analytics')}
                style={{ 
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  padding: '10px 20px',
                  borderRadius: '20px',
                  background: selectedAction === 'career-analytics' ? '#7C3AED' : '#F3E8FF',
                  color: selectedAction === 'career-analytics' ? '#FFFFFF' : '#5B21B6',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                Show me my career analytics
              </button>
              <button
                onClick={() => setSelectedAction('find-job')}
                style={{ 
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  padding: '10px 20px',
                  borderRadius: '20px',
                  background: selectedAction === 'find-job' ? '#7C3AED' : '#F3E8FF',
                  color: selectedAction === 'find-job' ? '#FFFFFF' : '#5B21B6',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                Help me find a job
              </button>
              <button
                onClick={() => setSelectedAction('land-job')}
                style={{ 
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  padding: '10px 20px',
                  borderRadius: '20px',
                  background: selectedAction === 'land-job' ? '#7C3AED' : '#F3E8FF',
                  color: selectedAction === 'land-job' ? '#FFFFFF' : '#5B21B6',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                I have a job listing, help me land it
              </button>
              <button
                onClick={() => setSelectedAction('ai-tools')}
                style={{ 
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  padding: '10px 20px',
                  borderRadius: '20px',
                  background: selectedAction === 'ai-tools' ? '#7C3AED' : '#F3E8FF',
                  color: selectedAction === 'ai-tools' ? '#FFFFFF' : '#5B21B6',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                I want to do my own thing, show me AI tools
              </button>
            </div>
          </div>
        )}

        {/* AI Tools Chat Display */}
        {aiToolsMessages.length > 0 && (
          <div style={{ marginTop: '60px', marginBottom: '220px' }}>
            <h2 className="text-[1.6rem] text-center" style={{ 
              fontWeight: '800',
              color: '#0A0A0A',
              marginBottom: '48px'
            }}>
              AI Tools for Your Project
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {aiToolsMessages.map((msg, i) => (
                <div
                  key={i}
                  className={msg.role === 'user' ? '' : 'bg-white border border-[#E5E5E5] rounded-lg'}
                  style={{
                    animation: 'slideUp 0.4s ease-out',
                    padding: msg.role === 'user' ? '20px 0' : '16px'
                  }}
                >
                  {msg.role === 'user' ? (
                    <div style={{ 
                      fontSize: '1.1rem', 
                      fontWeight: '500', 
                      color: '#202020'
                    }}>
                      {msg.content}
                    </div>
                  ) : (
                    <div style={{ 
                      fontSize: '0.9rem', 
                      color: '#303030', 
                      lineHeight: '1.7',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {msg.content}
                    </div>
                  )}
                </div>
              ))}
              {actionFlowLoading && (
                <div className="p-4 rounded-lg bg-white border border-[#E5E5E5] text-[#909090]">
                  <p className="text-[0.9rem]">Finding tools...</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Job Results - Show on same page */}
        {hasSearched && intent === 'find-job' && jobs.length > 0 && (
          <div className="mt-8">
            {loading && (
              <div className="text-[0.9rem] text-[#707070]">Searching...</div>
            )}

            {!loading && jobs.length > 0 && (
              <>
                <div className="mb-4 text-[0.9rem] text-[#707070]">
                  {(() => {
                    const filtered = jobs.filter(job => {
                      if (filter === 'remote') {
                        const searchText = `${job.title} ${job.location} ${job.type} ${job.description}`.toLowerCase();
                        return searchText.includes('remote');
                      }
                      if (filter === 'fulltime') {
                        const searchText = `${job.type} ${job.title}`.toLowerCase();
                        return searchText.includes('full') || searchText.includes('full-time');
                      }
                      if (filter === 'contract') {
                        const searchText = `${job.type} ${job.title}`.toLowerCase();
                        return searchText.includes('contract') || searchText.includes('contractor');
                      }
                      if (locationFilter) {
                        return job.location.toLowerCase().includes(locationFilter.toLowerCase());
                      }
                      return true;
                    });
                    return `${filtered.length} ${searchQuery} jobs found`;
                  })()}
                </div>

                {/* Filter Options - Clean inline style */}
                <div className="mb-6 pb-4 border-b border-[#E0E0E0]">
                  <div className="flex flex-wrap gap-3 mb-3 text-[0.85rem]">
                    <button
                      onClick={() => { setFilter('all'); setLocationFilter(''); }}
                      className={`px-3 py-1 rounded-full transition-all ${
                        filter === 'all' && !locationFilter
                          ? 'bg-[#202020] text-white'
                          : 'bg-[#F5F5F5] text-[#707070] hover:bg-[#E0E0E0]'
                      }`}
                    >
                      All
                    </button>
                    <button
                      onClick={() => { setFilter('remote'); setLocationFilter(''); }}
                      className={`px-3 py-1 rounded-full transition-all ${
                        filter === 'remote'
                          ? 'bg-[#202020] text-white'
                          : 'bg-[#F5F5F5] text-[#707070] hover:bg-[#E0E0E0]'
                      }`}
                    >
                      Remote
                    </button>
                    <button
                      onClick={() => { setFilter('fulltime'); setLocationFilter(''); }}
                      className={`px-3 py-1 rounded-full transition-all ${
                        filter === 'fulltime'
                          ? 'bg-[#202020] text-white'
                          : 'bg-[#F5F5F5] text-[#707070] hover:bg-[#E0E0E0]'
                      }`}
                    >
                      Full-time
                    </button>
                    <button
                      onClick={() => { setFilter('contract'); setLocationFilter(''); }}
                      className={`px-3 py-1 rounded-full transition-all ${
                        filter === 'contract'
                          ? 'bg-[#202020] text-white'
                          : 'bg-[#F5F5F5] text-[#707070] hover:bg-[#E0E0E0]'
                      }`}
                    >
                      Contract
                    </button>
                  </div>
                  
                  {/* Location filter */}
                  <input
                    type="text"
                    value={locationFilter}
                    onChange={(e) => { setLocationFilter(e.target.value); setFilter('all'); }}
                    placeholder="Filter by location..."
                    className="w-full px-3 py-2 text-[0.85rem] border border-[#E0E0E0] rounded-lg focus:outline-none focus:border-[#E0E0E0]"
                  />
                </div>

                {/* Job listings - with filtering */}
                <div>
                  {jobs
                    .filter(job => {
                      if (filter === 'remote') {
                        const searchText = `${job.title} ${job.location} ${job.type} ${job.description}`.toLowerCase();
                        return searchText.includes('remote');
                      }
                      if (filter === 'fulltime') {
                        const searchText = `${job.type} ${job.title}`.toLowerCase();
                        return searchText.includes('full') || searchText.includes('full-time');
                      }
                      if (filter === 'contract') {
                        const searchText = `${job.type} ${job.title}`.toLowerCase();
                        return searchText.includes('contract') || searchText.includes('contractor');
                      }
                      if (locationFilter) {
                        return job.location.toLowerCase().includes(locationFilter.toLowerCase());
                      }
                      return true;
                    })
                    .map((job, idx) => {
                      const isExpanded = expandedJobIndex === idx;
                      return (
                        <div
                          key={idx}
                          className="border-t border-[#E0E0E0]"
                        >
                          {/* Clickable job summary */}
                          <div
                            className="py-4 cursor-pointer hover:opacity-70 transition-opacity"
                            onClick={() => setExpandedJobIndex(isExpanded ? null : idx)}
                          >
                            {/* Job title - BLUE AND LEFT ALIGNED */}
                            <div className="text-[0.95rem] font-medium text-[#2563eb] mb-2 text-left">
                              {job.title} {isExpanded ? '▼' : '▶'}
                            </div>
                            {/* Company info - GREY AND LEFT ALIGNED */}
                            <div className="text-[0.85rem] text-[#707070] text-left">
                              {job.company} • {job.location} • {job.type}
                            </div>
                          </div>

                          {/* Expanded job details */}
                          {isExpanded && (
                            <div className="pb-6 px-4 bg-[#FAFAFA] rounded-lg mb-4">
                              {/* Description */}
                              <div className="mb-6">
                                <h3 className="text-[0.95rem] font-medium text-[#202020] mb-3">Description</h3>
                                <p className="text-[0.85rem] text-[#303030] leading-relaxed whitespace-pre-wrap">
                                  {job.description}
                                </p>
                              </div>

                              {/* Requirements */}
                              {job.requirements && job.requirements.length > 0 && (
                                <div className="mb-6">
                                  <h3 className="text-[0.95rem] font-medium text-[#202020] mb-3">Requirements</h3>
                                  <ul className="list-disc list-inside space-y-2">
                                    {job.requirements.map((req, reqIdx) => (
                                      <li key={reqIdx} className="text-[0.85rem] text-[#303030]">
                                        {req}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Action Buttons */}
                              <div className="space-y-3">
                                {job.url && (
                                  <a
                                    href={job.url}
            target="_blank"
            rel="noopener noreferrer"
                                    className="block w-full px-4 py-3 text-center text-[0.9rem] bg-[#2563eb] text-white rounded-lg hover:opacity-90 transition-opacity"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    Apply Now →
                                  </a>
                                )}
                                
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    localStorage.setItem('jobToApply', JSON.stringify(job));
                                    router.push('/apply');
                                  }}
                                  className="block w-full px-4 py-3 text-center text-[0.9rem] border border-[#2563eb] text-[#2563eb] rounded-lg hover:bg-[#2563eb] hover:text-white transition-all"
                                >
                                  Help me get hired →
                                </button>
        </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                </div>

                {/* No results message */}
                {jobs.filter(job => {
                  if (filter === 'remote') {
                    const searchText = `${job.title} ${job.location} ${job.type} ${job.description}`.toLowerCase();
                    return searchText.includes('remote');
                  }
                  if (filter === 'fulltime') {
                    const searchText = `${job.type} ${job.title}`.toLowerCase();
                    return searchText.includes('full') || searchText.includes('full-time');
                  }
                  if (filter === 'contract') {
                    const searchText = `${job.type} ${job.title}`.toLowerCase();
                    return searchText.includes('contract') || searchText.includes('contractor');
                  }
                  if (locationFilter) {
                    return job.location.toLowerCase().includes(locationFilter.toLowerCase());
                  }
                  return true;
                }).length === 0 && (
                  <div className="text-[0.9rem] text-[#707070] py-8 text-center">
                    No jobs match your filters. Try adjusting them.
                  </div>
                )}
              </>
            )}

            {!loading && jobs.length === 0 && (
              <div className="text-[0.9rem] text-[#707070]">
                No jobs found. Try a different search.
              </div>
            )}
          </div>
        )}
        </>
        ) : null}

        {/* General Chat Messages */}
        {chatMessages.length > 0 && !careerAnalytics && !tailoredResults && !(hasSearched && jobs.length > 0) && (
          <div style={{ marginTop: '40px', marginBottom: '200px' }}>
            <h2 className="text-[1.6rem] text-center" style={{ 
              fontWeight: '800',
              color: '#0A0A0A',
              marginBottom: '32px'
            }}>
              Career Chat
            </h2>
            
            {chatMessages.length > 0 ? (
              <div className="space-y-6">
                {chatMessages.map((msg, i) => (
                  <div key={i} style={{ animation: 'slideUp 0.4s ease-out' }}>
                    <div style={{
                      background: msg.role === 'user' 
                        ? 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)' 
                        : 'linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%)',
                      borderRadius: '20px',
                      padding: '20px 24px',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                      border: '1px solid #E5E7EB'
                    }}>
                      <div style={{
                        fontSize: '0.9rem',
                        fontWeight: '600',
                        color: msg.role === 'user' ? '#FFFFFF' : '#6B7280',
                        marginBottom: '8px'
                      }}>
                        {msg.role === 'user' ? 'You' : 'Pathio'}
                      </div>
                      <div style={{
                        fontSize: '1rem',
                        lineHeight: '1.6',
                        color: msg.role === 'user' ? '#FFFFFF' : '#0A0A0A',
                        whiteSpace: 'pre-wrap'
                      }}>
                        {msg.content}
                      </div>
                    </div>
                  </div>
                ))}
                
                {loading && (
                  <div className="text-center text-[0.9rem] text-[#505050]" style={{ marginTop: '24px' }}>
                    Thinking...
                  </div>
                )}
              </div>
            ) : loading ? (
              <div className="text-center text-[0.9rem] text-[#505050]">
                Thinking...
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* Fixed Bottom Chat Panel - For analytics */}
      {careerAnalytics && !tailoredResults && (
        <div 
          style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            background: '#FFFFFF',
            borderTop: '1px solid #E5E5E5',
            boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.08)',
            zIndex: 9999,
            padding: '20px 0'
          }}
        >
          <div className="mx-auto px-4" style={{ maxWidth: '680px' }}>
            <form onSubmit={handleAnalyticsChatSend}>
              <textarea
                value={analyticsChatInput}
                onChange={(e) => setAnalyticsChatInput(e.target.value)}
                placeholder="Ask anything... Try: 'Show me more future-proof career paths' or 'What AI skills should I learn?'"
                className="w-full text-[0.9rem] resize-none"
                rows={3}
                disabled={analyticsChatLoading}
                style={{ 
                  background: '#FAFAF9',
                  padding: '18px 22px',
                  border: '2px solid #D8B4FE',
                  borderRadius: '20px',
                  fontWeight: '500',
                  minHeight: '80px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                  opacity: analyticsChatLoading ? 0.6 : 1
                }}
                onFocus={(e) => e.target.style.borderColor = '#A78BFA'}
                onBlur={(e) => e.target.style.borderColor = '#D8B4FE'}
              />
              <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  type="submit"
                  disabled={analyticsChatLoading}
                  className="text-[0.85rem] hover:opacity-90 transition-opacity"
                  style={{ 
                    background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                    padding: '12px 36px',
                    borderRadius: '24px',
                    color: '#FFFFFF',
                    fontWeight: 'bold',
                    border: 'none',
                    cursor: analyticsChatLoading ? 'not-allowed' : 'pointer',
                    boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)',
                    opacity: analyticsChatLoading ? 0.6 : 1
                  }}
                >
                  {analyticsChatLoading ? 'Thinking...' : '→'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Fixed Bottom Chat Panel - For tailored results */}
      {tailoredResults && chatMessages.length > 0 && (
        <div 
          style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            background: '#FFFFFF',
            borderTop: '1px solid #E5E5E5',
            boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.08)',
            zIndex: 9999,
            padding: '20px 0'
          }}
        >
          <div className="mx-auto px-4" style={{ maxWidth: '680px' }}>
            <form onSubmit={handleChatSend}>
              <textarea
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleChatSend(e as any);
                  }
                }}
                placeholder="Ask me: What changed? OR what can I do today to be a better candidate for this job?"
                className="w-full text-[0.9rem] resize-none"
                disabled={chatLoading}
                rows={3}
                style={{ 
                  background: '#FAFAF9',
                  padding: '18px 22px',
                  border: '2px solid #D8B4FE',
                  borderRadius: '20px',
                  fontWeight: '500',
                  minHeight: '80px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                  opacity: chatLoading ? 0.6 : 1
                }}
                onFocus={(e) => e.target.style.borderColor = '#A78BFA'}
                onBlur={(e) => e.target.style.borderColor = '#D8B4FE'}
              />
              <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  type="submit"
                  disabled={chatLoading || !chatInput.trim()}
                  className="text-[0.85rem] hover:opacity-90 transition-opacity"
                  style={{ 
                    background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                    padding: '12px 36px',
                    borderRadius: '24px',
                    color: '#FFFFFF',
                    fontWeight: 'bold',
                    border: 'none',
                    cursor: chatLoading || !chatInput.trim() ? 'not-allowed' : 'pointer',
                    boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)',
                    opacity: chatLoading || !chatInput.trim() ? 0.6 : 1
                  }}
                >
                  {chatLoading ? 'Thinking...' : '→'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Fixed Bottom Chat Panel - For general career chat */}
      {chatMessages.length > 0 && !careerAnalytics && !tailoredResults && !(hasSearched && jobs.length > 0) && (
        <div 
          style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            background: '#FFFFFF',
            borderTop: '1px solid #E5E5E5',
            boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.08)',
            zIndex: 9999,
            padding: '20px 0'
          }}
        >
          <div className="max-w-[720px] mx-auto w-full" style={{ paddingLeft: '13px', paddingRight: '59px' }}>
            <div className="mb-6">
              <div className="flex flex-col items-center gap-4">
                <div className="w-full" style={{ maxWidth: '680px' }}>
                  <form onSubmit={handleGeneralChatSend}>
                    <textarea
                      value={generalChatInput}
                      onChange={(e) => setGeneralChatInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleGeneralChatSend(e as any);
                        }
                      }}
                      placeholder="Follow up..."
                      className="w-full text-[1rem] border-2 border-[#D8B4FE] focus:outline-none focus:border-[#A78BFA] transition-colors resize-none font-medium"
                      disabled={generalChatLoading}
                      rows={2}
                      style={{ 
                        background: '#FAFAF9',
                        borderRadius: '20px',
                        padding: '18px 22px',
                        minHeight: '60px',
                        outline: 'none',
                        opacity: generalChatLoading ? 0.6 : 1
                      }}
                    />
                    <div className="flex justify-center items-center" style={{ marginTop: '8px', paddingLeft: '4px', paddingRight: '4px', gap: '12px' }}>
                      <button
                        type="submit"
                        disabled={generalChatLoading || !generalChatInput.trim()}
                        style={{ 
                          background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                          padding: '12px 36px',
                          borderRadius: '24px',
                          color: '#FFFFFF',
                          fontWeight: 'bold',
                          border: 'none',
                          cursor: generalChatLoading || !generalChatInput.trim() ? 'not-allowed' : 'pointer',
                          boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)',
                          opacity: generalChatLoading || !generalChatInput.trim() ? 0.6 : 1,
                          fontSize: '0.85rem',
                          fontFamily: 'inherit',
                          lineHeight: '1',
                          textAlign: 'center',
                          textDecoration: 'none',
                          display: 'inline-block',
                          transition: 'opacity 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                          if (!generalChatLoading && generalChatInput.trim()) {
                            e.currentTarget.style.opacity = '0.9';
                          }
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.opacity = (generalChatLoading || !generalChatInput.trim()) ? '0.6' : '1';
                        }}
                      >
                        {generalChatLoading ? 'Thinking...' : '→'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Fixed Bottom Chat Panel - For action flows and job search */}
      {((activeActionFlow || aiToolsMessages.length > 0 || (hasSearched && jobs.length > 0) || selectedJobForTailoring) && !careerAnalytics && !tailoredResults) && (
        <div 
          style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            background: '#FFFFFF',
            borderTop: '1px solid #E5E5E5',
            boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.08)',
            zIndex: 9999,
            padding: '20px 0'
          }}
        >
          <div className="mx-auto px-4" style={{ maxWidth: '680px' }}>
            {selectedJobForTailoring && !activeActionFlow ? (
              <form onSubmit={handleTailorResumeSubmit}>
                <textarea
                  value={actionFlowInput}
                  onChange={(e) => setActionFlowInput(e.target.value)}
                  disabled={actionFlowLoading}
                  placeholder="Paste your resume here"
                  className="w-full text-[0.9rem] resize-none"
                  rows={2}
                  style={{ 
                    background: '#FAFAF9',
                    padding: '18px 22px',
                    border: '2px solid #D8B4FE',
                    borderRadius: '20px',
                    fontWeight: '500',
                    minHeight: '60px',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                    opacity: actionFlowLoading ? 0.6 : 1
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#A78BFA'}
                  onBlur={(e) => e.target.style.borderColor = '#D8B4FE'}
                />
                <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', position: 'relative' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedJobForTailoring(null);
                      setActionFlowInput('');
                    }}
                    className="hover:opacity-70 transition-opacity"
                    style={{ 
                      position: 'absolute',
                      left: '12px',
                      background: 'rgba(124, 58, 237, 0.1)',
                      padding: '8px 12px',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '1.2rem',
                      color: '#7C3AED',
                      lineHeight: '1',
                      borderRadius: '20px',
                      fontWeight: 'bold',
                      transition: 'all 0.2s ease',
                      boxShadow: '0 2px 8px rgba(124, 58, 237, 0.2)'
                    }}
                  >
                    ×
                  </button>
                  <button
                    type="submit"
                    disabled={actionFlowLoading}
                    className="text-[0.85rem] hover:opacity-90 transition-opacity"
                    style={{ 
                      background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                      padding: '12px 36px',
                      borderRadius: '24px',
                      color: '#FFFFFF',
                      fontWeight: 'bold',
                      border: 'none',
                      cursor: actionFlowLoading ? 'not-allowed' : 'pointer',
                      boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)',
                      opacity: actionFlowLoading ? 0.6 : 1
                    }}
                  >
                    {actionFlowLoading ? 'Tailoring...' : 'Tailor Resume'}
                  </button>
    </div>
              </form>
            ) : (activeActionFlow === 'job-search' || (hasSearched && jobs.length > 0 && !activeActionFlow)) && (
              <form onSubmit={handleJobSearch}>
                <textarea
                  value={actionFlowInput}
                  onChange={(e) => setActionFlowInput(e.target.value)}
                  disabled={actionFlowLoading}
                  placeholder={hasSearched && jobs.length > 0 ? "Search for different jobs..." : "Find a job ie. writer, data scientist, etc...."}
                  className="w-full text-[0.9rem] resize-none"
                  rows={2}
                  style={{ 
                    background: '#FAFAF9',
                    padding: '18px 22px',
                    border: '2px solid #D8B4FE',
                    borderRadius: '20px',
                    fontWeight: '500',
                    minHeight: '60px',
                    outline: 'none',
                    transition: 'border-color 0.2s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#A78BFA'}
                  onBlur={(e) => e.target.style.borderColor = '#D8B4FE'}
                />
                <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', position: 'relative' }}>
                  <button
                    type="button"
                    onClick={() => setActiveActionFlow(null)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(124, 58, 237, 0.2)';
                      e.currentTarget.style.transform = 'scale(1.05)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(124, 58, 237, 0.1)';
                      e.currentTarget.style.transform = 'scale(1)';
                    }}
                    style={{ 
                      position: 'absolute',
                      left: '12px',
                      background: 'rgba(124, 58, 237, 0.1)',
                      padding: '8px 12px',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '1.2rem',
                      color: '#7C3AED',
                      lineHeight: '1',
                      borderRadius: '20px',
                      fontWeight: 'bold',
                      transition: 'all 0.2s ease',
                      boxShadow: '0 2px 8px rgba(124, 58, 237, 0.2)'
                    }}
                  >
                    ×
                  </button>
                  <button
                    type="submit"
                    disabled={actionFlowLoading}
                    className="text-[0.85rem] hover:opacity-90 transition-opacity"
                    style={{ 
                      background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                      padding: '12px 36px',
                      borderRadius: '24px',
                      color: '#FFFFFF',
                      fontWeight: 'bold',
                      border: 'none',
                      cursor: actionFlowLoading ? 'not-allowed' : 'pointer',
                      boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)',
                      opacity: actionFlowLoading ? 0.6 : 1
                    }}
                  >
                    {actionFlowLoading ? 'Searching...' : '→'}
                  </button>
                </div>
              </form>
            )}

            {activeActionFlow === 'land-job' && (
              <form onSubmit={handleLandJob}>
                <textarea
                  value={actionFlowInput}
                  onChange={(e) => setActionFlowInput(e.target.value)}
                  disabled={actionFlowLoading}
                  placeholder="Paste the job listing here"
                  className="w-full text-[0.9rem] resize-none"
                  rows={2}
                  style={{ 
                    background: '#FAFAF9',
                    padding: '18px 22px',
                    border: '2px solid #D8B4FE',
                    borderRadius: '20px',
                    fontWeight: '500',
                    minHeight: '60px',
                    outline: 'none',
                    transition: 'border-color 0.2s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#A78BFA'}
                  onBlur={(e) => e.target.style.borderColor = '#D8B4FE'}
                />
                <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', position: 'relative' }}>
                  <button
                    type="button"
                    onClick={() => setActiveActionFlow(null)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(124, 58, 237, 0.2)';
                      e.currentTarget.style.transform = 'scale(1.05)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(124, 58, 237, 0.1)';
                      e.currentTarget.style.transform = 'scale(1)';
                    }}
                    style={{ 
                      position: 'absolute',
                      left: '12px',
                      background: 'rgba(124, 58, 237, 0.1)',
                      padding: '8px 12px',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '1.2rem',
                      color: '#7C3AED',
                      lineHeight: '1',
                      borderRadius: '20px',
                      fontWeight: 'bold',
                      transition: 'all 0.2s ease',
                      boxShadow: '0 2px 8px rgba(124, 58, 237, 0.2)'
                    }}
                  >
                    ×
                  </button>
                  <button
                    type="submit"
                    disabled={actionFlowLoading}
                    className="text-[0.85rem] hover:opacity-90 transition-opacity"
                    style={{ 
                      background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                      padding: '12px 36px',
                      borderRadius: '24px',
                      color: '#FFFFFF',
                      fontWeight: 'bold',
                      border: 'none',
                      cursor: actionFlowLoading ? 'not-allowed' : 'pointer',
                      boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)',
                      opacity: actionFlowLoading ? 0.6 : 1
                    }}
                  >
                    {actionFlowLoading ? 'Processing...' : '→'}
                  </button>
                </div>
              </form>
            )}

            {(activeActionFlow === 'ai-tools' || aiToolsMessages.length > 0) && (
              <form onSubmit={handleAiTools}>
                <textarea
                  value={actionFlowInput}
                  onChange={(e) => setActionFlowInput(e.target.value)}
                  disabled={actionFlowLoading}
                  placeholder="What do you want to build? (e.g., a pitch deck for my startup, a portfolio website)"
                  className="w-full text-[0.9rem] resize-none"
                  rows={2}
                  style={{ 
                    background: '#FAFAF9',
                    padding: '18px 22px',
                    border: '2px solid #D8B4FE',
                    borderRadius: '20px',
                    fontWeight: '500',
                    minHeight: '60px',
                    outline: 'none',
                    transition: 'border-color 0.2s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#A78BFA'}
                  onBlur={(e) => e.target.style.borderColor = '#D8B4FE'}
                />
                <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', position: 'relative' }}>
                  <button
                    type="button"
                    onClick={() => setActiveActionFlow(null)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(124, 58, 237, 0.2)';
                      e.currentTarget.style.transform = 'scale(1.05)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(124, 58, 237, 0.1)';
                      e.currentTarget.style.transform = 'scale(1)';
                    }}
                    style={{ 
                      position: 'absolute',
                      left: '12px',
                      background: 'rgba(124, 58, 237, 0.1)',
                      padding: '8px 12px',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '1.2rem',
                      color: '#7C3AED',
                      lineHeight: '1',
                      borderRadius: '20px',
                      fontWeight: 'bold',
                      transition: 'all 0.2s ease',
                      boxShadow: '0 2px 8px rgba(124, 58, 237, 0.2)'
                    }}
                  >
                    ×
                  </button>
                  <button
                    type="submit"
                    disabled={actionFlowLoading}
                    className="text-[0.85rem] hover:opacity-90 transition-opacity"
                    style={{ 
                      background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
                      padding: '12px 36px',
                      borderRadius: '24px',
                      color: '#FFFFFF',
                      fontWeight: 'bold',
                      border: 'none',
                      cursor: actionFlowLoading ? 'not-allowed' : 'pointer',
                      boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)',
                      opacity: actionFlowLoading ? 0.6 : 1
                    }}
                  >
                    {actionFlowLoading ? 'Finding...' : 'Find Tools'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
