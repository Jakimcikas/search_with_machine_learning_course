import os
import argparse
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import csv

# Useful if you want to perform stemming.
from nltk.stem.snowball import SnowballStemmer
stemmer = SnowballStemmer("english")

categories_file_name = r'/workspace/datasets/product_data/categories/categories_0001_abcat0010000_to_pcmcat99300050000.xml'

queries_file_name = r'/workspace/datasets/train.csv'
output_file_name = r'/workspace/datasets/labeled_query_data.txt'

# for quicker iterations to see if everything works as it suppose to
categories_sample_name = r'/workspace/search_with_machine_learning_course/week4/sample_categories_data.xml'

parser = argparse.ArgumentParser(description='Process arguments.')
general = parser.add_argument_group("general")
general.add_argument("--min_queries", default=1,  help="The minimum number of queries per category label (default is 1)")
general.add_argument("--output", default=output_file_name, help="the file to output to")
general.add_argument("--sample", default=False, help="Use a smaller sample of the category data")

args = parser.parse_args()
output_file_name = args.output
use_sample = args.sample

if args.min_queries:
    min_queries = int(args.min_queries)

# The root category, named Best Buy with id cat00000, doesn't have a parent.
root_category_id = 'cat00000'

if use_sample:
    print("Using sample")
    categories_file_name = categories_sample_name

tree = ET.parse(categories_file_name)
root = tree.getroot()

# Parse the category XML file to map each category id to its parent category id in a dataframe.
categories = []
parents = []
for child in root:
    id = child.find('id').text
    cat_path = child.find('path')
    cat_path_ids = [cat.find('id').text for cat in cat_path]
    leaf_id = cat_path_ids[-1]
    if leaf_id != root_category_id:
        categories.append(leaf_id)
        parents.append(cat_path_ids[-2])
parents_df = pd.DataFrame(list(zip(categories, parents)), columns =['category', 'parent'])

# Read the training data into pandas, only keeping queries with non-root categories in our category tree.
df = pd.read_csv(queries_file_name)[['category', 'query']]
df = df[df['category'].isin(categories)]

# IMPLEMENT ME: Convert queries to lowercase, and optionally implement other normalization, like stemming.
def transform_query(query):
    '''
    Method taken from week3 instructor solution for product transform
    '''
    ret = query.lower()
    ret = ''.join(c for c in ret if c.isalpha() or c.isnumeric() or c=='-' or c==' ' or c =='.')
    ret = ' '.join(map(stemmer.stem, ret.split(' ')))
    return ret

# IMPLEMENT ME: Roll up categories to ancestors to satisfy the minimum number of queries per category.
def roll_up(category, thresholds):
    if category == root_category_id or not thresholds[thresholds.isin([category])].empty:
        return category
    
    category_parents = parents_df[parents_df['category'] == category]
    category_parent_series = category_parents['parent'].values

    if not category_parent_series:
        return category

    return roll_up(category_parent_series[0], thresholds)

# Transform queries
print('Normalizing queries')
df['query'] = df['query'].apply(transform_query)

category_count = df.groupby(['category']).size().reset_index(name='counts')
categories_above_threshold = category_count[category_count['counts'] >= min_queries]
treshold_series = pd.Series(categories_above_threshold['category'])

print(f"category count that is above min threshold: {len(categories_above_threshold)}")

print(f"unique categories before roll up: {len(df['category'].unique())}")

print("Rolling up categories with bellow threshold count")
df['category'] = df['category'].apply(lambda c: roll_up(c, treshold_series))

print(f"unique categories after roll up: {len(df['category'].unique())}")

# Create labels in fastText format.
df['label'] = '__label__' + df['category']

# Output labeled query data as a space-separated file, making sure that every category is in the taxonomy.
df = df[df['category'].isin(categories)]
df['output'] = df['label'] + ' ' + df['query']
df[['output']].to_csv(output_file_name, header=False, sep='|', escapechar='\\', quoting=csv.QUOTE_NONE, index=False)
