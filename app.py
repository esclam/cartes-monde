import streamlit as st
import anthropic
import feedparser
import pandas as pd
import folium
from streamlit_folium import st_folium

# Configuration de la page
st.set_page_config(layout="wide", page_title="Monde : Conflits & Ethnies")

# BARRE LATÉRALE : Ta Clé API
with st.sidebar:
    st.title("Configuration")
    api_key = st.text_input("Entre ta clé API Claude ici :", type="password")
    st.info("Tes 6$ de crédit seront utilisés ici pour analyser les news.")

if not api_key:
    st.warning("Veuillez entrer votre clé API pour activer la carte.")
else:
    client = anthropic.Anthropic(api_key=api_key)

    st.title("🌍 Carte Interactive des Points Chauds")
    
    # 1. Récupération des news
    feeds = ["https://www.theguardian.com/world/rss", "https://www.lemonde.fr/international/rss_full.xml"]
    all_titles = []
    for url in feeds:
        f = feedparser.parse(url)
        all_titles.extend([e.title for e in f.entries[:8]])

    # 2. Analyse Claude (Haiku pour économiser tes crédits)
    @st.cache_data(ttl=3600) # Garde en mémoire pendant 1h pour ne pas repayer
    def get_ai_analysis(titles):
        prompt = f"Analyse ces titres et renvoie UNIQUEMENT un tableau CSV avec 5 colonnes : Pays | Latitude | Longitude | Cause_Conflit | Ethnies_Religions. Titres: {titles}"
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    try:
        raw_data = get_ai_analysis(", ".join(all_titles))
        
        # 3. Affichage de la Carte
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
        
        # Ici on simule l'affichage des points (dans la version finale on parse le CSV)
        st_folium(m, width=1200, height=500)
        
        st.subheader("Analyse détaillée par zone")
        st.write(raw_data) # Affiche le texte de Claude

    except Exception as e:
        st.error(f"Erreur : {e}")
