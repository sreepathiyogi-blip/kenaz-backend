from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS to allow all origins
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False,
        "max_age": 3600
    }
})

# Perplexity API Configuration
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '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')
PERPLEXITY_API_URL = 'https://api.perplexity.ai/chat/completions'

def call_perplexity(prompt, system_message="You are an expert Facebook ads analyst."):
    """
    Helper function to call Perplexity API
    Returns the AI response or None on failure
    """
    try:
        if not PERPLEXITY_API_KEY or PERPLEXITY_API_KEY == '':
            logger.error("PERPLEXITY_API_KEY is not set!")
            return None
        
        logger.info(f"Calling Perplexity API with prompt length: {len(prompt)}")
        
        response = requests.post(
            PERPLEXITY_API_URL,
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.1-sonar-small-128k-online',
                'messages': [
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 1000
            },
            timeout=30
        )
        
        logger.info(f"Perplexity API Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            logger.info("Successfully received response from Perplexity")
            return content
        else:
            logger.error(f"Perplexity API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Perplexity API request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Perplexity API Request Exception: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in call_perplexity: {e}")
        return None

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/', methods=['GET'])
def home():
    """Homepage route - shows service info"""
    return jsonify({
        "service": "Kenaz AI Backend",
        "status": "running",
        "version": "1.0.0",
        "api_key_configured": bool(PERPLEXITY_API_KEY and PERPLEXITY_API_KEY != ''),
        "endpoints": {
            "health": "/health",
            "ai_insights": "/api/ai-insights",
            "gender_analysis": "/api/gender-analysis",
            "product_analysis": "/api/product-analysis",
            "creative_analysis": "/api/creative-analysis",
            "budget_optimization": "/api/budget-optimization",
            "audience_analysis": "/api/audience-analysis",
            "campaign_report": "/api/campaign-report"
        }
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    api_key_set = bool(PERPLEXITY_API_KEY and PERPLEXITY_API_KEY != '')
    return jsonify({
        "status": "healthy",
        "api_key_configured": api_key_set,
        "message": "Server is running properly" if api_key_set else "Warning: API key not configured"
    }), 200

# ============================================================================
# AI ANALYSIS ENDPOINTS
# ============================================================================

@app.route('/api/ai-insights', methods=['POST', 'OPTIONS'])
def ai_insights():
    """Individual Ad Analysis"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        logger.info("Received request for ai-insights")
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ad_data = data.get('adData', {})
        
        if not ad_data:
            return jsonify({'error': 'adData is required'}), 400
        
        prompt = f"""Analyze this Facebook ad performance for a perfume brand:

Ad Name: {ad_data.get('name', 'N/A')}
Spend: ₹{ad_data.get('spend', 0):,.2f}
Revenue: ₹{ad_data.get('revenue', 0):,.2f}
ROAS: {ad_data.get('roas', 0):.2f}x
Purchases: {ad_data.get('purchases', 0)}
Impressions: {ad_data.get('impressions', 0):,}
Clicks: {ad_data.get('clicks', 0)}
CTR: {ad_data.get('ctr', 0):.2f}%
CPC: ₹{ad_data.get('cpc', 0):.2f}

Provide a concise analysis with:
1. Performance Verdict (Excellent/Good/Average/Poor)
2. Key Strengths (2-3 points)
3. Areas for Improvement (2-3 points)
4. Actionable Recommendations (3-4 specific actions)

Keep it under 200 words. Be direct and specific."""

        insights = call_perplexity(prompt)
        
        if insights:
            return jsonify({'insights': insights}), 200
        else:
            return jsonify({'error': 'Failed to generate insights. Please check API key.'}), 500
            
    except Exception as e:
        logger.error(f"Error in ai_insights: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/gender-analysis', methods=['POST', 'OPTIONS'])
def gender_analysis():
    """Gender Targeting Analysis"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        logger.info("Received request for gender-analysis")
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ads = data.get('ads', [])
        
        if not ads:
            return jsonify({'error': 'No ads provided'}), 400
        
        # Build ad list summary (limit to first 20)
        ad_summary = "\n".join([
            f"- {ad.get('name', 'N/A')} | Spend: ₹{ad.get('spend', 0):,.0f} | ROAS: {ad.get('roas', 0):.2f}x | Purchases: {ad.get('purchases', 0)}"
            for ad in ads[:20]
        ])
        
        prompt = f"""Analyze gender targeting patterns in these Facebook perfume ads:

{ad_summary}

Provide insights on:
1. Which gender segments are performing best (based on ad naming patterns like M, F, M+F)
2. Gender-specific messaging patterns that work
3. Recommendations for gender-specific campaigns
4. Budget allocation suggestions between male/female/unisex products

Keep analysis under 250 words. Be specific and actionable."""

        analysis = call_perplexity(
            prompt, 
            "You are an expert in perfume marketing and gender-based ad targeting with deep knowledge of Indian market."
        )
        
        if analysis:
            return jsonify({'analysis': analysis}), 200
        else:
            return jsonify({'error': 'Failed to generate analysis'}), 500
            
    except Exception as e:
        logger.error(f"Error in gender_analysis: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/product-analysis', methods=['POST', 'OPTIONS'])
def product_analysis():
    """Product Performance Analysis"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        logger.info("Received request for product-analysis")
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ads = data.get('ads', [])
        
        if not ads:
            return jsonify({'error': 'No ads provided'}), 400
        
        # Build product performance summary (limit to 25)
        product_summary = "\n".join([
            f"- Product: {ad.get('product', 'Unknown')} | Ad: {ad.get('name', 'N/A')} | Spend: ₹{ad.get('spend', 0):,.0f} | ROAS: {ad.get('roas', 0):.2f}x"
            for ad in ads[:25]
        ])
        
        prompt = f"""Analyze product performance across these perfume ads:

{product_summary}

Provide:
1. Top 3 performing products (by ROAS and revenue)
2. Underperforming products that need attention
3. Product positioning insights
4. Cross-selling opportunities
5. Product-specific scaling recommendations

Keep it under 250 words. Focus on actionable insights."""

        analysis = call_perplexity(
            prompt, 
            "You are an expert in perfume product marketing and e-commerce strategy."
        )
        
        if analysis:
            return jsonify({'analysis': analysis}), 200
        else:
            return jsonify({'error': 'Failed to generate analysis'}), 500
            
    except Exception as e:
        logger.error(f"Error in product_analysis: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/creative-analysis', methods=['POST', 'OPTIONS'])
def creative_analysis():
    """Creative Pattern Analysis"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        logger.info("Received request for creative-analysis")
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ads = data.get('ads', [])
        
        if not ads:
            return jsonify({'error': 'No ads provided'}), 400
        
        # Analyze top performers (limit to 15)
        ad_summary = "\n".join([
            f"- {ad.get('name', 'N/A')} | ROAS: {ad.get('roas', 0):.2f}x | CTR: {ad.get('ctr', 0):.2f}% | Purchases: {ad.get('purchases', 0)}"
            for ad in ads[:15]
        ])
        
        prompt = f"""Analyze creative patterns in these top-performing perfume ads:

{ad_summary}

Identify:
1. Winning creative patterns (video vs image, formats)
2. Ad copy themes that resonate
3. Visual/format preferences
4. Messaging strategies that work
5. Creative testing recommendations

Keep it under 250 words. Be specific about what to test next."""

        analysis = call_perplexity(
            prompt, 
            "You are an expert in creative advertising and ad copywriting for e-commerce."
        )
        
        if analysis:
            return jsonify({'analysis': analysis}), 200
        else:
            return jsonify({'error': 'Failed to generate analysis'}), 500
            
    except Exception as e:
        logger.error(f"Error in creative_analysis: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/budget-optimization', methods=['POST', 'OPTIONS'])
def budget_optimization():
    """Budget Allocation Optimization"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        logger.info("Received request for budget-optimization")
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ads = data.get('ads', [])
        total_budget = data.get('totalBudget', 0)
        
        if not ads:
            return jsonify({'error': 'No ads provided'}), 400
        
        # Build spending summary (limit to 20)
        spend_summary = "\n".join([
            f"- {ad.get('name', 'N/A')} | Current: ₹{ad.get('spend', 0):,.0f} | ROAS: {ad.get('roas', 0):.2f}x | CTR: {ad.get('ctr', 0):.2f}%"
            for ad in ads[:20]
        ])
        
        prompt = f"""Analyze budget allocation for these perfume ads:

Total Budget: ₹{total_budget:,.2f}

{spend_summary}

Provide:
1. Budget reallocation recommendations (specific amounts/percentages)
2. Top 3 ads to scale up (and by how much)
3. Ads to pause or reduce spend
4. Expected ROAS impact of changes
5. Budget efficiency tips

Keep it under 250 words. Give specific numbers."""

        analysis = call_perplexity(
            prompt, 
            "You are an expert in Facebook ads budget optimization and ROI maximization."
        )
        
        if analysis:
            return jsonify({'analysis': analysis}), 200
        else:
            return jsonify({'error': 'Failed to generate analysis'}), 500
            
    except Exception as e:
        logger.error(f"Error in budget_optimization: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/audience-analysis', methods=['POST', 'OPTIONS'])
def audience_analysis():
    """Audience Targeting Analysis"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        logger.info("Received request for audience-analysis")
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ads = data.get('ads', [])
        
        if not ads:
            return jsonify({'error': 'No ads provided'}), 400
        
        # Build summary (limit to 25)
        ad_summary = "\n".join([
            f"- {ad.get('name', 'N/A')} | ROAS: {ad.get('roas', 0):.2f}x | Spend: ₹{ad.get('spend', 0):,.0f}"
            for ad in ads[:25]
        ])
        
        prompt = f"""Analyze audience targeting patterns in these perfume ads:

{ad_summary}

Based on ad naming and performance, identify:
1. Most effective audience segments
2. Demographics performing best (age, gender, location patterns)
3. Interest targeting insights
4. Lookalike audience opportunities
5. Audience expansion recommendations for scaling

Keep it under 250 words. Focus on Indian market insights."""

        analysis = call_perplexity(
            prompt, 
            "You are an expert in Facebook audience targeting and customer segmentation for Indian e-commerce."
        )
        
        if analysis:
            return jsonify({'analysis': analysis}), 200
        else:
            return jsonify({'error': 'Failed to generate analysis'}), 500
            
    except Exception as e:
        logger.error(f"Error in audience_analysis: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/campaign-report', methods=['POST', 'OPTIONS'])
def campaign_report():
    """Comprehensive Campaign Report"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        logger.info("Received request for campaign-report")
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ads = data.get('ads', [])
        date_range = data.get('dateRange', {})
        
        if not ads:
            return jsonify({'error': 'No ads provided'}), 400
        
        # Calculate totals
        total_spend = sum(ad.get('spend', 0) for ad in ads)
        total_revenue = sum(ad.get('revenue', 0) for ad in ads)
        total_purchases = sum(ad.get('purchases', 0) for ad in ads)
        avg_roas = total_revenue / total_spend if total_spend > 0 else 0
        
        prompt = f"""Generate a comprehensive campaign report for this perfume ad account:

📅 Date Range: {date_range.get('since', 'N/A')} to {date_range.get('until', 'N/A')}
📊 Total Ads: {len(ads)}
💰 Total Spend: ₹{total_spend:,.2f}
💵 Total Revenue: ₹{total_revenue:,.2f}
🛒 Total Purchases: {total_purchases}
📈 Average ROAS: {avg_roas:.2f}x

Provide:
1. Overall campaign performance summary
2. Key wins and highlights (top 3)
3. Major challenges identified (top 3)
4. Strategic recommendations for next period
5. Immediate action items (3-5 specific tasks)

Keep it under 300 words. Be executive-level concise."""

        report = call_perplexity(
            prompt, 
            "You are an expert marketing strategist specializing in e-commerce and Facebook advertising in India."
        )
        
        if report:
            return jsonify({'report': report}), 200
        else:
            return jsonify({'error': 'Failed to generate report'}), 500
            
    except Exception as e:
        logger.error(f"Error in campaign_report: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    logger.info("=" * 50)
    logger.info("🚀 Starting Kenaz AI Backend Server")
    logger.info(f"📍 Port: {port}")
    logger.info(f"🔑 API Key Configured: {bool(PERPLEXITY_API_KEY and PERPLEXITY_API_KEY != '')}")
    logger.info("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )
