![](https://github.com/what-want/github-crawler/workflows/crawling/badge.svg)
# GitHub Crawler
특정 키워드에 대한 GitHub Repository 검색 결과 및 Repository 상세 정보를 수집


## Prequisite (Development/Execution Environment)

- Python 2.7.x (+ requests)
```bash
$ sudo apt install python-requests
```


## Execute
`키워드 검색`과 `Repo 정보 수집`을 나누어서 실행


### Step-0 : Token 값 등록
  - Token 값을 등록하지 않으면 API 호출에 더 많은 제약이 발생

```bash
$ export WW_TOKEN='token'
```


### Step-1 : 키워드 검색
  - star 갯수가 1개 이상인 Repository에 대해서만 수집

```bash
$ ./1searchKeyword.py "keyword"
```

  - 검색 결과는 아래 경로에 저장된다.
```
./data/(keyword).tar.gz
```

### Step-2 : Repository 정보 검색
  - 앞에서 저장한 결과 데이터를 가지고 Repository 정보를 수집

```bash
$ ./2getRepoInfo.py "./data/(keyword).tar.gz"
```

  - 수집된 결과물은 아래 경로에 저장된다.
```
./data/(keyword).csv
```

  - 중간에 끊긴 경우, 다시 실행하면 이어서 진행됩니다.


## FAQ

  1. 왜 나누어서 실행하나요?
      - Repo. 정보 수집하는 시간이 오래 걸려서, 그동안 변경되는 Repository 정보들도 많이 발생합니다.
      - 그래서 검색 결과를 먼저 뽑아놓고, 정해진 검색 결과를 바탕으로 Repository 정보를 수집하도록 했습니다.

  1. github.com에서 검색한 결과와 갯수가 틀린데요?
      - 여기에서는 star 갯수가 1개 이상 되는 것들만 검색되도록 했습니다.
      - 검색에 많은 시간이 걸리기도 하기에 모든 결과를 수집하는 것은 의미가 별로 없다고 판단했습니다.
