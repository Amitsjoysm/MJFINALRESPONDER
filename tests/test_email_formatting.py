"""
Test email formatting to verify plain text and HTML generation
"""
import sys
sys.path.append('/app/backend')

from services.email_formatter import EmailFormatter

# Test draft text
draft_text = """Hi there,

Thank you for reaching out regarding the meeting request.

I've scheduled a meeting for next Tuesday at 2:00 PM UTC. Here are the details:

MEETING DETAILS:
Title: Project Discussion
Date & Time: 2025-11-12T14:00:00 to 2025-11-12T15:00:00 (UTC)
Location: Virtual Meeting
Google Meet Link: https://meet.google.com/abc-defg-hij
View in Calendar: https://calendar.google.com/event?eid=abc123

Please let me know if you have any questions or need to reschedule.

Looking forward to our discussion!"""

# Test signature
signature = """Best regards,
John Doe
Senior Product Manager
Example Company
john.doe@example.com
+1 (555) 123-4567"""

# Generate formatted versions
html_body, plain_body = EmailFormatter.create_html_and_plain(draft_text, signature)

print("="*80)
print("PLAIN TEXT VERSION (PRIMARY):")
print("="*80)
print(plain_body)
print("\n")
print("="*80)
print("HTML VERSION (ALTERNATIVE):")
print("="*80)
print(html_body[:500])  # Show first 500 chars of HTML
print("...")
print("\n")
print("="*80)
print("VERIFICATION:")
print("="*80)
print(f"✓ Plain text length: {len(plain_body)} characters")
print(f"✓ HTML length: {len(html_body)} characters")
print(f"✓ Signature included in plain text: {'Yes' if signature in plain_body else 'No'}")
print(f"✓ Signature included in HTML: {'Yes' if 'john.doe@example.com' in html_body else 'No'}")
newline_check = 'Yes' if '\n\n' in plain_body else 'No'
print(f"✓ Proper paragraph spacing in plain text: {newline_check}")
print(f"✓ Meeting details preserved: {'Yes' if 'MEETING DETAILS' in plain_body else 'No'}")
