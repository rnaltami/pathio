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
      <div className="max-w-[680px] mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-12">
          <a href="/">
            <h1 className="text-3xl font-normal text-[#303030] tracking-tight cursor-pointer hover:opacity-70 transition-opacity">
              pathio
            </h1>
          </a>
        </header>

        {/* Title */}
        <div className="mb-8">
          <h2 className="text-xl font-medium text-[#202020] mb-2">
            Application Preparation
          </h2>
          {job && (
            <p className="text-[0.9rem] text-[#707070]">
              Preparing for: <span className="text-[#2563eb]">{job.title}</span> at {job.company}
            </p>
          )}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Job Description Field */}
          <div>
            <label className="block text-[0.95rem] font-medium text-[#202020] mb-2">
              Job Description
            </label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here..."
              className="w-full h-48 px-4 py-3 text-[0.9rem] border border-[#E0E0E0] rounded-lg focus:outline-none focus:border-[#E0E0E0] resize-y"
              required
            />
          </div>

          {/* Resume Field */}
          <div>
            <label className="block text-[0.95rem] font-medium text-[#202020] mb-2">
              Your Current Resume
            </label>
            <textarea
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              placeholder="Paste your resume here..."
              className="w-full h-64 px-4 py-3 text-[0.9rem] border border-[#E0E0E0] rounded-lg focus:outline-none focus:border-[#E0E0E0] resize-y"
              required
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-3 text-center text-[0.95rem] bg-[#2563eb] text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Tailor Resume & Generate Cover Letter →'}
          </button>

          {/* Back Link */}
          <div className="text-center">
            <button
              type="button"
              onClick={() => router.back()}
              className="text-[0.9rem] text-[#707070] hover:opacity-70 transition-opacity"
            >
              ← Back to job search
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}

