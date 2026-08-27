import React, { useState } from 'react';

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { text: "Hello! I am your AI Canopy Assistant. Click on a grid cell or run the optimizer to see planting suggestions, or ask me any urban forestry questions here.", sender: "ai" }
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages(prev => [...prev, { text: input, sender: "user" }]);
    setInput("");
    
    // Simulate AI response (to be connected to FastAPI POST /api/chat)
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        text: "Neem trees are excellent for reducing street temperatures. They provide broad shade coverage, are highly drought resistant, and survive urban pollution well.", 
        sender: "ai" 
      }]);
    }, 1000);
  };

  return (
    <div className="w-full h-96 border border-slate-200 rounded-lg flex flex-col justify-between bg-white shadow-sm overflow-hidden">
      <div className="p-3 bg-slate-50 border-b border-slate-200 font-bold text-sm text-slate-700">
        AI Canopy Assistant
      </div>
      
      <div className="flex-1 p-3 overflow-y-auto space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg p-3 text-xs leading-relaxed ${
              msg.sender === 'user' 
                ? 'bg-green-600 text-white font-medium' 
                : 'bg-slate-100 text-slate-700'
            }`}>
              {msg.text}
            </div>
          </div>
        ))}
      </div>
      
      <div className="p-3 border-t border-slate-200 flex gap-2">
        <input 
          type="text" 
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask about tree care, planting guides..."
          className="flex-1 border border-slate-200 rounded-md px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-green-500"
          onKeyDown={e => e.key === 'Enter' && handleSend()}
        />
        <button 
          onClick={handleSend}
          className="bg-green-600 hover:bg-green-700 text-white text-xs font-bold px-4 py-2 rounded-md transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}
