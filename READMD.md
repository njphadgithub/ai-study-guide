About The Project

Professors and educators spend countless hours manually summarizing lecture notes, textbooks, and research papers to create study materials for students. This project automates that process, saving valuable time and effort.



This application provides a simple web interface where an educator can upload their course content. The AI then reads and analyzes the text to automatically generate:



Key Topic Summaries: Concise summaries of the main ideas and concepts.



Question-Answer Pairs: Insightful questions and their corresponding answers to test comprehension.



Interactive Flashcards: A modern, flippable flashcard slider to help with memorizing key terms and definitions.



A key feature is the difficulty selector (Beginner, Intermediate, Advanced), which tailors the generated content to the appropriate learning level.



Built With 🛠️

This project is built with the following technologies:



Streamlit - For the web application framework.



Google Gemini API - For the core generative AI capabilities.



Python - The primary programming language.



Pandas - For handling CSV data.



PyPDF - For extracting text from PDF files.



Getting Started

To get a local copy up and running, follow these simple steps.



Prerequisites

Python 3.8 or higher



A Google Gemini API Key. You can get one from Google AI Studio.



Installation

Clone the repository:



Bash



git clone https://github.com/your-username/your-repository-name.git

cd your-repository-name

Create and activate a virtual environment:



Bash



\# For Windows

python -m venv venv

venv\\Scripts\\activate



\# For macOS/Linux

python3 -m venv venv

source venv/bin/activate

Create a requirements.txt file:

Before you can install the dependencies, you need to create this file. Run the following command in your terminal to automatically generate it from your current environment:



Bash



pip freeze > requirements.txt

Now, add this new requirements.txt file to your GitHub repository.



Install the required packages:



Bash



pip install -r requirements.txt

Set up your API Key:



Create a file named .env in the root of your project folder.



Inside the .env file, add your API key like this:



GOOGLE\_API\_KEY="YOUR\_ACTUAL\_API\_KEY\_HERE"

Usage 🚀

Run the Streamlit app:



Bash



streamlit run app.py

Open your web browser and navigate to the local URL provided.



Upload a .pdf, .txt, or .csv file.



Select your desired difficulty level.



Click the "Generate Study Guide" button and wait for the AI to work its magic!

