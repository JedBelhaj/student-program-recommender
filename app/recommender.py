"""Recommendation engine logic."""

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
from pathlib import Path

from .config import (
    TFIDF_VECTORIZER, TFIDF_MATRIX, CF_MODEL,
    PROGRAMS_FILE, HYBRID_CONTENT_WEIGHT, HYBRID_CF_WEIGHT
)


class RecommendationEngine:
    """Hybrid recommendation engine combining content-based and collaborative filtering."""
    
    def __init__(self):
        """Load pre-trained models and data."""
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.cf_model = None
        self.programs_df = None
        self.loaded = False
        
    def load_models(self):
        """Load all required models and data files."""
        if self.loaded:
            return
            
        try:
            # Load TF-IDF models
            if TFIDF_VECTORIZER.exists():
                self.tfidf_vectorizer = joblib.load(TFIDF_VECTORIZER)
            
            if TFIDF_MATRIX.exists():
                self.tfidf_matrix = joblib.load(TFIDF_MATRIX)
            
            # Load CF model
            if CF_MODEL.exists():
                self.cf_model = joblib.load(CF_MODEL)
            
            # Load program data
            if PROGRAMS_FILE.exists():
                self.programs_df = pd.read_csv(PROGRAMS_FILE)
                # Create combined text field like in the training notebook
                self.programs_df['text'] = (self.programs_df['description'] + ' ' + 
                                           self.programs_df['tags_text']).str.lower()
            
            self.loaded = True
            print("✓ Models loaded successfully")
        except Exception as e:
            print(f"✗ Error loading models: {e}")
            raise
        
    def content_based_recommendations(
        self, 
        user_interests: str, 
        k: int = 5
    ) -> List[Tuple[str, float, str]]:
        """Generate content-based recommendations using TF-IDF similarity."""
        if not self.loaded:
            self.load_models()
        
        # Transform user interests to TF-IDF vector
        user_vector = self.tfidf_vectorizer.transform([user_interests])
        
        # Calculate cosine similarity with all programs
        similarities = cosine_similarity(user_vector, self.tfidf_matrix).flatten()
        
        # Get top-k programs with non-zero similarity
        # Sort by score descending
        scored_programs = [(idx, similarities[idx]) for idx in range(len(similarities))]
        scored_programs.sort(key=lambda x: x[1], reverse=True)
        
        # Filter to only meaningful matches (score > 0)
        relevant_programs = [(idx, score) for idx, score in scored_programs if score > 0]
        
        # Take top-k from relevant programs
        top_programs = relevant_programs[:k] if len(relevant_programs) >= k else relevant_programs
        
        recommendations = []
        for idx, score in top_programs:
            program = self.programs_df.iloc[idx]
            explanation = self._generate_content_explanation(user_interests, program)
            recommendations.append((program['program_id'], float(score), explanation))
        
        return recommendations
    
    def collaborative_recommendations(
        self, 
        user_id: str, 
        k: int = 5
    ) -> List[Tuple[str, float, str]]:
        """Generate collaborative filtering recommendations."""
        if not self.loaded:
            self.load_models()
        
        # Check if CF model exists
        if self.cf_model is None:
            return []
        
        # Check if user exists in training data
        if user_id not in self.cf_model.get('user_id_map', {}):
            return []
        
        user_idx = self.cf_model['user_id_map'][user_id]
        
        # Get predicted scores for all programs
        predicted_scores = self.cf_model['user_factors'][user_idx] @ self.cf_model['item_factors'].T
        
        # Get top-k programs
        top_indices = predicted_scores.argsort()[-k:][::-1]
        
        recommendations = []
        reverse_item_map = {v: k for k, v in self.cf_model['item_id_map'].items()}
        
        for idx in top_indices:
            if idx in reverse_item_map:
                program_id = reverse_item_map[idx]
                score = predicted_scores[idx]
                program = self.programs_df[self.programs_df['program_id'] == program_id].iloc[0]
                explanation = "Users with similar interests also liked this program."
                recommendations.append((program_id, float(score), explanation))
        
        return recommendations
    
    def hybrid_recommendations(
        self, 
        user_interests: str, 
        user_id: str = None,
        k: int = 5
    ) -> List[Dict]:
        """Generate hybrid recommendations combining content and CF."""
        if not self.loaded:
            self.load_models()
        
        # Get content-based recommendations
        content_recs = self.content_based_recommendations(user_interests, k=20)
        content_scores = {pid: score for pid, score, _ in content_recs}
        content_explanations = {pid: exp for pid, _, exp in content_recs}
        
        # Get collaborative recommendations if user exists
        cf_scores = {}
        if user_id:
            cf_recs = self.collaborative_recommendations(user_id, k=20)
            cf_scores = {pid: score for pid, score, _ in cf_recs}
        
        # Combine scores
        all_programs = set(content_scores.keys()) | set(cf_scores.keys())
        hybrid_scores = {}
        
        for program_id in all_programs:
            content_score = content_scores.get(program_id, 0)
            cf_score = cf_scores.get(program_id, 0)
            
            # Normalize CF scores if they exist
            if cf_scores:
                max_cf = max(cf_scores.values()) if cf_scores else 1
                cf_score_norm = cf_score / max_cf if max_cf > 0 else 0
            else:
                cf_score_norm = 0
            
            # Weighted average
            if cf_scores:
                hybrid_score = (HYBRID_CONTENT_WEIGHT * content_score + 
                               HYBRID_CF_WEIGHT * cf_score_norm)
            else:
                # New user: use only content-based
                hybrid_score = content_score
            
            hybrid_scores[program_id] = hybrid_score
        
        # Sort by hybrid score and get top-k
        # Filter out programs with very low scores (less relevant)
        sorted_programs = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        # Only include programs with meaningful scores (> 0.01 for content-based threshold)
        filtered_programs = [(pid, score) for pid, score in sorted_programs if score > 0.01]
        top_programs = filtered_programs[:k] if len(filtered_programs) >= k else filtered_programs
        
        # If we don't have enough, fill with top scored ones anyway
        if len(top_programs) < k:
            top_programs = sorted_programs[:k]
        
        # Build recommendation list with full details
        recommendations = []
        for program_id, score in top_programs:
            program = self.programs_df[self.programs_df['program_id'] == program_id].iloc[0]
            
            # Use content explanation or create hybrid explanation
            explanation = content_explanations.get(program_id, 
                "Recommended based on your interests and similar user preferences.")
            
            recommendations.append({
                'program_id': program_id,
                'program_name': program['name'],
                'description': program['description'],
                'skills': program.get('tags_text', program.get('skills', '')),
                'score': float(score),
                'explanation': explanation
            })
        
        return recommendations
    
    def _generate_content_explanation(self, user_interests: str, program: pd.Series) -> str:
        """Generate human-readable explanation for content-based recommendation."""
        interests_list = [i.strip().lower() for i in user_interests.split(',')]
        program_text = program.get('text', '').lower()
        program_tags = program.get('tags_text', '').lower()
        
        # Find matching interests in program text
        matches = []
        for interest in interests_list:
            # Check if interest appears in program text
            if interest in program_text:
                matches.append(interest)
        
        if matches:
            if len(matches) == 1:
                matched_text = matches[0]
            elif len(matches) == 2:
                matched_text = f"{matches[0]} and {matches[1]}"
            else:
                matched_text = f"{matches[0]}, {matches[1]}, and others"
                
            return f"Recommended because you're interested in {matched_text}, and this program focuses on {program.get('tags_text', '')}."
        else:
            return f"This program focuses on {program.get('tags_text', '')}, which may align with your background and interests."


# Global instance
engine = RecommendationEngine()
