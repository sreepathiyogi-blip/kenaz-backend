from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_API_URL = 'https://api.perplexity.ai/chat/completions'

def call_perplexity(prompt, system_message="You are an expert Facebook ads analyst."):
    """Helper function to call Perplexity API"""
    try:
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
                ]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return None
    except Exception as e:
        print(f"Perplexity API Error: {e}")
        return None

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

# 1. Individual Ad Analysis
@app.route('/api/ai-insights', methods=['POST', 'OPTIONS'])
def ai_insights():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        ad_data = data.get('adData', {})
        
        prompt = f"""Analyze this Facebook ad performance:
        
Ad Name: {ad_data.get('name')}
Spend: ${ad_data.get('spend', 0):.2f}
Revenue: ${ad_data.get('revenue', 0):.2f}
ROAS: {ad_data.get('roas', 0):.2f}
Purchases: {ad_data.get('purchases', 0)}
Impressions: {ad_data.get('impressions', 0)}
Clicks: {ad_data.get('clicks', 0)}
CTR: {ad_data.get('ctr', 0):.2f}%
CPC: ${ad_data.get('cpc', 0):.2f}

Provide:
1. Performance verdict
2. Key strengths
3. Areas for improvement
4. Actionable recommendations

Keep it under 200 words."""

        insights = call_perplexity(prompt)
        
        if insights:
            return jsonify({'insights': insights}), 200
        else:
            return jsonify({'error': 'Failed to generate insights'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 2. Gender Analysis
@app.route('/api/gender-analysis', methods=['POST', 'OPTIONS'])
def gender_analysis():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        ads = data.get('ads', [])
        
        # Build ad list summary
        ad_summary = "\n".join([
            f"- {ad.get('name')} | Spend: ${ad.get('spend', 0):.2f} | ROAS: {ad.get('roas', 0):.2f} | Purchases: {ad.get('purchases', 0)}"
            for ad in ads[:20]  # Limit to first 20
        ])
        
        prompt = f"""Analyze gender targeting patterns in these Facebook ads for perfume products:

{ad_summary}

Provide insights on:
1. Which gender segments are performing best
2. Gender-specific messaging patterns
3. Recommendations for gender-specific campaigns
4. Budget allocation suggestions

Keep it under 250 words."""

        analysis = call_perplexity(prompt, "You are an expert in perfume marketing and gender-based ad targeting.")
        
        if analysis:
            return jsonify({'analysis': analysis}), 200
        else:
            return jsonify({'error': 'Failed to generate analysis'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 3. Product Analysis
@app.route('/api/product-analysis', methods=['POST', 'OPTIONS'])
def product_analysis():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        ads = data.get('ads', [])
        
        # Build product performance summary
        product_summary = "\n".join([
            f"- Product: {ad.get('product', 'Unknown')} | Ad: {ad.get('name')} | Spend: ${ad.get('spend', 0):.2f} | ROAS: {ad.get('roas', 0):.2f}"
            for ad in ads[:25]
        ])
        
        prompt = f"""Analyze product performance across these perfume ads:

{product_summary}

Provide:
1. Top performing products
2. Underperforming products
3. Product positioning insights
4. Cross-selling opportunities
5. Product-specific recommendations

Keep it under 250 words."""

        analysis = call_perplexity(prompt, "You are an expert in perfume product marketing and e-commerce.")
        
        if analysis:
            return jsonify({'analysis': analysis}), 200
        else:
            return jsonify({'error': 'Failed to generate analysis'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 4. Creative Analysis
@app.route('/api/creative-analysis', methods=['POST', 'OPTIONS'])
def creative_analysis():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        ads = data.get('ads', [])
        
        # Analyze top performers
        ad_summary = "\n".join([
            f"- {ad.get('name')} | ROAS: {ad.get('roas', 0):.2f} | CTR: {ad.get('ctr', 0):.2f}% | Purchases: {ad.get('purchases', 0)}"
            for ad in ads[:15]
        ])
        
        prompt = f"""Analyze creative patterns in these top-performing perfume ads:

{ad_summary}

Identify:
1. Winning creative patterns
2. Ad copy themes
3. Visual/format preferences
4. Messaging strategies
5. Creative recommendations

Keep it under 250 words."""

        analysis = call_perplexity(prompt, "You are an expert in creative advertising and ad copywriting.")
        
        if analysis:
            return jsonify({'analysis': analysis}), 200
        else:
            return jsonify({'error': 'Failed to generate analysis'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 5. Budget Optimization
@app.route('/api/budget-optimization', methods=['POST', 'OPTIONS'])
def budget_optimization():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        ads = data.get('ads', [])
        total_budget = data.get('totalBudget', 0)
        
        # Build spending summary
        spend_summary = "\n".join([
            f"- {ad.get('name')} | Current Spend: ${ad.get('spend', 0):.2f} | ROAS: {ad.get('roas', 0):.2f} | CTR: {ad.get('ctr', 0):.2f}%"
            for ad in ads[:20]
        ])
        
        prompt = f"""Analyze budget allocation for these perfume ads:

Total Budget: ${total_budget:.2f}

{spend_summary}

Provide:
1. Budget reallocation recommendations
2. Ads to scale up
3. Ads to pause or reduce
4. Expected impact of changes
5. Budget efficiency tips

Keep it under 250 words."""

        analysis = call_perplexity(prompt, "You are an expert in Facebook ads budget optimization and ROI maximization.")
        
        if analysis:
            return jsonify({'analysis': analysis}), 200
        else:
            return jsonify({'error': 'Failed to generate analysis'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 6. Audience Analysis
@app.route('/api/audience-analysis', methods=['POST', 'OPTIONS'])
def audience_analysis():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        ads = data.get('ads', [])
        
        # Extract ad names for pattern analysis
        ad_names = [ad.get('name', '') for ad in ads[:30]]
        
        # Build summary
        ad_summary = "\n".join([
            f"- {ad.get('name')} | ROAS: {ad.get('roas', 0):.2f} | Spend: ${ad.get('spend', 0):.2f}"
            for ad in ads[:25]
        ])
        
        prompt = f"""Analyze audience targeting patterns in these perfume ads:

{ad_summary}

Based on ad naming and performance, identify:
1. Most effective audience segments
2. Demographics performing best
3. Interest targeting insights
4. Lookalike audience opportunities
5. Audience expansion recommendations

Keep it under 250 words."""

        analysis = call_perplexity(prompt, "You are an expert in Facebook audience targeting and customer segmentation.")
        
        if analysis:
            return jsonify({'analysis': analysis}), 200
        else:
            return jsonify({'error': 'Failed to generate analysis'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 7. Campaign Report
@app.route('/api/campaign-report', methods=['POST', 'OPTIONS'])
def campaign_report():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        ads = data.get('ads', [])
        date_range = data.get('dateRange', {})
        
        # Calculate totals
        total_spend = sum(ad.get('spend', 0) for ad in ads)
        total_revenue = sum(ad.get('revenue', 0) for ad in ads)
        total_purchases = sum(ad.get('purchases', 0) for ad in ads)
        avg_roas = total_revenue / total_spend if total_spend > 0 else 0
        
        prompt = f"""Generate a comprehensive campaign report for this perfume ad account:

Date Range: {date_range.get('since', 'N/A')} to {date_range.get('until', 'N/A')}
Total Ads: {len(ads)}
Total Spend: ${total_spend:.2f}
Total Revenue: ${total_revenue:.2f}
Total Purchases: {total_purchases}
Average ROAS: {avg_roas:.2f}

Provide:
1. Overall campaign performance summary
2. Key wins and highlights
3. Major challenges
4. Strategic recommendations
5. Action items for next period

Keep it under 300 words."""

        report = call_perplexity(prompt, "You are an expert marketing strategist specializing in e-commerce and Facebook advertising.")
        
        if report:
            return jsonify({'report': report}), 200
        else:
            return jsonify({'error': 'Failed to generate report'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
