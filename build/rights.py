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
    'iran-anthem': (CR, None, 1990),
    'ireland-anthem': (PD, None, 1910),
    'italy-anthem': (PD, None, 1847),
    'japan-anthem': (PD, None, 1880),
    'laos-anthem': (CR, None, 1941),
    'malaysia-anthem': (PD, None, None),
    'mexico-anthem': (PD, None, 1854),
    'mongolia-anthem': (CR, None, 1950),
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
    'saudi-arabia-anthem': (CR, None, 1947),
    'singapore-anthem': (CR, "Zubir Said's family", 1958),
    'south-africa-anthem': (CR, 'the Government of South Africa', 1897),
    'south-korea-anthem': (CR, 'the Government of the Republic of Korea (given by Ahn Eak-tai\'s family in 2005)', 1935),
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
