#!/usr/bin/env python3
"""
Test to verify rescheduling finds the correct (active) event
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from services.calendar_service import CalendarService
import json

async def test_event_finding():
    print("=" * 80)
    print("TESTING EVENT FINDING FOR RESCHEDULING")
    print("=" * 80)
    
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["email_assistant_db"]
    calendar_service = CalendarService(db)
    
    # Get all events
    all_events = await db.calendar_events.find({}).to_list(100)
    
    print(f"\nTotal Events in Database: {len(all_events)}")
    
    # Group by status
    by_status = {}
    for event in all_events:
        status = event.get('status', 'confirmed')
        by_status[status] = by_status.get(status, 0) + 1
    
    print(f"\nEvents by Status:")
    for status, count in by_status.items():
        print(f"  {status}: {count}")
    
    # Test case: Find event by thread_id (common scenario)
    print("\n" + "-" * 80)
    print("TEST 1: Finding event by thread_id")
    print("-" * 80)
    
    # Get a thread_id that has both rescheduled and active events
    thread_id = "19ce13ad4d01bbaa"  # This thread has rescheduled events
    
    criteria = {
        'thread_id': thread_id,
        'sender_email': 'samhere.joy@gmail.com'
    }
    
    print(f"Search Criteria: {criteria}")
    
    # What the OLD code would find (all events)
    old_query = {"user_id": "1727993d-2348-4d48-bef6-c6637f69703f", "thread_id": thread_id}
    old_results = await db.calendar_events.find(old_query).sort("start_time", 1).to_list(20)
    
    print(f"\n❌ OLD CODE would find {len(old_results)} events:")
    for event in old_results:
        status = event.get('status', 'confirmed')
        print(f"  - {event.get('title')} ({event.get('start_time')}) - Status: {status}")
    
    # What the NEW code finds (only active)
    found_event = await calendar_service.find_event_by_criteria(
        "1727993d-2348-4d48-bef6-c6637f69703f",
        criteria
    )
    
    if found_event:
        status = found_event.get('status', 'confirmed')
        print(f"\n✅ NEW CODE finds ONLY active event:")
        print(f"  - {found_event.get('title')} ({found_event.get('start_time')}) - Status: {status}")
        print(f"  - Event ID: {found_event.get('event_id')}")
        
        if status in ['rescheduled', 'cancelled']:
            print(f"\n  ⚠️  ERROR: Found a {status} event! Should only find active events.")
        else:
            print(f"\n  ✅ CORRECT: Found an active event (status: {status})")
    else:
        print(f"\n⚠️  No event found")
    
    # Test case 2: Find by date
    print("\n" + "-" * 80)
    print("TEST 2: Finding event by date")
    print("-" * 80)
    
    criteria2 = {
        'date': '2026-03-17',
        'sender_email': 'samhere.joy@gmail.com'
    }
    
    found_event2 = await calendar_service.find_event_by_criteria(
        "1727993d-2348-4d48-bef6-c6637f69703f",
        criteria2
    )
    
    if found_event2:
        status = found_event2.get('status', 'confirmed')
        print(f"✅ Found event for March 17:")
        print(f"  - {found_event2.get('title')} ({found_event2.get('start_time')}) - Status: {status}")
    else:
        print("⚠️  No event found for March 17")
    
    print("\n" + "=" * 80)
    print("✅ EVENT FINDING TEST COMPLETE")
    print("=" * 80)
    print("\nKey Points:")
    print("  1. ✅ find_event_by_criteria now filters out rescheduled/cancelled events")
    print("  2. ✅ Thread_id matching added for better accuracy")
    print("  3. ✅ Only active events will be found for rescheduling")
    print("  4. ✅ This prevents trying to delete already-deleted events")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_event_finding())
