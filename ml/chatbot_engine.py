import json
import requests
from typing import Any

class CounselingChatbot:
    """
    A dynamic AI Chatbot powered by local Ollama (Llama 3.2).
    Provides professional, factual responses based on the session's prediction results.
    """

    def __init__(self, context_data: dict[str, Any]):
        """
        Initializes the chatbot with the current prediction context.
        """
        self.context = context_data

    def get_response(self, query: str) -> str:
        system_prompt = self._build_system_prompt()

        try:
            url = "http://localhost:11434/api/chat"
            payload = {
                "model": "llama3.2",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 250
                }
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            return data.get("message", {}).get("content", "I am sorry, but I couldn't formulate a response.")
            
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to the local Ollama service. Please ensure Ollama is running."
        except Exception as e:
            return f"I apologize, but I encountered an error with the AI service: {str(e)}"

    def _build_system_prompt(self) -> str:
        # Extract context safely
        rank = self.context.get('rank', 'Unknown')
        category = self.context.get('category', 'Unknown')
        state = self.context.get('state', 'Unknown')
        budget = self.context.get('budget', 'No limit specified')
        course = self.context.get('course', 'MBBS')

        # Format college lists for the prompt
        def format_colleges(colleges):
            if not colleges: return "None identified."
            return ", ".join([f"{c.get('college')} (Prob: {c.get('probability')}%)" for c in colleges])

        safes = format_colleges(self.context.get('safe_colleges', []))
        targets = format_colleges(self.context.get('target_colleges', []))
        dreams = format_colleges(self.context.get('dream_colleges', []))

        prompt = f"""You are an advanced, ChatGPT-style AI NEET Counseling Assistant. You possess complete knowledge of every medical college in India, their fees, cutoffs, AIQ (15%), and State Quota (85%) rules.

USER'S CURRENT SITUATION:
- NEET Rank: {rank}
- Category: {category}
- Domicile State: {state}
- Target Course: {course}
- Budget: {budget}

SYSTEM PREDICTION RESULTS FOR THIS USER:
- Safe Options: {safes}
- Target Options: {targets}
- Dream Options: {dreams}

INSTRUCTIONS:
1. Act exactly like ChatGPT: helpful, highly knowledgeable, and professional. Do NOT use emojis or an informal tone.
2. Focus ONLY on decision-making and clarity. Do NOT simply read back the list of MBBS colleges.
3. **Alternative Course Recommendation**: If the user's rank is high (e.g., > 100,000) and MBBS is unlikely, recommend BDS, BAMS, BHMS, BUMS. Indicate admission likelihood. IMPORTANT: If listing top alternative colleges, you MUST ONLY use the specific BDS/BAMS/BHMS/BUMS colleges provided above in the "SYSTEM PREDICTION RESULTS". Do NOT guess or hallucinate any college names. If no alternative colleges are in the results, state that they should consider applying to top BDS/BAMS institutions generally.
4. **Course-Level Decision Guidance**: Provide a clear decision statement on whether MBBS is realistically achievable, or whether alternative courses should be considered as primary options.
5. **Final Recommendation Summary**: Provide a structured conclusion with: 1. Best Possible Option, 2. Safer Backup Plan, 3. Risk Level (Low/Moderate/High), 4. Suggested Action.
6. Format your answers beautifully using HTML (e.g., <strong>, <br>, <ul>). Do not use markdown.
7. **BALANCE DETAIL & BREVITY**: Keep your response concise, structured, and factual. Aim for a medium length to balance detail with fast local generation times. Do not ramble.
"""
        return prompt
