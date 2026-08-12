# Studio Background Library

一个面向设计师、电商从业者和内容创作者的公益摄影棚背景素材库。

本仓库采用“**GitHub Releases 保存原始压缩包和独立原图 + GitHub Pages 自动生成可视化图库**”的结构。上传 ZIP 后，自动化程序会解压并把每张原图发布为独立 Release Asset，因此每张图片都有自己的稳定下载 URL；原 ZIP 同时保留，方便整批下载。

## 如何浏览和下载

- 在线图库：启用 GitHub Pages 后显示在仓库首页右侧的 **Deployments** / **Pages** 链接中。
- 整批下载：进入 [Releases](../../releases)，选择对应批次并下载 ZIP。
- 每张预览卡片都有独立原图下载 URL，同时提供所属批次的完整 ZIP 下载入口。
- URL 表格：在线图库提供自动更新的 Excel 和 CSV，逐行记录每张图片的独立 URL 与批次信息。

## 管理员：上传新素材

在线管理员入口：[GitHub Release 上传页](https://github.com/Arthurescc/studio-background-portfolio/releases/new)。上传只使用 GitHub 账号和仓库写入权限，不经过 ChatGPT 登录或地区校验。

1. 登录 GitHub，打开 Release 上传页。
2. 创建批次标签和标题，选择一个或多个 `.zip` 文件并发布。
3. 自动化程序立即读取 ZIP 内的 JPG、JPEG、PNG 和 WebP 文件名，为每张图预分配固定 URL，并优先发布 Excel/CSV 清单。
4. 随后原图、尺寸和轻量预览会载入这些已分配 URL；地址不会因处理顺序改变。

建议按主题拆包，例如：

```text
minimal-podiums-001.zip
natural-light-studios-001.zip
fabric-backgrounds-001.zip
stone-and-wood-scenes-001.zip
```

## 压缩包规范

- 支持：`.jpg`、`.jpeg`、`.png`、`.webp`
- 可以包含多层文件夹，系统会自动扫描。
- 文件名尽量使用英文、数字、连字符和下划线。
- 不要放入密码保护压缩包、可执行文件或与素材无关的文件。
- 每个 Release 建议放 500–1000 张；更大的图库拆成多个批次能缩短自动处理时间，也方便用户按主题下载。
- 同一批次如需重新处理，可在 Actions 中手动运行导入任务；相同文件会覆盖，不会重复创建。

## 为什么不直接提交所有原图

GitHub 的普通 Git 仓库不适合长期存放数十 GB 的二进制图片：单文件上限为 100 MB，仓库体积过大后克隆、浏览和自动处理都会明显变慢。Release 用于保存完整 ZIP 和可单独下载的原图；普通 Git 分支仅保存网页、索引和压缩后的预览图。

## 许可

除非单个 Release 另有说明，本项目素材计划采用 [CC BY 4.0](LICENSE.md) 发布：允许复制、修改和再分发，包括商业使用，但需要合理署名。

上传素材前请确认你拥有公开发布和授权这些内容的权利。
