#!/usr/bin/env python3
"""为 Enzyme Atlas 全部文献写入统一的「研究专题」多标签归类（topics 数组）。

设计原则：
- 专题是面向读者的「研究问题」入口；一篇文献可归入 1-3 个专题。
- 经典库原「细粒度 topic」经 TOPIC_MAP 映射到统一专题集合，绝不勉强归类。
- 保留原 topic 字段不变，新增 topics 数组。

新增专题（12 个大专题无法自然承接时）：
  1. 辅因子、辅酶与再生
  2. 酶的应用与环境生物催化
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# 细粒度 topic -> [大专题...]
TOPIC_MAP: dict[str, list[str]] = {
    "定向进化": ["定向进化与理性设计"],
    "理性设计": ["定向进化与理性设计"],
    "从头酶设计": ["定向进化与理性设计", "计算酶学与分子模拟"],
    "计算酶设计": ["计算酶学与分子模拟", "定向进化与理性设计"],
    "机器学习": ["AI 与机器学习辅助酶研究"],
    "机器学习与酶工程": ["AI 与机器学习辅助酶研究", "定向进化与理性设计"],
    "酶的进化": ["酶的发现与挖掘", "定向进化与理性设计"],
    "新功能酶": ["定向进化与理性设计", "酶催化方法与分析技术"],
    "非天然催化": ["酶催化方法与分析技术", "定向进化与理性设计"],
    "生物催化": ["酶催化方法与分析技术"],
    "酶稳定性": ["酶的稳定性工程"],
    "稳定性工程": ["酶的稳定性工程"],
    "热稳定性工程": ["酶的稳定性工程"],
    "溶剂耐受性": ["酶的稳定性工程", "酶动力学、选择性与底物特异性"],
    "底物特异性": ["酶动力学、选择性与底物特异性"],
    "催化机制": ["酶的结构与催化机制"],
    "变构调控": ["酶的结构与催化机制"],
    "信号酶": ["酶的结构与催化机制"],
    "结构酶学": ["酶的结构与催化机制"],
    "结构预测": ["计算酶学与分子模拟", "酶的结构与催化机制"],
    "蛋白酶结构": ["酶的结构与催化机制"],
    "RNA 酶": ["酶的结构与催化机制"],
    "核糖核蛋白酶": ["酶的结构与催化机制"],
    "核酸酶": ["酶的结构与催化机制", "酶催化方法与分析技术"],
    "RNA 加工酶": ["酶的结构与催化机制"],
    "多酶级联": ["多酶级联反应"],
    "酶的级联组装": ["酶的级联组装", "多酶级联反应"],
    "融合酶": ["融合酶与多功能酶"],
    "酶固定化": ["酶固定化与酶—材料体系"],
    "辅因子再生": ["辅因子、辅酶与再生"],
    "塑料降解": ["酶的应用与环境生物催化"],
}

# 按经典库记录的行序（0-based index，与 classics.json items 顺序一致）追加专题
# 用于处理「细粒度 topic 无法完全表达、需补 1 个专题」的少数情况。
EXTRA_TOPICS_BY_INDEX: dict[int, list[str]] = {
    # 08 De novo design of luciferases using deep learning -> 补 AI
    8: ["AI 与机器学习辅助酶研究"],
    # 58 FAST-PETase 机器学习辅助 PET 解聚 -> 补 AI（应用类已由「塑料降解」映射覆盖）
    58: ["AI 与机器学习辅助酶研究"],
}

# 每周论文（papers.json 与 history）按 id 追加的专题（在已有 topic 基础上补）
PAPER_EXTRA_TOPICS: dict[str, list[str]] = {}


def normalize(topics: list[str]) -> list[str]:
    seen: list[str] = []
    for t in topics:
        t = (t or "").strip()
        if t and t not in seen:
            seen.append(t)
    return seen


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    # ---- 经典库 ----
    classics_path = DATA / "classics.json"
    classics = json.loads(classics_path.read_text(encoding="utf-8"))
    counter: dict[str, int] = {}
    for i, item in enumerate(classics["items"]):
        mapped = list(TOPIC_MAP.get(item["topic"], []))
        mapped += EXTRA_TOPICS_BY_INDEX.get(i, [])
        item["topics"] = normalize(mapped)
        for t in item["topics"]:
            counter[t] = counter.get(t, 0) + 1
    write_json(classics_path, classics)
    print("=== 经典库（83 篇）归类 ===")
    for t, n in sorted(counter.items(), key=lambda x: -x[1]):
        print(f"  {n:2d}  {t}")
    total_assigned = sum(len(i["topics"]) for i in classics["items"])
    print(f"  共 {len(classics['items'])} 篇，标签总数 {total_assigned}，平均 {total_assigned/len(classics['items']):.2f} 个/篇")

    # ---- 每周论文（当前 + 归档）----
    paper_paths = [DATA / "papers.json"] + sorted((DATA / "history").glob("papers-*.json"))
    print("\n=== 每周论文归类 ===")
    for pp in paper_paths:
        data = json.loads(pp.read_text(encoding="utf-8"))
        for item in data["items"]:
            base = [item.get("topic", "")] if item.get("topic") else []
            extra = PAPER_EXTRA_TOPICS.get(item.get("id", ""), [])
            item["topics"] = normalize(base + extra)
        write_json(pp, data)
        rel = pp.relative_to(ROOT).as_posix()
        for item in data["items"]:
            print(f"  {rel:38s} {item['id']:32s} -> {item['topics']}")


if __name__ == "__main__":
    main()
