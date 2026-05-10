"""
大纲模板 — 各题材的大纲结构模板
"""

# === 题材模板 ===

GENRE_TEMPLATES = {
    "玄幻": {
        "name": "玄幻修仙",
        "power_system": "修炼体系：炼气→筑基→金丹→元婴→化神→渡劫→大乘→飞升",
        "world_structure": "凡人界→修真界→仙界→神界",
        "typical_conflicts": [
            "宗门争斗",
            "资源争夺",
            "渡劫危机",
            "正邪对抗",
            "天道压制",
        ],
        "chapter_structure": "开局（废材/穿越）→ 觉醒 → 宗门历练 → 大比争锋 → 秘境探险 → 宗门危机 → 踏入更大世界",
        "hook_frequency": "每 2-3 章至少一个爽点",
    },
    "都市": {
        "name": "都市异能",
        "power_system": "异能等级：E→D→C→B→A→S→SS→SSS",
        "world_structure": "校园/职场→都市→全国→全球",
        "typical_conflicts": [
            "商业竞争",
            "势力争斗",
            "异能对决",
            "身份隐藏",
            "情感纠葛",
        ],
        "chapter_structure": "开局（获得异能/重生）→ 小试牛刀 → 势力扩张 → 城市争锋 → 全国扬名 → 巅峰对决",
        "hook_frequency": "每 2 章至少一个爽点",
    },
    "科幻": {
        "name": "科幻星际",
        "power_system": "科技等级：行星文明→恒星文明→星系文明→宇宙文明",
        "world_structure": "地球→太阳系→银河系→本星系群→宇宙",
        "typical_conflicts": [
            "文明冲突",
            "科技竞争",
            "星际战争",
            "种族存亡",
            "宇宙危机",
        ],
        "chapter_structure": "开局（地球/星际）→ 崛起 → 星际探索 → 文明接触 → 战争与和平 → 宇宙奥秘",
        "hook_frequency": "每 3 章至少一个爽点",
    },
    "悬疑": {
        "name": "悬疑推理",
        "power_system": "推理能力：观察力→逻辑力→直觉力→全局掌控",
        "world_structure": "案件→城市→全国→国际",
        "typical_conflicts": [
            "破案推理",
            "凶手对抗",
            "真相揭露",
            "阴谋揭秘",
            "信任危机",
        ],
        "chapter_structure": "案件发生→调查→线索→误导→突破→真相大白→下一个案件",
        "hook_frequency": "每章结尾设置悬念",
    },
    "言情": {
        "name": "现代言情",
        "power_system": "感情进展：相遇→相识→暧昧→确认→考验→圆满",
        "world_structure": "校园/职场→城市→全国",
        "typical_conflicts": [
            "误会",
            "第三者",
            "家庭反对",
            "身份差距",
            "信任危机",
        ],
        "chapter_structure": "相遇→相处→暧昧→告白→考验→分离→重逢→圆满",
        "hook_frequency": "每 3-5 章一个感情爽点",
    },
    "历史": {
        "name": "历史架空",
        "power_system": "势力发展：个人→小队→城池→州郡→天下",
        "world_structure": "村/镇→县城→州府→京城→天下",
        "typical_conflicts": [
            "政治斗争",
            "军事征战",
            "权谋算计",
            "忠奸对立",
            "改朝换代",
        ],
        "chapter_structure": "开局（穿越/重生）→ 崛起 → 建立势力 → 征战四方 → 权谋巅峰 → 一统天下",
        "hook_frequency": "每 2-3 章至少一个爽点",
    },
}


def get_genre_template(genre: str) -> dict:
    """获取指定题材的模板"""
    # 模糊匹配
    for key, template in GENRE_TEMPLATES.items():
        if key in genre or genre in key:
            return template
    # 默认返回玄幻
    return GENRE_TEMPLATES["玄幻"]


def list_genres() -> list[str]:
    """获取所有支持的题材"""
    return list(GENRE_TEMPLATES.keys())
