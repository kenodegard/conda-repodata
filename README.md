# conda-repodata

Ever wanted to modify the `repodata.json` (or even just look at it) before downloading the packages? This is the tool for you!

Conda-repodata adds the ability to apply transformations to any `repodata.json` file before downloading the packages. This is useful for things like:
    - debugging `repodata.json` issues
    - testing hotfix patches to `repodata.json`
    - any other `repodata.json` manipulation you can think of!

## Installation

> **Warning**
> This relies on an unreleased version of conda.

```bash
conda install kenodegard::conda-repodata
```

## Usage

### View `repodata.json`

```bash
conda repodata --channel pkgs/main --subdir linux-64
```

### Write `repodata.json` to a file

```bash
conda repodata --channel pkgs/main --subdir linux-64 --output path/to/repodata.json
```

### Transform `repodata.json`

To apply a transformation to the `repodata.json` file, set the `CONDA_TRANSFORMATIONS` environment variable to a Python script containing a function called `transformation` that accepts the parsed repodata object and returns the patched object.

```python
# transformation.py
def transformation(repodata):
    # do something to repodata
    return repodata
```

```bash
CONDA_TRANSFORMATIONS=tranfromation.py conda repodata ...
```

See [example_transformations](./example_transformations) for additional inspiration.
