'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

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

export default function JobDetailPage() {
  const [job, setJob] = useState<Job | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Get job from localStorage
    const savedJob = localStorage.getItem('selectedJob');
    if (savedJob) {
      setJob(JSON.parse(savedJob));
    }
  }, []);

  if (!job) {
    return (
      <main className="min-h-screen bg-white">
        <div className="max-w-[680px] mx-auto px-4 py-8">
          <div className="text-[0.9rem] text-[#707070]">Loading...</div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-white">
      <div className="max-w-[680px] mx-auto px-4 py-8">
        {/* Header with logo */}
        <header className="text-center mb-8">
          <a href="/">
            <h1 className="text-3xl font-normal text-[#303030] tracking-tight cursor-pointer hover:opacity-70 transition-opacity">
              pathio
            </h1>
          </a>
        </header>

        {/* Back button */}
        <button
          onClick={() => router.back()}
          className="mb-6 text-[0.9rem] text-[#707070] hover:opacity-70 transition-opacity"
        >
          ← Back to results
        </button>

        {/* Job Details */}
        <div className="mb-8">
          {/* Job Title */}
          <h2 className="text-[1.5rem] font-medium text-[#202020] mb-3">
            {job.title}
          </h2>

          {/* Company Info */}
          <div className="text-[0.9rem] text-[#707070] mb-6">
            {job.company} • {job.location} • {job.type}
          </div>

          {/* Description */}
          <div className="mb-6">
            <h3 className="text-[1rem] font-medium text-[#202020] mb-3">Description</h3>
            <p className="text-[0.9rem] text-[#303030] leading-relaxed whitespace-pre-wrap">
              {job.description}
            </p>
          </div>

          {/* Requirements */}
          {job.requirements && job.requirements.length > 0 && (
            <div className="mb-8">
              <h3 className="text-[1rem] font-medium text-[#202020] mb-3">Requirements</h3>
              <ul className="list-disc list-inside space-y-2">
                {job.requirements.map((req, idx) => (
                  <li key={idx} className="text-[0.9rem] text-[#303030]">
                    {req}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="space-y-3 pt-6 border-t border-[#E0E0E0]">
          {job.url && (
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full px-4 py-3 text-center text-[0.95rem] bg-[#202020] text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              Apply on {job.company}'s site →
            </a>
          )}
          
          <button
            onClick={() => {
              // Store job for application flow
              localStorage.setItem('jobToApply', JSON.stringify(job));
              router.push('/apply');
            }}
            className="block w-full px-4 py-3 text-center text-[0.95rem] border border-[#202020] text-[#202020] rounded-lg hover:opacity-70 transition-opacity"
          >
            Tailor my resume & cover letter for this job
          </button>
        </div>
      </div>
    </main>
  );
}

