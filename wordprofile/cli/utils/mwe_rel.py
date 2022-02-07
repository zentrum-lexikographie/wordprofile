from tabulate import tabulate
from termcolor import colored


def get_mwe_free(wp, args):
    selection = wp.get_mwe_relations_by_list({
        'Parts': args.LemmaList.split(','),
    })
    for surface, relations in selection['data'].items():
        for rel_ctr, relation in enumerate(relations):
            print()
            print(colored("{}. {} ({}): {}".format(rel_ctr + 1,
                                                   relation['Relation'],
                                                   relation['RelId'],
                                                   relation['Description']),
                          "green"))

            table_items = []
            for coocc_ctr, coocc in enumerate(relation['Tuples']):
                table_items.append([
                    str(coocc_ctr + 1), coocc['POS'], coocc["Lemma"], coocc["Form"], coocc['Score']['Frequency'],
                    coocc['Score'][args.order], coocc['ConcordId']
                ])
            headers = ['Rank', 'POS', "Lemma", "Form", 'Frequency', args.order, 'MWE-ID']
            print(tabulate(table_items, headers=headers, tablefmt='fancy_grid'))
