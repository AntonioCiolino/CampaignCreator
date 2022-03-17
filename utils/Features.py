import csv
import random
import streamlit as st

class Features:
    prompts = []
    features = []
    def __init__(self, **kwargs):

        with open('../csv/features.csv') as data_file:
            data = csv.reader(data_file, delimiter=',')
            for row in data:
                self.features.append(str(row[0]))
                self.prompts.append(str(row[1]))


    def get_prompt(self, item):
        try:
            idx = self.features.index(item)
            return self.prompts[idx]
        except Exception as oops:
            st.error('ERROR in get_prompt function:' + oops)
