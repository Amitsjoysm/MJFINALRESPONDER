#!/usr/bin/env python3
"""
Test script for contact features:
1. Test download CSV template
2. Test bulk contact upload
"""
import requests
import json
import io
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8001/api"
TEST_USER = {
    "email": "amits.joys@gmail.com",
    "password": "ij@123"
}

def get_auth_token():
    """Login and get JWT token"""
    print("\n🔐 Logging in...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=TEST_USER
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return None
    
    token = response.json()['access_token']
    print(f"✅ Login successful")
    return token

def test_download_template(token):
    """Test downloading CSV template"""
    print("\n📥 Testing CSV template download...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/campaign/contacts/template/download",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Download failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"✅ Template downloaded successfully")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
    print("\nTemplate content:")
    print("-" * 60)
    print(response.text)
    print("-" * 60)
    
    # Save template for testing upload
    with open('/tmp/test_template.csv', 'w') as f:
        f.write(response.text)
    print("✅ Template saved to /tmp/test_template.csv")
    
    return True

def test_bulk_upload(token):
    """Test bulk contact upload"""
    print("\n📤 Testing bulk contact upload...")
    
    # Create test CSV content
    csv_content = """Email,First Name,Last Name,Company,Title,LinkedIn URL,Company Domain
testuser1@example.com,Test,User1,TestCorp,Engineer,https://linkedin.com/in/testuser1,testcorp.com
testuser2@example.com,Test,User2,TestCorp,Manager,https://linkedin.com/in/testuser2,testcorp.com
testuser3@example.com,Test,User3,AnotherCorp,Developer,https://linkedin.com/in/testuser3,anothercorp.com"""
    
    # Create file-like object
    files = {
        'file': ('test_contacts.csv', io.BytesIO(csv_content.encode('utf-8')), 'text/csv')
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/campaign/contacts/bulk-upload",
        files=files,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Bulk upload failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    result = response.json()
    print(f"✅ Bulk upload successful!")
    print(f"   - Created: {result.get('created', 0)} contacts")
    print(f"   - Updated: {result.get('updated', 0)} contacts")
    print(f"   - Errors: {len(result.get('errors', []))} errors")
    
    if result.get('errors'):
        print("\nErrors:")
        for error in result['errors'][:5]:  # Show first 5 errors
            print(f"   - {error}")
    
    return True

def verify_contacts(token):
    """Verify contacts were created"""
    print("\n🔍 Verifying contacts...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/campaign/contacts",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch contacts: {response.status_code}")
        return False
    
    contacts = response.json()
    print(f"✅ Total contacts in database: {len(contacts)}")
    
    # Show some contacts
    print("\nSample contacts:")
    for contact in contacts[:5]:
        print(f"   - {contact['email']} ({contact.get('first_name', '')} {contact.get('last_name', '')})")
    
    return True

def verify_lists(token):
    """Verify contact lists"""
    print("\n📋 Verifying contact lists...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/campaign/lists",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch lists: {response.status_code}")
        return False
    
    lists = response.json()
    print(f"✅ Total lists: {len(lists)}")
    
    # Show lists
    for lst in lists:
        print(f"   - {lst['name']}: {lst['total_contacts']} contacts")
    
    # Check if 'rapid' list exists
    rapid_list = next((l for l in lists if l['name'] == 'rapid'), None)
    if rapid_list:
        print(f"\n✅ 'rapid' list found with {rapid_list['total_contacts']} contacts")
        print(f"   Contact IDs: {rapid_list['contact_ids'][:3]}...")
    else:
        print("\n⚠️ 'rapid' list not found")
    
    return True

def verify_templates(token):
    """Verify email templates"""
    print("\n📝 Verifying email templates...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/campaign/templates",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch templates: {response.status_code}")
        return False
    
    templates = response.json()
    print(f"✅ Total templates: {len(templates)}")
    
    # Show templates
    for template in templates:
        print(f"   - {template['name']} ({template['template_type']})")
    
    return True

def main():
    """Run all tests"""
    print("="*60)
    print("CONTACT FEATURES TEST")
    print("="*60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Failed to authenticate. Exiting.")
        return
    
    # Test download template
    download_success = test_download_template(token)
    
    # Test bulk upload
    upload_success = test_bulk_upload(token)
    
    # Verify data
    verify_contacts(token)
    verify_lists(token)
    verify_templates(token)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Download Template: {'PASSED' if download_success else 'FAILED'}")
    print(f"✅ Bulk Upload: {'PASSED' if upload_success else 'FAILED'}")
    print("="*60)

if __name__ == "__main__":
    main()
