from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple, Dict
import pickle
from pathlib import Path

class EmbeddingService:
    """Semantic similarity using sentence-transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.cache_path = Path("models/embeddings_cache/")
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        cache_file = self.cache_path / "embeddings.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_cache(self):
        with open(self.cache_path / "embeddings.pkl", "wb") as f:
            pickle.dump(self.cache, f)
    
    def get_embedding(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Get 384-dim embedding vector for text"""
        
        if use_cache and text in self.cache:
            return self.cache[text]
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        if use_cache:
            self.cache[text] = embedding
            if len(self.cache) % 10 == 0:
                self._save_cache()
        
        return embedding
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Cosine similarity between two texts (-1 to 1)"""
        
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        
        similarity = np.dot(emb1, emb2) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2)
        )
        return float(similarity)
    
    def find_most_similar_leads(
        self,
        ideal_customer_description: str,
        candidate_leads: List[Dict],
        top_k: int = 20
    ) -> List[Tuple[Dict, float]]:
        """
        Find leads most similar to ideal customer profile
        
        Returns: List of (lead, similarity_score) tuples
        """
        
        ideal_emb = self.get_embedding(ideal_customer_description)
        
        similarities = []
        for lead in candidate_leads:
            lead_text = f"{lead.get('company_name', '')} {lead.get('description', '')}"
            
            if not lead_text.strip():
                continue
            
            lead_emb = self.get_embedding(lead_text)
            similarity = np.dot(ideal_emb, lead_emb) / (
                np.linalg.norm(ideal_emb) * np.linalg.norm(lead_emb)
            )
            
            similarities.append((lead, float(similarity)))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
