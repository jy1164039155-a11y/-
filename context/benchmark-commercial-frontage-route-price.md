# B-3 路线价与临街修正体系 — 决策备忘录

更新日期：2026-06-16  
维护：CH-2（架构实现）  
任务：`task_mqg5fkyl_2nnkg8`

---

## 一、现状判断

| 维度 | 现状 |
|------|------|
| 代码 | `benchmark_correction.py` 商服 `FORMULA_PROFILES` 仅含 `base/ki/ky/kv/kt/ks/ka/ku/kf`；**无** `frontage_mode`、路线价 Po、Kc/Kd/Kk 分支 |
| 门禁 | 商服一律 `incomplete`，pending 提示「Ku + 路线价及街角、宽度、深度」 |
| 通道配置 | `tongdao_benchmark_land_price.json` 有级别价（2560/2080/1335/950/750），**无**路线价段表、Kc/Kd/Kk |
| 设计参考 | 道县 2019006：路线价 **1810** → 修正链 → **2418**；混合加权见 `benchmark-commercial-mixed-use.md` |
| 内部 Excel | `scratch/full_audit_output.txt` 中「基准地价法」sheet 已出现 Kc（街角）、Kd（临街深度）、Kk（临街宽度）三表结构，列按级别（一～四级） |

**符号对齐（待 B-2/B-6 最终确认）**

| 符号 | 通道 Excel | 道县 2019-8 / 2019006 | 本方案采用 |
|------|-----------|----------------------|-----------|
| 年期 | Ky | Kn | **Ky**（与住宅一致） |
| 街角 | Kc | Kc | **Kc** |
| 临街深度 | Kd | （报告待 OCR） | **Kd** |
| 临街宽度 | Kk | 2019006 正文写 Kd 处可能混用 | **Kk**（宽度），与 Excel 一致 |
| 面积/形状 | Ks/Ka | KS/KX | **Ks/Ka** |
| 周边土地利用 | Ku | KX | **Ku** |

> `benchmark-commercial-mixed-use.md` 中「Kd=宽度」与通道 Excel「Kk=宽度、Kd=深度」不一致；**实现以通道技术报告 + Excel 三表为准**，2019006 仅作数值链验证。

---

## 二、`frontage_mode` 决策

### 2.1 枚举定义

```yaml
frontage_mode:
  non_street:          # 场景 A：不临街商服
    po_source: level_base_price   # P1b = 级别基准地价
    formula: "P商 = P1b × (1+∑Ki) × Ky × Kv × Kt × Ks × Ka × Ku + Kf"
    required_factors: [level, ki, ky, kv, kt, ks, ka, ku, kf]
    gold_standard: [GS-COM-02A, GS-COM-02B]

  street_route_price:  # 场景 B：临街商服
    po_source: route_price        # Po = 路线价（元/㎡）
    formula: "P商 = Po × Ky × Kv × Kt × Ks × Ka × Kc × Kd × Kk × Ku + Kf"
    required_factors: [route_segment, ky, kv, kt, ks, ka, kc, kd, kk, ku, kf]
    gold_standard: [GS-COM-03 商服段]  # 2418 链，设计参考
    excludes: [ki]                 # 临街路线价法不用 ∑Ki
```

### 2.2 切换条件（何时走哪条路）

| 条件 | 走 `street_route_price` | 走 `non_street` |
|------|-------------------------|-----------------|
| 宗地临城镇规划道路且该道路有公布路线价段 | ✅ | |
| 路线价段表未结构化 / 无法匹配段 | ❌ → **incomplete** | 若用户确认「不临街」可降级 |
| 不临主街、背街、内院、仅通道开口 | | ✅ |
| 加油站等临路但政策按级别价 | 待用户确认 | 默认 ✅ |
| 混合用途 | 商服段独立选 mode；住宅段始终级别价 | 同左 |

**结论：两者不能在同一商服段并存** — Po 只能取「路线价」或「级别基准地价」之一；混合用途是**分用途各算再加权**，不是同一公式内双 Po。

### 2.3 2019006 路线价链（设计参考，用于 B-6 验收）

```
Po = 1810（荷叶塘东路/石牌楼路路线价段）
  × Ky × Kv × Kt × Ks × Ka × Kc × Kd × Kk × Ku …
  → P商 = 2418 元/㎡
P综合 = 2418 × 9.09% + 1258 × 90.91% = 1363 元/㎡
```

B-3 不展开各系数具体取值（由 B-2 结构化表 + B-6 拆解）；本备忘录只锁定**分支与数据结构**。

---

## 三、需结构化表号（阻塞清单）

| 序号 | 内容 | 预期来源 | 负责 | 阻塞 |
|------|------|----------|------|------|
| 1 | 路线价段表（路名→段价） | 通道技术报告 + 道县 2019-8 对照 | B-3→配置 | 临街 hard gate |
| 2 | Kc 街角系数 | 通道报告 / Excel 基准地价法 sheet | B-2 | 临街 |
| 3 | Kd 临街深度 | 同上 | B-2 | 临街 |
| 4 | Kk 临街宽度 | 同上 | B-2 | 临街 |
| 5 | Ku 周边土地利用 | **表 5.6.13** | B-2 | 两种 mode 均需 |
| 6 | 商服 Kv | 通道报告（表号待标） | B-2 | 两种 mode 均需 |

---

## 四、前端必填项（`benchmark_corr_analysis` 扩展）

### 4.1 共用

| 字段 | 说明 |
|------|------|
| `land_use_type` | 商业服务业用地 |
| `frontage_mode` | `non_street` \| `street_route_price` |
| `set_plot_ratio` / `land_use_term` / `valuation_date` | 与住宅相同 |
| `individual_factors.area/shape` | Ks/Ka |
| `ku_type` + `ku` | 表 5.6.13 选项 → 系数 |
| `development_adjustment` / `land_development_set` | Kf |

### 4.2 `non_street` 额外

| 字段 | 说明 |
|------|------|
| `land_level` | 一级～五级 |
| `region_factor_selections` | ∑Ki（若通道商服与居住分表，见 B-2） |

### 4.3 `street_route_price` 额外

| 字段 | 说明 |
|------|------|
| `route_segment_id` | 路线价段 ID（下拉） |
| `route_name` | 路名（展示/审计） |
| `route_price` | Po（元/㎡，由段表带出，可只读） |
| `is_corner` / `corner_type` | 是否街角 → Kc |
| `frontage_width_m` | 临街宽度 → Kk |
| `frontage_depth_m` | 临街深度 → Kd |

**UI 行为（供 B-4）**

- 切换 `frontage_mode` 时：隐藏/显示对应字段组；`po_source` 标签在「级别基准地价 P1b」与「路线价 Po」间切换。
- 通道县路线价表缺失时：`street_route_price` 选项置灰并提示 incomplete 原因。

---

## 五、Word 正文差异段

| 段落 key | `non_street` | `street_route_price` |
|----------|--------------|----------------------|
| `benchmark_corr_po` | 「…位于×级商服用地，级别基准地价 Po=…」 | 「…临×路，查路线价表得路线价 Po=…元/㎡」 |
| `benchmark_corr_formula` | P1b×(1+∑Ki)×… | Po×Ky×…×Kc×Kd×Kk×Ku+Kf（无 ∑Ki） |
| 新增 `benchmark_corr_kc/kd/kk` | **不输出** | 各一段 + 附表 |
| `benchmark_corr_ki` | 输出表 3-6/3-7 | **跳过** |
| `benchmark_corr_solve` | GS-COM-02A 链 | 2019006 式链（2418） |
| 方法选用理由（第四部分） | 「级别与区域因素修正体系完备…」 | 增加「临主街，路线价体系完备…」 |

混合用途：商服段与住宅段**分块输出**，最后增加「按容居比例加权综合单价」段（已有 `benchmark-commercial-mixed-use.md`）。

---

## 六、实现方案（CH-2 → B-2/B-4 交接）

1. **`benchmark_correction.py`**
   - 扩展 `FORMULA_PROFILES["商业服务业用地"]` 为双 profile，由 `frontage_mode` 选择。
   - `calculate_benchmark_correction` 增加 Po 分支：`route_price` lookup vs `_base_price_lookup`。
   - pending 逻辑按 mode 拆分（临街缺 Kc/Kd/Kk/路线价；不临街缺 ∑Ki/Ku）。

2. **配置 `tongdao_benchmark_land_price.json`（B-2 填表）**
   ```json
   "route_price_segments": [],
   "corner_coefficient_table": {},
   "frontage_depth_table": {},
   "frontage_width_table": {},
   "surrounding_land_use_table": { "ref": "表5.6.13", "rows": [] }
   ```

3. **金标准**
   - 不临街：GS-COM-02A（2154）、GS-COM-02B（1427.4）— **已拍板**
   - 临街链：GS-COM-03 商服段 2418 — 设计参考，不扩展通道可算县市

---

## 七、待用户/主控确认的业务规则

1. 通道县路线价表未完成前，临街门面评估是否**一律 incomplete**，还是允许手工填 Po？
2. 状元路加油站等范本：默认 `street_route_price` 还是 `non_street`？
3. 商服区域因素 ∑Ki 是否与居住共用表 3-6，还是独立商服表（B-2 阻塞）？
4. 乡镇商服（场景 D）是否永不走路线价？

---

## 八、风险

| 风险 | 缓解 |
|------|------|
| 道县/通道符号不一致 | 以通道 Excel + 技术报告为准；2019006 只验算 |
| 路线价表工作量大 | 先 JSON 段表 + 下拉，不做地图 GIS |
| 混合用途 UI 复杂 | B-4 分 Tab；计算层按用途数组 |

---

## 九、验证

- [ ] `frontage_mode=non_street` + GS-COM-02A fixture → 2154（B-2 实现后）
- [ ] `frontage_mode=street_route_price` + 2019006 段表 stub → 2418（B-6 对照）
- [ ] 切换 mode 时 Word 正文 diff 符合第五节
- [ ] 路线价表缺失 → `support_status=incomplete`，无正式单价

---

## 十、B-1 索引复核结论（@CH-1）

已核对 `context/benchmark-commercial-material-index.md`：

| 项 | 结论 |
|----|------|
| Ku **表 5.6.13** | ✅ 索引正确，与 `benchmark_correction.py` pending 一致 |
| 商服 Kv 表号 | ⚠️ 索引写「表号待标」— 维持，待 B-2 从通道报告补 |
| 路线价 / Kc / Kd / Kk | ✅ 标为 B-3 范围 — 本备忘录已覆盖 |
| GS-COM-02A/B | ✅ 2154 / 1427.4 双 fixture 结论正确 |
| 2019006 路径 | ✅ CH-1 确认：`01_Source/02_Word_Templates/…2019006…合并报告.docx` 存在，索引有效；B-6 可直接拆解 |

**索引无需改表号**；建议在第七节「缺失表号」第 2 行补充「商服 Kv → 通道报告表 X-X（B-2 认领后回填）」。
