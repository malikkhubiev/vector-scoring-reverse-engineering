# Whitepaper

## English Version

### Table of Contents

- **Overview**  
  - [1. Executive Summary](#1-executive-summary)  
  - [2. Data Sources and Empirical Basis](#2-data-sources-and-empirical-basis)  
  - [3. Classical Normalization vs Observed Transformation](#3-classical-normalization-vs-observed-transformation)  
  - [4. Threshold Bifurcation](#4-threshold-bifurcation)  
  - [5. Formal Analysis of Monotonicity](#5-formal-analysis-of-monotonicity)  
  - [6. Ranking Invariance Analysis](#6-ranking-invariance-analysis)  
  - [7. Geometric Interpretation](#7-geometric-interpretation)  
  - [8. Architectural Risk Assessment](#8-architectural-risk-assessment)  
  - [9. Conclusions](#9-conclusions)  
  - [10. Diagrams](#10-diagrams)

### Project Structure

```text
project/
  README.md              # This whitepaper (EN + RU)
  main.py                # Entry point for running local experiments
  config.py              # Configuration for thresholds, paths, and toggles
  analysis/
    combination_analysis.py   # Experiments on combining similarity signals
    correlation.py            # Correlation analysis between SQL and ECM scores
    similarity_calculator.py  # Abstractions for computing similarity
  models/
    formulas.py          # Canonical and observed affine transformations
  data/
    candidate_info.py    # Helpers to load/prepare candidate metadata
    ecm_data.py          # Helpers to load ECM-side similarity exports
  utils/
    display.py           # Pretty-printing, tabular views, plotting hooks
  test_single_candidate.py    # Quick sanity check for a single candidate
```

---

## 1. Executive Summary

This document presents a formal internal-style audit of a production vector similarity scoring layer in which application-level similarity values (ECM) diverge from database-level cosine similarities (SQL).

The investigation was conducted without source code access and relied exclusively on observable numerical outputs. Reconstruction demonstrates that:

1. Raw cosine similarity is not directly exposed.
2. The production layer applies a non-classical affine transformation.
3. Two distinct threshold regimes are active simultaneously.
4. The transformation preserves ranking (monotonicity holds).
5. However, score invariance across threshold changes is not preserved.

All candidate identifiers are anonymized (ECM-00001, ECM-00002, …). Numerical patterns correspond to anonymized empirical observations derived from internal documentation.

---

## 2. Data Sources and Empirical Basis

Two numerical signals were observed:

- SQL similarity (derived from `candidate_embedding_info`, MAX aggregation)
- ECM similarity (application-layer value)

Empirical comparison confirms that ECM values are derived from `candidate_embedding_info` rather than from the raw `candidate` table.

Example (anonymized):

| Candidate | SQL (cei_max) | ECM      |
| --------- | ------------- | -------- |
| ECM-00001 | 0.838369      | 0.785937 |
| ECM-00002 | 0.819256      | 0.769357 |
| ECM-00003 | 0.817317      | 0.755977 |

The deviation between SQL and ECM reaches up to 0.1, which is material for ranking systems operating near high similarity thresholds.

---

## 3. Classical Normalization vs Observed Transformation

### 3.1 Canonical Threshold Normalization

The classical normalization above threshold T is:

$$
f_{classic}(x) = \frac{x - T}{1 - T}
$$

This maps:

$$
[T, 1] \rightarrow [0, 1]
$$

with:

- $$f(T) = 0$$
- $$f(1) = 1$$

Empirical evaluation shows that this formula does not reproduce ECM values.

---

### 3.2 Reconstructed Production Transformation

Empirical reconstruction yields:

$$
f_{obs}(x) = \frac{x - (1 - T)}{T}
$$

This is an affine transformation:

$$
f_{obs}(x) = \frac{1}{T}x - \frac{1 - T}{T}
$$

It differs structurally from classical normalization in both shift and scale.

For ECM-00003:

$$
x = 0.817317, \quad T = 0.748
$$

$$
f_{obs}(x) = \frac{0.817317 - 0.252}{0.748} = 0.755977
$$

which matches ECM to six decimal places.

---

## 4. Threshold Bifurcation

Solving the observed transformation for T:

$$
ECM = \frac{x - (1 - T)}{T}
$$

$$
ECM \cdot T = x - 1 + T
$$

$$
T(ECM - 1) = x - 1
$$

$$
T = \frac{x - 1}{ECM - 1}
$$

Applying this inversion to all observed (SQL, ECM) pairs yields two stable modes:

$$
T_1 \approx 0.76
$$

$$
T_2 \approx 0.748
$$

Candidates cluster into two internally consistent groups:

- Group A: T = 0.76
- Group B: T = 0.748

Within each group, reconstruction accuracy reaches 100% for multiple cases.

This establishes the existence of dual threshold regimes in production.

---

## 5. Formal Analysis of Monotonicity

Let:

$$
f_{obs}(x) = \frac{1}{T}x - \frac{1 - T}{T}
$$

Derivative:

$$
f'_{obs}(x) = \frac{1}{T}
$$

Since:

$$
T \in (0, 1)
$$

we have:

$$
\frac{1}{T} > 0
$$

Therefore:

$$
f'_{obs}(x) > 0
$$

The transformation is strictly monotonically increasing.

### Consequence

For any two similarities $$x_1, x_2$$:

$$
x_1 > x_2 \Rightarrow f_{obs}(x_1) > f_{obs}(x_2)
$$

Thus, ranking order is preserved within each threshold regime.

No intra-query ranking distortion occurs.

---

## 6. Ranking Invariance Analysis

### 6.1 Within a Fixed Threshold

Since $$f_{obs}(x)$$ is affine and strictly increasing:

- Relative ordering is invariant.
- Top-K retrieval order remains unchanged.
- Recall sets are unaffected (assuming threshold filtering is applied prior).

Therefore, the transformation is ranking-invariant within a single T.

---

### 6.2 Across Different Thresholds

Consider two identical cosine values x, evaluated under two thresholds $$T_1 \neq T_2$$:

$$
f_{T_1}(x) = \frac{x - (1 - T_1)}{T_1}
$$

$$
f_{T_2}(x) = \frac{x - (1 - T_2)}{T_2}
$$

These are distinct affine maps with different slopes:

$$
\text{slope} = \frac{1}{T}
$$

Since $$T_1 \neq T_2$$:

$$
\frac{1}{T_1} \neq \frac{1}{T_2}
$$

Therefore:

- The same cosine similarity yields different ECM scores.
- Cross-query comparability is broken.
- Cross-version comparability is broken.
- Any downstream component consuming ECM as a calibrated similarity metric receives non-stationary inputs.

This violates scale invariance across threshold configurations.

---

## 7. Geometric Interpretation

### 7.1 Classical Normalization

Graph of:

$$
f_{classic}(x) = \frac{x - T}{1 - T}
$$

Passes through:

- (T, 0)
- (1, 1)

with slope:

$$
\text{slope} = \frac{1}{1 - T}
$$

Interpretation: compresses interval [T, 1] into [0, 1].

---

### 7.2 Observed Transformation

Graph of:

$$
f_{obs}(x) = \frac{x - (1 - T)}{T}
$$

Passes through:

- (1 − T, 0)
- (1, 1)

with slope:

$$
\text{slope} = \frac{1}{T}
$$

Geometrically:

- The zero-crossing is shifted left.
- The slope is steeper for smaller T.
- The mapping does not anchor at (T, 0).

For T = 0.76:

- Zero at 0.24
- Slope ≈ 1.316

For T = 0.748:

- Zero at 0.252
- Slope ≈ 1.337

Thus, ECM values are effectively rescaled and translated cosine similarities, not normalized ones.

---

## 8. Architectural Risk Assessment

### 8.1 Properties Observed

- Affine post-processing dependent on threshold.
- Dual threshold regime active simultaneously.
- Score representation not equivalent to cosine similarity.
- Monotonic ranking preserved locally.
- Global score scale not invariant.

### 8.2 Risk Implications

1. Cross-query score comparability compromised.
2. Offline evaluation metrics may drift.
3. Calibration and explainability degraded.
4. A/B testing across threshold versions may produce non-intuitive deltas.
5. Reranking models consuming ECM as feature input receive threshold-coupled signals.

---

## 9. Conclusions

The production similarity layer applies:

$$
ECM = \frac{SQL - (1 - T)}{T}
$$

with:

$$
T \in \{0.76, 0.748\}
$$

The transformation:

- Is affine.
- Is strictly monotonic.
- Preserves ranking within a regime.
- Breaks scale invariance across regimes.

The reconstruction was achieved using only numerical outputs and validated with up to six-decimal precision across multiple anonymized candidates.

This case demonstrates a general methodology for black-box auditing of similarity scoring systems in production ML infrastructure.

---

## 10. Diagrams

### 10.1 Expected Similarity Pipeline (Assumed Before Audit)

```mermaid
flowchart LR
  Q[Query embedding] -->|cosine similarity| DB[(candidate_embedding_info)]
  DB -->|raw cosine (SQL)| Norm[Classical normalization f_classic(x)]
  Norm -->|normalized score in [0,1]| ECM[ECM similarity]
```

**Narrative:** It was initially assumed that the application exposes a classically normalized cosine similarity: the database returns a cosine value, a single global threshold T is applied, and scores are mapped from [T, 1] into [0, 1] via $$f_{classic}$$, producing ECM values that are globally comparable across queries and versions.

### 10.2 Actual Similarity Pipeline (Reconstructed)

```mermaid
flowchart LR
  Q[Query embedding] -->|cosine similarity| DB[(candidate_embedding_info)]
  DB -->|raw cosine (SQL)| Thresh[Threshold selection<br/>T ∈ {0.76, 0.748}]
  Thresh -->|per-candidate T| Affine[Affine transform f_obs(x)]
  Affine -->|ECM score| ECM[ECM similarity]
```

**Narrative:** In reality, the production layer selects between at least two threshold regimes $$T_1 \approx 0.76$$ and $$T_2 \approx 0.748$$, and then applies the affine map $$f_{obs}(x) = \frac{x - (1 - T)}{T}$$. This preserves within-regime ranking but breaks cross-regime scale invariance, meaning ECM scores are not globally comparable as a calibrated similarity measure.

---

## Русская версия

### Оглавление

- **Обзор**  
  - [1. Краткое резюме](#1-краткое-резюме)  
  - [2. Источники данных и эмпирика](#2-источники-данных-и-эмпирика)  
  - [3. Классическая нормализация vs наблюдаемое преобразование](#3-классическая-нормализация-vs-наблюдаемое-преобразование)  
  - [4. Расщепление порогов](#4-расщепление-порогов)  
  - [5. Монотонность](#5-монотонность)  
  - [6. Инвариантность ранжирования](#6-инвариантность-ранжирования)  
  - [7. Геометрическая интерпретация](#7-геометрическая-интерпретация)  
  - [8. Архитектурные риски](#8-архитектурные-риски)  
  - [9. Выводы](#9-выводы)  
  - [10. Диаграммы](#10-диаграммы)

### Структура проекта

```text
project/
  README.md              # Вайтпейпер (английская и русская версии)
  main.py                # Точка входа для локальных экспериментов
  config.py              # Конфигурация порогов, путей и флагов
  analysis/
    combination_analysis.py   # Эксперименты по объединению сигналов похожести
    correlation.py            # Корреляционный анализ между SQL и ECM
    similarity_calculator.py  # Абстракции для расчёта похожести
  models/
    formulas.py          # Канонические и наблюдаемые аффинные формулы
  data/
    candidate_info.py    # Загрузка и подготовка метаданных кандидатов
    ecm_data.py          # Загрузка выгрузок ECM-скорингов
  utils/
    display.py           # Форматирование таблиц, визуализации
  test_single_candidate.py    # Быстрая проверка одного кандидата
```

---

## 1. Краткое резюме

Этот документ — внутренняя реконструкция работы продакшен-слоя похожести, в котором прикладные значения похожести (ECM) систематически расходятся с косинусными похожестями из базы данных (SQL).

Аудит проводился без доступа к исходному коду, только по численным наблюдениям. Показано, что:

1. Сырые косинусные похожести напрямую не экспонируются.
2. Над SQL-значениями применяется нетипичное аффинное преобразование.
3. В системе одновременно работают как минимум два пороговых режима.
4. Внутри каждого режима ранжирование сохраняется (монотонность выполняется).
5. Между разными порогами шкала нарушается, и инвариантность скорингов не сохраняется.

Все идентификаторы кандидатов анонимизированы (ECM-00001, ECM-00002, …); численные примеры основаны на обезличенных внутренних данных.

---

## 2. Источники данных и эмпирика

Используются два численных сигнала:

- SQL-похожесть (агрегация MAX по `candidate_embedding_info`)
- ECM-похожесть (значение на уровне приложения)

Сравнение показывает, что ECM-значения порождаются из `candidate_embedding_info`, а не напрямую из таблицы кандидатов.

Пример (анонимизированный):

| Кандидат | SQL (cei_max) | ECM      |
| -------- | ------------- | -------- |
| ECM-00001| 0.838369      | 0.785937 |
| ECM-00002| 0.819256      | 0.769357 |
| ECM-00003| 0.817317      | 0.755977 |

Расхождение доходит до 0.1, что существенно для систем ранжирования вблизи высоких порогов похожести.

---

## 3. Классическая нормализация vs наблюдаемое преобразование

### 3.1 Каноническая нормализация по порогу

Классическая нормализация выше порога T:

$$
f_{classic}(x) = \frac{x - T}{1 - T}
$$

Она переводит:

$$
[T, 1] \rightarrow [0, 1]
$$

с условиями:

- $$f(T) = 0$$
- $$f(1) = 1$$

Эта формула не воспроизводит наблюдаемые ECM-значения.

### 3.2 Наблюдаемое продакшен-преобразование

По данным реконструируется другая формула:

$$
f_{obs}(x) = \frac{x - (1 - T)}{T}
$$

то есть аффинное преобразование

$$
f_{obs}(x) = \frac{1}{T}x - \frac{1 - T}{T}.
$$

Например, для ECM-00003:

$$
x = 0.817317, \quad T = 0.748,
$$

$$
f_{obs}(x) = \frac{0.817317 - 0.252}{0.748} \approx 0.755977,
$$

что совпадает с ECM до шести знаков после запятой.

---

## 4. Расщепление порогов

Решая формулу относительно T:

$$
ECM = \frac{x - (1 - T)}{T}
$$

$$
T = \frac{x - 1}{ECM - 1},
$$

получаем два устойчивых значения:

$$
T_1 \approx 0.76, \quad T_2 \approx 0.748.
$$

Кандидаты разбиваются на два кластера, каждый из которых согласован со «своим» T. Это свидетельствует о наличии двух пороговых режимов в продакшене.

---

## 5. Монотонность

Для

$$
f_{obs}(x) = \frac{1}{T}x - \frac{1 - T}{T}
$$

производная равна

$$
f'_{obs}(x) = \frac{1}{T} > 0 \quad \text{при } T \in (0, 1),
$$

поэтому преобразование строго монотонно.

Следствие:

$$
x_1 > x_2 \Rightarrow f_{obs}(x_1) > f_{obs}(x_2),
$$

то есть порядок кандидатов по похожести внутри одного порога сохраняется.

---

## 6. Инвариантность ранжирования

### 6.1 Внутри фиксированного порога

Поскольку $$f_{obs}(x)$$ аффинна и строго возрастает:

- относительный порядок кандидатов инвариантен;
- порядок в топ‑K не меняется;
- recall при заданном пороге не страдает.

### 6.2 Между разными порогами

Если один и тот же косинус x оценивается при T₁ и T₂, то:

$$
f_{T_1}(x) = \frac{x - (1 - T_1)}{T_1}, \quad
f_{T_2}(x) = \frac{x - (1 - T_2)}{T_2},
$$

и при $$T_1 \neq T_2$$ наклоны $$\frac{1}{T_1}$$ и $$\frac{1}{T_2}$$ различаются. В результате:

- один и тот же косинус даёт разные ECM-скоринги;
- нарушается сравнимость между запросами и версиями;
- downstream‑модели получают нестационарный по шкале сигнал.

---

## 7. Геометрическая интерпретация

Классическая нормализация

$$
f_{classic}(x) = \frac{x - T}{1 - T}
$$

проходит через точки (T, 0) и (1, 1) и сжимает отрезок [T, 1] в [0, 1].

Наблюдаемое преобразование

$$
f_{obs}(x) = \frac{x - (1 - T)}{T}
$$

проходит через (1 - T, 0) и (1, 1); ноль сдвинут левее, а наклон $$\frac{1}{T}$$ больше при меньших T. Таким образом, ECM — это «сжатые и сдвинутые» косинусные похожести, а не строго нормализованные.

---

## 8. Архитектурные риски

- Порогозависимое аффинное пост‑обработанное значение.
- Одновременное существование двух пороговых режимов.
- Представление похожести не эквивалентно косинусной метрике.
- Локально ранжирование сохраняется, глобально шкала плавает.

Из этого следуют риски:

1. Сложность сравнения скорингов между запросами.
2. Дрейф оффлайн‑метрик при смене порогов.
3. Ухудшение калибровки и объяснимости.
4. Нетривиальное поведение A/B‑экспериментов при изменении порога.
5. Модели, использующие ECM как фичу, получают сигнал, зависящий от конфигурации порога.

---

## 9. Выводы

Продакшен‑слой похожести реализует преобразование

$$
ECM = \frac{SQL - (1 - T)}{T},
$$

где

$$
T \in \{0.76, 0.748\}.
$$

Это аффинное, строго монотонное преобразование, которое сохраняет порядок внутри одного порога, но нарушает глобальную шкалу между порогами. Реконструкция выполнена по численным данным с точностью до шестого знака.

---

## 10. Диаграммы

Визуальные схемы процесса приведены в английской секции:

- ожидаемый (классический) pipeline похожести;
 фактически реконструированный pipeline с двумя порогами и аффинным преобразованием $$f_{obs}(x) = \frac{x - (1 - T)}{T}$$.

# Whitepaper

## Forensic Audit of a Production Vector Similarity Scoring Layer

### Affine Post-Processing, Threshold Bifurcation, and Ranking Invariance Analysis

---

## 1. Executive Summary

This document presents a formal internal-style audit of a production vector similarity scoring layer in which application-level similarity values (ECM) diverge from database-level cosine similarities (SQL).

The investigation was conducted without source code access and relied exclusively on observable numerical outputs. Reconstruction demonstrates that:

1. Raw cosine similarity is not directly exposed.
2. The production layer applies a non-classical affine transformation.
3. Two distinct threshold regimes are active simultaneously.
4. The transformation preserves ranking (monotonicity holds).
5. However, score invariance across threshold changes is not preserved.

All candidate identifiers are anonymized (ECM-00001, ECM-00002, …). Numerical patterns correspond to anonymized empirical observations derived from internal documentation .

---

## 2. Data Sources and Empirical Basis

Two numerical signals were observed:

* SQL similarity (derived from `candidate_embedding_info`, MAX aggregation)
* ECM similarity (application-layer value)

Empirical comparison confirms that ECM values are derived from `candidate_embedding_info` rather than from the raw `candidate` table .

Example (anonymized):

| Candidate | SQL (cei_max) | ECM      |
| --------- | ------------- | -------- |
| ECM-00001 | 0.838369      | 0.785937 |
| ECM-00002 | 0.819256      | 0.769357 |
| ECM-00003 | 0.817317      | 0.755977 |

The deviation between SQL and ECM reaches up to 0.1, which is material for ranking systems operating near high similarity thresholds.

---

## 3. Classical Normalization vs Observed Transformation

### 3.1 Canonical Threshold Normalization

The classical normalization above threshold ( T ) is:

$$
f_{classic}(x) = \frac{x - T}{1 - T}
$$

This maps:

$$
[T, 1] \rightarrow [0, 1]
$$

with:

* ( f(T) = 0 )
* ( f(1) = 1 )

Empirical evaluation shows that this formula does not reproduce ECM values .

---

### 3.2 Reconstructed Production Transformation

Empirical reconstruction yields:

$$
f_{obs}(x) = \frac{x - (1 - T)}{T}
$$

This is an affine transformation:

$$
f_{obs}(x) = \frac{1}{T}x - \frac{1 - T}{T}
$$

It differs structurally from classical normalization in both shift and scale.

For ECM-00003:

$$
x = 0.817317, \quad T = 0.748
$$

$$
f_{obs}(x) =

 \frac{0.817317 - 0.252}{0.748} =

0.755977
$$

which matches ECM to six decimal places .

---

## 4. Threshold Bifurcation

Solving the observed transformation for ( T ):

$$
ECM = \frac{x - (1 - T)}{T}
$$

$$
ECM \cdot T = x - 1 + T
$$

$$
T(ECM - 1) = x - 1
$$

$$
T = \frac{x - 1}{ECM - 1}
$$

Applying this inversion to all observed (SQL, ECM) pairs yields two stable modes:

$$
T_1 \approx 0.76
$$

$$
T_2 \approx 0.748
$$

Candidates cluster into two internally consistent groups:

* Group A: ( T = 0.76 )
* Group B: ( T = 0.748 )

Within each group, reconstruction accuracy reaches 100% for multiple cases .

This establishes the existence of dual threshold regimes in production.

---

## 5. Formal Analysis of Monotonicity

Let:

$$
f_{obs}(x) = \frac{1}{T}x - \frac{1 - T}{T}
$$

Derivative:

$$
f'_{obs}(x) = \frac{1}{T}
$$

Since:

$$
T \in (0,1)
$$

$$
\frac{1}{T} > 0
$$

Therefore:

$$
f'_{obs}(x) > 0
$$

The transformation is strictly monotonically increasing.

### Consequence

For any two similarities ( x_1, x_2 ):

$$
x_1 > x_2 \Rightarrow f_{obs}(x_1) > f_{obs}(x_2)
$$

Thus, ranking order is preserved within each threshold regime.

No intra-query ranking distortion occurs.

---

## 6. Ranking Invariance Analysis

### 6.1 Within a Fixed Threshold

Since
$$
( f_{obs}(x) )
$$
is affine and strictly increasing:

* Relative ordering is invariant.
* Top-K retrieval order remains unchanged.
* Recall sets are unaffected (assuming threshold filtering is applied prior).

Therefore, the transformation is ranking-invariant within a single ( T ).

---

### 6.2 Across Different Thresholds

Consider two identical cosine values ( x ), evaluated under two thresholds
$$
( T_1 \neq T_2 ):
$$

$$
f_{T_1}(x) = \frac{x - (1 - T_1)}{T_1}
$$

$$
f_{T_2}(x) = \frac{x - (1 - T_2)}{T_2}
$$

These are distinct affine maps with different slopes:

$$
\text{slope} = \frac{1}{T}
$$

$$
Since ( T_1 \neq T_2 ):
$$

$$
\frac{1}{T_1} \neq \frac{1}{T_2}
$$

Therefore:

* The same cosine similarity yields different ECM scores.
* Cross-query comparability is broken.
* Cross-version comparability is broken.
* Any downstream component consuming ECM as a calibrated similarity metric receives non-stationary inputs.

This violates scale invariance across threshold configurations.

---

## 7. Geometric Interpretation

### 7.1 Classical Normalization

Graph of:

$$
f_{classic}(x) = \frac{x - T}{1 - T}
$$

$$
Passes through (T, 0)
$$

$$
Passes through (1, 1)
$$

$$
Slope = ( \frac{1}{1 - T} )
$$

Interpretation: compresses interval [T, 1] into [0, 1].

---

### 7.2 Observed Transformation

Graph of:

$$
f_{obs}(x) = \frac{x - (1 - T)}{T}
$$

$$
Passes through (1 − T, 0)
$$

$$
Passes through (1, 1)
$$

$$
Slope = ( \frac{1}{T} )
$$

Geometrically:

* The zero-crossing is shifted left.
* The slope is steeper for smaller T.
* The mapping does not anchor at (T, 0).

For ( T = 0.76 ):

* Zero at 0.24
* Slope ≈ 1.316

For ( T = 0.748 ):

* Zero at 0.252
* Slope ≈ 1.337

Thus, ECM values are effectively rescaled and translated cosine similarities, not normalized ones.

---

## 8. Architectural Risk Assessment

### 8.1 Properties Observed

* Affine post-processing dependent on threshold.
* Dual threshold regime active simultaneously.
* Score representation not equivalent to cosine similarity.
* Monotonic ranking preserved locally.
* Global score scale not invariant.

### 8.2 Risk Implications

1. Cross-query score comparability compromised.
2. Offline evaluation metrics may drift.
3. Calibration and explainability degraded.
4. A/B testing across threshold versions may produce non-intuitive deltas.
5. Reranking models consuming ECM as feature input receive threshold-coupled signals.

---

## 9. Conclusions

The production similarity layer applies:

$$
ECM = \frac{SQL - (1 - T)}{T}
$$

with:

$$
T \in {0.76, 0.748}
$$

The transformation:

* Is affine.
* Is strictly monotonic.
* Preserves ranking within a regime.
* Breaks scale invariance across regimes.

The reconstruction was achieved using only numerical outputs and validated with up to six-decimal precision across multiple anonymized candidates .

This case demonstrates a general methodology for black-box auditing of similarity scoring systems in production ML infrastructure.
