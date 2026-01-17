import React, { useState, useEffect, useRef } from 'react';
import { SystemState, ChatMessage } from '../types';

interface InterfaceProps {
  state: SystemState;
  onSend: (message: string) => void;
  history: ChatMessage[];
}

export const Interface: React.FC<InterfaceProps> = ({ state, onSend, history }) => {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const isThinking = state === SystemState.ANALYZING;

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isThinking) {
      onSend(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="absolute inset-0 z-10 flex w-full h-full pointer-events-none p-6 md:p-12 lg:p-16">
      
      {/* LEFT PANEL - CONTROLS & INPUT */}
      <div className="flex flex-col w-full max-w-md h-full pointer-events-auto justify-between pr-8">
        
        {/* HEADER SECTION */}
        <div>
          <h1 className="text-3xl font-light tracking-tight text-white mb-2 leading-none">
            Recursive Language Model
          </h1>
          <p className="text-sm text-neutral-400 font-light mb-6 leading-relaxed max-w-xs">
            A persistent, policy-driven conversational system.
          </p>
          
          <div className="border-l-2 border-neutral-800 pl-4 mb-10">
            <p className="text-xs text-neutral-500 leading-5 font-light">
              A Recursive Language Model maintains context, reflects across turns, and converges responses through internal feedback loops rather than single-pass generation.
            </p>
          </div>
        </div>

        {/* INPUT SECTION */}
        <div className="flex-1 flex flex-col justify-center">
            <form onSubmit={handleSubmit} className="flex flex-col gap-6 backdrop-blur-sm bg-black/40 p-6 border border-white/5 rounded-sm">
              <div className="flex flex-col gap-2">
                <label htmlFor="chat-input" className="text-[10px] uppercase tracking-widest text-neutral-400 font-mono">
                  Conversation Input
                </label>
                <textarea 
                  id="chat-input"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isThinking}
                  rows={4}
                  className="bg-transparent border-b border-neutral-700 text-neutral-200 py-2 focus:outline-none focus:border-neutral-400 transition-colors font-sans text-sm resize-none placeholder-neutral-700 leading-relaxed"
                  placeholder="Ask a question, explore an idea, or continue the conversation..."
                />
              </div>

              <div className="flex justify-between items-center mt-2">
                <div className="flex items-center gap-2">
                   <div className={`w-1.5 h-1.5 rounded-full ${isThinking ? 'bg-blue-400 animate-pulse' : 'bg-neutral-600'}`}></div>
                   <span className="text-[9px] uppercase tracking-widest text-neutral-500 font-mono">
                     {isThinking ? 'Recursion Active' : 'System Ready'}
                   </span>
                </div>

                <button 
                  type="submit"
                  disabled={isThinking || !input.trim()}
                  className={`py-2 px-6 text-[10px] uppercase tracking-[0.2em] font-medium transition-all duration-300 border border-neutral-800 
                    ${isThinking 
                      ? 'opacity-50 cursor-not-allowed text-neutral-600 bg-transparent' 
                      : 'text-neutral-200 hover:border-neutral-500 hover:bg-neutral-900/50'}`}
                >
                  Send
                </button>
              </div>
            </form>
        </div>

        {/* FOOTER */}
        <div className="mt-8">
           <div className="mb-4">
              <h4 className="text-[10px] uppercase tracking-widest text-neutral-600 mb-1 font-mono">System Identity</h4>
              <p className="text-[10px] text-neutral-500 leading-4 max-w-xs">
                Recursive Language Model (Experimental)
                <br/>
                Responses generated through iterative internal reasoning.
              </p>
           </div>
        </div>

      </div>

      {/* RIGHT PANEL - CONVERSATION HISTORY */}
      <div className="flex flex-col w-full max-w-xl h-full ml-auto pointer-events-auto border-l border-neutral-900/50 pl-8 bg-gradient-to-l from-black/20 to-transparent">
        
        <div className="flex items-center gap-3 mb-6 border-b border-neutral-900 pb-4">
          <span className="text-[10px] uppercase tracking-widest font-mono text-neutral-500">
            Conversation History
          </span>
        </div>

        {/* SCROLLABLE CHAT AREA */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto pr-4 space-y-8 scroll-smooth"
          style={{
            maskImage: 'linear-gradient(to bottom, transparent 0%, black 5%, black 95%, transparent 100%)',
            WebkitMaskImage: 'linear-gradient(to bottom, transparent 0%, black 5%, black 95%, transparent 100%)'
          }}
        >
          {history.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center opacity-30 select-none">
              <div className="w-12 h-12 border border-neutral-700 rounded-full flex items-center justify-center mb-4">
                <div className="w-1 h-1 bg-neutral-500 rounded-full"></div>
              </div>
              <p className="text-[10px] uppercase tracking-widest text-neutral-500">Awaiting Input</p>
            </div>
          )}

          {history.map((msg, index) => (
            <div key={index} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              
              <span className={`text-[9px] uppercase tracking-widest font-mono mb-2 ${msg.role === 'user' ? 'text-neutral-600' : 'text-blue-900/60'}`}>
                {msg.role === 'user' ? 'Input Signal' : 'Recursive Output'}
              </span>
              
              <div className={`max-w-[90%] md:max-w-[85%] text-sm leading-6 font-light tracking-wide whitespace-pre-wrap ${
                msg.role === 'user' 
                  ? 'text-neutral-400 text-right border-r border-neutral-800 pr-4' 
                  : 'text-neutral-200 text-left border-l border-neutral-800 pl-4 py-1'
              }`}>
                {msg.content}
              </div>
              
              <span className="text-[9px] text-neutral-800 font-mono mt-2">
                 T+{index}
              </span>
            </div>
          ))}

          {isThinking && (
             <div className="flex flex-col items-start opacity-50">
                <span className="text-[9px] uppercase tracking-widest font-mono mb-2 text-blue-900/60">
                  Recursive Output
                </span>
                <div className="pl-4 border-l border-neutral-800">
                  <div className="flex gap-1">
                    <span className="w-1 h-1 bg-neutral-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                    <span className="w-1 h-1 bg-neutral-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                    <span className="w-1 h-1 bg-neutral-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                  </div>
                </div>
             </div>
          )}
          
          {/* Spacer for bottom mask */}
          <div className="h-12"></div>
        </div>

      </div>

    </div>
  );
};