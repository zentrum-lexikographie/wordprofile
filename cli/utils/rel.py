from tabulate import tabulate
from termcolor import colored


def get_relation(wp, args):
    mapping = wp.get_lemma_and_pos({
        "Word": args.lemma,
        "Subcorpus": args.corpus,
        "UseVariations": args.variations
    })
    if len(mapping) == 0:
        print("): Wort nicht enthalten")
        return
    if len(mapping) == 1:
        selection = mapping[0]
        print("({}) {} [{}]".format(
            colored("1", "green"),
            selection["Lemma"],
            selection["POS"]
        ))
    else:
        print(colored("Grundform Wählen:", "green"))
        while True:
            for iCounter, i in enumerate(mapping):
                print("({}) {} [{}]".format(
                    colored(iCounter, "green"),
                    colored(i["Lemma"], "yellow"),
                    colored(i["POS"], "cyan")
                ))
            index_select = int(input(">"))
            if 0 <= index_select < len(mapping):
                selection = mapping[index_select]
                break

    print("{}: {}".format(colored("Anzahl an Relationen mit Doppelten", "green"), selection["Frequency"]))
    print("{}: {}".format(colored("mögliche Relationen", "green"), selection["Relations"]))

    relations = wp.get_relations({
        "Lemma": selection["Lemma"],
        "LemmaId": selection.get("LemmaId", ""),
        "POS": selection["POS"],
        "PosId": selection.get("PosId", ""),
        "Start": args.start,
        "Number": args.number,
        "OrderBy": args.order,
        "MinFreq": args.min_freq,
        "MinStat": args.min_stat,
        "Subcorpus": args.corpus,
        "Relations": args.relations or selection["Relations"],
    })

    for rel_ctr, relation in enumerate(relations):
        print()
        if 'RelId' in relation:
            print(colored("{}. {}({}): {}".format(rel_ctr,
                                                  relation['Relation'],
                                                  relation['RelId'],
                                                  relation['Description']),
                          "green"))
        else:
            print(colored("{}. {}: {}".format(rel_ctr,
                                              relation['Relation'],
                                              relation['Description']),
                          "green"))

        table_items = []

        for coocc_ctr, coocc in enumerate(relation['Tuples']):
            table_items.append([
                str(coocc_ctr + 1), coocc['POS'], coocc["Lemma"], coocc['Score']['Frequency'],
                coocc['Score'][args.order], coocc['ConcordId']
            ])
        headers = ['Rank', 'POS', "Lemma", 'Frequency', args.order, 'Hit/MWE-ID']
        print(tabulate(table_items, headers=headers, tablefmt='fancy_grid'))
