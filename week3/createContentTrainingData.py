import argparse
import os
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from nltk.stem import SnowballStemmer
import re
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

stemmer = SnowballStemmer("english")


def transform_name(product_name):
    cleaned = re.sub("[^0-9a-zA-Z]+", " ", product_name).lower()
    return " ".join([stemmer.stem(token) for token in cleaned.split()])


# Directory for product data
directory = r'/workspace/search_with_machine_learning_course/data/pruned_products/'

parser = argparse.ArgumentParser(description='Process some integers.')
general = parser.add_argument_group("general")
general.add_argument("--input", default=directory,
                     help="The directory containing product data")
general.add_argument(
    "--output", default="/workspace/datasets/fasttext/output.fasttext", help="the file to output to")

# Consuming all of the product data will take over an hour! But we still want to be able to obtain a representative sample.
general.add_argument("--sample_rate", default=1.0, type=float,
                     help="The rate at which to sample input (default is 1.0)")

# IMPLEMENT: Setting min_products removes infrequent categories and makes the classifier's task easier.
general.add_argument("--min_products", default=0, type=int,
                     help="The minimum number of products per category (default is 0).")

general.add_argument("--depth", default=1, type=int,
                    help="Category depth reduction(default is 1")

args = parser.parse_args()
output_file = args.output
path = Path(output_file)
output_dir = path.parent
if os.path.isdir(output_dir) == False:
    os.mkdir(output_dir)

if args.input:
    directory = args.input
# IMPLEMENT:  Track the number of items in each category and only output if above the min
min_products = args.min_products
sample_rate = args.sample_rate
category_depth = args.depth

products = []
print("Writing results to %s" % output_file)
for filename in os.listdir(directory):
    if filename.endswith(".xml"):
        print("Processing %s" % filename)
        f = os.path.join(directory, filename)
        tree = ET.parse(f)
        root = tree.getroot()
        for child in root:
            if random.random() > sample_rate:
                continue
            # Check to make sure category name is valid
            if (child.find('name') is not None and child.find('name').text is not None and
                child.find('categoryPath') is not None and len(child.find('categoryPath')) > 0 and
                    child.find('categoryPath')[len(child.find('categoryPath')) - category_depth][0].text is not None):
                # Choose last element in categoryPath as the leaf categoryId
                cat = child.find('categoryPath')[len(
                    child.find('categoryPath')) - 1][0].text
                # Replace newline chars with spaces so fastText doesn't complain
                name = child.find('name').text.replace('\n', ' ')

                products.append({
                    "category": cat,
                    "product": transform_name(name)
                })

products_df = pd.DataFrame(products)
if min_products > 0:
    print(f"Min products per category - {min_products}")
    products_df = products_df.groupby('category').filter(lambda p: p['category'].count() > min_products)

print("Writing results to %s" % output_file)
with open(output_file, 'w') as output:
    for _, row in products_df.iterrows():
        output.write("__label__%s %s\n" % (row["category"], row["product"]))
