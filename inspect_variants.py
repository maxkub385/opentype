import sys
from collections import defaultdict

from ttxread import read_ttx
from ttxfont import SingleSubstitution1, ChainSubstitution3

# Usage: python inspect_variants.py [ttx_path]
# Default TTX path: eot.ttx

def main():
    ttx_path = sys.argv[1] if len(sys.argv) > 1 else 'eot.ttx'
    font = read_ttx(ttx_path)

    # Map lookup index -> list of single-subst rules (input, output)
    single_rules = defaultdict(list)
    chain_refs = []  # (lookup_index, lefts, inputs, rights, refs)

    for index, lookup in font.GSUB_lookups.items():
        for sub in getattr(lookup, 'substitutions', []):
            if isinstance(sub, SingleSubstitution1):
                single_rules[index].append((sub.input, sub.output))
            elif isinstance(sub, ChainSubstitution3):
                chain_refs.append((index, sub.lefts, sub.inputs, sub.rights, sub.refs))

    def is_variant(name):
        # Match names like A1_11R, A1_33R, B1_11R, B1_33R, and bare A11R/A33R/D33R
        return (
            ('_11R' in name) or ('_33R' in name) or 
            name.endswith('11R') or name.endswith('33R')
        )
    def is_size_class(name):
        # Match names ending with _11 or _33 but not the R-suffixed ones
        return (
            ('_11' in name and not name.endswith('11R')) or 
            ('_33' in name and not name.endswith('33R'))
        )

    # Collect examples of variants from single substitutions
    variants_11 = []
    variants_33 = []
    sizes_11 = []
    sizes_33 = []
    for idx, rules in single_rules.items():
        for inp, out in rules:
            if is_variant(out):
                if '11R' in out:
                    variants_11.append((idx, inp, out))
                if '33R' in out:
                    variants_33.append((idx, inp, out))
            elif is_size_class(out):
                if '_11' in out:
                    sizes_11.append((idx, inp, out))
                if '_33' in out:
                    sizes_33.append((idx, inp, out))

    print('=== Variant SingleSubstitution summary ===')
    print(f'Total single-subst producing 11R: {len(variants_11)}')
    print(f'Total single-subst producing 33R: {len(variants_33)}')
    print('Examples (up to 10 each):')
    def feature_tag_for_lookup(idx):
        feat = font.GSUB_lookup_index_to_feature.get(str(idx)) or font.GSUB_lookup_index_to_feature.get(idx)
        return getattr(feat, 'tag', None)
    for rec in variants_11[:10]:
        tag = feature_tag_for_lookup(rec[0])
        print(f'  feature {tag} lookup {rec[0]}: {rec[1]} -> {rec[2]}')
    for rec in variants_33[:10]:
        tag = feature_tag_for_lookup(rec[0])
        print(f'  feature {tag} lookup {rec[0]}: {rec[1]} -> {rec[2]}')

    print('\n=== Size-class SingleSubstitution summary (no R) ===')
    print(f'Total single-subst producing _11 (no R): {len(sizes_11)}')
    print(f'Total single-subst producing _33 (no R): {len(sizes_33)}')
    print('Examples (up to 10 each):')
    for rec in sizes_11[:10]:
        tag = feature_tag_for_lookup(rec[0])
        print(f'  feature {tag} lookup {rec[0]}: {rec[1]} -> {rec[2]}')
    for rec in sizes_33[:10]:
        tag = feature_tag_for_lookup(rec[0])
        print(f'  feature {tag} lookup {rec[0]}: {rec[1]} -> {rec[2]}')

    # Analyze ChainSubstitution3 contexts that dispatch to lookups creating variants
    def lookup_produces_variant(lk_idx):
        rules = single_rules.get(str(lk_idx), []) if isinstance(lk_idx, str) else single_rules.get(lk_idx, [])
        return any(is_variant(out) for _, out in rules)

    def flatten_cov(cov):
        # cov is a list of coverages; each coverage is a list of glyph names
        return [g for coverage in cov for g in coverage]

    def has_marker(glyphs):
        return any(g in glyphs for g in ['vj','hj']) or any(g.startswith('ch') for g in glyphs)

    print('\n=== ChainSubstitution3 dispatch summary ===')
    dispatchers = []
    for idx, lefts, inputs, rights, refs in chain_refs:
        target_lookups = [li for (_, li) in refs]
        if any(lookup_produces_variant(li) for li in target_lookups):
            left_g = flatten_cov(lefts)
            in_g = flatten_cov(inputs)
            right_g = flatten_cov(rights)
            dispatchers.append((idx, target_lookups, left_g, in_g, right_g))

    print(f'ChainSubst entries that dispatch to variant-producing lookups: {len(dispatchers)}')
    for idx, targets, left_g, in_g, right_g in dispatchers[:10]:
        markers = []
        if has_marker(left_g): markers.append('left: markers present')
        if has_marker(in_g): markers.append('input: markers present')
        if has_marker(right_g): markers.append('right: markers present')
        print(f'  chain lookup {idx} -> target lookups {targets} | markers: {", ".join(markers) or "none"}')
        # Show small sample of context glyphs
        print(f'    sample left: {left_g[:6]} input: {in_g[:6]} right: {right_g[:6]}')

    print('\n=== Conclusion (heuristic) ===')
    print('- The font uses SingleSubstitution rules to map base signs to 11R/33R variants.')
    print('- Many of these are driven via ChainSubstitution3 that triggers variant lookups based on context.')
    print('- Context coverages often include construction markers (e.g., vj/hj) and ch* tokens.')
    print('- When vertical/hieroglyph stacking context is detected, 33R variants are selected;')
    print('  otherwise, 11R variants are used for default or horizontally constrained contexts.')
    print('\nNote: This script inspects rules only; actual runtime selection depends on GSUB application order.')

if __name__ == '__main__':
    main()
