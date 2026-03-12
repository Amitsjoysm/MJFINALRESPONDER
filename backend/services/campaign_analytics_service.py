"""
Campaign Analytics Service
Provides advanced analytics for campaigns including sentiment analysis, lead tracking, and conversion metrics
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import re

logger = logging.getLogger(__name__)

class CampaignAnalyticsService:
    """Service for campaign analytics and reporting"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def analyze_reply_sentiment(self, reply_text: str) -> str:
        """
        Analyze sentiment of email reply using keyword-based approach
        Returns: 'positive', 'neutral', or 'negative'
        """
        try:
            if not reply_text:
                return "neutral"
            
            reply_lower = reply_text.lower()
            
            # Positive indicators
            positive_keywords = [
                'interested', 'yes', 'sounds good', 'great', 'excellent', 'perfect',
                'love', 'amazing', 'awesome', 'fantastic', 'wonderful', 'brilliant',
                'thank you', 'thanks', 'appreciate', 'helpful', 'excited', 'looking forward',
                'would like', 'want to', 'let\'s', 'schedule', 'meeting', 'call me',
                'tell me more', 'learn more', 'more information'
            ]
            
            # Negative indicators
            negative_keywords = [
                'not interested', 'no thanks', 'unsubscribe', 'remove', 'stop',
                'spam', 'annoying', 'waste', 'don\'t', 'never', 'cannot', 'won\'t',
                'bad', 'terrible', 'awful', 'horrible', 'worst', 'disappointed',
                'frustrated', 'angry', 'upset', 'not happy', 'complaint'
            ]
            
            positive_count = sum(1 for keyword in positive_keywords if keyword in reply_lower)
            negative_count = sum(1 for keyword in negative_keywords if keyword in reply_lower)
            
            if negative_count > positive_count:
                return "negative"
            elif positive_count > negative_count:
                return "positive"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return "neutral"
    
    async def identify_lead_from_reply(self, reply_text: str) -> tuple[bool, int]:
        """
        Identify if reply indicates a lead and score it
        Returns: (is_lead, lead_score)
        """
        try:
            if not reply_text:
                return False, 0
            
            reply_lower = reply_text.lower()
            score = 0
            
            # High-intent keywords (20 points each)
            high_intent = [
                'interested', 'schedule', 'meeting', 'call', 'demo', 'trial',
                'pricing', 'quote', 'buy', 'purchase', 'sign up'
            ]
            
            # Medium-intent keywords (10 points each)
            medium_intent = [
                'more information', 'tell me more', 'learn more', 'details',
                'features', 'how does', 'can you', 'budget', 'timeline'
            ]
            
            # Low-intent keywords (5 points each)
            low_intent = [
                'maybe', 'possibly', 'considering', 'thinking about',
                'future', 'later', 'next year', 'keep in touch'
            ]
            
            for keyword in high_intent:
                if keyword in reply_lower:
                    score += 20
            
            for keyword in medium_intent:
                if keyword in reply_lower:
                    score += 10
            
            for keyword in low_intent:
                if keyword in reply_lower:
                    score += 5
            
            # Negative indicators (subtract points)
            negative = ['not interested', 'no thanks', 'unsubscribe', 'stop']
            for keyword in negative:
                if keyword in reply_lower:
                    score = 0
                    return False, 0
            
            # Cap at 100
            score = min(score, 100)
            
            # Consider it a lead if score >= 20
            is_lead = score >= 20
            
            return is_lead, score
            
        except Exception as e:
            logger.error(f"Error identifying lead: {e}")
            return False, 0
    
    async def identify_opportunity(self, reply_text: str, sentiment: str, is_lead: bool) -> bool:
        """
        Identify if reply indicates an opportunity (high-quality lead)
        """
        try:
            if not is_lead or sentiment == "negative":
                return False
            
            reply_lower = reply_text.lower()
            
            # Opportunity keywords
            opportunity_keywords = [
                'schedule', 'meeting', 'call', 'demo', 'pricing', 'quote',
                'when can', 'available', 'next steps', 'sign up', 'get started'
            ]
            
            for keyword in opportunity_keywords:
                if keyword in reply_lower:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error identifying opportunity: {e}")
            return False
    
    async def identify_conversion(self, reply_text: str, is_opportunity: bool) -> bool:
        """
        Identify if reply indicates a conversion (meeting booked, deal closed)
        """
        try:
            if not is_opportunity:
                return False
            
            reply_lower = reply_text.lower()
            
            # Conversion keywords
            conversion_keywords = [
                'booked', 'confirmed', 'scheduled', 'signed up', 'purchased',
                'enrolled', 'registered', 'yes, let\'s', 'deal', 'agreed'
            ]
            
            for keyword in conversion_keywords:
                if keyword in reply_lower:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error identifying conversion: {e}")
            return False
    
    async def update_campaign_metrics(self, campaign_id: str) -> Dict[str, Any]:
        """
        Calculate and update all campaign metrics
        """
        try:
            campaigns_collection = self.db['campaigns']
            emails_collection = self.db['campaign_emails']
            
            # Get campaign
            campaign = await campaigns_collection.find_one({"id": campaign_id})
            if not campaign:
                return {}
            
            # Get all emails for this campaign
            emails = await emails_collection.find({"campaign_id": campaign_id}).to_list(length=None)
            
            # Calculate metrics
            total_sent = len([e for e in emails if e.get('status') == 'sent'])
            total_delivered = total_sent - len([e for e in emails if e.get('bounced', False)])
            total_opened = len([e for e in emails if e.get('opened', False)])
            total_clicked = len([e for e in emails if e.get('clicked', False)])
            total_replied = len([e for e in emails if e.get('replied', False)])
            total_bounced = len([e for e in emails if e.get('bounced', False)])
            
            # Sentiment analysis
            positive_replies = len([e for e in emails if e.get('reply_sentiment') == 'positive'])
            neutral_replies = len([e for e in emails if e.get('reply_sentiment') == 'neutral'])
            negative_replies = len([e for e in emails if e.get('reply_sentiment') == 'negative'])
            
            # Lead generation
            leads_generated = len([e for e in emails if e.get('is_lead', False)])
            opportunities = len([e for e in emails if e.get('is_opportunity', False)])
            conversions = len([e for e in emails if e.get('is_converted', False)])
            
            # Calculate rates
            open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
            click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
            reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
            bounce_rate = (total_bounced / total_sent * 100) if total_sent > 0 else 0
            delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
            
            lead_rate = (leads_generated / total_replied * 100) if total_replied > 0 else 0
            opportunities_rate = (opportunities / total_replied * 100) if total_replied > 0 else 0
            conversion_rate = (conversions / total_replied * 100) if total_replied > 0 else 0
            
            # Estimate inbox rate (simplified - opens indicate inbox placement)
            inbox_rate = open_rate if open_rate > 0 else delivery_rate * 0.8  # Assume 80% of delivered go to inbox if no opens
            
            # Update campaign
            update_data = {
                "emails_sent": total_sent,
                "emails_delivered": total_delivered,
                "emails_opened": total_opened,
                "emails_clicked": total_clicked,
                "emails_replied": total_replied,
                "emails_bounced": total_bounced,
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "reply_rate": round(reply_rate, 2),
                "bounce_rate": round(bounce_rate, 2),
                "delivery_rate": round(delivery_rate, 2),
                "inbox_rate": round(inbox_rate, 2),
                "positive_replies": positive_replies,
                "neutral_replies": neutral_replies,
                "negative_replies": negative_replies,
                "leads_generated": leads_generated,
                "lead_rate": round(lead_rate, 2),
                "opportunities_created": opportunities,
                "opportunities_rate": round(opportunities_rate, 2),
                "conversions": conversions,
                "conversion_rate": round(conversion_rate, 2),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await campaigns_collection.update_one(
                {"id": campaign_id},
                {"$set": update_data}
            )
            
            return update_data
            
        except Exception as e:
            logger.error(f"Error updating campaign metrics: {e}")
            return {}
    
    async def get_campaign_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a campaign
        """
        try:
            # First update metrics
            await self.update_campaign_metrics(campaign_id)
            
            campaigns_collection = self.db['campaigns']
            campaign = await campaigns_collection.find_one({"id": campaign_id})
            
            if not campaign:
                return {}
            
            # Build analytics report
            analytics = {
                "campaign_id": campaign_id,
                "campaign_name": campaign.get("name"),
                "status": campaign.get("status"),
                
                # Volume metrics
                "total_contacts": campaign.get("total_contacts", 0),
                "emails_sent": campaign.get("emails_sent", 0),
                "emails_delivered": campaign.get("emails_delivered", 0),
                "emails_bounced": campaign.get("emails_bounced", 0),
                
                # Engagement metrics
                "emails_opened": campaign.get("emails_opened", 0),
                "emails_clicked": campaign.get("emails_clicked", 0),
                "emails_replied": campaign.get("emails_replied", 0),
                
                # Engagement rates
                "open_rate": campaign.get("open_rate", 0),
                "click_rate": campaign.get("click_rate", 0),
                "reply_rate": campaign.get("reply_rate", 0),
                "bounce_rate": campaign.get("bounce_rate", 0),
                
                # Deliverability
                "delivery_rate": campaign.get("delivery_rate", 0),
                "inbox_rate": campaign.get("inbox_rate", 0),
                
                # Sentiment analysis
                "sentiment_breakdown": {
                    "positive": campaign.get("positive_replies", 0),
                    "neutral": campaign.get("neutral_replies", 0),
                    "negative": campaign.get("negative_replies", 0)
                },
                
                # Lead metrics
                "leads_generated": campaign.get("leads_generated", 0),
                "lead_rate": campaign.get("lead_rate", 0),
                "opportunities_created": campaign.get("opportunities_created", 0),
                "opportunities_rate": campaign.get("opportunities_rate", 0),
                "conversions": campaign.get("conversions", 0),
                "conversion_rate": campaign.get("conversion_rate", 0),
                
                # Performance indicators
                "performance_score": await self._calculate_performance_score(campaign),
                "recommendations": await self._get_recommendations(campaign)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting campaign analytics: {e}")
            return {}
    
    async def _calculate_performance_score(self, campaign: Dict) -> int:
        """
        Calculate overall performance score (0-100)
        """
        try:
            score = 0
            
            # Open rate (30 points)
            open_rate = campaign.get("open_rate", 0)
            score += min(open_rate / 30 * 30, 30)  # 30% open rate = full points
            
            # Reply rate (25 points)
            reply_rate = campaign.get("reply_rate", 0)
            score += min(reply_rate / 5 * 25, 25)  # 5% reply rate = full points
            
            # Conversion rate (25 points)
            conversion_rate = campaign.get("conversion_rate", 0)
            score += min(conversion_rate / 10 * 25, 25)  # 10% conversion rate = full points
            
            # Deliverability (20 points)
            delivery_rate = campaign.get("delivery_rate", 0)
            score += min(delivery_rate / 95 * 20, 20)  # 95% delivery rate = full points
            
            return int(score)
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0
    
    async def _get_recommendations(self, campaign: Dict) -> List[str]:
        """
        Get recommendations for improving campaign performance
        """
        try:
            recommendations = []
            
            # Check open rate
            if campaign.get("open_rate", 0) < 20:
                recommendations.append("📧 Low open rate - Consider improving subject lines and send timing")
            
            # Check bounce rate
            if campaign.get("bounce_rate", 0) > 5:
                recommendations.append("⚠️ High bounce rate - Clean your email list and verify addresses")
            
            # Check reply rate
            if campaign.get("reply_rate", 0) < 2:
                recommendations.append("💬 Low reply rate - Personalize your emails and include clear CTAs")
            
            # Check deliverability
            if campaign.get("delivery_rate", 0) < 90:
                recommendations.append("📬 Low delivery rate - Check email authentication (SPF, DKIM, DMARC)")
            
            # Check sentiment
            negative_replies = campaign.get("negative_replies", 0)
            total_replies = campaign.get("emails_replied", 0)
            if total_replies > 0 and negative_replies / total_replies > 0.3:
                recommendations.append("😟 High negative sentiment - Review your messaging and targeting")
            
            # Check conversion
            if campaign.get("conversion_rate", 0) < 5:
                recommendations.append("🎯 Low conversion rate - Optimize your value proposition and follow-up strategy")
            
            # Check tracking settings
            tracking_settings = campaign.get("tracking_settings", {})
            if not tracking_settings.get("enable_open_tracking", True):
                recommendations.append("📊 Enable open tracking for better insights")
            
            return recommendations if recommendations else ["✅ Campaign performing well! Keep up the good work."]
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
