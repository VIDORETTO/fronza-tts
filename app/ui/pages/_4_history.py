import streamlit as st
from pathlib import Path

from app.db.repositories import generation_repo


def show():
    st.title("📜 Histórico")
    st.caption("Gerações anteriores de áudio.")

    tab_all, tab_favorites = st.tabs(["Todas", "Favoritas"])

    with tab_all:
        generations = generation_repo.list_all(limit=50)

        if not generations:
            st.info("Nenhuma geração encontrada. Gere seu primeiro áudio!")
            return

        for gen in generations:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])

                with c1:
                    st.markdown(f"**{gen.provider_id}** | {gen.model_id or 'N/A'} | {gen.voice_id or 'N/A'}")
                    st.caption(f"{gen.input_characters} caracteres | {gen.language or 'N/A'}")
                    preview = gen.input_text[:120] + "..." if len(gen.input_text) > 120 else gen.input_text
                    st.text(preview)

                    if gen.fallback_chain:
                        chain = gen.fallback_chain.split(",") if isinstance(gen.fallback_chain, str) else []
                        fallback_html = "Fallback: "
                        for i, fp in enumerate(chain):
                            fallback_html += f'<span style="background:#d32f2f;padding:1px 8px;border-radius:8px;color:white;font-size:0.7em">{fp}</span>'
                            if i < len(chain) - 1:
                                fallback_html += " → "
                        st.markdown(fallback_html, unsafe_allow_html=True)

                with c2:
                    st.caption(gen.created_at.strftime("%d/%m/%Y %H:%M") if gen.created_at else "")

                    status = gen.status.upper() if gen.status else ""
                    if status == "SUCCESS":
                        st.success("✅ Sucesso")
                    elif "ERROR" in status:
                        st.error(f"❌ Erro")
                        if gen.error_message:
                            st.caption(gen.error_message[:60])
                    else:
                        st.info(status)

                    audio_path = Path(gen.output_file_path) if gen.output_file_path else None
                    if audio_path and audio_path.exists():
                        with open(audio_path, "rb") as f:
                            audio_bytes = f.read()
                        st.audio(audio_bytes, format=f"audio/{gen.output_format}")
                        st.download_button(
                            "📥 Baixar",
                            data=audio_bytes,
                            file_name=f"{gen.id}.{gen.output_format}",
                            mime=f"audio/{gen.output_format}",
                            key=f"dl_{gen.id}",
                            use_container_width=True,
                        )
