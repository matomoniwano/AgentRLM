import React, { useState, useCallback } from 'react';
import { Scene } from './components/Scene';
import { Interface } from './components/Interface';
import { SystemState, ChatMessage } from './types';
import { sendMessage } from './services/analysisService';

export default function App() {
  const [state, setState] = useState<SystemState>(SystemState.IDLE);
  const [history, setHistory] = useState<ChatMessage[]>([]);

  const handleSend = useCallback(async (content: string) => {
    // Optimistic Update: Add user message
    const userMsg: ChatMessage = {
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    
    setHistory(prev => [...prev, userMsg]);
    setState(SystemState.ANALYZING);

    try {
      // Get RLM response
      const responseText = await sendMessage(history, content);
      
      const agentMsg: ChatMessage = {
        role: 'assistant',
        content: responseText,
        timestamp: new Date().toISOString()
      };

      setHistory(prev => [...prev, agentMsg]);
      setState(SystemState.DECISION_READY);
      
    } catch (error) {
      console.error("System Error:", error);
      setState(SystemState.ERROR);
    }
  }, [history]);

  return (
    <div className="relative w-screen h-screen bg-black overflow-hidden selection:bg-white/20 selection:text-white">
      {/* 
         Visual Layer: 
         - Represents "Cognitive Structure" 
         - ANALYZING state triggers active node traversal animation
      */}
      <Scene state={state} />

      {/* 
         Interaction Layer:
         - Recursive Chat Interface
      */}
      <Interface 
        state={state} 
        onSend={handleSend} 
        history={history} 
      />
    </div>
  );
}