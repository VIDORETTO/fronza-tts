import streamlit as st

st.set_page_config(
    page_title="TTS Fallback App",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.core.config import config
from app.db.init_db import init_database
from app.db.repositories import api_key_repo, provider_repo
from app.utils.logging import logger
from app.utils.security import mask_api_key

init_database()

# Import all providers to register them
import app.providers.elevenlabs  # noqa: F401
import app.providers.cartesia  # noqa: F401
import app.providers.smallest  # noqa: F401
import app.providers.gemini  # noqa: F401
import app.providers.inworld  # noqa: F401
import app.providers.async_voice  # noqa: F401

from app.providers.registry import registry

st.sidebar.title("🎤 TTS Fallback App")
st.sidebar.caption("Gerenciador inteligente de TTS multi-API")

mode = "🛡️ Gratuito" if config.app.free_only_mode else "⚠️ Permitir pagos"
st.sidebar.info(f"Modo: **{mode}**")

page = st.sidebar.radio(
    "Navegação",
    ["Gerar Áudio", "Limites e Cotas", "Provedores", "Histórico", "Comparar"],
)

st.sidebar.divider()
st.sidebar.markdown("### API Keys")

for pid in registry.list_ids():
    keys = api_key_repo.get_by_provider(pid)
    if keys:
        st.sidebar.success(f"✅ {pid}: configurada")
    else:
        st.sidebar.warning(f"❌ {pid}: não configurada")

if page == "Gerar Áudio":
    from app.ui.pages._1_generate import show as g
    g()
elif page == "Limites e Cotas":
    from app.ui.pages._2_limits import show as l
    l()
elif page == "Provedores":
    from app.ui.pages._3_providers import show as p
    p()
elif page == "Histórico":
    from app.ui.pages._4_history import show as h
    h()
elif page == "Comparar":
    from app.ui.pages._5_compare import show as c
    c()
