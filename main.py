from grooming import Grooming


def main():
    Grooming.groom_xml_data_app()
    Grooming.split_app_nouns_files()

    # ML.train_noun_data()
    # ML.run_network()


if __name__ == "__main__":
    main()
