# Enzyme Atlas

**面向所有酶研究者的每周文献推荐平台。** 每周一整理值得优先阅读的新论文，并维护按研究问题组织的经典文献库；不做个人相关性排序，也不试图替代通用文献搜索引擎。

[进入公开网站](https://given921.github.io/enzyme-atlas/) · [浏览经典论文](https://given921.github.io/enzyme-atlas/classics.html) · [查看筛选标准](https://given921.github.io/enzyme-atlas/#method)

| 📖 读者 | 🧰 开发者 | 🤖 Agent |
| --- | --- | --- |
| 找到本周最值得读的酶学论文，理解推荐理由与关键证据。 | 了解零依赖静态站点、数据结构、测试和 GitHub Pages 发布流程。 | 使用稳定的 JSON 入口，在证据边界内读取、核验或更新内容。 |
| [从本周精选开始](#给读者) | [运行与贡献](#给开发者) | [机器接口与约束](#给-agent) |

## 给读者

Enzyme Atlas 把“搜索”和“推荐”分开：搜索框用于找已知论文，首页负责回答“这一周哪些论文值得优先读、为什么”。

- **本周精选**：每期 3–5 篇，附一句话结论、推荐理由、关键证据、适合读者和 DOI。
- **全部收录**：保留当期通过编辑核验的完整记录，数量由真实数据计算。
- **经典论文库**：当前 83 篇，覆盖 Nature、Science、Cell 正刊、Nature 子刊及少量其他重要来源。
- **专题入口**：覆盖通用酶学问题，并独立保留多酶级联、酶的级联组装和融合酶。
- **阅读管理**：支持收藏、稍后读、已读、隐藏和 BibTeX 导出。

经典库的“经典”不是简单等同于高被引，而是强调范式转折、方法学基石、机制框架和专题入门价值。每条记录均提供 DOI / 出版社入口。

## 给开发者

项目是无构建步骤、无运行时依赖的静态网站：

```text
index.html / app.js          每周推荐与全部收录
classics.html / classics.js  经典论文库
topics.html                  通用研究专题
search.html / search.js      已知论文查找
data/papers.json             当前周刊数据
data/classics.json           经典文献数据
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
node --check app.js
node --check search.js
node --check classics.js
node scripts/test_classics_ui.js
```

联网 DOI 核验：

```powershell
python scripts/validate_site.py --online
```

`.github/workflows/pages.yml` 会在 `main` 更新后先执行校验，再部署 GitHub Pages。公网验收脚本默认从当前检出的 `data/classics.json` 读取应发布的经典文献数量，避免写死统计：

```powershell
python scripts/verify_public_site.py --base-url https://given921.github.io/enzyme-atlas/ --edition 2026-08-31
```

## 给 Agent

Agent 应优先读取结构化数据，而不是从页面文本反向提取：

| 入口 | 用途 | 关键字段 |
| --- | --- | --- |
| [`data/papers.json`](data/papers.json) | 当前一期新论文与推荐 | `updatedAt`, `periodStart`, `periodEnd`, `observations`, `items` |
| [`data/classics.json`](data/classics.json) | 经典论文阅读库 | `updatedAt`, `selectionPolicy`, `items` |
| [`AGENTS.md`](AGENTS.md) | 更新边界与验证清单 | 产品定位、发布门槛、禁止事项 |

使用约束：

1. 不按个人研究方向计算相关性；面向所有酶研究者组织内容。
2. 所有结论必须限制在摘要或原文证据范围内，保留 DOI、来源与版本关系。
3. 经典条目不得因自动更新被静默删除；新增条目必须具有明确的阅读价值说明。
4. 网络失败、零候选、字段缺失、DOI 失败或撤稿/更正状态不明时，不覆盖线上版本。
5. 周刊只在每周一正式发布；经典库可独立维护，但必须通过完整校验后随站点发布。

## 安全的每周更新

更新固定分为“候选采集 → 推荐编辑 → 完整校验 → 正式发布”四阶段。候选采集器不会直接写入 `data/papers.json`。

```powershell
python scripts/fetch_crossref.py --as-of 2026-09-07
# 编辑 data/staging/candidates-2026-09-07.json，并保存完整 curated 文件
python scripts/publish_weekly.py --input data/staging/curated-2026-09-07.json --online
```

`publish_weekly.py` 仅在周期、3–5 篇精选、三条编辑观察、必填字段和 DOI 校验全部通过后原子替换正式数据，并在 `data/history/` 保留上一个版本。

## 当前边界

- 邮件订阅仍是本地偏好演示，尚未接入邮件服务。
- GitHub 组织主页迁移完成前，公开地址仍为 `given921.github.io/enzyme-atlas/`。
- 搜索功能服务于站内已知论文查找，不扩展为通用全文检索引擎。

