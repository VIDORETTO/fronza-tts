import streamlit as st

from app.db.repositories import provider_repo, quota_repo
from app.ui.components.quota_badge import quota_badge, reset_badge

RESET_BADGES = {
    "monthly_billing_cycle": ("RESET MENSAL", "#1a73e8"),
    "daily_rate_limit": ("RESET DIÁRIO", "#e8710a"),
    "one_time_trial_credit": ("CRÉDITO INICIAL", "#9c27b0"),
    "manual_balance": ("MANUAL", "#607d8b"),
    "unknown": ("INCERTO", "#f44336"),
    "pay_as_you_go": ("RISCO COBRANÇA", "#d32f2f"),
    "paid_topup": ("TOP-UP", "#ff9800"),
    "billing_cycle_or_topup": ("CICLO/TOP-UP", "#795548"),
    "monthly_or_on_demand": ("MENSAL/ON-DEMAND", "#1565c0"),
    "one_time_trial_credit_or_manual": ("CRÉDITO INICIAL", "#9c27b0"),
    "daily_and_per_minute_rate_limits": ("DIÁRIO/MINUTO", "#e8710a"),
    "official_api_or_local": ("API OFICIAL", "#2e7d32"),
    "response_metadata_or_local": ("METADADOS", "#f57f17"),
    "portal_or_local": ("PORTAL", "#5d4037"),
}


def show():
    st.title("📊 Limites e Cotas")
    st.caption("Acompanhe o consumo de cada provedor de TTS.")

    providers = provider_repo.list_all()

    if not providers:
        st.info("Nenhum provedor cadastrado. Adicione chaves de API na tela de Provedores.")
        return

    for p in providers:
        snapshot = quota_repo.get_latest_snapshot(p.id)

        with st.container(border=True):
            cols = st.columns([1, 1, 1, 1, 1, 1])
            cols[0].markdown(f"**{p.id.upper()}**")

            status = p.status.upper() if p.status else "DESCONHECIDO"
            if status in ("OK", "ENABLED", ""):
                cols[1].success("✅ OK")
            elif status in ("ATENÇÃO", "WARNING", "ERROR"):
                cols[1].warning("⚠️ Atenção")
            elif status == "BLOCKED":
                cols[1].error("🚫 Bloqueado")
            else:
                cols[1].info(status)

            if snapshot:
                used = snapshot.used or 0
                limit = snapshot.limit or 0
                remaining = snapshot.remaining or 0
                pct = (used / limit * 100) if limit > 0 else 0

                cols[2].metric("Usado", f"{used:.0f} / {limit:.0f}" if limit else "N/D")
                cols[3].metric("Restante", f"{remaining:.0f}" if limit else "N/D")

                if pct > 90:
                    cols[4].error(f"{pct:.0f}%")
                elif pct > 70:
                    cols[4].warning(f"{pct:.0f}%")
                else:
                    cols[4].success(f"{pct:.0f}%")

                st.markdown(reset_badge(snapshot.reset_policy), unsafe_allow_html=True)
                st.caption(f"Fonte: {snapshot.source} | Confiança: {snapshot.confidence} | Atualizado: {snapshot.updated_at.strftime('%d/%m/%Y %H:%M') if snapshot.updated_at else 'N/A'}")
            else:
                cols[2].metric("Usado", "N/D")
                cols[3].metric("Restante", "N/D")
                cols[4].write("N/D")
                st.caption("Sem dados de cota. Configure uma chave de API primeiro.")

    st.divider()
    st.subheader("📋 Legenda")

    col_l1, col_l2, col_l3, col_l4 = st.columns(4)
    with col_l1:
        st.markdown(reset_badge("monthly_billing_cycle"), unsafe_allow_html=True)
        st.markdown(reset_badge("daily_rate_limit"), unsafe_allow_html=True)
    with col_l2:
        st.markdown(reset_badge("one_time_trial_credit"), unsafe_allow_html=True)
        st.markdown(reset_badge("manual_balance"), unsafe_allow_html=True)
    with col_l3:
        st.markdown(reset_badge("pay_as_you_go"), unsafe_allow_html=True)
        st.markdown(reset_badge("paid_topup"), unsafe_allow_html=True)
    with col_l4:
        st.markdown(reset_badge("unknown"), unsafe_allow_html=True)
