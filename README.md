# Enzyme Atlas（酶学文献推荐）

面向课题组内部试运行、可逐步公开的酶学文献发现与筛选网站雏形。

## 已实现

- 每周一更新的完整收录、本周精选与 55 篇经典/里程碑论文阅读路径
- 经典库按 Nature、Science、Cell 正刊、Nature 子刊与其他精选分层，全部提供 DOI 出版入口
- 12 个通用酶学研究栏目（含多酶级联、酶的级联组装、融合酶）
- 推荐卡片提供一句话结论、推荐理由、证据、适合读者与 DOI
- 顶部精确搜索、专题浏览与推荐流职责分离
- 收藏、稍后读、已读、隐藏、BibTeX 导出与订阅偏好演示
- 数据驱动的收录/精选数量、透明筛选标准与移动端适配
- 以黑白灰、留白和单一主动作为核心的 OpenAI 风格视觉系统

## 运行

无需安装依赖。在本目录运行：

```powershell
python -m http.server 4173
```

然后访问 <http://localhost:4173>。

## 安全的每周更新流程

网站只在每周一更新，定位是文献推荐而不是通用搜索引擎。更新严格分成四个阶段：候选采集、推荐编辑、完整校验、正式发布。候选采集器永远不会写入 `data/papers.json`。

```powershell
python scripts/fetch_crossref.py --as-of 2026-09-07
# 编辑 data/staging/candidates-2026-09-07.json，并另存为完整的 curated-2026-09-07.json
python scripts/publish_weekly.py --input data/staging/curated-2026-09-07.json --online
python scripts/validate_site.py
python scripts/validate_site.py --online
python scripts/test_weekly_pipeline.py
node --check app.js
node --check search.js
node --check classics.js
node scripts/test_classics_ui.js
```

`publish_weekly.py` 只有在周期、3–5 篇精选、三条编辑观察、必填字段和 DOI 校验全部通过后才会原子替换正式数据；替换前的版本保存在本地 `data/history/`。网络失败、零候选、字段缺失、DOI 失败或发现撤稿关系时均停止发布。

## GitHub Pages

仓库包含 `.github/workflows/pages.yml`。推送到 `main` 后，GitHub Actions 会先执行静态数据、流水线、JavaScript 和经典库交互测试，全部通过后才部署 Pages。部署后运行：

```powershell
python scripts/verify_public_site.py --base-url https://<GitHub用户名>.github.io/enzyme-atlas/ --edition 2026-09-07
```

邮件发送仍是本地订阅偏好演示，尚未接入邮件服务。
