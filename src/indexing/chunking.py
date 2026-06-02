import re
import hashlib
from typing import List

class Chunk:
    def __init__(self, text: str, start_line: int, end_line: int, hash_val: str):
        self.text = text
        self.start_line = start_line
        self.end_line = end_line
        self.hash = hash_val

def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def chunk_text(text: str, max_tokens: int = 256, overlap: int = 32) -> List[Chunk]:
    """
    Splits text into chunks by sentence boundaries roughly targeting max_tokens.
    Uses a very simple token heuristic: 1 word ~ 1.3 tokens.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    start_line = 1
    
    # Very basic line tracking
    lines = text.split('\n')
    line_offsets = []
    cur_len = 0
    for l in lines:
        line_offsets.append(cur_len)
        cur_len += len(l) + 1
        
    def get_line_number(char_idx: int) -> int:
        for i, offset in enumerate(line_offsets):
            if char_idx < offset:
                return max(1, i)
        return len(lines)
        
    char_cursor = 0
    
    for sentence in sentences:
        # Estimate tokens
        tokens = len(sentence.split()) * 1.3
        
        if current_tokens + tokens > max_tokens and current_chunk:
            chunk_text_str = " ".join(current_chunk)
            chunk_hash = compute_sha256(chunk_text_str)
            end_line = get_line_number(char_cursor)
            chunks.append(Chunk(chunk_text_str, start_line, end_line, chunk_hash))
            
            # Keep overlap sentences
            overlap_target = overlap
            overlap_sentences = []
            overlap_tokens = 0
            for s in reversed(current_chunk):
                s_toks = len(s.split()) * 1.3
                if overlap_tokens + s_toks > overlap_target:
                    break
                overlap_sentences.insert(0, s)
                overlap_tokens += s_toks
                
            current_chunk = overlap_sentences
            current_tokens = overlap_tokens
            start_line = get_line_number(max(0, char_cursor - len(" ".join(current_chunk))))
            
        current_chunk.append(sentence)
        current_tokens += tokens
        char_cursor += len(sentence) + 1 # +1 for space
        
    if current_chunk:
        chunk_text_str = " ".join(current_chunk)
        chunk_hash = compute_sha256(chunk_text_str)
        end_line = get_line_number(char_cursor)
        chunks.append(Chunk(chunk_text_str, start_line, end_line, chunk_hash))
        
    return chunks
