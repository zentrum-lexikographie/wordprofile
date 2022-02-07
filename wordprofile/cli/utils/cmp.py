from tabulate import tabulate
from termcolor import colored


def compare_lemmas(wp, args):
    mapping = wp.get_lemma_and_pos_diff({
        "Word1": args.lemma1,
        "Word2": args.lemma2,
    })

    if len(mapping) == 0:
        print("): Wort nicht enthalten")
        return
    if len(mapping) == 1:
        mapSelect = mapping[0]
        print("({}) {}/{} [{}]".format(
            colored("1", "green"),
            colored(mapSelect["LemmaId1"], "yellow"),
            colored(mapSelect["LemmaId2"], "cyan"),
            colored(mapSelect["POS"], "cyan")
        ))
    else:
        print(colored("Grundform Wählen:", "green"))
        while True:
            for iCounter, i in enumerate(mapping):
                print("({}) {}/{} [{}]".format(
                    colored(iCounter, "green"),
                    colored(i["LemmaId1"], "yellow"),
                    colored(i["LemmaId2"], "cyan"),
                    colored(i["POS"], "cyan")
                ))
            index_select = int(input(">"))
            if 0 <= index_select < len(mapping):
                mapSelect = mapping[index_select]
                break

    # Abfrageoptionen für den Wortvergleich erstellen
    params = {
        "LemmaId1": mapSelect["LemmaId1"],
        "LemmaId2": mapSelect["LemmaId2"],
        "POS": mapSelect["POS"],
        "Relations": args.relations or mapSelect["Relations"],
        "Number": args.number,
        "OrderBy": args.order,
        "MinFreq": args.min_freq,
        "MinStat": args.min_stat,
    }
    if args.nbest != -1:
        params["NBest"] = args.nbest
    params["Operation"] = args.operation

    relation_diffs = wp.get_diff(params)

    # Durchgehen der Relationen
    for rel_ctr, relation in enumerate(relation_diffs):
        print()
        print(colored(" {}. {}: {}".format(
            rel_ctr,
            relation['Relation'],
            relation['Description']),
            "green"))

        table_items = []
        for i in relation['Tuples']:
            table_row = [i["Lemma"], i['Form'],
                         i['Score']['AScomp'], i['Score']['Frequency1'], i['Score']['Frequency2'],
                         i['Score']['Rank1'], i['Score']['Rank2'], i['Score']['Assoziation1'],
                         i['Score']['Assoziation2']]
            if i['Position'] == "left":
                table_row = list(map(lambda t: colored(t, "yellow"), table_row))
            elif i['Position'] == "right":
                table_row = list(map(lambda t: colored(t, "cyan"), table_row))
            else:
                table_row = list(map(lambda t: colored(t, "red"), table_row))
            table_items.append(table_row)
        headers = [
            'Lemma', 'Form',
            'Score', 'Frequency1', 'Frequency2', 'Rank1', 'Rank2', 'Association1', 'Association2'
        ]
        print(tabulate(table_items, headers=headers, tablefmt='fancy_grid'))
