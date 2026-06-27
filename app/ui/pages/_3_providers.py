import streamlit as st

from app.db.repositories import api_key_repo, provider_repo
from app.providers.registry import registry
from app.ui.components.quota_badge import quota_badge, reset_badge
from app.utils.security import encrypt_value, mask_api_key

PROVIDER_INFO = {
    "elevenlabs": {"name": "ElevenLabs", "free_limit": "10.000 caracteres/mês", "docs": "https://elevenlabs.io/docs"},
    "cartesia": {"name": "Cartesia", "free_limit": "20.000 créditos/mês", "docs": "https://docs.cartesia.ai"},
    "smallest": {"name": "Smallest.ai", "free_limit": "Crédito inicial (valor variável)", "docs": "https://smallest.ai"},
    "gemini": {"name": "Gemini API", "free_limit": "1.500 requisições/dia (tier grátis)", "docs": "https://ai.google.dev"},
    "inworld": {"name": "Inworld", "free_limit": "60 min/mês (plano On-Demand)", "docs": "https://docs.inworld.ai"},
    "async_voice": {"name": "Async Voice", "free_limit": "Crédito inicial/plano (manual)", "docs": "https://async-voice.com"},
}

RESET_LABELS = {
    "monthly_billing_cycle": "🔄 Reset mensal",
    "daily_rate_limit": "📅 Reset diário",
    "one_time_trial_credit": "💎 Crédito inicial (não reseta)",
    "manual_balance": "✋ Saldo manual",
    "billing_cycle_or_topup": "🔄 Ciclo ou top-up",
    "monthly_or_on_demand": "🔄 Mensal ou On-Demand",
    "unknown": "❓ Desconhecido",
    "pay_as_you_go": "💳 Pago por uso",
    "paid_topup": "💰 Top-up pago",
}


def show():
    st.title("🔌 Provedores")
    st.caption("Gerencie as configurações e veja os limites grátis de cada provedor de TTS.")

    provider_ids = ["elevenlabs", "cartesia", "smallest", "gemini", "inworld", "async_voice"]

    for pid in provider_ids:
        info = PROVIDER_INFO.get(pid, {})
        db_provider = provider_repo.get(pid)
        has_key = api_key_repo.has_key(pid)
        keys = api_key_repo.get_by_provider(pid)

        adapter = registry.get(pid)

        quota = None
        if adapter and has_key:
            try:
                quota = adapter.get_quota()
            except Exception:
                pass

        with st.expander(f"**{info.get('name', pid.upper())}**", expanded=True):
            c_top = st.columns([2, 1, 1])

            with c_top[0]:
                st.markdown(f"**Status:** {'✅ Ativo' if has_key else '❌ Sem chave'}")

                if db_provider:
                    st.markdown(f"**Prioridade:** {db_provider.priority}")
                    reset_label = RESET_LABELS.get(db_provider.reset_policy, db_provider.reset_policy)
                    st.markdown(f"**Reset:** `{reset_label}`")

            with c_top[1]:
                st.markdown("**Limite grátis oficial:**")
                st.markdown(f"`{info.get('free_limit', 'N/D')}`")

            with c_top[2]:
                if keys:
                    masked = mask_api_key(keys[0].encrypted_value)
                    st.markdown(f"**API Key:** `{masked}`")
                if db_provider and db_provider.last_error:
                    st.error(f"Último erro: {db_provider.last_error}")

            if quota:
                st.divider()
                c_quota = st.columns(5)
                c_quota[0].metric("Usado", f"{quota.used:.0f}" if quota.used is not None else "N/D")
                c_quota[1].metric("Limite", f"{quota.limit:.0f}" if quota.limit else "N/D")
                c_quota[2].metric("Restante", f"{quota.remaining:.0f}" if quota.remaining is not None else "N/D")
                if quota.limit and quota.used is not None and quota.limit > 0:
                    pct = (quota.used / quota.limit) * 100
                    c_quota[3].metric("Usado %", f"{pct:.1f}%")
                else:
                    c_quota[3].metric("Usado %", "N/D")
                c_quota[4].markdown(f"**Unidade:** `{quota.unit}`")
                st.caption(f"Fonte: `{quota.source}` | Confiança: `{quota.confidence}` | Atualizado: {quota.updated_at.strftime('%d/%m/%Y %H:%M') if quota.updated_at else 'N/A'}")
                st.markdown(reset_badge(quota.reset_policy), unsafe_allow_html=True)
            else:
                st.caption("💡 Configure uma chave de API para ver os limites em tempo real.")

            st.divider()

            col_key, col_actions = st.columns([2, 1])

            with col_key:
                new_key = st.text_input(
                    "Nova chave de API",
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

                    if st.button(f"🔍 Testar e atualizar cota", key=f"test_{pid}", use_container_width=True):
                        with st.spinner(f"Consultando {pid}..."):
                            if adapter:
                                try:
                                    models = adapter.list_models()
                                    if models:
                                        st.success(f"✅ API OK! {len(models)} modelos disponíveis")
                                    try:
                                        q = adapter.get_quota()
                                        st.info(f"📊 Cota: {q.used:.0f}/{q.limit:.0f} {q.unit} usados")
                                    except Exception as qe:
                                        st.warning(f"⚠️ Não foi possível consultar cota: {qe}")
                                except NotImplementedError:
                                    st.warning("⏳ Provedor não implementado ainda")
                                except Exception as e:
                                    st.error(f"❌ Erro: {e}")
                            else:
                                st.warning("⏳ Provider não registrado")

            st.divider()
