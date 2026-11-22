"""Search words in each anthem's own language: "sheet music", the instruments, "full score".

Used only in titles, descriptions, headings and alt text (the pages are English), so that a search such as
"partitura violín Himno Nacional Argentino" finds the violin page. One entry per language; an anthem names its
language in LANG_OF (anthem-orchestra slug -> code). Checked by hand: keep the words a musician would type.
"""
from __future__ import annotations

WORDS = {
    'es': dict(
        sheet='partitura', score='partitura completa', orchestra='orquesta', melody='melodía', anthem='himno',
        pattern='partitura de {inst} {title}',
        inst=dict(violin='violín', viola='viola', cello='violonchelo', **{'double-bass': 'contrabajo'},
                  flute='flauta', piccolo='flautín', oboe='oboe', clarinet='clarinete', bassoon='fagot',
                  horn='trompa', trumpet='trompeta', trombone='trombón', tuba='tuba', timpani='timbales',
                  percussion='percusión', harp='arpa', piano='piano', choir='coro')),
}

LANG_OF = {
    'argentina-anthem': 'es', 'colombia-anthem': 'es', 'mexico-anthem': 'es', 'peru-anthem': 'es',
    'venezuela-anthem': 'es', 'spain-anthem': 'es',
}


def words(slug: str) -> dict | None:
    return WORDS.get(LANG_OF.get(slug, ''))


def native_phrase(slug: str, inst_slug: str | None, title: str) -> str:
    """'partitura de violín Himno Nacional Argentino', or '' when the language has no table yet."""
    w = words(slug)
    if not w:
        return ''
    if inst_slug is None:
        return f"{w['sheet']} {title}"
    if inst_slug == 'full-score':
        return f"{w['score']} {title} {w['orchestra']}"
    if inst_slug == 'melody':
        return w['pattern'].format(inst=w['melody'], title=title)
    return w['pattern'].format(inst=w['inst'][inst_slug], title=title)
