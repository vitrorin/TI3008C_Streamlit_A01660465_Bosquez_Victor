
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Tablero ejecutivo de operación",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def cargar_datos() -> pd.DataFrame:
    """Carga los datos que utilizará la aplicación."""
    datos = pd.read_csv("datos_ejemplo.csv")
    datos["Fecha"] = pd.to_datetime(datos["Fecha"])
    return datos


df = cargar_datos()

st.title("Tablero ejecutivo de operación")
st.caption(
    "Monitorea casos atendidos, tiempo de atención y satisfacción por área y región. "
    "Usa los filtros de la barra lateral; todos los indicadores, gráficas y tablas "
    "se actualizan con tu selección."
)

st.write("**Desarrollado por:** Victor D. Bosquez")

# ----------------------------------------------------------------
# Filtros
# ----------------------------------------------------------------
st.sidebar.header("Filtros")

areas_disponibles = sorted(df["Área"].unique())
areas_seleccionadas = st.sidebar.multiselect(
    "Área",
    options=areas_disponibles,
    default=areas_disponibles,
)

regiones_disponibles = sorted(df["Región"].unique())
regiones_seleccionadas = st.sidebar.multiselect(
    "Región",
    options=regiones_disponibles,
    default=regiones_disponibles,
)

satisfaccion_minima = st.sidebar.slider(
    "Satisfacción mínima",
    min_value=int(df["Satisfacción"].min()),
    max_value=int(df["Satisfacción"].max()),
    value=int(df["Satisfacción"].min()),
    help="Muestra solo los registros con una satisfacción igual o mayor a este valor.",
)

df_filtrado = df[
    df["Área"].isin(areas_seleccionadas)
    & df["Región"].isin(regiones_seleccionadas)
    & (df["Satisfacción"] >= satisfaccion_minima)
].copy()

if df_filtrado.empty:
    st.warning(
        "No hay registros con los filtros seleccionados. "
        "Agrega áreas o regiones, o reduce la satisfacción mínima."
    )
    st.stop()

# ----------------------------------------------------------------
# Indicadores (se comparan contra el total de los datos)
# ----------------------------------------------------------------
total_casos = int(df_filtrado["Casos"].sum())
tiempo_promedio = df_filtrado["Tiempo_min"].mean()
satisfaccion_promedio = df_filtrado["Satisfacción"].mean()
participacion = total_casos / df["Casos"].sum() * 100

col_1, col_2, col_3, col_4 = st.columns(4)
with col_1:
    st.metric("Casos atendidos", f"{total_casos:,}", border=True)
with col_2:
    st.metric(
        "% del total de casos",
        f"{participacion:.1f}%",
        border=True,
    )
with col_3:
    st.metric(
        "Tiempo promedio (min)",
        f"{tiempo_promedio:.1f}",
        delta=f"{tiempo_promedio - df['Tiempo_min'].mean():.1f} vs. general",
        delta_color="inverse",
        border=True,
    )
with col_4:
    st.metric(
        "Satisfacción promedio",
        f"{satisfaccion_promedio:.1f}",
        delta=f"{satisfaccion_promedio - df['Satisfacción'].mean():.1f} vs. general",
        border=True,
    )

# ----------------------------------------------------------------
# Vistas
# ----------------------------------------------------------------
tab_resumen, tab_detalle = st.tabs(["Resumen", "Detalle"])

with tab_resumen:
    st.subheader("Tendencia y comparación por área")

    casos_por_fecha = (
        df_filtrado.groupby("Fecha", as_index=False)["Casos"]
        .sum()
        .sort_values("Fecha")
    )
    fig_linea = px.line(
        casos_por_fecha,
        x="Fecha",
        y="Casos",
        markers=True,
        title="Casos por semana",
    )

    resumen_area = (
        df_filtrado.groupby("Área", as_index=False)
        .agg(
            Casos=("Casos", "sum"),
            Tiempo_promedio=("Tiempo_min", "mean"),
            Satisfacción_promedio=("Satisfacción", "mean"),
        )
        .sort_values("Casos", ascending=False)
    )
    fig_barras = px.bar(
        resumen_area,
        x="Área",
        y="Casos",
        color="Satisfacción_promedio",
        color_continuous_scale="Blues",
        title="Casos por área (color = satisfacción promedio)",
        labels={"Satisfacción_promedio": "Satisfacción"},
    )

    grafica_1, grafica_2 = st.columns(2)
    with grafica_1:
        st.plotly_chart(fig_linea, width="stretch")
    with grafica_2:
        st.plotly_chart(fig_barras, width="stretch")

    area_lider = resumen_area.iloc[0]
    area_lenta = resumen_area.sort_values("Tiempo_promedio", ascending=False).iloc[0]
    st.info(
        f"**{area_lider['Área']}** concentra más casos en la selección "
        f"({int(area_lider['Casos'])}), mientras que **{area_lenta['Área']}** "
        f"tiene el mayor tiempo promedio de atención "
        f"({area_lenta['Tiempo_promedio']:.1f} min)."
    )

with tab_detalle:
    st.subheader("Resumen por área")
    st.dataframe(
        resumen_area,
        width="stretch",
        hide_index=True,
        column_config={
            "Tiempo_promedio": st.column_config.NumberColumn(
                "Tiempo promedio (min)", format="%.1f"
            ),
            "Satisfacción_promedio": st.column_config.NumberColumn(
                "Satisfacción promedio", format="%.1f"
            ),
        },
    )

    st.subheader(f"Registros visibles ({len(df_filtrado)})")
    st.dataframe(
        df_filtrado.sort_values("Fecha"),
        width="stretch",
        hide_index=True,
        column_config={
            "Fecha": st.column_config.DateColumn("Fecha", format="YYYY-MM-DD"),
            "Tiempo_min": st.column_config.NumberColumn("Tiempo (min)", format="%.1f"),
        },
    )
