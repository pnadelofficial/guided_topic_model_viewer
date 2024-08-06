import streamlit as st
from rank_bm25 import BM25Okapi
import re

class BM25WithOperators:
    def __init__(self, documents):
        self.documents = documents
        self.tokenized_documents = [self._tokenize(doc) for doc in documents]
        self.bm25 = BM25Okapi(self.tokenized_documents)

    def _tokenize(self, text):
        return re.findall(r'\w+', text.lower())

    def _parse_query(self, query):
        tokens = re.findall(r'\w+|AND|OR|NOT|\(|\)', query.upper())
        parsed = []
        i = 0
        while i < len(tokens):
            if tokens[i] in ('AND', 'OR'):
                parsed.append({'op': tokens[i], 'term': tokens[i+1]})
                i += 2
            elif tokens[i] == 'NOT':
                parsed.append({'op': 'NOT', 'term': tokens[i+1]})
                i += 2
            else:
                parsed.append({'op': 'OR', 'term': tokens[i]})
                i += 1
        return parsed

    def search(self, query, top_k = 5):
        parsed_query = self._parse_query(query)
        scores = [0] * len(self.documents)

        for item in parsed_query:
            term_scores = self.bm25.get_scores(self._tokenize(item['term']))
            if item['op'] == 'AND':
                scores = [min(s1, s2) for s1, s2 in zip(scores, term_scores)]
            elif item['op'] == 'OR':
                scores = [max(s1, s2) for s1, s2 in zip(scores, term_scores)]
            elif item['op'] == 'NOT':
                scores = [s1 if s2 == 0 else 0 for s1, s2 in zip(scores, term_scores)]

        results = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [{'doc_id': i, 'score': score, 'text': self.documents[i]} 
                for i, score in results[:top_k] if score > 0]
