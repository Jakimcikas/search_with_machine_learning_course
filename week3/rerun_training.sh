# Shuffle data and create test/train split
echo "Shuffling and creating slipts"
shuf /workspace/datasets/categories/output.fasttext > /workspace/datasets/categories/output_shuffled.fasttext
tail /workspace/datasets/categories/output_shuffled.fasttext -n 10000 > /workspace/datasets/categories/sample_train.fasttext
head /workspace/datasets/categories/output_shuffled.fasttext -n 10000 > /workspace/datasets/categories/sample_test.fasttext

echo "Training model"
~/fastText-0.9.2/fasttext supervised -input /workspace/datasets/categories/sample_train.fasttext -output /workspace/datasets/categories/test_model -lr 1.1 -epoch 30 -wordNgrams 2

echo "Validating model on 1 label"
~/fastText-0.9.2/fasttext test /workspace/datasets/categories/test_model.bin /workspace/datasets/categories/sample_test.fasttext

echo "Validating model on 3 labels"
~/fastText-0.9.2/fasttext test /workspace/datasets/categories/test_model.bin /workspace/datasets/categories/sample_test.fasttext 3
