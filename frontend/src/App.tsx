import React, { useState, useEffect, useRef } from 'react';
import { 
  PenTool, 
  Mail, 
  Settings2, 
  Send, 
  Download, 
  Copy, 
  CheckCircle2, 
  Sparkles, 
  History,
  Layout,
  Eye,
  Type,
  MoreVertical,
  ChevronRight,
  Cpu,
  Zap,
  ShieldCheck,
  Globe,
  MessageSquare,
  Briefcase,
  Linkedin
} from 'lucide-react';
import { ContentType } from './types';
import { generateContent } from './services/api';
import { BlogPostForm } from './components/forms/BlogPostForm';
import { EmailForm } from './components/forms/EmailForm';
import { SocialMediaForm } from './components/forms/SocialMediaForm';
import { LinkedInForm } from './components/forms/LinkedInForm';
import { JobApplicationForm } from './components/forms/JobApplicationForm';
import { exportToPlainText, exportToMarkdown, exportToHTML, exportToPDF } from './utils/exporters';
import ReactMarkdown from 'react-markdown';

const App = () => {
  // --- State ---
  const [contentType, setContentType] = useState<ContentType>('blog_post'); 
  const [isGenerating, setIsGenerating] = useState(false);
  const [content, setContent] = useState('');
  const [draftStatus, setDraftStatus] = useState('System Ready');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<'editor' | 'preview'>('editor');
  const [showExportMenu, setShowExportMenu] = useState(false); 
  
  // --- Content Generation ---
  const handleContentGenerated = (generatedContent: string) => {
    setContent(generatedContent);
    setIsGenerating(false);
    setDraftStatus('Draft Optimized');
    setActiveTab('editor');
  };

  const handleGenerationStart = () => {
    setIsGenerating(true);
    setContent('');
    setDraftStatus('Establishing Neural Link...');
  };

  const handleGenerationError = (error: string) => {
    setIsGenerating(false);
    setDraftStatus(`Error: ${error}`);
  };

  const copyToClipboard = () => {
    if (content) {
      navigator.clipboard.writeText(content);
      setDraftStatus('Copied to Clipboard');
      setTimeout(() => setDraftStatus('Draft Optimized'), 2000);
    }
  };

  const getFormComponent = () => {
    switch (contentType) {
      case 'blog_post':
        return (
          <BlogPostForm
            onGenerate={handleContentGenerated}
            onGenerateStart={handleGenerationStart}
            onError={handleGenerationError}
          />
        );
      case 'email':
        return (
          <EmailForm
            onGenerate={handleContentGenerated}
            onGenerateStart={handleGenerationStart}
            onError={handleGenerationError}
          />
        );
      case 'social_media':
        return (
          <SocialMediaForm
            onGenerate={handleContentGenerated}
            onGenerateStart={handleGenerationStart}
            onError={handleGenerationError}
          />
        );
      case 'linkedin':
        return (
          <LinkedInForm
            onGenerate={handleContentGenerated}
            onGenerateStart={handleGenerationStart}
            onError={handleGenerationError}
          />
        );
      case 'job_application':
        return (
          <JobApplicationForm
            onGenerate={handleContentGenerated}
            onGenerateStart={handleGenerationStart}
            onError={handleGenerationError}
          />
        );
      default:
        return null;
    }
  };

  const wordCount = content.split(/\s+/).filter(x => x.length > 0).length;

  return (
    <div className="flex h-screen bg-[#020617] text-slate-100 font-sans overflow-hidden">
      
      {/* Background Ambient Glows */}
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-cyan-600/10 rounded-full blur-[120px] pointer-events-none" />
      
      {/* --- Left Sidebar: Cyber Controls --- */}
      <aside 
        className={`${
          sidebarOpen ? 'w-[360px]' : 'w-0'
        } transition-all duration-500 ease-in-out border-r border-white/5 bg-white/5 backdrop-blur-xl flex flex-col relative z-20 overflow-hidden`}
      >
        <div className="p-8 flex-1 overflow-y-auto no-scrollbar">
          <div className="flex items-center gap-3 mb-10 group cursor-default">
            <div className="relative">
              <div className="absolute inset-0 bg-cyan-400 blur-md opacity-40 group-hover:opacity-80 transition-opacity"></div>
              <div className="relative bg-gradient-to-br from-cyan-400 to-indigo-600 p-2.5 rounded-xl text-white shadow-lg">
                <Zap size={22} fill="currentColor" />
              </div>
            </div>
            <div>
              <h1 className="font-black text-2xl tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400">
                CONTENT AI
              </h1>
              <p className="text-[10px] font-bold tracking-[0.2em] text-cyan-400 opacity-80 uppercase text-center">Neural Engine v4.0</p>
            </div>
          </div>

          {/* Type Selection */}
          <section className="mb-10">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4 block">
              Content Type
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button 
                onClick={() => setContentType('blog_post')}
                className={`group relative p-3 rounded-2xl border transition-all duration-300 ${
                  contentType === 'blog_post' 
                  ? 'border-cyan-500/50 bg-cyan-500/10 shadow-[0_0_20px_rgba(6,182,212,0.15)]' 
                  : 'border-white/5 bg-white/5 hover:border-white/20'
                }`}
              >
                <div className={`flex flex-col items-center gap-2 ${contentType === 'blog_post' ? 'text-cyan-400' : 'text-slate-400'}`}>
                  <PenTool size={18} />
                  <span className="text-[10px] font-bold uppercase tracking-wider">Blog</span>
                </div>
              </button>
              <button 
                onClick={() => setContentType('email')}
                className={`group relative p-3 rounded-2xl border transition-all duration-300 ${
                  contentType === 'email' 
                  ? 'border-violet-500/50 bg-violet-500/10 shadow-[0_0_20px_rgba(139,92,246,0.15)]' 
                  : 'border-white/5 bg-white/5 hover:border-white/20'
                }`}
              >
                <div className={`flex flex-col items-center gap-2 ${contentType === 'email' ? 'text-violet-400' : 'text-slate-400'}`}>
                  <Mail size={18} />
                  <span className="text-[10px] font-bold uppercase tracking-wider">Email</span>
                </div>
              </button>
              <button 
                onClick={() => setContentType('social_media')}
                className={`group relative p-3 rounded-2xl border transition-all duration-300 ${
                  contentType === 'social_media' 
                  ? 'border-pink-500/50 bg-pink-500/10 shadow-[0_0_20px_rgba(236,72,153,0.15)]' 
                  : 'border-white/5 bg-white/5 hover:border-white/20'
                }`}
              >
                <div className={`flex flex-col items-center gap-2 ${contentType === 'social_media' ? 'text-pink-400' : 'text-slate-400'}`}>
                  <MessageSquare size={18} />
                  <span className="text-[10px] font-bold uppercase tracking-wider">Social</span>
                </div>
              </button>
              <button 
                onClick={() => setContentType('linkedin')}
                className={`group relative p-3 rounded-2xl border transition-all duration-300 ${
                  contentType === 'linkedin' 
                  ? 'border-blue-500/50 bg-blue-500/10 shadow-[0_0_20px_rgba(59,130,246,0.15)]' 
                  : 'border-white/5 bg-white/5 hover:border-white/20'
                }`}
              >
                <div className={`flex flex-col items-center gap-2 ${contentType === 'linkedin' ? 'text-blue-400' : 'text-slate-400'}`}>
                  <Linkedin size={18} />
                  <span className="text-[10px] font-bold uppercase tracking-wider">LinkedIn</span>
                </div>
              </button>
              <button 
                onClick={() => setContentType('job_application')}
                className={`group relative p-3 rounded-2xl border transition-all duration-300 col-span-2 ${
                  contentType === 'job_application' 
                  ? 'border-emerald-500/50 bg-emerald-500/10 shadow-[0_0_20px_rgba(16,185,129,0.15)]' 
                  : 'border-white/5 bg-white/5 hover:border-white/20'
                }`}
              >
                <div className={`flex flex-col items-center gap-2 ${contentType === 'job_application' ? 'text-emerald-400' : 'text-slate-400'}`}>
                  <Briefcase size={18} />
                  <span className="text-[10px] font-bold uppercase tracking-wider">Job Application</span>
                </div>
              </button>
            </div>
          </section>

          {/* Form Component */}
          <section className="space-y-6">
            {getFormComponent()}
          </section>
        </div>
      </aside>

      {/* --- Main Workspace --- */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#020617] relative">
        {/* Pattern Overlay */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '32px 32px' }}></div>

        {/* HUD Header */}
        <header className="h-20 border-b border-white/5 flex items-center justify-between px-10 bg-black/40 backdrop-blur-md z-10 sticky top-0">
          <div className="flex items-center gap-6">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2.5 hover:bg-white/5 rounded-xl text-slate-500 hover:text-cyan-400 transition-all border border-transparent hover:border-white/10"
            >
              <Layout size={20} />
            </button>
            <div className="flex flex-col">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Status</span>
              <div className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)] ${isGenerating ? 'bg-amber-400 shadow-amber-400 animate-pulse' : 'bg-emerald-500 shadow-emerald-500'}`} />
                <span className="text-xs font-bold text-slate-300 uppercase tracking-tighter">{isGenerating ? 'AI is writing...' : draftStatus}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden lg:flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/5">
              <button 
                onClick={() => setActiveTab('editor')}
                className={`px-4 py-2 text-[10px] font-black rounded-lg uppercase tracking-widest transition-all ${
                  activeTab === 'editor' ? 'bg-white/10 text-cyan-400 shadow-inner' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                Editor
              </button>
              <button 
                onClick={() => setActiveTab('preview')}
                className={`px-4 py-2 text-[10px] font-black rounded-lg uppercase tracking-widest transition-all ${
                  activeTab === 'preview' ? 'bg-white/10 text-cyan-400 shadow-inner' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                Preview
              </button>
            </div>
            
            <div className="h-8 w-px bg-white/5 mx-2" />

            <button 
              onClick={copyToClipboard}
              className="flex items-center gap-2 px-5 py-2.5 text-xs font-bold text-slate-400 hover:text-white hover:bg-white/5 rounded-xl transition-all border border-white/5 hover:border-white/10"
              disabled={!content}
            >
              <Copy size={16} />
              Copy
            </button>
            {content && (
              <div className="relative">
                <button 
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  className="flex items-center gap-2 px-5 py-2.5 text-xs font-bold bg-white text-black hover:bg-cyan-400 rounded-xl transition-all shadow-xl shadow-white/5"
                >
                  <Download size={16} />
                  Export
                </button>
                {showExportMenu && (
                  <>
                    <div 
                      className="fixed inset-0 z-40" 
                      onClick={() => setShowExportMenu(false)}
                    />
                    <div className="absolute right-0 mt-2 w-48 bg-[#0b0f1a] border border-white/10 rounded-xl shadow-2xl z-50">
                      <button 
                        onClick={() => {
                          exportToPlainText(content);
                          setShowExportMenu(false);
                        }}
                        className="w-full text-left px-4 py-3 text-xs text-slate-300 hover:bg-white/5 hover:text-cyan-400 transition-all rounded-t-xl"
                      >
                        Export TXT
                      </button>
                      <button 
                        onClick={() => {
                          exportToMarkdown(content);
                          setShowExportMenu(false);
                        }}
                        className="w-full text-left px-4 py-3 text-xs text-slate-300 hover:bg-white/5 hover:text-cyan-400 transition-all"
                      >
                        Export MD
                      </button>
                      <button 
                        onClick={() => {
                          exportToHTML(content);
                          setShowExportMenu(false);
                        }}
                        className="w-full text-left px-4 py-3 text-xs text-slate-300 hover:bg-white/5 hover:text-cyan-400 transition-all"
                      >
                        Export HTML
                      </button>
                      <button 
                        onClick={async () => {
                          await exportToPDF(content, contentType);
                          setShowExportMenu(false);
                        }}
                        className="w-full text-left px-4 py-3 text-xs text-slate-300 hover:bg-white/5 hover:text-cyan-400 transition-all rounded-b-xl"
                      >
                        Export PDF
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </header>

        {/* Editor Zone */}
        <div className="flex-1 overflow-y-auto p-12 custom-scrollbar">
          <div className="max-w-4xl mx-auto">
            {!content && !isGenerating ? (
              <div className="py-32 flex flex-col items-center justify-center text-center">
                <div className="relative mb-8">
                  <div className="absolute inset-0 bg-cyan-500/20 blur-2xl rounded-full"></div>
                  <div className="relative bg-white/5 border border-white/10 w-24 h-24 rounded-3xl flex items-center justify-center">
                    <Globe className="text-slate-600 animate-[spin_10s_linear_infinite]" size={40} />
                  </div>
                </div>
                <h2 className="text-3xl font-black text-white mb-4 tracking-tighter uppercase italic">Ready to write?</h2>
                <p className="text-slate-500 max-w-md text-sm leading-relaxed mb-12">
                  Configure your content settings in the sidebar and click generate to start your draft.
                </p>
                <div className="flex gap-4">
                  <div className="px-4 py-2 bg-white/5 border border-white/5 rounded-full text-[10px] font-bold text-slate-500 uppercase tracking-widest">Latency: 24ms</div>
                  <div className="px-4 py-2 bg-white/5 border border-white/5 rounded-full text-[10px] font-bold text-slate-500 uppercase tracking-widest">Uptime: 99.9%</div>
                </div>
              </div>
            ) : (
              <div className="relative group">
                {/* Neon Border Effect */}
                <div className="absolute -inset-[1px] bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-[2rem] blur-[2px] opacity-30 group-hover:opacity-100 transition duration-1000"></div>
                
                <div className="relative bg-[#0b0f1a]/80 backdrop-blur-2xl p-16 rounded-[2rem] shadow-2xl min-h-[700px] border border-white/10">
                  {activeTab === 'editor' ? (
                    <textarea 
                      value={content}
                      onChange={(e) => setContent(e.target.value)}
                      className="w-full h-full min-h-[600px] bg-transparent outline-none resize-none font-mono text-lg leading-loose text-cyan-50/90 selection:bg-cyan-500/40"
                      spellCheck="false"
                      placeholder="Generated content will appear here..."
                    />
                  ) : (
                    <div className="prose prose-invert max-w-none text-cyan-50/90 prose-headings:text-cyan-400 prose-p:text-slate-200 prose-strong:text-white prose-code:text-cyan-300">
                      <ReactMarkdown>{content || 'No content to preview'}</ReactMarkdown>
                    </div>
                  )}
                  {isGenerating && (
                    <div className="inline-block w-3 h-6 bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)] animate-pulse ml-2 align-middle" />
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* HUD Footer */}
        <footer className="h-12 border-t border-white/5 px-10 flex items-center justify-between text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] bg-black/40 backdrop-blur-md">
          <div className="flex gap-8">
             <div className="flex items-center gap-2">
                <ShieldCheck size={12} className="text-emerald-500" />
                <span>Secure Encryption Active</span>
             </div>
             <div className="flex items-center gap-2">
                <span className="text-white/20">|</span>
                <span>Words: {wordCount}</span>
             </div>
          </div>
          <div className="flex items-center gap-6">
            <span className="animate-pulse">LLM_CORE_V4</span>
            <div className="flex gap-1">
              {[1,2,3,4,5].map(i => (
                <div key={i} className={`h-3 w-0.5 rounded-full ${i < 4 ? 'bg-cyan-500' : 'bg-white/10'}`}></div>
              ))}
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default App;
