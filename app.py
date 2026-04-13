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
            for entry in f.entries[:8]: # On prend un peu plus de news
                titles.append(entry.title)

        @st.cache_data(ttl=600)
        def get_analysis(news_list):
            # ON TESTE LES NOMS LES PLUS STANDARDS POSSIBLES
            models_to_try = [
                "claude-3-5-sonnet-latest", 
                "claude-3-haiku-20240307", 
                "claude-3-sonnet-20240229"
            ]
            
            last_err = ""
            for model_name in models_to_try:
                try:
                    message = client.messages.create(
                        model=model_name,
                        max_tokens=1000,
                        messages=[{"role": "user", "content": f"Analyse ces titres et renvoie UNIQUEMENT un JSON (liste d'objets) avec: pays, lat, lng, cause, population. Titres: {news_list}"}]
                    )
                    return message.content[0].text
                except Exception as e:
                    last_err = str(e)
                    continue
            raise Exception(f"Aucun modèle n'a répondu. Dernière erreur : {last_err}")

        response_text = get_analysis(". ".join(titles))
        
        # Nettoyage et affichage
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        conflicts = json.loads(response_text[start:end])

        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
        for c in conflicts:
            popup_html = f"<b>{c['pays']}</b><br><b>Cause:</b> {c['cause']}<br><b>Démographie:</b> {c.get('population', 'N/A')}"
            folium.Marker(
                location=[float(c['lat']), float(c['lng'])],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
            ).add_to(m)

        st_folium(m, width="100%", height=600)
        st.write("### 🔍 Détails par pays :")
        st.table(conflicts)

    except Exception as e:
        st.error(f"Erreur technique : {e}")
