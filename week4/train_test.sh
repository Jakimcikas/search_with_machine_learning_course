#!/bin/bash 
# Shuffle data and create test/train split
workspace="/workspace/datasets/"
query_data="labeled_query_data.txt"
data_file="data.fasttext"
train_file="train.fasttext"
test_file="test.fastttext"
model="label_model"

learning_rate=0.35
ep=30
word_grams=2

echo "Shuffling and creating slipts"
shuf "${workspace}${query_data}" > "${workspace}${data_file}"
tail "${workspace}${data_file}" -n 100000 > "${workspace}${train_file}"
head "${workspace}${data_file}" -n 100000 > "${workspace}${test_file}"

echo "Training model"
~/fastText-0.9.2/fasttext supervised -input "${workspace}${train_file}" -output "${workspace}${model}" -lr $learning_rate -epoch $ep -wordNgrams $word_grams

# -lr $learning_rate -epoch $ep -wordNgrams $word_grams
# -lr 1.1 -epoch 30 -wordNgrams 2

echo "Validating model on 1 label"
~/fastText-0.9.2/fasttext test "${workspace}${model}.bin" "${workspace}${test_file}"

echo "Validating model on 3 labels"
~/fastText-0.9.2/fasttext test "${workspace}${model}.bin" "${workspace}${test_file}" 3

echo "Validating model on 5 labels"
~/fastText-0.9.2/fasttext test "${workspace}${model}.bin" "${workspace}${test_file}" 5
