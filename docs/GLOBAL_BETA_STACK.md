# 海外 / 全球邀请制 Beta：默认云端方案

## 默认选择

第一阶段采用托管服务组合，而不是租一台需要自己维护的服务器：

| 能力 | 默认服务 | 为什么 |
| --- | --- | --- |
| 数据库、认证、私有文件存储 | Supabase | 一个控制台提供 PostgreSQL、用户认证、私有 Storage 和访问策略，适合早期多用户产品。 |
| Web / API / CPU Worker | Render | 可分别部署 Web API 和后台 worker，不需要维护操作系统或 GPU。 |
| 域名与 DNS | Cloudflare | 负责域名解析、HTTPS、基础防护；第一阶段不承载用户原书。 |
| 事务邮件 | 后续选择 | 邀请、验证、密码重置在实现账号系统后接入。 |

## 第一阶段实际运行形态

```text
用户浏览器
   ↓ https://app.<你的域名>
Render：Web / API（CPU）
   ├── Supabase Auth：登录与会话
   ├── Supabase PostgreSQL：书目、进度、笔记、权限
   └── Supabase Storage 私有 bucket：用户原书、封面、提取产物

Render：CPU Worker
   └── 只执行元数据、封面、EPUB/PDF 文本提取任务
```

没有 GPU，没有模型 API Key，没有 OCR/LLM 调用，也没有用户付费系统。

## 为什么不先租裸 VPS

裸 VPS 意味着你要自行维护：操作系统升级、HTTPS、数据库备份、磁盘扩容、访问控制、故障恢复。对邀请制 Beta，托管 PostgreSQL / Storage 能明显降低数据丢失和运维风险；真正需要一台“服务器”的部分交给 Render 的托管应用服务即可。

## 开通顺序

1. 注册或确认 Supabase、Render、Cloudflare 账号；
2. 注册产品域名；
3. 在 Supabase 建立一个生产项目：开启邮件登录，创建私有 Storage bucket，启用数据库备份；
4. 创建 Render 的 staging Web / API 服务与 CPU Worker；
5. 把域名 DNS 接到 Cloudflare，并仅开放 HTTPS；
6. 完成多用户代码、私有上传和权限测试后再配置生产环境；
7. 首批仅邀请 5–10 位测试用户，不开启公共注册；
8. 每周验证备份恢复、删除书籍和跨用户越权访问。

## 需要你亲自完成的账户动作

这些涉及付款、账户所有权和域名，不能由项目代码替代：

- 选择并购买域名；
- 在 Supabase / Render 绑定支付方式或选择免费试用方案；
- 决定生产项目归属个人账号还是未来团队组织；
- 配置用于邮件登录的发件域名（可在账号功能实现后做）。

项目不应存储任何平台 token、数据库密码或服务密钥；它们只存在各平台的环境变量/密钥管理中。
