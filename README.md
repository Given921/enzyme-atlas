# Enzyme Atlas

**面向所有酶研究者的每周文献推荐平台。** 每周一整理值得优先阅读的新论文，并维护按研究问题组织的经典文献库；不做个人相关性排序，也不试图替代通用文献搜索引擎。

<!-- ea-address:start -->
[进入公开网站](https://enzyme-atlas.github.io/enzyme-atlas/) · [浏览经典论文](https://enzyme-atlas.github.io/enzyme-atlas/classics.html) · [查看筛选标准](https://enzyme-atlas.github.io/enzyme-atlas/#method)
<!-- ea-address:end -->

| 📖 读者 | 🧰 开发者 | 🤖 Agent |
| --- | --- | --- |
| 找到本周最值得读的酶学论文，理解推荐理由与关键证据；可切换中英文，并按期号回看往期。 | 了解零依赖静态站点、数据结构、测试和 GitHub Pages 发布流程。 | 使用稳定的 JSON 入口，在证据边界内读取、核验或更新内容。 |
| [从本周精选开始](#给读者) | [运行与贡献](#给开发者) | [机器接口与约束](#给-agent) |

## 给读者

Enzyme Atlas 把“搜索”和“推荐”分开：搜索框用于找已知论文，首页负责回答“这一周哪些论文值得优先读、为什么”。

- **本周精选**：每期 3–5 篇，附一句话结论、推荐理由、关键证据、适合读者和 DOI。
- **全部收录**：保留当期通过编辑核验的完整记录，数量由真实数据计算。
- **往期精选**：按期号归档每一期的精选与完整收录（当前第 02 期，第 01 期为 2026-08-31 期），可从 `archive.html` 逐期回看。
- **中英文切换**：页面右上角可切换中文 / English，切换后正文、栏目文案与经典库注释同步切换。
- **经典论文库**：当前 83 篇，覆盖 Nature、Science、Cell 正刊、Nature 子刊及少量其他重要来源。
- **专题入口**：覆盖通用酶学问题，并独立保留多酶级联、酶的级联组装和融合酶。
- **阅读管理**：支持收藏、稍后读、已读、隐藏和 BibTeX 导出。

经典库的“经典”不是简单等同于高被引，而是强调范式转折、方法学基石、机制框架和专题入门价值。每条记录均提供 DOI / 出版社入口。

## 给开发者

项目是无构建步骤、无运行时依赖的静态网站：

```text
index.html / app.js          每周推荐、全部收录与往期精选栏目
classics.html / classics.js  经典论文库
archive.html / archive.js    往期期号归档（含单期详情）
topics.html                  通用研究专题
search.html / search.js      全站已知论文查找：当期 + 往期 + 经典库（中英文双语检索）
i18n.js                      中英文运行时：语言切换、静态文案与受控词表
data/papers.json             当前周刊数据（含 edition 期号与英文内容）
data/editions.json           期号清单：每期的日期、篇数、标题与数据路径
data/history/                历史各期完整数据（归档后不再改动）
data/classics.json           经典文献数据（含英文注释）
scripts/                     校验、发布与公网验收
```

本地运行：

```powershell
python -m http.server 4173
```

访问 <http://localhost:4173>。提交前运行：

```powershell
python scripts/validate_site.py
python scripts/test_weekly_pipeline.py
python scripts/check_public_disclosure.py --verbose
python scripts/set_site_address.py --check
node --check i18n.js
node --check app.js
node --check search.js
node --check classics.js
node --check archive.js
node scripts/test_classics_ui.js
node scripts/test_search_pool.js
```

联网 DOI 核验：

```powershell
python scripts/validate_site.py --online
```

`.github/workflows/pages.yml` 会在 `main` 更新后先执行校验，再部署 GitHub Pages。公网验收脚本默认从当前检出的 `data/classics.json` 读取应发布的经典文献数量，避免写死统计：

```powershell
python scripts/verify_public_site.py --from-config --edition 2026-09-07
```

地址由 `site.config.json` 提供；也可临时用 `--base-url https://…` 覆盖。未配置地址时脚本会提示先运行 `scripts/set_site_address.py`。

验收脚本同时检查首页、经典库、归档页、`i18n.js`、期号清单与两处数据的英文覆盖。

## 给 Agent

Agent 应优先读取结构化数据，而不是从页面文本反向提取：

| 入口 | 用途 | 关键字段 |
| --- | --- | --- |
| [`data/papers.json`](data/papers.json) | 当前一期新论文与推荐 | `edition`, `updatedAt`, `periodStart`, `periodEnd`, `observations`, `observationsEn`, `items`, `items[].en` |
| [`data/editions.json`](data/editions.json) | 期号归档清单 | `current`, `editions[].edition`, `editions[].path`, `editions[].itemCount`, `editions[].headline` |
| [`data/classics.json`](data/classics.json) | 经典论文阅读库 | `updatedAt`, `selectionPolicy`, `items`, `items[].en.note` |
| [`i18n.js`](i18n.js) | 中英文运行时与受控词表 | `EA.t`, `EA.v`, `EA.pick`, `data-lang-slot` |
| [`AGENTS.md`](AGENTS.md) | 更新边界与验证清单 | 产品定位、发布门槛、禁止事项 |

使用约束：

1. 不按个人研究方向计算相关性；面向所有酶研究者组织内容。
2. 所有结论必须限制在摘要或原文证据范围内，保留 DOI、来源与版本关系。
3. 经典条目不得因自动更新被静默删除；新增条目必须具有明确的阅读价值说明。
4. 网络失败、零候选、字段缺失、DOI 失败或撤稿/更正状态不明时，不覆盖线上版本。
5. 周刊只在每周一正式发布；经典库可独立维护，但必须通过完整校验后随站点发布。
6. 每一期必须同时提供中文正文与英文正文（`items[].en`、`observationsEn`），缺少英文的编辑稿无法通过发布校验。
7. 期号由发布脚本按归档序列自动递增（上一期 + 1），往期数据写入 `data/history/` 后不得改动；`data/editions.json` 由发布脚本重建。

## 安全的每周更新

更新固定分为“候选采集 → 推荐编辑 → 完整校验 → 正式发布”四阶段。候选采集器不会直接写入 `data/papers.json`。

```powershell
python scripts/fetch_crossref.py --as-of 2026-09-14
# 编辑 data/staging/candidates-2026-09-14.json，并保存完整的 curated 文件
# 新增条目必须同时写中英文正文（含 en 对象与 observationsEn），不要手写 edition
python scripts/publish_weekly.py --input data/staging/curated-2026-09-14.json --online
```

`publish_weekly.py` 仅在周期、3–5 篇精选、三条编辑观察、必填字段、双语内容与 DOI 校验全部通过后原子替换正式数据，自动分配期号（上一期 + 1）、把上一期归档到 `data/history/`，并重建 `data/editions.json` 供「往期精选」与归档页读取。

## 当前边界

- 邮件订阅仍是本地偏好演示，尚未接入邮件服务。
- 归档页为只读视图：收藏与阅读清单只作用于首页当期。
- 站点不内置任何绝对地址，可部署到任意域名或子目录；公开地址通过 `site.config.json` 统一下发（见下）。
- 搜索功能服务于站内已知论文查找，不扩展为通用全文检索引擎。

## 公开地址配置

站点输出中不出现托管商品牌字样，也不出现个人账号信息。地址只在一个地方维护：

```powershell
# 设置中性公开地址（会同步页面 canonical / og 标签、README 入口与 CNAME）
python scripts/set_site_address.py --url https://<中性地址>/ --contact-email <公开联系邮箱>

# 清除地址（恢复为“未配置”状态）
python scripts/set_site_address.py --clear

# 校验已提交文件是否与 site.config.json 一致（CI 也会执行）
python scripts/set_site_address.py --check
```

命名与泄露防护：

```powershell
# 本地、被 git 忽略的敏感词清单：仓库本身不会写进这些词
python scripts/check_public_disclosure.py --verbose
```

`check_public_disclosure.py` 会扫描所有已跟踪文件，命中「本地敏感词清单」或「git remote 中的仓库属主名」即失败。
由于属主名是从 `git remote` 实时推导的，纯克隆环境（含 CI）同样能拦住个人账号名。

