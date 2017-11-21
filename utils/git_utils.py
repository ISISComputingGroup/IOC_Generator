"""
Utilities for interacting with Git. This is largely done via the command line because it's simpler and easier
to maintain than the PythonGit API.
"""
from git import Repo, GitCommandError, InvalidGitRepositoryError
import logging


class RepoWrapper(object):
    """
    A wrapper around a git repository
    """
    def __init__(self, path):
        """
        :param path: The path to the git repository
        """
        try:
            self._repo = Repo(path)
        except InvalidGitRepositoryError:
            self._repo = Repo.init(path)
        except Exception:
            raise RuntimeError("Unable to attach to git repository at path {}".format(path))

    def prepare_new_branch(self, branch, epics=False):
        """
        :param branch: Name of the new branch
        :param epics: Is this the main epics repo?
        """
        logging.info("Preparing new branch, {}, for repo {}".format(branch, self._repo.working_tree_dir))
        try:
            self._repo.git.reset("HEAD", hard=True)
            try:
                self._repo.git.clean(f=True, d=True, x=True)
            except GitCommandError:  # Fall back on no -x. Some repos (e.g. GUI) have paths that are too long
                self._repo.git.clean(f=True, d=True)
            self._repo.git.checkout("master", force=True)
            self._repo.git.pull()
            branch_is_new = branch not in self._repo.branches
            self._repo.git.checkout(branch, b=branch_is_new)
            self._repo.git.checkout(branch)
            # self._repo.git.push("origin", branch, set_upstream=True)
            logging.info("Branch {} ready".format(branch))
        except GitCommandError as e:
            raise RuntimeError("Error whilst executing preparing git branch, {}".format(e))

    def push_all_changes(self, message, allow_master=False):
        """
        Adds all modified and un-tracked files to git, commits with the message provided and pushes to git

        :param message: The commit message to include with the push
        :param allow_master: Can commit changes to the master branch
        """
        logging.info("Pushing all changes to current branch, {}, for repo {}".format(
            self._repo.active_branch, self._repo.working_tree_dir))
        if not allow_master and self._repo.active_branch is "master":
            raise RuntimeError("Attempting to commit to master branch")

        try:
            self._repo.git.add(A=True)
            n_files = len(self._repo.index.diff("HEAD"))
            if n_files > 0:
                self._repo.git.commit(m=message)
                # self._repo.git.push()
                logging.info("{} files pushed to {}: {}".format(n_files, self._repo.active_branch, message))
            else:
                logging.warn("Commit aborted. No files changed")
        except GitCommandError as e:
            raise RuntimeError("Error whilst pushing changes to git, {}".format(e))
