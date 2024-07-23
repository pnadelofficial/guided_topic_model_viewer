import streamlit as st
import pandas as pd
from docx import Document
from datetime import date
from html import escape
import re
from ast import literal_eval
import json

st.title('Guided Topic Model Viewer')

@st.cache_resource
def load_tokenizer():
    return json.load(open("./tokenizer.json"))
tokenizer_dict = load_tokenizer()

st.markdown("""
<style>
    body {
        background-color: #f0f0f0;
    }
    .highlight {
        padding: 2px 0;
        border-radius: 3px;
        transition: all 0.2s;
    }
    .highlight:hover {
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    }
    /* Custom tooltip */
    .highlight {
        position: relative;
    }
    .highlight::after {
        content: attr(title);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background-color: #333;
        color: white;
        padding: 5px 10px;
        border-radius: 3px;
        font-size: 14px;
        white-space: nowrap;
        opacity: 0;
        transition: opacity 0.3s;
        pointer-events: none;
    }
    .highlight:hover::after {
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

def highlight_text(text, lexical_weights, tokenizer_dict):
    sorted_words = sorted(
        [(tokenizer_dict['model']['vocab'][int(id)][0].replace('▁', ''), weight) 
         for id, weight in lexical_weights.items()],
        key=lambda x: len(x[0]),
        reverse=True
    )

    max_weight = max(weight for _, weight in sorted_words)
    min_weight = min(weight for _, weight in sorted_words)
    weight_range = max_weight - min_weight

    def replace_word(match):
        word = match.group(0)
        for token, weight in sorted_words:
            if word.lower() == token.lower():
                normalized_weight = (weight - min_weight) / weight_range if weight_range > 0 else 1
                hue = int(240 * weight) 
                color = f"hsla({hue}, 90%, 65%, {0.3 + 0.7 * normalized_weight})"
                tooltip = f"Token: {escape(word)}, Lexical weight: {weight:.4f}"
                return f'<span class="highlight" style="background-color: {color};" title="{tooltip}">{escape(word)}</span>'
        return word

    pattern = r'\b(' + '|'.join(re.escape(word) for word, _ in sorted_words) + r')\b'
    highlighted_text = re.sub(pattern, replace_word, text, flags=re.IGNORECASE)

    return highlighted_text

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, lineterminator='\n')
    if 'lexical_weights' in df.columns:
        df['lexical_weights'] = df['lexical_weights'].apply(literal_eval)

    if 'topic_df' not in st.session_state:
        st.session_state['topic_df'] = df

if 'topic_df' in st.session_state:
    topic_choice = st.selectbox('Pick a topic to look at more closely', list(st.session_state['topic_df'].topic.unique()))
    st.markdown(f"#### Topic: **{topic_choice.replace('<|eot_id|>', '')}**")
    selected_df = st.session_state['topic_df'][st.session_state['topic_df'].topic == topic_choice]
    fnames = list(selected_df.filename.unique())
    tabs = st.tabs([u.replace('.pdf', '').split('/')[-1].replace('"', '') for u in fnames])
    
    for i, tab in enumerate(tabs):
        with tab:
            for j, row in selected_df[selected_df.filename == fnames[i]].iterrows():
                text = row['chunk']
                lexical_weights = row['lexical_weights']
                
                highlighted_text = highlight_text(text, lexical_weights, tokenizer_dict)
                st.markdown(highlighted_text.replace("<p>","").replace("</p>",""), unsafe_allow_html=True)
                st.divider()
            # rerank_list = reranker.rank(topic_choice, list(selected_df[selected_df.filename == fnames[i]].chunk.unique()))
            # for d in rerank_list:
            #     chunk = st.session_state['topic_df'].iloc[d['corpus_id']]['chunk']
            #     st.write(markdown(chunk, raw_html=True).replace("<p>","").replace("</p>",""))
            #     st.divider()

    if st.button('Export data'):
        with st.spinner("Exporting data"):
            xl = selected_df.to_excel(f"{topic_choice}_{date.today()}.xlsx", engine='xlsxwriter', index=False)
            with open(f"{topic_choice}_{date.today()}.xlsx", 'rb') as x_file:
                btn = st.download_button(
                    label="Download data as Excel",
                    data=x_file,
                    file_name=f"{topic_choice}_{date.today()}.xlsx",
                    key='excel_dl'
                )
        
            doc = Document()
            doc.add_heading(topic_choice, 0)
            p = doc.add_paragraph(f"{date.today()}")
            p.italic = True
            for i, row in selected_df.dropna().iterrows():
                p = doc.add_paragraph(f"Document chunk {i+1}")
                p.bold = True
                doc.add_paragraph(row['filename'])
                text = re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', '', row['chunk'])
                c = doc.add_paragraph(text)
                run = c.add_run()
                run.add_break()
            doc.save(f"{topic_choice}_{date.today()}.docx")
            with open(f"{topic_choice}_{date.today()}.docx", 'rb') as w_file:
                btn = st.download_button(
                    label="Download data as Word",
                    data=w_file,
                    file_name=f"{topic_choice}_{date.today()}.docx",
                    key='word_dl'
                )