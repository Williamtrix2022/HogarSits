# HogarSits — Validación de los modelos: parámetros estimados frente a simulados

**Versión:** 1.0 · **Fecha:** 2026-11-23 · **Sprint:** 6 · **Issue:** #41 (RF-61, HU-10)
**Código:** `apps/analitica/services/validacion.py` · `python manage.py validar_modelos` · **Pruebas:** `tests/test_validacion.py` (28)

## 1. Qué se valida y cómo
Como el simulador (`simulacion.py`) **conoce** λ, μ y P verdaderos, se corren sobre sus datos los mismos servicios que usa el panel de Análisis y se mide **cuánto se equivocan**. Cada escenario se repite con 20 semillas distintas (120 días simulados) y se resume el sesgo, la dispersión y el error relativo medio y en el percentil 95.

> **Qué demuestra y qué no.** Demuestra que **el código estima bien cuando los datos cumplen los supuestos del modelo** (llegadas de Poisson, servicio exponencial, matriz estacionaria). **No** demuestra que una inmobiliaria real cumpla esos supuestos: eso solo lo dirán datos reales (la ronda 2 y el piloto). Es una prueba de consistencia del código, no de realismo.

## 2. Resumen
| Hallazgo | Evidencia |
|---|---|
| **λ, μ y los pasos esperados se recuperan con error de 1 a 2 %** | Error relativo medio de 1,2 a 1,9 % (λ), 1,4 a 2,2 % (μ) y 1,0 a 1,7 % (pasos) en los seis escenarios; sesgo despreciable |
| **P(cierre) es la medida más ruidosa** | 2,6 a 6,5 % de error medio con 120 días, y hasta ~12 % en el percentil 95 |
| **El error baja al tener más datos** | P(cierre): 10,2 % con 30 días, 5,0 % con 90, 2,2 % con 300 (§4) |
| **Con 30 días, solo la mitad de las horas llega al mínimo de datos** | 51 % de franjas con ≥ 30 llegadas: el aviso de RN-40 es necesario, no decorativo |
| **La prueba χ² de Poisson está bien calibrada** | Rechaza 3,8 a 5,5 % de las veces con datos que sí son de Poisson (esperado 5 %); una corrida dio 9,5 %, que resultó azar (§8) |
| **⚠️ El modelo de esperas M/M/c NO predice la espera simulada** | Simulada 9,7 min frente a 0,15 / 1,6 / 12,3 según cómo se defina c (§5) |

## 3. Resultados por escenario
Los seis escenarios son los de [`../investigacion/SUPUESTOS_DE_TRABAJO.md`](../investigacion/SUPUESTOS_DE_TRABAJO.md): son **hipótesis**, no datos de campo. Tablas generadas por el comando; «Error rel.» es el valor absoluto.

Réplicas por escenario: 20 · días simulados: 120 · semilla base: 100

### Escenario «base»

λ = 12 clientes/día · 3 asesores · servicio medio 25 min · 8:00 a 18:00 · visitas 30–120 min.

| Parámetro | Verdadero | Estimado (media) | Sesgo | Desv. entre réplicas | Error rel. medio (abs.) | Error rel. p95 (abs.) |
|---|---:|---:|---:|---:|---:|---:|
| λ por día laboral (clientes/día) | 12,000 | 11,987 | -0,013 | 0,273 | 1,7 % | 4,4 % |
| μ (clientes/hora por asesor) | 2,400 | 2,419 | 0,019 | 0,060 | 1,9 % | 5,2 % |
| P(cierre desde Consulta) (probabilidad) | 0,227 | 0,225 | -0,002 | 0,014 | 5,5 % | 9,9 % |
| Pasos esperados desde Consulta (seguimientos) | 2,399 | 2,386 | -0,013 | 0,042 | 1,3 % | 3,2 % |

- Error máximo de una entrada de P (media de réplicas): 0,031.
- Error máximo de λ por hora (media de réplicas): 0,19 clientes/hora.
- Franjas con datos suficientes (RN-40): 100 %.
- Tasa de rechazo del χ² de Poisson: 5,5 % (esperado ≈ 5 %, porque los datos SÍ son de Poisson).
- Réplicas sin datos suficientes para P(cierre): 0 de 20.

| Espera media (min) | Valor |
|---|---:|
| **Simulada** | **9,71** |
| M/M/c con c nominal (3) | 0,15 |
| M/M/c con c efectivo (promedio 1,81, redondeado) | 1,63 |
| M/M/c hora por hora (c efectivo de cada hora) | 12,27 |

### Escenario «oficina cargada»

λ = 20 clientes/día · 2 asesores · servicio medio 45 min · 7:00 a 19:00 · visitas 30–120 min.

| Parámetro | Verdadero | Estimado (media) | Sesgo | Desv. entre réplicas | Error rel. medio (abs.) | Error rel. p95 (abs.) |
|---|---:|---:|---:|---:|---:|---:|
| λ por día laboral (clientes/día) | 20,000 | 20,046 | 0,046 | 0,386 | 1,5 % | 3,4 % |
| μ (clientes/hora por asesor) | 1,333 | 1,328 | -0,006 | 0,027 | 1,7 % | 3,5 % |
| P(cierre desde Consulta) (probabilidad) | 0,227 | 0,226 | -0,002 | 0,007 | 2,6 % | 6,1 % |
| Pasos esperados desde Consulta (seguimientos) | 2,399 | 2,385 | -0,013 | 0,026 | 1,0 % | 2,1 % |

- Error máximo de una entrada de P (media de réplicas): 0,022.
- Error máximo de λ por hora (media de réplicas): 0,24 clientes/hora.
- Franjas con datos suficientes (RN-40): 100 %.
- Tasa de rechazo del χ² de Poisson: 3,8 % (esperado ≈ 5 %, porque los datos SÍ son de Poisson).
- Réplicas sin datos suficientes para P(cierre): 0 de 20.

| Espera media (min) | Valor |
|---|---:|
| **Simulada** | **242,90** |
| M/M/c con c nominal (2) | 29,77 |
| M/M/c con c efectivo (promedio 0,43, redondeado) | n/d |
| M/M/c hora por hora (c efectivo de cada hora) | n/d |

### Escenario «oficina cargada + 3er asesor»

λ = 20 clientes/día · 3 asesores · servicio medio 45 min · 7:00 a 19:00 · visitas 30–120 min.

| Parámetro | Verdadero | Estimado (media) | Sesgo | Desv. entre réplicas | Error rel. medio (abs.) | Error rel. p95 (abs.) |
|---|---:|---:|---:|---:|---:|---:|
| λ por día laboral (clientes/día) | 20,000 | 20,024 | 0,024 | 0,331 | 1,2 % | 3,0 % |
| μ (clientes/hora por asesor) | 1,333 | 1,329 | -0,005 | 0,028 | 1,6 % | 3,5 % |
| P(cierre desde Consulta) (probabilidad) | 0,227 | 0,226 | -0,001 | 0,008 | 2,7 % | 6,6 % |
| Pasos esperados desde Consulta (seguimientos) | 2,399 | 2,385 | -0,014 | 0,027 | 1,0 % | 2,2 % |

- Error máximo de una entrada de P (media de réplicas): 0,022.
- Error máximo de λ por hora (media de réplicas): 0,24 clientes/hora.
- Franjas con datos suficientes (RN-40): 100 %.
- Tasa de rechazo del χ² de Poisson: 5,4 % (esperado ≈ 5 %, porque los datos SÍ son de Poisson).
- Réplicas sin datos suficientes para P(cierre): 0 de 20.

| Espera media (min) | Valor |
|---|---:|
| **Simulada** | **70,17** |
| M/M/c con c nominal (3) | 4,09 |
| M/M/c con c efectivo (promedio 1,37, redondeado) | n/d |
| M/M/c hora por hora (c efectivo de cada hora) | n/d |

### Escenario «oficina cargada, visitas cortas»

λ = 20 clientes/día · 2 asesores · servicio medio 45 min · 7:00 a 19:00 · visitas 30–45 min.

| Parámetro | Verdadero | Estimado (media) | Sesgo | Desv. entre réplicas | Error rel. medio (abs.) | Error rel. p95 (abs.) |
|---|---:|---:|---:|---:|---:|---:|
| λ por día laboral (clientes/día) | 20,000 | 20,008 | 0,008 | 0,321 | 1,2 % | 3,0 % |
| μ (clientes/hora por asesor) | 1,333 | 1,327 | -0,006 | 0,025 | 1,4 % | 3,6 % |
| P(cierre desde Consulta) (probabilidad) | 0,227 | 0,226 | -0,001 | 0,008 | 2,6 % | 6,7 % |
| Pasos esperados desde Consulta (seguimientos) | 2,399 | 2,385 | -0,014 | 0,027 | 1,0 % | 2,2 % |

- Error máximo de una entrada de P (media de réplicas): 0,022.
- Error máximo de λ por hora (media de réplicas): 0,24 clientes/hora.
- Franjas con datos suficientes (RN-40): 100 %.
- Tasa de rechazo del χ² de Poisson: 4,2 % (esperado ≈ 5 %, porque los datos SÍ son de Poisson).
- Réplicas sin datos suficientes para P(cierre): 0 de 20.

| Espera media (min) | Valor |
|---|---:|
| **Simulada** | **103,20** |
| M/M/c con c nominal (2) | 29,59 |
| M/M/c con c efectivo (promedio 0,94, redondeado) | n/d |
| M/M/c hora por hora (c efectivo de cada hora) | n/d |

### Escenario «más permanencia»

λ = 12 clientes/día · 3 asesores · servicio medio 25 min · 8:00 a 18:00 · visitas 30–120 min.

| Parámetro | Verdadero | Estimado (media) | Sesgo | Desv. entre réplicas | Error rel. medio (abs.) | Error rel. p95 (abs.) |
|---|---:|---:|---:|---:|---:|---:|
| λ por día laboral (clientes/día) | 12,000 | 12,036 | 0,036 | 0,284 | 1,9 % | 4,8 % |
| μ (clientes/hora por asesor) | 2,400 | 2,402 | 0,002 | 0,071 | 2,2 % | 5,4 % |
| P(cierre desde Consulta) (probabilidad) | 0,228 | 0,230 | 0,002 | 0,018 | 6,5 % | 11,9 % |
| Pasos esperados desde Consulta (seguimientos) | 3,112 | 3,110 | -0,002 | 0,066 | 1,7 % | 3,8 % |

- Error máximo de una entrada de P (media de réplicas): 0,030.
- Error máximo de λ por hora (media de réplicas): 0,21 clientes/hora.
- Franjas con datos suficientes (RN-40): 100 %.
- Tasa de rechazo del χ² de Poisson: 9,5 % (esperado ≈ 5 %, porque los datos SÍ son de Poisson).
- Réplicas sin datos suficientes para P(cierre): 0 de 20.

| Espera media (min) | Valor |
|---|---:|
| **Simulada** | **9,79** |
| M/M/c con c nominal (3) | 0,15 |
| M/M/c con c efectivo (promedio 1,82, redondeado) | 1,68 |
| M/M/c hora por hora (c efectivo de cada hora) | 13,30 |

### Escenario «seguimiento lento»

λ = 12 clientes/día · 3 asesores · servicio medio 25 min · 8:00 a 18:00 · visitas 30–120 min.

| Parámetro | Verdadero | Estimado (media) | Sesgo | Desv. entre réplicas | Error rel. medio (abs.) | Error rel. p95 (abs.) |
|---|---:|---:|---:|---:|---:|---:|
| λ por día laboral (clientes/día) | 12,000 | 12,018 | 0,018 | 0,287 | 1,6 % | 4,6 % |
| μ (clientes/hora por asesor) | 2,400 | 2,414 | 0,014 | 0,056 | 2,0 % | 3,9 % |
| P(cierre desde Consulta) (probabilidad) | 0,227 | 0,226 | -0,001 | 0,013 | 5,0 % | 10,0 % |
| Pasos esperados desde Consulta (seguimientos) | 2,399 | 2,389 | -0,010 | 0,037 | 1,2 % | 2,7 % |

- Error máximo de una entrada de P (media de réplicas): 0,031.
- Error máximo de λ por hora (media de réplicas): 0,19 clientes/hora.
- Franjas con datos suficientes (RN-40): 100 %.
- Tasa de rechazo del χ² de Poisson: 4,0 % (esperado ≈ 5 %, porque los datos SÍ son de Poisson).
- Réplicas sin datos suficientes para P(cierre): 0 de 20.

| Espera media (min) | Valor |
|---|---:|
| **Simulada** | **9,89** |
| M/M/c con c nominal (3) | 0,15 |
| M/M/c con c efectivo (promedio 1,84, redondeado) | 1,65 |
| M/M/c hora por hora (c efectivo de cada hora) | 12,06 |

### Error según los días de datos (escenario base)

| Días | λ día: error rel. medio | μ: error rel. medio | P(cierre): error rel. medio | P(cierre): error rel. p95 | Franjas suficientes | Sin P(cierre) |
|---:|---:|---:|---:|---:|---:|---:|
| 30 | 4,0 % | 4,7 % | 10,2 % | 22,5 % | 51 % | 0 de 20 |
| 90 | 2,7 % | 2,1 % | 5,0 % | 9,7 % | 100 % | 0 de 20 |
| 300 | 1,1 % | 1,3 % | 2,2 % | 4,2 % | 100 % | 0 de 6 |

## 4. Cuántos datos hacen falta
La última tabla de arriba es el resultado más útil para el uso real: el error de las estimaciones **baja aproximadamente con la raíz del número de datos**, y el mínimo de datos por franja (RN-40) no se alcanza con un mes. En la práctica: **con menos de ~90 días de datos, las cifras del panel son orientativas** (P(cierre) con ±10 % de error relativo típico y la mitad de las horas sin datos suficientes). Con ~300 días el error de P(cierre) baja a ~2 %.

## 5. El límite importante: la espera estimada con M/M/c
Los parámetros se recuperan bien, pero **la espera que predice el modelo no se parece a la simulada**:

| Escenario | Espera simulada (min) | M/M/c, c nominal | M/M/c, c efectivo | M/M/c, hora por hora |
|---|---:|---:|---:|---:|
| base (3 asesores) | **9,7** | 0,15 | 1,6 | 12,3 |
| oficina cargada (2 asesores) | **242,9** | 29,8 | inestable | inestable |
| oficina cargada + 3er asesor | **70,2** | 4,1 | inestable | inestable |
| oficina cargada, visitas cortas | **103,2** | 29,6 | inestable | inestable |

**Qué se observa (hechos):**
- Con c nominal el modelo **subestima** la espera entre 3,5 y 65 veces (según el escenario).
- El modelo acierta la **dirección**: pasar de 2 a 3 asesores baja la espera simulada de 243 a 70 min, y la del modelo, de 29,8 a 4,1.
- En los escenarios de oficina cargada, el promedio de asesores *realmente libres* (descontando visitas) es de 0,43 a 1,4, aunque haya 2 o 3 contratados. Por eso el modelo con c efectivo dice «inestable», lo cual es coherente con las esperas de horas de la simulación.
- El único caso en que se acerca es el escenario base **hora por hora** (12,3 frente a 9,7), pero se vuelve inutilizable cuando alguna hora es inestable.

**Por qué (hipótesis, no probadas aquí):** M/M/c supone servidores siempre disponibles y llegadas estables; en este sistema las **visitas sacan a los asesores de la oficina** de forma irregular y las llegadas tienen picos, así que un promedio esconde las horas en que la fila se forma. Además el redondeo de c a un entero (1,8 → 2; 1,4 → 1) cambia mucho el resultado.

**Consecuencias para el panel de Análisis:**
1. Las **esperas en minutos** que muestra son una aproximación de **orden de magnitud**; sirven para comparar «con más asesores, ¿baja?» (la dirección es correcta) pero no como pronóstico exacto. El panel debe decirlo.
2. Es más fiable el cálculo **por franja** que el de un promedio del día.
3. Las cifras de λ, μ y de probabilidad de cierre **sí** son fiables dentro de las tolerancias de §3 y §4.

## 6. Otros límites
- **Supuestos del simulador:** servicio exponencial (con un mínimo de 1 min, sesgo ≈ +0,02 min), llegadas de Poisson y matriz constante. Los datos reales pueden violarlos.
- **Un solo tipo de recurso:** los asesores hacen consultas y visitas; no se modelan descansos, ausencias ni canales (teléfono, WhatsApp).
- **c efectivo** solo descuenta visitas, no las consultas en curso.
- **Escenarios hipotéticos:** los seis son supuestos de trabajo; el comportamiento real puede ser distinto.
- **Semillas:** los números dependen de las semillas (base 100) y de la versión del simulador; el comando los regenera.

## 7. Cómo reproducirlo
```
python manage.py validar_modelos --escenario todos --por-tamano --replicas 20 --informe validacion.md
python manage.py validar_modelos --escenario "oficina cargada" --dias 300 --replicas 40
```
No lee ni escribe la base de datos. La consola muestra solo ASCII (la de Windows no imprime λ); el informe se guarda en UTF-8.

## 8. Una anomalía que se investigó
En la primera corrida, el escenario «más permanencia» rechazó el χ² de Poisson el 9,5 % de las veces, el doble de lo esperado. Como ese escenario solo cambia la matriz de etapas (y no las llegadas), se repitió con otras tres semillas y 40 réplicas (1 200 pruebas): **5,2 %, 4,5 % y 4,8 %**. Era azar (un evento de cola de ~1 %), no un defecto de la prueba.
