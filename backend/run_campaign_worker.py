#!/usr/bin/env python3
"""Script to run campaign worker"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from workers.campaign_worker import process_campaign_emails, process_campaign_follow_ups, check_campaign_replies
    import asyncio
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting campaign worker...")
    
    async def run_campaign_worker():
        """Main campaign worker loop"""
        while True:
            try:
                # Process campaign emails
                await process_campaign_emails()
                
                # Process follow-ups
                await process_campaign_follow_ups()
                
                # Check for replies
                await check_campaign_replies()
                
                # Wait 60 seconds before next iteration
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Campaign worker error: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    asyncio.run(run_campaign_worker())
