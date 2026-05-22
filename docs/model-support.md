# Model Support

The knowledge base automatically adapts to 38 known models across three profiles. Not listed? It will auto-detect from the model name.

## Profile Overview

| Profile | Model Size | Entries | Format | Use When |
|:---|:---|:---:|:---|:---|
| **Small** | 7-14B | 3 | Full | Maximum help for small models |
| **Medium** | 14-32B | 5 | Condensed | Balanced help for mid-size models |
| **Large** | 30B+ | 8 | Reference | Quick reminders for large models |

## Full Model List

| Model | Profile | Context Window | Entries | Mode |
|:---|:---|:---:|:---:|:---|
| codellama:7b | small | 4096 | 3 | full |
| codellama:7b-instruct | small | 4096 | 3 | full |
| codellama:13b | small | 4096 | 3 | full |
| codellama:13b-instruct | small | 4096 | 3 | full |
| codellama:70b | large | 16384 | 8 | reference |
| codellama:70b-instruct | large | 16384 | 8 | reference |
| codestral:22b | medium | 8192 | 5 | condensed |
| codestral-mamba:7b | medium | 8192 | 5 | condensed |
| command-r:35b | medium | 8192 | 5 | condensed |
| command-r-plus:104b | large | 16384 | 8 | reference |
| deepseek-coder:6.7b | small | 4096 | 3 | full |
| deepseek-coder:6.7b-instruct | small | 4096 | 3 | full |
| deepseek-coder-v2:16b | medium | 8192 | 5 | condensed |
| deepseek-coder-v2:236b | large | 16384 | 8 | reference |
| gemma-2:27b | medium | 8192 | 5 | condensed |
| granite-code:8b | small | 4096 | 3 | full |
| llama3.1:70b | large | 16384 | 8 | reference |
| llama3.1:70b-instruct | large | 16384 | 8 | reference |
| llama3.3:70b | large | 16384 | 8 | reference |
| llama3.3:70b-instruct | large | 16384 | 8 | reference |
| mixtral:8x7b | medium | 8192 | 5 | condensed |
| mixtral:8x7b-instruct | medium | 8192 | 5 | condensed |
| phi-3:14b | small | 4096 | 3 | full |
| phi-3:mini | small | 4096 | 3 | full |
| qwen2.5-coder:7b | small | 4096 | 3 | full |
| qwen2.5-coder:7b-instruct | small | 4096 | 3 | full |
| qwen2.5-coder:14b | small | 4096 | 3 | full |
| qwen2.5-coder:14b-instruct | small | 4096 | 3 | full |
| qwen2.5-coder:32b | medium | 8192 | 5 | condensed |
| qwen2.5-coder:32b-instruct | medium | 8192 | 5 | condensed |
| qwen2.5:72b | large | 16384 | 8 | reference |
| qwen2.5:72b-instruct | large | 16384 | 8 | reference |
| qwq:32b | medium | 8192 | 5 | condensed |
| qwq:32b-preview | medium | 8192 | 5 | condensed |
| starcoder2:3b | small | 4096 | 3 | full |
| starcoder2:7b | small | 4096 | 3 | full |
| starcoder2:15b | small | 4096 | 3 | full |
| yi-coder:34b | medium | 8192 | 5 | condensed |

## Auto-Detection

If your model isn't in the list, the system auto-detects the profile from the model name:

```bash
# Extracts "7b" → small profile
llm-kb prompt "write a REST API" --model my-custom-model:7b

# Extracts "32b" → medium profile
llm-kb prompt "write a REST API" --model my-custom-model:32b

# Extracts "70b" → large profile
llm-kb prompt "write a REST API" --model my-custom-model:70b
```

## Request a New Model

Open a [model request issue](https://github.com/glennguilloux/llm-knowledge-base/issues/new?template=model_request.md) with:
- Model name and parameter count
- Context window size
- Recommended profile (small/medium/large)
