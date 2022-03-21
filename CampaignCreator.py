import streamlit as st
from streamlit_quill import st_quill

import utils.Features as Features
import utils.Tables as Tables
import utils.Writing as Writing

# check to see if this is making a difference.
def update_content(args):
    pass

def process_block(content, prefix, suffix):
    sentences = content.split("\n")
    processed = []
    for s in sentences:
        found = False
        for x in range(1 , 9):
            if s.find(str(x) + ". ")!= -1:
                processed.append(s.replace( str(x)+". ", str.format(prefix, x)) + suffix)
                found = True
        if found == False:
            processed.append(s + "\n")
    return "".join(processed)

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

#autogenerate a title selection and store what was selected
if 'campaign_titles' not in st.session_state:
    st.session_state.campaign_titles = []
if 'campaign_title' not in st.session_state:
    st.session_state.campaign_title = []

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
    
    The content can be exported at the bottom to Homebrewery, and as it is an editor,
    information can be done in an iterative process to make larger campaigns.
    
    Note, GPT-3 will kick out an error and lose your data if the number of PGT-3 token are greater than 2048,
    usually about 3000 words.  And no, currently I can't calculate that. Copy early and often!
    """)

    st.caption("Choose which model that OpenAI will use to generate your content. Choose DaVinci, Curie, or your own fine tuned models.")
    model = st.selectbox("Select a model", st.session_state.models)

    concept = st.text_input('Idea for your campaign', '', key='concept', help="Enter your idea for the campaign. Add thoughts, character names, etc.")
    if (st.button('Generate campaign concept', help="This is the overall purpose of the campaign.")):
        st.session_state.campaign = Writing.Writing().generate_campaign(st.session_state.concept + " " + st.session_state.campaign, model)
    if (st.session_state.campaign):
        st.text_area('Campaign', '', key='campaign')

    if (st.button('Generate potential campaign titles', help="Alternate titles")):
        st.session_state.campaign_titles = Writing.Writing().generate_campaign_titles(st.session_state.concept, model).split("\n")
        for title in st.session_state.campaign_titles:
            st.write("title: " + title)
        st.selectbox('Campaign', st.session_state.campaign_titles, key='campaign_titles')

    # AC: for now decided to totally regenerate the toc every time so we don't have to figure out if it's partial.
    if (st.button('Generate table of contents', help="Generates a table of contents. You'll have to prettify it yourself before brewig it...")):
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

    # ----------------------------------------------------------------------------------------------------------------------
    st.text_area(label="Your campaign",
                 help="The campaign that you are creating is here.",
                 height=500,
                 key="chapter",
                 on_change=update_content, args=(st.session_state.chapter, ))

    if (st.button("Create Homebrewery content", help="Do some initial formatting for Homebrewery")):

        concept_header = st.session_state.concept.split(".")[0]

        # make some slight mods until OpenAI can edit - need to test this more
        camp = st.session_state.campaign.replace("\\n", "\n") + "\n\n"
        camp = camp.replace("Campaign Name:", "### ")\
                    .replace("Campaign Settings:","\n:\n#### Campaign Settings\n") \
                   .replace("Background story:", "\n:\n#### DM Background\n") \
                   .replace("Summary:", "\n:\n#### Summary\n") \
                   .replace("Background settings:", "\n:\n#### DM Background\n")\
                    .replace("\\n", "\n") + "\n\n"

        chap = st.session_state.chapter.replace("Background:", ":\n###  Background\n")
        prefix = "### {}. "
        suffix = "\n"
        chap = process_block(chap, prefix, suffix)

        outtoc = st.session_state.toc.replace("Table of Contents:", "# Table of Contents\n- ### {{ " + concept_header + " }}{{ }}\n")
        outtoc = outtoc.replace("\\n", "\n")

        sentences = outtoc.split("\n")
        prefix = "\t- ####  {{{{  {}. "     #str.format needs to double these up
        suffix = " }}{{ 0}}\n"
        outtoc = process_block(outtoc, prefix, suffix)

        title_page_style = """
<style>
  .page#p1{ text-align:center; counter-increment: none; }
  .page#p1:after{ display:none; }
  .page:nth-child(2n) .pageNumber { left: inherit !important; right: 2px !important; }
  .page:nth-child(2n+1) .pageNumber { right: inherit !important; left: 2px !important; }
  .page:nth-child(2n)::after { transform: scaleX(1); }
  .page:nth-child(2n+1)::after { transform: scaleX(-1); }
  .page:nth-child(2n) .footnote { left: inherit; text-align: right; }
  .page:nth-child(2n+1) .footnote { left: 80px; text-align: left; }
</style>
"""
        page_image = "![Painting](https://get.pxhere.com/photo/landscape-forest-people-sky-wood-valley-village-painting-trees-art-clouds-mountains-screenshot-huts-rural-area-oil-on-canvas-charles-blomfield-1138873.jpg) {position:absolute,top:0px,right:0px,width:100%}"

        page_header = """
{{{{watermark DRAFT}}}}    
       
{{{{margin-top:625px}}}}  
        
#  {}         
{{{{margin-top:25px}}}}
              
{{{{wide
##### {}
}}}}
\page

"""

        st.text_area("Homebrewery Content",
                     value = title_page_style + page_image + page_header.format(st.session_state.campaign_title, concept_header) +
                        "{{note,wide\n##### Campaign Concept: " + concept_header + "\n}}\n::\n" +
                        "{{wide\n" + camp + "}}\n::\n" +
                        "{{toc,wide\n" + outtoc + "}}\n::\n"
                        "\n\n## Campaign\n\n" + chap.replace("\\n", "\n"))

        st.write("Copy the content to your files at https://homebrewery.naturalcrit.com/")
