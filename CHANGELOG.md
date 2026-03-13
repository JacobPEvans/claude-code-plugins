# Changelog

## [1.6.0](https://github.com/JacobPEvans/claude-code-plugins/compare/v1.5.0...v1.6.0) (2026-03-13)


### Bug Fixes

* **process-cleanup:** replace bash 4+ declare -A with sort -u deduplication ([#117](https://github.com/JacobPEvans/claude-code-plugins/issues/117)) ([d89e006](https://github.com/JacobPEvans/claude-code-plugins/commit/d89e006b0b6dfb443d8c9c12d7245f337c50e6b3))

## [1.5.0](https://github.com/JacobPEvans/claude-code-plugins/compare/v1.4.0...v1.5.0) (2026-03-10)


### Features

* add 4 standards plugins migrated from auto-loaded rules ([#113](https://github.com/JacobPEvans/claude-code-plugins/issues/113)) ([fcf8acf](https://github.com/JacobPEvans/claude-code-plugins/commit/fcf8acfa0b0385551b15b9061c515df020638276))

## [1.4.0](https://github.com/JacobPEvans/claude-code-plugins/compare/v1.3.0...v1.4.0) (2026-03-08)


### Features

* disable automatic triggers on Claude-executing workflows ([6c42de9](https://github.com/JacobPEvans/claude-code-plugins/commit/6c42de9d7f8cb3bfc28271714e462f91f8f3c53d))

## [1.3.0](https://github.com/JacobPEvans/claude-code-plugins/compare/v1.2.0...v1.3.0) (2026-03-07)


### Bug Fixes

* port main-branch-guard to Python, fix CI and TC14 JSON ([#108](https://github.com/JacobPEvans/claude-code-plugins/issues/108)) ([92e323e](https://github.com/JacobPEvans/claude-code-plugins/commit/92e323efda21e57ab4f2807457db0e428d687341))

## [1.2.0](https://github.com/JacobPEvans/claude-code-plugins/compare/v1.1.0...v1.2.0) (2026-03-07)


### Features

* **rebase-pr:** auto-dispatch to Haiku subagent with bypassPermissions ([#103](https://github.com/JacobPEvans/claude-code-plugins/issues/103)) ([8af9bec](https://github.com/JacobPEvans/claude-code-plugins/commit/8af9bec5b715231865240da952e3b2195bc35b9f))


### Bug Fixes

* **content-guards:** lower PR/issue rate limit to 5/day and add duplicate detection ([#101](https://github.com/JacobPEvans/claude-code-plugins/issues/101)) ([1563350](https://github.com/JacobPEvans/claude-code-plugins/commit/1563350df7d4cfe61dfd20b72b5019f155302e17))

## [1.1.0](https://github.com/JacobPEvans/claude-code-plugins/compare/v1.0.0...v1.1.0) (2026-03-07)


### ⚠ BREAKING CHANGES

* Plugin consolidation and skill renames

### Features

* add ci and local test automation ([#41](https://github.com/JacobPEvans/claude-code-plugins/issues/41)) ([181c6a5](https://github.com/JacobPEvans/claude-code-plugins/commit/181c6a58f7baeb98ba77642c23582ba269dcb02a))
* add codeql-resolver plugin with 3-tier resolution architecture ([#8](https://github.com/JacobPEvans/claude-code-plugins/issues/8)) ([a45ac3b](https://github.com/JacobPEvans/claude-code-plugins/commit/a45ac3bd8f2bd54cb00de6d29954ba03adfb2983))
* add full AI workflow suite ([#75](https://github.com/JacobPEvans/claude-code-plugins/issues/75)) ([4a1d6fe](https://github.com/JacobPEvans/claude-code-plugins/commit/4a1d6fecef0dcdef504f566764868b75ad4ac06b))
* add gh-aw agentic workflows and cspell config ([#64](https://github.com/JacobPEvans/claude-code-plugins/issues/64)) ([9f90f33](https://github.com/JacobPEvans/claude-code-plugins/commit/9f90f331b815e957749a1d9078710f082bf3eaef))
* add rate limiting, README validation, and externalize init-worktree ([#72](https://github.com/JacobPEvans/claude-code-plugins/issues/72)) ([97bfa05](https://github.com/JacobPEvans/claude-code-plugins/commit/97bfa05a43de066c58fa637acc41d9734fad0ab6))
* add token-validator and issue-limiter plugins ([#2](https://github.com/JacobPEvans/claude-code-plugins/issues/2)) ([8a64289](https://github.com/JacobPEvans/claude-code-plugins/commit/8a642899d2c5287cb2cdb48c3f2b5209c796ba79))
* add webfetch-guard and markdown-validator plugins ([705dbe8](https://github.com/JacobPEvans/claude-code-plugins/commit/705dbe82f0ddfac8ef6c2aeb24ec6b7aad3ba0fc))
* adopt conventional branch standard (feature/, bugfix/) ([#74](https://github.com/JacobPEvans/claude-code-plugins/issues/74)) ([e826b67](https://github.com/JacobPEvans/claude-code-plugins/commit/e826b677d471d0771d34c66af4ece45ff671c588))
* **ci:** add release-please and improve renovate auto-merge ([#53](https://github.com/JacobPEvans/claude-code-plugins/issues/53)) ([94fbaca](https://github.com/JacobPEvans/claude-code-plugins/commit/94fbaca05b06da71a6039421eb4f039d7a27874e))
* consolidate plugins from 15 to 8 with consistent naming ([#31](https://github.com/JacobPEvans/claude-code-plugins/issues/31)) ([d36a028](https://github.com/JacobPEvans/claude-code-plugins/commit/d36a028c4e62d0a89fea8f902a1689a29c34b1f4))
* enhance resolve-pr-threads with comment reading ([#46](https://github.com/JacobPEvans/claude-code-plugins/issues/46)) ([fc6a34c](https://github.com/JacobPEvans/claude-code-plugins/commit/fc6a34c553a3699b932dc92cb70325ee9e2d139b))
* **finalize-pr:** add multi-PR modes, bot support, and skill authoring guidance ([#70](https://github.com/JacobPEvans/claude-code-plugins/issues/70)) ([7704876](https://github.com/JacobPEvans/claude-code-plugins/commit/7704876d2c012f4f9d854a9a49e2ed7d84d6682f))
* **finalize-pr:** add Phase 4 to auto-update PR metadata ([#65](https://github.com/JacobPEvans/claude-code-plugins/issues/65)) ([1c1e881](https://github.com/JacobPEvans/claude-code-plugins/commit/1c1e881a5b931e9e07edffb216dea158c848bf6b))
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
* **agents-md:** add resolve-pr-threads and shape-issues to github-workflows entry ([81e61be](https://github.com/JacobPEvans/claude-code-plugins/commit/81e61be3ccc587be23977c52debf7a2bfaed0748))
* **ci:** dispatch flake update to nix-ai instead of nonexistent nix repo ([#73](https://github.com/JacobPEvans/claude-code-plugins/issues/73)) ([1ed7c40](https://github.com/JacobPEvans/claude-code-plugins/commit/1ed7c40276327f2cf3b71c7c414e2cdd91cadd0a))
* **codeql-resolver:** convert flat skill files to skill directories ([#59](https://github.com/JacobPEvans/claude-code-plugins/issues/59)) ([81ab6af](https://github.com/JacobPEvans/claude-code-plugins/commit/81ab6af92f9074fb44f33111d3228a076d753d8f))
* **content-guards:** clarify extract-to-files means committed artifacts ([#62](https://github.com/JacobPEvans/claude-code-plugins/issues/62)) ([ed82608](https://github.com/JacobPEvans/claude-code-plugins/commit/ed82608f2b649db0314efbab78bc507b6091e23b))
* **content-guards:** handle empty config_flag array in bash 3.2 ([#55](https://github.com/JacobPEvans/claude-code-plugins/issues/55)) ([0385c9b](https://github.com/JacobPEvans/claude-code-plugins/commit/0385c9b502cec6a2c55aad8391b39fb4f83bf89e))
* **content-guards:** improve token-validator error message with detailed resolution steps ([#37](https://github.com/JacobPEvans/claude-code-plugins/issues/37)) ([cf355e3](https://github.com/JacobPEvans/claude-code-plugins/commit/cf355e31178ccde28a546c9afbedc211e94bf3b1))
* **content-guards:** resolve unbound variable error in markdown validator ([#39](https://github.com/JacobPEvans/claude-code-plugins/issues/39)) ([2202144](https://github.com/JacobPEvans/claude-code-plugins/commit/2202144ee388e39cf012d0ea2f1521b28f2808fa))
* **content-guards:** support markdown linting in git worktrees ([#48](https://github.com/JacobPEvans/claude-code-plugins/issues/48)) ([8cbf6a1](https://github.com/JacobPEvans/claude-code-plugins/commit/8cbf6a1201db2b00c92bdbf79ff94f09281c481b))
* convert GraphQL queries to single-line format in resolve-pr-threads ([#35](https://github.com/JacobPEvans/claude-code-plugins/issues/35)) ([0b482c5](https://github.com/JacobPEvans/claude-code-plugins/commit/0b482c51476ab6a60d9bcad71d0e5a930e360888))
* correct best-practices permissions and add ref-scoped concurrency ([#77](https://github.com/JacobPEvans/claude-code-plugins/issues/77)) ([f5806d5](https://github.com/JacobPEvans/claude-code-plugins/commit/f5806d5c7c13ebd72224cc5e0338fcd8aa3499e5))
* correct plugin.json schema violations for all 8 plugins ([#33](https://github.com/JacobPEvans/claude-code-plugins/issues/33)) ([770b2b4](https://github.com/JacobPEvans/claude-code-plugins/commit/770b2b442d0d95258dba90febde4a974961a7bea))
* **finalize-pr:** remove pre-PR steps from workflow diagram ([#76](https://github.com/JacobPEvans/claude-code-plugins/issues/76)) ([6dca3fc](https://github.com/JacobPEvans/claude-code-plugins/commit/6dca3fc6d4b3f98dd6d3b05365e45187257f050d))
* **git-guards:** always scan subcommand for hook-path bypass pattern ([#88](https://github.com/JacobPEvans/claude-code-plugins/issues/88)) ([63bd1c6](https://github.com/JacobPEvans/claude-code-plugins/commit/63bd1c694488f5ee7ae5dc7a21b9241469c4583f))
* **git-guards:** auto-allow git worktree remove ([#54](https://github.com/JacobPEvans/claude-code-plugins/issues/54)) ([9d0bec6](https://github.com/JacobPEvans/claude-code-plugins/commit/9d0bec66bad8a908e26cd318133231006c1c8ae7))
* **git-guards:** check DENY patterns against extracted subcommand for git global options ([#80](https://github.com/JacobPEvans/claude-code-plugins/issues/80)) ([48daad8](https://github.com/JacobPEvans/claude-code-plugins/commit/48daad89176d71a06d108e56472edbbff96267d0))
* **git-guards:** make test_graphql_guidance.py executable ([2bbb4cf](https://github.com/JacobPEvans/claude-code-plugins/commit/2bbb4cfeee75fb97206eba0005156d0773d3527e))
* **git-guards:** use shlex tokenisation in hook-path fallback to prevent false positives ([#93](https://github.com/JacobPEvans/claude-code-plugins/issues/93)) ([a0edfa0](https://github.com/JacobPEvans/claude-code-plugins/commit/a0edfa05c6e7379ce8d25fb1f5a75ffae96b6325))
* **git-guards:** use word-boundary regex for mutation name detection ([3db588f](https://github.com/JacobPEvans/claude-code-plugins/commit/3db588f78f5fe7f03deeb67d2018124d52365932))
* improve GraphQL reliability and prevent git-guard false positives ([500d893](https://github.com/JacobPEvans/claude-code-plugins/commit/500d89366e1cd7cf852a341f1de452e4891c0346))
* **markdown-validator:** bundle default config and add fallback resolution ([#26](https://github.com/JacobPEvans/claude-code-plugins/issues/26)) ([103a108](https://github.com/JacobPEvans/claude-code-plugins/commit/103a108e38f530f6598b85cb51ebc3c2943bdd21))
* **markdown-validator:** use global markdownlint config with MD013=160 ([#11](https://github.com/JacobPEvans/claude-code-plugins/issues/11)) ([326c27b](https://github.com/JacobPEvans/claude-code-plugins/commit/326c27b540827030a91761b467d7a3f104a8e3e6))
* prevent main-branch-guard from blocking non-repository files ([#36](https://github.com/JacobPEvans/claude-code-plugins/issues/36)) ([7abe699](https://github.com/JacobPEvans/claude-code-plugins/commit/7abe69987162fa7859fc08c4718377e9f1424aaf))
* **release:** replace bump-minor-pre-major with versioning always-bump-minor ([#89](https://github.com/JacobPEvans/claude-code-plugins/issues/89)) ([d8a1670](https://github.com/JacobPEvans/claude-code-plugins/commit/d8a1670e8bcfcee1a97428e84cf473b16b4b0970))
* replace jq != operator and add markdownlint troubleshooting ([#68](https://github.com/JacobPEvans/claude-code-plugins/issues/68)) ([3c61cb5](https://github.com/JacobPEvans/claude-code-plugins/commit/3c61cb5a5ada52b1fcb5e114f0ef7e0811ae37e7))
* **resolve-pr-threads:** cut 40% of lines to eliminate hallucination failure modes ([#52](https://github.com/JacobPEvans/claude-code-plugins/issues/52)) ([949151c](https://github.com/JacobPEvans/claude-code-plugins/commit/949151cdf100df7674422581213996d870319425))
* **resolve-pr-threads:** rewrite negation rules as affirmative clarity ([#58](https://github.com/JacobPEvans/claude-code-plugins/issues/58)) ([d5a25c4](https://github.com/JacobPEvans/claude-code-plugins/commit/d5a25c4e436337be9abf2160d4b598213d68042b))
* revert to cclint@latest (no versions published yet) ([55c2488](https://github.com/JacobPEvans/claude-code-plugins/commit/55c24883174f3978526d1d30f22e5309e0915401))
* **squash-merge-pr:** use --delete-branch, git switch main, and consistent placeholder style ([b2743f7](https://github.com/JacobPEvans/claude-code-plugins/commit/b2743f73bb8e42ad56282706bb16d261a061418b))
* **squash-merge-pr:** use @ import syntax and document git-workflows dependency ([479baef](https://github.com/JacobPEvans/claude-code-plugins/commit/479baef8846414fcf8cf8fc35fca83bd72afb106))
* **sync-main:** remove confirmation gates — merge immediately on invoke ([#78](https://github.com/JacobPEvans/claude-code-plugins/issues/78)) ([0add171](https://github.com/JacobPEvans/claude-code-plugins/commit/0add1712ccd2812e3b9b91739d27b2fea9aeef65))
* use correct flake input name jacobpevans-cc-plugins ([#28](https://github.com/JacobPEvans/claude-code-plugins/issues/28)) ([8c18e26](https://github.com/JacobPEvans/claude-code-plugins/commit/8c18e262dcc436376a14388679f423470dc35446))
* use Go to install cclint, validate both plugins ([0e0890c](https://github.com/JacobPEvans/claude-code-plugins/commit/0e0890c45e8f9ce405eb746f592ef31072f54932))
