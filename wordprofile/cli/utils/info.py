from termcolor import colored


def get_wordprofile_info(wp):
    result = wp.get_info()

    # Projektinformationen
    print(colored("project:", "green"))
    print("author:", result['author'])
    print("creation date:", result['creation_date'])
    print("spec version:", result['spec_file_version'])
    print("spec file:", result['spec_file'])

    # verwendete Korpora
    corpora = result['used_corpora']
    print(colored("corpora:", "green"))
    print(",".join(corpora))

    # Zahlen über Gößen
    print(colored("global info:", "green"))
    print("NoOfLemmas:", result['lemma_size'])
    print("NoOfCooccurrences:", result['relation_size'])
    print("NoOfSentences:", result['sentence_size'])
    print("NoOfHits:", result['info_size'])

    # relationsbezogene Kookkurrenzinformationen
    print(colored("cooccurrence info:", "green"))
    for i in list(result['cooccurrence_info'].items()):
        print(i[0] + ":", i[1])

    # Schwellwerte
    print(colored("global threshold info:", "green"))
    print("LemmaCut:", result['lemma_cut'])
    print(colored("relation threshold info:", "green"))
    for i in list(result['threshold'].items()):
        print(i[0] + ":", i[1])
