# 🧠 TalentParse

TalentParse is an intelligent resume parsing web app built with **Streamlit**, designed to extract structured information from resumes (PDFs), analyze them using **Google Gemini AI**, and store the data for future access. This application is ideal for HR teams, recruiters, and career portals looking to automate resume screening and candidate evaluation.

---

## 🚀 Features

- 📄 Upload resume PDFs
- 🧠 Extract:
  - Name, Email, Phone
  - Skills
  - Work Experience
  - Projects
  - Hyperlinks
- 🔗 Link classification (GitHub, LinkedIn, Portfolio, etc.)
- 🤖 AI-powered insights using **Gemini**:
  - Suggest suitable job roles
  - Resume feedback
- 🧱 SQLAlchemy-based database to store resumes
- 🗂 Sidebar to view all uploaded resumes
- 🌐 Fully interactive web interface via Streamlit

---

## 🔗 Live App

👉 [TalentParse Streamlit App](https://share.streamlit.io/your-deployment-link)  
_Replace with your actual Streamlit Cloud deployment link_

---

## 👨‍💻 Author

**Neelmani Ramkripalu**  
[LinkedIn](https://www.linkedin.com/in/neelmaniramkripalu/)  
[GitHub](https://github.com/neelmaniramkripalu)

---

## 🛠️ Tech Stack

- Python
- Streamlit
- pdfplumber
- spaCy (NLP)
- SQLAlchemy (ORM)
- SQLite (default DB)
- Google Gemini API
- dotenv
- Pandas

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/TalentParse.git
cd TalentParse
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 5. Create a .env File
Create a .env file in the root directory and add your Gemini API key

```bash
GEMINI_API_KEY=your_google_gemini_api_key
DATABASE_URL=sqlite:///./resumes.db  # or change to your preferred DB

```

### ▶️ Run the App

```bash
streamlit run resume_extractor.py

```
### 📂 Directory Structure

```bash
TalentParse/
├── app.py
├── requirements.txt
├── .env
├── resumes.db  # (auto-created)
├── README.md

```

### 🧪 Sample Usage

Upload a PDF resume → Automatically extract and analyze → View results + AI suggestions → Resume saved in the sidebar table
