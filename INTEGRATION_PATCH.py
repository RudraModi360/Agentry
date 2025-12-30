"""
Quick integration patch for SmartAgent - adds query analysis
"""

async def enhanced_chat(self, user_input, session_id="default"):
    """Enhanced chat with query analysis"""
    
    # INTELLIGENCE LAYER
    if isinstance(user_input, str) and len(user_input) > 0:
        analysis = self.query_analyzer.analyze(user_input)
        
        if self.debug:
            print(f"[Agentry Intelligence] 🔍 {analysis.query_type.value} | "
                  f"Complexity: {analysis.complexity_score:.2f} | "
                  f"Web Search: {'✅ Required' if analysis.needs_web_search else '❌ Not needed'}")
        
        # Enforce web_search for factual queries
        if analysis.needs_web_search and 'web_search' in analysis.suggested_tools:
            hint = f"\n\n[SYSTEM DIRECTIVE: This {analysis.query_type.value} query requires web_search for current information. You MUSTcall web_search tool first before answering.]"
            user_input = user_input + hint
            
            if self.debug:
                print(f"[Agentry Intelligence] 💡 Injected mandatory web_search directive")
    
    # Call original chat logic...
    # (rest of the method continues as before)
