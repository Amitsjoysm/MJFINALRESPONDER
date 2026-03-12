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
        
        Args:
            draft_text: Draft text that may contain AI-generated signature
            
        Returns:
            Draft text without AI-generated signature
        """
        if not draft_text:
            return draft_text
        
        # Split into lines
        lines = draft_text.split('\n')
        
        # Find the last substantial content line
        # Look for signature patterns from the end
        signature_start_idx = len(lines)
        
        # Scan from the end to find signature markers
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip().lower()
            
            # Check for common closing phrases
            if any(phrase in line for phrase in [
                'best regards', 'sincerely', 'regards', 'cheers',
                'thank you', 'thanks', 'warm regards', 'kind regards',
                'best wishes', 'yours truly', 'yours sincerely'
            ]):
                signature_start_idx = i
                break
            
            # Check for separator lines
            if re.match(r'^[-_=]{2,}$', line):
                signature_start_idx = i
                break
            
            # If we find substantial content, stop looking
            if len(line) > 50 and not line.endswith(':'):
                break
        
        # Keep only content before signature
        if signature_start_idx < len(lines):
            # Also remove any trailing empty lines before the signature
            while signature_start_idx > 0 and not lines[signature_start_idx - 1].strip():
                signature_start_idx -= 1
            
            cleaned_lines = lines[:signature_start_idx]
            return '\n'.join(cleaned_lines).rstrip()
        
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
