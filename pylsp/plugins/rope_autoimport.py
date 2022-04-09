import logging

from rope.contrib.autoimport import AutoImport

from pylsp import hookimpl, lsp
from pylsp.config.config import Config
from pylsp.workspace import Workspace

log = logging.getLogger(__name__)


@hookimpl
def pylsp_settings():
    # Default rope_completion to disabled
    return {"plugins": {"rope_autoimport": {"enabled": True}}}


@hookimpl
def pylsp_completions(config: Config, workspace: Workspace, document, position):
    rope_config = config.settings(document_path=document.path).get("rope", {})
    rope_project = workspace._rope_project_builder(rope_config)
    autoimport = AutoImport(rope_project, memory=False)
    autoimport.close()


@hookimpl
def pylsp_initialize(config: Config, workspace: Workspace):
    rope_config = config.settings().get("rope", {})
    rope_project = workspace._rope_project_builder(rope_config)
    autoimport = AutoImport(rope_project, memory=False)
    autoimport.generate_modules_cache()
    autoimport.close()
