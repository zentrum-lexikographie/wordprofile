#!/usr/bin/python
# -*- coding: utf-8 -*-

replacements = {'ß': 'ss', '①': 'ß',
                'F': 'Ph', '②': 'F', 'f': 'ph', '③': 'f',
                't': 'th', 'T': 'Th', '④': 'T', '⑤': 't'}
replacement_endings = {'r@': 'th@', 'é@': 'ee@', 'ée@': 'ee@', 'tial@': 'tiell@', 'zial@': 'ziell@'}


def generate_variants(surface, pos=0):
    if pos >= len(surface):
        return {surface}

    variants = set()
    if surface[pos] in replacements:
        char_new = replacements[surface[pos]]
        surface_new = surface[:pos] + char_new + surface[pos + 1:]
        variants |= generate_variants(surface_new, pos + len(char_new))
    variants |= generate_variants(surface, pos + 1)
    return variants


# TODO seems not working correctly...
# seems to me like randomly changing something to just change something (try 'Schifffahrt' ;)
# there is definitely some potential for improvements
def generate_orth_variations(surface):
    surface_trans = surface.replace('ss', '①').replace('Ph', '②').replace('ph', '③').replace('Th',
                                                                                             '④').replace('th',
                                                                                                          '⑤')
    variations = set()
    for var in generate_variants(surface_trans):
        variations.add(
            var.replace('①', 'ss').replace('②', 'Ph').replace('③', 'ph').replace('④', 'Th').replace('⑤', 'th'))
        for i, j in replacement_endings.items():
            variation = (surface + "@").replace(i, j).replace("@", "")
            variations.add(variation)
    return list(variations - {surface})
