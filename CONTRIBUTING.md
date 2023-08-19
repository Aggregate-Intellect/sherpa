# Contributing 
We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the book or the accompanying software
- Submitting a fix
- Proposing new features
- Becoming a maintainer


## Report bugs and suggest improvements using Github's [issues](https://github.com/Aggregate-Intellect/sherpa/issues)
We use GitHub issues to track public bugs and feature requests. Report a bug or suggest an improvement by [opening a new issue](); it's that easy!

That said, we avoid keeping a massive backlog of "someday, maybe" ideas. We periodically review the issues list so that all issues are things we have a reasonably high likelihood of acting on.


## Write bug reports with detail, background, and sample code
**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can. 
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

Here is [an example of a great bug report from Craig Hockenberry](http://www.openradar.me/11905408).

People *love* thorough bug reports. I'm not even kidding.


## Contribute documentation and code via GitHub
We use GitHub to host code and documentation, track issues and feature requests, and accept pull requests. Here's how it works:

### The origin/main branch on GitHub is "The Truth"
https://github.com/Aggregate-Intellect/sherpa is the primary repository. In terms of git remotes we refer to this repository as **`origin`**.

The [`origin/main` branch](https://github.com/Aggregate-Intellect/sherpa/tree/main) is the "one source of truth". This is what we run in production. Every other branch, including remote branches and forks, derives from
origin/main.

### We try to keep `origin/main` deployable at all times
For this reason we implement software changes in separate branches, and merge those
branches into main only when we are finished testing and ready to deploy.

### We use [Github Flow](https://docs.github.com/en/get-started/quickstart/github-flow), so all changes happen through pull requests
Pull requests are the best way to propose changes to the codebase (we use [Github Flow](https://docs.github.com/en/get-started/quickstart/github-flow)). We actively welcome your pull requests.

Here are the Github Flow steps. Note you can complete all these steps through the GitHub web interface, the command line and GitHub CLI, the command line and `git`, or [GitHub Desktop](https://docs.github.com/en/desktop). Here we explain how to do it with a combination of the GitHub web interface and command line.

1. Fork the repository to your own GitHub account. *(GitHub web: click the "Fork" button on the top right of the repository page.)*
2. Clone the forked repository to your local machine. *(Command line: `git clone https://github.com/your-username/repo-name.git`)*
3. Create a new branch from `main` for your changes. *(Command line: `git checkout -b your-branch-name`)* Use a short, descriptive branch name so that your collaborators can see ongoing work at a glance. For example, `increase-test-timeout` or `add-code-of-conduct`.
4. Make the desired changes.
5. If you've added code...
    - add tests if the code should be tested
    - ensure the test suite passes
    - make sure your code lints
6. Commit your changes with a descriptive commit message. *(Command line: `git commit -m "your commit message"`)* See below for our commit message conventions.
7. Push your changes to your forked repository. *(Command line: `git push origin your-branch-name`)*
8. Go to the main repository and submit a pull request with a description of your changes.

Once your pull request is submitted, a maintainer on our team will review it and either merge or comment for further changes.

NOTE: If the change you are considering is fairly major, please suggest it as an issue first so that we can coordinate before you put in the effort.

### Follow these rules of thumb for your contributions

#### 1. Use a consistent coding style
* Follow [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/) 
* You can try running `make lint` for style unification

#### 2. Group distinct changes into distinct commits
A.k.a. separation of concerns. If you’re working on a larger feature or fixing multiple unrelated issues, break your changes into smaller, logical commits. Each commit should represent a self-contained unit of work that makes sense on its own. This helps us review and maintain code, and makes it easier to track down bugs. 

For example, let's say you're adding a new package requirement, fixing an unrelated typo, and then adding a module and a corresponding unit test. This should probably be 3 distinct commits, each one with a single purpose. 

#### 3. Write nice git commit messages
We try to follow these 7 commonly accepted rules on how to write a great git commit message:

1. Limit the subject line to 50 characters.
2. Capitalize only the first letter in the subject line.
3. Don't end the subject line with punctuation, e.g. a period.
4. Put a blank line between the subject line and the body.
5. Wrap the body at 72 characters.
6. Use the imperative mood. E.g. "Eat carrots at noon", rather than "Changes carrot-eating time to noon" 
7. Describe what was done and why, but not how.

For rationale and examples, see [How to Write a Git Commit Message](http://chris.beams.io/posts/git-commit).
Please review this prior to pushing awesome code changes. 

#### 4. Reference GitHub Issues
If your commit addresses a GitHub issue, make sure to reference it in the commit message, e.g. "Fix #28" in the subject line, or "Fixes #45" in the body. GitHub automatically links issue references.

#### 5. Keep your changes in sync with the `main` branch
When you create a branch to contain your changes, you start by forking the HEAD of the `main` branch. This way you're building on what everyone else has already created. Subsequently, while you're working, `main` evolves over time with new commits that maintainers merge in from other contributors. When this happens, and especially if your branch lives for many days or weeks, we prefer to `git rebase` your branch on the latest commits within `main` -- the commits merged after your created your branch -- so that we have a linear (chronological) commit history. A linear history makes the repository easier to understand as it evolves over time. Rebasing isn't a hard and fast rule, but for smaller commits it generally improves readability.

If you have not yet created a Pull Request, you can rebase on your own by merging the latest commits from `origin/main` into your local repository's `main` branch and then using `git rebase main`. Rebase will "replay" your commits atop the HEAD of the `main` branch. Git rebase can be a bit tricky to use, so if you aren't familiar with it then start with a good primer like the [BitBucket rebase tutorial](https://www.atlassian.com/git/tutorials/rewriting-history/git-rebase).

If you have already submitted a Pull Request and you don't have permission to write to https://github.com/Aggregate-Intellect/sherpa, one of the maintainers can rebase/update the PR on your behalf, e.g. via [GitHub's Update Branch feature](https://github.blog/changelog/2022-02-03-more-ways-to-keep-your-pull-request-branch-up-to-date/
) or by running `git rebase main` on their own clone of the repo.  


## License
By contributing, you agree that your contributions will be licensed under the repository's License.

When you submit code (software) changes, ... #TODO

When you submit book (non-software) changes, ... #TODO

## References
This document was adapted from this [awesome gist by Brian A. Danielak](https://gist.github.com/briandk/3d2e8b3ec8daf5a27a62).

See also:
- https://docs.github.com/en/get-started/quickstart/github-flow
