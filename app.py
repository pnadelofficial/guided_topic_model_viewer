import streamlit as st
import pandas as pd
from docx import Document
from datetime import date
from markdown import markdown
import re

st.title('Guided Topic Model Viewer')

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, lineterminator='\n')

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
                st.write(markdown(row['chunk'], raw_html=True).replace("<p>","").replace("</p>",""))
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