import json, csv
import numpy as np
from keras import models
from keras import layers


class ML:
    @staticmethod
    def save_json_file(filename, data):
        with open(filename + ".json", "w") as f:
            f.write(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))

    @staticmethod
    def get_noun_data():
        with open("output_nouns.json", "r") as f:
            return json.load(f)

    @staticmethod
    def convert_string_to_ascii_list(input_string):
        """
        raw_list = [(ord(c)) for c in input_string]
        output = []

        for i, item in enumerate(raw_list):
            output.append(item)
        """

        return list(input_string)

    @staticmethod
    def train_noun_data():
        labels = ["declension", "gender", "gp", "gs", "np", "ns"]
        data = ML.preprocess_noun_data()
        index_to_char_map, char_to_index_map = ML.generate_index_mappings(data)

        output_data = []
        for item in data:
            for l in item:
                output_data.append(l)
            output_data.append(" ")

        output_data.pop()
        data = output_data

        # pre-processing done

        # let's generate new words
        SEQ_LENGTH = 9
        VOCAB_SIZE = len(index_to_char_map)

        X = np.zeros((int(len(data) / SEQ_LENGTH), SEQ_LENGTH, VOCAB_SIZE))
        y = np.zeros((int(len(data) / SEQ_LENGTH), SEQ_LENGTH, VOCAB_SIZE))
        for i in range(0, int(len(data) / SEQ_LENGTH)):
            X_sequence = data[i * SEQ_LENGTH:(i + 1) * SEQ_LENGTH]
            X_sequence_ix = []

            for l in X_sequence:
                X_sequence_ix.append(char_to_index_map[l])

            input_sequence = np.zeros((SEQ_LENGTH, VOCAB_SIZE))
            for j in range(SEQ_LENGTH):
                input_sequence[j][X_sequence_ix[j]] = 1.
            X[i] = input_sequence

            y_sequence = data[i * SEQ_LENGTH + 1:(i + 1) * SEQ_LENGTH + 1]
            y_sequence_ix = []

            for l in y_sequence:
                y_sequence_ix.append(char_to_index_map[l])

            target_sequence = np.zeros((SEQ_LENGTH, VOCAB_SIZE))
            for j in range(SEQ_LENGTH):
                target_sequence[j][y_sequence_ix[j]] = 1.
            y[i] = target_sequence

        HIDDEN_DIM = 500
        LAYER_NUM = 2
        VOCAB_SIZE = 80
        BATCH_SIZE = 50
        GENERATE_LENGTH = 500

        model = models.Sequential()
        model.add(layers.LSTM(HIDDEN_DIM, input_shape=(None, VOCAB_SIZE), return_sequences=True))
        for i in range(LAYER_NUM - 1):
            model.add(layers.LSTM(HIDDEN_DIM, return_sequences=True))
        model.add(layers.TimeDistributed(layers.Dense(VOCAB_SIZE)))
        model.add(layers.Activation('softmax'))
        model.compile(loss="categorical_crossentropy", optimizer="rmsprop")

        nb_epoch = 0

        while True:
            print('\n\n')
            model.fit(X, y, batch_size=BATCH_SIZE, verbose=1, nb_epoch=1)
            nb_epoch += 1
            ML.generate_text(model, GENERATE_LENGTH, VOCAB_SIZE, index_to_char_map)
            model.save_weights('checkpoint_{}_epoch_{}.hdf5'.format(HIDDEN_DIM, nb_epoch))

    @staticmethod
    def run_network():
        data = ML.preprocess_noun_data()
        index_to_char_map, char_to_index_map = ML.generate_index_mappings(data)

        HIDDEN_DIM = 500
        LAYER_NUM = 2
        VOCAB_SIZE = 80
        GENERATE_LENGTH = 9

        model = models.Sequential()
        model.add(layers.LSTM(HIDDEN_DIM, input_shape=(None, VOCAB_SIZE), return_sequences=True))
        for i in range(LAYER_NUM - 1):
            model.add(layers.LSTM(HIDDEN_DIM, return_sequences=True))
        model.add(layers.TimeDistributed(layers.Dense(VOCAB_SIZE)))
        model.add(layers.Activation('softmax'))
        model.compile(loss="categorical_crossentropy", optimizer="rmsprop")

        model.load_weights(str('checkpoint_{}_epoch_{}.hdf5').format(HIDDEN_DIM, 5))

        NUM_WORDS_GENERATED = 50
        for i in range(NUM_WORDS_GENERATED):
            ML.generate_text(model, GENERATE_LENGTH, len(index_to_char_map), index_to_char_map)

    @staticmethod
    def generate_text(model, length, VOCAB_SIZE, index_to_char_map):
        ix = [np.random.randint(VOCAB_SIZE)]
        y_char = [index_to_char_map[ix[-1]]]
        X = np.zeros((1, length, VOCAB_SIZE))
        for i in range(length):
            X[0, i, :][ix[-1]] = 1
            print(index_to_char_map[ix[-1]], end="")
            ix = np.argmax(model.predict(X[:, :i + 1, :])[0], 1)
            y_char.append(index_to_char_map[ix[-1]])
        return ''.join(y_char)

    @staticmethod
    def generate_index_mappings(data):
        unique_letters_in_set = []

        total_size = len(data)
        word_length = 0

        for item in data:
            word_length += len(item)
            for letter in item:
                if letter not in unique_letters_in_set:
                    unique_letters_in_set.append(letter)

            """
            for ns in item["ns"]:
                word_length += len(ns)
                if ns not in unique_letters_in_set:
                    unique_letters_in_set.append(ns)
            for np in item["np"]:
                word_length += len(np)
                if ns not in unique_letters_in_set:
                    unique_letters_in_set.append(np)

            for gs in item["gs"]:
                word_length += len(gs)
                if ns not in unique_letters_in_set:
                    unique_letters_in_set.append(gs)

            for gp in item["gp"]:
                word_length += len(gp)
                if ns not in unique_letters_in_set:
                    unique_letters_in_set.append(gp)
            """

        unique_letters_in_set = sorted(unique_letters_in_set)

        print(total_size, word_length, word_length / total_size)

        index_to_char_mapping = {ix: char for ix, char in enumerate(unique_letters_in_set)}
        char_to_index_mapping = {char: ix for ix, char in enumerate(unique_letters_in_set)}

        return index_to_char_mapping, char_to_index_mapping

    @staticmethod
    def csvify_json(json_data):
        output = []

        for item in json_data:
            attributes = []
            for key, data in item.items():
                attributes.append(data)

            output.append(attributes)

        return np.array(output)

    @staticmethod
    def output_csv(labels, json_data):
        output = [labels]

        for item in json_data:
            attributes = []
            for key, data in item.items():
                attributes.append(data)

            output.append(attributes)

        with open('output.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(output)

    @staticmethod
    def preprocess_noun_data():
        original_data = ML.get_noun_data()
        gender_hash = {"verbal noun": 0, "masculine": 1, "feminine": 2}
        output = []

        i = 0
        limit = 10

        for item in original_data:
            if i >= limit:
                break

            ns_list = ML.convert_string_to_ascii_list(item["ns"])
            np_list = ML.convert_string_to_ascii_list(item["np"])
            gs_list = ML.convert_string_to_ascii_list(item["gs"])
            gp_list = ML.convert_string_to_ascii_list(item["gp"])

            modified_data = {
                "declension": item["declension"], "gender": gender_hash[item["gender"]],
                "gp": gp_list, "gs": gs_list, "np": np_list, "ns": ns_list
            }

            # output.append(modified_data)
            output.append(list(item["ns"]))

        return output
