# Job Autopilot - ATS Scorer
# ATS compatibility scoring inspired by Resume-Matcher
# License: Apache-2.0 (Resume-Matcher) compatible with AGPL-3.0

import hashlib
from typing import Dict, List
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
from modules.logger_config import app_logger

class ATSScorer:
    """
    ATS compatibility scorer inspired by Resume-Matcher
    https://github.com/srbhr/Resume-Matcher (Apache-2.0)
    
    Features:
    - NLP-based keyword extraction
    - TF-IDF + cosine similarity matching
    - Missing keyword detection
    - Improvement suggestions
    - In-memory caching to reduce API costs
    """
    
    def __init__(self):
        """Initialize ATS scorer with spaCy and caching"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            app_logger.info("ATS Scorer initialized with spaCy model")
        except OSError:
            app_logger.error("spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
            raise
        
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            ngram_range=(1, 2)  # Unigrams and bigrams
        )
        self.cache = {}  # Simple in-memory cache
        app_logger.info("TF-IDF vectorizer initialized")
    
    def score_resume(self, resume_text: str, job_description: str) -> Dict:
        """
        Calculate ATS match score (0-100)
        
        Args:
            resume_text: Full resume text
            job_description: Job description text
        
        Returns:
            dict: {
                'score': int (0-100),
                'missing_keywords': List[str],
                'suggestions': List[str]
            }
        """
        # Check cache first
        cache_key = self._get_cache_key(resume_text, job_description)
        if cache_key in self.cache:
            app_logger.info("Returning cached ATS score")
            return self.cache[cache_key]
        
        app_logger.info("Calculating ATS score...")
        
        try:
            # 1. Calculate text similarity using TF-IDF + cosine similarity
            vectors = self.vectorizer.fit_transform([resume_text, job_description])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            score = int(similarity * 100)
            
            # 2. Extract keywords from both texts
            jd_keywords = self._extract_keywords(job_description)
            resume_keywords = self._extract_keywords(resume_text)
            
            # 3. Find missing keywords
            missing = set(jd_keywords) - set(resume_keywords)
            missing_sorted = sorted(missing, key=lambda x: jd_keywords.count(x), reverse=True)
            
            # 4. Generate suggestions
            suggestions = self._generate_suggestions(missing_sorted[:5])
            
            result = {
                "score": score,
                "missing_keywords": missing_sorted[:10],  # Top 10
                "suggestions": suggestions
            }
            
            # Cache result
            self.cache[cache_key] = result
            
            app_logger.info(f"ATS Score: {score}/100, Missing {len(missing)} keywords")
            
            return result
        
        except Exception as e:
            app_logger.error(f"ATS scoring failed: {e}")
            return {
                "score": 0,
                "missing_keywords": [],
                "suggestions": ["Error calculating ATS score. Please try again."]
            }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords using spaCy NLP
        
        Args:
            text: Input text
        
        Returns:
            List of keywords (lowercase)
        """
        doc = self.nlp(text.lower())
        
        keywords = []
        for token in doc:
            # Extract nouns, proper nouns, and adjectives
            if token.pos_ in ["NOUN", "PROPN", "ADJ"] and not token.is_stop:
                if len(token.text) > 2:  # Ignore very short words
                    keywords.append(token.text)
        
        # Also extract named entities (companies, technologies, etc.)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "SKILL"]:
                keywords.append(ent.text.lower())
        
        return keywords
    
    def _generate_suggestions(self, missing_keywords: List[str]) -> List[str]:
        """
        Generate improvement suggestions based on missing keywords
        
        Args:
            missing_keywords: List of keywords missing from resume
        
        Returns:
            List of actionable suggestions
        """
        suggestions = []
        
        if not missing_keywords:
            suggestions.append("✅ Great! Your resume covers most key terms from the job description.")
            return suggestions
        
        # Group similar keywords
        for keyword in missing_keywords[:5]:  # Top 5 missing keywords
            suggestions.append(f"• Consider adding '{keyword}' to your resume (appears frequently in JD)")
        
        # General advice
        if len(missing_keywords) > 10:
            suggestions.append("💡 Tip: Your resume is missing several key terms. Review the job description carefully.")
        elif len(missing_keywords) > 5:
            suggestions.append("💡 Tip: Add 2-3 more relevant keywords to improve your ATS score.")
        
        return suggestions
    
    def _get_cache_key(self, resume_text: str, job_description: str) -> str:
        """Generate cache key from text hashes"""
        combined = f"{resume_text[:100]}_{job_description[:100]}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear the in-memory cache"""
        self.cache = {}
        app_logger.info("ATS cache cleared")


# Global instance
ats_scorer = ATSScorer()


if __name__ == "__main__":
    # Test
    test_resume = """
    John Doe
    Senior Software Engineer
    
    Python, JavaScript, React, Node.js, AWS, Docker
    
    Experience:
    - Built RESTful APIs using Flask and FastAPI
    - Deployed applications on AWS EC2 and Lambda
    - Implemented CI/CD pipelines with GitHub Actions
    """
    
    test_jd = """
    We're looking for a Senior Software Engineer with:
    - Strong Python and JavaScript skills
    - Experience with cloud platforms (AWS, Azure)
    - Knowledge of Docker and Kubernetes
    - RESTful API design experience
    - CI/CD experience preferred
    """
    
    result = ats_scorer.score_resume(test_resume, test_jd)
    
    print(f"\n🎯 ATS Score: {result['score']}/100")
    print(f"\n❌ Missing Keywords ({len(result['missing_keywords'])}):")
    for kw in result['missing_keywords'][:5]:
        print(f"   - {kw}")
    
    print(f"\n💡 Suggestions:")
    for suggestion in result['suggestions']:
        print(f"   {suggestion}")
