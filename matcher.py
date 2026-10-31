import re
import math
from datetime import datetime
from typing import List, Dict, Any, Optional

# Predefined keyword weights and synonym groups for campus lost & found
CATEGORY_SYNONYMS = {
    "electronics": ["laptop", "phone", "iphone", "android", "macbook", "ipad", "tablet", "airpods", "earbuds", "headphones", "charger", "cable", "mouse", "calculator", "kindle", "watch", "smartwatch"],
    "bags_wallets": ["bag", "backpack", "wallet", "purse", "tote", "handbag", "pouch", "clutch", "fanny", "duffel"],
    "keys": ["key", "keys", "keychain", "fob", "lanyard", "car key", "dorm key"],
    "cards_ids": ["id", "card", "student id", "driver license", "credit card", "debit card", "metro card", "badge", "pass"],
    "clothing": ["jacket", "hoodie", "coat", "sweater", "hat", "cap", "gloves", "scarf", "umbrella", "glasses", "sunglasses"],
    "books_stationery": ["book", "textbook", "notebook", "binder", "pen", "pencil case", "notes", "folder"],
    "bottles_containers": ["bottle", "flask", "tumbler", "hydro flask", "yeti", "thermos", "mug", "lunchbox"],
    "jewelry_accessories": ["ring", "necklace", "bracelet", "watch", "earring", "chain"],
    "other": []
}

COLORS = [
    "black", "white", "silver", "gray", "grey", "gold", "blue", "navy", "red", "maroon",
    "green", "forest green", "yellow", "orange", "purple", "pink", "brown", "tan", "beige", "clear", "transparent"
]

BRANDS = [
    "apple", "samsung", "dell", "hp", "lenovo", "asus", "acer", "sony", "bose", "anker",
    "hydro flask", "hydroflask", "yeti", "stanley", "nike", "adidas", "north face", "patagonia",
    "jansport", "herschel", "casio", "texas instruments", "fossil", "logitech", "toyota", "honda"
]

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can't", "cannot", "could", "did", "do", "does", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "has", "have", "having", "he", "her", "here",
    "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it",
    "its", "itself", "let's", "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "same", "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasn't", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "won't", "would", "you", "your", "yours", "yourself", "yourselves",
    "item", "lost", "found", "looking", "please", "help", "reward", "contact", "left", "somewhere"
}


def clean_tokens(text: str) -> List[str]:
    """Tokenize and filter stop words from text."""
    if not text:
        return []
    words = re.findall(r'[a-zA-Z0-9]+', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 1]


def extract_attributes(text: str) -> Dict[str, List[str]]:
    """Extract recognized colors, brands, and item types from text."""
    lower = text.lower() if text else ""
    found_colors = [c for c in COLORS if re.search(r'\b' + re.escape(c) + r'\b', lower)]
    found_brands = [b for b in BRANDS if re.search(r'\b' + re.escape(b) + r'\b', lower)]
    
    types = []
    for cat, syns in CATEGORY_SYNONYMS.items():
        for syn in syns:
            if re.search(r'\b' + re.escape(syn) + r'\b', lower):
                types.append(syn)
                
    return {
        "colors": list(set(found_colors)),
        "brands": list(set(found_brands)),
        "item_types": list(set(types))
    }


def jaccard_similarity(tokens1: List[str], tokens2: List[str]) -> float:
    """Calculate Jaccard token similarity with overlap weight."""
    if not tokens1 or not tokens2:
        return 0.0
    set1, set2 = set(tokens1), set(tokens2)
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    if not union:
        return 0.0
    return len(intersection) / len(union)


def ngram_similarity(text1: str, text2: str, n: int = 3) -> float:
    """Character n-gram similarity to catch spelling variations and typos."""
    def get_ngrams(s: str):
        s = re.sub(r'[^a-z0-9]', '', s.lower())
        return {s[i:i+n] for i in range(len(s) - n + 1)} if len(s) >= n else {s}
    
    ng1 = get_ngrams(text1)
    ng2 = get_ngrams(text2)
    if not ng1 or not ng2:
        return 0.0
    intersection = ng1.intersection(ng2)
    union = ng1.union(ng2)
    return len(intersection) / len(union)


def compute_date_proximity(date_str1: str, date_str2: str) -> float:
    """
    Score date closeness.
    Lost before or on Found is ideal.
    Within 0-3 days: 1.0
    Within 7 days: 0.8
    Within 14 days: 0.5
    Within 30 days: 0.3
    Older: 0.1
    """
    if not date_str1 or not date_str2:
        return 0.5
    try:
        d1 = datetime.strptime(date_str1[:10], "%Y-%m-%d")
        d2 = datetime.strptime(date_str2[:10], "%Y-%m-%d")
        diff_days = abs((d1 - d2).days)
        
        if diff_days <= 1:
            return 1.0
        elif diff_days <= 3:
            return 0.9
        elif diff_days <= 7:
            return 0.75
        elif diff_days <= 14:
            return 0.55
        elif diff_days <= 30:
            return 0.35
        else:
            return 0.15
    except Exception:
        return 0.5


def calculate_match_score(lost_item: Dict[str, Any], found_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates detailed composite match score between a Lost item and a Found item.
    Returns:
    {
        "score": int (0 - 100),
        "confidence": "HIGH" | "MEDIUM" | "LOW",
        "reasons": List[str],
        "breakdown": {
            "title_score": float,
            "description_score": float,
            "category_score": float,
            "attribute_score": float,
            "location_score": float,
            "date_score": float
        }
    }
    """
    reasons = []
    
    # 1. Categories
    cat_lost = (lost_item.get("category") or "").strip().lower()
    cat_found = (found_item.get("category") or "").strip().lower()
    
    if cat_lost and cat_found:
        if cat_lost == cat_found:
            category_score = 1.0
            reasons.append(f"Matching category: {lost_item.get('category')}")
        elif cat_lost == "other" or cat_found == "other":
            category_score = 0.5
        else:
            category_score = 0.1
    else:
        category_score = 0.5
        
    # 2. Title Similarity
    title_lost = lost_item.get("title", "")
    title_found = found_item.get("title", "")
    t_tokens_lost = clean_tokens(title_lost)
    t_tokens_found = clean_tokens(title_found)
    
    title_jaccard = jaccard_similarity(t_tokens_lost, t_tokens_found)
    title_ngram = ngram_similarity(title_lost, title_found)
    title_score = max(title_jaccard * 0.7 + title_ngram * 0.3, 0.0)
    
    # Shared title words
    shared_title = set(t_tokens_lost).intersection(set(t_tokens_found))
    if shared_title:
        reasons.append(f"Key title overlap: {', '.join(sorted(list(shared_title))[:3])}")
        
    # 3. Description Similarity
    desc_lost = lost_item.get("description", "")
    desc_found = found_item.get("description", "")
    d_tokens_lost = clean_tokens(desc_lost)
    d_tokens_found = clean_tokens(desc_found)
    
    desc_jaccard = jaccard_similarity(d_tokens_lost, d_tokens_found)
    desc_ngram = ngram_similarity(desc_lost, desc_found)
    description_score = max(desc_jaccard * 0.6 + desc_ngram * 0.4, 0.0)
    
    all_lost_tokens = set(t_tokens_lost + d_tokens_lost)
    all_found_tokens = set(t_tokens_found + d_tokens_found)
    shared_all = all_lost_tokens.intersection(all_found_tokens)
    
    # 4. Extracted Attributes (Colors, Brands, Types)
    attr_lost = extract_attributes(f"{title_lost} {desc_lost}")
    attr_found = extract_attributes(f"{title_found} {desc_found}")
    
    shared_colors = set(attr_lost["colors"]).intersection(set(attr_found["colors"]))
    shared_brands = set(attr_lost["brands"]).intersection(set(attr_found["brands"]))
    shared_types = set(attr_lost["item_types"]).intersection(set(attr_found["item_types"]))
    
    attr_points = 0.0
    if shared_brands:
        attr_points += 0.45
        reasons.append(f"Same brand identified: {', '.join(shared_brands)}")
    if shared_colors:
        attr_points += 0.30
        reasons.append(f"Matching color: {', '.join(shared_colors)}")
    if shared_types:
        attr_points += 0.25
        reasons.append(f"Matching item type: {', '.join(shared_types)}")
        
    attribute_score = min(attr_points, 1.0)
    
    # 5. Location Proximity
    loc_lost = (lost_item.get("location_name") or "").strip().lower()
    loc_found = (found_item.get("location_name") or "").strip().lower()
    
    if loc_lost and loc_found:
        if loc_lost == loc_found:
            location_score = 1.0
            reasons.append(f"Same location: {lost_item.get('location_name')}")
        elif any(part in loc_found for part in loc_lost.split()) or any(part in loc_lost for part in loc_found.split()):
            location_score = 0.75
            reasons.append("Proximity location match")
        else:
            location_score = 0.3
    else:
        location_score = 0.4
        
    # 6. Date Proximity
    date_lost = lost_item.get("date_occurred", "")
    date_found = found_item.get("date_occurred", "")
    date_score = compute_date_proximity(date_lost, date_found)
    if date_score >= 0.75:
        reasons.append("Dates occurred in close temporal proximity")
        
    # Weighted composite score
    # Title & text: 35%
    # Attribute (brand/color/type): 25%
    # Category: 15%
    # Location: 15%
    # Date: 10%
    text_combined = max(title_score * 0.6 + description_score * 0.4, 
                        jaccard_similarity(list(all_lost_tokens), list(all_found_tokens)))
    
    weighted_total = (
        (text_combined * 0.35) +
        (attribute_score * 0.25) +
        (category_score * 0.15) +
        (location_score * 0.15) +
        (date_score * 0.10)
    )
    
    # Category conflict damper (e.g. if completely different category, cap the max score)
    if category_score <= 0.1 and not shared_brands and not shared_types:
        weighted_total = min(weighted_total, 0.40)
        
    final_percentage = int(round(weighted_total * 100))
    final_percentage = max(0, min(100, final_percentage))
    
    if final_percentage >= 70:
        confidence = "HIGH"
    elif final_percentage >= 45:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
        
    if not reasons and shared_all:
        reasons.append(f"Shared keywords: {', '.join(sorted(list(shared_all))[:3])}")
        
    return {
        "score": final_percentage,
        "confidence": confidence,
        "reasons": reasons,
        "breakdown": {
            "title_score": round(title_score, 2),
            "description_score": round(description_score, 2),
            "attribute_score": round(attribute_score, 2),
            "category_score": round(category_score, 2),
            "location_score": round(location_score, 2),
            "date_score": round(date_score, 2)
        }
    }


def find_matches_for_item(
    target_item: Dict[str, Any], 
    candidates: List[Dict[str, Any]], 
    min_score: int = 25, 
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Given a target item (either 'lost' or 'found'), find top matching candidates from the opposite type.
    """
    results = []
    target_type = target_item.get("type", "").lower()
    
    for candidate in candidates:
        cand_type = candidate.get("type", "").lower()
        # Candidate must be opposite type or target type if unspecified
        if target_type and cand_type and target_type == cand_type:
            continue
            
        # Determine who is lost vs found for scoring
        if target_type == "lost":
            lost_obj, found_obj = target_item, candidate
        else:
            lost_obj, found_obj = candidate, target_item
            
        match_info = calculate_match_score(lost_obj, found_obj)
        if match_info["score"] >= min_score:
            results.append({
                "item": candidate,
                "score": match_info["score"],
                "confidence": match_info["confidence"],
                "reasons": match_info["reasons"],
                "breakdown": match_info["breakdown"]
            })
            
    # Sort descending by score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def find_all_matches(
    lost_items: List[Dict[str, Any]], 
    found_items: List[Dict[str, Any]], 
    min_score: int = 35, 
    top_k: int = 20
) -> List[Dict[str, Any]]:
    """
    Matrix matching between all active lost items and all active found items.
    """
    matches = []
    for lost in lost_items:
        for found in found_items:
            match_info = calculate_match_score(lost, found)
            if match_info["score"] >= min_score:
                matches.append({
                    "lost_item": lost,
                    "found_item": found,
                    "score": match_info["score"],
                    "confidence": match_info["confidence"],
                    "reasons": match_info["reasons"],
                    "breakdown": match_info["breakdown"]
                })
                
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:top_k]


if __name__ == "__main__":
    # Test sample item matching
    sample_lost = {
        "id": 1,
        "type": "lost",
        "title": "White Apple AirPods Pro 2 in MagSafe Case",
        "description": "Lost my white AirPods Pro case with small scratch on the front lid. Left on 2nd floor library study desk.",
        "category": "Electronics",
        "location_name": "Central Library",
        "date_occurred": "2026-10-28"
    }
    
    sample_found = {
        "id": 2,
        "type": "found",
        "title": "Apple Wireless Earbuds / AirPods in white charging case",
        "description": "Found white Apple earbuds on a desk in the quiet reading area of Central Library.",
        "category": "Electronics",
        "location_name": "Central Library",
        "date_occurred": "2026-10-28"
    }
    
    res = calculate_match_score(sample_lost, sample_found)
    print("Match Test Result:")
    print(f"Score: {res['score']}% ({res['confidence']})")
    print(f"Reasons: {res['reasons']}")
    print(f"Breakdown: {res['breakdown']}")
