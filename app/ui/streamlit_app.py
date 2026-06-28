import streamlit as st

st.set_page_config(
    page_title="Fronza TTS",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.core.config import config
from app.db.init_db import init_database
from app.db.repositories import api_key_repo

init_database()

import app.providers.elevenlabs  # noqa: F401
import app.providers.cartesia  # noqa: F401
import app.providers.smallest  # noqa: F401
import app.providers.gemini  # noqa: F401
import app.providers.inworld  # noqa: F401
import app.providers.async_voice  # noqa: F401

from app.providers.registry import registry
from app.ui.pages._1_generate import show as gen
from app.ui.pages._2_limits import show as limits
from app.ui.pages._3_providers import show as providers
from app.ui.pages._4_history import show as history
from app.ui.pages._5_compare import show as compare

gen_page = st.Page(gen, title="Gerar Áudio", icon="🎙️", url_path="generate", default=True)
limits_page = st.Page(limits, title="Limites e Cotas", icon="📊", url_path="limits")
providers_page = st.Page(providers, title="Provedores", icon="🔌", url_path="providers")
history_page = st.Page(history, title="Histórico", icon="📜", url_path="history")
compare_page = st.Page(compare, title="Comparar", icon="⚖️", url_path="compare")

pg = st.navigation([gen_page, limits_page, providers_page, history_page, compare_page])

st.sidebar.title("🎤 Fronza TTS")
st.sidebar.caption("Gerenciador inteligente de TTS multi-API")

mode = "🛡️ Gratuito" if config.app.free_only_mode else "⚠️ Permitir pagos"
st.sidebar.info(f"Modo: **{mode}**")

st.sidebar.divider()
st.sidebar.markdown("### API Keys")

for pid in registry.list_ids():
    keys = api_key_repo.get_by_provider(pid)
    if keys:
        st.sidebar.success(f"✅ {pid}")
    else:
        st.sidebar.warning(f"❌ {pid}")

pg.run()
