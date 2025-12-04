from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_URL = 'https://api.perplexity.ai/chat/completions'

def call_perplexity_ai(system_prompt, user_prompt, temperature=0.2):
    """Helper function to call Perplexity AI"""
    try:
        headers = {
            'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'llama-3.1-sonar-small-128k-online',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': temperature,
            'max_tokens': 1000
        }
        
        response = requests.post(PERPLEXITY_URL, json=payload, headers=headers)
        data = response.json()
        
        if 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content']
        else:
            raise Exception('Invalid AI response')
            
    except Exception as e:
        print(f'AI Error: {e}')
        raise e

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'Kenaz AI Backend Running!', 'version': '2.0'}), 200

# 1. Individual Ad Insights
@app.route('/api/ai-insights', methods=['POST'])
def ai_insights():
    try:
        data = request.json
        ad_data = data.get('adData')
        
        if not ad_data:
            return jsonify({'error': 'Ad data is required'}), 400
        
        system_prompt = 'You are an expert Facebook Ads analyst for perfume e-commerce in India. Provide actionable insights in clear bullet points.'
        
        user_prompt = f"""Analyze this perfume ad:

Ad: {ad_data.get('name')}
Spend: ₹{ad_data.get('spend')} | Revenue: ₹{ad_data.get('revenue')}
ROAS: {ad_data.get('roas')}x | Purchases: {ad_data.get('purchases')}
Impressions: {ad_data.get('impressions')} | Clicks: {ad_data.get('clicks')}
CTR: {ad_data.get('ctr')}% | CPC: ₹{ad_data.get('cpc')}

Provide:
1. Performance Assessment (Good/Average/Needs Improvement)
2. Top 3 Key Insights
3. 2-3 Specific Recommendations to improve ROAS"""

        insights = call_perplexity_ai(system_prompt, user_prompt)
        return jsonify({'insights': insights}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate insights'}), 500

# 2. Gender Analysis
@app.route('/api/gender-analysis', methods=['POST'])
def gender_analysis():
    try:
        data = request.json
        ads = data.get('ads', [])
        
        if not ads:
            return jsonify({'error': 'Ads data is required'}), 400
        
        system_prompt = 'You are a perfume marketing expert specializing in gender-based targeting and fragrance preferences.'
        
        ads_summary = '\n'.join([
            f"{ad['name']} - Spend: ₹{ad['spend']}, ROAS: {ad['roas']}x, Purchases: {ad['purchases']}"
            for ad in ads
        ])
        
        user_prompt = f"""Analyze gender targeting for these perfume ads:

{ads_summary}

Based on ad names (which may contain gender indicators like "Men", "Women", "Unisex"), provide:

1. **Gender Distribution Analysis:**
   - How many ads target men vs women vs unisex?
   - Which gender segment has better ROAS?
   - Total spend and revenue by gender

2. **Performance by Gender:**
   - Which gender ads are most profitable?
   - Average ROAS for each gender segment

3. **Recommendations:**
   - Should they invest more in specific gender segments?
   - Any untapped opportunities?

Format as clear sections with bullet points."""

        analysis = call_perplexity_ai(system_prompt, user_prompt, 0.3)
        return jsonify({'analysis': analysis}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate gender analysis'}), 500

# 3. Product Category Analysis
@app.route('/api/product-analysis', methods=['POST'])
def product_analysis():
    try:
        data = request.json
        ads = data.get('ads', [])
        
        if not ads:
            return jsonify({'error': 'Ads data is required'}), 400
        
        system_prompt = 'You are a perfume product analyst specializing in fragrance categories and pricing strategies.'
        
        # Group by product
        product_groups = {}
        for ad in ads:
            product = ad.get('product', 'Unknown')
            if product not in product_groups:
                product_groups[product] = {
                    'totalSpend': 0,
                    'totalRevenue': 0,
                    'purchases': 0,
                    'count': 0
                }
            product_groups[product]['totalSpend'] += float(ad.get('spend', 0))
            product_groups[product]['totalRevenue'] += float(ad.get('revenue', 0))
            product_groups[product]['purchases'] += int(ad.get('purchases', 0))
            product_groups[product]['count'] += 1
        
        product_summary = '\n'.join([
            f"{product}: {data['count']} ads, ₹{data['totalSpend']:.0f} spend, {data['purchases']} purchases, ROAS: {(data['totalRevenue'] / data['totalSpend'] if data['totalSpend'] > 0 else 0):.2f}x"
            for product, data in product_groups.items()
        ])
        
        user_prompt = f"""Analyze perfume product performance:

{product_summary}

Provide:
1. **Top Performing Products** (by ROAS and revenue)
2. **Underperforming Products** (needs optimization)
3. **Budget Allocation Recommendations**
4. **Product Mix Strategy** (which products to scale/pause)

Be specific with product names and numbers."""

        analysis = call_perplexity_ai(system_prompt, user_prompt, 0.3)
        return jsonify({'analysis': analysis}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate product analysis'}), 500

# 4. Creative & Copy Analysis
@app.route('/api/creative-analysis', methods=['POST'])
def creative_analysis():
    try:
        data = request.json
        ads = data.get('ads', [])
        
        if not ads:
            return jsonify({'error': 'Ads data is required'}), 400
        
        system_prompt = 'You are a creative advertising analyst specializing in visual content and ad copy for perfume brands.'
        
        top_ads = '\n'.join([
            f'"{ad["name"]}" - ROAS: {ad["roas"]}x, CTR: {ad["ctr"]}%, Purchases: {ad["purchases"]}'
            for ad in ads[:10]
        ])
        
        user_prompt = f"""Analyze these top-performing perfume ad creatives based on their names:

{top_ads}

Based on the ad names and performance, identify:

1. **Winning Ad Copy Patterns:**
   - What words/phrases appear in high-ROAS ads?
   - Common themes (sale, luxury, seasonal, etc.)

2. **Creative Format Success:**
   - Which formats work best (Reel, Video, Image)?
   - Optimal ad length/style indicators

3. **Messaging Recommendations:**
   - What messaging should be replicated?
   - What to avoid?

4. **Next Creative Ideas:**
   - 3 specific ad concepts to test based on winners"""

        analysis = call_perplexity_ai(system_prompt, user_prompt, 0.4)
        return jsonify({'analysis': analysis}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate creative analysis'}), 500

# 5. Budget Optimization
@app.route('/api/budget-optimization', methods=['POST'])
def budget_optimization():
    try:
        data = request.json
        ads = data.get('ads', [])
        total_budget = data.get('totalBudget', 0)
        
        if not ads:
            return jsonify({'error': 'Ads data is required'}), 400
        
        system_prompt = 'You are a performance marketing expert specializing in budget allocation and ROI optimization for e-commerce.'
        
        ads_summary = '\n'.join([
            f"{ad['name']} - Current Spend: ₹{ad['spend']}, ROAS: {ad['roas']}x, Purchases: {ad['purchases']}, CTR: {ad['ctr']}%"
            for ad in ads
        ])
        
        user_prompt = f"""Current total budget: ₹{total_budget}

Ad Performance:
{ads_summary}

Provide a detailed budget reallocation strategy:

1. **High Priority Ads** (increase budget):
   - Which ads deserve more budget and why?
   - Recommended budget increase percentage

2. **Low Priority Ads** (reduce/pause):
   - Which ads to scale down or stop?
   - Reasoning based on metrics

3. **Budget Reallocation Table:**
   - Current vs Recommended budget for each ad
   - Expected impact on overall ROAS

4. **Testing Budget:**
   - How much to allocate for new ad tests?

Be specific with rupee amounts."""

        analysis = call_perplexity_ai(system_prompt, user_prompt, 0.3)
        return jsonify({'analysis': analysis}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate budget optimization'}), 500

# 6. Audience & Targeting Insights
@app.route('/api/audience-analysis', methods=['POST'])
def audience_analysis():
    try:
        data = request.json
        ads = data.get('ads', [])
        
        if not ads:
            return jsonify({'error': 'Ads data is required'}), 400
        
        system_prompt = 'You are an audience targeting expert for perfume brands in India, specializing in demographic and psychographic segmentation.'
        
        avg_roas = sum(float(ad.get('roas', 0)) for ad in ads) / len(ads) if ads else 0
        
        user_prompt = f"""Analyze audience performance across these perfume ads:

Total Ads: {len(ads)}
Average ROAS: {avg_roas:.2f}x
Total Spend: ₹{sum(float(ad.get('spend', 0)) for ad in ads):.0f}

Based on ad performance patterns, provide:

1. **Audience Segmentation Insights:**
   - What audience characteristics likely respond best?
   - Age groups, interests, behaviors to target

2. **Geographic Recommendations:**
   - Which Indian cities/regions to focus on for perfumes?

3. **Timing & Seasonality:**
   - Best times to run perfume ads
   - Seasonal opportunities

4. **Lookalike Audience Strategy:**
   - How to scale winning audiences?

5. **Exclusion Recommendations:**
   - Audiences to exclude to improve efficiency"""

        analysis = call_perplexity_ai(system_prompt, user_prompt, 0.3)
        return jsonify({'analysis': analysis}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate audience analysis'}), 500

# 7. Comprehensive Campaign Report
@app.route('/api/campaign-report', methods=['POST'])
def campaign_report():
    try:
        data = request.json
        ads = data.get('ads', [])
        date_range = data.get('dateRange', {})
        
        if not ads:
            return jsonify({'error': 'Ads data is required'}), 400
        
        total_spend = sum(float(ad.get('spend', 0)) for ad in ads)
        total_revenue = sum(float(ad.get('revenue', 0)) for ad in ads)
        total_purchases = sum(int(ad.get('purchases', 0)) for ad in ads)
        avg_roas = (total_revenue / total_spend) if total_spend > 0 else 0
        
        system_prompt = 'You are a senior marketing director creating executive-level campaign reports for perfume e-commerce brands.'
        
        user_prompt = f"""Generate an executive summary for this perfume ad campaign:

📅 **Period:** {date_range.get('since')} to {date_range.get('until')}
📊 **Campaign Overview:**
- Total Ads: {len(ads)}
- Total Spend: ₹{total_spend:.0f}
- Total Revenue: ₹{total_revenue:.0f}
- Average ROAS: {avg_roas:.2f}x
- Total Purchases: {total_purchases}

Create a comprehensive report with:

1. **Executive Summary** (2-3 sentences)
2. **Key Wins** (Top 3 successes)
3. **Key Challenges** (Top 3 issues)
4. **Strategic Recommendations** (5 action items)
5. **Next 30 Days Plan** (Priorities)

Make it executive-friendly and action-oriented."""

        report = call_perplexity_ai(system_prompt, user_prompt, 0.3)
        return jsonify({'report': report}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate campaign report'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
