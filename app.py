import streamlit as st
import anthropic
import feedparser
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(layout="wide", page_title="Monde : Edition Deluxe")

with st.sidebar:
    st.title("🛡️ Mode Premium")
    # On change encore la clé interne pour forcer un reset total
    api_key = st.text_input("Clé API (vérifiée Workbench) :", type="password", key="ultra_key_reset")

if not api_key:
    st.info("En attente de la clé API pour activer la carte...")
else:
    try:
        client = anthropic.Anthropic(api_key=api_key)
        st.title("🌍 Carte Interactive des Points Chauds (Mode Opus)")
        
        # Récupération News
        feeds = ["https://www.theguardian.com/world/rss", "https://www.lemonde.fr/international/rss_full.xml"]
        titles = []
        for url in feeds:
            f = feedparser.parse(url)
            for entry in f.entries[:10]:
                titles.append(entry.title)

        @st.cache_data(ttl=10) # Presque pas de cache pour être en temps réel
        def get_analysis_premium(news_list, key):
            # Priorité à OPUS (le plus cher/robuste)
            models = ["claude-3-opus-20240229", "claude-3-5-sonnet-20240620", "claude-3-haiku-20240307"]
            
            last_err = ""
            for model_name in models:
                try:
                    prompt = f"Analyse ces titres de presse et identifie les zones de tension. Renvoie UNIQUEMENT un JSON (liste d'objets) avec les clés: pays, lat, lng, cause, population. Titres: {news_list}"
                    message = client.messages.create(
                        model=model_name,
                        max_tokens=2000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return message.content[0].text, model_name
                except Exception as e:
                    last_err = str(e)
                    continue
            raise Exception(f"Échec global. Anthropic renvoie : {last_err}")

        # Exécution
        with st.spinner('Claude Opus analyse les données mondiales...'):
            response_text, model_used = get_analysis_premium(". ".join(titles), api_key)
        
        # Extraction JSON
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        conflicts = json.loads(response_text[start:end])

        # Interface
        st.success(f"Analyse réussie avec le modèle : {model_used}")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
            for c in conflicts:
                folium.Marker(
                    location=[float(c['lat']), float(c['lng'])],
                    popup=f"<b>{c['pays']}</b><br>{c['cause']}",
                    icon=folium.Icon(color='red', icon='bolt', prefix='fa')
                ).add_to(m)
            st_folium(m, width="100%", height=600)

        with col2:
            st.write("### Focus IA")
            st.write(conflicts)

    except Exception as e:
        st.error(f"Erreur d'accès : {e}")
        st.warning("Si vous voyez 404, c'est que votre clé ne possède pas encore les droits 'développeur' complets malgré le paiement.")
