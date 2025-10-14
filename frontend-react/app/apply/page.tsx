'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
}

export default function ApplyPage() {
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [resume, setResume] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load job from localStorage
    const savedJob = localStorage.getItem('jobToApply');
    if (savedJob) {
      const jobData = JSON.parse(savedJob);
      console.log('Loaded job data:', jobData); // Debug log
      setJob(jobData);
      
      // Pre-fill job description with all details
      const fullJobDescription = `${jobData.title || 'Unknown Position'} at ${jobData.company || 'Unknown Company'}

Location: ${jobData.location || 'Not specified'}
Type: ${jobData.type || 'Not specified'}

Description:
${jobData.description || 'No description available'}
${jobData.requirements && jobData.requirements.length > 0 ? `\n\nRequirements:\n${jobData.requirements.map((req: string) => `• ${req}`).join('\n')}` : ''}`;
      
      console.log('Full job description:', fullJobDescription); // Debug log
      setJobDescription(fullJobDescription);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobDescription.trim() || !resume.trim()) {
      alert('Please fill in both fields');
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch(`${API_URL}/quick-tailor`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_text: jobDescription,
          resume_text: resume,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to tailor resume');
      }

      const data = await response.json();
      
      // Store the results and navigate to results page
      localStorage.setItem('tailoredResults', JSON.stringify(data));
      router.push('/results');
      
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred while tailoring your resume. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-white">
      <div className="max-w-[720px] mx-auto px-4 pt-20 pb-8">
        {/* Header */}
        <header className="text-center mb-18">
          <a href="/">
            <h1 className="text-[2rem] font-light text-[#202020] tracking-tight cursor-pointer hover:opacity-60 transition-opacity">
              pathio
            </h1>
          </a>
        </header>

        {/* Back Button */}
        <button
          onClick={() => router.back()}
          className="mb-8 text-[0.85rem] text-[#909090] hover:text-[#505050] transition-colors"
        >
          ← Back
        </button>

        {/* Title */}
        <div className="mb-10">
          <h2 className="text-[1.5rem] font-normal text-[#202020] mb-3">
            Get this job
          </h2>
          {job && (
            <p className="text-[0.9rem] text-[#606060]">
              {job.title} at {job.company}
            </p>
          )}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Job Description Field */}
          <div>
            <label className="block text-[0.9rem] text-[#505050] mb-3">
              Job Details
            </label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here..."
              className="w-full h-48 px-4 py-3 text-[0.9rem] border border-[#E0E0E0] rounded-lg focus:outline-none focus:border-[#B0B0B0] resize-y transition-colors"
              required
            />
          </div>

          {/* Resume Field */}
          <div>
            <label className="block text-[0.9rem] text-[#505050] mb-3">
              Your Resume
            </label>
            <textarea
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              placeholder="Paste your current resume here..."
              className="w-full h-64 px-4 py-3 text-[0.9rem] border border-[#E0E0E0] rounded-lg focus:outline-none focus:border-[#B0B0B0] resize-y transition-colors"
              required
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full px-6 py-4 text-center text-[0.95rem] bg-[#202020] text-white rounded-full hover:opacity-80 transition-opacity disabled:opacity-50"
          >
            {loading ? 'Tailoring your application...' : 'Generate tailored resume & cover letter'}
          </button>
        </form>
      </div>
    </main>
  );
}

