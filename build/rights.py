"""Who owns each anthem's melody, and the licence of this site's arrangement of it.

A melody in the public domain: the arrangement is CC BY-SA 4.0.
A melody still in copyright (the composer died less than 70 years ago, or a state or body holds the rights): the
melody belongs to its owner and is used as they permit; the arrangement asks only for attribution (CC BY 4.0).

Rows: slug -> (status, holder, year the tune dates from). status 'pd' or 'copyright'. holder is None where the
owner is not documented; the page then says "its rights holders in <country>". Review a row before changing it:
the pages and the JSON-LD licence follow it.
"""

PD, CR = 'pd', 'copyright'

BY_SA = ('CC BY-SA 4.0', 'https://creativecommons.org/licenses/by-sa/4.0/')
BY = ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/')

RIGHTS = {
    'argentina-anthem': (PD, None, 1813),
    'asean-anthem': (CR, 'the ASEAN Secretariat', 2008),
    'australia-anthem': (PD, None, 1878),
    'bahrain-anthem': (CR, None, 1971),
    'belgium-anthem': (PD, None, 1830),
    'brazil-anthem': (PD, None, 1831),
    'brunei-anthem': (CR, None, 1947),
    'cambodia-anthem': (PD, None, 1941),
    'canada-anthem': (PD, None, 1880),
    'china-anthem': (PD, None, 1935),
    'colombia-anthem': (PD, None, 1887),
    'denmark-anthem': (PD, None, 1835),
    'european-union-anthem': (PD, None, 1824),
    'finland-anthem': (PD, None, 1848),
    'france-anthem': (PD, None, 1792),
    'germany-anthem': (PD, None, 1797),
    'greece-anthem': (PD, None, 1828),
    'india-anthem': (PD, None, 1911),
    'indonesia-anthem': (PD, None, 1928),
    'iran-anthem': (CR, None, 1990),
    'iraq-anthem': (CR, None, 1934),
    'ireland-anthem': (PD, None, 1910),
    'israel-anthem': (PD, None, 1888),
    'italy-anthem': (PD, None, 1847),
    'japan-anthem': (PD, None, 1880),
    'laos-anthem': (CR, None, 1941),
    'malaysia-anthem': (PD, None, None),
    'mexico-anthem': (PD, None, 1854),
    'mongolia-anthem': (CR, None, 1950),
    'myanmar-anthem': (CR, None, 1930),
    'netherlands-anthem': (PD, None, 1568),
    'new-zealand-anthem': (PD, None, 1876),
    'north-korea-anthem': (CR, None, 1947),
    'norway-anthem': (PD, None, 1864),
    'peru-anthem': (PD, None, 1821),
    'philippines-anthem': (PD, None, 1898),
    'poland-anthem': (PD, None, 1797),
    'portugal-anthem': (PD, None, 1890),
    'qatar-anthem': (CR, None, 1996),
    'romania-anthem': (PD, None, 1848),
    'russia-anthem': (PD, None, 1939),
    'saudi-arabia-anthem': (CR, None, 1947),
    'singapore-anthem': (CR, "Zubir Said's family", 1958),
    'south-africa-anthem': (CR, 'the Government of South Africa', 1897),
    'south-korea-anthem': (CR, 'the Government of the Republic of Korea (given by Ahn Eak-tai\'s family in 2005)', 1935),
    'south-sudan-anthem': (CR, 'the Government of South Sudan', 2011),
    'spain-anthem': (PD, None, 1761),
    'sweden-anthem': (PD, None, 1844),
    'switzerland-anthem': (PD, None, 1841),
    'taiwan-anthem': (CR, None, 1928),
    'thailand-anthem': (CR, None, 1932),
    'turkiye-anthem': (CR, None, 1930),
    'uae-anthem': (CR, None, 1971),
    'ukraine-anthem': (PD, None, 1863),
    'united-kingdom-anthem': (PD, None, 1744),
    'united-states-anthem': (PD, None, 1773),
    'vatican-anthem': (PD, None, 1869),
    'venezuela-anthem': (PD, None, 1810),
    'vietnam-anthem': (CR, 'the State of Vietnam (given by Văn Cao\'s family in 2016)', 1944),
}


def rights(slug: str) -> tuple[str, str | None, int | None]:
    return RIGHTS[slug]


def licence(slug: str) -> tuple[str, str]:
    """(name, url) of the arrangement's licence."""
    return BY_SA if RIGHTS[slug][0] == PD else BY


# ------------------------------------------------------------------------------------------------ credit lines
# The names in an attribution, where anthems.py's music / words text (years, notes, phrases) does not read as one.
COMPOSER = {
    'israel-anthem': 'Samuel Cohen, after the folk song "Carul cu boi"',
    'south-sudan-anthem': 'students and faculty of the University of Juba',
    'bahrain-anthem': 'an uncredited composer',
    'cambodia-anthem': 'F. Perruchot and J. Jekyll, after a Khmer folk melody',
    'european-union-anthem': 'Ludwig van Beethoven',
    'japan-anthem': 'Hayashi Hiromori, harmonised by Franz Eckert',
    'malaysia-anthem': 'an uncredited composer (the melody of the Perak state anthem)',
    'netherlands-anthem': 'an anonymous composer (a French melody of 1568)',
    'poland-anthem': 'an anonymous composer (a Polish folk mazurka)',
    'south-africa-anthem': 'Enoch Sontonga and Marthinus Lourens de Villiers',
    'spain-anthem': 'an unknown composer',
    'sweden-anthem': 'an anonymous composer (a folk melody from Västmanland)',
    'united-kingdom-anthem': 'an unknown composer',
    'united-states-anthem': 'John Stafford Smith',
    'venezuela-anthem': 'Juan José Landaeta (attributed)',
}
LYRICIST = {   # '' = no lyricist to name
    'south-sudan-anthem': '',
    'australia-anthem': 'Peter Dodds McCormick',
    'belgium-anthem': 'Jenneval and Charles Rogier',
    'european-union-anthem': '',
    'ireland-anthem': 'Peadar Kearney and Liam Ó Rinn',
    'mongolia-anthem': 'Tsendiin Damdinsüren',
    'netherlands-anthem': '',
    'philippines-anthem': 'José Palma',
    'south-africa-anthem': 'Enoch Sontonga, Samuel Mqhayi, C. J. Langenhoven and others',
    'vatican-anthem': 'Raffaello Lavagna and Antonio Allegra',
}


def _names(text: str) -> str:
    """'Calixa Lavallée (1880)' -> 'Calixa Lavallée'; parentheses that hold a year go, others stay."""
    import re
    t = re.sub(r'\s*\([^()]*\d[^()]*\)', '', text or '').strip()
    parts = [p.strip() for p in t.split(';') if p.strip()]
    return ' and '.join(parts) if len(parts) <= 2 else ', '.join(parts[:-1]) + ' and ' + parts[-1]


def composer(slug: str, music: str) -> str:
    return COMPOSER.get(slug) or _names(music)


def lyricist(slug: str, words: str, language: str) -> str:
    """The lyricist to credit, '' for an instrumental anthem or words with no author to name."""
    if slug in LYRICIST:
        return LYRICIST[slug]
    if not words or 'instrumental' in (language or '').lower():
        return ''
    n = _names(words)
    return '' if not n or n[0].islower() else n
