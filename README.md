# cartoon-autocaption

Automatic captions for New Yorker cartoons. Work in progress.

## Installation

```bash
pipenv shell
pipenv install
```

## Downloading training data

Cartoons, competing captions and winners are provided by Jain, L., Jamieson, K., Mankoff, R., Nowak, R., and Sievert, S. from NextML. You can access the homepage of this dataset [here](https://nextml.github.io/caption-contest-data2/).

```bash
pipenv run python download_data.py --start 660 --end 790
```
