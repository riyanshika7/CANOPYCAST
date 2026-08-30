import React, { useState, useEffect } from 'react';
import { Leaf, Menu, X, ArrowUpRight } from 'lucide-react';

export default function Navbar({ currentView, setView }) {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNavClick = (id) => {
    setIsOpen(false);
    setView('landing');
    setTimeout(() => {
      const element = document.getElementById(id);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  };

  return (
    <nav className={`fixed top-0 left-0 w-full z-50 transition-all duration-300 border-b ${
      scrolled 
        ? 'bg-white/80 backdrop-blur-md border-emerald-900/10 shadow-sm py-4' 
        : 'bg-transparent border-transparent py-5'
    }`}>
      <div className="max-w-7xl mx-auto px-6 flex justify-between items-center">
        {/* Logo */}
        <div 
          onClick={() => setView('landing')} 
          className="flex items-center gap-2 cursor-pointer select-none group"
        >
          <div className="w-9 h-9 rounded-xl bg-nature-100 flex items-center justify-center border border-nature-300 group-hover:bg-nature-300 transition-colors">
            <Leaf className="w-5 h-5 text-nature-800" />
          </div>
          <span className="font-extrabold text-nature-text tracking-tight text-lg">
            CanopyCast
          </span>
        </div>

        {/* Center Navigation Links */}
        <div className="hidden md:flex items-center gap-8">
          {['overview', 'how-it-works', 'intelligence', 'impact'].map((item) => (
            <button
              key={item}
              onClick={() => handleNavClick(item)}
              className="text-xs font-semibold text-nature-secText hover:text-nature-text transition-colors capitalize tracking-wide"
            >
              {item.replace('-', ' ')}
            </button>
          ))}
        </div>

        {/* Right CTA */}
        <div className="hidden md:block">
          <button
            onClick={() => setView(currentView === 'planner' ? 'landing' : 'planner')}
            className="flex items-center gap-1 bg-nature-800 hover:bg-nature-900 text-white font-bold text-xs py-2.5 px-5 rounded-full shadow-sm hover:shadow-md transition-all duration-300 transform hover:-translate-y-[1px]"
          >
            <span>{currentView === 'planner' ? 'Home Portal' : 'Launch Planner'}</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Mobile Menu Toggle */}
        <button 
          onClick={() => setIsOpen(!isOpen)} 
          className="md:hidden p-2 text-nature-text hover:bg-nature-surface rounded-lg transition-colors"
        >
          {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {isOpen && (
        <div className="md:hidden absolute top-full left-0 w-full bg-white/95 backdrop-blur-md border-b border-nature-300/30 p-6 flex flex-col gap-5 shadow-lg animate-fade-in">
          {['overview', 'how-it-works', 'intelligence', 'impact'].map((item) => (
            <button
              key={item}
              onClick={() => handleNavClick(item)}
              className="text-left font-bold text-sm text-nature-secText hover:text-nature-text transition-colors capitalize"
            >
              {item.replace('-', ' ')}
            </button>
          ))}
          <button
            onClick={() => {
              setView(currentView === 'planner' ? 'landing' : 'planner');
              setIsOpen(false);
            }}
            className="w-full text-center bg-nature-800 hover:bg-nature-900 text-white font-bold py-3 px-4 rounded-xl transition-colors text-xs flex items-center justify-center gap-1.5"
          >
            <span>{currentView === 'planner' ? 'Home Portal' : 'Launch Planner'}</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </nav>
  );
}
