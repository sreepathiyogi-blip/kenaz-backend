from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_API_URL = 'https://api.perplexity.ai/chat/completions'

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

# Individual Ad Analysis
@app.route('/api/ai-insights', methods=['POST', 'OPTIONS'])
def ai_insights():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        ad_data = data.get('adData', {})
        
        # Create prompt for Perplexity
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

Provide a brief analysis with:
1. Performance verdict (Excellent/Good/Average/Poor)
2. Key strengths
3. Areas for improvement
4. Actionable recommendations

Keep it concise (under 200 words)."""

        # Call Perplexity API
        response = requests.post(
            PERPLEXITY_API_URL,
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.1-sonar-small-128k-online',
                'messages': [
                    {'role': 'system', 'content': 'You are an expert Facebook ads analyst. Provide concise, actionable insights.'},
                    {'role': 'user', 'content': prompt}
                ]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            insights = result['choices'][0]['message']['content']
            return jsonify({'insights': insights}), 200
        else:
            return jsonify({'error': 'Perplexity API error'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add similar endpoints for other analyses...
# Gender, Product, Creative, Budget, Audience, Campaign Report

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
