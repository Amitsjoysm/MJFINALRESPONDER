"""
Email formatting service to convert plain text to beautiful HTML emails
"""

import re
from typing import Optional


class EmailFormatter:
    """Format plain text emails into beautiful HTML"""
    
    @staticmethod
    def text_to_html(plain_text: str, signature: Optional[str] = None) -> str:
        """
        Convert plain text email to beautifully formatted HTML
        
        Args:
            plain_text: Plain text email content
            signature: Optional signature to append
            
        Returns:
            HTML formatted email
        """
        # Split into paragraphs
        paragraphs = plain_text.split('\n\n')
        
        html_parts = []
        
        for para in paragraphs:
            if not para.strip():
                continue
            
            para = para.strip()
            
            # Check if it's a heading (ALL CAPS or starts with specific patterns)
            if EmailFormatter._is_heading(para):
                html_parts.append(f'<h2 style="color: #2c3e50; margin-top: 20px; margin-bottom: 10px; font-size: 18px; font-weight: 600;">{EmailFormatter._escape_html(para)}</h2>')
            
            # Check if it's a list
            elif EmailFormatter._is_list_item(para):
                list_items = EmailFormatter._parse_list(para)
                list_html = '<ul style="margin: 10px 0; padding-left: 20px;">'
                for item in list_items:
                    list_html += f'<li style="margin: 5px 0; line-height: 1.6;">{EmailFormatter._escape_html(item)}</li>'
                list_html += '</ul>'
                html_parts.append(list_html)
            
            # Check if it's a separator or divider
            elif re.match(r'^[=━\-]{3,}$', para):
                html_parts.append('<hr style="border: none; border-top: 2px solid #e0e0e0; margin: 20px 0;">')
            
            # Check if it contains meeting details or important info
            elif any(keyword in para.lower() for keyword in ['meeting', 'calendar', 'event', 'scheduled', 'google meet', 'zoom']):
                html_parts.append(EmailFormatter._format_meeting_info(para))
            
            # Check if it contains links
            elif 'http://' in para or 'https://' in para:
                formatted = EmailFormatter._format_links(para)
                html_parts.append(f'<p style="margin: 10px 0; line-height: 1.6; color: #333;">{formatted}</p>')
            
            # Regular paragraph
            else:
                # Handle line breaks within paragraph
                lines = para.split('\n')
                formatted_lines = '<br>'.join([EmailFormatter._escape_html(line) for line in lines if line.strip()])
                html_parts.append(f'<p style="margin: 10px 0; line-height: 1.6; color: #333;">{formatted_lines}</p>')
        
        # Add signature if provided
        if signature:
            html_parts.append('<div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">')
            sig_lines = signature.split('\n')
            sig_html = '<div style="color: #666; font-size: 14px; line-height: 1.6;">'
            for line in sig_lines:
                if line.strip():
                    sig_html += f'{EmailFormatter._escape_html(line)}<br>'
            sig_html += '</div></div>'
            html_parts.append(sig_html)
        
        # Wrap everything in a responsive container that works in all email clients
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <div style="max-width: 100%; padding: 20px; margin: 0; box-sizing: border-box;">
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
            {''.join(html_parts)}
        </div>
    </div>
</body>
</html>
"""
        return html
    
    @staticmethod
    def _is_heading(text: str) -> bool:
        """Check if text should be formatted as a heading"""
        text = text.strip()
        # All caps and short
        if text.isupper() and len(text) < 60:
            return True
        # Starts with heading patterns
        if re.match(r'^(IMPORTANT|NOTE|ATTENTION|REMINDER|MEETING|EVENT|CALENDAR):', text, re.IGNORECASE):
            return True
        return False
    
    @staticmethod
    def _is_list_item(text: str) -> bool:
        """Check if text contains list items"""
        lines = text.split('\n')
        # Check if at least 2 lines start with list markers
        list_markers = sum(1 for line in lines if re.match(r'^\s*[-•*\d+.]\s+', line))
        return list_markers >= 2
    
    @staticmethod
    def _parse_list(text: str) -> list:
        """Parse list items from text"""
        items = []
        for line in text.split('\n'):
            # Remove list markers
            cleaned = re.sub(r'^\s*[-•*\d+.]\s+', '', line).strip()
            if cleaned:
                items.append(cleaned)
        return items
    
    @staticmethod
    def _format_meeting_info(text: str) -> str:
        """Format meeting/event information with special styling"""
        # Detect meeting details
        html = '<div style="background-color: #f8f9fa; border-left: 4px solid #4CAF50; padding: 15px; margin: 15px 0; border-radius: 4px;">'
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Bold important labels
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    label, value = parts
                    # Check for links in value
                    if 'http://' in value or 'https://' in value:
                        value = EmailFormatter._format_links(value)
                    else:
                        value = EmailFormatter._escape_html(value)
                    html += f'<div style="margin: 5px 0;"><strong style="color: #2c3e50;">{EmailFormatter._escape_html(label)}:</strong> {value}</div>'
                else:
                    html += f'<div style="margin: 5px 0;">{EmailFormatter._format_links(line)}</div>'
            else:
                html += f'<div style="margin: 5px 0;">{EmailFormatter._format_links(line)}</div>'
        
        html += '</div>'
        return html
    
    @staticmethod
    def _format_links(text: str) -> str:
        """Convert URLs to clickable links"""
        # Match URLs - exclude trailing punctuation that's not part of the URL
        url_pattern = r'(https?://[^\s<>"]+?)([.,;:!?\)]*(?:\s|$))'
        
        def replace_url(match):
            url = match.group(1)
            trailing = match.group(2)
            
            # Remove trailing periods or commas that are likely sentence punctuation
            # But keep them if they're part of the URL path (like file.html)
            while url.endswith(('.', ',', ';', ':')) and '/' in url:
                # Move trailing punctuation to trailing group
                trailing = url[-1] + trailing
                url = url[:-1]
            
            # Make link more readable
            display_text = url
            if len(display_text) > 60:
                display_text = display_text[:57] + '...'
            return f'<a href="{url}" style="color: #2196F3; text-decoration: none; font-weight: 500;">{EmailFormatter._escape_html(display_text)}</a>{trailing}'
        
        # First escape HTML, then replace URLs
        escaped_text = EmailFormatter._escape_html(text)
        return re.sub(url_pattern, replace_url, escaped_text)
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters"""
        if not isinstance(text, str):
            text = str(text)
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    @staticmethod
    def create_html_and_plain(draft_text: str, signature: Optional[str] = None) -> tuple:
        """
        Create both HTML and plain text versions of an email
        
        Args:
            draft_text: Plain text draft
            signature: Optional signature
            
        Returns:
            Tuple of (html_version, plain_version)
        """
        # Create HTML version
        html_version = EmailFormatter.text_to_html(draft_text, signature)
        
        # Create well-formatted plain text version
        plain_version = EmailFormatter.format_plain_text(draft_text, signature)
        
        return html_version, plain_version
    
    @staticmethod
    def format_plain_text(draft_text: str, signature: Optional[str] = None) -> str:
        """
        Format plain text email - NO LINE WRAPPING
        Let email client handle natural text flow for proper display
        
        Args:
            draft_text: Plain text draft
            signature: Optional signature
            
        Returns:
            Plain text email with paragraph breaks, no forced line wrapping
        """
        # Simply preserve paragraphs, no wrapping
        lines = draft_text.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            # Keep the line as-is, just trim excessive whitespace
            formatted_lines.append(line.rstrip())
        
        # Join all lines
        plain_version = '\n'.join(formatted_lines)
        
        # Clean up excessive blank lines (more than 2 consecutive)
        import re
        plain_version = re.sub(r'\n{3,}', '\n\n', plain_version)
        
        # Add signature if provided
        if signature:
            plain_version = plain_version.rstrip()
            plain_version += f"\n\n{signature.strip()}"
        
        return plain_version.strip()
    
    @staticmethod
    def _is_plain_text_heading(text: str) -> bool:
        """Check if text should be treated as a heading in plain text"""
        # All caps and relatively short
        if text.isupper() and len(text) < 60 and len(text) > 3:
            return True
        # Starts with heading keywords
        if re.match(r'^(IMPORTANT|NOTE|ATTENTION|REMINDER|MEETING|EVENT|CALENDAR|DETAILS):', text, re.IGNORECASE):
            return True
        return False
    
    @staticmethod
    def _is_plain_text_list_item(text: str) -> bool:
        """Check if text is a list item in plain text"""
        # Starts with common list markers
        return bool(re.match(r'^\s*[-•*]\s+', text) or re.match(r'^\s*\d+[\.\)]\s+', text))


# Convenience function
def format_email_html(plain_text: str, signature: Optional[str] = None) -> str:
    """Quick function to format email as HTML"""
    return EmailFormatter.text_to_html(plain_text, signature)
