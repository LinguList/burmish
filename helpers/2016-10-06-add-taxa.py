from pyburmish import *
from lingpy import *
from collections import defaultdict
from lingpy.sequence.sound_classes import syllabify
from lingpy.settings import rcParams

db = load_burmish()
concepts = load_concepts('stdb')
burmish_concepts = [c for c in concepts if c not in db.concepts]

_sounds = load_csv(
        'gorleben',
        '2016-10-06',
        'Burmese_ sounds in 8 languages - Sheet1.tsv'
        )
sheet1 = load_csv(
        'gorleben',
        '2016-10-06',
        'Missing concepts Burmese and Old Burmese - Sheet1.tsv'
        )
sheet2 = load_csv(
        'gorleben',
        '2016-10-06',
        'Missing concepts Burmese and Old Burmese - Sheet2.tsv'
        )

# make converter for sounds
sounds = {}
for row in _sounds:
    sounds[row[0].strip(), row[4].strip()] = row[1].strip().replace(' ', '')
    sounds[rc('morpheme_separator'), row[4].strip()] = '+'
    if row[1] =='?':
        sounds[row[0], row[4]] = '†'+row[0].strip()

for k in db:
    taxon, alignments, tokens = db[k, 'doculect'], db[k, 'alignment'], db[k, 'tokens']
    alm = []
    if not alignments:
        alignments = tokens
        
    for token in alignments.split(' '):
        alm += [sounds.get((token, taxon), '†'+token if token not in '()-' else
            token)]
    db[k][db.header['alignment']] = ' '.join(alm)
    db[k][db.header['tokens']] = ' '.join([x for x in alm if x not in '()-'])

for k in db:
    if db[k, 'language'] in ['Old_Burmese', 'Burmese']:
        db.blacklist += [k]
D = {}
idx = 1
for line in sheet1[1:]:
    concept = line[1]
    if concept not in concepts:
        concept = concept[:-2]
    taxon = line[2]
    tokens = line[3]
    if not tokens.strip():
        pass
    else:
        alm = []
        for t in tokens.split(' '):
            alm += [sounds.get((t, taxon), '†'+t if t not in '()-'
                    else t)]
        D[idx] = [taxon, concept, tokens.replace(' ', ''), alm, alm]
        idx += 1
D[0] = ['doculect', 'concept', 'ipa', 'tokens', 'alignment']
wl = Wordlist(D)
db.add_data(wl)

D = {}
idx = 1
new_concepts = {}
D[0] = ['doculect', 'concept', 'ipa', 'tokens', 'alignment', 'note']
for line in sheet2[1:]:
    concept = line[1].strip()
    cid = line[0].strip()
    tbl = line[2].strip()
    new_concepts[tbl] = concept, cid
    if line[5].strip():
        alm = []
        for t in line[5].split(' '):
            alm += [sounds.get((t, 'Burmese'), '†'+t if t not in '()-'
                else t)]
        D[idx] = ['Burmese', concept, line[5].replace(' ',''), 
                ' '.join([x for x in alm if x not in '()-']), ' '.join(alm), line[7]]
        idx += 1
    if line[6].strip():
        alm = []
        for t in line[6].split(' '):
            alm += [sounds.get((t, 'Old_Burmese'), '†'+t if t not in '()-'
                else t)]
        D[idx] = ['Old_Burmese', concept, line[6].replace(' ',''), 
                ' '.join([x for x in alm if x != '-']), ' '.join(alm), line[7]]
        idx += 1
db.add_data(Wordlist(D))

# load tbl 
tbl = load_csv('sources', 'TBL.csv')
doculects = {
        'Achang (Longchuan)' : 'Achang_Longchuan', 
        'Atsi [Zaiwa]' : 'Atsi',
        'Bola (Luxi)' : 'Bola',
        'Leqi (Luxi)' : 'Lashi',
        'Burmese (Written)' : 'Written_Burmese',
        'Burmese (Rangoon)' : 'Rangoon',
        'Achang (Xiandao)' : 'Xiandao',
        'Langsu (Luxi)' : 'Maru'
        }
D = {}
idx = 1
for line in tbl[1:]:
    ridx, reflex, gloss = line[:3]
    if line[-1].strip():
        tbl = str(int(line[-1].split('.')[0]))
        lang = line[6].strip()
        if lang in doculects and tbl in new_concepts:
            doc = doculects[lang]
            tokens = syllabify(ipa2tokens(reflex.replace(' ', '_'), 
                    merge_vowels=False, expand_nasals=True,
                    semi_diacritics='shɕʑʃʒʐʂ'))
            ipa = ''.join(tokens)
            alm = []
            for t in tokens:
                alm += [sounds.get((t, doc), '†'+t if t in '()_' else t)]
            alm = ' '.join(alm)
            tokens = ' '.join(tokens)
            concept = new_concepts[tbl][0]
            if reflex.strip() == '*':
                pass
            else:
                D[idx] = [ridx,
                        reflex,
                        gloss,
                        ipa,
                        alm,
                        alm,
                        concept,
                        lang,
                        doc,
                        line[-1]]
                idx += 1

D[0] = ['stedt_rn', 'stedt_reflex', 'stedt_gloss', 'ipa', 'tokens', 
        'alignment', 'concept', 'original_taxname', 'doculect', 'stedt_srcid']
db.add_data(Wordlist(D))

for k, (a, b) in new_concepts.items():
    concepts[a] = dict(
            TBL_ID = k,
            CONCEPTICON_ID = b)
with open(burmish_path('concepts', 'burmish-concepts-new.csv'), 'w') as f:
    f.write('NUMBER\tGLOSS\tTBL_ID\tCONCEPTICON_ID\n')
    for i, c in enumerate(sorted(concepts)):
        f.write('\t'.join([str(i+1),
            c, 
            concepts[c]['TBL_ID'],
            concepts[c]['CONCEPTICON_ID']])+'\n')
for k in db:
    if db[k, 'concept'] not in concepts:
        db.blacklist += [k]
    if db[k, 'doculect'] == 'Hpun':
        db.blacklist += [k]
print(len(db.blacklist))
db.add_entries('concepticon_id', 'concept', lambda x:
        concepts.get(x, {}).get('CONCEPTICON_ID', ''))
#db.update('burmish')
#
db.create('burmish', ignore=['concept_id'])

        
