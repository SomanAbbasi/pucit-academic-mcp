# PUCIT GPA & CGPA Assistant

A conversational AI assistant for PUCIT BS(CS) students to calculate GPA, CGPA, required GPA, and view semester courses and credit hours.

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate it on Windows:

```bash
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install langchain langchain-groq python-dotenv streamlit
```

4. Create a `.env` file and add your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key
```

5. Run the application:

```bash
streamlit run app.py
```
