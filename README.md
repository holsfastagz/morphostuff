# MorphoStuff

![coverage](https://img.shields.io/badge/coverage-70%25-yellowgreen)
![version](https://img.shields.io/badge/version-0.0.1-blue)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

A small python package to aid morphometric analysis. Automates allometric
correction and principal component analysis.

**Table of Contents**
- [Installation](#installation)
- [Execution / Usage](#execution--usage)
- [Technologies](#technologies)
- [Contributing](#contributing)
- [Author](#author)
- [Change log](#change-log)
- [License](#license)

## Installation

MorphoStuff is not in PyPI yet, but I plan to add it in soon. In the meantime,
it can be downloaded from GitHub using pip.

```sh
python -m pip install MorphoStuff@git+https://github.com/holsfastagz/MorphoStuff.git
```

## Execution / Usage

### Importing

You can import MorphoStuff into a Python script like so:

```python
import MorphoStuff
```

### allom Function

Ensure your data are in the proper format. The first column (index 0)
should consist of the species name or other identifying information. The
second column (index 1) should consist of a standard body length measurement
such as SVL. The following columns (indices 2:) should consist of other
measurements. 

The allom function only requires a data frame as input. A Polars data frame
is recommended, but it can also take a Pandas data frame as input. Example:

```python
morph_data = pl.read_csv('morph_data.csv')

allom_data = allom(morph_data)
```

This function outputs a table of allometrically corrected features.

Use `help(allom)` for more information.

### morph_pca Function

The input of this function should be a data frame of allometrically corrected
characters (i.e., the output of `allom`). It should follow the same structure
as the `allom` inputs.

```python
morpho_data = morpho_stuff(allom_data)
```

This function outputs a table containing allometric size corrections, a table
containing PCA results, and a PCA biplot.

Use `help(morpho_data)` for more information.

### significant_features Function

This function will determine how many principal components account for at least
90% of explained variance and which characters weigh heavily on each PC
according to the following formula:

$$
\sqrt{\frac{1} {\mathrm{no. \ of\ characters}}}
$$

The input of this function should be the data frame generated as output of
`morph_pca`. 

```
significant_features(morpho_data)
```

This function outputs a scree plot, barplots for each PC, a table of loadings
of the significant PCS, and a table of significance of each character by PC.
These outputs are all written to the disk.

Use `help(significant_features)` for more information.

## Technologies

MorphoStuff uses the following technologies and tools:

- [Python](https://www.python.org/): ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
- [Polars](https://pola.rs/): <img src="https://github.com/pola-rs/polars-static/blob/master/logos/polars_logo_blue_text.svg" width="50" />
- [scikit-learn](https://scikit-learn.org/stable/): ![scikit-learn](https://github.com/scikit-learn/scikit-learn/blob/main/doc/logos/1280px-scikit-learn-logo.png)
- [seaborn](https://seaborn.pydata.org/): ![seaborn](https://seaborn.pydata.org/_images/logo-wide-lightbg.svg)

## Contributing

To contribute to the development of MorphoStuff, follow the steps below:

1. Fork MorphoStuff from <https://github.com/holsfastagz/MorphoStuff/fork>
2. Create your feature branch (`git checkout -b feature-new`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add some new feature'`)
5. Push to the branch (`git push origin feature-new`)
6. Create a new pull request

## Author

Holsen B. Moore - [@h0ls.bsky.social](https://bsky.app/profile/h0ls.bsky.social) - holsenmoore@utexas.edu

## Change Log 

- 0.0.1
    - First working version.

## License

MorphoStuff is distributed under the MIT license. See [`LICENSE`](LICENSE) for more details.