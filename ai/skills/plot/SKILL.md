---
name: plot
description: 当用户需要绘制折线图、柱状图、直方图等时使用此技能
---


# plot

## 库

使用 matplotlib 或 seaborn 来进行绘制。如果当前 uv 环境中没有安装，使用 `uv run --with` 来带上需要的库。

Seaborn 是 基于 Matplotlib 的高级封装。Matplotlib 更底层、可控性更强；Seaborn 更简洁，适合快速做统计图和数据分析图。

使用建议：
- 想快速出好看的图：用 Seaborn
-	想精细定制或画复杂图：用 Matplotlib
-	实际项目里常一起用：Seaborn 画图，Matplotlib 微调


## 中文字体

使用 `assets/fonts/SimSun.ttf`。
