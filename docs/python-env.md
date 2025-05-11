# Python Environment Considerations

## Introduction

Many of the currently available plugins for `python-lsp-server` need to run in or access your project's Python environment (virtualenv/venv) in order to work correctly, while others at least benefit from it (cf. the listing below). There are several ways to achieve this, which we'll discuss here.


## List of plugins

Here is a non-exhaustive list of plugins with information relevant to this discussion (credit goes to [David Vicente](https://github.com/david-vicente) for compiling the original list this is based on[^discussion]):

- **flake8:**
  - Version of Python interpreter in which it runs needs to match the project's.[^discussion]
  - Launches `flake8` in a subprocess (executable configurable).[^config]
- **Jedi:**
  - Should have access to project venv for certain functionality.[^discussion]
  - Runs entirely in same Python process as `pylsp`.
  - Can be configured to inspect a different environment.[^config]
- **pylsp-mypy**
  - Should run inside project venv so that Mypy can obtain type information for imported modules.
  - Launches `mypy` in a subprocess (executable configurable, but only if an unwieldy env var set).[^pylsp-mypy-config]
- **python-lsp-black**
  - Is commonly part of a project's dev dependencies and CI checks, so running with the project's exact version to get results consistent with CI may be preferable.
  - Runs entirely in same Python process as `pylsp`.
- **pylint:**
  - Should have access to project venv for certain functionality[^discussion].
  - Launches `pylint` in a subprocess (executable configurable).[^config]
- **Rope:**
  - Version of Python interpreter in which it runs needs to match the project's because it uses Python's own `ast` module for parsing.[^rope-ast]
  - Runs entirely in same Python process as `pylsp`.
- **Rope autoimport:**
  - Should run in project Python env so that it can find modules eligible for auto-import.
  - Runs entirely in same Python process as `pylsp`.
  - Python module search path can be _extended_ (but not reduced) using Rope's own per-project configuration.[^rope-config]

[^discussion]: [`python-lsp-server` discussion #304 (comment)](https://github.com/python-lsp/python-lsp-server/discussions/304#discussioncomment-4256015)
[^config]: [CONFIGURATION.md](../CONFIGURATION.md)
[^rope-ast]: [`rope` discussion #557 (comment)](https://github.com/python-rope/rope/discussions/557#discussioncomment-4272747)
[^rope-config]: [Rope docs: Configuration](https://rope.readthedocs.io/en/latest/configuration.html)
[^pylsp-mypy-config]: [`pylsp-mypy-config` README: Configuration](https://github.com/python-lsp/pylsp-mypy?tab=readme-ov-file#configuration)

### Conclusions

Many plugins should really run inside the project's virtualenv, but not all of these come with configuration options to facilitate this (e.g. the Black and Rope plugins).

So we can already see that it seems preferable to run `python-lsp-server` as a whole in the project environment.

In the section below, we'll compare this approach to others, while the section after that will discuss how to make your editor/IDE use the correct environment.


## Question 1: Where to install `python-lsp-server`, its plugins & their dependencies?

### Option 1 (bad): In the global system or user Python env

This is always a bad idea, so bad that many operating systems now make you add `--break-system-packages` to `pip` invocations when you try to do this. So it's not recommended in this case either.

### Option 2 (better but still bad): In a global virtualenv specifically for `python-lsp-server` or your editor

This is better than the approach above, but won't help with plugins that need to run in your project's environment and don't have configuration variables to facilitate this.

### Option 3 (ok): In the project environment

This is the first option that should work fine for all plugins.

A potential drawbacks is that it is sometimes recommended to only install packages in your project's virtualenv that are specified by your project's `pyproject.toml` (or equivalent configs). Many Python dev tools come with functionality to ensure this (e.g. `poetry install --sync`, `uv sync` unless run with `--inexact`, ...). To use these together with this option, you have to add `python-lsp-server` and any plugins you want to use to your `pyproject.toml`'s dev dependencies section. This is OK but may be annoying for users who don't want to use LSP features or have their own setup.

### Option 4 (best? but complicated): In a venv layered "on top" of the project environment

It is possible to "overlay" a virtualenv on top of another [using `.pth` hacks](https://stackoverflow.com/a/72972198) or by just manually setting `PYTHONPATH` and `PATH` to contain both venvs.

So you could have all your project's normal and dev dependencies installed in one venv, but then have an "overlay" venv in which you install `python-lsp-server` and the plugins you want to use, ideally at versions compatible with your project's main dependencies.

One tool that can do all of this automatically is [uv](https://github.com/astral-sh/uv): Running

```bash
uv run --with python-lsp-server,pylsp-mypy pylsp
```

in your project directory creates an ephemeral venv (typically in a location under `~/.cache`) that links to your project's venv but also has `python-lsp-server` and `pylsp-mypy` installed, and then runs `pylsp` inside this virtualenv.

The obvious drawback of this solution is that it is rather complicated and requires special tooling like `uv` or a handwritten script.


## Question 2: How to make `pylsp` & plugins run in / use the correct env?

### Option 1 (ok but limited & possibly complicated): Per-plugin configuration of executable / env

As we saw in the initial sections, some plugins come with options to configure the executable to run or environment to work in. As long as you limit yourself to these plugins, you can use these configuration options.

How to use different values for these options in different projects is editor-dependent and may involve some scripting.

### Option 2 (ok): Run editor from inside target venv

If you have an editor that is easy to launch inside a virtualenv (e.g. Vim or Emacs which are typically launched from within a shell) and will use that virtualenv's Python interpreter to run tools like `pylsp`, then you can just do that.

A possible drawback is that this will apply not just to `pylsp` but any other similar Python tooling the editor may use (e.g. Vim plugins written in Python), which may not be desired.

### Option 3 (better): Configure editor to launch `pylsp` in target venv

A better approach may be to configure your editor to launch only `pylsp` in the desired venv.

#### Example: NeoVim

For instance, if you use NeoVim's `vim.lsp` functions to set up the LSP configuration yourself, whether with your own config or a default one provided by [`nvim-lspconfig`](https://github.com/neovim/nvim-lspconfig), you can set/override the command it uses to launch `pylsp` like so:

```vim
lua << EOF
  vim.lsp.config('pylsp', {
    -- Using the approach from Question 1, Option 4 to launch in an "overlay" venv
    -- on top of the project's venv, if any (NeoVim takes care of sharing LSP servers
    -- invocations between files in the same project):
    cmd = { 'uv', 'run', '--with', 'python-lsp-server,pylsp-mypy', 'pylsp' },
  }
EOF
```

See [python-lsp-config#68 (comment)][issue-68-comment] for an example that doesn't use `uv` but tries to determine the project venv manually (e.g. for use with Question 1, Option 3).

[issue-68-comment]: https://github.com/python-lsp/python-lsp-server/pull/68#issuecomment-894650876
