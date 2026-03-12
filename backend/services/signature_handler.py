"""Service to handle email signatures and prevent duplicates"""

import re
from typing import Optional


class SignatureHandler:
    """Handle email signatures to prevent duplicates"""
    
    # Common signature patterns
    SIGNATURE_PATTERNS = [
        r'\n\s*[-_=]{2,}\s*\n',  # Separator lines
        r'\n\s*Best regards?[,\s]*\n',
        r'\n\s*Sincerely[,\s]*\n',
        r'\n\s*Thanks?[,\s]*\n',
        r'\n\s*Regards?[,\s]*\n',
        r'\n\s*Cheers[,\s]*\n',
        r'\n\s*Warm regards?[,\s]*\n',
        r'\n\s*Kind regards?[,\s]*\n',
        r'\n\s*With (best |warm )?regards?[,\s]*\n',
    ]
    
    @staticmethod
    def remove_ai_signature(draft_text: str) -> str:
        """
        Remove any AI-generated signature from draft text.
        Signatures typically appear at the end with closing phrases.
        Only checks the LAST few lines to avoid stripping body content.
        
        Args:
            draft_text: Draft text that may contain AI-generated signature
            
        Returns:
            Draft text without AI-generated signature
        """
        if not draft_text:
            return draft_text
        
        # Split into lines
        lines = draft_text.split('\n')
        
        # Only check the last 5 lines for signature patterns
        # This avoids stripping body content that happens to contain "thank you" etc.
        signature_start_idx = len(lines)
        check_start = max(0, len(lines) - 5)
        
        # Scan from the end to find signature markers (only last 5 lines)
        for i in range(len(lines) - 1, check_start - 1, -1):
            line = lines[i].strip().lower()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for common closing phrases (standalone lines only)
            closing_phrases = [
                'best regards', 'sincerely', 'warm regards', 'kind regards',
                'best wishes', 'yours truly', 'yours sincerely', 'cheers',
                'with regards', 'with best regards'
            ]
            
            # Only strip if the line is PRIMARILY a closing phrase (not embedded in content)
            is_closing_line = False
            for phrase in closing_phrases:
                if line.startswith(phrase) or line == phrase or line.rstrip(',. ') == phrase:
                    is_closing_line = True
                    break
            
            if is_closing_line:
                signature_start_idx = i
                break
            
            # Check for separator lines
            if re.match(r'^[-_=]{2,}$', line):
                signature_start_idx = i
                break
            
            # Check for standalone "Thanks," or "Thank you," as a sign-off (not body text)
            if line in ['thanks,', 'thanks.', 'thanks!', 'thank you,', 'thank you.', 'thank you!',
                        'thanks', 'thank you', 'many thanks', 'many thanks,', 'many thanks.']:
                signature_start_idx = i
                break
            
            # If we find substantial content, stop looking for signatures
            if len(line) > 30:
                break
        
        # Keep only content before signature
        if signature_start_idx < len(lines):
            # Also remove any trailing empty lines before the signature
            while signature_start_idx > 0 and not lines[signature_start_idx - 1].strip():
                signature_start_idx -= 1
            
            cleaned_lines = lines[:signature_start_idx]
            result = '\n'.join(cleaned_lines).rstrip()
            return result if result else draft_text.rstrip()
        
        return draft_text.rstrip()
    
    @staticmethod
    def detect_signature_in_text(text: str) -> bool:
        """
        Detect if text contains a signature pattern
        
        Args:
            text: Text to check
            
        Returns:
            True if signature pattern detected
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for common signature phrases
        signature_phrases = [
            'best regards', 'sincerely', 'regards', 'cheers',
            'thank you', 'thanks', 'warm regards', 'kind regards',
            'best wishes', 'yours truly', 'yours sincerely'
        ]
        
        for phrase in signature_phrases:
            if phrase in text_lower:
                # Check if it's near the end (last 200 characters)
                if text_lower.rfind(phrase) > len(text_lower) - 200:
                    return True
        
        # Check for separator patterns
        for pattern in SignatureHandler.SIGNATURE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
