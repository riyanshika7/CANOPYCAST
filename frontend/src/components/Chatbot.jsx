import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, MessageSquare } from 'lucide-react';

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { 
      text: "Hello! I am your AI Canopy Assistant. I can help recommend native tree species, explain microclimate calculations, or give advice on urban forestry regulations.", 
      sender: "ai" 
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMessage = input;
    setMessages(prev => [...prev, { text: userMessage, sender: "user" }]);
    setInput("");
    setIsLoading(true);

    try {
      // Connect to FastAPI endpoint
      const response = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage })
      });

      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [...prev, { text: data.response, sender: "ai" }]);
      } else {
        throw new Error("API call failed");
      }
    } catch (error) {
      // Fallback response for offline demo reliability
      setTimeout(() => {
        let fallbackText = "For this urban zone, planting Neem (Azadirachta indica) is highly recommended. It has an average mature canopy spread of 10m, excels in air filtration, and provides massive shading to reduce concrete temperatures.";
        if (userMessage.toLowerCase().includes("water") || userMessage.toLowerCase().includes("care")) {
          fallbackText = "Young saplings require watering 2-3 times a week during hot months. Once established, native species are drought resistant and need minimal irrigation.";
        } else if (userMessage.toLowerCase().includes("rule") || userMessage.toLowerCase().includes("law") || userMessage.toLowerCase().includes("regulation")) {
          fallbackText = "Urban forestry standards mandate maintaining a 3-meter safety distance from power lines and water conduits. Standard sapling spacing should be 5-6 meters.";
        }
        setMessages(prev => [...prev, { text: fallbackText, sender: "ai" }]);
      }, 800);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full h-full border border-slate-200 rounded-2xl flex flex-col justify-between bg-white shadow-sm overflow-hidden">
      {/* Bot Header */}
      <div className="p-4 bg-slate-50 border-b border-slate-200 font-bold text-sm text-slate-700 flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-emerald-600 animate-pulse" />
        <span>Canopy Intelligence Assistant</span>
      </div>
      
      {/* Message List */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-2.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.sender === 'ai' && (
              <div className="w-7 h-7 rounded-full bg-emerald-100 flex items-center justify-center shrink-0 border border-emerald-200">
                <MessageSquare className="w-4 h-4 text-emerald-800" />
              </div>
            )}
            <div className={`max-w-[75%] rounded-2xl p-3.5 text-xs leading-relaxed shadow-sm ${
              msg.sender === 'user' 
                ? 'bg-emerald-700 text-white font-medium rounded-tr-none' 
                : 'bg-slate-100 text-slate-700 rounded-tl-none border border-slate-200'
            }`}>
              {msg.text}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-2.5 justify-start">
            <div className="w-7 h-7 rounded-full bg-emerald-100 flex items-center justify-center shrink-0 border border-emerald-200">
              <MessageSquare className="w-4 h-4 text-emerald-800" />
            </div>
            <div className="bg-slate-100 text-slate-400 rounded-2xl rounded-tl-none border border-slate-200 p-3.5 text-xs flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Message Input */}
      <div className="p-4 border-t border-slate-200 flex gap-2 bg-slate-50">
        <input 
          type="text" 
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={isLoading}
          placeholder="Ask about local native species, tree spacing, maintenance..."
          className="flex-1 border border-slate-200 rounded-xl px-4 py-3 text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500 bg-white"
          onKeyDown={e => e.key === 'Enter' && handleSend()}
        />
        <button 
          onClick={handleSend}
          disabled={isLoading}
          className="bg-emerald-700 hover:bg-emerald-800 disabled:bg-emerald-300 text-white p-3 rounded-xl shadow-sm transition-colors flex items-center justify-center"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
