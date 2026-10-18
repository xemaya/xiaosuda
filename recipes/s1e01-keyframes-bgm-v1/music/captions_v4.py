"""Episode V4 caption profile; no shared renderer or frozen recipe modification."""
import math,re
from functools import lru_cache
from workbench import finishing as base
EN_SIZE=46
ZH_SIZE=42
WIDTH=620
ORIGINAL_HEADER=base.caption_header

def balanced_wrap(value,size):
 font=base.caption_font(size);result=[]
 for paragraph in str(value).splitlines() or ['']:
  english=bool(re.search(r'[A-Za-z]',paragraph) and ' ' in paragraph)
  tokens=paragraph.split() if english else list(paragraph)
  sep=' ' if english else ''
  if not tokens:continue
  measure=lambda i,j:font.getlength(sep.join(tokens[i:j]))
  @lru_cache(None)
  def solve(i,rows):
   if rows==0:return (0,()) if i==len(tokens) else (math.inf,())
   best=(math.inf,())
   for j in range(i+1,len(tokens)+1):
    width=measure(i,j)
    if width>WIDTH:break
    if j<len(tokens) and tokens[j] in '，。！？、；：,.!?;:':continue
    cost,tail=solve(j,rows-1)
    line=sep.join(tokens[i:j]);penalty=(WIDTH-width)**2
    if j<len(tokens) and line[-1] not in ',.!?;:，。！？；：':penalty+=100000
    if j<len(tokens) and english and tokens[j].lower() in ['a','an','the','is','my']:penalty+=200
    candidate=(cost+penalty,(line,)+tail)
    if candidate[0]<best[0]:best=candidate
   return best
  for rows in range(1,len(tokens)+1):
   cost,lines=solve(0,rows)
   if math.isfinite(cost):result.extend(lines);break
  else:raise ValueError('Caption token exceeds safe width')
 return result

def caption_header():
 return ORIGINAL_HEADER().replace('Alibaba PuHuiTi,38,','Alibaba PuHuiTi,46,')

def caption_content(line):
 english_lines={"d6":["And this is my","big sister, Angela.","She's a gentle sheep."],"d7":["We live together happily","and love each other","very much."]}.get(line.get('id'),balanced_wrap(line['text'],EN_SIZE))
 english='\\N'.join(base.ass_text(x) for x in english_lines)
 chinese='\\N'.join(base.ass_text(x) for x in balanced_wrap(line.get('translation',''),ZH_SIZE))
 return english+('\\N{\\fs42}'+chinese if chinese else '')

def install():
 base.caption_header=caption_header;base.caption_content=caption_content
