"""Empaqueta el frontend compilado en un HTML completo servido junto a la API."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'frontend'/'dist'
index=(DIST/'vite-src'/'index.html').read_text(encoding='utf-8')
scripts=list((DIST/'assets').glob('*.js'))
if len(scripts)!=1:
    raise SystemExit('El build debe contener un único bundle JavaScript antes de empaquetar.')
js=scripts[0].read_text(encoding='utf-8').replace('</script','<\\/script')
index=re.sub(r'<script\b[^>]*type="module"[^>]*>.*?</script>',lambda _: '<script type="module">'+js+'</script>',index,flags=re.S)
def inline_css(match):
    path=DIST/match.group(1).lstrip('/')
    return '<style>'+path.read_text(encoding='utf-8')+'</style>'
index=re.sub(r'<link\b[^>]*rel="stylesheet"[^>]*href="(/assets/[^"]+)"[^>]*>',inline_css,index)
target=ROOT/'frontend'/'monda-dashboard.html'
target.write_text(index,encoding='utf-8')
assert '/assets/' not in re.sub(r'<script.*?</script>','',index,flags=re.S)
print(f'HTML completo: {target.name} ({target.stat().st_size:,} bytes).')
