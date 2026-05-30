"""
Ejercicio 3 — BAC SSC: Operaciones SWIFT
Solución con PuLP (equivalente al modelo AMPL) + Streamlit
II-1122 | UCR Alajuela
"""

import streamlit as st
import pandas as pd
from pulp import (
    LpProblem, LpMinimize, LpVariable, lpSum,
    value, LpStatus, PULP_CBC_CMD
)

# ── Datos del problema ────────────────────────────────────────
ANALISTAS   = ["Andrea (A)", "Beatriz (B)", "Carlos (C)", "Daniel (D)", "Esteban (E)"]
OPERACIONES = ["MT103", "MT202", "MT700", "MT760", "MT940"]
OP_DESC     = {
    "MT103": "Transferencia cliente → Panamá",
    "MT202": "Transferencia interbancaria → Guatemala",
    "MT700": "Carta de crédito (LC) → Honduras",
    "MT760": "Garantía bancaria",
    "MT940": "Reporte de cuenta",
}

# Tiempos en minutos (0 donde la celda está bloqueada)
TIEMPOS = {
    "Andrea (A)":  {"MT103": 25, "MT202": 30, "MT700":  0, "MT760":  0, "MT940": 20},
    "Beatriz (B)": {"MT103": 35, "MT202": 28, "MT700": 40, "MT760": 45, "MT940": 22},
    "Carlos (C)":  {"MT103": 40, "MT202": 45, "MT700": 35, "MT760": 30, "MT940": 25},
    "Daniel (D)":  {"MT103": 30, "MT202": 32, "MT700": 50, "MT760":  0, "MT940": 18},
    "Esteban (E)": {"MT103":  0, "MT202":  0, "MT700": 30, "MT760": 28, "MT940": 30},
}

# Disponibilidad Bridger (1 = puede, 0 = bloqueado)
DISPONIBLE = {
    "Andrea (A)":  {"MT103": 1, "MT202": 1, "MT700": 0, "MT760": 0, "MT940": 1},
    "Beatriz (B)": {"MT103": 1, "MT202": 1, "MT700": 1, "MT760": 1, "MT940": 1},
    "Carlos (C)":  {"MT103": 1, "MT202": 1, "MT700": 1, "MT760": 1, "MT940": 1},
    "Daniel (D)":  {"MT103": 1, "MT202": 1, "MT700": 1, "MT760": 0, "MT940": 1},
    "Esteban (E)": {"MT103": 0, "MT202": 0, "MT700": 1, "MT760": 1, "MT940": 1},
}

# ── Solver ────────────────────────────────────────────────────
def resolver():
    prob = LpProblem("BAC_SWIFT_Assignment", LpMinimize)

    # Variables binarias x[i][j]
    x = {
        (i, j): LpVariable(f"x_{i[:1]}_{j}", cat="Binary")
        for i in ANALISTAS for j in OPERACIONES
    }

    # Objetivo
    prob += lpSum(
        TIEMPOS[i][j] * x[i, j]
        for i in ANALISTAS for j in OPERACIONES
    )

    # Cada operación → exactamente 1 analista
    for j in OPERACIONES:
        prob += lpSum(x[i, j] for i in ANALISTAS) == 1, f"Op_{j}"

    # Cada analista → exactamente 1 operación
    for i in ANALISTAS:
        prob += lpSum(x[i, j] for j in OPERACIONES) == 1, f"An_{i[:1]}"

    # Compliance Bridger
    for i in ANALISTAS:
        for j in OPERACIONES:
            if DISPONIBLE[i][j] == 0:
                prob += x[i, j] == 0, f"Comp_{i[:1]}_{j}"

    prob.solve(PULP_CBC_CMD(msg=0))
    return prob, x

# ── Interfaz Streamlit ────────────────────────────────────────
st.set_page_config(page_title="BAC SSC — SWIFT Optimizer", page_icon="🏦", layout="wide")

st.title("🏦 BAC SSC — Asignación de Operaciones SWIFT")
st.caption("Ejercicio 3 · II-1122 Programación Entera Mixta · UCR Alajuela")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📋 Matriz de tiempos (min)")

    # Construir DataFrame con indicador de bloqueo
    df_display = pd.DataFrame(TIEMPOS).T
    df_display.index.name = "Analista"

    def highlight_blocked(val, i, j):
        if DISPONIBLE[i][j] == 0:
            return "background-color: #ffe0e0; color: #cc0000; font-weight: bold"
        return ""

    # Mostrar con formato
    styled = df_display.style.format(
        lambda v: "🚫" if v == 0 else str(v)
    ).set_table_styles([
        {"selector": "th", "props": [("background-color", "#8b0000"), ("color", "white")]}
    ])
    st.dataframe(styled, use_container_width=True)

    st.caption("🚫 = bloqueado por compliance Bridger")

    st.subheader("⚠️ Restricciones Bridger")
    st.markdown("""
    - **Andrea**: no puede ejecutar MT700 ni MT760  
    - **Daniel**: no puede ejecutar MT760  
    - **Esteban**: no puede ejecutar MT103 ni MT202  
    """)

with col2:
    st.subheader("🔧 Modelo AMPL (referencia)")
    st.code("""set ANALISTAS;
set OPERACIONES;

param tiempo{i in ANALISTAS, j in OPERACIONES} >= 0;
param disponible{i in ANALISTAS, j in OPERACIONES} binary;

var x{i in ANALISTAS, j in OPERACIONES} binary;

minimize Tiempo_total:
  sum{i in ANALISTAS, j in OPERACIONES}
    tiempo[i,j] * x[i,j];

s.t. Op{j in OPERACIONES}:
  sum{i in ANALISTAS} x[i,j] = 1;

s.t. An{i in ANALISTAS}:
  sum{j in OPERACIONES} x[i,j] = 1;

s.t. Comp{i in ANALISTAS, j in OPERACIONES}:
  x[i,j] <= disponible[i,j];""", language="text")

st.divider()

# ── Resolver ─────────────────────────────────────────────────
if st.button("🚀 Resolver con CBC", type="primary", use_container_width=True):
    with st.spinner("Optimizando asignación..."):
        prob, x = resolver()

    status = LpStatus[prob.status]

    if status == "Optimal":
        st.success(f"✅ Solución óptima encontrada — Estado: {status}")

        # Extraer solución
        asignaciones = []
        for i in ANALISTAS:
            for j in OPERACIONES:
                if value(x[i, j]) > 0.5:
                    asignaciones.append({
                        "Analista": i,
                        "Operación": j,
                        "Descripción": OP_DESC[j],
                        "Tiempo (min)": TIEMPOS[i][j],
                    })

        df_sol = pd.DataFrame(asignaciones)
        tiempo_total = df_sol["Tiempo (min)"].sum()

        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("⏱️ Tiempo total", f"{tiempo_total} min")
        m2.metric("👥 Analistas asignados", len(df_sol))
        m3.metric("📄 Operaciones cubiertas", df_sol["Operación"].nunique())

        st.subheader("📊 Asignación óptima")
        st.dataframe(
            df_sol.style.set_properties(**{"text-align": "left"})
                  .highlight_max(subset=["Tiempo (min)"], color="#fff3cd")
                  .highlight_min(subset=["Tiempo (min)"], color="#d4edda"),
            use_container_width=True,
            hide_index=True,
        )

        # Tabla resumen tipo tablero de control
        st.subheader("🗂️ Vista de tablero")
        pivot = pd.DataFrame(index=ANALISTAS, columns=OPERACIONES, data="")
        for row in asignaciones:
            pivot.loc[row["Analista"], row["Operación"]] = f"✅ {row['Tiempo (min)']} min"

        st.dataframe(pivot, use_container_width=True)

    else:
        st.error(f"❌ No se encontró solución óptima. Estado: {status}")
