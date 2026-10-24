import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, BookOpen, Mic, ShieldCheck, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-white font-sans">
      {/* Navigation */}
      <nav className="flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="bg-primary-600 p-2 rounded-lg text-white">
            <Sparkles size={20} />
          </div>
          <span className="text-lg font-bold text-slate-800">OBC EduAssistant</span>
        </div>
        <Link
          to="/chat"
          className="bg-primary-600 text-white px-5 py-2 rounded-full text-sm font-medium hover:bg-primary-700 transition-all shadow-sm"
        >
          Launch Chat
        </Link>
      </nav>

      {/* Hero Section */}
      <section className="px-6 py-20 max-w-7xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="inline-block px-4 py-1.5 mb-6 text-xs font-semibold tracking-wide text-primary-600 uppercase bg-primary-50 rounded-full border border-primary-100">
            Now powered by Llama 3.2
          </span>
          <h1 className="text-5xl md:text-7xl font-extrabold text-slate-900 mb-6 tracking-tight">
            Your Gateway to <br />
            <span className="text-primary-600">OBC Education</span> Support
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-10 leading-relaxed">
            Instantly access information about scholarships, hostel guidelines, and education schemes
            specifically for OBC students in Maharashtra. Grounded in official government records.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/chat"
              className="w-full sm:w-auto px-8 py-4 bg-primary-600 text-white rounded-2xl font-semibold text-lg hover:bg-primary-700 transition-all shadow-xl flex items-center justify-center gap-2 group"
            >
              Start Chatting <ChevronRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <button className="w-full sm:w-auto px-8 py-4 bg-white text-slate-600 border border-slate-200 rounded-2xl font-semibold text-lg hover:bg-slate-50 transition-all">
              Learn More
            </button>
          </div>
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="px-6 py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">Why Use EduAssistant?</h2>
            <p className="text-slate-500">Engineered for accuracy, accessibility, and speed.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: <BookOpen className="text-primary-600" />,
                title: "Grounded Knowledge",
                desc: "Unlike generic AI, we use RAG to ensure every answer is based on official Maharashtra govt records."
              },
              {
                icon: <Mic className="text-primary-600" />,
                title: "Voice First",
                desc: "Communicate naturally in English, Hindi, or Marathi with our integrated voice-to-voice pipeline."
              },
              {
                icon: <ShieldCheck className="text-primary-600" />,
                title: "100% Local & Private",
                desc: "Your data never leaves your machine. Powered by Ollama for maximum privacy and security."
              }
            ].map((feat, i) => (
              <div key={i} className="bg-white p-8 rounded-3xl border border-slate-200 hover:shadow-xl transition-shadow">
                <div className="bg-primary-50 w-12 h-12 rounded-xl flex items-center justify-center mb-6">
                  {feat.icon}
                </div>
                <h3 className="text-xl font-bold text-slate-800 mb-3">{feat.title}</h3>
                <p className="text-slate-500 leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-12 border-t border-slate-200 text-center text-slate-400 text-sm">
        <p>© 2026 OBC EduAssistant. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default LandingPage;
