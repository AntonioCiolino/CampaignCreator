import csv
import random
import streamlit as st

class Tables:
    random_tables = {}
    def __init__(self, **kwargs):
        tables = {}
        with open('../csv/tables1e.csv') as data_file:
            data = csv.reader(data_file, delimiter='\t')
            for row in data:
                if (row[0] == 'd100'):
                    current_table = row[1]
                    tables[current_table] = []
                else:
                    tables[current_table].append(row[1])
        self.random_tables = tables

    def get_random_thing(self):
        try:
            return random.choice(st.session_state.random_tables[st.session_state.sel])
        except Exception as oops:
            st.error('ERROR in get_random_thing function:' +  oops)
