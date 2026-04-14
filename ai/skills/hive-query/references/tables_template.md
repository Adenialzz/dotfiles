# Tables Template

把这里当成表文档和口径备注的入口。表多起来后，优先按主题拆成多个文件，再在这里补索引。

## 建议记录项

- 表全名
- 业务含义
- 数据粒度
- 主键或唯一键
- 分区字段和分区规则
- 常用过滤条件
- 常见 join key
- 重要字段说明
- 口径 caveat
- 示例 SQL

## 单表模板

````md
## <db.table_name>

- 业务含义：
- 数据粒度：
- 主键或唯一键：
- 分区字段：
- 常用过滤条件：
- 常见 join key：
- 口径 caveat：

### 重要字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
|  |  |  |

### 示例 SQL

```sql
SELECT
  *
FROM <db.table_name>
WHERE <partition_column> = '${date}'
LIMIT 20
```
````
