# Python Language Server Configuration
This server can be configured using `workspace/didChangeConfiguration` method. Each configuration option is described below:

| **Configuration Key** | **Type** | **Description** | **Default** 
|----|----|----|----|
| `pyls.configurationSources` | `array`  of unique `string` items | List of configuration sources to use. | `["pycodestyle"]` |
| `pyls.plugins.flake8.config` | `string` | Path to the config file that will be the authoritative config source. | `null` |
| `pyls.plugins.flake8.enabled` | `boolean` | Enable or disable the plugin. | `false` |
| `pyls.plugins.flake8.exclude` | `array`  | List of files or directories to exclude. | `null` |
| `pyls.plugins.flake8.executable` | `string` | Path to the flake8 executable. | `"flake8"` |
| `pyls.plugins.flake8.filename` | `string` | Only check for filenames matching the patterns in this list. | `null` |
| `pyls.plugins.flake8.hangClosing` | `boolean` | Hang closing bracket instead of matching indentation of opening bracket's line. | `null` |
| `pyls.plugins.flake8.ignore` | `array`  | List of errors and warnings to ignore (or skip). | `null` |
| `pyls.plugins.flake8.maxLineLength` | `integer` | Maximum allowed line length for the entirety of this run. | `null` |
| `pyls.plugins.flake8.perFileIgnores` | `array`  | A pairing of filenames and violation codes that defines which violations to ignore in a particular file, for example: `["file_path.py:W305,W304"]`). | `null` |
| `pyls.plugins.flake8.select` | `array`  | List of errors and warnings to enable. | `null` |
| `pyls.plugins.jedi.extra_paths` | `array`  | Define extra paths for jedi.Script. | `[]` |
| `pyls.plugins.jedi.env_vars` | `object` | Define environment variables for jedi.Script and Jedi.names. | `null` |
| `pyls.plugins.jedi.environment` | `string` | Define environment for jedi.Script and Jedi.names. | `null` |
| `pyls.plugins.jedi_completion.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.plugins.jedi_completion.include_params` | `boolean` | Auto-completes methods and classes with tabstops for each parameter. | `true` |
| `pyls.plugins.jedi_completion.include_class_objects` | `boolean` | Adds class objects as a separate completion item. | `true` |
| `pyls.plugins.jedi_completion.fuzzy` | `boolean` | Enable fuzzy when requesting autocomplete. | `false` |
| `pyls.plugins.jedi_completion.eager` | `boolean` | Resolve documentation and detail eagerly. | `false` |
| `pyls.plugins.jedi_completion.resolve_at_most_labels` | `number`  | How many labels (at most) should be resolved? | `25` |
| `pyls.plugins.jedi_completion.cache_labels_for` | `array`  of  `string` items | Modules for which the labels should be cached. | `["pandas", "numpy", "tensorflow", "matplotlib"]` |
| `pyls.plugins.jedi_definition.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.plugins.jedi_definition.follow_imports` | `boolean` | The goto call will follow imports. | `true` |
| `pyls.plugins.jedi_definition.follow_builtin_imports` | `boolean` | If follow_imports is True will decide if it follow builtin imports. | `true` |
| `pyls.plugins.jedi_hover.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.plugins.jedi_references.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.plugins.jedi_signature_help.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.plugins.jedi_symbols.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.plugins.jedi_symbols.all_scopes` | `boolean` | If True lists the names of all scopes instead of only the module namespace. | `true` |
| `pyls.plugins.jedi_symbols.include_import_symbols` | `boolean` | If True includes symbols imported from other libraries. | `true` |
| `pyls.plugins.mccabe.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.plugins.mccabe.threshold` | `number`  | The minimum threshold that triggers warnings about cyclomatic complexity. | `15` |
| `pyls.plugins.preload.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.plugins.preload.modules` | `array`  of unique `string` items | List of modules to import on startup | `null` |
| `pyls.plugins.pycodestyle.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.plugins.pycodestyle.exclude` | `array`  of unique `string` items | Exclude files or directories which match these patterns. | `null` |
| `pyls.plugins.pycodestyle.filename` | `array`  of unique `string` items | When parsing directories, only check filenames matching these patterns. | `null` |
| `pyls.plugins.pycodestyle.select` | `array`  of unique `string` items | Select errors and warnings | `null` |
| `pyls.plugins.pycodestyle.ignore` | `array`  of unique `string` items | Ignore errors and warnings | `null` |
| `pyls.plugins.pycodestyle.hangClosing` | `boolean` | Hang closing bracket instead of matching indentation of opening bracket's line. | `null` |
| `pyls.plugins.pycodestyle.maxLineLength` | `number`  | Set maximum allowed line length. | `null` |
| `pyls.plugins.pydocstyle.enabled` | `boolean` | Enable or disable the plugin. | `false` |
| `pyls.plugins.pydocstyle.convention` | `string` | Choose the basic list of checked errors by specifying an existing convention. | `null` |
| `pyls.plugins.pydocstyle.addIgnore` | `array`  of unique `string` items | Ignore errors and warnings in addition to the specified convention. | `null` |
| `pyls.plugins.pydocstyle.addSelect` | `array`  of unique `string` items | Select errors and warnings in addition to the specified convention. | `null` |
| `pyls.plugins.pydocstyle.ignore` | `array`  of unique `string` items | Ignore errors and warnings | `null` |
| `pyls.plugins.pydocstyle.select` | `array`  of unique `string` items | Select errors and warnings | `null` |
| `pyls.plugins.pydocstyle.match` | `string` | Check only files that exactly match the given regular expression; default is to match files that don't start with 'test_' but end with '.py'. | `"(?!test_).*\\.py"` |
| `pyls.plugins.pydocstyle.matchDir` | `string` | Search only dirs that exactly match the given regular expression; default is to match dirs which do not begin with a dot. | `"[^\\.].*"` |
| `pyls.plugins.pyflakes.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.plugins.pylint.enabled` | `boolean` | Enable or disable the plugin. | `false` |
| `pyls.plugins.pylint.args` | `array`  of non-unique `string` items | Arguments to pass to pylint. | `null` |
| `pyls.plugins.pylint.executable` | `string` | Executable to run pylint with. Enabling this will run pylint on unsaved files via stdin. Can slow down workflow. Only works with python3. | `null` |
| `pyls.plugins.rope_completion.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.plugins.rope_completion.eager` | `boolean` | Resolve documentation and detail eagerly. | `false` |
| `pyls.plugins.yapf.enabled` | `boolean` | Enable or disable the plugin. | `true` |
| `pyls.rope.extensionModules` | `string` | Builtin and c-extension modules that are allowed to be imported and inspected by rope. | `null` |
| `pyls.rope.ropeFolder` | `array`  of unique `string` items | The name of the folder in which rope stores project configurations and data.  Pass `null` for not using such a folder at all. | `null` |

This documentation was generated from `pylsp/config/schema.json`. Please do not edit this file directly.
