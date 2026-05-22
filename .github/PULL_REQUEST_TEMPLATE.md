## Description

<!-- What does this PR add or fix? -->

## Type

- [ ] New knowledge entry
- [ ] Fix to existing entry
- [ ] New model profile
- [ ] Bug fix
- [ ] Documentation
- [ ] Other

## Checklist

- [ ] Entry added under the correct category folder structure
- [ ] Frontmatter contains all required fields (`id`, `title`, `language`, `category`, `tags`, `retrieval_hint`, `confidence`)
- [ ] Entry contains at least **3+ WRONG/CORRECT pairs** in the Mistakes section
- [ ] Entry contains at least **3+ Gotchas**
- [ ] Entry contains at least **2+ Related links** matching existing `.md` files
- [ ] `llm-kb validate` exits with code 0
- [ ] All tests pass (`python -m pytest -v`)
- [ ] No credentials, tokens, or API keys in any file

## Testing

<!-- How did you test this? What did `llm-kb validate` and `pytest` output? -->

## Related Issues

<!-- Link any related issues: Fixes #123, Closes #456 -->
