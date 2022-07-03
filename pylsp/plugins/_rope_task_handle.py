from __future__ import annotations

import logging
from typing import List, Optional, Sequence
from rope.base.taskhandle import BaseJobSet, BaseTaskHandle

from pylsp.workspace import Workspace


log = logging.getLogger(__name__)


class PylspJobSet(BaseJobSet):
    name: str
    count: int
    done: int = 0
    job_name: str = ""
    handle: PylspTaskHandle
    token: str

    def __init__(self, handle: PylspTaskHandle, token: str, count: Optional[int]):
        self.token = token
        self.handle = handle
        self.count = 0 if count is None else count

    def started_job(self, name: Optional[str]) -> None:
        if name:
            self.job_name = name

    def finished_job(self) -> None:
        self.done += 1
        log.warn(f"{self.done}/{self.count}")
        if self.get_percent_done() is not None and self.get_percent_done() >= 100:
            self._workspace.progress_end(self.token, self.name)
        self._workspace.progress_report(self.token, None, self.get_percent_done())

    def check_status(self) -> None:
        pass

    def get_percent_done(self) -> Optional[float]:
        if self.count == 0:
            return 0
        return (self.done / self.count) * 100

    def increment(self) -> None:
        """
        Increment the number of tasks to complete.
        This is used if the number is not known ahead of time.
        """
        self.count += 1
        self._workspace.progress_report(self.token, self.name, self.get_percent_done())

    @property
    def _workspace(self) -> Workspace:
        return self.handle.workspace


class PylspTaskHandle(BaseTaskHandle):
    name: str
    observers: List
    job_sets: List[PylspJobSet]
    stopped: bool
    workspace: Workspace

    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self.job_sets = []
        self.observers = []

    def create_jobset(self, name="JobSet", count: Optional[int] = None):
        token = self.workspace.progress_begin(name, name, 0)
        result = PylspJobSet(self, token, count)
        self.job_sets.append(result)
        self._inform_observers()
        return result

    def stop(self) -> None:
        pass

    def current_jobset(self) -> Optional[BaseJobSet]:
        pass

    def add_observer(self) -> None:
        pass

    def is_stopped(self) -> bool:
        pass

    def get_jobsets(self) -> Sequence[BaseJobSet]:
        pass

    def _inform_observers(self) -> None:
        for observer in self.observers:
            observer()
