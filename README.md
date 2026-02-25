# napari-microscopy-metrics

[![License CeCILL-B](https://img.shields.io/pypi/l/napari-microscopy-metrics.svg?color=green)](https://github.com/MontpellierRessourcesImagerie/napari-microscopy-metrics/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-microscopy-metrics.svg?color=green)](https://pypi.org/project/napari-microscopy-metrics)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-microscopy-metrics.svg?color=green)](https://python.org)
[![tests](https://github.com/MontpellierRessourcesImagerie/napari-microscopy-metrics/workflows/tests/badge.svg)](https://github.com/MontpellierRessourcesImagerie/napari-microscopy-metrics/actions)
[![codecov](https://codecov.io/gh/MontpellierRessourcesImagerie/napari-microscopy-metrics/branch/main/graph/badge.svg)](https://codecov.io/gh/MontpellierRessourcesImagerie/napari-microscopy-metrics)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-microscopy-metrics)](https://napari-hub.org/plugins/napari-microscopy-metrics)
[![npe2](https://img.shields.io/badge/plugin-npe2-blue?link=https://napari.org/stable/plugins/index.html)](https://napari.org/stable/plugins/index.html)
[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-purple.json)](https://github.com/copier-org/copier)

A plugin using the microscopy metrics module for doing quality control with PSFs in Napari.

----------------------------------

This [napari] plugin was generated with [copier] using the [napari-plugin-template] (None).

<!--
Don't miss the full getting started guide to set up your new package:
https://github.com/napari/napari-plugin-template#getting-started

and review the napari docs for plugin developers:
https://napari.org/stable/plugins/index.html
-->

## Installation

Python 3.12 is required to use the plugin in best conditions

You can install `napari-microscopy-metrics` via [pip]:

```
pip install napari-microscopy-metrics
```

If napari is not already installed, you can install `napari-microscopy-metrics` with napari and Qt via:

```
pip install "napari-microscopy-metrics[all]"
```


To install latest development version :

```
pip install git+https://github.com/MontpellierRessourcesImagerie/napari-microscopy-metrics.git
```

You will also need to install `microscopy-metrics` and `auto-options` from MRI github :
```
pip install --upgrade git+https://github.com/MontpellierRessourcesImagerie/microscopy-metrics.git

pip install --upgrade git+https://github.com/MontpellierRessourcesImagerie/auto-options-python.git
```



## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [CeCILL-B] license,
"napari-microscopy-metrics" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[copier]: https://copier.readthedocs.io/en/stable/
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[napari-plugin-template]: https://github.com/napari/napari-plugin-template

[file an issue]: https://github.com/MontpellierRessourcesImagerie/napari-microscopy-metrics/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
