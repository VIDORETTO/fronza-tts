import streamlit as st

from app.providers.registry import registry
from app.schemas.tts import TTSRequest


def show():
    st.title("⚖️ Comparar Provedores")
    st.caption("Compare a qualidade dos provedores com o mesmo texto.")

    text = st.text_area(
        "Texto curto para comparação",
        height=100,
        placeholder="Digite um texto curto para testar todos os provedores...",
    )

    if st.button("🔊 Testar todos os provedores", type="primary", disabled=not text.strip()):
        if not text.strip():
            st.error("Digite um texto primeiro.")
            return

        providers = registry.list_ids()
        if not providers:
            st.warning("Nenhum provedor registrado.")
            return

        st.subheader("Resultados")

        for pid in providers:
            with st.container(border=True):
                st.markdown(f"### {pid}")

                with st.spinner(f"Gerando com {pid}..."):
                    try:
                        from app.core.fallback_engine import TTSService
                        service = TTSService()
                        request = TTSRequest(
                            text=text,
                            provider_id=pid,
                            force_provider=True,
                            free_only=True,
                        )
                        result = service.generate(request)

                        if result.audio_file_path != "mock_audio.mp3":
                            with open(result.audio_file_path, "rb") as f:
                                audio_bytes = f.read()
                            st.audio(audio_bytes, format=f"audio/{result.output_format}")

                        st.success(f"✅ OK | Caracteres: {len(text)}")
                    except NotImplementedError:
                        st.warning("⏳ Provider não implementado ainda")
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")
