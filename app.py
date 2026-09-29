import streamlit as st
import pandas as pd
import plotly.express as px


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Mergulho por Aquecimento",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #f5f7fa;
}

.main .block-container {
    max-width: 1600px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Títulos */

h1, h2, h3 {
    color: #111827;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
}

section[data-testid="stSidebar"] > div {
    padding-top: 2rem;
}

/* Header */

.dashboard-header {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 25px 30px;
    margin-bottom: 25px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.04);
}

.header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-badge {
    display: inline-block;
    background: #eef2ff;
    color: #4338ca;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 10px;
    border-radius: 8px;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.dashboard-header h1 {
    margin: 0;
    font-size: 32px;
    font-weight: 700;
}

.dashboard-header p {
    margin-top: 8px;
    color: #6b7280;
    font-size: 15px;
}

.header-status {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #f0fdf4;
    color: #166534;
    border: 1px solid #bbf7d0;
    padding: 8px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
}

.status-dot {
    width: 8px;
    height: 8px;
    background: #22c55e;
    border-radius: 50%;
}

/* Cards */

.metric-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.035);
    min-height: 120px;
}

.metric-title {
    color: #6b7280;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 10px;
}

.metric-value {
    color: #111827;
    font-size: 30px;
    font-weight: 700;
}

.metric-description {
    color: #9ca3af;
    font-size: 12px;
    margin-top: 5px;
}

/* Navegação */

div[role="radiogroup"] {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    padding: 6px;
    border-radius: 12px;
    margin-bottom: 25px;
}

/* Tabelas */

[data-testid="stDataFrame"] {
    background: #ffffff;
    border-radius: 12px;
}

/* Upload */

[data-testid="stFileUploader"] {
    background: #ffffff;
    border-radius: 12px;
}

/* Botões */

button {
    border-radius: 8px !important;
}

/* Scroll */

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
}

::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="dashboard-header">

    <div class="header-content">

        <div>

            <div class="header-badge">
                PAINEL COMERCIAL
            </div>

            <h1>
                Mergulho por Aquecimento
            </h1>

            <p>
                Análise de visitas realizadas, aquecimento,
                vendedores e eventos comerciais.
            </p>

        </div>

        <div class="header-status">

            <span class="status-dot"></span>

            Sistema ativo

        </div>

    </div>

</div>
""", unsafe_allow_html=True)


# ============================================================
# UPLOAD
# ============================================================

st.sidebar.title("⚙️ Configurações")

arquivo = st.sidebar.file_uploader(
    "Lançar planilha",
    type=["xlsx", "xls"]
)


if arquivo is None:

    st.info(
        "📂 Envie a planilha **Mergulho Por Aquecimento** "
        "para carregar os dados."
    )

    st.stop()


# ============================================================
# LEITURA DA PLANILHA
# ============================================================

try:

    # A planilha possui informações antes do cabeçalho.
    # O cabeçalho real começa na terceira linha.
    df = pd.read_excel(
        arquivo,
        header=2
    )

except Exception as e:

    st.error(
        f"Erro ao carregar a planilha: {e}"
    )

    st.stop()


# ============================================================
# LIMPEZA DOS NOMES DAS COLUNAS
# ============================================================

df.columns = (
    df.columns
    .astype(str)
    .str.replace("\n", " ", regex=False)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)


# ============================================================
# GARANTIR COLUNAS IMPORTANTES
# ============================================================

colunas_necessarias = [
    "Evento",
    "Cliente",
    "Data Inclusão",
    "Tipo Evento",
    "Status",
    "Empresa",
    "Temperatura",
    "Mídia",
    "Etapa Funil",
    "Visita Agendada",
    "Visita Realizada",
    "Aquecido",
    "Aquecimento",
    "Vendedor"
]

colunas_existentes = [
    coluna
    for coluna in colunas_necessarias
    if coluna in df.columns
]

if "Evento" not in df.columns:

    st.error(
        "A coluna **Evento** não foi encontrada na planilha."
    )

    st.stop()


# ============================================================
# LIMPEZA DOS DADOS
# ============================================================

for coluna in df.columns:

    if df[coluna].dtype == "object":

        df[coluna] = (
            df[coluna]
            .astype(str)
            .str.strip()
        )


# ============================================================
# CONVERSÃO DE DATAS
# ============================================================

if "Data Inclusão" in df.columns:

    df["Data Inclusão"] = pd.to_datetime(
        df["Data Inclusão"],
        errors="coerce"
    )


# ============================================================
# NORMALIZAÇÃO DA VISITA REALIZADA
# ============================================================

if "Visita Realizada" in df.columns:

    df["Visita Realizada"] = (
        df["Visita Realizada"]
        .astype(str)
        .str.strip()
        .str.upper()
    )


# ============================================================
# REGRA PRINCIPAL
# ============================================================
#
# REGRA:
# UMA VISITA POR EVENTO
#
# Exemplo:
#
# Evento 123
# SIM
# SIM
#
# Resultado:
#
# Evento 123 = 1 visita
#
# ============================================================

if "Visita Realizada" in df.columns:

    df_visitas = df[
        df["Visita Realizada"] == "SIM"
    ].copy()

else:

    df_visitas = pd.DataFrame()


# ============================================================
# REMOVER EVENTOS DUPLICADOS
# ============================================================

if not df_visitas.empty:

    # Remove linhas sem Evento
    df_visitas = df_visitas[
        df_visitas["Evento"].notna()
    ].copy()

    # Remove eventos vazios
    df_visitas = df_visitas[
        df_visitas["Evento"].astype(str).str.strip() != ""
    ].copy()

    # --------------------------------------------------------
    # REGRA:
    # UM EVENTO = UMA VISITA
    # --------------------------------------------------------

    df_visitas = df_visitas.drop_duplicates(
        subset=["Evento"],
        keep="first"
    ).copy()


# ============================================================
# FILTROS
# ============================================================

st.sidebar.markdown("---")
st.sidebar.subheader("🔎 Filtros")


def criar_filtro(
    dataframe,
    coluna,
    titulo
):

    if coluna not in dataframe.columns:

        return dataframe

    valores = sorted(
        dataframe[coluna]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selecionados = st.sidebar.multiselect(
        titulo,
        valores
    )

    if selecionados:

        dataframe = dataframe[
            dataframe[coluna]
            .astype(str)
            .isin(selecionados)
        ]

    return dataframe


# Aplicar filtros SOMENTE depois da deduplicação
df_filtrado = df_visitas.copy()


df_filtrado = criar_filtro(
    df_filtrado,
    "Empresa",
    "Empresa"
)


df_filtrado = criar_filtro(
    df_filtrado,
    "Aquecimento",
    "Aquecimento"
)


df_filtrado = criar_filtro(
    df_filtrado,
    "Vendedor",
    "Vendedor"
)


df_filtrado = criar_filtro(
    df_filtrado,
    "Mídia",
    "Mídia"
)


df_filtrado = criar_filtro(
    df_filtrado,
    "Tipo Evento",
    "Tipo de Evento"
)


df_filtrado = criar_filtro(
    df_filtrado,
    "Temperatura",
    "Temperatura"
)


# ============================================================
# NAVEGAÇÃO
# ============================================================

pagina = st.radio(
    "Navegação",
    [
        "📊 Visão Geral",
        "🔥 Aquecimento",
        "👥 Vendedores",
        "📅 Eventos",
        "📋 Dados"
    ],
    horizontal=True,
    label_visibility="collapsed"
)


# ============================================================
# MÉTRICAS
# ============================================================

total_eventos = df_filtrado["Evento"].nunique()


if "Cliente" in df_filtrado.columns:

    total_clientes = df_filtrado["Cliente"].nunique()

else:

    total_clientes = 0


if "Vendedor" in df_filtrado.columns:

    total_vendedores = (
        df_filtrado["Vendedor"]
        .replace(
            ["", "nan", "None"],
            pd.NA
        )
        .dropna()
        .nunique()
    )

else:

    total_vendedores = 0


if "Aquecimento" in df_filtrado.columns:

    total_aquecimentos = (
        df_filtrado["Aquecimento"]
        .replace(
            ["", "nan", "None"],
            pd.NA
        )
        .dropna()
        .nunique()
    )

else:

    total_aquecimentos = 0


# ============================================================
# FUNÇÃO DE CARD
# ============================================================

def card(
    titulo,
    valor,
    descricao=""
):

    st.markdown(
        f"""
        <div class="metric-card">

            <div class="metric-title">
                {titulo}
            </div>

            <div class="metric-value">
                {valor:,}
            </div>

            <div class="metric-description">
                {descricao}
            </div>

        </div>
        """.replace(",", "."),
        unsafe_allow_html=True
    )


# ============================================================
# VISÃO GERAL
# ============================================================

if pagina == "📊 Visão Geral":

    st.subheader("Visão Geral")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        card(
            "Visitas realizadas",
            total_eventos,
            "Eventos únicos"
        )

    with col2:

        card(
            "Clientes",
            total_clientes,
            "Clientes únicos"
        )

    with col3:

        card(
            "Vendedores",
            total_vendedores,
            "Vendedores envolvidos"
        )

    with col4:

        card(
            "Aquecimentos",
            total_aquecimentos,
            "Tipos de aquecimento"
        )


    st.markdown("---")


    col1, col2 = st.columns(2)


    # --------------------------------------------------------
    # AQUECIMENTOS
    # --------------------------------------------------------

    with col1:

        if "Aquecimento" in df_filtrado.columns:

            dados = (
                df_filtrado[
                    df_filtrado["Aquecimento"]
                    .notna()
                ]
                .groupby("Aquecimento")
                .size()
                .reset_index(name="Visitas")
                .sort_values(
                    "Visitas",
                    ascending=False
                )
            )

            if not dados.empty:

                fig = px.bar(
                    dados,
                    x="Aquecimento",
                    y="Visitas",
                    title="Visitas por Aquecimento",
                    text="Visitas"
                )

                fig.update_layout(
                    xaxis_title="Aquecimento",
                    yaxis_title="Visitas",
                    plot_bgcolor="white",
                    paper_bgcolor="white"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


    # --------------------------------------------------------
    # VENDEDORES
    # --------------------------------------------------------

    with col2:

        if "Vendedor" in df_filtrado.columns:

            dados = (
                df_filtrado[
                    df_filtrado["Vendedor"]
                    .notna()
                ]
                .groupby("Vendedor")
                .size()
                .reset_index(name="Visitas")
                .sort_values(
                    "Visitas",
                    ascending=False
                )
                .head(15)
            )

            if not dados.empty:

                fig = px.bar(
                    dados,
                    x="Visitas",
                    y="Vendedor",
                    orientation="h",
                    title="Visitas por Vendedor",
                    text="Visitas"
                )

                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


# ============================================================
# AQUECIMENTO
# ============================================================

elif pagina == "🔥 Aquecimento":

    st.subheader("Análise por Aquecimento")


    if "Aquecimento" in df_filtrado.columns:

        dados = (
            df_filtrado
            .groupby("Aquecimento")
            .agg(
                Visitas=("Evento", "nunique")
            )
            .reset_index()
            .sort_values(
                "Visitas",
                ascending=False
            )
        )

        st.dataframe(
            dados,
            use_container_width=True,
            hide_index=True
        )


        fig = px.bar(
            dados,
            x="Aquecimento",
            y="Visitas",
            text="Visitas",
            title="Ranking de Aquecimentos"
        )

        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# VENDEDORES
# ============================================================

elif pagina == "👥 Vendedores":

    st.subheader("Performance dos Vendedores")


    if "Vendedor" in df_filtrado.columns:

        ranking = (
            df_filtrado
            .groupby("Vendedor")
            .agg(
                Visitas=("Evento", "nunique"),
                Clientes=("Cliente", "nunique")
            )
            .reset_index()
            .sort_values(
                "Visitas",
                ascending=False
            )
        )


        ranking["Participação"] = (
            ranking["Visitas"]
            / ranking["Visitas"].sum()
            * 100
        ).round(2)


        st.dataframe(
            ranking,
            use_container_width=True,
            hide_index=True
        )


        fig = px.bar(
            ranking.head(20),
            x="Visitas",
            y="Vendedor",
            orientation="h",
            text="Visitas",
            title="Ranking de Vendedores"
        )

        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# EVENTOS
# ============================================================

elif pagina == "📅 Eventos":

    st.subheader("Eventos / Visitas")

    st.info(
        "Cada Evento é considerado apenas uma vez, "
        "mesmo que apareça repetido na planilha."
    )


    colunas_exibicao = [
        "Evento",
        "Cliente",
        "Data Inclusão",
        "Tipo Evento",
        "Empresa",
        "Temperatura",
        "Mídia",
        "Etapa Funil",
        "Visita Agendada",
        "Visita Realizada",
        "Aquecido",
        "Aquecimento",
        "Vendedor"
    ]


    colunas_exibicao = [
        coluna
        for coluna in colunas_exibicao
        if coluna in df_filtrado.columns
    ]


    tabela = df_filtrado[
        colunas_exibicao
    ].copy()


    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# DADOS
# ============================================================

elif pagina == "📋 Dados":

    st.subheader("Dados e validação")


    # --------------------------------------------------------
    # COMPARAÇÃO ANTES / DEPOIS
    # --------------------------------------------------------

    if "Visita Realizada" in df.columns:

        registros_visita = len(
            df[
                df["Visita Realizada"] == "SIM"
            ]
        )

    else:

        registros_visita = 0


    eventos_unicos = df_visitas[
        "Evento"
    ].nunique()


    duplicados_removidos = (
        registros_visita
        - eventos_unicos
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        card(
            "Registros de visita",
            registros_visita,
            "Linhas com Visita Realizada = SIM"
        )


    with col2:

        card(
            "Eventos únicos",
            eventos_unicos,
            "Regra de 1 visita por evento"
        )


    with col3:

        card(
            "Duplicidades removidas",
            duplicados_removidos,
            "Registros desconsiderados"
        )


    st.markdown("---")


    # --------------------------------------------------------
    # DUPLICADOS
    # --------------------------------------------------------

    st.subheader(
        "🔎 Eventos que estavam duplicados"
    )


    if "Visita Realizada" in df.columns:

        visitas_originais = df[
            df["Visita Realizada"] == "SIM"
        ].copy()


        contagem_eventos = (
            visitas_originais
            .groupby("Evento")
            .size()
            .reset_index(
                name="Quantidade de registros"
            )
        )


        duplicados = contagem_eventos[
            contagem_eventos[
                "Quantidade de registros"
            ] > 1
        ].sort_values(
            "Quantidade de registros",
            ascending=False
        )


        if not duplicados.empty:

            st.warning(
                f"Foram encontrados "
                f"**{len(duplicados)} eventos duplicados**. "
                f"Todos passam a contar como uma única visita."
            )


            st.dataframe(
                duplicados,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.success(
                "Nenhum evento duplicado encontrado."
            )


    st.markdown("---")


    # --------------------------------------------------------
    # BASE FINAL
    # --------------------------------------------------------

    st.subheader(
        "Base utilizada pelo painel"
    )


    st.caption(
        f"{len(df_filtrado):,} registros após filtros e "
        f"deduplicação por Evento."
    )


    st.dataframe(
        df_filtrado,
        use_container_width=True,
        hide_index=True
    )