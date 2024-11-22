import random
import re
import streamlit as st
import os
from langchain_community.chat_models.openai import ChatOpenAI
from langchain.prompts import PromptTemplate

# Constants
os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']
MODEL = "gpt-4o"
EXERCISES = [
    "Walk me through what a typical weekend looks like for you.",
    "Tell me about a time you tried something new and how it went.",
    "What does your ideal day off look like, from start to finish?",
    "Describe what your mornings are usually like.",
    "How did you spend your holiday, and what moments stood out the most?"
]

# Streamlit page config
st.set_page_config(page_title="Language Learning App", page_icon=":books:")

# Function to highlight marked incorrect words with red strikethrough
def highlight_incorrect(original, incorrect_words):
    highlighted_text = original
    for word in incorrect_words:
        highlighted_text = re.sub(rf'\b{re.escape(word)}\b', f'<span style="color: red; text-decoration: line-through;">{word}</span>', highlighted_text)
    return highlighted_text

# Function to make corrected words green
def highlight_corrected(corrected):
    highlighted_corrected = re.sub(r"\{(.*?)\}", r"<span style='color: green; font-weight: bold;'>\1</span>", corrected)
    return highlighted_corrected

# Initialize chain only once
@st.cache_resource
def initialize_qa_chain():
    llm = ChatOpenAI(model_name=MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)
    prompt = PromptTemplate(
        input_variables=["user_answer"],
        template="""
        You are a language tutor. Please analyze the following answer given by the user:

        User's Answer: {user_answer}

        1. Identify all incorrect words or phrases in the user's answer by surrounding them with double curly braces {{like this}}.
        2. Provide a corrected answer to improve grammar, vocabulary, and sentence structure, changing only the identified incorrect parts. Highlight corrected parts by surrounding them with double curly braces {{like this}}.
        3. Write a short feedback with constructive advice on how the user could improve their response.

        Example:
        User's Answer: I goed to the market yesterday.
        Marked Incorrect Words: I {{goed}} to the market yesterday.
        Corrected Answer: I {{went}} to the market yesterday.
        Feedback: The word "goed" is incorrect. Use the correct past tense "went".

        Marked Incorrect Words:
        Corrected Answer:
        Feedback:"""
    )
    return prompt | llm

# Initialize session state variables
if 'chain' not in st.session_state:
    st.session_state['chain'] = initialize_qa_chain()
if 'exercise' not in st.session_state:
    st.session_state['exercise'] = random.choice(EXERCISES)
if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False

# Main UI
st.title("Language Learning App")
st.markdown("### Practice and improve your language skills with personalized feedback.")

# Show the exercise if one is set
st.write("#### Your Exercise:")
st.write(st.session_state['exercise'])

# Text area for user's response
user_answer = st.text_area("Your response:", key='user_response', height=100, disabled=st.session_state['submitted'], value='' if st.session_state['submitted'] else st.session_state.get('user_response', ''))

# Conditional display of buttons based on whether the answer is submitted or not
if not st.session_state['submitted']:
    # Show "Submit Answer" button
    if st.button("Submit Answer"):
        # Run the chain to get corrected answer and feedback
        with st.spinner("Analyzing your answer..."):
            try:
                # Call the agent with the user’s answer
                response = st.session_state['chain'].invoke({"user_answer": user_answer})

                # Extract and process the response, with error handling
                try:
                    answer_text = response.content

                    # Parse the answer text to separate marked incorrect words, corrected answer, and feedback
                    if "Marked Incorrect Words:" in answer_text and "Corrected Answer:" in answer_text and "Feedback:" in answer_text:
                        marked_incorrect = answer_text.split("Marked Incorrect Words:")[1].split("Corrected Answer:")[0].strip()
                        corrected_answer = answer_text.split("Corrected Answer:")[1].split("Feedback:")[0].strip()
                        feedback = answer_text.split("Feedback:")[1].strip()
                    else:
                        marked_incorrect = "Marked incorrect words data missing."
                        corrected_answer = "Correction data missing."
                        feedback = "Feedback data missing."

                    # Extract and format the marked incorrect words
                    incorrect_words = re.findall(r"\{(.*?)\}", marked_incorrect)
                    highlighted_original = highlight_incorrect(user_answer, incorrect_words)

                    # Highlight corrections in the corrected answer
                    highlighted_corrected = highlight_corrected(corrected_answer)

                    # Corrected version for displaying highlighted text consistently
                    st.markdown("### Feedback")

                    # Highlight User Answer (with corrections)
                    st.markdown("**Your Answer (with corrections):**", unsafe_allow_html=True)
                    st.markdown(f"<div>{highlighted_original}</div>",
                                unsafe_allow_html=True)  # Wrap it in a div for safe HTML handling

                    # Highlight Corrected Answer
                    st.markdown("**Corrected Version:**", unsafe_allow_html=True)
                    st.markdown(f"<div>{highlighted_corrected}</div>",
                                unsafe_allow_html=True)  # Corrected parts in green and bold

                    # Display Feedback
                    st.markdown(f"**Feedback:** {feedback}", unsafe_allow_html=True)

                    # Mark as submitted so that the "Next Question" button appears
                    st.session_state['submitted'] = True

                except Exception as parse_error:
                    st.error(f"Error parsing the response: {parse_error}")
            except Exception as e:
                st.error(f"Error generating feedback: {e}")

if st.session_state['submitted']:
    # Show "Next Question" button at the bottom after the answer is submitted
    if st.button("Next Question"):
        # Reset the state for the next question
        st.session_state['exercise'] = random.choice(EXERCISES)
        st.session_state['submitted'] = False
        st.experimental_set_query_params(_=random.random())  # Reload the page to show the next question
