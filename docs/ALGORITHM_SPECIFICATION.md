# RescuE-Triage: Algorithm Specification & Mathematical Formulation

## 1. Algorithmic Overview: Dynamic Emergency Priority Index (DEPI)

During high-concurrency disaster surges, triage decisions cannot rely purely on static clinical scores (such as START or ESI) because the physical environment and queue latency directly influence patient survival. DEPI dynamically aggregates medical status, physical environmental threat, demographic vulnerability, and cumulative queue latency into a single unified priority metric.

---

## 2. Mathematical Definition

The dynamic priority index of an incident ticket $i$ at real-time clock $t$ is formulated as:

$$DEPI_i(t) = \Big(w_m \cdot M_i\Big) + \Big(w_h \cdot H_i\Big) + \Big(w_v \cdot V_i\Big) + W\big(\Delta t_i\big)$$

### Variables and Parameters:
1. **Medical Urgency ($M_i \in [1, 10]$):**
   - $w_m = 4.5$
   - $10$: Cardiorespiratory arrest, unconscious, major arterial hemorrhage, severe asphyxiation.
   - $8 - 9$: Acute trauma, crush injury, penetrating wound, severe respiratory distress.
   - $5 - 7$: Closed fractures, moderate burns, deep lacerations with controlled bleeding.
   - $1 - 4$: Superficial abrasions, mild sprains, stable chronic conditions.

2. **Environmental Hazard Level ($H_i \in [1, 10]$):**
   - $w_h = 3.0$
   - $10$: Actively spreading fire, submerged room/building, toxic chemical/gas cloud, imminent collapse.
   - $7 - 9$: Rising flood waters ($>1.5\text{m}$), unstable structural walls, live electrical wires.
   - $4 - 6$: Knee-deep flooding, localized water stagnation, road access cut off.
   - $1 - 3$: Elevated ground, structurally sound building, low physical hazard.

3. **Demographic Vulnerability Multiplier ($V_i \in [1.0, 5.0]$):**
   - $w_v = 3.0$
   - Let $N_{inf}, N_{dis}, N_{eld}, N_{preg}, N_{ch}$ denote the count of infants, disabled individuals, elderly ($>65$), pregnant women, and children ($3-12$), respectively:
   $$V_i = \min\left(5.0, \; 1.0 + 1.5 N_{inf} + 1.5 N_{dis} + 1.0 N_{eld} + 1.0 N_{preg} + 0.8 N_{ch}\right)$$

4. **Dynamic Wait-Time Scaling Function ($W(\Delta t_i)$):**
   - Let $\Delta t_i = \frac{t - t_{arrival}}{60}$ be the elapsed waiting duration in minutes:
   $$W(\Delta t_i) = \min\left(W_{\max}, \; \lambda \cdot (\Delta t_i)^\gamma\right)$$
   - Standard parameters: $\lambda = 0.35$, $\gamma = 1.15$, $W_{\max} = 20.0$.
   - **Mathematical Invariant:** The saturation cap $W_{\max} = 20.0$ guarantees that no lower-urgency case ($M=2$, initial base score $\approx 15$) can ever artificially surpass an acute critical case ($M=10$, base score $\ge 45$), strictly preserving clinical life safety while preventing unbounded queue starvation.

---

## 3. Data Structure: Binary Max-Heap Specification

The priority queue $\mathcal{Q}$ stores elements structured as tuples:
$$\mathcal{Q}[k] = \langle DEPI_k(t), \; \text{Ticket}_k \rangle$$

### Heap Property:
$$\forall k > 0: \quad DEPI_{\text{parent}(k)}(t) \ge DEPI_k(t), \quad \text{where } \text{parent}(k) = \left\lfloor \frac{k - 1}{2} \right\rfloor$$

### Primary Operations:
1. **`push(ticket, t)`:**
   - Evaluates $DEPI(t)$ and appends to dynamic list $\mathcal{Q}$.
   - Executes sift-up bubbling from leaf index to restore heap property.
   - **Time Complexity:** $\mathcal{O}(\log N)$
   - **Auxiliary Map Update:** Records `index_map[ticket.id] = index` in $\mathcal{O}(1)$.

2. **`pop_max()`:**
   - Swaps root $\mathcal{Q}[0]$ with the last element $\mathcal{Q}[N-1]$.
   - Pops the last element and executes sift-down propagation from index $0$.
   - **Time Complexity:** $\mathcal{O}(\log N)$

3. **`refresh_priorities(t)` (Aging Cycle):**
   - Re-evaluates wait component $W(\Delta t_i)$ across all $N$ elements.
   - Performs bottom-up Floyd's heap construction starting from index $\lfloor N/2 \rfloor - 1$ down to $0$.
   - **Time Complexity:**
     $$\sum_{h=0}^{\lfloor \log N \rfloor} \left\lceil \frac{N}{2^{h+1}} \right\rceil \mathcal{O}(h) = \mathcal{O}(N)$$
   - Proven strictly linear $\mathcal{O}(N)$, significantly more efficient than re-sorting via TimSort ($\mathcal{O}(N \log N)$).
