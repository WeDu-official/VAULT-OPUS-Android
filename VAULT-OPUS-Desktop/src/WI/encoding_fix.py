#---------------------------------------------------------------------
#encoding_fix.py (in WI) (Phanuel II) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#I HAD MADE THIS PROJECT FOR FREE FOR ALL
#from mankind to mankind... if I disappear don't worry it might just be my exams or anything else, but regardless
#this code will still be here so DO GOOD NO EVIL....good luck :)
#---------------------------------------------------------------------
#[]=================START OF ACTUAL CODE========================[]
import sys
import io

_ALREADY_FIXED = False

def apply():
    global _ALREADY_FIXED
    if _ALREADY_FIXED:
        return
    _ALREADY_FIXED = True
    
    for name in ('stdout', 'stderr'):
        stream = getattr(sys, name)
        if getattr(stream, 'encoding', None) == 'utf-8':
            continue
        if not hasattr(stream, 'buffer'):
            continue
        # CRITICAL: check if buffer is already a TextIOWrapper
        if isinstance(stream, io.TextIOWrapper):
            continue  # Already wrapped, don't double-wrap
        try:
            new_stream = io.TextIOWrapper(
                stream.buffer,
                encoding='utf-8',
                errors='replace'
            )
            setattr(sys, name, new_stream)
        except Exception:
            pass