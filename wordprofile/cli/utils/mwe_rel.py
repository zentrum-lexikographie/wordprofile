from tabulate import tabulate
from termcolor import colored


def get_mwe_free(wp, args):
    mappings = []
    for lemma in filter(None, args.LemmaList.split(',')):
        # Lemma-Informationen zu den einzelnen Lemmaformen ermitteln
        # vLemmaList = s.get_lemma_and_pos_by_list(mapParam)
        mapping = wp.get_lemma_and_pos({
            "Word": lemma,
        })
        if len(mapping) == 0:
            print("): Ein Wort nicht enthalten")
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
        mappings.append(selection)

    # print("{}: {}".format(colored("Anzahl an Relationen mit Doppelten", "green"), selection["Frequency"]))
    # print("{}: {}".format(colored("mögliche Relationen", "green"), selection["Relations"]))
    print(mappings)

    relations = wp.get_relations({
        "Lemma": mappings[0]["Lemma"],
        "POS": mappings[0]["POS"],
        "Lemma2": mappings[1]["Lemma"],
        "Pos2Id": mappings[1]["POS"],
        "Start": args.start,
        "Number": args.number,
        "OrderBy": args.order,
        "MinFreq": args.min_freq,
        "MinStat": args.min_stat,
        "Relations": ["META"],
    })

    # TODO currently uses a hack which makes concordId positive
    collocation_ids = [abs(int(colloc['ConcordId'])) for relation_type in relations for colloc in
                       relation_type['Tuples']]
    for collocation_id in collocation_ids:
        print("MWE relations for collocation id:", collocation_id)
        mwe_parts_relations = wp.get_mwe_relations({
            "ConcordId": collocation_id,
            "Start": args.start,
            "Number": args.number,
            "OrderBy": args.order,
            "MinFreq": args.min_freq,
            "MinStat": args.min_stat,
        })

        for lemma, mwe_relations in mwe_parts_relations['data'].items():
            for rel_ctr, relation in enumerate(mwe_relations):
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
                headers = ['Rank', 'POS', "Lemma", 'Frequency', args.order, 'MWE-ID']
                print(tabulate(table_items, headers=headers, tablefmt='fancy_grid'))
