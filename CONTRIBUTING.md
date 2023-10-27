# Setup the environment

1. Clone the repo: `git clone git@github.com:python-lsp/python-lsp-server.git`
2. Create the virtual environment: `python3 -m venv .venv`
3. Activate: `source .venv/bin/activate`
4. Install an editable installation: `pip3 install -e .`
    - This will ensure you'll see your edits immediately without reinstalling the project

## Configure your editor

In Sublime Text 4, open LSP-pylsp settings and change the path to the `pylsp` command:

```json
{
    "command": ["/home/user/projects/python-lsp-server/run", "-vvv", "--log-file", "pylsp.log"]
}
```

Option `-v` increases verbosity and `--log-file` will write all log messages
into a file, which can be used for debugging.

Running command `LSP: Troubleshoot server` you should now see the configured command,
if not, then the configuration doesn't work as expected.

To enabled plugins like `ruff`, you also need to point your editor to the correct
`PYTHONPATH`:

```json
{
    "command": ["/home/user/projects/python-lsp-server/run", "-vvv", "--log-file", "pylsp.log"],
    "env": {
        "PYTHONPATH": "/home/user/projects/python-lsp-server/.venv/lib/python3.11/site-packages",
    },
}
```

## Trying out if it works

Go to file `pylsp/python_lsp.py`, function `start_io_lang_server`,
and on the first line of the function, add some logging:

```py
log.info("It works!")
```

Save the file, restart the LSP server and you should see the log line:

```
2023-10-12 16:46:38,320 CEST - INFO - pylsp._utils - It works!
```

Now the project is setup in a way you can quickly iterate change you want to add.

# Running tests

1. Install runtime dependencies: `pip3 install .[all]`
2. Install test dependencies: `pip3 install .[test]`
3. Run `pytest`: `pytest -v`

## Useful pytest options

- To run a specific test file, use `pytest test/test_utils.py`
- To run a specific test function within a test file,
  use `pytest test/test_utils.py::test_debounce`
- To run tests matching a certain expression, use `pytest -k format`
- To increase verbosity of pytest, use `pytest -v` or `pytest -vv`
- To enter a debugger on failed tests, use `pytest --pdb`
