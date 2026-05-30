# ============================================================
# Ejercicio 3 — BAC SSC: Asignación de Operaciones SWIFT
# Modelo de Asignación Binaria — Min tiempo total de procesamiento
# II-1122 | UCR Alajuela
# ============================================================

set ANALISTAS;
set OPERACIONES;

param tiempo{i in ANALISTAS, j in OPERACIONES} >= 0;
param disponible{i in ANALISTAS, j in OPERACIONES} binary;

var x{i in ANALISTAS, j in OPERACIONES} binary;

# Objetivo: minimizar tiempo total de procesamiento
minimize Tiempo_total:
    sum{i in ANALISTAS, j in OPERACIONES} tiempo[i,j] * x[i,j];

# Restricción 1: cada operación debe ser asignada a exactamente 1 analista
s.t. Op{j in OPERACIONES}:
    sum{i in ANALISTAS} x[i,j] = 1;

# Restricción 2: cada analista recibe exactamente 1 operación
s.t. An{i in ANALISTAS}:
    sum{j in OPERACIONES} x[i,j] = 1;

# Restricción 3: compliance Bridger (celdas bloqueadas = 0)
s.t. Comp{i in ANALISTAS, j in OPERACIONES}:
    x[i,j] <= disponible[i,j];
