import zipfile
import random
import torch
import numpy


def string_to_one_hot(s, char_to_index):
    if len(char_to_index.keys()) <= 0:
        return
    one_hot = torch.zeros(len(s), len(char_to_index.keys()))
    for i, char in enumerate(s):
        one_hot[i, char_to_index[char]] = 1.0
    return one_hot


def split_list(input_list, split_ratio=0.9):
    # Shuffle the list to ensure randomness
    shuffled_list = input_list[:]
    random.shuffle(shuffled_list)

    # Determine the split index
    split_index = int(len(shuffled_list) * split_ratio)

    # Split the list
    list_90 = shuffled_list[:split_index]
    list_10 = shuffled_list[split_index:]

    return list_90, list_10


# Part e
def split_string_to_consecutive_sequences(whole_sequence: str, sub_seq_len: int):
    if sub_seq_len > len(whole_sequence):
        return
    ret_list = list()
    for i in range(len(whole_sequence)-sub_seq_len-1):
        ret_list.append(whole_sequence[i:(i+sub_seq_len)])
    return ret_list


class StringClassifier(torch.nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(StringClassifier, self).__init__()
        self.flatten = torch.nn.Flatten()
        self.fc1 = torch.nn.Linear(input_size, hidden_size)
        self.relu = torch.nn.ReLU()
        self.fc2 = torch.nn.Linear(hidden_size, output_size)
        self.sigmoid = torch.nn.Sigmoid()

    def forward(self, x):
        x = self.flatten(x)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.sigmoid(x)
        return x


def main():
    neg_list, pos_list = list(), list()
    with zipfile.ZipFile("ex1 data", 'r') as zip_ref:
        with zip_ref.open("ex1 data/neg_A0201.txt", 'r') as neg:
            for line in neg:
                neg_list.append(line.decode())
            neg.close()
        with zip_ref.open("ex1 data/pos_A0201.txt", 'r') as pos:
            for line in pos:
                pos_list.append(line.decode())
            pos.close()
        zip_ref.close()

    # Getting all the letter representations of the amino acids
    all_data = neg_list + pos_list
    all_letters = set()
    for dpoint in all_data:
        for l in dpoint:
            all_letters.add(l)
    char_to_index = {char: idx for idx, char in enumerate(all_letters)}

    # Example dataset
    pre_shuffled_data = neg_list + pos_list
    pre_shuffled_labels = [0]*len(neg_list) + [1]*len(pos_list)
    paired_list = list(zip(pre_shuffled_data, pre_shuffled_labels))

    random.shuffle(paired_list)

    split_train, split_test = split_list(paired_list)
    split_train_data, split_train_labels = zip(*split_train)
    split_test_data, split_test_labels = zip(*split_test)

    split_train_data, split_train_labels = list(split_train_data), list(split_train_labels)
    split_test_data, split_test_labels = list(split_test_data), list(split_test_labels)

    # Neural Network creation and training
    inputs = torch.stack([string_to_one_hot(s.replace('\n', ''), char_to_index) for s in split_train_data])
    targets = torch.tensor(split_train_labels, dtype=torch.float32)

    input_size = 9 * len(char_to_index.keys())  # 9 characters each with a one-hot encoding of length num_chars
    hidden_size = 128  # Number of hidden units
    output_size = 1  # Binary output

    model = StringClassifier(input_size, hidden_size, output_size)
    criterion = torch.nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    print("---------------------------------------------------------- Training outputs:")
    
    # Training loop
    num_epochs = 200
    for epoch in range(num_epochs):
        model.train()
        optimizer.zero_grad()

        outputs = model(inputs)
        loss = criterion(outputs.squeeze(), targets)

        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}')

    print("Training complete.")

    # Trained Neural Network on test data
    test_inputs = torch.stack([string_to_one_hot(s.replace('\n', ''), char_to_index) for s in split_test_data])
    test_targets = torch.tensor(split_test_labels, dtype=torch.float32)

    outputs = model(test_inputs)
    loss = criterion(outputs.squeeze(), test_targets)

    print("---------------------------------------------------------- Test outputs:")
    print(f'Test Loss: {loss.item():.4f}')

    # Getting results for the given spike protein
    with open("spike.txt", 'r') as spike_txt:
        whole_sent = spike_txt.read()
        spike_txt.close()

    spike_data = split_string_to_consecutive_sequences(whole_sent, 9)
    # print(string_to_one_hot(spike_data[0], char_to_index).shape)

    spike_inputs = torch.stack([string_to_one_hot(s, char_to_index) for s in spike_data])
    outputs = model(spike_inputs)

    print("---------------------------------------------------------- Spike outputs:")
    print(torch.sum(torch.round(outputs)))


if __name__ == '__main__':
    main()
