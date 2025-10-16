'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { API_URL } from '../../config';

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
  salary_min?: number;
  salary_max?: boolean;
  salary_is_predicted?: boolean;
  job_type?: string;
}

export default function TailorPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobParam = searchParams?.get('job');
  
  const [job, setJob] = useState<Job | null>(null);
  const [jobListing, setJobListing] = useState('');
  const [resume, setResume] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);

  useEffect(() => {
    if (jobParam) {
      try {
        const jobData = JSON.parse(decodeURIComponent(jobParam));
        setJob(jobData);
        setJobListing(jobData.description);
      } catch (error) {
        console.error('Error parsing job data:', error);
        setJobListing(jobParam);
      }
    }
  }, [jobParam]);

  const handleTailor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobListing.trim() || !resume.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/quick-tailor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_description: jobListing,
          resume_text: resume
        })
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (type: 'resume' | 'cover_letter') => {
    try {
      const response = await fetch(`${API_URL}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: type === 'resume' ? results.tailored_resume : results.cover_letter,
          filename: type === 'resume' ? 'tailored_resume.docx' : 'cover_letter.docx'
        })
      });
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = type === 'resume' ? 'tailored_resume.docx' : 'cover_letter.docx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading file:', error);
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
        
        {job && (
          <h1 className="text-[1.6rem] text-center mb-6" style={{ fontWeight: '800', color: '#0A0A0A' }}>
            {job.title} at {job.company}
          </h1>
        )}

        {results ? (
          /* Results Display */
          <div className="space-y-6">
            {/* Tailored Resume */}
            <div 
              className="bg-white border border-[#E5E5E5] rounded-lg p-6"
              style={{ 
                background: 'linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%)',
                border: '2px solid #E2E8F0'
              }}
            >
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-[1.2rem] font-bold text-[#313338]">Your Tailored Resume</h2>
                <button
                  onClick={() => handleDownload('resume')}
                  className="px-4 py-2 text-[0.9rem] bg-[#7C3AED] text-white rounded-lg hover:opacity-90 transition-opacity"
                >
                  Download
                </button>
              </div>
              <div 
                className="text-[0.9rem] leading-relaxed"
                style={{ color: '#374151', lineHeight: '1.6' }}
                dangerouslySetInnerHTML={{ __html: results.tailored_resume.replace(/\n/g, '<br>') }}
              />
            </div>

            {/* Cover Letter */}
            <div 
              className="bg-white border border-[#E5E5E5] rounded-lg p-6"
              style={{ 
                background: 'linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%)',
                border: '2px solid #E2E8F0'
              }}
            >
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-[1.2rem] font-bold text-[#313338]">Cover Letter</h2>
                <button
                  onClick={() => handleDownload('cover_letter')}
                  className="px-4 py-2 text-[0.9rem] bg-[#7C3AED] text-white rounded-lg hover:opacity-90 transition-opacity"
                >
                  Download
                </button>
              </div>
              <div 
                className="text-[0.9rem] leading-relaxed"
                style={{ color: '#374151', lineHeight: '1.6' }}
                dangerouslySetInnerHTML={{ __html: results.cover_letter.replace(/\n/g, '<br>') }}
              />
            </div>

            {/* Follow-up Chat */}
            <div className="mt-8">
              <form onSubmit={async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target as HTMLFormElement);
                const question = formData.get('question') as string;
                
                setLoading(true);
                try {
                  const response = await fetch(`${API_URL}/coach`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      question: question,
                      context: `Job: ${jobListing}\nResume: ${resume}\nTailored Resume: ${results.tailored_resume}`
                    })
                  });
                  const data = await response.json();
                  // Handle response - could display in a chat interface
                  alert(data.reply);
                } catch (error) {
                  console.error('Error:', error);
                } finally {
                  setLoading(false);
                }
              }}>
                <textarea
                  name="question"
                  placeholder="Ask me: What changed? OR what can I do today to be a better candidate for this job?"
                  className="w-full text-[0.9rem] border-2 border-[#D8B4FE] focus:outline-none focus:border-[#A78BFA] transition-colors resize-none font-medium"
                  style={{ borderRadius: '20px', padding: '18px 22px', background: '#FAFAF9', minHeight: '60px' }}
                  rows={2}
                />
                <div className="flex justify-center mt-2">
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
                    {loading ? 'Thinking...' : '→'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : (
          /* Input Form */
          <form onSubmit={handleTailor}>
            <div className="space-y-6">
              <div>
                <label className="block text-[0.9rem] font-semibold text-[#313338] mb-2">
                  Job Listing
                </label>
                <textarea
                  value={jobListing}
                  onChange={(e) => setJobListing(e.target.value)}
                  placeholder="Paste the job listing here..."
                  className="w-full text-[0.9rem] border-2 border-[#D8B4FE] focus:outline-none focus:border-[#A78BFA] transition-colors resize-none font-medium"
                  style={{ borderRadius: '20px', padding: '18px 22px', background: '#FAFAF9' }}
                  rows={6}
                />
              </div>

              <div>
                <label className="block text-[0.9rem] font-semibold text-[#313338] mb-2">
                  Your Resume
                </label>
                <textarea
                  value={resume}
                  onChange={(e) => setResume(e.target.value)}
                  placeholder="Paste your resume here..."
                  className="w-full text-[0.9rem] border-2 border-[#D8B4FE] focus:outline-none focus:border-[#A78BFA] transition-colors resize-none font-medium"
                  style={{ borderRadius: '20px', padding: '18px 22px', background: '#FAFAF9' }}
                  rows={8}
                />
              </div>

              <div className="flex justify-center">
                <button
                  type="submit"
                  disabled={loading || !jobListing.trim() || !resume.trim()}
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
                    opacity: (loading || !jobListing.trim() || !resume.trim()) ? 0.6 : 1
                  }}
                >
                  {loading ? 'Tailoring...' : 'Tailor My Resume'}
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </main>
  );
}
