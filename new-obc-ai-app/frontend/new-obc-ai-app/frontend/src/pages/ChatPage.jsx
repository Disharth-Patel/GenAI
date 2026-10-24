import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Send,
  User,
  Bot,
  BookOpen,
  Loader2,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Sparkles,
  ChevronRight,
  ArrowLeft
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

const API_BASE = "http://localhost:8000";

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [language, setLanguage] = useState('en');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const scrollRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsRecording(false);
        handleSend(transcript);
      };

      recognitionRef.current.onerror = () => setIsRecording(false);
      recognitionRef.current.onend = () => setIsRecording(false);
    }
  }, []);

  const toggleRecording = () => {
    if (!recognitionRef.current) return alert("Speech recognition not supported.");
    if (isRecording) {
      recognitionRef.current.stop();
    } else {
      const langMap = { 'en': 'en-IN', 'hi': 'hi-IN', 'mr': 'mr-IN' };
      recognitionRef.current.lang = langMap[language] || 'en-IN';
      recognitionRef.current.start();
      setIsRecording(true);
    }
  };

  const speakText = (text) => {
    if (!synthRef.current) return;
    synthRef.current.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const langMap = { 'en': 'en-IN', 'hi': 'hi-IN', 'mr': 'mr-IN' };
    utterance.lang = langMap[language] || 'en-IN';
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    synthRef.current.speak(utterance);
  };

  const handleSend = async (text = input) => {
    if (!text.trim()) return;
    const userMsg = { role: 'user', content: text, timestamp: new Date().toLocaleTimeString() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const { data } = await axios.post(`${API_BASE}/api/chat/`, { message: text, language });
      const aiMsg = { role: 'ai', content: data.answer, sources: data.sources, timestamp: new Date().toLocaleTimeString() };
      setMessages(prev => [...prev, aiMsg]);
      speakText(data.answer);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: "Connection error. Is the backend running?", timestamp: new Date().toLocaleTimeString() }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      <header className="h-16 glass-panel sticky top-0 z-10 flex items-center justify-between px-6 border-b border-slate-200">
        <div className="flex items-center gap-4">
          <Link to="/" className="p-2 hover:bg-slate-100 rounded-full transition-colors">
            <ArrowLeft size={20} className="text-slate-500" />
          </Link>
          <div className="flex items-center gap-2">
            <div className="bg-primary-600 p-2 rounded-lg text-white">
              <Sparkles size={20} />
            </div>
            <h1 className="text-lg font-bold tracking-tight text-slate-800">
              OBC <span className="text-primary-600">EduAssistant</span>
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {isSpeaking && (
            <button onClick={() => { synthRef.current.cancel(); setIsSpeaking(false); }}
              className="flex items-center gap-2 text-xs bg-red-100 text-red-600 px-3 py-1 rounded-full animate-pulse font-medium">
              <VolumeX size={14} /> Stop Audio
            </button>
          )}
          <select value={language} onChange={(e) => setLanguage(e.target.value)}
            className="bg-white border border-slate-200 text-sm rounded-full px-3 py-1 outline-none">
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="mr">मराठी</option>
          </select>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-4 md:p-8 max-w-4xl mx-auto w-full">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center py-20">
            <div className="bg-primary-100 p-4 rounded-full text-primary-600 mb-4"><Bot size={48} /></div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">How can I help you today?</h2>
            <p className="text-slate-500 max-w-md mb-8">Ask about scholarships, hostels, or OBC education schemes.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-lg">
              {["What are the OBC scholarships?", "How to apply for hostels?"].map(s => (
                <button key={s} onClick={() => handleSend(s)} className="p-3 text-left text-sm bg-white border border-slate-200 rounded-xl hover:border-primary-400 transition-all flex items-center justify-between group">
                  <span className="text-slate-600">{s}</span>
                  <ChevronRight size={16} className="text-slate-300 group-hover:text-primary-500" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((msg, idx) => (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-primary-600 text-white' : 'bg-slate-200 text-slate-600'}`}>
                    {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                  </div>
                  <div className="flex flex-col gap-1">
                    <div className={`p-4 shadow-sm relative group ${msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}`}>
                      <p className="text-sm leading-relaxed">{msg.content}</p>
                      {msg.role === 'ai' && (
                        <button onClick={() => speakText(msg.content)} className="absolute top-2 right-2 p-1 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-primary-600">
                          <Volume2 size={14} />
                        </button>
                      )}
                    </div>
                    {msg.sources && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {msg.sources.map((src, sIdx) => (
                          <div key={sIdx} className="flex items-center gap-1 text-[10px] bg-white border border-slate-200 px-2 py-1 rounded-md text-slate-500">
                            <BookOpen size={10} />
                            <span>{src.metadata.scheme_name || src.metadata.source_name || 'Source'}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    <span className="text-[10px] text-slate-400 px-1">{msg.timestamp}</span>
                  </div>
                </div>
              </motion.div>
            ))}
            {isLoading && (
              <div className="flex justify-start gap-3">
                <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center"><Bot size={16} /></div>
                <div className="chat-bubble-ai p-4 flex items-center gap-2">
                  <Loader2 size={16} className="animate-spin text-primary-600" />
                  <span className="text-sm text-slate-500">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        )}
      </main>

      <footer className="p-4 md:p-8 max-w-4xl mx-auto w-full">
        <div className="relative flex items-center gap-2 glass-panel p-2 rounded-2xl border border-slate-200 shadow-lg">
          <button onClick={toggleRecording} className={`p-3 rounded-xl transition-all ${isRecording ? 'bg-red-100 text-red-600 animate-pulse' : 'text-slate-400 hover:bg-slate-100'}`}>
            {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
          </button>
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={isRecording ? "Listening..." : "Ask about scholarships, hostels..."}
            className="flex-1 bg-transparent border-none outline-none px-2 py-3 text-sm" />
          <button onClick={() => handleSend()} disabled={isLoading || (!input.trim() && !isRecording)}
            className="p-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 transition-all shadow-md">
            <Send size={20} />
          </button>
        </divC
        <p className="text-center text-[11px] text-slate-400 mt-3">Powered by Llama 3.2 Local LLM • Grounded in Maharashtra Govt Records</p>
      </footer>
    </div>
  );
};

export default ChatPage;
