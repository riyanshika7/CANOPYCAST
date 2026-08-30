import React from 'react';
import { Leaf } from 'lucide-react';

export default function Footer({ setView }) {
  return (
    <footer className="bg-nature-surface border-t border-nature-800/10 py-12 md:py-16">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-10 md:gap-6">
        
        {/* Brand Column */}
        <div className="space-y-4 md:col-span-2">
          <div 
            onClick={() => setView('landing')} 
            className="flex items-center gap-2 cursor-pointer select-none group w-fit"
          >
            <div className="w-8 h-8 rounded-lg bg-nature-100 flex items-center justify-center border border-nature-300">
              <Leaf className="w-4.5 h-4.5 text-nature-800" />
            </div>
            <span className="font-extrabold text-nature-text tracking-tight">
              CanopyCast
            </span>
          </div>
          <p className="text-xs text-nature-secText max-w-[280px] leading-relaxed">
            Planning greener, cooler, and more ecologically connected cities using local climate intelligence.
          </p>
        </div>

        {/* Links Column 1 */}
        <div>
          <h4 className="text-xs font-bold text-nature-text uppercase tracking-widest mb-4">
            Navigation
          </h4>
          <ul className="space-y-2.5 text-xs text-nature-secText">
            <li><button onClick={() => setView('landing')} className="hover:text-nature-text transition-colors">Overview</button></li>
            <li><button onClick={() => setView('planner')} className="hover:text-nature-text transition-colors">Launch Planner</button></li>
            <li><a href="https://github.com/riyanshika7/CANOPYCAST.git" target="_blank" rel="noreferrer" className="hover:text-nature-text transition-colors">Methodology</a></li>
          </ul>
        </div>

        {/* Links Column 2 */}
        <div>
          <h4 className="text-xs font-bold text-nature-text uppercase tracking-widest mb-4">
            Resources
          </h4>
          <ul className="space-y-2.5 text-xs text-nature-secText">
            <li><a href="https://github.com/riyanshika7/CANOPYCAST.git" target="_blank" rel="noreferrer" className="hover:text-nature-text transition-colors">Urban Forestry</a></li>
            <li><a href="https://github.com/riyanshika7/CANOPYCAST.git" target="_blank" rel="noreferrer" className="hover:text-nature-text transition-colors">GitHub Repository</a></li>
          </ul>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="max-w-7xl mx-auto px-6 border-t border-nature-800/10 mt-10 pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
        <p className="text-[10px] text-nature-mutedText font-semibold uppercase tracking-wider">
          Built for smarter urban climate action.
        </p>
        <p className="text-[10px] text-nature-mutedText">
          &copy; {new Date().getFullYear()} CanopyCast. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
