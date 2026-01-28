"""
Coffee Chat AI Agents
Handles contact prioritization, message personalization, and scam detection
"""
import os
import sys
from typing import Dict, List, Optional
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.logger_config import app_logger


class ContactRankerAgent:
    """
    Ranks contacts based on multiple factors:
    - Job match score
    - Alumni status
    - Connection degree
    - Domain verification
    - Mutual connections
    """
    
    def __init__(self):
        pass
    
    def rank_contact(
        self,
        contact: Dict,
        job: Optional[Dict] = None,
        user_profile: Optional[Dict] = None
    ) -> float:
        """
        Calculate priority score for a contact
        
        Args:
            contact: Contact information
            job: Related job posting (optional)
            user_profile: User's profile (optional)
            
        Returns:
            Priority score (0-100)
        """
        score = 0.0
        
        # Factor 1: Job match score (0-40 points)
        if job and job.get('match_score'):
            score += job['match_score'] * 4
        
        # Factor 2: Alumni status (+30 points)
        if contact.get('is_alumni'):
            score += 30
        
        # Factor 3: Connection degree
        degree = contact.get('connection_degree', '3rd')
        if degree == '2nd':
            score += 20  # Easy to connect
        elif degree == '1st':
            score += 25  # Already connected
        elif degree == '3rd':
            score += 10  # Needs bridge
        
        # Factor 4: Domain verified (+10 points)
        if contact.get('domain_verified'):
            score += 10
        
        # Factor 5: Mutual connections (0-10 points)
        mutual_count = len(contact.get('mutual_connections', []))
        score += min(mutual_count, 10)
        
        # Factor 6: Has active job posting (+10 points)
        if contact.get('has_active_posting'):
            score += 10
        
        # Normalize to 0-100
        score = min(score, 100)
        
        app_logger.info(f"Contact {contact.get('name', 'Unknown')}: Score = {score:.1f}")
        
        return score
    
    def rank_contacts(
        self,
        contacts: List[Dict],
        jobs: Optional[List[Dict]] = None,
        user_profile: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Rank a list of contacts
        
        Args:
            contacts: List of contacts
            jobs: Related jobs (optional)
            user_profile: User profile (optional)
            
        Returns:
            Sorted list of contacts with priority_score added
        """
        # Match contacts to jobs if available
        job_map = {}
        if jobs:
            for job in jobs:
                company = job.get('company', '').lower()
                job_map[company] = job
        
        # Calculate scores
        for contact in contacts:
            company = contact.get('company', '').lower()
            job = job_map.get(company)
            
            contact['priority_score'] = self.rank_contact(contact, job, user_profile)
        
        # Sort by score (descending)
        sorted_contacts = sorted(
            contacts,
            key=lambda c: c.get('priority_score', 0),
            reverse=True
        )
        
        return sorted_contacts


class PersonalizationAgent:
    """
    Generates personalized messages for connection requests and coffee chats
    Uses OpenAI GPT-4 for natural language generation
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    def generate_connection_message(
        self,
        contact: Dict,
        job: Optional[Dict] = None,
        user_profile: Optional[Dict] = None
    ) -> str:
        """
        Generate personalized connection request message
        
        Args:
            contact: Contact information
            job: Related job (optional)
            user_profile: User profile (optional)
            
        Returns:
            Personalized message (max 300 chars)
        """
        try:
            # Build context
            name = contact.get('name', 'there')
            first_name = name.split()[0]
            company = contact.get('company', 'your company')
            school = contact.get('school_name', 'our school')
            title = contact.get('title', 'your role')
            
            prompt = f"""Write a LinkedIn connection request message (MAX 300 characters).

Contact: {name}
Title: {title}
Company: {company}
Shared school: {school}

Requirements:
- Mention shared alumni connection
- Express genuine interest in their work
- Keep it professional but friendly
- MAX 300 characters (strict limit!)
- Sound natural, not AI-generated
- Do NOT mention job postings directly

Generate the message:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional networking expert helping craft authentic LinkedIn messages."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            message = response.choices[0].message.content.strip().strip('"')
            
            # Ensure it's under 300 chars
            if len(message) > 300:
                message = message[:297] + "..."
            
            app_logger.info(f"Generated connection message for {name}")
            
            return message
            
        except Exception as e:
            app_logger.error(f"Failed to generate connection message: {e}")
            # Fallback to template
            return f"Hi {first_name}, fellow {school} alum here! I'd love to connect and learn about your experience. Looking forward to chatting!"
    
    def generate_message(self, contact: Dict) -> str:
        """
        Alias for generate_connection_message (for backward compatibility)
        
        Args:
            contact: Contact information with name, company, title, school
            
        Returns:
            Personalized connection message
        """
        return self.generate_connection_message(contact)
    
    def generate_coffee_chat_message(
        self,
        contact: Dict,
        user_profile: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate coffee chat invitation message
        
        Args:
            contact: Contact information
            user_profile: User profile
            conversation_history: Previous successful messages (from memory)
            
        Returns:
            Coffee chat invitation message
        """
        try:
            name = contact.get('name', 'there')
            first_name = name.split()[0]
            company = contact.get('company', 'your company')
            school = contact.get('school_name', 'our school')
            title = contact.get('title', 'your role')
            
            # Include successful patterns from memory if available
            success_context = ""
            if conversation_history:
                success_context = "\n\nSuccessful message patterns to learn from:\n"
                for msg in conversation_history[:3]:
                    success_context += f"- {msg.get('message_text', '')[:100]}\n"
            
            prompt = f"""Write a LinkedIn coffee chat invitation message.

Context:
- Contact: {name}
- Title: {title}
- Company: {company}
- Shared school: {school}
- You're interested in learning about their work

{success_context}

Requirements:
- 80-120 words
- Mention alumni connection
- Express genuine interest in their work
- Ask for 15-20min virtual coffee chat
- Suggest flexibility for timing
- Professional but warm tone
- Sound natural, not templated

Generate the message:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a career coach helping craft authentic coffee chat invitations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            
            message = response.choices[0].message.content.strip().strip('"')
            
            app_logger.info(f"Generated coffee chat message for {name}")
            
            return message
            
        except Exception as e:
            app_logger.error(f"Failed to generate coffee chat message: {e}")
            # Fallback
            return f"Hi {first_name},\n\nThank you for connecting! As a fellow {school} alum, I'm really interested in learning about your experience at {company}. Would you be open to a quick 15-20 minute virtual coffee chat? I'm flexible with timing and would love to hear about your journey.\n\nLooking forward to connecting!"

    def generate_message_from_snapshot(
        self,
        contact_name: str,
        snapshot: str,
        user_context: str = "I am a Learning Technologist and Educator with a background in Instructional Design and AI."
    ) -> str:
        """
        Generate a deeply personalized message by analyzing the raw profile snapshot.
        This replicates the 'Human-Level' deep dive.
        """
        try:
            # 1. Analyze Snapshot
            analysis_prompt = f"""Analyze this LinkedIn profile text for a cold outreach message.
            
            Contact: {contact_name}
            Profile Text:
            {snapshot[:1500]}... (truncated)
            
            Identify 2-3 specific "Hooks" or "Talking Points" that I can mention to build rapport.
            Focus on:
            - Shared interests (EdTech, AI, Learning Design)
            - Specific articles, posts, or projects they mentioned
            - Unique career transitions
            
            Return ONLY the hooks as a bulleted list.
            """
            
            analysis_res = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=150
            )
            hooks = analysis_res.choices[0].message.content.strip()
            
            # 2. Generate Message
            msg_prompt = f"""Write a warm, professional LinkedIn cold message to {contact_name}.
            
            My Context: {user_context}
            
            Their Profile Hooks:
            {hooks}
            
            Goal: Request a 15-min virtual coffee chat to learn from their experience.
            
            Requirements:
            - Start with a specific observation from their profile (use one of the hooks).
            - Be humble and genuine.
            - "I saw your background in..." or "I noticed you..."
            - Keep it under 150 words.
            - NO generic fluff ("I hope this email finds you well").
            - End with a low-pressure ask ("Open to a brief chat?").
            """
            
            msg_res = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": msg_prompt}],
                max_tokens=200
            )
            
            return msg_res.choices[0].message.content.strip().replace('"', '')

        except Exception as e:
            app_logger.error(f"Deep dive generation failed: {e}")
            return f"Hi {contact_name}, I came across your profile and was really impressed by your experience. As a fellow professional in EdTech/L&D, I'd love to connect and hear your insights on the field. Would you be open to a brief chat?"


class ScamDetectionAgent:
    """
    Analyzes LinkedIn profiles to detect suspicious/fake accounts
    Checks multiple factors to calculate risk score
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    def analyze_profile(
        self,
        contact: Dict,
        linkedin_snapshot: Optional[str] = None
    ) -> Dict:
        """
        Analyze profile for authenticity
        
        Args:
            contact: Contact information
            linkedin_snapshot: LinkedIn profile snapshot (optional)
            
        Returns:
            Dict with risk_score, is_safe, flags, recommendation
        """
        risk_score = 0
        flags = []
        
        # Basic checks (without snapshot)
        
        # 1. Connection count
        connections = contact.get('connections_count', 0)
        if connections < 50:
            risk_score += 3
            flags.append("Low connections (<50)")
        elif connections > 5000:
            risk_score += 1
            flags.append("Very high connections (>5000)")
        
        # 2. Profile photo
        if not contact.get('has_photo', True):
            risk_score += 2
            flags.append("No profile photo")
        
        # 3. Work history
        work_history = contact.get('work_history', [])
        if len(work_history) < 2:
            risk_score += 2
            flags.append("Limited work history (<2 positions)")
        
        # 4. Generic title
        title = contact.get('title', '').lower()
        generic_titles = ['entrepreneur', 'founder', 'ceo', 'business owner', 'consultant']
        if any(g in title for g in generic_titles) and connections < 100:
            risk_score += 2
            flags.append("Generic title with low connections")
        
        # 5. AI-enhanced analysis (if snapshot available)
        if linkedin_snapshot:
            ai_result = self._ai_check(contact, linkedin_snapshot)
            risk_score += ai_result.get('risk_score', 0)
            flags.extend(ai_result.get('flags', []))
        
        # Determine recommendation
        is_safe = risk_score < 7
        if risk_score < 4:
            recommendation = 'safe'
        elif risk_score < 7:
            recommendation = 'caution'
        else:
            recommendation = 'skip'
        
        result = {
            'risk_score': risk_score,
            'is_safe': is_safe,
            'flags': flags,
            'recommendation': recommendation
        }
        
        app_logger.info(f"Scam check for {contact.get('name')}: {recommendation} (score: {risk_score})")
        
        return result
    
    def _ai_check(self, contact: Dict, snapshot: str) -> Dict:
        """
        AI-powered profile authenticity check
        
        Args:
            contact: Contact info
            snapshot: Profile snapshot
            
        Returns:
            Dict with risk_score and flags
        """
        try:
            prompt = f"""Analyze this LinkedIn profile for authenticity.

Name: {contact.get('name')}
Title: {contact.get('title')}
Company: {contact.get('company')}

Profile snapshot (first 1000 chars):
{snapshot[:1000]}

Check for red flags:
- Generic/fake-sounding title
- Company doesn't seem real
- Profile appears auto-generated
- Suspicious patterns
- Overly promotional language

Return JSON with:
{{"risk_score": 0-5, "flags": ["flag1", "flag2"]}}

Only return the JSON, nothing else.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a LinkedIn profile authenticity analyzer. Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content.strip())
            
            return result
            
        except Exception as e:
            app_logger.error(f"AI scam check failed: {e}")
            return {"risk_score": 0, "flags": []}


# Demo/Test
if __name__ == "__main__":
    print("🤖 AI Agents Demo\n")
    print("=" * 60)
    
    # Sample contact
    contact = {
        'name': 'John Doe',
        'title': 'Software Engineer',
        'company': 'Shopify',
        'school_name': 'University of Western Ontario',
        'connection_degree': '2nd',
        'is_alumni': True,
        'domain_verified': True,
        'connections_count': 500,
        'has_photo': True,
        'work_history': [{'company': 'Shopify'}, {'company': 'Amazon'}],
        'mutual_connections': ['Alice', 'Bob']
    }
    
    job = {
        'title': 'Learning Designer',
        'company': 'Shopify',
        'match_score': 9
    }
    
    # Test ContactRankerAgent
    print("\n1. Contact Ranking:")
    print("-" * 60)
    ranker = ContactRankerAgent()
    score = ranker.rank_contact(contact, job)
    print(f"   Priority Score: {score:.1f}/100")
    
    # Test PersonalizationAgent
    print("\n2. Message Generation:")
    print("-" * 60)
    personalizer = PersonalizationAgent()
    
    conn_msg = personalizer.generate_connection_message(contact, job)
    print(f"   Connection Request ({len(conn_msg)} chars):")
    print(f"   '{conn_msg}'")
    
    chat_msg = personalizer.generate_coffee_chat_message(contact)
    print(f"\n   Coffee Chat Invitation ({len(chat_msg)} chars):")
    print(f"   '{chat_msg}'")
    
    # Test ScamDetectionAgent
    print("\n3. Scam Detection:")
    print("-" * 60)
    scam_detector = ScamDetectionAgent()
    result = scam_detector.analyze_profile(contact)
    print(f"   Risk Score: {result['risk_score']}/10")
    print(f"   Safe: {result['is_safe']}")
    print(f"   Recommendation: {result['recommendation']}")
    if result['flags']:
        print(f"   Flags: {', '.join(result['flags'])}")
    
    print("\n" + "=" * 60)
    print("✅ AI Agents Demo Complete!")
