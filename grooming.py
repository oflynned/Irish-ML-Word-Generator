import xml.etree.ElementTree as et
import re
import json

from string import digits


class Grooming:
    @staticmethod
    def generate_modified_files():
        with open("input_copy.xml", "r") as f:
            data = f.read().replace("xml:lang", "lang")

        with open("xml_modified.xml", "w") as f:
            f.write(data)

    @staticmethod
    def groom_xml_data_app():
        output = []

        tree = et.parse("xml_modified.xml")
        elements = tree.getroot()
        for element in elements.iter("termEntry"):
            en_translations = []
            ga_term = ""
            gender = ""

            is_noun = False
            should_add_to_output = False

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
                                    if term_note.text in gender_selection:
                                        gender = gender_selection[term_note.text.translate({ord(k): None for k in digits})]
                                        if re.findall(r'\d+', term_note.text) is not None:
                                            # long phrases don't add anything in comparison to short phrases
                                            # we should probably assume 5 words are enough
                                            should_add_to_output = phrase_size < 5
                                            break

                if should_add_to_output:
                    output.append({"ga": ga_term, "en": en_translations, "gender": gender})

        for item in output:
            print(item)

        # 15,286 words
        print(len(output), "items generated")

        with open("output_app_nouns.json", "w") as f:
            f.write(json.dumps(output, indent=4, ensure_ascii=False))

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
