# LLM

模型提供商一般都会兼容 openai 接口协议，默认使用 openai 的 chat.completion 或 responses 接口来实现对 llm 的调用；

## 输入参数

- `--model`：可以从 `references/llm_client.json` 中选择模型。 如无特殊说明，默认使用 doubao-1.8 模型；
  - 注意配置文件中的 `extra_body` 字段要在代码中一起透传；
  
## 输出字段

LLM 模型一般都会返回这几个字段，但不同提供商、不同接口返回的具体名称可能有所不同。有必要时你需要自行理解并对应到以下几个字段。在测试验证完成后，解释给用户。

- `model_response`: 模型直接回复的内容

- `model_response_reasoing`：可选，如果模型有返回推理思考的过程，输出到此字段中；

- `input_message`：经过任务相关的逻辑，最终输入到模型中的输入。可能是字符串，也可能是消息列表；

- `usage`：本次请求使用的 token 数。存成字典的形式，包含 `input_tokens`、`cached_tokens`、`output_tokens` 三个字段
