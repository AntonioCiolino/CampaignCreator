import streamlit as st
from streamlit_quill import st_quill

import utils.Features as Features
import utils.Tables as Tables
import utils.Writing as Writing

import re

# check to see if this is making a difference.
def update_content(args):
    pass


# Title of the page
st.title('Campaign Creator')
st.caption("Try to create campaigns")
st.warning("DO NOT DEPEND ON THIS TOOL TO KEEP YOUR STORY. It depends on session state, and it will reset at random times.")

if 'random_tables' not in st.session_state:
    st.session_state.random_tables = {}
if 'features' not in st.session_state:
    st.session_state.features = {}
if 'sel' not in st.session_state:
    st.session_state.sel = ""
if 'feat' not in st.session_state:
    st.session_state.feat = ""
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'result' not in st.session_state:
    st.session_state.result = ""
if 'models' not in st.session_state:
    st.session_state.models = []
if 'chapter' not in st.session_state:
    st.session_state.chapter = ""

# campaign session state
if 'campaign' not in st.session_state:
    st.session_state.campaign = ""
#concept text box
if 'concept' not in st.session_state:
    st.session_state.concept = ""
#toc text box
if 'toc' not in st.session_state:
    st.session_state.toc = ""

# attempt to convert to HB format
if 'converted' not in st.session_state:
    st.session_state.converted = ""
if  'randomness' not in st.session_state:
    st.session_state.randomness = 0.5

with st.expander("Enter your API Key", expanded= (st.session_state.api_key == '')):
    st.session_state.api_key = st.text_input('API Key', st.session_state.api_key, type='password')

if (st.session_state.api_key == ""):
    st.write("You need to enter your API Key to use this app.")
else:
    st.session_state.features = Features.Features.features
    st.session_state.random_tables = Tables.Tables().random_tables

    if (st.session_state.models == []):
        st.session_state.models = Writing.Writing().getModels()

    st.info("""
    The Campaign Creator tool is a tool that allows you to create a campaign by selecting ideas, 
    generating a table of contents, and adding content iteratively to the campaign,
    using the model to fill in the next block of content.
    """)

    st.caption("Choose which model that OpenAI will use to generate your content. Choose DaVinci, Curie, or your own fine tuned models.")
    model = st.selectbox("Select a model", st.session_state.models)

    concept = st.text_input('Idea for your campaign', '', key='concept')
    if (st.button('Generate campaign concept', help="This is the overall purpose of the campaign.")):
        st.session_state.campaign = Writing.Writing().generate_campaign(st.session_state.concept + " " + st.session_state.campaign, model)
    if (st.session_state.campaign):
        st.text_area('Campaign', '', key='campaign')

    # AC: for now decided to totally regenerate the toc every time so we don't have to figure out if it's partial.
    if (st.button('Generate table of contents', help="Generates a table of contents.")):
        st.session_state.toc = "Table of Contents: " +  Writing.Writing().generate_toc(st.session_state.campaign, model)
    if (st.session_state.toc):
        st.session_state.toc = st.session_state.toc
        st.text_area('Table of Contents', '', key='toc')

    st.slider('Change randomness', help="Modified how close the camapign sections stick to the subject. Higher is more random.",
              min_value=0.00, max_value=1.00, key='randomness')

    if (st.button('Add sections', help="Add sections to the campaign.")):
        st.session_state.chapter += Writing.Writing().completeModel(st.session_state.campaign + "###\n\n" +
                                                                    st.session_state.toc + "\n\n" +
                                                                    st.session_state.chapter,
                                                                    model,
                                                                    temp=st.session_state.randomness)

    # completions vs. tuning.
    # make a section with the buttons near it
    #col1, col2 = st.columns(2)
    #with col1:

        # st.session_state.chapter += Writing.Writing().completeModel(st.session_state.chapter, model)
    #with col2:
    #     if (st.button('Get Davinci content', help="(Shortcut) Sends the story to OpenAI for additional DaVinci (GPT-3) content.")):
    #         # st.success("Sent to OpenAI: "+ st.session_state.chapter)
    #         st.session_state.chapter += Writing.Writing().completeDavinci(st.session_state.chapter)


    # ----------------------------------------------------------------------------------------------------------------------
    st.text_area(label="Your campaign",
                 help="The campaign that you are creating is here.",
                 height=500,
                 key="chapter",
                 on_change=update_content, args=(st.session_state.chapter, ))

    if (st.button("Display campaign", help="Display your campaign to copy for sharing.")):

        concept_header = st.session_state.concept.split(".")[0]

        # make some slight mods until OpenAI can edit
        camp = st.session_state.campaign.replace("Campaign name:", "### ")\
                    .replace("Campaign settings:","\n:\n### Campaign Settings\n")\
                    .replace("Background story:", "\n:\n### DM Background\n")\
                    .replace("Background settings:", "\n:\n### DM Background\n")\
                    .replace("\\n", "\n") + "\n\n"

        chap = st.session_state.chapter.replace("Background:", ":\n###  Background\n")

        outtoc = st.session_state.toc.replace("Table of Contents:", "{{toc,wide\n# Table of Contents\n- ### {{ " + concept_header + " }}{{ }}\n")
        outtoc = outtoc.replace("\\n", "\n")

        sentences = outtoc.split("\n")
        processed = []
        for s in sentences:
            found = False
            for x in range(1 , 9):
                if s.find(str(x) + ". ")!= -1:
                    processed.append(s.replace( str(x)+". ", "- #### {{ " + str(x) + ". ") + " }}{{ 0}}\n")
                    found = True
            if found == False:
                processed.append(s + "\n")
        outtoc = "".join(processed) + "}}\n"

        st.text_area("Homebrewery Content",
                     value = "##### Concept: " + concept_header + "\n\n" +
                             camp +
                             outtoc +
                             "\n\n## Campaign\n\n" + chap.replace("\\n", "\n"))

