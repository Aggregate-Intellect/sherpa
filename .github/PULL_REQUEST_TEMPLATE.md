# Your checklist for this pull request
Thank you for submitting a pull request! To speed up the review process, please follow this checklist:

- [ ] My Pull Request is small and focused on one topic so it can be reviewed easily 
- [ ] My code follows the style guidelines of this project (`make format`)
- [ ] Commit messages are detailed
- [ ] I have performed a self-review of my code
- [ ] I commented hard-to-understand parts of my code
- [ ] I updated the documentation (docstrings, `/docs`)
- [ ] My changes generate no new warnings (or explain any new warnings and why they're ok)
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] All tests pass when I run `pytest tests` (offline mode)

Additional steps for code with networking dependencies:

- [ ] I followed the [offline and online testing guidelines](https://sherpa-ai.readthedocs.io/en/latest/How_To/Test/test.html#offline-and-online-testing)
- [ ] All tests pass when I run `pytest tests --external_api` (online mode, making network calls)

# Description
Describe your pull request here.

What does this PR implement or fix? Explain.

If this PR resolves any currently open issues then mention them like this: `Closes #xxx`.
Github will close such issues automatically when your PR is merged into `main`.

Any relevant logs, error output, etc?

Any other comments? For example, will other contributors need to install new libraries via `poetry install` after picking up these changes?

💔Thank you!