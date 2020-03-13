import re

from tabulate import tabulate
from termcolor import colored


def color_word_markers(s):
    while True:
        match = re.findall(r"(.*)_&([^&]+)&_(.*)", s)
        if not match:
            break
        s = "{}{}{}".format(match[0][0],
                            colored(match[0][1], "red", attrs=["underline"]),
                            match[0][2])
    while True:
        match = re.findall(r"(.*)&&([^&]+)&&(.*)", s)
        if not match:
            break
        s = "{}{}{}".format(match[0][0],
                            colored(match[0][1], "red", ),
                            match[0][2])
    return s


def get_hits(wp, args):
    relation_info = wp.get_concordances_and_relation({
        "InfoId": args.info,
        "Start": args.start,
        "Number": args.number,
        "Subcorpus": args.corpus,
        "DateDesc": args.dateDesc,
        "UseScore": args.score,
        "UseContext": args.context,
        "InternalUser": args.internal_user
    })

    table_rows = []
    for ctr, i in enumerate(relation_info['Tuples']):
        bibl_corpus = i['Bibl']['Corpus']
        bibl_date = i['Bibl']['Date']
        bibl_text_class = i['Bibl']['TextClass']
        bibl_orig = i['Bibl']['Orig']
        bibl_scan = i['Bibl']['Scan']
        bibl_avail = str(i['Bibl']['Avail'])
        bibl_page = i['Bibl']['Page']
        score = str(i['Score'])

        sentence_center = color_word_markers(i['ConcordLine'])
        sentence_left = " ".join(colored(w, 'blue') for w in i['ConcordLeft'].split()) if i['ConcordLeft'] else ""
        sentence_right = " ".join(colored(w, 'blue') for w in i['ConcordRight'].split()) if i['ConcordRight'] else ""
        context = "{} {} {}".format(sentence_left, sentence_center, sentence_right)
        line_chars = 0
        line = []
        new_context = ""
        for word in context.split(' '):
            if line_chars > 120:
                new_context += " ".join(line) + "\n"
                line = []
                line_chars = 0
            line.append(word)
            line_chars += len(word)
        new_context += " ".join(line)
        context = new_context
        meta_info = "{} | {} | {} | {} | {} | {} | {} | {}".format(
            bibl_corpus, bibl_date, bibl_text_class, bibl_orig, bibl_scan, bibl_avail, bibl_page, score)
        table_rows.append((ctr + 1, colored(meta_info, "green") + "\n" + context))

    print("{}: {}".format(colored("Relation", "green"), relation_info['Relation']))
    print("{}: {}".format(colored("Lemma1", "green"), relation_info['Lemma1']))
    print("{}: {}".format(colored("Lemma2", "green"), relation_info['Lemma2']))
    print("{}: {}".format(colored("Description", "green"), relation_info['Description']))
    print(tabulate(table_rows, tablefmt='grid'))
