===============
Release Process
===============

.. tip:: 
      This section is for repository maintainers.

Steps:

First make sure everything builds cleanly:

* `make format`
* `make lint`
* `make test` 
* run tests with the `external_api` option enabled

If there are issues in any of these steps, pause and resolve the problems first
before proceeding. Create and merge new Pull Requests as needed.

Next, increase the version number to indicate a change:

* increase version number in `pyproject.toml` (we use Semantic Versioning)
* set `future-release=x.y.z` in `.github_changelog_generator` file
* run `github_changelog_generator` in repo root to update the changelog
* commit changes and push as a Pull Request
