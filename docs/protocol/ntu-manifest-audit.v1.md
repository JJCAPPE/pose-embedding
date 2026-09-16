# NTU RGB+D 120 manifest audit v1

Status: manifest construction is complete for the verified usable aggregate. Final novel evaluation remains sealed until the documented result-blind protocol amendment is advisor-approved for both the usable source count and the aggregate-aware physical-source verification contract.

## Source accounting

- Aggregate: `ntu120_hrnet.pkl`
- Aggregate bytes: 1238461428
- Aggregate SHA-256: `aaf1f928b4629fa9a0850528d43fdd8d920532805d16672bfdda78085b649df8`
- Usable annotations: 113945
- Official missing-skeleton exclusions: 535
- Nominal captures accounted for: 114480
- Locked source-inventory row expectation: 114480
- Protocol amendment required: `true`
- Required amendment scope: 113,945 usable rows plus verification of the hash-pinned aggregate and official missing-skeleton list instead of 114,480 declared per-sample files.
- Pose-track counts: `{"1": 89253, "2": 24692}`
- Nonempty-track counts: `{"1": 89253, "2": 24692}`
- Source frame-count range: 15 to 300
- Keypoint tail shape: `[17, 2]`
- Confidence tail shape: `[17]`

No placeholder rows were fabricated for officially missing skeletons.

## File checksums

| File | Rows | Classes | SHA-256 |
| --- | ---: | ---: | --- |
| `source-inventory.jsonl` | 113945 | 120 | `e0ab842fe2a62b50ff7205d0f8658fad373a03c5b29527c281a2db0225ea0058` |
| `development-train.jsonl` | 76013 | 80 | `2278b58090dbd3a00255936c8e4a2bd40887af995a88672334e4ed296605661c` |
| `development-validation.jsonl` | 18988 | 20 | `339f330d21e8a4bb712585d8c4074adac0adfad253c9046d3a397451f2f69b15` |
| `final-train.jsonl` | 95001 | 100 | `5775b0b05dd2c80504433273d620069c64804a705a8f373a217e318c4aa28622` |
| `official-novel.jsonl` | 18944 | 20 | `44a0da454a930530e56a6a398ede145cc6f8f0258403c01df7676305c143ba1c` |
| `novel-anchor.jsonl` | 20 | 20 | `176cd1715bfdff30613381834b90c7e0aba434648780e0ea435f2ccaab440d30` |
| `novel-query-primary.jsonl` | 18884 | 20 | `c401ee11b3b0965ce46c3fb06e30eaa4859efbc8eb74931273ad793f77d9b4b9` |
| `novel-query-official.jsonl` | 18924 | 20 | `cf74650e6c0d5fda31d4a3dc59fcd3825ca0b8f166e1963d85ac449d525412e9` |

## Counts by class and split

| Action | Source inventory | `development-train.jsonl` | `development-validation.jsonl` | `final-train.jsonl` | `official-novel.jsonl` | `novel-anchor.jsonl` | `novel-query-primary.jsonl` | `novel-query-official.jsonl` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A001 | 940 | 0 | 0 | 0 | 940 | 1 | 937 | 939 |
| A002 | 941 | 0 | 941 | 941 | 0 | 0 | 0 | 0 |
| A003 | 938 | 938 | 0 | 938 | 0 | 0 | 0 | 0 |
| A004 | 940 | 940 | 0 | 940 | 0 | 0 | 0 | 0 |
| A005 | 942 | 942 | 0 | 942 | 0 | 0 | 0 | 0 |
| A006 | 943 | 943 | 0 | 943 | 0 | 0 | 0 | 0 |
| A007 | 944 | 0 | 0 | 0 | 944 | 1 | 941 | 943 |
| A008 | 941 | 0 | 941 | 941 | 0 | 0 | 0 | 0 |
| A009 | 936 | 936 | 0 | 936 | 0 | 0 | 0 | 0 |
| A010 | 941 | 941 | 0 | 941 | 0 | 0 | 0 | 0 |
| A011 | 937 | 937 | 0 | 937 | 0 | 0 | 0 | 0 |
| A012 | 932 | 932 | 0 | 932 | 0 | 0 | 0 | 0 |
| A013 | 938 | 0 | 0 | 0 | 938 | 1 | 935 | 937 |
| A014 | 943 | 0 | 943 | 943 | 0 | 0 | 0 | 0 |
| A015 | 945 | 945 | 0 | 945 | 0 | 0 | 0 | 0 |
| A016 | 940 | 940 | 0 | 940 | 0 | 0 | 0 | 0 |
| A017 | 943 | 943 | 0 | 943 | 0 | 0 | 0 | 0 |
| A018 | 941 | 941 | 0 | 941 | 0 | 0 | 0 | 0 |
| A019 | 942 | 0 | 0 | 0 | 942 | 1 | 939 | 941 |
| A020 | 939 | 0 | 939 | 939 | 0 | 0 | 0 | 0 |
| A021 | 942 | 942 | 0 | 942 | 0 | 0 | 0 | 0 |
| A022 | 943 | 943 | 0 | 943 | 0 | 0 | 0 | 0 |
| A023 | 944 | 944 | 0 | 944 | 0 | 0 | 0 | 0 |
| A024 | 946 | 946 | 0 | 946 | 0 | 0 | 0 | 0 |
| A025 | 946 | 0 | 0 | 0 | 946 | 1 | 943 | 945 |
| A026 | 947 | 0 | 947 | 947 | 0 | 0 | 0 | 0 |
| A027 | 948 | 948 | 0 | 948 | 0 | 0 | 0 | 0 |
| A028 | 944 | 944 | 0 | 944 | 0 | 0 | 0 | 0 |
| A029 | 944 | 944 | 0 | 944 | 0 | 0 | 0 | 0 |
| A030 | 944 | 944 | 0 | 944 | 0 | 0 | 0 | 0 |
| A031 | 944 | 0 | 0 | 0 | 944 | 1 | 941 | 943 |
| A032 | 947 | 0 | 947 | 947 | 0 | 0 | 0 | 0 |
| A033 | 946 | 946 | 0 | 946 | 0 | 0 | 0 | 0 |
| A034 | 947 | 947 | 0 | 947 | 0 | 0 | 0 | 0 |
| A035 | 947 | 947 | 0 | 947 | 0 | 0 | 0 | 0 |
| A036 | 946 | 946 | 0 | 946 | 0 | 0 | 0 | 0 |
| A037 | 946 | 0 | 0 | 0 | 946 | 1 | 943 | 945 |
| A038 | 948 | 0 | 948 | 948 | 0 | 0 | 0 | 0 |
| A039 | 948 | 948 | 0 | 948 | 0 | 0 | 0 | 0 |
| A040 | 936 | 936 | 0 | 936 | 0 | 0 | 0 | 0 |
| A041 | 948 | 948 | 0 | 948 | 0 | 0 | 0 | 0 |
| A042 | 947 | 947 | 0 | 947 | 0 | 0 | 0 | 0 |
| A043 | 946 | 0 | 0 | 0 | 946 | 1 | 943 | 945 |
| A044 | 946 | 0 | 946 | 946 | 0 | 0 | 0 | 0 |
| A045 | 947 | 947 | 0 | 947 | 0 | 0 | 0 | 0 |
| A046 | 948 | 948 | 0 | 948 | 0 | 0 | 0 | 0 |
| A047 | 948 | 948 | 0 | 948 | 0 | 0 | 0 | 0 |
| A048 | 946 | 946 | 0 | 946 | 0 | 0 | 0 | 0 |
| A049 | 946 | 0 | 0 | 0 | 946 | 1 | 943 | 945 |
| A050 | 941 | 0 | 941 | 941 | 0 | 0 | 0 | 0 |
| A051 | 945 | 945 | 0 | 945 | 0 | 0 | 0 | 0 |
| A052 | 946 | 946 | 0 | 946 | 0 | 0 | 0 | 0 |
| A053 | 948 | 948 | 0 | 948 | 0 | 0 | 0 | 0 |
| A054 | 941 | 941 | 0 | 941 | 0 | 0 | 0 | 0 |
| A055 | 906 | 0 | 0 | 0 | 906 | 1 | 903 | 905 |
| A056 | 948 | 0 | 948 | 948 | 0 | 0 | 0 | 0 |
| A057 | 945 | 945 | 0 | 945 | 0 | 0 | 0 | 0 |
| A058 | 948 | 948 | 0 | 948 | 0 | 0 | 0 | 0 |
| A059 | 939 | 939 | 0 | 939 | 0 | 0 | 0 | 0 |
| A060 | 940 | 940 | 0 | 940 | 0 | 0 | 0 | 0 |
| A061 | 935 | 0 | 0 | 0 | 935 | 1 | 932 | 934 |
| A062 | 943 | 0 | 943 | 943 | 0 | 0 | 0 | 0 |
| A063 | 951 | 951 | 0 | 951 | 0 | 0 | 0 | 0 |
| A064 | 952 | 952 | 0 | 952 | 0 | 0 | 0 | 0 |
| A065 | 955 | 955 | 0 | 955 | 0 | 0 | 0 | 0 |
| A066 | 955 | 955 | 0 | 955 | 0 | 0 | 0 | 0 |
| A067 | 954 | 0 | 0 | 0 | 954 | 1 | 951 | 953 |
| A068 | 957 | 0 | 957 | 957 | 0 | 0 | 0 | 0 |
| A069 | 957 | 957 | 0 | 957 | 0 | 0 | 0 | 0 |
| A070 | 957 | 957 | 0 | 957 | 0 | 0 | 0 | 0 |
| A071 | 957 | 957 | 0 | 957 | 0 | 0 | 0 | 0 |
| A072 | 957 | 957 | 0 | 957 | 0 | 0 | 0 | 0 |
| A073 | 954 | 0 | 0 | 0 | 954 | 1 | 951 | 953 |
| A074 | 951 | 0 | 951 | 951 | 0 | 0 | 0 | 0 |
| A075 | 946 | 946 | 0 | 946 | 0 | 0 | 0 | 0 |
| A076 | 955 | 955 | 0 | 955 | 0 | 0 | 0 | 0 |
| A077 | 955 | 955 | 0 | 955 | 0 | 0 | 0 | 0 |
| A078 | 955 | 955 | 0 | 955 | 0 | 0 | 0 | 0 |
| A079 | 956 | 0 | 0 | 0 | 956 | 1 | 953 | 955 |
| A080 | 958 | 0 | 958 | 958 | 0 | 0 | 0 | 0 |
| A081 | 954 | 954 | 0 | 954 | 0 | 0 | 0 | 0 |
| A082 | 958 | 958 | 0 | 958 | 0 | 0 | 0 | 0 |
| A083 | 958 | 958 | 0 | 958 | 0 | 0 | 0 | 0 |
| A084 | 954 | 954 | 0 | 954 | 0 | 0 | 0 | 0 |
| A085 | 957 | 0 | 0 | 0 | 957 | 1 | 954 | 956 |
| A086 | 957 | 0 | 957 | 957 | 0 | 0 | 0 | 0 |
| A087 | 959 | 959 | 0 | 959 | 0 | 0 | 0 | 0 |
| A088 | 960 | 960 | 0 | 960 | 0 | 0 | 0 | 0 |
| A089 | 959 | 959 | 0 | 959 | 0 | 0 | 0 | 0 |
| A090 | 960 | 960 | 0 | 960 | 0 | 0 | 0 | 0 |
| A091 | 956 | 0 | 0 | 0 | 956 | 1 | 953 | 955 |
| A092 | 947 | 0 | 947 | 947 | 0 | 0 | 0 | 0 |
| A093 | 957 | 957 | 0 | 957 | 0 | 0 | 0 | 0 |
| A094 | 954 | 954 | 0 | 954 | 0 | 0 | 0 | 0 |
| A095 | 956 | 956 | 0 | 956 | 0 | 0 | 0 | 0 |
| A096 | 957 | 957 | 0 | 957 | 0 | 0 | 0 | 0 |
| A097 | 958 | 0 | 0 | 0 | 958 | 1 | 955 | 957 |
| A098 | 957 | 0 | 957 | 957 | 0 | 0 | 0 | 0 |
| A099 | 958 | 958 | 0 | 958 | 0 | 0 | 0 | 0 |
| A100 | 957 | 957 | 0 | 957 | 0 | 0 | 0 | 0 |
| A101 | 957 | 957 | 0 | 957 | 0 | 0 | 0 | 0 |
| A102 | 957 | 957 | 0 | 957 | 0 | 0 | 0 | 0 |
| A103 | 958 | 0 | 0 | 0 | 958 | 1 | 955 | 957 |
| A104 | 959 | 0 | 959 | 959 | 0 | 0 | 0 | 0 |
| A105 | 958 | 958 | 0 | 958 | 0 | 0 | 0 | 0 |
| A106 | 959 | 959 | 0 | 959 | 0 | 0 | 0 | 0 |
| A107 | 960 | 960 | 0 | 960 | 0 | 0 | 0 | 0 |
| A108 | 959 | 959 | 0 | 959 | 0 | 0 | 0 | 0 |
| A109 | 959 | 0 | 0 | 0 | 959 | 1 | 956 | 958 |
| A110 | 958 | 0 | 958 | 958 | 0 | 0 | 0 | 0 |
| A111 | 959 | 959 | 0 | 959 | 0 | 0 | 0 | 0 |
| A112 | 960 | 960 | 0 | 960 | 0 | 0 | 0 | 0 |
| A113 | 959 | 959 | 0 | 959 | 0 | 0 | 0 | 0 |
| A114 | 959 | 959 | 0 | 959 | 0 | 0 | 0 | 0 |
| A115 | 959 | 0 | 0 | 0 | 959 | 1 | 956 | 958 |
| A116 | 960 | 0 | 960 | 960 | 0 | 0 | 0 | 0 |
| A117 | 958 | 958 | 0 | 958 | 0 | 0 | 0 | 0 |
| A118 | 959 | 959 | 0 | 959 | 0 | 0 | 0 | 0 |
| A119 | 957 | 957 | 0 | 957 | 0 | 0 | 0 | 0 |
| A120 | 960 | 960 | 0 | 960 | 0 | 0 | 0 | 0 |

## Primary-query exclusions

The primary query differs from the exact-official query only by the following synchronized camera views of official anchor performances. Other synchronized query views are retained.

| Excluded query | Anchor | Setup | Performer | Repetition | Action | Reason |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `S001C001P008R001A001` | `S001C003P008R001A001` | 1 | 8 | 1 | A001 | synchronized camera view of the anchor performance |
| `S001C001P008R001A007` | `S001C003P008R001A007` | 1 | 8 | 1 | A007 | synchronized camera view of the anchor performance |
| `S001C001P008R001A013` | `S001C003P008R001A013` | 1 | 8 | 1 | A013 | synchronized camera view of the anchor performance |
| `S001C001P008R001A019` | `S001C003P008R001A019` | 1 | 8 | 1 | A019 | synchronized camera view of the anchor performance |
| `S001C001P008R001A025` | `S001C003P008R001A025` | 1 | 8 | 1 | A025 | synchronized camera view of the anchor performance |
| `S001C001P008R001A031` | `S001C003P008R001A031` | 1 | 8 | 1 | A031 | synchronized camera view of the anchor performance |
| `S001C001P008R001A037` | `S001C003P008R001A037` | 1 | 8 | 1 | A037 | synchronized camera view of the anchor performance |
| `S001C001P008R001A043` | `S001C003P008R001A043` | 1 | 8 | 1 | A043 | synchronized camera view of the anchor performance |
| `S001C001P008R001A049` | `S001C003P008R001A049` | 1 | 8 | 1 | A049 | synchronized camera view of the anchor performance |
| `S001C001P008R001A055` | `S001C003P008R001A055` | 1 | 8 | 1 | A055 | synchronized camera view of the anchor performance |
| `S001C002P008R001A001` | `S001C003P008R001A001` | 1 | 8 | 1 | A001 | synchronized camera view of the anchor performance |
| `S001C002P008R001A007` | `S001C003P008R001A007` | 1 | 8 | 1 | A007 | synchronized camera view of the anchor performance |
| `S001C002P008R001A013` | `S001C003P008R001A013` | 1 | 8 | 1 | A013 | synchronized camera view of the anchor performance |
| `S001C002P008R001A019` | `S001C003P008R001A019` | 1 | 8 | 1 | A019 | synchronized camera view of the anchor performance |
| `S001C002P008R001A025` | `S001C003P008R001A025` | 1 | 8 | 1 | A025 | synchronized camera view of the anchor performance |
| `S001C002P008R001A031` | `S001C003P008R001A031` | 1 | 8 | 1 | A031 | synchronized camera view of the anchor performance |
| `S001C002P008R001A037` | `S001C003P008R001A037` | 1 | 8 | 1 | A037 | synchronized camera view of the anchor performance |
| `S001C002P008R001A043` | `S001C003P008R001A043` | 1 | 8 | 1 | A043 | synchronized camera view of the anchor performance |
| `S001C002P008R001A049` | `S001C003P008R001A049` | 1 | 8 | 1 | A049 | synchronized camera view of the anchor performance |
| `S001C002P008R001A055` | `S001C003P008R001A055` | 1 | 8 | 1 | A055 | synchronized camera view of the anchor performance |
| `S018C001P008R001A061` | `S018C003P008R001A061` | 18 | 8 | 1 | A061 | synchronized camera view of the anchor performance |
| `S018C001P008R001A067` | `S018C003P008R001A067` | 18 | 8 | 1 | A067 | synchronized camera view of the anchor performance |
| `S018C001P008R001A073` | `S018C003P008R001A073` | 18 | 8 | 1 | A073 | synchronized camera view of the anchor performance |
| `S018C001P008R001A079` | `S018C003P008R001A079` | 18 | 8 | 1 | A079 | synchronized camera view of the anchor performance |
| `S018C001P008R001A085` | `S018C003P008R001A085` | 18 | 8 | 1 | A085 | synchronized camera view of the anchor performance |
| `S018C001P008R001A091` | `S018C003P008R001A091` | 18 | 8 | 1 | A091 | synchronized camera view of the anchor performance |
| `S018C001P008R001A097` | `S018C003P008R001A097` | 18 | 8 | 1 | A097 | synchronized camera view of the anchor performance |
| `S018C001P008R001A103` | `S018C003P008R001A103` | 18 | 8 | 1 | A103 | synchronized camera view of the anchor performance |
| `S018C001P008R001A109` | `S018C003P008R001A109` | 18 | 8 | 1 | A109 | synchronized camera view of the anchor performance |
| `S018C001P008R001A115` | `S018C003P008R001A115` | 18 | 8 | 1 | A115 | synchronized camera view of the anchor performance |
| `S018C002P008R001A061` | `S018C003P008R001A061` | 18 | 8 | 1 | A061 | synchronized camera view of the anchor performance |
| `S018C002P008R001A067` | `S018C003P008R001A067` | 18 | 8 | 1 | A067 | synchronized camera view of the anchor performance |
| `S018C002P008R001A073` | `S018C003P008R001A073` | 18 | 8 | 1 | A073 | synchronized camera view of the anchor performance |
| `S018C002P008R001A079` | `S018C003P008R001A079` | 18 | 8 | 1 | A079 | synchronized camera view of the anchor performance |
| `S018C002P008R001A085` | `S018C003P008R001A085` | 18 | 8 | 1 | A085 | synchronized camera view of the anchor performance |
| `S018C002P008R001A091` | `S018C003P008R001A091` | 18 | 8 | 1 | A091 | synchronized camera view of the anchor performance |
| `S018C002P008R001A097` | `S018C003P008R001A097` | 18 | 8 | 1 | A097 | synchronized camera view of the anchor performance |
| `S018C002P008R001A103` | `S018C003P008R001A103` | 18 | 8 | 1 | A103 | synchronized camera view of the anchor performance |
| `S018C002P008R001A109` | `S018C003P008R001A109` | 18 | 8 | 1 | A109 | synchronized camera view of the anchor performance |
| `S018C002P008R001A115` | `S018C003P008R001A115` | 18 | 8 | 1 | A115 | synchronized camera view of the anchor performance |

## Verified invariants

- Every source annotation has one unique canonical sample ID and normalized metadata.
- Development training and validation classes are disjoint (80/20 classes).
- Final training is exactly the union of both development partitions (100 classes).
- Official novel samples are disjoint from auxiliary samples and complete source coverage.
- There is exactly one official anchor for each of the 20 novel actions.
- Exact-official queries are official novel samples minus anchors.
- Primary queries are exact-official queries minus anchor-performance camera mates.
- Every JSONL file preserves its declared source or published-anchor order.
