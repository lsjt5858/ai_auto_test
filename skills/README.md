这里用于存放 Skill 的脚本实现。

推荐目录结构：

- `skills/<skill_name>/scripts/`：可执行脚本目录
- `skills/<skill_name>/README.md`：Skill 的快速说明
- `skills/<skill_name>/SKILL.md`：Skill 的详细说明

运行时配置文件放在 `config/skills/<skill_name>.yaml`。
测试用例放在 `data/`。

核心注意点：

- `skills/` 目录是框架固定使用的脚本运行目录。
- 这个目录下的内容默认不能随意变更，包括重命名、移动、删除、替换脚本文件。
- 这里的主要用途只有一个：存放并执行 Skill 脚本。
- 如果修改了 `skills/<skill_name>/scripts/` 下的脚本路径，但没有同步修改 `config/skills/<skill_name>.yaml`，自动化会在业务执行前直接失败。
- 新增 Skill 时可以在 `skills/` 下新增目录，但已有 Skill 的脚本入口文件必须保持稳定。
