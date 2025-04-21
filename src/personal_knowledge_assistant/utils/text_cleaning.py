import re
import glob
import os
from typing import Optional
from loguru import logger

def clean_notion_text(raw: str, min_len: int = 20) -> str:
    """
    Clean Notion text for embedding and vector search while preserving
    important elements like images, links, math, code, and headings.
    
    Args:
        raw: Raw text from Notion
        min_len: Minimum length for lines to keep
        
    Returns:
        Cleaned text
    """
    # Track original length
    original_length = len(raw)
    
    # Make a copy of the raw text
    text = raw
    
    # Preserve images with markdown format
    # Keep original ![alt text](url) format for multimodal RAG
    
    # Format inline links nicely
    # [text](url) → text | url
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 | \2', text)
    
    # Standardize headers to have proper spacing
    text = re.sub(r'(?m)^\s{0,3}(#{1,6})\s*(.+)$', r'\1 \2', text)
    
    # Limit heading depth to 3 levels
    text = re.sub(r'#{4,}', '###', text)
    
    # Standardize code block formatting
    text = re.sub(r'```\s*(\w*)\s*\n', r'```\1\n', text)
    
    # Preserve math blocks
    # Keep original $begin:math:display$ and $end:math:display$
    
    # Remove Notion-specific boilerplate
    text = re.sub(r'Page link:.*', '', text)
    text = re.sub(r'\[Synced block (?:start|end)\]', '', text)
    
    # Normalize whitespace
    text = text.replace('\t', ' ')
    text = re.sub(r'\r\n?', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove emojis and special characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # Filter tiny lines but preserve code blocks and math blocks
    lines = []
    in_code_block = False
    in_math_block = False
    
    for line in text.split('\n'):
        ln = line.strip()
        
        # Toggle code block state
        if ln.startswith('```'):
            in_code_block = not in_code_block
            lines.append(ln)
            continue
            
        # Toggle math block state
        if '$begin:math:display$' in ln:
            in_math_block = True
            lines.append(ln)
            continue
            
        if '$end:math:display$' in ln:
            in_math_block = False
            lines.append(ln)
            continue
        
        # Always keep lines in code blocks or math blocks
        if in_code_block or in_math_block:
            lines.append(line)  # keep original indentation
        # Otherwise apply length filter
        elif len(ln) >= min_len or ln.startswith('#'):  # Always keep headings
            lines.append(ln)
    
    result = '\n'.join(lines)
    
    # Log the reduction
    reduction_pct = 100 - (len(result) / max(original_length, 1)) * 100
    logger.debug(f"Cleaned text: {original_length} chars → {len(result)} chars ({reduction_pct:.1f}% reduction)")
    
    return result

