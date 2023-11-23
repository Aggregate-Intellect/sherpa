======================
Sherpa Test Guidelines
======================


References: https://docs.python-guide.org/writing/tests/

Best Practices and Guidelines
=============================

**Single Responsibility Principle (SRP):**

Each test should test a single logical concept or behavior. This is a
reflection of the Single Responsibility Principle (SRP) applied to
testing. When a test only checks one thing, it's easier to identify
issues and fix bugs when the test fails.

**Clear and Descriptive Naming:**

Use clear and descriptive naming for your test functions to indicate
what concept or behavior the test is verifying. This makes your test
suite easier to understand and maintain.

**Keep It Short and Sweet (KISS):**

Keep your tests short, simple, and focused. A test should be easy to
understand at a glance. This often translates to testing a single thing
per test.

**Avoid Test Dependencies:**

Tests should be independent of each other. Don’t share state between
tests.

**Use Setup and Teardown Wisely:**

Use setup and teardown methods to manage common test setup and cleanup
tasks. This will help focus each test on a single concept by removing
unrelated setup and cleanup code.

**Assert on a Single Outcome:**

It's generally a good practice to have a single assertion per test.
However, in some cases, it might make sense to have multiple assertions
if they are verifying different aspects of the same logical concept.
This is especially true for tests with complicated or lengthy setup.

**Make Each Test Useful:**

Every test should provide value and help verify that your code is
working correctly. Avoid writing tests that don't provide meaningful
feedback.

**Ensure Deterministic Behavior:**

Tests should be deterministic, always producing the same result when run
with the same conditions. Avoid non-deterministic factors like
randomness or time dependence in your tests.

**Maintainability and Readability:**

Strive for maintainability and readability in your tests, making it easy
for others (and future-you) to understand what is being tested and why.

**Document Complex Tests Only:**

Write your test code in a clear and descriptive manner, so that the code
is self-documenting. If a test is complex or non-intuitive, it's a good
practice to include comments or docstrings explaining the purpose and
functionality of the test. However, a complex or non-intuitive test is
generally a code smell… try first to simplify the test code.

What to Test
============

**Core Functionality:**

Always test the core functionality of your application. These are the
parts that would cause the most disruption if they failed.

**Complex Logic:**

Any part of your code with complex logic should be tested to ensure it
functions correctly under all conditions.

**Boundary Conditions:**

Test the boundary conditions of your code, such as edge cases, input
limits, and unusual or unexpected conditions.

**Bug Fixes:**

Whenever you fix a bug, write a test to ensure the bug stays fixed.

**Critical Path:**

The critical path through your code that will be executed frequently
should be thoroughly tested to ensure reliability and performance.

**Error Handling:**

Test how your code handles errors. This includes testing exception
handling and error reporting.

**Database Access:**

Test the parts of your code that interact with databases to ensure
correct data handling, especially if complex queries or transactions are
involved.

**Security Features:**

Security-related code should always be tested to ensure that security
requirements are met.

**Integration Points:**

Test the points where your code integrates with other systems,
libraries, or frameworks


What Not to Test
================

**Third-party Code and External Systems:**

Avoid testing code from third-party libraries or frameworks that you
trust. It's their responsibility to test their code. For external
systems and services, you can use mocks.

**Simple Wrapper Functions:**

Simple wrapper functions that only call other functions with no
additional logic may not need individual tests.

**Very Simple Code:**

Extremely simple code that has a trivial implementation and is easy to
visually inspect may not need extensive testing.

**Code that is about to be Deprecated**

**Constant Definitions:**

Constants or configuration settings generally do not need to be tested

Naming Conventions, Tools, and Test Infrastructure
==================================================

Folder Structure
----------------

**app/**: Contains application interface

**src/sherpa_ai/**: Contains the main application code

**src/tests/**: Houses all test files.

**src/tests/fixtures/**: Contains fixtures for testing.

**src/tests/data**: Data files and cached responses from 3rd party APIs for test mocks.

**src/tests/unit/**: Unit tests for individual functions or components.

**src/tests/integration/**: Integration tests for interactions between
different components.

**src/tests/e2e/**: End-to-end tests for testing the application as a whole.

Naming Conventions
------------------

**The naming convention for a testing file is to add the prefix**
**test\_** to the original file name

      -  eg . If the file name is utility then the test file name is
            test_utility

The naming convention for a test function is to add the prefix
test\_ to the original function name

      -  e.g. test_subtractor. If an edge case exists, add a descriptive
            name at the end e.g. test_subtractor_zero.

Tools
-----

**Testing Packages:**
      We use **pytest** for testing

**Mocking**

We use **unittest.mock** for mocking. Mocking allows you to
replace parts of your system under test with mock objects and
make assertions about how they have been used. This can be
useful for testing external systems or services that your code
interacts with.

**Test Coverage**

Measure test coverage with **pytest-cov**. Run tests with coverage
using **pytest --cov=sherpa_ai .** We do not yet have a code coverage target.

Running Tests
-------------

To run test cases lcoally, first switch to the src directory: **cd src**

To run all tests, use the command **pytest tests**.

For a specific test file, run **pytest tests/test_module_name.py**

To run a specific test function, use **pytest -k test_function_name**.

By default, the tests run using locally cached data. See "offline and online testing" below
for more details. 
To run the tests without using the local caches, use **pytest --external_api**.

.. warning:: 
      The `external_api` option will result in calls to 3rd party APIs from the machine runnning tests, 
      which may incur real dollar costs,
      and may be significantly slower than a local (offline) test run.

GitHub Actions Integration
--------------------------

We use GitHub Actions for automated testing. When you create a
pull request, the automated tests will be triggered
automatically. View the workflow configuration in **.github/workflows/tests.yml**.

Maintaining and Updating Tests
------------------------------

Update tests whenever there are changes in dependencies or code.
When updating tests, verify that they still pass and accurately
represent the intended behavior of the code.

Offline and Online Testing
--------------------------

By default, all tests run entirely offline, using locally cached data to mock the results of network calls. 
This has several important benefits:

1. No network calls to 3rd party APIs for services such as LLMs, which can be both slow and costly
2. Tests run offline, enabling offline development
3. Tests are deterministic
4. Tests are fast 

We want to preserve these benefits. Therefore, when you modify or add tests, 
make sure they run offline by default.

Guidelines for testing code that makes network calls:

1. Mark your test `@pytest.mark.external_api` to indicate that it calls code which uses the network. 
2. Define a *mock* as described in "Mocking" to simulate the results of calling 3rd party APIs over the network. See "Test with LLMs" below for guidance on mocking LLMs. 
3. Run your tests both with and without the `external_api` option, to ensure your test works when offline (the default) and when making actual network calls.

When we deploy a release to production we run tests with the `external_api` 
option enabled as an integration test. 



Testing with LLMs
-----------------

As described above, by default, all tests run offline and use mocks where necessary.
However, there are some situations where you need to use real LLM-generated data in your tests. 
To support this, we periodically cache the output of LLM API calls so that we can run the tests
offline later on using previously captured data. 

Here's how it works:

- the `tests.fixtures.llms.get_llm` *fixture* automatically caches LLM calls. If you have a test that needs to call LLMs, get the LLM using the `get_llm` fixture and pass it as an attribute to the module under test. Behind the scenes, `get_llm` will either use cached test data (the default) or append new data from an actual LLM API call to the appropriate cache file (when tests run with `external_api` option).
- To avoid cache conflicts, pass the file name (the `__file__` attribute) of the module and the name of the test function (the `__name__` attribute of the function) to the `get_llm` fixture.

For example, if we have test file name `test.py`:

      .. code:: python

            from tests.fixtures.llms import get_llm
            def test_my_llm(get_llm): # noqa F811
                  llm = get_llm(__file__, test_my_llm.__name__)
                  # use llm to test your code            
            
The name of the resulting cache file will be `tests/data/<test filename>_<test_name>.jsonl`.
In the above example, the cache file will be `test_test_my_llm.jsonl`.

The file will be automatically created if it does not exist.

.. note:: 
      Notice that when tests are run with external APIs using the `--external_api` option, the LLMs interactions
      will be appended in the cache file rather than overwriting it. To create a new cache file, you should
      delete the old cache file first.