---
name: modelo-estocastico
description: Guía para añadir un modelo estocástico nuevo a HogarSits (p. ej. otro tipo de cola o una estimación nueva) con su prueba contra un ejemplo conocido. Usar cuando se vaya a crear o ampliar un módulo de apps/analitica/services/.
---

# modelo-estocastico

Añade un modelo a `apps/analitica/services/` siguiendo el método de los tres módulos que ya existen (`poisson.py`, `colas.py`, `markov.py`). El orden importa: **primero el ejemplo conocido, después el código**.

## 1. Antes de escribir código
1. **Escribe la fórmula y el supuesto** en una frase cada uno (qué modelo es, qué hay que cumplir para que valga: independencia, estacionariedad, servicio exponencial…).
2. **Busca un ejemplo con respuesta conocida**: de la Propuesta, del README, de un libro, o calculable a mano. Anota los números esperados. Si no hay ninguno, **detente**: sin un valor de referencia no se puede saber si el módulo está bien.
3. **Define las unidades** (clientes por hora, minutos…) y quién convierte: el módulo trabaja en una sola unidad.

## 2. El módulo
- **Python puro:** nada de `import django`. Entra y sale información simple (números, `datetime`, listas, `@dataclass(frozen=True)`).
- **Estructura:** funciones pequeñas y un `@dataclass` con el resultado. Un docstring de módulo con la fórmula, las unidades, los supuestos y **cuándo el modelo no vale**.
- **Entradas inválidas → `ValueError`** con un mensaje que dice qué corregir (no `assert`, no `None` silencioso).
- **Pocos datos no se inventan:** si faltan observaciones, el resultado lo dice (`suficiente`, `faltan`) y no se rellena (RN-40, RN-43). Un número que no se puede calcular es `None`, no `0`.
- **Condiciones de validez:** si el modelo deja de valer (p. ej. ρ ≥ 1), se devuelve «no estable», no cifras sin sentido (RN-41).
- **Hora local:** cualquier franja se calcula en `America/Bogota` (RN-42).
- **Estabilidad numérica:** logaritmos o recursiones para factoriales y potencias grandes; comprobar con un valor grande.

## 3. Las pruebas (`tests/test_<modelo>.py`, sin base de datos)
Cuatro tipos, todos:
1. **El ejemplo conocido**, con los números esperados del paso 1.2.
2. **Una comprobación independiente**: el mismo resultado por **otro camino** (la cadena de nacimiento y muerte para una cola; `P^k` para una absorción; la fórmula con factoriales para una distribución). Si el código y el otro camino coinciden, es muy difícil que ambos estén mal igual.
3. **Recuperar los parámetros de una simulación** con `simulacion.py` (misma semilla, tolerancia explícita): si el modelo estima λ, μ o P cerca de los valores con que se simuló, el código es correcto.
4. **Los bordes**: vacío, un solo dato, cero, el límite exacto (ρ = 1, `N` exacto), valores enormes, entradas inválidas.

**Si una prueba falla, no ajustes la prueba para que pase.** Averigua si el error está en el código, en la expectativa o en el documento de referencia. (Ejemplo real: la Propuesta dice «≈ 22,8 %» pero el valor exacto es 22,748 %; el test afirma el valor exacto.)

## 4. Cerrar
1. **Lenguaje de negocio (RF-59):** cada cifra nueva necesita una frase que un gerente entienda («de cada 10 clientes, 2 cierran»), sin «λ» ni «P» sueltas. Va en `apps/analitica/textos.py`.
2. **Revisión:** pasa el subagente `revisor-estocastico` sobre el módulo y atiende sus hallazgos.
3. **Documenta** en `docs/aprendizaje/` lo que costó trabajo o sorprendió.
4. `ruff check .` y la prueba del módulo en verde; commit `feat:` en una rama `feature/<n>-descripcion`, PR con `Closes #n`.

## Errores que ya ocurrieron (para no repetirlos)
- Suponer que mezclar horas con picos **siempre** hace que Poisson se rechace: con picos suaves la dispersión es 1,05 y no se rechaza. Se comprobó con la fórmula `1 + Var(λ)/E(λ)`.
- Citar «22,8 %» sin saber que es doble redondeo: se calcula con precisión completa y se redondea **al final**.
- Estimar λ promediando solo las horas con llegadas: **las horas con cero cuentan**.
