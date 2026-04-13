import streamlit as st
import anthropic
import feedparser
import folium
from streamlit_folium import st_folium
import json

# Configuration de la page
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
        
        # Récupération des news
        feeds = ["https://www.theguardian.com/world/rss", "https://www.lemonde.fr/international/rss_full.xml"]
        titles = []
        for url in feeds:
            f = feedparser.parse(url)
            for entry in f.entries[:5]:
                titles.append(entry.title)

        @st.cache_data(ttl=600)
        def get_analysis(news_list):
            # Liste des noms de modèles à tester par ordre de priorité
            models_to_try = ["claude-3-haiku-20240307", "claude-3-5-sonnet-latest", "claude-3-5-sonnet-20240620"]
            
            last_err = ""
            for model_name in models_to_try:
                try:
                    prompt = f"Analyse ces titres et renvoie UNIQUEMENT un JSON (liste d'objets) avec: pays, lat, lng, cause, population. Titres: {news_list}"
                    message = client.messages.create(
                        model=model_name,
                        max_tokens=1000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return message.content[0].text
                except Exception as e:
                    last_err = str(e)
                    continue # On essaie le modèle suivant
            raise Exception(f"Aucun modèle n'a répondu. Dernière erreur : {last_err}")

        response_text = get_analysis(". ".join(titles))
        
        # Nettoyage JSON
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        clean_json = response_text[start:end]
        conflicts = json.loads(clean_json)

        # Création de la carte
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
        for c in conflicts:
            popup_text = f"<b>{c['pays']}</b><br>Cause: {c['cause']}<br>Population: {c.get('population', 'N/A')}"
            folium.Marker(
                location=[float(c['lat']), float(c['lng'])],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color='red', icon='fire', prefix='fa')
            ).add_to(m)

        st_folium(m, width="100%", height=600)
        st.write("### Détails des analyses de l'IA :")
        st.table(conflicts)

    except Exception as e:
        st.error(f"Erreur technique : {e}")
        st.info("💡 Si l'erreur est '404', c'est qu'Anthropic n'a pas encore activé les modèles pour votre nouvelle clé. Réessayez dans 15-30 minutes sans rien toucher.")
