Introduction
------------

This is a ``pytest`` plugin to run ``interrogate`` when invoking **pytest**.

Requirements:
-------------

* `interrogate`_
    - ``pip install interrogate``


Usage:
------

* ``--interrogate`` to have reports with verbosity 0 written to output.
* ``--interrogate-CMD`` for most of `interrogate cli`_ e.g ``--interrogate-verbose=0`` or  ``--interrogate-fail-under=90`` etc. Not all CMD are supported but all options used for interrogate is supported.
* Some extra args: 
    * ``--interrogate-quiet`` for not using interrogate. Taken from `pytest-cov` and made compatible with `quiet` option of interrogate.
    * ``--interrogate-no-color`` for no color output. `color` is on by default.
    * ``--interrogate-tofile`` for writing to file output.
    * ``--interrogate-no-pyproject`` for not using `pyproject.toml` settings. It is used for config by default for `interrogate`
    * ``--interrogate-noreport-on-fail`` for not reporting anything.

.. _interrogate cli: https://interrogate.readthedocs.io/en/latest/#command-line-options
.. _interrogate: https://interrogate.readthedocs.io/en/latest/
