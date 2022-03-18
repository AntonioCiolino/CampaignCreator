import streamlit as st
from streamlit_quill import st_quill

import utils.Features as Features
import utils.Tables as Tables
import utils.Writing as Writing

# check to see if this is making a difference.
def update_content(args):
    pass


# Title of the page
st.title('Campaign Creator')
st.caption("Try to create campaigns")
st.caption("DO NOT DEPEND ON THIS TOOL TO KEEP YOUR STORY. It depends on session state, and it can reset at any time.")

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


with st.expander("Enter your API Key"):
    st.session_state.api_key = st.text_input('API Key', st.session_state.api_key, type='password')

if (st.session_state.api_key == ""):
    st.write("You need to enter your API Key to use this app.")
else:
    st.session_state.features = Features.Features.features
    st.session_state.random_tables = Tables.Tables().random_tables

    if (st.session_state.models == []):
        st.session_state.models = Writing.Writing().getModels()

    st.caption("choose which model that OpenAI will use to generate your content. Choose DaVinci, Curie, or your own fine tuned models.")
    model = st.selectbox("Select a model", st.session_state.models)

    # with st.expander("Optional Tool: Inject random data"):
    #     st.caption("Appends a random thing from the collection of options into the story area. This can be used to spark ideas for yourself or the generator.")
    #     st.session_state.sel = st.selectbox('Select grouping of content', st.session_state.random_tables.keys(),
    #                                         help="Select a random table to generate content from.")
    #
    #     # detemine button stuff before displaying or loading text boxes
    #     if st.button('Inject a thing', help="Add a random thing to the content from a list of items."):
    #         st.session_state.chapter += "\n" + Tables.Tables().get_random_thing()

    # with st.expander("Optional tool: generate a style based on a specific sentence, phrase or idea."):
    #     prompt = st.text_input('Prompt to process', '', help="If you have a specific short prompt, place it here to process. It will append the results to the story.")
    #
    #     # for the prompt, if the prompt is blank, disable the controls, but still render.
    #     d = (prompt == "")
    #     st.session_state.feat = st.selectbox('Select a style', st.session_state.features, disabled = d,
    #                                          help="Requests data from GPT-3 in the selected style.")
    #
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         if (st.button('Generate tuned content', help="Calls OpenAI for fine tuned content based on the prompt.", disabled = d)):
    #             st.session_state.chapter += Writing.Writing().get_tuned_content(prompt, model)
    #     with col2:
    #         if (st.button('Generate generic content', help="(Shortcut) Calls OpenAI for Davinci content based no the prompt.", disabled = d)):
    #             st.session_state.chapter += Writing.Writing().get_generic_content(prompt)

    st.info("""
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
    
    """)


    concept = st.text_input('Idea for your campaign', '', key='concept')
    if (st.button('Generate campaign concept', help="This is the overall purpose of the campaign.")):
        st.session_state.campaign = Writing.Writing().generate_campaign(st.session_state.concept + " " + st.session_state.campaign, model).replace("\n", '\n').replace("\n", "\n\n")
    if (st.session_state.campaign):
        st.text_area('Campaign', '', key='campaign')

    # AC: for now decided to totally regenerate the toc every time so we don't have to figure out if it's partial.
    if (st.button('Generate table of contents', help="Generates a table of contents.")):
        st.session_state.toc = "Table of Contents:\n" +  Writing.Writing().generate_toc(st.session_state.campaign, model).replace("\n", '\n')
    if (st.session_state.toc):
        st.text_area('Table of Contents', '', key='toc')

    if (st.button('Add sections', help="Add sections to the campaign.")):
        st.session_state.chapter += Writing.Writing().completeModel(st.session_state.campaign + "###\n\n" + st.session_state.toc + "\n\n" +  st.session_state.chapter, model).replace("\n", '\n')

    #completions vs. tuning.
    # make a section with the buttons near it
    col1, col2 = st.columns(2)
    with col1:
        if (st.button('Get selected model content', help="Sends the story to OpenAI for additional model (fine tuned) content.")):
            # st.success("Sent to OpenAI: "+ st.session_state.chapter)
            st.session_state.chapter += Writing.Writing().completeModel(st.session_state.chapter, model).replace("\n", '\n')
    with col2:
        if (st.button('Get Davinci content', help="(Shortcut) Sends the story to OpenAI for additional DaVinci (GPT-3) content.")):
            # st.success("Sent to OpenAI: "+ st.session_state.chapter)
            st.session_state.chapter += Writing.Writing().completeDavinci(st.session_state.chapter).replace("\n", '\n')


    # ----------------------------------------------------------------------------------------------------------------------
    st.text_area(label="Your campaign",
                 help="The camapign that you are creating is here. You can add content to it by clicking the buttons above.",
                 height=500,
                 key="chapter",
                 on_change=update_content, args=(st.session_state.chapter, ))


    if (st.button('Create Homebrewery file', help='Experiment: convert to HB file')):
        prompt="""
        For each example below change to Homebrewery format:
        +++
        Table of Contents:
        # Table of Contents:
        +++
        Campaign Name:
        # Campaign:
        +++
        Background:
        ## Background:
        +++
        1. Some chapter content
        ### 1. Some Chapter Content
        """ + "+++" + st.session_state.chapter + "+++\n"
        st.write(prompt)
        st.session_state.converted = Writing.Writing().completeDavinci(prompt)
        st.text_area('Homebrewery', '', key='converted')
