#!/usr/bin/env python3
"""
Test to verify calendar events are being returned by the API
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient

async def test_calendar_api():
    print("=" * 80)
    print("TESTING CALENDAR API EVENT RETRIEVAL")
    print("=" * 80)
    
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["email_assistant_db"]
    
    user_id = "1727993d-2348-4d48-bef6-c6637f69703f"
    
    # Simulate what the API does
    events = await db.calendar_events.find({
        "user_id": user_id,
        "$or": [
            {"status": {"$exists": False}},
            {"status": "confirmed"},
            {"status": None}
        ]
    }).sort("start_time", 1).to_list(100)
    
    print(f"\nTotal active events found: {len(events)}")
    print("\n" + "=" * 80)
    
    # Check for potential issues
    issues = []
    
    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event.get('title')}")
        print(f"   Start Time: {event.get('start_time')}")
        print(f"   Status: {event.get('status', 'NO STATUS FIELD')}")
        
        # Check for missing fields
        if 'calendar_provider_id' not in event and 'provider_id' not in event:
            issues.append(f"Event {i}: Missing provider_id field")
            print(f"   ⚠️  Missing: calendar_provider_id/provider_id")
        else:
            provider_id = event.get('calendar_provider_id', event.get('provider_id'))
            print(f"   ✅ Provider ID: {provider_id[:20]}...")
        
        if 'detected_from_email' not in event:
            print(f"   ⚠️  Missing: detected_from_email (will default to False)")
        else:
            print(f"   ✅ Detected from email: {event.get('detected_from_email')}")
        
        if 'attendees' not in event:
            print(f"   ⚠️  Missing: attendees (will default to [])")
        else:
            print(f"   ✅ Attendees: {len(event.get('attendees', []))} people")
        
        print(f"   Event ID (Google): {event.get('event_id')}")
    
    print("\n" + "=" * 80)
    
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ NO ISSUES FOUND - All events have required fields")
    
    print("\n" + "=" * 80)
    print("API RESPONSE SIMULATION")
    print("=" * 80)
    
    # Simulate API response
    try:
        api_events = []
        for e in events:
            api_event = {
                'id': e['id'],
                'calendar_provider_id': e.get('calendar_provider_id', e.get('provider_id', '')),
                'title': e['title'],
                'description': e.get('description'),
                'location': e.get('location'),
                'start_time': e['start_time'],
                'end_time': e['end_time'],
                'attendees': e.get('attendees', []),
                'detected_from_email': e.get('detected_from_email', False),
                'created_at': e['created_at']
            }
            api_events.append(api_event)
        
        print(f"\n✅ API would return {len(api_events)} events successfully")
        
        # Show first 3 events
        print("\nFirst 3 events in API response:")
        for i, event in enumerate(api_events[:3], 1):
            print(f"{i}. {event['title']} - {event['start_time']}")
        
    except Exception as e:
        print(f"\n❌ ERROR building API response: {e}")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_calendar_api())
