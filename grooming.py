import xml.etree.ElementTree as et
import re
import json
import copy

from string import digits


class Grooming:
    @staticmethod
    def generate_modified_files():
        with open("data/input_copy.xml", "r") as f:
            data = f.read().replace("xml:lang", "lang")

        with open("data/xml_modified.xml", "w") as f:
            f.write(data)

    @staticmethod
    def groom_xml_data_app():
        groomed_terms = []

        tree = et.parse("data/xml_modified.xml")
        elements = tree.getroot()
        for element in elements.iter("termEntry"):
            en_translations = []
            domains = []
            examples = []
            ga_term = ""
            gender = ""
            declension = -1

            is_noun = False
            should_add_to_output = False

            for domain in element.iter("descrip"):
                if domain.attrib["type"] == "domain" and domain.attrib["lang"] == "en":
                    curated_domains = str(domain.text).split("›")[0].split(",")
                    for curation in curated_domains:
                        domains.append(curation.strip())

            # prevent duplications of domains
            temp_domains = []
            for domain in domains:
                if domain not in temp_domains:
                    temp_domains.append(domain)

            domains = temp_domains

            for termEntry in element.iter("langSet"):
                if termEntry.attrib["lang"] == "en":
                    is_noun = termEntry.find("./tig/termNote[@type='partOfSpeech']")
                    if is_noun is not None:
                        is_noun = (is_noun.text == "s")
                        if is_noun:
                            for en_tig in termEntry:
                                en_translations.append(en_tig.find("./term").text)

                elif termEntry.attrib["lang"] == "ga":
                    if is_noun:
                        for ga_tig in termEntry:
                            ga_term = ga_tig.find("./term").text
                            phrase_size = len(str(ga_term).split(" "))

                            term_note = termEntry.find("./tig/termNote[@type='partOfSpeech']")

                            gender_selection = {"fir": "masculine", "bain": "feminine"}

                            # plurals are bad, avoid them as much as possible
                            if str(ga_term[:3]) != "na ":
                                if term_note is not None:
                                    gender = ''.join([i for i in term_note.text if not i.isdigit()])
                                    declension = ''.join(c for c in term_note.text if c.isdigit())
                                    has_declension = len(declension) > 0

                                    if len(domains) > 0 and has_declension and gender in gender_selection:
                                        gender = gender_selection[gender]
                                        # long phrases don't add anything in comparison to short phrases
                                        # we should probably assume 1 word is enough for vocab learning
                                        WORD_SIZE_LIMIT = 2
                                        should_add_to_output = phrase_size < WORD_SIZE_LIMIT
                                        break

            if should_add_to_output:
                groomed_terms.append({
                    "ga": ga_term, "en": en_translations,
                    "gender": gender, "declension": int(declension),
                    "domains": domains
                })

        # sort list by ga term alphabetically
        output = []
        groomed_terms = sorted(groomed_terms, key=lambda k: k["ga"], reverse=False)
        for item in groomed_terms:
            for domain in item["domains"]:
                temp_item = copy.deepcopy(item)
                temp_item.pop("domains", None)
                temp_item["domain"] = domain
                output.append(item)

        for item in groomed_terms:
            print(item)

        # ~44,510 words
        print(len(groomed_terms), "items generated")

        with open("data/output_app_nouns.json", "w") as f:
            f.write(json.dumps(groomed_terms, indent=4, ensure_ascii=False))

    @staticmethod
    def split_app_nouns_files():
        with open("data/output_app_nouns.json", "r") as f:
            data = json.loads(f.read())

        output = {}
        domains = []

        for term in data:
            for domain in term["domains"]:
                if domain not in domains and str(domain) is not "":
                    domains.append(domain)

        for item in domains:
            output[item] = []

        for term in data:
            for domain in term["domains"]:
                if str(domain) is not "":
                    temp_item = term
                    temp_item.pop("domains", None)
                    output[domain].append(temp_item)

        output = [output]

        with open("data/output_domained_nouns.json", "w") as f:
            f.write(json.dumps(output, indent=4, sort_keys=True, ensure_ascii=False))

        # first save the master list of the domains as its own json to refer to later in the app
        with open("data/domains.json", "w") as f:
            f.write(json.dumps(domains, indent=4, sort_keys=True, ensure_ascii=False))

        # now split each list element into its own file for individual loading later
        for item in output:
            for i, key in enumerate(item):
                with open("data/nouns/" + Grooming.format_file_name(key) + ".json", "w") as f:
                    data_to_save = sorted(item[key], key=lambda k: k["ga"], reverse=False)
                    f.write(json.dumps(data_to_save, indent=4, sort_keys=True, ensure_ascii=False))

    @staticmethod
    def format_file_name(raw_string):
        return str(raw_string).lower().replace("&", "and").replace(" ", "_")

    @staticmethod
    def groom_xml_data():
        raw_nouns = []

        tree = et.parse("xml_modified.xml")
        elements = tree.findall("//langSet[@lang='ga']/tig")
        for element in elements:
            entry = {}

            # first find the POS to know how to parse
            pos = element.find("./termNote[@type='partOfSpeech']")
            if pos is not None:
                is_noun = pos.text[:3] in ["fir", "bai", "abr"]
                is_verb = pos.text in ["br"]
                is_adjective = pos.text in ["a", "a1", "a2", "a3"]

                if is_noun:
                    # fir, bain, ?
                    gender_selection = {"fir": "masculine", "fir iol": "masculine", "bain": "feminine",
                                        "bain iol": "feminine", "abr": "verbal noun"}
                    gender = gender_selection[pos.text.translate({ord(k): None for k in digits})]

                    # None, 1, 2, 3, 4, 5
                    declension = re.findall(r'\d+', pos.text)
                    if len(declension) > 0:
                        declension = declension[0]
                    if len(declension) == 0:
                        declension = -1

                    entry["gender"] = gender
                    entry["declension"] = int(declension)

                for node in element:
                    if is_noun:
                        if node.tag == "term":
                            entry["ns"] = str(node.text).replace("?", "").strip()

                        if node.tag == "termNote":
                            if node.attrib["type"] == "gu":
                                entry["gs"] = str(node.text).replace("?", "").strip()
                            if node.attrib["type"] == "gi":
                                entry["gp"] = str(node.text).replace("?", "").strip()
                            if node.attrib["type"] == "ai":
                                entry["np"] = str(node.text).replace("?", "").strip()
                            if node.attrib["type"] == "iol":
                                entry["np"] = str(node.text).replace("?", "").strip()
                                entry["gp"] = entry["np"]

                if entry is not {}:
                    raw_nouns.append(entry)

        nouns = []
        for noun in raw_nouns:
            # TODO change back to 3
            if noun is not {} and len(noun) > 5:
                nouns.append(noun)

        print(len(nouns), "items generated")

        with open("output_nouns.json", "w") as f:
            f.write(json.dumps(nouns, indent=4, sort_keys=True, ensure_ascii=False))
