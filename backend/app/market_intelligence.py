from typing import List, Dict, Any
import statistics
from datetime import datetime
from .reasoning import recommend_markets

class MarketIntelligence:
    def __init__(self):
        self.risk_categories = {
            'low': {'volume_threshold': 100000, 'liquidity_threshold': 50000, 'spread_threshold': 0.05},
            'medium': {'volume_threshold': 50000, 'liquidity_threshold': 25000, 'spread_threshold': 0.10},
            'high': {'volume_threshold': 10000, 'liquidity_threshold': 5000, 'spread_threshold': 0.20}
        }
    
    def analyze_market_health(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the overall health and risk profile of a market"""
        pricing = market.get('pricing', {})
        volume = pricing.get('volume', 0)
        liquidity = pricing.get('liquidity', 0)
        spread = pricing.get('spread', 0)
        
        risk_level = self._calculate_risk_level(volume, liquidity, spread)
        confidence = self._calculate_confidence(volume, liquidity, spread)
        activity_score = self._calculate_activity_score(volume, liquidity)
        
        return {
            'risk_level': risk_level,
            'confidence_score': confidence,
            'activity_score': activity_score,
            'volume_health': 'healthy' if volume > 50000 else 'low' if volume > 10000 else 'very_low',
            'liquidity_health': 'healthy' if liquidity > 25000 else 'low' if liquidity > 5000 else 'very_low',
            'spread_health': 'tight' if spread < 0.05 else 'moderate' if spread < 0.15 else 'wide'
        }
    
    def generate_market_insights(self, market: Dict[str, Any], all_markets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive insights for a specific market"""
        question = market.get('question', '')
        category = market.get('category', '')
        pricing = market.get('pricing', {})
        
        health_analysis = self.analyze_market_health(market)
        price_analysis = self._analyze_pricing(pricing)
        category_context = self._analyze_category_context(category, all_markets)
        similar_markets = self._find_similar_markets(market, all_markets)
        probability_analysis = self._assess_probability(market, all_markets)
        recommendations = self._generate_recommendations(market, health_analysis, price_analysis)
        
        return {
            'market_question': question,
            'category': category,
            'health_analysis': health_analysis,
            'price_analysis': price_analysis,
            'category_context': category_context,
            'similar_markets': similar_markets,
            'probability_analysis': probability_analysis,
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_risk_level(self, volume: float, liquidity: float, spread: float) -> str:
        """Calculate risk level based on market metrics"""
        if (volume >= self.risk_categories['low']['volume_threshold'] and 
            liquidity >= self.risk_categories['low']['liquidity_threshold'] and 
            spread <= self.risk_categories['low']['spread_threshold']):
            return 'low'
        elif (volume >= self.risk_categories['medium']['volume_threshold'] and 
              liquidity >= self.risk_categories['medium']['liquidity_threshold'] and 
              spread <= self.risk_categories['medium']['spread_threshold']):
            return 'medium'
        else:
            return 'high'
    
    def _calculate_confidence(self, volume: float, liquidity: float, spread: float) -> int:
        """Calculate confidence score (0-100) based on market metrics"""
        volume_score = min(volume / 100000 * 30, 30)
        liquidity_score = min(liquidity / 50000 * 30, 30)
        spread_score = max(0, 40 - (spread * 200))
        
        return int(volume_score + liquidity_score + spread_score)
    
    def _calculate_activity_score(self, volume: float, liquidity: float) -> int:
        """Calculate activity score based on trading volume and liquidity"""
        if volume > 100000 and liquidity > 50000:
            return 90
        elif volume > 50000 and liquidity > 25000:
            return 70
        elif volume > 10000 and liquidity > 5000:
            return 50
        else:
            return 30
    
    def _analyze_pricing(self, pricing: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pricing data and trends"""
        yes_price = pricing.get('outcomeYesPrice', 0)
        no_price = pricing.get('outcomeNoPrice', 0)
        spread = pricing.get('spread', 0)
        
        implied_probability = yes_price if yes_price > 0 else 0.5
        price_stability = 'stable' if spread < 0.05 else 'volatile' if spread < 0.15 else 'highly_volatile'
        
        return {
            'yes_price': yes_price,
            'no_price': no_price,
            'spread': spread,
            'implied_probability': implied_probability,
            'price_stability': price_stability,
            'arbitrage_opportunity': 'yes' if abs(yes_price + no_price - 1.0) > 0.05 else 'no'
        }
    
    def _analyze_category_context(self, category: str, all_markets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the broader context of the market's category"""
        category_markets = [m for m in all_markets if m.get('category', '').lower() == category.lower()]
        
        if not category_markets:
            return {'total_markets': 0, 'avg_volume': 0, 'trend': 'unknown'}
        
        volumes = [m.get('pricing', {}).get('volume', 0) for m in category_markets]
        avg_volume = statistics.mean(volumes) if volumes else 0
        
        high_volume_count = len([v for v in volumes if v > avg_volume * 1.5])
        trend = 'hot' if high_volume_count > len(volumes) * 0.3 else 'stable'
        
        return {
            'total_markets': len(category_markets),
            'avg_volume': avg_volume,
            'trend': trend,
            'category_activity': 'high' if avg_volume > 50000 else 'medium' if avg_volume > 10000 else 'low'
        }
    
    def _find_similar_markets(self, target_market: Dict[str, Any], all_markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find markets similar to the target market"""
        target_slug = target_market.get('slug', '')
        if not target_slug:
            return []
        
        try:
            recommendations = recommend_markets(all_markets, target_slug)
            similar_markets = []
            
            for slug in recommendations[:3]:
                similar_market = next((m for m in all_markets if m.get('slug') == slug), None)
                if similar_market:
                    similar_markets.append({
                        'question': similar_market.get('question', ''),
                        'slug': slug,
                        'volume': similar_market.get('pricing', {}).get('volume', 0),
                        'liquidity': similar_market.get('pricing', {}).get('liquidity', 0)
                    })
            
            return similar_markets
        except Exception as e:
            print(f"Error finding similar markets: {e}")
            return []
    
    def _assess_probability(self, market: Dict[str, Any], all_markets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the probability of the market outcome"""
        pricing = market.get('pricing', {})
        yes_price = pricing.get('outcomeYesPrice', 0.5)
        
        market_probability = yes_price
        historical_accuracy = 0.52
        
        confidence = self._calculate_confidence(
            pricing.get('volume', 0),
            pricing.get('liquidity', 0),
            pricing.get('spread', 0)
        )
        
        return {
            'market_implied_probability': market_probability,
            'historical_accuracy': historical_accuracy,
            'confidence_level': confidence,
            'probability_assessment': self._get_probability_description(market_probability, confidence)
        }
    
    def _get_probability_description(self, probability: float, confidence: int) -> str:
        """Get a human-readable description of the probability"""
        if probability < 0.3:
            desc = "Very unlikely"
        elif probability < 0.4:
            desc = "Unlikely"
        elif probability < 0.6:
            desc = "Toss-up"
        elif probability < 0.7:
            desc = "Likely"
        else:
            desc = "Very likely"
        
        confidence_desc = "high confidence" if confidence > 70 else "medium confidence" if confidence > 40 else "low confidence"
        
        return f"{desc} ({confidence_desc})"
    
    def _generate_recommendations(self, market: Dict[str, Any], health_analysis: Dict[str, Any], price_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations for the market"""
        recommendations = []
        
        risk_level = health_analysis['risk_level']
        if risk_level == 'high':
            recommendations.append("⚠️ High risk market - consider smaller position size")
        elif risk_level == 'low':
            recommendations.append("✅ Low risk market - good for larger positions")
        
        volume_health = health_analysis['volume_health']
        if volume_health == 'very_low':
            recommendations.append("📉 Very low volume - may have liquidity issues")
        elif volume_health == 'healthy':
            recommendations.append("📈 Healthy volume - good liquidity available")
        
        if price_analysis['arbitrage_opportunity'] == 'yes':
            recommendations.append("💰 Arbitrage opportunity detected - prices don't sum to 1.0")
        
        if price_analysis['price_stability'] == 'highly_volatile':
            recommendations.append("⚡ Highly volatile - expect significant price swings")
        
        confidence = health_analysis['confidence_score']
        if confidence < 40:
            recommendations.append("❓ Low confidence - consider waiting for more data")
        elif confidence > 80:
            recommendations.append("🎯 High confidence - strong market signals")
        
        return recommendations

def generate_market_analysis(market: Dict[str, Any], all_markets: List[Dict[str, Any]]) -> str:
    """Generate a comprehensive market analysis in natural language"""
    intelligence = MarketIntelligence()
    insights = intelligence.generate_market_insights(market, all_markets)
    
    analysis = f"""
🔍 **MARKET ANALYSIS: {insights['market_question']}**

**📊 Market Health:**
• Risk Level: {insights['health_analysis']['risk_level'].upper()}
• Confidence Score: {insights['health_analysis']['confidence_score']}/100
• Activity Level: {insights['health_analysis']['activity_score']}/100

**💰 Pricing Analysis:**
• Yes Price: ${insights['price_analysis']['yes_price']:.3f}
• No Price: ${insights['price_analysis']['no_price']:.3f}
• Implied Probability: {insights['price_analysis']['implied_probability']:.1%}
• Price Stability: {insights['price_analysis']['price_stability'].replace('_', ' ').title()}

**📈 Category Context:**
• Total {insights['category']} markets: {insights['category_context']['total_markets']}
• Average volume: ${insights['category_context']['avg_volume']:,.0f}
• Category trend: {insights['category_context']['trend'].title()}

**🎯 Probability Assessment:**
• Market-implied probability: {insights['probability_analysis']['market_implied_probability']:.1%}
• Assessment: {insights['probability_analysis']['probability_assessment']}

**💡 Recommendations:**
"""
    
    for rec in insights['recommendations']:
        analysis += f"• {rec}\n"
    
    if insights['similar_markets']:
        analysis += f"\n**🔗 Similar Markets:**\n"
        for similar in insights['similar_markets']:
            analysis += f"• {similar['question'][:60]}... (Vol: ${similar['volume']:,.0f})\n"
    
    return analysis.strip()
