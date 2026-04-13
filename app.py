import streamlit as st
import anthropic
import feedparser
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(layout="wide", page_title="Monde : Conflits & Ethnies")

with st.sidebar:
    st.title("Configuration")
    api_key = st.text_input("Entre ta clé API Claude ici :", type="password")

if not api_key:
    st.warning("Veuillez entrer votre clé API.")
else:
    try:
        client = anthropic.Anthropic(api_key=api_key)
        st.title("🌍 Carte Interactive des Points Chauds")
        
        # News
        feeds = ["https://www.theguardian.com/world/rss", "https://www.lemonde.fr/international/rss_full.xml"]
        titles = []
        for url in feeds:
            f = feedparser.parse(url)
            for entry in f.entries[:5]:
                titles.append(entry.title)

        @st.cache_data(ttl=600)
        def get_analysis(news_list):
            prompt = f"Analyse ces titres et renvoie UNIQUEMENT un JSON (liste d'objets) avec: pays, lat, lng, cause, population. Titres: {news_list}"
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text

        response_text = get_analysis(". ".join(titles))
        
        # Nettoyage du JSON au cas où Claude ajoute du texte
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        conflicts = json.loads(response_text[start:end])

        # Carte
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
        for c in conflicts:
            folium.Marker(
                location=[c['lat'], c['lng']],
                popup=f"<b>{c['pays']}</b><br>Cause: {c['cause']}<br>Ethnies/Religions: {c.get('population', 'N/A')}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

        st_folium(m, width="100%", height=500)
        st.write("### Dernières analyses de Claude :", conflicts)

    except Exception as e:
        st.error(f"Erreur technique : {e}")
        st.info("Si l'erreur parle de 'credit balance', attends encore 10min, Anthropic est lent à activer les nouveaux comptes.")
