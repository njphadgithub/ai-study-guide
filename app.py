import os
import streamlit as st
import pandas as pd
from pypdf import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv
import json
from bs4 import BeautifulSoup

# --- STAGE 1: SETUP AND CONFIGURATION ---

# Load environment variables
load_dotenv()

# Configure the Gemini API
try:
    api_key = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))
    if not api_key:
        st.error("Google API Key not found. Please set it in your .env file or Streamlit secrets.")
        st.stop()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro-preview-03-25') # Using a modern, powerful model
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}")
    st.stop()

# --- STAGE 2: DATA INGESTION & TEXT PROCESSING ---

def get_text_from_file(uploaded_file):
    text = ""
    file_extension = os.path.splitext(uploaded_file.name)[1]
    if file_extension == ".pdf":
        pdf_reader = PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    elif file_extension == ".txt":
        text = uploaded_file.read().decode("utf-8")
    elif file_extension == ".csv":
        df = pd.read_csv(uploaded_file)
        text = ' '.join(df.astype(str).apply(lambda x: ' '.join(x), axis=1))
    return text

def chunk_text(text, chunk_size=3000):
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 1 < chunk_size:
            current_chunk += paragraph + "\n"
        else:
            chunks.append(current_chunk)
            current_chunk = paragraph + "\n"
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

# --- NEW HELPER FUNCTION TO PARSE FLASHCARDS ---

def parse_flashcards(raw_text):
    """Parses raw text from Gemini into a list of flashcard dictionaries."""
    flashcards = []
    # Using BeautifulSoup to handle potentially messy AI output
    soup = BeautifulSoup(f"<div>{raw_text}</div>", 'html.parser')
    text_lines = soup.get_text().strip().split('\n')
    
    term = None
    definition = None
    for line in text_lines:
        line = line.strip()
        if line.lower().startswith("term:"):
            if term and definition: # Save the previous card
                flashcards.append({"term": term, "definition": definition})
            term = line[5:].strip()
            definition = None
        elif line.lower().startswith("definition:"):
            if term:
                definition = line[11:].strip()
    
    if term and definition: # Add the last card
        flashcards.append({"term": term, "definition": definition})
        
    return flashcards


# --- STAGE 3: AI CONTENT GENERATION ---

PROMPTS = {
    # Prompts for summary and qa remain the same
    "summary": {
        "Beginner": "Explain the main points of this text in simple, easy-to-understand language...\n\nText: \"\"\"{text}\"\"\"",
        "Intermediate": "Provide a detailed summary covering the key arguments...\n\nText: \"\"\"{text}\"\"\"",
        "Advanced": "Create a critical summary for a graduate-level audience...\n\nText: \"\"\"{text}\"\"\""
    },
    "qa": {
        "Beginner": "Generate basic factual questions and answers...\n\nText: \"\"\"{text}\"\"\"",
        "Intermediate": "Generate questions that require understanding relationships...\n\nText: \"\"\"{text}\"\"\"",
        "Advanced": "Generate challenging questions that require critical thinking...\n\nText: \"\"\"{text}\"\"\""
    },
    # Updated flashcard prompt for cleaner output
    "flashcards": {
        "Beginner": "Identify 5-7 fundamental terms from this text. For each, provide a 'Term:' on one line and a 'Definition:' on the next, suitable for a beginner.\n\nText: \"\"\"{text}\"\"\"",
        "Intermediate": "Identify 5-7 important technical terms from this text. For each, provide a 'Term:' on one line and a 'Definition:' on the next, suitable for a college student.\n\nText: \"\"\"{text}\"\"\"",
        "Advanced": "Identify 5-7 nuanced or highly technical terms from this text. For each, provide a 'Term:' on one line and a 'Definition:' on the next, suitable for an expert.\n\nText: \"\"\"{text}\"\"\""
    }
}

def generate_content_with_gemini(text_chunks, generation_type, difficulty, progress_bar):
    full_response = ""
    prompt_template = PROMPTS[generation_type][difficulty]
    
    for i, chunk in enumerate(text_chunks):
        prompt = prompt_template.format(text=chunk)
        try:
            response = model.generate_content(prompt)
            full_response += response.text + "\n\n"
        except Exception as e:
            full_response += f"Error processing a chunk: {e}\n\n"
        progress_bar.progress((i + 1) / len(text_chunks))
    return full_response

# --- NEW INTERACTIVE FLASHCARD COMPONENT ---
def flashcard_component(flashcards_data):
    """A custom component to display interactive, flippable flashcards."""
    
    # Convert Python list of dicts to a JSON string to pass to JavaScript
    flashcards_json = json.dumps(flashcards_data)
    
    component_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            /* General styling for the container */
            .flashcard-container {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 1rem;
            }}
            /* The scene for the 3D effect */
            .scene {{
                width: 100%;
                max-width: 500px;
                height: 280px;
                perspective: 600px;
                margin-bottom: 1rem;
            }}
            /* The card itself, which flips */
            .card {{
                width: 100%;
                height: 100%;
                position: relative;
                cursor: pointer;
                transition: transform 0.8s;
                transform-style: preserve-3d;
                border-radius: 20px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .card.is-flipped {{
                transform: rotateY(180deg);
            }}
            /* Front and back faces of the card */
            .card__face {{
                position: absolute;
                width: 100%;
                height: 100%;
                backface-visibility: hidden;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 20px;
                box-sizing: border-box;
                border-radius: 20px;
                font-size: 1.25rem;
                text-align: center;
            }}
            .card__face--front {{
                background: white;
                border: 1px solid #ddd;
            }}
            .card__face--back {{
                background: #f0f2f6;
                border: 1px solid #ddd;
                transform: rotateY(180deg);
            }}
            .term-title {{
                font-weight: bold;
                font-size: 1.5rem;
                color: #333;
            }}
            .definition-text {{
                font-size: 1.1rem;
                color: #555;
            }}
            /* Navigation controls */
            .navigation {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                width: 100%;
                max-width: 500px;
            }}
            .nav-button {{
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1rem;
                transition: background-color 0.3s;
            }}
            .nav-button:hover {{
                background-color: #0056b3;
            }}
            .nav-button:disabled {{
                background-color: #cccccc;
                cursor: not-allowed;
            }}
            #card-counter {{
                font-size: 1rem;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="flashcard-container">
            <div class="scene">
                <div class="card" id="flashcard">
                    <div class="card__face card__face--front" id="card-front"></div>
                    <div class="card__face card__face--back" id="card-back"></div>
                </div>
            </div>
            <div class="navigation">
                <button class="nav-button" id="prevBtn">Previous</button>
                <span id="card-counter"></span>
                <button class="nav-button" id="nextBtn">Next</button>
            </div>
        </div>

        <script>
            const flashcards = {flashcards_json};
            let currentIndex = 0;

            const cardElement = document.getElementById('flashcard');
            const cardFront = document.getElementById('card-front');
            const cardBack = document.getElementById('card-back');
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            const cardCounter = document.getElementById('card-counter');

            function showCard(index) {{
                if (flashcards.length === 0) return;
                const card = flashcards[index];
                cardFront.innerHTML = `<div class="term-title">${{card.term}}</div>`;
                cardBack.innerHTML = `<div class="definition-text">${{card.definition}}</div>`;
                
                // Reset flip state
                cardElement.classList.remove('is-flipped');
                
                // Update counter and button states
                cardCounter.textContent = `${{index + 1}} / ${{flashcards.length}}`;
                prevBtn.disabled = index === 0;
                nextBtn.disabled = index === flashcards.length - 1;
            }}

            // Flip card on click
            cardElement.addEventListener('click', () => {{
                cardElement.classList.toggle('is-flipped');
            }});

            // Navigation
            prevBtn.addEventListener('click', () => {{
                if (currentIndex > 0) {{
                    currentIndex--;
                    showCard(currentIndex);
                }}
            }});

            nextBtn.addEventListener('click', () => {{
                if (currentIndex < flashcards.length - 1) {{
                    currentIndex++;
                    showCard(currentIndex);
                }}
            }});

            // Initial load
            showCard(currentIndex);
        </script>
    </body>
    </html>
    """
    return st.components.v1.html(component_html, height=400)

# --- STAGE 4: STREAMLIT USER INTERFACE ---

st.set_page_config(page_title="AI Study Guide By Prof Nitin Phadkule", layout="wide")

st.title("🧑‍🏫 AI Study Guide By Prof Nitin Phadkule, Govt College of Engineering, Aurangabad, Chh. Sambhajinagar")
st.write("Upload course material to generate study aids at your chosen difficulty level.")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("Choose a file (PDF, TXT, or CSV)", type=["pdf", "txt", "csv"])
with col2:
    difficulty = st.selectbox("Select Difficulty Level", ("Beginner", "Intermediate", "Advanced"))

if uploaded_file is not None:
    if st.button(f"Generate {difficulty} Study Guide"):
        with st.spinner("Reading and processing file..."):
            raw_text = get_text_from_file(uploaded_file)
            if not raw_text.strip():
                st.error("Could not extract text from the file.")
            else:
                text_chunks = chunk_text(raw_text)

                st.info("Generating content... This may take a moment.")
                # Create progress bars inside a container
                progress_container = st.container()
                summary_progress = progress_container.progress(0, text="Summaries...")
                summaries = generate_content_with_gemini(text_chunks, "summary", difficulty, summary_progress)

                qa_progress = progress_container.progress(0, text="Q&A...")
                qa_pairs = generate_content_with_gemini(text_chunks, "qa", difficulty, qa_progress)
                
                flashcard_progress = progress_container.progress(0, text="Flashcards...")
                flashcards_raw = generate_content_with_gemini(text_chunks, "flashcards", difficulty, flashcard_progress)
                
                # Parse the raw text into a structured list
                parsed_flashcards = parse_flashcards(flashcards_raw)
                
                st.success("✅ Study Guide Generated!")

                tab1, tab2, tab3 = st.tabs(["Key Summaries", "Question & Answer", "Flashcards"])
                with tab1:
                    st.markdown(summaries)
                with tab2:
                    st.markdown(qa_pairs)
                with tab3:
                    if parsed_flashcards:
                        # 
                        flashcard_component(parsed_flashcards)
                    else:
                        st.warning("Could not parse flashcards from the generated text. Displaying raw text instead.")
                        st.markdown(flashcards_raw)