# Changelog

## [2.0.0](https://github.com/JacobPEvans/claude-code-plugins/compare/v1.0.0...v2.0.0) (2026-03-01)


### ⚠ BREAKING CHANGES

* Plugin consolidation and skill renames

### Features

* add ci and local test automation ([#41](https://github.com/JacobPEvans/claude-code-plugins/issues/41)) ([181c6a5](https://github.com/JacobPEvans/claude-code-plugins/commit/181c6a58f7baeb98ba77642c23582ba269dcb02a))
* add codeql-resolver plugin with 3-tier resolution architecture ([#8](https://github.com/JacobPEvans/claude-code-plugins/issues/8)) ([a45ac3b](https://github.com/JacobPEvans/claude-code-plugins/commit/a45ac3bd8f2bd54cb00de6d29954ba03adfb2983))
* add gh-aw agentic workflows and cspell config ([#64](https://github.com/JacobPEvans/claude-code-plugins/issues/64)) ([9f90f33](https://github.com/JacobPEvans/claude-code-plugins/commit/9f90f331b815e957749a1d9078710f082bf3eaef))
* add token-validator and issue-limiter plugins ([#2](https://github.com/JacobPEvans/claude-code-plugins/issues/2)) ([8a64289](https://github.com/JacobPEvans/claude-code-plugins/commit/8a642899d2c5287cb2cdb48c3f2b5209c796ba79))
* add webfetch-guard and markdown-validator plugins ([705dbe8](https://github.com/JacobPEvans/claude-code-plugins/commit/705dbe82f0ddfac8ef6c2aeb24ec6b7aad3ba0fc))
* **ci:** add release-please and improve renovate auto-merge ([#53](https://github.com/JacobPEvans/claude-code-plugins/issues/53)) ([94fbaca](https://github.com/JacobPEvans/claude-code-plugins/commit/94fbaca05b06da71a6039421eb4f039d7a27874e))
* consolidate plugins from 15 to 8 with consistent naming ([#31](https://github.com/JacobPEvans/claude-code-plugins/issues/31)) ([d36a028](https://github.com/JacobPEvans/claude-code-plugins/commit/d36a028c4e62d0a89fea8f902a1689a29c34b1f4))
* enhance resolve-pr-threads with comment reading ([#46](https://github.com/JacobPEvans/claude-code-plugins/issues/46)) ([fc6a34c](https://github.com/JacobPEvans/claude-code-plugins/commit/fc6a34c553a3699b932dc92cb70325ee9e2d139b))
* **git-guards:** add GraphQL command guidance for known failure patterns ([232eee3](https://github.com/JacobPEvans/claude-code-plugins/commit/232eee3becf85690f543e10a9fe57000e02a9f1d))
* **git-guards:** allow git rm without confirmation ([#63](https://github.com/JacobPEvans/claude-code-plugins/issues/63)) ([c94d959](https://github.com/JacobPEvans/claude-code-plugins/commit/c94d959d21056ae2e02c6cb1a1b0079b5fd72d77))
* **git-guards:** block gh pr comment, enforce GraphQL review threads ([#56](https://github.com/JacobPEvans/claude-code-plugins/issues/56)) ([c6b6234](https://github.com/JacobPEvans/claude-code-plugins/commit/c6b6234441ca471ffa15a315013889a9d22a2441))
* **git-permission-guard:** add centralized git/gh permission hook plugin ([#12](https://github.com/JacobPEvans/claude-code-plugins/issues/12)) ([12268b0](https://github.com/JacobPEvans/claude-code-plugins/commit/12268b09e8038360030850df61cd290ea1133191))
* **git-rebase-workflow:** handle branch protection with CodeQL scanning ([#25](https://github.com/JacobPEvans/claude-code-plugins/issues/25)) ([9b40416](https://github.com/JacobPEvans/claude-code-plugins/commit/9b40416fa381ca116f54ac0acd2ad430eb73ca27))
* **github-workflows:** add trigger-ai-reviews skill ([#47](https://github.com/JacobPEvans/claude-code-plugins/issues/47)) ([b505c82](https://github.com/JacobPEvans/claude-code-plugins/commit/b505c82caeb26306d0db2d3f3b59d49f8d1b3d83))
* **main-branch-guard:** add PreToolUse hook to block main branch edits ([#22](https://github.com/JacobPEvans/claude-code-plugins/issues/22)) ([9456f5d](https://github.com/JacobPEvans/claude-code-plugins/commit/9456f5d6e9ea1c9dd26b5856d18602da7a4891a7))
* **markdown-validator:** add skip logic and MD013 fallback ([#27](https://github.com/JacobPEvans/claude-code-plugins/issues/27)) ([77cd37b](https://github.com/JacobPEvans/claude-code-plugins/commit/77cd37b01d35050f6859c4377f40a257a96b3d6f))
* migrate 13 commands to skills in 6 new plugins ([#23](https://github.com/JacobPEvans/claude-code-plugins/issues/23)) ([fb72d06](https://github.com/JacobPEvans/claude-code-plugins/commit/fb72d065726ecf5a62bf55d98a15224740381c06))
* **pr-review-toolkit:** add PR review thread resolution plugin ([#24](https://github.com/JacobPEvans/claude-code-plugins/issues/24)) ([3368eaa](https://github.com/JacobPEvans/claude-code-plugins/commit/3368eaa20a3b82b39b6dff9c25a88144f66fa63a))
* **process-cleanup:** add Stop hook plugin for orphaned MCP process cleanup ([#51](https://github.com/JacobPEvans/claude-code-plugins/issues/51)) ([27caa6f](https://github.com/JacobPEvans/claude-code-plugins/commit/27caa6f3d2d6b38d1b90a36098a90eba8854e095))
* **renovate:** extend shared preset for org-wide auto-merge rules ([#60](https://github.com/JacobPEvans/claude-code-plugins/issues/60)) ([b5197ed](https://github.com/JacobPEvans/claude-code-plugins/commit/b5197edf191e7e1aea80e04667eda1bd24c7f6bc))
* **webfetch-guard:** add grace period for previous year searches ([#9](https://github.com/JacobPEvans/claude-code-plugins/issues/9)) ([18a39a5](https://github.com/JacobPEvans/claude-code-plugins/commit/18a39a5d6bd9a125f961bd01ef138f5d26566cea))


### Bug Fixes

* add explicit GITHUB_TOKEN permissions to workflow ([a8f44d3](https://github.com/JacobPEvans/claude-code-plugins/commit/a8f44d39215b3cb8a4140781832f8cdbeb2a4551))
* **codeql-resolver:** convert flat skill files to skill directories ([#59](https://github.com/JacobPEvans/claude-code-plugins/issues/59)) ([81ab6af](https://github.com/JacobPEvans/claude-code-plugins/commit/81ab6af92f9074fb44f33111d3228a076d753d8f))
* **content-guards:** clarify extract-to-files means committed artifacts ([#62](https://github.com/JacobPEvans/claude-code-plugins/issues/62)) ([ed82608](https://github.com/JacobPEvans/claude-code-plugins/commit/ed82608f2b649db0314efbab78bc507b6091e23b))
* **content-guards:** handle empty config_flag array in bash 3.2 ([#55](https://github.com/JacobPEvans/claude-code-plugins/issues/55)) ([0385c9b](https://github.com/JacobPEvans/claude-code-plugins/commit/0385c9b502cec6a2c55aad8391b39fb4f83bf89e))
* **content-guards:** improve token-validator error message with detailed resolution steps ([#37](https://github.com/JacobPEvans/claude-code-plugins/issues/37)) ([cf355e3](https://github.com/JacobPEvans/claude-code-plugins/commit/cf355e31178ccde28a546c9afbedc211e94bf3b1))
* **content-guards:** resolve unbound variable error in markdown validator ([#39](https://github.com/JacobPEvans/claude-code-plugins/issues/39)) ([2202144](https://github.com/JacobPEvans/claude-code-plugins/commit/2202144ee388e39cf012d0ea2f1521b28f2808fa))
* **content-guards:** support markdown linting in git worktrees ([#48](https://github.com/JacobPEvans/claude-code-plugins/issues/48)) ([8cbf6a1](https://github.com/JacobPEvans/claude-code-plugins/commit/8cbf6a1201db2b00c92bdbf79ff94f09281c481b))
* convert GraphQL queries to single-line format in resolve-pr-threads ([#35](https://github.com/JacobPEvans/claude-code-plugins/issues/35)) ([0b482c5](https://github.com/JacobPEvans/claude-code-plugins/commit/0b482c51476ab6a60d9bcad71d0e5a930e360888))
* correct plugin.json schema violations for all 8 plugins ([#33](https://github.com/JacobPEvans/claude-code-plugins/issues/33)) ([770b2b4](https://github.com/JacobPEvans/claude-code-plugins/commit/770b2b442d0d95258dba90febde4a974961a7bea))
* **git-guards:** auto-allow git worktree remove ([#54](https://github.com/JacobPEvans/claude-code-plugins/issues/54)) ([9d0bec6](https://github.com/JacobPEvans/claude-code-plugins/commit/9d0bec66bad8a908e26cd318133231006c1c8ae7))
* **git-guards:** make test_graphql_guidance.py executable ([2bbb4cf](https://github.com/JacobPEvans/claude-code-plugins/commit/2bbb4cfeee75fb97206eba0005156d0773d3527e))
* **git-guards:** use word-boundary regex for mutation name detection ([3db588f](https://github.com/JacobPEvans/claude-code-plugins/commit/3db588f78f5fe7f03deeb67d2018124d52365932))
* improve GraphQL reliability and prevent git-guard false positives ([500d893](https://github.com/JacobPEvans/claude-code-plugins/commit/500d89366e1cd7cf852a341f1de452e4891c0346))
* **markdown-validator:** bundle default config and add fallback resolution ([#26](https://github.com/JacobPEvans/claude-code-plugins/issues/26)) ([103a108](https://github.com/JacobPEvans/claude-code-plugins/commit/103a108e38f530f6598b85cb51ebc3c2943bdd21))
* **markdown-validator:** use global markdownlint config with MD013=160 ([#11](https://github.com/JacobPEvans/claude-code-plugins/issues/11)) ([326c27b](https://github.com/JacobPEvans/claude-code-plugins/commit/326c27b540827030a91761b467d7a3f104a8e3e6))
* prevent main-branch-guard from blocking non-repository files ([#36](https://github.com/JacobPEvans/claude-code-plugins/issues/36)) ([7abe699](https://github.com/JacobPEvans/claude-code-plugins/commit/7abe69987162fa7859fc08c4718377e9f1424aaf))
* **resolve-pr-threads:** cut 40% of lines to eliminate hallucination failure modes ([#52](https://github.com/JacobPEvans/claude-code-plugins/issues/52)) ([949151c](https://github.com/JacobPEvans/claude-code-plugins/commit/949151cdf100df7674422581213996d870319425))
* **resolve-pr-threads:** rewrite negation rules as affirmative clarity ([#58](https://github.com/JacobPEvans/claude-code-plugins/issues/58)) ([d5a25c4](https://github.com/JacobPEvans/claude-code-plugins/commit/d5a25c4e436337be9abf2160d4b598213d68042b))
* revert to cclint@latest (no versions published yet) ([55c2488](https://github.com/JacobPEvans/claude-code-plugins/commit/55c24883174f3978526d1d30f22e5309e0915401))
* use correct flake input name jacobpevans-cc-plugins ([#28](https://github.com/JacobPEvans/claude-code-plugins/issues/28)) ([8c18e26](https://github.com/JacobPEvans/claude-code-plugins/commit/8c18e262dcc436376a14388679f423470dc35446))
* use Go to install cclint, validate both plugins ([0e0890c](https://github.com/JacobPEvans/claude-code-plugins/commit/0e0890c45e8f9ce405eb746f592ef31072f54932))
