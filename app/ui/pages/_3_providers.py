import streamlit as st

from app.db.repositories import api_key_repo, provider_repo
from app.db.models import Provider
from app.providers.registry import registry
from app.utils.security import encrypt_value, mask_api_key


def show():
    st.title("🔌 Provedores")
    st.caption("Gerencie as configurações de cada provedor de TTS.")

    provider_ids = ["elevenlabs", "cartesia", "smallest", "gemini", "inworld", "async_voice"]

    for pid in provider_ids:
        db_provider = provider_repo.get(pid)
        has_key = api_key_repo.has_key(pid)
        keys = api_key_repo.get_by_provider(pid)

        with st.expander(f"**{pid.upper()}**", expanded=True):
            cols = st.columns([1, 1, 1])

            with cols[0]:
                st.markdown(f"**Status:** {'✅ Ativo' if has_key else '❌ Sem chave'}")
                if db_provider:
                    st.markdown(f"**Prioridade:** {db_provider.priority}")

            with cols[1]:
                if keys:
                    masked = mask_api_key(keys[0].encrypted_value)
                    st.markdown(f"**API Key:** `{masked}`")
                if db_provider:
                    st.markdown(f"**Reset:** `{db_provider.reset_policy}`")

            with cols[2]:
                if db_provider:
                    st.markdown(f"**Cota:** `{db_provider.quota_source}`")
                    if db_provider.last_error:
                        st.error(f"Último erro: {db_provider.last_error}")

            col_key, col_actions = st.columns([2, 1])

            with col_key:
                new_key = st.text_input(
                    f"Nova chave de API",
                    type="password",
                    placeholder="Cole a chave aqui...",
                    key=f"key_{pid}",
                    label_visibility="collapsed",
                )
                if new_key:
                    encrypted = encrypt_value(new_key)
                    api_key_repo.save(pid, encrypted)
                    st.success(f"✅ Chave salva para {pid}!")
                    st.rerun()

            with col_actions:
                if has_key:
                    if st.button(f"🗑️ Remover", key=f"del_{pid}", use_container_width=True):
                        api_key_repo.delete(pid)
                        st.rerun()

                    if st.button(f"🔍 Testar", key=f"test_{pid}", use_container_width=True):
                        with st.spinner(f"Testando {pid}..."):
                            adapter = registry.get(pid)
                            if adapter:
                                try:
                                    models = adapter.list_models()
                                    if models:
                                        st.success(f"✅ OK! {len(models)} modelos")
                                    else:
                                        st.warning("⚠️ Sem modelos retornados")
                                except NotImplementedError:
                                    st.warning("⏳ Provedor não implementado")
                                except Exception as e:
                                    st.error(f"❌ {e}")
                            else:
                                st.warning("⏳ Provider não registrado")

            st.divider()
