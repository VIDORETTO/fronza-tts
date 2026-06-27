import streamlit as st

from app.core.config import config
from app.db.repositories import api_key_repo
from app.providers.registry import registry
from app.schemas.tts import TTSRequest
from app.ui.components.quota_badge import fallback_timeline, warning_box

ALL_LANGUAGES = [
    "Auto", "pt-BR", "en", "es", "fr", "de", "it", "ja",
    "ko", "zh", "ar", "ru", "nl", "pl", "vi", "tr", "hi",
]

LANGUAGE_NAMES = {
    "Auto": "🌐 Detectar automaticamente",
    "pt-BR": "🇧🇷 Português (Brasil)",
    "en": "🇺🇸 Inglês",
    "es": "🇪🇸 Espanhol",
    "fr": "🇫🇷 Francês",
    "de": "🇩🇪 Alemão",
    "it": "🇮🇹 Italiano",
    "ja": "🇯🇵 Japonês",
    "ko": "🇰🇷 Coreano",
    "zh": "🇨🇳 Chinês",
    "ar": "🇸🇦 Árabe",
    "ru": "🇷🇺 Russo",
    "nl": "🇳🇱 Holandês",
    "pl": "🇵🇱 Polonês",
    "vi": "🇻🇳 Vietnamita",
    "tr": "🇹🇷 Turco",
    "hi": "🇮🇳 Hindi",
}


def _get_models_for_provider(provider_id: str, language: str | None) -> list[tuple[str, str]]:
    adapter = registry.get(provider_id)
    if not adapter:
        return []
    models = adapter.list_models()
    result = []
    for m in models:
        if language and language != "Auto":
            if m.languages and language not in m.languages:
                base = language.split("-")[0]
                if not any(l.split("-")[0] == base for l in m.languages):
                    continue
        label = m.name or m.model_id
        if m.is_default:
            label += " (padrão)"
        result.append((m.model_id, label))
    return result


def _get_voices_for_provider(provider_id: str, language: str | None) -> list[VoiceUIData]:
    adapter = registry.get(provider_id)
    if not adapter:
        return []
    voices = adapter.list_voices(language=language)
    return [
        VoiceUIData(v.voice_id, v.name or v.voice_id, v.preview_url, v.labels)
        for v in voices
    ]


class VoiceUIData:
    def __init__(self, voice_id: str, name: str, preview_url: str | None = None, labels: dict | None = None):
        self.voice_id = voice_id
        self.name = name
        self.preview_url = preview_url
        self.labels = labels or {}


def show():
    st.title("🎙️ Gerar Áudio")
    st.caption("Digite o texto e escolha as configurações para gerar áudio via TTS.")

    mode_msg = (
        "🛡️ **Modo gratuito ativo.** O app nunca usará provedores pagos automaticamente."
        if config.app.free_only_mode
        else "⚠️ **Modo pago ativo.** O app pode usar provedores com cobrança."
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
            m1, m2, m3 = st.columns(3)
            m1.metric("Caracteres", char_count)
            m2.metric("Máx. recomendado", config.app.max_text_chars_warning)
            if char_count > config.app.max_text_chars_warning:
                st.warning(f"⚠️ Texto grande ({char_count} caracteres). Será dividido em chunks.")

    with col2:
        lang_display = {v: k for k, v in LANGUAGE_NAMES.items()}
        selected_lang_name = st.selectbox(
            "Idioma",
            options=list(LANGUAGE_NAMES.values()),
            index=1,
        )
        language = lang_display[selected_lang_name]

        provider_options = ["Automático (fallback)"] + registry.list_ids()
        provider_choice = st.selectbox("Provedor", provider_options, index=0)

        output_format = st.selectbox("Formato", ["mp3", "wav", "ogg"], index=0)

    provider_id = None if provider_choice == "Automático (fallback)" else provider_choice

    if provider_id:
        st.divider()
        st.markdown(f"**⚙️ Configurações — {provider_id}**")

        models = _get_models_for_provider(provider_id, language)
        if models:
            model_labels = [m[1] for m in models]
            default_idx = next((i for i, m in enumerate(models) if "padrão" in m[1]), 0)
            selected_model_label = st.selectbox("Modelo", model_labels, index=default_idx, key="model_select")
            selected_model = models[model_labels.index(selected_model_label)][0]
        else:
            selected_model = None
            st.info("Nenhum modelo disponível para este idioma.")

        voices = _get_voices_for_provider(provider_id, language)
        if voices:
            voice_options = [f"{v.name} ({v.voice_id[:8]}...)" if not v.name else v.name for v in voices]
            default_voice_idx = 0
            selected_voice_label = st.selectbox("Voz", voice_options, index=default_voice_idx, key="voice_select")
            selected_voice_idx = voice_options.index(selected_voice_label)
            selected_voice = voices[selected_voice_idx]

            preview_url = selected_voice.preview_url
            if preview_url:
                if st.button(f"🔊 Preview de {selected_voice.name}", key="voice_preview"):
                    import httpx
                    try:
                        resp = httpx.get(preview_url, timeout=10)
                        if resp.status_code == 200:
                            st.audio(resp.content, format="audio/mpeg")
                    except Exception as e:
                        st.warning(f"Preview indisponível: {e}")
            else:
                st.caption("Preview não disponível para esta voz via API.")
        else:
            selected_voice = None
            st.info("Nenhuma voz disponível.")

        with st.expander("🎛️ Ajustes avançados"):
            speed = st.slider("Velocidade", 0.5, 2.0, 1.0, 0.1)
    else:
        selected_model = None
        selected_voice = None
        with st.expander("⚙️ Configurações avançadas"):
            speed = st.slider("Velocidade", 0.5, 2.0, 1.0, 0.1)

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
            model_id=selected_model or None,
            voice_id=selected_voice.voice_id if selected_voice else None,
            free_only=config.app.free_only_mode,
            force_provider=False,
        )

        if provider_id:
            request.provider_id = provider_id
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
                    st.markdown(f"- **Idioma:** {request.language or 'auto'}")
                    st.markdown(f"- **Caracteres:** {len(request.text)}")
                    if result.duration_seconds:
                        st.markdown(f"- **Duração:** {result.duration_seconds:.1f}s")
                    if result.usage:
                        st.markdown(f"- **Consumo:** {result.usage.amount} {result.usage.unit}")

            except Exception as e:
                st.error(f"❌ Erro ao gerar áudio: {e}")
                st.markdown(warning_box(f"Detalhes: {e}", "error"), unsafe_allow_html=True)
