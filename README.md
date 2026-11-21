# 匡子闲的个人主页

[匡子闲（kuangzixian）的个人主页](https://kuangzixian.pages.dev/)，也是一个 QQ 空间风格的小站。我是一名后端开发工程师，之前做了三年游戏，现在在即刻做后端开发。业余做了 [EasyOffer](https://github.com/kuangzixian/easy-offer) 和 [EasyLife](https://github.com/kuangzixian/easy-life)。

静态 HTML / CSS / 原生 JavaScript，部署在 Cloudflare Pages。没有构建工具链，也不引用会被中国大陆拦截的外部字体或脚本 CDN。主页、日志、读书、音乐、桌游、推荐网站、留言板、个人档用选项卡切换。留言板和访问量由 Cloudflare Pages Functions + D1 提供；访问量每人每天最多计 1 次。 站点支持中文、英语、西班牙语、韩语和日语。中文在 `/`，其他语言分别在 `/en/`、`/es/`、`/ko/`、`/ja/`。界面文案会翻译，书名、歌名、对话正文和留言保持原文。语言选择会记在浏览器里，也可以用页面上的语言开关切换。

## 本地预览

直接用浏览器打开 `index.html`，或在本目录启动任意静态服务器。留言板和访问量需要下面的 Functions 本地或线上环境。

机器可读档案：

- 个人资料：`data/profile.json`
- 阅读明细：`data/reading.json`（来自微信读书公开书架；私密书和「文章收藏」未收录）
- 与 GPT 的对话：`data/chats.json`
- 音乐口味：`data/music.json`
- 桌游：`data/boardgames.json`
- 推荐网站：`data/sites.json`
- 界面翻译：`data/i18n.json`

页面上的互动（抽书、换一句、主题切换等）都是本地脚本，不依赖外部 CDN。

## 构建和部署

静态输出由脚本复制到 `dist/`，并生成 AI 友好文件：

```bash
python3 scripts/build_dist.py
npx wrangler pages deploy dist --project-name kuangzixian --branch main
```

也可以在设置了 `CLOUDFLARE_API_TOKEN` 后运行 `bash scripts/deploy.sh`（可选 `CLOUDFLARE_ACCOUNT_ID`）。不要用 Dashboard 的 zip 直传，那样不会带上 Functions。

`ADMIN_TOKEN` 和 `IP_HASH_SALT` 是 Pages 密钥，不要写进仓库。本地调试用 `.dev.vars`（已加入 `.gitignore`），可以从 `.dev.vars.example` 复制后自行填写。

## 增收内容

- **文章 / 对话**：把条目加进 `data/chats.json`，或运行 `python3 scripts/add_chat.py <ChatGPT分享链接>`，再补上标题和摘要。对话正文在 `/writing/<id>`。旧地址 `/chat?id=<id>` 和 `/chat.html?id=<id>` 会跳转到新地址。
- **桌游**：往 `data/boardgames.json` 的 `games` 数组追加一条（`id`、`name_zh`、`name_en`、`players`、`genre_zh`、`genre_en`、`blurb_zh`、`blurb_en`、`emoji`）。介绍只写公开的人数和类型，不要编个人评分或对局次数。
- **推荐网站**：往 `data/sites.json` 的 `sites` 数组追加一条（必填 `id`、`url`、`name`；可选 `canonical`、`domain`、`title`、`description`、`image`、`image_alt`、`image_source`、`favicon`、`emoji`、`own`）。`own` 为 true 时显示「自己做的 / Made by me」标记。介绍只摘自站点自己的公开信息，不要编造，网址保持原样。数组顺序就是页面上的顺序。旧地址 `#friends`、`#links` 会转到 `#sites`。
- **音乐**：口味数据在 `data/music.json`，分析报告在 `/music/report`。

改完数据后运行 `python3 scripts/build_dist.py` 再部署。构建时会把 `data/sites.json`、`data/chats.json` 和 `data/boardgames.json` 写进 `dist/index.html`，并为每篇对话生成独立的 `/writing/<id>` 页面（含标题、摘要、正文和结构化数据）。未知路径由 `404.html` 以 HTTP 404 返回，不要加 SPA 回退。构建时还会为每种语言生成对应的首页和 `/writing/<id>` 页面，并带上 hreflang。已经写进页面的推荐网站、日志和桌游列表带有 `data-static="1"`，前端脚本不会再用 JSON 覆盖，以免把已翻译的内容冲掉。

## AI 友好页面

构建时会生成给 AI agent 阅读的文本版本，结构参考 [tuxi.dev](https://tuxi.dev/llms.txt)：

- `/llms.txt`：身份、项目、阅读概况、对话列表和 agent 使用说明
- `/llms-full.txt`：更完整的档案，含公开书架、划线和对话全文
- `/writing/<id>`：每篇对话的独立 HTML 页面
- `/index.md`、`/reading.md`、`/writing.md`、`/writing/<id>.md`、`/music.md`、`/boardgames.md`、`/sites.md`
- `/sitemap.md`、`/sitemap.xml`、`/robots.txt`

访问 `/?mode=agent` 会跳转到 `/index.md`。`robots.txt` 里的 `Content-Signal` 目前是 `ai-train=no`（允许检索和作为回答依据，不允许用来训练），并显式允许用于 ChatGPT 搜索的 OAI-SearchBot、拒绝用于训练的 GPTBot，如需修改，改 `scripts/build_ai.py` 后再部署。不要手改这些生成文件，改数据后再构建即可。

## 留言板

访客可以留下昵称和一句话，不用登录。后端是 Cloudflare Pages Functions + D1，数据存在 `kuangzixian-guestbook`。

后台 zip 直传不能带上 Functions，必须用 wrangler 部署：

```bash
export CLOUDFLARE_API_TOKEN="..."
export CLOUDFLARE_ACCOUNT_ID="5c671af519baf38ea22b836d9430674a"
bash scripts/deploy.sh
```

API token 需要的权限（Account 范围）：

- Cloudflare Pages: Edit
- D1: Edit

D1 绑定写在 `wrangler.toml` 里。用 wrangler 部署时，这个文件就是绑定的唯一来源，不必再去 Dashboard 里手动加；如果只在后台绑定、而不写进 `wrangler.toml`，下一次 `wrangler pages deploy` 会把后台绑定清掉。

首次部署后还要设置两个密钥（脚本不会代设）：

```bash
npx wrangler pages secret put ADMIN_TOKEN --project-name kuangzixian
npx wrangler pages secret put IP_HASH_SALT --project-name kuangzixian
```

管理员删除一条留言：

```bash
# 推荐：脚本从环境变量或本地密钥文件读取 token，不要把 token 写进仓库
bash scripts/delete_message.sh <id>

# 或手动调用
curl -X DELETE "https://kuangzixian.pages.dev/api/messages/<id>" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

本地调试：

```bash
cp .dev.vars.example .dev.vars   # 填入本地测试用的 ADMIN_TOKEN 和 IP_HASH_SALT
python3 scripts/build_dist.py
npx wrangler d1 migrations apply kuangzixian-guestbook --local
npx wrangler pages dev dist --port 8788
```

## 致谢

「音乐」栏目的分析报告由 [musicanalysis](https://github.com/ryohgicc/musicanalysis) 生成。
