import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(
    page_title="Painel de Aquecimento",
    page_icon="📊",
    layout="wide"
)

# -----------------------------------------------------------------
# Mesmo arquivo que a página admin (app.py) escreve.
# -----------------------------------------------------------------
PASTA_DADOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dados")
ARQUIVO_RESULTADO = os.path.join(PASTA_DADOS, "ultimo_resultado.json")

# -----------------------------------------------------------------
# Atualiza a página sozinha a cada 30 segundos, para que quem estiver
# com essa página aberta veja o novo resultado sem precisar recarregar
# manualmente assim que você enviar uma planilha nova.
# -----------------------------------------------------------------
st.markdown('<meta http-equiv="refresh" content="30">', unsafe_allow_html=True)

st.title("🔥 Painel de Aquecimento")

if not os.path.exists(ARQUIVO_RESULTADO):
    st.warning(
        "Ainda não há nenhum resultado publicado. "
        "Assim que uma planilha for processada, os números aparecerão aqui."
    )
else:
    with open(ARQUIVO_RESULTADO, "r", encoding="utf-8") as f:
        resultado = json.load(f)

    st.caption(f"🕒 Última atualização: **{resultado['atualizado_em']}**")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📅 Total de Visitas Agendadas", resultado["total_visitas_agendadas"])
    with col2:
        st.metric("🔥 Total de Aquecedores", resultado["total_aquecedores"])

    ranking = pd.DataFrame(resultado["ranking"]).set_index("Posição")

    st.subheader("🏆 Ranking dos Aquecedores")
    st.dataframe(ranking, use_container_width=True)

    st.subheader("📊 Visitas Agendadas por Aquecedor")
    st.bar_chart(ranking.set_index("Aquecedor"))

    st.caption("Esta página se atualiza automaticamente a cada 30 segundos.")
