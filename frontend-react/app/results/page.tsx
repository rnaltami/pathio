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
  const [activeTab, setActiveTab] = useState<'resume' | 'cover' | 'changes' | 'tasks'>('resume');
  const [completedTasks, setCompletedTasks] = useState<Set<string>>(new Set());
  const [isUpdating, setIsUpdating] = useState(false);

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
    } else {
      // No results, redirect to home
      router.push('/');
    }
  }, [router]);

  const extractSkillsFromTask = (task: string): string[] => {
    // Extract skills from common task patterns
    const skillPatterns = [
      /add|include|mention|highlight.*?(?:skills?|technologies?|tools?)[:\s]+([^.]+)/i,
      /experience with ([^.]+)/i,
      /knowledge of ([^.]+)/i,
      /proficiency in ([^.]+)/i,
    ];

    for (const pattern of skillPatterns) {
      const match = task.match(pattern);
      if (match) {
        // Split by common separators and clean up
        return match[1]
          .split(/,|and|\||&/)
          .map(s => s.trim())
          .filter(s => s.length > 2 && s.length < 30);
      }
    }

    return [];
  };

  const updateResumeWithTask = (resume: string, task: string, completedTasksList: Set<string>): string => {
    const skills = extractSkillsFromTask(task);
    let updatedResume = resume;
    const lines = resume.split('\n');
    
    // Find or create "Job-Specific Highlights" section at the top (after summary/name)
    let highlightsSectionIndex = -1;
    for (let i = 0; i < lines.length; i++) {
      if (/^#{1,3}\s*Job-Specific Highlights/i.test(lines[i])) {
        highlightsSectionIndex = i;
        break;
      }
    }

    // Collect all completed tasks with their extracted skills
    const allCompletedTasks = Array.from(completedTasksList);
    const allSkills: string[] = [];
    
    allCompletedTasks.forEach(t => {
      const taskSkills = extractSkillsFromTask(t);
      allSkills.push(...taskSkills);
    });

    if (highlightsSectionIndex === -1) {
      // Create new section after the first heading (usually name) or after summary
      let insertIndex = 3; // Default after name
      for (let i = 0; i < lines.length; i++) {
        if (/^#{1,3}\s*(?:Experience|Work Experience|Professional Experience|Relevant Skills)/i.test(lines[i])) {
          insertIndex = i;
          break;
        }
      }
      
      const highlightsContent = [
        '',
        '### Job-Specific Highlights',
        '',
      ];

      // Show unique skills from all completed tasks
      if (allSkills.length > 0) {
        const uniqueSkills = Array.from(new Set(allSkills));
        highlightsContent.push(`✓ Additional Skills: ${uniqueSkills.join(' • ')}`);
      }

      // Show completed tasks
      highlightsContent.push(`✓ Completed ${allCompletedTasks.length} improvement${allCompletedTasks.length > 1 ? 's' : ''} to strengthen this application`);
      highlightsContent.push('');
      
      lines.splice(insertIndex, 0, ...highlightsContent);
    } else {
      // Update existing highlights section
      // Find the end of the section
      let sectionEnd = highlightsSectionIndex + 1;
      while (sectionEnd < lines.length && !lines[sectionEnd].match(/^#{1,3}\s/)) {
        sectionEnd++;
      }

      // Replace section content
      const newContent = [''];
      if (allSkills.length > 0) {
        const uniqueSkills = Array.from(new Set(allSkills));
        newContent.push(`✓ Additional Skills: ${uniqueSkills.join(' • ')}`);
      }
      newContent.push(`✓ Completed ${allCompletedTasks.length} improvement${allCompletedTasks.length > 1 ? 's' : ''} to strengthen this application`);
      newContent.push('');

      lines.splice(highlightsSectionIndex + 1, sectionEnd - highlightsSectionIndex - 1, ...newContent);
    }

    return lines.join('\n');
  };

  const handleTaskComplete = async (task: string, isDoNow: boolean) => {
    if (!results) return;

    const newCompleted = new Set(completedTasks);
    if (newCompleted.has(task)) {
      newCompleted.delete(task);
      setCompletedTasks(newCompleted);
      return;
    }

    newCompleted.add(task);
    setCompletedTasks(newCompleted);

    // Update the resume organically
    setIsUpdating(true);
    
    // Small delay to show the "updating" message
    await new Promise(resolve => setTimeout(resolve, 500));

    const updatedResume = updateResumeWithTask(results.tailored_resume_md, task, newCompleted);
    
    const updatedResults = {
      ...results,
      tailored_resume_md: updatedResume,
    };

    setResults(updatedResults);
    
    // Save to localStorage
    localStorage.setItem('tailoredResults', JSON.stringify(updatedResults));
    
    setIsUpdating(false);
    
    // Auto-switch to resume tab to show the changes
    setActiveTab('resume');
  };

  const handleExport = async (type: 'resume' | 'cover') => {
    if (!results) return;

    try {
      const response = await fetch(`${API_URL}/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tailored_resume_md: results.tailored_resume_md,
          cover_letter_md: results.cover_letter_md,
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
              onClick={() => setActiveTab('resume')}
              className={`pb-3 text-[0.9rem] transition-colors whitespace-nowrap ${
                activeTab === 'resume'
                  ? 'text-[#2563eb] border-b-2 border-[#2563eb]'
                  : 'text-[#707070] hover:text-[#303030]'
              }`}
            >
              Tailored Resume
            </button>
            <button
              onClick={() => setActiveTab('cover')}
              className={`pb-3 text-[0.9rem] transition-colors whitespace-nowrap ${
                activeTab === 'cover'
                  ? 'text-[#2563eb] border-b-2 border-[#2563eb]'
                  : 'text-[#707070] hover:text-[#303030]'
              }`}
            >
              Cover Letter
            </button>
            <button
              onClick={() => setActiveTab('changes')}
              className={`pb-3 text-[0.9rem] transition-colors whitespace-nowrap ${
                activeTab === 'changes'
                  ? 'text-[#2563eb] border-b-2 border-[#2563eb]'
                  : 'text-[#707070] hover:text-[#303030]'
              }`}
            >
              What Changed
            </button>
            <button
              onClick={() => setActiveTab('tasks')}
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
                    📋 Do Before Applying {isUpdating && <span className="text-[0.8rem] text-[#2563eb]">(Updating resume...)</span>}
                  </h3>
                  <ul className="space-y-4">
                    {results.insights.do_now.map((task, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={completedTasks.has(task)}
                          onChange={() => handleTaskComplete(task, true)}
                          className="mt-1 w-4 h-4 text-[#2563eb] border-gray-300 rounded focus:ring-[#2563eb] cursor-pointer flex-shrink-0"
                        />
                        <div className="flex-1">
                          <span className={`text-[0.85rem] block mb-1 ${completedTasks.has(task) ? 'line-through text-[#707070]' : 'text-[#303030]'}`}>
                            {task}
                          </span>
                          {!completedTasks.has(task) && (
                            <a
                              href={`/chat?task=${encodeURIComponent(task)}`}
                              className="text-[0.8rem] text-[#2563eb] hover:opacity-70 transition-opacity"
                              onClick={(e) => e.stopPropagation()}
                            >
                              Show me how →
                            </a>
                          )}
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
                        <input
                          type="checkbox"
                          checked={completedTasks.has(task)}
                          onChange={() => handleTaskComplete(task, false)}
                          className="mt-1 w-4 h-4 text-[#2563eb] border-gray-300 rounded focus:ring-[#2563eb] cursor-pointer flex-shrink-0"
                        />
                        <div className="flex-1">
                          <span className={`text-[0.85rem] block mb-1 ${completedTasks.has(task) ? 'line-through text-[#707070]' : 'text-[#303030]'}`}>
                            {task}
                          </span>
                          {!completedTasks.has(task) && (
                            <a
                              href={`/chat?task=${encodeURIComponent(task)}`}
                              className="text-[0.8rem] text-[#2563eb] hover:opacity-70 transition-opacity"
                              onClick={(e) => e.stopPropagation()}
                            >
                              Show me how →
                            </a>
                          )}
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

          <button
            onClick={() => router.push('/')}
            className="w-full px-4 py-3 text-center text-[0.95rem] border border-[#E0E0E0] text-[#303030] rounded-lg hover:bg-[#F5F5F5] transition-colors"
          >
            Search for More Jobs
          </button>
        </div>
      </div>
    </main>
  );
}

