
"""
Script to remove comments from common file types in the workspace.
It makes a backup copy of each modified file under `.comment_backups/<timestamp>/...`.

Handles safely:
- Python: removes `#` comments using the `tokenize` module (preserves docstrings).
- HTML: removes `<!-- -->`, Django `{# #}` and `{% comment %}...{% endcomment %}` blocks.
- JS/CSS: removes `/* ... */` and `// ...` comments (best-effort; may not catch edge cases inside strings).

Run from the repository root.
"""

import os 
import re 
import sys 
import shutil 
import time 
from pathlib import Path 
import io 
import tokenize 

ROOT =Path (__file__ ).resolve ().parents [1 ]
BACKUP_ROOT =ROOT /".comment_backups"/time .strftime ("%Y%m%d_%H%M%S")
EXTS ={
".py",
".html",
".htm",
".js",
".css",
}

def ensure_backup_path (p :Path ):
    dest =BACKUP_ROOT /p .relative_to (ROOT )
    dest .parent .mkdir (parents =True ,exist_ok =True )
    shutil .copy2 (p ,dest )

def remove_comments_python (src :str )->str :
    try :
        tokens =[]
        gen =tokenize .generate_tokens (io .StringIO (src ).readline )
        for tok in gen :
            if tok .type ==tokenize .COMMENT :
                continue 
            tokens .append ((tok .type ,tok .string ))
        return tokenize .untokenize (tokens )
    except Exception :

        lines =[]
        for line in src .splitlines ():

            if line .strip ().startswith ('#'):
                continue 
            parts =line .split ('#')
            if len (parts )>1 :

                lines .append (parts [0 ].rstrip ())
            else :
                lines .append (line )
        return "\n".join (lines )

def remove_comments_js_css (src :str )->str :

    src =re .sub (r"/\*.*?\*/","",src ,flags =re .DOTALL )

    src =re .sub (r"(?<!:)//.*?$","",src ,flags =re .MULTILINE )
    return src 

def remove_comments_html (src :str )->str :
    src =re .sub (r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}","",src ,flags =re .DOTALL )
    src =re .sub (r"\{#.*?#\}","",src ,flags =re .DOTALL )
    src =re .sub (r"<!--.*?-->","",src ,flags =re .DOTALL )

    def _strip_tag_content(m):
        open_tag = m.group(1)
        tag = m.group(2).lower()
        content = m.group(3)
        close_tag = m.group(4)
        if tag in ('style', 'script'):
            new_content = remove_comments_js_css(content)
        else:
            new_content = content
        return f"{open_tag}{new_content}{close_tag}"

    src =re .sub (r"(<(script|style)[^>]*>)(.*?)(</\2>)", _strip_tag_content, src ,flags =re .DOTALL | re .IGNORECASE )
    return src 

def process_file (path :Path )->bool :
    text =path .read_text (encoding ="utf-8")
    original =text 
    ext =path .suffix .lower ()
    if ext ==".py":
        new =remove_comments_python (text )
    elif ext in {".html",".htm"}:
        new =remove_comments_html (text )
    elif ext in {".js",".css"}:
        new =remove_comments_js_css (text )
    else :
        return False 

    new =re .sub (r"\n{3,}","\n\n",new )

    if new !=original :
        ensure_backup_path (path )
        path .write_text (new ,encoding ="utf-8")
        return True 
    return False 

def should_skip (path :Path )->bool :

    parts =set (path .parts )
    if ".git"in parts or ".venv"in parts or "venv"in parts or "env"in parts or ".comment_backups"in parts :
        return True 
    return False 

def main ():
    changed =[]
    BACKUP_ROOT .mkdir (parents =True ,exist_ok =True )
    for root ,dirs ,files in os .walk (ROOT ):

        if any (skip in root for skip in (os .path .join (str (ROOT ),".git"),os .path .join (str (ROOT ),".comment_backups"))):
            continue 
        for f in files :
            p =Path (root )/f 
            if should_skip (p ):
                continue 
            if p .suffix .lower ()in EXTS :
                try :
                    ok =process_file (p )
                    if ok :
                        changed .append (str (p .relative_to (ROOT )))
                except Exception as e :
                    print (f"Error procesando {p }: {e }",file =sys .stderr )

    print ("Modificados:")
    for c in changed :
        print (" -",c )
    print (f"Backups guardadas en: {BACKUP_ROOT }")

if __name__ =='__main__':
    main ()
