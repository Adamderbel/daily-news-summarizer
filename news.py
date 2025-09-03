import requests
import streamlit as st
import subprocess
import math
from fpdf import FPDF
from datetime import datetime

# ------------------------- PDF Generation -------------------------
def create_pdf(topic, summary, articles):
    pdf = FPDF()
    pdf.add_page()
    
    # Use the built-in 'helvetica' font which supports basic characters
    pdf.set_font("helvetica", size=12)
    
    # Add title
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(200, 10, txt=f"Daily News Summary: {topic.capitalize()}", ln=1, align='C')
    pdf.ln(10)
    
    # Add date
    pdf.set_font("helvetica", 'I', 10)
    pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align='C')
    pdf.ln(15)
    
    # Add summary - clean any special characters first
    clean_summary = summary.encode('latin-1', 'replace').decode('latin-1')
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(200, 10, txt="Summary", ln=1)
    pdf.set_font("helvetica", '', 12)
    pdf.multi_cell(0, 8, txt=clean_summary)
    pdf.ln(10)
    
    # Add articles
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(200, 10, txt="Articles", ln=1)
    pdf.set_font("helvetica", '', 12)
    
    for i, article in enumerate(articles, 1):
        # Clean article text
        clean_title = article['title'].encode('latin-1', 'replace').decode('latin-1')
        clean_summary = article['summary'].encode('latin-1', 'replace').decode('latin-1')
        
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 10, txt=f"{i}. {clean_title}", ln=1)
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 7, txt=clean_summary)
        pdf.set_text_color(0, 0, 255)
        pdf.cell(0, 7, txt=f"Read more: {article['url']}", ln=1, link=article['url'])
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
    
    return pdf.output(dest='S').encode('latin1')
# ------------------------- News API Functions -------------------------
NEWS_API_KEY = "your_news_api_key_here"  # Replace with your key

def fetch_news(topic, page_size=30):
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={topic}&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize={page_size}&"
        f"apiKey={NEWS_API_KEY}"
    )
    response = requests.get(url)
    data = response.json()
    articles = []
    if data["status"] == "ok":
        for item in data["articles"]:
            if item["title"] and item["description"]:
                articles.append({
                    "title": item["title"],
                    "summary": item["description"],
                    "url": item["url"]
                })
    return articles

def summarize_with_ollama(topic, summaries, model="mistral"):
    prompt = (
        f"Create a concise paragraph (4-5 sentences) summarizing the key developments in {topic} today. "
        f"Combine all the news into one coherent summary that captures the main trends and important events. "
        f"Focus on what's most significant and newsworthy. Start with: \"Today's news about {topic} reveals...\"\n\n"
        "Here are the article summaries to analyze:\n"
        + "\n".join([f"- {s}" for s in summaries])
    )
    
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return result.stdout.decode("utf-8").strip()

# ------------------------- Streamlit UI -------------------------
st.set_page_config(page_title="🗞️ Daily News Summarizer", layout="wide")
st.markdown("<h1 style='text-align: center;'>📰 Daily News Summarizer</h1>", unsafe_allow_html=True)

# Session state init
if 'articles' not in st.session_state:
    st.session_state.articles = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'general_summary' not in st.session_state:
    st.session_state.general_summary = ""

# Topic input
with st.container():
    st.markdown("### 🔎 Choose a topic to summarize the latest news")
    topic = st.text_input("Enter a topic (e.g., technology, politics, football):", "technology")

    if st.button("🚀 Fetch News & Generate Summary"):
        with st.spinner("Fetching and summarizing the latest news..."):
            articles = fetch_news(topic)
            if not articles:
                st.error("❌ No articles found. Try a different topic.")
            else:
                st.session_state.articles = articles
                st.session_state.current_page = 1
                summaries = [a["summary"] for a in articles][:20]
                st.session_state.general_summary = summarize_with_ollama(topic, summaries)

# Show the general summary
if st.session_state.general_summary:
    st.markdown("---")
    st.markdown(f"<h3 style='color: #1f77b4;'>📌 Today's News About <em>{topic.capitalize()}</em></h3>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='padding: 10px 5px; font-size: 17px; line-height: 1.6;'>{st.session_state.general_summary}</div>",
        unsafe_allow_html=True
    )

# Show articles
if st.session_state.articles:
    st.markdown("---")
    st.markdown("### 📰 Top Articles")

    articles_per_page = 10
    total_pages = math.ceil(len(st.session_state.articles) / articles_per_page)
    start_idx = (st.session_state.current_page - 1) * articles_per_page
    end_idx = start_idx + articles_per_page

    for i, article in enumerate(st.session_state.articles[start_idx:end_idx], start=start_idx + 1):
        st.markdown(
            f"""
            <div style='padding: 10px 0 20px 0; margin-bottom: 10px;'>
                <strong>{i}. {article['title']}</strong><br><br>
                <span>{article['summary']}</span><br><br>
                <a href="{article['url']}" target="_blank">🔗 Read more</a>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Pagination controls
    if total_pages > 1:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("◀ Previous", disabled=st.session_state.current_page == 1):
                st.session_state.current_page -= 1
        with col2:
            st.markdown(
                f"<div style='text-align: center; font-size: 16px;'>Page {st.session_state.current_page} of {total_pages}</div>",
                unsafe_allow_html=True
            )
        with col3:
            if st.button("Next ▶", disabled=st.session_state.current_page == total_pages):
                st.session_state.current_page += 1

    # Download options
    st.markdown("---")
    st.markdown("### 💾 Download Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download Current Page as PDF"):
            current_articles = st.session_state.articles[
                (st.session_state.current_page - 1)*10 : st.session_state.current_page*10
            ]
            pdf_data = create_pdf(
                topic,
                st.session_state.general_summary,
                current_articles
            )
            st.download_button(
                label="⬇️ Confirm Download (Current Page)",
                data=pdf_data,
                file_name=f"news_summary_{topic}_page_{st.session_state.current_page}.pdf",
                mime="application/pdf"
            )
    
    with col2:
        if st.button("📥 Download All Articles as PDF"):
            pdf_data = create_pdf(
                topic,
                st.session_state.general_summary,
                st.session_state.articles
            )
            st.download_button(
                label="⬇️ Confirm Download (All Articles)",
                data=pdf_data,
                file_name=f"news_summary_{topic}_full.pdf",
                mime="application/pdf"
            )