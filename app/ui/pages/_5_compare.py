import streamlit as st

from app.db.repositories import api_key_repo, generation_repo
from app.providers.registry import registry
from app.schemas.tts import TTSRequest
from app.ui.components.quota_badge import fallback_timeline


def show():
    st.title("⚖️ Comparar Provedores")
    st.caption("Compare a qualidade dos provedores com o mesmo texto.")

    lang = st.selectbox("Idioma", ["pt-BR", "en", "es", "fr", "de", "it", "ja"], index=0)

    text = st.text_area(
        "Texto curto para comparação",
        height=120,
        placeholder="Digite um texto curto para testar todos os provedores...",
    )

    available = []
    for pid in registry.list_ids():
        has_key = api_key_repo.has_key(pid)
        adapter = registry.get(pid)
        if adapter:
            supports = adapter.supports_language(lang) if has_key else False
        else:
            supports = False
        available.append((pid, has_key, supports))

    st.caption(f"Provedores disponíveis: {sum(1 for _, h, s in available if h and s)}/{len(available)}")

    if st.button("🔊 Testar todos", type="primary", disabled=not text.strip(), use_container_width=True):
        if not text.strip():
            st.error("Digite um texto primeiro.")
            return

        st.subheader("Resultados")

        for pid, has_key, supports in available:
            if not has_key:
                continue
            if not supports:
                continue

            with st.container(border=True):
                st.markdown(f"### {pid}")

                with st.spinner(f"Gerando..."):
                    try:
                        from app.core.fallback_engine import TTSService
                        service = TTSService()
                        request = TTSRequest(
                            text=text,
                            language=lang,
                            provider_id=pid,
                            force_provider=True,
                            free_only=True,
                        )
                        result = service.generate(request)

                        import os
                        if os.path.exists(result.audio_file_path):
                            with open(result.audio_file_path, "rb") as f:
                                audio_bytes = f.read()
                            st.audio(audio_bytes, format=f"audio/{result.output_format}")

                        col1, col2 = st.columns(2)
                        col1.success(f"✅ OK")
                        col2.metric("Caracteres", len(text))

                        if result.model_id:
                            st.caption(f"Modelo: {result.model_id} | Voz: {result.voice_id or 'padrão'}")

                    except Exception as e:
                        st.error(f"❌ {e}")
