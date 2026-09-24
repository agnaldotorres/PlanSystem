import streamlit as st
import json
import os

st.set_page_config(
    page_title="Ranking de Visitas em Loja",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PASTA_DADOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dados")
ARQUIVO_RESULTADO = os.path.join(PASTA_DADOS, "ultimo_resultado.json")

# -----------------------------------------------------------------
# CSS: esconde menu lateral, cabeçalho e rodapé do Streamlit para
# ocupar a tela toda na TV, e estiliza como um placar de ranking.
# Fica FORA do fragment porque não muda a cada atualização.
# -----------------------------------------------------------------
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarCollapsedControl"] {display: none;}
        header[data-testid="stHeader"] {display: none;}
        footer {display: none;}
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        body {
            background-color: #0a0f1e;
        }
        .tv-title {
            text-align: center;
            font-size: 3rem;
            font-weight: 900;
            color: #ffffff;
            letter-spacing: 1px;
            margin-bottom: 0;
        }
        .tv-subtitle {
            text-align: center;
            font-size: 1.3rem;
            color: #f5a623;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .tv-updated {
            text-align: center;
            font-size: 1.1rem;
            color: #8a93a6;
            margin-bottom: 2rem;
        }
        .tv-row {
            display: flex;
            align-items: center;
            margin-bottom: 14px;
            height: 68px;
        }
        .tv-pos {
            width: 70px;
            font-size: 2rem;
            font-weight: 900;
            color: #f5a623;
            text-align: center;
            flex-shrink: 0;
        }
        .tv-bar {
            flex-grow: 1;
            height: 100%;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 28px;
            background: linear-gradient(90deg, #10204a, #16305e);
            box-shadow: 0 2px 10px rgba(0,0,0,0.35);
        }
        .tv-row:nth-child(1) .tv-bar { background: linear-gradient(90deg, #b8860b, #f5a623); }
        .tv-row:nth-child(2) .tv-bar { background: linear-gradient(90deg, #4a4a4a, #8a8a8a); }
        .tv-row:nth-child(3) .tv-bar { background: linear-gradient(90deg, #6e3a12, #a8621f); }
        .tv-name {
            font-size: 1.6rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: 0.5px;
        }
        .tv-name.meta-atingida {
            color: #22c55e;
            text-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
        }
        .tv-name.meta-atingida::after {
            content: " ✅";
            font-size: 1.2rem;
        }
        .tv-value {
            font-size: 1.8rem;
            font-weight: 900;
            color: #ffffff;
        }
        .tv-empty {
            text-align: center;
            font-size: 1.5rem;
            color: #8a93a6;
            margin-top: 4rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="tv-title">🔥 RANKING DE VISITAS EM LOJA</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------
# Fragment nativo do Streamlit: só este bloco reroda a cada 30s,
# isolado do resto da página. Diferente do streamlit_autorefresh,
# ele não depende de reconexão de WebSocket nem de navegação de
# página, então não corre o risco de "voltar pra home" se a sessão
# cair — o Streamlit trata isso internamente sem sair da página.
# -----------------------------------------------------------------
@st.fragment(run_every=30)
def placar():
    if not os.path.exists(ARQUIVO_RESULTADO):
        st.markdown(
            '<div class="tv-empty">Nenhum resultado publicado ainda.</div>',
            unsafe_allow_html=True,
        )
        return

    with open(ARQUIVO_RESULTADO, "r", encoding="utf-8") as f:
        resultado = json.load(f)

    st.markdown(
        f'<div class="tv-subtitle">📅 {resultado["total_visitas_agendadas"]} visitas agendadas • '
        f'🔥 {resultado["total_aquecedores"]} aquecedores</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="tv-updated">Última atualização: {resultado["atualizado_em"]}</div>',
        unsafe_allow_html=True,
    )

    linhas_html = ""
    for item in resultado["ranking"]:
        # -------------------------------------------------------------
        # Se o resultado publicado tiver a coluna "Atingiu Meta" (planilhas
        # que possuem a coluna "Empresa"), o nome do aquecedor aparece em
        # verde com um ✅ quando ele bateu a meta da empresa dele.
        # -------------------------------------------------------------
        atingiu = bool(item.get("Atingiu Meta"))
        classe_nome = "tv-name meta-atingida" if atingiu else "tv-name"

        linhas_html += f"""
        <div class="tv-row">
            <div class="tv-pos">{item['Posição']}</div>
            <div class="tv-bar">
                <div class="{classe_nome}">{item['Aquecedor']}</div>
                <div class="tv-value">{item['Quantidade']}</div>
            </div>
        </div>
        """

    st.markdown(linhas_html, unsafe_allow_html=True)


placar()