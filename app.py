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
        
        feeds = ["https://www.theguardian.com/world/rss", "https://www.lemonde.fr/international/rss_full.xml"]
        titles = []
        for url in feeds:
            f = feedparser.parse(url)
            for entry in f.entries[:5]:
                titles.append(entry.title)

        @st.cache_data(ttl=600)
        def get_analysis(news_list):
            # ON UTILISE LE NOM DE MODÈLE PLUS SIMPLE ICI
            prompt = f"Analyse ces titres et renvoie UNIQUEMENT un JSON (liste d'objets) avec: pays, lat, lng, cause, population. Titres: {news_list}"
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620", # Modèle plus récent et très fiable
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text

        response_text = get_analysis(". ".join(titles))
        
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        clean_json = response_text[start:end]
        conflicts = json.loads(clean_json)

        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
        for c in conflicts:
            popup_text = f"<b>{c['pays']}</b><br>Cause: {c['cause']}<br>Population: {c.get('population', 'N/A')}"
            folium.Marker(
                location=[float(c['lat']), float(c['lng'])],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color='red')
            ).add_to(m)

        st_folium(m, width="100%", height=600)
        st.write("### Détails des analyses de l'IA :")
        st.table(conflicts)

    except Exception as e:
        # Si Sonnet ne marche pas non plus, on essaie une version encore plus basique
        st.error(f"Erreur technique : {e}")
        st.info("Tentative de reconnexion au modèle Claude...")
