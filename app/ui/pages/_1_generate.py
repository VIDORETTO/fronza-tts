import streamlit as st
from app.core.config import config
from app.providers.registry import registry
from app.schemas.tts import TTSRequest
from app.ui.components.quota_badge import fallback_timeline, quota_badge, reset_badge, warning_box


def show():
    st.title("🎙️ Gerar Áudio")
    st.caption("Digite o texto e escolha as configurações para gerar áudio via TTS.")

    mode_msg = (
        "🛡️ **Modo gratuito ativo.** O app nunca usará provedores pagos automaticamente."
        if config.app.free_only_mode
        else "⚠️ **Modo pago ativo.** O app pode usar provedores com cobrança. Cuidado com gastos!"
    )
    st.markdown(warning_box(mode_msg, "info" if config.app.free_only_mode else "warning"), unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col1:
        text = st.text_area(
            "Texto para converter em fala",
            height=200,
            placeholder="Cole ou digite o texto aqui...",
        )

        char_count = len(text)
        if char_count > 0:
            col_c1, col_c2, col_c3 = st.columns(3)
            col_c1.metric("Caracteres", char_count)
            col_c2.metric("Máx. recomendado", config.app.max_text_chars_warning)

            if char_count > config.app.max_text_chars_warning:
                st.warning(f"⚠️ Texto grande ({char_count} caracteres). O texto será dividido em chunks.")

    with col2:
        language = st.selectbox(
            "Idioma",
            ["Auto", "pt-BR", "en", "es", "fr", "de", "it", "ja"],
            index=1,
        )

        provider_options = ["Automático (fallback)"] + registry.list_ids()
        provider_choice = st.selectbox("Provedor", provider_options, index=0)

        output_format = st.selectbox("Formato", ["mp3", "wav", "ogg"], index=0)

    with st.expander("⚙️ Configurações avançadas"):
        speed = st.slider("Velocidade", 0.5, 2.0, 1.0, 0.1)
        model_id = st.text_input("Modelo (opcional)", placeholder="Deixe vazio para usar o padrão")
        voice_id = st.text_input("Voz (opcional)", placeholder="ID da voz ou padrão")

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        generate = st.button("🔊 Gerar Áudio", type="primary", use_container_width=True)
    with col_b:
        test = st.button("🎵 Gerar Teste Curto", use_container_width=True)
    with col_c:
        clear = st.button("🗑️ Limpar", use_container_width=True)

    if clear:
        st.rerun()

    if generate or test:
        if not text.strip():
            st.error("O texto não pode estar vazio.")
            return

        request = TTSRequest(
            text=text if not test else text[:200],
            language=None if language == "Auto" else language,
            output_format=output_format,
            speed=speed if speed != 1.0 else None,
            model_id=model_id or None,
            voice_id=voice_id or None,
            free_only=config.app.free_only_mode,
            force_provider=False,
        )

        if provider_choice != "Automático (fallback)":
            request.provider_id = provider_choice
            request.force_provider = True

        with st.spinner("Gerando áudio..."):
            try:
                from app.core.fallback_engine import TTSService
                service = TTSService()
                result = service.generate(request)

                st.markdown(warning_box("✅ Áudio gerado com sucesso!", "success"), unsafe_allow_html=True)

                if result.warnings:
                    for w in result.warnings:
                        st.warning(w)

                if result.fallback_chain:
                    st.markdown(fallback_timeline(result.fallback_chain), unsafe_allow_html=True)

                col_r1, col_r2 = st.columns([2, 1])
                with col_r1:
                    import os
                    if os.path.exists(result.audio_file_path):
                        with open(result.audio_file_path, "rb") as f:
                            audio_bytes = f.read()
                        st.audio(audio_bytes, format=f"audio/{result.output_format}")

                        st.download_button(
                            "📥 Baixar áudio",
                            data=audio_bytes,
                            file_name=f"{result.generation_id}.{result.output_format}",
                            mime=f"audio/{result.output_format}",
                            use_container_width=True,
                        )

                with col_r2:
                    st.markdown("**Detalhes da geração:**")
                    st.markdown(f"- **Provedor:** `{result.provider_id}`")
                    if result.model_id:
                        st.markdown(f"- **Modelo:** `{result.model_id}`")
                    if result.voice_id:
                        st.markdown(f"- **Voz:** `{result.voice_id}`")
                    st.markdown(f"- **Caracteres:** {len(request.text)}")
                    if result.duration_seconds:
                        st.markdown(f"- **Duração:** {result.duration_seconds:.1f}s")
                    if result.usage:
                        st.markdown(f"- **Consumo:** {result.usage.amount} {result.usage.unit}")

            except Exception as e:
                st.error(f"❌ Erro ao gerar áudio: {e}")
                st.markdown(warning_box(f"Detalhes: {e}", "error"), unsafe_allow_html=True)
