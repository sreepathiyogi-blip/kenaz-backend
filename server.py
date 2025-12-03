# server.py - Complete Kenaz Analytics API (All-in-One)
import json
import logging
import os
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

# --- Logging setup ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("kenaz_insight")

# --- FastAPI app ---
app = FastAPI(
    title="Kenaz Complete Analytics API",
    version="3.0",
    description="Ad performance insights + Video/Influencer content analysis for perfume marketing"
)

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ==================== PROMPTS (EMBEDDED) ====================

VIDEO_CONTENT_ANALYSIS_PROMPT = """
You are an expert video content analyzer specializing in advertising and marketing content for perfume and beauty brands. Analyze the provided video with precision, focusing on linguistic elements, visual text, and audio composition.

**ANALYSIS FRAMEWORK:**

## 1. SPOKEN CONTENT ANALYSIS (`speech_spoken`)

**Detection Protocol:**
- Identify ONLY human spoken dialogue or narration (voiceovers, presenters, testimonials)
- EXCLUDE: Sung lyrics, musical vocalizations, background chatter that's part of ambiance
- Confidence threshold: Only report if you can clearly understand words/sentences

**Output Rules:**
- If NO clear spoken dialogue detected: Return the exact string `"No discernible spoken dialogue or narration detected"`
- If spoken content IS detected:
  * Describe evidence (e.g., "Female narrator speaking throughout in Hindi")
  * List languages with confidence levels: "Hindi: 80% (Confidence: High)", "English: 20% (Confidence: Medium)"
  * For mixed languages (Hinglish): "Hinglish: 100% (Hindi ~60%, English ~40%) (Confidence: High)"

## 2. ON-SCREEN TEXT ANALYSIS (`written_text_on_screen`)

**Inclusion Criteria:**
- Legible text visible for 1+ seconds
- Product names, key benefits, pricing, offers, hashtags, captions
- Brand names, CTAs ("Shop Now", "Use Code XYZ")

**Exclusion Criteria:**
- Highly stylized/decorative text where letters are barely recognizable
- Fleeting text (<1 second) in small font
- Text embedded in complex logos where it's not the focus

**Output Rules:**
- If NO significant text detected: Return the exact string `"No significant, clearly discernible on-screen text detected"`
- If text IS detected:
  * List 2-4 key phrases extracted
  * Estimate language distribution: "English: 85% (Confidence: High)", "Hindi: 15% (Confidence: Medium)"

## 3. BACKGROUND AUDIO ANALYSIS (`background_audio_details`)

**Track Types:** song, instrumental_music, dialogue_snippet, sound_effect, ambient_noise, jingle

**For Each Element:**
```json
{
  "track_type": "song",
  "language": "Hindi" or "N/A",
  "confidence": "High|Medium|Low",
  "identifier": "Description or song name"
}
```

## 4. CONTENT SUMMARY (`content_summary`)

```json
{
  "overall_video_purpose": "Brief description of video purpose",
  "dominant_spoken_languages": "Language list or 'No discernible...'",
  "dominant_written_languages": ["Language list"] or "No significant...",
  "key_text_content_themes": ["Theme1", "Theme2"],
  "primary_background_audio_profile": "Audio description"
}
```

**OUTPUT JSON:**
```json
{
  "video_content_analysis": {
    "speech_spoken": "No discernible spoken dialogue or narration detected",
    "written_text_on_screen": ["English: 100% (Confidence: High)"],
    "background_audio_details": [{...}],
    "content_summary": {...}
  }
}
```
"""

INFLUENCER_VIDEO_ANALYSIS_PROMPT = """
You are an expert influencer marketing analyst for Kenaz India perfume brand. Extract these 8 fields from influencer videos:

## FIELDS TO EXTRACT:

1. **influencer_genre** + **influencer_genre_reason**
   Values: Beauty/Skincare, Fashion, Lifestyle, Travel, Daily Vlogs, Entertainment, Tips/Tricks, Fitness, Cooking/Food, Parenting, Comedy, Sketch Comedy, Tech, Hair Care, Home & DIY, Education & Career, Others

2. **influencer_gender**
   Values: Male, Female, Cannot Determine

3. **target_concern_mentioned** + **target_concern_mentioned_reason**
   Values: Acne, Uneven Skin Tone & Dullness, Hair Fall, Dandruff, Oiliness, Body Odor, Long-lasting Fragrance, Confidence Boost, Special Occasion, None/Others

4. **concept**
   Values: Before & After, Longevity Test, Comparison Test, Unboxing, First Impression, Empty Bottle Review, Favorites, Get Ready With Me, No Concept

5. **summary**
   2-3 sentences covering what influencer did, key message, CTA

6. **product_details**
   List of products with:
   ```json
   {
     "brand_name": "Kenaz" or competitor or null,
     "product_name": "Product name" or null,
     "mentioned_seconds": 45 or null
   }
   ```

7. **competitor_mentioned**
   Boolean: true/false

8. **kenaz_product_featured**
   Boolean: true/false

**OUTPUT JSON:**
```json
{
  "influencer_genre": "Fashion",
  "influencer_genre_reason": "Creator focuses on outfit styling",
  "influencer_gender": "Female",
  "target_concern_mentioned": "Long-lasting Fragrance",
  "target_concern_mentioned_reason": "Influencer states need for all-day scent",
  "concept": "Longevity Test",
  "summary": "Fashion influencer tests perfume over 8 hours...",
  "product_details": [{...}],
  "competitor_mentioned": false,
  "kenaz_product_featured": true
}
```
"""

LANGUAGE_EXTRACTION_PROMPT = """
Extract the SINGLE most dominant language from video analysis for both spoken and written content.

**LOGIC:**

1. **Spoken Language:**
   - If `speech_spoken` = "No discernible..." → Return "NA"
   - If list → Extract language with highest percentage
   - Example: ["Hindi: 70%", "English: 30%"] → "Hindi"

2. **Written Language:**
   - If `written_text_on_screen` = "No significant..." → Return "NA"
   - If list → Extract language with highest percentage

**OUTPUT:**
```json
{
  "spoken_language": "Hindi",
  "written_language": "English"
}
```
"""

PRODUCT_CATEGORIZATION_PROMPT = """
Categorize Kenaz India perfume products based on existing product mappings.

**KENAZ CATEGORIES:**
1. Perfumes - Eau de Parfum (EDP)
2. Perfumes - Eau de Toilette (EDT)
3. Perfumes - Perfume Oil
4. Body Care - Body Mist
5. Body Care - Deodorant
6. Gift Sets

**SUBCATEGORIES:**
- Target: Unisex, Men, Women
- Notes: Floral, Woody, Citrus, Oriental, Fresh, Spicy
- Size: 30ml, 50ml, 100ml, Travel Size

**OUTPUT:**
```json
{
  "new_product_name": "Product name",
  "category": "Perfumes - Eau de Parfum",
  "subcategory": "Men, Woody, 100ml",
  "reasoning": "Classification explanation"
}
```
"""


# ==================== PAYLOAD MODELS ====================

class AdPayload(BaseModel):
    """Payload model for ad performance data"""
    ad_name: str = Field(..., min_length=1, max_length=200)
    product: Optional[str] = Field(None, max_length=100)
    platform: Optional[str] = Field(None, max_length=50)
    
    spend: float = Field(0.0, ge=0)
    revenue: float = Field(0.0, ge=0)
    roas: Optional[float] = Field(None, ge=0)
    
    ctr: float = Field(0.0, ge=0, le=100)
    cpc: float = Field(0.0, ge=0)
    hook_rate: float = Field(0.0, ge=0, le=100)
    hold_rate: float = Field(0.0, ge=0, le=100)
    completion_rate: float = Field(0.0, ge=0, le=100)
    
    impressions: Optional[int] = Field(None, ge=0)
    clicks: Optional[int] = Field(None, ge=0)
    purchases: Optional[int] = Field(None, ge=0)
    
    extra: Optional[Dict[str, Any]] = None
    
    @validator('roas', always=True)
    def calculate_roas(cls, v, values):
        if v is None and 'spend' in values and values['spend'] > 0:
            revenue = values.get('revenue', 0.0)
            return round(revenue / values['spend'], 2)
        return v or 0.0


class LanguageExtractionPayload(BaseModel):
    """Payload for language extraction"""
    video_content_analysis: Dict[str, Any]


class ProductCategorizationPayload(BaseModel):
    """Payload for product categorization"""
    product_mapping: List[Dict[str, str]]
    new_product_name: str


# ==================== HELPER FUNCTIONS ====================

def round2(x: Any) -> float:
    try:
        return round(float(x), 2)
    except (ValueError, TypeError):
        return 0.0


def seed_from_text(s: str) -> int:
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(h[:16], 16)


def pick_deterministic(seed: int, options: List[str], k: int = 4) -> List[str]:
    import random
    r = random.Random(seed)
    shuffled = options.copy()
    r.shuffle(shuffled)
    return shuffled[:min(k, len(shuffled))]


# ==================== AD INSIGHT GENERATION ====================

def build_diagnostics(payload: AdPayload) -> Dict[str, Any]:
    return {
        "spend": round2(payload.spend),
        "revenue": round2(payload.revenue),
        "roas": round2(payload.roas),
        "impressions": int(payload.impressions or 0),
        "clicks": int(payload.clicks or 0),
        "purchases": int(payload.purchases or 0),
        "ctr_pct": round2(payload.ctr),
        "cpc": round2(payload.cpc),
        "hook_rate_pct": round2(payload.hook_rate),
        "hold_rate_pct": round2(payload.hold_rate),
        "completion_rate_pct": round2(payload.completion_rate),
    }


def identify_primary_bottleneck(diag: Dict[str, Any]) -> str:
    if diag["hold_rate_pct"] < 6.0 and diag["completion_rate_pct"] < 5.0:
        return "Critical viewer retention issue — very low hold and completion rates indicate viewers drop off quickly before conversion. Prioritize engaging content in the first 5-10 seconds and mid-video storytelling."
    
    if diag["hook_rate_pct"] < 50.0 and diag["ctr_pct"] < 0.5:
        return "Weak initial hook — low hook rate and CTR suggest the opening frame/first 3 seconds aren't compelling enough. Test stronger visual hooks, clearer value propositions, and improved thumbnails."
    
    if diag["roas"] < 1.0 and diag["clicks"] > 50:
        return "Conversion bottleneck — decent traffic but poor ROAS indicates landing page or offer misalignment. Review product-message fit, landing page load speed, checkout friction, and pricing clarity."
    
    if diag["ctr_pct"] < 0.5:
        return "Traffic generation challenge — low CTR suggests the ad isn't resonating with the target audience. Test different audience segments, creative formats, and messaging angles."
    
    if diag["roas"] >= 1.0 and diag["roas"] < 2.5:
        return "Moderate performance — ROAS is positive but has optimization potential. Focus on incremental improvements: creative iteration, audience refinement, and funnel optimization."
    
    return "Strong baseline performance — ad shows healthy metrics across the funnel. Focus on scaling winning elements, testing new creative variations, and exploring expansion audiences."


def generate_perfume_specific_suggestions() -> List[str]:
    return [
        "Test sensory-rich language in copy: emphasize notes (e.g., 'warm amber,' 'crisp citrus,' 'deep oud') to create olfactory imagination and emotional connection with the fragrance.",
        "Add short 2-3 second testimonial clips or user reaction shots (genuine surprise/delight expressions) to build social proof and convey the 'experience' of wearing the perfume.",
        "Create A/B test with lifestyle context: show the perfume in aspirational moments (date night, office confidence, evening out) vs. product-only shots to see which drives higher engagement.",
        "For Instagram Reels: front-load the bottle reveal within the first 2 seconds with dramatic lighting or slow-motion pour to capture attention before the algorithm decides to show your ad.",
        "Test urgency messaging for limited editions or seasonal scents: 'Only 200 bottles left' or 'Summer collection ending soon' can drive immediate action for premium perfumes.",
        "Leverage ASMR-style sound: include the 'click' of the bottle cap, spray sound, or subtle ambient music that complements the fragrance personality (elegant piano for floral, upbeat for citrus).",
        "Segment by occasion: run separate campaigns for 'everyday confidence' vs. 'special occasion luxury' with different creative angles and budget allocations based on performance.",
        "Include ingredient storytelling: if using premium/rare ingredients (saffron, rose absolute, jasmine sambac), highlight the craftsmanship to justify premium pricing and differentiate from mass-market options.",
        "Test influencer partnership clips: 2-3 second genuine reaction from a micro-influencer in your niche (fashion, lifestyle) can boost credibility and expand reach through their audience.",
        "Move CTA to the 60-70% mark instead of end-screen: viewers who watch past halfway are highly engaged; prompt them before they naturally drop off to maximize conversion capture."
    ]


def build_insight_and_suggestions(payload: AdPayload) -> Dict[str, Any]:
    diag = build_diagnostics(payload)
    
    insight_parts = []
    product_display = payload.product or "Product"
    platform_display = payload.platform or "Platform"
    
    insight_parts.append(
        f'**{payload.ad_name}** promoting {product_display} on {platform_display} '
        f'achieved **{diag["roas"]:.2f}x ROAS** with ₹{diag["spend"]:,.0f} spend generating ₹{diag["revenue"]:,.0f} revenue.'
    )
    
    insight_parts.append(
        f'Engagement: **{diag["ctr_pct"]:.2f}% CTR** (₹{diag["cpc"]:.2f} CPC), '
        f'**{diag["hook_rate_pct"]:.1f}% hook rate**, '
        f'**{diag["hold_rate_pct"]:.1f}% hold rate**, '
        f'**{diag["completion_rate_pct"]:.1f}% completion**.'
    )
    
    bottleneck = identify_primary_bottleneck(diag)
    insight_parts.append(f'\n**Primary Bottleneck:** {bottleneck}')
    
    insight_text = " ".join(insight_parts)
    
    all_suggestions = generate_perfume_specific_suggestions()
    seed = seed_from_text(payload.ad_name)
    selected_suggestions = pick_deterministic(seed, all_suggestions, k=5)
    
    context_parts = []
    if payload.product:
        context_parts.append(f"Product: {payload.product}")
    if payload.platform:
        context_parts.append(f"Platform: {payload.platform}")
    
    if context_parts:
        selected_suggestions[0] = f"{selected_suggestions[0]} [Context: {', '.join(context_parts)}]"
    
    return {
        "insight": insight_text,
        "suggestions": selected_suggestions,
        "diagnostics": diag,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# ==================== VIDEO ANALYSIS FUNCTIONS ====================

def extract_language_from_analysis(video_analysis: Dict[str, Any]) -> Dict[str, str]:
    try:
        speech_data = video_analysis.get("speech_spoken", "NA")
        text_data = video_analysis.get("written_text_on_screen", "NA")
        
        spoken_lang = "NA"
        if isinstance(speech_data, list) and len(speech_data) > 0:
            first_lang = speech_data[0].split(":")[0].strip()
            spoken_lang = first_lang
        elif isinstance(speech_data, str) and "No discernible" not in speech_data:
            spoken_lang = speech_data
        
        written_lang = "NA"
        if isinstance(text_data, list) and len(text_data) > 0:
            first_lang = text_data[0].split(":")[0].strip()
            written_lang = first_lang
        elif isinstance(text_data, str) and "No significant" not in text_data:
            written_lang = text_data
        
        return {
            "spoken_language": spoken_lang,
            "written_language": written_lang
        }
    except Exception as e:
        logger.error(f"Language extraction error: {str(e)}")
        return {"spoken_language": "NA", "written_language": "NA"}


def categorize_product(product_mapping: List[Dict[str, str]], new_product: str) -> Dict[str, str]:
    try:
        new_product_lower = new_product.lower()
        
        # Determine category
        if any(word in new_product_lower for word in ['edp', 'eau de parfum', 'perfume']):
            category = "Perfumes - Eau de Parfum"
        elif any(word in new_product_lower for word in ['edt', 'eau de toilette']):
            category = "Perfumes - Eau de Toilette"
        elif 'oil' in new_product_lower and 'perfume' in new_product_lower:
            category = "Perfumes - Perfume Oil"
        elif any(word in new_product_lower for word in ['mist', 'body mist']):
            category = "Body Care - Body Mist"
        elif any(word in new_product_lower for word in ['deo', 'deodorant']):
            category = "Body Care - Deodorant"
        elif any(word in new_product_lower for word in ['set', 'combo', 'kit', 'bundle']):
            category = "Gift Sets"
        else:
            category = "Perfumes - General"
        
        # Determine subcategory
        subcategory_parts = []
        
        if 'men' in new_product_lower or 'male' in new_product_lower:
            subcategory_parts.append("Men")
        elif 'women' in new_product_lower or 'female' in new_product_lower:
            subcategory_parts.append("Women")
        else:
            subcategory_parts.append("Unisex")
        
        if any(word in new_product_lower for word in ['oud', 'woody', 'sandalwood']):
            subcategory_parts.append("Woody")
        elif any(word in new_product_lower for word in ['rose', 'jasmine', 'floral']):
            subcategory_parts.append("Floral")
        elif any(word in new_product_lower for word in ['citrus', 'lemon', 'orange']):
            subcategory_parts.append("Citrus")
        
        if '100ml' in new_product_lower:
            subcategory_parts.append("100ml")
        elif '50ml' in new_product_lower:
            subcategory_parts.append("50ml")
        elif '30ml' in new_product_lower:
            subcategory_parts.append("30ml")
        
        subcategory = ", ".join(subcategory_parts) if subcategory_parts else "Standard"
        
        return {
            "new_product_name": new_product,
            "category": category,
            "subcategory": subcategory,
            "reasoning": f"Classified based on product name keywords and structure"
        }
    except Exception as e:
        logger.error(f"Product categorization error: {str(e)}")
        return {
            "new_product_name": new_product,
            "category": "Unknown",
            "subcategory": "Unknown",
            "reasoning": f"Error: {str(e)}"
        }


# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "service": "Kenaz Complete Analytics API",
        "version": "3.0",
        "endpoints": {
            "health": "/health",
            "ad_insights": "/api/kenaz-llm-insight (POST)",
            "video_prompt": "/api/video-analysis-prompt (GET)",
            "influencer_prompt": "/api/influencer-analysis-prompt (GET)",
            "language_extraction": "/api/extract-languages (POST)",
            "product_categorization": "/api/categorize-product (POST)",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "kenaz-complete-analytics",
        "version": "3.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/api/kenaz-llm-insight")
async def kenaz_llm_insight(request: Request):
    """Generate AI-powered insights for perfume ad campaigns"""
    try:
        payload_raw = await request.json()
        logger.info(f"Request received for ad: {payload_raw.get('ad_name', 'unknown')[:100]}")
        payload = AdPayload.parse_obj(payload_raw)
    except Exception as e:
        logger.error(f"Payload parsing failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request payload: {str(e)}")
    
    try:
        result = build_insight_and_suggestions(payload)
        logger.info(
            f"Generated insight for '{payload.ad_name}' | "
            f"ROAS: {result['diagnostics']['roas']:.2f}x | "
            f"Spend: ₹{result['diagnostics']['spend']:.0f}"
        )
        return result
    except Exception as e:
        logger.exception("Insight generation error")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@app.get("/api/video-analysis-prompt")
async def get_video_analysis_prompt():
    """Get prompt for video content analysis (use with LLM API)"""
    return {
        "prompt": VIDEO_CONTENT_ANALYSIS_PROMPT,
        "usage": "Send this prompt with your video to an LLM API (Claude, GPT-4V, etc.)",
        "expected_output": "JSON with video_content_analysis structure"
    }


@app.get("/api/influencer-analysis-prompt")
async def get_influencer_analysis_prompt():
    """Get prompt for influencer video analysis (use with LLM API)"""
    return {
        "prompt": INFLUENCER_VIDEO_ANALYSIS_PROMPT,
        "usage": "Send this prompt with influencer video to extract marketing metrics",
        "expected_output": "JSON with influencer metadata"
    }


@app.post("/api/extract-languages")
async def extract_languages(payload: LanguageExtractionPayload):
    """Extract dominant spoken and written languages from video analysis"""
    try:
        result = extract_language_from_analysis(payload.video_content_analysis)
        logger.info(f"Extracted languages - Spoken: {result['spoken_language']}, Written: {result['written_language']}")
        return result
    except Exception as e:
        logger.exception("Language extraction error")
        raise HTTPException(status_code=500, detail=f"Failed to extract languages: {str(e)}")


@app.post("/api/categorize-product")
async def categorize_product_endpoint(payload: ProductCategorizationPayload):
    """Categorize a new Kenaz product based on existing mappings"""
    try:
        result = categorize_product(payload.product_mapping, payload.new_product_name)
        logger.info(f"Categorized '{payload.new_product_name}' as {result['category']} - {result['subcategory']}")
        return result
    except Exception as e:
        logger.exception("Product categorization error")
        raise HTTPException(status_code=500, detail=f"Failed to categorize product: {str(e)}")


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )